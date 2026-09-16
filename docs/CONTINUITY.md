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
- current HEAD: **`d5a8affb2c917c874ec6854558bec40dc7f33710`**
- state: **OPEN / NOT MERGED**
- changed files now include `docs/PROFILING.md`, repaired to match current evidence.
- current `Build and Validate`: run **`35117036962`**, queued/in progress at checkpoint.
- current `Ares Profile Validation`: run **`35117041816`**, in progress at checkpoint.

The previous HEAD `5a1c0cd4759482ae913a20e6f14491cb456f2b53` already passed normal build, PROFILE build and Mupen smoke, and produced the valid replacement ares matrix below. The current HEAD changes documentation only, so it must still pass normal CI before merge.

## MEASUREMENT PROOF — ares CPU/RSP JIT isolation

Diagnostic run: **`35113184294`**.
Artifact: `sodium64-ares-recompiler-isolation`, ID **`10453682432`**.

Same Sodium64 build/workload/settings:

| ares mode | samples | frames / 60 VI | SP_STATUS | DMA busy/full | SP_PC | result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| CPU JIT ON / RSP JIT ON | 3583 | **0/60** | 1 | 0 / 0 | `0x0D90` | collapsed |
| CPU JIT OFF / RSP JIT OFF | 1242 | **60/60** | 1 | 0 / 0 | `0x0D98` | good |
| CPU JIT ON / RSP JIT OFF | 2477 | **60/60** | 1 | 0 / 0 | `0x0D98` | good |
| CPU JIT OFF / RSP JIT ON | 1872 | **0/60** | 1 | 0 / 0 | `0x0D90` | collapsed |

**MEASURED:** collapse follows the pinned ares **RSP recompiler**, independently of the R4300 engine.

**REJECTED:** R4300 JIT as cause.

**LAB LIMITATION:** ares RSP JIT is not a valid Sodium64 synchronization/performance lab for this custom RSP microcode/workload.

Validated high-density ares mode: **R4300 JIT + RSP interpreter**.

`SP_PC=0x0D90` maps to RSP `next_frame`, the intentional self-halt at end of frame. Therefore **REJECTED:** “RSP is stuck in DMA wait.” DMA is idle at bad capture.

Do not debug ares RSP JIT further unless a Road gate later requires it.

## VALID REPLACEMENT MATRIX

Run: **`35114866448`** on HEAD `5a1c0cd4759482ae913a20e6f14491cb456f2b53`.
Artifact: `sodium64-ares-profile-matrix`, ID **`10454678803`**.

Lab mode: CPU JIT + RSP interpreter. Settings: frameskip `0`, APU clock `21`, audio enabled (`4`), precision `8`.

| workload | samples | S-CPU | APU JIT | APU static | DSP | PPU | DMA | VRAM/RSP wait | VI wait |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| idle | 1303 | 49.8% | 5.1% | 31.5% | 1.4% | 2.3% | 0.2% | 0.0% | 9.7% |
| cpu-alu | 1055 | 59.0% | 2.0% | 36.2% | 0.9% | 1.6% | 0.3% | 0.0% | 0.0% |
| wram | 1474 | 56.7% | 3.3% | 36.8% | 0.5% | 2.3% | 0.4% | 0.0% | 0.0% |
| ppu-registers | 1123 | 42.7% | 4.0% | 31.3% | 0.6% | 21.2% | 0.1% | 0.0% | 0.0% |
| dma-vram | 878 | 1.1% | 1.5% | 7.7% | 0.1% | 31.2% | 30.5% | 27.8% | 0.0% |
| gameplay-balanced | 930 | 6.3% | 7.5% | 27.3% | 0.6% | 4.3% | 2.0% | 0.3% | 51.5% |

Virtual frame budget over last complete 60-VI window:

- idle: **60/60**
- cpu-alu: **41/60**
- wram: **47/60**
- ppu-registers: **38/60**
- dma-vram: **16/60**
- gameplay-balanced: **61/60**

### Interpretation

**MEASURED:** cleaned `gameplay-balanced` is not throughput-bound in the valid ares lab. More than half of R4300 samples land in `frame_wait` and VRAM/RSP semaphore wait is only 0.3%.

**IMPORTANT:** `61/60` is **not** “better than perfect” and does not prove exact cadence. It shows throughput headroom under this synthetic game-shaped workload; exact temporal cadence is a separate correctness question.

**SUPERSEDED:** old `dma-vram ~=96.7% PPU` / 1-fps-style readings from the RSP-JIT lab. Valid DMA stress now separates actual PPU (31.2%), DMA (30.5%) and VRAM/RSP synchronization (27.8%).

**MEASUREMENT PROOF:** the harness distinguishes controlled CPU, PPU, DMA and wait pressure; frame-budget signal moves coherently with synthetic stress.

**NOT PROVEN:** commercial-game performance, real-N64 FPS, representative S-CPU dominance, or that the 65C816 dynarec is already the correct M1 architecture.

## PROFILING canonical doc repaired

HEAD `d5a8affb2c917c874ec6854558bec40dc7f33710` rewrites `docs/PROFILING.md` to preserve the old matrix as explicitly **SUPERSEDED**, document the ares RSP-JIT `LAB LIMITATION`, define CPU-JIT + RSP-interpreter as the valid high-density lab mode, and record the replacement matrix/frame-budget above.

Do not reintroduce the old claim that `dma-vram` is ~97% PPU.

## Rejected / superseded explanations

Do not rediscover these:

- **REJECTED:** ares lacks SP semaphore semantics.
- **REJECTED:** RSP JIT simply drops semaphore-clearing `MTC0`; JIT calls same helper path as interpreter.
- **REJECTED as simple explanation:** CPU polling trivially starves RSP.
- **REJECTED:** accidental OAM/sprite wall as primary cause.
- **REJECTED:** R4300 JIT as source of collapse.
- **REJECTED:** RSP stuck in DMA wait.
- **SUPERSEDED:** old `dma-vram ~=98% PPU` interpretation.
- **SOURCE FACT:** Sodium64 RSP copies 64 KiB VRAM in synchronous 1 KiB DMA blocks at frame start, then clears semaphore.
- **SOURCE FACT:** `fps_display` represents completed SNES frames over a complete 60-VI interval.

## Immediate next action

1. Let runs `35117036962` and `35117041816` finish on documentation HEAD `d5a8affb...`.
2. If green, inspect PR #9 diff/body and update PR description with final measured results / LAB LIMITATION.
3. Merge PR #9 if candidate remains clean and mergeable.
4. Immediately checkpoint merged SHA/master state in this file.
5. Then choose the **next representativeness/authority step**, not more profiler plumbing: either a more complex open/homebrew workload or a focused real-N64 M0 milestone package, based on which best closes Phase 1 before M1 architecture commitment.

## Hardware status

**No real-N64 request yet at this checkpoint.** Synthetic + mixed lab evidence is now clean. After PR #9 merge, decide whether one more open complex workload materially reduces uncertainty or whether the next authority should be a real-N64 M0 milestone measurement.

## Guardrails

- No game-specific modes as strategy.
- No frameskip/APU underclock/audio omission counted as performance.
- No endless profiler/tooling expansion.
- No diagnostic code merged merely because it produced knowledge.
- `master` remains best integrated state.
- Important rejected explanations survive here.

## Resume protocol

1. Read this file.
2. Inspect PR #9 HEAD `d5a8affb...` and runs `35117036962` / `35117041816`.
3. If both green, finish PR #9 merge sequence before opening unrelated work.
4. Read Road/Roadmap and Profiling/Validation before M1 decisions.
5. Repair this file immediately if repo/CI evidence is newer.
