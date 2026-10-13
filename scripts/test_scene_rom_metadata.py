#!/usr/bin/env python3
"""Linked Lo/Hi mapper word extraction, without serial or real ROM bytes."""
import argparse,itertools,json
from pathlib import Path
from test_native_diag_continuous import CPU,load_elf,sx32
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('elf',type=Path)
    ap.add_argument('--output',type=Path);a=ap.parse_args();base,s=load_elf(a.elf);cases=0
    for mapper,cart,exp,type_ in itertools.product(('lo','hi'),(0x10104000,0x10200000),(5,9,10,13),(0,1,2,6)):
        cpu=CPU(base.copy());cpu.pattern(cases);cpu.regs[8]=0;cpu.regs[9]=0xffffff;cpu.regs[10]=0x2000
        cpu.regs[13]=(0x01<<24)|((0x20 if mapper=='lo' else 0x21)<<16)|(type_<<8)|exp
        cpu.regs[24]=sx32(cart)
        cpu.write(cart+(0x7fd8 if mapper=='lo' else 0xffd8),0x03000000)
        assert cpu.execute(s['scene_rom_'+('lomap' if mapper=='lo' else 'himap')+'_metadata'],stop=s['build_'+('lomap' if mapper=='lo' else 'himap')])=='return'
        assert cpu.read(s['scene_rom_cart'])==cart and cpu.read(s['scene_rom_bytes'])==1<<(exp+10)
        assert cpu.read(s['scene_rom_exp'])==exp and cpu.read(s['scene_rom_type'])==type_
        assert cpu.read(s['native_diag_guest_sram_exp'])==3
        assert cpu.regs[8]==0 and cpu.regs[9]==0xffffff and cpu.regs[24]&0xffffffff==cart
        assert not cpu.cp_writes;cases+=1
    result=dict(passed=True,cases=cases,actual_linked_mapper=True,aligned_word_metadata_extraction=True,
        mapper_address_bounds_and_SRAM_unchanged=True,PI_byte_semantics_mocked=True,native_acceptance=False)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
