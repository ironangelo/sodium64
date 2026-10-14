#!/usr/bin/env python3
"""Production C transaction executes actual RSP binaries via synthetic MMIO/PI.

Original numeric context only. No serial, ROM or physical timing acceptance.
"""
import argparse,ctypes as c,json,os,random,struct,subprocess,tempfile
from pathlib import Path
from check_rsp_branch_delay_slots import read_text
from test_scene_rsp_context import execute,state
from test_rsp_dsp_brr_resident import ResidentDMA,DMAStalled
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
    ap.add_argument('--brr-elf',type=Path,help='exercise the32-sample primitive under the same owner')
    ap.add_argument('--brr-resident',action='store_true',help='raw jobs and private output DMA')
    ap.add_argument('--gauss-dma',action='store_true',help='test bounded input DMA and register recovery')
    ap.add_argument('--expect-cursor-rejection',action='store_true',help='reproduce native v2 current/pending cursor rejection')
    ap.add_argument('--source',type=Path,help='optional preserved production C source for a regression reproduction')
    a=ap.parse_args();root=Path(__file__).resolve().parents[1];cases=0
    _,capture=read_text(a.build/'src/rsp_scene_capture.elf');_,restore=read_text(a.build/'src/rsp_scene_restore.elf')
    def array(blob):return (c.c_uint32*(len(blob)//4))(*struct.unpack('>'+str(len(blob)//4)+'I',blob))
    cap,res=array(capture),array(restore)
    gauss=b''
    assert not(a.gauss_elf and a.brr_elf)
    if a.gauss_elf:_,gauss=read_text(a.gauss_elf);assert len(gauss)==80
    if a.brr_elf:_,gauss=read_text(a.brr_elf);assert len(gauss)==(1028 if a.brr_resident else 444)
    assert not a.brr_resident or (a.brr_elf and a.gauss_dma)
    input_bytes=128 if a.brr_resident else 96 if a.brr_elf else 128
    output_offset=0x120 if a.brr_elf else 0x90
    expected_samples=2048 if a.brr_elf else 512
    assert not a.gauss_dma or gauss
    assert not a.expect_cursor_rejection or a.gauss_dma
    with tempfile.TemporaryDirectory(prefix='s64-rsp-ctx-',ignore_cleanup_errors=True) as directory:
        dll=Path(directory)/('context.dll' if os.name=='nt' else 'context.so')
        cmd=[a.cc,'-std=c11','-O2','-shared','-Wall','-Wextra','-Werror']
        cmd+=['-Wl,--export-all-symbols'] if os.name=='nt' else ['-fPIC']
        if gauss:
            stub=Path(directory)/'gauss.c'
            program='rsp_dsp_brr' if a.brr_elf else 'rsp_dsp_gauss'
            words=','.join(hex(x)+'u' for x in struct.unpack('>'+str(len(gauss)//4)+'I',gauss))
            stub.write_text('#include <stdint.h>\nconst uint32_t '+program+'_text_start['+str(len(gauss)//4)+']={'+words+'};\n'
                '__asm__(".globl '+program+'_text_end\\n.set '+program+'_text_end,'+program+'_text_start+'+str(len(gauss))+'");\n'
                'volatile uint32_t scene_rsp_gauss_host_stride=1;\n'
                'volatile uint32_t scene_rsp_gauss_host_source_invalid=0;\n'
                'uint32_t scene_rsp_gauss_host_visible[32];\n'
                'uintptr_t scene_rsp_brr_host_source_ptr;\n'
                'uint32_t scene_rsp_gauss_host_ticks(void){static uint32_t n;return n+=scene_rsp_gauss_host_stride;}\n'
                'uint32_t scene_rsp_gauss_host_dma_source(uint32_t *p){\n'
                'if(((uintptr_t)p&15)||scene_rsp_gauss_host_source_invalid)return 0;\nscene_rsp_brr_host_source_ptr=(uintptr_t)p;\nfor(unsigned i=0;i<32;i++)scene_rsp_gauss_host_visible[i]=p[i];\nreturn 0x10000;}\n')
            cmd+=['-DSODIUM64_DSP_RSP_GAUSS_PROBE=1','-DSODIUM64_RSP_GAUSS_HOST=1',str(stub)]
            if a.brr_elf:cmd+=['-DSODIUM64_DSP_RSP_BRR_PROBE=1']
            if a.brr_resident:cmd+=['-DSODIUM64_DSP_RSP_BRR_RESIDENT=1']
            if a.gauss_dma:cmd+=['-DSODIUM64_DSP_RSP_GAUSS_DMA=1']
        subprocess.run(cmd+['-I',str(root/'src'),str(a.source or root/'src/scene_rsp_context.c'),'-o',str(dll)],check=True)
        lib=c.CDLL(str(dll));fn=lib.scene_rsp_context_roundtrip
        fn.argtypes=[U32,U32,c.c_uint,U32,c.c_uint,Read,Write,Transfer,Wait];fn.restype=c.c_uint32
        def test(*,fail=0,corrupt=0,wait_fault=0,bad_stop=False,SP_busy=False,readback_fault=False,old_programs=None,gauss_fault=False,dma_mode=1,dma_busy_fault=False,dma_input_fault=False,dma_length_fault=False,dma_address_fault=False,dma_source_fault=False,cursor_busy_fault=False,cursor_bytes_fault=False,source_before_fault=False,source_after_fault=False,original_cursor=0x1790,original_skip=0,original_bad=False,resident_output_stall=False,resident_guard_fault=False):
            nonlocal cases
            rng=random.Random(4560);sp=bytearray(rng.randbytes(8192));cart=bytearray(9216)
            struct.pack_into('>III',sp,0x13c0,0x40882000,0x0900040f,0)
            struct.pack_into('>I',sp,0x13bc,0x24080002)
            saved=bytes(sp);machine=list(state(4500));machine[0][8]=2
            before=([*machine[0]],[x.copy() for x in machine[1]],machine[2].copy(),machine[3].copy())
            status=0x1801;pc=0x3c8 if not bad_stop else 0x3c0
            calls=waits=writes=0;trace=[];errors=[]
            # CPU writes pending addresses; reads expose current/last transfer.
            # This distinction reproduced native1790->80, unlike the former
            # direct-write/readback fixture. ares/n64/rsp/io.cpp and dma.cpp.
            dma_regs=[original_cursor,0x12000,0xff8|original_skip,0xff8|original_skip]
            if original_bad:dma_regs[1]=7
            dma_before=dma_regs.copy();dma_pending=dma_regs[:2].copy();dma_started=cursor_replays=0
            resident_busy=False;private_output_writes=0
            tail=(original_cursor&0x1000)|((original_cursor-8)&0xfff)
            source_tail=bytes(sp[tail:tail+8])
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
                    if address in (0xa4040018,0xa4040014):return int(SP_busy or resident_busy or (dma_busy_fault and dma_started) or (cursor_busy_fault and cursor_replays))
                    if a.gauss_dma and address in (0xa0011ff8,0xa0011ffc):
                        value=struct.unpack_from('>I',source_tail,address-0xa0011ff8)[0]
                        return value^(1 if source_before_fault or (source_after_fault and dma_started) else 0)
                    assert 0xa4000000<=address<0xa4002000 and address%4==0,hex(address)
                    return struct.unpack_from('>I',sp,address-0xa4000000)[0]
                except Exception as e:errors.append(e);return 0
            @Write
            def write(address,value):
                nonlocal writes,status,pc,dma_started,cursor_replays
                try:
                    writes+=1
                    if address==0xa4040010:
                        assert value in ((2,5,6) if gauss else (5,6))
                        if value==5:status&=~3
                        elif value==6:status=(status|1)&~2
                        else:status|=1
                    elif address==0xa4080000:pc=value
                    elif a.gauss_dma and address in (0xa4040000,0xa4040004):
                        dma_pending[(address-0xa4040000)//4]=value
                    elif a.gauss_dma and address==0xa4040008:
                        assert dma_mode==1
                        dma_regs[:2]=dma_pending
                        if value==input_bytes-1:
                            assert dma_pending==[0,0x10000]
                            visible=(c.c_uint32*32).in_dll(lib,'scene_rsp_gauss_host_visible')
                            sp[:input_bytes]=struct.pack('>'+str(input_bytes//4)+'I',*visible[:input_bytes//4])
                            dma_regs[0]=input_bytes;dma_regs[1]+=input_bytes;dma_started+=1
                            if dma_input_fault:sp[0]^=0x80
                            if dma_busy_fault:c.c_uint32.in_dll(lib,'scene_rsp_gauss_host_stride').value=10000000
                        else:
                            assert value==(7|original_skip) and dma_pending==[tail,0x11ff8]
                            sp[tail:tail+8]=source_tail;cursor_replays+=1
                            dma_regs[0]=(tail&0x1000)|((tail+8)&0xfff);dma_regs[1]+=8
                            if cursor_bytes_fault:sp[tail]^=1
                            if cursor_busy_fault:c.c_uint32.in_dll(lib,'scene_rsp_gauss_host_stride').value=10000000
                            if dma_address_fault:dma_regs[0]^=8
                        dma_regs[2]=dma_regs[3]=0xff8|(value&0xfff00000)
                        if dma_length_fault and cursor_replays:dma_regs[2]=dma_regs[3]=dma_before[2]^8
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
                nonlocal waits,status,dma_started,resident_busy,private_output_writes
                try:
                    waits+=1
                    if waits==wait_fault:return 0
                    assert pc==0 and not status&3
                    d=bytearray(sp[:4096]);code=bytes(sp[4096:])
                    is_gauss=bool(gauss) and code[:len(gauss)]==gauss
                    if is_gauss and a.brr_resident:
                        address=c.c_void_p.in_dll(lib,'scene_rsp_brr_host_source_ptr').value;assert address
                        owner=(c.c_uint32*52).from_address(address)
                        memory=bytearray(struct.pack('>48I',*owner[:48]))
                        def completed(kind,current,memory):
                            nonlocal dma_started,private_output_writes
                            dma_regs[:]=current;dma_pending[:]=device.pending
                            if kind=='input':dma_started+=1
                            else:
                                for i,value in enumerate(struct.unpack('>16I',memory[128:])):owner[32+i]=value
                                private_output_writes+=1
                                if resident_guard_fault:owner[48]^=1
                        device=ResidentDMA(d,memory,read_fault=dma_input_fault,output_fault=gauss_fault,
                            stalled='input' if dma_busy_fault else 'output' if resident_output_stall else None,
                            on_transfer=completed)
                        try:execute(code,d,*machine,rcp=device.control)
                        except DMAStalled:
                            sp[:4096]=d;resident_busy=True;return 0
                        assert not device.active
                    else:
                        execute(code,d,*machine,pending_entry=None if is_gauss else 0x3c)
                        if is_gauss and gauss_fault:d[output_offset]^=1
                    sp[:4096]=d;status|=3;return 1
                except Exception as e:errors.append(e);return 0
            scratch=(c.c_uint32*128)()
            selected_cap,selected_res=old_programs or (cap,res)
            actual=fn(scratch,selected_cap,len(selected_cap),selected_res,len(selected_res),read,write,transfer,wait)
            assert not errors,errors
            safe_gauss_wait=bool(gauss) and 2<=wait_fault<=65
            expected=0 if bad_stop or SP_busy or original_bad or source_before_fault or 0<fail<=48 or 0<corrupt<=48 else 2 if fail or corrupt or (wait_fault and not safe_gauss_wait) or readback_fault or old_programs or dma_busy_fault or resident_output_stall or dma_length_fault or dma_address_fault or cursor_busy_fault or cursor_bytes_fault or source_after_fault else 1
            if a.expect_cursor_rejection and dma_mode:expected=2
            assert actual==expected,(cases,actual,expected,calls,waits)
            if actual==0:assert not writes and bytes(sp)==saved and tuple(machine)==before,'mutation before full backup'
            if actual==1:
                assert calls==92 and bytes(sp)==saved and tuple(machine)==before
                assert status==0x1801 and pc==0x3c
                if gauss:
                    metrics=(c.c_uint32*8).in_dll(lib,'scene_rsp_gauss_metrics')
                    assert metrics[0]==(0 if safe_gauss_wait or gauss_fault or dma_input_fault or dma_source_fault or resident_guard_fault else 1)
                    if metrics[0]:assert waits==67 and metrics[1]==expected_samples and metrics[2]==0xffffffff
                else:assert waits==5
                if a.gauss_dma:
                    assert dma_regs==dma_before,'DMA register owner not restored'
                    if not safe_gauss_wait and not gauss_fault and not dma_input_fault and not dma_source_fault and not resident_guard_fault:
                        assert dma_started==(64 if dma_mode else 0)
                        if a.brr_resident:assert private_output_writes==64
                    assert cursor_replays==(1 if dma_mode else 0)
                    if dma_mode:assert dma_pending==dma_before[:2]
            if a.gauss_dma and (dma_busy_fault or dma_length_fault or dma_address_fault or dma_source_fault):
                diag=(c.c_uint32*3).in_dll(lib,'scene_rsp_gauss_dma_diag')
                assert diag[0]==(1 if dma_busy_fault else 4 if dma_source_fault else 3)
                if dma_length_fault or dma_address_fault:
                    index=2 if dma_length_fault else 0
                    assert diag[1]==dma_before[index] and diag[2]==dma_regs[index]
                    assert c.c_uint32.in_dll(lib,'scene_rsp_context_mismatch_word').value==0x80000000|index
            if a.gauss_dma and (cursor_busy_fault or cursor_bytes_fault or source_after_fault):
                assert (c.c_uint32*3).in_dll(lib,'scene_rsp_gauss_dma_diag')[0]==5
            if old_programs:
                assert c.c_uint32.in_dll(lib,'scene_rsp_context_stage').value==4
                assert c.c_uint32.in_dll(lib,'scene_rsp_context_mismatch_word').value==8
            cases+=1;return trace
        if a.expect_cursor_rejection:
            test()
            diag=(c.c_uint32*3).in_dll(lib,'scene_rsp_gauss_dma_diag')
            metrics=(c.c_uint32*8).in_dll(lib,'scene_rsp_gauss_metrics')
            assert list(diag)==[3,6032,128] and metrics[0]==1 and metrics[1]==512
            assert c.c_uint32.in_dll(lib,'scene_rsp_context_mismatch_word').value==0x80000000
            result=dict(passed=True,native1790_to80_rejection_reproduced=True,
                        production_C_and_actual_RSP_binary=True,current_and_pending_DMA_distinct=True,
                        exact_primitive_lanes=512,native_DMA_cost_acceptance=False)
            if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps(result))
            if os.name=='nt':c.windll.kernel32.FreeLibrary(c.c_void_p(lib._handle))
            return
        trace=test()
        for position in range(1,93):test(fail=position)
        for position,offset,to_cart in trace:
            if not to_cart:test(corrupt=position)
        wait_positions=67 if gauss else 5
        for wait in range(1,wait_positions+1):test(wait_fault=wait)
        if gauss:test(gauss_fault=True)
        if a.gauss_dma:
            if not a.brr_resident:test(dma_mode=0)
            test(dma_busy_fault=True);test(dma_input_fault=True)
            test(dma_length_fault=True);test(dma_address_fault=True);test(dma_source_fault=True)
            test(cursor_busy_fault=True);test(cursor_bytes_fault=True)
            test(source_before_fault=True);test(source_after_fault=True);test(original_bad=True)
            for cursor in (0,0x1000,0x1ff8):test(original_cursor=cursor)
            test(original_skip=0x12800000)
            if a.brr_resident:test(resident_output_stall=True);test(resident_guard_fault=True)
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
        if gauss:result.update(primitive_output_samples=expected_samples,gauss_clobbered_context_restored=True,
            all64_primitive_wait_faults_safely_halted_and_restored=True,gauss_result_mutation_rejected=True)
        if a.gauss_dma:result.update(DMA_input_extent_and_alignment=True,DMA_register_addresses_and_idle_lengths_exact=True,
            DMA_busy_timeout_stops_before_context_memory_overwrite=True,DMA_corrupt_input_detected=True,
            DMA_length_or_address_restore_fault_requires_menu=True,same_image_PIO_control=True,
            DMA_fault_kind_expected_observed_and_register_index_exact=True,
            invalid_CPU_DMA_source_safely_restores_and_reports_failure=True,
            current_and_pending_DMA_distinct=True,exact8byte_no_change_cursor_DMA=True,
            DMEM_IMEM_wrap_and_skip_preserved=True,source_tail_guards_before_and_after_mutation=True,
            cursor_DMA_timeout_and_byte_fault_require_menu=True,no_RDRAM_writes=True,
            CPU_cache_writeback_and_hardware_DMA_timing_mocked=True)
        if a.brr_elf:result.update(BRR32_sample_actual_kernel=True,input_bytes=input_bytes,output_bytes=64,
            preparation_included_in_transport_metric=True,per_term_floors_saturation_double_wrap_exact=True)
        if a.brr_resident:result.update(no_RDRAM_writes=False,only_static_private64B_output_DMA_writes=True,
            same_image_PIO_control=False,
            all64_input_and_output_transfers_exact=True,output_DMA_timeout_requires_menu=True,
            output_guard_fault_detected=True,static_output_lifetime_survives_unhalted_DMA=True)
        if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
        if os.name=='nt':c.windll.kernel32.FreeLibrary(c.c_void_p(lib._handle))
if __name__=='__main__':main()
