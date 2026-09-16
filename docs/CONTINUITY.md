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
Previous validated hardware-package HEAD: **`26545b209c7657c98ffc22cdd7a954e688ac8c07`**.
Current candidate HEAD: **`0430c8c2be6f6f35119cc299ec0f07eaf3da1150`** (`m0: keep Gothicvania alive through hardware profile`).

## Valid ares lab
Isolation run `35113184294`, artifact `10453682432` proved pinned ares RSP JIT is a **LAB LIMITATION**: every RSP-JIT mode collapsed while RSP-interpreter modes progressed. Valid high-density lab is **R4300 JIT + RSP interpreter**.

**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy explanation; accidental OAM wall as primary cause. Old RSP-JIT profiling must not drive architecture.

Valid synthetic run `35114866448`, artifact `10454678803`: idle 60/60; cpu-alu 41/60; wram 47/60; ppu-registers 38/60; dma-vram 16/60; gameplay-balanced 61/60 with 51.5% VI wait. Synthetic results are causal controls, not real-game/N64 authority.

## Gothicvania representative workload
Open workload: `donth77/snes-homebrew:gothicvania`.
Pins: final source `119496e6a2f1e53b7704712fef8cb81814f1698a`; source-art history `913ea78a3b35d3dfb62d7b76a33598b02107a2e7`; PVSnesLib 4.5.0 SHA-256 `b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`; Kenney font commit `9d94d3b50c68036a740115c577598fa1a02723f0`, blob `e6978d7d6f6a91ca8cdd5515e338110d9977fe69`.

Original deterministic benchmark edits at validated package HEAD `26545b...`: `ST_TITLE -> ST_PLAY` and `padsCurrent(0) -> KEY_RIGHT`; no physics/render/audio/timing simplification.

Validated source run `35121473665`, artifact `10458190844`: 524288-byte ROM SHA-256 **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**. Independent run `35122086605`, artifact `10458276218`, produced byte-identical ROM and patch. **VALIDATED / MEASUREMENT PROOF:** reproducible workload.

Source-build hygiene knowledge to preserve:
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

## Validated first hardware package
Package source HEAD **`26545b209c7657c98ffc22cdd7a954e688ac8c07`**.
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

## MEASURED — first real-N64 execution and persisted capture
**2026-09-16 / real N64 + SummerCart64.** User loaded the exact packaged `sodium64-m0-gothicvania.z64` as an ordinary N64 ROM. N64FlashcartMenu identified it as `sodium64`, game code `NED`, big-endian and **SRAM 256kbit**. The ROM booted, entered Gothicvania, showed `GAME OVER`, then reached the intentional solid-red completion screen.

The user had to power the console off because normal reset did not return from the intentional terminal state. Despite that, the SummerCart had already persisted the save correctly.

Returned SRAM/save:
- filename: `sodium64-m0-gothicvania.sav`
- size: **32768 bytes** (exact SRAM 256 kbit)
- SHA-256: **`c9862cc3ec821a783e2a79f38f01b4e4fd5377d9f8683a05eb429122a1bdaf2a`**
- capture format: canonical big-endian
- `S64H`: valid, version 1, complete=1
- `S64P`: valid
- warmup: 2 s; measured: 5 x 60-VI windows
- settings verified: frameskip **0**, APU clock **21**, audio **4**, precision **8**
- sample interval: 65521; sample count / valid samples: **3580**
- RSP context: SP DMA busy 0, DMA full 0; raw SP_PC `0x0B80`, marked non-meaningful for this capture
- frame budgets: **48/60, 49/60, 52/60, 60/60, 60/60**

**VALIDATED / MEASUREMENT PROOF:** real-N64 boot, profiler sampling, completion marker, standard PI SRAM write, SummerCart persistence, save-format normalization and host-side decoder all work end-to-end. Gate A evidence materially advanced.

Aggregate 3580-sample profile from this capture:
- APU JIT generated: 771 (21.54%)
- APU/SPC700 static: 829 (23.16%)
- DSP/audio: 388 (10.84%)
- combined APU/audio aggregate: **1988 / 3580 = 55.53%**
- S-CPU interpreter: **465 / 3580 = 12.99%**
- PPU/events/frame prep: **252 / 3580 = 7.04%**
- DMA/HDMA: **137 / 3580 = 3.83%**
- RSP/VRAM semaphore wait: **43 / 3580 = 1.20%**
- frame/VI wait: **694 / 3580 = 19.39%**
- input: 1 sample

These aggregate proportions are **NOT architecture-driving yet** because the supplied video and the rising frame budgets prove the workload transitions into `GAME OVER` during the measured interval. In particular, the final 60/60 windows are cheaper post-death state, not proof of native-frame gameplay. The first two windows (48/60, 49/60) align strikingly with the stable ares 48/60 result, but one hardware run is not enough to claim ares is quantitatively hardware-accurate.

**SUPERSEDED FOR ARCHITECTURE DECISION:** the full five-window aggregate from this first hardware capture. It validates transport/profiling, but not a representative all-gameplay subsystem distribution.

## LIVE — controlled survivability rerun
Goal: change only benchmark survivability so all five measured windows remain active gameplay; do not change Sodium64 core or remove collision/hurt/audio work.

Candidate commit **`0430c8c2be6f6f35119cc299ec0f07eaf3da1150`** modifies only the deterministic Gothicvania build patch in `.github/workflows/open-homebrew-build.yml`:
- keeps existing auto-enter gameplay and held Right;
- changes local gameplay `health` initialization from `PLAYER_HP` to `255`;
- enemy/spike collision checks, HP decrement, hurt knockback, SFX, rendering, physics, streaming and audio remain active;
- death is simply unreachable within the ~7 s M0 session.

This deliberately changes the guest ROM, so the previous pinned guest SHA is expected to fail until the new deterministic ROM SHA is measured and pinned. That failure is a controlled checksum gate, not a runtime regression.

Current CI launched from `0430c8c2...`:
- Open Homebrew run **`35145140673`** — in progress at checkpoint.
- Build and Validate run **`35145140752`** — queued/in progress at checkpoint.

## Immediate next action
1. Let run `35145140673` finish source build; obtain the new deterministic Gothicvania SHA. A package-stage failure against old `634fe02f...` is expected and should be interpreted only as the checksum pin doing its job.
2. Pin the new guest SHA in the workflow, rerun CI, require source build + HW_PROFILE compile/link + embedded-payload verification + package checksum self-check to pass.
3. Independently inspect/download the resulting hardware package and verify ZIP/file checksums and embedded guest bytes.
4. Update this continuity checkpoint with final candidate SHA/run/artifact/ROM SHA.
5. Hand Iron only the new `.z64` for one repeat N64 session. Expected behavior: gameplay remains alive for all five windows, then solid red. Return the new 32 KiB `.sav`.
6. Decode with exact matching reporter/ELF/map. If all five windows are gameplay and sample density is sufficient, close representative M0 and choose the first M1 bottleneck from hardware evidence.

Falsifiers/branches:
- Still reaches GAME OVER before red -> survivability control failed; inspect exact damage/death path before using profile.
- No red / invalid save -> new guest change unexpectedly altered test path; isolate before performance interpretation.
- Five active gameplay windows + valid capture -> **M0 real-N64 bottleneck map achieved**; choose M1 from hardware.
- Do **not** start M1 dynarec before this representative hardware evidence chooses the first wall.

## Resume protocol
Read this file + Road/Profiling/Validation; verify master/branch/CI state. Current resume point is candidate `0430c8c2...` running CI after the first real-N64 capture validated the end-to-end profiler but exposed GAME OVER contamination. Finish checksum pin/package validation, hand off the survivability `.z64`, decode the repeat save, checkpoint, then choose the first M1 architecture experiment from representative hardware evidence.