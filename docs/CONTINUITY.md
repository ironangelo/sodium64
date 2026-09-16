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
- current HEAD: `2fbd83d6a2491e2a663b21f545fff5b8323aa50f`
- PR remains **open, mergeable, not merged**.
- prior ares diagnostic workflow: run `35109280375`, success.
- prior diagnostic artifact: `sodium64-ares-profile-matrix`, artifact ID `10451624678`.
- current 2x2 isolation workflow: `Ares Recompiler Isolation`, run `35113184294`, **IN PROGRESS** when this checkpoint was written.
- normal Ares Profile Validation for the same HEAD: run `35113187984`, **IN PROGRESS** when this checkpoint was written.

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

Host tests, normal build, `PROFILE=1`, Mupen smoke and ares workflow all remain green on the previous diagnostic HEAD.

## Critical finding — recompiler-only gameplay collapse

The cleaned workload collapses under the normal ares recompiler configuration, but **does not collapse when ares is forced to interpreter mode**.

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

**MEASURED:** the catastrophic 1/60 gameplay result is not intrinsic to the cleaned SNES workload. It appears only when ares recompilers are enabled.

**OPEN QUESTION:** `ForceInterpreter=true` disables both the ares R4300 CPU recompiler and the ares RSP recompiler, so the A/B test does not identify which recompiler is responsible.

Do not claim yet that the RSP JIT alone is broken, nor that Sodium64 itself would show this behavior on real hardware.

## Source-level facts already checked during this investigation

These explanations have been investigated and should **not** be rediscovered from scratch:

1. **REJECTED:** “ares does not implement the SP semaphore.” It does.
2. **REJECTED:** “ares RSP JIT optimizes away the semaphore-clearing `MTC0`.” Its JIT calls the same `RSP::MTC0` helper path as the interpreter.
3. **REJECTED as simple explanation:** “CPU polling trivially starves the RSP.” `cpu.forceSynchronize()` forces CPU JIT exit to `CPU::synchronize()`, which explicitly advances `rsp.main()`.
4. **MEASURED/SOURCE FACT:** Sodium64 intentionally uses this semaphore as VRAM protection. R4300-side `write_vmdatal` waits while the RSP protects/copies VRAM.
5. **SOURCE FACT:** at frame start the Sodium64 RSP copies the full 64 KiB VRAM snapshot in synchronous 1 KiB DMA blocks, then clears/releases the semaphore. That should not reasonably consume dozens of N64 VI periods on real hardware.
6. **SUPERSEDED INTERPRETATION:** the earlier `dma-vram` profile classification was misleading. Most samples called `PPU/frame prep` were the same `write_vmdatal` semaphore spin. The profiler now classifies this separately as `RSP/VRAM semaphore wait`.
7. **REJECTED:** accidental OAM state as the primary cause. Cleaning OAM and enabling a legitimate BG1+OBJ scene did not remove the recompiler collapse.
8. **SOURCE FACT:** `fps_display` is updated after each complete 60-VI interval with the completed emulated-frame count; 0/60 or 1/60 observations are therefore real virtual-N64 frame-budget observations, not uninitialized values.

## LIVE EXPERIMENT — isolate CPU JIT vs RSP JIT

Status: **IN PROGRESS** at checkpoint.

Diagnostic-only workflow added on PR #9 HEAD `2fbd83d6a2491e2a663b21f545fff5b8323aa50f`:

- `.github/workflows/ares-recompiler-isolation.yml`
- run ID: `35113184294`
- pinned ares remains `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`.

The workflow builds three binaries from that exact ares source using ccache:

1. original ares binary: normal switch controls both CPU and RSP recompilers;
2. CPU-only diagnostic binary: CPU recompiler follows the normal switch, RSP recompiler is forced OFF;
3. RSP-only diagnostic binary: RSP recompiler follows the normal switch, CPU recompiler is forced OFF.

It then runs the **same cleaned `gameplay-balanced` ROM and identical Sodium64 settings** in four modes:

1. `both-jit` = CPU JIT ON / RSP JIT ON;
2. `neither-jit` = CPU JIT OFF / RSP JIT OFF;
3. `cpu-jit-only` = CPU JIT ON / RSP JIT OFF;
4. `rsp-jit-only` = CPU JIT OFF / RSP JIT ON.

Every mode captures:

- statistical profile;
- `fps_display`, `fps_native`, `fps_emulate`, `frame_count`;
- frameskip/APU/audio/precision settings;
- `SP_STATUS`, `SP_DMA_BUSY`, `SP_DMA_FULL`, `SP_PC`.

Decision tree after run `35113184294` completes:

- collapse follows **RSP JIT ON** -> treat ares RSP recompiler as leading LAB LIMITATION; inspect exact PC/halt transition only as needed, then stop expanding ares tooling.
- collapse follows **CPU JIT ON** -> inspect R4300 JIT synchronization / MMIO semaphore polling path.
- only **both JITs ON** collapse -> investigate cross-recompiler synchronization/interleaving.
- neither isolated pattern matches -> preserve exact state and inspect before touching Sodium64.

This ares source modification is **diagnostic-only**. Do not vendor it into Sodium64 and do not merge the temporary isolation workflow after the question is answered unless a continuing measurement need is demonstrated.

## Hardware-test status

**No real-N64 test requested yet.**

The current uncertainty is still cheaper to isolate in the automated lab. After CPU-JIT-vs-RSP-JIT is separated, decide whether the remaining synchronization question is a `LAB LIMITATION` that should stop influencing architecture decisions or whether a real-N64 milestone is needed.

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
