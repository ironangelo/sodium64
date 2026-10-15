#!/usr/bin/env python3
"""Decode S64H/S64P and the bounded S64V final native pixel/PCM snapshot.

Snapshot validity and color fidelity are separate. A valid green band is a
useful diagnostic result, not a decoder failure. One snapshot cannot qualify
intermittent presentation, actual audible output or all-game performance.
"""
import argparse
import json
import math
import struct
import wave
import zlib
from collections import Counter
from pathlib import Path
from hw_profile_report import normalize_save, parse_capture

OFFSET, SIZE = 0x4200, 0x3D10
HEAD_NAMES = ('magic version size complete valid sp_status dp_status dp_current dp_end '
              'sp_dma_busy sp_dma_full vi_origin vi_control vi_width vi_current '
              'dsp_pointer enabled ai_address ai_length ai_status ai_dacrate ai_bitrate '
              'guest_counter frame_count interrupted_epc vi_origin_before '
              'dp_status_before sp_status_before dsp_address fb1 fb2 fb3').split()

def window(n):
    left = n & 127
    return left, left + 32 + ((n >> 2) & 63)

def band_info(pixels):
    rows = [pixels[y*256:(y+1)*256] for y in range(8)]
    candidates = []
    for n in range(256):
        left, right = window(n)
        ref = [1 if left <= x <= right else 0x7BC1 for x in range(256)]
        if all(row == ref for row in rows):
            candidates.append(n)
    return dict(reference_matches=len(candidates) == 1, phases=candidates,
                colors=dict(Counter(f'0x{p:04x}' for row in rows for p in row)),
                rows_equal=all(row == rows[0] for row in rows))

def decode(blob):
    normalized, fmt = normalize_save(blob)
    if len(normalized) != 32768:
        raise ValueError('expected a complete 32768-byte SRAM save')
    hw, _ = parse_capture(normalized, strict=True)
    if (hw.snapshot_offset, hw.profile_size, hw.sample_interval, hw.audio_set) != (0x100, 0x4020, 65521, 4):
        raise ValueError('unexpected preserved S64H/S64P geometry/settings')
    raw = normalized[OFFSET:OFFSET+SIZE]
    h = dict(zip(HEAD_NAMES, struct.unpack_from('>32I', raw)))
    if (h['magic'], h['version'], h['size'], h['complete']) != (0x53363456, 1, SIZE, 1):
        raise ValueError('missing, incomplete or unsupported S64V capture')
    if h['valid'] != 7 or not h['sp_status'] & 1 or h['dp_status'] & 0x70:
        raise ValueError('snapshot not naturally drained; timeout/validity failure')
    if h['sp_dma_busy'] or h['sp_dma_full'] or h['dp_current'] != h['dp_end']:
        raise ValueError('snapshot has pending SP/DP work')
    if h['vi_width'] != 280 or h['vi_origin'] not in [h['fb1'], h['fb2'], h['fb3']]:
        raise ValueError('unexpected VI source/geometry')
    if [h['fb1'], h['fb2'], h['fb3']] != [0xF2300, 0x113000, 0x133D00]:
        raise ValueError('unexpected fixed framebuffer allocation')
    if h['dsp_pointer'] >= 8192 or h['dsp_pointer'] % 4:
        raise ValueError('invalid next-write DSP ring offset')
    pixels = list(struct.unpack_from('>4096H', raw, 0x80))
    buffers = [list(struct.unpack_from('>256H', raw, 0x2080+i*512)) for i in range(3)]
    selected = [h['fb1'], h['fb2'], h['fb3']].index(h['vi_origin'])
    if buffers[selected] != pixels[:256]:
        raise ValueError('selected VI row disagrees with its independent buffer copy')
    pcm = raw[0x2D10:0x3D10]
    samples = struct.unpack('>2048h', pcm)
    channels = [samples[::2], samples[1::2]]
    result = dict(format=fmt, header=h, frame_budgets=list(hw.frame_budgets),
                  measured_samples=hw.sample_count, band=band_info(pixels),
                  below_band_colors=dict(Counter(f'0x{p:04x}' for p in pixels[2048:])),
                  buffer_rows=[dict(Counter(f'0x{p:04x}' for p in row)) for row in buffers],
                  consumed_input=list(struct.unpack_from('>4I', raw, 0x2C80)),
                  audio=dict(nonzero=any(samples), unique_left=len(set(channels[0])),
                             unique_right=len(set(channels[1])),
                             channels_differ=channels[0] != channels[1],
                             sample_frames=1024, nominal_rate=32000),
                  limitations=['Final snapshot only; no intermittent-flash cadence proof',
                               'Latest renderer provenance may differ from VI-selected frame',
                               'PCM generation and AI state do not certify audible hardware output',
                               'AI address/DAC/bitrate raw readbacks are not configuration authority'])
    return result, raw, pixels, pcm

def qualify_workload(result, raw, mixed):
    if not result['band']['reference_matches'] or result['frame_budgets'] != [60]*5:
        raise ValueError('laboratory band/frame-budget regression')
    samples=struct.unpack('>2048h',raw[0x2D10:0x3D10])
    left,right=samples[::2],samples[1::2]
    if mixed:
        # Original SPC driver uses volume16 in BOTH channels for all voices.
        if result['header']['enabled'] != 255 or left != right:
            raise ValueError('original eight-voice equal-channel contract violated')
        regs=raw[0x2C90:0x2D10]
        if regs[0x4C]!=255 or regs[0x5D]!=5:
            raise ValueError('missing original DSP driver')
        for voice in range(8):
            if regs[voice*16:voice*16+8] != bytes((16,16,0,4+voice,0,0,0,127)):
                raise ValueError('DSP voice settings differ from original guest')
        rms=math.sqrt(sum(x*x for x in left)/len(left))
        if rms<100 or min(left)>=0 or max(left)<=0 or len(set(left))<16:
            raise ValueError('inactive/constant/one-sided mixed PCM')
        return dict(passed=True,mixed=True,active_voices=8,equal_channels=True,
                    rms=round(rms,3),minimum=min(left),maximum=max(left),unique_samples=len(set(left)))
    if result['header']['enabled'] or any(samples):
        raise ValueError('visual-only guest unexpectedly generates audio')
    return dict(passed=True,mixed=False,active_voices=0,silent=True)

def write_png(path, pixels):
    def chunk(tag, data):
        return struct.pack('>I', len(data))+tag+data+struct.pack('>I', zlib.crc32(tag+data))
    body = bytearray()
    for y in range(16):
        body.append(0)
        for p in pixels[y*256:(y+1)*256]:
            body.extend(((p>>11 & 31)*255//31, (p>>6 & 31)*255//31, (p>>1 & 31)*255//31))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>2I5B',256,16,8,2,0,0,0))+
                     chunk(b'IDAT',zlib.compress(body))+chunk(b'IEND',b''))

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('save', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result, raw, pixels, pcm = decode(args.save.read_bytes())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.output/'native-probe.bin').write_bytes(raw)
    write_png(args.output/'native-pixels.png', pixels)
    with wave.open(str(args.output/'native-pcm.wav'), 'wb') as out:
        out.setnchannels(2); out.setsampwidth(2); out.setframerate(32000)
        out.writeframes(struct.pack('<2048h', *struct.unpack('>2048h', pcm)))
    print(json.dumps(result,indent=2))

if __name__ == '__main__':
    main()
