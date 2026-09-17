# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating protocol
Authority: **current Iron instruction > repo/artifact evidence > canonical docs > continuity > chats/memory/inference**. `master` is integrated truth; phase branches are candidates only.

Cadence is mandatory: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**. Continuity is a live scientific log: after every material result, changed hypothesis, falsification, risk, lab limitation, meaningful CI/artifact result, branch/HEAD transition or next-action change, checkpoint here before advancing. For long experiments record exact SHA/run/question/possible readings before leaving them running.

Iron delegates technical direction toward Road to 1.0 to the assistant. Choose architecture, experiments, implementation, profiling, Git/CI and validation without pushing low-level choices to Iron unless they change scope, hardware requirements, material risk or the target.

Transparency in chat: expose hypothesis, evidence, what it demonstrates / does not demonstrate, rejections, next controlled change, expected result and falsifier. Do not expose private chain-of-thought verbatim.

## Target / gate
Current milestone: **M0 ACHIEVED / M1 — faster base core, APU/audio first**.

Perfect target remains real N64 with correct native cadence; one required SNES frame per corresponding native frame; no required frameskip/frame generation; full-rate SPC700/APU and correct audio; high CPU/PPU/DMA/HDMA/timing fidelity; broad compatibility; no per-game modes; DSP-1 family, SuperFX/2 and SA-1. N64-alone first; cartridge assistance only after a quantified N64 ceiling.

Integrated `master`: **`ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`**.
Completed M0 measurement branch: `phase1/open-homebrew-workload`; representative HEAD **`89df64192d622bfa12e4bb53e0f41ceab928efe6`**.
Active M1 branch: **`phase2/apu-audio-first`**.
M1 paired baseline: **`c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`** (`BLOCK_SIZE=16`).
Current M1 HEAD: **`a758629014d0ecada6358c57eaf77c60afc80cad`** (`BLOCK_SIZE=32`, controlled candidate).
Open PRs: none at last checkpoint.

**DOC DRIFT / TODO:** `master:docs/ROAD_TO_1_0.md` and `master:docs/ROADMAP.md` still contain older pre-M0 / dynarec-first framing. Repair after the current controlled APU experiment is resolved; do not weaken the 1.0 target.

## Ares laboratory authority
Isolation run **`35113184294`**, artifact **`10453682432`** proved pinned ares RSP JIT is a **LAB LIMITATION**: RSP-JIT modes collapse while RSP-interpreter modes progress. Valid high-density lab is **R4300 JIT + RSP interpreter**.

**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy explanation; accidental OAM wall as primary cause. Old RSP-JIT profiles must not drive architecture. `SP_PC=0x020F` while RSP runs is non-interpretable in this lab.

Synthetic control run **`35114866448`**, artifact **`10454678803`**: idle 60/60; cpu-alu 41/60; wram 47/60; ppu-registers 38/60; dma-vram 16/60; gameplay-balanced 61/60 with 51.5% VI wait. Synthetic workloads are causal controls, not real-game/N64 authority.

## Representative workload — Gothicvania
Open workload: `donth77/snes-homebrew:gothicvania`; final source pin `119496e6a2f1e53b7704712fef8cb81814f1698a`.
Survivability ROM SHA-256: **`5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`**.
Benchmark patch SHA-256: **`ab1ec83925571e916be9ae0a3abf3d2bb84b5f9efb1aae9fd2ac608ecc0f0bc9`**.
Deterministic controls: `ST_TITLE -> ST_PLAY`, `padsCurrent(0) -> KEY_RIGHT`; survivability initializes local health to 255 only so death is unreachable during the short capture. Collisions, damage path, SFX, rendering, physics, streaming and audio remain active. Sodium64 core is unchanged by survivability.

Source-build hygiene knowledge: **REJECTED** parallel make/PVSnesLib, parallax generation, and broken gfx4snes as root causes. Actual failure was checkout-mtime interaction with committed/frozen conversion products. Freeze only high-level source-of-truth outputs and let low-level products rebuild.

## M0 real-N64 closure
Representative exact candidate HEAD **`89df64192d622bfa12e4bb53e0f41ceab928efe6`**. Open Homebrew run **`35145447113` SUCCESS**, source artifact `10466504920`, hardware package **`10467585906`**; Build and Validate **`35145447039` SUCCESS**.

Returned real-N64 save SHA-256 **`3316bd99dc26224050153c5a10c167b0e0b520aa9e4b85699b8ab45911f1f395`**, 32768 bytes, complete `S64H/S64P`, frameskip 0, APU clock 21, audio 4, precision 8, 3581 valid samples, queue 0, SP DMA full/busy 0/0. Complete frame windows **48/60, 49/60, 48/60, 50/60, 50/60**, mean **49.0/60**. Video shows active gameplay through measurement; no GAME OVER before completion marker.

Real-N64 sample split: APU static 24.91%; APU JIT generated 19.18%; DSP/audio 17.73%; **combined APU/audio 61.83%**; S-CPU 22.12%; PPU/events 7.99%; DMA/HDMA 6.67%; RSP/VRAM wait 1.31%; VI wait 0. Hot regions include generated JIT 19.18%, `apu_execute` 11.56%, `cpu_execute` 8.99%, `apu_read8` 6.03%, `skip_sample` 4.05%, `get_pitch` 3.52%, `apu_write8` 2.88%, `load_sample` 2.40%.

**MEASURED / M0 ACHIEVED:** representative N64 is throughput-bound near 49 completed SNES frames per 60 VI with no frameskip, full-rate APU, active audio and essentially no VI headroom.

**SUPPORTED INTERPRETATION:** 49->60 requires roughly 18.3% less total host time/frame if approximately linear. Closing only from the measured APU/audio 61.83% would require ~29.7% reduction of that aggregate; closing only from S-CPU 22.12% would require ~82.9% reduction of that bucket. Hardware evidence therefore rejects a 65C816 dynarec as the **first** M1 attack. Dynarec remains strategically valuable later and for SA-1 leverage.

Earlier real-N64 save SHA `c9862cc...` is **SUPERSEDED FOR ARCHITECTURE DECISION** because later windows were post-GAME OVER; preserve as profiler transport proof only.

## M1 baseline — 16-byte APU JIT blocks
Baseline SHA **`c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`**. Build/Validate run **`35148379354` SUCCESS**; ares run **`35148379400` SUCCESS**; artifact **`10467972587`**, digest `5471854958404c63bba8ee70ae5ead236f02b220881a4b8dfeaee60cdcd559a4`.

Exact workload/settings: Gothicvania survivability SHA above; frameskip 0, APU clock 21, audio 4, precision 8; valid ares mode. **2000 samples**. Last complete virtual budget **44/60**; partial state `fps_native=48`, `fps_emulate=39`, queue1. APU static36.60 + JIT3.30 + DSP14.50 = **54.40%**; S-CPU30.85; PPU7.45; DMA4.40; RSP wait2.55; VI0.35. `apu_execute`13.10; `cpu_execute`15.85; `apu_read8`2.90.

This is local comparison baseline only; real N64 remains performance authority.

## M1 experiment 1 — confounded 32-byte SHA
SHA **`3b39523c637ac5d076ddfb3714c6023e8d1106f4`** produced repeated **48/60** in ares (1183 and 915 samples) but changed more than `BLOCK_SIZE`: license text plus `TEXREC_OFS SHIFT_TABLE+0x8 -> +0x4` and `PRIO_CHECKS MODE7_MASK+0x4 -> +0x8`, shifting intermediate runtime layout offsets.

**SUPERSEDED AS CAUSAL CANDIDATE:** its 44->48 movement cannot be attributed to block size. Do not merge or hardware-test this SHA for the optimization claim.

## M1 experiment 1b — clean 32-byte candidate
Active HEAD **`a758629014d0ecada6358c57eaf77c60afc80cad`** restores exact baseline `src/defines.h` except `#define BLOCK_SIZE 16 -> 32`.

Direct compare `c55b6b... -> a758629...`: exactly one modified file, **1 addition / 1 deletion**. Known source confound removed.

CI: Build and Validate **`35174886449` SUCCESS**; Open Homebrew Ares Profile **`35174886403` SUCCESS**.
First clean profile artifact **`10477834229`**, digest **`faf8ec269072824613d9b9297c0f700cfd418ad6883f69097907c48c56b004b0`**.

**MEASURED / first clean run:** last complete virtual budget **48/60** versus baseline 44/60; 957 samples. Runtime: frameskip0, APU clock21, audio4, precision8, queue0, SP DMA full/busy0/0. APU static33.33 + JIT5.64 + DSP12.02 = **50.99%**; S-CPU30.93; PPU9.61; DMA5.54; RSP wait2.51; VI0.42. `apu_execute`11.39; `cpu_execute`15.15; `apu_read8`1.57; `apu_write8`0.94.

**SUPPORTED:** the one-variable clean candidate reproduces 44->48/60. The known layout confound is not required to explain the gain. +4 frames is about +9.1% completed frames/window relative to 44, but is not a direct real-N64 speedup percentage. Exact subsystem deltas are noisy because 957 vs 2000 samples; frame budget is stronger evidence.

**NOT VALIDATED:** one clean ares run does not establish reproducibility, real-N64 speed, SPC700/DSP timing, audio correctness or broad compatibility.

### Code-level semantic review of BLOCK_SIZE=32
**SUPPORTED / lower risk:** `compile_block` sets its linear byte limit as `PC + BLOCK_SIZE`; normal `finish_opcode` continues only below that limit. SPC700 branches/jumps/calls explicitly terminate through `finish_block` / PC handling, so increasing the limit does not simply compile through control-flow boundaries.

**SUPPORTED / lower risk:** JIT invalidation tags are indexed at 64-byte APU-memory granularity (`address >> 6`); cached blocks store/check start and end tag regions. A 32-byte linear block is still shorter than 64 bytes, so it can intersect at most two 64-byte regions and start/end tags cover those extrema. This reduces the self-modifying-code invalidation concern for 32; it is not broad correctness validation.

**OPEN QUESTION / MATERIAL CORRECTNESS RISK:** `apu_execute` checks whether DSP work is due **before** entering a cached/compiled JIT block. Generated blocks accumulate SPC700 cycles and return to `cpu_execute` only at `finish_block`; `cpu_execute` then gates APU/PPU events by cycle counters. Doubling maximum block length can therefore increase CPU↔APU/DSP scheduling latency even when opcode semantics are correct. `dsp_sample` advances the DSP schedule by `DSP_SAMPLE` and runs only when control returns through the scheduler path. A performance gain must not be accepted if it comes from materially coarser DSP/APU interleave.

**SUPPORTED clarification:** APU timer state is largely updated lazily on relevant timer I/O reads/writes (`read_t*out`, control/divider writes invoke `update_timers`), so do not conflate the new concern with proof of a timer bug. The immediate risk to isolate is block-cycle overshoot / DSP and CPU↔APU interleave granularity.

**Decision consequence:** even if same-SHA 32-byte throughput reproduces, do **not** merge yet. Next controlled correctness experiment must quantify scheduler/DSP overshoot or otherwise demonstrate that 32 preserves required timing/interleave semantics before hardware acceptance.

### Reproducibility experiment in progress
Run **`35174886403`**, direct job rerun, **attempt 2**, exact same head SHA **`a758629...`** with no source change. Attempt-2 ares job id **`105062197629`**; profile-build id `105062224398` completed SUCCESS. At last observation ares job was building pinned ares.

Question: does exact same binary reproduce materially-above-baseline throughput near 48/60? Readings: repeat near48 with unchanged state strengthens local reproducibility; collapse near44 indicates run noise; runtime/timing anomaly blocks acceptance regardless of throughput.

## RESUME HERE / immediate action
1. Read completion/artifact of run **`35174886403` attempt 2**, verify exact SHA/workload/settings, then compare complete frame budget first and sample split second.
2. **If repeat remains materially >44/60:** mark clean32 **CANDIDATE / LOCALLY REPRODUCED**, checkpoint immediately. Do not merge. Next isolate maximum/observed JIT-block cycle overshoot versus DSP scheduling/interleave; prefer profile-only or host-side evidence before invasive runtime instrumentation.
3. **If repeat collapses near44 or shows anomaly:** keep 32 **OPEN QUESTION** or **REJECTED** as evidence warrants; checkpoint before next path.
4. After timing/interleave question is bounded, decide whether 32 proceeds to real-N64 hardware validation or is rejected. Hardware remains final performance/timing authority.
5. Once experiment 1b materially resolves, repair `master` Road/Roadmap for M0 closure + evidence-driven APU/audio-first M1.
6. No second emulator or unbounded JIT/tooling project. Every batch reduces a concrete Road-to-1.0 uncertainty.

Resume summary: M0 real-N64 = 48/49/48/50/50, mean49, APU/audio61.83%, no VI wait. M1 baseline16 =44/60 ares. Confounded32=48/60 but superseded causally. Clean32 `a758629...` differs only by BLOCK_SIZE and first clean run=48/60. Same-SHA repeat is running. New material risk: verify DSP/CPU↔APU scheduler granularity before any merge.