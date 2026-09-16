# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating rule
Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**. Preserve material measurements, hypotheses, rejections, lab limitations, exact SHA/run/artifact identity and next action. Continue from repo/artifact evidence, not chat memory.

## Gate / authority
Current milestone: **M0 / ROADMAP Phase 1 — baseline and bottleneck map**.
Canonical hierarchy: `master:docs/ROAD_TO_1_0.md` -> `ROADMAP.md` -> `PROFILING.md` / `VALIDATION.md` -> this live handoff.
Perfect target remains real-N64 native cadence, no required frameskip/frame generation, full-rate APU/audio, high base-system fidelity, broad compatibility, DSP-1 family, Super FX/2 and SA-1. N64-alone first.

Integrated master: **`ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`**; PR #9 is **MERGED-CONSUMED**.
Active branch: **`phase1/open-homebrew-workload`**.
Current branch HEAD: **`26545b209c7657c98ffc22cdd7a954e688ac8c07`**.

## Valid ares lab
Isolation run `35113184294`, artifact `10453682432` proved pinned ares RSP JIT is a **LAB LIMITATION**: every RSP-JIT mode collapsed while RSP-interpreter modes progressed. Valid high-density lab is **R4300 JIT + RSP interpreter**.

**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy explanation; accidental OAM wall as primary cause. Old RSP-JIT profiling must not drive architecture.

Valid synthetic run `35114866448`, artifact `10454678803`: idle 60/60; cpu-alu 41/60; wram 47/60; ppu-registers 38/60; dma-vram 16/60; gameplay-balanced 61/60 with 51.5% VI wait. Synthetic results are causal controls, not real-game/N64 authority.

## Gothicvania representative workload
Open workload: `donth77/snes-homebrew:gothicvania`.
Pins: final source `119496e6a2f1e53b7704712fef8cb81814f1698a`; source-art history `913ea78a3b35d3dfb62d7b76a33598b02107a2e7`; PVSnesLib 4.5.0 SHA-256 `b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`; Kenney font commit `9d94d3b50c68036a740115c577598fa1a02723f0`, blob `e6978d7d6f6a91ca8cdd5515e338110d9977fe69`.

Original deterministic benchmark edits: `ST_TITLE -> ST_PLAY` and `padsCurrent(0) -> KEY_RIGHT`; no physics/render/audio/timing simplification.

Validated source run `35121473665`, artifact `10458190844`: 524288-byte ROM SHA-256 **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**. Independent run `35122086605`, artifact `10458276218`, produced byte-identical ROM and patch. **VALIDATED / MEASUREMENT PROOF:** reproducible workload.

Source-build hygiene history, preserved so it is not re-investigated:
- **REJECTED:** parallel make/PVSnesLib as root cause of frozen-source failures.
- **REJECTED:** parallax generation itself as a problem.
- **REJECTED:** gfx4snes/PVSnesLib as broken.
- Root cause was checkout-mtime interaction with upstream committed/frozen conversion outputs. Final policy freezes only high-level committed source-of-truth outputs and lets low-level products/companions rebuild.
- Final package scratch/checksum-path leaks were packaging-only hygiene and did not change ROM bytes/runtime.

## Stable representative ares result
Run `35122086545`, artifact `10457627853`: 1312 samples, **48/60**, APU/audio 52.7%, S-CPU 30.4%, graphics/DMA/sync 16.3%, VI wait 0.5%.
Repeat `35122958028`, artifact `10457874257`: 1320 samples, **48/60**, APU/audio 52.9%, S-CPU 30.3%, graphics/sync 16.3%, VI wait 0.45%. Normal run `35122957981` green including Mupen.

Repeat `SP_PC=0x020F` was non-interpretable because pinned ares returns random SP_PC while RSP is running; **not** a new RSP anomaly.

**SUPPORTED INTERPRETATION:** representative lab pressure is not S-CPU alone. APU/audio aggregate is largest, S-CPU a large second, graphics/sync meaningful. `APU static` includes support/I-O/synchronization around the existing JIT. ares proportions are not real-N64 proportions.

**SUPPORTED FALSIFICATION:** do not begin 65C816 dynarec merely because synthetic CPU controls were heavy. Dynarec remains a strong candidate (~30% + SA-1 leverage), but hardware must choose the first M1 wall.

## Real-N64 M0 profiler design
`HW_PROFILE=1` implies `PROFILE=1`; normal builds unchanged. Diagnostic sets frameskip 0, APU clock 21, audio 4 and precision 8 before guest/APU-JIT execution.

Timer sampler observes 60-VI `fps_native` wraps: 2 full seconds warmup, reset sampler, then five complete measured 60-VI windows. `S64H` records five frame-budget windows/settings/sample count/RSP context; canonical `S64P` snapshot is stored at save offset 0x100. After measurement only, cache is written back and snapshot/header are sent through standard N64 PI cartridge SRAM at `0x08000000`. After both writes complete, RSP halts, framebuffer becomes solid red and diagnostic intentionally freezes. **RED = capture written.** Historical SC64 runtime telemetry that froze hardware is **REJECTED**.

`scripts/hw_profile_report.py` validates/extracts; host tests cover canonical/word-swapped saves, incomplete capture, underclock/low-density and RSP context. CI rebuilds exact Gothicvania and packages `.z64` + exact ELF/map/reporters/manifest.

## Validated hardware package
Commit **`26545b209c7657c98ffc22cdd7a954e688ac8c07`**.
- `Build and Validate` run **`35136729624` SUCCESS**.
- Open Homebrew run **`35136729628` SUCCESS**.
- Gothicvania job **`104930862059` SUCCESS**; exact guest SHA **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**.
- Source artifact **`10463845969`**.
- HW package job **`104931318025` SUCCESS**: 29 host tests, HW_PROFILE compile/link, exact workload/embedded guest verification, checksum self-check.
- Final hardware package artifact **`10463541468`**.
- Artifact ZIP SHA-256 **`fa39d94499156a206983ffd4dc3c0771c5a6641c350c34776c5e3843dc3a9a92`**.
- Wrapped N64 ROM SHA-256 **`081c23df1d41101abad373aa1e53b30a34287a049640bd4f349546fd6920425d`**.
- Emulator base ROM SHA-256 `54039dca813356bd8976aa2761214520ef6460b157ada27e05ff055c126496a9`.
- Independent extraction contained exactly 11 intended files, `sha256sum -c` passed, and embedded 512 KiB guest at offset `0x104000` rehashed exactly to `634fe02f...c17a5fff`.

## MEASURED — first real-N64 capture
**2026-09-16 / real N64 + SummerCart64 / exact package above.** N64FlashcartMenu identified the ROM as `sodium64`, game code `NED`, big-endian, **SRAM 256kbit**. The exact ROM booted, entered Gothicvania, later showed `GAME OVER`, then reached the intentional solid-red completion screen.

Returned save: `sodium64-m0-gothicvania.sav`, **32768 bytes**, SHA-256 **`c9862cc3ec821a783e2a79f38f01b4e4fd5377d9f8683a05eb429122a1bdaf2a`**. User had to power off because normal reset did not return from the intentional terminal freeze, but the SRAM still persisted successfully.

Decoded with the exact packaged `hw_profile_report.py`, ELF and map from artifact `10463541468`.

**VALIDATED / MEASUREMENT PROOF — hardware capture transport:**
- save format: canonical big-endian;
- valid complete `S64H` + canonical embedded `S64P`;
- 2 s warmup + 5 s measured;
- **3580 samples** at 65,521 Count ticks, well above 800-sample decision minimum;
- frameskip **0**;
- APU clock **21** (full-rate target);
- audio setting **4**;
- precision **8**;
- queue at capture **1**;
- SP DMA full/busy **0/0**;
- SP was running at capture, therefore `SP_PC=0x00000B80` is explicitly non-interpretable.

Five real-N64 frame-budget windows were **48/60, 49/60, 52/60, 60/60, 60/60**.

Aggregate five-second R4300 profile:
- APU/SPC700 static **23.16%**;
- APU JIT generated **21.54%**;
- DSP/audio **10.84%**;
- S-CPU interpreter **12.99%**;
- PPU/events/frame prep **7.04%**;
- DMA/HDMA **3.83%**;
- RSP/VRAM semaphore wait **1.20%**;
- frame/VI wait **19.39%**;
- input **0.03%**.

Hottest regions: APU JIT generated code 21.54%, `frame_wait` 19.39%, `apu_execute` 10.81%, `apu_read8` 5.47%, `cpu_execute` 5.36%, `apu_write8` 3.94%, `cpu_io` 2.63%.

**SUPPORTED INTERPRETATION:** the profiler itself and SummerCart SRAM transport are now validated on real N64. The first three windows (48/60, 49/60, 52/60) are consistent with active gameplay being below the native-frame target and strikingly close to the ares 48/60 result, but this does not yet validate ares proportions or establish the first M1 wall.

**SUPERSEDED / NOT ARCHITECTURE-DRIVING:** the aggregate five-second subsystem percentages from this first hardware capture must not choose M1 because the video proves `GAME OVER` occurred before completion and the final two windows are 60/60. The 19.39% `frame_wait` and reduced aggregate S-CPU/graphics shares are therefore mixed with a lighter post-death state. This is a workload-segment contamination, not a profiler or Sodium64 failure.

**REJECTED:** SRAM persistence failure, incomplete capture, low sample density, wrong frameskip/APU/audio/precision settings, and standard PI SRAM transport as blockers.

## Immediate next action
Create one controlled repeat package that changes only benchmark survivability while preserving gameplay work. Preferred patch: keep deterministic `KEY_RIGHT`, but raise the benchmark-only initial health enough that enemy/spike damage still executes normally while `GAME OVER` cannot occur during the 7-second warmup+measurement interval. Do not remove enemies, collision, hurt handling, rendering, audio, physics or timing work.

Rebuild/revalidate exact guest + HW package in CI, then run one more focused real-N64 session. Exit condition: five measured windows all remain in active gameplay with a valid `S64H/S64P` capture. Only then use real-hardware subsystem distribution to choose the first M1 architecture experiment.

Do **not** start the 65C816 dynarec yet.

## Resume protocol
Read this file + Road/Roadmap/Profiling/Validation; verify master, active branch/HEAD and CI. Current resume point is: real-N64 profiler/capture transport **VALIDATED**, first frame-budget evidence obtained, but first representative aggregate profile **SUPERSEDED by GAME OVER contamination**. Next technical batch is the single-variable survivability patch + CI package; then one real-N64 repeat decides M1.