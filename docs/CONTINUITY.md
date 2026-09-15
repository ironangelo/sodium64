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

## Current phase

**Phase 1 — baseline and bottleneck map.**

The next runtime work is low-overhead instrumentation. Do not begin the 65C816 dynarec proof of concept until the current frame budget has been measured well enough to rank the main costs.

Phase 1 should quantify at least:

- S-CPU execution cost;
- APU/SPC700 work;
- DSP/audio work;
- PPU events/HDMA/section preparation;
- RSP rendering time and R4300 wait time;
- memory/cache/TLB-sensitive paths where practical;
- frame queue pressure / missed native-frame deadlines.

Instrumentation must be low-overhead, attributable, and removable/disableable so the profiler does not become the bottleneck being measured.

## Immediate next steps

1. Inspect the source for existing R4300 CP0 Count/timing instrumentation or reusable counters.
2. Design the smallest useful per-frame profiler, preferably based on CP0 Count deltas and aggregated counters rather than logging.
3. Create a new Phase 1 instrumentation branch/PR from current `master`.
4. Compile and validate it through CI before any emulator or hardware run.
5. Add automated N64-emulator execution only when it can produce deterministic telemetry that host/static validation cannot.
6. Request a real N64 session only when a milestone build can answer several unresolved timing/performance questions at once.

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

## Resume protocol for a future chat

Read these in order:

1. `continuity:docs/CONTINUITY.md` — canonical current handoff/state.
2. `master:docs/ROADMAP.md` — long-term phase plan.
3. `master:docs/VALIDATION.md` — testing and merge policy.
4. `master:docs/BASELINE.md` — Phase 1 measurement model.
5. Active PR description/diff and CI results.

If those sources disagree, prefer the most recent concrete repository/PR state, then update this continuity file to remove the inconsistency.
