# R61 - complete DSP window and SPC bus visibility

Status: HYPOTHESIS for a generic window controller; four original production-
core counterexamples reject naive deferred execution. No controller, resident
complete DSP backend, native cost or live audio acceptance yet.

R60's raw-job/private-DMA protocol measured15.103667 us per32 BRR outputs
versus14.567 us scalar, with23.232 us observed maximum. Standalone BRR
offload remains rejected. The next direction is a persistent complete DSP
state/dataflow boundary that can amortize synchronization over required DSP
work, preserving every SPC-visible effect. This is not another BRR refinement.

## Dependencies found in the current source

`SPC_DSP.cpp:GEN_DSP_TIMING` publishes ENDX at V7, OUTX at V8 and ENVX at V9,
on different clocks for each voice. Global PMON is latched at27; NON/EON/DIR
at28; KON/KOFF/counters/noise have29/30 ordering. BRR and directory RAM reads
also occur on distinct clocks. Echo reads left/right at22/23, writes left/right
at29/30, and latches its address separately from subsequent ESA/EDL writes.
The existing full DSP API explicitly requires catching up before register
reads/writes. A32-clock sample count is insufficient to establish bus order.

Current native `apu_execute` checks the legacy sample deadline between JIT
blocks. `apu_emitter.S` bounds a block at32 worst-case SPC cycles, but emits
the accumulated S3 debit at the block return; conditional cycles have separate
runtime debits. `read_dspdata` and `write_dspdata` directly access the legacy
register path. These facts do not supply exact within-block DSP bus timestamps.
That is a separate integration gate, not permission to round writes to samples.

`apu_write8` increments a64-byte RAM page's JIT tag. Future full-DSP echo
writes through DMA must also keep CPU data-cache visibility and translated
instruction invalidation correct. The present full C core is a paused probe;
these are requirements for a live bridge, not a claim that it is integrated.

## Executed counterexamples

The fixture uses two instances of the unchanged production full core and
original numeric RAM/register state. Four small tests expose these differences:

| Operation | Chronological result | Unqualified deferred result |
| --- | --- | --- |
| PMON write254 at28 after the27 latch | latched0 | latched254 |
| RAM byte write233 at2 after BRR read at1 | read18 | read233 |
| CPU read after left echo write at29 | RAM word4660 | RAM word0 |
| OUTX read after publication at3 | register86 | register0 |

`scripts/test_full_dsp_window.py` compiles this fixture against the actual core.
All four counterexamples execute and reject the unsafe transformation. The
last two deferred cases eventually converge after catch-up; eventual equality
does not repair an earlier wrong CPU read. This proves specific ordering
hazards, not safe batching, complete bus emulation or hardware performance.
See `FULL_DSP_WINDOW_R61_COUNTEREXAMPLES.json`.

## Next bounded implementation

Prove a transport-independent window controller using the existing full core
as its execution backend. Keep a DSP RAM view distinct from immediately
updated CPU RAM, and journal timestamped CPU RAM/register writes in original
order. Replay those writes at their exact clocks, never exposing a future byte
to an earlier DSP read. Bound a window by the next32-phase boundary and flush
before a DSP register read, state export/reset, required PCM consumption or
a CPU access to pending echo RAM. Reads and writes include instruction fetches.
Queue overflow must flush safely, never discard a write.

Derive the current pending four-byte echo span from the actual DSP phase:
before its22 latch, use the previous ESA latch plus current echo offset;
after that latch, use the captured echo pointer. Stop before entering another
period whose address may have changed. Treat this admission rule as unproved
until differential cases cover all phases, ESA/EDL/FLG changes and wrapping.
Replay echo writes to CPU RAM with a callback suitable for later cache/JIT-tag
integration. Preserve same-clock ordering and arbitrary short returns.

Compare every producer-visible RAM/register read against an immediate
clock-by-clock reference, and compare normalized full DSP state, all64KiB RAM
and PCM at every flush. Include register/RAM mutations, echo wrap, FIFO
overflow, reset/export and the four executed hazards as regressions. Reject
mutations that admit a hazard or replay writes late. This is a semantic/dataflow
qualification only; do not time the scalar controller as an RSP speed claim.

After that boundary is proved, choose a dedicated64KiB shadow-RAM lease and
event/state owners in the real memory map; none is assigned yet. Establish
exact JIT bus timestamps before live SPC integration. A resident RSP complete-
DSP kernel must reuse the preserved arithmetic/owner evidence, count all
events, cache maintenance, DMA, output and synchronization, and get an early
native full-work discriminator before broad CI. No second standalone emulator,
game-specific policy, skipped work or speculative future inputs are introduced.

Full DSP/DAC audio, renderer sharing, sustained native60/50, the required
corpus and master integration remain open. R49/master/R44/R45 and all rejected
branches are preserved. All commercial inputs and derived data remain private.
