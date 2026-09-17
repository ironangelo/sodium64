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
Completed M0 branch representative HEAD: **`89df64192d622bfa12e4bb53e0f41ceab928efe6`**.
Clean M1 candidate / measurement authority: **`a758629014d0ecada6358c57eaf77c60afc80cad`** (`BLOCK_SIZE=32`).
M1 paired baseline: **`c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`** (`BLOCK_SIZE=16`).
`phase2/apu-audio-first` current HEAD **`255b7a3c4af9c4d6d76c2e5b1bca5ab40e1479ea`**, tree-equivalent to `a758629...` after hygiene correction.
**Active diagnostic branch:** `phase2/apu-interleave-diagnostic`; current HEAD **`6921055dfb180503f5e05cc04d70d53f3eccc578`**, parent exactly **`a758629...`**.
Open PRs: none at last checkpoint.

**HYGIENE NOTE / CORRECTED:** accidental temporary root file `noop` was created at `2fbff6e9...` while invoking the wrong Git action, then immediately removed by `255b7a3...`. Direct compare `a758629... -> 255b7a3...` has zero changed files. Do not use those hygiene commits as measurement identity. No history was rewritten.

**DOC DRIFT / TODO:** `master:docs/ROAD_TO_1_0.md` and `master:docs/ROADMAP.md` retain older pre-M0 / dynarec-first framing. Repair after the current APU experiment materially resolves; do not weaken 1.0.

## Ares laboratory authority
Isolation run **`35113184294`**, artifact **`10453682432`** proved pinned ares RSP JIT is a **LAB LIMITATION**. Valid high-density lab = **R4300 JIT + RSP interpreter**.
**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy; accidental OAM wall as primary cause. Old RSP-JIT profiles must not drive architecture. `SP_PC=0x020F` while RSP runs is non-interpretable.
Synthetic run **`35114866448`**, artifact **`10454678803`**: idle60/60; cpu-alu41; wram47; ppu-registers38; dma-vram16; gameplay-balanced61 with51.5% VI wait. Synthetic = causal controls only.

## Representative workload — Gothicvania
`donth77/snes-homebrew:gothicvania`; source pin `119496e6a2f1e53b7704712fef8cb81814f1698a`.
Survivability ROM SHA-256 **`5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`**; patch SHA-256 **`ab1ec83925571e916be9ae0a3abf3d2bb84b5f9efb1aae9fd2ac608ecc0f0bc9`**.
Controls: `ST_TITLE -> ST_PLAY`, `KEY_RIGHT`; health255 only prevents death during capture. Collisions, damage path, SFX, rendering, physics, streaming/audio remain active.
Source-build hygiene: **REJECTED** parallel make/PVSnesLib, parallax, broken gfx4snes. Actual issue = checkout-mtime interaction with frozen conversion products.

## M0 real-N64 closure
HEAD **`89df641...`**; Open Homebrew `35145447113` SUCCESS, source artifact `10466504920`, hardware package `10467585906`; Build/Validate `35145447039` SUCCESS.
Returned save SHA **`3316bd99...`**: frameskip0/APU21/audio4/precision8, 3581 samples, queue0, SP DMA0/0; windows **48,49,48,50,50 /60**, mean49.0. Active gameplay through capture.
Split: APU static24.91 + JIT19.18 + DSP17.73 = **APU/audio61.83%**; S-CPU22.12; PPU7.99; DMA6.67; RSPwait1.31; VI wait0.
**M0 ACHIEVED.** 49->60 needs ~18.3% less host time/frame if approximately linear; evidence rejects 65C816 dynarec as first M1 attack. APU/audio first.
Earlier save `c9862cc...` **SUPERSEDED FOR ARCHITECTURE DECISION** due post-GAME OVER windows.

## M1 baseline16
SHA **`c55b6b...`**; ares run **`35148379400`**, artifact **`10467972587`**; 2000 samples; **44/60**. APU/audio54.40%; SCPU30.85; PPU7.45; DMA4.40; RSPwait2.55; VI0.35; `apu_execute`13.10.

## M1 confounded32
SHA **`3b39523...`** repeated48/60 but also changed license/runtime layout macros. **SUPERSEDED AS CAUSAL CANDIDATE.**

## M1 clean32 — locally reproduced candidate
SHA **`a758629...`** differs from baseline only by `BLOCK_SIZE 16->32` (one file,1+/1-). CI green.
Run A artifact **`10477834229`**: **48/60**, 957 samples, APU/audio50.99%, `apu_execute`11.39.
Same-SHA run B artifact **`10478782129`**, digest `f607a5f0...`: **48/60**, 1175 samples, APU/audio52.69%, `apu_execute`12.77. Both frameskip0/APU21/audio4/precision8/queue0/SP DMA0/0.

**MEASURED / LOCALLY REPRODUCED:** clean32 = **48/60 twice** vs baseline16=44/60. Stable frame budget is stronger than sampling-share variation. No third throughput repeat warranted.
**CANDIDATE, NOT VALIDATED:** not mergeable until timing/interleave is bounded and later real-N64 authority confirms.

## BLOCK_SIZE32 semantic/timing review
**SUPPORTED / lower risk:** branches/jumps/calls terminate JIT block; 32 does not compile through control-flow boundaries.
**SUPPORTED / lower risk:** invalidation tags are 64-byte regions and blocks check start/end tags; a <64B linear block intersects at most two tag regions.

**OPEN QUESTION / MATERIAL CORRECTNESS RISK:** DSP due-check happens at `apu_execute` entry; JIT blocks return through scheduler only at `finish_block`. Larger block can increase DSP/APU/CPU interleave latency. `dsp_sample` returns to `apu_execute`, so overdue samples catch up one by one; concern is lateness/bunching/order, not obvious loss of sample count.

**STATIC BOUNDARY:** measured mode `apu_clock=21`, `DSP_SAMPLE=672`; **32*21=672 exactly**, one DSP period from instruction-stream fetch accounting alone before runtime data accesses. Baseline16 may also overshoot via data-heavy instructions, so paired measurement is required.
APU timers are mostly lazily updated on relevant I/O; this is not proof of timer failure.

## Paired DSP-lateness diagnostic
Goal: profile-only counters at DSP-due entry for max `a3-s3`, sum/average lateness, due-event count, and count with lateness >= `DSP_SAMPLE` (672). Instrumentation must not alter emulated cycle counters. Run BLOCK32 instrumented first, then change only BLOCK_SIZE32->16 under identical instrumentation/workload/settings. Interpret lateness metrics, **not instrumented FPS**.

**IMPLEMENTED BUT NOT INTERPRETABLE / EXPERIMENTAL CONFOUND:** diagnostic HEAD **`6921055dfb180503f5e05cc04d70d53f3eccc578`** is a direct child of clean32 `a758629...` and adds the DSP-due lateness logic inside `src/apu.S`, guarded by `SODIUM64_PROFILE`. However the same commit also changes unrelated timer-2 code in `stamp_timer2`: baseline `sub t1,t1,t2; sw t1,apu_ocycles+8` becomes `sub t0,t0,t2; sw t0,apu_ocycles+8`.

That timer-2 change may be a real correctness fix, but it is **not allowed inside the paired interleave experiment**. Any diagnostic result from `6921055...` would mix DSP-lateness instrumentation with altered timer semantics and must not be interpreted causally. The commit changes only `src/apu.S`, so supporting counter storage/reset/workflow plumbing must also be verified before treating it as runnable measurement code.

**DECISION:** isolate the diagnostic first. Restore `stamp_timer2` exactly to `a758629...` for the 32/16 comparison. If the timer-2 correction is valid, preserve it as separate knowledge/work after the controlled experiment rather than losing it.

## RESUME HERE
1. On `phase2/apu-interleave-diagnostic`, restore the unrelated `stamp_timer2` lines to exact parent `a758629...`; preserve only diagnostic intent.
2. Verify what support plumbing already exists for `profile_apu_dsp_*`; add profile-only counter definitions/reset and workflow observations as needed. Do not change emulated cycle state.
3. Before interpreting CI, compare against `a758629...` and verify no unrelated core-semantic change remains.
4. Run BLOCK32 diagnostic; checkpoint exact SHA/run/artifact/result immediately.
5. Change only BLOCK_SIZE32->16 under identical instrumentation; run and checkpoint.
6. Compare max/average lateness and >=672 frequency. If 32 materially worsens required interleave, mark32 REJECTED despite throughput. If equivalent/safely bounded, proceed toward real-N64 validation of **clean candidate `a758629...`**.
7. Separately investigate the discovered `stamp_timer2` t1/t0 issue after the paired experiment; do not silently discard it.
8. After experiment resolves, repair master Road/Roadmap for M0 closure + evidence-driven APU/audio-first M1.

Resume summary: M0 real-N64 mean49/60, APU/audio61.83%, no VI wait. Baseline16=44/60 ares. Clean32 `a758629...`=48/60 twice, **CANDIDATE / LOCALLY REPRODUCED**, blocked by paired interleave correctness diagnostic. Current diagnostic commit `6921055...` contains useful lateness instrumentation but is **confounded by an unrelated timer-2 change**, so isolate it before any measurement.