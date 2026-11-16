"""Check emitted REMOTE DSP-read observer behavior and upper-memory ownership."""
import argparse
import json
from pathlib import Path
import re

from linked_cpu_regression import CPU, RETURN, load_elf, sx32

DSP_STATE = Path(__file__).resolve().parents[1] / "src/dsp_rsp_deadlines.h"
SP_STATUS = 0xA4040010


class ObserverCPU(CPU):
    def __init__(self, memory):
        super().__init__(memory)
        self.reads = set()

    def read(self, address, size=4):
        self.reads.add(address & 0x1FFFFFFF)
        return super().read(address, size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("elf", type=Path)
    args = parser.parse_args()
    mem, sym = load_elf(args.elf)
    cpu = ObserverCPU(mem)
    cpu.allow_rcp_writes = True
    words = {label: int(address, 16) for label, address
             in re.findall(r"^#define (DSP_\w+)\s+(0x\w+)$", DSP_STATE.read_text(), re.M)}
    assert set(words.values()) == set(range(0x80441CB0, 0x80441CD4, 4))
    assert sym["__bss_end"] <= 0x800BE200
    owned = {a & 0x1FFFFFFF for a in words.values()}

    def set_fields(**values):
        for name, value in values.items():
            cpu.write(words["DSP_" + name], value)

    def read_field(name):
        return cpu.read(words["DSP_" + name])

    def observe(entry, stop=RETURN):
        cpu.memory_writes.clear()
        cpu.reads.clear()
        cpu.execute(sym[entry], stop)
        return {a for a, _, _ in cpu.memory_writes}

    def init(ram, halt):
        cpu.write(sym["remote_boot_ram_bytes"], ram)
        cpu.write(SP_STATUS, halt)
        for address in owned:
            cpu.write(address, 0)

    cases = 0
    for ram, halt in ((0, 0), (0x400000, 0), (0x800000, 0), (0x800000, 1)):
        for index in range(256):
            init(ram, halt)
            set_fields(RSP_LAUNCHES=19)
            cpu.write(sym["dsp_addr"], index, 1)
            register = index & 0x7F
            value = (register * 31 + 17) & 255
            cpu.write(sym["dsp_regs"] + register, value, 1)
            cpu.pattern(index)
            initial = cpu.regs.copy()
            cpu.cp[9] = 917
            writes = observe("read_dspdata")
            assert cpu.regs[2] == value
            assert all(cpu.regs[i] == initial[i] for i in range(32) if i not in (1, 2, 8, 9, 10))
            enabled = ram == 0x800000
            if not enabled:
                assert not (owned & cpu.reads) and not writes
            assert writes <= owned
            assert read_field("REG_READS") == enabled
            assert read_field("VOLATILE_READS") == (enabled and
                (register == 0x7C or register & 0xF in (8, 9)))
            assert read_field("READ_JOBS") == (enabled and not halt)
            assert read_field("READ_COUNT") == (917 if enabled and not halt else 0)
            cases += 1

    # Cross COUNT wrap. A busy sample at each threshold increments once.
    init(0x800000, 0)
    cpu.write(sym["audio_set"], 4, 1)
    stamp = 0xFFFFF000
    set_fields(READ_STATE=1, READ_COUNT=stamp)
    for current, quarter, millisecond in ((11718, 0, 0), (11719, 1, 0), (11800, 1, 0),
                                           (46874, 1, 0), (46875, 1, 1), (59000, 1, 1)):
        cpu.pattern(1)
        cpu.regs[7] = 0
        cpu.cp[9] = (stamp + current) & 0xFFFFFFFF
        assert observe("dsp_sample", sym["dsp_rsp_deadline_done"]) <= owned
        assert read_field("READ_WAIT_PEAK") == current
        assert read_field("READ_WAIT_250US") == quarter
        assert read_field("READ_WAIT_1MS") == millisecond

    cpu.write(SP_STATUS, 1)
    cpu.cp[9] = (stamp + 65000) & 0xFFFFFFFF
    observe("dsp_sample", sym["dsp_rsp_deadline_done"])
    assert read_field("READ_WAIT_PEAK") == 59000
    assert read_field("READ_STATE") == 0

    # Starting a new job must clear pending demand while retaining its summary.
    set_fields(READ_STATE=3, RSP_LAUNCHES=19)
    cpu.write(sym["frame_count"], 1, 1)
    cpu.pattern()
    cpu.regs[12] = sx32(RETURN)
    writes = observe("frame_wait")
    assert writes <= owned | {SP_STATUS & 0x1FFFFFFF}
    assert cpu.read(SP_STATUS) == 1
    assert read_field("RSP_LAUNCHES") == 20
    assert read_field("READ_STATE") == 0 and read_field("READ_WAIT_PEAK") == 59000

    print(json.dumps({"register_cases": cases, "read_value_and_live_registers_preserved": True,
                      "threshold_checks": 6, "count32_wrap": True, "halt_keeps_peak": True,
                      "new_job_resets_pending": True, "upper_address_guard": True,
                      "static_end": hex(sym["__bss_end"])}, indent=2))


if __name__ == "__main__":
    main()
