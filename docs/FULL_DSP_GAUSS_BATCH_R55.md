# R55 - Closed-time eight-voice Gaussian batch boundary

IMPLEMENTED; native CPU cost and RSP backend pending. From R49 6d6e4eb, opt-in
DSP_FULL_GAUSS_BATCH0/FULL_DSP_PROBE1. Signal1/snapshot1 native configurations;
no R50 counter, R51 sampler, R52 BRR grouping, R53 chunks or R54 placement flags.

At phase0 each voice's decoded history and interpolation position already
belong to its upcoming V3c. V4 changes them after that voice's V3c. Current
PMON changes upcoming pitch, not the position used by that interpolation.
KON-delay voices silence their output and use the scalar fallback; other
voices with nonzero envelope compute pure raw Gaussian values at phase0.
Original envelope/noise/PMON/KON/KOFF/echo/BRR/latch/PCM work still runs in its
original phases. The batch has no APU RAM or DSP register reads. Consumption
identifies a voice from its regs pointer and clears its valid bit.

Eight results plus valid mask are36 derived bytes outside the unchanged
logical state_t. init/load/soft-reset/state-copy invalidate them; imports at
partial phases fall back until the next phase0. Public serialized state stays
byte-exact to the reference. No cached values are required in a savestate.

CPU execution currently establishes this boundary for a possible eight-lane
RSP kernel; no RSP backend or asynchronous task has been implemented. RSP
sharing still requires bounded DMA/handshake, returned results before first
use, and renderer ownership/contention proof. A passing CPU cache or primitive
throughput result does not establish whole-game speed or fidelity.

Pinned local comparison:12288 directed V3c cases,9216 partial-phase cases
across32 entry phases and1..64/95/96/97/127/128/129/255/256 clocks,13052 phase
matrix stereo frames,8192 arbitrary slices/11590 additional frames,39944
full-state/RAM/PCM comparisons. Another1024 one-clock calls each inject a
DSP register write and APURAM mutation; KON/KOFF/FLG/PMON/NON/echo controls
vary. All65536RAM/all128regs/PCM/internal output buffers match. Derived cache
admission/reset/export/import are checked; exported logical state is byte-exact.
Env1/noise/batch-value/voice-identity/reset mutations reject. Original6144-frame
transaction/checksums/nonzero/fullRAM backup/readback/restore/faults/snapshot
tail passes. Unchanged RPC219+1000 fuzz/admission tests reuse exact hashes.

Both native builds pass boot12/TV5/all linked core HI-LO/CPU6 queue words/two
banks/four actualD6400 DMA sites/three mutations. Full24576events/194ROMslots/
43owners and13 exact RSP banks remain. StaticD4A88/D5A88<D6000. Default18 core
executable sections match physicalR49 signal1. Flag1 adds the batch and changes
V3c/run plus init/load/reset/copy-state invalidation functions; no arena or
capacity change. [Numeric preflight](evidence/full-dsp-gauss-batch-r55-preflight.json).

Next freeze same-source0/1 and perform the existing short native three-workload
A/B, original2048-frame cases three repeats each at ALttP600. Require host
checksums/nonzero/full64KiB RAMrestore, unchanged live image/PCM/state, step660
and finallycoordinate8/menu/install/readback. Root aloneCOM3. >=8% both active
CPU saving warrants qualification; <3% both rejects CPU performance value.
Regardless of CPU timing, the proven semantic batch boundary is only a
foundation. Do not present an unmeasured RSP backend as working or reduce the
full goal to this cache. No broadCI before native value. All standalone64ms
budgets, real DSP/CPU/APU/render integration, DSP/DAC/SNES fidelity/native60/
corpus and master integration stay OPEN. Earlier candidates remain preserved.
