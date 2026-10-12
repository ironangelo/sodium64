#!/usr/bin/env python3
"""Execute aligned resident-island swaps without overwriting running code."""
import argparse
import json
import struct
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from test_hcomp_sub_presence import section
from test_hcomp_tlut_candidate import ShaderVM
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_rsp_math_dma import ROOT, put, symbols
from test_native_diag_arm import load_elf,execute as cpu_execute

ORIGINAL, MAIN, PHASE, SETUP = 0x180000,0x181000,0x182000,0x183000


class AdaptiveVM(ShaderVM):
    def queue_dma(self,write,length):
        island=not write and (self.spaddr&0x1fff)==0x1ad0
        if island:
            assert length==183, 'resident island DMA extent'
            assert not 0xad0<=self.pc<0xb88, 'executing resident island overwrite'
            saved=self.signal_profile;self.signal_profile=False
            try:super().queue_dma(write,length)
            finally:self.signal_profile=saved
            self.dma['island']=True
        else:super().queue_dma(write,length)
    def poll_dma(self):
        if not self.dma or not self.dma.get('island'):return super().poll_dma()
        self.dma['polls']-=1
        if self.dma['polls']:return 1
        p=self.dma;assert p['sp']==0xad0 and p['size']==184
        self.code[p['sp']:p['sp']+p['size']]=self.ram[p['ram']:p['ram']+p['size']]
        self.transfers.append({k:v for k,v in p.items() if k!='polls'});self.dma=None
        return 0


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('build',type=Path)
    p.add_argument('--baseline',type=Path,required=True);args=p.parse_args()
    a=parse_macros(ROOT).name
    _,original=read_text(args.build/'src/rsp_decoder_original.elf')
    _,old=read_text(args.baseline/'src/rsp_main.elf')
    _,new=read_text(args.build/'src/rsp_main.elf')
    _,phase=read_text(args.build/'src/rsp_hcomp.elf')
    _,setup=read_text(args.build/'src/rsp_hcomp_setup.elf')
    assert original==old[0xad0:0xb88] and len(original)==184
    ps=symbols(args.build/'src/rsp_hcomp.elf');ss=symbols(args.build/'src/rsp_hcomp_setup.elf')
    assert ps['hcomp_context_ready']+0x1000==a('RSP_CONTEXT_PHASE_RETURN')
    assert ss['hcomp_setup_copy']+0x1000==a('RSP_CONTEXT_SWITCH_ENTRY')
    image,cs=load_elf(args.build/'sodium64-adaptive-r40.elf');before=image.copy()
    cpu_execute(image,cs['adaptive_decoder_cpu_bind'],[0]*32,{},cs['adaptive_decoder_cpu_bind_end'])
    field=(0xa4000000+a('OVERLAY_DECODER_ORIGINAL_SRC'))&0x1fffffff
    actual=int.from_bytes(bytes(image[field+i] for i in range(4)),'big')
    assert actual==cs['rsp_decoder_original_text_start']|1
    assert all(image[k]==v for k,v in before.items() if not field<=k<field+4)
    def run_case(current,effective,delay,setup_image=setup):
       wanted=int(bool(effective));d=bytearray(section(args.build/'src/rsp_main.elf','.data'))
       d[a('HCOMP_EFFECTIVE_TS')]=effective
       put(d,a('OVERLAY_DECODER_ORIGINAL_SRC'),ORIGINAL|current)
       put(d,a('OVERLAY_MAIN_SRC'),(MAIN+0x3a8)|1)
       put(d,a('OVERLAY_HCOMP_SRC'),PHASE|3);put(d,a('OVERLAY_HCOMP_SETUP_SRC'),SETUP|7)
       for index,address in enumerate((0x1b3c,0x1b20,0x1ae8)):
           put(d,a('SHARED_JUMPS')+index*4,0xa4000000+address-(0x52c if current else 0))
       code=bytearray(new);code[0xad0:0xb88]=new[0xad0:0xb88] if current else original
       code[0x3a8:0x790]=phase
       ram=bytearray([0xa5])*0x400000;ram[ORIGINAL:ORIGINAL+184]=original
       ram[MAIN:MAIN+4096]=new;ram[PHASE:PHASE+1000]=phase;ram[SETUP:SETUP+1000]=setup_image
       initial_ram=bytes(ram);r=[0]*32
       owners=set(range(a('SHARED_JUMPS'),a('SHARED_JUMPS')+12))
       owners.update(range(a('OVERLAY_DECODER_ORIGINAL_SRC'),a('OVERLAY_DECODER_ORIGINAL_SRC')+4))
       owners.update(range(a('NATIVE_DIAG_RSP_BANK'),a('NATIVE_DIAG_RSP_BANK')+2))
       vm=AdaptiveVM(code,d,ram,r,owners,set(),delay,overlays={PHASE:3,SETUP:7})
       vm.pc=ps['hcomp_band_start'];vm.execute(ps['hcomp_context_ready'])
       assert bytes(vm.code[0xad0:0xb88])==(new[0xad0:0xb88] if wanted else original), 'resident island image mismatch'
       assert struct.unpack_from('>I',d,a('OVERLAY_DECODER_ORIGINAL_SRC'))[0]==ORIGINAL|wanted
       expected=tuple(0xa4000000+x-(0x52c if wanted else 0) for x in (0x1b3c,0x1b20,0x1ae8))
       assert struct.unpack_from('>3I',d,a('SHARED_JUMPS'))==expected, 'decoder jump table mismatch'
       assert vm.overlay_history==([7,3] if wanted!=current else [])
       islands=[x for x in vm.transfers if x.get('island')]
       assert len(islands)==int(wanted!=current)
       assert vm.ram==initial_ram and not vm.captures
       assert vm.code[:0x3a8]==code[:0x3a8] and vm.code[0x790:0xad0]==code[0x790:0xad0] and vm.code[0xb88:]==code[0xb88:]
       return vm
    cases=0
    for current in (0,1):
     for effective in (0,1,2,16,31):
      for delay in (1,9,31):
       run_case(current,effective,delay);cases+=1
    def mutate_immediate(match,replacement):
        image=bytearray(setup)
        offsets=[i for i in range(0,len(image),4) if match(struct.unpack_from('>I',image,i)[0])]
        assert len(offsets)==1, ('unique emitted operand',offsets)
        off=offsets[0];word=struct.unpack_from('>I',image,off)[0]
        struct.pack_into('>I',image,off,(word&0xffff0000)|replacement)
        return bytes(image)
    mutants=[
        ('length',mutate_immediate(lambda w:w>>26 in (8,9) and (w>>16)&31==6 and (w>>21)&31==0 and w&0xffff==183,191),'resident island DMA extent'),
        ('jump spacing',mutate_immediate(lambda w:w>>26==12 and w&0xffff==0x52c,0x32c),'decoder jump table mismatch'),
    ]
    caught=[]
    for name,image,reason in mutants:
        try:run_case(0,1,9,image)
        except AssertionError as error:
            assert str(error)==reason,(name,str(error));caught.append(name)
        else:raise AssertionError('accepted unsafe '+name)
    vm=run_case(0,0,9);vm.spaddr=0x1ad0;vm.pc=0xad0
    try:vm.queue_dma(False,183)
    except AssertionError as error:
        assert str(error)=='executing resident island overwrite';caught.append('executing island')
    else:raise AssertionError('accepted executing island overwrite')
    print(json.dumps({'passed':True,'island_and_table_cases':cases,'original_code_byte_exact':184,
                      'immutable_boundaries_and_CPU_binding':True,'unsafe_mutations_rejected':caught,'native_gain_claim':False}))

if __name__=='__main__':main()
