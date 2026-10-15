#!/usr/bin/env python3
"""Published dispatch ABI and identical resident helper contract for Stage 1."""
import argparse
from pathlib import Path
from test_gate_c_hcomp_main_sub_exec_clean import syms, text_size


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--maps', nargs=3, type=Path, required=True)
    ap.add_argument('--symbols', nargs=3, type=Path, required=True)
    args = ap.parse_args()
    tables = [syms(p) for p in args.symbols]
    for i, table in enumerate(tables):
        expected = dict(draw_bg=0xA40013A8, draw_mode7_entry=0xA4001788)
        if i < 2:
            expected.update(draw_frame=0xA400103C, next_section=0xA40010C0,
                            draw_obj=0xA4001790, calc_window_spans=0xA4001CE4,
                            dma_write=0xA4001F08, dma_read=0xA4001F40,
                            rdp_send=0xA4001F5C, overlay_load_slot=0xA4001F7C,
                            overlay_load_main=0xA4001F90)
            assert text_size(args.maps[i]) == 0x1000
        else:
            expected.update(hcomp_entry=0xA40013B0, hcomp_screen_switch=0xA4001760)
            assert text_size(args.maps[i]) <= 0x790
        for name, value in expected.items():
            assert table[name] == value, (name, hex(table[name]), hex(value))
    # Main/Mode7 resident suffix is retained across the slot swap. Compare
    # emitted bytes, not duplicated source spelling.
    from check_rsp_branch_delay_slots import read_text
    main = read_text(Path('build/src/rsp_main.elf'))[1]
    mode7 = read_text(Path('build/src/rsp_mode7.elf'))[1]
    assert main[0xCE4:0xE8C] == mode7[0xCE4:0xE8C], 'window helper differs'
    assert main[0xF08:0xFAC] == mode7[0xF08:0xFAC], 'retained DMA/loader differs'
    assert tables[0]['next_layer'] == 0xA4001370
    assert tables[1]['next_layer'] == 0xA4001364
    print('STAGE1_DISPATCH_ABI_VALIDATED')


if __name__ == '__main__':
    main()
