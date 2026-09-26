#!/usr/bin/env python3
"""Classify the guest-only single-heavy-tile Mode7 discriminator."""

from __future__ import annotations
import argparse,json,tempfile
from pathlib import Path
import make_gate_c_hcomp_mode7_single_heavy_boot as guestcfg

ROOT=Path(__file__).resolve().parents[1]
SLOT0_SENTINEL=bytes.fromhex("1122334455667788")
SLOT1_SENTINEL=bytes.fromhex("99AABBCCDDEEFF00")
MAILBOX_SENTINEL=bytes.fromhex("DEADBEEFCAFEBABE")
EXPECTED_GUEST=bytes((0x00,0x33,0x02,0x01,0x01,0x00,0x00,0x00))
MODE7_MASK=0x3FFFF

def swap32(data:bytes)->bytes:
    if len(data)%4:
        raise ValueError("word_swap32 requires multiple of four")
    return b"".join(data[i:i+4][::-1] for i in range(0,len(data),4))

def match(raw:bytes,target:bytes):
    for mode,data in (("identity",raw),("word_swap32",swap32(raw))):
        if data==target:
            return mode
    return None

def marker(raw:bytes):
    expected_tail=bytes(6)
    for mode,data in (("identity",raw),("word_swap32",swap32(raw))):
        if len(data)==8 and data[1]==0x51 and data[0] in (0x00,0xFF) and data[2:]==expected_tail:
            return mode,data
    return None

def signed16(v:int)->int:
    return v-0x10000 if v&0x8000 else v

def minmax(a0:int,a1:int)->tuple[int,int]:
    vals=(0,a0,a1,a0+a1)
    return min(vals),max(vals)

def model_contract()->dict:
    mode7=(ROOT/"src/rsp_mode7.S").read_text()
    ppu=(ROOT/"src/ppu.S").read_text()

    for anchor in (
        "addi t7, t0, 3 // Width shift",
        "li s0, 0",
        "lbu t0, SHIFT_TABLE(t7)",
        "bne t6, t1, set_texels",
        "bnez t0, finish_tile7",
        "jal dma_write",
        "jal rdp_send",
        "add s0, s0, t0",
        "blt s0, 256, next_tile7",
    ):
        if anchor not in mode7:
            raise AssertionError(f"Mode7 source anchor drift: {anchor}")
    if "mode7_mask: .word 0x0003FFFF" not in mode7:
        raise AssertionError("MODE7 mask drift")
    if "write_bg1hofs:" not in ppu or "sh t0, m7hofs" not in ppu:
        raise AssertionError("BG1HOFS->M7HOFS contract drift")

    if guestcfg.M7_OOB_EMPTY!=0x80:
        raise AssertionError("M7SEL must use native OOB-empty mode")
    if (guestcfg.M7_A,guestcfg.M7_HOFS,guestcfg.M7_X,guestcfg.M7_Y)!=(0x80,0x3F8,0x3F8,0):
        raise AssertionError("single-heavy guest constants drift")
    if (guestcfg.IRQ1_LINE,guestcfg.IRQ2_LINE)!=(80,82):
        raise AssertionError("section height drift")

    a=signed16(guestcfg.M7_A)
    c=0
    b=d=0
    s1=guestcfg.IRQ1_LINE
    k1=guestcfg.IRQ2_LINE
    t7=4 if (-0x100<=a<=0xFF and -0x100<=c<=0xFF) else 3
    if t7!=4:
        raise AssertionError("expected 16-pixel Mode7 tile width")

    a3=min(k1-s1-1,7)
    xbounds=minmax(a3*b,(a<<t7)-a)
    ybounds=minmax(a3*d,(c<<t7)-c)

    t8=(guestcfg.M7_X<<8)+(guestcfg.M7_HOFS-guestcfg.M7_X)*a
    t9=(guestcfg.M7_Y<<8)+(s1-guestcfg.M7_Y+1)*d
    step=1<<t7
    heavy=[]
    rows=[]
    for index,s0 in enumerate(range(0,256,step)):
        xmin=t8+xbounds[0]; xmax=t8+xbounds[1]
        ymin=t9+ybounds[0]; ymax=t9+ybounds[1]
        skip=((xmin|ymin)>MODE7_MASK) and ((xmax|ymax)>MODE7_MASK)
        rows.append((index,s0,xmin,xmax,skip))
        if not skip:
            heavy.append(index)
        t8+=a<<t7

    if heavy!=[0]:
        raise AssertionError(f"expected exactly first tile heavy, got {heavy}")
    if rows[0][2:]!=(260096,262016,False):
        raise AssertionError(f"first tile bounds drift: {rows[0]}")
    if rows[1][2] != 262144 or not rows[1][4]:
        raise AssertionError(f"second tile should begin OOB: {rows[1]}")

    return {
        "heavy_tiles":heavy,
        "tile0_x":[rows[0][2],rows[0][3]],
        "tile1_x_start":rows[1][2],
        "width_shift":t7,
    }

def classify(root:Path)->dict:
    model=model_contract()
    s0=(root/"mode7-texture-slot0.bin").read_bytes()
    s1=(root/"mode7-texture-slot1.bin").read_bytes()
    mb=(root/"mailbox.bin").read_bytes()
    gs=(root/"guest-state.bin").read_bytes()
    if any(len(x)!=8 for x in (s0,s1,mb,gs)):
        return {"passed":False,"reason":"evidence size mismatch"}

    gm=match(gs,EXPECTED_GUEST)
    if gm is None:
        return {"passed":False,"reason":"guest discriminator incomplete","guest_raw":gs.hex()}

    slot0_changed=match(s0,SLOT0_SENTINEL) is None
    slot1_seed_mode=match(s1,SLOT1_SENTINEL)
    if not slot0_changed:
        return {
            "passed":False,
            "reason":"single heavy tile texture DMA not observed",
            "slot0_raw":s0.hex(),
            "model":model,
        }
    if slot1_seed_mode is None:
        return {
            "passed":False,
            "reason":"second texture slot changed despite one-heavy model",
            "slot1_raw":s1.hex(),
            "model":model,
        }

    mm=match(mb,MAILBOX_SENTINEL)
    mk=marker(mb)
    if mk is not None:
        mailbox_mode=mk[0]; mailbox_norm=mk[1].hex()
        helper_observed=mk[1][0]==0xFF
        if not helper_observed:
            return {
                "passed":False,
                "reason":"H-COMP reached but color-window helper marker absent",
                "mailbox_normalization":mailbox_mode,
                "mailbox_normalized":mailbox_norm,
                "model":model,
            }
        classification="MODE7_SINGLE_HEAVY_HCOMP_HELPER_REACHED"
        meaning="one heavy Mode7 tile reached H-COMP and the existing F10..F17 mailbox transport directly observed color_window_all helper execution"
    elif mm is not None:
        return {
            "passed":False,
            "reason":"H-COMP/helper not reached",
            "mailbox_normalization":mm,
            "mailbox_normalized":MAILBOX_SENTINEL.hex(),
            "model":model,
        }
    else:
        return {"passed":False,"reason":"mailbox invalid","mailbox_raw":mb.hex(),"model":model}

    return {
        "passed":True,
        "classification":classification,
        "meaning":meaning,
        "semantic_scope":"pinned-Mupen localization only; not real-N64 timing/performance authority",
        "model":model,
        "slot0_changed":slot0_changed,
        "slot0_raw":s0.hex(),
        "slot1_unchanged":True,
        "slot1_raw":s1.hex(),
        "slot1_seed_normalization":slot1_seed_mode,
        "mailbox_normalization":mailbox_mode,
        "mailbox_normalized":mailbox_norm,
        "guest_normalization":gm,
        "helper_color_window_all_observed":True,
        "helper_marker_transport":"H-COMP existing DMA of DMEM F10..F17 to RDRAM 0xA00F0000",
    }

def self_test()->None:
    model=model_contract()
    assert model["heavy_tiles"]==[0]
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)
        (p/"guest-state.bin").write_bytes(EXPECTED_GUEST)
        (p/"mode7-texture-slot0.bin").write_bytes(bytes(8))
        (p/"mode7-texture-slot1.bin").write_bytes(SLOT1_SENTINEL)

        (p/"mailbox.bin").write_bytes(MAILBOX_SENTINEL)
        r=classify(p)
        assert not r["passed"] and r["reason"]=="H-COMP/helper not reached"

        (p/"mailbox.bin").write_bytes(swap32(bytes((0x00,0x51,0,0,0,0,0,0))))
        (p/"guest-state.bin").write_bytes(swap32(EXPECTED_GUEST))
        r=classify(p)
        assert not r["passed"] and r["reason"]=="H-COMP reached but color-window helper marker absent"

        (p/"mailbox.bin").write_bytes(swap32(bytes((0xFF,0x51,0,0,0,0,0,0))))
        r=classify(p)
        assert r["passed"] and r["classification"]=="MODE7_SINGLE_HEAVY_HCOMP_HELPER_REACHED"
        assert r["helper_color_window_all_observed"]

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("evidence",type=Path,nargs="?")
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    if args.self_test:
        self_test()
        print("Mode7 single-heavy classifier self-test: PASS")
        return 0
    if args.evidence is None:
        ap.error("evidence directory required")
    result=classify(args.evidence)
    text=json.dumps(result,indent=2,sort_keys=True)
    print(text)
    if args.output:
        args.output.write_text(text+"\n")
    return 0 if result.get("passed") else 1

if __name__=="__main__":
    raise SystemExit(main())
