# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating rule

Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**.

Checkpoint whenever branch/PR/HEAD, measured result, interpretation, rejected cause, lab limitation, next experiment, long-running CI experiment, hardware need, merge/reject/supersede, or Road/phase direction changes.

Do not rely on chat history or hidden reasoning. A new session must continue from this file + referenced repo/CI evidence.

## Project hierarchy

1. `master:docs/ROAD_TO_1_0.md` = destination / gates.
2. `master:docs/ROADMAP.md` = technical route.
3. `master:docs/PROFILING.md` = measurement methodology/limits.
4. `master:docs/VALIDATION.md` = validation authority.
5. `continuity:docs/CONTINUITY.md` = current position / live investigation.

Current milestone: **M0 / ROADMAP Phase 1 — baseline and bottleneck map**.

Perfect target remains real-N64 native cadence, no required frameskip/frame generation, full-rate APU/audio, high CPU/PPU/DMA/HDMA/timing fidelity, broad compatibility, DSP-1 family, Super FX / Super FX 2 and SA-1. N64-alone first; cartridge assistance only after a quantified hardware-budget gap.

## Stable master

Master before active PR: `798ebcb9969d94eda3eba4592eae2792d6304cb5`.

Integrated: PR #1 foundation, #2 baseline, #3 statistical profiler, #4 branch CI, #5 ares GDB profiling, #6 synthetic matrix, #7 Road to 1.0, #8 virtual-N64 frame-budget correlation.

Leading future hypothesis remains 65C816 -> R4300 MIPS dynarec, but **do not start M1 merely from CPU-heavy synthetic controls**.

## RESUME HERE — PR #9

PR: `#9 Phase 1: add balanced gameplay-like profiling workload`

- branch: `phase1/gameplay-mixed-workload`
- base: master `798ebcb9969d94eda3eba4592eae2792d6304cb5`
- current HEAD: **`5a1c0cd4759482ae913a20e6f14491cb456f2b53`**
- state: **OPEN / NOT MERGED**
- temporary isolation workflow has been **removed** from the branch after producing its evidence.
- normal `Build and Validate` for current HEAD: run **`35114858150`**, pending/in progress at checkpoint.
- replacement `Ares Profile Validation` for current HEAD: run **`35114866448`**, pending/in progress at checkpoint.

Current branch now changes the normal ares lab so the pinned ares build keeps **R4300 recompiler ON** for decision-lab runs but forces **RSP recompiler OFF / RSP interpreter ON**. This is a laboratory workaround only; Sodium64 runtime is not altered by it.

`gameplay-balanced` is a cleaned deterministic game-shaped workload: `WAI`/NMI pacing, bounded CPU/WRAM logic, bounded OAM/VRAM/CGRAM work, BG1+OBJ enabled, one visible sprite, remaining sprites hidden, frameskip 0, full-rate APU (21) with JIT invalidation, audio enabled.

## MEASUREMENT PROOF — ares CPU/RSP JIT isolation

Diagnostic run: **`35113184294`** on old diagnostic HEAD `2fbd83d6a2491e2a663b21f545fff5b8323aa50f`.

Artifact: **`sodium64-ares-recompiler-isolation`**, artifact ID **`10453682432`**.

Same Sodium64 build/workload/settings for all four modes:

| ares mode | samples | frames / 60 VI | SP_STATUS | DMA busy/full | SP_PC | result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| CPU JIT ON / RSP JIT ON | 3583 | **0/60** | 1 | 0 / 0 | `0x0D90` | collapsed |
| CPU JIT OFF / RSP JIT OFF | 1242 | **60/60** | 1 | 0 / 0 | `0x0D98` | good |
| CPU JIT ON / RSP JIT OFF | 2477 | **60/60** | 1 | 0 / 0 | `0x0D98` | good |
| CPU JIT OFF / RSP JIT ON | 1872 | **0/60** | 1 | 0 / 0 | `0x0D90` | collapsed |

Both modes with **RSP JIT ON** sampled 100% in `write_vmdatal` -> RSP/VRAM semaphore wait. Both modes with **RSP JIT OFF** progressed normally.

### Interpretation

**MEASURED:** collapse follows the **ares RSP recompiler** independently of the R4300 recompiler.

**REJECTED:** R4300 JIT as cause. CPU JIT ON + RSP interpreter reaches 60/60.

**LAB LIMITATION:** pinned ares RSP recompiler is not a valid performance/synchronization laboratory for Sodium64 custom RSP microcode under this workload.

Do not attribute old 0/60 or 1/60 recompiler gameplay results to Sodium64 or real N64 hardware.

Validated high-density lab mode: **R4300 JIT + RSP interpreter**.

## SP_PC / semaphore finding

Exact profiling ELF disassembly maps `SP_PC=0x0D90` to Sodium64 RSP label `next_frame`:

- `li t0, 2`;
- `mtc0 t0, SP_STATUS` — intentional self-halt;
- branch back toward `draw_frame` after restart.

Therefore **REJECTED:** “RSP is stuck in DMA wait.” At bad capture RSP has reached intentional end-of-frame halt; DMA is idle while R4300 spins on VRAM semaphore.

## Rejected / superseded explanations

Do not rediscover these:

- **REJECTED:** ares lacks SP semaphore semantics.
- **REJECTED:** RSP JIT simply drops semaphore-clearing `MTC0`; JIT calls same helper path as interpreter.
- **REJECTED as simple explanation:** CPU polling trivially starves RSP; `CPU::synchronize()` explicitly advances `rsp.main()`.
- **REJECTED:** accidental OAM/sprite wall as primary cause.
- **REJECTED:** R4300 JIT as source of the gameplay collapse.
- **SUPERSEDED:** old `dma-vram ~=98% PPU` interpretation. Most samples were semaphore wait, now classified separately.
- **SOURCE FACT:** Sodium64 RSP copies 64 KiB VRAM in synchronous 1 KiB DMA blocks at frame start, then clears semaphore.
- **SOURCE FACT:** `fps_display` represents completed SNES frames over a complete 60-VI interval.

## LIVE EXPERIMENT — rebuild valid Phase 1 matrix

Status: **IN PROGRESS** at checkpoint.

Current HEAD `5a1c0cd4759482ae913a20e6f14491cb456f2b53` modifies the existing `Ares Profile Validation` build only:

- pinned ares source remains `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`;
- a one-line diagnostic lab patch forces `rsp.recompiler.enabled = false`;
- R4300 recompiler still follows the normal `ForceInterpreter` switch;
- ordinary decision runs therefore use **CPU JIT + RSP interpreter**;
- interpreter controls use **CPU interpreter + RSP interpreter**.

Question answered by run `35114866448`:

1. Do all existing synthetic workloads still produce coherent distributions without the invalid RSP JIT path?
2. Does cleaned `gameplay-balanced` reproduce ~60/60 at high sample density?
3. How much do old PPU/DMA percentages change once semaphore/JIT contamination is removed?

After run completion:

- download `sodium64-ares-profile-matrix` artifact;
- inspect frame-budget + subsystem matrix, not merely CI status;
- supersede contaminated historical numbers where necessary;
- update `PROFILING.md` with the demonstrated ares RSP-JIT `LAB LIMITATION` and valid lab mode;
- if both stable CI and replacement ares evidence are good, prepare PR #9 for merge.

Do not debug ares RSP JIT further unless a Road gate later requires it. The 2x2 already answered the Sodium64 decision question.

## Hardware status

**No real-N64 request yet.** First finish the replacement emulator-lab matrix. Then decide whether Phase 1 needs one more representative workload or whether the next authority should be a real-N64 M0 milestone package.

## Guardrails

- No game-specific modes as strategy.
- No frameskip/APU underclock/audio omission counted as performance.
- No endless profiler/tooling expansion.
- No diagnostic code merged merely because it produced knowledge.
- `master` remains best integrated state.
- Important rejected explanations survive here.

## Resume protocol

1. Read this file.
2. Inspect PR #9 HEAD `5a1c0cd...`.
3. Inspect runs `35114858150` and especially `35114866448`.
4. Interpret replacement matrix artifact before any architecture decision.
5. Read Road/Roadmap and Profiling/Validation before M1 work.
6. Repair this file immediately if repo/CI evidence is newer.
