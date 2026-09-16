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

1. **BUILD SYSTEM:** `make -j` raced incomplete hand-written dependencies. **REJECTED:** parallel build as valid reproducibility test; upstream documents plain `make`.
2. **SOURCE PACK:** final commit intentionally removed `assets/gothicvania-cemetery-files/`, while ignored `.pic/.pal/.map` products still need it on a clean build.

Upstream `968b61874c5c39e43679b4f3977de73f279cb192` explicitly says the CC0 pack is recoverable from Git history. `913ea78...` is last feature-complete state before removal. Later `ec9a3d3...` says converter consolidation left ROM byte-identical.

Audio converter has a host-specific ffmpeg path; tracked `.it` intermediates are retained/freshened rather than patching audio. `adapt_title.py` expects a host-local Kenney Pixel font; CI recreates that path using pinned CC0 font bytes without changing upstream tool source.

## MEASUREMENT PROOF — reproducible Gothicvania benchmark
Validated source-build HEAD: **`0e5c53846e67c192b75d58f236126a458e8d53b9`**.
Run **`35121473665` — SUCCESS**.
Artifact **`gothicvania-benchmark-source-build`**, ID **`10458190844`**.

Downloaded artifact verification:
- ROM size: **524,288 bytes** (512 KiB exact upper bound);
- ROM SHA-256: **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**;
- patch SHA-256: **`c2317550ee3a1654095b462e20553432918e7d6ee85caf30efaf11ba81e3842a`**;
- recorded hashes match downloaded bytes;
- provenance records final game SHA, source-pack SHA, PVSnesLib version/checksum, Kenney font repo/commit/blob and ROM size;
- exact patch contains only `main.c: ST_TITLE -> ST_PLAY` and `play.c: padsCurrent(0) -> KEY_RIGHT`.

**VALIDATED:** final Gothicvania workload is reproducible from explicit pinned provenance on clean Ubuntu with only the two declared benchmark-control runtime edits.

**NOT YET PROVEN:** Sodium64 can run it correctly; ares bottleneck/frame budget; real-N64 performance; final visual/audio fidelity.

Normal Sodium64 run for source-build HEAD: `35121473585`; normal + PROFILE builds passed, Mupen smoke was still running at prior checkpoint.

## RESUME HERE — LIVE GOTHICVANIA ARES PROFILE
Active branch: **`phase1/open-homebrew-workload`**.
Current HEAD: **`0b6fc0d110428ed6136f56e6d60c0601a011d9e8`**.

Temporary diagnostic workflow added: `.github/workflows/open-homebrew-profile.yml`.
**Do not merge this orchestration merely because it produces knowledge; remove it before merge unless it earns a durable CI role.**

Live run: **Open Homebrew Ares Profile `35122086545` — IN PROGRESS at checkpoint.**
A new source-build validation also launched on the same HEAD: `35122086605`.

The profiling workflow deliberately adds **no new profiler machinery**. It reuses:
- PROFILE=1 Sodium64 build;
- pinned ares `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`;
- demonstrated valid lab mode: R4300 JIT + forced RSP interpreter;
- existing `gdb_rsp_dump.py`, `profile_report.py`, `profile_matrix.py`, `frame_budget_report.py`;
- frameskip 0;
- full-rate APU 21 + lookup invalidation/JIT pointer reset;
- audio setting 4;
- precision setting expected/asserted 8;
- minimum 800 samples, max 60 measured host seconds.

Input is not rebuilt inside the profiler. The workflow downloads exact validated Gothicvania artifact **ID `10458190844`**, verifies ROM SHA-256 **`634fe02f...c17a5fff`**, copies identical bytes under `.smc` extension only to avoid the legacy converter's interactive `.sfc` prompt, then uses existing `rom-converter.py` to produce the N64 test ROM.

Measurement timing: 1 host-second warm-up + 1 host-second settle before clean reset, then bounded sampling. Because player starts near the first skeleton trigger and spikes are far later, this should capture scrolling + enemy/sprite streaming + SNESMod activity without requiring an elaborate input bot.

Question answered by run `35122086545`:
**under the real open-game workload, which R4300 cost buckets dominate, and is the last complete 60-VI frame-budget window at target or below it?**

Decision after run:
- inspect artifact/profile/state, not just status;
- verify >=800 samples and measurement settings exactly;
- distinguish boot/compatibility failure from throughput pressure if red or anomalous;
- checkpoint profile + frame budget + limitations;
- then decide whether M0 now needs a focused real-N64 milestone package before any M1 architecture selection.

Do not start 65C816 dynarec based only on synthetic controls.

## Hardware status
**No real-N64 request yet.** Gothicvania profiling is the final cheap representativeness step currently preferred before deciding whether next authority should be a focused M0 hardware session.

## Guardrails
No game-specific emulator modes. No frameskip/APU underclock/audio omission counted as performance. No endless profiler/tooling expansion. No diagnostic code merged merely because it produced knowledge. `master` remains best integrated state. Important rejected explanations survive here.

## Resume protocol
1. Read this file.
2. Verify master at/after `ee86d339...` and branch HEAD `0b6fc0d1...`.
3. Inspect run `35122086545` and its artifact first; also check source revalidation `35122086605`.
4. Interpret Gothicvania evidence before any architecture decision.
5. Maintain batch -> checkpoint cadence.
