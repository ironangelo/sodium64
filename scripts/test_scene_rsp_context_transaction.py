#!/usr/bin/env python3
"""Production C transaction executes actual RSP binaries via synthetic MMIO/PI.

Original numeric context only. No serial, ROM or physical timing acceptance.
"""
import argparse,ctypes as c,json,os,random,struct,subprocess,tempfile
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from test_scene_rsp_context import execute,state
from test_native_diag_continuous import load_elf
U32=c.POINTER(c.c_uint32)
Read=c.CFUNCTYPE(c.c_uint32,c.c_uint32)
Write=c.CFUNCTYPE(None,c.c_uint32,c.c_uint32)
Transfer=c.CFUNCTYPE(c.c_int,U32,c.c_uint32,c.c_int)
Wait=c.CFUNCTYPE(c.c_int)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build',type=Path)
    ap.add_argument('--cc',default=os.environ.get('CC','gcc'));ap.add_argument('--output',type=Path)
    ap.add_argument('--unprefixed-elf',type=Path)
    ap.add_argument('--gauss-elf',type=Path,help='exercise opt-in primitive and its safe timeout recovery')
    ap.add_argument('--gauss-dma',action='store_true',help='test bounded input DMA and register recovery')
    a=ap.parse_args();root=Path(__file__).resolve().parents[1];cases=0
    _,capture=read_text(a.build/'src/rsp_scene_capture.elf');_,restore=read_text(a.build/'src/rsp_scene_restore.elf')
    def array(blob):return (c.c_uint32*(len(blob)//4))(*struct.unpack('>'+str(len(blob)//4)+'I',blob))
    cap,res=array(capture),array(restore)
    gauss=b''
    if a.gauss_elf:_,gauss=read_text(a.gauss_elf);assert len(gauss)==80
    assert not a.gauss_dma or gauss
    with tempfile.TemporaryDirectory(prefix='s64-rsp-ctx-',ignore_cleanup_errors=True) as directory:
        dll=Path(directory)/('context.dll' if os.name=='nt' else 'context.so')
        cmd=[a.cc,'-std=c11','-O2','-shared','-Wall','-Wextra','-Werror']
        cmd+=['-Wl,--export-all-symbols'] if os.name=='nt' else ['-fPIC']
        if gauss:
            stub=Path(directory)/'gauss.c'
            words=','.join(hex(x)+'u' for x in struct.unpack('>20I',gauss))
            stub.write_text('#include <stdint.h>\nconst uint32_t rsp_dsp_gauss_text_start[20]={'+words+'};\n'
                '__asm__(".globl rsp_dsp_gauss_text_end\\n.set rsp_dsp_gauss_text_end,rsp_dsp_gauss_text_start+80");\n'
                'volatile uint32_t scene_rsp_gauss_host_stride=1;\n'
                'volatile uint32_t scene_rsp_gauss_host_source_invalid=0;\n'
                'uint32_t scene_rsp_gauss_host_visible[32];\n'
                'uint32_t scene_rsp_gauss_host_ticks(void){static uint32_t n;return n+=scene_rsp_gauss_host_stride;}\n'
                'uint32_t scene_rsp_gauss_host_dma_source(uint32_t *p){\n'
                'if(((uintptr_t)p&15)||scene_rsp_gauss_host_source_invalid)return 0;\nfor(unsigned i=0;i<32;i++)scene_rsp_gauss_host_visible[i]=p[i];\nreturn 0x10000;}\n')
            cmd+=['-DSODIUM64_DSP_RSP_GAUSS_PROBE=1','-DSODIUM64_RSP_GAUSS_HOST=1',str(stub)]
            if a.gauss_dma:cmd+=['-DSODIUM64_DSP_RSP_GAUSS_DMA=1']
        subprocess.run(cmd+[str(root/'src/scene_rsp_context.c'),'-o',str(dll)],check=True)
        lib=c.CDLL(str(dll));fn=lib.scene_rsp_context_roundtrip
        fn.argtypes=[U32,U32,c.c_uint,U32,c.c_uint,Read,Write,Transfer,Wait];fn.restype=c.c_uint32
        def test(*,fail=0,corrupt=0,wait_fault=0,bad_stop=False,SP_busy=False,readback_fault=False,old_programs=None,gauss_fault=False,dma_mode=1,dma_busy_fault=False,dma_input_fault=False,dma_length_fault=False,dma_address_fault=False,dma_source_fault=False):
            nonlocal cases
            rng=random.Random(4560);sp=bytearray(rng.randbytes(8192));cart=bytearray(9216)
            struct.pack_into('>III',sp,0x13c0,0x40882000,0x0900040f,0)
            struct.pack_into('>I',sp,0x13bc,0x24080002)
            saved=bytes(sp);machine=list(state(4500));machine[0][8]=2
            before=([*machine[0]],[x.copy() for x in machine[1]],machine[2].copy(),machine[3].copy())
            status=0x1801;pc=0x3c8 if not bad_stop else 0x3c0
            calls=waits=writes=0;trace=[];errors=[]
            dma_regs=[0x380,0x12000,0xff8,0xff8];dma_before=dma_regs.copy();dma_started=0
            if a.gauss_dma:
                c.c_uint32.in_dll(lib,'scene_rsp_gauss_dma').value=dma_mode
                c.c_uint32.in_dll(lib,'scene_rsp_gauss_host_stride').value=1
                c.c_uint32.in_dll(lib,'scene_rsp_gauss_host_source_invalid').value=int(dma_source_fault)
            @Read
            def read(address):
                try:
                    if address==0xa4040010:return status
                    if address==0xa4080000:return pc
                    if a.gauss_dma and 0xa4040000<=address<0xa4040010:return dma_regs[(address-0xa4040000)//4]
                    if address in (0xa4040018,0xa4040014):return int(SP_busy or (dma_busy_fault and dma_started))
                    assert 0xa4000000<=address<0xa4002000 and address%4==0,hex(address)
                    return struct.unpack_from('>I',sp,address-0xa4000000)[0]
                except Exception as e:errors.append(e);return 0
            @Write
            def write(address,value):
                nonlocal writes,status,pc,dma_started
                try:
                    writes+=1
                    if address==0xa4040010:
                        assert value in ((2,5,6) if gauss else (5,6))
                        if value==5:status&=~3
                        elif value==6:status=(status|1)&~2
                        else:status|=1
                    elif address==0xa4080000:pc=value
                    elif a.gauss_dma and address in (0xa4040000,0xa4040004):
                        if dma_address_fault and dma_started and value==dma_before[0]:value^=8
                        dma_regs[(address-0xa4040000)//4]=value
                    elif a.gauss_dma and address==0xa4040008:
                        assert dma_mode==1 and dma_regs[:2]==[0,0x10000] and value==127
                        visible=(c.c_uint32*32).in_dll(lib,'scene_rsp_gauss_host_visible')
                        sp[:128]=struct.pack('>32I',*visible);dma_regs[0]=128;dma_regs[1]+=128;dma_started+=1
                        if dma_input_fault:sp[0]^=0x80
                        if dma_length_fault:dma_regs[2]=dma_before[2]^8
                        if dma_busy_fault:c.c_uint32.in_dll(lib,'scene_rsp_gauss_host_stride').value=10000000
                    else:
                        assert 0xa4000000<=address<0xa4002000 and address%4==0,hex(address)
                        if readback_fault and calls>76 and address==0xa4000020:value^=1
                        struct.pack_into('>I',sp,address-0xa4000000,value)
                except Exception as e:errors.append(e)
            @Transfer
            def transfer(buffer,offset,to_cart):
                nonlocal calls
                try:
                    calls+=1;trace.append((calls,offset,to_cart))
                    assert offset%512==0 and offset+512<=len(cart)
                    if calls==fail:return 0
                    if to_cart:cart[offset:offset+512]=struct.pack('>128I',*(buffer[i] for i in range(128)))
                    else:
                        values=struct.unpack_from('>128I',cart,offset)
                        for i,value in enumerate(values):buffer[i]=value
                    if calls==corrupt:buffer[10]^=1
                    return 1
                except Exception as e:errors.append(e);return 0
            @Wait
            def wait():
                nonlocal waits,status
                try:
                    waits+=1
                    if waits==wait_fault:return 0
                    assert pc==0 and not status&3
                    d=bytearray(sp[:4096]);code=bytes(sp[4096:])
                    is_gauss=bool(gauss) and code[:len(gauss)]==gauss
                    execute(code,d,*machine,pending_entry=None if is_gauss else 0x3c)
                    if is_gauss and gauss_fault:d[144]^=1
                    sp[:4096]=d;status|=3;return 1
                except Exception as e:errors.append(e);return 0
            scratch=(c.c_uint32*128)()
            selected_cap,selected_res=old_programs or (cap,res)
            actual=fn(scratch,selected_cap,len(selected_cap),selected_res,len(selected_res),read,write,transfer,wait)
            assert not errors,errors
            safe_gauss_wait=bool(gauss) and 2<=wait_fault<=65
            expected=0 if bad_stop or SP_busy or 0<fail<=48 or 0<corrupt<=48 else 2 if fail or corrupt or (wait_fault and not safe_gauss_wait) or readback_fault or old_programs or dma_busy_fault or dma_length_fault or dma_address_fault else 1
            assert actual==expected,(cases,actual,expected,calls,waits)
            if actual==0:assert not writes and bytes(sp)==saved and tuple(machine)==before,'mutation before full backup'
            if actual==1:
                assert calls==92 and bytes(sp)==saved and tuple(machine)==before
                assert status==0x1801 and pc==0x3c
                if gauss:
                    metrics=(c.c_uint32*8).in_dll(lib,'scene_rsp_gauss_metrics')
                    assert metrics[0]==(0 if safe_gauss_wait or gauss_fault or dma_input_fault or dma_source_fault else 1)
                    if metrics[0]:assert waits==67 and metrics[1]==512 and metrics[2]==0xffffffff
                else:assert waits==5
                if a.gauss_dma:
                    assert dma_regs==dma_before,'DMA register owner not restored'
                    if not safe_gauss_wait and not gauss_fault and not dma_input_fault and not dma_source_fault:assert dma_started==(64 if dma_mode else 0)
            if a.gauss_dma and (dma_busy_fault or dma_length_fault or dma_address_fault or dma_source_fault):
                diag=(c.c_uint32*3).in_dll(lib,'scene_rsp_gauss_dma_diag')
                assert diag[0]==(1 if dma_busy_fault else 4 if dma_source_fault else 3)
                if dma_length_fault or dma_address_fault:
                    index=2 if dma_length_fault else 0
                    assert diag[1]==dma_before[index] and diag[2]==dma_regs[index]
                    assert c.c_uint32.in_dll(lib,'scene_rsp_context_mismatch_word').value==0x80000000|index
            if old_programs:
                assert c.c_uint32.in_dll(lib,'scene_rsp_context_stage').value==4
                assert c.c_uint32.in_dll(lib,'scene_rsp_context_mismatch_word').value==8
            cases+=1;return trace
        trace=test()
        for position in range(1,93):test(fail=position)
        for position,offset,to_cart in trace:
            if not to_cart:test(corrupt=position)
        wait_positions=67 if gauss else 5
        for wait in range(1,wait_positions+1):test(wait_fault=wait)
        if gauss:test(gauss_fault=True)
        if a.gauss_dma:
            test(dma_mode=0);test(dma_busy_fault=True);test(dma_input_fault=True)
            test(dma_length_fault=True);test(dma_address_fault=True);test(dma_source_fault=True)
        test(bad_stop=True);test(SP_busy=True);test(readback_fault=True)
        if a.unprefixed_elf:
            memory,symbols=load_elf(a.unprefixed_elf)
            def previous(name):
                first=symbols['rsp_scene_'+name+'_text_start'];last=symbols['rsp_scene_'+name+'_text_end']
                return array(bytes(memory[(first&0x1fffffff)+i] for i in range(last-first)))
            test(old_programs=(previous('capture'),previous('restore')))
        result=dict(passed=True,cases=cases,production_C_and_actual_RSP_binaries=True,
            transfer_fault_positions=92,read_corruptions=sum(not x[2] for x in trace),wait_fault_positions=wait_positions,
            pre_mutation_full_backup=True,deliberate_zero_context_proved=not bool(gauss),
            full700byte_register_recapture_exact=True,SP8KiB_restore_checksum_readback=True,
            no_DP_AI_guest_SD_or_ROM_access=True,callback_exceptions_fail=True,
            hardware_timing_mocked=True,native_acceptance=False,complete_machine_restore=False)
        result['unprefixed_native_stage4_word8_reproduced']=bool(a.unprefixed_elf)
        if gauss:result.update(gauss_lanes=512,gauss_clobbered_context_restored=True,
            all64_primitive_wait_faults_safely_halted_and_restored=True,gauss_result_mutation_rejected=True)
        if a.gauss_dma:result.update(DMA_input_extent_and_alignment=True,DMA_register_addresses_and_idle_lengths_exact=True,
            DMA_busy_timeout_stops_before_context_memory_overwrite=True,DMA_corrupt_input_detected=True,
            DMA_length_or_address_restore_fault_requires_menu=True,same_image_PIO_control=True,
            DMA_fault_kind_expected_observed_and_register_index_exact=True,
            invalid_CPU_DMA_source_safely_restores_and_reports_failure=True,
            CPU_cache_writeback_and_hardware_DMA_timing_mocked=True)
        if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
        if os.name=='nt':c.windll.kernel32.FreeLibrary(c.c_void_p(lib._handle))
if __name__=='__main__':main()
