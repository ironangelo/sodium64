# Sodium64 — Road to 1.0

## Purpose

This document defines the destination of the `ironangelo/sodium64` fork. It is intentionally more stable than `docs/ROADMAP.md`.

- `ROAD_TO_1_0.md` defines **what success means**.
- `ROADMAP.md` defines **the current technical route** to get there and may change as measurements teach us more.
- `continuity:docs/CONTINUITY.md` records **where the project is today**, what was learned, and what happens next.

The project may change architecture many times. The destination should not quietly move just because a hard problem appears.

## North star

Build a Sodium64 that treats Nintendo 64 hardware as a serious target platform for high-fidelity SNES emulation rather than accepting historical compromises as permanent limits.

The final target is:

> Run the target SNES software library on real Nintendo 64 hardware at correct native temporal speed, with one emulated SNES frame per intended display frame, full-rate audio, high visual/audio fidelity, broad base-system compatibility, and first-class support for important enhancement hardware including Super FX / Super FX 2 and SA-1.

The project starts from Hydr8gon's Sodium64 architecture and improves it. It should not drift into a second unrelated emulator merely because an experiment is interesting.

## What “full speed” means

A result does **not** count as full speed merely because an FPS counter shows 60.

For a workload to count as meeting the native-frame target:

- the guest advances at the intended SNES temporal rate;
- no required frames are deliberately skipped to manufacture throughput;
- no frame generation or duplicated-frame trick is used to hide missed emulation work;
- the SPC700/APU runs at full intended rate rather than Sodium64's inherited underclock mode;
- DSP/audio output remains synchronized and is not stretched, muted, or otherwise reduced to hide CPU cost;
- required PPU, DMA/HDMA, coprocessor, interrupt, and memory work is still performed;
- the result is reproducible on real N64 hardware, not only in an N64 emulator.

PAL software should be judged against its intended 50 Hz-class cadence and NTSC software against its intended 60 Hz-class cadence rather than forcing every title into one nominal number.

## What “high fidelity” means

Performance is not allowed to come from amputating the SNES experience.

The 1.0 target requires:

- correct-enough CPU semantics and timing for the compatibility corpus;
- stable PPU rendering across normal backgrounds, sprites, windows, color math, Mode 7, interlace/hires cases where supported by the target corpus, and timing-sensitive effects;
- synchronized SPC700/DSP behavior and audio output without the inherited APU underclock compromise;
- correct DMA/HDMA, interrupts, controller behavior, SRAM and cartridge mapping for supported software;
- enhancement chips represented as timed cartridge devices rather than per-game hacks;
- regressions backed by deterministic tests whenever practical.

Cycle-perfect behavior everywhere is an aspiration, not something that may be claimed without evidence. Where exact timing cannot yet be reproduced, the remaining approximation should be documented rather than hidden.

## Compatibility target

The long-term target is broad commercial-library compatibility, not a hand-picked list of easy games.

Compatibility work should use an explicit corpus containing:

1. base SNES titles that stress CPU, PPU, DMA/HDMA, audio and timing in different ways;
2. known edge cases and homebrew/test ROMs that isolate hardware behavior;
3. representative enhancement-chip titles;
4. PAL and NTSC coverage where timing differences matter.

A game-specific toggle or custom execution mode is not the preferred definition of support. Exceptions should be treated as temporary diagnostic tools unless the original cartridge genuinely contained distinct hardware that must be modeled.

The exact release corpus will evolve, but its membership and expected results must be versioned so that compatibility cannot improve merely by changing what gets tested.

## Enhancement-chip target

### Required major targets

The “Perfect target” explicitly includes:

- DSP-1 family support hardened beyond the current partial implementation;
- Super FX / Super FX 2;
- SA-1.

Other enhancement hardware should be added according to compatibility value and architectural leverage, including suitable decompression, math and cartridge-controller devices.

Super FX and SA-1 are intentionally written into the destination even though they are difficult. Their difficulty is a reason to measure and redesign, not a reason to silently remove them from scope.

### N64-alone first; cartridge assistance only with evidence

The primary target is an unmodified Nintendo 64 doing the emulation itself.

A smart flashcart or cartridge-side accelerator may become an optional architectural path only after we can show, with measurements, that a required workload exceeds a demonstrated N64-alone budget or that offloading a cartridge-like coprocessor produces a materially better result without compromising fidelity.

“Other emulators have not done it” is not evidence of a hardware ceiling.

## Architectural principles

The final implementation may use very different techniques from the starting fork. The following are allowed when justified by measurement and validation:

- 65C816-to-MIPS dynamic translation;
- reusable translation infrastructure for SA-1;
- GSU/Super FX block translation;
- targeted RSP or RDP assistance;
- aggressive cache-aware code/data layout;
- specialized fast paths that preserve observable SNES semantics;
- cartridge assistance after the N64-alone path has been quantitatively evaluated.

The following are warning signs rather than progress:

- hundreds of tiny builds with no measured performance movement;
- instrumentation that becomes the project instead of enabling decisions;
- game-specific modes replacing hardware emulation;
- speedups achieved by frame skipping, APU underclocking or omitted rendering/audio work;
- a clean-sheet emulator growing beside Sodium64 without a demonstrated reason to replace an existing subsystem.

## 1.0 release gates

Sodium64 1.0 should not be declared from one showcase title. The release gates below are cumulative.

### Gate A — Measurable, reproducible platform

- automated N64 builds are reproducible;
- deterministic host tests cover critical tooling and translated-code semantics where applicable;
- profiling can separate major runtime costs without materially distorting them;
- milestone builds can be validated on real N64 hardware with recorded settings and results.

### Gate B — Base SNES native-frame performance

On the defined base-system performance corpus:

- no required frameskip;
- full-rate APU;
- stable audio synchronization;
- native temporal cadence is sustained in the measured gameplay segments;
- no major visual or gameplay regression is accepted as the source of the speedup.

### Gate C — Base-system fidelity and compatibility

- the compatibility corpus boots and progresses to its defined checkpoints at the expected rate;
- PPU/audio/timing regression suites meet their expected results;
- known accuracy compromises are either fixed or explicitly documented with evidence and severity;
- ordinary supported games do not require manual per-game emulator modes.

### Gate D — Coprocessor framework

- cartridge devices have explicit memory, timing, IRQ/DMA and state boundaries;
- DSP-1-class support is hardened;
- adding a new enhancement device no longer requires scattering game-specific logic through unrelated core subsystems.

### Gate E — Super FX / Super FX 2

Representative Super FX and Super FX 2 titles must:

- boot and remain stable through defined extended-play checkpoints;
- render and synchronize correctly enough to meet the project's fidelity criteria;
- sustain the native temporal target in the defined measured gameplay segments, or have no 1.0 claim for those titles yet.

### Gate F — SA-1

Representative SA-1 titles must meet the same standard: functional correctness, extended-play stability, fidelity and native temporal performance in the defined measured segments.

### Gate G — Release hardening

- broad compatibility regression pass;
- real-hardware validation on representative N64 configurations/flashcart paths;
- sensible defaults with performance cheats disabled;
- user-facing diagnostics and compatibility documentation;
- no unresolved blocker that contradicts Gates A–F.

## Milestone ladder

The project can celebrate intermediate releases without pretending they are 1.0.

- **M0 — Measured Sodium64:** reliable profiling and reproducible workloads identify where frame budget is spent.
- **M1 — Faster base core:** major measured bottlenecks are reduced without fidelity loss.
- **M2 — Base SNES native-frame:** representative ordinary SNES titles sustain the target with full-rate audio and no required frameskip.
- **M3 — Accuracy recovery:** inherited performance compromises are removed and regression coverage expands.
- **M4 — Coprocessor-ready architecture:** cartridge enhancement devices have a reusable framework.
- **M5 — Super FX class:** representative Super FX / Super FX 2 software reaches the project's correctness and performance target.
- **M6 — SA-1 class:** representative SA-1 software reaches the same target.
- **M7 — Compatibility hardening:** broad library coverage and real-hardware regression are the main remaining work.
- **1.0 — Perfect-target release gate:** all mandatory gates above are satisfied by evidence, not expectation.

The milestone order may change if profiling reveals a better dependency order. Their definitions should remain measurable.

## Current position

**M0, M1 and M2 / Gate B are achieved; M3 / Gate C is active.**

M0 established the first representative real-N64 authority measurement. The Gothicvania survivability workload, with frameskip `0`, full-rate APU clock `21`, audio enabled and precision `8`, completed **48/60, 49/60, 48/60, 50/60 and 50/60** guest frames across five complete 60-VI windows (mean **49.0/60**). That capture had essentially no VI idle headroom and placed **61.83%** of R4300 samples in APU/JIT/DSP-audio work, making APU/audio the first measured M1 gate driver.

M1 corrected the SPC700 timing foundation and replaced byte-span-only JIT interleave with a **guest-cycle-bounded multi-op contract**. The compiler retains the independent 16-byte source safety limit, but returns to the scheduler after a completed block exceeds a 20-SPC-cycle continuation threshold. With the pinned finite-op maximum of 12 cycles, a block can consume at most **32 SPC cycles / 672 master cycles** before scheduler return at Road-valid APU clock `21`.

The architecture was not accepted from throughput alone. A corrected multi-op baseline reached the ares throughput ceiling while producing DSP events at least one full period late; a one-op causal control removed that lateness but fell to about **49.4/60**; the clobber-safe cycle-budget v2 restored multi-op throughput while keeping the measured DSP scheduler tail below one 32-cycle period. A directed edge proof now covers **119 cases plus halted-state observations**, including exact `20 + DIV = 32` blocks, access-built 32-cycle blocks, conditional paths near the cutoff, cached replay and entry-tag invalidation. This is strong regression evidence for the audited contract, not an exhaustive proof of every SPC700 state or observable bus side effect.

The resulting real-N64 M1 capture completed **60/60 in all five measured 60-VI windows** with frameskip `0`, APU clock `21`, audio `4`, precision `8` and 3,580 valid samples. The profile contained **11.51% frame/VI wait**, showing that this exact workload is no longer throughput-bound on the R4300. APU/JIT/DSP-audio accounted for **51.03% of samples** versus 61.83% at M0; that is a change in sampled execution share, not a direct measurement of absolute subsystem cost.

The defensible causal statement is therefore:

> The combined corrected timing foundation plus guest-cycle-bounded APU JIT removes the measured Gothicvania frame-budget deficit on real N64 under Road-valid settings. The cycle-budget architecture specifically preserves multi-op throughput while restoring the validated DSP scheduler-return bound.

It is **not** justified to assign the entire M0 `49/60 -> 60/60` movement to the final cycle-budget patch in isolation.

M1's material exit condition is satisfied: a measured base-core bottleneck was reduced without using frameskip, additional APU underclock, muted audio or an accepted timing regression, and the result materially improved the real-N64 frame budget.

Gate B was subsequently closed with a three-workload versioned base-system corpus: **Gothicvania, Space Rescue Squad, and Nova the Squirrel 2**. After emulator-lab route/semantic qualification, the two remaining workloads were measured on real N64 hardware with the same Road-valid settings. Both SRS and Nova2 completed **60/60 in all five measured 60-VI windows** with frameskip `0`, APU clock `21`, audio `4`, and precision `8`; the returned captures contained 3,582 and 3,583 valid statistical samples respectively. Together with Gothicvania's prior real-hardware 60/60 ×5 result, the defined Gate-B corpus now sustains native-frame throughput on real hardware without frameskip or APU underclocking.

The Nova2 hardware video was effectively silent, but this is not currently evidence of an emulator audio regression: the exact pinned benchmark level's upstream `levels/firstlevel.json` sets `"Music": null`, while the hardware capture still shows full-rate APU execution, DSP/audio activity, and audio setting `4`. Space Rescue Squad produced audible output in the hardware video and substantial DSP/audio execution in the profile. This evidence is sufficient for the measured Gate-B performance corpus; it is **not** a claim of full-library PCM fidelity, long-run drift immunity, or broad audio compatibility, which remain Gate-C/release-hardening concerns.

**M2 / Gate B is therefore achieved.** Gothicvania, SRS and Nova2 become regression controls rather than automatic optimization targets. Do not resume S-CPU/APU/DSP optimization, a 65C816 dynarec, or other major performance architecture work unless a new measured workload demonstrates a real blocker. The active milestone is **M3 / Gate C: base-system fidelity and compatibility**, beginning from already-known PPU/compositor regressions and expanding deterministic compatibility evidence.

## Decision rule

For major work, ask:

> Which 1.0 gate does this move, what measurement would prove that movement, and what would make us abandon this approach?

If those questions cannot be answered, the work probably needs a stronger justification before becoming a major branch.
