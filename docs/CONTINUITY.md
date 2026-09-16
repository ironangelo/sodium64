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

Upstream `968b618...` explicitly says the removed CC0 pack is recoverable from Git history; `913ea78...` is last feature-complete source-pack state. Host-specific audio/font paths are handled as pinned build inputs/intermediates, not gameplay changes.

Validated source build:
- run **`35121473665` SUCCESS**, artifact **`10458190844`**;
- ROM size **524,288 bytes**;
- ROM SHA-256 **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**;
- patch SHA-256 **`c2317550ee3a1654095b462e20553432918e7d6ee85caf30efaf11ba81e3842a`**;
- exact patch contains only the two declared C edits.

Independent repeat source build run **`35122086605` SUCCESS**, artifact `10458276218`: downloaded ROM and patch are **byte-identical** to first artifact.

**VALIDATED / MEASUREMENT PROOF:** benchmark ROM is deterministic and reproducible from explicit pinned provenance.

## MEASURED — first real open-game ares profile
Active branch: **`phase1/open-homebrew-workload`**.
Current HEAD: **`0b6fc0d110428ed6136f56e6d60c0601a011d9e8`**.
Temporary workflow: `.github/workflows/open-homebrew-profile.yml`; remove before merge unless it earns durable CI value.

Run **`35122086545` — SUCCESS**.
Artifact **`sodium64-open-homebrew-ares-profile`**, ID **`10457627853`**.
Input artifact/hash verified inside workflow before conversion: source artifact `10458190844`, SNES ROM SHA `634fe02f...c17a5fff`.

Measurement conditions verified in captured state:
- samples: **1,312** (>=800 target);
- frameskip `0`;
- APU clock `21`;
- audio setting `4`;
- precision `8`;
- R4300 JIT + RSP interpreter;
- RSP `SP_PC=0x0D98`, `SP_STATUS=1`, DMA busy/full = `0/0` — same non-collapsed end-of-frame state as valid isolation mode.

### R4300 profile
| major group | share |
| --- | ---: |
| APU static + APU JIT + DSP/audio | **52.7%** |
| S-CPU interpreter | **30.4%** |
| PPU + DMA + VRAM/RSP semaphore wait | **16.3%** |
| frame/VI wait | **0.5%** |

Exact primary buckets:
- APU/SPC700 static **35.4%** (464/1312);
- S-CPU interpreter **30.4%** (399/1312);
- DSP/audio **13.6%** (178/1312);
- PPU **8.1%** (106/1312);
- DMA/HDMA **5.0%** (66/1312);
- APU JIT **3.7%** (49/1312);
- VRAM/RSP wait **3.2%** (42/1312);
- VI wait **0.5%** (6/1312).

Hottest symbols include `cpu_execute` 15.6%, `apu_execute` 11.6%, `read_unk` 7.5%, `io_read8` 4.1%, APU JIT 3.7%, `cpu_io` 3.2%, `skip_sample` 3.2%, `write_vmdatah` 3.0%, `set_nz16` 2.7%, `apu_read8` 2.2%, `read_apuio1` 2.1%, `write_vmdatal` 2.0%, `mix_sample` 2.0%.

### Virtual frame budget
Last complete 60-VI window: **48/60 = 80.0% of target**, below virtual target.
Partial window at capture: `fps_native=51`, `fps_emulate=37`, queue/frame_count `0`.
Host measured wall time was 6s only to collect samples and is **not real-N64 FPS**.

### Interpretation
**MEASURED:** unlike synthetic `gameplay-balanced`, this real open-game workload exposes material base-system pressure in the valid ares lab and has almost no VI-wait headroom.

**SUPPORTED INTERPRETATION:** the cost ranking is not “S-CPU alone.” Audio/APU-related R4300 work is the largest aggregate (~52.7%), S-CPU is still a large second (~30.4%), and graphics/DMA/synchronization is meaningful but smaller (~16.3%).

**IMPORTANT:** this does **not** prove ares ratios equal real-N64 ratios, nor does it choose M1 architecture yet. In particular, “APU static” includes APU support/I-O/synchronization code around the existing JIT and should not be simplistically described as an SPC700 interpreter cost.

**SUPPORTED FALSIFICATION:** prior leading idea that a 65C816 dynarec is obviously the sole/automatic first answer is not supported by this representative profile. It remains a candidate because 30.4% S-CPU is substantial, but APU/DSP paths must now be treated as co-equal architecture evidence.

## RESUME HERE — REPEAT REPRESENTATIVE PROFILE BEFORE HARDWARE DECISION
Before moving to hardware or choosing M1, repeat the exact same Gothicvania profile once at the same SHA/artifact/settings to test statistical/frame-budget stability.

Expected stability question:
- does frame budget remain materially below 60 (near the first 48/60, not necessarily identical)?
- does ordering remain roughly audio/APU > S-CPU > PPU/DMA/sync?
- do measurement settings remain exact and RSP stay in valid `0x0D98`/DMA-idle state?

If repeat is consistent, checkpoint it as the end of cheap M0 representativeness work and design a focused **real-N64 M0 milestone package** to distinguish whether emulator-lab proportions survive hardware and to quantify actual native frame budget before selecting M1 architecture.

Do not start 65C816 dynarec yet.

## Hardware status
**No user hardware action requested yet.** One exact repeat of the representative lab result is cheaper and will make the eventual hardware session more decision-dense.

## Guardrails
No game-specific emulator modes. No frameskip/APU underclock/audio omission counted as performance. No endless profiler/tooling expansion. No diagnostic code merged merely because it produced knowledge. `master` remains best integrated state. Preserve rejected explanations.

## Resume protocol
1. Read this file.
2. Verify master `ee86d339...`, branch HEAD `0b6fc0d1...`.
3. Repeat run `35122086545` or equivalent exact same workflow/inputs.
4. Compare frame budget, subsystem ordering and settings/state.
5. Checkpoint result before designing hardware package or M1 work.
