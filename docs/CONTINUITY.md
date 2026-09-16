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
PR #9 `Phase 1: add balanced gameplay-like profiling workload` is **MERGED-CONSUMED**.
Integrated foundation: #1 workflow, #2 baseline, #3 statistical profiler, #4 branch validation, #5 ares GDB profiling, #6 synthetic matrix, #7 Road to 1.0, #8 virtual frame budget, #9 cleaned gameplay-like workload + corrected VRAM/RSP classification + valid ares lab mode.

## MEASUREMENT PROOF — valid ares lab

2x2 isolation run `35113184294`, artifact `10453682432`:

| CPU | RSP | frames/60 VI | result |
| --- | --- | ---: | --- |
| JIT | JIT | 0 | collapsed |
| interpreter | interpreter | 60 | good |
| JIT | interpreter | 60 | good |
| interpreter | JIT | 0 | collapsed |

**LAB LIMITATION:** collapse follows the pinned ares RSP recompiler, independently of the R4300 engine.
**REJECTED:** R4300 JIT as cause; RSP stuck in DMA wait; missing semaphore semantics; dropped semaphore `MTC0`; accidental OAM wall as primary cause.
Valid high-density ares mode: **R4300 JIT + RSP interpreter**.
`SP_PC=0x0D90` maps to intentional RSP `next_frame` self-halt. Do not debug ares RSP JIT further unless a Road gate later requires it.

Replacement matrix run `35114866448`, artifact `10454678803`, frameskip 0 / APU 21 / audio enabled / precision 8:

| workload | S-CPU | APU JIT | APU static | PPU | DMA | VRAM/RSP wait | VI wait | frames/60 VI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| idle | 49.8% | 5.1% | 31.5% | 2.3% | 0.2% | 0.0% | 9.7% | 60 |
| cpu-alu | 59.0% | 2.0% | 36.2% | 1.6% | 0.3% | 0.0% | 0.0% | 41 |
| wram | 56.7% | 3.3% | 36.8% | 2.3% | 0.4% | 0.0% | 0.0% | 47 |
| ppu-registers | 42.7% | 4.0% | 31.3% | 21.2% | 0.1% | 0.0% | 0.0% | 38 |
| dma-vram | 1.1% | 1.5% | 7.7% | 31.2% | 30.5% | 27.8% | 0.0% | 16 |
| gameplay-balanced | 6.3% | 7.5% | 27.3% | 4.3% | 2.0% | 0.3% | 51.5% | 61 |

**MEASURED:** `gameplay-balanced` is not throughput-bound in valid ares lab. `61/60` is headroom, not proof of exact cadence.
**SUPERSEDED:** old `dma-vram ~=98% PPU`; valid stress separates PPU/DMA/synchronization.
**NOT PROVEN:** commercial performance, real-N64 FPS, representative S-CPU dominance, or dynarec justification.
`master:docs/PROFILING.md` records the full history and limits.

## SELECTED NEXT WORKLOAD — Gothicvania

**DECIDED / MEASUREMENT PROOF:** use `donth77/snes-homebrew` → `gothicvania` as the next Phase 1 representativeness step.

Pinned upstream commit: **`119496e6a2f1e53b7704712fef8cb81814f1698a`**.
Repo license: **MIT**. README states the GothicVania Cemetery graphics are adapted from a **CC0** pack. Source/assets needed to build are committed.
Toolchain: **PVSnesLib 4.5.0**. Official Linux release asset exists: `pvsneslib_450_64b_linux.zip`, SHA-256 **`b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`**.

Why selected:
- real original SNES action-platformer, not a synthetic stress loop;
- LoROM <512 KiB, no enhancement chip;
- boots on real SNES per upstream README;
- sustained Mode 1 gameplay with 4800px scrolling;
- 3-depth HDMA parallax + per-scanline color-math gradient;
- dynamic VRAM page streaming;
- hero/enemies/sprite streaming/collision;
- SNESMod looping music + SFX;
- first skeleton spawns around tile 10, so integrated enemy/streaming/audio activity occurs near the start;
- spike hazards are much farther into the level, allowing a short deterministic benchmark window.

Automation must remain minimal and auditable. Intended diagnostic-only upstream patch:
1. change initial game state `ST_TITLE` -> `ST_PLAY` to skip only the title screen;
2. in `playState`, replace `padsCurrent(0)` with deterministic `KEY_RIGHT` during the measured benchmark.

Do **not** alter physics, enemy logic, renderer, HDMA, streaming, audio, collision, timing, or Sodium64 runtime to make the workload easier. The workload should therefore be described as a **deterministic benchmark derivation of an open game**, not an untouched game run.

Candidate considered but not selected first: `240pTestSNES` (GPL, real-hardware-tested) is excellent for later fidelity/PPU validation, but its default menu/static-pattern flow requires more automation to become a sustained gameplay-performance workload.

## RESUME HERE — implementation batch

1. Create a phase branch from master `ee86d339...`, likely `phase1/open-homebrew-workload`.
2. Reuse existing profiler/frame-budget infrastructure; **do not add new profiling machinery** unless Gothicvania exposes a specific unanswered question.
3. CI should pin Gothicvania source SHA + PVSnesLib 4.5.0 Linux archive/checksum, build the minimally patched ROM from source, convert/inject it using the existing Sodium64 workload path, and run it under valid ares CPU-JIT + RSP-interpreter mode.
4. Use a short deterministic gameplay window long enough to trigger scrolling/enemy/sprite/audio activity but before distant spike hazards dominate.
5. Capture existing profile + `fps_display`/settings. Interpret major costs and virtual frame budget.
6. Checkpoint result before deciding hardware or M1.

Question: under a real open game workload, which major R4300 costs dominate, and does virtual frame budget still show headroom or expose a base-system pressure point?

## Hardware status

**No real-N64 request yet.** Gothicvania is the final cheap representativeness step currently preferred before deciding whether the next authority should be a focused M0 hardware package.

## Guardrails

No game-specific emulator modes. No frameskip/APU underclock/audio omission counted as performance. No endless profiler/tooling expansion. No diagnostic code merged merely because it produced knowledge. `master` remains best integrated state. Important rejected explanations survive here.

## Resume protocol

1. Read this file.
2. Verify master at/after `ee86d339...`.
3. Read Road/Roadmap/Profiling/Validation if direction or interpretation is involved.
4. Continue Gothicvania implementation from pinned upstream SHA/toolchain above.
5. Maintain batch -> checkpoint cadence.
