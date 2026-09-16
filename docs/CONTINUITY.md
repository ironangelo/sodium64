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

Final game code pin: **`119496e6a2f1e53b7704712fef8cb81814f1698a`**.
Historical source-pack pin: **`913ea78a3b35d3dfb62d7b76a33598b02107a2e7`** (last feature-complete state before the source-art pack removal).
License: repo **MIT**; graphics adaptation credited upstream to CC0 source pack.
Toolchain: **PVSnesLib 4.5.0** Linux archive, SHA-256 **`b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`**.

Why: real original no-chip LoROM action-platformer; Mode 1; 4800px scroll; HDMA parallax; scanline color-math gradient; VRAM page streaming; enemies/sprite streaming/collision; SNESMod music/SFX. First skeleton triggers near start; spike hazards much later.

Diagnostic-only gameplay automation remains limited to:
1. initial state `ST_TITLE -> ST_PLAY`;
2. gameplay `padsCurrent(0) -> KEY_RIGHT`.

Do not modify physics, enemies, renderer, HDMA, streaming, audio, collision, timing or Sodium64 runtime to make it easier. Describe result as a deterministic benchmark derivation of an open game, not untouched gameplay.

`240pTestSNES` remains useful later for fidelity/PPU validation but was not selected first because default flow is menu/static patterns rather than sustained gameplay.

## SOURCE BUILD HISTORY
### Attempt 1
Branch HEAD: `e72566dd5af1739ef3a1257a1ffb12fe3f985a98`.
Run **`35119197827` — FAILURE**.

Passed: PVSnesLib checksum; Gothicvania SHA checkout; two benchmark patches.
Failure: clean Git mtimes caused upstream **FROZEN ART** converters to run; `adapt_hero.py` / `adapt_enemy.py` hit missing `numpy`.

Initial interpretation was that frozen converters should never run. This was only partly correct.

### Attempt 2
Branch HEAD: **`c7d60a98ea7ebcfa4a22cb78810472c2cc55e7e2`**.
Run **`35119454457` — FAILURE**.

The mtime fix successfully prevented the truly frozen high-level hero/enemy converters from running. The next failure exposed two separate issues:

1. **BUILD SYSTEM:** CI used `make -j`, but Gothicvania's Makefile does not express every `data.asm` dependency. `data.obj` attempted to include `res/level/parallax_tiles.pic` before its generator completed. Upstream documents plain `make`, not parallel make. **REJECTED:** parallel build as a valid reproducibility test.
2. **SOURCE PACK:** `adapt_parallax.py` and `adapt_title.py` need files under `assets/gothicvania-cemetery-files/`, which are absent from final commit `119496e6...`. Their generated `.pic/.pal/.map` outputs are ignored by Git, so a clean clone cannot reproduce them using only the final tree.

**SOURCE FACT:** upstream commit `968b61874c5c39e43679b4f3977de73f279cb192` explicitly removed the original CC0 source-art pack after the game was feature-complete and says it is "recoverable from git history if needed". It also says the local ROM still built because committed intermediate outputs were treated as source of truth and converter mtimes were older.

**SOURCE FACT:** immediately preceding commit `913ea78a3b35d3dfb62d7b76a33598b02107a2e7` contains the source pack. Later commit `ec9a3d30e3643ec6f33581377f0542ed5fdd1a0e` states its converter consolidation leaves the ROM byte-identical.

**SUPPORTED INTERPRETATION:** keep final game code at `119496e6...`, restore only `gothicvania/assets/gothicvania-cemetery-files/` from historical `913ea78...` as temporary build input, exactly following upstream's recovery note. Do not roll gameplay back.

Audio caveat: historical `adapt_sfx.py` hardcodes the author's macOS ffmpeg path. `res/effectssfx.it`, `res/title.it`, and `res/baroque.it` are already tracked outputs; keep those committed audio intermediates newer than their converter scripts rather than patching audio generation. This avoids a third game/tool source modification.

Host Python requirements for the art converters are explicit: `numpy` + Pillow. Install them in CI. Build **sequentially** with plain `make`.

## RESUME HERE — THIRD SOURCE-BUILD EXPERIMENT
Active branch: **`phase1/open-homebrew-workload`**.
Current HEAD before next fix: **`c7d60a98ea7ebcfa4a22cb78810472c2cc55e7e2`**.
Normal branch run associated with this HEAD: `35119454462` (check independently if needed).

Next controlled change to `.github/workflows/open-homebrew-build.yml` only:
- keep final Gothicvania checkout `119496e6...`;
- fetch historical `913ea78...` and restore/copy only `gothicvania/assets/gothicvania-cemetery-files/` into the temporary build tree;
- install `python3-numpy` and `python3-pil` (or equivalent pinned Ubuntu packages);
- keep tracked audio `.it` outputs fresh so `adapt_sfx.py` / MIDI conversion do not rerun;
- remove `-j`; use upstream-documented plain `make`;
- retain exact two-file tracked-diff guard for `main.c` + `play.c` (historical pack may be untracked temporary build input);
- verify ROM size/SHA/provenance and upload artifact.

Question: can final Gothicvania be rebuilt reproducibly on a clean Linux runner when the exact source-art pack upstream says to recover from history is restored, without any gameplay/runtime changes beyond the two benchmark controls?

Decision:
- green -> inspect artifact/provenance, checkpoint reproducibility, then integrate this exact ROM with the existing ares profiler/frame-budget harness;
- red -> inspect only the next concrete build failure; no ares yet.

## Hardware status
**No real-N64 request yet.** Gothicvania remains the final cheap representativeness step before deciding whether next authority should be focused M0 hardware validation.

## Guardrails
No game-specific emulator modes. No frameskip/APU underclock/audio omission counted as performance. No endless profiler/tooling expansion. No diagnostic code merged merely because it produced knowledge. `master` remains best integrated state. Important rejected explanations survive here.

## Resume protocol
1. Read this file.
2. Verify master at/after `ee86d339...`.
3. Inspect branch `phase1/open-homebrew-workload` from HEAD `c7d60a98...` onward.
4. Run the third source-build experiment above; resolve reproducibility before ares profiling.
5. Maintain batch -> checkpoint cadence.
