#!/usr/bin/env python3
"""Directed real-JIT data-bus order against pinned SPC700 microsequences."""
import argparse,hashlib,json
from pathlib import Path
from test_native_diag_arm import load_elf
from test_spc_bus_clock import run

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--require-exact',action='store_true')
    a=p.parse_args();base,s=load_elf(a.elf)
    cases=[
      ('absolute_read','e5f3002ffb',8,[('read',0xf3,4)],()),
      ('absolute_write','c5f3002ffb',9,[('read',0xf3,4),('write',0xf3,5)],()),
      ('direct_X_read','f4ef2ffc',8,[('read',0xf3,4)],()),
      ('direct_X_write','d4ef2ffc',9,[('read',0xf3,4),('write',0xf3,5)],()),
      ('absolute_X_read','f5ef002ffb',9,[('read',0xf3,5)],()),
      ('absolute_X_write','d5ef002ffb',10,[('read',0xf3,5),('write',0xf3,6)],()),
      ('absolute_Y_read','f6ed002ffb',9,[('read',0xf3,5)],()),
      ('absolute_Y_write','d6ed002ffb',10,[('read',0xf3,5),('write',0xf3,6)],()),
      ('indexed_indirect_read','e71c2ffc',10,[('read',0x20,4),('read',0x21,5),('read',0xf3,6)],((0x20,0xf3),(0x21,0))),
      ('indexed_indirect_write','c71c2ffc',11,[('read',0x20,4),('read',0x21,5),('read',0xf3,6),('write',0xf3,7)],((0x20,0xf3),(0x21,0))),
      ('indirect_indexed_read','f7202ffc',10,[('read',0x20,4),('read',0x21,5),('read',0xf3,6)],((0x20,0xed),(0x21,0))),
      ('indirect_indexed_write','d7202ffc',11,[('read',0x20,3),('read',0x21,4),('read',0xf3,6),('write',0xf3,7)],((0x20,0xed),(0x21,0))),
      ('direct_direct_write','fa20f32ffb',9,[('read',0x20,3),('write',0xf3,5)],((0x20,0x33),)),
      ('direct_Y_read','f9ed2ffc',8,[('read',0xf3,4)],()),
      ('direct_Y_write','d9ed2ffc',9,[('read',0xf3,4),('write',0xf3,5)],()),
      ('direct_modify','abf32ffc',8,[('read',0xf3,3),('write',0xf3,4)],()),
      ('absolute_modify','acf3002ffb',9,[('read',0xf3,4),('write',0xf3,5)],()),
      ('direct_indexed_modify','bbef2ffc',9,[('read',0xf3,4),('write',0xf3,5)],()),
      ('direct_direct_modify','0920f32ffb',10,[('read',0x20,3),('read',0xf3,5),('write',0xf3,6)],((0x20,0x33),)),
      ('direct_immediate_modify','1801f32ffb',9,[('read',0xf3,4),('write',0xf3,5)],()),
      ('direct_word_read','baf32ffc',9,[('read',0xf3,3),('read',0xf4,5)],()),
      ('direct_word_write','daf32ffc',9,[('read',0xf3,3),('write',0xf3,4),('write',0xf4,5)],()),
    ]
    wraps=[
      ('indexed_indirect_DP1_wrap','e7fb2ffc',10,[('read',0x1ff,4),('read',0x100,5),('read',0xf3,6)],((0x1ff,0xf3),(0x100,0))),
      ('indirect_indexed_DP1_wrap','f7ff2ffc',10,[('read',0x1ff,4),('read',0x100,5),('read',0xf3,6)],((0x1ff,0xed),(0x100,0))),
      ('indirect_indexed_write_DP1_wrap','d7ff2ffc',11,[('read',0x1ff,3),('read',0x100,4),('read',0xf3,6),('write',0xf3,7)],((0x1ff,0xed),(0x100,0))),
    ]
    results=[]
    for name,code,total,expected,memory in cases+wraps:
        r=run(base,s,bytes.fromhex(code),observe_data=True,memory_values=memory,flags=0x20 if 'DP1_wrap' in name else 0)
        observed=[(v['kind'],v['address'],v['elapsed_master_cycles']//21)for v in r['events']]
        exact=observed==expected and r['total_cycles']==total
        item=dict(name=name,observed=observed,expected=expected,total=r['total_cycles'],expected_total=total,exact=exact)
        results.append(item);print(name+(' EXACT 'if exact else ' OPEN ')+json.dumps(item))
        if a.require_exact:assert exact,item
    proof=dict(passed=all(x['exact']for x in results),status='directed data bus audit',cases=results,
        ELF_sha256=hashlib.sha256(a.elf.read_bytes()).hexdigest(),
        primary_reference='https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/component/processor/spc700/instructions.cpp',
        exact=sum(x['exact']for x in results),open=sum(not x['exact']for x in results),
        actual_linked_JIT_and_cached_replay=True,full_256_opcode_bus_accuracy_proved=False,
        native_performance_claim=False,commercial_data=False)
    print('SPC_BUS_ADDRESS cases='+str(len(results))+' exact='+str(proof['exact'])+' open='+str(proof['open']))
    if a.output:a.output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
