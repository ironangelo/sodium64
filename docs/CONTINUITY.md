# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating rule
Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**. Preserve material measurements, hypotheses, rejections, lab limitations, exact SHA/run/artifact identity and next action. Continue from repo/artifact evidence, not chat memory.

## Gate / authority
Current milestone: **M0 / ROADMAP Phase 1 — baseline and bottleneck map**.
Canonical hierarchy: `master:docs/ROAD_TO_1_0.md` -> `ROADMAP.md` -> `PROFILING.md` / `VALIDATION.md` -> this live handoff.
Perfect target remains real-N64 native cadence, no required frameskip/frame generation, full-rate APU/audio, high base-system fidelity, broad compatibility, DSP-1 family, Super FX/2 and SA-1. N64-alone first.

Integrated master: **`ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`**; PR #9 is **MERGED-CONSUMED**.

## Valid ares lab
Isolation run `35113184294`, artifact `10453682432` proved pinned ares RSP JIT is a **LAB LIMITATION**: every RSP-JIT mode collapsed while RSP-interpreter modes progressed. Valid high-density lab is **R4300 JIT + RSP interpreter**.

**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy explanation; accidental OAM wall as primary cause. Old RSP-JIT profiling must not drive architecture.

Valid synthetic run `35114866448`, artifact `10454678803`: idle 60/60; cpu-alu 41/60; wram 47/60; ppu-registers 38/60; dma-vram 16/60; gameplay-balanced 61/60 with 51.5% VI wait. Synthetic results are causal controls, not real-game/N64 authority.

## Gothicvania representative workload
Open workload: `donth77/snes-homebrew:gothicvania`.
Pins: final source `119496e6a2f1e53b7704712fef8cb81814f1698a`; source-art history `913ea78a3b35d3dfb62d7b76a33598b02107a2e7`; PVSnesLib 4.5.0 SHA-256 `b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`; Kenney font commit `9d94d3b50c68036a740115c577598fa1a02723f0`, blob `e6978d7d6f6a91ca8cdd5515e338110d9977fe69`.

Diagnostic-only game edits: `ST_TITLE -> ST_PLAY` and `padsCurrent(0) -> KEY_RIGHT`; no physics/render/audio/timing simplification.

Source-build history preserved: first clean-clone attempt exposed frozen-converter mtimes; second exposed **REJECTED** parallel `make -j` plus intentionally removed source-art inputs. Upstream explicitly says pack is recoverable from history.

Validated source run `35121473665`, artifact `10458190844`: 524288-byte ROM SHA-256 **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**. Independent run `35122086605`, artifact `10458276218`, produced byte-identical ROM and patch. **VALIDATED / MEASUREMENT PROOF:** reproducible workload.

## Stable representative ares result
Run `35122086545`, artifact `10457627853`: 1312 samples, **48/60**, APU/audio 52.7%, S-CPU 30.4%, graphics/DMA/sync 16.3%, VI wait 0.5%.
Repeat `35122958028`, artifact `10457874257`: 1320 samples, **48/60**, APU/audio 52.9%, S-CPU 30.3%, graphics/sync 16.3%, VI wait 0.45%. Normal run `35122957981` green including Mupen.

Repeat `SP_PC=0x020F` was non-interpretable because pinned ares returns random SP_PC while RSP is running; **not** a new RSP anomaly.

**SUPPORTED INTERPRETATION:** representative lab pressure is not S-CPU alone. APU/audio aggregate is largest, S-CPU a large second, graphics/sync meaningful. `APU static` includes support/I-O/synchronization around the existing JIT. ares proportions are not real-N64 proportions.

**SUPPORTED FALSIFICATION:** do not begin 65C816 dynarec merely because synthetic CPU controls were heavy. Dynarec remains a strong candidate (~30% + SA-1 leverage), but hardware must choose the first M1 wall.

## LIVE — real-N64 M0 package
Temporary ares workflow/repeat trigger were removed. Active branch: **`phase1/open-homebrew-workload`**.
Current HEAD: **`2cd2245acfecf8cf051eeb3a8d2851716015d453`**.

Hardware design:
- `HW_PROFILE=1` implies current statistical `PROFILE=1`; normal builds unchanged.
- Before guest/APU-JIT execution, diagnostic sets frameskip 0, APU clock 21, audio 4, precision 8.
- No flashcart-specific runtime register or USB telemetry access. Historical SC64 runtime telemetry that froze hardware is **REJECTED**.
- Timer sampler observes 60-VI `fps_native` wraps: 2 full seconds warmup, reset sampler, then five complete measured 60-VI windows.
- `S64H` header records five `fps_display` budgets/settings/sample count/RSP context; canonical `S64P` snapshot stored at save offset 0x100.
- After measurement only, cache is written back and snapshot/header are sent through standard N64 PI cartridge SRAM at `0x08000000`.
- After both writes complete, RSP halts, framebuffer becomes solid red and diagnostic intentionally freezes. **RED = capture written.**
- `scripts/hw_profile_report.py` validates/extracts; six host tests cover canonical/word-swapped saves, incomplete capture, underclock and low density.
- source-builder CI rebuilds exact Gothicvania and packages a self-contained `.z64` plus exact ELF/map/decoder/manifest.

### First HW package build
HEAD `d3fa62dce67d273a02814e8b80ba4470bdc9d650`:
- `Build and Validate` run **`35125720591` SUCCESS**, including normal, PROFILE and Mupen smoke: no normal-path regression.
- Open Homebrew run **`35125720562`** rebuilt Gothicvania successfully; `hw-profile-package` failed only at link.
- All 29 host tests passed.
- `profile.S` assembled successfully, including new header/cache/PI/red-screen paths.
- Link error: undefined external `fps_native` from `profile.o`.

**CAUSE:** `fps_native` already exists in `main.S` but upstream had never exported it.
**REJECTED:** hardware-profiler assembly syntax, PI path and decoder as cause of this red.
Controlled fix `2cd2245a...`: add only `.globl fps_native`; no counter logic changed.

Retry runs:
- **Open Homebrew Workload Build `35126221276` — IN PROGRESS at checkpoint.**
- **Build and Validate `35126221380` — IN PROGRESS at checkpoint.**

Question: does the single symbol export resolve the sole link failure and produce a package with exact embedded guest SHA `634fe02f...c17a5fff`?

Decision: green -> inspect artifact/hashes/ELF/procedure, then request one focused real-N64 session; red -> inspect the next concrete failure only. Do **not** start M1 dynarec before hardware evidence.

## Resume protocol
Read this file + Road/Profiling/Validation; inspect runs `35126221276` and `35126221380`; verify artifact before asking Iron to test; checkpoint after material result.
