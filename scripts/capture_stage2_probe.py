#!/usr/bin/env python3
"""Boot continuously through real PI SRAM writes, then read cart and source.

Only breakpoint: existing final done loop, after red fill. No guest/memory
seeding, frame stops or single steps. GDB readback independently verifies
actual cart transport, captured pixels/context and chronological PCM bytes.
"""
import argparse
import json
from pathlib import Path
from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS, connect_with_retry, validate_stop
from capture_stage2_publication import load_symbols
from capture_gate_c_stage1_ares import set_breakpoint
from decode_stage2_probe import decode, OFFSET, SIZE

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port',type=int,required=True)
    ap.add_argument('--elf',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--mixed',action='store_true')
    args = ap.parse_args(); syms = load_symbols(args.elf)
    out=args.output; out.mkdir(parents=True,exist_ok=True)
    c=connect_with_retry('127.0.0.1',args.port,30,120)
    try:
        supported=c.request('qSupported:multiprocess+;swbreak+;hwbreak+')
        c.request('?')
        assert b'QPassSignals+' in supported
        assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS)==b'OK'
        set_breakpoint(c,syms['hw_profile_done'],True)
        validate_stop(c.request('c'),'continuous final PI capture')
        save=c.read_memory(0xA8000000,32768,0x400)
        (out/'cart.sav').write_bytes(save)
        result,raw,pixels,pcm=decode(save)
        # Local SRAM is merely transport source; reading cart proves PI writes.
        assert raw==c.read_memory((syms['sram']|0x20000000)+OFFSET,SIZE,0x400)
        # Profiler header/payload are separately written by the existing path.
        assert save[:128]==c.read_memory(syms['hw_profile_header'],128,128)
        assert save[0x100:0x4120]==c.read_memory(syms['profile_magic'],0x4020,0x400)
        spans=[(0x2080,0xA00F2300+4480+24,512),
               (0x2280,0xA0113000+4480+24,512),
               (0x2480,0xA0133D00+4480+24,512),
               (0x2680,0xA00E2000+24,512),
               (0x2880,0xA00E6000+24,512),
               (0x2A80,0xA00E4000+24,512),
               (0x2C80,0xA00F0000,16),
               (0x2C90,syms['dsp_regs'],128)]
        origin=result['header']['vi_origin']
        for offset,start,size in spans:
            data=c.read_memory(start,size,0x400)
            # Final red fill changes just the displayed buffer. All other
            # buffers/context remain available for independent byte checks.
            if not (offset in (0x2080,0x2280,0x2480) and (start-4504)&0x1FFFFFFF==origin):
                assert raw[offset:offset+size]==data,(offset,start)
        ring=c.read_memory(syms['dsp_buffer']|0x20000000,8192,0x400)
        ptr=result['header']['dsp_pointer'];start=(ptr-4096)&8191
        expected=(ring+ring)[start:start+4096]
        assert pcm==expected,'chronological PCM mismatch'
        assert result['band']['reference_matches'],result
        assert result['frame_budgets']==[60]*5,result
        if args.mixed:
            assert result['header']['enabled']==255,result
            assert result['audio']['nonzero'] and result['audio']['channels_differ'],result
            assert result['audio']['unique_left']>16,result
        else:
            assert result['header']['enabled']==0 and not result['audio']['nonzero'],result
        result['cart_transport_verified']=True
        result['continuous_execution']=True
        (out/'transport-result.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
    finally:
        c.close()

if __name__=='__main__':
    main()
