#!/usr/bin/env python3
"""Execute a linked TLUT shader; numeric palettes only, never RDP timing.

This guard requires the candidate ELF. It does not relabel the preparation
oracle or a model-generated palette as an executed production transform.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_packed_math import execute as kernel_execute, reference, rgba, seeds
from test_hcomp_sub_presence import section
from test_hcomp_tlut_transform import (ROOM, TlutVM, consume_palette,
                                      expected_backdrop_rgba, expected_tlut_tables,
                                      tlut_image)
from test_native_diag_arm import load_elf
from test_rsp_math_dma import PHASE_BANK, ROOT, put, symbols

TLUT_BANK, MAIN_BANK = 0x190000, 0x1a0000


class ShaderVM(TlutVM):
    """Retired overlay/stub DMA and palette readers share real RDRAM leases."""
    def __init__(self,*args,overlays,**kwargs):
        super().__init__(*args,**kwargs)
        self.overlays = overlays
        self.overlay_history = []
        self.stub_writes = []

    def queue_dma(self,write,length):
        stub = bool(self.spaddr&0x1000) and self.spaddr&0xfff==0
        if stub:
            assert not write and ((length&0xfff)|7)+1==56
            assert not 0<=self.pc<56, 'executing binder while its instructions are overwritten'
            # This prefix is retired while the shader slot keeps executing.
            # SIG1 still correctly describes bank5; only the overlay slot
            # replacement itself must expose the loading identity0.
            enabled = self.signal_profile
            self.signal_profile = False
            try: super().queue_dma(write,length)
            finally: self.signal_profile = enabled
        else: super().queue_dma(write,length)

    def poll_dma(self):
        if self.dma is None: return 0
        pending = self.dma
        if not pending['imem']: return super().poll_dma()
        pending['polls'] -= 1
        if pending['polls']: return 1
        sp,ram,size = pending['sp'],pending['ram'],pending['size']
        if sp==0:
            assert size==56, 'startup binder DMA must account for 8-byte rounding'
            self.stub_writes.append(bytes(self.ram[ram:ram+size]))
        else:
            assert sp==0x3a8 and size==1000, 'unknown overlay DMA owner'
            assert ram in self.overlays, ('unknown linked overlay',hex(ram))
            bank = self.overlays[ram]
            if self.signal_profile:
                assert self.sp_status&(7<<11)==0, 'bank identity visible while IMEM overwritten'
                self.completed_overlay_bank = bank
            self.overlay_history.append(bank)
            self.phase_loaded = bank==3
        self.code[sp:sp+size] = self.ram[ram:ram+size]
        self.transfers.append({k:v for k,v in pending.items() if k!='polls'})
        self.dma = None
        return 0


def link_images(main_path,tlut_path,phase_path):
    mb,mc = read_text(main_path)
    tb,tc = read_text(tlut_path)
    pb,pc = read_text(phase_path)
    assert mb&0xfff==0 and len(mc)==4096
    assert tb&0xfff==pb&0xfff==0x3a8 and len(tc)==len(pc)==1000
    ts,ps = symbols(tlut_path),symbols(phase_path)
    assert ts['hcomp_tlut_generate']==0x3b0
    assert ts['hcomp_tlut_bind']==0x3b8 and ts['hcomp_tlut_restore']==0x3c0
    code = bytearray(mc)
    code[0x3a8:0x790] = tc
    return code,section(main_path,'.data'),mc,tc,pc,ts,ps


def kernel_batch(code,symbols,colors,operands,subtract,half):
    vectors = seeds()
    vectors[0],vectors[1] = list(map(rgba,colors)),list(map(rgba,operands))
    vectors[7] = [0xffff]*8
    vectors[13] = [0xffff if half else 0]*8
    vectors[16][2:4] = [0x0800,2]
    vectors[19][:3] = [0x0421,0x8420,0x7bde]
    regs = [0]*32
    regs[3] = 0x80 if subtract else 0
    _,out,steps = kernel_execute(code,0x3a8,symbols['hcomp_tlut_kernel'],
                                 symbols['hcomp_tlut_kernel_end'],regs,vectors)
    want = [reference(a,b,subtract,half)&0xfffe for a,b in zip(colors,operands)]
    assert out[0]==want, ('linked TLUT packed kernel',colors,operands,subtract,half,out[0],want)
    return steps


def exhaustive_kernel(images):
    code,symbols = images[3],images[5]
    cases,pixels,counts = 0,0,set()
    for subtract in (False,True):
        for half in (False,True):
            for fixed in (0,1,0x4210,0x7fff,None):
                for start in range(0,32768,8):
                    colors = list(range(start,start+8))
                    operands = [fixed]*8 if fixed is not None else [((a*977)^0x4210)&0x7fff for a in colors]
                    counts.add(kernel_batch(code,symbols,colors,operands,subtract,half))
                    cases += 1;pixels += 8
    changed = bytearray(code)
    put(changed,symbols['hcomp_tlut_kernel']-0x3a8,0)
    try: kernel_batch(changed,symbols,list(range(1,9)),[0]*8,False,False)
    except AssertionError as e:
        assert 'linked TLUT packed kernel' in str(e), str(e)
    else: raise AssertionError('linked TLUT guard accepted skipped source conversion')
    return dict(cases=cases,pixels=pixels,distinct_input_colors=32768,
                fixed_operands=[0,1,0x4210,0x7fff,'lane_mixed'],
                instruction_counts=sorted(counts),compiled_fault_rejected=True)


def generation(images,palette,policy,slot,delay,lease_table=None,fault=None,
               admitted=True,row_variation=None,diag_limit=0,return_vm=False,windows=None):
    code,initial,main_code,tlut_code,phase_code,ts,ps = images
    addr = parse_macros(ROOT).name
    d = bytearray(initial)
    workspace = addr('HCOMP_WINNER_ARENA')&0x1fffffff
    source = addr('PALETTE_QUEUE1' if slot==0 else 'PALETTE_QUEUE2')&0x1fffffff
    rowqueue = addr('HCOMP_ROW_FIXED_QUEUE1')&0x1fffffff
    ram = bytearray([0xa5])*0x400000
    ram[source:source+2048] = tlut_image(palette)
    ram[TLUT_BANK:TLUT_BANK+1000] = tlut_code
    ram[MAIN_BANK:MAIN_BANK+1000] = main_code[0x3a8:0x790]
    ram[PHASE_BANK:PHASE_BANK+1000] = phase_code
    for y in range(256): struct.pack_into('>H',ram,rowqueue+y*2,policy['fixed'])
    if row_variation is not None:
        struct.pack_into('>H',ram,rowqueue+row_variation*2,policy['fixed']^0x0800)
    for name,value in (('CGWSEL',policy['cgwsel']),('CGADSUB',policy['cgadsub']),
                       ('TS',policy['ts']),('TM',policy.get('tm',0x16)),('BG_MODE',policy.get('bgmode',8))):
        d[addr(name)] = value
    if windows is not None:
        selector,logic,edges=windows
        d[addr('WOBJSEL')]=selector<<4
        d[addr('WOBJLOG')]=logic<<2
        d[addr('WHX'):addr('WHX')+4]=bytes(edges)
    put(d,addr('HCOMP_ROW_FIXED_SRC'),rowqueue)
    put(d,addr('OVERLAY_HCOMP_SRC'),PHASE_BANK|3)
    put(d,addr('OVERLAY_MAIN_SRC'),MAIN_BANK|1)
    put(d,0xf14,TLUT_BANK|5)
    put(d,addr('HCOMP_DIAG_COMPOSE_LIMIT'),diag_limit)
    put(d,addr('HCOMP_BAND_RAW'),0)
    struct.pack_into('>H',d,addr('SUB_COLOR'),policy['fixed'])
    struct.pack_into('>H',d,addr('MAIN_COLOR'),policy['main'])
    d[0xf13] = 0
    before_ram = bytes(ram)
    before_dmem = bytes(d)
    regs = [0x13500000+i for i in range(32)]
    regs[0],regs[26],regs[27],regs[29] = 0,0,policy.get('rows',224),slot
    owners = set(range(addr('TILE_TABLE'),addr('TILE_TABLE')+1024))
    owners.update(range(addr('SCRN_DATA'),addr('SCRN_DATA')+512))
    owners.update(range(addr('MAIN_COLOR'),addr('MAIN_COLOR')+2))
    owners.update(range(0xf13,0xf14))
    owners.update(range(addr('HCOMP_BAND_RAW'),addr('HCOMP_BAND_RAW')+4))
    owners.update(range(addr('HCOMP_OBJ_ADAPTIVE'),addr('HCOMP_OBJ_ADAPTIVE')+4))
    owners.update(range(addr('HCOMP_FAST_END'),addr('HCOMP_FAST_END')+4))
    owners.update(range(addr('HCOMP_EFFECTIVE_TS'),addr('HCOMP_EFFECTIVE_TS')+1))
    owners.update(range(addr('NATIVE_DIAG_RSP_BANK'),addr('NATIVE_DIAG_RSP_BANK')+2))
    if windows is not None:
        owners.update(range(addr('WIN_BOUNDS'),addr('WIN_BOUNDS')+6))
        owners.add(addr('WIN_COUNT'))
    lease = None if lease_table is None else (workspace+lease_table*2048,workspace+(lease_table+1)*2048)
    vm = ShaderVM(code,d,ram,regs,owners,set(range(workspace,workspace+6144)),delay,
                  lease=lease,overlays={PHASE_BANK:3,MAIN_BANK:1,TLUT_BANK:5})
    for register in range(23,31):
        vm.v[register] = [((register*977)^(lane*0x8421))&0xffff for lane in range(8)]
    protected_vectors = [lanes[:] for lanes in vm.v[23:32]]
    vm.pc = ts['hcomp_tlut_generate']
    if fault:
        assert fault['pc']>=0x3a8
        put(vm.code,fault['pc'],fault['word'])
    steps = vm.execute(ps['hcomp_policy_return'],require_phase=True,max_steps=250000)
    assert vm.dma is None and vm.pending_fetch is None
    assert regs[26:28]==[0,policy.get('rows',224)] and regs[29]==slot, 'shader changed span/queue owner'
    assert vm.v[23:32]==protected_vectors, 'shader changed shared renderer vector constants'
    if not admitted:
        assert struct.unpack_from('>I',d,addr('HCOMP_BAND_RAW'))[0]==0
        assert not vm.stub_writes, 'rejected policy installed startup binder'
        assert bytes(ram)==before_ram and d[addr('MAIN_COLOR'):addr('MAIN_COLOR')+2]==before_dmem[addr('MAIN_COLOR'):addr('MAIN_COLOR')+2]
        assert all(d[i]==before_dmem[i] for i in range(4096) if i not in owners)
        return dict(admitted=False,dma_starts=len(vm.transfers),overlay_banks=vm.overlay_history)
    assert vm.stub_writes and vm.code[56:64]==main_code[56:64], 'binder DMA changed startup tail/draw_frame3C'
    assert struct.unpack_from('>I',d,addr('HCOMP_BAND_RAW'))[0]==3, 'exact shader policy not admitted'
    assert struct.unpack_from('>H',d,addr('MAIN_COLOR'))[0]&0xfffe==expected_backdrop_rgba(policy)&0xfffe, 'backdrop incorrectly derived from texture index0'
    expected = b''.join(expected_tlut_tables(palette,policy))
    assert ram[workspace:workspace+6144]==expected, 'linked TLUT transform/alpha/quadruple/OBJ split mismatch'
    assert ram[:workspace]==before_ram[:workspace] and ram[workspace+6144:]==before_ram[workspace+6144:], 'shader changed external RDRAM owner'
    assert all(d[i]==before_dmem[i] for i in range(4096) if i not in owners), 'shader changed external DMEM owner'
    if lease is not None:
        assert vm.lease is None and vm.lease_capture==vm.lease_original, 'shader omitted source retirement'
    result = dict(instructions=steps,dma_starts=len(vm.transfers),
                  overlay_banks=vm.overlay_history,source_retired=lease is not None)
    return (result,vm) if return_vm else result


def packet_words(packets):
    return [struct.unpack_from('>II',packet,i) for packet in packets for i in range(0,len(packet),8)]


def assert_binding_stream(packets,source,initial):
    addr = parse_macros(ROOT).name
    words = packet_words(packets)
    texture = (0x3d100000,source)
    assert words.count(texture)==1, ('wrong TLUT class/source bound',words,texture)
    at = words.index(texture)
    assert at and words[at-1]==(0x27000000,0), 'TLUT reload lacks preceding PipeSync'
    expected = [texture,struct.unpack_from('>II',initial,addr('RDP_FRAME')+16),
                struct.unpack_from('>II',initial,addr('RDP_FILL'))]
    assert words[at:at+3]==expected, 'TLUT binding load command sequence changed'
    assert not any(word[0]>>24 in (0x24,0x0a,0x36) for word in words), 'palette bind drew pixels before pass restart'


def class_bindings(images,main_path,palette,policy,slot,windows=None):
    addr = parse_macros(ROOT).name
    _,vm = generation(images,palette,policy,slot,7,return_vm=True,windows=windows)
    ms = symbols(main_path)
    initial = images[1]
    vm.owners.update(range(addr('RDP_FRAME')+12,addr('RDP_FRAME')+16))
    vm.dmem[addr('HCOMP_SCREEN')] = 1
    commands = [addr('HCOMP_PROOF_RDP_CMDS')+24]+[
        addr('HCOMP_PROOF_BG_DEPTH_CMDS')+i*8 for i in range(4)]+[
        addr('HCOMP_OBJ_DEPTH_CMDS')+i*8 for i in range(2)]
    # Backdrop retains the separately generated primitive color. BG2 uses
    # the fully shaded upper CI8 indices, whereas OBJ uses its mixed table.
    current = 0
    changed,unchanged = 0,0
    for kind in (0,2,2,3,3,6,5,2,1,6):
        cg = policy['cgadsub']
        eligible = bool((0x20,1,2,4,8,0,0x10)[kind]&cg)
        wanted = 0 if kind==0 else 3 if kind in (5,6) else 2 if eligible else 1
        command = commands[kind]
        vm.r[4],vm.r[5],vm.r[19],vm.r[31] = command,command+8,0x93,0x790
        vm.r[9] = 0x90000800^(cg<<16)
        caller_t1 = vm.r[9]
        before = len(vm.captures)
        before_overlays = len(vm.overlay_history)
        vm.pc = ms['hcomp_eligibility_depth_send']
        will_bind = wanted and wanted!=current
        vm.execute(ms['next_layer'] if will_bind else 0x790,max_steps=10000)
        assert vm.r[9]==caller_t1, 'palette-class hook clobbered cached OAM t1'
        packets = vm.captures[before:]
        if will_bind:
            source = addr('HCOMP_WINNER_ARENA')+(wanted-1)*2048
            assert_binding_stream(packets,source,initial)
            assert vm.r[19]==0x92, 'palette class reload did not restart untouched Main pass'
            assert vm.overlay_history[before_overlays:]==[5,1]
            assert vm.dmem[0xf13]==0x80|wanted
            current = wanted;changed += 1
        else:
            assert not packets and len(vm.overlay_history)==before_overlays, 'cached/backdrop class reloaded TLUT'
            assert vm.r[19]==0x93
            unchanged += 1
    # Load Phase through the actual resident overlay loader, then execute
    # its band-end restoration chain through TLUT and back into Phase.
    vm.r[5],vm.r[25] = PHASE_BANK|3,0x1000|images[6]['hcomp_band_done']
    vm.pc = ms['overlay_load_slot']
    vm.execute(images[6]['hcomp_band_done'],require_phase=True,max_steps=10000)
    before = len(vm.captures)
    vm.execute(images[6]['hcomp_band_palette_restored'],require_phase=True,max_steps=10000)
    source = addr('PALETTE_QUEUE1' if slot==0 else 'PALETTE_QUEUE2')
    assert_binding_stream(vm.captures[before:],source,initial)
    assert vm.dmem[0xf13]==0, 'general successor inherited transformed class'
    assert struct.unpack_from('>I',vm.dmem,addr('RDP_FRAME')+12)[0]&0x1fffffff==source&0x1fffffff
    before = len(vm.overlay_history)
    vm.pc = images[6]['hcomp_band_done']
    vm.execute(images[6]['hcomp_band_palette_restored'],require_phase=True,max_steps=1000)
    assert len(vm.overlay_history)==before, 'restore reentered recursively after class cleared'
    return dict(changed_classes=changed,cached_or_backdrop=unchanged,
                compiled_restore_chain=True,original_palette_restored=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cpu',type=Path);ap.add_argument('main',type=Path)
    ap.add_argument('tlut',type=Path);ap.add_argument('phase',type=Path)
    ap.add_argument('--output',type=Path)
    a = ap.parse_args()
    images = link_images(a.main,a.tlut,a.phase)
    kernel = exhaustive_kernel(images)
    image,cpu_symbols = load_elf(a.cpu)
    results = []
    for brightness in (0,2,8,16):
        for slot in (0,4):
            palette = consume_palette(image,cpu_symbols,brightness,slot)
            for source in (0,2):
                for mode in (0x33,0x73,0xb3,0xf3):
                    policy = dict(ROOM,cgwsel=source,cgadsub=mode,main=0x4cd3)
                    results.append(generation(images,palette,policy,slot,2))
    palette = [0]+[(i*977&0x7fff)<<1|1 for i in range(1,256)]
    for table in range(3):
        results.append(generation(images,palette,dict(ROOM,main=0xf801),0,7,table))
    # The current absent-Sub Math consumes section SUB_COLOR, even when the
    # row-fixed queue differs; only actual fixed selection observes that queue.
    results.append(generation(images,palette,dict(ROOM,main=0x4cd2),0,2,row_variation=111))
    rejects = []
    for cgwsel in (1,3,0x10,0x20,0x40,0x80):
        rejects.append(generation(images,palette,dict(ROOM,cgwsel=cgwsel,main=0xf801),0,2,admitted=False))
    rejects.append(generation(images,palette,dict(ROOM,ts=1,main=0xf801),0,2,admitted=False))
    rejects.append(generation(images,palette,dict(ROOM,cgwsel=0,main=0xf801),0,2,admitted=False,row_variation=111))
    rejects.append(generation(images,palette,dict(ROOM,main=0xf801),0,2,admitted=False,diag_limit=8))
    bindings = [class_bindings(images,a.main,palette,dict(ROOM,main=0x4cd2),slot) for slot in (0,4)]
    report = dict(passed=True,candidate_tlut_transform_executed=True,
                  compiled_generation_cases=len(results),compiled_rejected_policies=len(rejects),painter_stream_executed=False,
                  fixture_abi_version=1,scope='linked_tlut_generation_with_guarded_ownership',
                  compiled_kernel=kernel,
                  compiled_class_binding_cases=bindings,
                  native_timing_authority=False,rdp_rasterization_authority=False,
                  commercial_data=False,results=results,
                  elf_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (a.cpu,a.main,a.tlut,a.phase)})
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(report,indent=2)+'\n')
    print('HCOMP_TLUT_GENERATION PASS',json.dumps({k:v for k,v in report.items() if k not in ('results','elf_sha256')}))


if __name__=='__main__': main()
