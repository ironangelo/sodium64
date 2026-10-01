#!/usr/bin/env python3
"""Historical ordinary-build audit pinned to 01a5242 / artifact 11180227088.

Consumes immutable prior ELFs; no ROM, emulator writes or commercial assets.
Its compact-geometry BLOCKED finding describes that earlier renderer only.
Use check_smw_probe_admission.py for the repaired full-height runtime.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from capture_stage2_publication import load_symbols
from check_stage2_row_repair import elf_section
from check_event_arena import layout


def words(path, first, last):
    symbols = load_symbols(path)
    base, text = elf_section(path, '.text')
    return tuple(w[0] for w in struct.iter_unpack(
        '>I', text[symbols[first]-base:symbols[last]-base]))


def audit(qualified, parent, defines):
    normal = qualified/'normal/build'
    cpu = normal/'sodium64.elf'
    symbols = load_symbols(cpu)
    forbidden = [name for name in symbols
                 if name.startswith(('color_diag_', 'hw_profile_', 'profile_'))]
    assert not forbidden, ('normal build includes diagnostic/profile hooks', forbidden)
    assert symbols['sram_dirty'] and symbols['sram'] and symbols['input_update']
    # Exact ordinary startup, PI SRAM load/save, VI and controller paths.
    # Both authorities have the same addresses here; no relocation masking.
    old_cpu = parent/'normal/build/sodium64.elf'
    assert words(cpu, 'main', 'reset_interrupt') == words(old_cpu, 'main', 'reset_interrupt')
    # Positive controls ensure the diagnostic symbols really are observable.
    hw = load_symbols(qualified/'hw-profile/build/sodium64.elf')
    color = load_symbols(qualified/'color/build/sodium64.elf')
    assert 'profile_init' in hw and 'hw_profile_done' in hw
    assert 'color_diag_init' in color and 'color_diag_vi_entry' in color
    for variant in ('normal', 'hw-profile', 'color'):
        for name in ('rsp_main', 'rsp_mode7', 'rsp_hcomp'):
            for section in ('.text', '.data'):
                path = f'{variant}/build/src/{name}.elf'
                assert elf_section(qualified/path, section) == elf_section(parent/path, section)
    main, hcomp = normal/'src/rsp_main.elf', normal/'src/rsp_hcomp.elf'
    ms, hs = load_symbols(main), load_symbols(hcomp)
    for name, address in {'draw_bg': 0xa40013a8, 'next_layer': 0xa4001370,
                          'draw_mode7_entry': 0xa4001788, 'rdp_send': 0xa4001f5c}.items():
        assert ms[name] == address, name
    assert hs['hcomp_screen_switch'] == 0xa4001760
    assert hs['hcomp_entry'] == 0xa40013b0
    # Actual unconditional compact Color Image selection, before section DMA.
    frame = words(main, 'draw_frame', 'next_section')
    assert frame[-9:-5] == (0x3c08000e, 0x35081d00, 0x8fa90be0, 0xac080c4c)
    # Only k0==0 is tested before Z commands: k1/height is not admitted here.
    assert words(main, 'not_blank', 'hcomp_proof_bound_done') == (
        0x17400003, 0x24040f30, 0x0d0007d7, 0x24050f50)
    end = words(hcomp, 'hcomp_provenance_end', 'hcomp_output_start')
    assert end[:3] == (0x17400097, 0x24080008, 0x17680095)
    db, data = elf_section(main, '.data')
    # Set Z Image's physical base from the actual immutable RDP table.
    z_base = struct.unpack_from('>I', data, ms['hcomp_proof_rdp_cmds']-db+20)[0]
    assert z_base == 0xdfd00
    owners = layout(defines)
    findings = []
    # SETINI=0 gives border8 + renderer offset8 = global y16 (224 lines).
    # These are conservative whole-row envelopes, not observed game captures.
    for name, image_base in [('sub_color', 0xe1d00), ('main_winner', z_base)]:
        start = image_base + 16*280*2
        bounded_end, full_end = start+8*280*2, start+224*280*2
        assert owners[name] == (start, bounded_end)
        intersections = [n for n, (a, b) in owners.items()
                         if n != name and start < b and full_end > a]
        assert 'preserved_ts' in intersections and 'FRAMEBUFFER1' in intersections
        findings.append(dict(surface=name, start=hex(start), owned_end=hex(bounded_end),
                             full_height_end=hex(full_end), crossed_owners=intersections))
    return dict(normal_profile_passed=True, diagnostic_hooks_absent=True,
                ordinary_sram_and_input_instructions_unchanged=True,
                sram_roundtrip_executed=False, rsp_sections_unchanged=True,
                hcomp_dispatch_retained=True, geometry_admission='BLOCKED',
                game_ready=False, commercial_rom_executed=False,
                normal_elf_sha256=hashlib.sha256(cpu.read_bytes()).hexdigest(),
                full_height_analysis='static conservative envelopes; not an SMW capture',
                compact_surface_findings=findings)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--qualified', type=Path, required=True)
    ap.add_argument('--parent', type=Path, required=True)
    ap.add_argument('--defines', type=Path, default=Path('src/defines.h'))
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result = audit(args.qualified, args.parent, args.defines)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print('NORMAL_PROFILE PASS; HCOMP retained; FULL_HEIGHT_GAME_ADMISSION BLOCKED')
