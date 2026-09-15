# Sodium64 fork continuity

This branch is the canonical handoff point for continuing the project across ChatGPT conversations, development sessions, and long gaps between milestones.

## Branch role

- Canonical continuity branch: `continuity`
- Stable integration branch: `master`
- Active development happens in feature/phase branches and pull requests targeting `master`.
- The `continuity` branch is **not** a feature branch and should not be merged into `master` as part of normal development.
- Update this file whenever the active phase, active PR, major hypothesis, important result, validation state, or immediate next action changes materially.

## Project ownership and working model

- Repository: `ironangelo/sodium64`
- Upstream parent: `Hydr8gon/sodium64`
- Iron is the project owner and sets the north star.
- The assistant acts as technical lead/captain: architecture, implementation strategy, profiling, validation, Git workflow, and deciding when real-hardware testing is worth requesting.
- Development PRs stay entirely inside `ironangelo/sodium64`. Do not open PRs against `Hydr8gon/sodium64` unless Iron explicitly asks for it.
- Real Nintendo 64 testing should be rare milestone validation, not part of every iteration.
- Preferred working cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**. Each checkpoint should record the useful engineering rationale, evidence, discarded interpretations, risks, and next action rather than relying on chat history or hidden reasoning.

## North star

Push Sodium64 toward a high-fidelity, full-speed SNES implementation on real Nintendo 64 hardware, with progressively broader enhancement-chip support.

Long-term stretch targets include:

- one emulated SNES frame per native display frame where the original game runs at that cadence;
- full-speed audio without deliberate APU underclocking;
- high visual/timing fidelity;
- Super FX / Super FX 2 support at real gameplay speed;
- SA-1 support using architecture that has a credible path to real gameplay speed;
- broader special-chip compatibility over time.

Do not redefine success as frame skipping, deliberately omitted rendering work, game-specific modes, or knowingly broken timing merely to increase an FPS counter.

## Starting architecture observed in upstream

The fork began cleanly from upstream commit `a4c75d3819691f5fdb6de49712090c643f17abea` (11 Jul 2025).

Important inherited characteristics:

- SNES S-CPU (65C816) is a highly optimized MIPS assembly interpreter driven by opcode tables.
- SPC700/APU already uses block JIT/recompilation to generated MIPS code.
- PPU state/event work runs on the R4300 while frame rendering is delegated to RSP code.
- RSP rendering and CPU-side emulation overlap, with explicit synchronization around frame completion.
- DSP/audio, DMA, memory, input, menu, and related subsystems are predominantly assembly.
- DSP-1 is the only explicit enhancement-chip implementation currently present (`src/xcop_dsp1.S`).
- Existing speed/accuracy compromises include optional frame skipping, configurable frame precision, APU underclocking, and known timing approximations.

## Primary architectural hypothesis

The highest-value hypothesis to test is a reusable **65C816 -> R4300 MIPS dynarec**.

Why it matters:

1. It may materially reduce the cost of the normal SNES S-CPU.
2. The freed R4300 budget can be spent on fidelity and enhancement chips.
3. Mature 65C816 translation machinery could later be reused for SA-1, which contains another 65C816-class CPU, rather than interpreting a second faster CPU from scratch.

This remains a hypothesis, not doctrine. Phase 1 profiling must establish where the current frame budget actually goes before committing the project to a large rewrite.

For Super FX, the leading future direction is a separate GSU -> MIPS block translator with accurate cache/ROM/RAM/timing integration. RSP/RDP assistance may be considered for narrowly measured workloads, not assumed as a drop-in replacement for the cartridge processor.

## Validation philosophy

Use the cheapest reliable validation layer first:

1. deterministic host-side tests;
2. N64 cross-build / static artifacts;
3. automated N64-emulator execution where hardware-specific behavior matters;
4. milestone emulator compatibility/performance runs;
5. real Nintendo 64 hardware as final authority for hardware-specific timing and performance.

The repository contains `docs/VALIDATION.md` on `master` with the full policy.

When adding a translator/JIT path, keep or create a trusted reference path long enough to support differential testing over machine state, registers, flags, memory, cycle accounting, branches, interrupts, and invalidation behavior.

## Development history

### PR #1 — Phase 0: establish measurable PR workflow

Status: **merged** into `master`.

Purpose:

- establish branch/PR development in the fork;
- add pull-request build validation;
- preserve ROM, ELF, linker maps, build log, and lightweight metrics as CI artifacts;
- keep rolling releases limited to successful `master` pushes;
- establish roadmap and validation docs;
- replace the upstream "PRs are not accepted" template with our own engineering template.

PR #1 was a bootstrap because GitHub Actions were still disabled for the newly created public fork.

### GitHub Actions activation

On 15 Sep 2026 Iron manually enabled GitHub Actions for the fork.

### PR #2 — Phase 1: record baseline measurement map

Status: **merged** into `master` as squash commit `1cb72a06a9c5ce5e4abb5cdd5c10f01a92ebeffd`.

Validation result:

- `Build and Validate` completed successfully on PR head `07cd9bda5be0684cab09715ed62af6c825d73ef6`.
- Compile, build metrics, and artifact upload all succeeded.
- The PR produced the expected `sodium64-build` artifact (ROM, ELF/maps/log/metrics bundle).
- The release job correctly skipped on the pull-request event.
- No real N64 hardware validation was required because runtime code was unchanged.

Purpose/results:

- `master:docs/BASELINE.md` now defines what Phase 1 must measure before architectural changes;
- the README points releases to `ironangelo/sodium64` rather than upstream;
- the README points future project handoffs to this dedicated `continuity` branch;
- normal PR validation is now proven operational.

### PR #4 — CI: validate development branch pushes

Status: **merged** into `master` as commit `58f2061cc22206c3b6fdf08845d7ea7b478f05d6`.

Purpose/result:

- `Build and Validate` now runs on pushes to development branches inside the fork, except `continuity`;
- this avoids workflow bootstrap deadlocks when a feature PR changes its own validation workflow;
- rolling releases remain restricted to `master`;
- runtime behavior is untouched.

### PR #3 — Phase 1: low-overhead statistical R4300 profiler

Status: **merged** into `master` as squash commit `6e002dc1e3387916013b994f3a62a0620b73aef8`.

What was implemented:

- compile-time opt-in profiling through `PROFILE=1`; normal builds do not enable profiler runtime behavior;
- periodic R4300 sampling driven by CP0 Count/Compare and IP7 timer interrupts;
- CP0 EPC captured into a 4,096-entry ring buffer;
- exception-time implementation intentionally restricted to `k0`/`k1` before `eret` to avoid clobbering interrupted emulator/JIT state;
- raw EPCs are kept for host-side symbolication against the exact matching ELF rather than hard-coding subsystem categories;
- separate `sodium64-profile-build` CI artifact;
- `scripts/profile_report.py` reconstructs wrapped ring buffers and symbolicates samples;
- decoder automatically accepts the natural big-endian layout and Mupen64Plus `dumpmem`'s observed per-word byte-swapped layout;
- deterministic host tests cover endian handling and ring-buffer reconstruction;
- an original synthetic 32 KiB SNES LoROM is generated in CI, so automated smoke testing requires no commercial game ROM.

Validation result:

- final PR head `e0a66f18dad18124e9c3b61ee2e3b20ab5d9140f` passed the complete `Build and Validate` workflow;
- host decoder tests passed;
- normal Sodium64 build passed and produced metrics/artifact;
- `PROFILE=1` build passed and produced metrics/artifact;
- pinned Mupen64Plus debugger + RSP-CXD4 LLE built successfully in CI;
- the normal synthetic-SNES Sodium64 ROM executed headlessly;
- the profiling build executed, was paused through the debugger, and its profiler RDRAM region was dumped successfully;
- the dumped snapshot decoded successfully against the matching profiling ELF.

Important observed evidence:

- an earlier successful runtime capture accumulated **4,769 total samples** in roughly three seconds;
- because capacity is 4,096, that capture proved the ring buffer wrapped and reconstruction still recovered the latest 4,096 valid EPC samples;
- all 4,096 retained samples from that synthetic/Mupen run symbolicated to `rsp_wait`.

Interpretation and limitation:

- the `rsp_wait` result is **not** accepted as the real Sodium64 gameplay bottleneck;
- Mupen64Plus emitted repeated `Unknown SI DMA PIF address: 000007c0` errors and `RSP Error: unknown task type: 0x00080010` during this smoke environment;
- therefore Mupen is currently trusted as a runtime/sampler integration gate, not yet as a decision-grade performance model for Sodium64;
- what PR #3 does prove is that the sampling mechanism, CP0 timer path, ring buffer, wraparound, RDRAM extraction, endian normalization, and symbolication pipeline all work end-to-end.

## Current phase

**Phase 1 — baseline and bottleneck map.**

Low-overhead runtime instrumentation now exists and is merged. The remaining Phase 1 job is to obtain a **representative, decision-grade workload profile** before selecting the first major optimization architecture.

Do not begin the 65C816 dynarec proof of concept merely because it remains the leading architectural hypothesis. First establish whether S-CPU execution is actually a dominant R4300 cost under representative gameplay and how much time is instead spent in APU/DSP/PPU/event work or waiting for RSP rendering.

Phase 1 should still quantify at least:

- S-CPU execution cost;
- APU/SPC700 work;
- DSP/audio work;
- PPU events/HDMA/section preparation;
- RSP rendering time and R4300 wait time;
- memory/cache/TLB-sensitive paths where practical;
- frame queue pressure / missed native-frame deadlines.

## Current engineering reasoning

- Statistical EPC sampling was chosen over per-opcode or per-JIT-block timing hooks because the latter would heavily perturb the very hot paths being measured.
- The profiler is intentionally a separate build mode so release performance/fidelity stays untouched.
- Automated emulator execution is valuable for proving integration, extraction, and tooling, but a profiler is only as useful as the workload and machine model feeding it.
- The present synthetic SNES ROM is excellent for deterministic CI smoke testing but deliberately poor as a gameplay-performance workload.
- Because Mupen currently reports Sodium64-specific PIF/RSP incompatibilities, its `rsp_wait` distribution must not drive optimization priorities.
- The next batch should therefore improve the **quality of the measurement environment/workload**, not prematurely optimize the first function that appeared hot in a compromised smoke run.

## Immediate next batch

1. Audit available N64 emulators and test modes for better compatibility with Sodium64's custom RSP microcode, prioritizing deterministic/headless automation and memory extraction where possible.
2. In parallel, inspect Sodium64's own runtime boundaries to identify a minimal set of coarse counters/markers that can complement EPC sampling without high observer overhead, especially RSP submit/wait and per-frame deadline information.
3. Build a more representative original SNES workload ROM that exercises S-CPU, PPU/event processing and APU deterministically without commercial game data, so CI can distinguish a trivial idle/wait loop from actual emulator work.
4. Only if emulator limitations still prevent trustworthy profiling, prepare one milestone `PROFILE=1` hardware package that can answer several Phase 1 questions in a single real-N64 session.
5. After that batch, update `continuity` before opening the first optimization architecture PR.

## Hardware-test policy for Iron

Do not ask Iron to copy a build to real N64 after every change. Request a hardware session only when a milestone build can answer several concrete questions at once or when emulator/host testing cannot resolve a hardware-specific uncertainty.

A hardware request should say exactly:

- which build/artifact to use;
- which ROMs/tests to run;
- which settings to use;
- what observations/metrics are needed;
- why those answers cannot be obtained reliably at a lower validation layer.

## Important guardrails

- Do not create game-specific manual modes as a route to compatibility.
- Do not count frameskip or audio underclock as progress toward full speed.
- Do not endlessly produce tiny numbered builds with no architectural hypothesis or measurable result.
- Do not merge risky low-level experiments merely because they compile.
- Do not send PRs to `Hydr8gon/sodium64` without Iron's explicit request.
- Prefer measurable architecture changes over accumulating hacks.
- Keep `master` as the best-known stable state.
- Keep this `continuity` branch as the freshest project handoff, even when active work has not yet merged to `master`.
- Preserve engineering rationale in repository docs at each checkpoint; do not make future sessions reconstruct key decisions from chat alone.

## Resume protocol for a future chat

Read these in order:

1. `continuity:docs/CONTINUITY.md` — canonical current handoff/state.
2. `master:docs/ROADMAP.md` — long-term phase plan.
3. `master:docs/VALIDATION.md` — testing and merge policy.
4. `master:docs/BASELINE.md` — Phase 1 measurement model.
5. Active PR description/diff and CI results.

If those sources disagree, prefer the most recent concrete repository/PR state, then update this continuity file to remove the inconsistency.
