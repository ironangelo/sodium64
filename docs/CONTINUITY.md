# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating protocol
Authority: **current Iron instruction > repo/artifact evidence > canonical docs > continuity > chats/memory/inference**. `master` is integrated truth; phase branches are candidates only.

Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**. Continuity is a live scientific log: checkpoint every material result, changed hypothesis, falsification, risk, lab limitation, meaningful CI/artifact result, branch/HEAD transition or next-action change before advancing. For long experiments record exact SHA/run/question/possible readings before leaving them running.

Iron delegates technical direction toward Road to 1.0 to the assistant. Choose architecture, experiments, implementation, profiling, Git/CI and validation without pushing low-level choices to Iron unless they change scope, hardware requirements, material risk or the target.

Transparency in chat: expose hypothesis, evidence, what it demonstrates / does not demonstrate, rejections, next controlled change, expected result and falsifier. Do not expose private chain-of-thought verbatim.

## Target / gate
Current milestone: **M0 ACHIEVED / M1 — faster base core, APU/audio first**.

Perfect target: real N64 with correct native cadence; one required SNES frame per corresponding native frame; no required frameskip/frame generation; full-rate SPC700/APU and correct audio; high CPU/PPU/DMA/HDMA/timing fidelity; broad compatibility; no per-game modes; DSP-1 family, SuperFX/2 and SA-1. N64-alone first; cartridge assistance only after a quantified N64 ceiling.

Integrated `master`: **`ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`**.
Completed M0 branch: `phase1/open-homebrew-workload`; representative HEAD **`89df64192d622bfa12e4bb53e0f41ceab928efe6`**.
Active M1 branch: **`phase2/apu-audio-first`**.
M1 baseline: **`c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`** (`BLOCK_SIZE=16`).
Current M1 HEAD: **`a758629014d0ecada6358c57eaf77c60afc80cad`** (`BLOCK_SIZE=32`, controlled candidate).
Open PRs: none at last checkpoint.

**DOC DRIFT / TODO:** `master:docs/ROAD_TO_1_0.md` and `master:docs/ROADMAP.md` still contain older pre-M0 / dynarec-first framing. Repair after the current controlled APU experiment materially resolves; do not weaken the 1.0 target.

## Ares laboratory authority
Isolation run **`35113184294`**, artifact **`10453682432`** proved pinned ares RSP JIT is a **LAB LIMITATION**: RSP-JIT modes collapse while RSP-interpreter modes progress. Valid high-density lab is **R4300 JIT + RSP interpreter**.

**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy explanation; accidental OAM wall as primary cause. Old RSP-JIT profiles must not drive architecture. `SP_PC=0x020F` while RSP runs is non-interpretable in this lab.

Synthetic control run **`35114866448`**, artifact **`10454678803`**: idle60/60; cpu-alu41/60; wram47/60; ppu-registers38/60; dma-vram16/60; gameplay-balanced61/60 with51.5% VI wait. Synthetic workloads are causal controls, not real-game/N64 authority.

## Representative workload — Gothicvania
Open workload `donth77/snes-homebrew:gothicvania`; final source pin `119496e6a2f1e53b7704712fef8cb81814f1698a`.
Survivability ROM SHA-256 **`5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`**; patch SHA-256 **`ab1ec83925571e916be9ae0a3abf3d2bb84b5f9efb1aae9fd2ac608ecc0f0bc9`**.
Deterministic controls: `ST_TITLE -> ST_PLAY`, `padsCurrent(0) -> KEY_RIGHT`; survivability initializes local health255 only so death is unreachable during short capture. Collisions, damage path, SFX, rendering, physics, streaming and audio remain active. Sodium64 core is unchanged by survivability.

Source-build hygiene: **REJECTED** parallel make/PVSnesLib, parallax generation, and broken gfx4snes as root causes. Actual failure was checkout-mtime interaction with committed/frozen conversion products; freeze high-level source-of-truth outputs only and rebuild low-level products.

## M0 real-N64 closure
Exact representative HEAD **`89df64192d622bfa12e4bb53e0f41ceab928efe6`**. Open Homebrew run **`35145447113` SUCCESS**, source artifact `10466504920`, hardware package **`10467585906`**; Build and Validate **`35145447039` SUCCESS**.

Returned real-N64 save SHA-256 **`3316bd99dc26224050153c5a10c167b0e0b520aa9e4b85699b8ab45911f1f395`**, 32768B, complete `S64H/S64P`, frameskip0, APU clock21, audio4, precision8, 3581 valid samples, queue0, SP DMA full/busy0/0. Complete windows **48/60,49/60,48/60,50/60,50/60**, mean **49.0/60**. Video shows active gameplay through measurement with no GAME OVER before completion marker.

Real-N64 split: APU static24.91%; JIT19.18%; DSP/audio17.73%; **combined APU/audio61.83%**; S-CPU22.12%; PPU7.99%; DMA6.67%; RSP/VRAM wait1.31%; VI wait0. Hot: generated JIT19.18, `apu_execute`11.56, `cpu_execute`8.99, `apu_read8`6.03, `skip_sample`4.05, `get_pitch`3.52, `apu_write8`2.88, `load_sample`2.40.

**MEASURED / M0 ACHIEVED:** representative N64 is throughput-bound near49 frames/60VI with no frameskip, full-rate APU, active audio and essentially no VI headroom.

**SUPPORTED:** 49->60 requires ~18.3% less total host time/frame if approximately linear. Closing only from APU/audio61.83% requires ~29.7% aggregate reduction; closing only from S-CPU22.12% requires ~82.9% reduction of that bucket. Hardware evidence rejects 65C816 dynarec as the **first** M1 attack; dynarec remains valuable later/SA-1.

Earlier real-N64 save SHA `c9862cc...` is **SUPERSEDED FOR ARCHITECTURE DECISION** due post-GAME OVER later windows; transport proof only.

## M1 baseline — 16-byte APU JIT blocks
Baseline SHA **`c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`**. Build/Validate **`35148379354` SUCCESS**; ares **`35148379400` SUCCESS**; artifact **`10467972587`**, digest `5471854958404c63bba8ee70ae5ead236f02b220881a4b8dfeaee60cdcd559a4`.

Exact workload/settings as above; frameskip0/APU21/audio4/precision8; valid ares mode. **2000 samples**. Complete virtual budget **44/60**. APU static36.60 + JIT3.30 + DSP14.50 = **54.40%**; S-CPU30.85; PPU7.45; DMA4.40; RSPwait2.55; VI0.35. `apu_execute`13.10; `cpu_execute`15.85; `apu_read8`2.90. Local comparison baseline only; real N64 remains authority.

## M1 experiment 1 — confounded 32-byte SHA
SHA **`3b39523c637ac5d076ddfb3714c6023e8d1106f4`** produced repeated **48/60** but changed `BLOCK_SIZE` plus license text and runtime layout (`TEXREC_OFS +0x8->+0x4`, `PRIO_CHECKS +0x4->+0x8`). **SUPERSEDED AS CAUSAL CANDIDATE.** Do not merge/hardware-test it for the optimization claim.

## M1 experiment 1b — clean 32-byte candidate
Active HEAD **`a758629014d0ecada6358c57eaf77c60afc80cad`** restores exact baseline `src/defines.h` except `BLOCK_SIZE 16 -> 32`. Direct compare: one file, **1 addition / 1 deletion**. Known source confound removed.

CI: Build and Validate **`35174886449` SUCCESS**; Open Homebrew Ares Profile run **`35174886403`**.

### Clean run A — attempt 1
Artifact **`10477834229`**, digest **`faf8ec269072824613d9b9297c0f700cfd418ad6883f69097907c48c56b004b0`**.
**MEASURED:** complete virtual budget **48/60**, 957 samples. Runtime frameskip0/APU21/audio4/precision8/queue0/SP DMA0/0. APU static33.33 + JIT5.64 + DSP12.02 = **50.99%**; S-CPU30.93; PPU9.61; DMA5.54; RSPwait2.51; VI0.42. `apu_execute`11.39; `cpu_execute`15.15.

### Clean run B — same-SHA attempt 2
Direct rerun of the same workflow/job with **no source change**, same HEAD `a758629...`. Attempt-2 ares job **`105062197629` SUCCESS**. New artifact **`10478782129`**, digest **`f607a5f0d6aa19b1fc42206c5a7aa93c6ee3983a8895630aaf5a1ab4c679c33d`**; exact Gothicvania ROM SHA remains `5519d51...`.

**MEASURED:** complete virtual budget **48/60** again; 1175 valid samples. Runtime frameskip0/APU21/audio4/precision8/queue0/SP DMA0/0; partial window40/60 with29 guest frames. APU static **35.83%**, JIT **4.43%**, DSP **12.43%** => combined APU/audio **52.69%**; S-CPU **28.77%**; PPU **9.19%**; DMA **6.55%**; RSP/VRAM wait **2.47%**; VI wait **0.34%**. `apu_execute` **12.77%**, `cpu_execute` **13.28%**, `apu_read8`1.70%, `apu_write8`1.19%.

**MEASURED / LOCALLY REPRODUCED:** clean one-variable 32-byte candidate measures **48/60 in two independent runs** (957 and1175 samples) versus paired baseline **44/60**. The stable frame-budget separation is stronger than fluctuating subsystem percentages. No third throughput repeat is justified now; the main uncertainty has moved from performance reproducibility to timing correctness.

**CANDIDATE, NOT VALIDATED:** `BLOCK_SIZE=32` is a locally reproduced performance candidate. It is not yet mergeable and does not establish real-N64 improvement or audio/SPC700 correctness.

## BLOCK_SIZE=32 semantic/timing review
**SUPPORTED / lower risk:** `compile_block` uses linear limit `PC + BLOCK_SIZE`; SPC700 branches/jumps/calls terminate through `finish_block` / PC handling, so 32 does not simply compile through control-flow boundaries.

**SUPPORTED / lower risk:** JIT invalidation tags use 64-byte APU-memory regions (`address >> 6`) and cached blocks check start/end tags. A 32-byte linear block is <64B, so it can intersect at most two tag regions and the extrema cover both. Self-modifying invalidation concern is therefore bounded for 32, not broadly validated.

**OPEN QUESTION / MATERIAL CORRECTNESS RISK:** `apu_execute` decides whether DSP work is due **before** entering the JIT block. Generated blocks accumulate SPC700 cycles and only at `finish_block` return through `cpu_execute`, which gates APU/PPU scheduling by cycle counters. Doubling maximum block length can increase CPU↔APU/DSP scheduler latency. `dsp_sample` advances the DSP schedule by `DSP_SAMPLE`; therefore a throughput gain must not be accepted if it results from materially coarser DSP/APU interleave.

**SUPPORTED clarification:** APU timer state is largely updated lazily on relevant timer I/O reads/writes (`read_t*out`, control/divider writes call `update_timers`), so this is not evidence of a timer bug. Immediate risk is JIT-block cycle overshoot / DSP and CPU↔APU interleave granularity.

**Decision:** do **not** merge clean32 yet. Throughput reproducibility is now sufficient locally; next experiment must quantify timing/scheduler effect rather than collect more FPS repeats.

## RESUME HERE / immediate action
1. Quantify the maximum and representative SPC700 cycle accumulation / scheduler overshoot caused by 16-byte versus 32-byte JIT blocks, specifically relative to DSP scheduling (`DSP_SAMPLE`) and CPU↔APU return points. Prefer source/static or profile-only measurement first; avoid perturbing the fast path unless needed.
2. Establish a correctness acceptance criterion before interpreting any diagnostic: 32 must not skip required DSP samples/events; bounded lateness must be understood against existing Sodium64 timing semantics, not merely “sounds okay”.
3. If timing risk is shown equivalent/safely bounded, checkpoint and decide whether clean32 merits exact real-N64 hardware validation. If 32 materially worsens required interleave, **REJECT** it despite 48/60 and seek a safer way to remove block-dispatch overhead.
4. Once experiment 1b materially resolves, repair `master` Road/Roadmap for M0 closure + evidence-driven APU/audio-first M1.
5. No second emulator or unbounded JIT/tooling project. Every batch reduces a Road-to-1.0 uncertainty.

Resume summary: M0 real-N64 mean49/60, APU/audio61.83%, no VI wait. M1 baseline16=44/60 ares. Confounded32 superseded causally. Clean32 `a758629...` differs only by BLOCK_SIZE and reproduces **48/60 twice**. Status: **CANDIDATE / LOCALLY REPRODUCED, blocked from merge by DSP/APU interleave correctness question**.