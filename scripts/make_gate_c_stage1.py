#!/usr/bin/env python3
"""Original Stage 1 guests. No assets from commercial ROMs."""
from pathlib import Path
import argparse
import hashlib
from make_gate_c_hcomp_color_window import build_case, WINDOW_HOOK_OFFSET
from make_gate_c_hcomp_transparent_sub import build_mode
from make_gate_c_hcomp_cgwsel_source import finalize_checksum

STATIC_MODES = ('fixed', 'absent', 'control', 'clip', 'prevent', 'both')
MODES = STATIC_MODES + ('visual', 'mixed')


def build(mode):
    if mode in ('visual', 'mixed'):
        return build_animated(mode == 'mixed')
    if mode in ('fixed', 'absent'):
        return build_mode({'fixed': 'fixed-half', 'absent': 'sub-absent-half'}[mode])
    rom = bytearray(build_case(mode + '-inside'))
    # WH0/WH1 are the fourth/fifth immediate stores in the verified hook.
    rom[WINDOW_HOOK_OFFSET + 3 * 5 + 1] = 64
    rom[WINDOW_HOOK_OFFSET + 4 * 5 + 1] = 191
    finalize_checksum(rom)
    return bytes(rom)



def dsp_write(a, reg, value):
    a.emit(0x8F, reg, 0xF2, 0x8F, value, 0xF3)  # MOV dp,#imm


def spc_image():
    from make_gate_c_hcomp_main_sub_lifetime import Assembler
    a = Assembler()
    a.emit(0x20)  # CLRP: direct page $0000
    for reg, value in ((0x6C, 0x20), (0x0C, 0x7F), (0x1C, 0x7F),
                       (0x2C, 0), (0x3C, 0), (0x5D, 5), (0x5C, 0)):
        dsp_write(a, reg, value)
    for voice in range(8):
        # Eight looping voices, 500/625/.../1375 Hz at native DSP rate.
        pitch = 0x400 + voice * 0x100
        for offset, value in ((0, 16), (1, 16), (2, pitch & 255),
                              (3, pitch >> 8), (4, 0), (5, 0), (7, 0x7F)):
            dsp_write(a, voice * 16 + offset, value)
    dsp_write(a, 0x4C, 0xFF)
    a.emit(0x8F, 64, 0xFC, 0x8F, 4, 0xF1)  # timer2 ~1kHz
    a.emit(0x8F, 0, 0x20, 0x8F, 0x5A, 0xF7)  # heartbeat/ready
    a.label('loop')
    a.emit(0xE4, 0xF5, 0xC4, 0xF5)  # echo CPU frame command
    a.emit(0xE4, 0xFF)  # read-clear timer2 output
    a.branch(0xF0, 'loop')
    a.emit(0xAB, 0x20, 0xE4, 0x20, 0xC4, 0xF4)
    a.branch(0x2F, 'loop')
    code = a.finish()
    assert len(code) < 0x300
    image = bytearray(0x409)  # $0200..$0608
    image[:len(code)] = code
    image[0x300:0x304] = bytes((0, 6, 0, 6))  # directory $0500
    # Filter0, shift11, loop+end. Original 16-sample triangular waveform.
    image[0x400:] = bytes((0xB3, 0x02, 0x46, 0x76, 0x42, 0x0E, 0xCA, 0x9A, 0xCE))
    return bytes(image)


def audio_upload():
    from make_gate_c_hcomp_main_sub_lifetime import Assembler, lda_sta_abs
    a = Assembler()
    # Standard IPL protocol, verified against the IPL already in apu.S.
    for port, value in ((0x2140, 0xAA), (0x2141, 0xBB)):
        a.label(f'ready{port}')
        a.emit(0xAD, port & 255, port >> 8, 0xC9, value)
        a.branch(0xD0, f'ready{port}')
    for port, value in ((0x2142, 0), (0x2143, 2), (0x2141, 1), (0x2140, 0xCC)):
        lda_sta_abs(a, value, port)
    a.label('start_ack')
    a.emit(0xAD, 0x40, 0x21, 0xC9, 0xCC)
    a.branch(0xD0, 'start_ack')
    a.emit(0xA2, 0, 0)  # X16=0
    a.label('upload')
    a.emit(0xBD, 0, 0xC0, 0x8D, 0x41, 0x21, 0x8A, 0x8D, 0x40, 0x21)
    a.label('byte_ack')
    a.emit(0xCD, 0x40, 0x21)
    a.branch(0xD0, 'byte_ack')
    a.emit(0xE8, 0xE0, len(spc_image()) & 255, len(spc_image()) >> 8)
    a.branch(0x90, 'upload')
    for port, value in ((0x2141, 0), (0x2142, 0), (0x2143, 2)):
        lda_sta_abs(a, value, port)
    a.emit(0x8A, 0x18, 0x69, 1, 0x8D, 0x40, 0x21)
    a.label('driver_ready')
    a.emit(0xAD, 0x43, 0x21, 0xC9, 0x5A)
    a.branch(0xD0, 'driver_ready')
    # Deterministic entity state, later updated 256 times every frame.
    a.emit(0xA2, 0, 0, 0xA9, 0)
    a.label('clear_entities')
    a.emit(0x9F, 0, 0x10, 0x7E, 0xE8, 0xE0, 0, 1)
    a.branch(0xD0, 'clear_entities')
    a.emit(0x60)
    return a.finish()


def animation_nmi(mixed):
    from make_gate_c_hcomp_main_sub_lifetime import Assembler, lda_sta_abs, lda_long, sta_long
    a = Assembler()
    a.emit(0x48, 0xDA, 0x5A, 0xAD, 0x10, 0x42)  # preserve A/X/Y, ack NMI
    lda_sta_abs(a, 2, 0x212D)
    lda_long(a, 0x7E0000)
    a.emit(0x1A)
    sta_long(a, 0x7E0000)
    # Left=n&127; right=left+32+((n>>2)&63). Motion AND varying width.
    a.emit(0x29, 0x7F)
    sta_long(a, 0x7E0004)
    a.emit(0x8D, 0x26, 0x21)
    lda_long(a, 0x7E0000)
    a.emit(0x4A, 0x4A, 0x29, 0x3F, 0x18, 0x69, 32, 0x18)
    a.emit(0x6F, 4, 0, 0x7E, 0x8D, 0x27, 0x21)
    if mixed:
        # Real CPU simulation, bounded to 256 WRAM read/ALU/write iterations.
        a.emit(0xA2, 0, 0)
        a.label('entities')
        a.emit(0xBF, 0, 0x10, 0x7E, 0x18, 0x69, 3, 0x49, 0x5A)
        a.emit(0x9F, 0, 0x10, 0x7E, 0xE8, 0xE0, 0, 1)
        a.branch(0xD0, 'entities')
        # Channel1: 512B actual VRAM upload into an unused 2bpp staging tile
        # area, while channel0 continues the section-defining TS HDMA.
        for port, value in ((0x2116, 0), (0x2117, 0x30), (0x4310, 1),
                            (0x4311, 0x18), (0x4312, 0), (0x4313, 0x10),
                            (0x4314, 0x7E), (0x4315, 0), (0x4316, 2), (0x420B, 2)):
            lda_sta_abs(a, value, port)
        # CGRAM channel1: redraw the same BG1/BG2 entries (4B); exercises
        # palette epoch transport without changing the image reference.
        for port, value in ((0x2121, 1), (0x4310, 0), (0x4311, 0x22),
                            (0x4312, 0), (0x4313, 0xC5), (0x4314, 0),
                            (0x4315, 4), (0x4316, 0), (0x420B, 2)):
            lda_sta_abs(a, value, port)
        lda_long(a, 0x7E0000)
        a.emit(0x8D, 0x41, 0x21)  # live CPU->SPC frame command
        a.emit(0xAD, 0x40, 0x21)
        sta_long(a, 0x7E0002)  # heartbeat observed by CPU
        a.emit(0xAD, 0x41, 0x21)
        sta_long(a, 0x7E0003)  # echoed frame command
    a.emit(0x7A, 0xFA, 0x68, 0x40)
    return a.finish()


def build_animated(mixed):
    rom = bytearray(build('both'))
    nmi = animation_nmi(mixed)
    assert len(nmi) < 0x300  # $8500..$87FF
    rom[0x500:0x500+len(nmi)] = nmi
    for offset in (0x7FEA, 0x7FFA):
        rom[offset:offset+2] = (0x8500).to_bytes(2, 'little')
    if mixed:
        code = audio_upload()
        assert len(code) < 0x100  # $8800 before BG1 tilemap $9000
        rom[0x800:0x800+len(code)] = code
        image = spc_image()
        rom[0x4000:0x4000+len(image)] = image
        rom[0x4500:0x4504] = bytes((0x1F, 0, 0xE0, 3))
        # Audio runs under forced blank, before the existing window setup.
        rom[0x1F0:0x200] = bytes((0x20, 0, 0x88, 0x20, 0xA0, 0x81, 0x60)) + bytes((0xEA,))*9
    rom[0x7FC0:0x7FD5] = (b'S64 STAGE1 MIXED' if mixed else b'S64 STAGE1 VISUAL').ljust(21, b' ')
    finalize_checksum(rom)
    return bytes(rom)


def window(frame):
    left = frame & 127
    return left, left + 32 + ((frame >> 2) & 63)

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode', choices=MODES, required=True)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    data = build(args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(args.mode, hashlib.sha256(data).hexdigest())


if __name__ == '__main__':
    main()
