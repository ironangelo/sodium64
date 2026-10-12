#!/usr/bin/env python3
"""Execute the linked four-slot cache against independent numeric textures.

Quick preflight: admission, collisions, cache epochs, mirrors, asynchronous
source leases and fixed ABI. This model makes no native speed/RDP timing claim.
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
from test_rsp_math_dma import ROOT, put, symbols


def run(build, fault=None):
    a = parse_macros(ROOT).name
    _, code = read_text(build/'src/rsp_main.elf')
    syms = symbols(build/'src/rsp_main.elf')
    d = bytearray(section(build/'src/rsp_main.elf', '.data'))
    base, source = 0x100000, 0x190000
    put(d, a('CACHE_PTRS'), base)
    put(d, a('VRAM_ADDRS'), source)
    ram = bytearray([0xa5])*0x400000
    rng = random.Random(0x52534d36)
    ram[base:base+0x40000] = bytes(rng.randrange(256) for _ in range(0x40000))
    before = bytes(ram)
    owners = set(range(64)) | set(range(a('CHAR_DATA'), a('CHAR_DATA')+64))
    owners.update(range(a('TILE_TABLE'), a('TILE_TABLE')+1024))
    owners.update(range(a('RDP_TILE')+24, a('RDP_TILE')+40))
    r = [0]*32
    vm = ShaderVM(code, d, ram, r, owners, set(range(base, base+0x40000)), 9, overlays={})
    if fault == 'invalidate': put(vm.code, syms['draw_tile'], 0)
    if fault == 'coordinates': put(vm.code, syms['tmem_resident_coord_store'], 0)
    if fault == 'restore': put(vm.code, syms['tmem_atlas_restore']+20, 0)
    tmem = bytearray((i*13)&255 for i in range(4096))
    palette = bytes(tmem[2048:])
    last_packet = draws = loads = hits = refreshes = 0
    tile1 = 0

    def consume(char, bg, rect):
        nonlocal last_packet, draws, loads, hits, tile1
        packets = vm.captures[last_packet:]; last_packet = len(vm.captures)
        assert len(packets) == 1
        packet = packets[0]
        assert len(packet) in (16, 56), len(packet)
        if len(packet) == 56:
            w = struct.unpack('>7Q', packet)
            assert w[0] == 0x2800000000000000
            assert w[1] == ((0x35500000 | ((char&3)*8))<<32 | 0x01054150)
            tile1 = (w[1]>>32 & 511)*8
            assert w[2]>>32 == 0x3d500003
            assert w[3] == 0x2600000000000000 and w[4] == 0x330000000101f800
            addr = w[2] & 0x1fffffff
            assert addr == base+bg*65536+char*64
            data = bytes(ram[addr:addr+64])
            for i, value in enumerate(data): tmem[tile1+(i^((i//8&1)*4))] = value
            vm.lease=(addr,addr+64); vm.lease_original=data
            vm.source_left=vm.delay; vm.source_fenced=False
            loads += 1
        else: hits += 1
        expected_rect = bytearray(rect)
        struct.pack_into('>H', expected_rect, 10,
                         struct.unpack_from('>H', rect, 10)[0]+(char&3)*256)
        assert packet[-16:] == expected_rect, 'wrong resident rectangle'
        ss,tt,dx,dy = struct.unpack_from('>4h', packet, len(packet)-8)
        actual = bytes(tmem[((((tt*32+dy*y)>>10)&31)*8+
                             (((ss*32+dx*x)>>10)&31)) ^ ((((tt*32+dy*y)>>10)&1)*4)]
                       for y in range(8) for x in range(8))
        texture = ram[base+bg*65536+char*64:base+bg*65536+(char+1)*64]
        expected = bytes(texture[(7-y if dy<0 else y)*8+(7-x if dx<0 else x)]
                         for y in range(8) for x in range(8))
        assert actual == expected, ('wrong texture/version in TMEM', char, bg)
        assert tmem[2048:] == palette
        draws += 1

    for bg in range(4):
        r[18] = bg*2; r[3] = 0xffff
        # Repeated working sets, arbitrary collisions and the highest indices.
        sequence = list(range(8))*4 + [rng.randrange(1024) for _ in range(48)] + list(range(1020,1024))*3
        for n, char in enumerate(sequence):
            pal = n%8; entry = char | pal<<10; flip = n%4
            rect = struct.pack('>4I', 0x24100100+n*4, 0x02030020+n*4,
                               (0xe00000 if flip&1 else 0)|(0xe0 if flip&2 else 0),
                               (0xfc000000 if flip&1 else 0x04000000)|(0xfc00 if flip&2 else 0x0400))
            d[a('RDP_TILE')+24:a('RDP_TILE')+40] = rect
            d[a('TILE_TABLE')+char] = (pal<<5)|1
            r[30]=char; r[14]=entry; r[25]=4
            for repeat in range(2):
                vm.pc=syms['check_cache']; vm.branch=None; vm.execute(syms['finish_tile'])
                consume(char, bg, rect)
                if repeat: assert len(vm.captures[-1]) == 16, 'resident repeat reloads'
            if n%11 == 0:
                # Palette/version miss must decode and invalidate all residency.
                d[a('TILE_TABLE')+char] = (((pal+1)&7)<<5)|1
                r[11]=0; r[25]=4
                vm.pc=syms['check_cache']; vm.branch=None; vm.execute(syms['decode_tile4'])
                d[:64] = bytes((n*19+i*7)&255 for i in range(64))
                r[4]=0; r[5]=base+bg*65536+char*64; r[6]=63; r[31]=0xabc
                vm.pc=0xf08; vm.branch=None; vm.execute(0xabc)
                assert vm.lease is None
                assert vm.captures[last_packet] == bytes.fromhex('2900000000000000')
                last_packet += 1
                r[5]=base+bg*65536+char*64
                vm.pc=syms['draw_tile']; vm.branch=None; vm.execute(syms['finish_tile'])
                consume(char, bg, rect); refreshes += 1
            if n%17 == 0:
                d[a('TILE_TABLE')+char] = 255
                previous=len(vm.captures)
                vm.pc=syms['check_cache']; vm.branch=None; vm.execute(syms['finish_tile'])
                assert len(vm.captures) == previous, 'empty tile drawn'
        vm.pc=syms['bg_restore_scissor']; vm.branch=None
        vm.execute(syms['bg_restore_scissor_end'])
        assert vm.captures[-3:] == [bytes(d[a('RDP_WINDOW'):a('RDP_WINDOW')+8]),
                                  bytes.fromhex('3550000001054150'),
                                  bytes(d[a('RDP_FILL')+8:a('RDP_FILL')+16])], 'load tile not restored'
        last_packet=len(vm.captures)
    assert ram[:base] == before[:base] and ram[base+0x40000:] == before[base+0x40000:]
    return dict(draws=draws,pixels=draws*64,loads=loads,hits=hits,
                cache_refreshes=refreshes,palette_unchanged=True,all_four_mirrors=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('build',type=Path); ap.add_argument('--baseline',type=Path,required=True)
    args=ap.parse_args()
    new,old = symbols(args.build/'src/rsp_main.elf'), symbols(args.baseline/'src/rsp_main.elf')
    for name in ('draw_bg','draw_obj','oam_skip','finish_tile','draw_tile','skip_decode','skip_upload','rdp_send','ret_jump'):
        assert new[name] == old[name], name
    for name in ('rsp_hcomp','rsp_hcomp_math','rsp_hcomp_rdp','rsp_hcomp_fixed_window','rsp_hcomp_rdp_fixed',
                 'rsp_hcomp_setup','rsp_hcomp_tlut','rsp_mode7','rsp_mode7_window','rsp_object_cache'):
        for sec in ('.text','.data'):
            assert section(args.build/'src'/f'{name}.elf',sec) == section(args.baseline/'src'/f'{name}.elf',sec), name
    result=run(args.build)
    for fault, message in (('invalidate','wrong texture/version in TMEM'),
                           ('coordinates','wrong resident rectangle'),('restore','load tile not restored')):
        try: run(args.build,fault)
        except AssertionError as e: assert message in str(e), str(e)
        else: raise AssertionError('accepted '+fault+' mutation')
    print(json.dumps(dict(passed=True,**result,negative_guards=3,unchanged_banks=10,native_speed_claim=False)))

if __name__ == '__main__': main()
