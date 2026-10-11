#!/usr/bin/env python3
"""Prepare the TLUT shader oracle from compiled palette and Math consumers.

Original numeric inputs reproduce the retired room policy, not game pixels.
This baseline fixture does not execute a future TLUT shader or an RDP rasterizer.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from check_rsp_branch_delay_slots import read_text
from test_hcomp_packed_math import ENABLES, load, reference, run_arithmetic
from test_hcomp_sub_presence import section
from test_hcomp_packed_math import seeds
from test_native_diag_arm import load_elf
from test_rsp_math_dma import MathVM, ROOT, put, symbols as rsp_symbols
from test_vram_flush import run as cpu_run

ROOM = dict(cgwsel=0x02,cgadsub=0xb3,ts=0,tm=0x16,bgmode=0x08,
            fixed=0x8400,rows=224,clip=0xffff,allow=0xffff)


class TlutVM(MathVM):
    """Delay command adoption and keep an earlier TLUT source leased.

    Command fetch completion does not retire the RDRAM palette reader.
    SyncFull and its busy wait must finish before generation reuses it.
    Only command/source ownership is modeled, never rasterized pixels.
    """
    def __init__(self,code,dmem,ram,regs,owners,ram_owner,delay,lease=None):
        super().__init__(code,dmem,ram,regs,seeds(),delay,owners)
        self.ram_owner = ram_owner
        self.lease = lease
        self.lease_original = bytes(ram[lease[0]:lease[1]]) if lease else None
        self.lease_capture = None
        self.source_left,self.source_fenced = delay,False
        self.rdp_start,self.current = 0,0
        self.pending_fetch,self.captures = None,[]

    def check_dmem(self,address,size,write=False):
        super().check_dmem(address,size,write)
        if write and self.pending_fetch:
            p = self.pending_fetch
            assert not (address < p['end'] and p['start'] < address+size), 'TLUT command scratch reused before fetch'

    def queue_dma(self,write,length):
        if write:
            size = ((length&0xfff)|7)+1
            target = self.ramaddr&0x1fffffff
            assert all(i in self.ram_owner for i in range(target,target+size)), 'TLUT DMA overwrote RDRAM owner'
            if self.lease:
                assert not (target < self.lease[1] and self.lease[0] < target+size), 'TLUT source reused before reader retired'
        super().queue_dma(write,length)

    def cop0_write(self,register,value):
        if register == 8:
            assert self.pending_fetch is None, 'TLUT sender replaced pending START'
            self.rdp_start = value
        elif register == 9:
            assert self.pending_fetch is None and 0 <= self.rdp_start < value <= 4096
            assert not (self.rdp_start|value)&7
            self.pending_fetch = dict(start=self.rdp_start,end=value,left=self.delay)
            self.current = value # Adversarial stale CURRENT from prior same END.
        else: super().cop0_write(register,value)

    def cop0_read(self,register):
        if register == 10: return self.current
        if register != 11: return super().cop0_read(register)
        flags = 0
        if self.pending_fetch:
            p = self.pending_fetch
            p['left'] -= 1
            if p['left']:
                flags |= 0x600
            else:
                packet = bytes(self.dmem[p['start']:p['end']])
                self.captures.append(packet)
                if any(packet[i:i+4]==bytes.fromhex('29000000') for i in range(0,len(packet),8)):
                    self.source_fenced = True
                self.current,self.pending_fetch = p['end'],None
        if self.lease:
            flags |= 0x40
            if self.source_fenced:
                self.source_left -= 1
                if not self.source_left:
                    self.lease_capture = bytes(self.ram[self.lease[0]:self.lease[1]])
                    assert self.lease_capture==self.lease_original, 'TLUT load captured overwritten palette'
                    self.lease = None
                    flags &= ~0x40
        return 0x81|flags


def read(memory,address,size):
    return bytes(memory.get((address+i)&0x1fffffff,0) for i in range(size))


def write(memory,address,data):
    memory.update(((address+i)&0x1fffffff,b) for i,b in enumerate(data))


def consume_palette(image,symbols,brightness,slot):
    """Run the actual queue producer; keep both palette owners and entry0."""
    addr = parse_macros(ROOT).name
    memory = image.copy()
    colors = [((i*977)^0x4210)&0x7fff for i in range(256)]
    colors[0:5] = (0x7fff,0,0x001f,0x03e0,0x7c00)
    queues = [addr('PALETTE_QUEUE1'),addr('PALETTE_QUEUE2')]
    for queue in queues:
        # The boot arena clear owns entry0, while every nonzero slot is poison.
        write(memory,queue,bytes(8)+bytes([0xa5])*2040)
        write(memory,queue-8,bytes([0x6d])*8)
        write(memory,queue+2048,bytes([0xb7])*8)
    write(memory,symbols['cgram'],struct.pack('>256H',*colors))
    write(memory,symbols['brightness'],bytes([brightness]))
    write(memory,symbols['dpal_dirty'],b'\3')
    write(memory,symbols['dpal_brightness'],b'\xff\xff')
    queue = queues[slot//4]
    before = memory.copy()
    regs = [0x13500000+i for i in range(32)]
    regs[0],regs[13] = 0,slot
    cpu_run(memory,symbols['dpal_update_begin'],symbols['dpal_update_end'],regs)
    palette = read(memory,queue,2048)
    expected = bytearray(2048)
    for index,color in enumerate(colors[1:],1):
        r,g,b = [(color>>shift&31)*brightness//16 for shift in (0,5,10)]
        rgba = r<<11|g<<6|b<<1|1
        expected[index*8:index*8+8] = struct.pack('>4H',*[rgba]*4)
    assert palette==expected, 'compiled TLUT brightness/alpha/quadruple entry mismatch'
    allowed = set(range(queue&0x1fffffff,(queue&0x1fffffff)+2048))
    allowed.update((symbols['dpal_dirty']&0x1fffffff,
                    (symbols['dpal_brightness']&0x1fffffff)+slot//4))
    assert all(memory[key]==value for key,value in before.items() if key not in allowed), 'palette producer changed an owner'
    assert set(memory)-set(before) <= allowed, 'palette producer wrote outside its owner'
    assert palette[:8]==bytes(8) and all(value&1 for value in struct.unpack('>1020H',palette[8:])), 'transparent0 / opaque black contract'
    return [struct.unpack_from('>H',palette,index*8)[0] for index in range(256)]


def expected_shades(palette,kind,policy=ROOM):
    eligible = bool(ENABLES[kind]&policy['cgadsub'] and policy['allow'])
    # Source2+TS0 is absent Sub; HALF is suppressed even when CGADSUB40 is set.
    half = bool(policy['cgadsub']&0x40 and policy['clip'] and
                not (policy['cgwsel']&2 and not policy['ts']))
    result = [0]
    for color in palette[1:]:
        clipped = (color&policy['clip'])>>1
        result.append(reference(clipped,policy['fixed']>>1,
                                bool(policy['cgadsub']&0x80),half) if eligible else clipped<<1|1)
    return result


def tlut_image(palette):
    """The real palette producer stores four halfword copies per CI8 index."""
    assert len(palette)==256
    return b''.join(struct.pack('>4H',*[color]*4) for color in palette)


def expected_tlut_tables(palette,policy):
    """Independent palette oracle; class binding remains a separate check.

    A BG eligible table applies math to every palette index, including the
    upper 128 indices consumed by 8bpp BGs. OBJ groups0..3 must instead retain
    the clipped base result. Index0 is texture transparency, never backdrop.
    """
    assert len(palette)==256 and palette[0]==0
    base = [0]+[((color&policy['clip'])&0xfffe)|1 for color in palette[1:]]
    half = bool(policy['cgadsub']&0x40 and policy['clip'] and
                not (policy['cgwsel']&2 and not policy['ts']&0x1f))
    shaded = [0]+[
        reference(color>>1,policy['fixed']>>1,bool(policy['cgadsub']&0x80),half)
        if policy['allow'] else color for color in base[1:]]
    obj = base[:]
    if policy['cgadsub']&0x10:
        obj[192:] = shaded[192:]
    return [tlut_image(colors) for colors in (base,shaded,obj)]


def expected_backdrop_rgba(policy):
    """Opaque backdrop comes from MAIN_COLOR, independently of CI8 0."""
    clipped = (policy['main']&policy['clip'])>>1
    half = bool(policy['cgadsub']&0x40 and policy['clip'] and
                not (policy['cgwsel']&2 and not policy['ts']&0x1f))
    return (reference(clipped,policy['fixed']>>1,bool(policy['cgadsub']&0x80),half)
            if policy['cgadsub']&0x20 and policy['allow'] else clipped<<1|1)


def expected_backdrop(policy):
    color = expected_backdrop_rgba(policy)
    return ((color&0xf800)<<16)|((color&0x07c0)<<13)|((color&0x003e)<<10)|0xff


def compiled_shades(math,palette,kind,policy=ROOM):
    eligible = [0xffff if ENABLES[kind]&policy['cgadsub'] and policy['allow'] else 0]*8
    half = bool(policy['cgadsub']&0x40 and policy['clip'] and
                not (policy['cgwsel']&2 and not policy['ts']))
    out = []
    for x in range(0,256,8):
        colors = [(value&policy['clip'])>>1 for value in palette[x:x+8]]
        values,_ = run_arithmetic(math,colors,[policy['fixed']>>1]*8,
                                 bool(policy['cgadsub']&0x80),[0xffff if half else 0]*8,eligible)
        out.extend(values)
    # A shader must preserve the transparent texture entry, independently of
    # the backdrop's separate opaque primitive fill.
    out[0] = palette[0]
    return out


def retirement_contract(code,data,syms,delay,fault=False):
    addr = parse_macros(ROOT).name
    scratch = addr('SCRN_DATA')
    workspace = addr('HCOMP_WINNER_ARENA')&0x1fffffff
    ram = bytearray([0xa5])*0x400000
    dmem = bytearray(data)
    payload = bytes((i*37+11)&255 for i in range(64))
    dmem[scratch:scratch+64] = payload
    expected = ram.copy();expected[workspace:workspace+64] = payload
    regs = [0x13500000+i for i in range(32)]
    regs[0],regs[4],regs[5],regs[6],regs[31] = 0,scratch,workspace,63,0x790
    vm = TlutVM(code,dmem,ram,regs,set(range(scratch,scratch+64)),
                set(range(workspace,workspace+0x1800)),delay,(workspace,workspace+2048))
    vm.pc = syms['rdp_source_retire']
    if fault:
        # An unconditional taken branch bypasses the real source-reader fence.
        branch = vm.pc+8
        word = struct.unpack_from('>I',vm.code,branch)[0]
        assert word>>26==4
        put(vm.code,branch,word&~(31<<21))
    vm.execute(0x790,max_steps=10000)
    assert vm.lease is None and vm.pending_fetch is None
    assert vm.lease_capture==vm.lease_original and vm.ram==expected
    assert bytes(dmem)==bytes(data[:scratch])+payload+bytes(data[scratch+64:])
    assert vm.transfers==[dict(write=True,imem=False,sp=scratch,ram=workspace,size=64)]
    assert vm.captures==[bytes(data[addr('HCOMP_TEXTURE_FENCE'):addr('HCOMP_TEXTURE_FENCE')+8])]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('cpu',type=Path);ap.add_argument('main_rsp',type=Path)
    ap.add_argument('math_rsp',type=Path);ap.add_argument('--output',type=Path)
    a = ap.parse_args()
    image,symbols = load_elf(a.cpu)
    math = load(a.math_rsp)
    addr = parse_macros(ROOT).name
    data = section(a.main_rsp,'.data')
    main_base,main_code = read_text(a.main_rsp)
    main_symbols = rsp_symbols(a.main_rsp)
    assert main_base&0xfff==0 and len(main_code)==4096
    assert struct.unpack_from('>II',data,addr('RDP_INIT'))==(0x2f0088ff,0x00040001)
    assert struct.unpack_from('>II',data,addr('RDP_INIT')+8)==(0x39000000,0xffffffff)
    assert struct.unpack_from('>II',data,addr('RDP_FILL'))==(0x33000000,0x00400000)
    assert struct.unpack_from('>II',data,addr('RDP_FRAME')+16)==(0x26000000,0)
    for delay in (2,7,31): retirement_contract(main_code,data,main_symbols,delay)
    try: retirement_contract(main_code,data,main_symbols,7,fault=True)
    except AssertionError as e: assert 'TLUT source reused before reader retired' in str(e)
    else: raise AssertionError('palette ownership fixture accepted skipped fence')
    palettes,cases,pixels = 0,0,0
    for brightness in (0,2,8,16):
        for slot in (0,4):
            palette = consume_palette(image,symbols,brightness,slot)
            palettes += 1
            for mode in (0x33,0x73,0xb3,0xf3):
                policy = dict(ROOM,cgadsub=mode)
                for kind in range(7):
                    want = expected_shades(palette,kind,policy)
                    assert compiled_shades(math,palette,kind,policy)==want, ('TLUT oracle preparation',brightness,slot,mode,kind)
                    assert want[0]==0 and all(color&1 for color in want[1:])
                    cases += 1;pixels += 256
            obj = expected_shades(palette,6)
            obj[128:192] = palette[128:192]
            assert obj[128:192]==palette[128:192] and obj[192:]==expected_shades(palette,6)[192:]
            # Same numeric palette index has different eligibility by owner:
            # BG2 eligible, BG3/OBJ-low forbidden, OBJ-high eligible.
            assert expected_shades(palette,2)==expected_shades(palette,6)
            assert expected_shades(palette,3)==expected_shades(palette,5)==palette
    negative_guards = 0
    for name,word in (('opaque_alpha',0x354a0001),('quadruple_copy',0xac6a0004)):
        # Mutate the linked ORI A=1 or second SW, rather than the oracle.
        anchors = [pc for pc in range(symbols['update_dpal'],symbols['dpal_update_end'],4)
                   if int.from_bytes(read(image,pc,4),'big')==word]
        assert len(anchors)==1, ('palette fault anchor',name,anchors)
        changed = image.copy();write(changed,anchors[0],bytes(4))
        try: consume_palette(changed,symbols,0,0)
        except AssertionError as e: assert 'compiled TLUT brightness/alpha/quadruple' in str(e)
        else: raise AssertionError(('palette fixture accepted linked fault',name))
        negative_guards += 1
    report = dict(passed=True,fixture_abi_version=1,room_policy=ROOM,
                  compiled_palette_cases=palettes,compiled_math_shade_cases=cases,palette_pixels=pixels,
                  negative_guards=negative_guards,boot_entry0_seeded=True,class_eligibility_seeded=True,
                  compiled_source_retirement_cases=3,source_retirement_fault_rejected=True,
                  entry0_transparent=True,nonzero_black_opaque=True,source2_absent_suppresses_half=True,
                  main_palette_owner_preserved=True,obj_palette_split_reference_prepared=True,
                  candidate_tlut_transform_executed=False,painter_stream_executed=False,
                  scope='compiled_original_palette_and_math_preparation_for_future_tlut_shader',
                  original_numeric_inputs=True,rdp_rasterization_authority=False,commercial_data=False,
                  elf_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (a.cpu,a.main_rsp,a.math_rsp)})
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(report,indent=2)+'\n')
    print('HCOMP_TLUT_ORACLE_PREPARATION PASS',json.dumps({k:v for k,v in report.items() if k!='elf_sha256'}))


if __name__=='__main__': main()
