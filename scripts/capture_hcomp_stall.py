#!/usr/bin/env python3
"""Read-only interrupted-state diagnosis; never a frame/cadence acceptance."""
import argparse,json,socket
from pathlib import Path
from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS,connect_with_retry,validate_stop
from capture_gate_c_stage1_ares import read_engine_state
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--port',type=int,required=True);ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
c=connect_with_retry('127.0.0.1',a.port,30,30)
try:
 c.sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
 c.request('qSupported:multiprocess+;swbreak+;hwbreak+');c.request('?')
 assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS)==b'OK'
 rows=[]
 for i in range(3):
  validate_stop(c.continue_then_interrupt(2.0),'stall diagnosis interrupt')
  for name,addr,size in [('dmem',0xa4000000,4096),('imem',0xa4001000,4096),('owner',0xa00f0000,64)]:
   (a.output/f'{name}-{i}.bin').write_bytes(c.read_memory(addr,size,0x400))
  (a.output/f'cpu-{i}.txt').write_text(c.request('g').decode()+'\n')
  rows.append(dict(index=i,sp_pc=hex(int.from_bytes(c.read_memory(0xa4080000,4,4),'big')),**read_engine_state(c),acceptance_authority=False))
  (a.output/'states.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps(rows),flush=True)
finally:c.close()
