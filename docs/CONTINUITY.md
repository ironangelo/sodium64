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
Perfect target: real-N64 native cadence, no required frameskip/frame generation, full-rate APU/audio, high CPU/PPU/DMA/HDMA/timing fidelity, broad compatibility, DSP-1 family, Super FX / Super FX 2 and SA-1. N64-alone first; cartridge assistance only after a quantified hardware-budget gap.

## Stable master
Integrated master: **`ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`**.
PR #9 is **MERGED-CONSUMED**. Integrated foundation includes workflow/baseline/statistical profiler/ares lab/synthetic matrix/Road/frame-budget correlation/gameplay-like workload.

## Valid ares decision laboratory
Isolation run `35113184294`, artifact `10453682432`:

| R4300 | RSP | frames / 60 VI |
| --- | --- | ---: |
| JIT | JIT | 0 |
| interpreter | interpreter | 60 |
| JIT | interpreter | 60 |
| interpreter | JIT | 0 |

**LAB LIMITATION:** pinned ares RSP recompiler collapses Sodium64 custom RSP microcode/synchronization.
**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP stuck in DMA wait; accidental OAM wall primary cause.
`SP_PC=0x0D90` at bad capture maps to intentional RSP `next_frame` self-halt.

Valid high-density lab: **R4300 JIT + RSP interpreter**. Do not debug ares RSP JIT further unless a Road gate requires it.

Valid synthetic/mixed replacement matrix: run `35114866448`, artifact `10454678803`, frameskip 0 / APU 21 / audio on / precision 8:
- idle 60/60;
- cpu-alu 41/60;
- wram 47/60;
- ppu-registers 38/60;
- dma-vram 16/60;
- gameplay-balanced 61/60, 51.5% VI wait, 0.3% VRAM/RSP wait.

**MEASURED:** synthetic `gameplay-balanced` has throughput headroom in valid ares lab. `61/60` is not cadence proof.
**SUPERSEDED:** old `dma-vram ~=98% PPU` interpretation.
**NOT PROVEN by synthetic matrix:** commercial performance, real-N64 FPS, representative S-CPU dominance, dynarec justification.

## Representative workload — Gothicvania
Selected `donth77/snes-homebrew` -> `gothicvania` as the open-game Phase 1 step.

Pins:
- final game source: **`119496e6a2f1e53b7704712fef8cb81814f1698a`**;
- historical CC0 source-pack input: **`913ea78a3b35d3dfb62d7b76a33598b02107a2e7`**;
- PVSnesLib 4.5.0 Linux SHA-256: **`b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`**;
- Kenney font mirror commit: `9d94d3b50c68036a740115c577598fa1a02723f0`, `Kenney Pixel.ttf` blob `e6978d7d6f6a91ca8cdd5515e338110d9977fe69` (CC0).

Why representative: real original no-chip LoROM game; Mode 1; 4800px scrolling; HDMA parallax + per-scanline color math; VRAM page streaming; hero/enemies/sprite streaming/collision; SNESMod looping music/SFX. First skeleton activates near start; spike hazards are much later.

Diagnostic-only gameplay changes:
1. initial `ST_TITLE -> ST_PLAY`;
2. gameplay `padsCurrent(0) -> KEY_RIGHT`.

Do not alter physics, enemies, renderer, HDMA, streaming, audio, collision, timing, or Sodium64 runtime to make workload easier.

### Reproducibility knowledge
Attempt 1 (`e72566dd`, run `35119197827`) failed because clean Git mtimes caused frozen converters to run.
Attempt 2 (`c7d60a98`, run `35119454457`) exposed two deeper issues: **REJECTED** parallel `make -j` for upstream hand-written dependencies, and final source tree intentionally lacks the historical source-art pack.

Upstream `968b618...` explicitly says removed CC0 pack is recoverable from Git history; `913ea78...` is last feature-complete source-pack state. Host-specific audio/font paths are handled as pinned build inputs/intermediates, not gameplay changes.

Validated source build:
- run **`35121473665` SUCCESS**, artifact **`10458190844`**;
- ROM size **524,288 bytes**;
- ROM SHA-256 **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**;
- patch SHA-256 **`c2317550ee3a1654095b462e20553432918e7d6ee85caf30efaf11ba81e3842a`**;
- exact patch contains only the two declared C edits.

Independent repeat source build run **`35122086605` SUCCESS**, artifact `10458276218`: downloaded ROM and patch are **byte-identical** to first artifact.

**VALIDATED / MEASUREMENT PROOF:** benchmark ROM is deterministic and reproducible from explicit pinned provenance.

## MEASURED — first real open-game ares profile
Temporary workflow `.github/workflows/open-homebrew-profile.yml` reuses existing sampler/reporters and is not intended to merge merely because it produced knowledge.

First profile run **`35122086545` SUCCESS**, artifact **`10457627853`**.
Input artifact/hash verified: Gothicvania source artifact `10458190844`, ROM SHA `634fe02f...c17a5fff`.

Verified measurement state:
- **1,312 samples**;
- frameskip 0;
- APU clock 21;
- audio 4;
- precision 8;
- R4300 JIT + RSP interpreter;
- `SP_PC=0x0D98`, SP status 1, DMA busy/full 0/0 — valid non-collapsed RSP state.

R4300 profile:
| major group | share |
| --- | ---: |
| APU static + APU JIT + DSP/audio | **52.7%** |
| S-CPU interpreter | **30.4%** |
| PPU + DMA + VRAM/RSP semaphore wait | **16.3%** |
| frame/VI wait | **0.5%** |

Primary buckets: APU static 35.4%, S-CPU 30.4%, DSP 13.6%, PPU 8.1%, DMA 5.0%, APU JIT 3.7%, VRAM/RSP wait 3.2%, VI wait 0.5%.

Hottest symbols: `cpu_execute` 15.6%, `apu_execute` 11.6%, `read_unk` 7.5%, `io_read8` 4.1%, APU JIT 3.7%, `cpu_io` 3.2%, `skip_sample` 3.2%, `write_vmdatah` 3.0%, `set_nz16` 2.7%, `apu_read8` 2.2%, `read_apuio1` 2.1%, `write_vmdatal` 2.0%, `mix_sample` 2.0%.

Virtual frame budget: **48/60** in last complete 60-VI window = 80.0% of target. Partial at capture: native VI count 51/60, 37 guest frames, queue/frame_count 0. Host wall 6s is not real-N64 FPS.

### Interpretation
**MEASURED:** unlike synthetic `gameplay-balanced`, real open-game Gothicvania exposes material base-system pressure and almost no VI-wait headroom in valid ares lab.

**SUPPORTED INTERPRETATION:** cost ranking is not “S-CPU alone.” Audio/APU-related R4300 work is largest aggregate (~52.7%), S-CPU remains a large second (~30.4%), graphics/DMA/synchronization is meaningful but smaller (~16.3%).

**IMPORTANT:** ares proportions are not real-N64 proportions. “APU static” includes APU support/I-O/synchronization around existing JIT and must not be called simple SPC700 interpreter cost.

**SUPPORTED FALSIFICATION:** a 65C816 dynarec is no longer justified as an automatic sole first architecture merely from prior synthetic evidence. It remains a candidate because 30.4% is substantial, but APU/DSP now has co-equal architecture evidence.

## RESUME HERE — LIVE STABILITY REPEAT
Active branch: **`phase1/open-homebrew-workload`**.
Current HEAD: **`1568a8c6ab2f4d655094fcefe5c40aaba4464844`**.

This HEAD differs from first profile HEAD only by temporary inert file `.github/phase1-gothicvania-repeat-trigger.txt`, created solely to start a new independent workflow run. It changes no Sodium64 source, workload bytes, profiler settings, or report tooling. Remove before merge.

Second Open Homebrew Ares Profile run: **`35122958028` — QUEUED at checkpoint**.
Normal Build and Validate on same inert-trigger HEAD: `35122957981`.

Stability questions:
- does frame budget remain materially below 60, near first 48/60 rather than reverting to synthetic-like headroom?
- does subsystem ordering remain roughly audio/APU > S-CPU > PPU/DMA/sync?
- are frameskip/APU/audio/precision exact and RSP still `0x0D98` / DMA idle?

After repeat:
- inspect artifact, not status alone;
- compare bucket percentages and frame budget quantitatively;
- checkpoint result;
- if stable, cheap M0 representativeness work is complete and next step is a focused **real-N64 M0 milestone package** before selecting M1 architecture.

Do not start 65C816 dynarec yet.

## Hardware status
**No user hardware action requested yet.** Stability repeat is the last cheap lab check before designing the decision-dense hardware package.

## Guardrails
No game-specific emulator modes. No frameskip/APU underclock/audio omission counted as performance. No endless profiler/tooling expansion. No diagnostic code merged merely because it produced knowledge. `master` remains best integrated state. Preserve rejected explanations.

## Resume protocol
1. Read this file.
2. Verify master `ee86d339...`, branch HEAD `1568a8c6...`.
3. Inspect repeat run `35122958028` first.
4. Compare repeat to first profile run `35122086545`.
5. Checkpoint before hardware package/M1 decision.
