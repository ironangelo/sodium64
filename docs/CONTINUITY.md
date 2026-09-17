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
**Active diagnostic branch:** `phase2/apu-interleave-diagnostic`; current HEAD **`8805fd6128a183ce2259dd4d85ef146f42f00d47`** (`BLOCK_SIZE=16` paired lateness control).
Open PRs: none at last checkpoint.

**HYGIENE NOTE / CORRECTED:** accidental temporary root file `noop` was created at `2fbff6e9...` while invoking the wrong Git action, then immediately removed by `255b7a3...`. Direct compare `a758629... -> 255b7a3...` has zero changed files. Do not use those hygiene commits as measurement identity. No history was rewritten.

**DOC DRIFT / TODO:** `master:docs/ROAD_TO_1_0.md` and `master:docs/ROADMAP.md` retain older pre-M0 / dynarec-first framing. Repair after the current APU experiment materially resolves; do not weaken 1.0.

## Ares laboratory authority
Isolation run **`35113184294`**, artifact **`10453682432`** proved pinned ares RSP JIT is a **LAB LIMITATION**. Valid high-density lab = **R4300 JIT + RSP interpreter**.
**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy; accidental OAM wall as primary cause. Old RSP-JIT profiling must not drive architecture. `SP_PC=0x020F` while RSP runs is non-interpretable.
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

Historical diagnostic commit **`6921055...`** added useful lateness logic but also an unrelated `stamp_timer2` t1->t0 change. **SUPERSEDED AS MEASUREMENT CANDIDATE**; preserve the timer issue for separate investigation.

`8bebdd9...` isolated `src/apu.S`; `cbe39be...` added counters/reset outside canonical S64P range.

**BLOCK32 DIAGNOSTIC — MEASURED:** SHA **`7f8faeff6efa1d94c421ad0369938d8c0d077195`**. Direct compare to clean candidate `a758629...` is limited to exactly three diagnostic files: `.github/workflows/open-homebrew-profile.yml` (51+/1-), `src/apu.S` (38+/1-), `src/profile.S` (23+/0-). No unrelated core-semantic or S64P-layout changes.

Open Homebrew Ares Profile run **`35183376105` SUCCESS**, artifact **`10481267575`**, digest **`d1a8b2dcac54e00c3e3c8330501dc5eea0471b59bb40a490083868e1f3b7af7c`**. Build and Validate run **`35183376137` SUCCESS**; normal build, profile build and emulator smoke all passed. Exact settings remained frameskip0/APU21/audio4/precision8.

BLOCK32 lateness result over the post-settle measured interval: **35,965 DSP-due events**, late sum **4,615,674 cycles**, average lateness **128.338 cycles**, maximum **1,218 cycles**, and **377 / 35,965 = 1.048241%** of due events were at least one full DSP period late (`>=672` cycles). Instrumented frame-budget remained 48/60 but is non-authoritative by design.

**MEASURED, NOT YET INTERPRETABLE AS A 32-BYTE REGRESSION:** BLOCK32 definitely exhibits occasional >1-period scheduling lateness. This alone does not prove 32 worsens correctness because baseline16 can also overshoot due to instruction/data-access cycle costs. Paired BLOCK16 is mandatory.

**BLOCK16 CONTROL HYGIENE:** commits `7715da11951f57db81fed37453802f5033d91095` and `f81370b22e5c410a3cd5e78248191bab79872538` are **SUPERSEDED / DO NOT INTERPRET**. They attempted the 32->16 control but also introduced formatting/layout differences while reconstructing `defines.h`; no results from those SHAs may be used.

**BLOCK16 CONTROL — CLEAN MEASUREMENT CANDIDATE:** SHA **`8805fd6128a183ce2259dd4d85ef146f42f00d47`** restores `src/defines.h` from exact BLOCK32 measurement source and changes only `#define BLOCK_SIZE 32 -> 16`. Direct compare **`7f8faeff... -> 8805fd61...`** reports exactly one modified file, **1 addition / 1 deletion**. Therefore this is the valid paired control and any following CI/artifact must be tied to this exact SHA.

## RESUME HERE
1. Read CI/run state for exact BLOCK16 control SHA **`8805fd6128a183ce2259dd4d85ef146f42f00d47`**. Ignore any runs from superseded hygiene SHAs `7715da...` or `f81370...`.
2. If successful, record exact ares run/artifact and BLOCK16 average/max lateness plus >=672 frequency immediately.
3. Compare BLOCK32 vs BLOCK16 directly. If 32 materially worsens required interleave, mark32 REJECTED despite throughput. If equivalent/safely bounded, proceed toward real-N64 validation of clean candidate `a758629...`.
4. Separately investigate the discovered `stamp_timer2` t1/t0 issue after the paired experiment; do not silently discard it.
5. After experiment resolves, repair master Road/Roadmap for M0 closure + evidence-driven APU/audio-first M1.

Resume summary: M0 real-N64 mean49/60, APU/audio61.83%, no VI wait. Baseline16=44/60 ares. Clean32 `a758629...`=48/60 twice, **CANDIDATE / LOCALLY REPRODUCED**. Clean BLOCK32 DSP-lateness diagnostic `7f8faeff...` measured avg128.338, max1218, >=672 in1.048241% of due events. Clean paired BLOCK16 control is now exact SHA `8805fd61...`, differing only by BLOCK_SIZE32->16; read that run next.