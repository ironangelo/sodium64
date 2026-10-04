#!/usr/bin/env python3
"""Original v4 fixtures: full cadence, two costs, partial tails and corruption."""
import struct,unittest
from native_diag_report import FIELDS,HEADER,SIZE,parse,render
from native_diag_v4 import CPU_MODULES,RSP_STAGES

HZ=46875000
def checksum(b):
    body=b[:HEADER]+b[HEADER+512:]
    struct.pack_into('>I',b,HEADER+FIELDS.index('body_sum32')*4,sum(struct.unpack(f'>{len(body)//4}I',body))&0xffffffff)
    return b

def make_blob():
    b=bytearray(SIZE);interval=131071;n=HZ*20//interval
    baseline=100;end=baseline;frames=[]
    while True:
        dt=HZ//40 if HZ<=end<2*HZ else HZ*18//1000 if 14*HZ<=end<15*HZ else HZ//60
        end+=dt
        if end>20*HZ:break
        rsp=dt//2 if HZ<=end<2*HZ else 100
        vi=dt//3 if rsp==100 else 50
        frames.append((end,rsp,vi));struct.pack_into('>3I',b,0x2600+(len(frames)-1)*12,end,rsp,vi)
    h=dict.fromkeys(FIELDS,0);h.update(magic=0x53363444,version=4,complete=1,reason=2,save_size=SIZE,
        count_hz=HZ,sample_interval=interval,sample_capacity=256,sample_count=n,pc_next_byte=((n+31)//32)*4,
        event_count=160,event_capacity=160,seconds_count=20,elapsed_ticks=HZ*20,frames_completed=len(frames)+1,
        precision=20,apu_clock=21,audio=4,halt_acknowledged=1,sp_dma_settled=1)
    struct.pack_into('>4I',b,HEADER+0x128,32,0,40,64)
    struct.pack_into('>7I',b,HEADER+0x138,0x46524d34,len(frames),1280,12,baseline,0,0)
    struct.pack_into('>3I',b,HEADER+0x188,HZ//8,3,1)
    struct.pack_into('>2I',b,HEADER+0x1d8,46875,0x42414e34)
    for i in range((n+31)//32):struct.pack_into('>I',b,0x2200+i*4,0x80001000+i*4)
    event_counts=[]
    for i in range(160):
        tick=(i+1)*HZ//8;ns=tick//interval-(tick-HZ//8)//interval
        fc=1+sum(f[0]<=tick for f in frames);sec=fc*73 # Full 32-bit sections; the later count exceeds 65535.
        counts=(3,ns-16,2,1,3,5,1,1) if 8<=i<16 else (5,ns-19,3,2,4,0,4,1)
        event_counts.append(counts)
        struct.pack_into('>2I2H2BH6BH16B',b,0x6200+i*40,tick,sec,fc,0x1f4c,0x40,0x21,0x61,0x12,0x20,2,0x15,0,0,8,*counts,0,0,ns,0,0,0,0,0)
    for i in range(20):
        tick=(i+1)*HZ;fc=1+sum(f[0]<=tick for f in frames)
        modules=tuple(sum(c[j] for c in event_counts[i*8:i*8+8]) for j in range(8));ns=sum(modules)
        counts=(ns,modules[5],modules[6],modules[1]//2,ns-modules[5]-modules[6]-modules[1]//2,ns//2,ns//3,ns//3,0)
        struct.pack_into('>3I9HH8H4H2I',b,0x7b00+i*64,tick,fc,fc*73,*counts,i+1,*modules,3,10,15,8,0,0)
    h['sections_created']=h['frames_completed']*73
    for i,name in enumerate(FIELDS):struct.pack_into('>I',b,HEADER+i*4,h[name])
    return checksum(b)

def field(b,name,value):struct.pack_into('>I',b,HEADER+FIELDS.index(name)*4,value)

class V4Tests(unittest.TestCase):
    def test_complete_cadence_and_separated_work(self):
        r,_=parse(make_blob());h=r['header']
        self.assertGreater(len(r['frames']),1100);self.assertEqual(len(r['events']),160)
        self.assertTrue(h['frame_analysis']['all_full_boundaries_retained'])
        self.assertGreater(r['events'][-1]['sections_created'],65535)
        heavy=[f for f in r['frames'] if 1.1*HZ<f['elapsed_ticks']<1.9*HZ]
        later=[f for f in r['frames'] if 14.1*HZ<f['elapsed_ticks']<14.9*HZ]
        self.assertTrue(all(f['cpu_rsp_wait_ms']>10 for f in heavy))
        self.assertTrue(all(f['cpu_rsp_wait_ms']<1 for f in later))
        self.assertTrue(all(f['interval_ms']>17 for f in later))
        self.assertFalse(h['frame_analysis']['completed_cadence_is_presentation_fps'])
        self.assertIn('Full completed boundaries',render(r))
    def test_partial_tail_accounts_for_every_irq(self):
        b=make_blob();struct.pack_into('>I',b,HEADER+0x198+7*4,1)
        struct.pack_into('>I',b,HEADER+0x1b8+7*4,1)
        struct.pack_into('>I',b,HEADER+0x158+7*4,1)
        struct.pack_into('>9I',b,HEADER+0x100,1,0,0,0,1,0,0,0,0)
        n=int.from_bytes(b[HEADER+32:HEADER+36],'big');field(b,'sample_count',n+1)
        retained=(n+32)//32;field(b,'pc_next_byte',retained*4)
        parse(b)
    def test_overlay_identity_and_stage_totals(self):
        r,_=parse(make_blob())
        self.assertEqual(r['events'][0]['rsp_bank'],'main')
        self.assertEqual(r['events'][0]['sp_pc_live'],0xf4c)
        self.assertTrue(r['header']['frame_analysis']['rsp_overlay_stage_attribution_available'])
        self.assertEqual(sum(r['header']['rsp_stage_samples_total'].values()),r['header']['sample_count'])
        b=make_blob();struct.pack_into('>H',b,0x620a,0x8f4c);checksum(b)
        with self.assertRaisesRegex(ValueError,'snapshot'):parse(b)
    def test_foreign_sram_rejected(self):
        b=make_blob();struct.pack_into('>I',b,HEADER+0x18c,4)
        with self.assertRaisesRegex(ValueError,'SRAM'):parse(b)
    def test_wait_cannot_exceed_interval(self):
        b=make_blob();struct.pack_into('>I',b,0x2604,HZ);checksum(b)
        with self.assertRaisesRegex(ValueError,'waits exceed'):parse(b)
    def test_baseline_cannot_count_partial_as_frame(self):
        b=make_blob();struct.pack_into('>I',b,HEADER+0x190,0)
        with self.assertRaisesRegex(ValueError,'frame'):parse(b)
    def test_bad_sample_and_frame_capacities(self):
        for off,value in ((0x13c,1281),(0x140,1281),(0x144,16),(0x128,8)):
            b=make_blob();struct.pack_into('>I',b,HEADER+off,value)
            with self.assertRaises(ValueError):parse(b)
    def test_byte_swap_and_truncation(self):
        b=make_blob();swapped=b''.join(b[i:i+4][::-1] for i in range(0,len(b),4))
        self.assertEqual(parse(swapped)[0]['header']['byte_order'],'word-swapped')
        with self.assertRaises(ValueError):parse(b[:-1])
    def test_payload_corruption(self):
        b=make_blob();b[0x6300]^=1
        with self.assertRaisesRegex(ValueError,'checksum'):parse(b)
    def test_observation_module_totals(self):
        b=make_blob();b[0x6218]+=1;checksum(b)
        with self.assertRaisesRegex(ValueError,'RSP/CPU observation totals'):parse(b)
    def test_second_modules_and_resident_wait_totals(self):
        b=make_blob();struct.pack_into('>H',b,0x7b20,500);checksum(b)
        with self.assertRaisesRegex(ValueError,'buckets disagree'):parse(b)
    def test_overflow_is_explicit(self):
        b=make_blob();struct.pack_into('>I',b,HEADER+0x12c,8)
        self.assertFalse(parse(b)[0]['header']['frame_analysis']['all_full_boundaries_retained'])
    def test_saturation_never_provides_precise_timeline_bounds(self):
        b=make_blob();struct.pack_into('>I',b,HEADER+0x12c,16)
        self.assertTrue(all(not x['bounds_valid'] for x in parse(b)[0]['cpu_timeline']))

if __name__=='__main__':unittest.main()

