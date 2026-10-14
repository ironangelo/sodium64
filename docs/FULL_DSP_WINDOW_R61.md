# R61 - complete DSP window and SPC bus visibility

Status: IMPLEMENTED transport-independent window controller, semantically
qualified against the unchanged immediate production core. The original four
counterexamples remain regression gates. No live SPC bridge, native RAM owner,
resident complete DSP backend, native cost or live audio acceptance yet.

## Implemented semantic boundary

`DSP_FULL_WINDOW=1` requires `FULL_DSP_PROBE=1` and both BRR/Gaussian batch
flags0; it defaults0. `src/full_dsp_window.{h,cpp}` uses the existing full core,
caller-owned disjoint CPU/shadow64KiB buffers and an ordered64-entry journal.
Timestamps are relative0..31, preserving same-clock producer order without an
absolute-clock wrap dependency. Flushes bound each window to the next period,
catch DSP reads and pending four-byte echo RAM accesses (including code fetch),
drain overflow without dropping writes, and precede reset/load/copy/PCM/KON
observation. Current native SPC bus handlers do not call this interface yet.

The pending echo address uses the previous ESA latch/current offset before
phase22 and the captured pointer after that latch, with no new period admitted
before catch-up. Actual enabled echo writes publish exactly two bytes and a
callback for later CPU cache/JIT-tag integration. Transport callbacks live
outside serialized logical state. No global64KiB allocation is introduced.

The differential fixture compiles a separate unchanged production reference,
runs it one clock at a time and checks the controller at every period closure
and producer-visible barrier. Both cores receive the same original numeric
inputs; no commercial input/state/PCM is used. Results:

- 72646 complete normalized state/CPU RAM/shadow RAM/PCM comparisons.
- 20023 producer reads,933286 DSP clocks,5669 directed cases.
- All32 phases and128 registers, ESA/EDL/FLG/address-wrap changes,31 FIFO
  overflow cases, same-clock order, soft/hard reset, export/import and PCM.
- 50955 enabled echo word publications, exact callback order/address/value
  and simulated JIT-page tag counts; real cache/JIT integration remains open.
- Eleven distinct unsafe mutations rejected, including future RAM visibility,
  early event replay, missing read/echo/reset/export/PCM barriers, wrong
  captured pointer, dropped FIFO events, missing echo publication and an
  omitted16-bit directory mask.

An existing core limitation was exposed while admitting arbitrary register
writes: `DIR*256 + SRCN*4` could exceed64KiB, and V2 would read a host pointer
outside the provided APURAM. The enabled window core now masks the V1 bus
address to16bits, matching
[ARES voice1/voice2](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/sfc/dsp/voice.cpp).
All65536 DIR/SRCN pairs with both start/loop word selections execute through
the actual phase31/0 production core:131072 independent numeric expected-word
checks pass; removing the mask fails. Four-byte entry alignment ensures the
V2+2 word stays within64KiB after masking. The unchanged immediate oracle is
used for admitted non-wrapping traces, not as authority for its unsafe corner.
This fixes the opt-in full-window core; default-off/legacy behavior is preserved.
No affected commercial game or native fidelity result has been established.

`scripts/test_full_dsp_window_controller.py --mutations` records this proof in
CONTROLLER.json. `check_full_dsp_window_build.py` compiles the core/controller/
probe for O64; all26 allocated default-off core sections exactly match source
6dc6a034362c1cab8f972b353e09f1f8e1b5376c. Disabled controller has no code/data;
enabled controller has no global writable owner. Code sizes9640/2224 bytes
are object evidence only. See BUILD.json. No native ROM run or broad CI was
needed to qualify this semantic boundary, and no performance claim is made.

## Current next action

R62 physically confirms8MiB available. Assign an explicit small upper-RAM
shadow/event owner using its verified boot capture, guard unknown/base4MiB
without accessing upper memory, and prove non-overlap plus CPU/DMA/cache/save
ownership. Preserve all existing base caches. Establish exact native SPC JIT
bus timestamps and echo cache/code-tag behavior before wiring a live bridge.
Then implement the complete resident RSP backend and use a short physical
full-work discriminator; scalar-window timing would not prove RSP value.

Full DSP/DAC, native60/50, graphics coexistence, corpus and master integration
remain OPEN. The earlier source audit and hypotheses below are retained.

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

## Original bounded implementation plan (now implemented above)

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
