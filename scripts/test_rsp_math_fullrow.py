#!/usr/bin/env python3
"""Linked full-row Math, byte-exact VRAM backup and Phase return guard.

Original numeric inputs only. Setup is seeded; linked RSP instructions and
delayed DMA execute in the existing subset VM. No RDP rasterization or native
timing claim. --baseline-only checks this fixture before a candidate is built.
"""
import argparse
import hashlib
import json
import random
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_eligibility_tags import emission
from test_hcomp_packed_math import ENABLES, TAGS, reference, rgba, seeds
from test_hcomp_sub_presence import section
from test_rsp_math_dma import MathVM, PHASE_BANK, ROOT, halves, put, symbols


def load(path):
    base, code = read_text(path)
    return base & 0xfff, code, symbols(path)


class FullRowVM(MathVM):
    def __init__(self, *args, vram, oam, backup, expect_full, **kwargs):
        super().__init__(*args, **kwargs)
        self.vram_start, self.vram_before = vram
        self.oam_start, self.oam_before = oam
        self.backup, self.expect_full = backup, expect_full
        self.backup_retired = False
        self.restored_before_phase = False

    def queue_dma(self, write, length):
        # This assertion runs before the overlay starts, not after its return.
        if self.spaddr & 0x1000:
            assert self.dmem[self.vram_start:self.vram_start+1024] == self.vram_before, 'VRAM not restored before Phase'
            assert self.dmem[self.oam_start:self.oam_start+len(self.oam_before)] == self.oam_before, 'OAM changed before Phase'
            assert self.backup_retired == self.expect_full, 'backup retirement missing or unexpected'
            self.restored_before_phase = True
        super().queue_dma(write, length)
        p = self.dma
        if not p['imem'] and p['ram'] == self.backup:
            assert self.expect_full and p['sp'] == self.vram_start and p['size'] == 1024, 'backup DMA ABI'
            if not p['write']:
                assert self.backup_retired, 'restore started before backup retired'

    def poll_dma(self):
        pending = self.dma.copy() if self.dma else None
        result = super().poll_dma()
        if pending and not result and not pending['imem'] and pending['ram'] == self.backup and pending['write']:
            assert self.ram[self.backup:self.backup+1024] == self.vram_before, 'backup not byte exact'
            self.backup_retired = True
        return result


def run_case(main, math, phase, c, case_id, backup, stage, full=False, fault=None, sub_alpha=None):
    addr = parse_macros(ROOT).name
    main_code, initial, main_symbols = main
    math_base, math_code, math_symbols = math
    phase_code, phase_symbols = phase
    name, rows, y, cgwsel, ts, cgadsub, masks, wide = c
    has_sub = bool(cgwsel & 2 and ts)
    alpha = 'hcomp_alpha_inputs' in math_symbols and sub_alpha is not False
    row_fixed = not cgwsel & 0xf2
    admitted = bool(full and wide and has_sub)
    batch = 512 if admitted else 256 if wide else 64
    queue, pad = (case_id & 1) * 4, ((y+8)*16) & 63
    framebuffer = 0xf2300
    origins = [addr(n) & 0x1fffffff for n in ('HCOMP_SUB_ORIGIN', 'HCOMP_WINNER_ORIGIN', 'HCOMP_PRESENCE_ORIGIN')]
    starts = [framebuffer+y*560+24]+[origin+24-pad for origin in origins]
    fixed_ptr = addr('HCOMP_ROW_FIXED_QUEUE1' if not queue else 'HCOMP_ROW_FIXED_QUEUE2') & 0x1fffffff
    d = bytearray((i*37+11) & 255 for i in range(4096))
    ram = bytearray([0xa5])*0x400000
    rng = random.Random(0x46524f57+case_id)
    fixed_rows = [rgba((i*977+0x421) & 0x7fff) for i in range(256)]
    halves(ram, fixed_ptr, fixed_rows)
    fixed = (0x1234+case_id*31) & 0x7fff
    clip, allow = masks if masks else ([0xffff]*256, [0xffff]*256)
    halves(d, addr('TILE_TABLE'), clip)
    halves(d, addr('TILE_TABLE')+512, fixed_rows if row_fixed else allow)
    put(d, addr('OVERLAY_HCOMP_SRC'), PHASE_BANK | 3)
    put(d, addr('HCOMP_ROW_FIXED_SRC'), fixed_ptr)
    for i, origin in enumerate(starts[1:]):
        put(d, addr('HCOMP_BAND_BASES')+4*i, origin)
    put(d, addr('HCOMP_BAND_ROWS'), rows)
    d[addr('HCOMP_EFFECTIVE_TS')] = ts
    sm = addr('NATIVE_DIAG_SIGNAL_MASKS')
    d[sm:sm+16] = initial[sm:sm+16]
    struct.pack_into('>H', d, addr('NATIVE_DIAG_RSP_BANK'), 0x1235)
    ram[PHASE_BANK:PHASE_BANK+1000] = phase_code
    expected_rows = []
    for row in range(rows):
        main_pixels = [rng.randrange(32768) for _ in range(256)]
        sub_pixels = [rng.randrange(32768) for _ in range(256)]
        main_pixels[0], main_pixels[255] = (row*31) & 0x7fff, 0x7fff
        sub_pixels[0], sub_pixels[255] = 0x7fff, (row*0x421) & 0x7fff
        tags = [TAGS[(x+row) % len(TAGS)] for x in range(256)]
        absent = [(x+row) % 5 == 0 for x in range(256)]
        # Opaque black must remain present; absence must not depend on RGB.
        sub_pixels[1] = 0
        sub_words = [rgba(pixel) & (0xfffe if alpha and missing else 0xffff)
                     for pixel, missing in zip(sub_pixels, absent)]
        streams = (list(map(rgba, main_pixels)), sub_words,
                   stage(cgadsub, tags), [0x400 if a else 0xc00 for a in absent])
        for start, values in zip(starts, streams):
            halves(ram, start+row*560, values)
        fixed_operand = fixed_rows[y+row] >> 1 if row_fixed else fixed
        result = []
        for x in range(256):
            color = (rgba(main_pixels[x]) & clip[x]) >> 1
            eligible = bool(ENABLES[TAGS.index(tags[x])] & cgadsub and allow[x])
            operand = sub_pixels[x] if has_sub and not absent[x] else fixed_operand
            half = bool(cgadsub & 0x40 and clip[x] and not (cgwsel & 2 and (not ts or absent[x])))
            result.append(reference(color, operand, bool(cgadsub & 0x80), half) if eligible else rgba(color))
        expected_rows.append(result)
    before = bytes(d)
    expected_ram = ram.copy()
    for row, values in enumerate(expected_rows):
        halves(expected_ram, starts[0]+row*560, values)
    if admitted:
        expected_ram[backup:backup+1024] = before[addr('VRAM_TABLE'):addr('OAM')]
    regs = [0xcafe0000+i for i in range(32)]
    regs[0], regs[2], regs[3], regs[16], regs[26], regs[29] = 0, cgwsel, cgadsub, starts[0], y, queue
    # Setup publishes this state; its actual linked producer is checked by
    # test_rsp_sub_alpha.py. Mode7 and absent Sub retain the old Z consumer.
    regs[30] = 0x10 if alpha and ts else 0
    vectors = seeds()
    vectors[22] = [rgba(fixed)]*8
    for i in range(23, 31):
        vectors[i] = [rng.randrange(65536) for _ in range(8)]
    constants = [v[:] for v in vectors[23:32]]
    owners = set(range(addr('SCRN_DATA'), addr('SCRN_DATA')+256))
    if wide:
        owners.update(range(addr('TILE_TABLE'), addr('OAM') if admitted else addr('VRAM_TABLE')))
    bank = addr('NATIVE_DIAG_RSP_BANK')
    owners.update((bank, bank+1))
    code = bytearray(main_code)
    code[math_base:math_base+len(math_code)] = math_code
    vm = FullRowVM(code, d, ram, regs, vectors, 2+case_id % 3, owners,
                   vram=(addr('VRAM_TABLE'), before[addr('VRAM_TABLE'):addr('OAM')]),
                   oam=(addr('OAM'), before[addr('OAM'):addr('SCRN_DATA')]), backup=backup, expect_full=admitted)
    vm.pc = math_symbols['hcomp_math_sources']
    if fault == 'skip_restore':
        at = math_symbols['hcomp_fullrow_restore']+4
        word = struct.unpack_from('>I', vm.code, at)[0]
        assert word >> 26 == 5
        put(vm.code, at, (4 << 26) | (word & 0xffff))
    elif fault == 'short_backup':
        at = math_symbols['hcomp_fullrow_admission']+36
        word = struct.unpack_from('>I', vm.code, at)[0]
        assert word & 0xffff == 1023
        put(vm.code, at, (word & 0xffff0000) | 511)
    elif fault == 'oam_overlap':
        # The presence DMA is retired in R44. Mutate the live Sub source
        # instead, so this guard still exercises an actual OAM overwrite.
        at = math_symbols['hcomp_fullrow_admission']+(48 if alpha else 52)
        word = struct.unpack_from('>I', vm.code, at)[0]
        assert word >> 26 == 8 and word & 0xffff == 1024
        put(vm.code, at, (word & 0xffff0000) | (2048 if alpha else 1280))
    elif fault == 'presence_dma':
        anchors = [pc for pc in range(math_symbols['hcomp_batch'], math_symbols['hcomp_optional_sub_done'], 4)
                   if (struct.unpack_from('>I', vm.code, pc)[0] >> 26 == 5 and
                       struct.unpack_from('>I', vm.code, pc)[0] >> 21 & 31 == 30)]
        assert len(anchors) == 1
        at = anchors[0]
        word = struct.unpack_from('>I', vm.code, at)[0]
        put(vm.code, at, (4 << 26) | (word & 0x03ffffff))
    steps = vm.execute(phase_symbols['hcomp_band_done'], require_phase=True)
    assert vm.ram == expected_ram, ('output or RDRAM owner changed', name)
    assert d[addr('VRAM_TABLE'):addr('OAM')] == before[addr('VRAM_TABLE'):addr('OAM')], 'VRAM byte-exact return'
    assert d[addr('OAM'):addr('SCRN_DATA')] == before[addr('OAM'):addr('SCRN_DATA')], 'OAM owner changed'
    assert all(d[i] == before[i] for i in range(4096) if i not in owners), 'unowned DMEM changed'
    assert vm.restored_before_phase and vm.dma is None and vm.branch is None
    assert vectors[23:32] == constants and vectors[20] == [0]*8
    assert regs[29] == queue and regs[16] == starts[0]+rows*560
    assert vm.code == main_code[:math_base]+phase_code+main_code[math_base+1000:], 'Phase slot differs'
    if vm.signal_profile:
        assert vm.signal_writes == [0, 3] and vm.sp_status >> 11 & 7 == 3
        assert vm.sp_status & ~(7 << 11) == vm.initial_sp_status & ~(7 << 11)
    data = [t for t in vm.transfers if not t['imem']]
    expected = [(True, backup, 1024, addr('VRAM_TABLE'))] if admitted else []
    for row in range(rows):
        if row_fixed:
            expected.append((False, (fixed_ptr+2*(y+row)) & ~7, 8, addr('SCRN_DATA')))
        for offset in range(0, 512, batch):
            scratch = addr('TILE_TABLE') if wide else addr('SCRN_DATA')
            win = 512 if admitted else 2*batch
            sub = 1024 if admitted else batch
            present = 1536 if admitted else 3*batch
            expected.extend(((False, starts[0]+row*560+offset, batch, scratch),
                             (False, starts[2]+row*560+offset, batch, scratch+win)))
            if has_sub:
                expected.append((False, starts[1]+row*560+offset, batch, scratch+sub))
                if not alpha:
                    expected.append((False, starts[3]+row*560+offset, batch, scratch+present))
            expected.append((True, starts[0]+row*560+offset, batch, scratch))
    if admitted:
        expected.append((False, backup, 1024, addr('VRAM_TABLE')))
    assert [(t['write'], t['ram'], t['size'], t['sp']) for t in data] == expected, ('DMA row ABI', name)
    pixels = b''.join(vm.ram[starts[0]+row*560:starts[0]+row*560+512] for row in range(rows))
    return dict(case=name, rows=rows, queue_slot=queue//4, batch_pixels=batch//2, sub_alpha=alpha,
                data_dma_calls=len(data), data_dma_bytes=sum(t['size'] for t in data),
                row_dma_calls=(len(data)-2 if admitted else len(data))//rows,
                backup_restore_calls=2 if admitted else 0, vram_restore_before_phase=True,
                oam_unchanged=True, instruction_steps=steps, output_sha256=hashlib.sha256(pixels).hexdigest())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('main', type=Path)
    ap.add_argument('math', type=Path)
    ap.add_argument('phase', type=Path)
    ap.add_argument('--baseline', type=Path, required=True, help='same MASK/TAGS Math with FULL_ROW=0')
    ap.add_argument('--backup-address', type=lambda v: int(v, 0), default=0xd2400,
                    help='physical Q1 sideband: 0xd2400 trace, 0xd4400 audio trace, 0xc2400 ordinary')
    ap.add_argument('--baseline-only', action='store_true', help='fixture validation only; no candidate PASS')
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    mb, mc, ms = load(a.main)
    candidate, baseline = load(a.math), load(a.baseline)
    pb, pc, ps = load(a.phase)
    initial = section(a.main, '.data')
    assert mb == 0 and pb == candidate[0] == baseline[0] == 0x3a8
    assert len(mc) == len(initial) == 4096 and len(pc) == len(candidate[1]) == len(baseline[1]) == 1000
    assert a.backup_address in (0xd2400, 0xd4400, 0xc2400)
    for image in (candidate, baseline):
        assert image[2]['hcomp_screen_switch'] == 0x760 and image[2]['draw_mode7_entry'] == 0x788
    if not a.baseline_only:
        assert 'hcomp_fullrow_admission' in candidate[2] and 'hcomp_fullrow_restore' in candidate[2], 'candidate FULL_ROW flag absent'
        assert 'hcomp_fullrow_admission' not in baseline[2], 'baseline already full row'
        def core(image):
            base, code, syms = image
            return code[syms['hcomp_channels_start']-base:syms['hcomp_vector_output']+4-base]
        assert core(candidate) == core(baseline), 'RGB555 arithmetic kernel changed'
    cache = {}
    def stage(cg, tags):
        key = cg & 0x3f
        if key not in cache:
            cache[key] = [emission(mc, ms, initial, key, 1, kind) for kind in range(7)]
        return [cache[key][TAGS.index(tag)] for tag in tags]
    main_image, phase = (mc, initial, ms), (pc, ps)
    cases = [
        ('flat_add', 1, 0, 2, 1, 0x3f, None, True),
        ('flat_half_add', 3, 7, 2, 31, 0x7f, None, True),
        ('flat_sub', 7, 123, 2, 1, 0xbf, None, True),
        ('last_row_half_sub', 1, 239, 2, 1, 0xff, None, True),
        ('full_height', 240, 0, 2, 31, 0x7f, None, True),
    ]
    for clip, allow in ((0, 0), (0, 0xffff), (0xffff, 0), (0xffff, 0xffff)):
        cases.append((f'scanned_{clip:04x}_{allow:04x}', 3, 7, 0x52, 1, 0xff,
                      ([clip]*256, [allow]*256), True))
    cases.extend((
        ('row_fixed_unchanged', 7, 121, 0, 0, 0x7f, None, True),
        ('absent_sub_unchanged', 3, 7, 2, 0, 0xff, None, True),
        ('nonuniform_narrow', 3, 11, 0x52, 1, 0xbf,
         ([0xffff]*255+[0], [0xffff]*256), False),
    ))
    old, new = [], []
    for i, case in enumerate(cases):
        old.append(run_case(main_image, baseline, phase, case, i, a.backup_address, stage))
        if not a.baseline_only:
            new.append(run_case(main_image, candidate, phase, case, i, a.backup_address, stage, full=True))
            assert new[-1]['output_sha256'] == old[-1]['output_sha256'], ('baseline pixels differ', case[0])
    mode7 = []
    alpha = 'hcomp_alpha_inputs' in candidate[2]
    if alpha and not a.baseline_only:
        for i in (0, 3, 11):
            result = run_case(main_image, candidate, phase, cases[i], i, a.backup_address,
                              stage, full=True, sub_alpha=False)
            assert result['output_sha256'] == old[i]['output_sha256'], 'Mode7 Z fallback differs'
            mode7.append(result)
    negatives = []
    if not a.baseline_only:
        faults = [('skip_restore', 'VRAM not restored before Phase'),
                               ('short_backup', 'backup DMA ABI'),
                               ('oam_overlap', 'DMA overwrote DMEM owner')]
        if alpha:
            faults.append(('presence_dma', 'DMA row ABI'))
        for fault, message in faults:
            try:
                run_case(main_image, candidate, phase, cases[0], 0, a.backup_address, stage, full=True, fault=fault)
            except AssertionError as e:
                assert message in str(e), (fault, str(e))
                negatives.append(fault)
            else:
                raise AssertionError(('negative guard accepted linked fault', fault))
    report = dict(fixture_passed=True, candidate_passed=not a.baseline_only, baseline_only=a.baseline_only,
                  scope='linked_math_bank_with_seeded_setup_and_delayed_dma', cases=len(cases),
                  pixels=sum(c[1] for c in cases)*256, hardware_mocked=True,
                  native_timing_authority=False, rdp_rasterization_authority=False, private_data=False,
                  backup_address=hex(a.backup_address), candidate_case_results=new, baseline_case_results=old,
                  mode7_z_fallback_results=mode7, sub_alpha=alpha,
                  negative_guards=negatives, elf_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (a.main, a.math, a.phase, a.baseline)})
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, indent=2)+'\n')
    print('RSP_MATH_FULLROW', 'FIXTURE_ONLY_PASS' if a.baseline_only else 'PASS',
          json.dumps({k:v for k,v in report.items() if k not in ('candidate_case_results', 'baseline_case_results', 'mode7_z_fallback_results', 'elf_sha256')}))


if __name__ == '__main__':
    main()
