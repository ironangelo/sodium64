#!/usr/bin/env python3
"""Original-guest ares test of dormant navigation, N64 Start and PI capture.

Only an emulated N64 controller sample is injected at get_pressed; no guest
state, framebuffer, renderer or diagnostic state is written by the debugger.
This qualifies recorder operation, never console FPS or commercial gameplay.
"""
import argparse,json,socket,time
from pathlib import Path
from native_diag_report import parse,symbolicate
from capture_stage2_publication import load_symbols
from capture_stage2_rows import memory_chunk
from capture_gate_c_stage1_ares import set_breakpoint
from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS,connect_with_retry,validate_stop

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port',type=int,required=True);ap.add_argument('--elf',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    s=load_symbols(a.elf);c=connect_with_retry('127.0.0.1',a.port,30,240)
    try:
        c.sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        chunk=memory_chunk(c.request('qSupported:multiprocess+;swbreak+;hwbreak+'));c.request('?')
        assert c.request('QPassSignals:'+ARES_N64_GUEST_SIGNALS)==b'OK'
        set_breakpoint(c,s['native_diag_finalize'],True)
        # These CPU counters are cached. The uncached RDRAM alias can contain
        # stale zeros; ares readDebug follows the CPU cache for this address.
        state=s['native_diag_state'];deadline=time.monotonic()+150
        while True:
            stop=c.continue_then_interrupt(0.5);validate_stop(stop,'dormant native recorder')
            b=c.read_memory(state,128,128)
            vi=int.from_bytes(b[52:56],'big');armed=int.from_bytes(b[112:116],'big')
            assert armed==0,'capture armed without N64 Start'
            assert int.from_bytes(b[8:12],'big')==0,'timer sampled before manual arm'
            if vi>=1320:break # >22 seconds in emulated VI domain, past old auto limit
            assert time.monotonic()<deadline,('dormant navigation timeout',vi)
        set_breakpoint(c,s['get_pressed'],True);validate_stop(c.request('c'),'N64 input boundary')
        joy=s['joybus_cmd']|0xa0000000
        buttons=bytearray(c.read_memory(joy,8,8))
        buttons[2]&=0x3f # Synthetic connected N64 controller, exactly this input sample
        buttons[4]=0x10;buttons[5:8]=bytes(3) # N64 Start, no other buttons
        c.write_memory(joy,bytes(buttons))
        set_breakpoint(c,s['get_pressed'],False)
        validate_stop(c.request('c'),'20-second manual capture trigger')
        b=c.read_memory(state,128,128)
        assert int.from_bytes(b[112:116],'big')==1,'N64 Start did not arm recorder'
        assert int.from_bytes(b[44:48],'big')<=20,'second records overflowed snapshot'
        set_breakpoint(c,s['native_diag_finalize'],False)
        set_breakpoint(c,s['native_diag_done'],True)
        validate_stop(c.request('c'),'PI capture and terminal screen complete')
        blob=c.read_memory(s['sram']|0xa0000000,0x8000,chunk)
        result,_=parse(blob);h=result['header']
        assert (h['version'],h['reason'],h['precision'],h['frameskip'])==(2,2,8,0)
        assert 20<=h['elapsed_seconds_count_domain']<21 and h['frames_completed']>0
        assert h['halt_acknowledged']==1 and h['sp_dma_settled']==1
        assert len(result['events'])==64 and all('ppu_live_sample' in e for e in result['events'])
        (a.output/'original-capture.sav').write_bytes(blob)
        symbolicate(result,a.elf);(a.output/'decoded-original.json').write_text(json.dumps(result,indent=2)+'\n')
        cart=c.read_memory(0xa8000000,0x8000,chunk)
        (a.output/'cart-sram.bin').write_bytes(cart)
        mismatches=[i for i,(x,y) in enumerate(zip(cart,blob)) if x!=y]
        print(json.dumps(dict(cart_pi_mismatches=len(mismatches),first_offsets=mismatches[:16],
                              pi_registers=c.read_memory(0xa4600000,0x34,0x34).hex())),flush=True)
        assert not mismatches,'cart SRAM PI write differs from the captured local payload'
        proof=dict(passed=True,dormant_vi_before_arm=vi,manual_n64_start=True,cart_pi_bytes_identical=True,
                   format_version=2,seconds=h['elapsed_seconds_count_domain'],precision='MEDIUM',
                   framebuffer_seeding=False,guest_state_writes=False,diagnostic_state_writes=False,
                   input_sample_injection_only=True,native_fps_authority=False)
        (a.output/'qualification.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
    finally:c.close()

if __name__=='__main__':main()
