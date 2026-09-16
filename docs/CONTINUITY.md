# Sodium64 fork continuity

This branch is the canonical handoff point for continuing the project across ChatGPT conversations, development sessions, and long gaps between milestones.

## Branch role

- Canonical continuity branch: `continuity`
- Stable integration branch: `master`
- Active development happens in feature/phase branches and pull requests targeting `master`.
- The `continuity` branch is **not** a feature branch and should not normally be merged into `master`.
- Update this file whenever the active phase, PR, major hypothesis, important result, validation state, or immediate next action changes materially.

## Project hierarchy

Three documents serve different purposes and should not be conflated:

1. `master:docs/ROAD_TO_1_0.md` — **destination / project contract**. Defines what success means and the cumulative release gates.
2. `master:docs/ROADMAP.md` — **current technical route**. May change when measurement shows a better path.
3. `continuity:docs/CONTINUITY.md` — **current position**. Records what just happened, what the evidence means, what remains uncertain, and the next batch.

A hard problem may change the route. It should not silently weaken the destination.

## Project ownership and working model

- Repository: `ironangelo/sodium64`
- Upstream parent: `Hydr8gon/sodium64`
- Iron is the project owner and sets the north star.
- The assistant acts as technical lead/captain: architecture, implementation strategy, profiling, validation, Git workflow, and deciding when real-hardware testing is worth requesting.
- Development PRs stay entirely inside `ironangelo/sodium64`. Do not open PRs against `Hydr8gon/sodium64` unless Iron explicitly asks.
- Real Nintendo 64 testing is a milestone validation layer, not a per-commit ritual.
- Preferred cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**.
- Checkpoints must record engineering rationale, evidence, rejected interpretations, risks, and next action rather than depending on chat history or hidden reasoning.

## North star / Perfect target

The stable definition now lives in `master:docs/ROAD_TO_1_0.md`.

In short, the project aims for Sodium64 on real Nintendo 64 hardware with:

- correct native temporal speed: one intended SNES frame per intended display frame;
- no required frame skipping or frame-generation tricks;
- full-rate SPC700/APU and synchronized DSP/audio, without the inherited APU underclock compromise;
- high visual, audio, CPU, PPU, DMA/HDMA and timing fidelity;
- broad base-system compatibility rather than a hand-picked easy-game list;
- enhancement chips modeled as first-class timed cartridge devices rather than game-specific modes;
- hardened DSP-1-family support;
- Super FX / Super FX 2 support at the same correctness/performance standard;
- SA-1 support at the same standard;
- real-N64 evidence as final authority for hardware-specific timing/performance claims.

N64-alone is the primary target. Cartridge-side acceleration may be considered only after measurements demonstrate a useful or necessary hardware-budget gap. “Nobody has done it before” is not accepted as proof of impossibility.

## Road-to-1.0 milestone ladder

- **M0 — Measured Sodium64:** reliable profiling and reproducible workloads identify where frame budget is spent.
- **M1 — Faster base core:** major measured bottlenecks are reduced without fidelity loss.
- **M2 — Base SNES native-frame:** representative ordinary SNES titles sustain native cadence with full-rate audio and no required frameskip.
- **M3 — Accuracy recovery:** inherited speed compromises are removed and regression coverage expands.
- **M4 — Coprocessor-ready architecture:** enhancement devices have a reusable framework.
- **M5 — Super FX class:** representative Super FX / Super FX 2 software reaches the correctness/performance target.
- **M6 — SA-1 class:** representative SA-1 software reaches the same target.
- **M7 — Compatibility hardening:** broad library and real-hardware regression dominate the remaining work.
- **1.0 — Perfect-target release gate:** all mandatory Road-to-1.0 gates are satisfied by evidence rather than expectation.

Current position: **M0 / ROADMAP Phase 1**.

## Starting architecture observed in upstream

Fork starting point: upstream commit `a4c75d3819691f5fdb6de49712090c643f17abea` (11 Jul 2025).

Important inherited characteristics:

- SNES S-CPU (65C816) is a highly optimized MIPS assembly interpreter driven by opcode tables.
- SPC700/APU already uses block JIT/recompilation to generated MIPS code.
- PPU state/event work runs on the R4300 while frame rendering is delegated to custom RSP code.
- RSP rendering and R4300-side emulation overlap, with explicit synchronization around frame completion.
- DSP/audio, DMA, memory, input, menu and related subsystems are predominantly assembly.
- DSP-1 is the only explicit enhancement-chip implementation currently present (`src/xcop_dsp1.S`).
- Existing compromises include configurable frame skipping, frame precision, APU underclocking and timing approximations.

## Primary architectural hypothesis

The leading major optimization hypothesis remains a reusable **65C816 -> R4300 MIPS dynarec** because it could:

1. materially reduce normal S-CPU cost;
2. recover R4300 budget for fidelity and enhancement-chip work;
3. provide reusable translation machinery for SA-1 rather than interpreting a second faster 65C816-class CPU from scratch.

This remains a hypothesis, not doctrine. Phase 1 must establish the real budget distribution before Phase 2 commits to it.

For Super FX, the leading future direction remains a distinct GSU -> MIPS block translator with correct cache/ROM/RAM/timing integration. RSP/RDP assistance should be targeted only where measurements justify it.

## Validation philosophy

Use the cheapest reliable validation layer first:

1. deterministic host-side tests;
2. N64 cross-build/static artifacts;
3. automated N64-emulator execution for integration and controlled experiments;
4. milestone emulator compatibility/performance runs;
5. real Nintendo 64 hardware as final authority.

Do not treat an N64 emulator’s wall-clock speed as the real N64 performance result. Automated N64 emulators are useful for validating execution, profiler behavior, workload differentiation and correctness of tooling; real hardware is still required before performance claims become final.

## Integrated development history

### PR #1 — project foundation

Merged. Established branch/PR workflow, build validation, artifacts, metrics, validation policy and engineering PR template.

### PR #2 — baseline measurement map

Merged as `1cb72a06a9c5ce5e4abb5cdd5c10f01a92ebeffd`.

Defined what Phase 1 must measure before selecting an architecture.

### PR #4 — development-branch CI bootstrap

Merged as `58f2061cc22206c3b6fdf08845d7ea7b478f05d6`.

Allows branch pushes inside the fork to validate automatically while keeping rolling releases restricted to `master`.

### PR #3 — statistical R4300 profiler

Merged as `6e002dc1e3387916013b994f3a62a0620b73aef8`.

Implemented:

- compile-time `PROFILE=1` mode with no profiler runtime behavior in normal builds;
- periodic CP0 Count/Compare IP7 sampling;
- EPC capture into a 4,096-entry ring buffer;
- host-side wrapped-buffer reconstruction and ELF symbolication;
- endian handling for both canonical layout and Mupen `dumpmem` word swapping;
- deterministic decoder tests;
- original synthetic SNES smoke ROM in CI;
- Mupen64Plus + RSP-CXD4 LLE runtime extraction.

Important result: an earlier Mupen capture reached 4,769 total samples and proved timer, wraparound, extraction and symbolication. Its retained samples were 100% `rsp_wait`, but Mupen also produced PIF/RSP incompatibility errors; therefore this distribution is not accepted as a real Sodium64 bottleneck result.

### PR #5 — ares statistical profiler validation

Merged into `master` as squash commit `c0334377f8c473e3b8168649eaf08d26e68bf19d`.

Key work:

- pinned ares N64 build in CI;
- minimal custom GDB RSP client;
- correct ares initial `+` handshake;
- guest MIPS exception pass-through via `QPassSignals` so normal N64 TLB handling does not stop profiling;
- direct RDRAM capture of profiler state;
- ares gate added without replacing normal build/Mupen validation.

The first valid short ares profile produced only eight samples but, unlike Mupen, observed real S-CPU/APU work rather than 100% `rsp_wait`. This validated ares as a better decision-lab candidate while explicitly **not** making an eight-sample bottleneck claim.

### PR #7 — define the Road to 1.0

Merged into `master` as squash commit `7fc7e21f9f674466680d0db73e16cf29dbb5878a`.

Added `docs/ROAD_TO_1_0.md` and linked it from README/ROADMAP.

Important decisions now frozen as project contract unless explicitly revised:

- Road to 1.0 = destination; ROADMAP = route; continuity = current position.
- “60 FPS” does not count if achieved through frameskip, APU underclock, omitted work or similar cheats.
- Super FX / Super FX 2 and SA-1 remain mandatory major targets of the Perfect target.
- N64 hardware ceilings must be demonstrated quantitatively before scope is weakened or cartridge assistance becomes the architectural answer.
- 1.0 is gated cumulatively rather than declared from one showcase game.

## Active work — PR #6

Branch: `phase1/workload-bottleneck-map`

PR: **#6 — Phase 1: build deterministic workload bottleneck map**

Purpose: turn the profiler from an integration smoke tool into evidence capable of deciding the first real optimization architecture.

Current branch includes:

- deterministic original SNES workloads: `idle`, `cpu-alu`, `wram`, `ppu-registers`, `dma-vram`;
- host tests for workload generation/checksum/vectors;
- symbol/subsystem classification using the exact Sodium64 linker map rather than fragile hand-maintained function lists;
- ares interpreter control run plus N64 recompiler runs;
- profile JSON and matrix generation;
- warm-up before measured intervals;
- host-side runtime patching to profile the APU at the full 21 master-cycle rate;
- explicit APU JIT invalidation before measurement so old underclock timing is not retained in already-compiled blocks;
- adaptive measured windows that can continue until a minimum useful sample count is reached.

### Evidence from the first PR #6 matrix attempt

The stable Build and Validate path remained green. The failure occurred only in the new experimental ares matrix.

Useful results before the failure:

- interpreter `idle`: **20 samples / 3 measured seconds**;
- recompiler `idle`: **2,116 samples / 3 measured seconds** — roughly 106x the profiling density of ForceInterpreter;
- recompiler `cpu-alu`: **1,565 samples**, with **1,165 / 1,565 = 74.4%** classified as S-CPU code;
- symbols in CPU-ALU included expected CPU operations such as `cpu_execute`, `set_nz16`, `cpu_bne`, `cpu_rol16`, `cpu_dex16`, etc.; this validates that the workload/classifier reacts logically to deliberately CPU-heavy guest code;
- `wram` produced only **12 samples** in the original three-second window, too few to interpret safely;
- `ppu-registers` completed warm-up and patches but timed out waiting for the Ctrl-C stop response; ares logs showed blocking graphics/RDP compilation activity, including a compile taking close to 0.9 wall-clock seconds.

Rejected interpretations:

- do **not** conclude that WRAM is cheap or expensive from 12 samples;
- do **not** conclude that S-CPU is the general-game bottleneck from the 74.4% CPU-ALU result, because that ROM is intentionally constructed to stress the CPU;
- do **not** treat the PPU timeout as a Sodium64 crash; evidence points to ares/debugger responsiveness during heavy graphics compilation.

### PR #6 fix currently under validation

Current active head: `4afd08c663eb6880241e39fff73f71081485917b`.

The latest batch changed the profiler harness so that:

- Ctrl-C stop response can wait much longer than the previous 10-second socket timeout;
- recompiler workloads may run repeated measured windows until at least **200 samples** are captured, with a bounded maximum total measurement time;
- APU is changed to `apu_clock = 21` only after warm-up;
- APU `jit_lookup` is cleared and `jit_pointer` reset to `JIT_BUFFER` before the measured window, matching the semantic need to recompile blocks at the new full-rate timing;
- the profiler ring is then reset, so JIT invalidation/preparation overhead is excluded from the measurement itself.

At the latest checkpoint:

- host profiling tests on the new PR #6 head passed;
- the PROFILE build passed;
- the normal Build and Validate jobs were running/green through their early build stages;
- the ares job had entered its dependency/build stage; the final second matrix result had **not yet been observed**.

## Current phase

**M0 / ROADMAP Phase 1 — baseline and bottleneck map.**

The statistical profiler and automated extraction environment are now infrastructure. The active task is to produce a decision-grade workload matrix that separates the major classes of cost before selecting a large optimization architecture.

Phase 1 still needs evidence on:

- S-CPU execution;
- memory/address translation/cache-sensitive paths;
- APU/SPC700 and its JIT;
- DSP/audio;
- PPU event/section preparation;
- DMA/HDMA;
- RSP rendering and R4300 wait time;
- frame queue pressure/native-frame deadline behavior.

Synthetic workloads are controls that establish causality and profiler sensitivity. They are **not** a replacement for later representative gameplay profiles and real-N64 performance validation.

## Immediate next actions

1. Observe the current PR #6 CI run at head `4afd08c...` without changing variables while it runs.
2. If the adaptive/full-rate matrix succeeds, inspect every workload’s sample count and subsystem distribution before accepting the matrix.
3. If a workload still fails or has inadequate density, fix that specific measurement failure rather than relaxing the gate to accept weak evidence.
4. Once the synthetic matrix is trustworthy, add/choose representative gameplay-oriented workloads or milestone ROMs sufficient to answer whether the S-CPU dynarec should enter Phase 2.
5. Complete Phase 1’s frame-budget map under no-frameskip/full-rate-audio conditions.
6. Only then decide whether to open the 65C816 dynarec proof-of-concept branch or redirect to a different measured bottleneck.
7. Checkpoint `continuity` before beginning the first large optimization architecture batch.

## Hardware-test policy for Iron

Do not ask Iron to copy a build to real N64 after every change. Request a hardware session only when one milestone package can answer several concrete questions at once or emulator/host testing cannot resolve a hardware-specific uncertainty.

A hardware request must specify:

- exact build/artifact;
- ROMs/tests;
- settings;
- observations/metrics needed;
- decision that the answers unlock;
- why a lower validation layer cannot answer it reliably.

## Guardrails

- Do not create game-specific manual modes as a route to compatibility.
- Do not count frameskip, audio underclock, frame generation or omitted work as progress toward full speed.
- Do not endlessly produce tiny numbered builds with no hypothesis or measurable result.
- Do not let instrumentation become a second emulator/project.
- Do not merge risky low-level experiments merely because they compile.
- Do not send PRs to `Hydr8gon/sodium64` without Iron's explicit request.
- Prefer measurable architectural wins over accumulating hacks.
- Keep `master` as the best-known stable integrated state.
- Keep this branch as the freshest handoff.
- Preserve useful engineering rationale in repository docs; future sessions should not have to reconstruct decisions from chat.

## Resume protocol for a future chat

Read in this order:

1. `continuity:docs/CONTINUITY.md` — current handoff/state.
2. `master:docs/ROAD_TO_1_0.md` — immutable-ish destination and release gates.
3. `master:docs/ROADMAP.md` — current technical route.
4. `master:docs/VALIDATION.md` — testing/merge policy.
5. `master:docs/BASELINE.md` — Phase 1 measurement model.
6. Active PR #6 description/diff and CI results.

If these disagree, prefer the most recent concrete repository/PR state, then update this file to remove the inconsistency.
