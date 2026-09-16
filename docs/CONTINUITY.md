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

Current integrated master: **`ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`**.

PR #9 `Phase 1: add balanced gameplay-like profiling workload` is **MERGED-CONSUMED** (squash).

Integrated foundation now includes:

- #1 project foundation / measurable PR workflow;
- #2 baseline measurement map;
- #3 statistical profiler;
- #4 branch validation;
- #5 pinned ares GDB profiling;
- #6 deterministic synthetic bottleneck matrix;
- #7 Road to 1.0 contract;
- #8 virtual-N64 frame-budget correlation;
- #9 cleaned gameplay-like workload + corrected VRAM/RSP classification + valid ares lab mode.

## MEASUREMENT PROOF — ares CPU/RSP JIT isolation

Diagnostic run: **`35113184294`**.
Artifact: `sodium64-ares-recompiler-isolation`, ID **`10453682432`**.

| ares mode | samples | frames / 60 VI | result |
| --- | ---: | ---: | --- |
| CPU JIT ON / RSP JIT ON | 3583 | **0/60** | collapsed |
| CPU JIT OFF / RSP JIT OFF | 1242 | **60/60** | good |
| CPU JIT ON / RSP JIT OFF | 2477 | **60/60** | good |
| CPU JIT OFF / RSP JIT ON | 1872 | **0/60** | collapsed |

**MEASURED:** collapse follows the pinned ares **RSP recompiler**, independently of the R4300 engine.

**REJECTED:** R4300 JIT as cause.

**LAB LIMITATION:** ares RSP JIT is not a valid Sodium64 synchronization/performance lab for this custom RSP microcode/workload.

Validated high-density ares mode: **R4300 JIT + RSP interpreter**.

`SP_PC=0x0D90` maps to RSP `next_frame`, intentional end-of-frame self-halt. **REJECTED:** “RSP stuck in DMA wait.”

Do not debug ares RSP JIT further unless a Road gate later requires it.

## VALID REPLACEMENT MATRIX

Run: **`35114866448`**.
Artifact: `sodium64-ares-profile-matrix`, ID **`10454678803`**.

Settings: CPU JIT + RSP interpreter, frameskip `0`, APU `21`, audio enabled, precision `8`.

| workload | samples | S-CPU | APU JIT | APU static | PPU | DMA | VRAM/RSP wait | VI wait | frames/60 VI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| idle | 1303 | 49.8% | 5.1% | 31.5% | 2.3% | 0.2% | 0.0% | 9.7% | **60** |
| cpu-alu | 1055 | 59.0% | 2.0% | 36.2% | 1.6% | 0.3% | 0.0% | 0.0% | **41** |
| wram | 1474 | 56.7% | 3.3% | 36.8% | 2.3% | 0.4% | 0.0% | 0.0% | **47** |
| ppu-registers | 1123 | 42.7% | 4.0% | 31.3% | 21.2% | 0.1% | 0.0% | 0.0% | **38** |
| dma-vram | 878 | 1.1% | 1.5% | 7.7% | 31.2% | 30.5% | 27.8% | 0.0% | **16** |
| gameplay-balanced | 930 | 6.3% | 7.5% | 27.3% | 4.3% | 2.0% | 0.3% | 51.5% | **61** |

### Interpretation

**MEASURED:** cleaned `gameplay-balanced` is not throughput-bound in the valid ares lab; 51.5% of R4300 samples are in `frame_wait` and VRAM/RSP wait is only 0.3%.

**IMPORTANT:** `61/60` is not “better than perfect” and does not prove exact cadence. It establishes throughput headroom for this synthetic game-shaped workload only.

**SUPERSEDED:** old `dma-vram ~=96.7% PPU` interpretation. Valid stress separates PPU (31.2%), DMA (30.5%) and VRAM/RSP synchronization (27.8%).

**NOT PROVEN:** commercial-game performance, real-N64 FPS, representative S-CPU dominance, or that 65C816 dynarec is already the correct M1 architecture.

`master:docs/PROFILING.md` now records this history, lab limitation, valid lab mode and replacement matrix.

## Rejected / superseded explanations

Do not rediscover:

- **REJECTED:** ares lacks SP semaphore semantics.
- **REJECTED:** RSP JIT simply drops semaphore-clearing `MTC0`.
- **REJECTED as simple explanation:** CPU polling trivially starves RSP.
- **REJECTED:** accidental OAM/sprite wall as primary cause.
- **REJECTED:** R4300 JIT as source of collapse.
- **REJECTED:** RSP stuck in DMA wait.
- **SUPERSEDED:** old `dma-vram ~=98% PPU` interpretation.
- **SOURCE FACT:** Sodium64 RSP copies 64 KiB VRAM in synchronous 1 KiB DMA blocks at frame start, then clears semaphore.
- **SOURCE FACT:** `fps_display` represents completed SNES frames over a complete 60-VI interval.

## RESUME HERE — next Phase 1 batch

PR #9 is finished. **Do not start M1 dynarec yet.**

The next batch must increase **representativeness/authority**, not profiling complexity.

Preferred next step: identify one **complex, legally redistributable/open-source SNES homebrew or test workload** that can be built reproducibly from source and run through the existing lab without adding new profiler machinery.

Selection criteria:

- meaningfully more integrated than our synthetic workload;
- exercises multiple real SNES subsystems over sustained frames;
- source and ROM redistribution/build license suitable for CI;
- reproducible build or pinned artifact provenance;
- deterministic enough to reach a defined measurement checkpoint automatically;
- no enhancement chip yet (Phase 1 base-system question first).

Use it to answer: under a more representative open workload, which major R4300 costs dominate and does virtual frame budget still show headroom or a real base-system pressure point?

After that result, decide whether M0 needs a focused **real-N64 milestone package** before selecting M1 architecture.

Do not add more instrumentation unless the new workload exposes a specific unanswerable question.

## Hardware status

**No real-N64 request yet.** One more step up the representativeness ladder is cheaper and should make any later hardware session more decision-dense.

## Guardrails

- No game-specific modes as strategy.
- No frameskip/APU underclock/audio omission counted as performance.
- No endless profiler/tooling expansion.
- No diagnostic code merged merely because it produced knowledge.
- `master` remains best integrated state.
- Important rejected explanations survive here.

## Resume protocol

1. Read this file.
2. Verify master at/after `ee86d339...` and PR #9 merged.
3. Read Road/Roadmap/Profiling/Validation before selecting next workload.
4. Research/select a complex open workload; record selection rationale before implementation.
5. Continue with batch -> checkpoint cadence.
