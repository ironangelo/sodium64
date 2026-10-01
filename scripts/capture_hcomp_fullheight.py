#!/usr/bin/env python3
"""Whole-frame oracle at natural RSP fences, with no framebuffer/guest writes."""
import argparse
import hashlib
import json
import socket
import struct
from pathlib import Path
from capture_stage2_publication import load_symbols
from capture_stage2_rows import memory_chunk
from capture_gate_c_stage1_ares import set_breakpoint, require_fenced_boundary, FRAMEBUFFER_ADDRS
from capture_event_arena_pressure import advance
from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS, connect_with_retry, validate_stop
from make_hcomp_fullheight import CASES


def expected(case,x,y):
    if case=='blank' and 13<=y<37:return 1
    if case=='window' and ((32<=x<=95) != (64<=x<=191)):return 1
    if case=='short' and (5<=y<13 or 37<=y<39):return 0xf83f
    if case in ('obj-low','obj-high') and 32<=x<40 and 17<=y<25:
        return 0x003f if case=='obj-low' else 0x03df
    return {'add':0xffc1,'sub':0xf801,'sub-half':0x7801}.get(case,0x7bc1)


def classify(image,case):
    values=struct.unpack('>67200H',image)
    errors=[]
    for y in range(224):
        for x in range(256):
            got=values[(y+8)*280+x+12];want=expected(case,x,y)
            if got!=want:
                if len(errors)<16:errors.append(dict(x=x,y=y,got=hex(got),expected=hex(want)))
    return dict(passed=not errors,mismatches=errors,checked_pixels=224*256)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case',choices=CASES,required=True)
    ap.add_argument('--port',type=int,required=True)
    ap.add_argument('--elf',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    syms=load_symbols(args.elf);stop=syms['frame_wait']+0x14
    c=connect_with_retry('127.0.0.1',args.port,30,240)
    try:
        c.sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        supported=c.request('qSupported:multiprocess+;swbreak+;hwbreak+')
        chunk=memory_chunk(supported);c.request('?')
        assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS)==b'OK'
        set_breakpoint(c,stop,True);validate_stop(c.request('c'),'full-height first prelaunch')
        observations=[];accepted=None
        for attempt in range(90 if args.case=='sram' else 12):
            dmem=c.read_memory(0xa4000000,4096,0x400)
            (args.output/f'dmem-{attempt:02d}.bin').write_bytes(dmem)
            (args.output/'sp-pc.bin').write_bytes(c.read_memory(0xa4080000,4,4))
            engine=require_fenced_boundary(c,stage=f'fullheight {args.case} {attempt}')
            guards={}
            for start in (0xe2000,0xe4000,0xe6000):
                for address in (start-64,start+0x1180):
                    guard=c.read_memory(address|0xa0000000,64,64)
                    guards[hex(address)]=guard.hex()
                    assert guard==bytes(64),('compact guard modified',hex(address),guard.hex())
            owner=int.from_bytes(c.read_memory(0xa00f0000,4,4),'big')
            report=dict(passed=False,owner=hex(owner))
            if owner in FRAMEBUFFER_ADDRS:
                # Observe the actual last rendered epoch, not just guest source
                # intent. Short-section HDMA can change TS during startup.
                # Pinned ares rounds a4-byte unaligned debugger read down.
                # Slice the aligned full-DMEM snapshot already captured here.
                controls=dmem[0xbb7:0xbbb]
                want_cg={'add':1,'sub':0x81,'sub-half':0xc1,'bg2':0x42,'bg3':0x44,'bg4':0x48,
                         'obj-low':0x51,'obj-high':0x51}.get(args.case,0x41)
                want_tm={'bg2':2,'bg3':4,'bg4':8,'obj-low':0x11,'obj-high':0x11}.get(args.case,1)
                want_ts=1 if args.case=='bg2' else 2
                want_window=0xa2 if args.case=='window' else 2
                image=c.read_memory(owner,280*240*2,chunk)
                report=classify(image,args.case)
                report['delivered_controls']=controls.hex()
                if report['passed']:
                    assert controls==bytes((want_window,want_cg,want_ts,want_tm)),('accepted epoch controls',args.case,controls.hex())
                    accepted=dict(case=args.case,**report,framebuffer=hex(owner),engine=engine,
                                  image_sha256=hashlib.sha256(image).hexdigest(),
                                  compact_guards_passed=True,compact_guards=guards,delivered_controls=controls.hex(),framebuffer_seeding=False,
                                  guest_state_writes=False,cadence_authority=False)
                    (args.output/'frame.bin').write_bytes(image)
                (args.output/'last-frame.bin').write_bytes(image)
            observations.append(dict(attempt=attempt,**report))
            (args.output/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
            if accepted and args.case!='sram':break
            if accepted and args.case=='sram':
                cart=c.read_memory(0xa8000000,32768,chunk)
                (args.output/'last-cart.sav').write_bytes(cart)
                if cart[:8]==b'S64GAME!':
                    assert cart[8]==0xa7,('ordinary SRAM load/import echo',cart[8])
                    assert cart[16]==0xa7
                    (args.output/'cart.sav').write_bytes(cart)
                    accepted['ordinary_sram_import_and_pi_save_passed']=True
                    break
            advance(c,stop)
        assert accepted is not None,observations[-1]
        if args.case=='sram':assert accepted.get('ordinary_sram_import_and_pi_save_passed'),observations
        (args.output/'result.json').write_text(json.dumps(accepted,indent=2)+'\n')
        print('FULL_HEIGHT_GUEST PASS',json.dumps(accepted),flush=True)
    finally:c.close()


if __name__=='__main__':main()
