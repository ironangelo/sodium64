#!/usr/bin/env python3
import hashlib,unittest
import make_gate_c_hcomp_third_overlay_short as d
class T(unittest.TestCase):
    def test_rom(self):
        a=d.build_rom(); b=d.build_rom(); self.assertEqual(a,b); self.assertEqual(len(a),0x8000)
        self.assertEqual(a[0x7FD5],0x20); self.assertEqual(hashlib.sha256(a).digest(),hashlib.sha256(b).digest())
    def test_short_true_mode7(self):
        p=d.program()
        self.assertEqual(p.count(bytes((0xA9,d.TREATMENT_MODE,0x8D,0x05,0x21))),1)
        self.assertGreaterEqual(p.count(bytes((0xA9,d.CONTROL_MODE,0x8D,0x05,0x21))),2)
        self.assertEqual(d.IRQ2_LINE-d.IRQ1_LINE,2)
        self.assertLess(d.IRQ2_LINE,224)
    def test_completion_state(self):
        p=d.program()
        self.assertIn(bytes((0xA9,d.POSTTEST_PHASE,0x8F,0x01,0x00,0x7E)),p)
        self.assertIn(bytes((0xA9,1,0x8F,0x04,0x00,0x7E)),p)
if __name__=="__main__": unittest.main()
