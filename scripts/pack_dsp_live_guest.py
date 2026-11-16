"""Pack an original mixed-render/audio workload into the private bench ROM."""
import argparse
from hashlib import sha256
from pathlib import Path
import sys

ROM_OFFSET = 0xE0000
MAIN_PC = 0x200
READ_PAIR_PC = 0x480


def audio_driver(stage1, assembler):
    code = assembler()
    code.emit(0x20)  # CLRP
    for register, value in (
        (0x6C, 0x20), (0x0C, 65), (0x1C, 57), (0x2C, 0), (0x3C, 0),
        (0x5D, 5), (0x5C, 0), (0x6D, 0x40), (0x7D, 1),
        (0x4D, 0), (0x0D, 0), (0x2D, 0x8A), (0x3D, 0x10),
    ):
        stage1.dsp_write(code, register, value)
    for voice in range(8):
        pitch = 0x400 + voice * 0x80
        for offset, value in ((0, 32), (1, 26), (2, pitch & 0xFF), (3, pitch >> 8),
                              (4, voice % 4), (5, 0), (7, 0x7F)):
            stage1.dsp_write(code, 16 * voice + offset, value)

    # Echo writes always produce zero with EON and EFB at zero. The last
    # echo byte can change CLRC to NOP, both of which safely fall into RET.
    code.emit(0xE8, 0x60, 0xC5, 0xFF, 0x47)  # MOV !$47FF,#CLRC
    code.emit(0xE8, 0x6F, 0xC5, 0x00, 0x48)  # MOV !$4800,#RET
    code.emit(0xE8, 0xA5, 0xC5, 0x00, 0x40)  # sentinel for echoed RAM
    stage1.dsp_write(code, 0x6C, 0x1F)
    stage1.dsp_write(code, 0x4C, 0xFF)
    code.emit(0x8F, 64, 0xFC, 0x8F, 4, 0xF1)  # timer 2, ~1 kHz
    code.emit(0x8F, 0, 0x20, 0x8F, 0x5A, 0xF7)  # heartbeat / ready
    code.label("idle")
    code.emit(0xE4, 0xF5, 0xC4, 0xF5)
    code.emit(0xE4, 0xFF)
    code.branch(0xF0, "idle")
    code.emit(0x8F, 8, 0xF2, 0x3F, READ_PAIR_PC & 0xFF, READ_PAIR_PC >> 8)
    for register in (9, 0x7C):
        code.emit(0x8F, register, 0xF2, 0xE4, 0xF3)
    code.emit(0xE5, 0, 0x40, 0xE5, 2, 0x40)
    code.emit(0x80, 0x3F, 0xFF, 0x47, 0xE8, 0x00, 0x88, 0, 0xC4, 0xF6)
    code.emit(0xAB, 0x20, 0xE4, 0x20, 0xC4, 0xF4)
    code.branch(0x2F, "idle")

    main = code.finish()
    assert len(main) < READ_PAIR_PC - MAIN_PC
    image = bytearray(0x400)
    image[:len(main)] = main
    pair = READ_PAIR_PC - MAIN_PC
    image[pair:pair + 5] = bytes((0xE4, 0xF3, 0xE4, 0xF3, 0x6F))
    wave = (0x02, 0x46, 0x76, 0x42, 0x0E, 0xCA, 0x9A, 0xCE)
    for filter_id in range(4):
        address = 0x600 + filter_id * 9
        offset = 0x300 + filter_id * 4
        image[offset:offset + 4] = address.to_bytes(2, "little") * 2
        image.extend(bytes((0x93 + filter_id * 4, *wave)))
    return bytes(image)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-tools", type=Path, required=True)
    parser.add_argument("base_rom", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.fixture_tools))
    import make_gate_c_stage1 as stage1
    from make_gate_c_hcomp_main_sub_lifetime import Assembler
    from make_gate_c_hcomp_cgwsel_source import finalize_checksum

    image = audio_driver(stage1, Assembler)
    stage1.spc_image = lambda: image
    rom = bytearray(stage1.build("mixed"))
    rom[0x7FC0:0x7FD5] = b"S64 DSP LIVE DEMAND".ljust(21, b" ")
    finalize_checksum(rom)
    assert len(rom) == 0x8000 and rom[0x4000:0x4000 + len(image)] == image
    base = args.base_rom.read_bytes()
    assert base[:4] == bytes.fromhex("80371240")
    assert len(base) <= ROM_OFFSET and ROM_OFFSET + len(rom) < 0x104000
    args.output.write_bytes(base.ljust(ROM_OFFSET, b"\0") + rom)
    print("guest", sha256(rom).hexdigest())
    print("packed", sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
