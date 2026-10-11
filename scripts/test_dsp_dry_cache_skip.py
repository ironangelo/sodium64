#!/usr/bin/env python3
"""Paired actual DSP/APU execution: unused cache removal must preserve PCM/state."""
from pathlib import Path
import sys,json,hashlib,argparse
repo=Path(__file__).resolve().parents[1]
from test_native_diag_arm import load_elf
from test_native_diag_continuous import CPU
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('elf',type=Path);parser.add_argument('--reference-elf',type=Path,required=True);parser.add_argument('--json-output',type=Path);args=parser.parse_args();paths=[args.reference_elf,args.elf]
models=[]
for p in paths:
 m,s=load_elf(p);models.append((CPU(m),s))
def put(c,s,name,value,size=4,offset=0):c.write(s[name]+offset,value,size)
def state(c,s):
 return {'regs':c.blob(s['dsp_regs'],128),'enabled':c.read(s['enabled'],1),'timer':c.read(s['dsp_timer'],2),'pointer':c.read(s['dsp_pointer'],2),'env':[c.read(s['envelopes']+16*i,2) for i in range(8)],'next':[c.read(s['next_steps']+16*i,2) for i in range(8)],'counter':[c.read(s['counters']+16*i,2) for i in range(8)]}
samples=0;writes=0
for seed in range(16):
 for c,s in models:
  put(c,s,'enabled',255,1);put(c,s,'audio_set',4,1);put(c,s,'dsp_timer',0,2);put(c,s,'dsp_pointer',0,2);put(c,s,'noise_step',65535,2)
  put(c,s,'dsp_regs',0,1,61);put(c,s,'dsp_regs',96,1,12);put(c,s,'dsp_regs',96,1,28);put(c,s,'dsp_regs',0,1,108)
  for voice in range(8):
   put(c,s,'envelopes',(seed*127+voice*233)&2047,2,16*voice);put(c,s,'next_steps',0x77ff,2,16*voice)
   put(c,s,'mode_funcs',s['release_mode'],4,16*voice);put(c,s,'counters',0,2,16*voice);put(c,s,'dsp_pitches',0,2,16*voice)
   put(c,s,'cached_vols',0x12345678,4,16*voice)
   for index in range(4):put(c,s,'cur_samples',((seed*1103+voice*1777)&32767)-16384,2,8*voice+2*index)
 for step in range(128):
  if step%16==0:
   for voice in range(8):
    for channel in (0,1):
     raw=(seed*31+step*7+voice*43+channel*17)&255
     for c,s in models:
      put(c,s,'dsp_addr',16*voice+channel,1);put(c,s,'apu_clock',21,1);put(c,s,'jit_tags',0x12345678,4,12)
      c.pattern();c.regs[4]=0xf3;c.regs[5]=raw;c.regs[19]=1000;c.execute(s['apu_write8'])
      assert c.regs[19]==979 and c.read(s['jit_tags']+12)==0x12345679
      assert c.read(s['apu_ram']+0xf3,1)==raw
     writes+=1
  for c,s in models:c.pattern();c.execute(s['dsp_sample'],stop=s['apu_execute'])
  a,sa=models[0];b,sb=models[1];assert state(a,sa)==state(b,sb)
  offset=step*4
  assert a.blob(sa['dsp_buffer']+offset,4)==b.blob(sb['dsp_buffer']+offset,4)
  samples+=1
proof={'passed':True,'paired_real_scheduler_samples':samples,'paired_actual_APU_volume_writes':writes,'PCM_and_active_voice_register_state_equal':True,'legacy_unused_cache_excluded_from_state_equality':True,'physical_FPS_claim':False,'reference_elf_sha256':hashlib.sha256(paths[0].read_bytes()).hexdigest(),'optimized_elf_sha256':hashlib.sha256(paths[1].read_bytes()).hexdigest()}
if args.json_output:args.json_output.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2))
