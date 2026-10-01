#!/usr/bin/env python3
"""Uninterrupted native PI trace qualification; only stop at final red done."""
import argparse
import json
import socket
import struct
from pathlib import Path
from capture_stage2_publication import load_symbols
from capture_stage2_rows import memory_chunk
from capture_gate_c_stage1_ares import set_breakpoint
from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS, connect_with_retry, validate_stop
from decode_stage2_color import decode, qualify, COLORS

def frame_check(frame):
    from capture_stage2_publication import classify_band
    band=classify_band(frame)
    p=struct.unpack('>67200H',frame)
    bad=[y for y in range(16,232) if y not in range(200,216)
         and any(x!=0xF801 for x in p[y*280+12:y*280+268])]
    for y in range(200,216):
        expected=[c for c in COLORS for _ in range(40)]
        assert list(p[y*280+12:y*280+252])==expected,('reference row',y)
    assert band['passed'] and not bad,(band,bad)
    return dict(band=band,red_rows_pass=True,reference_rows_pass=True,
                excluded_red_rows=[200,215],frame_seeded=False)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port',type=int,required=True)
    ap.add_argument('--elf',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--mixed',action='store_true')
    ap.add_argument('--frozen-phase',choices=['a','b'],help='fresh-boot semantic capture, no cadence authority')
    args=ap.parse_args();syms=load_symbols(args.elf)
    args.output.mkdir(parents=True,exist_ok=True)
    c=connect_with_retry('127.0.0.1',args.port,30,240)
    try:
        c.sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        supported=c.request('qSupported:multiprocess+;swbreak+;hwbreak+')
        chunk=memory_chunk(supported)
        c.request('?')
        assert b'QPassSignals+' in supported
        assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS)==b'OK'
        if args.frozen_phase:
            name='color_diag_phase_'+args.frozen_phase
            set_breakpoint(c,syms[name],True)
            validate_stop(c.request('c'),name)
            origin=struct.unpack('>I',c.read_memory(0xA4400004,4,4))[0]
            frame=c.read_memory(origin|0xA0000000,134400,chunk)
            (args.output/(name+'.bin')).write_bytes(frame)
            result=frame_check(frame)
            result['control']=struct.unpack('>I',c.read_memory(0xA4400000,4,4))[0]
            assert result['control']==(0x202 if args.frozen_phase=='a' else 0x3202)
            result['cadence_authority']=False
            result['fresh_boot']=True
            (args.output/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
            return
        set_breakpoint(c,syms['hw_profile_done'],True)
        validate_stop(c.request('c'),'continuous color diagnostic')
        save=c.read_memory(0xA8000000,32768,0x400)
        (args.output/'cart.sav').write_bytes(save)
        source=c.read_memory(syms['sram']|0x20000000,32768,0x400)
        (args.output/'source-sram.bin').write_bytes(source)
        assert save==source,'PI source/cart mismatch'
        result,canonical,raw,pixels,pcm=decode(save)
        result['workload']=qualify(result,raw,args.mixed)
        # Same stopped immutable state, alternate transfer size: classify the
        # prior large-cart-read anomaly without repairing or selecting bytes.
        large=c.read_memory(0xA8000000,32768,chunk)
        (args.output/'cart-large-read.bin').write_bytes(large)
        large_source=c.read_memory(syms['sram']|0x20000000,32768,chunk)
        (args.output/'source-large-read.bin').write_bytes(large_source)
        result['alternate_readback']=dict(chunk=chunk,cart_equal=large==save,
            source_equal=large_source==source,
            first_cart_difference=next((i for i,(a,b) in enumerate(zip(large,save)) if a!=b),None))
        ring=c.read_memory(syms['dsp_buffer']|0x20000000,8192,chunk)
        ptr=result['probe_header']['dsp_pointer']
        start=(ptr-4096)&8191
        assert pcm==(ring+ring)[start:start+4096],'PCM chronological mismatch'
        result['cart_transport_verified']=True
        result['continuous_execution']=True
        (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
    finally:c.close()
if __name__=='__main__':main()
