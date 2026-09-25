#!/usr/bin/env python3
from __future__ import annotations
import hashlib, unittest
import make_gate_c_hcomp_third_overlay_boot as d

class Tests(unittest.TestCase):
    def test_deterministic_lorom(self):
        a=d.build_rom(); b=d.build_rom()
        self.assertEqual(a,b); self.assertEqual(len(a),0x8000)
        self.assertEqual(a[0x7FD5],0x20)
        self.assertEqual(hashlib.sha256(a).digest(),hashlib.sha256(b).digest())
    def test_exact_midframe_requests(self):
        p=d.build_program()
        m7=bytes((0xA9,d.TREATMENT_MODE,0x8D,0x05,0x21))
        m1=bytes((0xA9,d.CONTROL_MODE,0x8D,0x05,0x21))
        self.assertEqual(p.count(m7),1)
        self.assertGreaterEqual(p.count(m1),2)
        self.assertLess(d.IRQ1_LINE,d.IRQ2_LINE)
        self.assertLess(d.IRQ2_LINE,224)
        self.assertEqual(d.IRQ2_LINE-d.IRQ1_LINE,2)
    def test_enabled_mode7_bounds_heavy_work_to_two_tiles(self):
        p=d.build_program()
        self.assertEqual(p.count(bytes((0xA9,0x01,0x8D,0x2C,0x21))),1)
        self.assertNotIn(bytes((0xA9,0x00,0x8D,0x2C,0x21)),p)
        self.assertEqual(p.count(bytes((0xA9,d.M7_EMPTY,0x8D,0x1A,0x21))),1)
        self.assertEqual(d.M7_EMPTY&0xC0,0x80)

        def word_seq(value,address):
            return bytes((
                0xA9,value&0xFF,0x8D,address&0xFF,(address>>8)&0xFF,
                0xA9,(value>>8)&0xFF,0x8D,address&0xFF,(address>>8)&0xFF,
            ))

        self.assertEqual(p.count(word_seq(d.M7_A,0x211B)),1)
        for address in (0x211C,0x211D,0x211E,0x211F,0x2120):
            self.assertEqual(p.count(word_seq(0,address)),1)
        self.assertEqual(d.M7_A,0x4000)
        self.assertEqual(d.M7_CENTER,0)

    def test_irq_is_boot_armed_without_nmi(self):
        p=d.build_program()
        self.assertIn(bytes((0xA9,0x20,0x8D,0x00,0x42)),p)
        self.assertIn(bytes((0xA9,0x00,0x8D,0x00,0x42)),p)
        self.assertEqual(int.from_bytes(d.build_rom()[0x7FEE:0x7FF0],"little"),d.IRQ_ADDRESS)
        self.assertEqual(int.from_bytes(d.build_rom()[0x7FFE:0x8000],"little"),d.IRQ_ADDRESS)
    def test_same_frame_evidence_slots(self):
        p=d.build_program()
        self.assertEqual(p.count(bytes((0x8F,0x05,0x00,0x7E))),2)
        self.assertEqual(p.count(bytes((0x8F,0x06,0x00,0x7E))),2)
        self.assertIn(bytes((0xA9,d.POSTTEST_PHASE,0x8F,0x01,0x00,0x7E)),p)

if __name__=="__main__":
    unittest.main()
