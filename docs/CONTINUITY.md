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
PR #9 is **MERGED-CONSUMED**. Integrated foundation: workflow/baseline/profiler/branch validation/ares GDB/synthetic matrix/Road/frame budget/gameplay-like workload + valid ares lab mode.

## MEASUREMENT PROOF — valid ares lab
2x2 isolation run `35113184294`, artifact `10453682432`:

| CPU | RSP | frames/60 VI | result |
| --- | --- | ---: | --- |
| JIT | JIT | 0 | collapsed |
| interpreter | interpreter | 60 | good |
| JIT | interpreter | 60 | good |
| interpreter | JIT | 0 | collapsed |

**LAB LIMITATION:** collapse follows pinned ares RSP recompiler, independently of R4300 engine.
**REJECTED:** R4300 JIT cause; RSP stuck in DMA wait; missing semaphore semantics; dropped semaphore `MTC0`; accidental OAM wall primary cause.
Valid lab: **R4300 JIT + RSP interpreter**. Do not debug ares RSP JIT further unless a Road gate requires it.

Replacement run `35114866448`, artifact `10454678803`, frameskip 0 / APU 21 / audio on / precision 8:
- idle 60/60;
- cpu-alu 41/60;
- wram 47/60;
- ppu-registers 38/60;
- dma-vram 16/60;
- gameplay-balanced 61/60 with 51.5% VI wait and 0.3% VRAM/RSP wait.

**MEASURED:** synthetic mixed workload has throughput headroom in valid ares lab. `61/60` is not cadence proof.
**SUPERSEDED:** old `dma-vram ~=98% PPU` interpretation.
**NOT PROVEN:** commercial performance, real-N64 FPS, representative S-CPU dominance, dynarec justification.

## SELECTED REPRESENTATIVE WORKLOAD — Gothicvania
**DECIDED / MEASUREMENT PROOF:** `donth77/snes-homebrew` → `gothicvania`.

Pinned upstream: **`119496e6a2f1e53b7704712fef8cb81814f1698a`**.
License: **MIT**; graphics adaptation credited upstream to CC0 source pack.
Toolchain: **PVSnesLib 4.5.0** Linux archive, SHA-256 **`b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`**.

Why: real original no-chip LoROM action-platformer; Mode 1; 4800px scroll; HDMA parallax; scanline color-math gradient; VRAM page streaming; enemies/sprite streaming/collision; SNESMod music/SFX. First skeleton triggers near start; spike hazards much later.

Diagnostic-only automation is intentionally limited to:
1. initial state `ST_TITLE -> ST_PLAY`;
2. gameplay `padsCurrent(0) -> KEY_RIGHT`.

Do not modify physics, enemies, renderer, HDMA, streaming, audio, collision, timing or Sodium64 runtime to make it easier. Describe result as a deterministic benchmark derivation of an open game, not untouched gameplay.

`240pTestSNES` remains useful later for fidelity/PPU validation but was not selected first because default flow is menu/static patterns rather than sustained gameplay.

## RESUME HERE — SOURCE BUILD FIX
Active branch: **`phase1/open-homebrew-workload`** from master `ee86d339...`.
Current HEAD before fix: **`e72566dd5af1739ef3a1257a1ffb12fe3f985a98`**.

Workflow: `.github/workflows/open-homebrew-build.yml`.
First source-build run: **`35119197827` — FAILURE**.
Normal branch validation run: `35119197754`.

What passed before failure:
- exact PVSnesLib archive download and SHA-256 verification;
- exact Gothicvania SHA checkout;
- both deterministic source replacements and diff checks.

Failure occurred only at `make`:
- `make` unexpectedly ran `tools/adapt_hero.py` / `tools/adapt_enemy.py`;
- those scripts failed first with `ModuleNotFoundError: numpy`.

**SUPPORTED INTERPRETATION / SOURCE FACT:** this is not a valid missing dependency of the intended Gothicvania build. Upstream Makefile explicitly marks these art converters as **FROZEN ART** and says their original source inputs were removed; committed `res/*.png`, `res/*.bin`, level outputs and generated animation headers are the source of truth and the converters are intentionally not supposed to run.

**CAUSE:** clean Git checkout does not preserve upstream file mtimes, so Make can see frozen converter scripts as new enough to regenerate committed outputs despite upstream's intended timestamp ordering.

**REJECTED NEXT ACTION:** do not install numpy and chase the frozen converters. That would move away from the documented upstream build model and may hit intentionally missing source-art inputs.

Correct next experiment:
- after checkout/patch, refresh **only mtimes** of committed frozen outputs (`gothicvania/res/**` plus generated animation headers as needed) so they are newer than converter scripts;
- bytes remain untouched; Git diff must still contain only the two intentional C-source benchmark changes;
- rerun the clean source build.

Question remains: can the benchmark ROM be reproduced from pinned open source + pinned SDK while respecting upstream's frozen-art build model?

If green: inspect ROM/provenance artifact, checkpoint, then profile this exact build using existing ares machinery. If red: inspect the next actual build dependency before adding ares.

## Hardware status
**No real-N64 request yet.** Gothicvania is the final cheap representativeness step currently preferred before deciding whether next authority should be focused M0 hardware validation.

## Guardrails
No game-specific emulator modes. No frameskip/APU underclock/audio omission counted as performance. No endless profiler/tooling expansion. No diagnostic code merged merely because it produced knowledge. `master` remains best integrated state. Important rejected explanations survive here.

## Resume protocol
1. Read this file.
2. Verify master at/after `ee86d339...`.
3. Inspect branch `phase1/open-homebrew-workload` and run `35119197827`.
4. Fix frozen-output mtimes only; do not add converter dependencies.
5. Resolve source build before adding ares profiling.
6. Maintain batch -> checkpoint cadence.
