# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating rule
Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**. Preserve material hypotheses, measurements, rejections, lab limitations, branch/HEAD/run/artifact identity and next action. Continue from repo/artifact evidence, not chat memory.

## Project hierarchy / current gate
1. `master:docs/ROAD_TO_1_0.md` = destination/gates.
2. `master:docs/ROADMAP.md` = route.
3. `master:docs/PROFILING.md` = measurement method/limits.
4. `master:docs/VALIDATION.md` = validation authority.
5. this file = live position.

Current milestone: **M0 / ROADMAP Phase 1 — baseline and bottleneck map**.
Perfect target remains real-N64 native cadence, no required frameskip/frame generation, full-rate APU/audio, high CPU/PPU/DMA/HDMA/timing fidelity, broad compatibility, DSP-1 family, Super FX / Super FX 2 and SA-1. N64-alone first; cartridge assistance only after a quantified gap.

## Stable master
Integrated master: **`ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`**. PR #9 is **MERGED-CONSUMED**. Integrated foundation includes build/validation, statistical R4300 profiler, Mupen smoke, ares GDB lab, synthetic matrix, frame-budget reporting and Road docs.

## Valid ares lab / retained rejections
Isolation run `35113184294`, artifact `10453682432`: R4300 JIT+RSP JIT 0/60; interpreter+interpreter 60/60; R4300 JIT+RSP interpreter 60/60; R4300 interpreter+RSP JIT 0/60.

**LAB LIMITATION:** pinned ares RSP recompiler collapses Sodium64 custom RSP microcode/synchronization. Valid high-density lab is **R4300 JIT + RSP interpreter**.
**REJECTED:** R4300 JIT cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy explanation; accidental OAM wall as primary cause. Bad-run `SP_PC=0x0D90` was the intentional RSP `next_frame` self-halt.

Valid synthetic replacement matrix: run `35114866448`, artifact `10454678803`, frameskip 0 / APU 21 / audio on / precision 8: idle 60/60; cpu-alu 41/60; wram 47/60; ppu-registers 38/60; dma-vram 16/60; gameplay-balanced 61/60 with 51.5% VI wait. **SUPERSEDED:** old `dma-vram ~=98% PPU` reading. Synthetic results are causal controls, not representative real-N64 performance.

## Representative open workload — Gothicvania
Selected `donth77/snes-homebrew:gothicvania`.
Pins: final source `119496e6a2f1e53b7704712fef8cb81814f1698a`; historical CC0 source pack `913ea78a3b35d3dfb62d7b76a33598b02107a2e7`; PVSnesLib 4.5.0 SHA-256 `b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`; Kenney font commit `9d94d3b50c68036a740115c577598fa1a02723f0`, `Kenney Pixel.ttf` blob `e6978d7d6f6a91ca8cdd5515e338110d9977fe69`.

Why: real original no-chip LoROM game; Mode 1; 4800px scrolling; HDMA parallax/color math; VRAM page streaming; enemies/sprites/collision; SNESMod music/SFX.
Diagnostic-only gameplay changes are exactly: initial `ST_TITLE -> ST_PLAY`; `padsCurrent(0) -> KEY_RIGHT`. Do not alter physics/rendering/audio/timing to ease the workload.

### Reproducibility
Attempt 1 run `35119197827`: clean-clone mtimes invoked frozen converters. Attempt 2 run `35119454457`: **REJECTED** parallel `make -j` for upstream hand-written deps and exposed final-tree removal of historical source-art inputs. Upstream `968b618...` explicitly says that pack is recoverable from Git history.

Validated source run **`35121473665` SUCCESS**, artifact **`10458190844`**: ROM 524,288 bytes, SHA-256 **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**; patch SHA-256 `c2317550ee3a1654095b462e20553432918e7d6ee85caf30efaf11ba81e3842a`. Independent run `35122086605`, artifact `10458276218`, produced byte-identical ROM and patch. **VALIDATED / MEASUREMENT PROOF:** deterministic source provenance.

## Stable Gothicvania ares measurement
Run 1 `35122086545`, artifact `10457627853`: 1,312 samples, **48/60**, APU/audio 52.7%, S-CPU 30.4%, PPU+DMA+VRAM sync 16.3%, VI wait 0.5%.
Repeat `35122958028`, artifact `10457874257`: 1,320 samples, **48/60**, APU/audio 52.9%, S-CPU 30.3%, graphics/sync 16.3%, VI wait 0.45%. Normal run `35122957981` also green including Mupen smoke.

Repeat captured RSP running (`SP_STATUS=0`); pinned ares intentionally returns random `SP_PC` while running, so `0x020F` is non-interpretable and **not** a new anomaly. First halted capture `SP_PC=0x0D98` was meaningful; DMA idle in both.

**VALIDATED / MEASUREMENT PROOF:** representative ares result is stable. **SUPPORTED INTERPRETATION:** base-system pressure is not S-CPU alone; audio/APU aggregate is largest in this lab, S-CPU remains a large second, graphics/sync meaningful. `APU static` includes support/I-O/synchronization around the existing JIT; do not call it simple SPC700 interpreter cost. ares proportions are not real-N64 proportions.

**SUPPORTED FALSIFICATION:** do not begin a 65C816 dynarec merely because synthetic CPU controls were heavy. Dynarec remains a strong M1 candidate (~30% lab share + SA-1 leverage), but hardware must decide whether it or APU/DSP/graphics is the first actionable wall.

## LIVE — real-N64 M0 package
Cheap lab representativeness is complete. Temporary Gothicvania ares workflow and repeat trigger were removed (`349b9d862...`, `be77b136...`).

Active branch: **`phase1/open-homebrew-workload`**.
Current implementation HEAD: **`d3fa62dce67d273a02814e8b80ba4470bdc9d650`**.

Implemented diagnostic design:
- `HW_PROFILE=1` automatically implies statistical `PROFILE=1`; normal builds remain unchanged.
- At `profile_init`, hardware build forces Road settings before guest/APU JIT execution: frameskip 0, APU clock 21, audio 4, precision 8.
- No SummerCart runtime-register or USB telemetry access. Prior historical `PROFILE_USB` froze this hardware after SC64 key-register access (`0x1FFF0010`); that path is explicitly **REJECTED** for M0.
- Existing timer sampler detects Sodium64's 60-VI `fps_native` wraps; 2 complete seconds warmup, then reset sampler, then 5 complete 60-VI measurement windows.
- Captures five `fps_display` frame-budget values plus settings/RSP context in an `S64H` header.
- After measurement only, writes raw `S64P` snapshot and then validity header directly through standard N64 PI SRAM (`0x08000000`), using no SC64-specific runtime API.
- Only after SRAM DMA completes, RSP halts, current framebuffer is painted solid red, and diagnostic intentionally freezes. **RED = capture written.**
- Host decoder `scripts/hw_profile_report.py` validates complete/settings/sample density and extracts canonical S64P; `test_hw_profile_report.py` covers canonical and 32-bit word-swapped saves, incomplete captures, underclock and low density.
- `.github/workflows/open-homebrew-build.yml` now rebuilds exact Gothicvania from source, then builds `HW_PROFILE=1`, verifies guest SHA, wraps a self-contained `.z64`, and packages ROM + exact ELF/map + decoder + manifest/test procedure.

Long-running CI started for exact HEAD:
- **Open Homebrew Workload Build run `35125720562` — PENDING at checkpoint.** This run is the authority for the hardware package.
- **Build and Validate run `35125720591` — PENDING at checkpoint.**

Question: does the new HW_PROFILE code compile cleanly and produce a self-contained artifact whose embedded Gothicvania payload is exactly `634fe02f...c17a5fff`?

Decision:
- package CI green -> inspect artifact, hashes, ELF symbols and test plan; then, and only then, request one focused real-N64/SummerCart session from Iron;
- red -> inspect exact failing step/log and fix only that cause;
- after hardware save is returned -> decode S64H/S64P against matching ELF/map and compare real-N64 ranking/frame budget to stable ares result before choosing M1 architecture.

Do **not** start dynarec before this hardware milestone result.

## Hardware authority / prior context
Real N64 + SummerCart64 is available. Historical hardware profiling proved SC64 USB runtime telemetry unsafe on this setup; visual/on-screen profiling worked. Current M0 design deliberately uses only standard N64 PI SRAM and an offline save-file decode.

## Resume protocol
1. Read this file + Road/Profiling/Validation.
2. Verify master and active branch HEAD.
3. Inspect runs `35125720562` and `35125720591` for `d3fa62dc...`.
4. If package succeeds, inspect artifact before asking Iron to test.
5. Maintain batch -> checkpoint cadence.
