#!/usr/bin/env python3
"""Resolve explicit linked guest owners. No private machine bytes are read."""
import argparse,json
from pathlib import Path
from native_diag_report import elf_symbols
from check_runtime_arena import allocated_sections

def owners(elf):
    symbols={name:address for address,name in elf_symbols(elf)}
    limit=0x800d6000 if 'scene_slot_tlb_save' in symbols else 0x800d4000
    result=[]
    for name,start in symbols.items():
        if not name.startswith('scene_owner_') or not name.endswith('_begin'):continue
        owner=name[len('scene_owner_'):-len('_begin')];end=symbols[name[:-len('_begin')]+'_end']
        assert 0x80000000<=start<end<=limit,(owner,'invalid linked owner')
        result.append(dict(name=owner,start=start,end=end,bytes=end-start))
    result.sort(key=lambda x:x['start'])
    assert len(result)<=32
    for a,b in zip(result,result[1:]):assert a['end']<=b['start'],('owner overlap',a,b)
    expected=dict(cpu_regs=12,apu_memory=66560,apu_jit=266760,dma=144,
                  dsp_pcm=8192,dsp_regs=128,dsp_pitches=128,dsp_noise=10,dsp_voices=192,
                  input=11,presentation=10,sram_guest8=8192,wram=131072,mapper=10240,
                  memory_io=7,cpu_arithmetic_io=7,ppu_cursors=12,ppu_epochs=6)
    by_name={x['name']:x for x in result}
    for name,bytes_ in expected.items():assert by_name[name]['bytes']==bytes_,(name,by_name.get(name))
    assert set(by_name)-set(expected)=={'apu_regs','ppu','dsp1'} or set(by_name)-set(expected)=={'apu_regs','ppu','dsp1','ppu_main_cursor','ppu_main_candidate'}
    exclusions=['joybus_cmd','native_diag_snapshot','remote_bridge_stack','remote_bridge_saved',
                'dsp_audio_blocks','dsp_audio_last_count','jit_opcodes','opcodes_e','pal_queues',
                'hcomp_row_fixed_queues','filter_jumps','timer_rates','dsp1_cmds','data_rom']
    # Some stack/local names are present only in the debug ELF; each resolved
    # exclusion must stay outside every saved interval, regardless of symbol type.
    for name in exclusions:
        if name in symbols:assert not any(x['start']<=symbols[name]<x['end'] for x in result),(name,'included host/immutable owner')
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('elf',type=Path)
    ap.add_argument('--baseline',type=Path);ap.add_argument('--output',type=Path)
    a=ap.parse_args();ranges=owners(a.elf)
    proof=dict(passed=True,explicit_linked_owners=ranges,owner_count=len(ranges),
               static_guest_bytes=sum(x['bytes'] for x in ranges),
               host_stacks_transport_observer_and_immutable_tables_excluded=True,
               complete_machine_state=False,native_restore=False)
    if a.baseline:
        from test_hcomp_sub_presence import section
        assert all(section(a.elf,n)==section(a.baseline,n) for n in ('.text','.data'))
        assert list(allocated_sections(a.elf))==list(allocated_sections(a.baseline))
        proof['CPU_text_data_allocated_extents_byte_exact_baseline']=True
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='explicit_linked_owners'}))
if __name__=='__main__':main()
