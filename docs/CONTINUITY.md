# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating rule
Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**. Preserve material measurements, hypotheses, rejections, lab limitations, exact SHA/run/artifact identity and next action. Continue from repo/artifact evidence, not chat memory.

## Gate / authority
Current milestone: **M0 ACHIEVED / entering M1 — faster base core**.
Canonical hierarchy: `master:docs/ROAD_TO_1_0.md` -> `ROADMAP.md` -> `PROFILING.md` / `VALIDATION.md` -> this live handoff.
Perfect target remains real-N64 native cadence, no required frameskip/frame generation, full-rate APU/audio, high base-system fidelity, broad compatibility, DSP-1 family, Super FX/2 and SA-1. N64-alone first.

Integrated master: **`ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`**; PR #9 is **MERGED-CONSUMED**.
Completed measurement branch: **`phase1/open-homebrew-workload`**.
Phase-1 HEAD: **`89df64192d622bfa12e4bb53e0f41ceab928efe6`** (`m0: pin survivability workload hash`).
No open PR exists for the measurement branch. Diagnostic work is not implicitly integrated merely because it produced knowledge.

## Valid ares lab
Isolation run `35113184294`, artifact `10453682432` proved pinned ares RSP JIT is a **LAB LIMITATION**: every RSP-JIT mode collapsed while RSP-interpreter modes progressed. Valid high-density lab is **R4300 JIT + RSP interpreter**.

**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy explanation; accidental OAM wall as primary cause. Old RSP-JIT profiling must not drive architecture.

Valid synthetic run `35114866448`, artifact `10454678803`: idle 60/60; cpu-alu 41/60; wram 47/60; ppu-registers 38/60; dma-vram 16/60; gameplay-balanced 61/60 with 51.5% VI wait. Synthetic results are causal controls, not real-game/N64 authority.

## Gothicvania representative workload
Open workload: `donth77/snes-homebrew:gothicvania`.
Pins: final source `119496e6a2f1e53b7704712fef8cb81814f1698a`; source-art history `913ea78a3b35d3dfb62d7b76a33598b02107a2e7`; PVSnesLib 4.5.0 SHA-256 `b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`; Kenney font commit `9d94d3b50c68036a740115c577598fa1a02723f0`, blob `e6978d7d6f6a91ca8cdd5515e338110d9977fe69`.

Base deterministic controls: `ST_TITLE -> ST_PLAY`; `padsCurrent(0) -> KEY_RIGHT`. Survivability rerun additionally changes local `playState` health initialization from `PLAYER_HP` to `255`. Enemy/spike collision, HP decrement, hurt state/knockback, SFX, rendering, physics, streaming and audio remain active; only death is unreachable during the short M0 window. No Sodium64 core code changed for survivability.

Original benchmark SHA: `634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`.
Survivability benchmark SHA: **`5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`**.
Benchmark patch SHA: **`ab1ec83925571e916be9ae0a3abf3d2bb84b5f9efb1aae9fd2ac608ecc0f0bc9`**.

Source-build hygiene knowledge to preserve:
- **REJECTED:** parallel make/PVSnesLib as root cause of frozen-source failures.
- **REJECTED:** parallax generation itself as a problem.
- **REJECTED:** gfx4snes/PVSnesLib as broken.
- Root cause was checkout-mtime interaction with upstream committed/frozen conversion outputs. Freeze only high-level committed source-of-truth outputs; let low-level products/companions rebuild.
- Package scratch/checksum-path leaks were packaging-only hygiene and did not change ROM/runtime.

## Stable representative ares result
Run `35122086545`, artifact `10457627853`: 1312 samples, **48/60**, APU/audio 52.7%, S-CPU 30.4%, graphics/DMA/sync 16.3%, VI wait 0.5%.
Repeat `35122958028`, artifact `10457874257`: 1320 samples, **48/60**, APU/audio 52.9%, S-CPU 30.3%, graphics/sync 16.3%, VI wait 0.45%. Normal run `35122957981` green including Mupen.

Repeat `SP_PC=0x020F` was non-interpretable because pinned ares returns random SP_PC while RSP is running; **not** a real RSP anomaly.

## Real-N64 M0 profiler design
`HW_PROFILE=1` implies `PROFILE=1`; normal builds unchanged. Diagnostic forces frameskip 0, APU clock 21, audio 4, precision 8 before the workload/APU-JIT measurement.

Timer sampler observes 60-VI `fps_native` wraps: 2 full seconds warmup, reset sampler, then five complete measured 60-VI windows. `S64H` records five frame budgets/settings/sample count/RSP context; canonical `S64P` snapshot is stored at save offset 0x100. After measurement only, cache is written back and snapshot/header are sent through standard N64 PI SRAM at `0x08000000`. Solid red appears only after both writes complete. Historical SummerCart runtime-register telemetry that froze hardware is **REJECTED**.

`scripts/hw_profile_report.py` validates/extracts; host tests cover canonical/word-swapped saves, incomplete capture, underclock/low density and RSP context.

## First real-N64 capture — transport proof, architecture aggregate superseded
Prior exact package booted on real N64/SummerCart64, reached Gothicvania gameplay, then `GAME OVER`, then solid red. Returned save `sodium64-m0-gothicvania.sav`: 32768 bytes, SHA-256 `c9862cc3ec821a783e2a79f38f01b4e4fd5377d9f8683a05eb429122a1bdaf2a`, valid complete `S64H`/`S64P`, 3580 samples, settings correct, frame budgets **48/60, 49/60, 52/60, 60/60, 60/60**.

**VALIDATED / MEASUREMENT PROOF:** real-N64 boot, sampling, completion marker, standard PI SRAM write, SummerCart persistence and host decoder work end-to-end.

**SUPERSEDED FOR ARCHITECTURE DECISION:** aggregate profile from this first run because the final windows were post-death state. Preserve it only as transport/profile validation and evidence that the first active-gameplay windows matched the later baseline.

## M0 CLOSURE — representative real-N64 survivability capture
Exact candidate package:
- HEAD **`89df64192d622bfa12e4bb53e0f41ceab928efe6`**.
- Open Homebrew run **`35145447113` SUCCESS**; source artifact `10466504920`; hardware package artifact **`10467585906`**.
- Build and Validate run **`35145447039` SUCCESS**.
- artifact ZIP SHA-256 `db187230e8728c22b5acebbeabd99489af538994c79eece0a6d4f2a054415086`.
- wrapped N64 ROM SHA-256 `7bb79d25168a73a9e539a1ced17c0e4073f3c8fb321ed7552db7a48a64ed217f`.
- emulator base ROM SHA `54039dca813356bd8976aa2761214520ef6460b157ada27e05ff055c126496a9`.

Real-hardware video confirms active gameplay persists through the measurement and reaches solid red with **no GAME OVER before red**. User reports both hardware runs feel slightly below native cadence, with gameplay only a little slowed and audio slightly choppy/intermittent. Treat this as qualitative hardware observation; exact timing authority is the SRAM capture.

Returned survivability save:
- filename `sodium64-m0-gothicvania-survivability.sav`
- size **32768 bytes**
- SHA-256 **`3316bd99dc26224050153c5a10c167b0e0b520aa9e4b85699b8ab45911f1f395`**
- canonical big-endian; valid `S64H` v1, complete=1; valid embedded `S64P`
- 2 s warmup + 5 measured 60-VI windows
- settings verified: frameskip **0**, APU clock **21**, audio **4**, precision **8**
- sample interval 65521; sample count / valid samples **3581**
- frame queue at capture 0
- SP DMA full/busy 0/0; SP status 0; raw SP_PC 0 and explicitly non-meaningful while RSP running
- frame budgets: **48/60, 49/60, 48/60, 50/60, 50/60**; mean **49.0/60**

Representative real-N64 R4300 sample distribution (3581 samples):
- APU/SPC700 static: **892 / 3581 = 24.91%**
- APU JIT generated: **687 / 3581 = 19.18%**
- DSP/audio: **635 / 3581 = 17.73%**
- combined APU/audio: **2214 / 3581 = 61.83%**
- S-CPU interpreter bucket: **792 / 3581 = 22.12%**
- PPU/events/frame prep: **286 / 3581 = 7.99%**
- DMA/HDMA: **239 / 3581 = 6.67%**
- RSP/VRAM semaphore wait: **47 / 3581 = 1.31%**
- RSP wait: 1 sample; input: 2 samples
- frame/VI wait: **0 samples** in this representative capture

Hottest sampled regions include: APU JIT generated 19.18%, `apu_execute` 11.56%, `cpu_execute` 8.99%, `apu_read8` 6.03%, `skip_sample` 4.05%, `get_pitch` 3.52%, `apu_write8` 2.88%, `load_sample` 2.40%, plus the remaining CPU/DSP/PPU/DMA paths.

**MEASURED / M0 ACHIEVED:** the representative hardware workload is stably throughput-bound around 49 completed SNES frames per 60 VI with no frameskip, full-rate APU and active audio. There is essentially no VI idle headroom. M0 now has both reproducible workload and an authority-level real-N64 bottleneck map.

**SUPPORTED INTERPRETATION:** current M1 priority changes. At 49/60, reaching 60/60 requires roughly **18.3% less total host time per frame** if workload cost scales approximately linearly. APU/audio owns 61.83% of sampled R4300 time, so recovering that gap solely from APU/audio would require about **29.7% reduction of the APU/audio aggregate**. By contrast, S-CPU's 22.12% bucket would require about **82.9% reduction of that entire bucket** to close the same gap alone. Therefore the hardware evidence does **not** support beginning M1 with the 65C816 dynarec as the first attack. Dynarec remains strategically valuable for later base-core work and SA-1 leverage, but it is no longer the first measured wall.

The ares representative result was directionally correct that APU/audio was largest and that the workload was near 48/60, but its proportions differed (about 53% APU/audio, 30% S-CPU). Do not promote ares to hardware authority; use it as the controlled iteration lab, with real N64 as milestone authority.

## M1 first architecture question
**GATE DRIVER / ARCHITECTURE PROOF:** reduce APU/audio scheduling/JIT/memory-access overhead first without lowering APU rate, muting/stretches, frameskip, or dropping DSP work.

The first bounded experiment should target APU JIT block-boundary/dispatch overhead because hardware samples show `apu_execute` alone at 11.56% and current JIT blocks are capped at only 16 guest opcode bytes. Generated block tails spill state and return through the central CPU scheduler; the dispatcher then validates JIT tags before re-entering generated code. This is a plausible large overhead source, but changing block granularity can alter CPU/APU/DSP interleave, so a naive larger `BLOCK_SIZE` is an **experiment**, not a merge-ready optimization.

Experiment falsifier: if increasing/reshaping APU block granularity in the valid ares representative lab does not materially improve frame budget and/or causes audio/timing/profile regressions, reject block-boundary work and move to the next measured APU/DSP hot path (`apu_read8`/`apu_write8` specialization or DSP inner-loop restructuring). Do not turn this into unbounded JIT tooling.

## Immediate next action
1. Preserve the completed M0 branch and hardware artifacts as evidence; do not merge diagnostic code merely because it worked.
2. Update the technical route so M1 begins with the measured APU/audio wall and the 65C816 dynarec moves behind that first proof.
3. Create a temporary M1 branch from the exact measured state for a controlled APU JIT block-boundary experiment.
4. Use the valid ares R4300-JIT + RSP-interpreter representative workload for rapid baseline/change measurement. Compare exact frame budget, samples, APU/audio distribution and any timing/audio symptoms. One variable first.
5. Only request another real-N64 session after a lab candidate demonstrates a meaningful M1 movement and passes lower-level validation.

## Resume protocol
Read this file + Road/Roadmap/Profiling/Validation; verify master/active M1 branch/CI. M0 is closed by save SHA `3316bd99...` from exact artifact `10467585906`: 48/49/48/50/50, 3581 samples, APU/audio 61.83%, S-CPU 22.12%, no VI wait. Resume by executing the bounded APU JIT block-boundary experiment in the valid ares lab, checkpointing the result, then keep/reject it and continue M1 from measured evidence.