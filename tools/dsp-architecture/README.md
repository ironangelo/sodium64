# Complete-DSP architectural reference fixtures

This host tool prepares reproducible inputs and expected results for the
integral resident-DSP cost test. It executes the complete pinned S-DSP, not an
isolated BRR/Gaussian kernel. No file here is linked by the emulator Makefile.

**Native integral cost remains NOT_MEASURED.** There is no complete resident RSP
backend or live SPC bridge in this tool. Host execution time, event counts and
successful replay cannot qualify either missing component or predict game FPS.

## Generate and validate

On Linux, with Python 3 and g++:

```sh
python3 tools/dsp-architecture/generate_trace.py --output dsp-fixtures --mutations
```

On Windows, supply the compiler executable if it is not on PATH:

```powershell
python tools/dsp-architecture/generate_trace.py --cxx C:/msys64/mingw64/bin/g++.exe --output dsp-fixtures --mutations
```

The output directory must be new. A run preserves earlier results instead of
overwriting them. `--frames` admits32..2048; the default 512-frame corpus has
canonical hashes in `default_corpus.json`. Its artifacts contain only original
numeric RAM/register patterns and resulting reference PCM. No ROM, SAV, game
state or captured commercial data is accepted or needed to regenerate them.

The unchanged source and LGPL license are retained in `vendor/snes_spc/`, pinned
and byte-checked by `vendor/UPSTREAM.json`. Observation hooks are applied only to
a temporary copy. A separately compiled unchanged reference verifies that copy.

## Work and evidence

Each default case includes 64 warmup frames and 512 evaluated stereo frames:

| Case | DSP workload | Producer schedule |
| --- | --- | --- |
|0|One active voice|Synthetic nominal|
|1|Eight high-pitch voices|Synthetic nominal|
|2|Eight voices, PMON, noise, echo/FIR/feedback|Synthetic nominal|
|3|Full features plus all BRR ranges|Explicit same-clock/FIFO stress|

The three nominal schedules issue at most one producer bus access per DSP clock.
They are controlled synthetic schedules, not traces of executing SPC instructions.
The stress case deliberately permits 65 queued writes and multiple same-clock
operations; it must not be presented as normal game traffic.

BRR, Gaussian, envelopes, KON/KOFF, counters, noise, PMON, echo/FIR and all32
phases execute through the complete core. Dynamic BRR/directory bytes, ESA
changes, echo-region fetch-like reads, ENVX/OUTX observations and an echo-ring
wrap are included. DIR/SRCN inputs stay within the admitted nonwrapping domain;
the known exhaustive R61 directory-wrap correctness requirement remains open
for a gameplay backend.

The generator compares the complete normalized DSP state, all 64 KiB APURAM and
the full PCM buffer every clock: 65,544 comparisons over 65,536 clocks by default.
It checks active-voice/work coverage and repeated byte-exact generation. Exported
inputs are then loaded into new complete-core instances and replayed, verifying
every chronological internal bus operation, producer result, final state, final
RAM and PCM. The RAM-only Python reader is deliberately insufficient to establish
DSP register semantics; compiled replay catches those errors.

`--mutations` also requires:

- 32 malformed actual fixtures rejected by the strict reader;
- five semantic trace corruptions rejected by complete-core replay, including
  same-clock register order and missing enabled echo writes;
- five actual core omissions rejected after warmup, covering BRR, Gaussian,
  PMON, noise and echo publication.

The generator records scopes, counts, tool/source hashes and the explicit
`NOT_MEASURED` native status in `receipt.json`. There is no host timing result.

## Container

`.s64darc` begins with a 128-byte big-endian header (`S64DARC1`). It identifies
aligned initial RAM/state, 16-byte clock/kind/address/value events, expected final
state/RAM and big-endian stereo PCM words. Opaque state blocks use the upstream
portable state format. The strict reader checks extents, padding, byte order,
all phases, publication ordering and chronological RAM values. Compiled replay
additionally validates actual complete-DSP execution from the serialized seed.

## Remaining integral gate

Use the same admitted producer inputs and expected full-state/RAM/PCM results
for both the scalar control and the complete resident backend. Measure the
entire native interval, including producer preparation, read/register/fetch
barriers, journal handling, cache/JIT echo publication, DMA, synchronization and
output. Include cold/warm behavior, actual renderer coexistence and verified
restoration; preserve any timeout or ownership failure.

A complete result still requires the real SPC bridge, a complete resident
backend, representative private live-driver coverage and comparable real-N64
timing. A transport-only floor or scalar-window timing cannot close that gate.
Do not sum costs or percentages from independent kernel branches.
