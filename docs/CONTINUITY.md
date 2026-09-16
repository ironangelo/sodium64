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
**DECIDED / MEASUREMENT PROOF:** `donth77/snes-homebrew` -> `gothicvania`.

Final game code pin: **`119496e6a2f1e53b7704712fef8cb81814f1698a`**.
Historical source-pack pin: **`913ea78a3b35d3dfb62d7b76a33598b02107a2e7`**.
Repo license: **MIT**; source art is upstream-credited CC0.
Toolchain: **PVSnesLib 4.5.0** Linux archive, SHA-256 **`b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`**.

Why selected: real original no-chip LoROM action-platformer; Mode 1; 4800px scroll; HDMA parallax; scanline color-math gradient; VRAM page streaming; enemies/sprite streaming/collision; SNESMod music/SFX. First skeleton triggers near start; spike hazards much later.

Diagnostic-only gameplay automation remains limited to:
1. initial state `ST_TITLE -> ST_PLAY`;
2. gameplay `padsCurrent(0) -> KEY_RIGHT`.

Do not modify physics, enemies, renderer, HDMA, streaming, audio, collision, timing or Sodium64 runtime to make it easier. Result is a deterministic benchmark derivation of an open game, not untouched gameplay.

`240pTestSNES` remains useful later for fidelity/PPU validation but was not selected first because default flow is menu/static patterns rather than sustained gameplay.

## SOURCE BUILD HISTORY
### Attempt 1 — `e72566dd...`, run `35119197827` — FAILURE
PVSnesLib checksum, final Gothicvania checkout and both benchmark patches passed. Clean Git mtimes caused high-level FROZEN ART converters to run; first visible error was missing `numpy`.

### Attempt 2 — `c7d60a98...`, run `35119454457` — FAILURE
Refreshing committed generated-output mtimes correctly prevented hero/enemy frozen converters from running. Two deeper causes were exposed:

1. **BUILD SYSTEM:** `make -j` raced incomplete hand-written dependencies. **REJECTED:** parallel build as a valid Gothicvania reproducibility test; upstream documents plain `make`.
2. **SOURCE PACK:** final commit intentionally removed `assets/gothicvania-cemetery-files/`, while ignored `.pic/.pal/.map` products still need it on a clean build.

Upstream `968b61874c5c39e43679b4f3977de73f279cb192` explicitly says the CC0 source pack was removed after feature completion and is **recoverable from Git history if needed**. `913ea78...` is the last feature-complete state before removal. Later `ec9a3d3...` states converter consolidation left the ROM byte-identical.

Audio converter has a host-specific ffmpeg path; tracked `.it` intermediates are retained/freshened instead of modifying audio tooling. `adapt_title.py` likewise expects a host-local Kenney Pixel font; CI recreates that expected input path using a pinned CC0 Kenney font, without editing upstream converter source.

## MEASUREMENT PROOF — reproducible Gothicvania benchmark
Active branch: **`phase1/open-homebrew-workload`**.
Validated source-build HEAD: **`0e5c53846e67c192b75d58f236126a458e8d53b9`**.

Open Homebrew Workload Build run **`35121473665` — SUCCESS**.
Artifact: **`gothicvania-benchmark-source-build`**, ID **`10458190844`**.

Artifact verified after download:
- `gothicvania-benchmark.sfc`: **524,288 bytes** (exactly 512 KiB; allowed upper bound);
- ROM SHA-256: **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**;
- benchmark patch SHA-256: **`c2317550ee3a1654095b462e20553432918e7d6ee85caf30efaf11ba81e3842a`**;
- artifact hashes exactly match their recorded `.sha256` files;
- provenance records final game SHA, historical source-pack SHA, PVSnesLib version/checksum, Kenney font repo/commit/blob and ROM size.

Exact patch inspection confirms only two runtime-source edits:
- `gothicvania/src/main.c`: `ST_TITLE -> ST_PLAY` initial state;
- `gothicvania/src/play.c`: `padsCurrent(0) -> KEY_RIGHT` deterministic input.

No other tracked upstream source/assets were modified by the build. Historical source-art is temporary/untracked build input only.

**VALIDATED:** final Gothicvania workload can be reproduced from explicit pinned provenance on a clean Ubuntu runner while game/runtime logic differs only by the two declared benchmark controls.

**NOT YET PROVEN:** Sodium64 can boot/run this ROM; its ares profile/frame budget; real-N64 performance; exact visual/audio correctness under Sodium64.

Normal Sodium64 `Build and Validate` for the same HEAD: run **`35121473585`**. Normal build + PROFILE build are SUCCESS; Mupen emulator-smoke was still in progress at this checkpoint. This run is not the Gothicvania decision result but must remain green before PR merge.

## RESUME HERE — PROFILE THE OPEN GAME, NO NEW PROFILER
Source reproducibility gate is closed. The next technical batch may now connect **this exact Gothicvania build** to the existing ares profiling/frame-budget lab.

Before editing, reread `master:docs/ROADMAP.md`, `PROFILING.md`, and `VALIDATION.md`, then inspect current `.github/workflows/ares-profile.yml` and existing workload-generation/injection scripts.

Requirements for the next batch:
- reuse the exact existing statistical PC sampler and frame-budget capture; **no new profiling machinery**;
- valid ares mode remains **R4300 JIT + RSP interpreter**;
- frameskip `0`, full-rate APU `21` with JIT invalidation, audio enabled, precision `8`;
- build Gothicvania from the same pinned provenance or consume a same-workflow build step whose ROM hash is checked against expected provenance;
- measure a short deterministic PLAY window long enough to reach early scroll + first skeleton/enemy sprite streaming + SNESMod activity, but before distant spike hazards dominate;
- retain minimum sample-density discipline;
- report profile buckets + complete 60-VI frame-budget windows;
- do not interpret ares wall-clock as real-N64 FPS.

Question: **under this real open game workload, which major R4300 costs dominate, and does the virtual frame budget still show headroom or expose a base-system pressure point?**

After the result: checkpoint evidence first, then decide whether M0 now needs a focused real-N64 milestone package before selecting any M1 architecture. Do not start 65C816 dynarec merely from prior synthetic results.

## Hardware status
**No real-N64 request yet.** Gothicvania profiling is the final cheap representativeness step currently preferred before deciding whether next authority should be a focused M0 hardware session.

## Guardrails
No game-specific emulator modes. No frameskip/APU underclock/audio omission counted as performance. No endless profiler/tooling expansion. No diagnostic code merged merely because it produced knowledge. `master` remains best integrated state. Important rejected explanations survive here.

## Resume protocol
1. Read this file.
2. Verify master at/after `ee86d339...` and branch HEAD `0e5c5384...`.
3. Check final state of normal run `35121473585`.
4. Reread Roadmap/Profiling/Validation and inspect current ares workflow before integrating Gothicvania.
5. Use existing profiler/frame-budget machinery; no new instrumentation unless a specific blocker appears.
6. Maintain batch -> checkpoint cadence.
