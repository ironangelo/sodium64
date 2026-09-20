#!/usr/bin/env python3
"""Generate original Gate-C H-COMP fixed-color half-add diagnostic SNES ROM.

No commercial data is used. One working BG1 source is combined with SNES fixed
color so the only semantic variable is CGADSUB bit 6 (half).

Mode 1:
- BG1 main only, solid RGB5 (16,0,0).
- no subscreen layers.
- fixed color RGB5 (0,16,0).
- CGWSEL=$00 selects fixed color as the second operand.
- no OBJ, windows, HDMA, or raster IRQ changes.

Two 120-frame phases differ only in CGADSUB:
- $01 full add: (16,0,0)+(0,16,0) => (16,16,0)
- $41 half add: same sum / 2      => (8,8,0)
"""

from __future__ import annotations
import argparse, hashlib
from pathlib import Path

ROM_SIZE=0x8000
HEADER=0x7FC0
LOAD_ADDRESS=0x8000
NMI_ADDRESS=0x8200
NMI_OFFSET=NMI_ADDRESS-LOAD_ADDRESS
TILE_ADDRESS=0x9000
BG_MAP_ADDRESS=0x9040
PALETTE_ADDRESS=0x9840

CONTROL_CGADSUB=0x01
TREATMENT_CGADSUB=0x41
PHASE_FRAMES=120
MAIN_RGB5=(16,0,0)
FIXED_RGB5=(0,16,0)
CONTROL_RGB5=(16,16,0)
TREATMENT_RGB5=(8,8,0)
FIXED_GREEN_COLDATA=0x50  # bit6 selects G; intensity 0x10

class Assembler:
    def __init__(self):
        self.code=bytearray(); self.labels={}; self.rel8_fixups=[]
    def emit(self,*values):
        for v in values:
            if not 0 <= v <= 0xff: raise ValueError(v)
            self.code.append(v)
    def label(self,name):
        if name in self.labels: raise ValueError(name)
        self.labels[name]=len(self.code)
    def branch(self,opcode,label):
        self.emit(opcode,0); self.rel8_fixups.append((len(self.code)-1,label))
    def pad_to(self,offset,value=0xea):
        if len(self.code)>offset: raise ValueError("cannot pad backwards")
        self.code.extend(bytes([value])*(offset-len(self.code)))
    def finish(self):
        for operand,label in self.rel8_fixups:
            if label not in self.labels: raise ValueError(label)
            delta=self.labels[label]-(operand+1)
            if not -128 <= delta <= 127: raise ValueError((label,delta))
            self.code[operand]=delta & 0xff
        return bytes(self.code)

def emit_lda_sta_abs(a,value,address):
    a.emit(0xA9,value,0x8D,address&0xff,(address>>8)&0xff)

def emit_vmadd(a,word_address):
    emit_lda_sta_abs(a,word_address&0xff,0x2116)
    emit_lda_sta_abs(a,(word_address>>8)&0xff,0x2117)

def emit_dma_from_rom(a,*,channel,mode,bbus,source,size):
    base=0x4300+channel*0x10
    for value,address in (
        (mode,base),(bbus,base+1),(source&0xff,base+2),((source>>8)&0xff,base+3),
        (0,base+4),(size&0xff,base+5),((size>>8)&0xff,base+6),
        (1<<channel,0x420B),
    ):
        emit_lda_sta_abs(a,value,address)

def rgb5_word(rgb):
    r,g,b=rgb
    return r | (g<<5) | (b<<10)

def build_program():
    a=Assembler()
    a.emit(0x78,0x18,0xFB,0xD8)  # SEI CLC XCE CLD
    a.emit(0xC2,0x10)             # X/Y 16-bit
    a.emit(0xE2,0x20)             # A 8-bit

    for value,address in (
        (0x80,0x2100), # forced blank
        (0x01,0x2105), # Mode1
        (0x04,0x2107), # BG1 map VRAM $0800
        (0x01,0x210B), # BG1 chars VRAM $1000
        (0x80,0x2115),
    ):
        emit_lda_sta_abs(a,value,address)

    emit_vmadd(a,0x1000)
    emit_dma_from_rom(a,channel=0,mode=1,bbus=0x18,source=TILE_ADDRESS,size=0x20)
    emit_vmadd(a,0x0800)
    emit_dma_from_rom(a,channel=0,mode=1,bbus=0x18,source=BG_MAP_ADDRESS,size=0x800)
    emit_lda_sta_abs(a,0x00,0x2121)
    emit_dma_from_rom(a,channel=0,mode=0,bbus=0x22,source=PALETTE_ADDRESS,size=0x200)

    # Fixed green is independent from CGRAM and is the explicit second operand.
    emit_lda_sta_abs(a,FIXED_GREEN_COLDATA,0x2132)

    for value,address in (
        (0x00,0x2123),(0x00,0x2124),(0x00,0x2125),
        (0x01,0x212C), # TM BG1 main
        (0x00,0x212D), # no subscreen
        (0x00,0x212E),(0x00,0x212F),
        (0x00,0x2130), # fixed color operand
        (CONTROL_CGADSUB,0x2131), # math on BG1
    ):
        emit_lda_sta_abs(a,value,address)

    a.emit(0xA9,0,0x8F,0,0,0x7E)
    a.emit(0xA9,CONTROL_CGADSUB,0x8F,1,0,0x7E)
    emit_lda_sta_abs(a,0x0F,0x2100)
    emit_lda_sta_abs(a,0x80,0x4200)

    a.label("main_loop"); a.emit(0xCB); a.branch(0x80,"main_loop")
    a.pad_to(NMI_OFFSET)
    a.label("nmi")
    a.emit(0x48,0xAD,0x10,0x42)
    a.emit(0xAF,0,0,0x7E,0x1A,0x8F,0,0,0x7E)
    a.emit(0xC9,PHASE_FRAMES); a.branch(0xD0,"check_wrap")
    emit_lda_sta_abs(a,TREATMENT_CGADSUB,0x2131)
    a.emit(0xA9,TREATMENT_CGADSUB,0x8F,1,0,0x7E)
    a.branch(0x80,"nmi_done")
    a.label("check_wrap")
    a.emit(0xC9,PHASE_FRAMES*2); a.branch(0xD0,"nmi_done")
    a.emit(0xA9,0,0x8F,0,0,0x7E)
    emit_lda_sta_abs(a,CONTROL_CGADSUB,0x2131)
    a.emit(0xA9,CONTROL_CGADSUB,0x8F,1,0,0x7E)
    a.label("nmi_done"); a.emit(0x68,0x40)

    program=a.finish()
    if a.labels["nmi"] != NMI_OFFSET: raise ValueError("NMI moved")
    return program

def build_assets():
    tile=bytes([0xFF,0x00]*8+[0x00]*16)
    bg_map=bytes(0x800)
    palette=bytearray(0x200)
    palette[2:4]=rgb5_word(MAIN_RGB5).to_bytes(2,"little")
    return tile,bg_map,bytes(palette)

def write_vector(rom,offset,address):
    rom[offset:offset+2]=address.to_bytes(2,"little")

def build_rom():
    program=build_program()
    if len(program) >= TILE_ADDRESS-LOAD_ADDRESS: raise ValueError("program overlaps assets")
    rom=bytearray([0xEA])*ROM_SIZE
    rom[:len(program)]=program
    for address,data in zip(
        (TILE_ADDRESS,BG_MAP_ADDRESS,PALETTE_ADDRESS),build_assets(),strict=True
    ):
        offset=address-LOAD_ADDRESS
        rom[offset:offset+len(data)]=data

    title=b"S64 GATEC HALF MATH"
    rom[HEADER:HEADER+21]=title.ljust(21,b" ")
    rom[0x7FD5]=0x20; rom[0x7FD6]=0; rom[0x7FD7]=0x05; rom[0x7FD8]=0
    rom[0x7FD9]=0x01; rom[0x7FDA]=0x33; rom[0x7FDB]=0
    write_vector(rom,0x7FE4,0x9000)
    write_vector(rom,0x7FEA,NMI_ADDRESS)
    for off in (0x7FF4,0x7FF6,0x7FF8,0x7FFC,0x7FFE): write_vector(rom,off,LOAD_ADDRESS)
    write_vector(rom,0x7FFA,NMI_ADDRESS)
    rom[0x7FDC:0x7FE0]=bytes(4)
    checksum=(sum(rom)+0x1FE)&0xFFFF
    rom[0x7FDC:0x7FDE]=(checksum^0xFFFF).to_bytes(2,"little")
    rom[0x7FDE:0x7FE0]=checksum.to_bytes(2,"little")
    return bytes(rom)

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("output",type=Path)
    args=p.parse_args(); rom=build_rom()
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_bytes(rom)
    print(f"wrote {len(rom)} bytes to {args.output}")
    print(f"sha256={hashlib.sha256(rom).hexdigest()}")

if __name__=="__main__":
    main()
