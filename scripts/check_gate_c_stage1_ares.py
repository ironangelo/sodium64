#!/usr/bin/env python3
"""Complete 2048-pixel expected output; historical sample mailboxes are unused."""
import argparse
import json
from pathlib import Path
from make_gate_c_stage1 import MODES
from check_gate_c_hcomp_transparent_sub_ares import require_queue
from check_gate_c_hcomp_main_provenance_ares import (
    expected_sub, expected_provenance, require_fence,
    PROVENANCE_PREFIX, PROVENANCE_SUFFIX,
)
from check_gate_c_hcomp_main_sub_pixels_ares import classify_surface, SENTINEL
from test_gate_c_h_comp_window_contract import decode_select, ares_color_enable_pixel


def pixel(mode, x):
    if mode == 'fixed':
        return 0x781F
    if mode == 'absent':
        return 0xF83F
    mask = {'control': 2, 'clip': 0x82, 'prevent': 0x22, 'both': 0xA2}[mode]
    kwargs = dict(cfg=decode_select(2, 0), one_left=64, one_right=191,
                  two_left=0, two_right=0)
    visible = ares_color_enable_pixel(x, color_mask=mask >> 6, **kwargs)
    permitted = ares_color_enable_pixel(x, color_mask=(mask >> 4) & 3, **kwargs)
    channels = (31 if visible else 0, 0, 0)
    if permitted:
        channels = tuple((a + b) // 2 if visible else min(31, a + b)
                         for a, b in zip(channels, (0, 31, 0)))
    r, g, b = channels
    return (r << 11) | (g << 6) | (b << 1) | 1


def classify(root, mode):
    require_fence(root)
    cgwsel = {'fixed': 0, 'absent': 2, 'control': 2, 'clip': 0x82,
              'prevent': 0x22, 'both': 0xA2}[mode]
    queue = require_queue(root, cgwsel=cgwsel, ts=0 if mode == 'absent' else 2)
    want = [pixel(mode, x-12) if 8 <= y < 16 and 12 <= x < 268 else SENTINEL
            for y in range(16) for x in range(280)]
    candidates = []
    for i in range(1, 4):
        data = (root / f'main{i}.bin').read_bytes()
        report = classify_surface(data, want, 16, f'main{i}')
        if report['passed']:
            candidates.append((i, report))
        elif not classify_surface(data, [SENTINEL] * len(want), 16, f'main{i}')['passed']:
            raise ValueError(f'{mode}: unexpected output in main{i}: {report}')
    if len(candidates) != 1:
        raise ValueError(f'{mode}: expected exactly one fully composed Main: {candidates}')
    for name, expected in (
        ('sub.bin', expected_sub(0x003F if mode == 'absent' else 0x07C1)),
        ('provenance.bin', expected_provenance(0x0C00)),
        ('ts-provenance.bin', expected_provenance(0x0400 if mode == 'absent' else 0x1400)),
    ):
        report = classify_surface((root / name).read_bytes(), expected, 8, name)
        if not report['passed']:
            raise ValueError(f'{mode}/{name}: {report}')
    for prefix in ('provenance', 'ts-provenance'):
        if (root / f'{prefix}-prefix.bin').read_bytes() != PROVENANCE_PREFIX:
            raise ValueError(f'{mode}: {prefix} prefix overwritten')
        if (root / f'{prefix}-suffix.bin').read_bytes() != PROVENANCE_SUFFIX:
            raise ValueError(f'{mode}: {prefix} suffix overwritten')
    return dict(passed=True, pixels=2048, main=candidates[0][0], queue=queue)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--captures', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    result = dict(classification='STAGE1_STATIC_BAND_VALIDATED', passed=True,
                  modes={m: classify(args.captures / m, m) for m in MODES},
                  real_n64='NOT_PROVEN', full_frame='NOT_PROVEN')
    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    print(text, end='')
    if args.output:
        args.output.write_text(text)


if __name__ == '__main__':
    main()
