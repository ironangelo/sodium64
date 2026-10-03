# Gate C causal performance diagnosis

Status: proposed design, not an implemented recorder or a demonstrated speedup.
Runtime baseline: A11, `ac534849002a04d342dd566a6f96ae1707680387`.
The normal emulator and master stay unchanged while this measurement design is qualified.

## Decision to make

Determine which work makes a native frame miss its deadline, and whether that work is necessary for correct output, repeated unnecessarily, or serialized by an ownership dependency. Keep full audio, APU clock 21, frameskip 0 and the established visual semantics. A busy percentage alone does not answer this question.

Use a hybrid of frame-boundary timing, classified sampling, rendering-work counters and controlled experiments. Avoid timestamps on every opcode, pixel or DMA poll iteration. CPU and RSP operate concurrently, so their sampled percentages and elapsed intervals must not be summed into a fictional exclusive frame budget.

## Evidence and hypotheses

The user's new A11 normal tests report visually improved ALttP and DKC1, with approximately 20 FPS in several scenes that original Sodium64 handles at 60 FPS with visual defects. These are observations, not decoded captures of those games. Settings parity and internal workload are not yet independently established.

ALttP observations: title; new-game telepathy/darkened house; exterior night/rain. DKC1 observations: developer screen, animated Cranky/DK intro, first-stage gameplay with a gradient horizon; the static logo and parts of the second rainy stage are faster. Visible rain or sprite count alone is therefore an inadequate workload classifier.

A11 source has three distinct HCOMP policies: Main-only raw, exact direct composition, and general composition. The general policy draws Sub and Main with provenance/presence handling and composes in virtual bands of at most 8 rows. Fast admission is deliberately restricted by color math, clipping, backdrop and eligible OBJ conditions. Missing admission can be conservative and correct; broadening it requires a proof.

Source-derived general-path work: each full-width arithmetic row processes 8 batches of 32 pixels; each batch performs four 64-byte input transfers and one 64-byte output transfer, hence 40 DMA operations and 2,560 transferred bytes per row. The Sub/provenance snapshot additionally copies a 560-byte row in both directions. A 224-row fully general, nonblank frame therefore implies 824,320 bytes of these transfers alone, excluding texture/overlay DMA and RDP framebuffer traffic. This is a structural work count, NOT measured cycles, bandwidth saturation, or an FPS prediction.

Each general band also constructs 256 horizontal mask entries. Ownership matters: these masks borrow TILE_TABLE, which renderers and the Sub snapshot reuse. Identical window registers do not by themselves permit skipping mask construction in the current storage layout.

SMW must remain a separate cost family until measured otherwise. Its A11 iris-heavy interval completes 39 frames in about 1.01 seconds, with about 73 created raster sections per completed frame. All 21 live observations in that interval report policy 2 (direct). All 21 observations in the strongest later microdip interval also report policy 2. Those live values are non-atomic and cannot prove every band was direct, but they do not support attributing the known iris to general arithmetic. The new games may stress the general compositor while SMW stresses fragmented direct rendering or other costs.

Hypotheses to distinguish:
- Necessary general arithmetic/transfer work dominates.
- Conservative admission forces general composition when a cheaper exact operation exists.
- Many short raster sections repeat drawing, setup, OAM work or mask construction.
- RDP command/texture retirement, DMA or overlay loading serializes otherwise concurrent work.
- CPU/APU/DSP or PPU preparation is the actual deadline blocker.
- Presentation/counter boundaries account for an apparent dip independently of completed emulation work.

## Layer 1: low-cost whole-interval measurement

Keep manual arming and 20 seconds of real-console capture. Make it reusable across compatible games through a separately named empty diagnostic emulator, without commercial ROM bytes. Diagnostic Start behavior must be explicit; normal Start continues to open its menu. Record exact source/build/settings and the loader's mapping/SRAM configuration. Never assume that a different game's SRAM size satisfies the present <=8 KiB recorder contract.

Associate CPU handoffs and RSP observations with the correct logical rendered frame. The CPU may prepare the next frame while the RSP renders the previous one; queue parity alone is not a monotonically increasing frame identity.

Record boundary Count deltas for completed-frame cadence and explicit CPU RSP/VI waits. Separately sample S-CPU, APU static/JIT, DSP, PPU preparation, DMA, VRAM semaphore wait and unknown addresses against the exact linked ranges. These domain shares are estimates; do not present them as exact per-frame CPU times.

At each valid RSP observation, identify active overlay and classify resident or overlay ranges as rendering, arithmetic/mask preparation, overlay loading, DMA wait, RDP command-fetch retirement, or texture/phase retirement. A native-only bank identity publication must be audited against fixed IMEM/DMEM ownership and register preservation. Reject or mark ambiguous observations during a bank transition; never resolve a shared PC using a guessed overlay.

Collect low-frequency validated DP counter deltas alongside existing status bits. Counter width, wrap/reset behavior and read semantics need qualification before they become authority. A busy bit is not a substitute for an active-time counter. Correlate counters with logical frames and explicit waits; a large RDP share is insufficient to show the CPU was stalled by it.

Collect rendering work, preferably at existing phase/band/section boundaries:
- sections and rows per policy, plus general-band and mask-build counts;
- fast-admission rejection categories from actual dispatch conditions;
- CGRAM/brightness/window epochs and OAM rebuilds;
- texture/overlay/snapshot/arithmetic transfer counts and bytes;
- RDP submissions/command bytes and phase/texture fences.

Exact counters must preserve bank ABI and data ownership. If a counter cannot fit cheaply and safely, use a targeted second pass after Layer 1 identifies the relevant family. Do not make exhaustive instrumentation a prerequisite for a useful first capture.

## Bounded retention

The present SRAM transport has 32 KiB total, of which the first 8 KiB are reserved for guest data: only 24 KiB are available for diagnostics.

An initial packing budget is:
- 512-byte self-describing header;
- 1,280 compact 12-byte completed-frame records:15,360 bytes;
- 20 detailed 96-byte interval summaries:1,920 bytes;
- two separately bounded pools of 48 detailed 64-byte records:6,144 bytes;
- total 23,936 bytes, leaving 640 bytes for alignment/guards/partial-tail metadata.

This is a capacity design, not a finalized binary schema. Compact records need elapsed Count and wait/progress data; detailed records cannot silently grow. Validate frame-rate bounds, quantization/saturation and partial-frame handling before adoption. Preserve compact records across the complete interval; stop appending and flag any exhausted pool instead of wrapping. Separate early-heavy and later-dip retention so the iris cannot consume all detail space. A detailed record is explicitly a selected observation, not a full trace of every pixel or every DMA.

Do not keep a redundant raw EPC ring merely because older versions had one if classified counters plus selected EPCs answer the decision better. Any omitted or uncertain data must remain explicit in decoder output.

## Layer 2: a discriminating experiment

Once Layer 1 names the leading cost, build one controlled comparison that changes that cost while retaining identical required output. Examples:
- default exact fast path versus forced general reference on the same admitted state;
- reduced redundant setup with audited workspace ownership;
- batched transfers with unchanged dependencies;
- a cheaper exact fixed-color/window arithmetic specialization.

A forced-general reference is a diagnostic control, not a performance solution. Removing an effect, reducing audio or underclocking cannot qualify as an optimization. Do not remove command or texture fences merely because their samples are large: existing fixes rely on correct retirement before command/texture memory reuse.

Use original synthetic recipes to isolate captured combinations of policy, raster fragmentation, windows, palette epochs and OBJ eligibility. These are causal controls, not substitutes for the user's real-game measurements. Recheck the corresponding actual scenes after any candidate passes deterministic output/state validation.

## Qualification and exit conditions

Before distributing:
1. Verify exact source, normal/diagnostic separation, SRAM bounds, guard bytes, Count wrap, partial capture and decoder rejection behavior.
2. Verify tags/counters/register and guest-state preservation, fixed bank entry points, unchanged renderer lifetime dependencies and final saved-byte identity.
3. Compare full framebuffer outputs on existing fidelity controls and newly relevant half/subtract/window/raster-fragmentation combinations.
4. Measure observer cost and progression on known controls, then quantify its effect on real-console cadence. ISR-body timing alone is not the complete perturbation budget.
5. Keep all real-game saves, footage, guest state, ROMs and guest hashes private; publish only emulator code/original controls and curated aggregate conclusions.

Initial real-scene matrix: SMW title iris plus later intro dips; ALttP title; DKC1 animated intro. These are accessible repeated scenes. Add the dark house/exterior and stage1/stage2 contrast only if the initial captures leave competing explanations unresolved or a candidate needs coverage there.

Layer 1 is complete when a report identifies the cost family, the relevant work quantities and how that cost crosses the frame deadline. Layer 2 is complete only when a controlled candidate reduces that cost on N64 without output, timing or audio regression. A successful local optimization does not declare constant60 FPS or whole library fidelity. If no measured candidate moves the target, revise the algorithm or dependency structure rather than issuing another unranked batch.
