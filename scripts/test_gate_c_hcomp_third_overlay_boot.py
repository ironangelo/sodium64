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
