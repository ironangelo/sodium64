# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating rule

Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**.

Checkpoint whenever branch/PR/HEAD, measured result, interpretation, rejected cause, lab limitation, next experiment, long-running CI experiment, hardware need, merge/reject/supersede, or Road/phase direction changes.

Do not rely on chat history or hidden reasoning. A new session must be able to continue from this file + referenced repo/CI evidence.

## Project hierarchy

1. `master:docs/ROAD_TO_1_0.md` = destination / gates.
2. `master:docs/ROADMAP.md` = current technical route.
3. `master:docs/PROFILING.md` = measurement methodology/limits.
4. `master:docs/VALIDATION.md` = validation authority.
5. `continuity:docs/CONTINUITY.md` = current position / live investigation.

Current milestone: **M0 / ROADMAP Phase 1 — baseline and bottleneck map**.

Perfect target remains real-N64 native temporal cadence, no required frameskip/frame generation, full-rate APU/audio, high CPU/PPU/DMA/HDMA/timing fidelity, broad compatibility, DSP-1 family, Super FX / Super FX 2 and SA-1. N64-alone first; cartridge assistance only after a quantified hardware-budget gap.

## Stable master

Master before active PR: `798ebcb9969d94eda3eba4592eae2792d6304cb5`.

Integrated foundation:

- PR #1 project foundation / CI.
- PR #2 baseline map.
- PR #3 statistical R4300 profiler.
- PR #4 development-branch validation.
- PR #5 pinned ares GDB profiling path.
- PR #6 deterministic synthetic bottleneck matrix.
- PR #7 Road to 1.0.
- PR #8 virtual-N64 frame-budget correlation using Sodium64's own 60-VI FPS state.

Leading future architecture hypothesis remains 65C816 -> R4300 MIPS dynarec, but **do not start M1 merely from CPU-heavy synthetic controls**. Phase 1 must first finish representative evidence.

## RESUME HERE — PR #9

PR: `#9 Phase 1: add balanced gameplay-like profiling workload`

- branch: `phase1/gameplay-mixed-workload`
- base: master `798ebcb9969d94eda3eba4592eae2792d6304cb5`
- current HEAD: `2fbd83d6a2491e2a663b21f545fff5b8323aa50f`
- state: **OPEN / mergeable / NOT MERGED**
- do **not** merge yet.

`gameplay-balanced` is now a cleaned deterministic game-shaped SNES workload:

- `WAI` / NMI frame pacing;
- bounded CPU/WRAM logic;
- bounded OAM/VRAM/CGRAM updates per frame;
- BG1 + OBJ enabled (`TM=$11`);
- one intended visible sprite;
- other 127 sprites explicitly hidden;
- frameskip forced 0 in measurement;
- APU forced full-rate (`apu_clock=21`) with APU JIT invalidated before measurement;
- audio enabled.

Host tests, N64 builds and prior Mupen/ares gates remain green. The remaining problem is an **ares recompiler-specific synchronization pathology**, not basic ROM validity.

## MEASURED — ares recompiler vs interpreter

Prior diagnostic run: `35109280375`; artifact `10451624678`.

### Both recompilers enabled — bad lab path

`recompiler-gameplay-balanced`:

- 959 samples;
- `fps_display = 1/60`;
- 98.75% (947/959) sampled in `write_vmdatal`'s RSP/VRAM semaphore wait;
- frameskip 0;
- APU 21;
- audio enabled;
- `SP_DMA_BUSY=0`;
- `SP_DMA_FULL=0`;
- `SP_STATUS=1` (halted);
- `SP_PC=0x0D90`.

### Both recompilers disabled — good control

`interpreter-gameplay` (`ForceInterpreter=true`):

- 875 samples;
- `fps_display = 59/60`;
- only 0.34% RSP/VRAM semaphore wait;
- frame/VI wait 52.80%; APU static 21.60%; S-CPU 13.26%; APU JIT 4.11%; PPU 3.09%; DSP 2.63%; DMA/HDMA 2.17%;
- frameskip 0;
- APU 21;
- audio enabled;
- `SP_DMA_BUSY=0`;
- `SP_DMA_FULL=0`;
- `SP_STATUS=0`;
- `SP_PC=0x020F`.

**SUPPORTED INTERPRETATION:** the catastrophic 1/60 result is not intrinsic to the cleaned SNES workload. It depends on an ares recompiler path.

**OPEN QUESTION:** `ForceInterpreter` disables both R4300 and RSP recompilers, so the responsible side is not yet known.

## MEASURED — SP_PC 0x0D90 meaning

Artifact disassembly was checked against the exact profiling ELF.

`SP_PC=0x0D90` decodes to Sodium64 RSP label `next_frame`:

- `li t0, 2`;
- `mtc0 t0, SP_STATUS` — intentional self-halt;
- branch back toward `draw_frame` after restart.

Therefore **REJECT** the interpretation that the captured RSP was stuck inside `dma_wait`.

The bad recompiler state is instead:

- R4300 spinning on VRAM semaphore;
- RSP has already reached its intentional end-of-frame halt;
- DMA engine is idle.

**HYPOTHESIS:** recompiler timing/interleaving allows the RSP to reach end-of-frame halt while the CPU later reaches a VRAM write that waits on a semaphore which will not be released until another RSP frame starts. This is not yet assigned to Sodium64 or ares; the 2x2 experiment below must isolate it.

## Rejected / superseded explanations

Do not rediscover these from scratch:

- **REJECTED:** ares lacks SP semaphore semantics. It implements read/set and write/clear.
- **REJECTED:** ares RSP JIT drops the semaphore-clearing `MTC0`. JIT `MTC0` calls the same `RSP::MTC0` helper path used by interpreter.
- **REJECTED as simple explanation:** CPU polling trivially starves the RSP. `cpu.forceSynchronize()` forces CPU JIT exit into `CPU::synchronize()`, which explicitly advances `rsp.main()`.
- **REJECTED:** accidental OAM/sprite wall is the primary cause. Clean OAM did not remove collapse.
- **SUPERSEDED:** old `dma-vram ~=98% PPU` interpretation. Most samples were actually the same `write_vmdatal` semaphore spin, now classified as `RSP/VRAM semaphore wait`.
- **SOURCE FACT:** Sodium64 RSP copies the full 64 KiB VRAM snapshot in synchronous 1 KiB DMA blocks at frame start and then clears the semaphore.
- **SOURCE FACT:** `fps_display` is updated after a complete 60-VI interval, so 0/60 or 1/60 are valid virtual-N64 frame-progress observations, not uninitialized data.

## LIVE EXPERIMENT — CPU JIT vs RSP JIT 2x2

Status at checkpoint: **IN PROGRESS**.

Diagnostic-only workflow:

- file: `.github/workflows/ares-recompiler-isolation.yml`
- PR #9 HEAD: `2fbd83d6a2491e2a663b21f545fff5b8323aa50f`
- pinned ares: `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`
- isolation run: `35113184294`
- normal Ares Profile Validation same HEAD: `35113187984`

The workflow builds temporary ares binaries using the same pinned source:

1. `both-jit`: CPU JIT ON / RSP JIT ON.
2. `neither-jit`: CPU JIT OFF / RSP JIT OFF.
3. `cpu-jit-only`: CPU JIT ON / RSP JIT OFF.
4. `rsp-jit-only`: CPU JIT OFF / RSP JIT ON.

Same Sodium64 ROM/workload/settings for all four. Capture profile, frame budget, `SP_STATUS`, `SP_DMA_BUSY`, `SP_DMA_FULL`, `SP_PC`.

Decision after run:

- collapse follows **RSP JIT ON** -> classify ares RSP recompiler as leading `LAB LIMITATION`; stop letting this path influence Sodium64 architecture and remove temporary workflow before merge.
- collapse follows **CPU JIT ON** -> inspect R4300 JIT/MMIO/semaphore synchronization.
- only **both JITs ON** collapse -> investigate cross-recompiler scheduling/interleaving.
- unexpected matrix -> preserve exact evidence and inspect before modifying Sodium64.

The isolation workflow is diagnostic-only. Do not vendor/fork ares or turn this into a second project.

## Hardware status

**No real-N64 request yet.** Current uncertainty is still cheaper to isolate automatically. After the 2x2 result, decide whether this becomes a documented `LAB LIMITATION` or whether hardware authority is required.

## Guardrails

- No game-specific modes as strategy.
- No frameskip/APU underclock/audio omission counted as performance.
- No endless profiler/tooling expansion.
- No diagnostic code merged just because it produced knowledge.
- `master` remains best integrated state.
- Important rejected explanations must survive in continuity.

## Resume protocol

1. Read this file.
2. Inspect PR #9, HEAD and run `35113184294` first.
3. Read Road/Roadmap and Profiling/Validation.
4. Compare repo/CI evidence to this checkpoint; repair continuity if newer.
5. Continue from the 2x2 decision tree, not from chat memory.
