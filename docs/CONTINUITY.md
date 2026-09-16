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
Current candidate HEAD: **`89df64192d622bfa12e4bb53e0f41ceab928efe6`** (`m0: pin survivability workload hash`).
Previous real-hardware package HEAD: `26545b209c7657c98ffc22cdd7a954e688ac8c07`.

## Valid ares lab
Isolation run `35113184294`, artifact `10453682432` proved pinned ares RSP JIT is a **LAB LIMITATION**: every RSP-JIT mode collapsed while RSP-interpreter modes progressed. Valid high-density lab is **R4300 JIT + RSP interpreter**.

**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy explanation; accidental OAM wall as primary cause. Old RSP-JIT profiling must not drive architecture.

Valid synthetic run `35114866448`, artifact `10454678803`: idle 60/60; cpu-alu 41/60; wram 47/60; ppu-registers 38/60; dma-vram 16/60; gameplay-balanced 61/60 with 51.5% VI wait. Synthetic results are causal controls, not real-game/N64 authority.

## Gothicvania representative workload
Open workload: `donth77/snes-homebrew:gothicvania`.
Pins: final source `119496e6a2f1e53b7704712fef8cb81814f1698a`; source-art history `913ea78a3b35d3dfb62d7b76a33598b02107a2e7`; PVSnesLib 4.5.0 SHA-256 `b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`; Kenney font commit `9d94d3b50c68036a740115c577598fa1a02723f0`, blob `e6978d7d6f6a91ca8cdd5515e338110d9977fe69`.

Base deterministic benchmark controls: `ST_TITLE -> ST_PLAY`; `padsCurrent(0) -> KEY_RIGHT`. The survivability rerun additionally changes local `playState` health initialization from `PLAYER_HP` to `255`. Enemy/spike collision, HP decrement, hurt state/knockback, SFX, rendering, physics, streaming and audio remain active; only death is made unreachable during the ~7 s measurement. No Sodium64 core code is changed by the survivability control.

Original benchmark SHA (before survivability): `634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`.
Current survivability benchmark SHA: **`5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`**.
Current benchmark patch SHA: **`ab1ec83925571e916be9ae0a3abf3d2bb84b5f9efb1aae9fd2ac608ecc0f0bc9`**.

Source-build hygiene knowledge to preserve:
- **REJECTED:** parallel make/PVSnesLib as root cause of frozen-source failures.
- **REJECTED:** parallax generation itself as a problem.
- **REJECTED:** gfx4snes/PVSnesLib as broken.
- Root cause was checkout-mtime interaction with upstream committed/frozen conversion outputs. Final policy freezes only high-level committed source-of-truth outputs and lets low-level products/companions rebuild.
- Earlier package scratch/checksum-path leaks were packaging-only hygiene and did not change ROM bytes/runtime.

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

`scripts/hw_profile_report.py` validates/extracts; host tests cover canonical/word-swapped saves, incomplete capture, underclock/low-density and RSP context.

## MEASURED — first real-N64 capture
**2026-09-16 / real N64 + SummerCart64.** Exact prior M0 ROM booted, entered Gothicvania, showed `GAME OVER`, then reached solid red. SummerCart recognized `SRAM 256kbit`. User had to power off because reset did not return from the intentional terminal state, but the save had already persisted.

Returned save:
- filename `sodium64-m0-gothicvania.sav`
- size **32768 bytes**
- SHA-256 **`c9862cc3ec821a783e2a79f38f01b4e4fd5377d9f8683a05eb429122a1bdaf2a`**
- canonical big-endian, valid `S64H` v1 complete=1 + valid `S64P`
- settings: frameskip 0, APU clock 21, audio 4, precision 8
- sample interval 65521; **3580** valid samples
- SP DMA busy 0, DMA full 0; raw SP_PC `0x0B80` non-meaningful for this capture
- five frame budgets: **48/60, 49/60, 52/60, 60/60, 60/60**

**VALIDATED / MEASUREMENT PROOF:** real-N64 boot, profiler sampling, completion marker, standard PI SRAM write, SummerCart persistence, save normalization and host decoder all work end-to-end. Gate A evidence materially advanced.

Aggregate first capture: APU JIT 21.54%, APU static 23.16%, DSP/audio 10.84% (APU/audio aggregate **55.53%**); S-CPU **12.99%**; PPU/events **7.04%**; DMA/HDMA **3.83%**; RSP/VRAM semaphore wait **1.20%**; frame/VI wait **19.39%**.

**SUPERSEDED FOR ARCHITECTURE DECISION:** this full five-window aggregate. Video + rising frame budgets prove the guest entered `GAME OVER`; final 60/60 windows are cheaper post-death state, not native-frame gameplay. The first two hardware windows align with stable ares 48/60, which is interesting but insufficient to claim quantitative hardware accuracy.

## VALIDATED / READY — survivability hardware rerun
Candidate HEAD **`89df64192d622bfa12e4bb53e0f41ceab928efe6`** pins the new deterministic guest SHA and contains only the controlled benchmark survivability change described above relative to the prior profiling package path.

CI:
- Open Homebrew Workload Build run **`35145447113` SUCCESS**.
  - `gothicvania-build` job `104960146459` SUCCESS.
  - `hw-profile-package` job `104960440607` SUCCESS.
  - source artifact **`10466504920`**.
  - hardware package artifact **`10467585906`**.
- Build and Validate run **`35145447039` SUCCESS**: normal build, PROFILE build and Mupen emulator smoke all green; update-release correctly skipped on phase branch.

Final survivability package verification:
- artifact ZIP SHA-256 **`db187230e8728c22b5acebbeabd99489af538994c79eece0a6d4f2a054415086`** (matches GitHub artifact digest).
- package contains exactly 11 intended top-level files; no staging directories.
- `sha256sum -c SHA256SUMS.txt` passes every file after independent download/extraction.
- manifest records exact HEAD `89df6419...`, frameskip 0, APU 21, audio 4, precision 8.
- guest SHA **`5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`**.
- wrapped N64 ROM SHA-256 **`7bb79d25168a73a9e539a1ced17c0e4073f3c8fb321ed7552db7a48a64ed217f`**.
- emulator base ROM SHA remains `54039dca813356bd8976aa2761214520ef6460b157ada27e05ff055c126496a9`.
- independent extraction of 512 KiB guest at wrapped-ROM offset `0x104000` rehashes exactly to `5519d51f...ee519`.

**STATUS: VALIDATED / READY FOR ONE REAL-N64 SURVIVABILITY RERUN.** This candidate is not an optimization; it is the controlled repeat needed to remove the known GAME OVER contaminant from M0.

## Immediate next action
Run the exact survivability `.z64` from artifact `10467585906` on real N64/SummerCart64. Do not press controls. Expected sequence: Gothicvania stays in active gameplay for the entire measurement, then solid red. **GAME OVER must not appear before red.** Because the prior session proved SRAM was already persisted even when power-off was required, if reset again cannot return from red, wait several seconds on red before power-off, then recover the new 32 KiB `.sav`.

Decode the returned save using the exact matching ELF/map/reporters from artifact `10467585906`. If all five windows are active gameplay and sample density is sufficient, close representative M0 and choose the first M1 architecture/optimization experiment from real-hardware evidence.

Falsifiers:
- GAME OVER before red -> survivability control failed; inspect death path and do not interpret profile.
- no red / invalid save -> isolate regression before performance interpretation.
- five active gameplay windows + valid capture -> **M0 real-N64 bottleneck map achieved**; choose M1 from hardware.
- Do **not** start M1 dynarec before this representative hardware evidence chooses the first wall.

## Resume protocol
Read this file + Road/Profiling/Validation; verify master/branch/CI state. Resume from survivability candidate `89df6419...`, artifact `10467585906`, ready for the one repeat hardware session. Decode the returned save with the exact package, checkpoint the result, then choose the first M1 experiment from representative real-N64 evidence.