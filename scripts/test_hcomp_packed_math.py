#!/usr/bin/env python3
"""Execute the compiled packed bank against independent five-bit arithmetic.

Original numeric operands only. This is kernel instruction semantics and issue
count evidence, not RSP pipeline timing, ordinary rendering or native cadence.
"""
import argparse
import json
import random
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from native_diag_report import elf_symbols

TAGS = (0x400, 0xc00, 0x1400, 0x1c00, 0x2800, 0x3800, 0x5000)
ENABLES = (0x20, 1, 2, 4, 8, 0, 0x10)

def signed(x):
    return x - 65536 if x & 32768 else x

def rgba(x):
    return (x << 1) | 1

def reference(x, y, subtract, half):
    result = 0
    for shift in (0, 5, 10):
        a, b = (x >> shift) & 31, (y >> shift) & 31
        value = max(a - b, 0) if subtract else a + b
        result |= min(31, value // (2 if half else 1)) << shift
    return rgba(result)

def execute(code, base, start, stop, regs, vectors, memory=None, max_steps=512):
    """Subset decoder for the actual linked RSP instructions and delay slots."""
    r, v = regs[:], [x[:] for x in vectors]
    memory = memory or {}
    pc, pending, vco_lo, vco_hi, vcc = start, None, [False]*8, [False]*8, [False]*8
    for steps in range(max_steps):
        if pc == stop:
            return r, v, steps
        w = struct.unpack_from('>I', code, pc-base)[0]
        op, rs, rt, rd, shift, fn = w>>26, w>>21&31, w>>16&31, w>>11&31, w>>6&31, w&63
        imm = w & 65535
        si = imm if imm < 32768 else imm-65536
        target = None
        if not w:
            pass
        elif op == 0:
            if fn == 0: r[rd] = (r[rt] << shift) & 0xffffffff
            elif fn == 2: r[rd] = (r[rt] & 0xffffffff) >> shift
            else: raise AssertionError(('scalar special', hex(pc), hex(w)))
        elif op in (8, 9): r[rt] = (r[rs]+si) & 0xffffffff
        elif op == 12: r[rt] = r[rs] & imm
        elif op == 13: r[rt] = r[rs] | imm
        elif op in (4, 5):
            if (r[rs] == r[rt]) == (op == 4): target = pc+4+(si<<2)
        elif op == 36: r[rt] = memory[(r[rs]+si) & 0xfff]
        elif op == 18 and rs == 4:
            # MTC2 replaces two bytes starting at the instruction's element.
            element = w>>7 & 15
            assert not element & 1
            v[rd][element//2] = r[rt] & 65535
        elif op == 18 and rs == 2:
            assert rd == 1
            r[rt] = sum(int(c) << i for i, c in enumerate(vcc))
        elif op == 18 and rs & 16:
            element, vt, vs, vd = rs&15, rt, rd, shift
            assert element == 0 or 8 <= element <= 15
            a = v[vs][:]
            b = v[vt][:] if element == 0 else [v[vt][element-8]]*8
            if fn == 4: out = [(x*y)>>16 for x,y in zip(a,b)] # VMUDL unsigned high
            elif fn == 6: out = [(x*signed(y)) & 65535 for x,y in zip(a,b)] # VMUDN low
            elif fn in (0x10, 0x11):
                raw = [signed(x)+(signed(y) if fn==0x10 else -signed(y)) +
                       (int(c) if fn==0x10 else -int(c)) for x,y,c in zip(a,b,vco_lo)]
                out = [max(-32768,min(32767,x)) & 65535 for x in raw]
                vco_lo, vco_hi = [False]*8, [False]*8
            elif fn == 0x14:
                raw = [x+y for x,y in zip(a,b)]
                out = [x & 65535 for x in raw]
                vco_lo, vco_hi = [x>65535 for x in raw], [False]*8
            elif fn == 0x15:
                out = [(x-y)&65535 for x,y in zip(a,b)]
                vco_lo, vco_hi = [x<y for x,y in zip(a,b)], [x!=y for x,y in zip(a,b)]
            elif fn in (0x20, 0x21, 0x22, 0x23):
                if fn == 0x20: cond = [signed(x)<signed(y) or (x==y and lo and hi) for x,y,lo,hi in zip(a,b,vco_lo,vco_hi)]
                elif fn == 0x21: cond = [x==y and not hi for x,y,hi in zip(a,b,vco_hi)]
                elif fn == 0x22: cond = [x!=y or hi for x,y,hi in zip(a,b,vco_hi)]
                else: cond = [signed(x)>signed(y) or (x==y and not (lo and hi)) for x,y,lo,hi in zip(a,b,vco_lo,vco_hi)]
                out = [x if c else y for x,y,c in zip(a,b,cond)]
                vcc, vco_lo, vco_hi = cond, [False]*8, [False]*8
            elif fn == 0x27: out = [x if c else y for x,y,c in zip(a,b,vcc)]
            elif fn == 0x28: out = [x&y for x,y in zip(a,b)]
            elif fn == 0x2a: out = [x|y for x,y in zip(a,b)]
            elif fn == 0x2c: out = [x^y for x,y in zip(a,b)]
            else: raise AssertionError(('vector', hex(pc), hex(w), hex(fn)))
            v[vd] = out
        else:
            raise AssertionError(('unsupported instruction', hex(pc), hex(w)))
        assert pending is None or target is None, 'control transfer in delay slot'
        pc, pending = (pending if pending is not None else pc+4), target
        r[0] = 0
    raise AssertionError('kernel did not return')

def load(path):
    base, code = read_text(path)
    symbols = {name: addr for addr,name in elf_symbols(path)}
    return base, code, symbols

def seeds():
    v = [[0]*8 for _ in range(32)]
    v[15][0], v[16][0], v[16][1], v[19][0] = 1, 0x8000, 0x400, 31
    v[21] = [65535]*8
    return v

def initialize(image):
    base, code, symbols = image
    v = seeds()
    if 'hcomp_packed_add' in symbols:
        # Decode the linked constant prologue, stopping at first source LW.
        _, v, steps = execute(code, base, symbols['hcomp_math_sources'],
                               symbols['hcomp_math_sources']+40, [0]*32, v)
        assert steps == 10
    return v

def run_arithmetic(image, x, y, subtract, half, eligible):
    base, code, symbols = image
    v = initialize(image)
    v[0], v[1], v[7], v[13] = [rgba(a) for a in x], [rgba(a) for a in y], eligible, half
    r = [0]*32
    r[3] = 0x80 if subtract else 0
    _, out, steps = execute(code, base, symbols['hcomp_channels_start'],
                             symbols['hcomp_vector_output']+4, r, v)
    return out[0], steps

def check_arithmetic(image):
    # Every channel's 32x32 pair with different neighbor-channel mixtures.
    pairs = []
    for channel in range(3):
      for a in range(32):
       for b in range(32):
        for neighbors in (0, 1, 15, 16, 30, 31):
            x = (neighbors | ((31-neighbors)<<5) | ((neighbors^16)<<10))
            y = ((31-neighbors) | (neighbors<<5) | ((neighbors^1)<<10))
            mask = 31 << (5*channel)
            pairs.append(((x&~mask)|(a<<(5*channel)),(y&~mask)|(b<<(5*channel))))
    rng = random.Random(420614)
    pairs.extend((rng.randrange(32768),rng.randrange(32768)) for _ in range(8192))
    assert len(pairs)%8 == 0
    checked, counts = 0, {}
    for subtract in (False,True):
     for policy in (0,1,2):
      for offset in range(0,len(pairs),8):
        batch = pairs[offset:offset+8]
        x, y = map(list, zip(*batch))
        # Each pair gets FULL and HALF. A third pass mixes HALF and every
        # eight-bit eligibility pattern to exercise lane selection/VCO.
        half = [65535*policy]*8 if policy<2 else [65535 if (offset//8)>>(i%5)&1 else 0 for i in range(8)]
        eligible = [65535]*8 if policy<2 else [65535 if (offset//8)>>(i%8)&1 else 0 for i in range(8)]
        actual, steps = run_arithmetic(image,x,y,subtract,half,eligible)
        for i, (a,b) in enumerate(batch):
            want = reference(a,b,subtract,bool(half[i])) if eligible[i] else rgba(a)
            assert actual[i] == want, (subtract,offset,i,a,b,actual[i],want)
        counts['subtract' if subtract else 'add'] = steps
        checked += 8
    return checked, counts

def check_selection(image):
    base, code, symbols = image
    rng, checked = random.Random(0x364420), 0
    for mode in (0,0x40,0x80,0xc0):
     for source in (0,2):
      for effective_ts in (0,1):
       for enables in (0,1,2,4,8,0x10,0x20,0x15,0x2a,0x3f):
        for case in range(64):
            v = initialize(image)
            main = [rng.randrange(32768) for _ in range(8)]
            sub = [rng.randrange(32768) for _ in range(8)]
            fixed = rng.randrange(32768)
            tags = [TAGS[(case+i)%7] for i in range(8)]
            absent = [bool((case+i)%3==0) for i in range(8)]
            clip = [65535 if case>>i&1 else 0 for i in range(8)]
            allow = [65535 if (case*7+1)>>i&1 else 0 for i in range(8)]
            v[0], v[1], v[2], v[3] = list(map(rgba,main)), list(map(rgba,sub)), tags, [0x400 if a else 0xc00 for a in absent]
            v[4], v[5], v[22] = clip, allow, [rgba(fixed)]*8
            v[20][:6] = [tag if bit & enables else 0 for tag,bit in zip((0xc00,0x1400,0x1c00,0x2800,0x5000,0x400),(1,2,4,8,0x10,0x20))]
            r = [0]*32
            r[2],r[3] = 0xf0|source,mode|enables
            _, out, _ = execute(code,base,symbols['hcomp_math_mask_ready'],
                                symbols['hcomp_vector_output']+4,r,v,{0xec9:effective_ts})
            for i in range(8):
                color = main[i] if clip[i] else 0
                active = bool(ENABLES[TAGS.index(tags[i])] & enables and allow[i])
                operand = sub[i] if source and effective_ts and not absent[i] else fixed
                half = bool(mode&0x40 and clip[i] and not (source and (not effective_ts or absent[i])))
                want = reference(color,operand,bool(mode&0x80),half) if active else rgba(color)
                assert out[0][i] == want, dict(mode=mode,source=source,ts=effective_ts,enables=enables,case=case,lane=i,actual=out[0][i],expected=want)
            checked += 8
    return checked

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('packed',type=Path)
    ap.add_argument('--baseline',type=Path)
    ap.add_argument('--output',type=Path)
    a = ap.parse_args()
    packed = load(a.packed)
    pixels, counts = check_arithmetic(packed)
    selected = check_selection(packed)
    report = dict(passed=True,arithmetic_pixels=pixels,selection_pixels=selected,
                  compiled_core_issue_counts=counts,native_timing_authority=False,
                  ordinary_frame_authority=False,private_data=False)
    if a.baseline:
        baseline = load(a.baseline)
        b_pixels, b_counts = check_arithmetic(baseline)
        b_selected = check_selection(baseline)
        assert pixels == b_pixels and selected == b_selected
        report['baseline_compiled_core_issue_counts'] = b_counts
    if a.output: a.output.write_text(json.dumps(report,indent=2)+'\n')
    print('HCOMP_PACKED_COMPILED PASS',json.dumps(report))

if __name__ == '__main__': main()
