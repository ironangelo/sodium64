import struct
import unittest
from test_stage2_probe import fixture as probe_fixture
from decode_stage2_color import decode, COLORS, qualify
from make_gate_c_stage1 import window

def fixture():
    b=probe_fixture()
    b[:0x4200]=bytes(0x4200)
    h=[0]*64
    h[:14]=[0x53363443,1,32768,1,320,48,300,300,0,256,0x4200,0x3D10,0x202,0x3202]
    h[14:20]=[100,93750100,93750200,187500200,0xF2300,0xF2300]
    h[26:28]=[0x7BC1]*2;h[32:37]=[60]*5;h[37]=0x15040800;h[40]=7;h[41]=3
    struct.pack_into('>64I',b,0,*h)
    for o in (80,92):struct.pack_into('>6H',b,o,*COLORS)
    for i in range(300):
        left,right=window(i&255)
        r=[i+1,1000000+i*781250,0xF2300,i+1,left<<24|right<<16,
           0,0x81,0xA68,0xA68,0x7BC10001,0xF8017BC1,0]
        struct.pack_into('>12I',b,256+i*48,*r)
    return b

class ColorTests(unittest.TestCase):
    def test_valid_trace_and_word_swap(self):
        b=fixture();r,_,raw,_,_=decode(b)
        self.assertTrue(qualify(r,raw,False)['silent'])
        swapped=b''.join(b[i:i+4][::-1] for i in range(0,len(b),4))
        self.assertEqual(decode(swapped)[0]['records'],r['records'])
    def test_format_and_bounds_failures(self):
        for off,value in [(4,2),(12,0),(16,321),(20,52),(24,301),(28,321),
                          (36,0),(40,0),(52,0x202),(60,99),(76,0x113000),
                          (148,0),(160,6),(164,1),(256,2)]:
            with self.subTest(off=off):
                b=fixture();struct.pack_into('>I',b,off,value)
                with self.assertRaises(ValueError):decode(b)
        with self.assertRaises(ValueError):decode(fixture()[:-1])
    def test_valid_capture_retains_memory_failure(self):
        for off,value in [(256+36,0x07C10001),(256+40,0x003F7BC1),
                          (256+16,0xFFFF0001),(80,0),(104,0x07C1)]:
            b=fixture();struct.pack_into('>I',b,off,value)
            r,_,raw,_,_=decode(b)
            with self.assertRaises(ValueError):qualify(r,raw,False)
    def test_dropped_trace_is_explicit(self):
        b=fixture()
        struct.pack_into('>I',b,24,301);struct.pack_into('>I',b,32,1)
        r,_,raw,_,_=decode(b);self.assertFalse(r['trace_complete'])
        with self.assertRaisesRegex(ValueError,'dropped'):qualify(r,raw,False)
    def test_source_phase_and_clock_corruption(self):
        for off,value in [(256+48+12,20),(256+48+4,1000000),(256+44,3),(256+48+4,2400000)]:
            b=fixture();struct.pack_into('>I',b,off,value)
            with self.assertRaises(ValueError):
                r,_,raw,_,_=decode(b);qualify(r,raw,False)
if __name__=='__main__':unittest.main()
