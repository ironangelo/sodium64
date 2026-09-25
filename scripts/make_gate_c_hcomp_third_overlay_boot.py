#!/usr/bin/env python3
"""Boot-first Mode1 -> enabled OOB-zero-fill Mode7 -> Mode1 overlay guest.

Original/homebrew-only. It arms V-IRQ immediately so the first RSP frame,
rather than a later handoff, exercises both renderer directions before the
frame-end third H-COMP overlay. This deliberately avoids the pinned-Mupen
second-handoff HALT-visibility limitation.

WRAM $7E0000..$7E0006:
  0 frame token (kept at 0; no NMI needed)
  1 phase: 0x11 armed, 0x33 post-test
  2 IRQ count
  3 BGMODE mirror
  4 done
  5 token seen by IRQ1
  6 token seen by IRQ2
"""

from __future__ import annotations
import argparse, hashlib
from pathlib import Path
from make_gate_c_obj_window import (
    Assembler, emit_dma_from_rom, emit_lda_sta_abs, emit_vmadd, write_vector,
)

ROM_SIZE=0x8000
HEADER=0x7FC0
LOAD_ADDRESS=0x8000
IRQ_ADDRESS=0x8300
IRQ_OFFSET=IRQ_ADDRESS-LOAD_ADDRESS
BG_TILE_ADDRESS=0x9000
BG_MAP_ADDRESS=0x9040
PALETTE_ADDRESS=0x9840
CONTROL_MODE=0x01
TREATMENT_MODE=0x07
M7_OOB_ZERO_FILL=0xC0
M7_OOB=0x0FFF
ARMED_PHASE=0x11
POSTTEST_PHASE=0x33
IRQ1_LINE=80
IRQ2_LINE=82

def lda_sta_long(asm:Assembler,value:int,address:int)->None:
    asm.emit(0xA9,value,0x8F,address&0xFF,(address>>8)&0xFF,(address>>16)&0xFF)

def lda_long(asm:Assembler,address:int)->None:
    asm.emit(0xAF,address&0xFF,(address>>8)&0xFF,(address>>16)&0xFF)

def sta_long(asm:Assembler,address:int)->None:
    asm.emit(0x8F,address&0xFF,(address>>8)&0xFF,(address>>16)&0xFF)

def build_assets()->tuple[bytes,bytes,bytes]:
    tile=bytes([0xFF,0x00]*8+[0x00]*16)
    bg_map=bytes(0x800)
    palette=bytearray(0x200)
    palette[2:4]=(0x03E0).to_bytes(2,"little")
    return tile,bg_map,bytes(palette)

def build_program()->bytes:
    a=Assembler()
    a.emit(0x78,0x18,0xFB,0xD8)  # SEI; CLC; XCE; CLD
    a.emit(0xC2,0x10)             # REP #$10
    a.emit(0xE2,0x20)             # SEP #$20

    for value,address in (
        (0x80,0x2100),(CONTROL_MODE,0x2105),(0x04,0x2107),
        (0x01,0x210B),(0x80,0x2115),
    ):
        emit_lda_sta_abs(a,value,address)

    # Keep BG1 enabled and the same out-of-bounds centers, but use 0xC0 so
    # check_wrap enters set_texels. Later mode7_read still sees bit7 and
    # zero-fills OOB map rows in DMEM instead of issuing map-entry RDRAM DMA.
    emit_lda_sta_abs(a,M7_OOB_ZERO_FILL,0x211A)
    for address in (0x211F,0x2120):
        emit_lda_sta_abs(a,M7_OOB&0xFF,address)
        emit_lda_sta_abs(a,(M7_OOB>>8)&0x1F,address)

    emit_vmadd(a,0x1000)
    emit_dma_from_rom(a,channel=0,mode=1,bbus=0x18,source=BG_TILE_ADDRESS,size=0x20)
    emit_vmadd(a,0x0800)
    emit_dma_from_rom(a,channel=0,mode=1,bbus=0x18,source=BG_MAP_ADDRESS,size=0x800)
    emit_lda_sta_abs(a,0x00,0x2121)
    emit_dma_from_rom(a,channel=0,mode=0,bbus=0x22,source=PALETTE_ADDRESS,size=0x200)

    for value,address in (
        (0x01,0x212C),(0x00,0x212D),(0x00,0x212E),
        (0x00,0x212F),(0x00,0x2130),(0x00,0x2131),
    ):
        emit_lda_sta_abs(a,value,address)

    for address in range(0x7E0000,0x7E0007):
        lda_sta_long(a,0,address)
    lda_sta_long(a,ARMED_PHASE,0x7E0001)
    lda_sta_long(a,CONTROL_MODE,0x7E0003)

    # Arm the two-step visible V-IRQ chain before the first unblanked frame.
    emit_lda_sta_abs(a,IRQ1_LINE&0xFF,0x4209)
    emit_lda_sta_abs(a,(IRQ1_LINE>>8)&1,0x420A)
    emit_lda_sta_abs(a,0x20,0x4200)  # V-IRQ only; no NMI needed
    emit_lda_sta_abs(a,0x0F,0x2100)
    a.emit(0x58)                     # CLI

    a.label("main_loop")
    a.emit(0xCB)                     # WAI
    a.branch(0x80,"main_loop")

    a.pad_to(IRQ_OFFSET)
    a.label("irq")
    a.emit(0x48)
    a.emit(0xAD,0x11,0x42)           # clear TIMEUP
    lda_long(a,0x7E0002)
    a.emit(0x1A)
    sta_long(a,0x7E0002)
    a.emit(0xC9,0x01)
    a.branch(0xD0,"irq_second")

    lda_long(a,0x7E0000)
    sta_long(a,0x7E0005)
    emit_lda_sta_abs(a,TREATMENT_MODE,0x2105)
    lda_sta_long(a,TREATMENT_MODE,0x7E0003)
    emit_lda_sta_abs(a,IRQ2_LINE&0xFF,0x4209)
    emit_lda_sta_abs(a,(IRQ2_LINE>>8)&1,0x420A)
    a.branch(0x80,"irq_done")

    a.label("irq_second")
    a.emit(0xC9,0x02)
    a.branch(0xD0,"irq_done")
    lda_long(a,0x7E0000)
    sta_long(a,0x7E0006)
    emit_lda_sta_abs(a,CONTROL_MODE,0x2105)
    lda_sta_long(a,CONTROL_MODE,0x7E0003)
    emit_lda_sta_abs(a,0x00,0x4200)  # stop V-IRQ
    lda_sta_long(a,POSTTEST_PHASE,0x7E0001)
    lda_sta_long(a,0x01,0x7E0004)

    a.label("irq_done")
    a.emit(0x68,0x40)

    p=a.finish()
    if a.labels["irq"]!=IRQ_OFFSET: raise ValueError("IRQ moved")
    return p

def build_rom()->bytes:
    program=build_program()
    if len(program)>=BG_TILE_ADDRESS-LOAD_ADDRESS: raise ValueError("program overlaps assets")
    rom=bytearray([0xEA])*ROM_SIZE
    rom[:len(program)]=program
    for address,data in zip((BG_TILE_ADDRESS,BG_MAP_ADDRESS,PALETTE_ADDRESS),build_assets(),strict=True):
        off=address-LOAD_ADDRESS
        rom[off:off+len(data)]=data
    rom[HEADER:HEADER+21]=b"S64 GATEC 3OVL BOOT".ljust(21,b" ")
    rom[0x7FD5]=0x20; rom[0x7FD6]=0; rom[0x7FD7]=0x05
    rom[0x7FD8]=0; rom[0x7FD9]=0x01; rom[0x7FDA]=0x33; rom[0x7FDB]=0
    write_vector(rom,0x7FEE,IRQ_ADDRESS)
    write_vector(rom,0x7FFE,IRQ_ADDRESS)
    for off in (0x7FE4,0x7FE6,0x7FE8,0x7FEA,0x7FF4,0x7FF6,0x7FF8,0x7FFA,0x7FFC):
        write_vector(rom,off,LOAD_ADDRESS)
    rom[0x7FDC:0x7FE0]=bytes(4)
    checksum=(sum(rom)+0x1FE)&0xFFFF
    rom[0x7FDC:0x7FDE]=(checksum^0xFFFF).to_bytes(2,"little")
    rom[0x7FDE:0x7FE0]=checksum.to_bytes(2,"little")
    return bytes(rom)

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("output",type=Path)
    args=ap.parse_args()
    rom=build_rom()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(rom)
    print(f"wrote {len(rom)} bytes to {args.output}")
    print(f"sha256={hashlib.sha256(rom).hexdigest()}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
