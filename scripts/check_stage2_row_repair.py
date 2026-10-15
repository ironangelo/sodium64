#!/usr/bin/env python3
"""Bound the compiled repair to one regular-BG row block and its source copy."""
import argparse
import struct
from pathlib import Path
from capture_stage2_publication import load_symbols
from check_rsp_branch_delay_slots import read_text


def elf_section(path, wanted):
    data = path.read_bytes()
    assert data[:6] == b'\x7fELF\x01\x02', path
    hdr = struct.unpack_from('>16sHHIIIIIHHHHHH', data)
    sections = [struct.unpack_from('>10I', data, hdr[6]+i*hdr[11])
                for i in range(hdr[12])]
    sec = sections[hdr[13]]
    names = data[sec[4]:sec[4]+sec[5]]
    for sec in sections:
        name = names[sec[0]:].split(b'\0', 1)[0].decode()
        if name == wanted:
            return sec[3], data[sec[4]:sec[4]+sec[5]]
    raise AssertionError((path, wanted))


def check(current, parent):
    main = current/'src/rsp_main.elf'
    old_main = parent/'src/rsp_main.elf'
    base, new = read_text(main)
    old_base, old = read_text(old_main)
    syms, old_syms = load_symbols(main), load_symbols(old_main)
    assert base == old_base == 0xa4001000 and len(new) == len(old) == 4096
    for name in ['draw_bg', 'draw_row', 'bg_windows', 'finish_row',
                 'draw_mode7_entry', 'rdp_send', 'overlay_load_slot', 'overlay_load_main']:
        assert syms[name] == old_syms[name], name
    first, end = syms['draw_row']-base, syms['bg_windows']-base
    assert new[:first] == old[:first] and new[end:] == old[end:], 'repair escaped row setup'
    words = struct.unpack(f'>{(end-first)//4}I', new[first:end])
    # SRL t3,s2,1 immediately precedes LBU t2,BGXSC(t3). Later mask lookup
    # uses that same t3. Check actual emitted operands, not a source comment.
    assert words[2:4] == (0x00125842, 0x916a0baa), words[:4]
    assert 0x00125042 not in words, 'redundant second recovery remains'
    assert 0x916a0e64 in words, 'SHIFT_TABLE lookup does not reuse recovered t3'
    assert elf_section(main, '.data') == elf_section(old_main, '.data')
    for name in ['rsp_mode7', 'rsp_hcomp']:
        for sec in ['.text', '.data']:
            assert elf_section(current/f'src/{name}.elf', sec) == elf_section(parent/f'src/{name}.elf', sec), (name, sec)
    cpu, old_cpu = current/'sodium64.elf', parent/'sodium64.elf'
    assert read_text(cpu) == read_text(old_cpu), 'CPU runtime text changed'
    data_base, data = elf_section(cpu, '.data')
    old_data_base, old_data = elf_section(old_cpu, '.data')
    assert data_base == old_data_base and len(data) == len(old_data)
    offset = load_symbols(cpu)['rsp_main_text_start']-data_base
    assert data[offset:offset+4096] == new
    assert old_data[offset:offset+4096] == old
    assert data[:offset] == old_data[:offset] and data[offset+4096:] == old_data[offset+4096:], 'other runtime data changed'
    print('STAGE2_ROW_REPAIR_BINARY_SCOPE PASS', current)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--current', type=Path, required=True)
    ap.add_argument('--parent', type=Path, required=True)
    args = ap.parse_args()
    check(args.current, args.parent)
