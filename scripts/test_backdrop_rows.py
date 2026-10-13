#!/usr/bin/env python3
"""Linked row/epoch ownership and retired primitive packets; numeric inputs only."""
import argparse
import json
import random
import struct
from pathlib import Path
from test_native_diag_arm import load_elf
from test_native_diag_v4 import execute as cpu_execute, sx
from test_renderer_batching import put as cpu_put
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_sub_presence import section
from test_rsp_sub_alpha import PacketVM
from test_rsp_math_dma import ROOT, put, symbols
from check_rsp_branch_delay_slots import read_text

EXIT = 0xdead0000
STOP = 0xf7c


def cpu_cases(build):
    image, s = load_elf(build/'sodium64-backdrop45.elf')
    rows = epochs = bindings = 0
    for parity, queue in ((0,0xa03e7400),(4,0xa03e7600)):
        for line in (0,*range(1,242),255,65535):
            m = image.copy()
            before = bytes([0xa5])*640
            lo = (queue-64)&0x1fffffff
            m.update((lo+i,b) for i,b in enumerate(before))
            cpu_put(m,s['cur_line'],line,2)
            cpu_put(m,s['main_color'],0xb6ef,2)
            cpu_put(m,s['sub_color'],0x2aaa,2)
            cpu_put(m,s['hcomp_row_main_ptr'],queue)
            cpu_put(m,s['hcomp_row_fixed_ptr'],0xa03e7000+parity*128)
            cpu_execute(m,s['hcomp_record_row_input'],[0]*32,{},stop=s['hcomp_row_fixed_recorded'])
            expected = bytearray(before)
            if 1<=line<=240:
                expected[64+2*(line-1):66+2*(line-1)] = b'\xb6\xef'
            assert bytes(m[lo+i] for i in range(640)) == expected, ('Main row bounds',line)
            rows += 1
    rng = random.Random(45)
    checks = [None,*range(64),'palette1','marker','late_palette','late_marker','overflow','brightness','dirty','first',
              'mode7','direct','clip','window','sub_source','backdrop_math','sub_full']
    for half in (False,True):
        for changed in checks:
            m = image.copy()
            packet = bytearray(rng.randrange(256) for _ in range(64))
            packet[0x37]=0; packet[0x38]=0xc2 if half else 2
            packet[0x3d]=8; packet[0x3e]=0
            old = bytearray(packet); old[0x3e]=0x40; old[0x3f]=37
            old[40:42] = b'\x12\x35'
            packet[40:42] = b'\xab\xcd'
            event = 0x43210000
            if isinstance(changed,int): packet[changed] ^= 1
            elif changed=='palette1': event |= 8
            elif changed=='marker': event |= 0x8000
            elif changed=='dirty': packet[0x3e] |= 0x40
            elif changed=='mode7': packet[0x3d] = 7
            elif changed=='direct': packet[0x37] = 1
            elif changed=='clip': packet[0x37] = 0x80
            elif changed=='window': packet[0x37] = 0x10
            elif changed=='sub_source': packet[0x37] = 2
            elif changed=='backdrop_math': packet[0x38] |= 0x20
            elif changed=='sub_full': packet[38] ^= 2
            current, previous = s['bghofs'], 0xa0140000
            for i,b in enumerate(packet): cpu_put(m,current+i,b,1)
            for i,b in enumerate(old): cpu_put(m,previous+i,b,1)
            cpu_put(m,s['section_ptr'],previous+64)
            cpu_put(m,s['queue_id'],0,1)
            cpu_put(m,s['sect_queues'],previous+64 if changed=='first' else previous-64)
            count = 4 if changed in ('late_palette','late_marker') else 3
            cpu_put(m,s['hcomp_cgram_event_count'],count,2)
            cpu_put(m,s['hcomp_last_section_count'],2,2)
            cpu_put(m,s['hcomp_cgram_event_ptr'],0xa00d4e00+count*4)
            cpu_put(m,0xa00d4e00+8,event)
            if count==4:
                cpu_put(m,0xa00d4e00+12,0x12340008 if changed=='late_palette' else 0x12348000)
            cpu_put(m,s['hcomp_cgram_event_overflow'],int(changed=='overflow'),1)
            cpu_put(m,s['brightness'],8 if changed=='brightness' else 16,1)
            cpu_put(m,s['hcomp_last_section_brightness'],16,1)
            sentinel = s['hcomp_new_section']
            cpu_put(m,sentinel,0x03e00008); cpu_put(m,sentinel+4,0x24020001)
            r = [sx(0x11110000+i) for i in range(32)]
            r[0]=r[2]=0; r[31]=EXIT
            before = r.copy()
            cpu_execute(m,s['section_init'],r,{},stop=EXIT)
            allowed = changed is None or changed in (40,41,63) or (half and changed in (38,39,'sub_full'))
            assert bool(r[2]) == (not allowed), ('epoch',half,changed,r[2])
            assert all(r[i]==before[i] for i in (12,13,14,15,16,17,18,19,20,21,22,23,24,25,31)), ('CPU caller ownership',changed)
            assert int.from_bytes(bytes(m[(s['hcomp_last_section_count']&0x1fffffff)+i] for i in range(2)),'big') == (3 if allowed else 2)
            assert int.from_bytes(bytes(m[(0xa00d4e08&0x1fffffff)+i] for i in range(4)),'big') == event, 'typed event was dropped'
            epochs += 1
    for initial in (0,0x20000000):
        m = image.copy(); r=[0]*32; r[8]=s['rsp_hcomp_text_start']|3|initial
        cpu_execute(m,s['hcomp_backdrop_cpu_bind'],r,{},stop=s['hcomp_backdrop_cpu_bind_end'])
        def word(address):
            address &= 0x1fffffff
            return int.from_bytes(bytes(m[address+i] for i in range(4)),'big')
        assert s['rsp_hcomp_data_start']-s['rsp_hcomp_text_start']==1000
        assert s['rsp_hcomp_backdrop_data_start']-s['rsp_hcomp_backdrop_text_start']==1000
        assert word(s['rsp_hcomp_backdrop_data_start']) == (s['rsp_hcomp_text_start']|3|initial)&0xffffffff
        assert word(s['rsp_hcomp_data_start']) == s['rsp_hcomp_backdrop_text_start']|3
        bindings += 1
    return dict(row_bounds=rows,epoch_barriers=epochs,cpu_source_bindings=bindings)


class RowVM(PacketVM):
    def __init__(self,*args,ram,table,queue,**kwargs):
        super().__init__(*args,**kwargs)
        self.ram = ram
        self.table = table
        self.queue = queue
        self.backup_retired = False
    def poll_dma(self):
        pending = self.dma.copy() if self.dma else None
        result = super().poll_dma()
        if pending and not result and pending['write']:
            assert pending['ram'] == 0xd4400 and pending['sp'] == self.table and pending['size'] == 1024
            self.backup_retired = True
        return result
    def queue_dma(self,write,length):
        if not write:
            source = self.ramaddr&0x1fffffff
            if source == 0xd4400:
                assert self.backup_retired, 'restore before backup retirement'
                assert length == 1023 and self.spaddr == self.table, 'restore extent'
            elif source != 0x180000+1000:
                assert source == self.queue and length == 511 and self.spaddr == self.table, 'row queue parity/extent'
        super().queue_dma(write,length)


def rsp_case(build, *, start=0, rows=224, parity=0, pattern='gradient', cgws=0, cad=0xc2,
             mode=8, screen=1, flags=0, limit=0, fault=None):
    addr = parse_macros(ROOT).name
    main = read_text(build/'src/rsp_main.elf')[1]
    helper = read_text(build/'src/rsp_hcomp_backdrop.elf')[1]
    syms = symbols(build/'src/rsp_hcomp_backdrop.elf')
    code = bytearray(main); code[0x3a8:0x790]=helper
    d = bytearray(section(build/'src/rsp_main.elf','.data'))
    rand = random.Random(0x45+start+rows)
    table = addr('TILE_TABLE')
    original = bytes(rand.randrange(256) for _ in range(1024))
    d[table:table+1024]=original
    d[addr('CGWSEL')]=cgws; d[addr('CGADSUB')]=cad; d[addr('BG_MODE')]=mode
    d[addr('HCOMP_SCREEN')]=screen; d[addr('STAT_FLAGS')]=flags
    put(d,addr('FB_OFFSET')+parity,8)
    put(d,addr('HCOMP_DIAG_COMPOSE_LIMIT'),limit)
    put(d,addr('OVERLAY_MAIN_SRC'),0x80190001)
    put(d,addr('HCOMP_BAND_Y'),start+8); put(d,addr('HCOMP_BAND_ROWS'),rows)
    fill = addr('RDP_FILL')
    for offset,value in ((10,(start+8)*4),(14,(start+rows+8)*4),(38,(start+8)*4),(34,(start+rows+8)*4)):
        struct.pack_into('>H',d,fill+offset,value)
    put(d,fill+20,0x386898ff)
    ram = bytearray(0x400000)
    queue = (addr('HCOMP_ROW_MAIN_QUEUE1')&0x1fffffff)+parity*128
    colors = []
    for y in range(256):
        rgb = (y*911+32767)&32767 if pattern=='gradient' else 0 if pattern=='black' else ((y//7)*127)&32767
        colors.append((rgb<<1)|1)
        struct.pack_into('>H',ram,queue+y*2,colors[-1])
    put(ram,0x180000+1000,0x801a0003)
    before = bytes(d)
    owned = set(range(table,table+1024)) | set(range(addr('SCRN_DATA'),addr('SCRN_DATA')+8)) | set(range(addr('PRIO_CHECKS'),addr('PRIO_CHECKS')+8))
    for offset,size in ((10,2),(14,2),(20,4),(34,2),(38,2)):
        owned.update(range(fill+offset,fill+offset+size))
    r = [0]*32; r[5]=0x80180000; r[26]=start; r[27]=start+rows; r[29]=parity; r[23]=0x17
    vm = RowVM(code,d,r,owned,3,True,ram=ram,table=table,queue=queue)
    vm.pc=syms['hcomp_entry']
    if fault=='short_restore':
        # The last1023 literal is the actual TILE_TABLE restore length.
        matches=[pc for pc in range(0x3a8,0x790,4) if struct.unpack_from('>I',vm.code,pc)[0]==0x240603ff]
        assert len(matches)==2
        put(vm.code,matches[-1],0x240600ff)
    elif fault=='pending_latch':
        put(vm.code,symbols(build/'src/rsp_main.elf')['rdp_fetch_wait']+8,0)
    elif fault in ('wrong_queue','main_alpha'):
        wanted,replacement=(0x34a57400,0x34a57600) if fault=='wrong_queue' else (0x350800ff,0x3508003f)
        matches=[pc for pc in range(0x3a8,0x790,4) if struct.unpack_from('>I',vm.code,pc)[0]==wanted]
        assert len(matches)==1
        put(vm.code,matches[0],replacement)
    vm.execute(STOP,max_steps=150000)
    assert vm.pending_fetch is None and vm.dma is None
    assert d[table:table+1024]==original, 'TILE_TABLE not restored'
    assert all(d[i]==before[i] for i in range(4096) if i not in owned), 'unowned DMEM changed'
    assert (r[26],r[27],r[29],r[23])==(start,start+rows,parity,0x17), 'band/queue/layer ownership'
    assert r[5] == (0x801a0003 if flags&128 else 0x80190001)
    assert r[25] == (0x1778 if flags&128 else 0x1370)
    eligible=not flags&128 and screen and not cgws&0xf3 and not cad&0x20 and mode&7<2 and not limit and 0<=start<start+rows<=240
    assert vm.backup_retired == bool(eligible)
    assert vm.captures
    if eligible:
        actual = [None]*rows
        for packet in vm.captures:
            assert len(packet)==addr('RDP_WINDOW')-(fill+8)
            words = struct.unpack('>'+'Q'*(len(packet)//8),packet)
            assert [w>>56 for w in words] == [0x2d,0x3a,0x3c,0x36,0x27,0x3c]
            scissor,primitive,_,rect,_,_ = words
            y0,y1=(scissor>>32&0xfff)//4-8,(scissor&0xfff)//4-8
            assert (scissor>>44&0xfff)//4==12 and (scissor>>12&0xfff)//4==268
            assert rect&0xfff==(y0+8)*4 and rect>>32&0xfff==(y1+8)*4
            assert start<=y0<y1<=start+rows
            rgba=primitive&0xffffffff
            rgb=(rgba>>27&31)<<10 | (rgba>>19&31)<<5 | (rgba>>11&31)
            assert rgba&255==255, 'Main black/presence alpha changed'
            for y in range(y0,y1):
                assert actual[y-start] is None, 'overlapping row fill'
                actual[y-start]=rgb
        assert actual==[c>>1 for c in colors[start:start+rows]], 'Main row color or phase mismatch'
        for offset in (10,14,34,38):
            assert d[fill+offset:fill+offset+2]==before[fill+offset:fill+offset+2], 'band geometry not restored'
    else:
        assert len(vm.captures)==1
    return dict(rows=rows if eligible else 0,packets=len(vm.captures))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('build',type=Path); ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    result=cpu_cases(args.build)
    cases=[dict(start=s,rows=min(n,240-s),parity=p,pattern=pattern)
           for s,n in ((0,224),(1,1),(7,31),(113,127),(239,1)) for p in (0,4) for pattern in ('gradient','black','runs')]
    cases += [dict(cgws=c) for c in (1,2,0x10,0x40,0x80)]
    cases += [dict(cad=0xe2),dict(mode=7),dict(screen=0),dict(flags=128),dict(limit=8)]
    outcomes=[rsp_case(args.build,**c) for c in cases]
    rejected=[]
    for fault in ('short_restore','pending_latch','wrong_queue','main_alpha'):
        try: rsp_case(args.build,fault=fault)
        except AssertionError: rejected.append(fault)
        else: raise AssertionError('escaped negative: '+fault)
    result.update(rsp_cases=len(cases),colored_rows=sum(c['rows'] for c in outcomes),
                  pixels=sum(c['rows'] for c in outcomes)*256,negative_mutations_rejected=rejected,
                  passed=True,native_fidelity_or_performance=False)
    if args.output: args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
