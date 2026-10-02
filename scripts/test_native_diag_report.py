#!/usr/bin/env python3
"""Original byte fixtures for capture integrity, ring ordering and halt validity."""
import struct, unittest
from native_diag_report import FIELDS, HEADER, SIZE, parse, symbolicate

def make_capture(samples=3, events=2, seconds=1):
    b=bytearray(SIZE)
    h=dict.fromkeys(FIELDS,0)
    h.update(magic=0x53363444,version=1,complete=1,reason=1,save_size=SIZE,
             count_hz=46875000,sample_interval=131071,sample_capacity=2048,
             sample_count=samples,pc_next_byte=(samples%2048)*4,
             event_count=events,event_capacity=64,seconds_count=seconds,
             elapsed_ticks=(seconds+2)*46875000,halt_acknowledged=1,
             sp_status_after=1,sp_pc_after=0x2EC,cpu_epc=0x80001000)
    for i in range(samples):
        struct.pack_into(">I",b,0x2200+(i%2048)*4,0x80000000+i*4)
    for i in range(events):
        values=[0]*16
        values[0]=i+1;values[1]=(i+1)*2343750
        struct.pack_into(">16I",b,0x4200+(i%64)*64,*values)
    for i in range(seconds):
        row=[i+1,(i+1)*46875000,(i+1)*60,(i+1)*24,(i+1)*24,
             100,50,10,20,20,90,20,30,10,(i+1)*28,(i+1)*1000]
        struct.pack_into(">16I",b,0x7200+i*64,*row)
    commit(b,h)
    return b,h

def commit(b,h):
    body=b[:HEADER]+b[HEADER+512:]
    h["body_sum32"]=sum(struct.unpack(f">{len(body)//4}I",body))&0xFFFFFFFF
    struct.pack_into(f">{len(FIELDS)}I",b,HEADER,*[h[x] for x in FIELDS])

class CaptureTests(unittest.TestCase):
    def test_original_capture(self):
        result,_=parse(make_capture()[0])
        self.assertEqual(result["seconds"][0]["completed_fps_count_domain"],24)
        self.assertTrue(result["header"]["sp_pc_meaningful_after_halt"])
    def test_byte_orders(self):
        b,_=make_capture()
        for width in (2,4):
            swapped=b"".join(b[i:i+width][::-1] for i in range(0,SIZE,width))
            self.assertEqual(parse(swapped)[0]["header"]["sample_count"],3)
    def test_wrapped_rings(self):
        result,_=parse(make_capture(samples=2100,events=70)[0])
        self.assertEqual(result["cpu_samples"][0],0x80000000+52*4)
        self.assertEqual(result["cpu_samples"][-1],0x80000000+2099*4)
        self.assertEqual(result["events"][0]["sequence"],7)
        self.assertEqual(result["events"][-1]["sequence"],70)
    def test_incomplete(self):
        b,h=make_capture();h["complete"]=0;commit(b,h)
        with self.assertRaisesRegex(ValueError,"incomplete"):parse(b)
    def test_payload_corruption(self):
        b,_=make_capture();b[0x6200]=1
        with self.assertRaisesRegex(ValueError,"checksum"):parse(b)
    def test_truncated(self):
        with self.assertRaisesRegex(ValueError,"32 KiB"):parse(bytes(1000))
    def test_bad_cursor(self):
        b,h=make_capture();h["pc_next_byte"]=16;commit(b,h)
        with self.assertRaisesRegex(ValueError,"cursor disagree"):parse(b)
    def test_running_pc_not_meaningful(self):
        b,h=make_capture();h["sp_status_after"]=0;h["halt_acknowledged"]=0;commit(b,h)
        self.assertFalse(parse(b)[0]["header"]["sp_pc_meaningful_after_halt"])
    def test_delay_slot_epc(self):
        b,h=make_capture();h["cpu_cause"]=0x80000000;commit(b,h)
        self.assertEqual(parse(b)[0]["header"]["cpu_epc_instruction"],0x80001004)
    def test_occupancy_mismatch(self):
        b,h=make_capture();struct.pack_into(">I",b,0x7200+5*4,101);commit(b,h)
        with self.assertRaisesRegex(ValueError,"buckets"):parse(b)
    def test_partial_is_separate(self):
        b,h=make_capture();struct.pack_into(">9I",b,HEADER+0x100,10,2,3,4,1,9,3,2,1)
        self.assertEqual(parse(b)[0]["header"]["partial_window"]["samples"],10)
    def test_unmatched_save(self):
        with self.assertRaisesRegex(ValueError,"no S64D"):parse(bytes(SIZE))
    def test_no_elf(self):
        result,_=parse(make_capture()[0])
        self.assertEqual(len(symbolicate(result)["cpu_hotspots"]),3)
    def test_dp_counter_wrap(self):
        b,h=make_capture()
        struct.pack_into(">4I",b,0x7800,0xFFFFF0,0,0,0)
        struct.pack_into(">4I",b,0x7810,0x10,0,0,0)
        commit(b,h)
        row=parse(b)[0]["events"][1]
        self.assertEqual(row["dp_cycle_deltas_mod24"][0],32)
        self.assertTrue(row["dp_counter_delta_unambiguous"])
    def test_dp_counter_long_gap(self):
        b,h=make_capture()
        struct.pack_into(">I",b,0x4240+4,46875000)
        commit(b,h)
        self.assertFalse(parse(b)[0]["events"][1]["dp_counter_delta_unambiguous"])
    def test_outer_exception_wait_site(self):
        b,h=make_capture();h['direct_wait_pc']=0x80002000;h['cpu_status']=0x8403
        commit(b,h)
        head=parse(b)[0]['header']
        self.assertEqual(head['capture_via'],'direct wait watchdog')
        self.assertEqual(head['cpu_epc'],0x80001000)
        self.assertEqual(head['direct_wait_pc'],0x80002000)
if __name__=="__main__":unittest.main()
