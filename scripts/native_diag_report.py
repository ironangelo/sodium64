#!/usr/bin/env python3
"""Decode a PRIVATE S64D console diagnostic SRAM save; no external packages.

Supply the matching CPU ELF/map to symbolicate EPC samples. A halted RSP PC
belongs to the *captured IMEM*, including a possibly installed overlay bank.
The post-HALT PC is intrusive diagnostic evidence, not a pre-stop live PC.
"""
from __future__ import annotations
import argparse, bisect, collections, json, struct
from pathlib import Path

MAGIC = 0x53363444
SIZE = 0x8000
HEADER = 0x2000
FIELDS = [
    "magic", "version", "complete", "reason", "save_size", "count_hz",
    "sample_interval", "sample_capacity", "sample_count", "pc_next_byte",
    "event_count", "event_capacity", "seconds_count", "elapsed_ticks",
    "frames_completed", "frames_submitted", "vi_count", "sections_created",
    "start_count", "stop_count", "last_progress_count", "precision", "frameskip",
    "apu_clock", "audio", "layer", "cpu_epc", "cpu_cause", "cpu_status",
    "sp_status_before", "sp_dma_busy_before", "sp_dma_full_before",
    "dp_status_before", "dp_start_before", "dp_end_before", "dp_current_before",
    "sp_status_after", "sp_pc_after", "sp_dma_busy_after", "sp_dma_full_after",
    "dp_status_after", "dp_end_after", "dp_current_after", "mi_mask_before",
    "vi_origin", "vi_width", "ai_status", "ai_length", "dsp_pointer", "dsp_enabled",
    "section_pointer", "cur_line", "queue_id", "sp_mem_address", "sp_dram_address",
    "observer_ticks", "observer_max_ticks", "halt_acknowledged", "sp_dma_settled",
    "pi_status_before", "body_sum32", "direct_wait_pc",
]
EVENT_FIELDS = ["sequence", "elapsed_ticks", "cpu_epc", "frames_completed",
                "frames_submitted", "sp_status", "dp_status", "dp_start", "dp_end",
                "dp_current", "sp_dma_busy", "sp_dma_full", "cur_line",
                "band_y", "screen", "sections_created"]
SECOND_FIELDS = ["sequence", "elapsed_ticks", "vi_count", "frames_completed",
                 "frames_submitted", "samples", "cpu_rsp_wait", "cpu_frame_wait",
                 "cpu_apu_jit", "cpu_other", "sp_running", "dp_cmd_busy",
                 "dp_pipe_busy", "dp_tmem_busy", "sections_created", "observer_ticks"]

def normalize(blob):
    if len(blob) < SIZE:
        raise ValueError(f"need a complete 32 KiB SRAM save; got {len(blob)} bytes")
    blob = blob[:SIZE]
    if int.from_bytes(blob[HEADER:HEADER+4], "big") == MAGIC:
        return blob, "big-endian"
    for width, name in [(4, "word-swapped"), (2, "halfword-swapped")]:
        changed = b"".join(blob[i:i+width][::-1] for i in range(0, len(blob), width))
        if int.from_bytes(changed[HEADER:HEADER+4], "big") == MAGIC:
            return changed, name
    raise ValueError("no S64D header at save+0x2000; wrong save or no capture")

def parse(blob):
    blob, order = normalize(blob)
    h = dict(zip(FIELDS, struct.unpack_from(f">{len(FIELDS)}I", blob, HEADER)))
    if h["version"] != 1 or h["complete"] != 1:
        raise ValueError("unsupported or incomplete S64D capture")
    if h["reason"] not in (1, 2) or h["save_size"] != SIZE:
        raise ValueError("invalid trigger or save size")
    if h["count_hz"] != 46875000 or h["sample_interval"] != 131071:
        raise ValueError("unexpected sampling clock/interval")
    if h["sample_capacity"] != 2048 or h["event_capacity"] != 64:
        raise ValueError("unexpected ring capacities")
    if h["seconds_count"] > 20:
        raise ValueError("second records overlap the CPU register snapshot")
    if h["pc_next_byte"] >= 0x2000 or h["pc_next_byte"] % 4:
        raise ValueError("invalid CPU sample ring cursor")
    if h["pc_next_byte"] != (h["sample_count"] % 2048) * 4:
        raise ValueError("CPU sample count/cursor disagree")
    body = blob[:HEADER] + blob[HEADER+512:]
    checksum = sum(struct.unpack(f">{len(body)//4}I", body)) & 0xFFFFFFFF
    if checksum != h["body_sum32"]:
        raise ValueError("save payload checksum mismatch; reject truncated/stale capture")
    h["byte_order"] = order
    h["elapsed_seconds_count_domain"] = h["elapsed_ticks"]/h["count_hz"]
    h["observer_fraction"] = h["observer_ticks"]/max(1,h["elapsed_ticks"])
    h["sp_pc_meaningful_after_halt"] = bool(h["halt_acknowledged"] and h["sp_status_after"] & 1)
    h["cpu_epc_instruction"] = h["cpu_epc"] + (4 if h["cpu_cause"] & 0x80000000 else 0)
    h["capture_via"] = "direct wait watchdog" if h["direct_wait_pc"] else "timer watchdog"
    h["guest_cpu_pc_raw"] = struct.unpack_from(">Q", blob, 0x7C00+23*8)[0]
    capacity = 2048
    count = min(h["sample_count"], capacity)
    start = h["sample_count"] % capacity if h["sample_count"] >= capacity else 0
    pcs = list(struct.unpack_from(">2048I", blob, 0x2200))
    pcs = [pcs[(start+i)%capacity] for i in range(count)]
    events = []
    first = max(0,h["event_count"]-64)
    for index in range(first,h["event_count"]):
        values = struct.unpack_from(">16I",blob,0x4200+(index%64)*64)
        row = dict(zip(EVENT_FIELDS,values))
        if row["sequence"] != index+1:
            raise ValueError("event ring sequence mismatch")
        counters = struct.unpack_from(">4I",blob,0x7800+(index%64)*16)
        row["dp_cycle_counters24"] = [x & 0xFFFFFF for x in counters]
        if events:
            dt = row["elapsed_ticks"]-events[-1]["elapsed_ticks"]
            # A 24-bit RCP counter can wrap in ~0.268s. A long observation gap
            # cannot establish how many wraps occurred; retain raw values only.
            row["dp_counter_delta_unambiguous"] = 0 < dt < h["count_hz"]//4
            row["dp_cycle_deltas_mod24"] = [
                (a-b)&0xFFFFFF for a,b in zip(row["dp_cycle_counters24"],events[-1]["dp_cycle_counters24"])]
        events.append(row)
    seconds = []
    previous = dict(elapsed_ticks=0,vi_count=0,frames_completed=0,frames_submitted=0,
                    observer_ticks=0,sections_created=0)
    for i in range(h["seconds_count"]):
        row = dict(zip(SECOND_FIELDS,struct.unpack_from(">16I",blob,0x7200+i*64)))
        if row["sequence"] != i+1:
            raise ValueError("second record sequence mismatch")
        dt = row["elapsed_ticks"]-previous["elapsed_ticks"]
        if dt <= 0 or row["frames_completed"] < previous["frames_completed"]:
            raise ValueError("non-monotonic measurement interval")
        row["duration_seconds_count_domain"] = dt/h["count_hz"]
        row["completed_frames_in_interval"] = row["frames_completed"]-previous["frames_completed"]
        row["completed_fps_count_domain"] = row["completed_frames_in_interval"]/row["duration_seconds_count_domain"]
        row["vi_in_interval"] = row["vi_count"]-previous["vi_count"]
        row["observer_fraction"] = (row["observer_ticks"]-previous["observer_ticks"])/dt
        if sum(row[key] for key in ("cpu_rsp_wait","cpu_frame_wait","cpu_apu_jit","cpu_other")) != row["samples"]:
            raise ValueError("CPU occupancy buckets disagree with sample count")
        for key in ("sp_running","dp_cmd_busy","dp_pipe_busy","dp_tmem_busy"):
            if row[key] > row["samples"]:
                raise ValueError("hardware occupancy exceeds sample count")
        previous = row.copy()
        seconds.append(row)
    partial = struct.unpack_from(">9I",blob,HEADER+0x100)
    if sum(partial[1:5]) != partial[0]:
        raise ValueError("partial CPU bucket count mismatch")
    h["partial_window"] = dict(zip(SECOND_FIELDS[5:14],partial))
    # Export no game memory by default; the original save stays private.
    return {"header":h,"events":events,"seconds":seconds,"cpu_samples":pcs}, blob

def elf_symbols(path):
    """Read the ELF32/64 big-endian symbol table without a local MIPS toolchain."""
    b = Path(path).read_bytes()
    if b[:4] != b"\x7fELF":
        raise ValueError("expected matching CPU ELF")
    big = ">" if b[5] == 2 else "<"
    is64 = b[4] == 2
    hf = "16sHHIQQQIHHHHHH" if is64 else "16sHHIIIIIHHHHHH"
    sf = "IIQQQQIIQQ" if is64 else "IIIIIIIIII"
    hdr = struct.unpack_from(big+hf,b)
    sections = [struct.unpack_from(big+sf,b,hdr[6]+i*hdr[11]) for i in range(hdr[12])]
    result = []
    for sec in sections:
        if sec[1] != 2: continue
        strings = sections[sec[6]]
        names = b[strings[4]:strings[4]+strings[5]]
        size = sec[9]
        if not size: continue
        for offset in range(sec[4],sec[4]+sec[5],size):
            raw = struct.unpack_from(big+("IBBHQQ" if is64 else "IIIBBH"),b,offset)
            no,value,shndx = (raw[0],raw[4],raw[3]) if is64 else (raw[0],raw[1],raw[5])
            if no and shndx and value >= 0x80000000:
                name = names[no:].split(b"\0",1)[0].decode("utf-8","replace")
                result.append((value,name))
    return sorted(result)

def symbolicate(result, elf=None, linker_map=None):
    symbols = elf_symbols(elf) if elf else []
    addresses = [x[0] for x in symbols]
    def lookup(pc):
        if 0x801C0000 <= pc < 0x80200000: return "[APU JIT]"
        i = bisect.bisect_right(addresses,pc)-1
        if i < 0: return f"0x{pc:08X}"
        address,name = symbols[i]
        return name+(f"+0x{pc-address:X}" if pc != address else "")
    counts = collections.Counter(result["cpu_samples"])
    result["cpu_hotspots"] = [
        dict(pc=f"0x{pc:08X}",symbol=lookup(pc),samples=n)
        for pc,n in counts.most_common(30)
    ]
    result["header"]["cpu_epc_symbol"] = lookup(result["header"]["cpu_epc_instruction"])
    if result["header"]["direct_wait_pc"]:
        result["header"]["direct_wait_symbol"] = lookup(result["header"]["direct_wait_pc"])
    if linker_map:
        from profile_report import load_text_ranges, object_for_pc
        starts,ranges = load_text_ranges(Path(linker_map))
        modules = collections.Counter()
        for pc in result["cpu_samples"]:
            name = "APU JIT" if 0x801C0000 <= pc < 0x80200000 else object_for_pc(pc,starts,ranges) or "unknown"
            modules[name] += 1
        result["cpu_modules"] = dict(modules.most_common())
    return result

def render(result):
    h = result["header"]
    lines = ["Sodium64 S64D diagnostic capture",
             f"Trigger: {'NO COMPLETED FRAME FOR 2s' if h['reason']==1 else '20s TIME LIMIT'}",
             f"CPU EPC: 0x{h['cpu_epc']:08X} ({h.get('cpu_epc_symbol','unsymbolicated')})",
             f"Capture path: {h['capture_via']}; direct wait PC: 0x{h['direct_wait_pc']:08X}",
             f"Pre-stop SP: 0x{h['sp_status_before']:08X}; DP: 0x{h['dp_status_before']:08X}",
             f"Pre-stop DP CURRENT/END: 0x{h['dp_current_before']:08X}/0x{h['dp_end_before']:08X}",
             f"RSP PC after requested HALT: 0x{h['sp_pc_after']:08X}; valid={h['sp_pc_meaningful_after_halt']}",
             f"Count-domain duration: {h['elapsed_seconds_count_domain']:.3f}s",
             f"Observer cost (measured ISR body): {100*h['observer_fraction']:.2f}%",
             "Diagnostic FPS include observer cost; console origin must be independently established.",
             "DP pipe/TMEM busy bits are sampled status, not independent exact active-time counters.",
             "Interval | completed FPS | samples | CPU RSP wait | SP running | DP cmd busy"]
    for row in result["seconds"]:
        samples=max(1,row["samples"])
        lines.append(f"{row['sequence']:2d} | {row['completed_fps_count_domain']:6.2f} | {row['samples']:4d} | "
                     f"{100*row['cpu_rsp_wait']/samples:6.1f}% | {100*row['sp_running']/samples:6.1f}% | "
                     f"{100*row['dp_cmd_busy']/samples:6.1f}%")
    lines.append("CPU hotspots in retained sample ring:")
    for row in result.get("cpu_hotspots",[])[:12]:
        lines.append(f"  {row['samples']:4d} {row['symbol']}")
    return "\n".join(lines)+"\n"

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("save",type=Path)
    ap.add_argument("--elf",type=Path)
    ap.add_argument("--map",type=Path,dest="linker_map")
    ap.add_argument("--json-output",type=Path)
    ap.add_argument("--extract-private",type=Path,help="PRIVATE directory for DMEM/IMEM; never publish game-derived dumps")
    a=ap.parse_args()
    result,blob=parse(a.save.read_bytes())
    symbolicate(result,a.elf,a.linker_map)
    print(render(result),end="")
    if a.json_output: a.json_output.write_text(json.dumps(result,indent=2)+"\n")
    if a.extract_private:
        a.extract_private.mkdir(parents=True,exist_ok=True)
        (a.extract_private/"dmem.bin").write_bytes(blob[0x5200:0x6200])
        (a.extract_private/"imem.bin").write_bytes(blob[0x6200:0x7200])
    return 0
if __name__ == "__main__":
    try: raise SystemExit(main())
    except (OSError,ValueError,struct.error) as e: raise SystemExit(f"error: {e}")
