#!/usr/bin/env python3
"""Original continuous-format fixtures: separate cutoff, boundary and fault."""
import struct, unittest
from native_diag_report import HEADER, parse, render
from test_native_diag_v4_report import make_blob, field

def make_v5(context=1):
    b=make_blob();field(b,'version',5)
    start=0xff000000;elapsed=20*46875000;cut=(start+elapsed)&0xffffffff
    field(b,'start_count',start);field(b,'stop_count',cut)
    field(b,'sp_status_after',1)
    boundary=(cut+4687500)&0xffffffff if context==1 else 0
    struct.pack_into('>5I',b,HEADER+0x1e0,0x434f4e35,cut,boundary,3,context)
    if context==3:
        field(b,'reason',1)
        struct.pack_into('>3I',b,HEADER+0x1f4,(cut+93750000)&0xffffffff,0x80001234,0x401)
    return b

class V5Tests(unittest.TestCase):
    def test_separate_measurement_and_guest_boundary(self):
        r,_=parse(make_v5());h=r['header']
        self.assertEqual(h['elapsed_seconds_count_domain'],20)
        self.assertEqual(h['boundary_delay_ticks'],4687500)
        self.assertTrue(h['measurement_and_guest_snapshot_are_distinct_instants'])
        self.assertFalse(h['renderer_forced_halt'])
        self.assertIn('measurement ends at IRQ cutoff',render(r))
    def test_fault_after_seal_keeps_original_denominator(self):
        h=parse(make_v5(3))[0]['header']
        self.assertEqual(h['elapsed_seconds_count_domain'],20)
        self.assertTrue(h['recorder_duration_excludes_later_fault_wait'])
        self.assertEqual(h['fault_wait_pc'],0x80001234)
    def test_terminal_fault_context(self):
        b=make_v5(2);field(b,'reason',1)
        self.assertTrue(parse(b)[0]['header']['renderer_forced_halt'])
    def test_bad_context_rejected(self):
        for off,value in ((0x1e0,0),(0x1e4,123),(0x1ec,0),(0x1f0,4)):
            b=make_v5();struct.pack_into('>I',b,HEADER+off,value)
            with self.assertRaises(ValueError):parse(b)
    def test_missing_natural_fence_rejected(self):
        b=make_v5();field(b,'sp_status_after',0)
        with self.assertRaises(ValueError):parse(b)
    def test_incomplete_or_corrupted_body_rejected(self):
        b=make_v5();field(b,'complete',0)
        with self.assertRaises(ValueError):parse(b)
        b=make_v5();b[0x7000]^=1
        with self.assertRaises(ValueError):parse(b)

if __name__=='__main__':unittest.main()
