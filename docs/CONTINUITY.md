# Sodium64 fork continuity

This branch is the canonical handoff point for continuing the project across ChatGPT conversations, development sessions, and long gaps between milestones.

## Branch role

- Canonical handoff branch: `continuity`.
- Stable integration branch: `master`.
- Feature/phase work happens on branches and PRs targeting `master`.
- `continuity` is not a feature branch and should not normally be merged into `master`.
- Preferred cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**.
- Checkpoints preserve engineering rationale, evidence, rejected interpretations, risks, and the next action instead of relying on chat history or hidden reasoning.

## Project hierarchy

1. `master:docs/ROAD_TO_1_0.md` — **destination / contract**.
2. `master:docs/ROADMAP.md` — **current technical route**.
3. `continuity:docs/CONTINUITY.md` — **current position**.

A hard technical problem may change the route. It should not silently weaken the destination.

## Ownership and working model

- Repository: `ironangelo/sodium64`.
- Upstream: `Hydr8gon/sodium64`.
- Iron owns the project and sets the north star.
- The assistant acts as technical lead/captain: architecture, implementation strategy, profiling, validation, Git workflow, and deciding when real-hardware testing is worth requesting.
- Do not send PRs upstream unless Iron explicitly asks.
- Real Nintendo 64 testing is a milestone gate, not a per-commit ritual.

## Road-to-1.0 north star

The stable definition lives in `master:docs/ROAD_TO_1_0.md`.

The Perfect target is Sodium64 on real N64 hardware with:

- correct native temporal cadence rather than an FPS-counter illusion;
- no required frame skipping or frame generation;
- full-rate SPC700/APU and synchronized DSP/audio without the inherited APU underclock compromise;
- high CPU/PPU/audio/DMA/HDMA/timing fidelity;
- broad base-system compatibility rather than a hand-picked easy-game list;
- enhancement chips modeled as first-class timed cartridge devices rather than per-game modes;
- hardened DSP-1-family support;
- Super FX / Super FX 2 at the same correctness/performance standard;
- SA-1 at the same standard;
- real-N64 evidence as the authority for hardware-specific performance claims.

N64-alone is the primary target. Cartridge-side acceleration may be considered only after a hardware-budget gap is demonstrated quantitatively. “Nobody has done it before” is not evidence of impossibility.

### Milestone ladder

- **M0 — Measured Sodium64**
- **M1 — Faster base core**
- **M2 — Base SNES native-frame**
- **M3 — Accuracy recovery**
- **M4 — Coprocessor-ready architecture**
- **M5 — Super FX class**
- **M6 — SA-1 class**
- **M7 — Compatibility hardening**
- **1.0 — Perfect-target release gate**

Current position: **M0 / ROADMAP Phase 1**.

## Starting architecture and leading hypotheses

Fork starting point: upstream commit `a4c75d3819691f5fdb6de49712090c643f17abea` (11 Jul 2025).

Important inherited architecture:

- SNES S-CPU: optimized MIPS assembly 65C816 interpreter.
- SPC700/APU: existing block JIT to generated MIPS.
- PPU/event preparation: R4300 side.
- frame rendering: custom RSP microcode.
- DSP/audio, DMA, memory, input and menu: predominantly assembly.
- explicit existing enhancement-chip implementation: DSP-1 (`src/xcop_dsp1.S`).
- inherited compromises include frameskip options, frame-precision tradeoffs, APU underclock and timing approximations.

The leading future optimization hypothesis remains a reusable **65C816 -> R4300 MIPS dynarec** because it could reduce ordinary S-CPU cost, free budget for fidelity/coprocessors, and later provide reusable machinery for SA-1. It remains a hypothesis until Phase 1 representative measurements support it.

The leading Super FX direction remains a distinct GSU -> MIPS block translator with proper cache/ROM/RAM/timing integration; RSP/RDP assistance is considered only for narrowly measured wins.

## Validation philosophy

Use the cheapest reliable layer first:

1. deterministic host tests;
2. N64 cross-build/static artifacts;
3. automated N64-emulator execution for controlled integration experiments;
4. milestone emulator compatibility/performance runs;
5. real N64 as final authority.

Do not use an N64 emulator's host wall-clock throughput as real-N64 FPS. Automated emulators are laboratories for correctness, execution and causal workload profiling, not substitutes for hardware performance results.

## Integrated milestones

### PR #1 — project foundation

Merged. Established branch/PR workflow, automated build validation, artifacts, metrics, validation policy and engineering PR template.

### PR #2 — baseline measurement map

Merged as `1cb72a06a9c5ce5e4abb5cdd5c10f01a92ebeffd`.

Defined what Phase 1 must measure before committing to architecture changes.

### PR #4 — development-branch validation

Merged as `58f2061cc22206c3b6fdf08845d7ea7b478f05d6`.

Development-branch pushes validate automatically while rolling releases remain restricted to `master`.

### PR #3 — statistical R4300 profiler

Merged as `6e002dc1e3387916013b994f3a62a0620b73aef8`.

Implemented optional `PROFILE=1`, CP0 Count/Compare EPC sampling, a 4,096-entry ring, exact-ELF symbolication, endian normalization, deterministic decoder tests and automated Mupen extraction. Mupen proved the profiler plumbing but produced PIF/RSP incompatibilities and a misleading 100% `rsp_wait` distribution; that distribution is not accepted as the real bottleneck.

### PR #5 — ares profiling path

Merged as `c0334377f8c473e3b8168649eaf08d26e68bf19d`.

Added pinned N64-only ares, a minimal GDB RSP client, the ares-required initial `+` handshake, guest MIPS/TLB exception pass-through via `QPassSignals`, and RDRAM profile extraction without replacing the normal/Mupen validation path.

### PR #7 — Road to 1.0

Merged as `7fc7e21f9f674466680d0db73e16cf29dbb5878a`.

Added `docs/ROAD_TO_1_0.md` and froze the destination/route/current-position hierarchy. The Road explicitly keeps full-rate audio, no frameskip cheats, Super FX / Super FX 2, SA-1, real-hardware validation, and evidence-based hardware-ceiling decisions in the Perfect target.

### PR #6 — deterministic workload bottleneck map

Merged as `2f6d1a446ba81662a6079d94c6d7dfb5f00a9aac`.

Added five original deterministic SNES workloads (`idle`, `cpu-alu`, `wram`, `ppu-registers`, `dma-vram`), exact-linker-map subsystem classification, JSON/Markdown matrices, ares recompiler runs, full-rate APU profiling, APU JIT invalidation before measurement, adaptive sample windows and robust debugger stopping.

Final synthetic causal profile matrix from the validated run:

| workload | samples | S-CPU | APU JIT | APU static | DSP | PPU/frame prep | DMA/HDMA | frame/VI wait |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| idle | 2,138 | 49.2% | 4.1% | 33.6% | 1.4% | 2.0% | 0.1% | 9.5% |
| cpu-alu | 1,923 | 61.3% | 1.7% | 35.1% | 0.5% | 1.1% | 0.3% | 0.0% |
| wram | 1,594 | 59.2% | 2.9% | 35.1% | 0.8% | 1.9% | 0.1% | 0.0% |
| ppu-registers | 1,030 | 52.3% | 3.7% | 24.9% | 0.6% | 18.4% | 0.1% | 0.0% |
| dma-vram | 948 | 0.1% | 0.3% | 0.7% | 0.0% | 96.7% | 2.1% | 0.0% |

Interpretation: the profiler responds causally to deliberately different guest activity. These numbers validate the laboratory, not a commercial-game bottleneck claim.

### PR #8 — correlate profiles with virtual N64 frame budget

Merged as `798ebcb9969d94eda3eba4592eae2792d6304cb5`.

Purpose: connect the statistical profile to Sodium64's own frame-progress signal without adding runtime instrumentation.

Key design decisions:

- Reuse existing Sodium64 `fps_display`, `fps_native`, `fps_emulate`, and `frame_count` state instead of adding new per-frame counters.
- `fps_display` is updated by Sodium64 every 60 N64 VI interrupts from the guest-frame progress counter; with frameskip forced off it is an in-N64-model measure of completed SNES frames per 60 VIs.
- Do **not** treat ares/CI host wall-clock throughput as N64 performance.
- Measurement sequence is: normal warm-up -> apply full-rate/no-frameskip/audio-on settings and invalidate APU JIT -> short settle period -> reset profiler/FPS state -> measured interval.
- `fps_display` is seeded to `0xFF` before measurement so a valid report proves that at least one complete post-configuration 60-VI window occurred.
- Recompiler workloads require at least 800 statistical samples; below-60 frame results are reported as evidence rather than failing CI.
- The run verifies `skipped_set=0`, `apu_clock=21`, and audio enabled.

#### Final validated frame-budget evidence

| workload | completed guest frames / 60 VI | virtual budget | dominant sampled cost |
| --- | ---: | ---: | --- |
| idle | **60/60** | **100.0%** | S-CPU + APU, with some frame/VI wait |
| cpu-alu | **42/60** | **70.0%** | S-CPU interpreter (~60.9%) |
| wram | **47/60** | **78.3%** | S-CPU (~56.6%) + APU static (~36.9%) |
| ppu-registers | **34/60** | **56.7%** | S-CPU (~51.1%) + PPU/frame prep (~19.2%) + APU |
| dma-vram | **1/60** | **1.7%** | PPU/frame prep (~98.3%) |

Observed settings for all recompiler measurements:

- `apu_clock = 21`;
- `skipped_set = 0`;
- `audio_set = 4` (enabled);
- `precision_set = 8` was recorded rather than silently changed.

Important interpretation:

- The same measurement window now answers both **where the R4300 spends time** and **whether that workload meets the 60-VI virtual frame budget**.
- CPU/ALU stress reduces throughput and concentrates samples in S-CPU code.
- PPU-register stress increases PPU/frame-preparation cost and reduces throughput further.
- Extreme DMA-to-VRAM collapses throughput while concentrating almost all sampled R4300 time in PPU/frame preparation.
- This is coherent causal evidence, but still synthetic and emulator-lab based.
- It does **not** mean an ordinary commercial game runs at 42/60, 34/60 or 1/60; those ROMs were deliberately constructed stress controls.
- It does **not** yet prove that the 65C816 dynarec is the first M1 architecture.

The stable Build and Validate pipeline and the ares/frame-budget workflow both passed on PR #8 before merge.

## Current phase

**M0 / ROADMAP Phase 1 — baseline and bottleneck map.**

The profiling infrastructure is now mature enough. Do not keep expanding profiler plumbing unless a specific new measurement requires it.

We now know:

- the sampler/extraction/symbolication path works;
- subsystem classification responds causally;
- ares recompiler provides adequate sample density;
- the lab can enforce full-rate APU and no frameskip;
- the lab can correlate a profile with Sodium64's own completed-frames-per-60-VI signal.

What remains before choosing the first M1 optimization architecture is **representative mixed/gameplay-like evidence**, followed by a real-hardware milestone when emulator evidence has done all it reasonably can.

## Immediate next batch — deterministic gameplay-like workload

Goal: stop measuring isolated single-subsystem stress loops and profile a workload that behaves more like an actual SNES game frame.

Planned direction:

1. Build an original source-generated SNES workload that combines normal CPU game logic, WRAM state updates, VBlank/NMI-driven frame pacing, realistic PPU register changes, OAM/sprite work and bounded per-frame VRAM/CGRAM DMA rather than saturating one unit continuously.
2. Keep it deterministic and legally commit-able so CI always has the exact same workload.
3. Prefer one balanced mixed workload first; add variants only if a concrete question requires them.
4. Run it through the existing full-rate/no-frameskip frame-budget + statistical profile harness.
5. Measure repeated runs for stability and inspect both `fps_display` and subsystem share.
6. Use this mixed result to decide what additional representative workload is needed before the first real-N64 M0 milestone package.
7. Do not begin the 65C816 dynarec branch merely because CPU-heavy synthetic controls were CPU-heavy.
8. Checkpoint continuity again after the mixed-workload result.

## Hardware-test policy for Iron

Do not ask Iron to copy a build to real N64 after every change. Request a hardware session only when one milestone package can answer several concrete questions or a hardware-specific uncertainty cannot be resolved at a cheaper layer.

A hardware request must specify exact build/artifact, ROMs/tests, settings, observations/metrics, the decision unlocked, and why emulator/host validation is insufficient.

## Guardrails

- No game-specific manual modes as the compatibility strategy.
- No frameskip, APU underclock, frame generation, muted/stretched audio or omitted required work counted as full-speed progress.
- No endless tiny numbered builds without a measurable hypothesis.
- Do not let profiling become a second emulator/project.
- Do not merge risky low-level experiments merely because they compile.
- Do not send upstream PRs without Iron's explicit request.
- Prefer architecture changes that move a Road-to-1.0 gate and have a falsifiable measurement.
- Keep `master` as the best-known stable integrated state.
- Keep this branch as the freshest handoff.

## Resume protocol

Read in this order:

1. `continuity:docs/CONTINUITY.md`
2. `master:docs/ROAD_TO_1_0.md`
3. `master:docs/ROADMAP.md`
4. `master:docs/PROFILING.md`
5. `master:docs/VALIDATION.md`
6. `master:docs/BASELINE.md`
7. current open PR/branch and its CI evidence, if any

If sources disagree, prefer the newest concrete repository/CI state and then repair this file.
