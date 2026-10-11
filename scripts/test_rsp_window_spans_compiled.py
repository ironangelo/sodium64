#!/usr/bin/env python3
"""Execute both current resident window helpers against independent pixel truth."""
import argparse,importlib.util,json,struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('window_vm',ROOT/'docs/gate-c-a3/test_hcomp_direct_backdrop.py')
vm=importlib.util.module_from_spec(spec);spec.loader.exec_module(vm)

def selected(x,selector,logic,bounds):
    left,right,left2,right2=bounds
    first=(left<=x<=right)^bool(selector&1)
    second=(left2<=x<=right2)^bool(selector&4)
    one=bool(selector&2);two=bool(selector&8)
    if one and two:return (first or second,first and second,first!=second,first==second)[logic]
    return first if one else (second if two else False)

def check_case(code,data,entry,selector,logic,bounds,wanted):
    memory=bytearray(data);memory[0xbae:0xbb2]=bytes(bounds)
    before=bytes(memory)
    registers=[0x13570000+i*37 for i in range(32)]
    registers[0]=0;registers[4:7]=[selector,logic,wanted];registers[31]=0xff8
    initial=registers.copy()
    assert vm.run(code,memory,entry,registers,stop=0xff8)==[]
    count=memory[0xe8a];assert count<=3
    seen=set()
    for index in range(count):
        low,high=memory[0xe84+index*2:0xe86+index*2]
        assert low<=high
        points=set(range(low,high+1));assert not seen&points
        seen|=points
    expected={x for x in range(256) if selected(x,selector,logic,bounds)==bool(wanted)}
    assert seen==expected,(selector,logic,bounds,wanted,seen^expected)
    assert all(memory[i]==before[i] for i in range(4096) if not 0xe84<=i<=0xe8a)
    assert all(registers[i]==initial[i] for i in range(32) if i not in (8,9,10,11,12,14,15,24))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elves',nargs=2,type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args();cases=0;mutations=0;helpers=[]
    bounds=((0,255,0,255),(32,95,64,191),(255,255,0,0),
            (200,100,250,2),(0,0,255,255),(80,80,80,80),(2,254,3,253))
    for elf in args.elves:
        _,code=read_text(elf);assert len(code)==4096
        data=vm.section(elf,'.data');assert len(data)==4096
        symbols={name:value&0xfff for value,name in elf_symbols(elf)}
        entry=symbols['calc_window_spans'];end=symbols['multiply']
        helpers.append(code[entry:end])
        for selector in range(16):
            for logic in range(4):
                for limits in bounds:
                    for wanted in (0,1):
                        check_case(code,data,entry,selector,logic,limits,wanted);cases+=1
        candidates=[pc for pc in range(entry,end,4) if (vm.word(code,pc)>>26)==14
                    and (vm.word(code,pc)>>21&31)==6 and (vm.word(code,pc)&65535)==1]
        assert len(candidates)==1
        changed=bytearray(code);pc=candidates[0]
        struct.pack_into('>I',changed,pc,vm.word(changed,pc)^1)
        try:check_case(changed,data,entry,2,0,(32,95,64,191),1)
        except AssertionError:mutations+=1
        else:raise AssertionError('selector complement mutation escaped pixel oracle')
    assert helpers[0]==helpers[1],'resident helper instructions differ'
    proof={'passed':True,'compiled_cases':cases,'negative_mutations_rejected':mutations,
           'both_rsp_banks':True,'pixel_truth_width':256,'preserved_registers_and_memory':True,
           'physical_acceptance':False}
    if args.output:args.output.write_text(json.dumps(proof,indent=2)+'\n')
    print('RSP_WINDOW_SPANS_COMPILED PASS '+json.dumps(proof))

if __name__=='__main__':main()
