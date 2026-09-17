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
Active M1 branch `phase2/apu-audio-first`: **`989e1f5ba8d592f6efb8e593d7a83fc5b51f3f89`** = experiment 2A layout-control attempt 2.
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
SHA **`e2b1979a...`**. Build/Validate `35226731916` FAILED normal+PROFILE; Open Homebrew `35226731941` failed profile-build and skipped Gothicvania. Exact assembler cause: `lbu v0, apu_ram(a0)` pseudo-instruction expanded into multiple instructions in a branch delay slot; warnings-as-errors. This SHA has **no performance evidence**.

### 2A attempt 2 — BUILD/SMOKE VALIDATED / PROFILE IN PROGRESS
SHA **`989e1f5ba8d592f6efb8e593d7a83fc5b51f3f89`**. Minimal correction from attempt1 is exactly **+1/-0**: branch delay slot is `nop`, then the same `lbu` follows. Direct compare from safe `225859b1...` remains exactly one file `src/apu_address.S`, **+11/-0**. Helper is still unreachable; no existing read call target changed.

Exact runs: **Build and Validate `35227136991` SUCCESS** — normal build, PROFILE build and emulator-smoke all green. **Open Homebrew Ares Profile `35227136832`** — profile-build green; at this checkpoint `ares-gothicvania` is still in progress building pinned ares in valid lab mode. Experimental question remains: does helper-only code/layout alter the Gothicvania baseline? Expected sane reading is ~44/60. Material movement means layout itself is a confound and this 2A SHA becomes the paired baseline for 2B.

**What this proves now:** the corrected unreachable helper is acceptable to assembler/linker and does not break the independent Mupen smoke path. **What it does NOT prove:** any performance equivalence or benefit; no Gothicvania result exists yet for 2A attempt2.

If 2A is sane/equivalent, 2B keeps exact helper/layout and changes only the enumerated proven-low call targets. **Expected:** lower APU-read cost, possibly modest frame-budget gain. **Falsifier:** neutral result, semantic/build regression, or evidence any redirected call can reach IPL space / lose I/O semantics.

## RESUME HERE
1. Read completion of **Open Homebrew `35227136832`** for exact `989e1f5b...`. If successful, record exact artifact/frame budget immediately. Any material movement in 2A is layout-only by construction.
2. If 2A is sane, implement 2B changing only enumerated call targets; verify 2A->2B diff is target substitutions only and checkpoint exact SHA before interpretation.
3. Profile 2B on identical Gothicvania settings. Compare complete virtual frame budget first, then sampling shares; repeat same SHA if ambiguous.
4. Reject any semantic/timing regression even if faster. Hardware is final authority only for candidates that survive lab validation.

Resume summary: master `a2270699...`; M0 hardware mean49/60 with APU/audio61.83%. BLOCK32 local speedup was REJECTED by paired DSP-lateness. Experiment2 2A attempt1 failed assembly with no measurement; corrected helper-only layout control `989e1f5b...` now passes build + Mupen smoke, while exact Gothicvania run `35227136832` is still in progress.