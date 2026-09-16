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

Diagnostic-only game edits: `ST_TITLE -> ST_PLAY` and `padsCurrent(0) -> KEY_RIGHT`; no physics/render/audio/timing simplification.

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
`HW_PROFILE=1` implies `PROFILE=1`; normal builds unchanged.
Before guest/APU-JIT execution, diagnostic sets frameskip 0, APU clock 21, audio 4, precision 8.
No flashcart-specific runtime register or USB telemetry access. Historical SC64 runtime telemetry that froze hardware is **REJECTED**.

Timer sampler observes 60-VI `fps_native` wraps: 2 full seconds warmup, reset sampler, then five complete measured 60-VI windows. `S64H` records five frame-budget windows/settings/sample count/RSP context; canonical `S64P` snapshot is stored at save offset 0x100. After measurement only, cache is written back and snapshot/header are sent through standard N64 PI cartridge SRAM at `0x08000000`. After both writes complete, RSP halts, framebuffer becomes solid red and diagnostic intentionally freezes. **RED = capture written.**

`scripts/hw_profile_report.py` validates/extracts; host tests cover canonical/word-swapped saves, incomplete capture, underclock/low-density and RSP context. CI rebuilds exact Gothicvania and packages `.z64` + exact ELF/map/reporters/manifest.

## Validated hardware package
Final commit **`26545b209c7657c98ffc22cdd7a954e688ac8c07`**.
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

## LIVE — first real-N64 execution
**2026-09-16 / real N64 + SummerCart64.** User loaded the exact packaged `sodium64-m0-gothicvania.z64` as an ordinary N64 ROM. N64FlashcartMenu identified the ROM as `sodium64`, game code `NED`, big-endian and **SRAM 256kbit**, so the intended standard SRAM transport is recognized by the cart/menu before launch.

**MEASURED / IMPLEMENTED OBSERVATION:** the exact M0 ROM boots on real N64, enters Gothicvania gameplay, and reaches the intentional solid-red terminal screen. The supplied video visibly shows: menu load -> Gothicvania gameplay -> `GAME OVER` -> solid red. Therefore the hardware-only boot path and completion-to-red path work on real N64; the red state is intentional, not a crash.

**IMPORTANT OPEN QUESTION:** the video also shows `GAME OVER` before the red completion screen. Until the returned SRAM is decoded, do **not** assume all five measured windows represent active gameplay. Some measurement time may include death/game-over state. This is a potential workload-representativeness issue, not evidence of profiler failure. Decode the save first; if window timing/profile is contaminated, patch the deterministic input/workload to survive the whole measurement interval and rerun one focused hardware session.

**UNKNOWN pending save:** whether the SRAM payload persisted to SD; whether `S64H`/`S64P` are valid; exact five frame-budget values; sample density; real-N64 subsystem distribution. Red proves the runtime reached post-write completion logic, but does not by itself prove the menu persisted a valid save file.

## Immediate next action
1. From the solid red state, wait a few seconds and return to the SummerCart menu via the normal reset/menu flow; do not power off first.
2. Recover the `.sav` associated with `sodium64-m0-gothicvania.z64` (expected SRAM size: 256 kbit / 32 KiB) and return it unchanged.
3. Decode with the exact packaged `hw_profile_report.py` + matching ELF/map from artifact `10463541468`.
4. Validate `S64H`/`S64P`, settings, five frame windows and sample density; classify the real-N64 profile.
5. Check whether the `GAME OVER` timing contaminates the measured interval. If not, use hardware authority to choose the first M1 architecture experiment. If yes, fix only the workload survivability and repeat the same hardware gate before choosing M1.

Falsifiers/branches:
- Valid save/profile and representative windows -> **M0 real-N64 measurement achieved**; choose first M1 wall from hardware evidence.
- Valid save/profile but game-over contaminated windows -> measurement transport **VALIDATED**, workload segment **SUPERSEDED**; patch workload and rerun.
- Red but missing/invalid save -> isolate SummerCart SRAM persistence/transport; performance remains unknown.
- Do **not** start M1 dynarec before representative real-hardware M0 evidence chooses the first wall.

## Resume protocol
Read this file + Road/Profiling/Validation; verify master/branch/CI state. Current resume point is the first real-N64 boot/completion having succeeded. Next evidence is the returned `.sav`; decode it with the exact packaged reporter/ELF/map, determine whether the game-over state contaminated the five windows, checkpoint, then choose or defer the first M1 architecture experiment accordingly.
