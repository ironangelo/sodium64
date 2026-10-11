#!/usr/bin/env python3
"""Execute linked cache admission, atlas packets, DMA and object construction.

Original numeric textures/OAM only. This checks cache versions, indices,
command/source ownership and ABI; real RDP readback/timing remain required.
"""
import argparse
import json
import random
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_sub_presence import section
from test_hcomp_tlut_candidate import ShaderVM
from test_native_diag_arm import load_elf, execute as cpu_execute
from test_rsp_math_dma import ROOT, put, symbols

CACHE, MAIN, SOURCE, LISTS = 0x180000, 0x181000, 0x190000, 0x191000


def binding(cpu):
    image, syms = load_elf(cpu)
    original = image.copy()
    a = parse_macros(ROOT).name
    cpu_execute(image, syms['tmem_atlas_cpu_bind'], [0]*32, {}, syms['tmem_atlas_cpu_bind_end'])
    owner = (0xa4000000+a('OVERLAY_OBJECT_CACHE_SRC')) & 0x1fffffff
    value = int.from_bytes(bytes(image[owner+i] for i in range(4)), 'big')
    assert value == syms['rsp_object_cache_text_start'] | 1
    assert all(image[k] == v for k, v in original.items() if not owner <= k < owner+4)
    return 'immutable unreachable Mode7 padding; first terminator preserved'


def objects(build, baseline):
    a = parse_macros(ROOT).name
    _, candidate = read_text(build/'src/rsp_main.elf')
    _, control = read_text(baseline/'src/rsp_main.elf')
    _, bank = read_text(build/'src/rsp_object_cache.elf')
    syms = symbols(build/'src/rsp_main.elf')
    rng = random.Random(0x4f414d)
    cases = 0
    for size in range(8):
        for rotation in (0, 0x801f):
            for queue in (0, 4):
                for border in (0, 8):
                    initial = bytearray(section(baseline/'src/rsp_main.elf', '.data'))
                    initial[a('STAT_FLAGS')] = 0x40
                    initial[a('OBSEL')] = size << 5
                    struct.pack_into('>H', initial, a('OAMADD'), rotation)
                    put(initial, a('FB_OFFSET')+queue, border)
                    put(initial, a('OAM_PTR')+queue, SOURCE)
                    put(initial, a('CACHE_PTRS')+16, LISTS)
                    put(initial, a('OVERLAY_OBJECT_CACHE_SRC'), CACHE | 1)
                    put(initial, a('OVERLAY_MAIN_SRC'), MAIN | 1)
                    payload = bytes(rng.randrange(256) for _ in range(544))
                    owners = set(range(a('TILE_TABLE')+512, a('TILE_TABLE')+1024))
                    owners.update(range(a('OAM'), a('OAM')+544))
                    owners.update(range(a('OAM_PTR')+queue, a('OAM_PTR')+queue+4))
                    owners.update(range(a('NATIVE_DIAG_RSP_BANK'), a('NATIVE_DIAG_RSP_BANK')+2))
                    results = []
                    for code, use_overlay in ((control, False), (candidate, True)):
                        ram = bytearray([0xa5])*0x400000
                        ram[SOURCE:SOURCE+544] = payload
                        ram[CACHE:CACHE+1000] = bank
                        ram[MAIN:MAIN+1000] = candidate[0x3a8:0x790]
                        before = bytes(ram)
                        d = bytearray(initial)
                        r = [0]*32; r[29] = queue
                        vm = ShaderVM(code,d,ram,r,owners,set(range(LISTS,LISTS+2048)),7,
                                      overlays={CACHE:1,MAIN:1})
                        vm.pc = syms['hcomp_cgram_return']
                        vm.execute(syms['oam_skip'])
                        assert ram[:LISTS] == before[:LISTS] and ram[LISTS+2048:] == before[LISTS+2048:]
                        assert vm.overlay_history == ([1,1] if use_overlay else [])
                        assert not vm.captures
                        assert struct.unpack_from('>I',d,a('OAM_PTR')+queue)[0] == SOURCE+544
                        results.append((bytes(ram[LISTS:LISTS+2048]),bytes(d[a('OAM'):a('OAM')+544])))
                    assert results[0] == results[1], ('object construction changed',size,rotation,queue,border)
                    cases += 1
    return cases


def textures(build, fault=None, legacy=False):
    a = parse_macros(ROOT).name
    _, code = read_text(build/'src/rsp_main.elf')
    syms = symbols(build/'src/rsp_main.elf')
    coordinate = 'tmem_coord_legacy' in syms
    assert not legacy or coordinate
    shift=struct.unpack_from('>I',code,syms['tmem_atlas_group_shift'])[0]
    assert shift>>26==0 and shift&63==2 and shift>>16&31==30 and shift>>11&31==9
    group_bits=shift>>6&31
    assert 0<=group_bits<=5
    group_mask=(1<<group_bits)-1;group_bytes=64<<group_bits
    d = bytearray(section(build/'src/rsp_main.elf','.data'))
    d[a('HCOMP_EFFECTIVE_TS')]=1 if legacy else 0
    base = 0x100000
    put(d,a('CACHE_PTRS'),base)
    ram = bytearray([0xa5])*0x400000
    rng = random.Random(0x544d454d)
    ram[base:base+0x40000] = bytes(rng.randrange(256) for _ in range(0x40000))
    before = bytes(ram)
    owners = set(range(64)) | set(range(a('CHAR_DATA'),a('CHAR_DATA')+64))
    owners.update(range(a('RDP_TILE')+24,a('RDP_TILE')+40))
    if legacy:owners.update(range(a('RDP_TILE')+4,a('RDP_TILE')+8))
    owners.update(range(a('TILE_TABLE'),a('TILE_TABLE')+1024))
    r = [0]*32; r[3]=0xffff
    vm = ShaderVM(code,d,ram,r,owners,set(range(base,base+0x40000)),9,overlays={})
    if fault=='stale':
        put(vm.code,syms['draw_tile'],0) # Decoded RAM differs from the live group.
    elif fault=='source':
        put(vm.code,syms['rdp_texture_retire'],0x08000000 | ((0xa4001000+syms['dma_write_owned'])>>2 & 0x3ffffff))
        put(vm.code,syms['rdp_texture_retire']+4,0)
    elif fault=='eligibility':
        assert coordinate and legacy
        put(vm.code,syms['tmem_atlas_draw']+4,0)
    elif fault=='coordinates':
        assert coordinate and not legacy
        put(vm.code,syms['tmem_coord_store'],0)
    elif fault=='mask':
        assert coordinate and group_bits==3 and not legacy
        put(vm.code,syms['tmem_coord_tile_mask'],0)
    elif fault=='restore':
        assert coordinate and group_bits==3
        put(vm.code,syms['tmem_atlas_restore']+20,0)
    tmem = bytearray((i*13)&255 for i in range(4096));palette = bytes(tmem[2048:])
    last_packet = 0;draws=loads=pixels=misses=0;last_char=None;tile_mask=31
    def consume(char,bg,rect):
        nonlocal last_packet,loads,draws,pixels,last_char,tile_mask
        packets=vm.captures[last_packet:];last_packet=len(vm.captures)
        assert len(packets)==1
        packet=packets[0]
        load_bytes=0
        atlas_packet_bytes=(56 if group_bits==3 else 48) if coordinate else 64
        if len(packet)==atlas_packet_bytes and not legacy or legacy and len(packet)==40:
            w=struct.unpack('>'+str(len(packet)//8)+'Q',packet)
            if legacy:
                assert w[0]>>32==0x3d500003 and w[1]==0x2600000000000000
                assert w[2]==0x330000000101f800
                source=w[0]&0x1fffffff;load_bytes=64
                assert source==base+bg*65536+char*64
            else:
                assert w[0]==0x2800000000000000
                if not coordinate:assert w[4]==w[0]
                idx=2 if coordinate and group_bits==3 else 1
                if idx==2:
                    assert w[1]==0x3548020002058150,'wrong atlas tile mask'
                    tile_mask=(1<<((w[1]>>14)&15))-1
                assert w[idx]>>32==0x3d500003 and w[idx+1]==0x2600000000000000
                assert w[idx+2]==(0x3300000001000800 | (((group_bytes//2)-1)<<12))
                source=w[idx]&0x1fffffff;load_bytes=group_bytes
                assert source==base+bg*65536+(char&~group_mask)*64
            data=ram[source:source+load_bytes]
            for i,value in enumerate(data):tmem[i^((i//8&1)*4)]=value
            vm.lease=(source,source+load_bytes);vm.lease_original=bytes(data)
            vm.source_left=vm.delay;vm.source_fenced=False
            loads+=1
        elif not coordinate and len(packet)==32:
            assert len(packet)==32
            w=struct.unpack('>4Q',packet)
            assert w[0]==0x2800000000000000
        else:
            assert len(packet)==16, ('unadmitted atlas protocol',len(packet),legacy)
            if not coordinate or legacy:assert char==last_char
        if not coordinate and len(packet)>16:
            assert w[-3]==((0x35480200 | ((char&group_mask)*8))<<32 | 0x02054150)
        last_char=char
        expected_rect=bytearray(rect)
        if coordinate and not legacy:
            t=struct.unpack_from('>H',rect,10)[0]+(char&group_mask)*256
            struct.pack_into('>H',expected_rect,10,t)
        assert packet[-16:]==expected_rect, 'wrong atlas rectangle'
        assert tmem[2048:]==palette
        if coordinate and group_bits==2:
            assert all(packet[i] not in (0x35,0x32) for i in range(0,len(packet)-16,8)), 'render tile changed'
        params=struct.unpack_from('>4h',packet,len(packet)-8)
        ss,tt,dx,dy=params
        offset=0 if coordinate or legacy else (char&group_mask)*64
        actual=bytes(tmem[offset+(((tt*32+dy*y)>>10)&tile_mask)*8+(((ss*32+dx*x)>>10)&31)^((((tt*32+dy*y)>>10)&1)*4)] for y in range(8) for x in range(8))
        texture=ram[base+bg*65536+char*64:base+bg*65536+(char+1)*64]
        expected=bytes(texture[(7-y if dy<0 else y)*8+(7-x if dx<0 else x)] for y in range(8) for x in range(8))
        assert actual==expected, ('wrong texture/version in TMEM',char,bg)
        draws+=1;pixels+=64
    for bg in range(4):
        r[18]=bg*2;r[3]=0xffff
        for n,char in enumerate(list(range(64))+[rng.randrange(1024) for _ in range(64)]+list(range(992,1024))):
            pal=n%8;entry=char | pal<<10
            flip=n%4
            rect=struct.pack('>4I',0x24100100+n*4,0x02030020+n*4,
                             (0xe00000 if flip&1 else 0)|(0xe0 if flip&2 else 0),
                             (0xfc000000 if flip&1 else 0x04000000)|(0xfc00 if flip&2 else 0x0400))
            d[a('RDP_TILE')+24:a('RDP_TILE')+40]=rect
            d[a('TILE_TABLE')+char]=(pal<<5)|1
            r[30]=char;r[14]=entry;r[25]=4
            vm.pc=syms['check_cache'];vm.branch=None
            vm.execute(syms['finish_tile'])
            consume(char,bg,rect)
            if n%3==0:
                vm.pc=syms['check_cache'];vm.branch=None
                vm.execute(syms['finish_tile'])
                assert len(vm.captures[-1])==16
                consume(char,bg,rect)
            if n%17==0:
                d[a('TILE_TABLE')+char]=255
                before_packets=len(vm.captures)
                vm.pc=syms['check_cache'];vm.branch=None
                vm.execute(syms['finish_tile'])
                assert len(vm.captures)==before_packets, 'empty texture was drawn'
            if n%11==0:
                # A cache invalidation must reach decode even if this atlas
                # group is already live. Do not fake a cache hit after a write.
                d[a('TILE_TABLE')+char]=0 if n%22==0 else (((pal+1)&7)<<5)|1
                put(d,a('VRAM_ADDRS'),SOURCE)
                r[11]=0;r[25]=4
                vm.pc=syms['check_cache'];vm.branch=None
                vm.execute(syms['decode_tile4'])
                misses+=1
                # Numeric decoded texture materialization uses the actual
                # resident source fence/DMA, retaining a pending group lease.
                fresh=bytes((n*19+i*7)&255 for i in range(64));d[:64]=fresh
                r[4]=0;r[5]=base+bg*65536+char*64;r[6]=63;r[31]=0xabc
                vm.pc=0xf08;vm.branch=None;vm.execute(0xabc)
                assert vm.lease is None
                r[5]=base+bg*65536+char*64
                vm.pc=syms['draw_tile'];vm.branch=None;vm.execute(syms['finish_tile'])
                # An immutable SyncFull receipt precedes the refreshed packet.
                assert vm.captures[last_packet]==bytes.fromhex('2900000000000000')
                last_packet+=1
                consume(char,bg,rect)
        if coordinate:
            vm.pc=syms['bg_restore_scissor'];vm.branch=None
            vm.execute(syms['bg_restore_scissor_end'])
        else:
            r[31]=0xabc;vm.pc=syms['tmem_atlas_restore'];vm.branch=None;vm.execute(0xabc)
        packet=vm.captures[-1]
        if coordinate:
            if group_bits==3:
                assert vm.captures[-3:]==[
                    bytes(d[a('RDP_WINDOW'):a('RDP_WINDOW')+8]),
                    bytes.fromhex('3548020002054150'),
                    bytes(d[a('RDP_FILL')+8:a('RDP_FILL')+16])], 'original tile mask not restored'
                tile_mask=31
            else:assert packet==d[a('RDP_FILL')+8:a('RDP_FILL')+16]
        else:
            assert packet[:16]==bytes.fromhex('28000000000000003548020002054150')
            assert packet[16:]==d[a('RDP_FILL')+8:a('RDP_FILL')+16]
        last_packet=len(vm.captures)
    assert ram[:base]==before[:base] and ram[base+0x40000:]==before[base+0x40000:]
    return dict(group_bits=group_bits,draws=draws,pixels=pixels,atlas_loads=loads,cache_invalidations=misses,
                coordinate_atlas=coordinate,legacy_visible_sub=legacy,all_four_mirrors=True,
                palette_bytes_unchanged=True,source_fences_executed=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('build',type=Path);ap.add_argument('--baseline',type=Path,required=True)
    ap.add_argument('--cpu',type=Path,required=True);ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    for name in ('rsp_hcomp','rsp_hcomp_math','rsp_hcomp_rdp','rsp_hcomp_fixed_window','rsp_hcomp_rdp_fixed','rsp_hcomp_setup','rsp_hcomp_tlut','rsp_mode7','rsp_mode7_window'):
        assert read_text(args.build/'src'/f'{name}.elf')[1]==read_text(args.baseline/'src'/f'{name}.elf')[1],name
    old,new=symbols(args.baseline/'src/rsp_main.elf'),symbols(args.build/'src/rsp_main.elf')
    for name in ('draw_bg','draw_obj','oam_skip','finish_tile','draw_tile','skip_decode','skip_upload','rdp_send','ret_jump'):
        assert old[name]==new[name],name
    result=dict(passed=True,binding=binding(args.cpu),object_cases=objects(args.build,args.baseline),
                textures=textures(args.build),old_banks_byte_exact=9,hardware_fps_claim=False)
    if 'tmem_coord_legacy' in new:result['legacy_textures']=textures(args.build,legacy=True)
    for fault,message in (('stale','wrong texture/version in TMEM'),('source','source reused before reader retired')):
        try:textures(args.build,fault=fault)
        except AssertionError as error:assert message in str(error),str(error)
        else:raise AssertionError('accepted '+fault+' mutation')
    result['negative_guards']=2
    if 'tmem_coord_legacy' in new:
        for fault,legacy,message in (('eligibility',True,'unadmitted atlas protocol'),
                                     ('coordinates',False,'wrong atlas rectangle')):
            try:textures(args.build,fault=fault,legacy=legacy)
            except AssertionError as error:assert message in str(error),str(error)
            else:raise AssertionError('accepted '+fault+' mutation')
            result['negative_guards']+=1
        if result['textures']['group_bits']==3:
            for fault,message in (('mask','wrong atlas tile mask'),('restore','original tile mask not restored')):
                try:textures(args.build,fault=fault)
                except AssertionError as error:assert message in str(error),str(error)
                else:raise AssertionError('accepted '+fault+' mutation')
                result['negative_guards']+=1
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
