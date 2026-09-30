#!/usr/bin/env python3
"""Qualify moving-window output and actual CPU/SPC/DSP mixed workload."""
import argparse
import json
import math
import struct
import wave
from pathlib import Path
from make_gate_c_stage1 import window
from check_gate_c_stage1_ares import classify
from check_gate_c_hcomp_main_sub_lifetime import norm


def pcm(root):
    raw = (root / 'audio-pcm.bin').read_bytes()
    if len(raw) != 8192:
        raise ValueError('PCM ring geometry changed')
    samples = struct.unpack('>4096h', raw)
    # Both stereo channels deliberately receive the same eight voices.
    left, right = samples[::2], samples[1::2]
    if left != right:
        raise ValueError('unexpected stereo channel difference')
    rms = math.sqrt(sum(v*v for v in left) / len(left))
    if rms < 100 or max(left) <= 0 or min(left) >= 0:
        raise ValueError(f'inactive/one-sided PCM: rms={rms}, range={min(left),max(left)}')
    if len(set(left)) < 16:
        raise ValueError('PCM has no declared multi-voice variation')
    # Save an audible excerpt in canonical host little endian, with the
    # circular ring rotated by the next-write offset captured at the fence.
    state = json.loads((root / 'runtime-state.json').read_text())
    offset = state['dsp_pointer']
    if not 0 <= offset < 8192 or offset % 4:
        raise ValueError('DSP ring pointer invalid')
    words = samples[offset//2:] + samples[:offset//2]
    with wave.open(str(root / 'audio.wav'), 'wb') as wav:
        wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(32000)
        wav.writeframes(struct.pack('<4096h', *words))
    return dict(rms=round(rms, 3), minimum=min(left), maximum=max(left),
                unique_samples=len(set(left)), pointer=offset)


def sequence(root, mixed):
    frames = sorted(root.glob('frame-*'))
    if len(frames) != 8:
        raise ValueError('require exactly eight complete naturally fenced frames')
    records, phases, heartbeat, pcm_bytes = [], [], [], []
    for directory in frames:
        result = classify(directory, 'both', animated=True)
        expected_phases = [n for n in range(256) if list(window(n)) == result['window']]
        if len(expected_phases) != 1:
            raise ValueError(f'window is not from guest animation: {result["window"]}')
        phase = expected_phases[0]
        state = json.loads((directory / 'capture-state.json').read_text())
        if state['guest_frame_delta'] != 1:
            raise ValueError('animation advanced by more than one guest frame')
        # Queue produced before launch must carry the exact section consumed
        # by the compositor; requiring two copies to match would accept stale
        # windows and is invalid for real changing state.
        found = []
        for i in (1, 2):
            data = (directory / f'seed-section-q{i}.bin').read_bytes()
            for normalization in ('identity', 'word_swap32'):
                rec = norm(data, normalization)[:64]
                if rec[46:50] == bytes((*window(phase), 0, 0)) and rec[55:64] == bytes((0xA2, 0x41, 2, 1, 0, 0, 0, 0x40, 8)):
                    found.append((i, normalization))
        if len(found) != 1:
            raise ValueError(f'no unique consumed-section authority for animated output: {found}')
        # Section/guest pipeline phase is explicit: this rendered queue must
        # come from the guest frame known at the prelaunch seed boundary.
        if phase != state['baseline_counter']:
            raise ValueError(f'stale window phase {phase}, guest baseline {state["baseline_counter"]}')
        runtime = json.loads((directory / 'runtime-state.json').read_text())
        for name, value in (('apu_clock', 21), ('audio_set', 4), ('precision_set', 8), ('skipped_set', 0)):
            if runtime.get(name) != value:
                raise ValueError(f'Road setting {name}={runtime.get(name)} expected {value}')
        if mixed:
            if runtime.get('dsp_enabled') != 255 or runtime.get('apu_control') != 4:
                raise ValueError('eight voices and active SPC timer2 are not running')
            regs = (directory / 'dsp-regs.bin').read_bytes()
            if regs[0x4C] != 255 or regs[0x5D] != 5:
                raise ValueError('DSP driver configuration missing')
            for v in range(8):
                off = v * 16
                if regs[off:off+8] != bytes((16, 16, 0, 4+v, 0, 0, 0, 127)):
                    raise ValueError(f'voice{v} settings differ from workload')
            guest = (directory / 'guest-state.bin').read_bytes()
            val = 0
            for _ in range(guest[0]):
                val = ((val + 3) & 255) ^ 0x5A
            if (directory / 'entities.bin').read_bytes() != bytes((val,))*256:
                raise ValueError('bounded 256-entity CPU work did not complete')
            # Port3 readiness plus port1 echo proves uploaded SPC code runs;
            # the timer heartbeat and PCM must also change across frames.
            ports = runtime['apu_outputs'].to_bytes(4, 'big')
            if ports[3] != 0x5A or ports[1] != guest[0]:
                raise ValueError(f'SPC frame echo not current: {ports.hex()}, frame={guest[0]}')
            heartbeat.append(ports[0])
            pcm_bytes.append((directory / 'audio-pcm.bin').read_bytes())
            result['audio'] = pcm(directory)
        phases.append(phase)
        records.append(result)
    if any((b-a)&255 != 1 for a, b in zip(phases, phases[1:])):
        raise ValueError('animation skips/repeats guest phases')
    if mixed and (len(set(heartbeat)) < 6 or len(set(pcm_bytes)) < 6):
        raise ValueError('SPC timer heartbeat or DSP PCM is stale')
    return dict(passed=True, frames=8, phases=phases, records=records,
                active_voices=8 if mixed else 0, hardware_fps='NOT_MEASURED')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--captures', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    result = dict(classification='STAGE1_MOTION_AND_MIXED_LOAD_VALIDATED', passed=True,
                  visual=sequence(args.captures / 'visual', False),
                  mixed=sequence(args.captures / 'mixed', True),
                  real_n64='NOT_PROVEN', full_frame='NOT_PROVEN', iris='NOT_PROVEN')
    output = json.dumps(result, indent=2, sort_keys=True)+'\n'
    print(output, end='')
    if args.output:
        args.output.write_text(output)


if __name__ == '__main__':
    main()
