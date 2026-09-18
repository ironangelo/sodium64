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

### 2A attempt 2 — original in-progress checkpoint (completion audited below)
SHA **`989e1f5ba8d592f6efb8e593d7a83fc5b51f3f89`**. Minimal correction from attempt1 is exactly **+1/-0**: branch delay slot is `nop`, then the same `lbu` follows. Direct compare from safe `225859b1...` remains exactly one file `src/apu_address.S`, **+11/-0**. Helper is still unreachable; no existing read call target changed.

Exact runs: **Build and Validate `35227136991` SUCCESS** — normal build, PROFILE build and emulator-smoke all green. **Open Homebrew Ares Profile `35227136832`** — profile-build green; at this checkpoint `ares-gothicvania` is still in progress building pinned ares in valid lab mode. Experimental question remains: does helper-only code/layout alter the Gothicvania baseline? Expected sane reading is ~44/60. Material movement means layout itself is a confound and this 2A SHA becomes the paired baseline for 2B.

**What this proves now:** the corrected unreachable helper is acceptable to assembler/linker and does not break the independent Mupen smoke path. **What it does NOT prove:** any performance equivalence or benefit; no Gothicvania result exists yet for 2A attempt2.

If 2A is sane/equivalent, 2B keeps exact helper/layout and changes only the enumerated proven-low call targets. **Expected:** lower APU-read cost, possibly modest frame-budget gain. **Falsifier:** neutral result, semantic/build regression, or evidence any redirected call can reach IPL space / lose I/O semantics.

## Previous RESUME HERE — SUPERSEDED by the audit below
1. Read completion of **Open Homebrew `35227136832`** for exact `989e1f5b...`. If successful, record exact artifact/frame budget immediately. Any material movement in 2A is layout-only by construction.
2. If 2A is sane, implement 2B changing only enumerated call targets; verify 2A->2B diff is target substitutions only and checkpoint exact SHA before interpretation.
3. Profile 2B on identical Gothicvania settings. Compare complete virtual frame budget first, then sampling shares; repeat same SHA if ambiguous.
4. Reject any semantic/timing regression even if faster. Hardware is final authority only for candidates that survive lab validation.

Resume summary: master `a2270699...`; M0 hardware mean49/60 with APU/audio61.83%. BLOCK32 local speedup was REJECTED by paired DSP-lateness. Experiment2 2A attempt1 failed assembly with no measurement; corrected helper-only layout control `989e1f5b...` now passes build + Mupen smoke, while exact Gothicvania run `35227136832` is still in progress.
## Independent read-only direction audit — 2026-09-17

Scope: architecture/direction red-team, not implementation. Only this continuity file is changed by the audit. No runtime/workflow/other doc edits, PRs, merges or experiment launches. The full 1.0 target and N64-alone priority are unchanged.

### Evidence identity and audit limits

- Integrated master verified at `a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`; current master Build/Validate `35226256321` and Ares Profile Validation `35226256322` both SUCCESS.
- Active candidate remains `phase2/apu-audio-first@989e1f5ba8d592f6efb8e593d7a83fc5b51f3f89`; Build/Validate `35227136991` SUCCESS. No open PR at audit time.
- Diagnostic remains `8805fd6128a183ce2259dd4d85ef146f42f00d47`. Direct forward diff `7f8faeff6efa1d94c421ad0369938d8c0d077195 -> 8805fd61...` is ONLY BLOCK_SIZE32->16. Logs independently verify the recorded due counts/sums/maxima/tails. BLOCK32 rejection stands.
- `c55b6b44... -> 225859b1...` has zero changed files. `225859b1... -> 989e1f5b...` is ONLY the +11-line unreachable helper in apu_address.S.
- Read all five canonical docs, historical M0 closure at continuity commit `5ebe300ed7907970ca9f99ef4fac5a2620143c03`, APU generator/runtime modules, DSP, scheduler, relevant PPU/memory/coprocessor paths, profiler/harness/workflows and pinned ares reference paths.
- M0 artifact `10467585906` independently matches run `35145447113`, HEAD `89df64192d622bfa12e4bb53e0f41ceab928efe6`, ZIP digest `db187230e8728c22b5acebbeabd99489af538994c79eece0a6d4f2a054415086`. Original returned SRAM save `3316bd99dc26224050153c5a10c167b0e0b520aa9e4b85699b8ab45911f1f395` was NOT re-decoded in this audit; its measurements remain previously recorded hardware evidence, not new measurements.
- Artifact metadata and decoded CI logs were accessible; attempting to read the ZIP download bytes in this environment returned HTTP403. Consequently no claim of independent ELF disassembly/raw-snapshot decoding here. This audit's new runtime observations come from exact job logs; source conclusions are distinguished from dynamic validation.
- Gothicvania ROM remains `5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`, frameskip0/APU21/audio4/precision8, ares pin `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`, R4300 JIT + RSP interpreter.

### A. MEASURED: 2A completed, and the baseline has a material A/A discrepancy

Open Homebrew `35227136832` SUCCESS, job `105221944468`, artifact `10499991568`, digest `10b4fbac88be8c04fa47bbcdac2f7812099fa8c8d5001b2098030741ad772996`:
- exact SHA `989e1f5b...`, **52/60**, 1092 samples, partial VI32/60, partial guest27, queue1;
- APU static31.32%, generated4.95%, DSP14.38%, S-CPU31.04%, PPU9.07%, DMA6.41%, RSP/VRAM wait2.47%, VIwait0.37%;
- `apu_execute`7.23%, `apu_read8`1.83%; helper still never called.

The SAME baseline SHA `c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`, SAME run `35148379400`, has distinct attempts:
- attempt1 job `104970584720`, artifact `10467972587`: **44/60**, 2000 samples; `apu_execute`13.10%, APU aggregate54.40%.
- attempt2 job `104987346877`, artifact `10470371683`: **48/60**, 1288 samples; `apu_execute`14.13%, APU static36.34 + generated4.43 + DSP12.66 =53.43%; digest `7fd939959855f1389560f4d2db45fb439f334aa7648d21c027cdbd9f33ddf7ca`.
Both have identical reported guest ROM/settings and download the same profile-build artifact digest `6b2986bae04ae0c7efe8218e18ff37eb7fe3073a83064fcc79f6609b7a4fdc8e`.

**SUPPORTED INTERPRETATION:** the 4-frame baseline A/A movement is as large as the historical claimed BLOCK32 gain. The old statement “44->48 proves dispatch overhead” is too strong. Preserve the actual 44 and 48 observations; causal magnitude and mechanism are **UNKNOWN** until comparable windows/repeats establish an effect. This does NOT rehabilitate BLOCK32: its independently paired guest-cycle lateness regression still justifies rejection.

**REJECTED inference:** 2A's 52 proves map-elimination speedup (helper is unreachable). Also reject “any 2A movement must be layout-only by construction”: only the SOURCE difference is layout-only; measurement-phase/host-stop/sampling variation remains a competing cause.

**LAB LIMITATION / source evidence:** open-homebrew-profile.yml warms for 1 host second, patches APU clock/JIT, settles 1 host second, then gdb_rsp_dump.py stops every 3 host seconds until >=800 samples. It captures the last complete VI window, not a fixed guest checkpoint sequence; profile samples cover a broader interval than that single last window. Deterministic entropy and a fixed ROM do not make wall-time-selected guest segments identical. Changing clock/JIT at an arbitrary stop can also leave an in-flight old generated block and old cycle state; resetting lookup/pointer alone does not prove a clean temporal transition. Magnitude of this risk remains UNKNOWN. Pin settings before guest execution or at a proven safe scheduler boundary in a future measurement repair.

### B. SUPPORTED INTERPRETATION: verify effective SPC700 timing BEFORE a major JIT optimization

This is a direction issue: `apu_clock=21` proves the configured inherited rate, not correct instruction throughput or full SPC700 timing.

Source accounting at audited candidate:
- `jit_read8` subtracts one apu_clock from compile-time `s2` for each opcode/operand byte.
- `apu_read8/apu_write8` subtract one apu_clock from runtime `s3` per data access.
- `finish_block` emits the accumulated fetch debit at block exit.
- `apu_mul`, `apu_div`, `apu_bra` and conditional branch generators contain no additional internal/taken-branch cycle charge; NOP dispatches straight to next_opcode.

For isolated instruction accounting, source predicts NOP1, MUL1, DIV1 and BRA2 inherited clock units, versus 2,9,12,4 in the pinned independent ares SPC700 reference (`ares/component/processor/spc700/instruction.cpp` plus `instructions.cpp`, same ares pin above; reference fetch + read/idle calls). This is static accounting/reference disagreement, NOT a freshly run cycle test. Arbitrary MIPS execution time does not automatically debit Sodium64's guest `s3`.

**HYPOTHESIS:** part of the APU burden is excess SPC700 instructions executed per emulated time because internal cycles are undercharged. Correct timing could reduce host work while improving fidelity, but direction/magnitude on Gothicvania is UNKNOWN. Synchronization-sensitive drivers can change behavior; no speedup percentage is claimed.

**Direction change:** a small instruction-cycle and I/O-order proof now outranks broad memory/dispatch work. Do not “fix” this by global clock scaling or a game-specific mode. If confirmed, a bounded guest timing correction must be measured separately from optimization, then establish a new baseline. Baseline-equivalence remains useful for performance-only changes but is not proof of SNES fidelity.

**Additional source-backed risk:** BLOCK_SIZE is not an unconditional maximum. Opcode0x00 (NOP) maps directly to `next_opcode`, bypassing `finish_opcode` and its a0<t9 limit test. A long NOP sequence can cross nominal block and 64-byte tag-region limits before a terminating/checking opcode. This undermines generic claims “16 bytes guarantees interleave” and “only two endpoint tags always cover a block.” Runtime consequences and prevalence in Gothicvania are UNKNOWN. Test long NOP spans and mutation of a middle covered region before assuming bounded dispatch/SMC safety. Existing absolute-write self-modification handling in apu_absa does not establish safety for all indirect writes or changes later in an executing block.

### C. Architecture ranking and profiler interpretation

**SUPPORTED INTERPRETATION:** APU/audio remains the right first subsystem. Historical hardware: static24.91%, generated19.18%, DSP17.73%=61.83%; roughly18.3% total time reduction (29.7% of that aggregate) would close Gothicvania's 49->60 gap under fixed-cost linear assumptions. This is workload-local, not a 1.0 corpus/hardware ceiling. The 6.03% named apu_read8 share cannot by itself justify a plan to recover18.3%; the eligible mapping subpath is only part of that region, and attribution/cache cross-effects prevent treating 6.03 as an exact hard bound.

- **Memory specialization:** current 2A helper's low-address/map argument is supported by source. Only IPL entry0x3FF changes; proposed direct addresses are0..0x1FF, pointer second-byte reaches0x200. I/O tail fallback preserves existing semantics and exactly one data-cycle debit. However low-page is NOT synonymous with ordinary RAM: 0xF0..FF includes timers/DSP/CPU ports. The new helper adds a guard before the generic guard for those accesses. Net benefit depends on actual eligible RAM/I/O mix. Preserve P-page changes, index wrapping, second-byte behavior, register-clobber contract and unchanged final indirect reads. Do not silently turn this optimization into an addressing-correctness repair.
- **Generated code:** load_reg_* already load lazily, finish_block already spills only dirty state, and NZ updates are already deferred. “Add register caching/lazy flags” is not a new architecture. Remaining opportunity: repeated full_address LUI+access sequences, address generation, helper jal/jr, repeated apu_clock reads, and spills/reloads across short blocks. A compact state-base convention / selective generated RAM loads may reduce these without longer blocks; payoff and register-pressure/I-cache effects are HYPOTHESIS. Full memory-read inlining is not automatically a win.
- **Dispatch/invalidation:** apu_execute performs lookup plus two endpoint-tag validations per cached entry, even when both refer to the same64-byte region. Single-region specialization is a bounded candidate after the block-span proof. Keep DSP/CPU checks at the same logical boundaries and preserve invalidation. Do not remove checks based on a single game's apparent code immutability.
- **Write path:** every APU write increments a64-byte region tag, including data-only regions. Avoiding needless invalidation/updates could help, but executable-region ownership and code/data mixing are unproven. No hot-path “writes cannot be code” assumption; first establish write mix/recompile causes, only if samples justify it.
- **Compilation/cache maintenance:** emit_op invalidates I/D-cache aliases for each emitted word; line-batched maintenance could save compile cost. In read CI profiles apu_emitter.o is0–0.39%, so this is NOT a first optimization absent contrary representative evidence. Lookup table is256KiB, tags4KiB, generated buffer256KiB; these are allocated sizes, not measured hot working sets. Hardware cache savings require hardware evidence, not size arithmetic.
- **DSP:** historical get_pitch3.52% / DSP aggregate17.73% justify an independent bounded proof now, not an obligatory long queue of read-helper variants. Pitch endian/mask conversion happens per active voice/sample; cache the derived base pitch at register writes as one candidate. Do not cache future modulation/envelope-dependent results or defer observable writes. Existing volume products are already cached. Another larger path may win later; evidence does not yet justify RSP offload.
- **Scheduler:** cpu_execute includes APU/PPU checks yet is classified as S-CPU solely by object; apu_execute includes the DSP-due check as well as JIT validation. Bucket totals are not clean functional attribution to interpreters vs scheduling.
- **Symbol labels:** apu.S read_unk is also the ordinary non-I/O read return; write_unk likewise. High read_unk samples do NOT establish unknown-register polling. profile_report.py aggregates base symbol names without object qualification; local duplicate names need address/object context. Attribute raw EPC ranges and branch-delay effects before using tiny regions as optimization budgets.
- **LAB LIMITATION:** N64 hardware generated-code share19.18% versus baseline ares3.30% (repeat4.43%, 2A4.95%) means ranking generated-code/layout work solely by ares percentages can mislead. Cause is UNKNOWN: workload phase, cache/timing model and interrupt attribution compete. Pinned ares cpu.cpp/recompiler.cpp contain deferred cycle flushing and interrupt/synchronization boundaries plus actual I/D-cache modeling. Do not claim ares “has no cache”; do not claim its sample distribution is hardware-equivalent. A small CPU-interpreter control can test attribution sensitivity when needed, without reopening the rejected RSP-JIT investigation.

### D. Fidelity and 1.0 convergence risks

**SUPPORTED INTERPRETATION (source):** current DSP/audio budget excludes work required by the target. dsp.S selects stored BRR samples directly (no Gaussian interpolation path in this source), and contains no echo/FIR or pitch-modulation processing comparable to pinned ares sfc/dsp/{dsp,voice,echo,gaussian}. Its global output/timing behavior also needs reference validation. This is not a demand to transplant a second DSP/emulator; preserve Sodium64 and add only required behavior with tests. Near-term work should favor invariant access/dispatch/state costs that survive fidelity recovery.

“Audio enabled/full-rate setting” and “no lateness >=672” do not prove correct PCM, correct register visibility, AI delivery without underflow, or correct native cadence. BLOCK16's measured max651 is a local baseline, not an accuracy specification or universal bound.

Other recorded target debt: approximate APU/DSP integer cycle constants, fixed NTSC-oriented VI/262-line assumptions, PPU pre-VBlank timing workaround; DSP-1 has explicit unimplemented paths and SuperFX/SA-1 are absent. Do not infer GateB/C/D/E/F completion from one homebrew at60. Cost after accuracy recovery can increase or decrease; no quantitative N64-alone ceiling or cartridge-assistance rationale exists.

Keep M1 APU-first, but bring a SMALL timing/PCM reference contract forward from later accuracy work. Follow a credible first gain with a second meaningfully different audio driver/workload before a large architectural commitment. Do not grow an unbounded corpus/tooling project. Do not start 65C816 dynarec, SuperFX translation, or SA-1 infrastructure simply to avoid the current unresolved measurement/timing questions.

### E. Five prioritized experiments (proposals only; none run by this audit)

**E1 — comparable A/A and layout control (immediate; GateA / M1 measurement prerequisite).**
- Hypothesis/evidence: wall-time-selected phases and/or layout explain44/48/52; baseline same-build discrepancy and unreachable-helper result directly motivate it.
- Minimal change: unchanged existing binaries first, same boot/settings and a defined guest checkpoint/segment; collect several complete sequential VI windows, not only the last. Use an existing safe stop if sufficient; otherwise only the smallest measurement-boundary repair. Fix build/toolchain/ELF/ROM identities. Obtain baseline A/A then alternate safe-tree vs2A comparisons. Do not activate helper.
- Measure: guest checkpoint/state, each complete VI budget, total guest frames and virtual Count delta over same segment, sample count/window, queue/audio state, symbol addresses/layout. Pair aggregate cost with shares; do not multiply a whole-profile share by an unrelated last-frame budget.
- Expected/falsifier: repeated identical-build variation shrinks at matched checkpoints; a stable remaining safe-vs2A shift supports a layout mechanism. Persistent A/A spread comparable to candidate effect falsifies the lab's ability to rank small optimizations; no repeated safe-vs2A difference falsifies layout-gain attribution.
- Does NOT prove: any helper benefit, real-N64 gain, exact SNES timing or commercial representativeness.
- Environment: valid ares first; CPU-interpreter control only if needed to separate attribution. No immediate hardware ritual; real N64 for a material layout-sensitive candidate.

**E2 — SPC700 cycle/exit contract (highest architectural uncertainty; GatesA/C and M1/B).**
- Hypothesis/evidence: missing internal/taken-branch charges cause over-execution; NOP bypass also defeats nominal block limits. Source/reference ledger above.
- Minimal change: isolated original SPC snippets for NOP/MUL/DIV, taken/not-taken branches and one timer/port loop; compare existing Sodium64 state/cycle deltas and ordered accesses against an independent pinned reference. Include a long NOP span crossing64-byte regions and later mutation of a middle region. Begin with observation; any timing correction is a SEPARATE one-variable candidate, no memory-helper/dispatch rewrite.
- Measure: guest PC/registers, logical elapsed SPC/master cycles, instruction count per timer interval, ordered I/O timestamps, DSP due/late distribution, actual guest-byte span per block, re-entry after mutation. Then determine how frequent relevant opcodes are in Gothicvania before projecting savings.
- Expected/falsifier: original runtime exhibits the predicted per-op deficit / oversize span; an omitted charging/exit mechanism demonstrated dynamically falsifies that interpretation. If confirmed but rare in representative execution, it falsifies the predicted large performance relevance, not the correctness issue.
- Does NOT prove: how much FPS a timing repair gains, full SPC correctness, correct final audio, or acceptability of simply lengthening scheduler intervals.
- Environment: deterministic reference + valid ares; independent Mupen semantic check where feasible. N64 confirms subsequent candidate cadence/audio at milestone.

**E3 — finish controlled low-read proof (after E1, with E2 accounting explicit; GatesB/C / M1).**
- Hypothesis/evidence: map-lookup overhead on proven-low non-I/O reads exceeds helper/fallback costs; hardware read cost and source mapping invariant motivate it.
- Minimal change: exact2A->2B call-target substitutions only. No BLOCK_SIZE/write/final-indirect/ALU changes. Establish ABI and instruction expansion from ELF; exercise P0/P1, index wrap,0xEF/F0/FF/100/1FF/200, timers clear-on-read, CPU/DSP ports, IPL on/off.
- Measure: matched complete-frame/Count cost; selected non-I/O vs I/O access mix (bounded diagnostic only if necessary); combined generic/helper/I/O/return regions; unchanged guest state, cycle debits and event ordering. Use separate timing-instrumented pair rather than instrumented FPS.
- Expected/falsifier: reproducible absolute cost reduction beyond A/A spread and semantic equivalence. No useful net gain, fallback dominating, address proof failure or any timing/state mismatch rejects this narrow candidate.
- Does NOT prove: that direct generated loads cannot work if this helper is neutral, that all low-page reads are RAM, or that memory work alone closes49->60.
- Environment: valid ares + targeted semantic checks; N64 final for a candidate worth retaining, especially given JIT/cache-share discrepancy.

**E4 — short-block validation specialization (conditional, not bigger blocks; GatesB/C / M1).**
- Hypothesis/evidence: duplicate endpoint checks for blocks provably within one64-byte tag region materially cost dispatch; apu_execute and short-block source motivate it.
- Minimal change: specialize only validation for a proven single-region block; retain original two-region fallback, block/event boundaries, spill contract and invalidation. Do not combine chaining, permanent-register ABI or new cycle batching. E2 must first establish actual spans.
- Measure: single-vs-two-region entry frequency, absolute entry+generated+frame cost, code/header footprint, recompile counts, DSP/I/O ordering, SMC/IPL/boundary/rollover tests; paired layout control.
- Expected/falsifier: same correct entry decisions with lower representative cost. Rare eligibility, added branch/layout cost cancelling savings, stale execution or event-order divergence rejects it.
- Does NOT prove: longer blocks/chaining are safe, invalidation can be omitted, compiler-cache maintenance is hot, or real-N64 gain.
- Environment: ares/Mupen for semantics; N64 for cache/dispatch payoff. If supported, a later SEPARATE proof may reduce repeated state-address materialization in existing short generated blocks.

**E5 — hoist one DSP invariant (alternative to a long JIT micro-optimization series; GatesB/C / M1).**
- Hypothesis/evidence: derived base pitch can be computed on register writes instead of endian/mask work per voice/sample; historical hardware get_pitch3.52%, total DSP17.73%.
- Minimal change: cache only derived PITCHL/PITCHH base value, updated on either byte write with identical existing visibility; unchanged voice order, BRR, mixing and DSP schedule. No resampling/voice disabling/echo redesign in the same experiment.
- Measure: exact PCM and voice state against baseline for controlled pitch writes/KON/BRR boundaries and representative segment; compare reference behavior separately so baseline-equivalence is not called accuracy. Measure write-side cost, sample-side cost and absolute frame budget.
- Expected/falsifier: identical baseline state/output with a repeatable net saving. High write frequency, stale partial-register updates, changed visibility or no absolute gain rejects it.
- Does NOT prove: existing DSP is accurate, missing interpolation/echo is free, this is enough to close the remaining gap, or offload is justified.
- Environment: ares/Mupen lower-level execution and pinned SNES reference; N64 validates retained gain/audio. Future sub-sample DSP fidelity may require latching individual pitch bytes; do not freeze a combined cache into the fidelity contract.

### Audit decision

**Material immediate-route change is justified; subsystem direction is retained.** First stabilize measurement interpretation and falsify the inherited instruction-timing/block-span assumptions. Keep2B as a bounded candidate, not the automatic next implementation. DSP invariant work and same-boundary validation/generated-code improvements remain viable Sodium64-native routes. No quantified evidence justifies abandoning N64-alone or building a second emulator.

Master canonical docs still contain the stronger “44->48 proves overhead” interpretation; record this correction here and schedule a future authorized doc sync. They were deliberately NOT edited in this read-only audit.


## RESUME HERE

1. **Read the independent audit above before implementing2B.** Master remains `a2270699...`, active M1 remains `989e1f5b...`, diagnostic remains `8805fd61...`; no code was changed by the audit.
2. **2A is completed, not running:** `35227136832` / job `105221944468` / artifact `10499991568`:52/60,1092 samples. Record it as a helper-unreachable observation. Baseline same SHA/build also has44/60 AND48/60 attempts. Do not assert a mapping speedup or a proven layout cause.
3. Execute a bounded **E1 A/A and matched-window comparison** before ranking small changes. Preserve the historical observations but replace the unsupported causal reading; do not reopen BLOCK32, which remains REJECTED for timing.
4. Execute **E2 cycle-accounting/block-span proof** before a major JIT investment. Distinguish configured apu_clock21 from instruction-accurate full rate; verify NOP exit/invalidation assumptions. Any correction becomes its own measured timing candidate and fresh baseline.
5. With those uncertainties resolved, select the next bounded implementation from E3 low-read helper, E4 same-boundary validation, or E5 DSP invariant hoisting based on expected absolute savings and correctness. Keep one important variable per experiment.
6. Graduate retained candidates to one real-N64 milestone session with exact build/ROM/settings, frame windows, audio/cadence and decision criteria. No scope reduction, cartridge assistance, second emulator or unbounded tooling.

Resume summary: **M0 remains achieved as a measurement milestone; M1 remains APU/audio-first.** This audit changes the immediate order because previously unrecorded A/A variation and source-backed guest-cycle/block-span gaps undermine blind optimization of the inherited baseline. Current APU full-rate setting and BLOCK16 are diagnostic configurations, not universal timing/fidelity proofs.

## E1 execution checkpoint / E2 setup — 2026-09-17

### E1 — MEASUREMENT PROOF / current harness limitation confirmed
The rerun of `Open Homebrew Ares Profile` run **`35227136832`** reused the exact profile-build artifact rather than rebuilding it. Shared build artifact **`10499232867`**, digest **`dac80a1f3911e30e53a7e56e116916977540969035cc8530400776c089996668`**, exact source SHA **`989e1f5ba8d592f6efb8e593d7a83fc5b51f3f89`**.

- attempt1 job **`105221944468`**, result artifact `10499991568`: final state `vi_count=52`, `guest_frame_count=52`, `sample_count=1092`, partial VI `32/60`, partial guest `27`, `frame_wait_count=4`, `queue_count=1`.
- rerun attempt2 job **`105254633842`**, result artifact **`10503143461`**: final state `vi_count=63`, `guest_frame_count=61`, `sample_count=2100`, partial VI `9/60`, partial guest `8`, `frame_wait_count=0`, `queue_count=0`. Settings remain APU21/frameskip0/audio4/precision8.

**SUPPORTED INTERPRETATION:** this is a cleaner binary A/A than previously known because ROM/ELF/map build input is identical, but it is NOT a matched guest-window performance comparison. The two attempts stop at different VI/guest phases and radically different sample counts. The apparent 52-vs-61 totals therefore cannot be interpreted as performance drift or layout gain. It demonstrates that the current wall-time/sample-target stop condition is insufficient authority for ranking small 4–8-frame changes.

**REJECTED inference:** do not call the 2A `52/60` an optimization result; do not use attempt1-vs-attempt2 totals as a measured nine-frame A/A spread; and do not resurrect the historical BLOCK32 causal gain from these numbers. BLOCK32 remains independently REJECTED by paired DSP-lateness.

**Immediate measurement requirement:** before E3/E4/E5 performance ranking, repair or add the smallest possible matched-window boundary: same binary identity, same proven guest checkpoint, several complete sequential VI windows and comparable Count/sample windows. This is a bounded Gate-A measurement repair, not a profiling subproject.

### E2 — cycle-accounting/block-span proof in progress
Branch **`phase2/apu-cycle-proof`** starts from safe tree `225859b1d8fc0eb477a624ac76f8237667379f59`. Current HEAD **`f0159bf9fe6583b106798f2ce4a04708bd6930d2`**, commit `diag: add APU cycle proof capture state`; Build and Validate **`35237136742` SUCCESS**. The commit only adds PROFILE-only diagnostic state and changes no production behavior.

Source inspection sharpened the E2 hypothesis:
- `jit_read8` subtracts one `apu_clock` from compile-time `s2` for each opcode/operand byte; runtime memory accesses debit separately through `apu_read8`/`apu_write8`.
- `apu_alu.S` contains no additional `s2` debit for MUL/DIV internal cycles.
- opcode `0x00` NOP dispatches directly to `next_opcode`, bypassing `finish_opcode`; therefore a sufficiently long NOP run can ignore the nominal `BLOCK_SIZE=16` check until a later opcode reaches `finish_opcode`.
- cache validation records/checks endpoint 64-byte tags. If a generated block can span three or more regions through the NOP bypass, an intermediate-region mutation may be missed. This is **source-supported risk, not yet dynamic proof**.

Pinned ares SPC700 reference at `17813a3c...` independently models total NOP/MUL/DIV/taken-BRA timing as 2/9/12/4 SPC cycles. Sodium64 source currently appears to account isolated fetch units as 1/1/1/2 respectively before data accesses. **HYPOTHESIS:** inherited APU timing undercharges internal instruction cycles, potentially executing excess SPC700 work per emulated time. Magnitude and representative frequency remain UNKNOWN.

The dynamic E2 test must now prove or falsify two things separately: (1) actual generated static debit for BRA-only, NOP+BRA, MUL+BRA and DIV+BRA snippets; (2) actual long-NOP generated span/header behavior, including a middle-region mutation check. No timing fix or optimization is authorized until observation is complete.

## RESUME HERE — E1/E2 checkpoint 2026-09-17

1. Integrated `master` is still `a2270699...`; 2A remains `989e1f5b...`; diagnostic BLOCK16 remains `8805fd61...`; E2 branch is `phase2/apu-cycle-proof@f0159bf9...` and Build/Validate `35237136742` is green.
2. E1 has established a **LAB LIMITATION in the current stopping/measurement boundary**, not a quantified A/A slowdown: exact build artifact `10499232867` was reused, but attempt1 stopped at 52 VI/1092 samples and attempt2 at 63 VI/2100 samples. Small frame-total differences are not causal evidence until matched guest windows exist.
3. Continue E2 with a bounded dynamic proof script/workflow. Observe original JIT only; test BRA, NOP+BRA, MUL+BRA, DIV+BRA and a >128-byte NOP span. Decode generated block static debit and start/end tag regions; then mutate a middle region and test cache re-entry.
4. Falsifiers: any hidden debit that restores reference cycle totals rejects the under-accounting hypothesis; an observed enforced stop before crossing the nominal span rejects the NOP-span hypothesis; a middle-region change that invalidates/recompiles through another mechanism rejects the missed-intermediate-tag hypothesis.
5. If E2 confirms timing under-accounting, make the correction a separate correctness candidate and establish a fresh baseline before optimizing. If E2 falsifies it, return to E3/E4/E5 selection. Separately make the minimal matched-window E1 harness repair before using small ares throughput deltas to rank candidates.
6. 2B remains **DEFERRED, not REJECTED**. Do not merge diagnostic code, reopen BLOCK32, start 65C816 dynarec, move work to RSP, reduce fidelity, or build a second emulator to bypass these questions.

## E2 dynamic proof — CONFIRMED 2026-09-17

Diagnostic branch advanced from the setup checkpoint to **`phase2/apu-cycle-proof@e2ac0c29f5ca4d80b737f714d2d4ae30e91da897`**. Commit `c1e22e9e72dcb7d369113df6cb3ce0d07b04f97f` added the bounded GDB-RSP proof script; `e2ac0c29...` added the branch-only workflow. No production fix was applied.

Exact CI:
- **APU Cycle And Span Proof `35245970304` SUCCESS**, profile-build job `105286137431`, cycle-proof job `105286577504`.
- **Build and Validate `35245970309` SUCCESS** on the same exact SHA.
- proof artifact **`10508131011`**, digest **`sha256:3b6c2a6d1dcfba6f9bc5c89730b23b31a5c12bde366eb6671ae9ccf3bc2a61d0`**.
- exact proof-build artifact **`10507975608`**, digest **`sha256:5bd82c795c02e089ba600f14df4d2bc9a5cc385a88487b30e079491a236ff49a`**.
- pinned ares remains `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`, R4300 JIT + RSP interpreter; Gothicvania source/provenance/settings remain the validated diagnostic substrate.

### E2A — MEASURED: inherited SPC700 cycle under-accounting is real

The proof stops at a safe `apu_execute` scheduler boundary, injects isolated SPC700 snippets, forces a clean JIT lookup entry, stops at `compile_block`, then inspects the exact generated block and its unique emitted `ADDI s3,s3,imm` cycle debit.

| case | source bytes | measured debit | measured source clock units | pinned-reference SPC cycles |
| --- | ---: | ---: | ---: | ---: |
| BRA | 2 | -42 | **2** | **4** |
| NOP + BRA | 3 | -63 | **3** | **6** |
| MUL + BRA | 3 | -63 | **3** | **13** |
| DIV + BRA | 3 | -63 | **3** | **16** |

All measured debits exactly match Sodium64 source prediction and materially disagree with the pinned independent SPC700 reference totals.

**VALIDATED / correctness finding:** for these isolated instructions, Sodium64 is not merely configured with `apu_clock=21`; it actually undercharges guest instruction time. There is no hidden debit restoring NOP/MUL/DIV/BRA reference timing. The previous under-accounting hypothesis is therefore **CONFIRMED for the tested instruction classes**.

**SUPPORTED INTERPRETATION:** inherited timing can execute excess SPC700 instruction work per emulated interval. Correcting timing may therefore improve both fidelity and host cost, but Gothicvania magnitude is still UNKNOWN and no speedup percentage is claimed. Do not globally rescale `apu_clock`: the missing amount is instruction/path dependent.

### E2B — MEASURED: nominal BLOCK_SIZE and endpoint-only invalidation can fail

A controlled `126×NOP + DBNZ Y,-128` source sequence compiled as **128 source bytes** from PC `0x0200` despite `BLOCK_SIZE=16`.

Measured generated header:
- start tag region **8**;
- end tag region **10**;
- source clock units **128**;
- therefore the generated block spans at least **three 64-byte tag regions**.

The proof then changed an actually covered byte in middle region **9** (`0x0240`) from NOP to CLRC and incremented that region's tag exactly as `apu_write8` would. Start/end tags were untouched.

Measured re-entry:
- middle tag **0 -> 1**;
- lookup pointer before/after remained **`2149318676`**;
- JIT pointer before/after remained **`2686189652`**;
- breakpoint on the old generated-code entry was hit with SIGTRAP;
- **`old_block_reentered = true`**.

**VALIDATED / correctness finding:** NOP's direct dispatch to `next_opcode` can bypass the nominal block bound, and the current two-endpoint tag validation can then miss a mutation in an intermediate region and execute stale generated code. This is no longer a source-only risk.

**What E2 does NOT prove:** prevalence in Gothicvania, magnitude of real-game performance impact, or that all SPC700 opcodes have the same timing error. It also does not authorize merging the diagnostic harness.

### Decision after E2

1. **Timing correctness now outranks E3/E4/E5 performance optimization.** Build a separate bounded timing-correction candidate; establish a fresh baseline after semantic validation before attributing any throughput change.
2. Keep timing correction instruction/path-specific. First derive the minimum trustworthy cycle contract from the pinned reference and Sodium64's existing split: opcode/operand fetches are compile-time debits, runtime memory accesses already debit through `apu_read8/apu_write8`, and only the missing internal/taken-branch cycles should be added.
3. Fix the independently confirmed NOP block-bound/invalidation defect as a separate one-variable correctness candidate. The smallest candidate is to route NOP through the normal `finish_opcode` boundary, then rerun the >128-byte span + middle-tag mutation proof. Do not bundle this with timing correction.
4. E1 matched-window repair remains required before ranking small ares throughput deltas. Correctness tests can proceed independently.
5. 2B low-read helper remains **DEFERRED**, not rejected. BLOCK32 remains **REJECTED**.

## RESUME HERE — E2 confirmed 2026-09-17

1. Integrated `master` remains `a2270699...`; active performance 2A remains `989e1f5b...`; E2 diagnostic HEAD is now **`e2ac0c29...`** with both Build/Validate and APU Cycle/Span Proof green. No open PR is implied.
2. Treat E2 as two validated correctness findings: **instruction-cycle under-accounting for tested NOP/MUL/DIV/BRA paths**, and **NOP-driven overlong blocks that can miss intermediate tag invalidation and re-enter stale code**.
3. Next technical batch: create a **separate NOP-bound correctness candidate** from the safe BLOCK16 tree, change only NOP dispatch to obey `finish_opcode`, rerun the long-NOP span/middle-tag proof, and reject if it alters unrelated semantics or still permits >2 tag regions.
4. After that checkpoint, derive and implement the **smallest instruction/path-specific timing correction candidate** supported by the pinned SPC700 reference. Do not globally change `apu_clock`; do not combine timing correction with memory/JIT optimizations.
5. Before performance-ranking any resulting candidate, add the minimal matched-window E1 measurement boundary and establish a fresh baseline. Fidelity/cycle equivalence is required before any speed claim.
6. E3 low-read helper, E4 validation specialization and E5 DSP invariant hoist remain candidates only after timing semantics are on firmer ground. No second emulator, no RSP offload, no scope reduction, no cartridge-assistance pivot.


## NOP-bound candidate running — checkpoint 2026-09-17

Clean one-variable candidate **`phase2/apu-nop-bound-fix@fe5fcc0ca7b817a99095dcde40dc9d37d54d4a18`** starts from safe BLOCK16 tree `225859b1...`. Its only runtime change is opcode `0x00` NOP dispatch in `src/apu_emitter.S`: `next_opcode -> finish_opcode`. No cycle-timing correction is bundled.

Diagnostic child branch **`phase2/apu-nop-bound-proof@0eb17e80fc255bca61c021936b1d040abd87ceb4`** contains only the directed proof script/workflow on top of the clean candidate.

Runs currently in progress:
- candidate Build/Validate **`35283138453`** on exact `fe5fcc0c...`;
- child Build/Validate **`35283273619`** on exact `0eb17e80...`;
- directed **APU NOP Bound Proof `35283273808`** on exact `0eb17e80...`.

Directed question: starting at PC `0x0238` with a long NOP stream, does the clean candidate stop compilation after exactly 16 source bytes at PC `0x0248`, track only tag regions 8->9, and then reject/recompile the old block after an actually covered byte in region 9 is mutated and its tag incremented?

Acceptance requires all three:
- `nop_bound_enforced=true`;
- `bounded_block_tracks_only_two_regions=true`;
- `covered_end_tag_prevents_stale_reentry=true`.

Falsifier: any >16-byte compiled span, unexpected tag-region coverage, or re-entry into the old generated block after the covered end-region tag mutation. If falsified, do not broaden the fix until the exact mechanism is identified.

Do not merge or performance-rank this candidate while the proof is running. Cycle-timing design may proceed from the already-confirmed E2 evidence but remains a separate future candidate.


## SPC700 timing-contract design checkpoint — 2026-09-17

Source audit after E2 establishes the implementation boundary for the future timing correction:

- Across `apu_emitter.S`, `apu_address.S`, `apu_alu.S`, `apu_control.S` and `apu_transfer.S`, the inherited JIT has no general cycle debit beyond:
  1. `jit_read8`: one `apu_clock` per opcode/operand byte fetched at compile time into `s2`;
  2. runtime `apu_read8/apu_write8`: one `apu_clock` per emitted data access into `s3`.
  This explains the E2 measurements structurally: internal/dummy cycles are not hidden elsewhere.

- The pinned ares reference distinguishes several kinds of additional cycles. Many are `idle()`, but many are actual dummy `read(...)` operations (for example NOP performs `read(PC)`; multiple write/implied/control forms also issue reads). A cycle-only debit is therefore not automatically full bus/I/O fidelity. Future work must distinguish **fetch / real data read-write / dummy read / idle**, and preserve ordering when I/O can be touched.

- Conditional branch timing cannot be represented solely by a compile-time fixed debit. In the pinned reference, generic Branch fetches displacement and adds two `idle()` only when taken. Any Sodium64 correction must therefore put taken-only cycles on the emitted taken path rather than charging both outcomes.

- **OPEN QUESTION / source-supported risk:** `menu_close` changes `apu_clock` and sets `jit_pointer = ROM_BUFFER` but does not immediately clear `jit_lookup`. Existing generated blocks already embed their fetch-cycle debit, so a cached block may retain the prior clock value until a later JIT miss reaches `reset_buffer` and clears lookup. This predates the proposed timing work. Do not conflate it with the cycle correction; test/fix separately if the timing candidate depends on clock-setting transitions.

**Architecture direction:** do not use a global `apu_clock` scale and do not add one fixed “cycles per opcode” table that erases bus semantics. Build the timing contract from the exact pinned reference and Sodium64's emitted-access behavior, with constant internal cycles and runtime-conditional cycles represented separately. Dummy reads that can have observable I/O effects require semantic treatment, not just time debit.


## Correction — timed GDB SIGTRAP is not breakpoint identity (2026-09-17)

The first NOP-bound proof exposed a flaw in the diagnostic interpretation used by both the old E2 middle-region probe and the new candidate probe.

ares returns `S05` both for the directed software-breakpoint stops **and for the debugger Ctrl-C stop generated by `continue_then_interrupt()`**. The proof logs themselves demonstrate this: the warmup stop, which is explicitly a timed debugger interrupt, reports `S05`. Therefore `signal_number(reply) == 5` after `continue_then_interrupt(0.5)` does **not** prove that the armed code-entry breakpoint was hit.

**SUPERSEDED:** the earlier literal claim that E2 dynamically proved stale-block re-entry *because* the old-code breakpoint returned SIGTRAP. That breakpoint-identity criterion was invalid.

What remains valid from E2:
- **MEASURED:** the inherited long-NOP block compiled 128 source bytes and spanned header tag regions 8->10.
- **MEASURED:** mutating only covered middle region 9 left start/end tags untouched.
- **STATIC + MEASURED SUPPORT:** `apu_execute` validates only the two header endpoint tags, so this state is sufficient for the old block to pass current validation. Lookup/JIT-pointer also remained unchanged across the old timed probe, but the old SIGTRAP field itself is not authority.
- Final dynamic re-entry confirmation will be rerun without timed-stop ambiguity: after mutation, continue from the safe `apu_execute` boundary to the **first `cpu_execute` return**, then inspect whether lookup/JIT pointer changed. Unchanged means the old block executed; changed means recompilation occurred.

The clean NOP-bound candidate itself was **not falsified** by run `35283273808`; its first two directed properties passed:
- `source_clock_units = 16`;
- PC after block `0x0248`;
- header regions **8->9**.

After mutating the tracked end region 9, the same run measured:
- lookup changed `2149318676 -> 2149318708`;
- JIT pointer advanced `2686189620 -> 2686319648`.

Those measurements are consistent with successful invalidation/recompilation. The run failed only because the invalid `sig==5` criterion marked the timed debugger stop as old-block re-entry. **HYPOTHESIS:** `fe5fcc0c...` fixes the NOP-bound/invalidation defect as intended. Rerun with a first-`cpu_execute` boundary before promoting to VALIDATED.


## Deterministic invalidation reruns running — checkpoint 2026-09-17

The ambiguous timed-SIGTRAP criterion has been removed from both directed probes.

### NOP-bound candidate rerun
Diagnostic child HEAD: **`phase2/apu-nop-bound-proof@200aef5e9d90d739dc00f9250678eb31919a3512`**.
Clean runtime candidate remains unchanged: **`phase2/apu-nop-bound-fix@fe5fcc0ca7b817a99095dcde40dc9d37d54d4a18`**.

Current runs:
- APU NOP Bound Proof **`35283857525`** IN PROGRESS;
- Build and Validate **`35283857526`** IN PROGRESS.

New invalidation method: mutate the tracked end-tag at a safe `apu_execute` boundary, then continue to the **first `cpu_execute` return**. At that boundary exactly one APU block has completed. Lookup/JIT-pointer changed = recompilation before execution return; unchanged = cached block reused. No wall-time/SIGTRAP identity is used.

### Original E2 middle-tag rerun
Corrected diagnostic HEAD: **`phase2/apu-cycle-proof@30be54899133f518b52ca3ba1ddce00070ac812f`**.

Current runs:
- APU Cycle And Span Proof **`35283897586`** QUEUED;
- Build and Validate **`35283897497`** QUEUED.

It repeats the inherited 128-byte long-NOP case, mutates only middle tag region 9 while endpoint tags 8/10 remain untouched, then continues to the first `cpu_execute` return. Unchanged lookup/JIT pointer at that deterministic boundary dynamically confirms stale reuse; changed values falsify the prior dynamic interpretation.

Do not promote/reject the NOP candidate or restate dynamic stale re-entry as VALIDATED until these corrected runs finish.


## SPC700 timing scope sharpened — 2026-09-17

Independent cycle-count cross-check:
- pinned ares implementation remains the primary instruction/bus-sequence reference: `ares@17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`;
- second source checked: `gufranco/sony-spc700-python@50fbd2fb8f4ad8743fc1bca090a7968e25d30a9e`, MIT, whose `conformance/hardware.json` transcribes the Nintendo development-manual Appendix C instruction tables.
- machine check of that pinned hardware table: **17 tables, 256 rows, 256 unique opcode codes, zero duplicates, zero missing opcodes**.
- **28 opcodes have conditional cycle totals**: the eight normal conditional branches, BBS/BBC families, CBNE forms and DBNZ forms. The other **228 opcodes have fixed total cycle counts** in the hardware table.
- `gilyon/snes-tests@5ecdf555da920f0bd7b157542141965a8120186d` is MIT and comprehensive for SPC700 opcode/register/memory semantics, but its own README explicitly says it does **not** test cycle count, dummy reads, S-SMP I/O registers or DSP. Use it later as a semantic-regression guard, not as timing authority.
- SingleStepTests/ProcessorTests contains cycle-by-cycle bus vectors but declares no repository license; do not vendor or make CI depend on its data without a licensing decision.

### Two timing layers must not be conflated

**Layer 1 — total instruction-cycle correctness.**
This is the immediate correction target. Sodium64 currently charges instruction/operand fetch bytes at compile time plus emitted data reads/writes at runtime and omits other cycles. Fixed internal cycles can be represented by compiler-side debit; the 28 conditional branch families need taken-path runtime debit. Existing E2 snippets are an excellent architecture proof: after correction, BRA must be 4 units, NOP+BRA 6, MUL+BRA 13, DIV+BRA 16.

**Layer 2 — intra-block bus/I/O temporal ordering.**
This is a separate accuracy problem. Sodium64 batches `jit_read8` fetch-cycle debt into the generated block-end `ADDI s3,s3,imm`, while runtime data accesses debit `s3` at the access point. Timer reads `read_t0out/read_t1out/read_t2out` compare overflow timestamps directly against current `s3`. Therefore even correct *total* instruction cycles do not automatically prove exact timer/I/O timing inside a multi-instruction JIT block. Dummy reads also need semantic treatment when they can touch I/O.

**Decision:** implement/validate total-cycle correctness first and measure its effect, but label it honestly. Do not claim full SPC700 cycle-accurate I/O until Layer 2 has its own directed tests and solution. This is accuracy debt within Sodium64, not a reason to build a second emulator.


## Layer-1 total-cycle architecture proof running — checkpoint 2026-09-17

Separate experimental runtime branch **`phase2/apu-total-cycle-proof@b268b98b9cf83a9d13a5c59c49c0bd4c585caef8`** was created from the clean NOP-bound candidate `fe5fcc0c...`. It is contingent on the corrected NOP-bound proof and must not be promoted if that parent is falsified.

Runtime changes are deliberately limited to the four already-measured E2 paths:
- compiler-side primitive `jit_debit_cycles` subtracts `apu_clock` from compile-time block debt `s2` once per requested extra guest cycle;
- NOP charges +1 extra cycle;
- BRA charges +2 extra cycles;
- MUL charges +8 extra cycles beyond opcode fetch;
- DIV charges +11 extra cycles beyond opcode fetch.

This is **Layer-1 total-cycle accounting only**. It deliberately does not model NOP/MUL/DIV dummy `read(PC)` bus activity or exact intra-block timer/I/O ordering.

Diagnostic child branch **`phase2/apu-total-cycle-validate@215dc67722462f1fd768e58471ca599cdaf699cf`** adds only the directed GDB proof/workflow.

Current runs:
- APU Total Cycle Proof **`35284371466`** QUEUED;
- child Build and Validate **`35284371446`** PENDING.
(The intermediate child Build/Validate `35284345625` may be superseded/cancelled by the final workflow commit.)

Acceptance is exact and inherited from E2:
- BRA must debit **4** guest cycle units;
- NOP+BRA must debit **6**;
- MUL+BRA must debit **13**;
- DIV+BRA must debit **16**;
- all four must be observed from the exact generated JIT block at the first `cpu_execute` return.

Falsifier: any total differs, generated block lacks a unique `ADDI s3,s3,imm` debit, or Build/Validate fails. A pass validates only the debit primitive and these four paths, not the remaining 252 opcodes and not Layer-2 bus/I/O timing.


## Deterministic invalidation proofs complete — VALIDATED 2026-09-17

The corrected first-`cpu_execute` reruns removed the old timed-SIGTRAP ambiguity and now dynamically settle both sides of the NOP block-bound defect.

### Inherited baseline defect — VALIDATED

Exact diagnostic HEAD: **`phase2/apu-cycle-proof@30be54899133f518b52ca3ba1ddce00070ac812f`**.

Exact CI:
- **APU Cycle And Span Proof `35283897586` SUCCESS**;
- **Build and Validate `35283897497` SUCCESS**.

Inherited long-NOP block:
- 128 source clock units;
- header tag regions **8 -> 10**;
- therefore exceeds nominal `BLOCK_SIZE=16` and spans three 64-byte tag regions.

After changing an actually covered byte in middle region 9 and incrementing only tag 9, while endpoint tags 8/10 remained untouched, then continuing from a safe `apu_execute` boundary to the **first `cpu_execute` return**:
- lookup before/after: **2149318676 -> 2149318676** (unchanged);
- JIT pointer before/after: **2686189652 -> 2686189652** (unchanged);
- `recompiled_before_first_cpu_return = false`;
- `stale_block_reused_without_recompile = true`.

**VALIDATED:** the inherited NOP path can exceed the nominal block bound; endpoint-only validation then misses a covered intermediate-tag mutation and executes the cached stale generated block.

### One-line NOP-bound fix — VALIDATED

Clean runtime candidate remains **`phase2/apu-nop-bound-fix@fe5fcc0ca7b817a99095dcde40dc9d37d54d4a18`**, based on safe `225859b1...`. Its sole runtime change is opcode 0x00 dispatch `next_opcode -> finish_opcode`.

Exact corrected diagnostic HEAD: **`phase2/apu-nop-bound-proof@200aef5e9d90d739dc00f9250678eb31919a3512`**.

Exact CI:
- **APU NOP Bound Proof `35283857525` SUCCESS**;
- child **Build and Validate `35283857526` SUCCESS**;
- clean candidate Build/Validate had already passed on `fe5fcc0c...`.

Measured:
- test PC `0x0238`;
- long source payload remains 128 bytes, but generated block debits exactly **16 source clock units**;
- PC after block **0x0248**;
- header regions **8 -> 9**;
- `nop_bound_enforced = true`;
- `bounded_block_tracks_only_two_regions = true`.

After mutating an actually covered byte at `0x0240` in tracked end region 9 and incrementing tag 9, then continuing to the first `cpu_execute` return:
- lookup **2149318676 -> 2149318708**;
- JIT pointer **2686189620 -> 2686189672**;
- `recompiled_before_first_cpu_return = true`;
- `stale_block_reused_without_recompile = false`;
- `covered_end_tag_prevents_stale_reentry = true`.

**VALIDATED:** `fe5fcc0c...` fixes this specific internal JIT block-bound/invalidation defect with the intended one-line runtime change.

**Scope:** this does not prove every possible generated block is limited to at most two tag regions; other opcode generators can still terminate/bypass differently and require separate reasoning if future evidence points there. It does prove the concrete NOP bypass defect found by E2 and its stale-invalidation consequence.

### Decision

- Promote `fe5fcc0c...` from HYPOTHESIS/CANDIDATE to **VALIDATED** for this defect.
- Keep it separate from SPC700 timing corrections; do not bundle the correctness proof harness into the runtime commit.
- The Layer-1 total-cycle architecture proof may now legitimately use `fe5fcc0c...` as its parent.
- No throughput gain is claimed; E1 matched-window repair remains mandatory before performance ranking.


## Integration hygiene correction — NOP fix rebased cleanly onto master (2026-09-17)

Attempted integration PR **#11** from historical branch `phase2/apu-nop-bound-fix@fe5fcc0c...` exposed a Git-history problem before merge: GitHub reported **27 commits / 8 changed files / +1353 -1** versus current `master@a2270699...`. The runtime NOP change itself remained the validated one-line fix, but the historical safe-tree branch is not a clean integration base relative to current master.

**PR #11 was CLOSED / SUPERSEDED without merge.** Nothing from it entered master.

A new clean integration candidate was created directly from exact current master:
- branch **`phase2/apu-nop-bound-master`**;
- candidate SHA **`eaad08de0f0cc09bada7fe5093c9e8bd5fe3455b`**;
- base **`master@a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`**.

GitHub compare is exact:
- ahead by **1**;
- behind by **0**;
- total commits **1**;
- changed files **1**: `src/apu_emitter.S`;
- diff **+1/-1** only: opcode 0x00 dispatch `next_opcode -> finish_opcode`.

**State:** `fe5fcc0c...` remains the SHA on which the corrected directed proof established the behavior, but it is **SUPERSEDED FOR INTEGRATION** by `eaad08de...`. Because code layout/base changed, rerun the directed NOP proof on a diagnostic child of `eaad08de...` before opening the replacement PR. Do not merge based solely on equivalence of the one source line.


## Active reruns after clean-master integration correction — checkpoint 2026-09-17

### Clean-master NOP fix
Runtime candidate: **`phase2/apu-nop-bound-master@eaad08de0f0cc09bada7fe5093c9e8bd5fe3455b`** (exactly one +1/-1 source line over `master@a2270699...`).

Diagnostic child: **`phase2/apu-nop-bound-master-proof@b89345498664f126049c482c5d54b49c3268bfdd`**.

Current runs:
- clean candidate Build and Validate **`35284543571`** IN PROGRESS;
- directed APU NOP Bound Proof **`35284584269`** IN PROGRESS;
- diagnostic-child Build and Validate **`35284584261`** pending/in progress as GitHub schedules it.

Question/acceptance is unchanged from the already-validated historical-tree proof: exact 16-unit block from PC 0x0238, header 8->9, and tracked end-tag mutation must cause recompilation before first `cpu_execute`. Only after this passes should a replacement integration PR be opened.

### Layer-1 total-cycle proof
Runtime architecture candidate **`phase2/apu-total-cycle-proof@b268b98b9cf83a9d13a5c59c49c0bd4c585caef8`** has now passed **Build and Validate `35284214442` SUCCESS**.

Diagnostic child remains **`phase2/apu-total-cycle-validate@215dc67722462f1fd768e58471ca599cdaf699cf`**:
- child Build and Validate **`35284371446` SUCCESS**;
- directed APU Total Cycle Proof **`35284371466` IN PROGRESS**.

Do not generalize the timing mechanism until the directed totals are observed as exactly BRA=4, NOP+BRA=6, MUL+BRA=13, DIV+BRA=16.


## Layer-1 total-cycle architecture proof — VALIDATED for four paths 2026-09-17

Experimental runtime HEAD: **`phase2/apu-total-cycle-proof@b268b98b9cf83a9d13a5c59c49c0bd4c585caef8`**.
Diagnostic child HEAD: **`phase2/apu-total-cycle-validate@215dc67722462f1fd768e58471ca599cdaf699cf`**.

Exact CI:
- runtime **Build and Validate `35284214442` SUCCESS**;
- child **Build and Validate `35284371446` SUCCESS**;
- **APU Total Cycle Proof `35284371466` SUCCESS**.

Exact generated-block measurements at `apu_clock=21`:
- BRA: debit **-84 = 4 guest cycle units**, expected 4;
- NOP+BRA: debit **-126 = 6 units**, expected 6;
- MUL+BRA: debit **-273 = 13 units**, expected 13;
- DIV+BRA: debit **-336 = 16 units**, expected 16;
- `all_total_cycle_cases_match = true`.

**VALIDATED / ARCHITECTURE PROOF:** a compiler-side extra-cycle debit can represent the missing Layer-1 total guest cycles for the tested fixed/taken paths without changing memory fast paths. The four E2 mismatches are corrected exactly by this mechanism.

**Not proven / scope:** this does not validate the remaining 252 opcodes, conditional branch taken/not-taken handling, dummy-read bus effects, timer/I/O ordering, or any performance gain. It is Layer-1 total-cycle accounting only.

**Integration hygiene:** `b268b98b...` descends from the historical safe-tree NOP candidate `fe5fcc0c...`, whose Git history was later shown not to be a clean current-master integration base. Therefore `b268b98b...` is **VALIDATED AS AN ARCHITECTURE PROOF ONLY / NOT AN INTEGRATION CANDIDATE**. Reapply the mechanism on the clean current-master line after the clean NOP candidate `eaad08de...` is revalidated/merged, then rerun this proof before any PR.

### Next timing batch

Generalize Layer-1 timing by **semantic families**, not 256 ad-hoc fixes:
1. preserve fixed-cycle totals with compiler-side debt;
2. implement the 28 conditional opcode families with taken-path-only extra debit;
3. keep existing runtime data-access debits intact;
4. separately preserve/defer dummy-read and intra-block I/O semantics as Layer 2;
5. validate against the complete 256-opcode Nintendo cycle table, with targeted dynamic proof before performance interpretation.

Do not performance-rank until E1 matched-window measurement is repaired.


## Compatibility finding from 256-opcode audit — 2026-09-17

Crossing current `master`'s `jit_opcodes` table against the complete 256-opcode hardware table exposed a separate non-timing compatibility hole:

- opcode **0xBE = DAS A** maps to `apu_unk`;
- opcode **0xDF = DAA A** maps to `apu_unk`;
- `apu_unk` explicitly emits code that leaves the SPC700 PC on the unimplemented opcode, effectively looping there.
- opcodes **0xEF = SLEEP** and **0xFF = STOP** also map to `apu_unk`, but these are special control states and need their own semantics; do not conflate them with DAA/DAS.

**VALIDATED / static source finding:** DAA and DAS are legal SPC700 instructions but are currently unimplemented in Sodium64. This is a **COMPATIBILITY PROOF / REQUIRED SUPPORT** issue for the 1.0 accuracy target, independent of the current Layer-1 timing correction.

Do not bundle DAA/DAS implementation into the active NOP-bound integration or four-path total-cycle proof. Add directed semantic tests before implementation, using pinned ares plus an independent opcode semantic reference where licensing permits.


## E2 dynamic proof — CONFIRMED 2026-09-17

**MEASUREMENT PROOF / ARCHITECTURE PROOF.** The source-backed SPC700 timing and JIT-span risks were dynamically reproduced without modifying the APU core.

Authority run: **APU Cycle And Span Proof `35283897586`**, exact diagnostic SHA **`30be54899133f518b52ca3ba1ddce00070ac812f`**, jobs `105411838100` + `105412186149`, result artifact **`10523267264`** (digest `sha256:cdd4f4f47d23a59c47b851ea520dc169d59610cd5cea2412805f85c344bcdc69`). Exact proof build artifact **`10523307069`** (digest `sha256:300306b450239f895f20fad59483b5be801cba5d1f0e57280eef7849a124699c`).

Direct compare `225859b1... -> 30be5489...` is diagnostic-only: `.github/workflows/apu-cycle-proof.yml`, `scripts/apu_cycle_proof.py`, and `src/apu_cycle_diag.S`. **No APU/JIT production source is changed by the measured SHA.**

### E2-A — MEASURED: inherited SPC700 instruction timing under-accounting is real

Dynamic generated-code inspection reproduced the exact source-predicted debit at `apu_clock=21`:

| snippet | Sodium64 charged clock units | independent SPC700 reference cycles |
| --- | ---: | ---: |
| BRA | 2 | 4 |
| NOP + BRA | 3 | 6 |
| MUL + BRA | 3 | 13 |
| DIV + BRA | 3 | 16 |

Exact emitted debits were BRA `-42`, NOP+BRA `-63`, MUL+BRA `-63`, DIV+BRA `-63`. The generated blocks returned to the expected PCs and the emitted `ADDI s3,s3,imm` matched the static accounting prediction in every case.

**CONFIRMED:** configured `apu_clock=21` is NOT equivalent to instruction-accurate full-rate SPC700 timing. The inherited JIT omits instruction-internal/taken-branch timing work for the tested opcodes. This is a correctness defect, not merely a profiler attribution issue.

**SUPPORTED INTERPRETATION:** correcting guest timing can plausibly reduce excess SPC700 host work while improving fidelity, because Sodium64 currently advances more SPC700 instructions per emulated-time budget than these reference timings permit. The magnitude on Gothicvania remains UNKNOWN until a correctness candidate exists and is measured. Do not apply a single global clock multiplier; the discrepancy is instruction-specific.

### E2-B — MEASURED: BLOCK_SIZE=16 is not a universal generated-block bound

The long diagnostic snippet `126*NOP + DBNZ Y,-128` compiled as one **128-source-byte** block. Header coverage was region **8 -> 10**, despite nominal `BLOCK_SIZE=16`. Emitted debit was `-2688` = 128 configured clock units.

This dynamically confirms the NOP bypass: opcode `0x00` dispatches directly to `next_opcode` and therefore skips the `finish_opcode` limit check.

### E2-C — MEASURED: endpoint-only tag validation can reuse stale generated code

After compiling the three-region block, the proof mutated an actually covered byte in middle region **9** and incremented that region's JIT tag exactly as `apu_write8` would. Start/end region tags were left unchanged.

On the next safe APU re-entry:
- lookup pointer unchanged;
- JIT pointer unchanged;
- no recompile occurred before the first `cpu_execute` return;
- **stale generated block was reused.**

Therefore the inherited two-endpoint validation is insufficient whenever a generated block spans an untracked intermediate 64-byte region.

### Decision

**E2 is closed as CONFIRMED, not hypothesis.** The immediate M1 route changes again:

1. First make a **minimal block-bound correctness candidate** so every ordinary NOP also passes the existing `finish_opcode` boundary check. Before accepting it, prove no other opcode path can similarly bypass the bound and rerun the long-span/middle-tag proof.
2. Then design an instruction-accurate SPC700 timing model. Do not patch only NOP/MUL/DIV/BRA as a permanent architecture and do not globally scale `apu_clock`; derive/validate the missing internal and conditional cycles systematically against an independent reference.
3. After timing correction, establish a fresh correctness/performance baseline; old 44/48/52/61 ares totals are not directly comparable as “full-rate” performance because the guest timing contract was wrong.
4. E3 low-read, E4 validation specialization and E5 DSP invariant work remain **DEFERRED** until the corrected timing/block contract exists. A performance optimization of an over-executing guest is currently lower value than fixing the guest-time definition itself.

The current diagnostic branch moved after the authority run for additional PROFILE-only cross-check instrumentation; do not confuse those later diagnostic commits with the measured authority SHA `30be5489...`.

## RESUME HERE — E2 confirmed / correctness-first pivot 2026-09-17

1. Integrated `master` remains **`a2270699...`**. Safe M1 tree remains **`225859b1...`**. E2 authority is diagnostic SHA **`30be5489...`**, run **`35283897586`**, not the later diagnostic HEAD.
2. **CONFIRMED:** tested SPC700 opcodes are undercharged in guest cycles; `apu_clock=21` alone does not prove full-rate timing.
3. **CONFIRMED:** long NOP sequences can bypass `BLOCK_SIZE=16`, span 3 tag regions, and a middle-region tag mutation can reuse stale generated code because cached validation checks only endpoint tags.
4. Next controlled change: prove the NOP path is the only direct `next_opcode` bypass, then test a minimal NOP->`finish_opcode` block-bound fix on the diagnostic harness. If it restores <=16-byte span and removes the middle-region stale-reuse condition without semantic regression, recreate it as a clean code-only candidate from the safe tree.
5. In parallel, map the complete SPC700 missing-cycle contract from the pinned independent reference before implementing timing correction. Prefer a systematic model of internal/conditional cycles over per-game or global-clock hacks.
6. After correctness candidates, create a fresh matched-window baseline (E1 repair remains required) before ranking small throughput deltas.
7. 2B/E3, E4, E5 are **DEFERRED**. BLOCK32 remains REJECTED. No 65C816 dynarec/RSP offload/second emulator/cartridge assist is justified by this evidence.


## M1 block-bound correction — dynamic validation 2026-09-17

**VALIDATED in diagnostic harness.** The one-variable core change maps SPC700 NOP opcode `0x00` from direct `next_opcode` dispatch to the existing `finish_opcode` path, so NOP now obeys the same `BLOCK_SIZE` check as every other ordinary opcode.

Diagnostic branch HEAD for the proof: **`9880e2e146d3e48f9f7819654e792ae302bee275`**. The production-semantic change itself is commit **`31ad646a1221e7b55cc9a1efa4f2c74354049f73`**; later commits only adjust the proof expectations/reporting. Build and Validate **`35287658874` SUCCESS**.

Dynamic authority: **APU Cycle And Span Proof `35287658903` SUCCESS**, cycle-proof job **`105423781476`**, result artifact **`10525480018`** digest `sha256:2d7d1d311cf38bd9b5a2d7e82a70ae4cca63ed07d9795d8c197b0170731a4c5c`; exact proof-build artifact **`10524349509`** digest `sha256:c185e321272c28dc2ded529863e6a1521c52ea3d2e07073e617d640a04ecafc2`.

The same 128-byte source probe that previously compiled across regions 8->10 now produced:
- `cycle_debit=-336` = **16 configured clock units**;
- `apu_count_after_block=0x0210`, exactly 16 source bytes after `TEST_PC=0x0200`;
- JIT header start/end region **8 -> 8**;
- generated block 20 bytes;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`;
- middle-region mutation probe **not applicable**, because the bounded block no longer contains an untracked intermediate tag region.

BRA/NOP+BRA/MUL+BRA/DIV+BRA retained their previous under-accounted timing observations, proving the block-bound fix did not accidentally alter the separate timing defect.

Source-wide search found no other opcode-table/generator path that directly jumps to `next_opcode`; NOP was the only opcode bypassing `finish_opcode`. Therefore the narrow fix closes the dynamically demonstrated multi-region endpoint-tag stale-code condition for the audited path without changing tag architecture.

**Decision:** preserve this as a clean code-only candidate from safe tree `225859b1...`; do not carry PROFILE instrumentation/workflow changes into the candidate. Timing correctness remains the next gate driver.

## RESUME HERE — block bound validated / timing contract next

1. `master` remains `a2270699...`. E2 under-accounting authority remains `30be5489...` / run `35283897586`.
2. NOP block-bound fix is **VALIDATED in diagnostic harness** by run `35287658903`: 128-byte source probe is now bounded to 16 bytes/one tag region; the previously reproduced middle-tag stale-code condition cannot arise in that probe.
3. Create/verify a clean branch from `225859b1...` containing ONLY the NOP table mapping `next_opcode -> finish_opcode`; normal Build/Validate must pass. Keep diagnostic machinery out of the code candidate.
4. Then continue timing correctness. Current evidence says the inherited timing model undercharges not only internal idles but also dummy bus cycles; a global `apu_clock` scale is REJECTED as architecture.
5. Preferred timing direction: retain current data-access timing initially, add missing guest-cycle charges systematically by shared addressing/operation/control families, and emit conditional extra cycles for taken branches. Validate total cycles first, then refine I/O/timer cycle placement where needed.
6. A pinned independent cycle table agrees with ares for audited NOP/BRA/MUL/DIV values and can serve as host-test oracle/supporting evidence; ares dynamic semantics remain the primary independent reference.
7. E1 matched-window repair remains required before small performance ranking. E3/E4/E5 remain DEFERRED until timing contract is corrected enough to establish a new baseline.


## Clean block-bound candidate — CI validated 2026-09-17

Clean candidate branch **`phase2/apu-block-bound-fix@7e48bcc994483e7aaf7cc2793b03fe0ebf13ee84`** was recreated directly from safe tree `225859b1d8fc0eb477a624ac76f8237667379f59`.

Direct compare is exactly one file, **`src/apu_emitter.S +1/-1`**: opcode `0x00` NOP maps from `next_opcode` to `finish_opcode`. No diagnostic source, workflow, profiler or other runtime code is present.

**Build and Validate `35288085787` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.
Normal build artifact ID `10524987296`; PROFILE build artifact ID `10524444940`.

Combined with dynamic ares proof `35287658903`, this candidate is **VALIDATED** for the demonstrated block-bound/stale-middle-tag defect. It is not yet merged; keep it as the clean base for APU timing-correctness work so timing can be tested without reintroducing the NOP span bug.

### Timing-model design constraint learned during the same batch

Pinned ares reference confirms the missing timing is structurally regular, not just MUL/DIV special cases:
- indexed addressing introduces idle cycles;
- pure stores perform dummy/read-before-write cycles;
- many implied/register operations perform a dummy `read(PC)`;
- conditional taken branches add two cycles;
- MUL/DIV/XCN and similar operations have internal cycles.

Sodium64 currently batches opcode/operand fetch debits in compile-time `s2` and emits that debit at block end, while `apu_read8/apu_write8` debit data accesses at runtime. Timer/control paths observe `s3`; therefore the first correction should **preserve existing data-access debit placement** and add only missing guest cycles. This minimizes semantic movement while making total instruction timing correct. Exact intra-instruction bus-cycle placement remains a later fidelity refinement, not something to silently claim from the first timing candidate.

## RESUME HERE — clean block fix validated; timing proof mechanism next

1. `master` remains `a2270699...`. Clean block-bound candidate is **`phase2/apu-block-bound-fix@7e48bcc9...`**, one-line core diff, Build/Validate `35288085787` SUCCESS.
2. Dynamic authority for the block fix remains diagnostic run `35287658903`: long probe bounded to 16 source bytes / one tag region.
3. Next technical batch: on diagnostic `phase2/apu-cycle-proof`, introduce one shared compile-time mechanism for **missing guest cycles** and exercise it only on the already-audited NOP/BRA/MUL/DIV cases. Expected corrected sequence totals: BRA4, NOP+BRA6, MUL+BRA13, DIV+BRA16; 16 NOPs should debit32 cycles while still ending after16 source bytes.
4. This four-opcode step is a **mechanism proof, not the permanent timing coverage**. If validated, recreate the mechanism cleanly from `7e48bcc9...` and expand systematically by shared addressing/operation/control families plus runtime conditional charges for taken branches.
5. Do not remove `apu_read8/write8` timing debits yet. Do not globally scale `apu_clock`. Do not claim exact intra-instruction I/O timing until dedicated timer/port tests prove it.
6. E1 matched-window repair remains necessary before ranking small performance changes. E3/E4/E5 remain DEFERRED.


## Timing mechanism proof in progress — checkpoint 2026-09-17

Diagnostic branch **`phase2/apu-cycle-proof@842a14127669ce176c808ddcd718d0987d351223`** now contains a bounded mechanism proof for missing SPC700 guest cycles. This is NOT full timing coverage and is not a merge candidate.

Controlled semantic changes relative to the prior bounded-NOP diagnostic:
- shared compile-time helper `jit_charge_cycles(t0)` converts a count of missing SPC700 cycles into `apu_clock` master-cycle debit accumulated in JIT compiler `s2`;
- NOP charges +1 missing cycle then reaches `finish_opcode`;
- BRA charges +2 missing cycles;
- MUL charges +8 missing cycles;
- DIV charges +11 missing cycles;
- existing `apu_read8/apu_write8` runtime data-access debits are unchanged.

Expected audited totals at `apu_clock=21`:
- BRA: 4 guest cycles / debit `-84`;
- NOP+BRA: 6 / `-126`;
- MUL+BRA: 13 / `-273`;
- DIV+BRA: 16 / `-336`;
- 16 compiled NOPs from the 128-byte source probe: 32 guest cycles / `-672`, while source span must remain exactly 16 bytes and header region 8->8.

**Build and Validate `35288358663` SUCCESS** for exact SHA `842a1412...`: normal build, PROFILE build and pinned Mupen emulator smoke all green.

**Long experiment in progress:** APU Cycle And Span Proof **`35288358655`**, profile-build already SUCCESS; cycle-proof job **`105425907529`** is currently building pinned ares before executing the dynamic cases.

Question: does one shared compile-time missing-cycle mechanism reproduce independent SPC700 total cycles for the four already-audited fixed-cycle cases without undoing the validated NOP block bound?

Readings:
- all exact debits + 16-byte bound pass => mechanism **VALIDATED only for these audited fixed-cycle cases**; proceed to one separate addressing-family timing batch;
- debit mismatch => inspect helper/accounting composition, do not expand coverage;
- PC/span/header mismatch => reject mechanism as semantically intrusive;
- smoke/proof regression => reject candidate.

Do not interpret performance from this run. E1 matched-window measurement repair remains required for later throughput comparison.


## SPC700 missing-cycle mechanism — VALIDATED for audited fixed-cycle cases 2026-09-17

Exact diagnostic SHA: **`842a14127669ce176c808ddcd718d0987d351223`**.

**Build and Validate `35288358663` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.

Dynamic authority: **APU Cycle And Span Proof `35288358655` SUCCESS**, cycle-proof job **`105425907529`**.
- proof result artifact **`10525930543`**, digest `sha256:93adfb95e6ea06efa38d5ed2723f562b229544ec47d8d62e17930528b0a78832`;
- exact proof-build artifact **`10524814779`**, digest `sha256:48d4ac8e9d9a85b99aaa8a7478b9b2397b325f4fc8ec7b4066aa63eed11f022c`.

Measured generated JIT debit at `apu_clock=21`:
- BRA: **`-84` = 4 guest cycles**, reference 4;
- NOP+BRA: **`-126` = 6**, reference 6;
- MUL+BRA: **`-273` = 13**, reference 13;
- DIV+BRA: **`-336` = 16**, reference 16;
- 16 compiled NOPs from the 128-byte source probe: **`-672` = 32 guest cycles**, PC `0x0200 -> 0x0210`, header 8->8.

All static debit expectations and all span expectations passed. Middle-region stale-code probe remained not applicable because the block stayed within one tag region.

**VALIDATED scope:** the shared compile-time `jit_charge_cycles` mechanism can add missing fixed guest cycles without disturbing the demonstrated JIT block bound for these audited cases.

**NOT YET PROVEN:** complete SPC700 cycle coverage, taken/not-taken conditional timing, exact intra-instruction I/O/timer bus timing, or performance impact. Do not merge a four-opcode-only timing correction as if it were complete.

### Decision
Proceed with timing coverage by **shared addressing families first**, using the same mechanism and preserving existing runtime `apu_read8/apu_write8` data-access debits. For that batch, measure the actual R4300 `s3` delta from `compile_block` entry to the first `cpu_execute` return, so reference totals include both compile-time debit and runtime memory-helper debit.

Representative matrix should cover at least:
- direct read vs direct write;
- direct indexed read vs write;
- (X) read vs write;
- (X)+ read/write;
- absolute read vs write;
- absolute indexed read vs write;
- indexed-indirect read vs write;
- indirect-indexed read vs write.

Expected missing-cycle rule from pinned ares reference:
- unindexed direct/absolute read: +0; write: +1 dummy read;
- indexed read: +1; indexed write: +2;
- (X) read: +1; (X) write: +2;
- (X)+ read/write: +2;
- indexed/indirect read: +1; write: +2.

Keep branch conditional +2 timing as a separate later batch.

## RESUME HERE — mechanism validated; addressing-family timing next

1. `master` remains `a2270699...`. Clean block-bound candidate `phase2/apu-block-bound-fix@7e48bcc9...` remains VALIDATED and unmerged.
2. Missing-cycle mechanism proof `842a1412...`, run `35288358655` is **VALIDATED for NOP/BRA/MUL/DIV only**; exact cycle totals match pinned independent reference.
3. Next batch on diagnostic branch: extend proof harness to read GDB R4300 register **s3 = GPR19 / RSP packet `p13`** at `compile_block` and first `cpu_execute` return. Pinned ares N64 hook returns each GPR as a 16-hex-digit u64, so this can measure total master-cycle debit including runtime memory helpers.
4. Apply one controlled class of timing corrections: addressing-family missing cycles only. Validate representative read/write pairs against reference totals and semantics. Do not include conditional branch timing in this batch.
5. If addressing-family proof passes, checkpoint and recreate timing mechanism + validated addressing rules cleanly from `7e48bcc9...`; then proceed to conditional branches as a separate variable.
6. E1 matched-window repair remains required before performance ranking. E3/E4/E5 remain DEFERRED until timing baseline is meaningfully corrected.


## Addressing-family timing proof in progress — checkpoint 2026-09-17

Exact diagnostic SHA: **`19b3d6cfe7c042109fe08bc08e44eac0a9abb510`**, one commit ahead of validated mechanism SHA `842a1412...`.

Controlled class under test: **SPC700 addressing-family missing guest cycles only**. No conditional branch timing changes are included.

Core diagnostic changes:
- direct pure-write address path: +1 dummy destination-read cycle;
- direct X/Y indexed: +1 for reads/modifies, +2 for pure writes;
- `(X)`: +1 for reads, +2 for pure writes;
- `(X)+`: +2 for read and write directions;
- absolute pure stores use a new `apu_absw` wrapper with +1, while CALL/JMP retain uncharged `apu_absa`;
- absolute X/Y indexed: +1 read, +2 write;
- `[dp+X]` and `[dp]+Y`: +1 read, +2 write.
Existing runtime `apu_read8/apu_write8` data-access debits remain unchanged.

The proof harness now reads ares R4300 **GPR19 / s3 using RSP `p13`** at `compile_block` and at the first `cpu_execute` return. Pinned ares N64 debug hook returns GPRs as 16-hex-digit u64 values, so the signed delta measures total generated-block master-cycle debit including runtime memory helpers.

Representative matrix adds 16 cases:
direct read/write; direct+X read/write; `(X)` read/write; `(X)+` read/write; absolute read/write; absolute+X read/write; `[dp+X]` read/write; `[dp]+Y` read/write. Each checks static debit, total `s3` debit vs independent reference cycles, PC/header span, and a semantic postcondition (A/X or written RAM).

Direct compare `842a1412... -> 19b3d6cf...` is exactly:
- `.github/workflows/apu-cycle-proof.yml` +16/-6;
- `scripts/apu_cycle_proof.py` +179/-2;
- `src/apu_address.S` +54/-0;
- `src/apu_emitter.S` +3/-3.

Runs launched for exact SHA:
- **Build and Validate `35289165618`** — queued at checkpoint.
- **APU Cycle And Span Proof `35289165637`** — queued at checkpoint.

Acceptance requires ALL of:
1. normal + PROFILE build + Mupen smoke green;
2. existing BRA/NOP/MUL/DIV and NOP-span regressions remain green;
3. all 16 addressing cases match exact static expected debit;
4. measured total `s3` debit equals pinned independent reference cycle total ×21;
5. semantic postconditions and one-region block bound remain correct.

Any mismatch rejects or narrows the family rule; do not paper over a failure by adjusting the reference expectation without reconciling the pinned ares instruction sequence.


## Addressing proof attempt 1 — harness false negative 2026-09-17

Exact diagnostic SHA **`19b3d6cfe7c042109fe08bc08e44eac0a9abb510`**:
- Build and Validate **`35289165618` SUCCESS**: normal build, PROFILE build, pinned Mupen smoke all green.
- APU Cycle And Span Proof **`35289165637` FAILURE**, cycle-proof job `105428441273`.

The failure is **REJECTED as core evidence**. It occurred before any of the 16 new addressing-family cases ran.

Measured legacy regression cases before the stop all passed total-cycle measurement through R4300 `s3`:
- BRA: `s3 1064 -> 980`, delta **-84 = 4 cycles**;
- NOP+BRA: delta **-126 = 6**;
- MUL+BRA: delta **-273 = 13**;
- DIV+BRA: delta **-336 = 16**;
- long bounded NOP probe: delta **-672 = 32**, header 8->8, static debit -672, PC after block **0x0210**.

Harness bug: the newly added generic semantic check assumed every case must return `apu_count == TEST_PC (0x0200)`. That is wrong for the bounded long-NOP regression case, whose correct postcondition since the validated block-bound fix is `0x0210` after compiling/executing exactly 16 NOPs. The harness therefore raised `long_nop_dbnzy: semantic postcondition mismatch` despite its cycle/span result being correct.

**Decision:** fix only the diagnostic expected-PC postcondition for the long probe and rerun the exact addressing batch. Do not change core timing rules or reference cycle expectations based on this failure. The 16 addressing-family cases remain **UNMEASURED** by this attempt because execution stopped before reaching them.


## SPC700 addressing-family timing — VALIDATED 2026-09-17

Exact diagnostic SHA **`e78b3c47989359c3796887d00da9dcca56740e2b`** (core timing rules identical to `19b3d6cf...`; final commit only fixes the bounded-NOP diagnostic expected-PC postcondition).

**Build and Validate `35294386630` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

Dynamic authority: **APU Cycle And Span Proof `35294386627` SUCCESS**, cycle-proof job **`105444053413`**.
- result artifact **`10527331782`**, digest `sha256:3ddaf910afbb446093aa9fe154756f8e507d52633a05a18b29b96aba31e51f0b`;
- exact proof-build artifact **`10526324943`**, digest `sha256:92d3fcd835b0bebc9f4e7b662baa2216557a4c0cd1554b50f23cb1d3f75046c5`.

All 16 representative addressing cases matched:
- compile-time/static debit prediction;
- total runtime R4300 `s3` debit against pinned ares SPC700 cycles × `apu_clock=21`;
- expected register or RAM semantics;
- expected one-region JIT span.

Measured total sequence cycles (tested instruction + corrected 4-cycle BRA loop):
- direct read/write: **7 / 8**;
- direct+X read/write: **8 / 9**;
- `(X)` read/write: **7 / 8**;
- `(X)+` read/write: **8 / 8**;
- absolute read/write: **8 / 9**;
- absolute+X read/write: **9 / 10**;
- `[dp+X]` read/write: **10 / 11**;
- `[dp]+Y` read/write: **10 / 11**.

The measured total `s3` debit was exact in every case; e.g. direct read -147 (7), direct write -168 (8), absolute+X write -210 (10), indexed/indirect writes -231 (11).

Existing fixed-cycle regressions BRA/NOP/MUL/DIV and bounded 16-NOP block also remained green. Summary flags all true:
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`all_semantics_match_expected`,
`all_header_spans_match_source_prediction`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

### Interpretation / scope

**VALIDATED:** the shared missing-cycle mechanism plus audited addressing-family rules correctly reconstruct total SPC700 guest timing for the tested ordinary byte read/write paths while retaining existing runtime memory-helper timing.

**NOT PROVEN:** every opcode that happens to reuse one of these address generators is fully cycle-correct. Special operations such as word operations, read-modify-write, stack/control and other multi-access instructions may have additional operation-specific cycles and need their own family proof. Addressing correction is a component of their timing, not automatic proof of the whole instruction.

The previous attempt `35289165637` is retained as **HARNESS FALSE NEGATIVE / REJECTED AS CORE EVIDENCE**: it stopped on the long-NOP expected-PC bug before any addressing case ran.

### Decision

Recreate the validated semantic core cleanly from **`phase2/apu-block-bound-fix@7e48bcc9...`**:
- shared fixed-cycle charge mechanism;
- NOP dummy-cycle timing while retaining block bound;
- BRA fixed +2;
- MUL +8 / DIV +11;
- validated addressing-family rules including pure absolute-store wrapper.
No PROFILE diagnostic state, GDB harness or proof workflow belongs in the clean candidate.

Then run normal Build/Validate on the clean candidate. Conditional taken-branch timing remains the next separate variable and must use a runtime-only debit on the taken path, not compile-time `s2`.

## RESUME HERE — addressing validated; clean timing candidate next

1. `master` remains `a2270699...`.
2. Clean block-bound base: `phase2/apu-block-bound-fix@7e48bcc9...`, VALIDATED.
3. Fixed-cycle mechanism: `842a1412...` / run `35288358655`, VALIDATED for NOP/BRA/MUL/DIV.
4. Addressing timing: `e78b3c47...` / run `35294386627`, VALIDATED for 16 representative byte read/write cases with exact total `s3` timing and semantics.
5. Immediate action: create a clean timing-correctness branch from `7e48bcc9...` containing only validated semantic core changes; verify diff and Build/Validate.
6. Next controlled timing batch after that: conditional branches. Emit the +2 taken-cycle debit in generated MIPS only on the taken path. Test both taken and not-taken for ordinary condition flags, bit branches, CBNE, DBNZ memory and DBNZ Y.
7. Special operation families (word/RMW/implied/stack/call/return/XCN/etc.) remain TODO and must not be declared corrected by addressing validation alone.
8. E1 matched-window repair remains required before performance ranking. E3/E4/E5 remain DEFERRED.


## Clean SPC700 timing candidate — checkpoint 2026-09-17

Clean branch **`phase2/apu-timing-correctness@1248bc98e9f71e37d3f384bf3f8aef243022e4e4`** was created directly from validated clean block-bound base `7e48bcc994483e7aaf7cc2793b03fe0ebf13ee84`.

It is exactly one commit ahead of that base and modifies only four production core files:
- `src/apu_address.S` +47;
- `src/apu_alu.S` +8;
- `src/apu_control.S` +4;
- `src/apu_emitter.S` +23/-4.

Explicit audit found **zero** `SODIUM64_PROFILE` or `apu_cycle_diag` references in the clean emitter. No workflow, harness, diagnostic state or profiling source is present.

Included semantic scope is only already-validated work:
- retained NOP BLOCK_SIZE bound from the base;
- shared compile-time missing-cycle helper;
- NOP dummy cycle;
- unconditional BRA +2;
- MUL +8 / DIV +11;
- validated ordinary addressing-family fixed cycles;
- pure absolute-store wrapper so CALL/JMP do not inherit store timing.

Exact clean CI launched: **Build and Validate `35294889292`** for SHA `1248bc98...`. An earlier run `35294839654` belongs to the transient branch-creation base SHA `7e48bcc9...` and is not authority for the clean timing commit.

Next action remains conditional taken-branch timing only after `35294889292` is green.


## Clean SPC700 timing candidate — CI VALIDATED 2026-09-17

Clean production candidate **`phase2/apu-timing-correctness@1248bc98e9f71e37d3f384bf3f8aef243022e4e4`** passed **Build and Validate `35294889292` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

The candidate remains exactly one clean semantic commit over `7e48bcc9...`, touching only `apu_address.S`, `apu_alu.S`, `apu_control.S`, and `apu_emitter.S`. It carries no diagnostic workflow/state.

This candidate is therefore **CANDIDATE / CI-VALIDATED**, backed by the independent ares dynamic proofs already recorded for its included timing rules. It is not yet merged because SPC700 timing coverage is intentionally continuing before integration.

### Conditional-branch design refinement

Static comparison to pinned ares shows the next branch batch must not be modeled as a uniform “taken +2 only” rule:

- ordinary flag branches (BPL/BMI/BVC/BVS/BCC/BCS/BNE/BEQ): base 2 cycles, **+2 only if taken**;
- BBC/BBS: base includes **+1 fixed idle** beyond existing fetch/data accounting, then **+2 if taken**;
- CBNE direct/direct+X: operation contributes **+1 fixed idle** beyond the addressing timing already validated, then **+2 if taken**;
- DBNZ memory: base is already composed by fetch/read/write/fetch accounting, then **+2 if taken**;
- DBNZ Y: **+2 fixed** (dummy PC read + idle) beyond fetch accounting, then **+2 if taken**.

Architecture for the taken surcharge: emit one generated MIPS `ADDI s3,s3,-(2*apu_clock)` only on the taken path. Compute its immediate at JIT compile time from configured `apu_clock`; do not add a runtime helper call per branch.

Efficient control-flow shape: branch on the **not-taken** condition over the taken-only debit/PC assignment, using the branch delay slot to set the fallthrough SPC PC. Taken path then executes one timing `ADDI` and overwrites SPC PC with the target. This avoids charging not-taken paths and avoids a runtime call.

## RESUME HERE — clean timing core green; conditional branches next

1. Clean current candidate: `phase2/apu-timing-correctness@1248bc98...`, Build/Validate `35294889292` SUCCESS.
2. Diagnostic addressing authority remains `e78b3c47...` / ares proof `35294386627` SUCCESS.
3. Next technical batch should be diagnostic first: add an emitter helper that emits a runtime cycle-debit `ADDI`, then update conditional branch generators with fixed family charges plus taken-only +2.
4. Proof both taken and not-taken paths. Minimum coverage: all eight ordinary condition branches, BBC/BBS, CBNE direct and direct+X, DBNZ memory, DBNZ Y. Check total `s3` cycles, resulting PC, and memory/Y side effects where applicable.
5. Only after that proof passes, port the validated branch timing into the clean `apu-timing-correctness` candidate.
6. Special non-branch operation families remain TODO. E1 matched-window repair still gates performance ranking.


## Conditional branch timing proof in progress — checkpoint 2026-09-17

Exact diagnostic SHA: **`a435d8f8af05db4e155304812161adb295adf130`**, one conceptual commit over validated addressing diagnostic `e78b3c47...`.

Question: can Sodium64 reproduce SPC700 conditional branch timing exactly while charging the **+2 taken cycles only on the runtime-taken path**, without adding a runtime helper call or disturbing PC/side effects?

Controlled diagnostic changes:
- add generated-MIPS `BNE` encoding;
- add `jit_emit_runtime_cycles`, which emits one generated `ADDI s3,s3,-cycles*apu_clock`; it does not execute a timing helper from generated code;
- ordinary BPL/BMI/BVC/BVS/BCC/BCS/BNE/BEQ: base unchanged, generated -2-cycle surcharge only on taken path;
- BBC/BBS: +1 fixed compile-time cycle plus taken-only +2;
- CBNE direct/direct+X: +1 fixed operation cycle beyond already-validated addressing plus taken-only +2;
- DBNZ memory: taken-only +2;
- DBNZ Y: +2 fixed plus taken-only +2.

Generated control-flow uses the MIPS branch delay slot to establish fallthrough SPC PC, skips the surcharge on not-taken paths, and overwrites PC with target only on taken paths.

Proof matrix: **28 cases** — taken + not-taken for all 8 ordinary conditional branches, BBC/BBS, CBNE direct and direct+X, DBNZ memory, DBNZ Y. Each case checks:
- block-final static debit;
- presence/shape of exactly one generated conditional runtime debit `-42`;
- actual total R4300 `s3` delta vs pinned ares reference;
- final SPC PC;
- Y/RAM side effects where applicable;
- inherited block-span invariants.

Exact runs launched:
- **Build and Validate `35295336043`** for `a435d8f8...`;
- **APU Cycle And Span Proof `35295336130`** for `a435d8f8...`.

At checkpoint both are still compiling exact SHA.

Acceptance: both CI and all 28 path-specific dynamic cases must pass. A compile-only green result is insufficient. Any not-taken path executing the -42 debit, any taken path missing it, wrong PC, wrong DBNZ side effect, or disagreement with pinned ares cycles rejects/narrows the branch implementation.


## SPC700 addressing-family timing — VALIDATED 2026-09-17/18

Exact diagnostic SHA **`e78b3c47989359c3796887d00da9dcca56740e2b`**. This SHA differs from `19b3d6cf...` only by the harness correction for the already-validated bounded long-NOP expected PC; core timing rules are unchanged.

**Build and Validate `35294386630` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.

Dynamic authority: **APU Cycle And Span Proof `35294386627` SUCCESS**, cycle-proof job **`105444053413`**.
- proof result artifact **`10527331782`**, digest `sha256:3ddaf910afbb446093aa9fe154756f8e507d52633a05a18b29b96aba31e51f0b`;
- exact proof-build artifact **`10526324943`**, digest `sha256:92d3fcd835b0bebc9f4e7b662baa2216557a4c0cd1554b50f23cb1d3f75046c5`.

All required summary invariants were true:
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `all_semantics_match_expected=true`;
- `all_header_spans_match_source_prediction=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

### MEASURED representative addressing totals

Each case includes the already-corrected 4-cycle BRA loop. Total `s3` debit matched pinned ares reference exactly at `apu_clock=21`:

- direct read: **7 cycles**, total debit -147;
- direct write: **8**, -168;
- direct+X read: **8**, -168;
- direct+X write: **9**, -189;
- `(X)` read: **7**, -147;
- `(X)` write: **8**, -168;
- `(X)+` read: **8**, -168;
- `(X)+` write: **8**, -168;
- absolute read: **8**, -168;
- absolute write: **9**, -189;
- absolute+X read: **9**, -189;
- absolute+X write: **10**, -210;
- `[dp+X]` read: **10**, -210;
- `[dp+X]` write: **11**, -231;
- `[dp]+Y` read: **10**, -210;
- `[dp]+Y` write: **11**, -231.

All semantic postconditions passed: read cases produced the expected accumulator/X state, write cases wrote the expected RAM byte, and all tested blocks remained in the expected tag region.

**VALIDATED scope:** fixed missing-cycle charges for the audited direct/indexed/indirect addressing families, while preserving existing runtime data-access debit placement. This materially expands timing correctness beyond the four-opcode mechanism proof.

**NOT YET COMPLETE:** conditional branch taken-path cycles, implied/stack/call/return/bit/word/special instruction families, and exact intra-instruction I/O/timer bus-cycle placement remain open.

### Decision

Create a **clean code-only timing foundation branch from `phase2/apu-block-bound-fix@7e48bcc9...`** containing:
- shared compile-time missing-cycle helper;
- corrected NOP/BRA/MUL/DIV fixed timing;
- validated addressing-family charges and absolute-store wrapper;
- NO PROFILE diagnostic capture;
- NO GDB proof script/workflow changes.

Then Build/Validate the clean branch. After that, conditional branch timing is the next isolated batch. Conditional +2 cycles must be charged at runtime only on the taken path; compile-time `jit_charge_cycles` is not appropriate for that variable.

## RESUME HERE — addressing timing validated; clean timing foundation next

1. `master` remains `a2270699...`.
2. Clean block-bound branch `phase2/apu-block-bound-fix@7e48bcc9...` is the base for the next clean candidate.
3. Diagnostic authority for fixed timing/addressing is `e78b3c47...`, Build/Validate `35294386630`, ares proof `35294386627`; all 16 representative addressing cases match total reference cycles and semantics.
4. Recreate only validated core changes cleanly from `7e48bcc9...`. Do not copy `apu_cycle_diag.S`, diagnostic finish-block capture, workflow or proof script.
5. Next isolated timing variable after clean CI: conditional branches. Add +2 guest cycles only on the taken runtime path; keep not-taken timing unchanged. Validate taken/not-taken pairs for ordinary flag branch, bit branch, CBNE, DBNZ Y and DBNZ memory.
6. Remaining fixed-cycle families come after conditional branches. Exact I/O/timer cycle placement remains a later fidelity contract.
7. E1 matched-window repair remains required before ranking performance. E3/E4/E5 remain DEFERRED.


## Clean SPC700 timing foundation — candidate created 2026-09-17/18

Clean branch: **`phase2/apu-timing-foundation@a62e95b1764d296dc74e711903c2431c343a54c2`**, created directly from validated block-bound candidate `7e48bcc994483e7aaf7cc2793b03fe0ebf13ee84`.

This is a **CANDIDATE** code-only recreation of the dynamically validated fixed-timing/addressing work. Direct compare `7e48bcc9... -> a62e95b1...` is exactly one commit and exactly four core files:
- `src/apu_address.S` +54/-0;
- `src/apu_alu.S` +8/-0;
- `src/apu_control.S` +4/-0;
- `src/apu_emitter.S` +23/-4.

No diagnostic workflow, GDB script, `apu_cycle_diag.S`, PROFILE capture, profiler code or documentation is present in the candidate.

Included validated semantics:
- NOP uses shared fixed-cycle helper and still routes through `finish_opcode`;
- BRA +2 fixed internal cycles;
- MUL +8 missing cycles;
- DIV +11 missing cycles;
- validated direct/indexed/indirect addressing-family fixed charges;
- `apu_absw` wrapper only for pure absolute stores so CALL/JMP do not inherit store dummy-read timing.

Build and Validate run for exact candidate SHA: **`35296376545`**, currently PENDING at checkpoint. Branch creation itself triggered an earlier redundant run `35296360910` for base SHA `7e48bcc9...`; do not confuse that base run with candidate validation.

**Acceptance:** candidate remains unmerged until exact SHA `a62e95b1...` completes normal build, PROFILE build and pinned Mupen smoke successfully. The independent dynamic semantic authority remains diagnostic SHA `e78b3c47...` / ares proof `35294386627`.

### Next isolated variable after clean CI

Conditional branch timing remains next. Static/reference audit confirms:
- ordinary conditional branch: not taken = fetch-only base timing; taken adds **+2 cycles**;
- bit branch, CBNE, DBNZ memory/Y each have their own fixed pre-branch bus/idle work, but the **taken-path delta itself is +2 cycles**.
Because the decision is runtime-dependent, these +2 cycles must be emitted on the generated taken path, not added through compile-time `jit_charge_cycles`.

Do not modify the clean timing foundation until `35296376545` finishes.


## Clean SPC700 timing foundation — CI VALIDATED 2026-09-17/18

Clean candidate **`phase2/apu-timing-foundation@a62e95b1764d296dc74e711903c2431c343a54c2`** completed **Build and Validate `35296376545` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

The earlier branch-creation run `35296360910` for base SHA `7e48bcc9...` was cancelled by concurrency after the real candidate push; it is not relevant to candidate validity.

Combined authority for this candidate:
- clean code diff: exactly four APU core files, no diagnostics;
- exact candidate CI: `35296376545` SUCCESS;
- independent dynamic semantic/cycle authority: diagnostic `e78b3c47...`, ares proof `35294386627` SUCCESS.

State: **VALIDATED CANDIDATE**, not merged.

### Conditional branch timing design selected

The existing generated branch layout has two orientations:
- for conditions where the emitted MIPS branch corresponds to **SNES taken**, charge +2 cycles statically and emit one **+2-cycle refund** instruction only on the sequential SNES-not-taken path; increase branch skip from 2 to 3 emitted instructions;
- for conditions where the emitted MIPS branch corresponds to **SNES not-taken**, leave static timing unchanged and emit one **-2-cycle debit** instruction only on the sequential SNES-taken path; likewise increase skip from 2 to 3.

This preserves one extra runtime MIPS instruction on only the path needing adjustment and avoids new runtime helper calls.

Additional fixed branch-family timing from pinned ares reference:
- ordinary flag branches: +0 fixed, +2 only when taken;
- BBC/BBS: +1 fixed idle, +2 when taken;
- CBNE direct/direct+X: +1 fixed idle beyond addressing-family timing, +2 when taken;
- DBNZ Y: +2 fixed cycles, +2 when taken;
- DBNZ memory: +0 fixed beyond existing read/write/fetches, +2 when taken.

Next diagnostic matrix must exercise taken/not-taken pairs for BCC and BCS (both branch orientations), BBC/BBS, CBNE direct and direct+X, DBNZ Y and DBNZ memory; verify total `s3` delta, resulting PC and register/RAM postconditions. Do not modify clean `a62e95b1` until this diagnostic batch passes.


## SPC700 conditional branch timing — VALIDATED 2026-09-17/18

Diagnostic authority SHA: **`a435d8f8af05db4e155304812161adb295adf130`**.

CI:
- **Build and Validate `35295336043` SUCCESS**.
- **APU Cycle And Span Proof `35295336130` SUCCESS**, cycle-proof job **`105446873166`**.
- proof-build artifact **`10528215894`**, digest `sha256:25964401ec72a5c41e8edbfe86cfe718fc901da5686dbce52885865b30801149`;
- proof result artifact **`10527812627`**, digest `sha256:f1adacc4ecb5b64fc9384d000f9d080d6fd0b81ad4fca97e6020533260d3b64c`.

Implementation pattern validated:
- new compile-time helper emits one runtime `ADDI s3,s3,-cycles*apu_clock` into generated code;
- ordinary conditional branches choose fallthrough in the delay slot and execute the -2-cycle runtime debit only on the SNES-taken path;
- BNE opcode macro was added for the clear-condition branch orientation;
- BBC/BBS add +1 fixed cycle;
- CBNE adds +1 fixed cycle beyond its addressing work;
- DBNZ Y adds +2 fixed cycles;
- DBNZ memory adds no extra fixed cycles beyond existing read/write/fetch accounting;
- all conditional families add +2 cycles only when taken.

Dynamic matrix validated taken/not-taken semantics and total cycles for:
- BPL/BMI/BVC/BVS/BCC/BCS/BNE/BEQ: **2 not taken / 4 taken**;
- BBC/BBS: **5 / 7**;
- CBNE direct: **5 / 7**;
- CBNE direct+X: **6 / 8**;
- DBNZ memory: **5 / 7**;
- DBNZ Y: **4 / 6**.

All summary invariants passed:
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

The generated code contains the -42 master-cycle runtime instruction in both variants, but GDB `s3` delta proves it executes only on the taken path. Example ordinary branch: static debit remains 2 cycles; measured total is 4 taken and 2 not-taken.

**Decision:** consume only core changes from `a435d8f8...` into clean `phase2/apu-timing-foundation@a62e95b1...`: `apu_control.S`, runtime cycle helper in clean `apu_emitter.S`, and BNE encoding in `defines.h`. Do NOT copy diagnostic script/workflow/PROFILE capture.

After clean CI, proceed to remaining fixed-cycle SPC700 families (implied/flag/stack/call/return/bit/word/XCN/BRK/etc.) as the next timing-coverage batch. Performance ranking remains deferred until timing coverage is broad enough for a new honest baseline.


## Clean conditional-branch timing candidate — checkpoint 2026-09-17/18

Clean branch advanced to **`phase2/apu-timing-foundation@fe53aa5fe574baa5a4dba141e8c34ea8ce5996bc`**, one commit on top of CI-validated fixed/addressing foundation `a62e95b1...`.

Direct clean diff `a62e95b1... -> fe53aa5f...`:
- `src/apu_control.S` +78/-36;
- `src/apu_emitter.S` +17/-0;
- `src/defines.h` +1/-0.
No diagnostics, scripts, workflows or PROFILE capture.

Included semantics are exactly the dynamically validated `a435d8f8...` conditional timing changes:
- runtime conditional cycle-debit emitter;
- BNE encoding;
- taken-only +2 timing for all audited conditional branches;
- fixed +1/+2 family timing for BranchBit / CBNE / DBNZ Y.

Exact clean Build and Validate run: **`35296688540`**, QUEUED at checkpoint.

Authority split:
- dynamic timing/semantic proof: diagnostic `a435d8f8...`, ares run `35295336130` SUCCESS;
- clean integration candidate: `fe53aa5f...`, awaiting its own normal/PROFILE/Mupen CI.

Do not modify clean `fe53aa5f...` until run `35296688540` completes. Next work is read-only mapping of remaining fixed-cycle SPC700 instruction families.


## Clean conditional timing foundation — CI VALIDATED 2026-09-17/18

Clean **`phase2/apu-timing-foundation@fe53aa5fe574baa5a4dba141e8c34ea8ce5996bc`** completed **Build and Validate `35296688540` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

Combined authority:
- clean code-only branch `fe53aa5f...`;
- dynamic conditional timing/semantics authority `a435d8f8...` / ares proof `35295336130`;
- clean exact-SHA CI `35296688540`.

State: **VALIDATED CANDIDATE**, unmerged.

### New stack correctness question before next timing batch

Static audit of inherited POP generators shows a potentially material ordering issue:
`apu_ppa/ppx/ppy/ppp` increment S, mask to low 8 bits, call `apu_read8`, and only **after the read returns** execute `ORI A0,A0,0x100`. PUSH generators construct `0x01xx` before `apu_write8`.

**OPEN QUESTION / HYPOTHESIS:** POP may therefore read direct-page `0x00xx` instead of stack-page `0x01xx`. Do not infer a bug solely from the static sequence; prove it dynamically before adding stack timing charges.

Next controlled experiment: on diagnostic `phase2/apu-cycle-proof`, test PUSH/POP semantics with distinct sentinel bytes at `00xx` and `01xx`, initially without changing stack semantics. If POP observes the direct-page sentinel, classify as CONFIRMED correctness defect and repair stack addressing before timing it. If it observes the stack-page sentinel, reject the hypothesis and continue the planned implied/flags/transfers/stack timing batch.


## POP stack-page semantic proof in progress — checkpoint 2026-09-17/18

Diagnostic-only SHA **`410985f0ba2fbf22c1d8341890bbf5fd1dba2d32`** adds only harness/workflow support for `apu_stack` and one directed POP-A semantic case. No APU core source is changed.

Runs:
- **Build and Validate `35296994425`** — queued at checkpoint.
- **APU Cycle And Span Proof `35296994473`** — in progress at checkpoint.

Directed case:
- initial `S=0x7F`;
- `RAM[0x0080]=0xAA` direct-page sentinel;
- `RAM[0x0180]=0xBB` correct stack-page sentinel;
- program `POP A; BRA back`;
- expected postcondition: `S=0x80`, `A=0xBB`.

This experiment deliberately does **not** judge POP timing yet (`reference_cycles=None`). It only separates the static-addressing hypothesis.

Readings:
- `A=0xBB, S=0x80` => REJECT the suspected stack-page bug; proceed to timing charges.
- `A=0xAA, S=0x80` => CONFIRM inherited POP reads page `0x00xx` because `0x0100` is ORed into A0 after `apu_read8`; repair semantics before timing stack family.
- other value/state => inspect harness/JIT state before attributing a core defect.

Clean timing foundation remains frozen at **`fe53aa5f...`**, Build and Validate **`35296688540` SUCCESS**.


## Static compatibility debt surfaced during timing audit — DEFERRED 2026-09-17/18

**MEASURED STATIC / REQUIRED SUPPORT, but not current M1 variable:** the current SPC700 opcode table maps **0xBE (DAS)** and **0xDF (DAA)** to `apu_unk`. The pinned independent SPC700 reference implements both decimal-adjust instructions.

This is a real base-SPC700 compatibility/accuracy gap, not a missing-cycle-only issue. Do not silently include it in the current timing batch. Track it for a later Gate C/base-core completeness pass after the timing contract is stabilized, unless representative software proves it is an earlier blocker.

The active experiment remains POP stack-page semantics at `410985f0...` / run `35296994473`.


## POP stack-page hypothesis — REJECTED dynamically 2026-09-17/18

Diagnostic-only SHA **`410985f0ba2fbf22c1d8341890bbf5fd1dba2d32`** changed only the proof harness/workflow; no APU core source changed.

Authorities:
- **Build and Validate `35296994425` SUCCESS**.
- **APU Cycle And Span Proof `35296994473` SUCCESS**, cycle-proof job **`105451729667`**.
- proof result artifact **`10528910419`**, digest `sha256:a47ce297dace8fe48385fffcfadb07de141091dd12ee1e3900c635220c4611e8`;
- exact proof-build artifact **`10528369355`**, digest `sha256:b61b722699a915de1cb57d77ec0e6e9e2987c4a400b2c200e024790647a38c53`.

Directed sentinel case:
- initial `S=0x7F`;
- direct page `RAM[0x0080]=0xAA`;
- stack page `RAM[0x0180]=0xBB`;
- source `POP A; BRA back`;
- measured **A=0xBB**, **S=0x80**, semantic check true.

Therefore the suspected inherited POP stack-page bug is **REJECTED**.

Why the static sequence looked wrong: the generator calls `emit_jal` to emit a runtime MIPS `JAL apu_read8`; the immediately following emitted `ORI A0,A0,0x100` occupies that runtime JAL's **delay slot**. It executes before control enters `apu_read8`, so the read correctly sees `0x01xx`. This discarded explanation is now preserved so the code is not “fixed” incorrectly later.

The proof intentionally did not judge POP timing (`reference_cycles=None`). Its observed block had static 5 units and total 6 units including runtime read because the trailing validated BRA contributes 4 cycles; stack-family timing correction remains the next variable.

## RESUME HERE — fixed implied/flags/transfers/stack timing next

1. Clean timing foundation remains **`phase2/apu-timing-foundation@fe53aa5f...`**, Build/Validate `35296688540` SUCCESS, unmerged.
2. POP stack-page suspicion is REJECTED by `410985f0...` / proof `35296994473`; do not change POP addressing.
3. Next controlled diagnostic batch on `phase2/apu-cycle-proof`: add only fixed missing cycles for implied ALU/register operations, flag operations, register transfers and PUSH/POP.
4. Expected missing charges from pinned ares:
   - implied A/X/Y modify and register transfers: +1;
   - CLRC/SETC/CLRP/SETP/CLRV: +1;
   - DI/EI and NOTC: +2;
   - XCN: +4;
   - PUSH/POP family: +2 beyond existing opcode fetch + runtime stack read/write.
5. Validate representative semantics + total `s3` cycles before consuming anything cleanly.
6. Keep CALL/TCALL/PCALL/RET/RET1/BRK, word operations, bit operations and decimal-adjust support as separate later batches.
7. DAA/DAS remain MEASURED STATIC / REQUIRED SUPPORT / DEFERRED Gate C debt.


## Fixed implied/flags/transfers/stack timing proof in progress — checkpoint 2026-09-17/18

Exact diagnostic SHA: **`62e661b62a177c5b1c087226e589153c29e439fe`**, one commit after the POP semantic-only authority `410985f0...`.

Controlled timing class:
- implied A/X/Y register modify operations: +1 missing cycle;
- register transfers A/X/Y/SP: +1;
- CLRC/SETC/CLRV and CLRP/SETP: +1;
- NOTC: +2;
- DI/EI: +2;
- XCN: +4;
- PUSH A/X/Y/PSW and POP A/X/Y/PSW: +2 beyond existing opcode fetch + runtime stack access.

No CALL/TCALL/PCALL/RET/RET1/BRK, word, bit, decimal-adjust or other special-family timing changes are included.

Direct compare `410985f0... -> 62e661b6...` is one commit:
- `src/apu_alu.S` +60/-0;
- `src/apu_control.S` +16/-0;
- `src/apu_transfer.S` +56/-0;
- `scripts/apu_cycle_proof.py` +46/-2.

Representative dynamic cases added:
- INC A + BRA: expected total 6 cycles;
- MOV X,A + BRA: 6;
- MOV SP,X + BRA: 6;
- CLRC + BRA: 6;
- DI + BRA: 7;
- EI + BRA: 7;
- NOTC + BRA: 7;
- XCN + BRA: 9;
- PUSH A + BRA: static 7 cycles + runtime write = total 8;
- existing directed POP A stack sentinel now also expects static 7 + runtime read = total 8.

Each case checks static debit, total R4300 `s3` delta, PC/span and relevant A/X/SP/flags/RAM postcondition.

Runs for exact SHA:
- **Build and Validate `35297695310`** — in progress at checkpoint.
- **APU Cycle And Span Proof `35297695313`** — in progress at checkpoint.

Acceptance:
1. normal + PROFILE build + Mupen smoke green;
2. all previous timing/addressing/branch/span regressions remain green;
3. every new representative case matches pinned ares total cycles exactly;
4. PUSH/POP preserve proven stack-page semantics and expected S/RAM/A state;
5. no unexpected runtime debit instruction appears for these fixed-cycle-only families.

A mismatch narrows/rejects the specific family rule; do not adjust the reference expectation without reconciling the pinned ares instruction sequence.


## Fixed-family timing proof attempt 1 — harness false negative on 0xED 2026-09-17/18

Exact core/harness SHA **`62e661b62a177c5b1c087226e589153c29e439fe`**:
- **Build and Validate `35297695310` SUCCESS**, including normal build, PROFILE build and pinned Mupen smoke.
- **APU Cycle And Span Proof `35297695313` FAILURE**, cycle-proof job `105453803356`.
- failed proof result artifact **`10528981437`**, digest `sha256:d0ea14cfc5f171b9d6900bf7d977602d65271d079e01113ec464eb4910767a0b`;
- exact proof-build artifact **`10528736287`**, digest `sha256:2684ab8874f58050c4a5441ab722400b35a5ebb7000fdd9dadf681c3d03312a1`.

The failure is **REJECTED as core/timing evidence**. All prior regression cases remained green, POP A now matched 8 total cycles with correct stack semantics, and the new cases completed successfully through:
- INC A + BRA = **6 cycles**, semantic pass;
- MOV X,A + BRA = **6**, X semantic pass;
- MOV SP,X + BRA = **6**, SP semantic pass;
- CLRC + BRA = **6**, flags semantic pass;
- DI + BRA = **7**, flags semantic pass;
- EI + BRA = **7**, flags semantic pass.

Execution stopped while arming `notc_fixed`, before compiling or executing NOTC. The injected source bytes are `ED 2F FD`. Shared `RSPClient.read_memory()` currently treats **any** reply beginning with ASCII `E` as a GDB error. A valid memory reply `ED2FFD` therefore triggered:
`target rejected memory read ...: ED2FFD`.

This is a diagnostic-protocol parser defect, not an emulator result. GDB RSP errors have the shape `E` + two hex digits (normally exactly 3 ASCII bytes), while a memory/register hex payload can legitimately begin with hexadecimal E.

**Decision:** fix only RSP error recognition (and the identical single-register-read check) to recognize actual 3-byte `Ehh` error packets, then rerun the unchanged core timing candidate. Do not alter cycle charges or reference expectations.


## Fixed-family timing rerun after RSP parser fix — checkpoint 2026-09-17/18

Diagnostic HEAD **`2e01d323f458575fcaac8602331a87a36854c081`** has the **same APU core timing implementation as `62e661b6...`**. The only changes are diagnostic protocol parsing:
- `scripts/gdb_rsp_dump.py`: memory reads classify an error only when the reply is exactly a 3-byte `Ehh` packet;
- `scripts/apu_cycle_proof.py`: single GPR reads use the same exact `Ehh` rule.

This removes the false collision where valid hex payload `ED2FFD` was misread as a GDB error.

Exact rerun workflows:
- **Build and Validate `35298264597`** — queued at checkpoint.
- **APU Cycle And Span Proof `35298264479`** — queued at checkpoint.

Core acceptance criteria are unchanged from `62e661b6...`. In particular, NOTC/XCN/PUSH A and the already corrected POP timing must now be reached and judged without any change to their expected cycles.


## Fixed implied/flags/transfers/stack timing — VALIDATED 2026-09-17/18

Exact diagnostic core authority remains **`62e661b62a177c5b1c087226e589153c29e439fe`**. Exact rerun SHA **`2e01d323f458575fcaac8602331a87a36854c081`** changes only diagnostic GDB-RSP error parsing; APU core timing is identical to `62e661b6...`.

Authorities:
- **Build and Validate `35298264597` SUCCESS**.
- **APU Cycle And Span Proof `35298264479` SUCCESS**, cycle-proof job **`105455473977`**.
- proof result artifact **`10529235434`**, digest `sha256:11065dc6adc72c36c1af3d5c405214a9de6e6a1d265545ec2a23f69f38e63962`;
- exact proof-build artifact **`10529166425`**, digest `sha256:834ad7453b358ed56c18c3ab0cbb40e08e42c0e2c704bfd632b7613db38a338e`.

All required summary invariants are true:
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `all_runtime_cycle_debits_match_expected=true`;
- `all_semantics_match_expected=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

Representative newly validated totals, each combined with the already validated trailing BRA loop:
- INC A + BRA: **6 cycles**;
- MOV X,A + BRA: **6**;
- MOV SP,X + BRA: **6**;
- CLRC + BRA: **6**;
- DI + BRA: **7**;
- EI + BRA: **7**;
- NOTC + BRA: **7**;
- XCN + BRA: **9**;
- PUSH A + BRA: **8**, writes expected byte to stack page and updates S correctly;
- POP A + BRA: **8**, reads expected stack-page sentinel `0xBB` and updates S correctly.

The prior `62e661b6...` proof failure on source bytes beginning `ED...` is **REJECTED as core evidence**: exact rerun with parser-only correction passes unchanged timing implementation.

**VALIDATED scope:** fixed missing-cycle rules for implied A/X/Y modify operations, A/X/Y/SP register transfers, CLRC/SETC/CLRV/CLRP/SETP, DI/EI, NOTC, XCN, and PUSH/POP A/X/Y/PSW families.

**Decision:** consume only APU core changes from `62e661b6...` into clean `phase2/apu-timing-foundation@fe53aa5f...`: `src/apu_alu.S`, `src/apu_control.S`, `src/apu_transfer.S`. Do NOT copy proof script/workflow or GDB parser changes.

Next timing families remain isolated: CALL/TCALL/PCALL/RET/RET1/BRK first, then word/bit/special operations. DAA/DAS remain Gate-C REQUIRED SUPPORT debt, not part of timing-only changes.


## Clean implied/flags/transfers/stack timing candidate — checkpoint 2026-09-17/18

Clean branch advanced to **`phase2/apu-timing-foundation@46230daa7ac66b7b400ce6d2105e3834a15ed4ec`**, one commit on top of clean conditional foundation `fe53aa5f...`.

Direct compare `fe53aa5f... -> 46230daa...` is exactly:
- `src/apu_alu.S` +60/-0;
- `src/apu_control.S` +16/-0;
- `src/apu_transfer.S` +56/-0.

No diagnostic scripts/workflows, GDB parser fixes, PROFILE capture or `apu_cycle_diag` code are present.

This clean commit consumes the dynamically validated fixed-family timing rules from diagnostic core SHA `62e661b6...` / rerun authority `2e01d323...`.

Exact clean Build and Validate run: **`35301478900`**, QUEUED at checkpoint.

Acceptance remains normal build + PROFILE build + pinned Mupen smoke green on exact SHA `46230daa...`. Dynamic semantic/cycle authority remains ares proof `35298264479`.

While clean CI runs, next work is READ-ONLY mapping of CALL/TCALL/PCALL/RET/RET1/BRK timing and semantics against pinned ares. Do not modify clean `46230daa...` until its exact CI completes.


## Clean fixed-family timing foundation — CI VALIDATED 2026-09-17/18

Clean **`phase2/apu-timing-foundation@46230daa7ac66b7b400ce6d2105e3834a15ed4ec`** completed **Build and Validate `35301478900` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged. Dynamic cycle/semantic authority remains diagnostic `62e661b6...` with parser-only rerun `2e01d323...` / ares proof `35298264479`.

## CALL/TCALL/PCALL/RET/RET1/BRK timing proof in progress — checkpoint 2026-09-17/18

Exact diagnostic SHA: **`044009a4c8bc34ffa8314ddcb99fbe2b31099de5`**, based on `2e01d323...`.

Controlled core timing changes, only in `src/apu_control.S`:
- CALL +3 fixed cycles;
- TCALL +3;
- PCALL +2;
- RET +2;
- RET1 +2;
- BRK +2.

Reference-derived accounting:
- CALL absolute: opcode+2 operand fetches +3 fixed +2 stack writes = **8 total**;
- PCALL: opcode+operand +2 fixed +2 stack writes = **6**;
- TCALL0: opcode +3 fixed +2 stack writes +2 vector reads = **8**;
- RET: opcode +2 fixed +2 stack reads = **5**;
- RET1: opcode +2 fixed +3 stack reads = **6**;
- BRK: opcode +2 fixed +3 stack writes +2 vector reads = **8**.

The proof also:
- forces `apu_map[0x3FF]=0` so FFDE/FFDF vectors come deterministically from RAM, not inherited IPL-ROM mapping;
- validates final PC and S;
- validates pushed return-PC bytes for CALL/PCALL/TCALL;
- validates RET/RET1 stack reconstruction;
- validates RET1 PSW restore;
- validates BRK pushed PC/PSW and post-BRK flags.

Exact workflows:
- **Build and Validate `35301687790`** — QUEUED at checkpoint.
- **APU Cycle And Span Proof `35301687777`** — IN PROGRESS at checkpoint.

Expected readings:
- all six exact cycle totals + semantic postconditions pass => VALIDATE this timing family and consume only `apu_control.S` core timing changes cleanly on `46230daa...`;
- cycle mismatch with semantic pass => narrow/reject only the affected fixed-cycle rule against pinned ares;
- semantic mismatch with matching cycles => treat as pre-existing CALL/RET/BRK correctness defect, do not hide it with timing charges;
- harness/vector mismatch => repair diagnostic setup only after proving the mismatch is not core behavior.

**Known limitation preserved:** TCALL/BRK bus-access ordering in Sodium64 differs statically from pinned ares (vector vs stack access order). This batch tests total guest cycles and end-state semantics only; exact intra-instruction I/O/timer ordering remains separate fidelity work.


## CALL/PCALL proof exposed inherited PCALL target bug — 2026-09-17/18

Diagnostic SHA **`044009a4c8bc34ffa8314ddcb99fbe2b31099de5`**:
- Build and Validate **`35301687790` SUCCESS** (normal, PROFILE, pinned Mupen smoke all green).
- APU Cycle And Span Proof **`35301687777` FAILURE**, cycle-proof job **`105465701875`**.
- exact proof-build artifact **`10529863114`**, digest `sha256:219d6d9dae8d5dc860be1dd8a1e3ac7154fd9a06df751291d9e6759f27a01384`;
- failed-proof diagnostics artifact **`10529489052`**, digest `sha256:b697eab9d4d9d6c394e382ae3189fe15a75bad35030be96005f27afe95a89a98`.

The proof reached the new CALL/return family after all prior required timing cases continued to pass.

### MEASURED

**CALL absolute** passed completely:
- static debit -126 = 6 SPC cycles before runtime stack accesses;
- total debit -168 = **8 cycles**, matching pinned ares;
- final PC **0x1234**;
- S **0x80 -> 0x7E**;
- return bytes correctly pushed: `RAM[0x0180]=0x02`, `RAM[0x017F]=0x03`;
- semantic postcondition true.

**PCALL** timing and stack writes passed, but target semantics failed:
- static debit -84 = 4 cycles;
- total debit -126 = **6 cycles**, matching pinned ares;
- S **0x80 -> 0x7E**;
- return bytes correctly pushed: `RAM[0x0180]=0x02`, `RAM[0x017F]=0x02`;
- expected PC `0xFF34`, observed **`0xD475`**;
- semantic postcondition false; proof stopped here, so TCALL/RET/RET1/BRK are **NOT YET MEASURED** in this run.

### SUPPORTED CAUSE

This is an inherited PCALL semantic defect, not evidence against the +2 timing rule:
- `apu_pcall` computes target `0xFF00 | operand` into compile-time scratch `t2`;
- it then calls `load_stack`;
- `load_stack -> full_address` explicitly writes `t2 = low16(apu_stack)`;
- exact build symbol `apu_stack=0x8001D475`;
- observed wrong PC is exactly **0xD475**.

CALL does not suffer this because its destination is already carried in generated runtime `A0` and copied directly to S0.

State:
- **VALIDATED:** CALL total timing + end-state semantics for directed case.
- **MEASURED / SUPPORTED:** PCALL total timing 6 cycles.
- **CONFIRMED CORRECTNESS DEFECT:** PCALL target clobbered by volatile compile-time `t2`.
- **UNKNOWN:** TCALL/RET/RET1/BRK until proof advances past PCALL.

### Next controlled change

On diagnostic `phase2/apu-cycle-proof`, move `ori t2,v0,0xFF00` to immediately after `load_stack`, where `v0` still holds the fetched PCALL operand and before target emission. Do not change PCALL timing, stack sequence, harness expectations, or any other opcode.

Falsifier: if rerun still does not reach PC=0xFF34 with correct stack/timing, reject this cause and inspect the generated target instruction rather than broadening the patch.


## PCALL target-clobber diagnostic fix in progress — checkpoint 2026-09-17/18

Exact diagnostic SHA: **`f4da303dc3cd901672f923d476284b3f05372e38`**, parent `044009a4...`.

Controlled change: **only `src/apu_control.S` PCALL compile-time target lifetime**.
- Before: `t2 = 0xFF00 | operand` was computed before `load_stack`, then overwritten by `full_address`.
- Now: fetched operand remains in `v0` across `load_stack`, and `t2 = 0xFF00 | v0` is formed immediately afterward, before emitting S0 target.
- PCALL fixed timing (+2), stack sequence and all harness expectations are unchanged.

Exact workflows:
- **APU Cycle And Span Proof `35302251443`** — IN PROGRESS at checkpoint.
- **Build and Validate `35302251447`** — IN PROGRESS at checkpoint.

Question: does this single lifetime fix restore PCALL target `0xFF34` while preserving measured 6-cycle total and correct return-stack bytes, allowing the unchanged proof to advance to TCALL/RET/RET1/BRK?

Conditional next actions:
- PCALL passes and later cases pass => validate timing family plus PCALL semantic fix, then consume only validated core changes cleanly on `phase2/apu-timing-foundation@46230daa...`;
- PCALL still fails => inspect emitted target opcode/register value; do not broaden patch;
- later opcode fails => preserve PCALL as fixed and isolate only that later instruction.


## CALL/TCALL/PCALL/RET/RET1/BRK timing + PCALL semantic fix — VALIDATED 2026-09-17/18

Exact diagnostic authority: **`f4da303dc3cd901672f923d476284b3f05372e38`**.

CI:
- **Build and Validate `35302251447` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35302251443` SUCCESS**, cycle-proof job **`105467368408`**.
- proof-build artifact **`10529948912`**, digest `sha256:38d213c8e1727cef9310728d982975dc8bef202f7f2688729e843cebb7a5ef89`;
- proof result artifact **`10530423530`**, digest `sha256:9834d8846aa1b135a3e4b1e2f443d3a8a089e7a7d363b83be2fecdfbb0b13e50`.

All global proof invariants are true:
- `all_header_spans_match_source_prediction=true`;
- `all_runtime_cycle_debits_match_expected=true`;
- `all_semantics_match_expected=true`;
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

### MEASURED / VALIDATED directed control-flow cases

- **CALL absolute:** 8 total cycles; PC `0x1234`; S `0x80 -> 0x7E`; return bytes `0x02,0x03` pushed at `0x0180,0x017F`.
- **PCALL:** 6 total cycles; corrected PC **`0xFF34`**; S `0x80 -> 0x7E`; return bytes `0x02,0x02` correct.
- **TCALL0:** 8 total cycles; vector target PC `0x1234`; S `0x80 -> 0x7E`; return bytes correct.
- **RET:** 5 total cycles; PC `0x1234`; S `0x7E -> 0x80`.
- **RET1:** 6 total cycles; PC `0x1234`; S `0x7D -> 0x80`; PSW restored to `0x04`.
- **BRK:** 8 total cycles; vector PC `0x1234`; S `0x80 -> 0x7D`; pushed PC/PSW correct; post-BRK PSW `0x10` (I clear, B set).

The previous PCALL failure at `044009a4...` is now fully explained and superseded:
- old wrong PC `0xD475` exactly matched low16 of `apu_stack=0x8001D475`;
- `load_stack -> full_address` clobbered compile-time scratch `t2`;
- **validated fix:** preserve fetched PCALL operand in `v0` across `load_stack`, then form `t2=0xFF00|v0` immediately before target emission;
- rerun restores `0xFF34` while retaining exact 6-cycle total and stack semantics.

### Timing rules validated

- CALL +3 fixed missing cycles;
- TCALL +3;
- PCALL +2;
- RET +2;
- RET1 +2;
- BRK +2.

**Important remaining limitation:** these tests validate total guest cycles and directed end-state semantics. They do **not** validate exact intra-instruction bus-cycle ordering. Static comparison still shows Sodium64 TCALL/BRK vector-vs-stack access ordering differs from pinned ares. Preserve this as timing/fidelity debt for later timer/I/O-sensitive validation.

### Decision

Consume only validated core changes from diagnostic `f4da303d...` into clean `phase2/apu-timing-foundation@46230daa...`:
- `src/apu_control.S` fixed-cycle charges for CALL/TCALL/PCALL/RET/RET1/BRK;
- PCALL compile-time target lifetime fix.
Do NOT copy `apu_map` proof setup, scripts, workflows or diagnostics.

After exact clean CI, next isolated timing batch is word/bit coverage. Current read-only hypotheses:
- word: ADDW, SUBW, MOVW YA,dp likely +1 fixed each; CMPW/INCW/DECW/MOVW dp,YA likely already match total cycles;
- bit: OR1 variants, EOR1, MOV1 mem.bit,C and TSET1/TCLR1 likely each miss one cycle; AND1/MOV1 C,mem/NOT1/SET1/CLR1 likely already match.
These remain **HYPOTHESIS** until dynamic proof.


## Clean CALL/return/BRK + PCALL candidate — checkpoint 2026-09-17/18

Clean branch advanced to **`phase2/apu-timing-foundation@fafc08478bcf918bca4e17e04b9b6c9b4e7a62c8`**, one commit on top of `46230daa...`.

Direct compare `46230daa... -> fafc0847...` is exactly one file:
- `src/apu_control.S` +27/-2.

Patch contents are limited to validated core behavior:
- CALL +3 fixed cycles;
- TCALL +3;
- PCALL +2;
- RET +2;
- RET1 +2;
- BRK +2;
- PCALL target formation moved after `load_stack` so volatile compile-time `t2` is not clobbered.

No scripts, workflows, `apu_map` diagnostic setup, GDB code or PROFILE diagnostics are present.

Exact clean Build and Validate run: **`35302765614`**, IN PROGRESS at checkpoint.

Dynamic authority remains diagnostic `f4da303d...` / ares proof `35302251443` SUCCESS. Accept clean candidate only after normal build + PROFILE build + pinned Mupen smoke succeed on exact SHA `fafc0847...`.

Next technical batch after exact clean CI: dynamically prove the already-mapped word/bit timing hypotheses on diagnostic branch. Keep known H-flag semantic TODOs and TCALL/BRK intra-instruction bus-order debt explicit; do not conflate total-cycle correctness with those unresolved contracts.


## Clean CALL/return/BRK + PCALL foundation — CI VALIDATED 2026-09-17/18

Clean **`phase2/apu-timing-foundation@fafc08478bcf918bca4e17e04b9b6c9b4e7a62c8`** completed **Build and Validate `35302765614` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

Combined authority:
- dynamic timing + semantic proof: diagnostic `f4da303d...`, ares proof `35302251443` SUCCESS;
- clean integration diff: one core file only, `src/apu_control.S`;
- exact clean SHA CI: `35302765614` SUCCESS.

Next isolated variable: SPC700 word-instruction total-cycle coverage. Do not fold bit-family timing into the same experiment.


## SPC700 word timing proof in progress — checkpoint 2026-09-17/18

Exact diagnostic SHA: **`90c700a404f7d5a5abdc65d92e4869a431e7ad2d`**, parent `f4da303d...`.

Controlled core changes:
- `apu_addw`: +1 fixed cycle;
- `apu_subw`: +1 fixed cycle;
- `apu_movwya` (MOVW YA,dp): +1 fixed cycle.
No changes to CMPW, INCW, DECW or MOVW dp,YA controls.

Directed matrix:
- ADDW YA,dp + closing BRA: expected **9 total cycles**, verifies YA result;
- SUBW YA,dp + BRA: **9**, verifies YA result;
- MOVW YA,dp + BRA: **9**, verifies YA load;
- CMPW control + BRA: **8**;
- DECW control + BRA: **10**, verifies two output bytes;
- INCW control + BRA: **10**, verifies two output bytes;
- MOVW dp,YA control + BRA: **9**, verifies two output bytes.

Known semantic limitation intentionally not hidden: ADDW/SUBW source still has `TODO: set the H flag`. This proof validates total timing and chosen data-result postconditions; it does not claim full flag correctness.

Exact workflows:
- **Build and Validate `35302988477`** — IN PROGRESS at checkpoint.
- **APU Cycle And Span Proof `35302988483`** — IN PROGRESS at checkpoint.

Decision rules:
- all seven cases pass => validate the three +1 timing rules and consume only `apu_alu.S` / `apu_transfer.S` core changes cleanly on `fafc0847...`;
- corrected case cycle mismatch => reject/narrow the +1 rule for that opcode;
- control mismatch => stop and repair the timing model before consuming any word changes;
- data semantic mismatch with correct cycles => isolate inherited word-operation correctness separately from timing.

Bit-family hypotheses remain DEFERRED until this word batch closes.


## SPC700 word timing — VALIDATED 2026-09-18

Exact diagnostic authority: **`90c700a404f7d5a5abdc65d92e4869a431e7ad2d`**.

CI:
- **Build and Validate `35302988477` SUCCESS**: normal build, PROFILE build, pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35302988483` SUCCESS**, cycle-proof job **`105469587489`**.
- proof result artifact **`10531230748`**, digest `sha256:d4c061fd78f3e8ae99e8e358e6d51063ed79a953a623358c91a019f22d5baa68`;
- exact proof-build artifact **`10530635328`**, digest `sha256:96cdb5bfce147f4a4ba22535ae1266759380cdbd69a12b5c2c8d9b26a88e8e5e`.

All global proof invariants are true:
- `all_runtime_cycle_debits_match_expected=true`;
- `all_semantics_match_expected=true`;
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

### MEASURED / VALIDATED word cases

Corrected families:
- ADDW YA,dp + BRA: **9 total cycles**, expected YA result passed;
- SUBW YA,dp + BRA: **9**, expected YA result passed;
- MOVW YA,dp + BRA: **9**, expected YA load passed.

Controls with NO timing change required:
- CMPW + BRA: **8 total cycles**;
- DECW + BRA: **10**, both result bytes correct;
- INCW + BRA: **10**, both result bytes correct;
- MOVW dp,YA + BRA: **9**, both written bytes correct.

Therefore the validated fixed rules are exactly:
- `apu_addw`: +1;
- `apu_subw`: +1;
- `apu_movwya`: +1.

Do NOT add timing to CMPW/INCW/DECW/MOVW dp,YA based on this family.

Known semantic debt remains explicit: ADDW/SUBW source still contains `TODO: set the H flag`; this batch validates total timing and selected data results, not full flag fidelity.

### Decision
Consume only the three validated core timing additions into clean `phase2/apu-timing-foundation@fafc0847...`:
- `src/apu_alu.S` ADDW/SUBW +1;
- `src/apu_transfer.S` MOVW YA,dp +1.
Do NOT copy proof script/harness changes.

After exact clean CI, proceed to a separate bit-family timing batch. Current bit hypotheses remain unvalidated until dynamic proof.


## Clean word-timing candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@4a3cf13a54213b401b82bd715a07732b4b8dc66f`**, one commit on top of `fafc0847...`.

Direct clean diff `fafc0847... -> 4a3cf13a...` is exactly:
- `src/apu_alu.S` +8/-0 (ADDW +1, SUBW +1);
- `src/apu_transfer.S` +4/-0 (MOVW YA,dp +1).

No diagnostic scripts/workflows or unrelated core edits.

Exact clean Build and Validate run: **`35306811545`**, QUEUED at checkpoint.

Dynamic word timing/semantic authority remains diagnostic `90c700a4...` / ares proof `35302988483` SUCCESS.

Do not modify clean `4a3cf13a...` until exact CI completes. Next work is read-only mapping of bit-family timing and semantics.


## Clean SPC700 word timing foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@4a3cf13a54213b401b82bd715a07732b4b8dc66f`** completed **Build and Validate `35306811545` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

Combined authority:
- dynamic word timing/semantics: diagnostic `90c700a4...` / ares proof `35302988483` SUCCESS;
- clean integration: exactly `apu_alu.S` +8 and `apu_transfer.S` +4;
- exact clean CI `35306811545` SUCCESS.

## Next isolated variable — bit-family timing

Pinned ares/static mapping yields these hypotheses:

Likely +1 fixed timing:
- OR1 C,mem.bit;
- OR1 C,/mem.bit;
- EOR1 C,mem.bit;
- MOV1 mem.bit,C.

Likely cycle-complete controls:
- AND1 C,mem.bit;
- AND1 C,/mem.bit;
- MOV1 C,mem.bit;
- NOT1 mem.bit;
- SET1 dp.bit;
- CLR1 dp.bit.

Special case:
- TSET1/TCLR1 each need one additional **bus read** before write in pinned ares. A simple +1 fixed debit can validate total cycles for ordinary RAM but is NOT bus-semantically exact for I/O/timer side effects. If timing proof uses +1 fixed, preserve this as explicit fidelity debt and do not claim those opcodes are fully cycle/bus exact.

Next diagnostic batch should validate corrected cases and no-change controls separately, checking total `s3`, carry/RAM postconditions and block span.


## SPC700 bit timing proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`1958dff26eefdafffa849cd2d1b5ca83045230d2`**, one commit after validated word authority `90c700a4...`.

Direct compare is exactly:
- `src/apu_alu.S` +26/-0;
- `scripts/apu_cycle_proof.py` +60/-0.

Controlled timing candidates:
- OR1 C,mem.bit +1 fixed cycle;
- OR1 C,/mem.bit +1;
- EOR1 C,mem.bit +1;
- MOV1 mem.bit,C +1;
- TSET1 +1 total-cycle debit for ordinary RAM;
- TCLR1 +1 total-cycle debit for ordinary RAM.

No-change controls:
- AND1 C,mem.bit;
- AND1 C,/mem.bit;
- MOV1 C,mem.bit;
- NOT1 mem.bit;
- SET1 dp.bit;
- CLR1 dp.bit.

Directed proof checks carry/RAM semantics plus exact total `s3`, static debit and span.

Important limitation for TSET1/TCLR1: pinned ares performs a **second real bus read** before write. This diagnostic uses a fixed +1 debit, which can match ordinary-RAM total cycles but is not I/O/timer side-effect exact. Even if these two cases pass, do not classify them as fully bus-cycle-exact or consume them cleanly without an explicit decision on that semantic debt.

Exact workflows:
- **APU Cycle And Span Proof `35307039329`** — IN PROGRESS at checkpoint.
- **Build and Validate `35307039426`** — IN PROGRESS at checkpoint.

Acceptance:
1. previous regression matrix remains green;
2. corrected OR1/EOR1/MOV1 mem,C cases match reference totals and semantics;
3. no-change controls remain exact without added charges;
4. TSET/TCLR ordinary-RAM cases may establish total timing only, not bus fidelity.


## Bit timing attempt 1 — timing matched, pre-existing carry-persistence bug exposed 2026-09-18

Exact diagnostic SHA **`1958dff26eefdafffa849cd2d1b5ca83045230d2`**:
- **Build and Validate `35307039426` SUCCESS**: normal, PROFILE and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35307039329` FAILURE**, cycle-proof job **`105481467236`**.
- failed proof result artifact **`10532800207`**, digest `sha256:c2c56b360156d1a057f92e8fd0a057ee5fabc15ea480c35a98fa91f27d30e55a`;
- exact proof-build artifact **`10532056467`**, digest `sha256:d45aebc00ea68d6fb321608233ad49196d6c4816af9ac925d81c376e6b680539`.

The proof stopped on the **first new bit case, OR1 C,mem.bit**. Its timing evidence PASSED:
- static debit **-168 = 8 units**, exactly expected;
- total `s3` debit **-189 = 9 cycles**, exactly pinned-reference total;
- span/header checks passed.

The failure was semantic only:
- source bit = 1, initial C=0;
- expected persisted C=1;
- observed `apu_flags_after_block=0`;
- `semantics_match_expected=false`.

### Root cause — SUPPORTED STATIC + dynamic symptom

Inherited carry-modifying bit generators load PSW but do not mark it dirty in compiler state:
- `apu_mov1b` (MOV1 C,mem.bit);
- `apu_or1a`;
- `apu_or1b`;
- `apu_and1a`;
- `apu_and1b`;
- `apu_eor1`.

They call `load_flags` but omit `ori s1,s1,FLAG_SF`. Consequently generated code can modify runtime S1/C inside the block while `finish_block` is not told that PSW must be persisted. OR1's correct timing plus failed persisted carry is consistent with this defect.

State: **CONFIRMED semantic defect for OR1 persistence; HYPOTHESIS for the same missing-dirty cause across the sibling carry-bit generators until rerun.**

Decision:
1. Do NOT change the validated OR1 +1 timing rule based on this failure.
2. Add only the missing `FLAG_SF` dirty marking to all six carry-modifying bit generators.
3. Rerun the same bit matrix unchanged. This will simultaneously test OR1/EOR1/AND1/MOV1 C,bit persistence and continue into the timing/control cases that attempt 1 never reached.
4. TSET/TCLR remain separate: their +1 fixed debit is still diagnostic total-timing only; a bus-exact second-read implementation is planned after the carry persistence rerun.


## Bit carry persistence repair — rerun in progress 2026-09-18

Exact diagnostic HEAD: **`2602249fafb0084b3cbf45d352720e4e1ba73af9`**, one commit after failed bit attempt `1958dff2...`.

Controlled change is exactly one file, **`src/apu_alu.S +6/-6`**:
for `apu_mov1b`, `apu_or1a`, `apu_or1b`, `apu_and1a`, `apu_and1b`, `apu_eor1`, replace the `load_flags` delay-slot `nop` with:
`ori s1, s1, FLAG_SF`.

No timing charge, opcode dispatch, addressing or proof expectation changed.

Hypothesis: this marks PSW dirty so carry modifications that already occur correctly in generated runtime S1 are persisted at block exit. It directly addresses the observed OR1 symptom from `1958dff2...`.

Exact rerun workflows:
- **Build and Validate `35307619439`** — QUEUED at checkpoint.
- **APU Cycle And Span Proof `35307619471`** — QUEUED at checkpoint.

Readings:
- OR1 carry now persists and matrix advances => confirms dirty-flag root cause; continue judging unchanged bit timing rules.
- OR1 still returns C=0 => reject/narrow dirty-flag explanation and inspect generated spill path before further timing work.
- sibling AND/EOR/MOV1 C,bit failure after OR1 passes => family is not uniform; isolate that generator rather than broadening changes.
- TSET/TCLR remain total-timing-only in this rerun; their planned second-real-read repair is separate.


## Bit timing rerun — carry family VALIDATED; TSET/TCLR semantic defect isolated 2026-09-18

Exact diagnostic SHA **`2602249fafb0084b3cbf45d352720e4e1ba73af9`**:
- **Build and Validate `35307619439` SUCCESS**: normal, PROFILE and pinned Mupen smoke green.
- **APU Cycle And Span Proof `35307619471` FAILURE**, cycle-proof job **`105483171401`**.
- failed proof result artifact **`10532446373`**, digest `sha256:871961a769fce9d5fe79913bd4bce0f29687775a01981c3eaeea4ff66369a32f`;
- exact proof-build artifact **`10532302018`**, digest `sha256:03af6d1b7c3862113968eef5449939dec54fd0019d3f6acdde3b7f0a0077be71`.

### VALIDATED before the stop

Carry-persistence repair is confirmed:
- OR1 C,mem.bit: **9 cycles**, C persisted =1, semantic pass;
- OR1 C,/mem.bit: **9**, pass;
- EOR1 C,mem.bit: **9**, pass;
- MOV1 mem.bit,C: **10**, memory write pass;
- AND1 C,mem.bit control: **8**, C persistence pass;
- AND1 C,/mem.bit control: **8**, pass;
- MOV1 C,mem.bit control: **8**, pass;
- NOT1 control: **9**, memory pass;
- SET1 dp.bit control: **8**, memory pass;
- CLR1 dp.bit control: **8**, memory pass.

Thus the missing `FLAG_SF` dirty marking was the cause of the OR1 persistence defect and the six-generator family repair is **VALIDATED** for the reached carry-modifying cases.

Timing rules validated by these cases:
- OR1 normal/inverted +1 fixed;
- EOR1 +1 fixed;
- MOV1 mem.bit,C +1 fixed;
- AND1 variants / MOV1 C,mem / NOT1 / SET1 / CLR1 require no added fixed timing.

### TSET1 result — timing correct, flags wrong

`tset1_ram_total` measured:
- static debit **-168 = 8 units**, expected;
- total debit **-210 = 10 cycles**, exact reference total;
- RAM `0x0F -> 0xFF`, correct;
- observed PSW **0x02 (Z=1)**, expected **0x80 (N=1)** for `A=0xF0, data=0x0F`;
- semantic check failed, so TCLR1 was not reached.

**SUPPORTED ROOT CAUSE:** current generated order computes `SUB T0,T7,V0` in the delay slot of runtime `JAL apu_write8`; `apu_write8` then clobbers T0 before the subsequently emitted `queue_nz` instruction reads it. The comparison used for N/Z is therefore not preserved.

### Decision — repair TSET/TCLR semantically and bus-correctly

Do NOT consume the diagnostic fixed +1 TSET/TCLR charge.

Next controlled change:
1. remove TSET/TCLR fixed +1 charge;
2. compute A-first-read comparison and emit `queue_nz` **before** any helper call that can clobber T0;
3. emit the pinned-reference **second real `apu_read8`** to the same address;
4. preserve final write data through that read in A1 (all audited APU read paths do not touch A1; A2 used by queued NZ is also untouched);
5. emit the write using the first read's data;
6. update TSET/TCLR expected static debit from -168 to **-147**, while total remains **10 cycles** via 3 runtime memory accesses.

Expected: TSET PSW becomes N=1/Z=0, TCLR semantic case runs, both totals remain 10. Falsifier: changed total, wrong RAM/flags, or evidence A1/A2 are clobbered by a read path.


## TSET/TCLR bus-exact repair — proof in progress 2026-09-18

Exact diagnostic HEAD: **`df5fd66c76d5b3898a6c5d6020aacfff38e8daf5`**, one commit after carry-persistence authority `2602249f...`.

Controlled change:
- remove TSET/TCLR fixed +1 synthetic debit;
- preserve the first-read comparison into queued NZ before helper calls;
- emit the pinned-reference **second real `apu_read8`** to the same address;
- derive write data from the first read in that JAL delay slot and preserve it in A1;
- emit `apu_write8` afterward;
- A1/A2 preservation was statically audited across all current APU read paths.

Proof expectations change only for TSET/TCLR static debit:
- **-168 -> -147** (8 -> 7 static units);
- total reference remains **10 cycles**, now from three runtime memory accesses rather than two accesses + synthetic fixed cycle;
- RAM and PSW semantic expectations are unchanged.

Direct compare `2602249f... -> df5fd66c...`:
- `src/apu_alu.S` +29/-21;
- `scripts/apu_cycle_proof.py` +4/-5.

Exact workflows:
- **Build and Validate `35308254510`** — IN PROGRESS at checkpoint.
- **APU Cycle And Span Proof `35308254504`** — IN PROGRESS at checkpoint.

Acceptance:
1. all previously validated bit/carry/control cases remain green;
2. TSET1 total remains 10, RAM remains correct, PSW becomes N=1/Z=0 for directed case;
3. TCLR1 reaches execution and passes 10-cycle/RAM/PSW case;
4. no synthetic runtime cycle-debit instruction is needed for these instructions.


## SPC700 bit-family timing + semantics — VALIDATED 2026-09-18

Exact diagnostic authority: **`df5fd66c76d5b3898a6c5d6020aacfff38e8daf5`**.

CI:
- **Build and Validate `35308254510` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke green.
- **APU Cycle And Span Proof `35308254504` SUCCESS**, cycle-proof job **`105484997903`**.
- proof result artifact **`10531889516`**, digest `sha256:e51ef26ec7ccab0f85f1c4c2b6992bc554cf596d24854f408744deaaccb71427`;
- exact proof-build artifact **`10532298069`**, digest `sha256:a9d5fe5a8c2137b7b47fd900263c97a0d0388e5ce10071ec0a2ab86e52636a41`.

All global proof invariants are true:
- `all_runtime_cycle_debits_match_expected=true`;
- `all_semantics_match_expected=true`;
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

### VALIDATED bit-family cases

Added timing:
- OR1 C,mem.bit = **9 total cycles**, C persistence correct;
- OR1 C,/mem.bit = **9**, correct;
- EOR1 C,mem.bit = **9**, correct;
- MOV1 mem.bit,C = **10**, memory correct.

No-added-timing controls remain exact:
- AND1 C,mem.bit = **8**;
- AND1 C,/mem.bit = **8**;
- MOV1 C,mem.bit = **8**;
- NOT1 mem.bit = **9**;
- SET1 dp.bit = **8**;
- CLR1 dp.bit = **8**.

Carry-modifying bit generators now correctly mark PSW dirty via `FLAG_SF`; OR1/AND1/EOR1/MOV1 C,mem persistence passes.

TSET1/TCLR1 are now both timing- and bus-semantics-correct for the audited access pattern:
- TSET1: static **7 units**, three runtime memory accesses, **10 total cycles**, RAM `0x0F -> 0xFF`, PSW **0x80** (N=1/Z=0);
- TCLR1: static **7 units**, three runtime accesses, **10 total cycles**, RAM `0xFF -> 0xF0`, PSW **0x00**.

The previous synthetic +1 TSET/TCLR debit is **SUPERSEDED**. The validated implementation performs the second real `apu_read8` required by the pinned reference and preserves first-read-derived data/NZ across helper calls.

### Clean-consumption proof
`src/apu_alu.S` at clean foundation `4a3cf13a...` and diagnostic pre-bit authority `90c700a4...` have the **same blob SHA `ec2fbd2a00da7512f11b7a1ca89c807ced891b16`**. Diagnostic target blob `df5fd66c...` is `6bf7db555f2adf4a38c76b9b637cd4aae670ec5c` and contains no diagnostic/PROFILE references.

Decision: consume exactly that one core file into clean `phase2/apu-timing-foundation@4a3cf13a...`, then require exact clean Build/Validate before the next timing family.


## Clean bit timing/state candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@0fe8c45f9b1b1c719d52490d8f233950b4d4c489`**, one commit on top of clean word foundation `4a3cf13a...`.

Direct clean diff is exactly one core file:
- `src/apu_alu.S` +51/-17.

No diagnostic script/workflow changes.

Included validated bit work:
- OR1 normal/inverted +1 timing;
- EOR1 +1;
- MOV1 mem.bit,C +1;
- PSW dirty persistence for carry-modifying bit generators;
- TSET1/TCLR1 second real read, preserved first-read data/NZ, exact 10-cycle behavior.

Exact clean Build and Validate run: **`35308801632`**, QUEUED at checkpoint.

Dynamic semantic/cycle authority remains `df5fd66c...` / ares proof `35308254504` SUCCESS.

Do not modify clean `0fe8c45f...` until exact CI completes.

### Next read-only mapped timing family

Static comparison against pinned ares identifies a bounded remaining operand-form cluster:
- CMP dp,dp: likely +1 trailing idle;
- CMP dp,#imm: likely +1 trailing idle;
- `(X),(Y)` modifying ops: likely +1 dummy PC read;
- CMP `(X),(Y)`: likely +1 dummy PC read plus +1 trailing idle;
- MOV dp,#imm: missing a real dummy destination read before write; should prefer emitting the real `apu_read8` rather than a synthetic +1 debit.

JMP [abs+X] appears already covered by the validated indexed-addressing +1 and two runtime reads; treat as a no-change control, not a candidate fix.


## Clean bit timing/state foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@0fe8c45f9b1b1c719d52490d8f233950b4d4c489`** completed **Build and Validate `35308801632` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

Combined authority:
- dynamic bit timing/state/bus semantics: diagnostic **`df5fd66c76d5b3898a6c5d6020aacfff38e8daf5`**, APU Cycle And Span Proof **`35308254504` SUCCESS**;
- clean core consumption: `0fe8c45f...`;
- exact clean CI: `35308801632` SUCCESS.

Do not reopen the superseded synthetic TSET/TCLR +1 implementation: the validated path performs the real second read.

## Next controlled timing cluster — operand forms

Static comparison against pinned ares plus current generator structure yields a bounded three-rule experiment:

1. **CMP memory-form trailing idle**
   - `CMP dp,dp` (0x69) needs +1 trailing idle;
   - `CMP dp,#imm` (0x78) needs +1;
   - `CMP (X),(Y)` (0x79) needs the same +1 in addition to the addressing dummy cycle below.
   - Natural implementation point: `apu_cmpm`, because all three forms share it and modifying siblings do not.

2. **`(X),(Y)` dummy-PC cycle**
   - modifying forms OR/AND/EOR/ADC/SBC `(X),(Y)` need +1 dummy PC read cycle;
   - CMP `(X),(Y)` needs this +1 plus the CMP trailing idle.
   - Natural implementation point: `apu_bxy`.
   - This is a timing debit, consistent with the already validated treatment of dummy PC reads elsewhere; no claim of a separately observable bus read is made.

3. **MOV dp,#imm destination dummy read**
   - opcode 0x8F requires a real destination read before write;
   - opcode 0xFA MOV dp,dp is a no-change control and must NOT gain the extra read.
   - Use a dedicated `apu_movmi` handler for 0x8F rather than changing generic `apu_movm`.
   - Generated sequence: preserve immediate in A1 in the dummy-read JAL delay slot; `apu_read8` preserves A0/A1; then `apu_write8` to the same A0.
   - This reproduces the actual helper/bus access instead of a synthetic +1.

Directed proof matrix should include:
- CMP dp,dp;
- CMP dp,#imm;
- CMP (X),(Y);
- OR (X),(Y) modifying control for `apu_bxy`;
- MOV dp,#imm candidate;
- MOV dp,dp no-change control.

Expected totals including the existing 4-cycle BRA loop:
- CMP dp,dp: 10;
- CMP dp,#imm: 9;
- CMP (X),(Y): 9;
- OR (X),(Y): 9;
- MOV dp,#imm: 9;
- MOV dp,dp: 9.

Falsifiers: any shared-generator control overcharges, total `s3` differs, destination/data semantics differ, or new real-read path clobbers state.


## SPC700 operand-form timing proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`1dc544fa64a0d0fd9984bc94c492d0306766bf7a`**, one commit after validated bit-family authority `df5fd66c...`.

Direct compare `df5fd66c... -> 1dc544fa...` is exactly:
- `scripts/apu_cycle_proof.py` +32/-0;
- `src/apu_address.S` +4/-0;
- `src/apu_alu.S` +4/-0;
- `src/apu_emitter.S` +1/-1;
- `src/apu_transfer.S` +17/-0.

Controlled core rules:
- `apu_cmpm`: +1 trailing internal idle for memory-form CMP;
- `apu_bxy`: +1 dummy-PC timing cycle for `(X),(Y)` forms;
- opcode **0x8F MOV dp,#imm** dispatches to dedicated `apu_movmi`, which performs a real destination `apu_read8` before `apu_write8`; opcode 0xFA remains on generic `apu_movm`.

Directed cases and expected totals including the validated 4-cycle BRA loop:
- CMP dp,dp = 10;
- CMP dp,#imm = 9;
- CMP (X),(Y) = 9;
- OR (X),(Y) = 9;
- MOV dp,#imm = 9;
- MOV dp,dp no-change control = 9.

Exact workflows:
- **APU Cycle And Span Proof `35313083578`** — IN PROGRESS at checkpoint.
- **Build and Validate `35313083584`** — IN PROGRESS at checkpoint.

Acceptance:
1. previous complete regression matrix remains green;
2. three CMP cases match total timing and C/N/Z semantics;
3. OR `(X),(Y)` proves the shared `apu_bxy` +1 without overcharging a modifying sibling;
4. MOV dp,#imm gains exactly one real read and writes the immediate correctly;
5. MOV dp,dp remains exact and unchanged.

Falsifier: any total/static debit mismatch, shared-handler control overcharge, data/flags mismatch, or state clobber from the added real read.


## SPC700 operand-form timing — VALIDATED 2026-09-18

Exact diagnostic authority: **`1dc544fa64a0d0fd9984bc94c492d0306766bf7a`**.

CI:
- **Build and Validate `35313083584` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke green.
- **APU Cycle And Span Proof `35313083578` SUCCESS**, cycle-proof job **`105499188711`**.
- proof result artifact **`10533722861`**, digest `sha256:6f82bc03c9cc813facf2466f8c875540fa400f3f7e650444e850c731e642ba96`;
- exact proof-build artifact **`10533672483`**, digest `sha256:cb3d1956b9812f95ad76f7bf346309116bef745e444621ea48151cade3ecb22b`.

All global proof invariants remain true:
- `all_runtime_cycle_debits_match_expected=true`;
- `all_semantics_match_expected=true`;
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

### VALIDATED cases

- CMP dp,dp: static **8 units**, **10 total cycles**, C/N/Z postcondition correct.
- CMP dp,#imm: static **8**, **9 total**, flags correct.
- CMP (X),(Y): static **7**, **9 total**, flags correct.
- OR (X),(Y): static **6**, **9 total**, destination RAM correct; validates shared `apu_bxy` +1 without overcharge.
- MOV dp,#imm: static **7**, **9 total**, destination receives immediate correctly with the added real dummy read.
- MOV dp,dp control: static **7**, **9 total**, unchanged generic path remains correct.

Therefore the validated core rules are:
- `apu_cmpm`: +1 trailing internal idle;
- `apu_bxy`: +1 dummy-PC timing cycle;
- opcode 0x8F uses dedicated `apu_movmi` with a real destination read then write;
- opcode 0xFA remains on generic `apu_movm`.

### Clean-consumption note

Clean `0fe8c45f...` and diagnostic base `df5fd66c...` are byte-identical for:
- `src/apu_address.S`;
- `src/apu_alu.S`;
- `src/apu_transfer.S`.

`src/apu_emitter.S` differs only because the diagnostic branch carries a PROFILE-only cycle-proof observation block around block finalization. The direct diagnostic-base -> validated-target emitter change is exactly one opcode-table substitution:
- 0x8F `apu_movm -> apu_movmi`.

Decision: consume the three validated core blobs directly into clean foundation and apply only the single 0x8F table substitution to the clean emitter. Do NOT copy the diagnostic PROFILE block or proof script.


## Clean operand-form timing candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@68958b689750cbcdb2d703679b1a975858186637`**, one commit on top of clean bit foundation `0fe8c45f...`.

Direct clean diff is exactly four core files:
- `src/apu_address.S` +4/-0;
- `src/apu_alu.S` +4/-0;
- `src/apu_emitter.S` +1/-1;
- `src/apu_transfer.S` +17/-0.

No diagnostic script/workflow changes. Clean `apu_emitter.S` contains no `SODIUM64_PROFILE` / `apu_cycle_diag` references.

Included validated operand-form work:
- `apu_cmpm` +1 trailing idle;
- `apu_bxy` +1 dummy-PC timing cycle;
- dedicated 0x8F `apu_movmi` destination real-read + write;
- 0xFA remains on generic `apu_movm`.

Dynamic authority: diagnostic `1dc544fa...`, APU Cycle And Span Proof `35313083578` SUCCESS.
Diagnostic Build and Validate `35313083584` SUCCESS.

Exact clean Build and Validate run: **`35313761832`**, QUEUED at checkpoint.

Do not modify clean `68958b68...` until exact CI completes.


## Clean operand-form timing foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@68958b689750cbcdb2d703679b1a975858186637`** completed **Build and Validate `35313761832` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

Combined authority:
- dynamic operand-form timing/semantics: diagnostic **`1dc544fa64a0d0fd9984bc94c492d0306766bf7a`**, APU Cycle And Span Proof **`35313083578` SUCCESS**;
- clean core consumption: `68958b68...`;
- exact clean CI: `35313761832` SUCCESS.

## RESUME HERE — 2026-09-18 current authoritative state

### Phase / gate
- Road phase: **M1 faster/correcter base core**, APU/SPC700 timing foundation remains the active gate driver.
- This work primarily advances **Gate A / Gate C correctness prerequisites** and changes the validity of future Gate B performance measurements: configured `apu_clock=21` is no longer being treated as sufficient proof of effective full-rate SPC700 timing.

### Exact repo state
- `master`: **`a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`** — integrated truth, unchanged by this timing series.
- clean candidate: **`phase2/apu-timing-foundation@68958b689750cbcdb2d703679b1a975858186637`**.
- diagnostic authority: **`phase2/apu-cycle-proof@1dc544fa64a0d0fd9984bc94c492d0306766bf7a`**.
- no claim that the clean candidate is merged into master.

### Validated timing/state foundation now includes
- bounded JIT block behavior / NOP boundary repair already consumed earlier in this branch;
- fixed implied/register-transfer/stack timing;
- conditional/taken branch timing;
- CALL/TCALL/PCALL/RET/RET1/BRK timing and PCALL target repair;
- ADDW/SUBW/MOVW YA,dp word timing;
- absolute bit timing and carry-PSW persistence;
- bus-exact TSET1/TCLR1 second read + flags/data preservation;
- CMP memory-form trailing idle;
- `(X),(Y)` dummy-PC timing;
- bus-real MOV dp,#imm destination read;
- no-change controls for sibling/shared paths.

### Exact latest authorities
- bit-family proof `df5fd66c...` / run `35308254504` SUCCESS;
- clean bit foundation `0fe8c45f...` / run `35308801632` SUCCESS;
- operand-form proof `1dc544fa...` / run `35313083578` SUCCESS;
- clean operand foundation `68958b68...` / run `35313761832` SUCCESS.

### What this proves
- the directed SPC700 families above now match pinned-reference **total guest cycle debit** and the checked register/RAM/PSW semantics in the ares laboratory;
- all historical cases in the growing regression matrix still pass together;
- the latest clean candidate compiles and survives independent pinned Mupen smoke.

### What this does NOT prove
- complete 256-opcode SPC700 semantic/timing correctness;
- correct DSP PCM/echo/FIR/pitch-modulation fidelity;
- native cadence or performance improvement on real N64;
- that Gothicvania now reaches a higher frame budget;
- Gate B/C completion.

### Immediate next uncertainty
Before re-baselining performance, determine whether any **material SPC700 opcode/timing holes remain outside the validated families**. In particular inspect:
- opcode-table entries still mapped to `apu_unk`;
- explicit APU TODOs affecting arithmetic flags/semantics;
- any remaining pinned-reference dummy reads/idles not represented by existing addressing/operation generators.

Decision rule:
- if remaining gaps are bounded REQUIRED SUPPORT / correctness items, finish them first and then establish a new matched performance baseline;
- if the remaining gaps are only low-priority edge semantics that do not affect the current representative workload, record/defer them and re-baseline `68958b68...` before further optimization.

Do not resume Experiment 2B memory-helper optimization until this timing foundation has a new trustworthy baseline.


## Remaining SPC700 semantic inventory — 2026-09-18

Read-only scan of clean `phase2/apu-timing-foundation@68958b68...` found concrete remaining base-core gaps.

### REQUIRED SUPPORT — unimplemented opcodes
Opcode table still maps exactly four base SPC700 opcodes to `apu_unk`:
- **0xBE DAS A**;
- **0xDF DAA A**;
- **0xEF SLEEP/WAIT**;
- **0xFF STOP**.

Current `apu_unk` intentionally loops forever, so these are real compatibility holes, not minor timing approximations.

### OPEN semantic TODOs — Half-Carry / arithmetic
Seven explicit `TODO: set the H flag` sites remain:
- `apu_adca` — ADC accumulator forms;
- `apu_adcm` — ADC memory-modify forms;
- `apu_sbca` — SBC accumulator forms;
- `apu_sbcm` — SBC memory-modify forms;
- `apu_addw`;
- `apu_subw`;
- `apu_div`.

These are not one uniform change:
- ADC/SBC 8-bit share one nibble half-carry/borrow rule;
- ADDW/SUBW use the 16-bit word half-carry rule;
- DIV has special S-SMP H/V/result behavior and current simple MIPS DIV path needs separate semantic validation.

### Decision / order
Do NOT re-baseline performance yet; the remaining gaps are bounded base-SPC700 correctness work and therefore qualify as REQUIRED SUPPORT before declaring the timing foundation representative.

Proceed one semantic family at a time:
1. ADC/SBC 8-bit H flag proof + repair;
2. ADDW/SUBW H flag proof;
3. DIV semantic proof/repair;
4. DAA/DAS implementation once H/C prerequisites are trustworthy;
5. SLEEP/STOP scheduler semantics separately.

Each family must retain the full existing cycle/address/state regression matrix. Do not bundle WAIT/STOP scheduler behavior with arithmetic work.


## SPC700 ADC/SBC 8-bit Half-Carry proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`29aba03ab3eb07401cd521092e11aedc3436582e`**, one commit after operand-form proof authority `1dc544fa...`.

Direct compare `1dc544fa... -> 29aba03a...` is exactly:
- `src/apu_alu.S` +22/-4;
- `scripts/apu_cycle_proof.py` +28/-0.

Controlled semantic change only; **no guest cycle charge/addressing/dispatch change**.

Pinned ares reference:
- ADC: `HF = (x ^ y ^ result) & 0x10`;
- SBC reuses ADC with `~y`.

Candidate implementation updates exactly:
- `apu_adca`;
- `apu_adcm`;
- `apu_sbca`;
- `apu_sbcm`.

Directed matrix explicitly tests:
- ADC immediate H set;
- ADC immediate H clear from an initially-set H;
- SBC immediate H set;
- SBC immediate H clear from an initially-set H;
- ADC direct-page memory-modify H set;
- SBC direct-page memory-modify H set.

Timing expectations are unchanged. Any `s3`/static debit movement is a regression.

Exact workflows:
- **Build and Validate `35314192559`** — IN PROGRESS at checkpoint.
- **APU Cycle And Span Proof `35314192576`** — IN PROGRESS at checkpoint.

Acceptance:
1. H sets and clears exactly per pinned reference;
2. C/N/Z/V and data/register postconditions remain correct in directed cases;
3. accumulator and memory-modify generators agree;
4. exact guest cycle debit is unchanged;
5. entire existing timing/address/state regression matrix stays green.

Falsifiers:
- H remains stale when expected clear;
- SBC half-borrow polarity differs;
- accumulator vs memory form diverges;
- any total/static debit changes;
- any prior regression case fails.


## SPC700 ADC/SBC 8-bit Half-Carry — VALIDATED 2026-09-18

Exact diagnostic authority: **`29aba03ab3eb07401cd521092e11aedc3436582e`**.

CI:
- **Build and Validate `35314192559` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35314192576` SUCCESS**, cycle-proof job **`105502513799`**.
- proof result artifact **`10534743489`**, digest `sha256:fb25c9d2a9a71bd9a7117f953e95c9b42742011feb602e5a474eedfff50abe34`;
- exact proof-build artifact **`10533703688`**, digest `sha256:c90c229be2631974237d128427a73aba816acbf63a36d5e09ebbe662d5aab7d5`.

Directed cases all passed with unchanged timing:
- ADC immediate H set: A=0x10, H=1, **6 cycles**;
- ADC immediate H clear from initial H=1: A=0x02, H=0, **6 cycles**;
- SBC immediate H set: A=0x10, C/H=1, **6 cycles**;
- SBC immediate H clear from initial H=1: A=0x0F, C=1/H=0, **6 cycles**;
- ADC dp,#imm memory-modify: RAM result 0x10, H=1, **9 total cycles**;
- SBC dp,#imm memory-modify: RAM result 0x10, C/H=1, **9 total cycles**.

All global proof invariants remained true:
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

Validated core rule:
- ADC: H from bit 4 of `x ^ y ^ result`;
- SBC: equivalent half-borrow polarity using the existing complemented-operand subtraction path.

No guest timing changes were introduced.

### Decision
Consume only `src/apu_alu.S` core changes into clean timing foundation. Then run exact clean CI. Next isolated arithmetic semantic family: ADDW/SUBW H flag.


## Clean ADC/SBC Half-Carry candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@c2f2ecc1dfd521be724a832761db45d514ce2265`**, one commit on top of `68958b68...`.

Direct clean diff is exactly:
- `src/apu_alu.S` +22/-4.

No timing charge, addressing, dispatch, diagnostic script or workflow changes.

Dynamic semantic authority:
- diagnostic `29aba03a...`;
- Build and Validate `35314192559` SUCCESS;
- APU Cycle And Span Proof `35314192576` SUCCESS.

Exact clean Build and Validate run: **`35314885462`**, IN PROGRESS at checkpoint.

Do not modify clean `c2f2ecc1...` until exact CI completes. Next diagnostic work is isolated ADDW/SUBW H semantics on `phase2/apu-cycle-proof`.


## Clean ADC/SBC Half-Carry foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@c2f2ecc1dfd521be724a832761db45d514ce2265`** completed **Build and Validate `35314885462` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

## SPC700 ADDW/SUBW Half-Carry proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`06edb6afb10bc54dd79f6539c7484aad1b0d3469`**, one commit after ADC/SBC H authority `29aba03a...`.

Direct compare is exactly:
- `src/apu_alu.S` +13/-4;
- `scripts/apu_cycle_proof.py` +29/-0.

Controlled semantic change only; timing/addressing/dispatch unchanged.

Pinned reference semantics:
- ADW is two chained ADCs; final H is the high-byte nibble half-carry, equivalent to whole-word bit 12 of `x ^ y ^ result`.
- SBW is two chained SBCs; final H is the inverted whole-word bit-12 half-borrow relation.

Directed matrix:
- ADDW H set via low-byte carry into high byte;
- ADDW H clear from initially-set H;
- SUBW H set via low-byte borrow path;
- SUBW H clear via low-byte borrow path.

All four retain the already validated **9 total guest cycles**. Any s3/static debit movement is a regression.

Exact workflows:
- **Build and Validate `35315076872`** — QUEUED at checkpoint.
- **APU Cycle And Span Proof `35315076871`** — IN PROGRESS at checkpoint.

Acceptance:
1. A/Y results exact;
2. H set/clear exact;
3. C/N/Z/V remain correct for directed cases;
4. total/static cycles unchanged;
5. entire prior regression matrix remains green.


## SPC700 ADDW/SUBW Half-Carry — VALIDATED 2026-09-18

Exact diagnostic authority: **`06edb6afb10bc54dd79f6539c7484aad1b0d3469`**.

CI:
- **Build and Validate `35315076872` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35315076871` SUCCESS**, cycle-proof job **`105505142348`**.
- proof result artifact **`10535525484`**, digest `sha256:1389cc5dde25b485506c3e35e5e1e3af4b69ec2bf395ad761fd6657437098ef0`;
- exact proof-build artifact **`10535025192`**, digest `sha256:0d6597be2a80960cdcc8dc8eeda88b2c4da7e37bf90a6ea631201da9617b2d85`.

Directed word-H cases all passed at unchanged **9 total guest cycles**:
- ADDW H set via low-byte carry: YA 0x0FFF + 0x0001 -> **0x1000**, H=1;
- ADDW H clear from initial H=1: 0x0100 + 0x0100 -> **0x0200**, H=0;
- SUBW H set via low-byte borrow path: 0x1100 - 0x0001 -> **0x10FF**, C/H=1;
- SUBW H clear via low-byte borrow path: 0x1000 - 0x0001 -> **0x0FFF**, C=1/H=0.

All global invariants remained true:
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

Validated rules:
- ADDW H = whole-word bit 12 of `x ^ y ^ result`;
- SUBW H = inverted whole-word bit-12 half-borrow relation.

No timing changes were introduced.

### Decision
Consume only `src/apu_alu.S` core changes into clean timing foundation. Then exact clean CI. Next semantic family: DIV YA,X, which requires full result/H/V behavior proof, not just a flag patch.


## Clean ADDW/SUBW Half-Carry candidate — checkpoint 2026-09-18

Clean branch is **`phase2/apu-timing-foundation@74455bb8ae15b7b654eef7f9812a65db7ccdd964`**, consuming only validated `src/apu_alu.S` changes from diagnostic `06edb6af...`.

Exact clean Build and Validate run: **`35315787073`**, IN PROGRESS at checkpoint.

Dynamic authority remains:
- `06edb6af...`;
- Build and Validate `35315076872` SUCCESS;
- APU Cycle And Span Proof `35315076871` SUCCESS.

## DIV YA,X semantic defect — dynamic baseline before repair

Existing regression case `div_bra` on diagnostic run `35315076871` provides a direct pre-repair observation with default injected state:
- X = **0x04**;
- Y = **0x5A**;
- A = **0x11**;
- inherited DIV+BRA total timing = **16 cycles**, correctly measured.

Observed inherited Sodium64 result:
- A = **0x84**;
- Y = **0x01**;
- PSW = **0xC0**.

Pinned ares/S-SMP reference for the same DIV input:
- H = `(Y & 0x0F) >= (X & 0x0F)` => 1;
- V = `Y >= X` => 1;
- because `Y >= 2*X`, DIV must use the S-SMP overflow branch, not ordinary integer division;
- expected A = **0xAC**;
- expected Y = **0x61**;
- expected N=1, Z=0, H=1, V=1 => PSW arithmetic bits **0xC8**.

Therefore the inherited DIV implementation is **CONFIRMED semantically wrong**, not merely missing H:
- normal MIPS DIV is used unconditionally;
- overflow-branch A/Y behavior is absent;
- H is absent;
- X=0 behavior is also not safely modeled by the inherited direct MIPS DIV path.

Timing itself (12-cycle DIV + 4-cycle BRA) is already validated and must remain unchanged.

### Next controlled DIV repair
Use a dedicated runtime assembly helper called by generated DIV JIT code. It will:
- preserve C/I/B/P and clear/recompute H/V;
- set H and V from original Y/X;
- use normal quotient/remainder only when `Y < 2*X`;
- otherwise reproduce the S-SMP overflow formula;
- handle X=0 through the overflow formula, avoiding undefined divide-by-zero behavior;
- leave N/Z to the existing queued-A mechanism.

Directed proof cases must cover:
1. normal branch, V/H clear;
2. normal branch with quotient >255 and V/H set;
3. known failing overflow case X=4,Y=0x5A,A=0x11;
4. overflow case with H clear;
5. X=0;
6. unchanged **16 total cycles** and full historical regression matrix.


## Clean ADDW/SUBW Half-Carry foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@74455bb8ae15b7b654eef7f9812a65db7ccdd964`** completed **Build and Validate `35315787073` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

## SPC700 DIV semantic repair proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`18c25ce797ff49957da99cb0a31aef30a661fdfc`**, one commit after ADDW/SUBW H authority `06edb6af...`.

Direct compare is exactly:
- `src/apu_alu.S` +64/-17;
- `scripts/apu_cycle_proof.py` +32/-0.

Controlled repair:
- retain existing validated DIV timing: opcode fetch + 11 extra cycles = **12-cycle DIV**;
- replace unconditional normal MIPS division with one generated JAL to a dedicated runtime helper;
- helper recomputes H/V from original Y/X;
- normal arithmetic only when `Y < 2*X`;
- otherwise reproduce the S-SMP overflow formula;
- X=0 necessarily takes the special path, avoiding undefined divide-by-zero;
- N/Z still use the existing queued-A mechanism;
- C/I/B/P are preserved.

Directed semantic matrix, all still **16 cycles including trailing BRA**:
1. normal branch with H/V clear and preserved C;
2. normal branch with 9-bit quotient and H/V set;
3. known inherited failure X=4,Y=0x5A,A=0x11;
4. overflow branch with H clear;
5. X=0;
6. zero-result N/Z path.

Exact workflows:
- **APU Cycle And Span Proof `35316149582`** — IN PROGRESS at checkpoint.
- **Build and Validate `35316149675`** — IN PROGRESS at checkpoint.

Acceptance:
- all six A/Y outputs match pinned reference;
- H/V/N/Z exact and C preserved where directed;
- static/total guest debit unchanged;
- full historical regression matrix remains green;
- normal/PROFILE build and Mupen smoke remain green.


## DIV repair attempt 1 — helper arithmetic correct; MIPS JAL delay-slot bug in N/Z queue 2026-09-18

Exact diagnostic SHA **`18c25ce797ff49957da99cb0a31aef30a661fdfc`**:
- **Build and Validate `35316149675` SUCCESS**: normal, PROFILE and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35316149582` FAILURE**, cycle-proof job `105508379053`.
- failed proof result artifact **`10535217649`**, digest `sha256:276e5c96276ee443e4861154e3871b55cd0ac73fcdba21afb99bd601d16f7b0a`;
- exact proof-build artifact **`10534902330`**, digest `sha256:049ea06b575bd18a044b68ca550049e03b1bff850dcfdeeede36608de1175a43`.

### What passed before the failure

The runtime helper fixed the previously confirmed DIV arithmetic defect for the historical default case:
- X=0x04, Y=0x5A, A=0x11;
- repaired A=**0xAC**, Y=**0x61**;
- H/V=1/1;
- total timing remains **16 cycles including BRA**.

Directed normal case also passed:
- X=4, Y=1, A=8 -> A=0x42, Y=0;
- expected preserved C, H/V/N/Z clear;
- exact 16-cycle total.

Attempt stopped on `div_normal_9bit_quotient`:
- actual A=0x40, Y=0: arithmetic is correct;
- H/V are correct;
- total/static timing is correct;
- observed PSW **0x4A** vs expected **0x48**, i.e. Z remained set incorrectly.

### Root cause — CONFIRMED from generated-code ordering

The provisional interpretation that N/Z were being derived from Y is **REJECTED**.

`apu_div` emitted:
1. JAL to `apu_div_runtime`;
2. immediately afterward the instruction generated by `queue_nz`: `ANDI A2,T7,0xFF`.

On MIPS, instruction #2 is the **JAL delay slot** and therefore executes *before* entering the runtime helper. It queues the **old A**, not repaired A.

This exactly explains both observations:
- default old A=0x11 -> neither N nor Z, producing H/V-only 0x48 instead of expected 0xC8 despite repaired A=0xAC;
- 9-bit case old A=0x00 -> Z=1, producing 0x4A despite repaired A=0x40.

The runtime helper does not clobber A2; the defect is purely emitted instruction ordering.

### Decision

Keep the runtime DIV arithmetic helper unchanged. Insert one generated MIPS NOP (`SLL ZERO,ZERO,0`) immediately after emitted helper JAL so the JAL delay slot is neutral. Then `queue_nz` executes after helper return and snapshots new T7/A.

Do not change guest cycle accounting or proof expectations. Rerun the identical six-case DIV matrix plus full regression suite.


## DIV repair attempt 2 — delay-slot correction in progress 2026-09-18

Exact diagnostic SHA: **`f3bad9af878b94e7be3a2f3f1d0d04fa8db103ec`**, one commit after failed-but-informative DIV helper SHA `18c25ce...`.

Direct compare `18c25ce... -> f3bad9af...` is exactly:
- `src/apu_alu.S` +2/-0.

Controlled change:
- emit one runtime MIPS NOP (`SLL ZERO,ZERO,0`) immediately after the generated JAL to `apu_div_runtime`;
- no guest timing, arithmetic, flags formula, dispatch or harness expectation change.

Question: does neutralizing the JAL delay slot make queued N/Z sample repaired T7/A after helper return while leaving the already-correct A/Y/H/V and 16-cycle DIV+BRA total unchanged?

Exact workflows:
- **Build and Validate `35317084579`** — QUEUED at checkpoint.
- **APU Cycle And Span Proof `35317084547`** — IN PROGRESS at checkpoint.

Acceptance:
- all six directed DIV cases pass A/Y/H/V/N/Z;
- known overflow case becomes A=0xAC,Y=0x61,PSW arithmetic=0xC8;
- 9-bit normal case becomes A=0x40,Y=0,PSW H/V=0x48 with Z clear;
- X=0 passes without divide-by-zero;
- all total/static timing remains unchanged;
- complete historical regression matrix remains green.


## SPC700 DIV semantic repair — VALIDATED 2026-09-18

Final diagnostic authority: **`f3bad9af878b94e7be3a2f3f1d0d04fa8db103ec`**.

CI:
- **Build and Validate `35317084579` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35317084547` SUCCESS**, cycle-proof job **`105511291125`**.
- proof result artifact **`10535762581`**, digest `sha256:eccf0a9ad14818f32097858126ba015805eec458de3413ab2ca3fa1960197da6`;
- exact proof-build artifact **`10535992426`**, digest `sha256:9a452e37cb0d70ed2b2d5f903b1886822a3f5cb7945281dfc8cf23bc6067726e`.

The inherited unconditional MIPS DIV behavior is superseded.

Validated repair:
- dedicated runtime DIV helper reproduces the S-SMP normal and overflow branches;
- H = `(Y & 0x0f) >= (X & 0x0f)`;
- V = `Y >= X`;
- normal quotient/remainder path only when `Y < 2*X`;
- overflow formula used otherwise;
- X=0 is handled by the special path, avoiding undefined divide-by-zero;
- C/I/B/P preserved;
- N/Z queue reads repaired A after helper return by neutralizing the generated JAL delay slot with one MIPS NOP;
- already-validated guest timing remains exactly **12-cycle DIV**, or **16 total with the trailing BRA test loop**.

Directed results include:
- normal H/V-clear case: A=0x42,Y=0, PSW preserves C, **16 cycles**;
- 9-bit-quotient normal case: A=0x40,Y=0, H/V=1/1, Z clear, **16 cycles**;
- inherited failing overflow case X=4,Y=0x5A,A=0x11 now produces **A=0xAC,Y=0x61**, H/V=1/1 with correct N/Z;
- X=0 case passes without divide-by-zero and produces the pinned-reference state;
- zero-result case queues Z from repaired A correctly.

All global invariants remain true:
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

### Discarded explanation preserved
Attempt 1's N/Z mismatch was NOT caused by the runtime helper clobbering A2 or by sampling Y. The generated `queue_nz` instruction occupied the runtime JAL delay slot and therefore sampled old A before the helper ran. That explanation is REJECTED and should not be revisited.

### Decision
Consume only validated `src/apu_alu.S` DIV repair into clean timing foundation if clean/base blob identity is confirmed. Then exact clean CI.

Next REQUIRED SUPPORT arithmetic work: implement and prove **DAA (0xDF) / DAS (0xBE)** now that H/C semantics are trustworthy. SLEEP/STOP remain separate scheduler-state work.


## Clean DIV semantic candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@7f1d7f52c320ea065699f92737d1b320140f8141`**, one commit on top of validated ADDW/SUBW-H foundation `74455bb8...`.

Direct clean diff is exactly:
- `src/apu_alu.S` +66/-17.

No diagnostic script/workflow changes.

Dynamic semantic/timing authority:
- final diagnostic `f3bad9af...`;
- Build and Validate `35317084579` SUCCESS;
- APU Cycle And Span Proof `35317084547` SUCCESS.

Exact clean Build and Validate run: **`35345349822`**, IN_PROGRESS at checkpoint.

Do not modify clean `7f1d7f52...` until exact CI completes. Next diagnostic family is DAA/DAS only; SLEEP/STOP remain separate scheduler work.


## SPC700 DAA/DAS implementation proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`35a983e7e0d8f9161d599e498acbf8b004f2d6e5`**, one commit after validated DIV authority `f3bad9af...`.

Controlled core additions:
- `apu_daa` / `apu_das` handlers;
- runtime helpers implementing pinned S-SMP decimal-adjust semantics;
- opcode 0xDF maps to DAA;
- opcode 0xBE maps to DAS.

Guest timing:
- opcode fetch already charged;
- each instruction adds +2 fixed cycles for dummy PC read + idle;
- expected instruction total = **3 cycles**, or **7 with trailing validated BRA loop**.

Pinned semantics reproduced:
- DAA: if C or A>0x99, add 0x60 and set C; then if H or low nibble>9, add 0x06;
- DAS: if !C or A>0x99, subtract 0x60 and clear C; then if !H or low nibble>9, subtract 0x06;
- H and V preserved;
- N/Z recomputed from adjusted A;
- other PSW bits preserved.

Directed cases:
- DAA low-only;
- DAA high-only;
- DAA both adjustments with wrap to zero;
- DAS low-only;
- DAS high-only;
- DAS both adjustments to negative result.

Exact workflows are the newest runs for SHA `35a983e7...` on the diagnostic branch. Acceptance requires exact A/C/N/Z/H/V semantics, 7-cycle total with BRA, and all historical regression cases green.

SLEEP/STOP are deliberately excluded and remain separate scheduler-state work.


## Clean DIV semantic foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@7f1d7f52c320ea065699f92737d1b320140f8141`** completed **Build and Validate `35345349822` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

Combined authority:
- dynamic DIV semantic/timing proof: diagnostic `f3bad9af...`, ares run `35317084547` SUCCESS;
- clean consumption: exactly `src/apu_alu.S`;
- exact clean CI `35345349822` SUCCESS.

Next active diagnostic remains DAA/DAS at `35a983e7...`; SLEEP/STOP stay separate scheduler-state work.


## DAA/DAS proof attempt 1 — harness false negative 2026-09-18

Exact diagnostic SHA **`35a983e7e0d8f9161d599e498acbf8b004f2d6e5`**:
- **Build and Validate `35345543217` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35345543241` FAILURE**, cycle-proof job **`105601488300`**.
- failed proof artifact **`10547251142`**, digest `sha256:ae7405a8b48078ef8dc42be5fb941258ae429ae8c0597afcc14a79e59a739392`;
- exact proof-build artifact **`10547145095`**, digest `sha256:07c466993c6bdee4859f95f92106b76038ee348413e3cc7b44b61fcaa84c8c2c`.

The failure is **REJECTED as core evidence**. The entire historical regression matrix, including final DIV repair cases, passed before the harness reached the new decimal-adjust cases.

Traceback:
`TypeError: compile_one_case() missing 1 required keyword-only argument: 'y_value'`.

Cause: all six new `decimal_adjust_cases` omitted the harness-only `y_value` parameter. No DAA/DAS case executed, so DAA/DAS dynamic semantics/timing remain **UNMEASURED** by attempt 1.

Decision:
- do NOT modify DAA/DAS core code;
- do NOT alter cycle or semantic expectations;
- add only `y_value=0x06` to the six diagnostic case dictionaries;
- rerun the identical proof.


## DAA/DAS proof attempt 2 — harness-only rerun in progress 2026-09-18

Exact rerun SHA: **`db4137947d17403c81948c98907b16d424958181`**.

Direct compare `35a983e7... -> db413794...` is harness-only:
- `scripts/apu_cycle_proof.py` +6/-6;
- each decimal case now supplies required `y_value=0x06`.

No APU core source, timing expectation, semantic expectation or dispatch changed.

Exact workflows:
- **Build and Validate `35346467855`** — QUEUED at checkpoint.
- **APU Cycle And Span Proof `35346467906`** — IN PROGRESS at checkpoint.

Interpretation rules:
- all six decimal cases + historical regression matrix pass => DAA/DAS core at `35a983e7...` VALIDATED;
- any decimal semantic/timing failure => inspect that case as core evidence;
- any new harness/setup failure => fix only harness after proving it is not core behavior.


## SPC700 DAA/DAS — VALIDATED 2026-09-18

Core diagnostic authority: **`35a983e7e0d8f9161d599e498acbf8b004f2d6e5`**.
Harness-only rerun authority: **`db4137947d17403c81948c98907b16d424958181`**.

CI:
- **Build and Validate `35346467855` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35346467906` SUCCESS**, cycle-proof job **`105604478664`**.
- proof result artifact **`10547176802`**, digest `sha256:8867600f6a186efd91f8f60525aa3577789979eb1c6b072f2d80773f604ae3f3`;
- exact proof-build artifact **`10547940108`**, digest `sha256:5587c8a5c1d3384656bcd55e91e343ef7891aad74b8b19bacbfe7a6217d06bc4`.

All global invariants are true:
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

Directed results, each DAA/DAS followed by the validated 4-cycle BRA:
- DAA low-only: A=0x10, PSW V preserved, **7 cycles**;
- DAA high-only: A=0x75, C/V preserved/set correctly, **7**;
- DAA both adjustments with wrap: A=0x00, C/H/V/Z correct, **7**;
- DAS low-only: A=0x0F, C/V preserved, **7**;
- DAS high-only: A=0x15, H/V preserved and C cleared as reference requires, **7**;
- DAS both adjustments: A=0x9A, N/V correct, **7**.

Validated implementation:
- opcode 0xDF DAA is now implemented;
- opcode 0xBE DAS is now implemented;
- each charges +2 fixed guest cycles beyond fetch;
- runtime helper semantics match pinned ares;
- H/V and unrelated PSW bits are preserved; C/N/Z change per reference.

Attempt 1 failure is permanently classified **HARNESS FALSE NEGATIVE / REJECTED as core evidence**.

Decision: consume only DAA/DAS core into clean `phase2/apu-timing-foundation@7f1d7f52...`; then exact clean CI. Remaining unimplemented base SPC700 opcodes are only SLEEP/STOP and require scheduler-state design, not a normal opcode patch.


## Clean DAA/DAS candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@9f070faeb6e9ea20012601d3eff1947658cfb93f`**, one commit on top of clean DIV foundation `7f1d7f52...`.

Direct clean diff is exactly:
- `src/apu_alu.S` +95/-0;
- `src/apu_emitter.S` +2/-2.

Clean emitter contains no `SODIUM64_PROFILE` / `apu_cycle_diag` references.

Dynamic authority:
- DAA/DAS core `35a983e7...`;
- harness-only rerun `db413794...`;
- Build and Validate `35346467855` SUCCESS;
- APU Cycle And Span Proof `35346467906` SUCCESS.

Exact clean Build and Validate run: **`35347334777`**, IN PROGRESS at checkpoint.

Remaining unimplemented base SPC700 opcodes after this candidate are only:
- 0xEF SLEEP/WAIT;
- 0xFF STOP.

Do not implement them as normal returning JIT handlers. Pinned ares models each as a persistent processor state repeatedly consuming `read(PC)+idle` until external synchronization/reset semantics release it. Next work is scheduler/state design and proof, isolated from arithmetic/timing work.


## SLEEP/STOP scheduler design — pre-implementation checkpoint 2026-09-18

Pinned ares SFC behavior:
- SMP main checks `r.wait` / `r.stop` before decoding another opcode;
- WAIT and STOP each latch persistent state and repeatedly execute `read(PC) + idle`;
- pinned source clears these state bits in SPC700 power/reset; no ordinary CPU->APU port write wake path was found.

Sodium64 scheduler fit:
- `cpu_execute` hands control to `apu_execute` according to `s3`;
- `apu_execute` already checks DSP deadline before entering JIT;
- APU timers are derived from the same advancing `s3` timeline.

Selected diagnostic architecture:
1. add `apu_halt` byte: 0=RUN, 1=WAIT, 2=STOP;
2. `apu_execute` keeps the existing DSP-deadline check first, then if halted performs a real `apu_read8(apu_count)` plus one idle-cycle debit and returns to `cpu_execute`; PC does not advance;
3. SLEEP/STOP generated handlers set their distinct latch and immediately perform the **first** real read of next PC + one idle before block return, avoiding a one-iteration scheduler/interleave delay;
4. normal finish-block stores the already-incremented next PC;
5. CPU->APU communication must not clear the latch.

Expected timing:
- entry block containing SLEEP or STOP: opcode fetch + first read + idle = **3 SPC cycles**;
- each subsequent halted scheduler service = **2 SPC cycles**;
- halt PC remains instruction-after-opcode.

This is a scheduler-state proof, not a normal fixed-cycle opcode patch. Acceptance must show distinct WAIT/STOP latch values, exact entry/tick debits, stable PC, and no JIT/decode advance while halted. Reset/power initialization remains `apu_halt=0`.


## Clean DAA/DAS foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@9f070faeb6e9ea20012601d3eff1947658cfb93f`** completed **Build and Validate `35347334777` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

Artifacts:
- normal build `10547931294`, digest `sha256:5c98696cb55d7c824f0b19b0bac0cecdd2f28f31b801223be7587365b620ce27`;
- profile build `10547173242`, digest `sha256:0caa0a0e92f4b7ab85c5324c82e6205c0479d9862887237ad3a6a2702d994597`;
- emulator smoke `10547383323`, digest `sha256:684d663493aa48b7d38bd5d37a5a9aa11cb97f40378493129cf5fb55c4d47676`.

State: **VALIDATED CANDIDATE**, unmerged.

The diagnostic and clean branches are byte-unchanged from their recorded DAA/DAS checkpoints; no SLEEP/STOP implementation exists yet. The next technical batch is the already-designed isolated SLEEP/STOP scheduler-state proof. Do not re-baseline Gothicvania or resume memory-helper optimization before this bounded base-SPC700 correctness item is resolved.


## SPC700 SLEEP/STOP scheduler-state proof — checkpoint 2026-09-18

Exact diagnostic SHA: **`e7cc3cf27f10bd5e3310a158bd56cf9965b7166e`**, one atomic commit after validated DAA/DAS diagnostic authority `db413794...`.

Direct compare `db413794... -> e7cc3cf...` is exactly:
- `src/apu.S` +20/-0;
- `src/apu_emitter.S` +39/-2;
- `scripts/apu_cycle_proof.py` +116/-0;
- `.github/workflows/apu-cycle-proof.yml` +8/-2.

### Controlled architecture under test
- add persistent `apu_halt`: 0=RUN, 1=WAIT/SLEEP, 2=STOP;
- keep the existing DSP-deadline test ahead of halt servicing;
- halted `apu_execute` performs real `apu_read8(apu_count)` + one idle-cycle debit and returns to `cpu_execute`, without changing PC or entering JIT/decode;
- opcode 0xEF and 0xFF now latch distinct states;
- the entry JIT block immediately performs the first real read of the instruction-after-opcode PC + idle before returning;
- normal `finish_block` remains authoritative for storing that next PC;
- ordinary proof setup clears `apu_halt` so persistent state cannot contaminate historical cases.

Expected guest timing:
- SLEEP/STOP entry = opcode fetch + real read(next PC) + idle = **3 SPC cycles**;
- each subsequent halted scheduler service = real read(same PC) + idle = **2 SPC cycles**;
- PC remains `TEST_PC+1`;
- halt state remains latched;
- JIT pointer remains unchanged on halted service.

### Dynamic proof additions
Directed proof requires separately for SLEEP and STOP:
1. entry total = 3 cycles and state = 1/2 respectively;
2. two consecutive halted scheduler services each debit exactly 2 cycles;
3. the real bus read address equals the stable instruction-after-opcode PC;
4. PC and halt state remain unchanged;
5. JIT pointer does not advance, proving no further decode/compile during halted service;
6. the full historical timing/address/semantic regression matrix remains green.

The proof runs halt cases last so their persistent state cannot affect earlier cases.

### Exact workflows now running
- **Build and Validate `35349865989` SUCCESS** — normal build, PROFILE build and pinned Mupen emulator smoke all green.
- **APU Cycle And Span Proof `35349866045`** — IN PROGRESS; profile-build is already SUCCESS and the dynamic ares proof is still running.

Acceptance: both workflows green and all new halt invariants true.

Falsifiers:
- compile/PROFILE/Mupen regression;
- entry debit != 3 cycles;
- any persistent tick != 2 cycles;
- read address differs from stable PC;
- PC advances, latch changes, or JIT pointer moves while halted;
- any prior regression case fails.

If accepted, consume only the runtime core files `src/apu.S` and `src/apu_emitter.S` into clean `phase2/apu-timing-foundation@9f070fae...`, then run exact clean CI. Do **not** copy diagnostic script/workflow into the clean branch.

Do not re-baseline Gothicvania or resume the memory-helper experiment until this last base-SPC700 scheduler correctness item is resolved.


## SPC700 SLEEP/STOP scheduler-state proof — VALIDATED 2026-09-18

Exact diagnostic authority: **`e7cc3cf27f10bd5e3310a158bd56cf9965b7166e`**.

CI:
- **Build and Validate `35349865989` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35349866045` SUCCESS**, cycle-proof job **`105615549216`**.
- proof result artifact **`10549793093`**, digest `sha256:16ecb1d8f86c6045b11d2999c9562c0d166081826ab0583cb7cbbe204cb7a111`;
- exact proof-build artifact **`10548992246`**, digest `sha256:3be016038bb0f209d5528499f6d997b55edb18c8475e54568e950b90f469295a`;
- normal Build and Validate artifact **`10548652376`**, digest `sha256:07679ab4051faff12658e86600898f508c542e5e6285e3fb88732cee66bfdc44`.

Dynamic results at `apu_clock=21`:
- SLEEP entry: PC 0x0200 -> **0x0201**, latch=**1**, static debit=-42, total debit=**-63 = 3 SPC cycles**;
- STOP entry: PC 0x0200 -> **0x0201**, latch=**2**, static debit=-42, total debit=**-63 = 3 SPC cycles**;
- SLEEP halted tick 1: real read address **0x0201**, PC remains 0x0201, latch remains 1, JIT pointer unchanged, debit **-42 = 2 cycles**;
- SLEEP halted tick 2: same invariants, **2 cycles**;
- STOP halted tick 1: real read address **0x0201**, PC remains 0x0201, latch remains 2, JIT pointer unchanged, debit **2 cycles**;
- STOP halted tick 2: same invariants, **2 cycles**.

All proof summary invariants are true:
`all_halt_scheduler_ticks_match_expected`,
`all_header_spans_match_source_prediction`,
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

Pinned ares authority also confirms SMP dispatch checks persistent `r.wait`/`r.stop` before decoding another opcode and each state repeatedly performs `read(PC)+idle`; power/reset clears both states.

### Decision
SLEEP/STOP scheduler semantics are **VALIDATED** in the ares laboratory. This closes the previously enumerated `apu_unk` base-opcode holes: 0xEF and 0xFF are no longer unimplemented in the validated diagnostic core.

Consume only runtime core changes from `src/apu.S` and `src/apu_emitter.S` into clean `phase2/apu-timing-foundation@9f070fae...`. Do not copy diagnostic proof/workflow changes. Then run exact clean Build and Validate before any re-baseline.

This does **not** prove Gate B performance or real-N64 behavior. The added normal `apu_execute` halt-state check is a correctness cost that must be included in the new matched performance baseline rather than assumed negligible.


## Clean SLEEP/STOP consumption — checkpoint 2026-09-18

Clean candidate advanced atomically from validated DAA/DAS `9f070fae...` to **`phase2/apu-timing-foundation@9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`** with message `fix: implement SPC700 SLEEP STOP scheduler state`.

Direct clean compare is exactly two runtime files:
- `src/apu.S` +20/-0;
- `src/apu_emitter.S` +39/-2.

No diagnostic script or workflow changes were consumed.

The clean `src/apu.S` blob is exactly the dynamically validated diagnostic runtime blob `6f7a8f2015f588dd7b8773a28c22e57ed6cb82a7`. The clean emitter carries the same SLEEP/STOP runtime logic while retaining the clean branch's absence of PROFILE-only cycle diagnostics.

Exact clean validation:
- **Build and Validate `35350851813`** — QUEUED at checkpoint.

Acceptance: normal build, PROFILE build and pinned Mupen emulator smoke all SUCCESS on exact SHA `9204ad2f...`.

If green: mark SLEEP/STOP clean candidate VALIDATED and the enumerated base-SPC700 opcode/semantic foundation complete enough to move to a fresh matched APU/audio performance baseline. If red: diagnose clean-integration failure; do not reinterpret the already-green dynamic diagnostic proof.


## Clean SLEEP/STOP foundation — VALIDATED 2026-09-18

Exact clean candidate: **`phase2/apu-timing-foundation@9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`**.

**Build and Validate `35350851813` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen normal/profile emulator smoke and profile decode SUCCESS.

Artifacts:
- normal build **`10549768562`**, digest `sha256:31c0a7c41d74c75c7661de03d4b021736c9e9e4e420ea8ab5c51ed87bfb14705`;
- PROFILE build **`10548818655`**, digest `sha256:9d08f44a06ef252732221b33e9b7154340f6e2e5d709bae6dcded607370490ca`;
- emulator smoke **`10548888744`**, digest `sha256:6bddf2a328b3be20da8bbd6e38e5587ee9624386c55b03761cb22922f1c0092f`.

State: **VALIDATED CANDIDATE**, unmerged.

The clean branch now contains the validated DAA/DAS, Half-Carry, DIV, timing/address/bus corrections and persistent SLEEP/STOP scheduler state without diagnostic-only proof code.

### Immediate next action
Do **not** resume the old memory-helper experiment from pre-foundation measurements. First establish a **fresh matched, repeated APU/audio baseline on this exact clean SHA**. The audit demonstrated same-SHA ares A/A spread (44/60 vs 48/60), so single-run deltas of a few FPS are not attribution-quality evidence.

Baseline design must preserve:
- same exact `9204ad2f...` build/artifact;
- same Gothicvania workload and pinned ares configuration;
- CPU JIT + RSP interpreter laboratory mode;
- frameskip 0, full-rate APU and audio path intact;
- repeated independent observations sufficient to characterize run-to-run variance;
- paired DSP-lateness / audio-timing evidence, not FPS alone.

Only after that baseline should a new optimization hypothesis be selected from the corrected profile distribution.


## E1 matched-window baseline repair — running 2026-09-18

Measurement-only branch: **`phase2/apu-matched-baseline@d20258be3f783728b500cfd95065abc185b14f2b`**, created directly from validated clean core **`9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`**.

Direct compare `9204ad2f... -> d20258be...` is exactly two added diagnostic files and **zero emulator-core changes**:
- `.github/workflows/apu-matched-baseline.yml` +463;
- `scripts/gdb_matched_profile.py` +309.

### Measurement contract under test

The old open-homebrew harness is not attribution-grade for small deltas because it patches settings after host-time warmup/settle and terminates on host-time/sample targets, producing unmatched guest phases.

The new bounded E1 harness instead:
1. stops at the **first `cpu_execute` before any guest CPU/APU execution**;
2. there sets APU clock=21, frameskip=0, audio=4, precision=8, zeros APU JIT lookup and resets JIT pointer;
3. uses local `update_fps` as an exact guest boundary. At its entry exactly 60 VI have elapsed and `fps_emulate` still contains completed SNES frames for that just-finished interval;
4. warms for exactly **2 complete 60-VI windows**;
5. resets only profiler-ring metadata at that exact boundary;
6. captures exactly **5 consecutive complete 60-VI windows**;
7. repeats the whole process **3 times from fresh ares processes** while reusing one exact PROFILE binary, one exact Gothicvania ROM and one pinned ares build;
8. captures one statistical profile per repeat over the same five-window guest interval.

Pinned lab remains:
- Gothicvania source artifact `10466504920`, SNES ROM SHA-256 `5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`;
- ares `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`;
- R4300 JIT ON, RSP interpreter forced due documented ares RSP-JIT LAB LIMITATION;
- deterministic entropy;
- frameskip0 / APU21 / audio4 / precision8.

The script uses the already-proven ares software-breakpoint mechanism from the SPC700 proof harness. Between repeated `update_fps` boundaries it advances through `check_frame` so the same breakpoint cannot immediately re-hit.

### Exact runs
- **APU Matched Baseline `35351837163`** — IN PROGRESS at checkpoint.
- **Build and Validate `35351837019`** — PENDING/starting at checkpoint.

### Acceptance
This is a **MEASUREMENT PROOF**, not a speedup experiment. Accept the repair if:
- the exact branch compiles and ordinary Build/Validate remains green;
- all three fresh repeats reach the first-guest configuration boundary;
- every warmup/measured `update_fps` stop observes `fps_native=59`, confirming an exact 60-VI boundary;
- settings remain 21/0/4/8 through all measured windows;
- each repeat yields five complete windows and >=800 statistical samples;
- the artifact exposes the actual repeat/window distribution rather than reducing it to one host-time-selected total.

### Falsifiers / failure classes
- cannot reliably breakpoint `cpu_execute`, `update_fps` or `check_frame`;
- settings are not safely writable/retained before first guest execution;
- `fps_native` does not equal 59 at the claimed boundary;
- profiler sample count does not advance monotonically;
- build/Mupen regression despite no core changes indicates branch/harness integration error;
- repeated exact-window vectors remain materially phase-incomparable for a reason not controlled by the contract.

Do not require the three repeats to be numerically identical: variation itself is evidence. The goal is to make the **guest interval identical in definition**, so its observed variation becomes measurable instead of being conflated with different stop phases.

If accepted, this exact-window harness becomes the laboratory authority for a fresh baseline on clean `9204ad2f...`. Only then rank E3 low-read, E4 same-boundary validation or E5 DSP-invariant hypotheses. ares results remain laboratory evidence; real N64 remains final performance/timing authority.


## E1 matched-window baseline repair — VALIDATED 2026-09-18

Measurement-only authority: **`phase2/apu-matched-baseline@d20258be3f783728b500cfd95065abc185b14f2b`**, tree-equivalent in emulator core to clean timing foundation **`9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`**.

CI:
- **APU Matched Baseline `35351837163` SUCCESS**, matched job `105621983942`;
- **Build and Validate `35351837019` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green;
- matched diagnostics artifact **`10550167013`**, digest `sha256:0127fdbe1823fa40aa18fbbff0a4b99d82a32ee2bbd226d9ae1e2a1c5c2843d7`;
- exact matched PROFILE build **`10550355610`**, digest `sha256:99d8c6e0e4cd208f036db934a6b00d6b4c1c3404685ba09ad6fbfd2deafcb185`.

All three fresh ares processes produced the identical five-window vector:
**61, 60, 59, 61, 59 /60**, mean **60.00/60**, range **59..61**, with exactly **3582 samples** per repeat. Every warmup/measured boundary had `fps_native=59` and settings remained APU21 / frameskip0 / audio4 / precision8.

The statistical profile was also identical across all three repeats:
- S-CPU **23.5%**;
- APU generated **2.5%**;
- APU static **22.1%**;
- DSP/audio **23.2%**;
- PPU **10.9%**;
- DMA **6.1%**;
- VRAM/RSP wait **1.9%**;
- VI wait **9.7%**.

**MEASUREMENT PROOF:** the exact guest-window harness removes the prior same-binary phase ambiguity for this deterministic workload. Host wall time varied materially across repeats while guest frame vectors, sample counts and profiles remained identical, confirming host wall time is irrelevant to the guest-frame result.

**SUPPORTED INTERPRETATION:** on the corrected timing foundation, Gothicvania is no longer throughput-bound in the valid ares laboratory and has measurable VI idle headroom. This is a major change from pre-foundation ares observations, but it is NOT yet real-N64 performance evidence and does not prove Gate B.

**REJECTED inference:** do not rank E3/E4/E5 by ares FPS while this workload is already at the laboratory ceiling. Small speedups can be hidden inside VI wait.

### Immediate next action
Before promoting this corrected foundation to a real-N64 milestone, run one **separate PROFILE-only matched-window DSP-lateness diagnostic** on the exact core:
- reuse the previously validated due-count / late-sum / late-max / multi-due counters;
- measure the same exact five 60-VI windows;
- require **multi-due count = 0** (no lateness >= one 672-cycle DSP period);
- record due count, average and max as timing evidence;
- do not use the instrumented run for throughput comparison.

If DSP scheduling remains bounded, the next gate-relevant action is a milestone real-N64 measurement of exact clean `9204ad2f...` (or a byte-equivalent release artifact), because ares has ceased to be discriminative for this workload's performance.


## Matched DSP-lateness diagnostic — running 2026-09-18

Diagnostic child branch: **`phase2/apu-matched-dsp-lateness@a8c56301d3bc3d65b100b5cbb702f043ec6126de`**, based on measurement-only E1 authority `d20258be...`. Clean runtime candidate `9204ad2f...` is unchanged.

Direct compare from E1 measurement branch is exactly four diagnostic files:
- `src/apu.S` +37/-0, all scheduler observation under `SODIUM64_PROFILE`;
- `src/profile.S` +28/-0, PROFILE-only counters outside the canonical S64P snapshot;
- `scripts/gdb_matched_profile.py` +25/-0;
- `.github/workflows/apu-matched-baseline.yml` +29/-4.

Question: does the corrected timing foundation's exact-window 60/60-class ares result preserve DSP scheduling without ever becoming at least one full DSP sample period late?

Measurement contract:
- same exact first-guest configuration boundary and 2-warmup + 5-measured 60-VI windows as validated E1;
- counters reset at the exact measurement boundary;
- record DSP due count, lateness sum/average, max lateness and events with lateness >= `DSP_SAMPLE=672`;
- instrumented run is timing evidence only, **not** throughput evidence.

Acceptance:
- `dsp_due_count > 0`;
- `dsp_multi_due_count == 0`;
- `dsp_late_max < 672`;
- exact-window/settings contract still passes;
- ordinary Build and Validate remains green.

Falsifier: any >=672-cycle event, max >=672, settings/window-contract regression, or core/build regression.

Exact HEAD runs:
- **Build and Validate `35353207712`** — running;
- **APU Matched Baseline `35353207814`** — running; exact PROFILE build already SUCCESS, artifact `10550441933`, digest `sha256:6492d5e5c45661f0ba6772c637aade4c1a968bcad92fac3dfcb7f62a20a8d9f5`.

Decision map:
- if accepted, do not merge diagnostic instrumentation; promote exact clean `9204ad2f...` to a prepared real-N64 milestone because ares already has 9.7% VI idle and is no longer discriminative for Gothicvania performance;
- if lateness fails, treat 60/60 as cadence-invalid and repair scheduler/interleave before any hardware performance claim;
- if only harness/workflow fails, repair the diagnostic harness without changing clean core semantics.


## M1 hardware-package guard attempt 1 — HARNESS FALSE NEGATIVE 2026-09-18

Measurement-package branch was created from clean core `9204ad2f...` as **`phase2/apu-hardware-milestone`**. Its only intended repo change is the hardware-package workflow; emulator runtime files remain from the clean candidate.

First package SHA `d86de54b113ca18bdf56e61240ed9868ffdaed7a`, run **`35353828653`**, failed before compilation in the runtime-identity guard with:
`fatal: bad object 9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`.

Cause: `actions/checkout@v4` defaulted to `fetch-depth: 1`, so the clean parent commit object was absent locally. This is **HARNESS FALSE NEGATIVE / REJECTED as core evidence**.

No build, ROM, hardware result or Sodium64 behavior was tested by the failed attempt.

Workflow-only fix: package branch advanced to **`e0dfe19b59cd4b86ee96eb250c9ad4bfda437a3b`**, adding only `fetch-depth: 0` so the guard can compare against exact clean core `9204ad2f...`. Runtime core remains unchanged.


## Matched DSP-lateness diagnostic — FAILED CADENCE GATE / VALID EVIDENCE 2026-09-18

Exact diagnostic authority: **`phase2/apu-matched-dsp-lateness@a8c56301d3bc3d65b100b5cbb702f043ec6126de`**.

CI:
- **Build and Validate `35353207712` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Matched Baseline `35353207814`** completed all three exact-window repeats successfully, then intentionally FAILED the final acceptance assertion because DSP lateness exceeded the allowed period.
- diagnostic artifact **`10550684126`**, digest `sha256:50dcdc3c80aa8f834df8c13eb6aa5c0f0dc3ef374afe60e92f165af785fe54a6`;
- exact PROFILE build artifact **`10550441933`**, digest `sha256:6492d5e5c45661f0ba6772c637aade4c1a968bcad92fac3dfcb7f62a20a8d9f5`.

All three fresh ares processes were bit-for-bit deterministic at the reported measurement level:
- measured frame vector: **60,60,60,60,60 /60** in every repeat;
- final samples: **3581** in every repeat;
- DSP due count: **159849**;
- DSP late sum: **20846385** master cycles;
- average lateness: **130.4129835 master cycles = 6.210 SPC cycles**;
- maximum lateness: **1029 master cycles = 49 SPC cycles**;
- events with lateness >= one DSP period (`672 = 32 SPC cycles`): **1420**, about **0.8883%** of due events.

**VALIDATED correctness finding:** the corrected timing foundation can report 60/60 completed frames while violating the required DSP scheduler cadence. Therefore the current ares 60/60 result is **NOT cadence-valid Gate-B evidence**.

**REJECTED inference:** do not treat ares VI headroom or 60/60 as proof that the clean candidate is ready for real-N64 performance graduation. Throughput and event cadence are now explicitly separated.

The lateness counters are diagnostic-only and read `a3-s3` before their own logging work, so the observed lateness is not created by the counter instructions themselves. The repeated exact values across three fresh processes strengthen the scheduler/interleave interpretation.

### Hardware package status
A measurement-only branch **`phase2/apu-hardware-milestone@e0dfe19b59cd4b86ee96eb250c9ad4bfda437a3b`** successfully built the real-N64 M1 package after fixing a shallow-checkout guard false negative:
- package run **`35353932617` SUCCESS**;
- artifact **`10550379275`**, digest `sha256:8fff13c90307f90d21cab84afb2c6ecb4766ff3f3f3d3b0617efd4b1d6c28c8a`;
- runtime identity guard proved `src`/build inputs are exact clean core `9204ad2f...`, with workflow-only packaging changes.

State: **BLOCKED / DO NOT HARDWARE-TEST YET**. Preserve the artifact but do not ask Iron to run it while DSP cadence is invalid.

### Immediate next controlled experiment
Test whether JIT block interleave, rather than an individual instruction or DSP scheduler bug, causes the >672 tail:
- create a diagnostic child of `a8c56301...`;
- change only `BLOCK_SIZE 16 -> 1`, which forces one SPC700 instruction per generated block after the already-validated NOP-bound repair;
- keep identical matched-window lateness instrumentation and workload;
- accept as causal proof if `dsp_multi_due_count` falls to 0 and max <672;
- if lateness remains >=672, block aggregation is insufficient as the explanation and the next investigation must inspect individual-instruction / scheduler-event semantics.

This one-op mode is a **causal control only**, not a proposed permanent architecture. Its throughput cost is secondary to isolating the mechanism.


## One-op APU JIT interleave causal proof — running 2026-09-18

Diagnostic child branch: **`phase2/apu-one-op-interleave-proof@c1548c21e4764a1827ebe1af8980ec319f560bbb`**, based on matched-lateness authority `a8c56301...`.

Direct diff from `a8c56301...` is exactly:
- `src/defines.h`: **one runtime line**, `BLOCK_SIZE 16 -> 1`;
- `.github/workflows/apu-matched-baseline.yml`: one trigger-line addition for this diagnostic branch.

Production-semantic test variable: one SPC700 instruction per generated block. No timing charges, opcode semantics, scheduler checks, DSP logic, profiler counters or workload settings changed.

Purpose: causal isolation only. This is **not** a proposed permanent performance architecture.

Hypothesis: the validated >672 DSP lateness tail is produced by aggregating several now-correctly-timed SPC700 instructions inside one JIT block before returning to the scheduler.

Acceptance as causal proof:
- exact matched-window contract completes;
- `dsp_multi_due_count == 0`;
- `dsp_late_max < 672`.

Interpretation:
- if accepted, block aggregation/interleave is the demonstrated mechanism; next design must retain multi-op performance while adding a bounded guest-cycle return contract;
- if >=672 remains, multi-op aggregation alone is insufficient and investigation moves to individual-instruction / scheduler-event semantics.

Exact HEAD runs:
- **APU Matched Baseline `35354324333`** — queued/running;
- **Build and Validate `35354324334`** — queued/running.

Do not merge BLOCK_SIZE=1. Do not use throughput from this diagnostic as a performance target; frame counts only show the cost of the causal control.


## One-op APU JIT interleave proof — VALIDATED CAUSAL RESULT 2026-09-18

Exact diagnostic authority: **`phase2/apu-one-op-interleave-proof@c1548c21e4764a1827ebe1af8980ec319f560bbb`**.
Runtime test variable from matched-lateness authority `a8c56301...`: exactly **`BLOCK_SIZE 16 -> 1`**. Workflow has one trigger-line addition only.

CI:
- **Build and Validate `35354324334` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Matched Baseline `35354324333` SUCCESS**.
- diagnostic artifact **`10551701393`**, digest `sha256:109da718606b3d01332dfd65aff321f6b5a0ed26ef88fd3f4bdae4edc16e38b8`;
- exact PROFILE build artifact **`10550643405`**, digest `sha256:4bd6cdbbe58086d675f31c1adeff199d83d41f77ffb5f6286e94213b31beb1b9`.

All three fresh ares repeats were identical:
- measured windows: **48,49,49,51,50 /60**;
- mean **49.4/60**, range **48..51**;
- samples **3580**;
- DSP due count **131397**;
- late sum **5891319** master cycles;
- average lateness **44.836 master cycles = 2.135 SPC cycles**;
- max lateness **168 master cycles = 8 SPC cycles**;
- **`dsp_multi_due_count = 0`**.

Compared with the multi-op corrected-timing baseline:
- BLOCK16: max **1029 = 49 SPC cycles**, **1420 >=672** events, cadence FAIL despite 60/60 throughput;
- one-op: max **168 = 8 SPC cycles**, **0 >=672** events, cadence PASS but throughput falls to **49.4/60**.

**ARCHITECTURE PROOF:** multi-instruction JIT block aggregation before scheduler return is the demonstrated cause of the invalid DSP-lateness tail. The scheduler can maintain bounded DSP cadence when return frequency is sufficiently high.

**REJECTED architecture:** `BLOCK_SIZE=1` is not a production solution; its throughput cost essentially gives back the corrected-timing ares gain.

Pinned ares source audit at `17813a3c...` shows the highest-cost finite single SPC700 instruction is DIV at **12 total cycles** (opcode fetch + 11 explicit read/idle cycles). WAIT/STOP are persistent states and Sodium64 already returns to the scheduler after their 3-cycle entry / 2-cycle ticks.

### Next design — guest-cycle-bounded multi-op JIT blocks
Target invariant: retain multi-op blocks but guarantee a generated block cannot consume a full DSP period before scheduler return.

DSP period = `DSP_SAMPLE=672` master cycles = **32 SPC cycles** at `apu_clock=21`.

A conservative compile-time block budget can be derived from the existing cycle mechanisms:
1. each source byte fetched by `jit_read8` = 1 guest cycle;
2. `jit_charge_cycles` = fixed extra guest cycles;
3. `jit_emit_runtime_cycles` = conditional runtime cycles, counted at their worst-case value for budgeting;
4. every generated call to `apu_read8` / `apu_write8` = 1 guest bus cycle.

No other audited APU generator file emits direct guest-`apu_ram` accesses; guest data cycles flow through those helpers. The direct LBU/SB/SH/LHU emissions in `apu_emitter.S` are emulator-state register spill/load machinery, not guest bus cycles.

Since one finite instruction is <=12 cycles, a multi-op compiler can continue only while the completed block budget is <=20 cycles. Adding one more worst-case instruction then yields a hard maximum of **32 guest cycles**, while the existing 16-byte source-span cap remains as an independent safety bound.

Next controlled implementation must add compile-time-only cycle accounting and this continuation rule, with no change to per-instruction guest debits or opcode semantics. It must be validated by cycle/address regression plus the same exact-window DSP-lateness run before any hardware test.


## Guest-cycle-bounded multi-op JIT candidate — running 2026-09-18

Diagnostic branch: **`phase2/apu-cycle-budget-interleave@a4b8f2d74f368568ef519ea76bb589d7fe98d265`**, based on matched-lateness authority `a8c56301...`.

Direct diff:
- `src/apu_emitter.S` +44/-8 — compiler-only cycle accounting plus block continuation bound;
- `.github/workflows/apu-matched-baseline.yml` +1 trigger line.

No opcode semantic implementation, per-instruction guest debit, DSP scheduler ordering, APU memory helper semantics or workload setting changed.

Design:
- preserve inherited independent `BLOCK_SIZE=16` source-span/tag safety bound;
- maintain compile-only `jit_block_cycles` worst-case guest-cycle count;
- +1 per source-byte fetch in `jit_read8`;
- +N for fixed cycles in `jit_charge_cycles`;
- +N for conditional runtime cycles in `jit_emit_runtime_cycles`, conservatively counting the taken/worst-case path;
- +1 for every generated `apu_read8`/`apu_write8` guest bus access inside `emit_jal`;
- after each completed opcode, continue compiling only if source span remains under 16 bytes **and** completed worst-case budget <=20 cycles.

Pinned reference bound: maximum finite single opcode = DIV at 12 cycles. Therefore any continued block can reach at most **20+12 = 32 SPC cycles**, one DSP period. Because `apu_execute` services DSP when `s3 <= a3` and enters a block only with positive headroom, a <=32-cycle block must return with lateness <672 master cycles.

Source audit found no generated direct guest-`apu_ram` data accesses outside `apu_read8`/`apu_write8`; direct load/store emission in `apu_emitter.S` is emulator-state spill/load machinery. WAIT/STOP remain separate persistent scheduler state and do not violate the finite-op bound.

Exact HEAD runs:
- **APU Matched Baseline `35355419586`** — running;
- **Build and Validate `35355419608`** — queued/running.

Acceptance:
1. normal/PROFILE build + Mupen smoke green;
2. exact-window `dsp_multi_due_count=0` and `dsp_late_max<672`;
3. materially better throughput than one-op 49.4/60;
4. then consume the same emitter change into cycle/address proof and require the full timing/semantic regression matrix green before clean consumption.

Falsifiers:
- any >=672 event;
- build/runtime regression;
- cycle proof regression;
- throughput near one-op indicating the temporal cap destroys the multi-op benefit.


## Cycle-budget implementation v1 — SUPERSEDED before acceptance 2026-09-18

Source-contract audit found a real compiler-helper clobber regression in first cycle-budget implementation `a4b8f2d7...`: its new bookkeeping used **`t2`** inside `jit_read8` / cycle helpers even though those helpers historically clobbered only their existing temporaries.

Concrete proof: `apu_bbc1` and `apu_bbs1` compute the tested-bit mask into `t2`, call `jit_read8`, then use `t2` to encode the generated ANDI. Therefore v1 can silently corrupt BBS/BBC compiled semantics. This is source-proven, not hypothetical.

State:
- `phase2/apu-cycle-budget-interleave@a4b8f2d7...` = **SUPERSEDED implementation** regardless of its eventual matched-run numbers;
- `phase2/apu-cycle-budget-proof@1f7aa124...` = **SUPERSEDED proof implementation** for the same reason;
- any v1 CI result may be retained only as diagnostic evidence about that exact flawed SHA, not as candidate correctness/performance authority.

No clean branch was touched.

## Guest-cycle-bounded multi-op JIT v2 — running 2026-09-18

Corrected diagnostic candidate:
**`phase2/apu-cycle-budget-interleave-v2@5b9f16c0127b9ec99e7bdc5d811a183e87065b86`**.
Core commit before trigger-only workflow line: `709def0969c97e66c195b490deb480324e6e9a3f`.

Corrected cycle-proof child:
**`phase2/apu-cycle-budget-proof-v2@91f8f13a9a4cdd8ccc98da7452935e387664a8c0`**, based on immutable proof authority `e7cc3cf...`.

The temporal-budget design is unchanged from v1. The only implementation correction is register discipline:
- `jit_read8` bookkeeping reuses only historical clobbers `v0/t0/t1`; **t2 is preserved**;
- `jit_charge_cycles` reuses only existing `t0/t1`;
- `jit_emit_runtime_cycles` reuses only existing `t0/t1/t5`;
- `emit_jal` remains within existing `t0/t1` clobbers.

Direct v2 candidate diff from matched-lateness base `a8c56301...`: only `src/apu_emitter.S` +42/-9 plus one workflow trigger line.
Direct v2 proof diff from `e7cc3cf...`: only `src/apu_emitter.S` +42/-9 plus one proof-workflow trigger line.

Acceptance remains unchanged:
1. exact Build/Validate + Mupen green;
2. matched Gothicvania: `multi_due=0`, max <672 and throughput materially above one-op 49.4/60;
3. full APU Cycle And Span Proof regression matrix green;
4. only then consume the emitter change into clean timing foundation.


## Cycle-budget implementation v1 — MATCHED RESULT VALID, IMPLEMENTATION SUPERSEDED 2026-09-18

Exact v1 diagnostic authority: **`phase2/apu-cycle-budget-interleave@a4b8f2d74f368568ef519ea76bb589d7fe98d265`**, based on matched-lateness diagnostic authority `a8c56301...`. **Do not consume this SHA:** its matched result is valid evidence for the cycle-budget architecture, but the implementation is superseded by the source-proven `t2` clobber regression documented above.

Direct production-semantic change from `a8c56301...` remains confined to `src/apu_emitter.S`:
- compile-only `jit_block_cycles` accounting;
- +1 per `jit_read8` source/operand fetch;
- fixed extra guest cycles through existing `jit_charge_cycles`;
- conditional cycles conservatively budgeted at the existing `jit_emit_runtime_cycles` value;
- +1 for generated `apu_read8` / `apu_write8` guest bus calls;
- multi-op continuation only while completed worst-case block budget <=20 cycles, preserving the independent 16-byte source-span cap.

CI:
- **Build and Validate `35355419608` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Matched Baseline `35355419586` SUCCESS**.
- matched diagnostic artifact **`10551783478`**, digest `sha256:95c8a3a88ed7815e614440e1d366b2024e4043dfc7b18fdf60377611ad94950e`;
- exact PROFILE build artifact **`10551457203`**, digest `sha256:c16261aafd8ea11709d4e1cbcaceb9af5a46689330d5a8fc0458ae2603dc2ce6`.

All three fresh ares repeats were identical:
- measured frame vector **60,60,60,60,60 /60**;
- mean **60.00/60**, range **60..60**;
- samples **3584**;
- DSP due count **159539**;
- late sum **3350319 master cycles**;
- average lateness **21.0 master cycles = 1 SPC cycle**;
- maximum measured-window lateness **21 master cycles = 1 SPC cycle**;
- **`dsp_multi_due_count = 0`**.

Warmup still observed a bounded max of 483 master cycles (<672), with zero multi-due events. After the exact measurement-boundary reset, all five windows remained at one SPC cycle maximum lateness.

Comparison:
- original corrected multi-op BLOCK16: **60/60**, max **1029**, **1420 >=672** — cadence FAIL;
- one-op causal control: **49.4/60**, max **168**, **0 >=672** — cadence PASS, throughput FAIL;
- cycle-bounded multi-op: **60/60**, max **21**, **0 >=672** — cadence PASS + throughput target in valid ares lab.

**ARCHITECTURE PROOF (mechanism only):** the v1 matched result demonstrates that guest-cycle-bounded multi-op compilation can resolve the measured conflict between SPC700 JIT throughput and DSP scheduler cadence for Gothicvania in the valid ares lab. It does **not** validate the v1 implementation because that SHA violates a compiler-helper clobber contract. v2 must reproduce the result and pass cycle/semantic proof before clean consumption.

**What this does NOT prove:** commercial compatibility, real-N64 60 FPS, audio waveform correctness, or Gate B completion. ares remains a laboratory; exact opcode cycle/address regression and then real hardware authority are still required.

### Immediate next action (superseded by v2 work now running)
Validate the clobber-safe v2 emitter through both the matched cadence/throughput run and the existing cycle/address proof line. Do not consume the v1 emitter into any clean branch.

Acceptance:
- all existing 256-opcode cycle/address proof cases remain green;
- WAIT/STOP/NOP and branch taken/not-taken expectations remain green;
- normal/PROFILE build + emulator smoke remain green.

Only after that proof passes should the emitter change be consumed into the clean timing foundation and a fresh real-N64 M1 package be built from the resulting exact clean SHA.


## Cycle-budget v2 proof expectation repair — checkpoint 2026-09-18

Proof v2 advanced to **`phase2/apu-cycle-budget-proof-v2@151466bb39ab7a7739ec76e415e4deafb0a600e4`**.

Reason: the historical `long_nop_dbnzy` regression probe encoded the OLD architecture's desired cutoff: 16 NOP bytes / 32 guest cycles. Under the new temporal block contract the intentional cutoff is earlier:
- each NOP = 2 SPC cycles;
- after 10 NOPs budget =20 and one more finite instruction is permitted;
- after 11 NOPs budget =22, so the block terminates;
- expected PC advance =11 bytes;
- static/total debit =22 SPC cycles =462 master cycles.

Only proof expectations for this architecture-specific long-NOP cutoff changed:
- expected PC +16 -> +11;
- expected debit -672 -> -462;
- reference cycles 32 ->22;
- summary long-probe clock-units 32 ->22.

All instruction semantic/timing expectations, addressing cases, branch/runtime debits, halt scheduler checks, tag-region bound and historical family regressions remain unchanged.

Exact current proof runs:
- **APU Cycle And Span Proof `35356429346`** — queued;
- **Build and Validate `35356429215`** — queued.
Earlier proof-v2 run at `91f8f13a...` is superseded by this expectation-only correction.


## Guest-cycle-bounded multi-op JIT v2 — VALIDATED FOR CLEAN CONSUMPTION 2026-09-18

Corrected candidate authority: **`phase2/apu-cycle-budget-interleave-v2@5b9f16c0127b9ec99e7bdc5d811a183e87065b86`**.
Production emitter commit before trigger-only workflow change: **`709def0969c97e66c195b490deb480324e6e9a3f`**.

### L1/L2 build authority
**Build and Validate `35356204540` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen64Plus normal/profile smoke SUCCESS.

### Matched cadence + throughput authority
**APU Matched Baseline `35356204750` SUCCESS**, matched job `105636472480`.

All three fresh ares repeats produced the same five-window vector:
**61,59,60,61,60 /60**, mean **60.20/60**, range **59..61**, samples **3582**.

DSP scheduler evidence in each repeat:
- due count **159882**;
- late sum **16855692 master cycles**;
- average lateness **105.4258265 master cycles ~= 5.02 SPC cycles**;
- maximum lateness **546 master cycles = 26 SPC cycles**;
- **multi-due count = 0** (no event reached the 672-master / 32-SPC DSP period).

Warmup maximum was also bounded at 546 with zero multi-due events.

Artifacts:
- matched diagnostics **`10552485210`**, digest `sha256:f717d6488f0ef3ed04fd7a7c26d68ad7e29380d1533d8d467336dc4e0467c91b`;
- exact PROFILE build **`10551443618`**, digest `sha256:82122533a864a648aadbef12c660a565b63346c16bea1bbcc635dcd36071329e`.

**VALIDATED:** clobber-safe v2 retains the measured throughput benefit while keeping DSP scheduler lateness below one full sample period. This reproduces the architecture result without the v1 helper-clobber defect.

### Cycle/address/semantic proof authority
Proof branch: **`phase2/apu-cycle-budget-proof-v2@151466bb39ab7a7739ec76e415e4deafb0a600e4`**.

**APU Cycle And Span Proof `35356429346` SUCCESS**, dynamic proof job `105637636509`.
Companion **Build and Validate `35356429215` SUCCESS**.

Proof summary:
- `all_static_debits_match_source_prediction = true`;
- `all_header_spans_match_source_prediction = true`;
- `all_runtime_cycle_debits_match_expected = true`;
- `all_total_debits_match_reference = true`;
- `all_semantics_match_expected = true`;
- `all_halt_scheduler_ticks_match_expected = true`;
- `compiled_long_probe_is_bounded_to_one_tag_region = true`.

The architecture-specific long-NOP probe correctly compiled **11 NOP bytes / 22 SPC cycles / 462 master cycles**, not the old 16-NOP/32-cycle cutoff. BBS/BBC taken/not-taken, addressing families, branches, stack/call/return, word/bit operations, half-carry, DIV, decimal adjust, SLEEP and STOP remained in the unchanged semantic/timing matrix and passed.

Proof artifacts:
- diagnostics **`10552885741`**, digest `sha256:ca40f0c2e100b3b26b8c14b8c7f778e273bc77728f1511c4801203bc614114a2`;
- exact proof build **`10552426125`**, digest `sha256:4d9e5e4026fb5486036e7fe832273f916bcd10e004ada080155f546d4d325a1b`.

**ARCHITECTURE PROOF + COMPATIBILITY/TIMING REGRESSION:** v2 is now acceptable for clean consumption. This validates the audited SPC700 timing/address/semantic corpus and the Gothicvania matched cadence contract; it does not establish complete SPC700 correctness or real-N64 performance.

### Immediate next action
Create a clean child of **`phase2/apu-timing-foundation@9204ad2f...`** that consumes **only the exact v2 `src/apu_emitter.S` production change** from `709def09...`.
Do not consume PROFILE lateness counters, matched workflows, proof harness changes, or diagnostic files.

Then:
1. require clean Build and Validate + Mupen SUCCESS;
2. verify direct diff from `9204ad2f...` is only `src/apu_emitter.S`;
3. build a fresh real-N64 M1 Gothicvania package from that exact clean SHA;
4. only that fresh package may be presented for the next hardware milestone.


## Clean cycle-budget consumption — running 2026-09-18

Clean candidate: **`phase2/apu-cycle-budget-clean@d5ce93a03b2dbf5065fefa5276533e02f9658215`**.

Authority:
- parent is exact clean timing foundation **`9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`**;
- branch is ahead by exactly one commit;
- direct diff is exactly one production file: **`src/apu_emitter.S` +42/-9**;
- resulting emitter blob **`fc510743836c2a0a8afca771ca016cf2d02bf83a`** exactly matches the clobber-safe v2 emitter validated in matched and cycle-proof branches.

No PROFILE lateness counters, diagnostic workflows, proof scripts, or measurement-only source changes were consumed.

Exact clean CI:
- **Build and Validate `35357705471`** — queued/running.

Acceptance before hardware packaging:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen normal/profile smoke SUCCESS.

After clean CI passes, build a fresh M1 real-N64 package from this exact clean SHA. The previous hardware artifact from `9204ad2f...` remains BLOCKED/SUPERSEDED for this milestone because it predates the cycle-budget interleave fix.


## Clean cycle-budget candidate — VALIDATED 2026-09-18

Clean candidate authority: **`phase2/apu-cycle-budget-clean@d5ce93a03b2dbf5065fefa5276533e02f9658215`**.

Identity:
- exact parent: `phase2/apu-timing-foundation@9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`;
- exactly one commit ahead;
- only changed production file: **`src/apu_emitter.S` +42/-9**;
- emitter blob **`fc510743836c2a0a8afca771ca016cf2d02bf83a`**, byte-identical to clobber-safe v2 production emitter `709def09...`.

No matched-lateness instrumentation, proof harness, diagnostic source, or diagnostic workflow was consumed.

**Build and Validate `35357705471` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen64Plus normal runtime smoke SUCCESS;
- pinned Mupen64Plus PROFILE runtime/sample-decode smoke SUCCESS.

State: **VALIDATED clean M1 candidate / READY FOR REAL-N64 MILESTONE PACKAGE**.

This does not yet establish a real-N64 speedup. The next authority step is one fresh hardware package built from exact `d5ce93a0...`, using the already validated M0 SRAM capture method and the exact pinned Gothicvania workload.


## Real-N64 M1 cycle-budget package — READY FOR HARDWARE 2026-09-18

Measurement-package branch: **`phase2/apu-cycle-budget-hardware-m1@3d4555e5f4174770f1c98a8209fc6809ca57a447`**.
Runtime core authority: **`phase2/apu-cycle-budget-clean@d5ce93a03b2dbf5065fefa5276533e02f9658215`**.

Direct package-branch diff from runtime core is exactly one file:
`.github/workflows/apu-m1-hardware-package.yml`. No runtime source differs.

**APU M1 Real N64 Package `35358185620` SUCCESS**, package job `105642608821`.
Artifact:
- ID **`10552617325`**;
- name `sodium64-real-n64-m1-gothicvania`;
- artifact digest **`sha256:5e4ef08c647b2b9a3af905855258ca63809fa2767c3554bce1848b087c171100`**;
- expires 2026-10-02.

Package identity:
- `runtime_core_sha=d5ce93a03b2dbf5065fefa5276533e02f9658215`;
- mode `PROFILE=1 + HW_PROFILE=1`;
- warmup 2 complete 60-VI windows;
- measurement 5 complete 60-VI windows;
- frameskip 0;
- APU clock 21;
- audio 4;
- precision 8;
- pinned Gothicvania payload SHA256 `5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`;
- wrapped N64 ROM SHA256 **`d9c151c3246ecd553af247d565c52bad94ae33fe513b4f1a9f075f48fce1614b`**;
- underlying HW_PROFILE Sodium64 ROM SHA256 `8546b5fb7928b0d69d46dc9387bdaf926b2688fffc08579919a8f89f76d3df41`.

The workflow verified the embedded 512 KiB Gothicvania payload hash after wrapping and verified every package file against `SHA256SUMS.txt`.

### RESUME HERE — hardware authority required
Run **only** `sodium64-m1-gothicvania.z64` from artifact `10552617325` on the real N64/SummerCart64.

Procedure:
1. launch the ROM directly;
2. do not press the controller or open settings;
3. let automated Gothicvania gameplay run through 2 warmup + 5 measured 60-VI windows;
4. wait for the **solid red screen**, which is emitted only after SRAM capture DMA completes;
5. wait ~2 seconds, then use normal reset/return-to-cart flow so SRAM persists; do not power off first;
6. retrieve the SRAM/save for this ROM;
7. record whether gameplay, music and SFX looked/sounded sane before red.

Return the save file. Decode it with the package's `hw_profile_report.py` and exact ELF/map.

Hardware decision:
- compare the five real-N64 frame-budget windows against M0 **48,49,48,50,50 (mean 49.0/60)**;
- verify frameskip/APU/audio/precision metadata and sample density;
- compare R4300 profile distribution, especially APU/JIT/DSP and VI wait;
- use real hardware, not ares wall time, to decide whether the cycle-budget architecture materially advances M1.

Do not merge to master or update Road-to-1.0 convergence claims until this hardware result is interpreted.


## Real-N64 M1 cycle-budget milestone — MEASURED 60/60 x5 2026-09-18

Hardware authority capture received from exact package:
- runtime core **`phase2/apu-cycle-budget-clean@d5ce93a03b2dbf5065fefa5276533e02f9658215`**;
- package branch **`phase2/apu-cycle-budget-hardware-m1@3d4555e5f4174770f1c98a8209fc6809ca57a447`**;
- package artifact **`10552617325`**, artifact digest `sha256:5e4ef08c647b2b9a3af905855258ca63809fa2767c3554bce1848b087c171100`;
- wrapped ROM SHA256 **`d9c151c3246ecd553af247d565c52bad94ae33fe513b4f1a9f075f48fce1614b`**;
- returned SRAM/save decoded successfully by the exact package `hw_profile_report.py`.

Strict hardware capture validation:
- capture format: canonical big-endian;
- complete=1;
- warmup: 2 complete 60-VI windows;
- measurement: 5 complete 60-VI windows;
- sample count: **3580** at interval **65521**;
- frameskip: **0**;
- APU clock: **21** (full-rate project target);
- audio setting: **4** (active);
- precision: **8**;
- frame queue at capture: 1.

**REAL-N64 FRAME BUDGET:**
**60/60, 60/60, 60/60, 60/60, 60/60**.
Mean: **60.0/60**.
M0 authority baseline was **48,49,48,50,50**, mean **49.0/60**.

This is an absolute improvement of **+11.0 completed guest frames per 60-VI window on average**, about **+22.45%** relative completed-frame throughput versus M0, and eliminates the measured frame-budget deficit in this representative hardware workload.

Exact real-N64 R4300 sample profile (3580 valid samples):
- DSP/audio: **21.98%** (787);
- APU/SPC700 static: **20.36%** (729);
- APU JIT generated: **8.69%** (311);
- combined APU/JIT/DSP-audio: **51.03%**;
- S-CPU interpreter: **19.75%** (707);
- frame/VI wait: **11.51%** (412);
- PPU/events/frame prep: **8.63%** (309);
- DMA/HDMA: **7.01%** (251);
- RSP/VRAM semaphore wait: **2.01%** (72);
- input: **0.06%** (2).

Comparison to M0 real hardware:
- combined APU/audio: **61.83% -> 51.03%** (down 10.80 percentage points, ~17.5% relative share reduction);
- S-CPU: **22.12% -> 19.75%**;
- VI idle/headroom: **essentially 0% -> 11.51%**;
- frame budget: **49.0/60 -> 60.0/60**.

**MEASURED / ARCHITECTURE PROOF ON REAL HARDWARE:** the clobber-safe guest-cycle-bounded SPC700 multi-op JIT materially improves the representative real-N64 M1 workload while preserving frameskip=0, full-rate APU, active audio, precision=8, and the previously validated emulator-lab DSP scheduler invariant (max < one DSP period, multi-due=0).

User-provided video from the same run visually shows active Gothicvania gameplay and the final solid-red completion screen. Video is observational evidence only; SRAM is the performance/settings authority.

**What this proves:** this representative base workload now sustains the native 60/60 frame-budget target on real N64 under Road-valid settings, with measurable VI headroom and materially reduced APU/audio share.

**What this does NOT yet prove:** Gate B across the defined base-system corpus, complete audio waveform fidelity, broad commercial compatibility, or 1.0. One representative workload reaching 60/60 is a major M1 milestone, not a full base-system release claim.

### RESUME HERE
Interpret this as a major M1 convergence event. Before choosing the next optimization:
1. update Road/Roadmap only to the extent milestone/gate convergence has materially changed;
2. decide whether M1 exit condition is now satisfied or whether one additional representative hardware workload is required for milestone closure;
3. do **not** immediately optimize further against Gothicvania FPS because this workload now has **11.51% VI wait** on real hardware and is no longer throughput-bound;
4. re-profile/choose the next gate driver using a broader representative base workload/corpus rather than chasing more speed in this already-native workload;
5. keep the cycle-budget emitter architecture; v1 remains SUPERSEDED, v2 clean candidate is the valid implementation.


## Independent red-team audit after real-N64 60/60 — 2026-09-18

Independent Astra/Codex read-only audit reproduced the M0 and M1 SRAM decodes and profiles from the original artifacts and verified the recorded branch/commit identities, package provenance and checksums. The auditor did **not** modify the repository.

Additional authority:
- returned M1 SRAM SHA256: **`674e426257dff80ad1bcf3bbdd9837d3f68fe8f9d7a48f2fd21d2296d80f1582`**;
- audit independently reproduced M0 **48,49,48,50,50 /60** and M1 **60,60,60,60,60 /60**;
- both captures validate frameskip 0, APU clock 21, audio 4, precision 8 and complete capture state.

### Interpretation corrections

**SUPPORTED INTERPRETATION:** the measured real-N64 result establishes that the **combined timing-foundation + cycle-budget-v2 candidate** removes the Gothicvania frame-budget deficit for the measured hardware segment. Do not attribute the entire M0 49/60 -> M1 60/60 jump to the cycle-budget change alone.

Reason: the corrected timing foundation already reached the ares throughput ceiling while still violating DSP lateness. The strongest causal claim for cycle-budget v2 is that it preserved multi-op throughput while restoring the required scheduler return bound.

**REJECTED wording:** “cycle-budget alone produced +22.45% speedup.” The +22.45% figure is the relative increase in completed guest frames per 60-VI measurement window between two different full runtime states, not isolated causal attribution to one emitter patch.

**REJECTED wording:** “APU/audio costs 17.5% less.” The real-hardware profile shows APU/JIT/DSP **share** moving from 61.83% to 51.03%; statistical sample share is not an absolute cost measurement normalized to identical guest work.

**MEASURED:** M1 has 11.51% R4300 frame/VI wait in this capture. **SUPPORTED INTERPRETATION:** Gothicvania is no longer useful as an FPS-ranking workload for further optimization. **UNKNOWN:** that wait fraction is not a universal spare-N64 budget and does not directly measure unused RSP capacity.

### Cycle-budget contract audit

The source audit supports the current compile-time budget model:
- source/operand fetch through `jit_read8`: +1 guest cycle;
- fixed cycles through `jit_charge_cycles`: +N;
- conditional runtime cycles: budget worst-case/taken value;
- generated calls to guest `apu_read8` / `apu_write8`: +1 guest bus cycle;
- `jit_block_cycles` is compile-time accounting only and is not itself charged again at runtime.

Finite-op bound remains:
- completed-block continuation threshold = 20 SPC cycles;
- largest pinned finite single opcode = DIV at 12 SPC cycles;
- therefore a continued block can reach at most **32 SPC cycles = 672 master cycles** before scheduler return.

Important mathematical clarification: the **block duration may equal one DSP period**; the scheduler lateness remains strictly below one period if DSP is serviced whenever `s3 <= a3` before block entry and entry begins with positive headroom.

This contract is explicitly tied to the Road-valid **APU clock 21** configuration and must not be generalized blindly to other clock settings.

### Remaining bounded proof gap

Current dynamic APU proof contains **114 directed cases plus halted-state observations**. It validates audited families and regressions; it is **not** an exhaustive 256-opcode/state/composition proof.

The current largest deliberate block debit exercised by the proof is 22 SPC cycles (the long-NOP temporal-cutoff case). The exact **20 + DIV = 32-cycle boundary** has not yet been exercised dynamically.

**TODO / immediate proof batch:**
1. a 20-cycle NOP prefix followed by DIV;
2. a 20-cycle prefix built using real guest accesses followed by DIV;
3. taken/not-taken branch cases near the temporal cutoff;
4. a few tag/cache/reuse boundary cases, comparing first compile against cached execution.

Acceptance:
- compile-time budget is conservative relative to executed guest work;
- no produced block exceeds 32 SPC cycles;
- expected debit/state remain exact;
- cached execution matches initial compilation;
- no stale/self-modifying reuse is observed in the directed boundary cases.

This is a small extension of the existing proof harness, **not** a new profiling/tooling project.

### Accuracy risks preserved for later Gate C work

These are not demonstrated Gothicvania failures and were not introduced by v2, but remain architectural correctness boundaries:

- Some dummy reads are represented as cycle charge only rather than emitted observable bus reads; total cycles can therefore be correct while I/O side effects differ, especially around timer/DSP/port registers.
- Tag validation on block entry protects later reuse but does not by itself prove that a write performed during an executing block cannot invalidate not-yet-executed instructions within that same block.
- Future emitter helpers that bypass `apu_read8`/`apu_write8` or reintroduce direct guest-memory accesses could escape the cycle-budget accounting even if runtime debits remain correct. Any future APU-memory fast path must preserve or extend the budget contract deliberately.

### Milestone interpretation

**SUPPORTED INTERPRETATION:** M1's material performance objective is satisfied by the validated candidate: a measured APU/audio bottleneck was reduced enough for the representative hardware workload to reach native frame budget under Road-valid settings.

**ENGINEERING CLOSURE still required before declaring M1 closed/integrated:** complete the bounded edge proof above and integrate the clean candidate into `master` through normal validation.

A second hardware workload is **not** required retroactively to close M1. Broader workload coverage belongs to M2 / Gate B.

**Gate B remains OPEN.** The current SRAM does not prove sustained presentation cadence over a base corpus, AI underrun behavior, long-run A/V drift, PCM equivalence, or broad base-system compatibility.

### Direction after M1 closure

Do not resume Gothicvania FPS optimization or automatically return to `apu_read8`/`apu_write8` optimization.

After the bounded edge proof and integration:
- define a small base-system corpus with distinct CPU / PPU-HD-MA-Mode7 / audio characteristics;
- use emulator labs to filter correctness/progression;
- take the corpus to real N64 in one milestone batch;
- choose the next optimization or accuracy recovery from the **first demonstrated gate blocker**, not from subsystem sample share alone.

No evidence currently justifies cartridge assistance, a clean-sheet second emulator, or an immediate 65C816 dynarec.


## Cycle-budget boundary proof — running 2026-09-18

Diagnostic proof child:
**`phase2/apu-cycle-budget-edge-proof@4f197702ff81687d68a33842105c907b888a2be6`**, based on validated proof authority `151466bb...`.

Direct diff from proof authority:
- `.github/workflows/apu-cycle-proof.yml`: +1 branch-trigger line;
- `scripts/apu_cycle_proof.py`: directed proof additions only;
- **no emulator/runtime source changed**.

New bounded cases:
1. **`budget_20_nop_div_32`** — 10 NOPs (20 SPC cycles) + DIV (12), with a trailing sentinel NOP; expected compiled/executed block = exactly **32 cycles**, PC stops before sentinel.
2. **`budget_20_access_div_32`** — four real direct guest reads + four NOPs form a 20-cycle prefix, then DIV reaches exactly 32; validates that generated `apu_read8` costs participate in the temporal budget.
3. **`budget_branch_taken_22`** / **`budget_branch_not_taken_20`** — conditional path near cutoff, checking static debit plus runtime taken-cycle behavior.
4. Cached exact-32 block re-entry without mutation must reuse the existing block with identical debit/post-state and unchanged JIT pointer/lookup.
5. A covered-region tag increment before re-entry must force recompilation rather than execute the stale cached block.

Acceptance:
- all historical proof invariants remain green;
- every new `budget_*` case total <=32 SPC cycles;
- exact 20+DIV case reports 32 cycles and stops before trailing sentinel;
- access-built 20+DIV also totals 32 with correct state/debit;
- cached replay matches initial execution without recompile;
- covered tag mutation forces recompile.

Falsifiers:
- any produced edge block >32 cycles;
- missing access cost in the budget;
- wrong runtime branch debit/state;
- cached execution differs from initial execution;
- stale block survives an entry-tag mutation;
- any historical semantic/timing regression.

This proof does **not** attempt to close known Gate-C debts around observable dummy-read side effects or intra-block self-modifying code. Those remain explicitly separate accuracy work.

Exact triggered runs:
- **APU Cycle And Span Proof `35380159442`** @ `4f197702ff81...` — pending
- **Build and Validate `35380159566`** @ `4f197702ff81...` — pending
- **APU Cycle And Span Proof `35380154641`** @ `385caf3e0411...` — in_progress
- **Build and Validate `35380154737`** @ `385caf3e0411...` — completed/cancelled
- **Build and Validate `35380150454`** @ `151466bb39ab...` — in_progress


## Cycle-budget boundary proof attempt 1 — HARNESS FALSE NEGATIVE 2026-09-18

Exact attempt: **`phase2/apu-cycle-budget-edge-proof@4f197702ff81687d68a33842105c907b888a2be6`**.

- **Build and Validate `35380159566` SUCCESS** — runtime/build/Mupen remained green.
- **APU Cycle And Span Proof `35380159442` FAILED** only in the newly added cache-reuse assertion.
- diagnostic artifact **`10561814892`**, digest `sha256:0934deb69528d3da795b23834ad1e333756cbddee839bfec802f02dc209d80e4`.

The temporal-edge cases themselves **passed**:
- `budget_20_nop_div_32`: static/total debit **-672 master = 32 SPC cycles**, PC stopped at `0x020B` before the sentinel, DIV post-state matched.
- `budget_20_access_div_32`: static debit **-588** (28 static units) plus four real guest-read cycles produced exact total **-672 / 32 SPC cycles**, with correct DIV state.
- `budget_branch_taken_22`: exact 22-cycle total with expected +2 runtime taken debit.
- `budget_branch_not_taken_20`: exact 20-cycle total with identical compile-time worst-case shape and no taken debit applied.
- all historical cases reached the cache-reuse phase without a timing/semantic failure.

The tag-mutation half of the reuse experiment also worked:
- covered region tag increment changed the lookup/pointer on re-entry;
- stale block was rejected and recompilation occurred.

**HARNESS FALSE NEGATIVE:** the cached-reuse check was executed only after the rest of the full proof matrix. Every proof case uses the same fixed `TEST_PC=0x0200` and recompiles its own block there. Therefore the lookup and guest bytes no longer represented `budget_20_nop_div_32` when the reuse check ran. Evidence: the mutation byte observed at `0x0200` was **0xBE (DAS)** rather than the NOP expected from the 20+DIV seed. The observed cached debit/state therefore belonged to a later proof case and cannot test the intended block.

This failure is **REJECTED as runtime/cycle-budget evidence**.

Immediate repair: immediately before cache-reuse measurement, compile a fresh dedicated 20-NOP-cycle + DIV seed at the fixed test PC, then perform unchanged cached replay and tag-mutation checks before any other case can overwrite that lookup. No runtime source changes are permitted.


## Cycle-budget boundary proof — VALIDATED 2026-09-18

Final proof authority:
**`phase2/apu-cycle-budget-edge-proof@c72068140caa8d7c8b4c862c86de9ef59a9f9231`**.

CI:
- **APU Cycle And Span Proof `35382966438` SUCCESS**, dynamic job `105723612910`;
- **Build and Validate `35382966472` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke green.
- proof artifact **`10562273321`**, digest `sha256:7db0e005a55a19ac20c311cf00cb0bd3f26d9c619b816178a4ce0c173734d9ef`;
- exact proof build **`10562117702`**, digest `sha256:52ceeab65be69f74b41697b6f39129b4bdf3d14c6d067a8270b4a09e5e39798c`.

Validated new edge evidence:
- `budget_20_nop_div_32`: **32 SPC cycles / 672 master cycles exact**, PC stops before trailing sentinel, DIV state correct.
- `budget_20_access_div_32`: four real guest reads contribute runtime bus cycles; total remains **32 SPC cycles exact** with correct state.
- `budget_branch_taken_22`: total **22**, including expected runtime taken debit.
- `budget_branch_not_taken_20`: total **20**, with conservative compile-time branch budget and correct untaken runtime behavior.
- dedicated `budget_reuse_seed_32`: cached replay executed the exact same 32-cycle block with unchanged lookup/JIT pointer and identical PC/A/Y/flags.
- covered tag mutation incremented the region tag and **forced recompilation**; stale entry was not reused.

Proof summary additionally remained true:
- all static debits match source prediction;
- all runtime debits match expected;
- all total debits match pinned reference;
- all semantics match expected;
- all halt scheduler ticks match expected;
- long-probe temporal cutoff remains bounded;
- all directed cycle-budget edge cases <=32;
- exact 20+DIV reaches 32;
- cached replay succeeds without recompile;
- covered entry-tag mutation forces recompile.

The earlier `4f197702...` proof failure is **HARNESS FALSE NEGATIVE / SUPERSEDED**, caused by testing cached replay after later cases had replaced the fixed TEST_PC lookup. No runtime change was needed.

**M1 bounded architecture contract is now validated to the intended edge.** This still does not prove intra-block self-modifying-code behavior or observable dummy-read I/O effects; those remain Gate-C accuracy debt, not blockers to this M1 performance integration.

### Integration discovery
Direct comparison shows `phase2/apu-cycle-budget-clean` is **not** a fast-forward child of current `master`:
- current master: `a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`;
- clean: `d5ce93a03b2dbf5065fefa5276533e02f9658215`;
- merge base: `ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`;
- clean is 40 commits ahead of merge base while master contains 4 commits absent from clean.

**Do not merge the historical clean branch wholesale.** Next action: inspect the 4 master-only commits and reconstruct a fresh M1 integration branch from current master, porting the validated production state without losing current master changes or diagnostic-only branches.


## M1 master integration candidate — running 2026-09-18

Integration branch: **`phase2/m1-integration@671ed75c1f736ebb18bba7c40ec663b278f32865`**.
Parent authority: current **`master@a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`**.

### Runtime integration method
Historical `phase2/apu-cycle-budget-clean` diverges from master because master gained four documentation-only commits after their old merge base. To avoid importing rejected/noop experimental history, the M1 runtime was reconstructed **from current master** using an atomic Git tree whose 14 changed runtime/infrastructure files point to the exact final blob SHAs from clean `d5ce93a0...`.

First integration runtime commit:
**`bc64e8e6080aed53f8f85cff460ddbc930cbe4c1`**.

The master-only changes absent from historical clean were verified to be documentation only:
- `81e14f5f...` Road-to-1.0 M0/M1 docs;
- `69f893bc...` Roadmap APU-first route;
- `90fafc89...` Profiling M1 guidance;
- `a2270699...` docs synchronization.

No current-master emulator/runtime change was overwritten.

Exact clean blobs consumed include the validated emitter blob:
`src/apu_emitter.S = fc510743836c2a0a8afca771ca016cf2d02bf83a`
plus the final timing-foundation APU files and M0 hardware-profile infrastructure.

### Durable regression proof
The final edge-proof harness was preserved without importing proof-branch runtime diagnostics:
- `scripts/apu_cycle_proof.py`;
- `.github/workflows/apu-cycle-proof.yml`.

The durable workflow runs automatically on `master` only for relevant APU/JIT/proof paths (and on the integration branch for this graduation), plus manual dispatch. It does **not** import `src/apu_cycle_diag.S` or PROFILE-only diagnostic emitter changes.

Exact edge-proof scope now documented in Validation:
- **119 directed execution cases + 2 persistent SLEEP/STOP halt groups**;
- exact 20+DIV=32;
- access-built 32-cycle edge;
- conditional paths near cutoff;
- cached replay;
- entry-tag mutation/recompile;
- historical timing/address/semantic families.

### Canonical documentation convergence
On the integration branch:
- `ROAD_TO_1_0.md`: **M0 + M1 achieved; M2/Gate B active**;
- `ROADMAP.md`: Phase 2/M1 achieved; Phase 3 corpus discovery active; no automatic `apu_read8`/DSP/dynarec next step;
- `PROFILING.md`: matched guest-window and real-N64 SRAM authority, throughput vs event cadence vs presentation vs audio distinction, sample-share interpretation limits, Gothicvania demoted to regression workload;
- `VALIDATION.md`: exact 119-case proof scope and explicit non-coverage (dummy-read I/O effects, intra-block SMC, long-run A/V/PCM, broad compatibility).

The docs preserve the audit correction that the real-N64 49->60 movement belongs to the **combined timing-foundation + cycle-budget state**, not the final emitter patch alone, and that 61.83%->51.03% is a change in profile share rather than normalized absolute cost.

### Final integration gates now running
- final branch **Build and Validate `35384286620`** @ `671ed75c...` — pending/running;
- integrated runtime **APU Cycle And Span Proof `35384115986`** @ `5cf83f31...` — running. Later commits are documentation-only, so this proof exercises the exact integrated runtime/proof code.

Previous Build-and-Validate runs cancelled by subsequent sequential integration/doc commits are superseded and are not failure evidence.

### Decision map
If both gates pass:
1. open PR `phase2/m1-integration -> master`;
2. verify PR diff/status and merge without altering the candidate;
3. verify resulting master CI;
4. mark **M1 MERGED-CONSUMED / ACHIEVED** in continuity;
5. begin M2/Gate-B corpus definition as the next technical batch.

If either gate fails, do not merge; isolate whether failure belongs to runtime, durable proof packaging, documentation workflow behavior, or laboratory.


## Integrated durable proof attempt 1 — HARNESS FALSE NEGATIVE 2026-09-18

Integration runtime remained green under final **Build and Validate `35384286620`**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen normal/profile smoke SUCCESS.

The first durable integrated proof run **`35384115986`** at integration runtime/proof SHA `5cf83f31b0fae672e347b6310530372bf4e974f3` failed after the newly added cycle-budget edge/reuse cases had already passed.

Observed failure:
`RuntimeError: target rejected memory read at 0x8000E600: ED2FFD`.

This is **HARNESS FALSE NEGATIVE / REJECTED as runtime evidence**.

Cause:
- GDB RSP memory reads return raw hexadecimal text;
- the guest bytes `ED 2F FD` legitimately return `ED2FFD`;
- the master-era `scripts/gdb_rsp_dump.py` treated **any** reply beginning with ASCII `E` as an RSP error;
- the validated proof branch had already corrected this parser to recognize an error only when the reply has the three-byte RSP error form (`len(reply) == 3 && startswith("E")`);
- that one-line harness fix was accidentally omitted when preserving the proof on the fresh master-based integration branch.

Evidence that the runtime/proof contract itself was healthy before the parser false positive:
- `budget_20_nop_div_32`: exact 32 SPC cycles, semantic/debit/span checks true;
- `budget_20_access_div_32`: exact 32 total cycles with real guest-read timing included;
- taken/not-taken cutoff branch checks true;
- fresh cached 32-cycle replay: same -672 debit, same PC/A/Y/flags, lookup/JIT pointer unchanged;
- covered tag mutation: stale block rejected and lookup/JIT pointer changed through recompilation.

The integration branch must consume the exact validated one-line RSP parser fix before re-running the durable proof. Also add `scripts/gdb_rsp_dump.py` to the proof workflow path filter because the proof imports `RSPClient` from that file.

No emulator/runtime source change is authorized by this finding.


## M1 integration durable-proof parser repair — running 2026-09-18

Integration branch advanced to **`phase2/m1-integration@d701f80f5339c727f231e4e9cc2b7222ec9c1561`**.

Changes since the previously Build/Validate-green `671ed75c...`:
- `scripts/gdb_rsp_dump.py`: consume the already-validated one-line RSP parser fix from the edge-proof line, recognizing only the three-byte `E??` RSP error form rather than misclassifying arbitrary E-prefixed memory hex data;
- `.github/workflows/apu-cycle-proof.yml`: add `scripts/gdb_rsp_dump.py` to the path trigger because the proof imports `RSPClient` from that file.

No emulator/runtime source changed. The 14 M1 runtime/infrastructure blobs consumed from clean remain unchanged from the real-N64 60/60 candidate.

Exact current runs:
- **APU Cycle And Span Proof `35385014498`** @ `d701f80f...` — running;
- **Build and Validate `35385014527`** @ `d701f80f...` — queued/running.

Question: does the durable proof reproduce the already-green edge-proof result once its exact validated RSP parser dependency is present?

Acceptance:
- all 119 directed cases + halt groups pass;
- exact 32-cycle/access/branch/cache/tag invariants remain true;
- final Build and Validate remains green.

Falsifier:
- any timing/semantic/cache/tag invariant fails after the parser repair, or final build/smoke regresses.

If accepted, this closes the final pre-PR integration gate. If not, do not merge; classify the failure before changing runtime.


## M1 integration pre-PR gates — VALIDATED 2026-09-18

Final integration branch authority:
**`phase2/m1-integration@d701f80f5339c727f231e4e9cc2b7222ec9c1561`**.

No emulator/runtime source changed after the validated M1 runtime integration commit; later changes preserve the durable proof, canonical docs and the one-line RSP harness parser dependency.

### Final Build and Validate
**Run `35385014527` SUCCESS** at exact HEAD `d701f80f...`:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen normal/profile smoke SUCCESS.

Artifacts:
- normal build **`10564130283`**, digest `sha256:4f87d77b053bf7be137ca5f657aa74d38a272af66b524134674950d4cd858ce4`;
- PROFILE build **`10563627262`**, digest `sha256:d3a36d51c4251f4fc4119a7da7b0a06b92f5cf43dfbf50f469251fda542a2524`;
- emulator smoke **`10563682276`**, digest `sha256:6d0bac540a4178f8bfa81d4a85752e32223b5cf9fcb868e2e26797dbbff3aea5`.

### Final durable SPC700 cycle-budget proof
**APU Cycle And Span Proof `35385014498` SUCCESS**, exact HEAD `d701f80f...`, dynamic job `105730158853`.

Artifacts:
- exact proof build **`10563771898`**, digest `sha256:93cb8ee27b798a15eeb0457d872f1cbf1ce94f01fe18cc86bf816294fd8fc05b`;
- proof diagnostics **`10563443390`**, digest `sha256:7973295305bc6f71cbb131dbc22228d696cd131e1dce6220600fcde063627096`.

All durable summary invariants are true:
- all cycle-budget edge cases <=32 SPC cycles;
- all static debits match prediction;
- all runtime debits match expected;
- all total debits match pinned reference;
- all semantics match expected;
- all header spans match expected;
- all SLEEP/STOP halt scheduler ticks match;
- long temporal-cutoff probe remains bounded;
- exact 20+DIV reaches 32;
- cached exact-32 replay reuses without recompilation and reproduces state/debit;
- covered tag mutation forces recompilation.

The prior integrated proof failure `35384115986` is **HARNESS FALSE NEGATIVE / SUPERSEDED** by the exact RSP parser dependency repair. It is not runtime failure evidence.

State: **VALIDATED / READY FOR PR TO MASTER**.

Next action: open `phase2/m1-integration -> master`, verify mergeability/diff/checks, merge without modifying the candidate, then validate the resulting master SHA before marking M1 MERGED-CONSUMED.


## PR #12 — M1 integration candidate OPEN / awaiting PR-only lab gate 2026-09-18

PR: **#12 `phase2/m1-integration -> master`**
Title: `M1: integrate validated SPC700 timing and cycle-budget core`.
Exact head: **`d701f80f5339c727f231e4e9cc2b7222ec9c1561`**.
Base at PR open: **`master@a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`**.

GitHub recalculated the initial transient `mergeable=false` to:
- `mergeable=true`;
- `rebaseable=true`;
- `mergeable_state=unstable`.

There is **no merge conflict**. The unstable state is due to an additional PR-only workflow currently running:
- **Ares Profile Validation `35385948762`** @ exact PR head `d701f80f...`.

Already-green exact-head pre-PR gates remain:
- Build and Validate `35385014527` SUCCESS;
- durable APU Cycle And Span Proof `35385014498` SUCCESS.

Decision:
- wait for the PR-only Ares validation;
- if green, merge PR #12 without modifying the candidate;
- if it fails, classify the failure as workload/lab/runtime before merge.


## PR #12 PR-only Ares gate — VALIDATED 2026-09-18

Exact PR head remains:
**`phase2/m1-integration@d701f80f5339c727f231e4e9cc2b7222ec9c1561`**.

**Ares Profile Validation `35385948762` SUCCESS** on the exact PR head.

Jobs:
- profile-build SUCCESS;
- ares-smoke SUCCESS;
- pinned N64-only ares build SUCCESS;
- deterministic workload generation SUCCESS;
- interpreter control + CPU-JIT workload matrix SUCCESS;
- frame-budget/profile report generation SUCCESS.

Road-valid runtime state was observed during the lab:
- `apu_clock=21`;
- audio `4`;
- precision `8`;
- valid statistical sample densities for the decision matrix.

Artifact:
- `sodium64-ares-profile-matrix` ID **`10564595266`**;
- digest **`sha256:f4bc1721be208f84046a37b3d5360c8c3673a76082964f1945e1ddaec5ba32a6`**.

Exact profile-build artifact:
- ID **`10563408739`**;
- digest `sha256:0dcdc3439594d540ce3745617affb84dcdca7f49d3392889722c7cf2bc9c2f7e`.

Interpretation: this is the additional PR-only emulator-lab regression gate. It does not supersede real-N64 hardware authority, but no lab regression was found that blocks integration.

PR #12 is currently:
- open;
- `mergeable=true`;
- no merge conflict;
- exact head unchanged from all green pre-merge gates.

**PRE-MERGE STATE: VALIDATED / READY TO MERGE.**

Next action: squash-merge PR #12 to keep the mainline history free of integration/harness intermediate commits while preserving the exact validated final tree, then validate the resulting master SHA before marking M1 MERGED-CONSUMED.


## PR #12 MERGED — post-merge validation running 2026-09-18

PR **#12** was squash-merged successfully.

New integrated authority:
**`master@ac1ce74740d974b70206fcb6ba842e492b5d7272`**.

Squash integrity check:
- PR head `d701f80f5339c727f231e4e9cc2b7222ec9c1561` tree: `28147decc7994542d352738c43f40fe1249bbb71`;
- merged master `ac1ce747...` tree: `28147decc7994542d352738c43f40fe1249bbb71`;
- **exact tree match = true**.

Therefore the squash merge changed commit history only; it did not alter the validated candidate tree.

Merge parent:
- previous master `a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`.

Post-merge exact-SHA workflows automatically triggered:
- **Build and Validate `35387454297`** @ `ac1ce747...` — running;
- **APU Cycle And Span Proof `35387454371`** @ `ac1ce747...` — running;
- **Ares Profile Validation `35387454367`** @ `ac1ce747...` — running.

Do **not** mark M1 MERGED-CONSUMED until these post-merge gates finish. Because the merged tree is byte-identical to the fully validated PR tree, any new failure must first be classified as workflow/lab nondeterminism versus genuine exact-tree regression rather than assumed to be a new code change.

Next action:
- wait for all three exact-master-SHA gates;
- if green, mark M1 **MERGED-CONSUMED / ACHIEVED** and move RESUME HERE to Gate-B corpus definition;
- if any fails, inspect exact failure before changing code.


## M1 MERGED-CONSUMED / ACHIEVED — 2026-09-18

Integrated authority:
**`master@ac1ce74740d974b70206fcb6ba842e492b5d7272`**.

PR #12 was squash-merged with an exact tree match to the fully validated PR head.

All exact-master-SHA post-merge gates are green:
- **Build and Validate `35387454297` SUCCESS**;
- **APU Cycle And Span Proof `35387454371` SUCCESS**;
- **Ares Profile Validation `35387454367` SUCCESS**.

Therefore the M1 runtime and its durable regression proof are now **MERGED-CONSUMED** in master. M1 is **ACHIEVED**. Gate B / M2 is the active milestone.

The authoritative M1 hardware result remains the real-N64 Gothicvania capture:
- 60,60,60,60,60 /60;
- frameskip 0;
- APU clock 21;
- audio 4;
- precision 8;
- 3,580 samples;
- 11.51% frame/VI wait.

Do not resume Gothicvania FPS optimization unless a later regression makes it gate-relevant again.

## Gate-B autonomy constraint — 2026-09-18

Iron clarified an architectural workflow requirement:

**The normal technical loop must remain autonomous through repository-accessible infrastructure. Do not make local commercial ROMs, Iron's powered-on PC, or Iron's continuous availability a dependency of routine diagnosis, iteration or gate selection.**

Consequences:

- The **primary Gate-B development corpus must be fully reproducible by the assistant/CI from legally redistributable/open sources or generated test workloads available from GitHub-accessible infrastructure.**
- Do **not** fill the corpus with near-duplicate workloads merely because they are convenient. Diversity of engine/toolchain and exercised SNES subsystems is required.
- Gothicvania remains one representative regression workload, not the template all new workloads must resemble.
- Open-source/source-available workloads may be patched for deterministic input/checkpoints when the patch is explicit, hashed and does not amputate required emulation work.
- Commercial ROMs may be used later as **supplemental representativeness / milestone validation** when Iron is available, but they must never become the main daily development loop.
- Commercial ROM bytes must not be committed or uploaded to GitHub/Actions/artifacts. A commercial test, if later used, is local-only and should be requested only when a sufficiently mature batch has accumulated and multiple autonomous lab checks already indicate it is worth testing.
- Real N64 remains final performance authority, but hardware sessions should aggregate multiple hardware-ready questions/workloads rather than serving as an iterative debugger.

This refines the red-team Batch-2 interpretation:
- Astra's requirement is a **small diverse base corpus**, not specifically a commercial corpus.
- First build a diverse autonomous corpus and use it to discover the next Gate-B blocker.
- Use commercial software later to test representativeness once autonomous evidence has converged enough to justify a milestone session.

### RESUME HERE — Gate B / M2

M1 is integrated and closed.

Immediate next technical batch:
1. define a **four-workload autonomous Gate-B corpus**: Gothicvania plus three non-redundant workloads chosen for materially different CPU/gameplay, PPU/HDMA/Mode-7, and audio behavior;
2. prefer different codebases/toolchains/engines where practical rather than three more PVSnesLib examples;
3. pin source commit/toolchain/input/checkpoint/ROM hash and expected observable behavior for every workload;
4. run them first in reproducible emulator labs and classify failures before changing runtime;
5. choose the next runtime intervention only from the first demonstrated corpus blocker;
6. reserve commercial-ROM and real-hardware validation for a later aggregated milestone after the autonomous corpus has converged.

Do not preselect APU, DSP, PPU, S-CPU dynarec or another architecture before the corpus evidence exists.


## Gate-B corpus selection refinement — 2026-09-18

Iron refined the desired diversity criterion for the three new autonomous workloads:

Choose workloads whose **architectural behavior** approximates three materially different commercial SNES families, using **SMW / DKC / Zelda: A Link to the Past** as reference archetypes. Similarity is about execution patterns and subsystem pressure, not visual style or IP imitation.

Target archetypes:
- **SMW-like:** scrolling platformer, dynamic/map updates, collision/object logic, sprites and per-frame gameplay loop;
- **DKC-like:** heavier audiovisual pressure, entity/animation work, DMA/HDMA/PPU activity and active audio/SPC700;
- **ALttP-like:** top-down area/map logic, scripting/state, object interaction, tilemap updates and transitions.

This remains inside Astra's Batch-2 direction: Gothicvania + three diverse workloads, emulator labs first, one aggregated real-N64 milestone later, next runtime work selected only from the first demonstrated blocker.

Initial research findings, not yet locked:
- `undisbeliever/space-rescue-squad@e08333a6...` is a strong DKC-like candidate: full platformer/game code, custom entity/collision/scrolling engine, HDMA, DMA-time budgeting, animated tilesets and Terrific Audio Driver. Code is zlib; game resources are source-available but restricted to this game, so use only as its own workload.
- `undisbeliever/castle_platformer@79e2eb4e...` is a possible SMW-like candidate: MIT, ca65, dynamic editable map, tile-specific movement/friction, interactive tiles, static platforms and dynamically loaded animated sprites. It may be too simple and shares author/lineage with Space Rescue Squad, so do not lock it without a diversity comparison.
- `Ramsis-SNES/furryrpg@35b4eb22...` is architecturally attractive for the ALttP/RPG role (area loader, scripting, sprite-to-BG collision, Mode-1 world map, Mode-7, SPC700/audio), but repository license metadata/file is absent despite the README describing it as open-source freeware. Treat licensing/reuse status as **OPEN QUESTION**; do not consume or redistribute it until that is resolved.
- `undisbeliever/unnamed-snes-engine` is MIT and top-down but currently a single-screen tech demo; useful fallback/probe, probably too narrow for the main representativeness slot.

Next action: continue candidate search with explicit preference for different authors/toolchains/engines where practical; validate buildability, licensing/distribution boundaries and reproducible deterministic execution before fixing the final three.


## Gate-B candidate quality reassessment — 2026-09-18

Iron challenged whether visually/gameplay-poor homebrew or game-jam projects are representative enough for the three principal Gate-B slots. This distinction matters.

**Selection rule clarified:** visual polish, commercial appeal and fun are not requirements for a performance/correctness workload. However, project scope, sustained gameplay complexity, engine diversity, subsystem activity and duration **are** relevant. A tiny demo may be technically correct yet still be too narrow to represent a commercial-style engine family.

Current reclassification:

- **Space Rescue Squad — STRONG CANDIDATE, still not locked.** Although created for the 2025 SNESDEV game jam and visually modest, repository evidence shows materially nontrivial architecture/content: ~15 authored rooms including boss/water/gravity scenarios; multiple enemy/projectile/entity behaviors; collision and scrolling engine; HDMA; explicit VBlank/DMA-time budgeting; animated tilesets; Terrific Audio Driver; five music themes and substantial BRR/sample content. Its game-jam origin alone does not disqualify it. It must still pass build reproducibility and sustained-workload profiling before occupying a principal slot.

- **Castle Platformer — DOWNGRADED to AUXILIARY / FALLBACK.** It has a legitimate MIT ca65 engine, dynamic map, entity physics, interactive tiles, animated sprites and five levels, but it is explicitly a simple platformer engine/demo, materially smaller, and shares author/technical lineage with Space Rescue Squad. It is useful as an open diagnostic/regression workload but currently does not justify one of the three principal diversity slots if a stronger independent SMW-like candidate exists.

- **Furry RPG — TECHNICALLY STRONG, ELIGIBILITY BLOCKED.** Architecture remains attractive for the ALttP/RPG role: area loader, event scripting, collision, world map, Mode 7, NMI/IRQ work and SPC700/SNESGSS audio. It is WIP and the repository contains no explicit LICENSE despite the README calling it open-source freeware. Do not consume it into the principal corpus until redistribution/automation rights are unambiguous.

Implication: do not confuse source availability with representativeness. The three main slots should survive an **audition** based on sustained real gameplay complexity, independent engine/toolchain lineage, observable subsystem activity and reproducible build/input/checkpoint behavior. Smaller demos remain useful as probes but should not crowd out stronger candidates.


## Gate-B Space Rescue Squad audition — source-build proof running 2026-09-18

First execution-based corpus audition has started on:
**`phase3/gate-b-srs-audition@25f71f2e3690385727fc5b45ff2c0810b5667460`**,
parented directly from integrated **`master@ac1ce74740d974b70206fcb6ba842e492b5d7272`**.

This branch changes **workflow only**. No Sodium64 runtime/emulator source is modified.

Question:
Can the strongest currently clean DKC-/heavy-platformer candidate, **Space Rescue Squad**, be reconstructed autonomously and reproducibly from its exact public source without Iron's PC, proprietary Aseprite regeneration, or redistribution of its ROM?

Pinned upstream:
- `undisbeliever/space-rescue-squad@e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865`;
- `bass-untech@9db6088a378061afc7b82f50997a5b9a1d951175`;
- `untech-editor@4c72dc69619c0c246aa7e6325b18b6fb3c219821`;
- `terrific-audio-driver@17823e5a55893e8442917abadb4e84feb216e5ad`.

Controlled build proof:
- builds the exact upstream CLI tools from pinned submodules;
- uses committed generated PNG inputs instead of requiring the proprietary Aseprite editor;
- builds the **unmodified release game** first;
- rejects any tracked-source mutation;
- records ROM size/hash and toolchain provenance;
- uploads **provenance/hash only, not the SRS ROM**.

Run:
- **Gate B SRS Audition `35393181107`** @ `25f71f2e...` — queued/running at checkpoint.

Acceptance:
- exact pinned source/submodules reproduce a non-empty release ROM;
- upstream tracked tree remains clean;
- build requires no local/private input;
- only non-ROM provenance leaves the job.

Falsifier / downgrade:
- required source/assets are unavailable or non-reproducible;
- build depends materially on proprietary/local-only tooling despite committed generated inputs;
- fixing the build would require maintaining a second toolchain/project disproportionate to Gate-B value.

If accepted, next controlled step is a **temporary explicit benchmark patch** (auto-start + deterministic input + survival only if needed while preserving collisions/hurt/audio), followed by a pinned ares N64 profile/frame-budget audition at Road-valid settings. Do not request hardware.


## SRS source-build attempt 1 — HARNESS/BUILD INVOCATION FALSE NEGATIVE 2026-09-18

Exact run:
- branch `phase3/gate-b-srs-audition@25f71f2e3690385727fc5b45ff2c0810b5667460`;
- **Gate B SRS Audition `35393181107` FAILED** in the final game-build step.

What passed:
- Ubuntu dependency install;
- exact SRS checkout and all pinned submodules;
- UnTech Editor CLI toolchain build;
- pinned Wiz build;
- Terrific Audio Driver `tad-compiler` build.

Failure:
`python3 ../tables/sine-table.py > gen/tables/sine-table.inc`
returned `Directory nonexistent`.

Cause:
The audition invoked `make ... bin/space-rescue-squad.sfc` directly. Upstream's normal `all` path depends on its `directories` target, which creates `gen/tables` and the other generated-output directories. Directly naming the ROM target bypassed that prerequisite.

Classification:
**HARNESS/BUILD INVOCATION FALSE NEGATIVE / REJECTED as candidate evidence.**
This does not show unavailable dependencies, proprietary-tool dependence or an upstream source defect.

Immediate repair:
run upstream `make -C game directories` before the explicit release-ROM target, then repeat unchanged. No upstream source, assets, Sodium64 runtime or benchmark behavior changes.


## SRS source-build proof — VALIDATED 2026-09-18

Exact candidate/build authority:
- audition branch `phase3/gate-b-srs-audition@0c5f3a3df4f2f790d8c09c5dd2b3f01c6d68e432`;
- **Gate B SRS Audition `35393460280` SUCCESS**;
- upstream SRS `e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865`;
- exact release ROM size **262,144 bytes**;
- exact unmodified release ROM SHA-256 **`d5bd7b17aa19a1b370efa38554b6ebfd77c4756e7184e9f2e848e8193bc9bed0`**.

Pinned-source toolchain successfully rebuilt:
- bass-untech `9db6088a378061afc7b82f50997a5b9a1d951175`;
- untech-editor `4c72dc69619c0c246aa7e6325b18b6fb3c219821`;
- terrific-audio-driver `17823e5a55893e8442917abadb4e84feb216e5ad` plus its pinned Wiz submodule.

No Aseprite binary was required: committed generated PNGs were used as intended build inputs. The tracked upstream tree remained unmodified after the release build.

Provenance-only artifact:
- ID **`10566587049`**;
- digest **`sha256:d1a63b07b6a434cc101da6585da01f25fd4b0a46613c18995008527fda1eab27`**.
- artifact contains hashes/provenance only; **the SRS ROM is not uploaded**.

Interpretation:
**Space Rescue Squad passes the autonomy/buildability gate.** Its game-jam origin does not create a toolchain or source-availability dependency on Iron.

This does not yet establish corpus membership, correctness under Sodium64, representativeness, or real-N64 performance.

Next controlled step:
create an explicit temporary benchmark patch that preserves normal audio/game-state/room/entity/collision/render logic, starts directly in the first gameplay level after normal initialization, and supplies deterministic Right+Run input. Run the resulting workload under the existing pinned ares N64 Sodium64 profile/frame-budget lab at frameskip 0, APU21, audio4, precision8. Do not request hardware.


## Gate-B SRS deterministic-profile attempt 1 — HARNESS FALSE NEGATIVE 2026-09-18

Repo/CI reconciliation found continuity lagging one technical step behind the actual audition branch.

Current audition authority before repair:
- **`phase3/gate-b-srs-audition@300a358e50f88df8a4f03e98dc5f7adb9dc5772b`**;
- branch remains workflow-only relative to **`master@ac1ce74740d974b70206fcb6ba842e492b5d7272`**;
- no Sodium64 emulator/runtime source is changed.

The previously documented source-build proof remains valid:
- **Gate B SRS Audition `35393460280` SUCCESS** @ `0c5f3a3d...`;
- exact unmodified upstream release ROM SHA-256 `d5bd7b17aa19a1b370efa38554b6ebfd77c4756e7184e9f2e848e8193bc9bed0`;
- build is autonomous from pinned public source/toolchain and requires no Iron-local input.

A later commit attempted the next controlled step: explicit deterministic first-level gameplay + Road-valid Sodium64 PROFILE/ares measurement.

Exact run:
- **Gate B SRS Audition `35393812922` FAILED** @ `300a358e...`;
- branch **Build and Validate `35393812773` SUCCESS** at the same SHA.

What the failed audition actually reached:
- source/toolchain checkout/build SUCCESS;
- unmodified SRS release build SUCCESS;
- provenance-only artifact upload SUCCESS;
- **benchmark-creation shell step FAILED before the Python patch executed**;
- all Sodium64 PROFILE, ares, wrapping and profiling steps were skipped.

Exact failure:
`unexpected EOF while looking for matching '\''`.

Cause:
the workflow's post-patch changed-file assertion was emitted with malformed shell quoting:
`test "$changed" = game/src/_main.asm\ngame/src/gameloop.inc'`.

Classification:
**HARNESS FALSE NEGATIVE / REJECTED as SRS or Sodium64 evidence.**
No benchmark ROM was produced and no emulator-profile result exists from this run.

Important non-conclusion:
This run says nothing yet about SRS boot/progression, Sodium64 compatibility, throughput, subsystem pressure, cadence, or corpus suitability.

Immediate controlled repair:
replace only the malformed changed-file shell comparison with a correctly quoted two-line expected value, keep the intended benchmark patch and all profiling settings unchanged, then rerun. Do not change emulator/runtime code and do not request hardware.


## Gate-B SRS deterministic-profile attempt 2 — WORKFLOW PARSE FALSE NEGATIVE 2026-09-18

Repair commit **`phase3/gate-b-srs-audition@07b0b3b152b6e903c3c01289e095d305720c0fda`** attempted to replace the malformed changed-file assertion.

GitHub Actions run:
- workflow/run **`35394545732`** — immediate FAILURE;
- **no jobs were created**;
- Build and Validate for the same branch commit was separately queued/running and is not relevant to this YAML parser failure.

Repo inspection shows the intended ANSI-C quoted expected string did not survive in the workflow file: the block contains only `expected=` before the next command. GitHub therefore rejected the workflow before executing the source-build or benchmark steps.

Classification:
**WORKFLOW PARSE/HARNESS FALSE NEGATIVE / REJECTED as candidate or runtime evidence.**

What this does NOT prove:
- nothing new about SRS build/runtime;
- nothing about benchmark patch validity;
- nothing about Sodium64 compatibility/performance.

Next repair:
avoid multiline shell-string quoting entirely. Materialize actual and expected changed-file lists into temporary files and compare with `cmp`. Keep every benchmark/runtime/profile setting otherwise unchanged.

## Gate-B SRS workflow reconstruction — RUNNING 2026-09-18

Root cause of the immediate parser failures after `300a358e...` was broader than the intended one-line quote repair:
the two attempted edits contaminated the workflow with an accidental **~325-line duplicated tail**.

Evidence:
- compare `300a358e... -> 63ba40f5...`: +325/-1 lines in the single workflow file;
- GitHub rejected the contaminated workflows before creating jobs;
- these runs are **WORKFLOW PARSE FALSE NEGATIVES**, not runtime evidence.

Clean reconstruction:
- rebuilt `.github/workflows/gate-b-srs-audition.yml` from the last GitHub-executed base **`300a358e50f88df8a4f03e98dc5f7adb9dc5772b`**;
- replaced only the malformed changed-file assertion with three simple checks:
  - exactly two changed paths;
  - one is `game/src/_main.asm`;
  - one is `game/src/gameloop.inc`.
- new audition head: **`phase3/gate-b-srs-audition@6e5d444017ca899bcf2b69be6cbf8dd94eee9507`**;
- compare vs `300a358e...`: **+3/-1 lines only**;
- workflow line count restored to 530 (previous contaminated head 852).

Current exact runs:
- **Gate B SRS Audition `35394713398`** @ `6e5d4440...` — running;
- Build and Validate `35394713401` @ same SHA — queued/running.

No Sodium64 runtime/emulator source changed.

Acceptance remains unchanged:
produce the deterministic first-level SRS benchmark from pinned public source, preserve normal emulation/gameplay/audio work, run Road-valid Sodium64 PROFILE under pinned ares, and obtain valid profile/frame-budget evidence.

Until `35394713398` reaches the profile stage, there is still **no SRS execution evidence** beyond the already-validated autonomous source build.

## Gate-B SRS deterministic benchmark — BUILD ACCEPTED / profiling running 2026-09-18

Exact audition head remains **`phase3/gate-b-srs-audition@6e5d444017ca899bcf2b69be6cbf8dd94eee9507`**.

Run **Gate B SRS Audition `35394713398`** has now passed:
- exact pinned SRS/toolchain checkout;
- full CLI toolchain build;
- unmodified release ROM rebuild;
- provenance-only upload;
- **explicit deterministic gameplay benchmark creation and rebuild**.

The benchmark patch therefore compiles successfully and reaches the next lab stage. It:
- keeps normal SRS audio initialization;
- initializes normal game state;
- selects the first authored gameplay room (`a1a_entrance`);
- preserves room/entity/collision/camera/metatile/animation/script/WaitFrame work;
- injects deterministic held Right+Run input in the normal game loop;
- does not disable enemies, collision, audio, PPU work, APU work, frameskip or precision.

Current run has advanced to Sodium64 PROFILE build; ares/profile/frame-budget steps are still pending/running.

Interpretation:
**BUILD/WORKLOAD CONSTRUCTION ACCEPTED.** This is not yet execution/compatibility/performance evidence. Do not classify SRS as a corpus member until the pinned ares lab actually boots/progresses and yields valid Road-state counters.

Benchmark ROM/patch hashes will be recorded from the completed run artifact/log once available.

## Gate-B SRS first execution profile — MEASURED / needs repeatability 2026-09-18

Exact authority:
- audition head **`phase3/gate-b-srs-audition@6e5d444017ca899bcf2b69be6cbf8dd94eee9507`**;
- **Gate B SRS Audition `35394713398` SUCCESS**;
- same-head **Build and Validate `35394713401` SUCCESS**;
- non-ROM diagnostic artifact **`10567217952`**, digest `sha256:7bd5e9045de0d2fb3b55902829947b3448d3fcecfe265f006e8a0d8daa4e7d1a`;
- source-build provenance artifact `10567178769`, digest `sha256:ea44a19cf04e20501ce04fcc395bb7e85fd026deadce797551ad95a19d2dba2b`.

Pinned workload:
- upstream `undisbeliever/space-rescue-squad@e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865`;
- unmodified release ROM: 262144 bytes, SHA-256 **`d5bd7b17aa19a1b370efa38554b6ebfd77c4756e7184e9f2e848e8193bc9bed0`**;
- deterministic benchmark ROM: 262144 bytes, SHA-256 **`7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`**;
- benchmark patch SHA-256 **`4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`**.

Benchmark patch scope is exactly two upstream files:
- `_main.asm`: after normal audio init, initialize normal game state, select authored room `a1a_entrance`, enter `Mode.GAME`;
- `gameloop.inc`: inject held Right+Run into the normal controller state before normal gameplay processing.

Preserved workload work:
audio init/song path, game state, room loading, entities, collisions, camera, metatiles, animations, scripts, PPU/DMA/HDMA paths and `WaitFrame`. Nothing is disabled for speed.

Road-valid observed runtime settings:
- frameskip `0`;
- APU clock `21`;
- audio `4`;
- precision `8`.

First pinned ares lab measurement (R4300 recompiler ON, RSP interpreter forced due known ares LAB LIMITATION):
- measured wall time 9 s to reach sample-density threshold;
- **1,282 valid statistical samples**;
- last complete internal VI window: **53/60**;
- virtual budget: **88.3% — below virtual target**;
- partial window at stop: 48/60, 48 guest frames;
- queue `1`.

Sample shares:
- frame/VI wait **28.24%**;
- APU/SPC700 static **28.08%**;
- S-CPU interpreter **15.99%**;
- PPU/events/frame prep **8.19%**;
- DSP/audio **6.63%**;
- APU JIT generated **6.24%**;
- DMA/HDMA **4.29%**;
- RSP/VRAM semaphore wait **2.18%**;
- SNES memory/I/O 0.08%; input 0.08%.

Interpretation:
**MEASURED in emulator lab, not real-N64 performance authority.** SRS successfully survives the full autonomous build/wrap/profile path and produces a materially different profile from Gothicvania. The single measured complete window is below 60/60, so SRS is a strong candidate for exposing a Gate-B issue.

However, do NOT yet call `53/60` a real-N64 deficit or choose an optimization from it. The simultaneously high 28.24% VI-wait share makes the first run insufficient to distinguish sustained compute deficit from bursty workload, measurement-window/startup effects, presentation/cadence behavior, or another lab/runtime interaction.

Next controlled experiment:
repeat the exact same SRS benchmark/profile multiple times at the same SHA/settings, preferably without changing runtime or workload, and compare complete-window frame budget plus subsystem distribution. If the sub-60 result is stable, add a progression/checkpoint observation before selecting a runtime intervention. No hardware request yet.

## Gate-B SRS repeatability experiment — RUNNING 2026-09-18

Exact experiment head:
**`phase3/gate-b-srs-audition@466be943a7a725c2833e9dba4dd8d56c2f0a01ff`**.

Diff from first successful SRS profile head `6e5d4440...`:
- one commit;
- **workflow only** (`.github/workflows/gate-b-srs-audition.yml`);
- no Sodium64 runtime/emulator source change;
- no upstream SRS source or benchmark logic change.

Workload identity is now gated before profiling:
- deterministic benchmark ROM must remain SHA-256 `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`;
- benchmark patch must remain SHA-256 `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`.

Controlled experiment:
- build the same pinned SRS benchmark once;
- build the same Sodium64 PROFILE runtime once;
- build the same pinned ares lab once;
- launch **three fresh ares processes** (`r1/r2/r3`) sequentially;
- each repeat uses the same Road-valid settings and the same warmup/settle/sample-density contract as the first measured run;
- each repeat requires >=800 samples and validates frameskip 0, APU21, audio4, precision8;
- aggregate all three profile JSONs and frame-budget state files into comparison tables.

Exact runs:
- **Gate B SRS Audition `35395725393`** @ `466be943...` — running;
- Build and Validate `35395725495` @ same SHA — running.

Question:
Is the first `53/60` complete-window result a repeatable property of this exact SRS lab segment, or a one-run/start-window artifact?

Acceptance for repeatability:
- all three fresh processes complete with valid Road-state counters;
- complete-window frame budgets cluster tightly enough to describe a stable lab signal;
- subsystem distributions remain broadly consistent rather than changing qualitatively between repeats.

Falsifier / interpretation:
- large frame-budget dispersion or materially different profile shapes means the current measurement window/lab procedure is unstable for SRS; do not optimize runtime from it;
- stable sub-60 windows support treating SRS as a real Gate-B lab blocker candidate, but still do **not** establish real-N64 performance deficit.

If stable, next experiment is progression/checkpoint anchoring or later-segment measurement before selecting any runtime intervention. No hardware request yet.

## Gate-B SRS repeatability result — NOT STABLE / measurement window rejected 2026-09-18

Exact authority:
- experiment head **`phase3/gate-b-srs-audition@466be943a7a725c2833e9dba4dd8d56c2f0a01ff`**;
- **Gate B SRS Audition `35395725393` SUCCESS**;
- **Build and Validate `35395725495` SUCCESS** at the same SHA;
- diagnostic artifact **`10568281259`**, digest `sha256:b5b79dbf4ad6d6de5edaca568df5e2300767159f9d4ab719dee0e6d477e1cb00`;
- source-build provenance artifact `10567223794`, digest `sha256:9cab4c5d581e252d0c2a5ec3889163f8db7964699d32e055ebdbee7e1b3e7adc`.

Workload identity checks passed before profiling:
- benchmark ROM SHA-256 `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e` — exact match;
- benchmark patch SHA-256 `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7` — exact match;
- no Sodium64 production/runtime source changed.

Three fresh pinned-ares processes at frameskip0/APU21/audio4/precision8:
- **r1:** 2,203 samples; last complete VI window **60/60**; measurement stopped after 12 s host wall time; VI wait 29.10%, APU static 24.10%, S-CPU 14.84%, DSP 9.71%, PPU 8.40%, APU JIT 5.95%, DMA 4.86%, Memory/I-O 1.77%, VRAM/RSP wait 1.18%.
- **r2:** 1,221 samples; last complete VI window **59/60**; stopped after 3 s host wall time; VI wait 41.11%, APU static 29.07%, DSP 12.04%, S-CPU 7.78%, PPU 4.75%, APU JIT 3.52%, DMA 1.56%.
- **r3:** 881 samples; last complete VI window **53/60**; stopped after 12 s host wall time; VI wait 33.60%, APU static 19.64%, S-CPU 17.25%, PPU 9.31%, APU JIT 6.81%, DMA 5.79%, DSP 4.09%, VRAM/RSP wait 3.41%.

The earlier first successful run at `6e5d4440...` also ended on **53/60**, but that does not rescue stability: the controlled three-repeat matrix spans **53..60/60** with qualitatively different subsystem mixes.

Interpretation:
**REJECTED:** treating the current single `fps_display` value as a stable SRS Gate-B performance result.

The experiment's explicit falsifier fired. The >=800-sample stopping rule reaches threshold at materially different host times and therefore captures the 'last complete 60-VI window' at different guest/workload phases. The profile distributions changing with the window supports phase/measurement-position sensitivity rather than one stable compute ceiling.

What this DOES show:
- SRS repeatedly boots/runs through the lab path at Road-valid settings;
- its workload has materially varying frame cost over time;
- the current measurement method is insufficiently phase-aligned for using one terminal window to select an optimization.

What this does NOT show:
- no defensible single SRS FPS number;
- no real-N64 deficit;
- no evidence yet that CPU, APU, DSP, PPU or DMA should be the next optimization target.

Immediate next experiment:
replace the terminal-window question with an **internal-VI-window history** measurement. Capture several consecutive completed 60-VI budgets from Sodium64 itself, independent of when the host reaches the statistical-sample threshold. Keep runtime settings and SRS workload unchanged. Prefer tiny PROFILE-only instrumentation (one history write per completed 60-VI window) plus host decoding over any production behavior change.

Acceptance:
a single run yields an ordered series of consecutive complete internal VI windows with enough context to distinguish startup/transitions from sustained gameplay. Repeat only after that series is defined.

No hardware request and no runtime optimization until this measurement ambiguity is resolved.


## Gate-B SRS internal 60-VI history experiment — RUNNING 2026-09-18

Exact diagnostic head:
**`phase3/gate-b-srs-audition@bd9f7a75518a21563cb62cbce2c5dfd177cc777b`**,
one commit ahead of the repeatability head `466be943...`.

Reason:
The controlled repeatability matrix rejected the terminal-window method: identical SRS workload/settings produced last-window values 60/60, 59/60 and 53/60 because the >=800-sample stop condition landed at different guest phases. No runtime optimization is justified from those terminal values.

Controlled change:
- `src/profile.S`: add a PROFILE-only 64-byte ordered VI-window history and count **outside the canonical S64P snapshot**, preserving the existing statistical snapshot/hardware format;
- `src/main.S`: under `#ifdef SODIUM64_PROFILE` only, append the just-completed `fps_display` value once at each existing exact 60-VI `update_fps` boundary;
- audition workflow: reset history count together with `fps_native/fps_emulate/fps_display`, then run a fixed **20 host seconds** and read the ordered history plus the normal statistical profile.

No production/release behavior is intentionally changed. The new VI-history write executes only in PROFILE builds and only once per emulated 60-VI window.

Alignment:
The harness already resets `fps_native=0`, `fps_emulate=0` and `fps_display` while the target is stopped immediately before measurement. It now resets `profile_vi_history_count` at the same point. Therefore the first recorded entry is the first full 60-VI diagnostic window after reset; subsequent entries are consecutive internal windows independent of when the host stops.

History capacity:
64 completed 60-VI windows. The current fixed 20-second host observation is expected to produce at least 8; the workflow rejects fewer than 8.

Workload identity remains pinned and unchanged:
- SRS upstream `e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865`;
- benchmark ROM SHA-256 `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`;
- benchmark patch SHA-256 `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`;
- frameskip0 / APU21 / audio4 / precision8;
- normal SRS entity/collision/camera/metatile/animation/script/audio work preserved.

Exact runs:
- **Gate B SRS Audition `35398205311`** @ `bd9f7a75...` — running;
- **Build and Validate `35398205355`** @ same SHA — running.

Question:
What ordered frame-budget pattern does this exact SRS segment produce across consecutive internally aligned 60-VI windows?

Acceptance:
- Build/Validate stays green;
- >=8 consecutive history entries are captured;
- settings remain Road-valid;
- sequence is coherent enough to distinguish startup/transition cost from sustained gameplay.

Falsifier:
- history instrumentation/build fails;
- fewer than 8 internal windows are captured;
- repeated internal sequence later proves unstable even when indexed by the same 60-VI position.

Decision:
Do not choose CPU/APU/DSP/PPU/DMA work from SRS until this phase-aligned sequence is understood. No hardware request.


## Gate-B SRS internal 60-VI history — MEASURED 60/60 sustained in ares lab 2026-09-18

Exact authority:
- diagnostic head **`phase3/gate-b-srs-audition@bd9f7a75518a21563cb62cbce2c5dfd177cc777b`**;
- **Gate B SRS Audition `35398205311` SUCCESS**;
- **Build and Validate `35398205355` SUCCESS** at the same SHA, including normal build, PROFILE build and pinned Mupen smoke;
- non-ROM audition artifact **`10570116759`**, digest **`sha256:4221fb4e6aa103d1987226fc83098a0fb8b10e4c38ed8d38bfb621fa6ee6ddb5`**;
- source-build provenance artifact **`10569901158`**, digest `sha256:afc441006b18a6ccc615f9d8744f281d5c0fe3d6eca1bf60ba22d859a77cda56`.

Workload identity remained exact:
- benchmark ROM SHA-256 `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`;
- benchmark patch SHA-256 `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`.

Road-valid observed settings:
- frameskip 0;
- APU clock 21;
- audio 4;
- precision 8.

The PROFILE-only history captured **15 consecutive internally aligned 60-VI windows**:
**`61,60,60,60,60,60,60,60,60,60,60,60,60,60,60`**.

Interpretation:
- the first 61/60 is a boundary/queue-settling transient after diagnostic counter reset and is not evidence of >native target cadence;
- the following **14 consecutive windows are exactly 60/60**;
- therefore the earlier terminal values 53/60 and 59/60 are **REJECTED as sustained-throughput evidence**. They were artifacts of stopping at different guest phases and reading only the current/last visible counter.
- This exact SRS segment does **not** currently demonstrate a sustained Gate-B throughput blocker in the pinned ares lab.

The fixed 20-s host observation produced 11,230 total statistical samples (4,096 ring-valid). The terminal statistical distribution was dominated by frame/VI wait (**53.32%**) with APU static 25.17%, DSP/audio 7.98%, S-CPU 5.05%, PPU 3.56%, DMA 0.63%, VRAM/RSP wait 0.02%. Treat this as a long aggregate activity profile, not normalized subsystem cost and not real-N64 headroom.

Important non-conclusions:
- ares 60/60 does not prove N64-real 60/60;
- this does not prove broad SRS correctness or that the deterministic input actually traverses all intended gameplay states;
- no hardware request is justified yet;
- no CPU/APU/DSP/PPU/DMA optimization is justified from this result.

Next controlled checks before SRS can become a fixed corpus member:
1. repeat the **internal history metric** in fresh ares processes to verify that the ordered sustained 60/60 pattern itself is reproducible;
2. add a guest-progression/checkpoint observation so a stable 60/60 cannot be produced by a workload that has become stuck in one low-activity gameplay state.

Only after those checks should SRS be locked as the DKC-like/autonomous corpus slot.


## Gate-B SRS internally aligned repeatability — RUNNING 2026-09-18

Exact head:
**`phase3/gate-b-srs-audition@2694c455ba92bace9e644652eb5034f8a88d6961`**.

Diff from first internal-history result `bd9f7a75...`:
- workflow only;
- no Sodium64 source/runtime/instrumentation change;
- no SRS source/benchmark change.

Controlled experiment:
- same pinned benchmark ROM and patch;
- same PROFILE VI-history instrumentation;
- same Road-valid frameskip0/APU21/audio4/precision8;
- same pinned ares lab;
- three fresh ares processes;
- fixed 20 host-second observation each;
- each process resets `fps_native`, `fps_emulate`, `fps_display` and history count together before measurement;
- compare histories by internal 60-VI index, not terminal host stop phase.

Question:
Does the sustained internal sequence itself reproduce across fresh processes?

Interpretation rule:
- exact common-prefix agreement is strongest;
- the first window is tracked separately because queue/reset settling may produce a one-frame transient;
- the sustained common prefix after window 1 is the primary repeatability signal;
- do not fail the workflow merely because a measured window is sub-60; preserve the data and interpret it.

Exact runs:
- **Gate B SRS Audition `35398977369`** @ `2694c455...` — running;
- Build and Validate `35398977413` @ same SHA — queued/running.

If sustained internally indexed windows reproduce at 60/60, the earlier 53/59 terminal-window readings remain rejected and SRS moves to progression/checkpoint validation rather than performance optimization.
If the internally indexed sequences diverge materially, keep SRS measurement methodology OPEN and do not select a blocker or request hardware.
