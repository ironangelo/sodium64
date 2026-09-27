#!/usr/bin/env python3
"""Deterministic boot-first Mode1 -> short Mode7 -> Mode1 proof guest."""
from __future__ import annotations
import argparse,hashlib
from pathlib import Path

ROM_SIZE=0x8000; HEADER=0x7FC0; LOAD_ADDRESS=0x8000
IRQ_ADDRESS=0x8300; IRQ_OFFSET=IRQ_ADDRESS-LOAD_ADDRESS
BG_TILE_ADDRESS=0x9000; BG_MAP_ADDRESS=0x9040; PALETTE_ADDRESS=0x9840
CONTROL_MODE=0x01; TREATMENT_MODE=0x07
ARMED_PHASE=0x11; POSTTEST_PHASE=0x33
IRQ1_LINE=80; IRQ2_LINE=82

class Assembler:
    def __init__(self): self.code=bytearray(); self.labels={}; self.fix=[]
    def emit(self,*vs):
        for v in vs:
            if not 0<=v<=255: raise ValueError(v)
            self.code.append(v)
    def label(self,n):
        if n in self.labels: raise ValueError(n)
        self.labels[n]=len(self.code)
    def branch(self,op,n): self.emit(op,0); self.fix.append((len(self.code)-1,n))
    def pad_to(self,o):
        if len(self.code)>o: raise ValueError("pad backwards")
        self.code.extend([0xEA]*(o-len(self.code)))
    def finish(self):
        for i,n in self.fix:
            d=self.labels[n]-(i+1)
            if not -128<=d<=127: raise ValueError((n,d))
            self.code[i]=d&255
        return bytes(self.code)

def sta_abs(a,v,addr): a.emit(0xA9,v,0x8D,addr&255,(addr>>8)&255)
def vmadd(a,w): sta_abs(a,w&255,0x2116); sta_abs(a,(w>>8)&255,0x2117)
def dma(a,ch,mode,bbus,src,size):
    base=0x4300+ch*0x10
    for v,addr in ((mode,base),(bbus,base+1),(src&255,base+2),((src>>8)&255,base+3),
                   (0,base+4),(size&255,base+5),((size>>8)&255,base+6),(1<<ch,0x420B)):
        sta_abs(a,v,addr)
def sta_long_imm(a,v,addr): a.emit(0xA9,v,0x8F,addr&255,(addr>>8)&255,(addr>>16)&255)
def lda_long(a,addr): a.emit(0xAF,addr&255,(addr>>8)&255,(addr>>16)&255)
def sta_long(a,addr): a.emit(0x8F,addr&255,(addr>>8)&255,(addr>>16)&255)
def vector(rom,off,addr): rom[off:off+2]=addr.to_bytes(2,"little")

def program():
    a=Assembler(); a.emit(0x78,0x18,0xFB,0xD8,0xC2,0x10,0xE2,0x20)
    for v,addr in ((0x80,0x2100),(CONTROL_MODE,0x2105),(0x04,0x2107),(0x01,0x210B),(0x80,0x2115)): sta_abs(a,v,addr)
    vmadd(a,0x1000); dma(a,0,1,0x18,BG_TILE_ADDRESS,0x20)
    vmadd(a,0x0800); dma(a,0,1,0x18,BG_MAP_ADDRESS,0x800)
    sta_abs(a,0,0x2121); dma(a,0,0,0x22,PALETTE_ADDRESS,0x200)
    for v,addr in ((1,0x212C),(0,0x212D),(0,0x212E),(0,0x212F),(0,0x2130),(0,0x2131)): sta_abs(a,v,addr)
    for addr in range(0x7E0000,0x7E0007): sta_long_imm(a,0,addr)
    sta_long_imm(a,ARMED_PHASE,0x7E0001); sta_long_imm(a,CONTROL_MODE,0x7E0003)
    sta_abs(a,IRQ1_LINE&255,0x4209); sta_abs(a,(IRQ1_LINE>>8)&1,0x420A)
    sta_abs(a,0x20,0x4200); sta_abs(a,0x0F,0x2100); a.emit(0x58)
    a.label("loop"); a.emit(0xCB); a.branch(0x80,"loop")
    a.pad_to(IRQ_OFFSET); a.label("irq"); a.emit(0x48,0xAD,0x11,0x42)
    lda_long(a,0x7E0002); a.emit(0x1A); sta_long(a,0x7E0002); a.emit(0xC9,1); a.branch(0xD0,"second")
    lda_long(a,0x7E0000); sta_long(a,0x7E0005)
    sta_abs(a,TREATMENT_MODE,0x2105); sta_long_imm(a,TREATMENT_MODE,0x7E0003)
    sta_abs(a,IRQ2_LINE&255,0x4209); sta_abs(a,(IRQ2_LINE>>8)&1,0x420A); a.branch(0x80,"done")
    a.label("second"); a.emit(0xC9,2); a.branch(0xD0,"done")
    lda_long(a,0x7E0000); sta_long(a,0x7E0006)
    sta_abs(a,CONTROL_MODE,0x2105); sta_long_imm(a,CONTROL_MODE,0x7E0003)
    sta_abs(a,0,0x4200); sta_long_imm(a,POSTTEST_PHASE,0x7E0001); sta_long_imm(a,1,0x7E0004)
    a.label("done"); a.emit(0x68,0x40)
    p=a.finish()
    if a.labels["irq"]!=IRQ_OFFSET: raise ValueError("IRQ moved")
    return p

def build_rom():
    p=program(); rom=bytearray([0xEA])*ROM_SIZE; rom[:len(p)]=p
    tile=bytes([0xFF,0]*8+[0]*16); bg=bytes(0x800); pal=bytearray(0x200); pal[2:4]=(0x03E0).to_bytes(2,"little")
    for addr,data in ((BG_TILE_ADDRESS,tile),(BG_MAP_ADDRESS,bg),(PALETTE_ADDRESS,pal)):
        off=addr-LOAD_ADDRESS; rom[off:off+len(data)]=data
    rom[HEADER:HEADER+21]=b"S64 GATEC 3OVL SHORT".ljust(21,b" ")
    rom[0x7FD5]=0x20; rom[0x7FD6]=0; rom[0x7FD7]=5; rom[0x7FD8]=0; rom[0x7FD9]=1; rom[0x7FDA]=0x33; rom[0x7FDB]=0
    vector(rom,0x7FEE,IRQ_ADDRESS); vector(rom,0x7FFE,IRQ_ADDRESS)
    for off in (0x7FE4,0x7FE6,0x7FE8,0x7FEA,0x7FF4,0x7FF6,0x7FF8,0x7FFA,0x7FFC): vector(rom,off,LOAD_ADDRESS)
    rom[0x7FDC:0x7FE0]=bytes(4); cs=(sum(rom)+0x1FE)&0xFFFF
    rom[0x7FDC:0x7FDE]=(cs^0xFFFF).to_bytes(2,"little"); rom[0x7FDE:0x7FE0]=cs.to_bytes(2,"little")
    return bytes(rom)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("output",type=Path); a=ap.parse_args()
    data=build_rom(); a.output.write_bytes(data)
    print(f"wrote {len(data)} bytes"); print("sha256="+hashlib.sha256(data).hexdigest())
if __name__=="__main__": main()
