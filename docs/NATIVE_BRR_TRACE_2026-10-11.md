# R21 - BRR chunks checked on the physical N64 (2026-10-11)

## Purpose and implementation

R20 proves isolated BRR arithmetic through linked execution and an independent
reference. R21 closes a narrower hardware gap: an optional trace records the
actual decoder inputs and outputs on the N64, for comparison on the PC.
It changes no decoder algorithm and makes no full-audio acceptance claim.

`BRR_OBSERVER=1` requires `AUDIO_OBSERVER=1` and defaults off. The ring owns
32 records of 16 bytes: voice/header/four packed nibbles, two prior half-scaled
samples, and four decoded half-scaled samples. Input is recorded before any
invalid-range transformation; a record is published only after all four sample
stores finish. The next index wraps at 32; the completion counter wraps at
2^32. After counter wrap, the exported valid-record count conservatively
understates availability until 32 new records complete.

`audio-brr` exports 512 bytes only at an already retired pause, with no armed
or busy capture, no transport fault and a valid framebuffer. It does not reset
the ring or modify guest/PCM state. Raw records remain private. The hooks add
40 executed scalar instructions per decoded chunk; timing from this build
must not be attributed to observer-free production code.

## Checks

48 linked hook pairs cover all eight voices, ring slots 0/31 and ordinary/
wrapping completion counts. Only the owned trace slot and counters change;
existing scratch registers are the only clobbers, and HI/LO/CP0 survive.
The exhaustive BRR proof additionally checks these fields in 57,344 voice
cases and rejects the four arithmetic mutations. Parser checks cover 186
cases and 1,000 fuzz inputs, including running/busy/unavailable/invalid-index
and failed-export rejection. The linked recorder retains its 102 cases.
Reboot/framebuffer guards and the 41-owner arena checks pass.

With the flag disabled, CPU text/rodata/data are identical to R20. All 24
RSP sections are unchanged. The existing runtime arena still ends at
0xD15C8, below 0xD2000 by 0xA38. CI builds the optional trace candidate,
executes its production parser and linked hooks, and keeps the legacy
reference separate for negative arithmetic checks.

## Physical result and limits

The empty candidate was installed through the live menu with readback
verification. The same acknowledged ALttP input recipe reaches the retired
room checkpoint. At that boundary, all 67,200 RGB pixels match coordinate8;
all 8,192 PCM ring bytes and the corresponding DSP state match R20.

32 complete records yield 128 half-scaled samples. Every sample agrees with
the unmodified compiled `decode_brr` method from
[Snes9x 1.63](https://github.com/snes9xgit/snes9x/blob/1.63/apu/bapu/dsp/SPC_DSP.cpp).
This physical sample spans seven voices, filter 2 and three ranges; synthetic
checks cover the other filters/ranges. It is a bounded native decoder proof,
not a claim about all future chunks, complete mixing, echo, interpolation,
release, clock timing or DAC output. No performance interval was measured
with the trace enabled.

[Curated numeric evidence](evidence/native-brr-trace-2026-10-11.json) contains
only original code identities, test counts and numeric comparisons. All
commercial inputs, replay/transport logs, frames, PCM, registers and chunk
payloads stay private.

The candidate is opt-in development instrumentation. Coordinate8 was restored
with verified readback and the paired menu responded. Master is unchanged;
there is no merge, release, constant-60 qualification or Road 1.0 acceptance.
Remaining audio features and the rain renderer/guest-progress bottleneck are
still open. R20's exact source commit passes all three GitHub workflows;
fresh R21 CI must be verified independently after publication.
