# Sodium64 fork roadmap

## Relationship to the Road to 1.0

[`ROAD_TO_1_0.md`](ROAD_TO_1_0.md) defines the stable destination and release gates. This roadmap defines the current engineering route toward those gates.

The route may change when profiling, experiments, compatibility work, or real-hardware evidence show a better path. A roadmap change should not silently weaken the 1.0 target; if the destination itself ever needs revision, that decision belongs in `ROAD_TO_1_0.md` and should be justified explicitly.

## North star

Push Sodium64 toward a high-fidelity, full-speed SNES implementation on real Nintendo 64 hardware, while progressively adding enhancement-chip support. The target includes Super FX / Super FX 2 and SA-1 at real gameplay speed without relying on frame skipping, frame generation, audio underclocking, or omitted emulation work.

This fork starts from Hydr8gon's upstream architecture rather than replacing it. The existing MIPS assembly core, APU JIT, and RSP renderer are assets to build on.

## Engineering rules

- Measure before and after major performance work.
- Keep `master` as the best-known integrated state; risky ideas live on branches and PRs.
- Prefer architectural wins over endless micro-build iteration.
- Preserve fidelity by default. A speedup created by removing required emulation work or worsening required timing is not a win.
- Use deterministic host-side validation wherever hardware is not required.
- Treat ares/Mupen as laboratories, not real-N64 performance authority.
- Real N64 testing is a milestone gate, not a per-commit ritual.
- Enhancement chips should be integrated as first-class timed devices, not game-specific modes.
- A rejected explanation or architecture is retained as knowledge so it is not rediscovered repeatedly.

## Phase 0 — project foundation — ACHIEVED

Goal: make experimentation safe and measurable.

- Build validation runs automatically.
- ROM, ELF, linker maps, build logs and metrics are preserved as CI artifacts.
- Layered validation and hardware-test policy are documented.
- Profiling and deterministic harnesses can be enabled without changing normal release behavior.

Exit condition: achieved. Experimental work can be built, profiled and rejected without destabilizing `master`.

## Phase 1 — M0 representative baseline and bottleneck map — ACHIEVED

Goal: determine where representative native-frame budget is actually spent before committing to a major rewrite.

Completed evidence chain:

- statistical R4300 sampling separates S-CPU, APU/JIT, DSP/audio, PPU/events, DMA/HDMA, synchronization and VI wait;
- synthetic controls establish causal behavior but are not used as commercial-game proxies;
- pinned ares RSP JIT was isolated as a **LAB LIMITATION**; the valid high-density lab is R4300 JIT + RSP interpreter;
- Gothicvania survivability provides an open representative workload with deterministic progression;
- real N64 M0 capture ran frameskip `0`, APU clock `21`, audio `4`, precision `8`, with active gameplay throughout measurement.

Real-N64 M0 result: **48/60, 49/60, 48/60, 50/60, 50/60**, mean **49.0/60**, 3,581 samples, essentially no VI idle headroom. Sample split: **APU/audio 61.83%**, S-CPU **22.12%**, PPU/events **7.99%**, DMA/HDMA **6.67%**, RSP/VRAM wait **1.31%**.

Exit condition: achieved. The first M1 gate driver is APU/audio, not an assumed 65C816 dynarec.

## Phase 2 — M1 APU/audio-first base-core optimization — ACTIVE

Goal: recover enough representative frame budget from the measured APU/audio path to move the base system toward native cadence **without worsening SPC700/DSP timing or audio correctness**.

Current order of attack:

1. reduce hot `apu_read8` / `apu_write8` and related APU memory/dispatch overhead while preserving scheduler return frequency;
2. re-profile the exact Gothicvania workload after each bounded source-level change;
3. inspect DSP/audio inner loops only where samples continue to justify it;
4. graduate promising candidates to real-N64 milestone validation rather than treating emulator wall-clock as FPS.

Important rejected path: increasing APU JIT `BLOCK_SIZE` from 16 to 32 bytes reproducibly improved the ares frame budget **44->48/60**, proving block/dispatch overhead matters, but paired timing instrumentation showed a material DSP interleave regression. BLOCK16 measured avg lateness **119.073**, max **651**, `>=672` **0/35,982**; BLOCK32 measured avg **128.338**, max **1,218**, `>=672` **377/35,965 (1.048%)**. **BLOCK_SIZE32 is REJECTED.** Keep 16-byte blocks unless a future design reduces dispatch cost without lengthening required scheduling intervals.

Exit condition: a measured APU/audio optimization materially lowers representative host cost, survives timing/semantic checks, and improves the real-N64 base-system budget without fidelity loss.

## Phase 3 — broader base-core optimization, evidence-driven

Goal: attack the next gate driver after Phase 2 re-profiling rather than assuming which subsystem must be rewritten.

Possible paths include:

- further APU/DSP work if it remains dominant;
- S-CPU interpreter fast paths or a 65C816-to-MIPS dynarec if S-CPU becomes a material gate driver;
- memory/cache/code-layout work if profiling identifies it;
- PPU/DMA/RSP synchronization work where representative evidence points there.

### Conditional 65C816 dynarec proof

A 65C816 dynarec remains strategically attractive because the same mature translation infrastructure could later help SA-1. It is **not currently the first M1 architecture**.

If re-profiling justifies a dynarec:

- build a host-testable 65C816 block representation and translator model;
- cover a deliberately small instruction/addressing subset first;
- differentially test translated execution against a trusted/reference path;
- define invalidation, event-exit, interrupt and mode-change rules;
- generate MIPS suitable for Sodium64's existing runtime rather than building a second portable emulator around it;
- integrate only if representative savings justify the complexity.

Exit condition: the next measured bottleneck is reduced materially with equal or better correctness. A dynarec is integrated only if it earns that role with evidence.

## Phase 4 — base-system native-frame and fidelity convergence

Goal: convert isolated performance wins into a base SNES implementation that sustains correct native temporal cadence across a representative corpus.

- frameskip remains `0` for target measurements;
- APU/SPC700 remains full-rate;
- audio synchronization and DSP timing remain correct enough for the validation corpus;
- remove inherited timing/accuracy compromises as recovered budget allows;
- expand PPU, DMA/HDMA, interrupt, memory and audio regression coverage;
- validate meaningful milestones on real N64 hardware.

Exit condition: representative ordinary SNES titles meet the native-frame target with no major visual/audio/gameplay regression and no manual per-game execution modes.

## Phase 5 — enhancement-chip framework and lower-cost chips

Goal: make coprocessors a reusable architectural concept before tackling the hardest ones.

- Formalize cartridge-device dispatch, timing, memory ownership, IRQ/DMA interaction, and runtime state boundaries as needed by Sodium64.
- Complete/harden DSP-1 family support.
- Add suitable lower-cost enhancement devices where they validate the architecture.

Exit condition: adding a coprocessor no longer requires ad-hoc changes throughout unrelated core paths.

## Phase 6 — Super FX / Super FX 2

Goal: run representative GSU software at native gameplay speed.

Primary path to investigate: treat Super FX as a timed GSU cartridge device and evaluate block translation of GSU instructions to R4300 MIPS, with careful modeling of cache, ROM/RAM access and synchronization with S-CPU/PPU. RSP assistance may be used for narrowly defined data-parallel work only if measurements show it helps; the RSP is not assumed to be a drop-in GSU replacement.

Exit condition: representative Super FX titles are correct enough for extended play and sustain the native-frame target in measured gameplay workloads, or the project has quantitatively demonstrated the remaining N64-alone budget gap.

## Phase 7 — SA-1

Goal: reuse proven base-core machinery where it genuinely applies instead of interpreting a second fast 65C816 blindly.

- Reuse mature 65C816 translation/fast-path infrastructure if Phase 3 established it; otherwise build only the machinery SA-1 evidence requires.
- Maintain a separate SA-1 execution context and memory/timing model.
- Implement SA-1-specific DMA, arithmetic, bit operations, BW-RAM behavior, IRQs and character conversion.
- Investigate targeted RSP acceleration only for operations that benchmark as worthwhile.

Exit condition: representative SA-1 titles become correct and stable with a measured path toward, or achievement of, native-frame speed.

## Phase 8 — compatibility and polish

Goal: turn architectural success into an emulator that is pleasant and dependable to use.

- Broaden enhancement-chip coverage.
- Expand regression corpus across regions, timing-sensitive games, audio edge cases and PPU effects.
- Improve diagnostics, ROM detection, settings defaults and user-facing compatibility documentation.
- Revisit remaining accuracy/performance compromises with the benefit of the mature architecture.
- Complete representative real-hardware regression before 1.0.

## Current immediate batch

The active safe M1 tree uses **`BLOCK_SIZE=16`**. The next bounded experiment is the APU memory/dispatch path, beginning with measured `apu_read8` / `apu_write8` overhead. One important variable should change at a time. A candidate that gains throughput but worsens timing is rejected, as the 32-byte-block experiment demonstrated.

The question for each batch remains: **does this move a Road-to-1.0 gate?** If a tool, profiler or architecture branch stops reducing a gate-relevant uncertainty, stop expanding it.

## What this roadmap deliberately does not promise

It does not assume beforehand that every commercial SNES title and every enhancement chip can be made cycle-perfect at 60/50 Hz on an unmodified Nintendo 64. The project keeps the full target as its destination, while every hard architectural claim must survive measurement and ultimately real-hardware validation.
