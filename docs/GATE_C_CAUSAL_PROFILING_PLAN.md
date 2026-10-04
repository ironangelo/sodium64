# Gate C causal performance diagnosis

Status: the bounded physical-console A11/A13 batch has been analyzed. Current
qualified reference is A13 `b4206144fefe1d77b05397be154115d6328a2965`; A11
`ac534849002a04d342dd566a6f96ae1707680387` remains the regression control. The
A11 v4 diagnostic `bacc62315087eb135d6cf5f60e65e083af96719b` retained the
byte-identical A11 normal runtime. Master is unchanged. Historical checkpoints
remain in [Continuity](CONTINUITY.md).

The initial representative capture gate is met: 13 complete 20-second captures,
six paired A11/A13 scene labels, and one unpaired A13 ALttP intro. The named A11
ALttP intro capture was unavailable. All retained captures pass checksum,
capacity, wait/counter and completion checks, with MAX precision, frameskip 0,
audio ON, APU clock 21 and zero overflow. Scene identity and A13 ordering were
confirmed by the user; capture clocks are not aligned to identical guest frames.

The next comparison is two independent controlled candidates: packed arithmetic
`3a0c7fc` and Sub-presence dataflow `76f3f9`. Both have compiled contract passes;
complete pixel qualification has passed; physical-console comparisons are pending.
They are separate from A13 and from each other. No constant native 60-FPS result
or exact internal RSP-operation cause is claimed.

The shipped layout and limits are described in [Native diagnostic v4](NATIVE_DIAGNOSTIC_V4.md).
It retains completed-boundary timings, explicit CPU RSP/VI waits, linked CPU
sampling and 125 ms observations across the full interval. Live-DMEM
bank/stage/PPU fields remain unvalidated candidates, including observations
accepted by epoch bookends. The decoder does not treat them as precise hardware
attribution. A controlled change and repeated physical capture establish a causal
improvement. Design options below are not a field-by-field description of the
shipped format, nor prerequisites for more instrumentation now.

Both candidates passed exact-head Build and full Gate qualification: 94 normal complete images (5,390,336 pixels) and 12 armed v4 images (688,128 pixels) per candidate, with all compact guards passing. Manual and v4 original-guest recorders completed approximately 20 seconds, retained the whole v4 interval without overflow, and preserved cartridge PI payload bytes. Physical-console speed, normal output and audio comparisons remain pending.

## Decision to make

Determine which work makes a native frame miss its deadline, and whether that
work is necessary for correct output, repeated unnecessarily, or serialized by
an ownership dependency. Keep full audio, APU clock 21, frameskip 0 and the
established visual semantics. A busy percentage alone does not answer this question.

Use a hybrid of boundary timing, classified CPU sampling, source contracts and
controlled experiments. Avoid timestamps on every opcode, pixel or DMA poll
iteration. CPU and RSP operate concurrently, so sample shares and elapsed
intervals must not be summed into a fictional exclusive frame budget.

## Current curated evidence

Rates below are completed boundaries per Count-domain second over retained full
intervals whose endpoint lies after 5 s through the end of each capture (about 20 s). They are not visible
or presented FPS, and the first selected interval can begin before the window.
These are scene-level comparisons, not identical-frame A/B speedup claims.

| Scene | A11 boundaries/s | A13 boundaries/s | A13 mean explicit CPU RSP wait |
| --- | ---: | ---: | ---: |
| SMW intro, later portion | 59.52 | 59.50 | 0.002 ms |
| DKC1 animated intro | 27.28 | 28.24 | 24.30 ms |
| DKC1 first stage | 8.65 | 19.00 | 37.48 ms |
| ALttP darkened room/dialogue | 19.26 | 24.50 | 28.37 ms |
| ALttP exterior/rain | 17.22 | 18.57 | 40.10 ms |

A13 remains far from the target in the four sustained graphics-heavy windows.
Exact CPU waits establish a long dependency on RSP completion there; they are
not exclusive RSP execution durations. They do not identify which renderer,
arithmetic, transfer or RDP-retirement operation dominates.

SMW's whole-capture rate is effectively unchanged, about 58.41 boundaries/s in
both builds. Each includes approximately 39 ms worst intervals with an RSP-wait
component, at different capture offsets. Its later near-60 plateau has almost
no RSP waiting. The iris and later CPU-side dips must remain separate questions;
unvalidated live policy fields cannot prove every band took a particular route.

The DKC1 developer-logo capture contains changing workloads. Its early plateau
is RSP-wait dominant, followed by a CPU/APU-heavy plateau; A13 then returns to
RSP-wait dominance. During the CPU/APU plateaus, retained exact CPU EPCs map
principally to the APU compiler/emitter rather than generated APU execution.
Whole-capture averages mix these phases and are not a same-scene speedup measure.

The unpaired A13 ALttP intro averages 48.55 completed boundaries/s, but its final
four full second records are approximately 27.7–28.7/s. Early faster work
inflates that average. Without the missing A11 capture, no paired intro conclusion
is available.

The direct evidence supports at least two cost families: long RSP completion
dependencies in graphics-heavy scenes and APU compiler/emitter maintenance
during part of DKC startup. It does not demonstrate a physical N64 ceiling or
universal library fidelity. Total observer perturbation is not fully measured;
the instrumented builds are not clean-release performance measurements.

## Source structure and hypotheses

A13 has Main-only raw, exact direct and general composition policies. General
composition draws Sub and Main with provenance/presence handling. It can consume
whole real state sections; an at-most-eight-row virtual-band limit describes
older work and is not the current implementation. Short real raster epochs and
OBJ-sensitive spans still impose boundaries. Fast admission is restricted by
color math, clipping, backdrop and eligible OBJ conditions. Conservative
admission can be correct; broadening it requires a proof.

For A13's full-width arithmetic row, eight 32-pixel batches each perform four
64-byte input transfers and one 64-byte output transfer: 40 DMA operations and
2,560 transferred bytes per row. The Sub-tag snapshot additionally copies one
560-byte row in both directions. A fully general nonblank 224-row frame requiring all Sub reads implies
824,320 bytes of these transfers alone, excluding texture/overlay DMA and RDP
framebuffer traffic. This is a structural count, not measured cycles,
bandwidth saturation or an FPS prediction.

General resolution constructs horizontal mask entries in TILE_TABLE, which
renderers and the A13 snapshot also borrow. Identical window registers alone
do not establish safe mask reuse. Many real raster sections can repeat source,
setup, OAM and overlay work even on direct composition. A faster general math
kernel cannot be assumed to cure a direct or CPU-bound interval.

Hypotheses to distinguish:

- Necessary general source, arithmetic or transfer work dominates.
- Conservative admission selects general composition where a cheaper exact operation exists.
- Short raster epochs repeat drawing, setup, OAM work or mask construction.
- RDP command/texture retirement, DMA or overlays serialize required work.
- CPU/APU/DSP or PPU preparation is the actual deadline blocker.
- Presentation boundaries account for a visible dip independently of completed work.

## Current discriminating experiments

**Sub-presence dataflow, `76f3f9`:** draw Sub depth tags directly into the owned
presence surface, then select the independent Main winner surface after the
existing Sub SyncFull fence. Keep Sub colors, source rendering, Main enables,
TS=0 transition, raw/direct Z bypass, arbitrary-Y alignment and the unchanged
32-pixel resolver. This removes the two-way tag snapshot and its overlay trip;
the full-general 224-row structural reduction is 250,880 bytes. Its compiled
transition/address tests pass. No elapsed-cost fraction or native gain is yet known.

**Packed arithmetic, `3a0c7fc`:** replace the complete general add/subtract,
full/half operator using independently checked packed channel arithmetic. Keep
DMA grouping, source production, winner/eligibility, clipping, absent-Sub and
window semantics intact. Compiled arithmetic contracts pass. Reduced instruction
count is an experimental lead, not a complete-frame timing result.

Qualify and measure each candidate independently against A13 before combining
them. Complete image and memory-guard qualification, armed recorder progression
and exact build matching precede a physical comparison. Return to the same
scenes and settings; compare sustained cadence, explicit waits, normal output,
progression and audio. These bounded experiments are the next step. A complete
new renderer or newly qualified internal-stage recorder is not required now.

If neither changes the relevant budget enough, continue with the bounded
[renderer/dataflow experiment](GATE_C_RENDERER_ARCHITECTURE_PLAN.md), including
source production. Do not respond with another unranked series of admission patches.

## Measurement options if the decision remains ambiguous

Keep manual arming and 20-second capture. Repeated launches of the same personal
ROM already reserve unique diagnostic destinations through the opt-in paired
SummerCart menu; no ROM aliases are required. Preserve ordinary progress and
qualify the guest SRAM reservation per game. The recorder's <=8 KiB contract
cannot be applied blindly to another guest.

Associate CPU handoffs with the correct logical rendered frame. The CPU may
prepare N+1 while RSP renders N; queue parity alone is not a monotonically
increasing frame identity. Record exact source/build/settings and retain the
matching linked symbols.

Count deltas, completed boundaries, explicit CPU RSP/VI waits and linked CPU
domain samples are current evidence. Sample shares are estimates, not exact
per-frame CPU times. For a future qualified RSP publication mechanism, classify
active overlay and resident operation ranges only after auditing ownership,
fixed bank ABI, register preservation and observer cost. Reject ambiguous
transitions. Live-DMEM bookends do not satisfy that requirement.

Low-frequency DP counter deltas are an option only after counter width,
wrap/reset and read semantics are qualified. A busy bit is not an active-time
counter. Correlate any added counters with logical frames and explicit waits;
a large RDP share alone does not show a CPU stall.

If needed, collect work at existing phase/section boundaries:

- Rows and sections per policy, general resolution and mask-build counts.
- Admission rejection categories from actual dispatch conditions.
- CGRAM/brightness/window epochs and OAM rebuilds.
- Texture/overlay/snapshot/arithmetic transfer counts and bytes.
- RDP submissions, command bytes and phase/texture fences.

Add only one discriminating measurement when the alternatives cannot otherwise
be separated. Preserve data ownership and bank ABI. Exhaustive instrumentation
is not a prerequisite for a useful controlled experiment.

## Bounded retention design rationale

The present SRAM transport has 32 KiB total; guest data reserves the first
8 KiB, leaving 24 KiB for diagnostics. The shipped v4 layout is authoritative
in [Native diagnostic v4](NATIVE_DIAGNOSTIC_V4.md). The earlier proposed packing
budget below is retained as design history, not the delivered binary schema:

- 512-byte self-describing header.
- 1,280 compact 12-byte completed-frame records: 15,360 bytes.
- 20 detailed 96-byte interval summaries: 1,920 bytes.
- Two bounded pools of 48 detailed 64-byte records: 6,144 bytes.
- Total 23,936 bytes, leaving 640 bytes for alignment/guards/tails.

Any future packing must preserve the complete interval, Count wrap, explicit
partial records, saturation and exhaustion flags. Stop appending an exhausted
pool rather than silently wrapping. Selected detailed observations are not a
trace of every pixel or DMA. Keep omitted and uncertain data explicit.

## Qualification and exit conditions

Before distributing a changed emulator or recorder:

1. Verify exact source, normal/diagnostic separation, SRAM bounds, guards, Count wrap, partial capture and decoder rejection.
2. Verify register/guest-state preservation, fixed bank entries, renderer lifetimes and saved-byte identity.
3. Compare complete framebuffer outputs on fidelity controls and relevant half/subtract/window/raster combinations.
4. Verify observer progression and account for the limits of its cost measurement; ISR-body timing alone is not total perturbation.
5. Keep real-game inputs, raw saves, footage, state and guest hashes private; publish original controls and curated aggregate conclusions.

The initial scene-level evidence gate is complete. Precise internal-stage/work
attribution remains limited; it is needed only if the current controlled
comparisons cannot resolve the next decision. A causal optimization is qualified
only when it reduces the relevant complete cost on N64 without output, timing,
progression or audio regression. A successful local change does not declare
constant 60 FPS or whole-library fidelity. If measured movement is insufficient,
revise the algorithm or ownership structure rather than issuing another unranked batch.
