# Sodium64 fork roadmap

## North star

Push Sodium64 toward a high-fidelity, full-speed SNES implementation on real Nintendo 64 hardware, while progressively adding enhancement-chip support. The stretch targets include Super FX / Super FX 2 and SA-1 at real gameplay speed without relying on frame skipping or audio underclocking.

This fork starts from Hydr8gon's upstream architecture rather than replacing it. The existing MIPS assembly core, APU JIT, and RSP renderer are assets to build on.

## Engineering rules

- Measure before and after major performance work.
- Keep `master` stable; risky ideas live on branches and PRs.
- Prefer architectural wins over endless micro-build iteration.
- Preserve fidelity by default. A speedup created by removing required emulation work is not a win.
- Use deterministic host-side validation wherever hardware is not required.
- Real N64 testing is a milestone gate, not a per-commit ritual.
- Enhancement chips should be integrated as first-class timed devices, not game-specific modes.

## Phase 0 — project foundation

Goal: make experimentation safe and measurable.

- Run build validation on pull requests.
- Preserve ROM, ELF, linker maps, build logs, and build metrics as CI artifacts.
- Establish layered validation and hardware-test policy.
- Establish a PR format that records performance/fidelity impact and rollback.

Exit condition: a PR can be evaluated and built automatically without changing `master` or requiring a console test.

## Phase 1 — baseline and bottleneck map

Goal: understand where native-frame budget is actually spent before rewriting the CPU core.

- Add low-overhead timing/counter instrumentation suitable for emulator and hardware builds.
- Measure CPU emulation, APU/DSP work, PPU event work, RSP wait time, memory paths, and frame queue pressure.
- Record representative baseline behavior with no frame skip and full APU clock where possible.
- Identify cache/code-layout constraints, especially RSP IMEM/DMEM and R4300 I-cache pressure.

Exit condition: we can rank the major costs and quantify headroom rather than infer it from FPS alone.

## Phase 2 — 65C816 dynarec proof of concept

Goal: determine whether translating SNES CPU basic blocks to native R4300 code can materially lower S-CPU cost while preserving semantics and timing.

- Build a host-testable 65C816 block representation and translator model.
- Cover a deliberately small instruction/addressing subset first.
- Differentially test translated execution against a trusted/reference path over randomized machine states.
- Define invalidation rules for self-modifying code and mapped memory.
- Generate MIPS suitable for the existing Sodium64 runtime rather than introducing a portable abstraction layer into hot code.

Exit condition: representative translated blocks are correct and demonstrate enough projected/observed savings to justify integration.

If the result is weak, close the experiment and redirect effort based on Phase 1 measurements rather than forcing the architecture.

## Phase 3 — 65C816 dynarec integration

Goal: move useful S-CPU execution from interpretation to translated blocks without sacrificing compatibility.

- Integrate block lookup, compilation, invalidation, event exits, interrupts, and mode changes.
- Keep a fallback path during bring-up for differential validation.
- Optimize hot addressing/memory paths and code layout only after correctness is established.
- Re-run compatibility and timing corpus continuously.

Exit condition: normal SNES games show a meaningful native-frame budget improvement with equal or better correctness.

## Phase 4 — base-system fidelity recovery

Goal: spend part of recovered CPU budget on removing existing speed-oriented compromises.

- Full-rate APU as the default target.
- Improve timing approximations that are currently known hacks when tests can support them.
- Expand PPU edge-case coverage and audio fidelity without losing native-frame target.
- Add deterministic regression cases for every corrected behavior.

Exit condition: the base SNES platform is both faster and more accurate than the starting fork.

## Phase 5 — enhancement-chip framework and lower-cost chips

Goal: make coprocessors a reusable architectural concept before tackling the hardest ones.

- Formalize cartridge-device dispatch, timing, memory ownership, IRQ/DMA interaction, and save-state/runtime state boundaries as needed by Sodium64.
- Complete/harden DSP-1 support.
- Add suitable lower-cost enhancement devices before Super FX/SA-1 where they provide useful architectural validation.

Exit condition: adding a coprocessor no longer requires ad-hoc changes throughout unrelated core paths.

## Phase 6 — Super FX / Super FX 2

Goal: run representative GSU software at native gameplay speed.

Primary path to investigate: block translation of GSU instructions to R4300 MIPS, with careful modeling of cache, ROM/RAM access, and synchronization with the S-CPU/PPU. RSP assistance may be used for narrowly defined data-parallel work if measurements show it is beneficial; the RSP is not assumed to be a drop-in replacement for the GSU.

Exit condition: representative Super FX titles are correct enough for extended play and sustain the native-frame target in measured gameplay workloads, or the project has quantified the remaining hardware-budget gap.

## Phase 7 — SA-1

Goal: exploit the shared 65C816 work instead of interpreting a second fast CPU from scratch.

- Reuse the mature 65C816 translation machinery with a separate SA-1 execution context and memory/timing model.
- Implement SA-1-specific DMA, arithmetic, bit operations, BW-RAM behavior, IRQs, and character conversion.
- Investigate targeted RSP acceleration only for operations that benchmark as worthwhile.

Exit condition: representative SA-1 titles become playable with a measured path toward, or achievement of, native-frame speed.

## Phase 8 — compatibility and polish

Goal: turn architectural success into an emulator that is pleasant to use.

- Broaden enhancement-chip coverage.
- Expand regression corpus across regions, timing-sensitive games, audio edge cases, and PPU effects.
- Improve diagnostics, ROM detection, settings defaults, and user-facing compatibility documentation.
- Revisit remaining accuracy/performance compromises with the benefit of the new architecture.

## What this roadmap deliberately does not promise

It does not assume beforehand that every commercial SNES title and every enhancement chip can be made cycle-perfect at 60/50 Hz on an unmodified Nintendo 64. The project keeps that ambition as a direction, but each hard architectural claim must survive measurement on real hardware.
