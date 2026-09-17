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
Active M1 branch: **`phase2/apu-audio-first`**; current branch HEAD **`255b7a3c4af9c4d6d76c2e5b1bca5ab40e1479ea`**, tree-equivalent to clean candidate after hygiene correction.
Clean M1 candidate / measurement authority: **`a758629014d0ecada6358c57eaf77c60afc80cad`** (`BLOCK_SIZE=32`).
M1 paired baseline: **`c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`** (`BLOCK_SIZE=16`).
Open PRs: none at last checkpoint.

**HYGIENE NOTE / CORRECTED:** while attempting to create the diagnostic branch, an incorrect GitHub action created a temporary root file `noop` at commit **`2fbff6e9e5199459fc56c483345700b5e62e2e6e`**. It contained only `no`, touched no source/runtime code, and was immediately removed by **`255b7a3c4af9c4d6d76c2e5b1bca5ab40e1479ea`**. Direct compare `a758629... -> 255b7a3...` reports **zero changed files**. Do not use either hygiene commit as measurement identity; `a758629...` remains the exact clean32 evidence SHA. No history was rewritten.

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
Measurement SHA **`a758629014d0ecada6358c57eaf77c60afc80cad`** restores exact baseline `src/defines.h` except `BLOCK_SIZE 16 -> 32`. Direct compare: one file, **1 addition / 1 deletion**. Known source confound removed.

CI: Build and Validate **`35174886449` SUCCESS**; Open Homebrew Ares Profile run **`35174886403`**.

### Clean run A — attempt 1
Artifact **`10477834229`**, digest **`faf8ec269072824613d9b9297c0f700cfd418ad6883f69097907c48c56b004b0`**.
**MEASURED:** complete virtual budget **48/60**, 957 samples. Runtime frameskip0/APU21/audio4/precision8/queue0/SP DMA0/0. APU static33.33 + JIT5.64 + DSP12.02 = **50.99%**; S-CPU30.93; PPU9.61; DMA5.54; RSPwait2.51; VI0.42. `apu_execute`11.39; `cpu_execute`15.15.

### Clean run B — same-SHA attempt 2
No source change, same HEAD `a758629...`. Attempt-2 ares job **`105062197629` SUCCESS**. Artifact **`10478782129`**, digest **`f607a5f0d6aa19b1fc42206c5a7aa93c6ee3983a8895630aaf5a1ab4c679c33d`**; exact ROM SHA unchanged.

**MEASURED:** complete virtual budget **48/60** again; 1175 valid samples. Runtime frameskip0/APU21/audio4/precision8/queue0/SP DMA0/0. APU static35.83%, JIT4.43%, DSP12.43% => combined **52.69%**; S-CPU28.77; PPU9.19; DMA6.55; RSPwait2.47; VI0.34. `apu_execute`12.77; `cpu_execute`13.28.

**MEASURED / LOCALLY REPRODUCED:** clean32 is **48/60 in two independent runs** (957/1175 samples) versus baseline16 **44/60**. Stable frame-budget separation outweighs noisy subsystem percentages. No third throughput repeat is justified.

**CANDIDATE, NOT VALIDATED:** locally reproduced performance candidate; not yet mergeable and not proof of real-N64 speed/audio correctness.

## BLOCK_SIZE=32 semantic/timing review
**SUPPORTED / lower risk:** `compile_block` uses `PC + BLOCK_SIZE`; SPC700 branches/jumps/calls terminate through `finish_block`, so 32 does not compile through control-flow boundaries.

**SUPPORTED / lower risk:** JIT invalidation tags use 64-byte APU-memory regions (`address >> 6`) and cached blocks check start/end tags. A 32-byte linear block is <64B, so it can intersect at most two tag regions; start/end checks bound the self-modifying invalidation concern.

**OPEN QUESTION / MATERIAL CORRECTNESS RISK:** `apu_execute` decides whether DSP work is due **before** entering the JIT block. Generated blocks accumulate SPC700 cycles and return through `cpu_execute` only at `finish_block`. Doubling maximum block length can therefore increase CPU↔APU/DSP scheduler latency.

`dsp_sample` advances `a3` by `-DSP_SAMPLE` and returns to `apu_execute`; therefore overdue samples are caught up one by one rather than obviously dropped. The current correctness question is **lateness/bunching and interleave order**, not missing total DSP calls.

**STATIC BOUNDARY FINDING:** in the measured full-rate mode `apu_clock=21` and `DSP_SAMPLE=672`; **32 × 21 = 672 exactly**. A full 32-byte linear block consumes one DSP period from instruction-stream fetch accounting alone, before runtime data accesses (`apu_read8`/`apu_write8`) subtract further APU cycles. This does not prove incorrectness, but makes direct lateness measurement mandatory. Baseline16 can also overshoot through data-heavy instructions, so only a paired diagnostic can decide whether 32 materially worsens it.

**SUPPORTED clarification:** APU timers are largely updated lazily on relevant timer I/O operations; this is not evidence of a timer bug. Immediate risk is JIT-block cycle overshoot / DSP and CPU↔APU interleave granularity.

**Decision:** do **not** merge clean32 yet. Throughput reproducibility is locally sufficient; next experiment measures timing/scheduler effect.

## Next controlled experiment — paired DSP lateness diagnostic
Create temporary branch **`phase2/apu-interleave-diagnostic`** from exact clean candidate `a758629...`; do not use hygiene HEAD as measurement base.

Profile-only instrumentation will record at DSP-due entry: maximum `a3-s3` lateness, sum/average lateness, due-event count, and count with `lateness >= DSP_SAMPLE (672)`. Instrumentation must not modify emulated cycle counters. Reset counters at the same post-settle boundary used for profiling.

Run diagnostic first with BLOCK_SIZE32, then change only `BLOCK_SIZE 32->16` under identical instrumentation/workload/settings. Interpretation: compare lateness distribution/max and multi-due frequency, not instrumented FPS. If 32 materially worsens required interleave, reject it despite 48/60; if equivalent/safely bounded, candidate may proceed to real-N64 validation.

## RESUME HERE / immediate action
1. Create `phase2/apu-interleave-diagnostic` from **`a758629...`**.
2. Add profile-only lateness counters and workflow observations; compile/run BLOCK32 diagnostic; checkpoint exact SHA/run/artifact/result.
3. Change only BLOCK_SIZE32->16 on the same diagnostic instrumentation; run identical lab; checkpoint.
4. Compare max/average lateness and `>=672` frequency. Establish whether 32 changes interleave materially.
5. If timing risk is safely bounded, decide real-N64 validation of clean candidate `a758629...`; if not, mark 32 **REJECTED** and seek safer dispatch-overhead reduction.
6. Once experiment materially resolves, repair `master` Road/Roadmap for M0 closure + evidence-driven APU/audio-first M1.

Resume summary: M0 real-N64 mean49/60, APU/audio61.83%, no VI wait. Baseline16=44/60 ares. Clean32 `a758629...`=48/60 twice and is **CANDIDATE / LOCALLY REPRODUCED**, blocked from merge by paired DSP/APU interleave diagnostic. Accidental `noop` branch disturbance was fully corrected with zero net tree diff and is recorded as hygiene only.