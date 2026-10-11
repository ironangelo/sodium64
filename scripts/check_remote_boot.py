#!/usr/bin/env python3
"""Audit actual linked reboot instructions; no USB or physical boot claim."""
import argparse,hashlib,json,struct
from pathlib import Path
from test_native_diag_continuous import CPU,load_elf

def elf(path):
    data=Path(path).read_bytes()
    assert data[:6]==b'\x7fELF\x01\x02','expected ELF32 big-endian'
    h=struct.unpack_from('>HHIIIIIHHHHHH',data,16)
    sections=[struct.unpack_from('>IIIIIIIIII',data,h[5]+i*h[10]) for i in range(h[11])]
    symbols={}
    for section in sections:
        if section[1]!=2:continue
        strings=sections[section[6]];names=data[strings[4]:strings[4]+strings[5]]
        for offset in range(section[4],section[4]+section[5],section[9]):
            name,value,size,info,other,index=struct.unpack_from('>IIIBBH',data,offset)
            if name:
                text=names[name:names.find(b'\0',name)].decode('ascii')
                symbols[text]=value
    def word(address):
        for section in sections:
            if section[1]!=8 and section[3]<=address< section[3]+section[5]:
                return struct.unpack_from('>I',data,section[4]+address-section[3])[0]
        raise AssertionError(f'no loaded instruction at {address:#x}')
    return symbols,word

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--elf',required=True,type=Path)
    p.add_argument('--json-output',type=Path);a=p.parse_args()
    s,word=elf(a.elf);start=s['remote_reboot_start'];end=s['remote_reboot_end'];entry=s['remote_reboot_entry']
    assert 0<end-start<0x1000 and (end-start)%4==0
    target=0xa4001000+entry-start
    cases=0
    # Execute the actual entry capture before any RSP upload. Legacy low-RAM
    # TV and incoming s4 deliberately disagree with modern IPL3's DMEM byte9.
    # 0xff also catches a signed-byte load wrapping past the invalid-value gate.
    assert all(name in s for name in ('_start','remote_boot_tv_captured','remote_boot_tv_type'))
    base,_=load_elf(a.elf)
    tv_capture_cases=0
    for tv in (0,1,2,3,255):
        cpu=CPU(base.copy());cpu.pattern()
        cpu.cp[12]=0x9403
        cpu.memory[0x04000009]=tv
        cpu.write(0xa0000300,(tv+1)%3)
        cpu.regs[20]=(tv+1)%3
        cpu.memory_writes.clear();cpu.cp_writes.clear()
        cpu.execute(s['_start'],stop=s['remote_boot_tv_captured'],max_steps=50)
        expected=tv if tv<3 else 1
        assert cpu.read(s['remote_boot_tv_type'])==expected,('bad captured TV',tv,expected)
        assert cpu.memory_writes==[(s['remote_boot_tv_type']&0x1fffffff,4,expected)]
        assert cpu.cp_writes==[(12,0)],'TV capture must run before IRQs/RSP initialization'
        assert cpu.memory[0x04000009]==tv and cpu.regs[20]==(tv+1)%3
        tv_capture_cases+=1;cases+=1
    # Execute the linked entry for all supported TV types. This catches GNU as
    # truncating a symbolic li to its low immediate, before touching hardware.
    for tv,version in [(0,6),(1,1),(2,4)]:
        reg=[0]*32;reg[4]=tv;pc=s['remote_reboot_jump'];pending=None
        for _ in range(80):
            insn=word(pc);op=insn>>26;rs=(insn>>21)&31;rt=(insn>>16)&31;rd=(insn>>11)&31;imm=insn&65535
            signed=imm if imm<32768 else imm-65536;dest=None
            if op==15:reg[rt]=(imm<<16)&0xffffffff
            elif op==13:reg[rt]=reg[rs]|imm
            elif op==9:reg[rt]=(reg[rs]+signed)&0xffffffff
            elif op==4:
                if reg[rs]==reg[rt]:dest=(pc+4+signed*4)&0xffffffff
            elif op==0:
                fn=insn&63
                if fn==37:reg[rd]=reg[rs]|reg[rt]
                elif fn==8:
                    assert reg[rs]==target,(hex(reg[rs]),hex(target),'bad IMEM reboot jump')
                    break
                else:assert insn==0,hex(insn)
            else:assert op in (16,17),hex(insn) # CP0/FCSR boot initialization
            reg[0]=0;old=pending;pending=dest;pc=old if old is not None else pc+4
        else:raise AssertionError('boot entry did not reach IMEM')
        assert (reg[19],reg[20],reg[21],reg[22],reg[23])==(0,tv,0,63,version)
        cases+=1
    # The complete relocated receiver has no J/JAL or program-relative
    # external branches. Its only indirect jump loads fixed IPL3 hardware PC.
    jumps=0
    for pc in range(start,end,4):
        insn=word(pc);op=insn>>26
        assert op not in (2,3),'receiver depends on old absolute code address'
        if op in (4,5,6,7,20,21,22,23):
            imm=insn&65535;imm=imm if imm<32768 else imm-65536
            destination=pc+4+imm*4
            assert start<=destination<end,(hex(pc),hex(destination),'branch outside immutable receiver')
            cases+=1
        if op==0 and (insn&63)==8:
            assert ((insn>>21)&31)==11
            assert word(pc-8)==0x3c0ba400 and word(pc-4)==0x356b0040
            jumps+=1
    assert jumps==1
    proof=dict(passed=True,cases=cases,linked_instructions=True,receiver_bytes=end-start,
               elf_sha256=hashlib.sha256(a.elf.read_bytes()).hexdigest(),
               compiled_tv_capture_cases=tv_capture_cases,modern_ipl3_dmem_tv_source=True,
               legacy_low_ram_tv_ignored=True,invalid_tv_unsigned_byte_falls_back_ntsc=True,
               receiver_pc=f'{target:08x}',ipl3_pc='a4000040',external_code_references_after_jump=False,
               physical_acceptance=False)
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(f'REMOTE_BOOT_LINKED PASS cases={cases} tv_capture_cases={tv_capture_cases} receiver_bytes={end-start} pc={target:08x} no_external_receiver_refs=1')
if __name__=='__main__':main()
