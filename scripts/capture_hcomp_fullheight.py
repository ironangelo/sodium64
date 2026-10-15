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
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros


def expected(case,x,y):
    if case.startswith('obj-rows-'):
        from make_hcomp_obj_rows import expected_rows
        return expected_rows(case,x,y)
    if case=='fixed-half-raster':
        # Vblank reload runs HDMA at line 0 before the first displayed row.
        # The compiled scheduler/row-input test proves table[y] owns row y.
        blue=(y&31) if y<223 else 0
        return 0x7801|((blue//2)<<1)
    if case.startswith('span-seek-'):
        from make_bg_span_seek import expected_seek
        return expected_seek(case,x,y)
    if case.startswith('mode7-'):
        from make_mode7_windows import expected_mode7
        return expected_mode7(case,x,y)
    from make_hcomp_obj_backdrop import CASES as OBJ_BACKDROP_CASES,expected_obj
    if case in OBJ_BACKDROP_CASES:return expected_obj(case,x,y)
    if case.startswith('fast-'):
        from make_hcomp_direct_backdrop import expected_direct
        return expected_direct(case,x,y)
    if case.startswith("rgb-"):
        from make_hcomp_color_grid import expected_rgb
        return expected_rgb(case,x,y)
    if case in ('layer-window','layer-edge','layer-xor'):
        visible = (x==255) if case=='layer-edge' else (32<=x<=191)
        if case=='layer-xor':visible=not ((32<=x<=191)!=(64<=x<=127))
        return 0x7bc1 if visible else 0x003f
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
    ap.add_argument('--native-armed',action='store_true',help='arm at one natural N64 input sample and observe before diagnostic UI')
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    ev=parse_macros(Path(__file__).resolve().parents[1])
    arenas=[ev.name(n)&0x1fffffff for n in ('HCOMP_WINNER_ARENA','HCOMP_SUB_ARENA','HCOMP_PRESENCE_ARENA')]
    syms=load_symbols(args.elf);stop=syms['native_diag_rsp_wait_end'] if args.native_armed else syms['frame_wait']+0x14
    c=connect_with_retry('127.0.0.1',args.port,30,240)
    try:
        c.sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        supported=c.request('qSupported:multiprocess+;swbreak+;hwbreak+')
        chunk=memory_chunk(supported);c.request('?')
        assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS)==b'OK'
        if args.native_armed:
            assert args.case!='sram','ordinary save fixture requires normal build'
            # Initial get_pressed also belongs to controller/menu setup. Wait
            # for actual completed guest frames, then inject at the gameplay UI.
            set_breakpoint(c,stop,True)
            validate_stop(c.request('c'),'native pixel dormant frame boundary')
            for _ in range(16):
                count=int.from_bytes(c.read_memory(syms['native_diag_state']+24,4,4),'big')
                if count>=6:break
                advance(c,stop)
            else:raise AssertionError('guest never reached dormant frame progress')
            set_breakpoint(c,stop,False)
            set_breakpoint(c,syms['get_pressed'],True)
            validate_stop(c.request('c'),'native pixel arming input sample')
            joy=syms['joybus_cmd']|0xa0000000;buttons=bytearray(c.read_memory(joy,8,8))
            buttons[2]&=0x3f;buttons[4]=0x10;buttons[5:8]=bytes(3)
            c.write_memory(joy,bytes(buttons))
            set_breakpoint(c,syms['get_pressed'],False)
        set_breakpoint(c,stop,True);validate_stop(c.request('c'),'full-height first prelaunch')
        observations=[];accepted=None
        for attempt in range(90 if args.case=='sram' else 12):
            dmem=c.read_memory(0xa4000000,4096,0x400)
            (args.output/f'dmem-{attempt:02d}.bin').write_bytes(dmem)
            (args.output/'sp-pc.bin').write_bytes(c.read_memory(0xa4080000,4,4))
            engine=require_fenced_boundary(c,stage=f'fullheight {args.case} {attempt}')
            guards={}
            for start in arenas:
                # Arbitrary-Y alignment uses up to 48 bytes before the nominal
                # compact origin. Reserve that preceding cache line; keep a
                # complete 64-byte guard outside the expanded allocation.
                for address in (start,start+0x20fc0):
                    guard=c.read_memory(address|0xa0000000,64,64)
                    guards[hex(address)]=guard.hex()
                    assert guard==bytes(64),('compact guard modified',hex(address),guard.hex())
            owner=int.from_bytes(c.read_memory(0xa00f0000,4,4),'big')
            if args.case.startswith(('fast-','mode7-')) or args.case in ('rgb-main','rgb-subscreen','rgb-row-subscreen') or args.case.startswith('span-seek-') and args.case not in ('span-seek-math','span-seek-sub-hidden'):
                owner=int.from_bytes(c.read_memory(0xa4400004,4,4),'big')|0xa0000000
            if args.native_armed:
                addr=syms['queue_id'];aligned=addr&~3
                queue=c.read_memory(aligned,4,4)[addr&3]
                assert queue in (0,4),queue
                owner=int.from_bytes(dmem[0xc00+queue:0xc04+queue],'big')|0xa0000000
                state=c.read_memory(syms['native_diag_state']+112,4,4)
                assert int.from_bytes(state,'big')==1,'diagnostic was not armed'
            report=dict(passed=False,owner=hex(owner))
            if owner in FRAMEBUFFER_ADDRS:
                # Observe the actual last rendered epoch, not just guest source
                # intent. Short-section HDMA can change TS during startup.
                # Pinned ares rounds a4-byte unaligned debugger read down.
                # Slice the aligned full-DMEM snapshot already captured here.
                controls=dmem[0xbb7:0xbbb]
                want_cg={'add':1,'sub':0x81,'sub-half':0xc1,'bg2':0x42,'bg3':0x44,'bg4':0x48,
                         'obj-low':0x51,'obj-high':0x51,'rgb-add':1,'rgb-half':0x41,'rgb-sub':0x81,'rgb-sub-half':0xc1,'rgb-main':0,'rgb-subscreen':0,'rgb-row-add':1,'rgb-row-half':0x41,'rgb-row-sub':0x81,'rgb-row-sub-half':0xc1,'rgb-row-subscreen':0}.get(args.case,0x41)
                want_tm={'bg2':2,'bg3':4,'bg4':8,'obj-low':0x11,'obj-high':0x11,'rgb-subscreen':2,'rgb-row-subscreen':2}.get(args.case,1)
                want_ts=1 if args.case=='bg2' else 2
                if args.case.startswith('obj-rows-'):want_tm=0x11
                want_window=0 if args.case=='fixed-half-raster' else 0xa2 if args.case=='window' else 2
                if args.case.startswith('span-seek-'):
                    want_cg=1 if args.case in ('span-seek-math','span-seek-sub-hidden') else 0
                if args.case.startswith('mode7-'):
                    from make_mode7_windows import controls as mode7_controls
                    want_window,want_cg,want_ts,want_tm=mode7_controls(args.case)
                if args.case.startswith('fast-'):
                    from make_hcomp_direct_backdrop import canonical
                    kind=canonical(args.case)
                    want_cg=0x20;want_tm=1
                    if args.case=='fast-latent-bg2':want_cg=0x22
                    want_ts=0 if args.case=='fast-sub-empty' else 2
                    want_window=(0 if args.case.startswith('fast-fixed-') else 2)+(0 if kind=='fast-always' else 0x20 if kind=='fast-outside' else 0x10)
                    if args.case.startswith('fast-identity-'):
                        from make_hcomp_direct_backdrop import identity_controls
                        want_window,want_cg,want_ts=identity_controls(args.case)
                    from make_hcomp_obj_backdrop import CASES as OBJ_BACKDROP_CASES,controls as obj_controls
                    if args.case in OBJ_BACKDROP_CASES:
                        want_window,want_cg,want_ts,want_tm=obj_controls(args.case)
                image=c.read_memory(owner,280*240*2,chunk)
                report=classify(image,args.case)
                report['delivered_controls']=controls.hex()
                if report['passed']:
                    assert controls==bytes((want_window,want_cg,want_ts,want_tm)),('accepted epoch controls',args.case,controls.hex())
                    if args.case=='fixed-half-raster':
                        rows=int.from_bytes(dmem[0xec4:0xec8],'big')
                        assert rows>=220,('fixed HALF raster was not coalesced',rows)
                        report['coalesced_fixed_half_rows']=rows
                    if args.case.startswith('span-seek-'):
                        sub_window=args.case=='span-seek-sub-hidden'
                        assert dmem[0xbbb:0xbbd]==bytes((2,0) if sub_window else (0,1)),('BG window screen masks',args.case,dmem[0xbbb:0xbbd].hex())
                    if args.case.startswith('fast-'):
                        want_policy=1 if args.case.startswith('fast-identity-') else 2
                        from make_hcomp_obj_backdrop import policy as obj_policy
                        if args.case in OBJ_BACKDROP_CASES:want_policy=obj_policy(args.case)
                        assert int.from_bytes(dmem[0xef0:0xef4],'big')==want_policy,'direct/identity policy not exercised'
                        rows=int.from_bytes(dmem[0xec4:0xec8],'big')
                        if want_policy==0:assert 1<=rows<=240,('general section not exercised',rows)
                        elif kind!='fast-iris-rows':assert rows>8,('whole section not exercised',rows)
                        report['composition_policy']=want_policy
                    accepted=dict(case=args.case,**report,framebuffer=hex(owner),engine=engine,
                                  image_sha256=hashlib.sha256(image).hexdigest(),
                                  compact_guards_passed=True,compact_guards=guards,framebuffer_seeding=False,
                                  guest_state_writes=False,native_armed=args.native_armed,cadence_authority=False)
                    (args.output/'frame.bin').write_bytes(image)
                (args.output/'last-frame.bin').write_bytes(image)
            observations.append(dict(attempt=attempt,**report))
            (args.output/'observations.json').write_text(json.dumps(observations,indent=2)+'\n')
            if accepted and args.case!='sram':break
            if accepted and args.case=='sram':
                cart=c.read_memory(0xa8000000,32768,chunk&~3)
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
