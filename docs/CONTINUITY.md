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
M1 paired baseline / safe block-size authority: **`c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`** (`BLOCK_SIZE=16`).
Rejected clean32 throughput candidate: **`a758629014d0ecada6358c57eaf77c60afc80cad`** (`BLOCK_SIZE=32`).
**Active M1 branch:** `phase2/apu-audio-first`, current HEAD **`225859b1d8fc0eb477a624ac76f8237667379f59`**. Direct compare against `c55b6b...` has **zero changed files**: this is the restored safe BLOCK_SIZE16 tree after rejecting 32-byte blocks.
Diagnostic branch `phase2/apu-interleave-diagnostic` current HEAD **`8805fd6128a183ce2259dd4d85ef146f42f00d47`** (`BLOCK_SIZE=16` paired lateness control).
Open PRs: none at last checkpoint.

**HYGIENE NOTE / CORRECTED:** accidental temporary root file `noop` was created at `2fbff6e9...` while invoking the wrong Git action, then immediately removed by `255b7a3...`. Direct compare `a758629... -> 255b7a3...` has zero changed files. Do not use those hygiene commits as measurement identity. No history was rewritten.

**DOC DRIFT / TODO:** `master:docs/ROAD_TO_1_0.md` and `master:docs/ROADMAP.md` retain older pre-M0 / dynarec-first framing. The 32-byte experiment is resolved and the safe M1 branch restored; repair these canonical docs before the next substantial M1 architecture batch. Do not weaken 1.0.

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

## M1 experiment 1 — larger APU JIT blocks
Confounded SHA **`3b39523...`** repeated48/60 but also changed license/runtime layout macros: **SUPERSEDED AS CAUSAL CANDIDATE**.

Clean SHA **`a758629...`** differs from baseline only by `BLOCK_SIZE 16->32`. Uninstrumented ares run A artifact **`10477834229`** measured **48/60**, 957 samples, APU/audio50.99%, `apu_execute`11.39. Same-SHA run B artifact **`10478782129`** again measured **48/60**, 1175 samples, APU/audio52.69%, `apu_execute`12.77. Baseline16 was44/60.

**MEASURED / THROUGHPUT:** the one-variable 32-byte change reproducibly improves this ares lab frame budget from44->48/60. That performance finding is real local evidence, not a real-N64 percentage claim.

Static review lowered two risks: branches/jumps/calls terminate blocks; invalidation tags are64-byte regions and a <64B linear block intersects at most two tags. But DSP due-check occurs only at `apu_execute` entry, and a JIT block returns to scheduler at `finish_block`; larger blocks can therefore increase APU↔DSP lateness. At measured `apu_clock=21`, `32*21=672`, exactly one nominal DSP period before extra data-access costs.

### Paired DSP-lateness diagnostic
Profile-only instrumentation records DSP-due count, lateness sum/max, and events with lateness >= `DSP_SAMPLE=672`, without changing emulated cycle counters. Instrumented FPS is non-authoritative.

Historical diagnostic `6921055...` also changed `stamp_timer2` t1->t0 and is **SUPERSEDED AS MEASUREMENT CANDIDATE**. `8bebdd9...` isolated `apu.S`; `cbe39be...` added counters outside canonical S64P range. Hygiene attempts `7715da...` and `f81370...` for the paired16 control are **SUPERSEDED / DO NOT INTERPRET** because reconstructed `defines.h` carried extra formatting/layout changes.

**BLOCK32 MEASURED:** exact diagnostic SHA **`7f8faeff6efa1d94c421ad0369938d8c0d077195`**. Ares run **`35183376105` SUCCESS**, artifact **`10481267575`**, digest `d1a8b2dcac54e00c3e3c8330501dc5eea0471b59bb40a490083868e1f3b7af7c`; Build/Validate **`35183376137` SUCCESS**. 35,965 due events; late sum4,615,674; average **128.338 cycles**; max **1,218**; `>=672`: **377/35,965 = 1.048241%**.

**BLOCK16 MEASURED:** exact paired SHA **`8805fd6128a183ce2259dd4d85ef146f42f00d47`** differs from BLOCK32 diagnostic by exactly one file,1+/1- (`BLOCK_SIZE 32->16`). Ares run **`35190371200` SUCCESS**, artifact **`10483348244`**, digest **`5178c3c5f67843f3b99bb0ab3693147619cc652c65c9daf277318aee1b96c590`**; Build/Validate **`35190371186` SUCCESS** including normal build, profile build and emulator smoke. Settings remained frameskip0/APU21/audio4/precision8. 35,982 due events; late sum4,284,483; average **119.073 cycles**; max **651**; `>=672`: **0/35,982 = 0%**.

**SUPPORTED COMPARISON:** event counts differ by only17 (~0.047%), while BLOCK32 raises average lateness about7.8%, raises max from651 to1218 (~87%), and introduces377 >=one-period late events where paired BLOCK16 had none. This is a material tail/interleave regression attributable to the one changed variable in this paired lab.

**REJECTED / ARCHITECTURE DECISION:** `BLOCK_SIZE=32` is rejected despite its reproducible 44->48/60 throughput gain. Sodium64 1.0 requires correct audio/timing; we will not buy speed by allowing materially worse DSP scheduling lateness. Do not merge or hardware-test `a758629...` as a performance candidate. Retain the result as knowledge: dispatch/block overhead is significant, but must be reduced without lengthening scheduler return intervals this way.

## Timer2 side issue — closed
The superseded diagnostic commit `6921055...` changed `stamp_timer2` from baseline `sub t1,t1,t2; sw t1,apu_ocycles+8` to a `t0` variant.

**STATIC DATA-FLOW EVIDENCE:** `update_overflows` loads `t0 = apu_control` and preserves it to test timer enable bits. `stamp_timer0` and `stamp_timer1` compute timestamps from `apu_cycle1` in `t1`. `stamp_timer2` analogously loads `t1 = apu_cycle2`, then subtracts the computed cycles-to-overflow in `t2` and stores the result. Therefore the baseline `t1` path is internally consistent. The proposed `t0` path would subtract a cycle count from the APU control byte and store that as an overflow timestamp.

**REJECTED:** the `t1 -> t0` variant is not a bugfix; it is an erroneous diagnostic-side change. No source change is required. This explanation is preserved so it is not rediscovered later.

## RESUME HERE
1. Repair `master:docs/ROAD_TO_1_0.md` and `master:docs/ROADMAP.md` for M0 closure, real-N64 49/60 evidence, APU/audio-first M1, and rejection of 32-byte blocks on timing evidence. This doc repair is now the immediate batch before more M1 architecture work.
2. Start the next bounded APU optimization from safe HEAD **`225859b1...` / BLOCK_SIZE16**. Preferred next measured path: reduce `apu_read8`/`apu_write8` overhead without extending scheduler intervals; one important variable at a time. DSP inner-loop work follows if evidence warrants.
3. Use the existing Gothicvania paired lab first; only retain a change if throughput improves without new timing/semantic regression. Hardware remains final authority for accepted candidates.
4. No second emulator/unbounded JIT tooling. Every batch must reduce a Road-to-1.0 uncertainty.

Resume summary: M0 real-N64 mean49/60, APU/audio61.83%, no VI wait. Baseline16=44/60 ares. Clean32 improved to48/60 twice but paired DSP-lateness proved a timing regression: BLOCK16 avg119.073/max651/0 >=672 events vs BLOCK32 avg128.338/max1218/377 >=672 events. **BLOCK_SIZE32 REJECTED.** Active M1 HEAD `225859b1...` is tree-equivalent to safe baseline16. Timer2 t0 variant is **REJECTED** as an erroneous side change. Repair canonical Road/Roadmap next, then pursue safer APU memory/dispatch optimization.