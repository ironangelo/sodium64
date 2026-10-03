# Gate C general renderer architecture experiment

Status: design checkpoint, not a new renderer, benchmark result or claim of native speed.
Baseline: A11 source ac534849002a04d342dd566a6f96ae1707680387.
This plan takes precedence over expanding fast-admission conditions as the central performance strategy. The causal profiling plan remains supporting infrastructure; implementing its entire recorder is not a prerequisite for the architecture experiment.

## Road decision

Road 1.0 requires fidelity and native cadence together, including full audio and APU rate, no required skips and real-console evidence. It explicitly warns against hundreds of tiny builds without measured movement and instrumentation becoming the project.

A11 is a valuable qualified regression reference. It is not a proven fast general renderer or an exhaustive SNES correctness oracle. Keep its normal artifact and established fidelity tests available while evaluating a bounded replacement of the PPU rendering/composition subsystem. Reuse Sodium64's CPU, APU/DSP, guest timing, loader, typed PPU event stream, cache knowledge and tile decoding where practical. This is not a separate emulator project.

The user's ALttP/DKC1 observations show substantial performance deficits in visually improved scenes. Their exact internal routes remain unmeasured. SMW's iris and later dips mostly sample the direct route, so a general arithmetic kernel alone cannot be assumed to cure those scenes. These facts justify testing the rendering dataflow, not declaring one common cause or a hardware limit.

## Structural opportunity

Current general composition draws Sub and Main, preserves provenance/presence, fences phases, copies intermediate data and reads it back for vector arithmetic. The arithmetic already uses eight-pixel vector operations. Merely enabling SIMD would not be a new architecture.

Source-derived composition traffic for a full-width nonblank general row is 2,560 bytes for four inputs plus one output, and 1,120 bytes for a two-way Sub/provenance snapshot. At 224 rows these transfers alone total 824,320 bytes, excluding RDP, textures and overlays. There are 40 arithmetic DMA operations per full-width row. General bands also rebuild horizontal masks in workspace that renderers reuse. Many raster sections can repeat setup, traversal and overlay work even on the direct route.

These counts identify eliminable structures to investigate. They do not establish a bandwidth bottleneck or predict a speedup. A replacement also has to produce the input pixels: eliminating RDP intermediates could increase RSP tile/priority work enough to lose performance.

## Preferred candidate: streamed block resolution

Evaluate an RSP block pipeline that brings Main/Sub candidate data, priority/eligibility and window state together before committing final pixels. Resolve pixel winners and exact color operations in owned local working storage, then write final output once per block. Avoid creating a full intermediate image solely to recover metadata or reread values that the producer already knew.

Organize work by actual PPU state epochs and visible spans. Separate reusable geometry, tile decoding, palette state, sprite preparation, windows and arithmetic. Recompute only the dependencies that changed, while preserving every guest-visible event and real raster boundary. A window change may expose a lower layer; applying a mask to an already flattened Main image is not a valid substitute for winner resolution.

Use a complete operator family for sum/subtract, full/half intensity, fixed/Sub operands, absent Sub, Main clipping, math windows and layer/OBJ eligibility. Parameterize or generate kernels from hardware state so constant decisions are outside pixel loops. This is a finite hardware-semantic implementation, not recognized scenes or game identities. Mode7 should supply candidates through the same resolution interface rather than require title-specific behavior.

Audit ownership explicitly. The current TILE_TABLE mask workspace is overwritten by renderer/snapshot use, and fixed overlay entry points constrain local edits. The experimental kernel may need a different owned DMEM/IMEM layout and task schedule. Do not preserve an expensive allocation solely to avoid changing internal ABI, and do not remove required RDP retirement barriers without a replacement dependency proof.

## Bounded experiment, not a wholesale rewrite

1. **Complete resolution kernel.** Build the entire color/window/eligibility operator over controlled Main/Sub candidate blocks, with exact independent expected pixels. Test the new data representation, transfer grouping and owned working storage. This establishes a measured lower bound for the candidate, not complete renderer performance.

2. **Include source production.** Add representative tile/sprite candidate production and raster state changes using existing decode knowledge. Compare fused RSP source/resolution against retaining accelerated RDP source production plus streamed RSP resolution. Select on complete cost, including decode, transfers, synchronization, metadata and memory contention. The preferred fused candidate is a hypothesis; its replacement of RDP work must earn its place.

3. **Evaluate direct and general workloads.** The experiment must cover both full general arithmetic and frequent short state epochs. It must not win only by expanding the existing backdrop-only admission. Repeated geometry/OAM traversal and phase setup matter to the already-direct SMW iris.

4. **Integrate behind one renderer boundary.** Feed both implementations the same renderer inputs and compare complete outputs and progression. Move finite PPU features to the new engine after their contracts pass. Preserve the old implementation as a test/reference backend during migration. Guest CPU, full-rate audio and timing remain active during integrated qualification.

5. **Validate a fixed cross-game corpus.** SMW iris/action, ALttP title/dark exterior and DKC1 intro/stage contrast test the same backend. Games reveal regressions and workload diversity; they do not determine dispatch rules. Keep all commercial inputs, saves, snapshots and hashes private.

## Measurements that enable this decision

Use enough instrumentation to separate source production, pixel resolution, data movement and ownership waits, with logical frame identities across the CPU/RSP pipeline. A full 20-second cross-game recorder is useful later, but not the next milestone by itself.

Architecture controls use original deterministic PPU workloads and exact shader/operator inputs. They can isolate algorithmic cost and verify pixels; they cannot replace real-game progression or physical-N64 timing. Emulator timing is lab evidence, not proof of hardware FPS.

Measure isolated kernel cost first, then source production and complete frame scheduling with full CPU/APU/DSP activity. Concurrent work is not an additive percentage budget. An isolated kernel that already exceeds the native frame deadline fails the viability filter. One that fits still needs source, handoff, presentation and audio qualification.

## Acceptance and abandonment

Correctness: independent SNES arithmetic/window/priority rules plus the existing qualified outputs, including rounding/saturation order, absent-Sub half suppression, clipping, palettes, OBJ eligibility and raster changes. Passing the current images alone is insufficient for new semantics.

Performance: measured complete-cost reduction large enough to close a defined deadline deficit, followed by native cadence in the measured integrated corpus with no output/timing/audio regression. A tiny improvement that leaves the complete path far outside its budget does not justify a long migration.

If the streamed candidate is not viable, report which source/compute/transfer dependency exceeds budget and revise that structure. Do not replace that failed hypothesis with a growing scene whitelist or declare N64-alone impossible from one implementation. The Road destination remains unchanged; CPU/audio and later coprocessor bottlenecks still require their own evidence when encountered.

The next proposed deliverable is a bounded architecture proof with pixels and a cost report, not another speculative performance wrapper or an open-ended diagnostic framework.
