# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating protocol
Authority: **current Iron instruction > repo/artifact evidence > canonical docs > continuity > chats/memory/inference**. `master` is integrated truth; phase branches are candidates only.

Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**. Checkpoint every material result, changed hypothesis, falsification, risk, lab limitation, meaningful CI/artifact result, branch/HEAD transition or next-action change **before advancing**. For long experiments record exact SHA/run/question/possible readings before leaving them running.

Iron delegates technical direction toward Road to 1.0 to the assistant. Expose useful technical reasoning in chat (hypothesis, evidence, what it proves/does not, rejects, next controlled change, expected result, falsifier) without exposing private chain-of-thought verbatim.

## Target / current gate
Current milestone: **M0 ACHIEVED / M1 — faster base core, APU/audio first**.
Perfect target: real N64, correct native cadence, no required frameskip/frame generation, full-rate SPC700/APU and correct audio, high CPU/PPU/DMA/HDMA/timing fidelity, broad compatibility, no per-game modes, DSP-1 family, SuperFX/2 and SA-1. N64-alone first; cartridge assistance only after a quantified N64 ceiling.

Integrated `master`: **`a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`**.
Completed M0 representative HEAD: **`89df64192d622bfa12e4bb53e0f41ceab928efe6`**.
Safe M1 BLOCK16 authority: **`c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`**; safe branch tree before experiment 2: **`225859b1d8fc0eb477a624ac76f8237667379f59`**, tree-equivalent to baseline.
Active M1 branch `phase2/apu-audio-first`: **`e2b1979a4bda3cf853bd7c5c029dab4d0b9c481e`** = failed-to-build experiment 2A first attempt; do not measure/interpret this SHA.
Diagnostic branch `phase2/apu-interleave-diagnostic`: **`8805fd6128a183ce2259dd4d85ef146f42f00d47`**.

### Canonical docs
PR **#10 MERGED-CONSUMED**: docs head `90fafc89...` merged as master `a2270699...`. Exactly `ROAD_TO_1_0.md`, `ROADMAP.md`, `PROFILING.md`; no code/workflows. Build/Validate `35225126989` SUCCESS; Ares Profile Validation `35225221616` SUCCESS. Master now canonically states M0 achieved and M1 APU/audio-first; 65C816 dynarec is evidence-gated later work, not the current assumed route.

## Laboratory authority / known limitations
- ares pinned RSP JIT is a **LAB LIMITATION** for Sodium64 custom microcode. Isolation run `35113184294`, artifact `10453682432`: RSP-JIT modes collapse; RSP-interpreter modes progress. Valid high-density lab = **R4300 JIT + RSP interpreter**.
- **REJECTED causes** from that investigation: R4300 JIT itself, missing semaphore semantics, dropped semaphore `MTC0`, RSP DMA-busy, accidental OAM wall primary cause. Old RSP-JIT profiles must not drive architecture.
- valid synthetic matrix run `35114866448`, artifact `10454678803`: idle60/60, cpu-alu41, wram47, ppu-registers38, dma-vram16, gameplay-balanced61/60 with 51.5% VI wait. Synthetic workloads are causal controls only.

## Representative workload / M0 real hardware
Gothicvania source `donth77/snes-homebrew:gothicvania`, source pin `119496e6...`; survivability ROM SHA-256 `5519d51f...`, patch SHA `ab1ec839...`. Health255 only prevents death during short capture; gameplay/audio/rendering/collisions/damage path remain active.

M0 hardware save SHA `3316bd99...`: frameskip0/APU21/audio4/precision8, 3581 samples, windows **48,49,48,50,50 /60**, mean **49.0/60**, queue0, VI wait0. Split: **APU/audio61.83%**, S-CPU22.12, PPU7.99, DMA6.67, RSPwait1.31. **M0 ACHIEVED.** Approx. 18.3% total host-time reduction needed for 60 if locally linear. This rejected 65C816 dynarec as first M1 attack; APU/audio is gate driver.

## M1 baseline16
SHA `c55b6b...`, ares run `35148379400`, artifact `10467972587`: **44/60**, 2000 samples. APU/audio54.40%, SCPU30.85, PPU7.45, DMA4.40, RSPwait2.55, VI0.35; `apu_execute`13.10. Real-N64 M0 sampled `apu_read8`6.03% and `apu_write8`2.88%; ares baseline included `read_unk`7.75% and `apu_read8`2.90%.

## M1 experiment 1 — BLOCK_SIZE 32 — REJECTED
Confounded SHA `3b39523...` is **SUPERSEDED**. Clean one-variable SHA `a758629...` changed only BLOCK_SIZE16->32 and measured **48/60 twice** in ares (artifacts `10477834229`, `10478782129`), proving block/dispatch overhead matters locally.

Paired DSP-lateness diagnostic then falsified acceptability:
- BLOCK32 diagnostic `7f8faeff...`, run `35183376105`, artifact `10481267575`: 35,965 due events, avg128.338 cycles, max1218, `>=672` 377 (1.048241%).
- BLOCK16 paired `8805fd61...`, run `35190371200`, artifact `10483348244`: 35,982 due, avg119.073, max651, `>=672` 0.
Event counts differ only ~0.047%; BLOCK32 materially worsens the tail/interleave. **REJECTED despite throughput gain.** Do not merge/hardware-test 32. Knowledge retained: reduce dispatch overhead without lengthening scheduler return intervals.

Timer2 side issue from superseded diagnostic `6921055...`: proposed `stamp_timer2 t1->t0` is **REJECTED**. `t0` holds `apu_control`; baseline `t1` correctly holds `apu_cycle2` before subtracting cycles-to-overflow. No source fix needed.

## M1 experiment 2 — low/direct-page APU read fast path
### Hypothesis
`apu_map` only has a runtime-relevant nonzero entry at index `0x3FF`; `write_control` updates only that entry for IPL ROM mapping at `0xFFC0–0xFFFF`. Direct-page generators produce `0x0000–0x01FF`; pointer second-byte reads reach at most `0x0200`. Therefore those reads can omit `apu_map` safely while preserving I/O and guest-cycle semantics.

### Design
Local `apu_read8_nomap` is appended to `apu_address.S`, not `apu.S`. It checks `0x00F0–0x00FF`; I/O tail-jumps to generic `apu_read8`. Non-I/O low reads load RAM, load `apu_clock`, decrement `s3` exactly once and return. Scheduler return frequency, BLOCK_SIZE and write paths stay unchanged.

Use paired layout control:
1. **2A:** helper present but unreachable; zero call targets changed. Measure layout-only effect.
2. **2B:** on exact 2A layout, redirect only proven-low call targets. Initial scope: direct, direct+X/Y, `(X)`, `(X)+`, the two low pointer-byte reads in `[dp+X]` and `[dp]+Y`, `dp,dp` low read, `(X),(Y)` low read. Leave final indirect/absolute reads, `apu_drb`13-bit, ALU operation-level reads, stack/transfer reads, writes and BLOCK_SIZE untouched.

### 2A attempt 1 — COMPILE FAILURE / NO PERFORMANCE EVIDENCE
SHA **`e2b1979a4bda3cf853bd7c5c029dab4d0b9c481e`**, parent `225859b1...`. Net diff: one file `src/apu_address.S`, +10/-0; helper unreachable and no call target substitutions.

Build/Validate run **`35226731916` FAILED**: both normal and PROFILE builds fail assembler. Open Homebrew run **`35226731941` FAILED** in profile-build; `ares-gothicvania` skipped, so **no performance result exists** for this SHA.

Exact cause from build job `105220124897`: assembler at `src/apu_address.S:549` warns `macro instruction expanded into multiple instructions in a branch delay slot`, fatal due warnings-as-errors. Cause is `lbu v0, apu_ram(a0)` pseudo-instruction placed in the `beq` delay slot. This is a tooling/assembly-shape error, not evidence against the semantic hypothesis.

**Next controlled correction:** change only the helper branch delay slot to `nop` and move the `lbu v0, apu_ram(a0)` immediately after it. Helper remains unreachable; no call sites change. Re-run 2A under a new SHA. If that compiles, its frame budget is the layout-control authority. Do not interpret `e2b1979a...` beyond the compile failure.

## RESUME HERE
1. Correct 2A minimally on `phase2/apu-audio-first`: `beq ...; nop; lbu ...`; no other changes. Verify diff from `e2b1979a...` is exactly that assembly-shape fix and diff from safe `225859b1...` remains helper-only/unreachable. Checkpoint new SHA before CI interpretation.
2. Run Build/Validate + Gothicvania ares. Record exact runs/artifact. If 2A is ~44/60/sane, proceed to 2B. Material 2A movement means layout confound and 2A becomes paired baseline.
3. 2B changes only the enumerated proven-low call targets. Verify 2A->2B diff contains only target substitutions; profile same workload and compare complete virtual frame budget first, then sample shares. Repeat same SHA if ambiguous.
4. Reject any semantic/timing regression even if faster. Hardware is final authority only for candidates that survive lab validation.

Resume summary: master `a2270699...`; M0 hardware mean49/60 with APU/audio61.83%. BLOCK32 local speedup was REJECTED by paired DSP-lateness. Experiment2 2A first attempt `e2b1979a...` produced **no measurement** because a pseudo-instruction in a branch delay slot failed assembly; minimal shape correction is next.