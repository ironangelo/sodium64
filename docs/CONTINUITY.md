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
Historical source-pack pin: **`913ea78a3b35d3dfb62d7b76a33598b02107a2e7`** (last feature-complete state before source-art removal).
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

1. **BUILD SYSTEM:** CI incorrectly used `make -j`. Gothicvania's Makefile does not express all `data.asm` dependencies; assembly raced `parallax_tiles.pic`. Upstream documents plain `make`. **REJECTED:** parallel build as valid reproducibility test.
2. **SOURCE PACK:** ignored `.pic/.pal/.map` products still need `adapt_parallax.py` / `adapt_title.py`; final commit no longer contains `assets/gothicvania-cemetery-files/`.

**SOURCE FACT:** upstream `968b61874c5c39e43679b4f3977de73f279cb192` intentionally removed the CC0 source-art pack after feature completion and explicitly says it is **recoverable from Git history if needed**.

**SOURCE FACT:** `913ea78a3b35d3dfb62d7b76a33598b02107a2e7` is the last feature-complete state before pack removal. Later `ec9a3d30e3643ec6f33581377f0542ed5fdd1a0e` says converter consolidation kept the ROM byte-identical.

**SUPPORTED INTERPRETATION:** retain final game code `119496e6...`; restore only the historical CC0 source pack from `913ea78...` as temporary/untracked build input. Do not roll gameplay back.

Audio caveat: `adapt_sfx.py` hardcodes the author's macOS ffmpeg path. Tracked `res/effectssfx.it`, `res/title.it`, and `res/baroque.it` are valid committed intermediates; keep them newer than converter scripts so host-specific audio conversion does not rerun.

Title caveat discovered before attempt 3: `adapt_title.py` hardcodes the author's local `Kenney Pixel.ttf` path. Do not patch or replace title assets with placeholders because that would alter ROM layout. Recreate the expected host path using a pinned Kenney Pixel font instead.

Kenney font provenance for attempt 3:
- official Kenney Fonts pack is CC0;
- mirror repo: `ereborstudios/kenney-fonts`;
- pinned commit: **`9d94d3b50c68036a740115c577598fa1a02723f0`**;
- `Kenney Pixel.ttf` Git blob: **`e6978d7d6f6a91ca8cdd5515e338110d9977fe69`**;
- mirror `License.txt` identifies the package as Kenney and CC0.

## RESUME HERE — THIRD SOURCE-BUILD EXPERIMENT
Active branch: **`phase1/open-homebrew-workload`**.
Current HEAD: **`0e5c53846e67c192b75d58f236126a458e8d53b9`**.

Workflow `.github/workflows/open-homebrew-build.yml` now:
- pins final game code `119496e6...`;
- restores only `gothicvania/assets/gothicvania-cemetery-files/` from historical `913ea78...` into worktree without altering final index;
- installs Ubuntu `python3-numpy` + `python3-pil` for legitimate art generators;
- pins Kenney font repo/commit/blob and recreates the exact absolute font path expected by `adapt_title.py` without modifying upstream source;
- applies only the two C benchmark-control changes;
- refreshes tracked generated intermediates so removed high-level art conversion and host-specific audio conversion do not rerun;
- uses upstream-documented **sequential `make`**, no `-j`;
- requires tracked diff to remain exactly `gothicvania/src/main.c` + `gothicvania/src/play.c` before/after build;
- records ROM SHA256, patch SHA256, final source SHA, historical source-pack SHA, SDK checksum, Kenney font commit/blob and ROM size.

Live CI for this exact HEAD:
- **Open Homebrew Workload Build run `35121473665` — IN PROGRESS at checkpoint.**
- **Build and Validate run `35121473585` — IN PROGRESS at checkpoint.**

Question: can final Gothicvania be rebuilt reproducibly on a clean Linux runner when the exact historical build inputs documented by upstream are restored, while gameplay/runtime code differs only by the two benchmark controls?

Decision:
- green -> inspect artifact/provenance and ROM hash, checkpoint reproducibility, then integrate this exact built ROM with the existing ares profiler/frame-budget harness;
- red -> inspect only the next concrete build failure; no ares yet.

## Hardware status
**No real-N64 request yet.** Gothicvania remains the final cheap representativeness step before deciding whether next authority should be focused M0 hardware validation.

## Guardrails
No game-specific emulator modes. No frameskip/APU underclock/audio omission counted as performance. No endless profiler/tooling expansion. No diagnostic code merged merely because it produced knowledge. `master` remains best integrated state. Important rejected explanations survive here.

## Resume protocol
1. Read this file.
2. Verify master at/after `ee86d339...`.
3. Inspect branch HEAD `0e5c5384...`, run `35121473665`, and normal run `35121473585`.
4. Resolve source-build reproducibility before adding ares profiling.
5. Maintain batch -> checkpoint cadence.
