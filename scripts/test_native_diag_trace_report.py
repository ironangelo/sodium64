#!/usr/bin/env python3
"""Original v3 fixtures test retention, corrupt saves, bounds and timing."""
import struct,unittest
from native_diag_report import FIELDS,HEADER,SIZE,parse,render

def make_blob():
    b=bytearray(SIZE);hz=46875000;interval=131071;n=hz*20//interval
    h=dict.fromkeys(FIELDS,0);h.update(magic=0x53363444,version=3,complete=1,reason=2,save_size=SIZE,
      count_hz=hz,sample_interval=interval,sample_capacity=1024,sample_count=n,pc_next_byte=((n+7)//8)*4,
      event_count=400,event_capacity=400,seconds_count=20,elapsed_ticks=hz*20,
      precision=20,frameskip=0,apu_clock=21,audio=4,halt_acknowledged=1,sp_dma_settled=1)
    for i in range((n+7)//8):struct.pack_into('>I',b,0x2200+i*4,0x80001000+i*4)
    frames=sections=0;totals=[]
    for i in range(400):
        tick=(i+1)*2343750;frames+=1 if 40<=i<60 else 3;sections+=100 if 40<=i<60 else 3
        irq=tick//interval;episode=i//20;pc=(0xf5c if 40<=i<60 else 0x3a8)
        # First and last episodes have distinct controls, colors and PC.
        w=(tick,frames,sections,irq|pc<<16,0x20|1<<16|8<<24,0x123|1<<16|1<<24,
           0x00330000|episode<<8|(255-episode),(episode<<24)|0xff<<16|0x07c1,
           0x23000002,0x01150200,2,0xf801<<16|8)
        struct.pack_into('>12I',b,0x3200+i*48,*w);totals.append((tick,frames,sections))
    for i in range(20):
        tick,frames,sections=totals[i*20+19]
        samples=(i+1)*hz//interval-i*hz//interval
        cpu=(samples//5,samples//7,samples//10)
        counts=(samples,*cpu,samples-sum(cpu),samples//2,samples//3,samples//4,samples//8)
        struct.pack_into('>3I9HH',b,0x7d00+i*32,tick,frames,sections,*counts,i+1)
    h.update(frames_completed=frames,frames_submitted=frames,sections_created=sections)
    struct.pack_into('>4I',b,HEADER+0x128,8,0,48,32)
    for i,name in enumerate(FIELDS):struct.pack_into('>I',b,HEADER+i*4,h[name])
    return checksum(b)

def checksum(b):
    body=b[:HEADER]+b[HEADER+512:]
    struct.pack_into('>I',b,HEADER+FIELDS.index('body_sum32')*4,sum(struct.unpack(f'>{len(body)//4}I',body))&0xffffffff)
    return b

class TraceTests(unittest.TestCase):
    def test_first_and_last_and_separated_costs_survive(self):
        r,_=parse(make_blob());self.assertEqual(len(r['events']),400)
        self.assertEqual(r['events'][0]['ppu_live_sample']['window_bounds'],[0,255,0,255])
        self.assertEqual(r['events'][-1]['ppu_live_sample']['window_bounds'],[19,236,19,255])
        self.assertEqual(r['events'][45]['sp_pc_live'],0xf5c)
        self.assertEqual(r['events'][320]['sp_pc_live'],0x3a8)
        self.assertGreater(r['events'][45]['sections_in_interval'],r['events'][320]['sections_in_interval'])
        self.assertFalse(r['header']['terminal_memory_snapshots']);self.assertTrue(r['header']['trace_covers_whole_interval'])
        self.assertEqual(r['cpu_timeline'][0]['irq_sequence'],1)
        self.assertLess(r['cpu_timeline'][0]['elapsed_ticks_upper'],46875000//8)
        self.assertGreater(r['cpu_timeline'][-1]['elapsed_ticks_upper'],46875000*19.9)
        self.assertIn('Whole-interval trace',render(r))
    def test_corruption_rejected(self):
        b=make_blob();b[0x3255]^=1
        with self.assertRaisesRegex(ValueError,'checksum'):parse(b)
    def test_cursor_and_capacity_rejected(self):
        for name,value in (('sample_capacity',2048),('event_count',401),('pc_next_byte',4096)):
            b=make_blob();struct.pack_into('>I',b,HEADER+FIELDS.index(name)*4,value)
            with self.assertRaises(ValueError):parse(b)
    def test_non_monotonic_trace_rejected(self):
        b=make_blob();struct.pack_into('>I',b,0x3200+48,1);checksum(b)
        with self.assertRaisesRegex(ValueError,'non-monotonic'):parse(b)
    def test_global_irq_totals_checked(self):
        b=make_blob();struct.pack_into('>I',b,HEADER+0x100,1);struct.pack_into('>I',b,HEADER+0x104,1)
        with self.assertRaisesRegex(ValueError,'totals'):parse(b)
    def test_overflow_explicit_not_called_complete(self):
        b=make_blob();struct.pack_into('>I',b,HEADER+0x12c,1)
        r,_=parse(b);self.assertFalse(r['header']['trace_covers_whole_interval'])
    def test_swapped_save(self):
        b=make_blob();swapped=b''.join(b[i:i+4][::-1] for i in range(0,len(b),4))
        r,_=parse(swapped);self.assertEqual(r['header']['byte_order'],'word-swapped')

if __name__=='__main__':unittest.main()
