#!/usr/bin/env python3
"""Reject bad captures while preserving useful fidelity-failure evidence."""
import struct
import unittest
from decode_stage2_probe import decode, qualify_workload, OFFSET, SIZE, HEAD_NAMES, window

def fixture():
    b=bytearray(32768)
    h=[0]*32
    h[:8]=[0x53363448,1,2,5,1200,65521,0x4020,0x100]
    h[8:13]=[60]*5;h[14:17]=[21,4,8];h[22]=1
    struct.pack_into('>32I',b,0,*h)
    struct.pack_into('>I',b,0x100,0x53363450)
    p=[0]*32
    values=dict(magic=0x53363456,version=1,size=SIZE,complete=1,valid=7,
                sp_status=1,vi_origin=0xF2300,vi_width=280,
                fb1=0xF2300,fb2=0x113000,fb3=0x133D00)
    for k,v in values.items():p[HEAD_NAMES.index(k)]=v
    struct.pack_into('>32I',b,OFFSET,*p)
    left,right=window(64)
    row=[1 if left<=x<=right else 0x7BC1 for x in range(256)]
    struct.pack_into('>4096H',b,OFFSET+0x80,*(row*8+[1]*2048))
    struct.pack_into('>256H',b,OFFSET+0x2080,*row)
    return b

class ProbeTests(unittest.TestCase):
    def test_valid_and_word_swapped(self):
        b=fixture();self.assertTrue(decode(bytes(b))[0]['band']['reference_matches'])
        swapped=b''.join(b[i:i+4][::-1] for i in range(0,len(b),4))
        self.assertTrue(decode(swapped)[0]['band']['reference_matches'])
    def test_rejects_pending_or_invalid_capture(self):
        for name,value in [('magic',0),('version',2),('size',SIZE+4),('complete',0),
                           ('valid',6),('sp_status',0),('sp_dma_busy',1),
                           ('sp_dma_full',1),('dp_status',0x10),('dp_current',4),
                           ('vi_width',256),('vi_origin',0xDEAD),('fb1',0xF2200),
                           ('dsp_pointer',8192),('dsp_pointer',3)]:
            with self.subTest(name=name,value=value):
                b=fixture();struct.pack_into('>I',b,OFFSET+HEAD_NAMES.index(name)*4,value)
                with self.assertRaises(ValueError):decode(bytes(b))
        with self.assertRaises(ValueError):decode(bytes(fixture()[:-1]))
    def test_green_is_valid_diagnostic_but_fails_yellow_reference(self):
        b=fixture()
        for start,count in [(0x80,2048),(0x2080,256)]:
            for i in range(count):
                at=OFFSET+start+2*i
                if struct.unpack_from('>H',b,at)[0]==0x7BC1:
                    struct.pack_into('>H',b,at,0x07C1)
        self.assertFalse(decode(bytes(b))[0]['band']['reference_matches'])
    def test_rejects_copy_disagreement(self):
        b=fixture();struct.pack_into('>H',b,OFFSET+0x2080,0)
        with self.assertRaisesRegex(ValueError,'independent buffer copy'):decode(bytes(b))
    def test_original_equal_channel_driver_and_corruption_controls(self):
        b=fixture()
        struct.pack_into('>I',b,OFFSET+64,255)
        for voice in range(8):
            off=OFFSET+0x2C90+16*voice
            b[off:off+8]=bytes((16,16,0,4+voice,0,0,0,127))
        b[OFFSET+0x2C90+0x4C]=255;b[OFFSET+0x2C90+0x5D]=5
        values=[((n%54)-27)*100 for n in range(1024)]
        struct.pack_into('>2048h',b,OFFSET+0x2D10,*[x for v in values for x in (v,v)])
        r,raw,_,_=decode(bytes(b));self.assertTrue(qualify_workload(r,raw,True)['equal_channels'])
        for off in [0x2D12,0x2C90,0x2C90+0x4C]:
            bad=bytearray(raw);bad[off]^=1
            with self.assertRaises(ValueError):qualify_workload(r,bad,True)
        silent=bytearray(raw);silent[0x2D10:]=bytes(4096)
        with self.assertRaises(ValueError):qualify_workload(r,silent,True)

if __name__=='__main__':unittest.main()
