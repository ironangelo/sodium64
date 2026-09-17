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
