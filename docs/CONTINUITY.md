# Sodium64 fork continuity

This branch is the canonical handoff point for continuing the project across ChatGPT conversations, development sessions, and long gaps between milestones.

## Branch role

- Canonical handoff branch: `continuity`
- Stable integration branch: `master`
- Feature/phase work happens on branches and PRs targeting `master`.
- `continuity` is not a feature branch and should not normally be merged into `master`.
- Preferred cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**.
- Each checkpoint should preserve useful engineering rationale, evidence, rejected interpretations, risks, and the next action rather than relying on chat history or hidden reasoning.

## Project hierarchy

Read the project at three levels:

1. `master:docs/ROAD_TO_1_0.md` — **destination / contract**. Defines what success means and the cumulative release gates.
2. `master:docs/ROADMAP.md` — **current route**. May change when evidence shows a better way to reach the destination.
3. `continuity:docs/CONTINUITY.md` — **current position**. Records where the project actually is today.

A hard technical problem may change the route. It should not silently weaken the destination.

## Ownership and working model

- Repository: `ironangelo/sodium64`
- Upstream: `Hydr8gon/sodium64`
- Iron owns the project and the north star.
- The assistant acts as technical lead/captain: architecture, implementation strategy, profiling, validation, Git workflow, and deciding when real-hardware testing is worth requesting.
- Development stays inside `ironangelo/sodium64`; do not send PRs upstream unless Iron explicitly asks.
- Real Nintendo 64 testing is a milestone gate, not a per-commit ritual.

## Road-to-1.0 north star

The stable definition lives in `master:docs/ROAD_TO_1_0.md`.

The Perfect target requires Sodium64 on real N64 hardware with:

- correct native temporal cadence rather than an FPS-counter illusion;
- no required frame skipping or frame generation;
- full-rate SPC700/APU and synchronized DSP/audio, without the inherited APU underclock compromise;
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

## Starting architecture and leading hypothesis

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

Do not use an N64 emulator's host wall-clock throughput as real-N64 FPS. Automated emulators are laboratories for correctness, execution and causal workload profiling, not substitutes for the hardware performance result.

## Integrated milestones so far

### PR #1 — project foundation

Merged. Established branch/PR workflow, automated build validation, artifacts, metrics, validation policy and the engineering PR template.

### PR #2 — baseline measurement map

Merged as `1cb72a06a9c5ce5e4abb5cdd5c10f01a92ebeffd`.

Defined what Phase 1 must measure before committing to architecture changes.

### PR #4 — development-branch validation

Merged as `58f2061cc22206c3b6fdf08845d7ea7b478f05d6`.

Development-branch pushes validate automatically while rolling releases remain restricted to `master`.

### PR #3 — statistical R4300 profiler

Merged as `6e002dc1e3387916013b994f3a62a0620b73aef8`.

Key results:

- optional `PROFILE=1` mode; normal release runtime stays uninstrumented;
- CP0 Count/Compare IP7 statistical EPC sampling;
- 4,096-entry ring buffer with wrap reconstruction;
- exact-ELF host symbolication;
- canonical and Mupen word-swapped dump support;
- deterministic host decoder tests;
- original synthetic SNES smoke ROM;
- automated Mupen runtime extraction.

Mupen proved the profiler plumbing but produced Sodium64-specific PIF/RSP errors and a 100% `rsp_wait` retained distribution. That distribution is explicitly **not** accepted as the real gameplay bottleneck.

### PR #5 — ares profiling path

Merged as `c0334377f8c473e3b8168649eaf08d26e68bf19d`.

Key results:

- pinned N64-only ares build;
- custom minimal GDB RSP client;
- ares-required initial `+` handshake;
- `QPassSignals` so normal guest MIPS/TLB exceptions reach Sodium64 instead of stopping the debugger;
- RDRAM profile extraction and decoding without replacing the existing normal/Mupen validation path.

The initial short ares run demonstrated real S-CPU/APU samples instead of Mupen's 100% `rsp_wait`, but only eight samples were collected and no bottleneck conclusion was drawn.

### PR #7 — Road to 1.0

Merged as `7fc7e21f9f674466680d0db73e16cf29dbb5878a`.

Added `docs/ROAD_TO_1_0.md` and made the project hierarchy explicit:

- Road to 1.0 = destination;
- ROADMAP = route;
- continuity = current position.

The Road explicitly keeps full-rate audio, no frameskip cheats, Super FX / Super FX 2, SA-1, real-hardware validation, and evidence-based hardware-ceiling decisions in the Perfect target.

### PR #6 — deterministic workload bottleneck map

Merged as `2f6d1a446ba81662a6079d94c6d7dfb5f00a9aac`.

This is the first successful causal profiling suite rather than a single smoke loop.

Implemented:

- original deterministic SNES workloads: `idle`, `cpu-alu`, `wram`, `ppu-registers`, `dma-vram`;
- workload generation/checksum/vector tests;
- exact-linker-map subsystem classification on the host;
- JSON + Markdown profile matrices;
- one interpreter control plus ares N64 recompiler measurement runs;
- warm-up before diagnostic patches;
- full-rate APU measurement at `apu_clock = 21`;
- APU JIT lookup invalidation + `jit_pointer` reset before measurement so old underclock timing is not retained;
- profiler-ring reset after preparation so the preparation cost is excluded;
- longer debugger stop timeout for graphics-heavy workloads;
- adaptive repeated measured windows until a minimum sample density is reached.

#### Final validated synthetic matrix

| workload | samples | S-CPU | APU JIT | APU static | DSP | PPU/frame prep | DMA/HDMA | frame/VI wait |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| idle | 2,138 | 49.2% | 4.1% | 33.6% | 1.4% | 2.0% | 0.1% | 9.5% |
| cpu-alu | 1,923 | 61.3% | 1.7% | 35.1% | 0.5% | 1.1% | 0.3% | 0.0% |
| wram | 1,594 | 59.2% | 2.9% | 35.1% | 0.8% | 1.9% | 0.1% | 0.0% |
| ppu-registers | 1,030 | 52.3% | 3.7% | 24.9% | 0.6% | 18.4% | 0.1% | 0.0% |
| dma-vram | 948 | 0.1% | 0.3% | 0.7% | 0.0% | 96.7% | 2.1% | 0.0% |

PPU-register and DMA-VRAM needed two three-second windows; the others reached density in one. The ares recompiler produced orders of magnitude more samples per CI wall-clock second than the interpreter control, making the laboratory practical.

#### What this evidence means

The profiler/classifier reacts causally and in the expected direction:

- deliberately CPU-heavy guest work shifts samples toward S-CPU paths;
- PPU-register churn raises PPU/frame-preparation representation;
- DMA-to-VRAM drives samples overwhelmingly into the VRAM/PPU path.

This validates the **measurement harness**.

#### What this evidence does NOT mean

- `61.3% S-CPU` in the CPU-ALU control does not prove commercial games spend 61.3% there.
- `96.7% PPU` in DMA-VRAM does not mean ordinary gameplay spends 96.7% there.
- ares recompiler wall-clock speed is not N64 speed.
- PR #6 by itself does not justify starting the 65C816 dynarec.

Synthetic ROMs are controlled stress tests. They establish measurement sensitivity; they do not replace representative gameplay and hardware frame-budget evidence.

## Current phase

**M0 / ROADMAP Phase 1 — baseline and bottleneck map.**

The profiler, extraction paths and causal synthetic workload suite are now integrated infrastructure. The next job is no longer to build more profiler plumbing unless a specific measurement gap requires it.

Phase 1 still needs representative evidence for:

- S-CPU share during actual game-like workloads;
- APU/SPC700 + DSP share at full-rate audio;
- PPU/event/HDMA/frame-preparation cost in representative frames;
- RSP wait and framebuffer/VI back-pressure;
- memory/cache/TLB-sensitive paths where material;
- native-frame deadline/headroom under no-frameskip/full-rate-audio conditions.

## Next batch — representative gameplay / frame budget

Goal: move from controlled synthetic causality to evidence sufficient to choose the first M1 architecture.

Planned direction:

1. Define a small representative base-SNES profiling corpus/workload set that exercises different real game patterns without turning CI into a commercial-ROM repository.
2. Prefer legal/open test/homebrew workloads in automated CI; commercial titles, where necessary for compatibility/performance decisions, remain local/milestone inputs rather than committed assets.
3. Add or derive frame-progress/deadline measurements so Phase 1 can distinguish “where the R4300 was sampled” from “did this workload actually meet native cadence and how much headroom remained?”.
4. Keep full-rate APU and no required frameskip as the Road-to-1.0 measurement condition.
5. Compare repeated representative profiles for stability; do not select architecture from a single short run.
6. If emulator laboratories cannot provide credible frame-budget evidence, package one efficient real-N64 milestone session that answers several questions at once.
7. Use that evidence to decide whether Phase 2 opens with the 65C816 dynarec POC or whether another subsystem has a stronger measured claim on the first optimization batch.
8. Checkpoint continuity before beginning that major architecture branch.

## Hardware-test policy for Iron

Do not ask Iron to copy a build to real N64 after every change. Request a hardware session only when one milestone package can answer several concrete questions or a hardware-specific uncertainty cannot be resolved at a cheaper layer.

A hardware request must specify:

- exact build/artifact;
- exact ROMs/tests;
- settings;
- observations/metrics needed;
- decision the answers unlock;
- why host/emulator validation is insufficient.

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
