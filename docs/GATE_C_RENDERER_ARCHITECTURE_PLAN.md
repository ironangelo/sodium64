# Gate C general renderer architecture experiment

Status: the initial bounded cross-game evidence gate is met. Current qualified
reference is A13 `b4206144fefe1d77b05397be154115d6328a2965`; A11 remains a
regression control. Thirteen complete physical-console captures yield six
A11/A13 scene pairs and one unpaired A13 ALttP intro. The named A11 intro
capture was unavailable. See [curated cadence/wait evidence](GATE_C_CAUSAL_PROFILING_PLAN.md)
and [Continuity](CONTINUITY.md) for the current checkpoint.

The immediate work is two independent bounded experiments: packed arithmetic
`3a0c7fc` and Sub-presence dataflow `76f3f9`. Both have compiled contract passes;
complete pixel qualification has passed; physical-console comparison is pending.
Neither is part of A13 or a proven native speedup. Keep them separate until each
comparison establishes its effect. A complete renderer implementation and newly
qualified internal-stage instrumentation are not the next commitment.

Reliable current evidence consists of completed-boundary Count timings, explicit
CPU RSP/VI waits and exact linked CPU EPC attribution. Live-DMEM RSP bank/stage
and PPU controls are unvalidated candidates; they cannot identify the internal
operation responsible for a miss. CPU and RSP overlap. Completed boundaries are
not presented FPS, and sampled percentages are not an additive frame budget.

Both candidates passed exact-head Build and full Gate qualification: 94 normal complete images (5,390,336 pixels) and 12 armed v4 images (688,128 pixels) per candidate, with all compact guards passing. Manual and v4 original-guest recorders completed approximately 20 seconds, retained the whole v4 interval without overflow, and preserved cartridge PI payload bytes. Physical-console speed, normal output and audio comparisons remain pending.

## Current evidence and operating constraints

The sustained DKC intro/stage and ALttP room/exterior windows have long explicit
CPU waits for RSP completion and remain far below the target cadence. DKC's
developer-logo capture also contains a separate CPU/APU compiler/emitter-heavy
plateau. SMW's later near-60 interval has almost no RSP waiting, while its worst
iris intervals contain an RSP-wait component. No one internal color-math cause
or physical N64 ceiling has been established.

The current general renderer consumes real PPU sections and can process a whole
section; it is not capped at eight virtual rows. Short real epochs and
OBJ-sensitive spans still fragment work. Older eight-row descriptions are
historical, not the current ownership or scheduling contract.

Use the existing reusable empty diagnostic emulator and paired menu. Capture,
confirm completion/save, return to the flashcart menu and reload the same game
or launch the next game. The opt-in `tools/sc64-diagnostic-save` integration
reserves a unique game/build/identifier writeback target at every launch,
imports ordinary progress read-only and preserves previous reservations. An
unarmed launch can leave an incomplete reserved file. Require a complete record
and valid checksum rather than counting filenames. No duplicate or aliased ROM
files, hot game switching or new SD file browser are required.

The physical batch confirms usable capture transport on the tested menu/setup.
It does not qualify every upstream menu/firmware/storage combination. Preserve
the per-guest <=8 KiB recorder contract and ordinary saves. Commercial inputs,
raw saves, state, footage and hashes remain private.

## Road decision

Road 1.0 requires fidelity and native cadence together: full audio/APU rate,
frameskip 0, required work intact and reproducible real-console evidence. It
warns against hundreds of small builds without measured movement and against
instrumentation becoming the project.

A13 is the current qualified comparison reference. A11 remains a valuable
regression control; neither is an exhaustive SNES correctness oracle or a proven
fast general renderer. Retain their artifacts and fidelity controls while testing
a bounded replacement of rendering/composition structure. Reuse Sodium64's CPU,
APU/DSP, guest timing, loader, typed PPU event stream, caches and tile decoding
where practical.

Current evidence justifies investigating dataflow and complete rendering cost.
It does not justify a game whitelist, a common-cause assumption across all
scenes or abandoning the native target. CPU/APU costs still require their own
evidence when they block a particular interval.

## Two immediate independent candidates

**Sub-presence dataflow, `76f3f9`:** select the owned presence surface as Sub's
Z destination, then select the independent winner surface for Main after the
existing Sub SyncFull fence. Remove only the Sub-tag snapshot and its overlay
trip. Preserve Sub colors, all source production, Main enables including TS=0,
raw/direct Z-disabled paths, arbitrary-Y 64-byte alignment, fixed bank entries
and the unchanged 32-pixel resolver. Compiled transitions exercise both queues,
short/full sections and the retained fence. Full RDP pixel controls pass; native gain
remains pending.

**Packed arithmetic, `3a0c7fc`:** use component-guarded packed channel arithmetic
for the complete add/subtract/full/half operator. Preserve mask/clipping,
winner/OBJ eligibility, Sub presence/fallback, source production and DMA
grouping. Independent compiled operator checks pass; full images pass; native
complete-cost measurements remain pending.

Use A13 as the same reference for both candidates. Qualify full normal/armed
outputs, guards and recorder progression first. Then compare physical cadence,
waits, normal output and audio in the same scene set/settings. Combining them
before independent comparison would confound attribution. Neither candidate
alone is assumed sufficient for every long wait or the SMW CPU-side dips.

## Structural opportunity beyond these candidates

A13 general composition draws Sub and Main, preserves provenance/presence,
fences phases, snapshots Sub tags and reads inputs for vector arithmetic. The
arithmetic already uses eight-pixel SIMD operations. Enabling SIMD alone would
not be a new architecture.

A full-width nonblank general row requiring all Sub reads transfers 2,560 bytes for four inputs plus
one output and 1,120 bytes for the two-way tag snapshot. At 224 rows that totals
824,320 bytes, excluding RDP framebuffer, texture and overlay traffic. There
are 40 arithmetic DMA operations per full-width row. Snapshot elision removes
250,880 of those structural bytes while leaving 573,440 arithmetic bytes and
the source renderer intact. These counts are not measured bandwidth, elapsed
fractions or FPS predictions.

General resolution also rebuilds horizontal masks in storage shared with
renderers and the A13 snapshot. Real raster sections can repeat setup,
traversal and overlays on either direct or general paths. Reducing intermediate
images may help, but a replacement must also produce correct source pixels:
RSP tile/priority work can cost more than the RDP work it replaces.

## Subsequent bounded option: streamed block resolution

If the independent candidates leave a substantial complete-cost deficit,
evaluate a block pipeline that brings Main/Sub candidates, priority/eligibility
and windows together before committing final pixels. Resolve winners and exact
color operations in owned working storage, then write final output once per
block. Avoid creating an intermediate image solely to recover metadata the
producer already knew.

Organize work around real PPU state epochs and visible spans. Separate reusable
geometry, tile decoding, palette state, sprite preparation, windows and
arithmetic. Recompute changed dependencies while preserving every guest-visible
event and real raster boundary. A window can expose a lower layer; masking an
already flattened image cannot replace winner resolution.

Use the complete operator family: add/subtract, full/half, fixed/Sub operands,
absent Sub, Main clipping, math windows and layer/OBJ eligibility. Move constant
state decisions outside pixel loops. Dispatch from hardware state, not game
identity. Mode7 should later supply candidates through the same interface.

Metadata representation must preserve opaque black, transparent index-zero,
priority and OBJ eligibility independently. RDP framebuffer alpha/coverage is
not a qualified general-purpose eligibility channel; do not assume an alpha
bit survives unchanged or disable alpha comparison and silently alter occlusion.
RSP-owned indexed candidate words are a viable experiment only with explicit
ownership and independent winner/pixel controls.

Audit DMEM/IMEM lifetime deliberately. TILE_TABLE is currently reused by renderers,
masks and A13's snapshot, and overlay entry points constrain local edits. A
source/resolution experiment may require a separately owned layout and task
schedule. Do not retain an expensive allocation solely to preserve an internal
ABI; do not remove an RDP retirement barrier without a replacement dependency proof.

## Scope and viability controls

1. **Complete resolution.** Use the entire operator over independently expected Main/Sub blocks, including mixed eligibility, clipping, opaque-black Sub, absent-Sub HALF suppression and channel carry/borrow/rounding edges. Packed arithmetic is the current isolated lead. Include metadata, transfers and synchronization in its cost; instruction count alone is not a physical lower bound.

2. **Representative source production.** Add bounded Mode1 BG and OBJ candidate production with both Main/Sub selection, BG3 priority variants, tile flips/scroll and windows. Compare fused RSP source/resolution against retaining accelerated RDP source production plus streamed RSP resolution. Include cold/warm decode, map/tile/palette transfers, sprite preparation, priority, synchronization and memory contention. Fused production must earn its place on complete cost.

3. **Short real epochs.** Cover one/two-row raster changes and nonaligned section boundaries, in addition to a full general frame. Do not win solely through backdrop-only admission. Repeated geometry/OAM traversal and setup can dominate even when arithmetic is cheap. Keep direct and general workloads in the experiment.

4. **One renderer boundary.** Feed reference and experimental backends the same original deterministic inputs; compare complete outputs and progression. Preserve the old backend as a control during migration. Integration retains CPU, full APU/DSP, presentation and audio. A kernel-only pass is not integrated renderer qualification.

5. **Fixed physical corpus.** SMW iris/action, ALttP intro/room/exterior and DKC logo/intro/stage exercise the same hardware-state backend. Games reveal workload diversity and regressions; they do not determine dispatch. Reuse the existing bounded scene set rather than start an open-ended capture campaign.

These are subsequent viability controls, not a commitment to implement a whole
renderer now. Begin only after the two immediate candidates are qualified and
their complete-cost results justify the next structural experiment.

## Measurements and acceptance

Use enough evidence to distinguish source production, resolution, data movement
and ownership waits, with logical frame identities across the CPU/RSP pipeline.
Add one safe discriminating measurement only if existing timings and controlled
changes cannot resolve the choice. Precise RSP stages need qualified publication;
the shipped live-DMEM candidates are not such evidence.

Original deterministic PPU workloads isolate semantics and algorithmic cost;
emulator timing is laboratory evidence. Physical N64 is the authority for native
cadence, memory contention, DMA/RDP retirement and audio/presentation behavior.
Measure isolated cost, then source production and complete scheduling with
CPU/APU/DSP active. Concurrent work is not additive. A kernel that fits the
deadline still needs its input production and integration costs established.

Correctness requires independent SNES arithmetic/window/priority rules and the
qualified complete outputs: saturation/rounding order, absent-Sub half behavior,
clipping, palettes, OBJ eligibility, transparent holes and raster changes. New
semantics need new independent controls; existing image passes are not universal
fidelity proof.

Performance requires a defined complete-cost reduction and reproducible native
cadence in the measured integrated corpus without output, timing, progression
or audio regression. A small gain that leaves the path far outside its budget
does not justify a long migration or constant-60 claim.

If a candidate is insufficient, identify which source/compute/transfer/ownership
dependency remains and revise it. Do not grow scene-specific dispatch or declare
N64-alone impossible from one implementation. The immediate deliverable remains
two qualified, independently measured candidates; the later renderer experiment
is a bounded pixels-and-cost proof when the results require it.
