# Sodium64 fork continuity

This branch is the canonical handoff point for continuing the project across ChatGPT conversations, development sessions, crashes, context loss, and long gaps between milestones.

## Continuity operating rule

`continuity` is a **live engineering checkpoint**, not merely an end-of-phase summary.

Preferred cadence:

**technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**

A checkpoint must be written whenever any of these materially changes:

- active branch / PR / HEAD;
- measured result or bottleneck interpretation;
- a hypothesis is confirmed or rejected;
- a CI experiment is launched whose setup would be costly to reconstruct;
- the next action changes;
- a hardware-test request becomes necessary or unnecessary.

Do not rely on chat history, hidden reasoning, or remembering which experiment was running. If a chat window dies immediately after a checkpoint, another session should be able to continue from this file plus the referenced PR/CI artifacts without rediscovering the investigation.

## Project hierarchy

1. `master:docs/ROAD_TO_1_0.md` — destination / contract.
2. `master:docs/ROADMAP.md` — current technical route.
3. `continuity:docs/CONTINUITY.md` — current position and live investigation state.

A hard technical problem may change the route. It must not silently weaken the destination.

## Ownership and working model

- Repository: `ironangelo/sodium64`.
- Upstream: `Hydr8gon/sodium64`.
- Iron owns the project and sets the north star.
- The assistant acts as technical lead/captain: architecture, implementation strategy, profiling, validation, Git workflow, CI experiments, and deciding when real-N64 testing is worth requesting.
- Do not send PRs upstream unless Iron explicitly asks.
- Real Nintendo 64 testing is a milestone gate, not a per-commit ritual.

## Road-to-1.0 north star

The stable definition lives in `master:docs/ROAD_TO_1_0.md`.

The Perfect target remains Sodium64 on real N64 hardware with native temporal cadence, no required frameskip or frame generation, full-rate SPC700/APU and synchronized audio, high CPU/PPU/audio/DMA/HDMA/timing fidelity, broad compatibility, and first-class enhancement-chip support including Super FX / Super FX 2 and eventually SA-1.

N64-alone is the primary target. Cartridge-side acceleration may be considered only after a hardware-budget gap is demonstrated quantitatively. “Nobody has done it before” is not evidence of impossibility.

Current milestone position: **M0 / ROADMAP Phase 1 — baseline and bottleneck map**.

## Stable integrated foundation on `master`

Current stable master before the active PR:

- master SHA: `798ebcb9969d94eda3eba4592eae2792d6304cb5` (PR #8 merged).
- PR #1: project foundation / measurable PR workflow.
- PR #2: baseline measurement map.
- PR #3: optional statistical R4300 profiler.
- PR #4: development-branch validation.
- PR #5: pinned ares profiling path via GDB RSP.
- PR #6: deterministic isolated workload bottleneck map.
- PR #7: Road to 1.0 contract.
- PR #8: virtual-N64 frame-budget correlation using Sodium64's own `fps_display` / 60-VI signal.

Important inherited architecture:

- SNES S-CPU: optimized MIPS assembly 65C816 interpreter.
- SPC700/APU: existing block JIT to generated MIPS.
- CPU-side PPU/event preparation plus custom RSP rendering.
- DSP/audio, DMA, memory, input and menu are predominantly assembly.
- DSP-1 exists as the currently explicit enhancement-chip implementation.

The leading future optimization hypothesis remains a reusable 65C816 -> R4300 MIPS dynarec, but Phase 1 must finish representative evidence before M1 commits to that architecture.

## ACTIVE WORK — PR #9 gameplay-like workload

PR: `#9 Phase 1: add balanced gameplay-like profiling workload`

- branch: `phase1/gameplay-mixed-workload`
- base: `master` at `798ebcb9969d94eda3eba4592eae2792d6304cb5`
- current HEAD: `40f0f8616ed0bfbd7c28f38af5b72914a647ac27`
- PR remains **open, mergeable, not merged**.
- latest ares diagnostic workflow: run `35109280375`, **success**.
- latest diagnostic artifact: `sodium64-ares-profile-matrix`, artifact ID `10451624678`.

Do **not** merge PR #9 yet. The workload itself now looks valid, but the ares recompiler laboratory has exposed a recompiler-specific RSP/VRAM synchronization pathology that must be isolated before using its recompiler result as representative Phase 1 evidence.

### What `gameplay-balanced` now represents

The workload was cleaned so it is no longer accidentally pathological:

- original deterministic 32 KiB LoROM generated from source;
- `WAI` / NMI frame pacing;
- bounded CPU/WRAM game-like work;
- bounded OAM, VRAM and CGRAM updates per frame;
- BG1 + OBJ are actually enabled (`TM=$11`);
- exactly one intended visible sprite;
- all other 127 OAM entries are explicitly hidden/off-screen;
- no release-runtime Sodium64 core behavior is changed by the workload itself.

Host tests, normal build, `PROFILE=1`, Mupen smoke and ares workflow all remain green.

## Critical finding — recompiler-only gameplay collapse

The cleaned workload still collapses under the normal ares recompiler configuration, but **does not collapse when ares is forced to interpreter mode**.

### Recompiler result — failing laboratory path

Latest clean diagnostic (`recompiler-gameplay-balanced`):

- measured wall window: 6 s (host duration only; not N64 performance);
- statistical samples: **959**;
- `fps_display`: **1 / 60 VI**;
- partial `fps_native`: 20;
- partial `fps_emulate`: 0;
- `frame_count`: 0;
- frameskip setting: 0;
- APU clock: 21 (full-rate lab setting);
- audio enabled (`audio_set=4`);
- precision setting: 8.

Profile distribution:

- **98.75% (947/959) `write_vmdatal` -> RSP/VRAM semaphore wait**;
- 0.63% frame/VI wait;
- everything else individually negligible.

RSP state captured at the end of the measured window:

- `SP_DMA_BUSY = 0`;
- `SP_DMA_FULL = 0`;
- `SP_STATUS = 1` (**halted bit set**);
- `SP_PC = 3472` (`0x0D90`).

This means the R4300 is spinning on the VRAM semaphore while the RSP is not busy with DMA and is observed halted at PC 0x0D90.

### Interpreter control — same workload behaves normally

Latest `interpreter-gameplay` control with `Developer/ForceInterpreter=true`:

- measured wall window: 5 s;
- statistical samples: **875**;
- `fps_display`: **59 / 60 VI**;
- partial `fps_native`: 14;
- partial `fps_emulate`: 14;
- `frame_count`: 1;
- frameskip setting: 0;
- APU clock: 21;
- audio enabled (`audio_set=4`);
- precision setting: 8.

Profile distribution:

- 52.80% frame/VI wait;
- 21.60% APU/SPC700 static;
- 13.26% S-CPU interpreter;
- 4.11% APU generated JIT;
- 3.09% PPU/events/frame prep;
- 2.63% DSP/audio;
- 2.17% DMA/HDMA;
- only **0.34% RSP/VRAM semaphore wait**.

RSP state at capture:

- `SP_DMA_BUSY = 0`;
- `SP_DMA_FULL = 0`;
- `SP_STATUS = 0` (not halted);
- `SP_PC = 527` (`0x020F`).

### Interpretation of the A/B result

This is currently the most important Phase 1 finding:

**The catastrophic 1/60 gameplay result is not intrinsic to the cleaned SNES workload. It appears only on an ares recompiler path.**

However, `ForceInterpreter=true` disables **both** the ares R4300 CPU recompiler and the ares RSP recompiler, so this A/B test does **not yet identify which recompiler is responsible**.

Do not claim yet that the RSP JIT alone is broken, nor that Sodium64 itself would show this behavior on real hardware.

## Source-level facts already checked during this investigation

These simple explanations have been investigated and should **not** be rediscovered from scratch:

1. **Ares implements the SP semaphore semantics.** Reading the semaphore returns state / sets it; writing clears it.
2. **Ares RSP JIT does not optimize away `MTC0` semaphore writes.** Its `MTC0` emission calls the same `RSP::MTC0` helper path used by the interpreter, which reaches `ioWrite`.
3. **CPU polling should not trivially starve the RSP in ares.** `cpu.forceSynchronize()` forces the CPU JIT out to `CPU::synchronize()`, which explicitly advances `rsp.main()`.
4. **Sodium64 intentionally uses this semaphore as VRAM protection.** R4300-side `write_vmdatal` waits while the RSP protects/copies VRAM.
5. **At frame start the Sodium64 RSP copies the full 64 KiB VRAM snapshot in synchronous 1 KiB DMA blocks, then clears/releases the semaphore.** That should not reasonably consume dozens of N64 VI periods on real hardware.
6. The earlier `dma-vram` profile classification was misleading: most of what had been called `PPU/frame prep` was actually this same `write_vmdatal` semaphore spin. The profiler now classifies it separately as **`RSP/VRAM semaphore wait`**.
7. Cleaning accidental OAM state did **not** remove the recompiler collapse. The clean recompiler run still sampled essentially all time in the semaphore wait.
8. `fps_display` semantics were verified in Sodium64 source: after each complete 60-VI interval it receives the completed emulated-frame count. The observed 0/60 or 1/60 results are therefore real virtual-N64 frame-budget observations, not uninitialized values.

## Immediate next experiment — isolate CPU JIT vs RSP JIT

This is the next action. Do not branch off into unrelated optimization work first.

Ares currently exposes one `Recompiler` / `ForceInterpreter` switch that toggles both CPU and RSP recompilers together. Create a **diagnostic-only pinned ares variant in CI** that can independently enable/disable the R4300 recompiler and RSP recompiler, then run the same cleaned `gameplay-balanced` workload in four modes:

1. CPU JIT ON / RSP JIT ON — known bad reference (~1/60, semaphore spin).
2. CPU JIT OFF / RSP JIT OFF — known good reference (~59/60).
3. CPU JIT ON / RSP JIT OFF — isolates R4300 JIT with interpreted RSP.
4. CPU JIT OFF / RSP JIT ON — isolates RSP JIT with interpreted R4300.

Keep the Sodium64 ROM/workload/settings identical. Capture the same profiler data and `SP_STATUS`, `SP_DMA_BUSY`, `SP_DMA_FULL`, `SP_PC` for all four modes.

Decision tree:

- If only modes with **RSP JIT ON** collapse, investigate ares RSP recompiler execution/halt/PC/DMA/semaphore behavior around the observed stop state.
- If only modes with **CPU JIT ON** collapse, investigate R4300 JIT synchronization / memory-mapped SP I/O semantics around semaphore polling.
- If only the **combination** of both JITs collapses, investigate cross-thread synchronization/interleaving.
- If the supposedly isolated modes contradict this matrix, preserve the data and inspect exact SP PC/state before changing Sodium64.

This ares modification is a **laboratory diagnostic only**. Do not vendor it into Sodium64 or turn it into a second emulator project.

## Hardware-test status

**No real-N64 test requested yet.**

The current uncertainty is still cheaper to isolate in the automated lab. Once CPU-JIT-vs-RSP-JIT is separated, decide whether a real-N64 milestone run is the correct authority for the remaining synchronization question.

When hardware is requested, provide Iron with one exact milestone package, exact ROMs/settings, observations to report, and the decision that the test unlocks.

## Guardrails

- No game-specific manual modes as the compatibility strategy.
- No frameskip, APU underclock, frame generation, muted/stretched audio or omitted required work counted as full-speed progress.
- No endless tiny numbered builds without a measurable hypothesis.
- Do not let profiling or ares diagnostics become a second emulator/project.
- Do not merge risky low-level experiments merely because they compile.
- Do not send upstream PRs without Iron's explicit request.
- Prefer architecture changes that move a Road-to-1.0 gate and have a falsifiable measurement.
- Keep `master` as the best-known stable integrated state.
- Keep this branch as the freshest handoff.

## Resume protocol

Read in this order:

1. `continuity:docs/CONTINUITY.md`
2. active PR #9 and its current HEAD/CI if still open
3. `master:docs/ROAD_TO_1_0.md`
4. `master:docs/ROADMAP.md`
5. `master:docs/PROFILING.md`
6. `master:docs/VALIDATION.md`
7. `master:docs/BASELINE.md`

If sources disagree, prefer the newest concrete repository/CI state, then immediately repair this file.
