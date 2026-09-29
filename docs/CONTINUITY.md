# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

> **Continuity compaction / recovery (2026-09-28):** the live handoff again grew past the GitHub Contents API comfort boundary (~1.8 MB), which caused normal `fetch_file` reads to return an empty body. The complete pre-compaction Gate-C operational log is permanently preserved at continuity commit **`f175f2151d4adc0a9d0067e1714c649bc9088c66`**. Older pre-overflow history remains preserved at **`686f5a1da210f8fcd1b9cd6e74d5663f4d359c30`**, and the Sep-23–25 E4d block is also in `docs/CONTINUITY_ARCHIVE_E4D_2026-09-23_25.md`. This live file is intentionally compacted to current state, durable evidence, rejected explanations, risks and immediate next action. **Archived means preserved, not discarded.**

## RESUME HERE — current audited state (2026-09-29 UTC)

### L1 CHECKPOINT — repaired loaded-slot ABI accepted; L2 pending (2026-09-29 UTC)

- Exact head `77f4ecf7500e6eae329458ec361c83811283ea5b`, dedicated run `36634304085`, job `109631078101`: self-test/deterministic guests, exact runtime build + assembled source/binary ABI contract + branch-delay checks, and wrapping all eleven guests completed SUCCESS. Artifact/hash readback is still pending job completion.
- This resolves the immediate overflow/helper-entry risk for this candidate: the source estimate survived the actual build contract. It does not establish semantic execution. Runtime-state fence, pinned ares lab and first-hand eight-case repair + three source-control matrix remain required.
- No expansion to other modes/games and no master merge. Next checkpoint must distinguish a semantic mismatch from capture/build/lab limitations using exact first-hand logs/artifact.

### IMPLEMENTATION CHECKPOINT — clip/prevent candidate published; build authority pending (2026-09-29 UTC)

- Exact candidate `phase4/gate-c-hcomp-color-window-repair-clean@77f4ecf7500e6eae329458ec361c83811283ea5b`, tree `b5e5be909abe9851c70f877c9347e9ab9a0465a9`, from diagnostic `9a019599...`. Master unchanged.
- Runtime change confined to `src/rsp_hcomp.S`: retains independent two-pair palette proof and public entry labels; calls identical retained regular/Mode7 window helper before operands are live; stores independent visible/permitted flags. Main clips before math without losing BG1/BG2 winner mask. Effective HALF is computed once after the independent prevent gate, suppressing clipped Main and transparent selected Sub.
- Reclaimed bytes by equivalent source dispatch and unified HALF dispatch; source estimate is 948 active bytes before the 0x1760 switch plus 4 bytes padding. This is an estimate, not assembled ABI authority. Exact maps and delay-slot checks must pass before semantic capture.
- Diagnostic record extended from 28 to 32 bytes with raw Main and window flags. Capture defaults to the original 28 bytes for all three source controls; only eight window cases request 32. Parent oracle gained explicit optional expected Main/gate/extension parameters with unchanged defaults; old diagnostic gap oracle remains separate and passes locally.
- L0: repaired positive fixtures and corrupt effective-Main, gate, HALF, raw-carrier, predicate, queue-layout, geometry and stale-frame fixtures pass/reject as expected; parent source-control and baseline-gap self-tests pass; source carrier/lifetime and new decision contract pass.
- Dedicated workflow initially measures its own exact ROM/ELF hash without borrowing the old runtime pin. Do not close the stage until the first-hand matrix passes and this dedicated measured hash is repinned and rerun. CI SUCCESS alone is not full-frame/window/game correctness.
- Exact-head workflows: `Gate C H-COMP Color Window Sample Repair Clean 36634304085` (in_progress); `Build and Validate 36634304068` (pending); `Build and Validate 36634297568` (in_progress).
- Pending: assembled helper/entry/slot authority, all eleven naturally fenced first-hand captures, local artifact rehash/classifier replay, then exact-build pin checkpoint. Do not expand all16/W2/SMW until this rung closes.

### ACTIVE BATCH — bounded clip/prevent repair, slot-preserving plan (2026-09-29 UTC)

- Refreshed canonical docs and live refs: master remains `7cc8facf...`; diagnostic remains `9a019599...`. The previous eight-case gap and three source controls are the unchanged discriminator.
- Implementation plan: call retained regular `calc_window_spans=0xA4001CE4` after the independent palette-pair proof and before Main/Sub operands are loaded. Its clobbers (t0/t1/t2/t3/t4/t6/t7/t8) are dead there; s0/s1 retain normalized Main-visible / math-permitted decisions through DMA and arithmetic. Resident suffix is not overwritten by the H-COMP slot loader.
- Use selected-span membership at semantic x0 and the primary-reference mode truth table (0=always,1=inside,2=outside,3=never) separately for CGWSEL bits6:7 and4:5. Preserve rendered winner eligibility; clip effective Main before math; suppress HALF on clipped Main or absent selected Sub. TMW/TSW remain independent.
- Space strategy: preserve the palette proof and all fixed public entries. Recover loaded-slot bytes by equivalent source selection and arithmetic dispatch / branch-delay scheduling, with exact assembled maps and delay-slot checks as authority. Reject any overflow or helper entry drift; no use of unloaded leading padding, new surface, or resident IMEM growth.
- Evidence plan: extend only the diagnostic record with raw Main and independently visible window decisions. Keep the original 28-byte source controls available. Require strict repaired semantic acceptance for the same eight cases, actual effective Main/gate/HALF decisions, coherent queues, unchanged raw surfaces/provenance and all three regression controls. Existing gap classifier remains diagnostic-only.
- Still a bounded laboratory sample repair, not full-frame production compositor, SMW validation, real-N64 ownership or Gate-C closure. Record each implementation/run finding before another long experiment.

### STAGE CLOSED — CGWSEL clip/prevent gap isolated by complete first-hand matrix (2026-09-29 UTC)

- **Phase:** M3 / Gate C remains ACTIVE. **Closed stage:** deterministic color-window **isolation / COMPATIBILITY DIAGNOSTIC**, not the runtime repair and not Gate C.
- **Integrated truth:** `master@7cc8facfe8643fb85888f301f79995575830521d` remains unchanged. **Current diagnostic candidate:** `phase4/gate-c-hcomp-color-window-clean@9a019599f3a5a5aafa4ffed7dd8b1135db42d809`. No runtime source is changed or merged by this stage.
- **Exact-head generic:** Build and Validate `36629523185 SUCCESS` (normal, PROFILE, branch-delay checks and Mupen/LLE smoke).
- **Exact-head dedicated:** Gate C H-COMP Color Window Isolation Clean `36629523682 SUCCESS`; artifact `11062067939`, digest `sha256:0abecf86f0a87b958cd261aefdf1c7b244d037afb4cea38083bf79ffe57e8fe8`. Downloaded/rehashed locally; both dedicated classifiers rerun directly on the artifact and their full JSON outputs match CI exactly.
- **Runtime authority unchanged:** ROM `44e6ce2bf864716d96dfa4fb6c1d15ac59839119ca0c6a0afa36df1bf0575665`; ELF `2a3ae06e5ab446c502dfaa987511cbbf06d47d379293d4fcc69e42b0608c45b9`. Regular/Mode7 text 0x1000 each, H-COMP 0x790, public ABI and resident IMEM unchanged.
- **Classification:** `HCOMP_COLOR_WINDOW_GAP_REPRODUCED`, passed=true, **runtime_color_windows_validated=false**. Diagnostic SUCCESS means the exact missing semantics were reproduced. It must never be presented as a color-window correctness pass.
- **All 11 independent captures complete:** eight window cases + three frozen transparent-Sub controls. Every window case has guest_frame_delta=1, one renderer re-entry, RSP HALT, bufferBusy=false, DPC_CURRENT=DPC_END=0xC10, exact bounded 8/224 geometry and intact provenance guards. No searched RDP crash/TLUT hardware/cache-coherency diagnostics occur.
- **Both queue copies agree** in every window case: WOBJSEL=20, WOBJLOG=0, W1[0,0] or W1[1,1], W2 disabled, TMW=TSW=0, requested raw CGWSEL. Raw Main red `001F`, Sub green `03E0`, BG1 Main provenance `0C00/01`, Sub presence `1400/1`, selected live Sub and HALF flags remain invariant. Canonical Main/Sub surfaces and guarded provenance are byte-identical across cases, allowing physical framebuffer slot rotation.

| Case at semantic x0 | CGWSEL | Reference RGB555 | Measured RGB555 | Reading |
|---|---:|---:|---:|---|
| control inside | 02 | 01EF | 01EF | control agrees |
| control outside | 02 | 01EF | 01EF | control agrees |
| clip inside | 82 | 03E0 | 01EF | Main clipping + HALF suppression missing |
| clip outside | 82 | 01EF | 01EF | outside control agrees |
| prevent inside | 22 | 001F | 01EF | independent math prevention missing |
| prevent outside | 22 | 01EF | 01EF | outside control agrees |
| clip+prevent inside | A2 | 0000 | 01EF | combined decision missing |
| clip+prevent outside | A2 | 01EF | 01EF | outside control agrees |

- **MEASURED conclusion:** this clean H-COMP sample path ignores CGWSEL clip/prevent despite correctly delivered color-window state. This is no longer a missing-state/guest/queue hypothesis. The synthetic mismatch is isolated at the H-COMP decision/arithmetic boundary.
- **Controls retained:** direct fixed+HALF `3C0F`; live Sub+HALF `01EF`; truly absent Sub fixed fallback with HALF suppressed `7C1F`. The three-state classifier remains `HCOMP_TRANSPARENT_SUB_HALF_SUPPRESSION_VALIDATED`.
- **Harness repair outcome:** the process-group cleanup rerun completes all cases, and final job logs contain no orphan-process cleanup lines. This supports resource contention from surviving ares children as the earlier warmup-timeout explanation; it does not establish a general ares timing defect. Keep per-case full-session cleanup for larger matrices.
- **Host false-negative risk closed:** WHX=46 and WOBJSEL=52 now match independently derived header offsets and first-hand queues. Explicit old-offset mutations are rejected independently of fixtures. Do not return to shared-constant-only ABI tests.
- **Still NOT PROVEN:** repaired clip/prevent execution, all 16 CGWSEL mode pairs, W2/invert/combine behavior on the H-COMP path, full-band/full-frame output, final brightness ordering, SMW iris correctness, ALttP compositor correctness, production-safe real-N64 RDP->RSP ownership and final cadence.
- **Immediate next gate driver:** implement a bounded H-COMP clip/prevent decision from these frozen controls; clip Main before math, retain original winner eligibility, independently gate math, and suppress HALF for clipped Main as well as transparent selected Sub. Respect the loaded overlay slot and audit every helper clobber. Rerun the same eight-case semantic oracle plus the three source controls with new exact-build authority before expanding to other modes or SMW.
- **Architecture constraint retained:** H-COMP only loads IMEM 13A8..178F. Leading padding is not executable owned space. Existing retained regular `calc_window_spans=0xA4001CE4` may be reused if preservation and slot budget are proved; do not silently grow resident IMEM, move public ABI, allocate a new pixel surface, or resurrect cumulative compositor branches.
- **STOP / CHECKPOINT:** color-window isolation stage is CLOSED; runtime repair is TODO. Road/roadmap milestones are unchanged.


### RERUN CHECKPOINT — same runtime and guests; host lifecycle/ABI repaired (2026-09-29 UTC)

- Exact head `phase4/gate-c-hcomp-color-window-clean@9a019599f3a5a5aafa4ffed7dd8b1135db42d809`. Relative to `c2d2502...`, only the host classifier and dedicated workflow change. No runtime, guest generator, arithmetic, screen ownership, provenance, fence or public ABI change.
- Exact-head runs: `Gate C H-COMP Color Window Isolation Clean 36629523682` (in_progress); `Build and Validate 36629523185` (in_progress).
- Per-case ares/Xvfb processes now belong to a dedicated process group; TERM/wait/bounded cleanup prevents prior captures from consuming resources during later ones. Group cleanup also runs on workflow failure.
- Classifier offsets now match the runtime header independently: WHX=46, WOBJSEL=52, WOBJLOG=54. Local positive/negative fixtures and all four complete first-attempt captures pass the corrected host checks.
- Question/acceptance unchanged: require three frozen source controls plus eight naturally fenced first-hand window captures. All eight baseline results must remain `01EF`; only clip-inside/prevent-inside/both-inside must disagree with primary-reference `03E0/001F/0000`. Runtime hash must remain `44e6ce2b...`; broad/window correctness must stay false.
- On SUCCESS, close **color-window isolation** only; then implement one bounded runtime clip/prevent/HALF repair. On failure, inspect the exact first failed case and preserve partial artifact authority without calling the whole matrix complete.


### FIRST-HAND PARTIAL RESULT — clip omission reproduced; capture lifecycle repaired (2026-09-29 UTC)

- Exact first attempt `c2d2502e8dab3720205ffde1e9bc66fec4c2ea21`: generic `36627582887 SUCCESS`; dedicated `36627582947 FAILURE`. Artifact `11061313513`, digest `sha256:f9732bf5a92b0ea0e492a02cae7a35df37ae8c9222bd5061676d202f2fd16894`, downloaded/rehashed locally.
- **MEASURED partial authority:** the three frozen transparent-Sub controls passed. Four window guests (control inside/outside and clip inside/outside) completed exact fresh-frame fences, healthy surfaces/provenance/guards, correct geometry and raw CGWSEL. Both queues carry WOBJSEL=20, WOBJLOG=0, W1[0,0] or [1,1] exactly.
- **MEASURED clip-inside discrepancy:** requested CGWSEL=82 still gives mailbox `001F 03E0 01EF 0001 0C00 0001 0041 0000 7C00 03E0 0082 0101 1400 0001`. Reference requires `03E0`, not `01EF`, because Main must clip to black and suppress HALF. Clip-outside and both unconditional controls correctly remain `01EF`.
- **LAB LIMITATION / incomplete matrix:** prevent-inside timed out in GDB warmup at guest_counter=0; no fenced capture exists for it or the three later cases. Its ares log contains shader-compilation stall warnings but no measured semantic result. This is not evidence of a prevent-math runtime failure.
- **Harness lifecycle defect:** old inherited run_case killed only the xvfb-run wrapper. Final CI cleanup found eight orphan Xvfb/ares pairs, proving prior emulator children survived each case. Resource contention is a leading explanation for the late warmup timeout, not yet a proved cause. Controlled repair launches each case in its own session/process group, terminates the entire group before the next, and adds failure cleanup. Guest/runtime/oracle semantics remain frozen.
- **Classifier defect corrected before interpretation:** initial new classifier used WHX=44 and WOBJSEL=50; actual source/header and first-hand queue give WHX=46, WOBJSEL=52, WOBJLOG=54, CGWSEL=55. The fixtures shared the wrong offsets, so self-test alone did not catch this. Added an independent header-derived ABI check. Corrected classifier now accepts all four complete first-hand captures, including both coherent queue copies. This was a host false-negative risk, not broken window transport.
- **REJECTED:** placing helper in unloaded leading H-COMP padding; interpreting the partial GDB timeout as clip/prevent semantics; treating fixture success as sufficient section-layout authority.
- **Next:** rerun the same strict eight-state baseline with process-group cleanup and corrected classifier/header contract. The full isolation stage remains OPEN until all eight first-hand cases and the three source controls complete.


### CONTROLLED BASELINE — color-window discriminator published; runtime frozen (2026-09-29 UTC)

- **Exact candidate:** `phase4/gate-c-hcomp-color-window-clean@c2d2502e8dab3720205ffde1e9bc66fec4c2ea21`, from validated `5e84c809...`. Changes only three host files: deterministic eight-case guest generator, strict gap classifier, dedicated workflow. Sodium64 runtime is byte-for-byte unchanged; dedicated ROM pin remains `44e6ce2bf864716d96dfa4fb6c1d15ac59839119ca0c6a0afa36df1bf0575665`.
- **Decision / controlled experiment:** run the missing-window baseline before implementing a repair. This separates state-capture/guest/window topology defects from the known H-COMP omission. The planned runtime predicate is deferred until first-hand evidence isolates that omission.
- **Layout audit:** H-COMP loader copies only IMEM `0x13A8..0x178F` (0x3E8 bytes). Leading `0x1000..0x13A7` padding is NOT loaded and cannot safely host a new helper just because it appears free in the H-COMP ELF. Remaining loaded tail padding is only 0x58 bytes. **REJECTED implementation plan:** placing the color-window helper in leading H-COMP padding without changing overlay ownership. Existing regular resident `calc_window_spans=0xA4001CE4` is available beyond the overlay slot, but invoking it requires preserving its audited caller-clobber contract and accounting for bounded loaded-slot space. Do not grow resident IMEM or silently move public entries.
- **Guest controls:** new setup occupies verified unused startup padding `$81A0..$81C8`, called through inherited frozen `$81F0` hook. NMI remains `$8200`; the original TS HDMA table and 8/224 split remain unchanged. No commercial ROM bytes. Generator permits diffs only in these hook slots and checksum.
- **Strict baseline expectation:** all eight observed mailboxes remain the parent's exact live-Sub result `01EF`, with raw CGWSEL matching each guest and both queue copies proving WOBJSEL=20, WOBJLOG=0, exact singleton bounds, TMW/TSW=0 and bounded geometry. Only three inside states differ from the independent primary-reference oracle (`03E0 / 001F / 0000`); all five controls agree.
- **Classification must be** `HCOMP_COLOR_WINDOW_GAP_REPRODUCED` with `runtime_color_windows_validated=false`. Workflow success means a bug was reproduced, not semantic correctness. Any different arithmetic, carrier, guard, geometry or queue outcome fails this baseline rather than being relabeled convenient evidence.
- **L0 VALIDATED:** deterministic guest construction, positive and corrupt-capture classifier fixtures, reference-vs-precommitted eight-state matrix, parent transparent-Sub classifier and source/ABI contract pass locally. Corrupt window selector, HALF flag, section bound and stale-frame fixtures are rejected.
- **Running exact-head workflows:** `Gate C H-COMP Color Window Isolation Clean 36627582947` (in_progress); `Build and Validate 36627582887` (in_progress).
- **Long experiment handoff:** question is whether both delivered queues preserve the requested color window while H-COMP arithmetic ignores it. Accept only frozen runtime hash + healthy three-state transparent-Sub regression + eight coherent first-hand captures. If geometry/state fails, repair guest/harness first; if arithmetic differs, inspect exact first-hand evidence before touching runtime. If the precommitted gap reproduces, close the isolation stage and prepare one bounded clip/prevent repair.


### ACTIVE BATCH — CGWSEL color-window semantic audit and precommitted discriminator (2026-09-29 UTC)

- **Authority refreshed:** master is still `7cc8facfe8643fb85888f301f79995575830521d`; no open PRs. Validated parent is `5e84c8095bdce0385a8832cccec47d41521cc9b6`. Exact-head dedicated `36580550081` and generic `36580550048` are both SUCCESS.
- **GATE DRIVER / source-audited gap:** CPU section capture already transports WOBJSEL, WOBJLOG, WH0..WH3 and CGWSEL losslessly and changed writes request raster-sensitive sections. The clean H-COMP sample path reads only CGWSEL bit1; it does not yet consume clip bits7:6 or prevent bits5:4. Existing color-window host tests exercise legacy backdrop segmentation, not this winner-dependent H-COMP decision.
- **Primary reference re-read:** pinned ares `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`, `ares/sfc/ppu-performance/{io,window,dac}.cpp`. Color selector is WOBJSEL high nibble, logic WOBJLOG bits3:2; inclusive WH0..WH3 intervals, inversion and OR/AND/XOR/XNOR; no enabled window means selected=false. CGWSEL aboveMask=bits7:6, belowMask=bits5:4; both encode ENABLE modes 0=always,1=inside,2=outside,3=never.
- **SUPPORTED semantic order:** clip Main to black before math, independently prevent math while retaining the clipped/unclipped Main, retain original winner eligibility after clipping, and suppress HALF when Main is clipped. This adds a second HALF-suppression cause beyond already-validated transparent Sub. Layer TMW/TSW do not gate the color window.
- **Precommitted smallest first-hand matrix:** freeze live BG1 red `001F`, live BG2 green `03E0`, fixed blue `7C00`, CGADSUB `41`, TS presence `1400/1`, bounded 8/224 geometry and provenance. Test control `CGWSEL=02`, clip-inside `82`, prevent-inside `22`, and both `A2`, each with sample x0 inside singleton W1[0,0] or outside W1[1,1], WOBJSEL=20, WOBJLOG=0, TMW=TSW=0.
- **Exact results:** control inside/outside `01EF`; clip-only inside `03E0` (black+Sub, HALF suppressed), outside `01EF`; prevent-only inside raw Main `001F`, outside `01EF`; both inside `0000`, outside `01EF`. Require raw rendered Main/Sub/provenance unchanged, exact queued window controls, original Main evidence, effective Main, normalized window flags, math gate and HALF flags.
- **Planned controlled candidate:** reuse unused leading H-COMP fixed-slot padding for a scalar color-window predicate for the existing x0 sample, preserve public ABI and resident IMEM. No new pixel surface; no full-frame compositor or SMW correctness claim. Add reference-backed host edge coverage and strict first-hand ares evidence before declaring this rung validated.
- **Historical compatibility boundary:** SMW iris remains the Road target, not a measured success. Archived semantic audit confirms the same clip-before-math/HALF ordering; none of the synthetic results establish the commercial iris fix.
- **Immediate action:** implement this isolated sample decision and deterministic eight-case guest/oracle, run lower-level gates and exact-head ares. Preserve transparent-Sub controls. Real hardware remains final RDP/RSP and cadence authority.



### CHECKPOINT — transparent-Sub fixed fallback + pixel-local HALF suppression VALIDATED (2026-09-29 UTC)

- **Stage:** M3 / Gate C H-COMP source-selection special case is **VALIDATED in the pinned ares architecture lab**. Exact candidate head: `phase4/gate-c-hcomp-transparent-sub-clean@5e84c8095bdce0385a8832cccec47d41521cc9b6`. `master` is not changed by this checkpoint.
- The final change from `0ac4507...` is guest-only: exactly one modified file, `scripts/make_gate_c_hcomp_transparent_sub.py` (+14/-2). Sodium64 semantic runtime is unchanged; exact dedicated runtime hash remains `44e6ce2bf864716d96dfa4fb6c1d15ac59839119ca0c6a0afa36df1bf0575665` for `sodium64.z64`.
- **Generic hygiene:** Build and Validate `36580550048 SUCCESS`; normal build, PROFILE build, RSP branch-delay checks and emulator smoke all passed.
- **First-hand authority:** dedicated `36580550081 SUCCESS`; artifact `11039832437`, digest `sha256:5cc42461f6eddd9b508afea12d54e04f2b7b10ea11b237365c65055971fd66e6`. Result classification is exactly `HCOMP_TRANSPARENT_SUB_HALF_SUPPRESSION_VALIDATED`.
- **Direct fixed + HALF control:** Main `0x001F`, selected fixed `0x7C00`, source code 0, HALF effective, TS tag/presence `0x1400/1`, exact result `0x3C0F`.
- **Live Sub present + HALF control:** Main `0x001F`, selected live Sub `0x03E0`, source code 1, HALF effective, TS tag/presence `0x1400/1`, exact result `0x01EF`.
- **Live Sub selected but transparent:** Main `0x001F`, TS stays **0**, saved TS tag/presence is `0x0400/0`, selected operand falls back to fixed `0x7C00`, source code 2, HALF is **suppressed**, exact full-add result is `0x7C1F`.
- The repaired absent guest now has the same bounded geometry as the controls: exactly `TS=0 split=8 -> TS=0 split=224`; both queue copies agree. Compact Sub active pixels are the expected blue backdrop `0x003F` with only the 192 border words left at sentinel `0x55AA`. Main provenance is identical across all three states and both provenance guards remain intact.
- Fresh-frame/fence controls pass in all three states: one guest-frame delta, one renderer re-entry, RSP HALT, `bufferBusy=false`, and `DPC_CURRENT==DPC_END==0xC10`. Pinned ares still reports the known sticky `PIPE_BUSY` behavior; this is not used as completion authority.
- **Rejected prior interpretation:** the `0ac4507...` all-sentinel absent Sub surface / `0x56CA` raw sample did **not** prove that the strict color oracle was stale. It was a consequence of the guest's extra zero-height line-0 section. Resetting WH0 in VBlank removes that section and restores the original strict blue-surface expectation without changing runtime semantics.
- **Architecture result:** the existing compact Z16 TS winner tag is sufficient as the present-vs-transparent carrier for this rung; no new per-pixel surface is required. Direct fixed, live Sub, transparent-Sub fixed fallback, and HALF-effective/suppressed behavior now agree with the precommitted oracle.
- **Still NOT PROVEN:** CGWSEL clip/prevent/color-window semantics, broad software compatibility, and the proof bridge's RDP->RSP readback/fencing on real N64. The H-COMP path remains architecture/proof evidence, not a claim that the full production compositor is finished.
- **STAGE CLOSED. Immediate next gate-driving rung:** isolate and validate CGWSEL clip/prevent + color-window behavior, using the known SMW iris/window/color-math regression as the representative target while freezing all source/HALF/provenance controls validated here.




### CONTROLLED GUEST REPAIR — restore WH0 in NMI so line-0 write is inert (2026-09-29 UTC)

- Exact candidate head **`phase4/gate-c-hcomp-transparent-sub-clean@5e84c8095bdce0385a8832cccec47d41521cc9b6`** changes only the transparent-Sub guest generator; Sodium64 semantic runtime remains unchanged.
- Source audit resolved the leading zero-height section from **`0ac4507...`**. Sodium64 **`write_wh0`** compares old/new values and calls **`update_window_frame` only on an actual change**, so repeated WH0=0 writes are inert.
- The prior guest ended each frame with WH0=1 (from the post-line8 HDMA payload) but its NMI still patched the inherited TS restore into **TS=0**. Therefore the next frame's first HDMA transfer changed WH0 **1->0 at line0**, deterministically generating the measured **split=0** record before the intended line8 split.
- The repair keeps startup **TS=0**, but repurposes the inherited same-size NMI instruction slot to **WH0=0**. The startup proof hook still initializes WH0=0 for the first frame. Thus the first per-frame HDMA write of 0 should be a no-op and the only raster-sensitive transition should be WH0 **0->1 at line8**.
- **Expected:** absent queue becomes exactly **`TS=0 split=8 -> TS=0 split=224`** with no leading zero-height record, while raw TS tag **`0x0400`**, presence 0, selected fixed **`0x7C00`**, source/HALF **`0x0002`** and final **`0x7C1F`** remain unchanged. The stale absent-color oracle is intentionally not changed in this batch, so the dedicated workflow may still end red after producing usable evidence.
- **Falsifiers:** split=0 remains; TS becomes nonzero; the line8 bound disappears; present controls or runtime hash change; or semantic mailbox evidence regresses.
- **Static control-flow confirmation:** NMI runs during VBlank; `write_wh0` marks raster state dirty only on the real 1->0 reset, and `vblank_end` then clears **`sect_status`** before **`section_init`** / visible line0. Therefore the NMI reset cannot itself create a visible zero-height section. At visible line0 the HDMA WH0=0 write compares equal and is inert; the first possible visible split is the intended line8 0->1 edge.
- **HYGIENE MEASURED:** exact-head generic **Build and Validate `36580550048` SUCCESS**; normal build, PROFILE build, RSP branch-delay checks and emulator smoke all passed. This guest-only repair does not regress the generic runtime validation surface.





### FIRST-HAND RESULT — WH0 restores the 8-line bound, but the strict oracle is stale and a zero-height split remains (2026-09-29 UTC)

- Exact candidate head **`phase4/gate-c-hcomp-transparent-sub-clean@0ac4507d15beafad103d43c7ae7380990fb5944b`**; Sodium64 semantic runtime remains **`712766f39cb6ffd94709d70bbbbf0cb0e24f21ca`** and generic **Build and Validate `36527516094 SUCCESS`** is green.
- Dedicated **`36527516097 FAILURE`**, artifact **`11015427350`**, digest **`sha256:7d829bcc6a5901759922771db272cc2a2cf68dc701342a23500d149fe48f6f20`**. The failure occurs only in the classifier's old absent-Sub color-surface expectation; capture/build/ABI/fresh-frame gates all completed.
- **MEASURED semantic closure candidate:** fixed-half mailbox is exact **`001F 03E0 3C0F 0001 0C00 0001 0041 0000 7C00 7C00 0000 0100 1400 0001`**; sub-present-half is exact **`001F 03E0 01EF 0001 0C00 0001 0041 0000 7C00 03E0 0002 0101 1400 0001`**; truly absent is **`001F 56CA 7C1F 0001 0C00 0001 0041 0000 7C00 7C00 0002 0002 0400 0000`**. Thus the absent state has exact fixed fallback, HALF suppressed, raw backdrop tag **`0x0400`**, presence 0 and final result **`0x7C1F`**.
- In the absent state the compact Sub color surface is intentionally untouched: **2240/2240 words remain sentinel `0x55AA`**. Its raw sampled RGB mailbox word becomes **`0x56CA`** after the existing RGBA5551->RGB555 conversion. This is consistent with the already-audited rule that Sub color is not the presence authority; Z/tag metadata is. The current classifier comment says this, but still incorrectly requires an opaque blue Sub surface and therefore rejects before inspecting the valid mailbox.
- **MEASURED queue nuance:** fixed and present controls remain exactly **split 8 -> 224**. The absent guest now records **`TS=0 split=0 -> TS=0 split=8 -> TS=0 split=224`**. The leading zero-height record is caused by the explicit WH0 initialization/update path; the desired [0,8) bound is nevertheless restored and no 224-line proof-surface overrun occurs.
- **Interpretation:** runtime source/HALF semantics are supported strongly, but the rung is not yet VALIDATED because the oracle must be corrected and the zero-height section must be proven harmless or removed without changing the runtime result. Do not weaken raw-tag/source/result requirements.
- **Immediate next action:** audit the section/proof control flow for the zero-height record. Prefer removing the redundant line-0 WH0 split if a guest-only change can do so safely; otherwise teach the strict queue oracle to accept exactly one leading zero-height inert record while still requiring the bounded [0,8) and [8,224) sections. Separately change absent Sub surface expectation from blue to untouched sentinel and require the mailbox's raw Sub sample to match that sentinel-derived value. Then rerun the unchanged semantic runtime and strict three-state oracle.





### CONTROLLED HARNESS REPAIR — inert WH0 split restores 8-row proof geometry (2026-09-29 UTC)

- Exact branch head **`phase4/gate-c-hcomp-transparent-sub-clean@0ac4507d15beafad103d43c7ae7380990fb5944b`** changes only the transparent-Sub guest generator; Sodium64 runtime remains **`712766f39cb6ffd94709d70bbbbf0cb0e24f21ca`** and the Sync Full readback fence/oracle are unchanged.
- For `sub-absent-half`, startup/NMI TS remain forced to **0** for the whole frame. The inherited HDMA channel is now retargeted from **TS ($212D)** to **WH0 ($2126)**, and its transfer data is **0 for lines 0..7, 1 thereafter**.
- `TSW=TMW=0` throughout this discriminator, so WH0 is semantically inert for rendering/color math; its only intended effect is the existing raster-sensitive `write_wh0 -> update_window_frame` split at line8. The guest also explicitly initializes WH0=0 inside the already-unused proof-hook padding without moving the frozen NMI address.
- This restores the audited compact proof geometry **[0,8)** while keeping the subscreen truly absent. The expected delivered queue returns to `TS=0 split=8 -> TS=0 split=224`, so the existing strict queue oracle can remain unchanged.
- **Expected first-hand closure:** absent compact Sub is blue backdrop in the bounded first section, raw TS tag **`0x0400`**, source flags **`0x0002`**, selected fixed **`0x7C00`**, Main BG1 red **`0x001F`**, and full (HALF-suppressed) result **`0x7C1F`**. Present controls must remain `0x1400/0x0100/0x3C0F` and `0x1400/0x0101/0x01EF`.
- **Falsifiers:** WH0 unexpectedly affects pixels despite disabled windows; absent queue does not split exactly at 8/224; carrier/source/HALF/result drift; or generic runtime CI regresses.



### CONTROLLED HARNESS REPAIR — absent TS stays zero; WH0 preserves the 8-line proof section (2026-09-29 UTC)

- Exact branch head **`debe608d1cbae43645015dd4d177971208154334`** changes only the transparent-Sub guest generator. Sodium64 runtime remains frozen at semantic **`712766f39cb6ffd94709d70bbbbf0cb0e24f21ca`**.
- For `sub-absent-half`, startup writes TS=0 and HDMA is retargeted from **TS $212D** to **WH0 $2126**. Its payload is **0 for visible lines 0..7 and 1 thereafter**, creating exactly one line-8 register transition while TMW/TSW remain disabled. The former NMI TS write is repurposed, same size, to restore WH0=0 before each frame.
- Generator guards require no remaining literal TS=BG2 write, no HDMA destination targeting TS, exact inherited table length (224 lines), and exact WH0 payload shape.
- Purpose: restore the original bounded 280x8 proof geometry without ever enabling a real Sub layer. This addresses the measured `d7ee313...` 224-line scratch overrun while preserving the already-correct `0400 / presence0 / source0002` semantic evidence.
- Exact-head workflows **Build and Validate `36527451478`** and dedicated **`36527451444`** are queued/running. Acceptance remains the original strict three-state oracle; no runtime/oracle weakening is authorized.



### FIRST-HAND TRUE-ABSENT RESULT — absence tag is correct; 224-line proof surface overruns (2026-09-29 UTC)

- Exact host-only guest-repair head **`phase4/gate-c-hcomp-transparent-sub-clean@d7ee3131685f14203c45df8bd3c64713018481a2`**; Sodium64 semantic runtime remains **`712766f39cb6ffd94709d70bbbbf0cb0e24f21ca`** with ROM pin **`44e6ce2bf864716d96dfa4fb6c1d15ac59839119ca0c6a0afa36df1bf0575665`**.
- Dedicated **`36526333753 FAILURE`**, artifact **`11014543976`**, digest **`sha256:9d8d58f1fcb3d1e6331cf2b7f921309bc8249198b528d75910d00a5f99593010`**. Same-head generic **`36526333725 SUCCESS`** (build, PROFILE and pinned Mupen/LLE smoke all green).
- **The harness repair worked:** first-hand queue authority for `sub-absent-half` now begins **CGWSEL=0x02, CGADSUB=0x41, TS=0x00, TM=0x01, split=224**. There is no current-frame TS=BG2 interval before the final visible split.
- **Critical MEASURED result:** the saved TS carrier is exact **`0x0400`**, normalized presence is **0**, selected operand is exact fixed blue **`0x7C00`**, and source/half flags are exact **`0x0002`**. Therefore the runtime already distinguishes true Sub absence, selects fixed COLDATA, and suppresses HALF correctly. The Sync Full readback fence plus bounded Z carrier are working for both presence (`0x1400`) and absence (`0x0400`).
- The remaining failure is a **proof-surface geometry defect**, not source/HALF semantics. With no raster split until line224, the test drives a full-height section while the clean compact Sub color/Z proof surfaces were deliberately sized for only **8 rows**. The renderer keeps the compact Sub Color Image active through the first semantic-screen pass; a 224-line section therefore overruns the proof surface before TM. Artifact evidence is diagnostic:
  - compact Sub active 256px region becomes **`0x0C00`** (the BG1 provenance tag) on all 8 captured rows, while the 24 border pixels remain blue `0x003F`;
  - handed Main sample canonicalizes from the same `0x0C00` to `0x0201`, giving a meaningless arithmetic result `0x7E01`;
  - provenance itself remains exact BG1 `0x0C00`; no RDP crash/TLUT/cache-coherency diagnostics occur.
- **Supported interpretation:** making the absent guest one 224-line section exceeded the deliberately bounded clean proof arena. This does **not** falsify transparent-Sub fallback/HALF suppression; the raw carrier/source/HALF evidence actually moved in the expected direction.
- **Next controlled harness repair:** keep TS=0 for the entire frame but reintroduce the original **8-line section boundary using a raster-sensitive register that is semantically inert for this test** (window coordinates while TSW/TMW are disabled). This preserves the 8-row proof bound without re-enabling a Sub layer. Then rerun the unchanged runtime and strict raw-tag/source/result oracle.



### FIRST-HAND TRUE-ABSENT RESULT — semantics correct, proof geometry lost when TS HDMA became inert (2026-09-29 UTC)

- Exact guest-only head **`d7ee3131685f14203c45df8bd3c64713018481a2`**, dedicated **`36526333753 FAILURE`**, artifact **`11014543976`**, digest **`sha256:9d8d58f1fcb3d1e6331cf2b7f921309bc8249198b528d75910d00a5f99593010`**. Same-head generic **`36526333725 SUCCESS`**.
- All three guests reached the established fresh-frame capture fence; all ares logs contain zero RDP crash, TLUT hardware-bug and cache-coherency diagnostics.
- Present controls remain exact and unchanged:
  - fixed-half: `001F 03E0 3C0F 0001 0C00 0001 0041 0000 7C00 7C00 0000 0100 1400 0001`;
  - sub-present-half: `001F 03E0 01EF 0001 0C00 0001 0041 0000 7C00 03E0 0002 0101 1400 0001`.
- **Critical semantic evidence in the truly absent state:** despite later geometry corruption, the mailbox's second-operand metadata is already exact: selected fixed **`0x7C00`**, CGWSEL **`0x0002`**, source/HALF **`0x0002`**, raw TS tag **`0x0400`**, normalized presence **0**. Thus the current runtime carrier + Sync Full fence does distinguish real Sub presence from absence and selects fixed color with HALF suppressed.
- The absent mailbox begins `0201 0201 7E01 ...`: Main/Sub samples and final arithmetic are corrupted because the harness repair accidentally removed the section0 line-8 boundary. Queue evidence shows the absent guest now has **TS=0, split=224** for its first real section instead of the proof's required 8-line compact geometry.
- Correspondingly, absent `sub.bin` is no longer a bounded 280x8 color proof: histogram **2048 × `0x0C00` + 192 × `0x003F`**, consistent with the 224-line section overrunning/reusing the compact scratch. This is a harness geometry failure, not evidence against transparent-Sub semantics.
- **Classification: HARNESS GEOMETRY DEFECT / semantic core supported but rung not yet VALIDATED.**
- **Next controlled repair:** keep TS identically 0 in the absent mode, but retarget its inherited direct-HDMA channel from TS to an otherwise-disabled window coordinate (WH0) and use a harmless **0 for lines 0..7, 1 thereafter** stream. With TMW/TSW disabled this should recreate exactly the line-8 section boundary without enabling a Sub layer or changing visible semantics. Reset WH0 to 0 in NMI using the same-size instruction slot. Keep runtime/oracle/raw-tag requirements frozen.
- **Expected:** absent queue returns to section0 split=8 + section1 split=224 while TS remains 0 in both; compact Sub stays bounded, raw tag remains `0400`, source/HALF remains `0002`, Main returns `001F`, selected remains `7C00`, final result becomes exact `7C1F`.
- **Falsifiers:** any TS=2 appears; WH0 creates visible/window masking despite TMW/TSW=0; raw tag/source/HALF regress; or fixed/sub-present controls change.



### ROOT CAUSE FOUND — “sub-absent” guest was re-enabling BG2 via inherited HDMA (2026-09-29 UTC)

- First-hand artifact audit of **`10999050231`** resolved the apparent stale-tag contradiction. The generated `sub-absent-half` ROM patches the two explicit TS=BG2 writes (startup + NMI) to TS=0, **but it inherits the base lifetime guest's direct-HDMA TS table unchanged**.
- Exact bytes at guest table address **$B000** are identical in all three generated ROMs: **`FF 02 02 02 02 02 02 02 02 00 ...`**. The eight leading data bytes rewrite **TS=$02 (BG2)** during exactly the first eight visible lines / measured section0.
- Therefore the dedicated result **`raw TS tag=0x1400`** in the nominal “sub-absent” case is **correct for the guest that actually executed**. It is not stale Z, not a failed Sync Full fence, and not evidence that the runtime ignored TS=0.
- This also explains the otherwise contradictory artifact: the queue/startup state could show TS=0 while raster HDMA re-enabled BG2 in the measured band.
- **REJECTED interpretation:** “absence baseline is not written and 0x1400 is stale prior-frame metadata” is rejected by the guest construction audit.
- **MEASURED support retained:** Sync Full/PIPE_BUSY converted the two valid BG2-present cases from sentinel `0x55AA` to exact `0x1400`, with no RDP crash/coherency diagnostics. Do not change runtime yet.
- **Immediate controlled repair:** change only `scripts/make_gate_c_hcomp_transparent_sub.py` so `sub-absent-half` also zeros the inherited first-eight-line TS HDMA payload. Keep fixed-half and sub-present-half byte-identical, keep runtime/oracle/capture fence unchanged, and add a deterministic generator assertion that the absent ROM contains no BG2 re-enable in that HDMA band.
- **Expected after guest-only repair:** absent compact Sub shows backdrop/fallback rather than BG2, raw TS tag `0x0400`, presence=0, source code=2 with HALF suppressed, result `0x7C1F`. If not, only then return to runtime carrier investigation.



### CONTROLLED HARNESS REPAIR — absent guest neutralizes inherited TS HDMA (2026-09-29 UTC)

- Exact branch head **`phase4/gate-c-hcomp-transparent-sub-clean@d7ee3131685f14203c45df8bd3c64713018481a2`** changes **only** `scripts/make_gate_c_hcomp_transparent_sub.py`; Sodium64 runtime/source and the validated Sync Full readback fence are unchanged.
- The `sub-absent-half` generator now preserves the inherited HDMA table's block headers/length but forces every transferred TS byte to **0**, after verifying the ROM still contains the exact expected parent table. Startup and NMI TS writes remain patched to 0 as before.
- Purpose: remove the accidental `TS=2` [0,8) interval and the zero-height `TS=0 -> TS=2` section split so this case finally tests a genuinely transparent/absent subscreen.
- **Expected:** no section in the absent guest may advertise TS/BG2; the saved TS carrier should now reveal whether the existing proof path actually establishes an absence value when no Sub layer renders. Present controls must remain `0x1400` and unchanged.
- **Falsifiers:** any TS=2 section remains in the absent capture; present controls change; runtime hash/ABI unexpectedly changes; or the repaired guest cannot reach the same capture fence.
- Exact-head dedicated **`36526333753`** and generic **`36526333725`** were queued at checkpoint time.



### HARNESS CAUSE FOUND — “sub-absent” guest was not actually absent (2026-09-29 UTC)

- First-hand section-queue audit of artifact **`10999050231`** exposes a deterministic guest-construction defect that the classifier had not reached because it failed earlier on the Sub surface.
- Present controls are as intended: section0 **TS=2 split=8**, section1 **TS=0 split=224**.
- The supposed **`sub-absent-half`** guest is different: section0 **TS=0 split=0**, section1 **TS=2 split=8**, section2 **TS=0 split=224**.
- Root cause is in `make_gate_c_hcomp_transparent_sub.py`: the absent variant patches the two literal startup/NMI `LDA #$02; STA $212D` writes to zero, but inherits `build_hdma_ts_table()` unchanged from the lifetime guest. That HDMA table still writes **TS=BG2 for the first eight visible lines** and then TS=0.
- Because the first section has zero height, `k0` remains 0 entering the next section; the section0-only proof guard/helper therefore executes again for the real BG2 [0,8) section and overwrites the saved “absence” evidence with valid **`0x1400`** presence. The Sync Full result is therefore internally consistent.
- **Classification: HARNESS DEFECT / REJECTED AS ABSENCE SEMANTIC EVIDENCE.** The `sub-absent-half` result from runs through `4df594c3...` cannot decide transparent-Sub fallback/HALF suppression.
- This also means the prior conclusion “carrier initialization/lifetime is definitely wrong” is **not yet proven** for a truly absent frame; the current-frame BG2 writer fully explains the observed `0x1400`.
- **Immediate controlled repair:** make the absent guest neutralize the inherited TS HDMA table as well as startup/NMI TS writes, preserving the runtime, Sync Full fence and raw-tag oracle. Run this repaired guest first without weakening runtime semantics. Update queue/surface expectations only where the corrected guest/reference semantics require it.



### FIRST-HAND RESULT — Sync Full fixes present-TS readback; absence carrier remains invalid (2026-09-29 UTC)

- Exact workflow head **`phase4/gate-c-hcomp-transparent-sub-clean@4df594c3c2f927969845641624a4a3fb5d2d55e5`**, semantic runtime **`712766f39cb6ffd94709d70bbbbf0cb0e24f21ca`**. Dedicated **`36483470386 FAILURE`**; artifact **`10999050231`**, digest **`sha256:ab3f1437dd2a36dfd275fb7419f97befb9bc8b3bd08db4fe7c8616fe1245fc68`**. Same-head generic **Build and Validate `36483470861 SUCCESS`**.
- **MEASURED:** all three guests reach the established fresh-frame fence; no RDP crash, TLUT hardware-bug message or cache-coherency diagnostic occurs. Build/PROFILE/Mupen-LLE smoke are green and the frozen RSP/H-COMP ABI remains intact.
- **MEASURED / fence effect:** first-hand mailbox raw TS tag is now exact **`0x1400`** for both states with a real BG2 subscreen pixel:
  - fixed-half: `001F 03E0 3C0F 0001 0C00 0001 0041 0000 7C00 7C00 0000 0100 1400 0001`;
  - sub-present-half: `001F 03E0 01EF 0001 0C00 0001 0041 0000 7C00 03E0 0002 0101 1400 0001`.
  This directly validates that the prior `0x55AA` in those states was an unfenced RDP->RSP readback race; **Sync Full + PIPE_BUSY is effective for completed TS winner writes in the pinned-ares lab**.
- **OPEN / absence state:** `sub-absent-half` has TS=0 in the captured section queue and its compact Sub surface remains entirely untouched sentinel `0x55AA` (2240/2240 words), but the saved raw Z sample is nevertheless **`0x1400`** and is normalized as present. Mailbox: `001F 56CA 2974 0001 0C00 0001 0041 0000 7C00 56CA 0002 0101 1400 0001`.
- External SNES reference semantics agree that when CGWSEL selects the subscreen but the subscreen pixel is transparent, the addend falls back to fixed COLDATA and HALF is suppressed; the transparent Sub color itself is not required to become an opaque fixed-color pixel. Therefore the oracle's current requirement that the compact Sub color surface be blue in the absent state is suspect and must not be used as presence authority.
- **Supported interpretation:** the remaining blocker is carrier initialization/lifetime, not the readback fence. A present winner can now be read reliably, but the no-winner path lacks a trustworthy per-frame absence value and can expose a stale/otherwise non-absence Z word.
- **Next controlled action:** audit the deterministic guest and renderer control flow to determine whether the absent state's `0x1400` can be inherited from an earlier TS-enabled frame or is written in the same frame. Do not weaken the raw-tag requirement yet; do not infer absence from RGB/sentinel alone. If no real TS writer exists, explicitly initialize the bounded Z carrier to an absence state before TS rendering, then rerun the unchanged three-state semantic oracle (with only the incorrect absent-color-surface expectation corrected if reference-backed).



### MEASURED — Sync Full fixes TS readback race; absent carrier remains stale (2026-09-29 UTC)

- Exact workflow head **`4df594c3c2f927969845641624a4a3fb5d2d55e5`**, semantic runtime **`712766f39cb6ffd94709d70bbbbf0cb0e24f21ca`**, dedicated run **`36483470386 FAILURE`**, artifact **`10999050231`**, digest **`sha256:ab3f1437dd2a36dfd275fb7419f97befb9bc8b3bd08db4fe7c8616fe1245fc68`**. Same-head **Build and Validate `36483470861 SUCCESS`**.
- All pre-ares gates passed; all three guests advanced and reached the fresh-frame fence. All three ares logs contain **zero** RDP crashes, zero multi-line-TLUT failures and zero cache-coherency diagnostics.
- **MEASURED / hypothesis supported:** the architectural Sync Full + PIPE_BUSY fence fixes the prior mid-frame RDP->RSP readback race. Raw TS tags are now exact **`0x1400`** in both states where BG2 is genuinely rendered:
  - fixed-half mailbox: `001F 03E0 3C0F 0001 0C00 0001 0041 0000 7C00 7C00 0000 0100 1400 0001`;
  - sub-present-half: `001F 03E0 01EF 0001 0C00 0001 0041 0000 7C00 03E0 0002 0101 1400 0001`.
- **New isolated failure:** sub-absent-half has an entirely untouched compact Sub surface (**2240 × `0x55AA`**) yet the saved TS tag is still **`0x1400`**, yielding mailbox `001F 56CA 2974 0001 0C00 0001 0041 0000 7C00 56CA 0002 0101 1400 0001`. The strict oracle correctly rejects this state before accepting transparent-Sub fallback.
- **Supported interpretation:** `0x1400` in the absent case is a **stale valid depth tag from prior rendering**, not a readback sentinel and not evidence of present Sub coverage. The fence works; the absence baseline is simply not being written/initialized when TS has no drawable layer.
- **REJECTED:** “Sync Full/PIPE_BUSY is insufficient to expose current TS tags” is rejected for real BG2 writes. Do not remove the fence.
- **Immediate next experiment:** initialize only the proof sample/absence carrier to the exact stored backdrop tag **`0x0400`** before section0 TS rendering, then let any real TS BG winner overwrite it. Preserve current Z address, winner tags, Sync Full fence, force-blank lifetime guard, guest/oracle and public ABI. Do not expand into windows/clip/prevent or a new per-pixel surface.
- **Falsifiers:** fixed/sub-present cease producing `0x1400`; absent does not remain `0x0400`; any RDP crash/ABI movement returns; or Main/provenance/source/HALF results regress.



### MEASUREMENT CHECKPOINT — Sync Full fence builds with frozen ABI; stale pin only (2026-09-28 UTC)

- Exact semantic candidate **`712766f39cb6ffd94709d70bbbbf0cb0e24f21ca`**, dedicated **`36483249139 FAILURE`**, artifact **`10998465429`**, digest **`sha256:a926999695311f65d3ab2c18ccbfacff05ba82cf9effcc6ca54e5c8c076a0071`**.
- Deterministic oracle/guests passed; `HCOMP_TRANSPARENT_SUB_EXEC_CLEAN_CONTRACT_VALIDATED` passed; all RSP branch-delay checks passed. Frozen ABI holds: regular RSP **0x1000**, Mode7 **0x1000**, H-COMP **0x790**, `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788`, resident IMEM growth zero.
- New dedicated-build authority: ROM **`44e6ce2bf864716d96dfa4fb6c1d15ac59839119ca0c6a0afa36df1bf0575665`**, ELF **`2a3ae06e5ab446c502dfaa987511cbbf06d47d379293d4fcc69e42b0608c45b9`**.
- Failure is only the deliberately stale previous ROM pin `be9c41a3...`; guest wrapping and ares were skipped.
- **Classification: REJECTED AS SEMANTIC EVIDENCE / TOOLING-PIN ONLY.** The Sync Full/PIPE_BUSY hypothesis remains untested at runtime.
- **Immediate action:** repin only the dedicated workflow to `44e6ce2b...`, preserving semantic runtime/oracle unchanged, then rerun.



### HYGIENE FAILURE — first Sync Full candidate rejected by stale source-contract literal (2026-09-28 UTC)

- Exact head **`ec81d68f695b5332576e70a8129fe1cd8ba49354`**, dedicated run **`36482932649 FAILURE`**, artifact **`10998065557`**, digest **`sha256:dcb98d995da09a497281bdae1cc77a13732b206aa7a9b374ed9cff0257afd7bb`**.
- Build assembled H-COMP at the expected total size (**0x790**) but `test_gate_c_hcomp_transparent_sub_exec_clean.py` stopped before binary ABI/hash/aress execution because one stale literal still required old padding **`.byte 0:0x80`**. The same test already contained the new Sync Full/PIPE_BUSY sequence checks.
- **Classification: HYGIENE-BLOCKER / NOT SEMANTIC EVIDENCE.** No pinned-ares execution occurred, so this run neither supports nor rejects the readback-fence hypothesis.
- Runtime source was not changed in response. Follow-up **`712766f39cb6ffd94709d70bbbbf0cb0e24f21ca`** changes only the stale contract literal to the correct **0x58**. The 10-instruction fence and its runtime bytes are otherwise unchanged.
- **Immediate action:** let exact-head generic/dedicated CI measure frozen ABI and new runtime hash; if the dedicated exact ROM pin is stale, record the hash and repin workflow-only before semantic rerun.



### CONTROLLED REPAIR CANDIDATE — architectural Sync Full fence before TS Z readback (2026-09-28 UTC)

- Exact candidate head **`phase4/gate-c-hcomp-transparent-sub-clean@ec81d68f695b5332576e70a8129fe1cd8ba49354`** adds only the missing mid-frame RDP->RSP readback fence before section0 TS Z is DMA-read.
- In `hcomp_provenance_switch_helper`, section0 now emits a scratch **Sync Full (opcode 0x29)**, then polls **DPC_STATUS PIPE_BUSY (0x20)** clear before the existing unchanged `0xA00E2018` Z sample. Later sections still skip the sample. Main Color Image retarget, TM rendering, final provenance, source logic and oracle are unchanged.
- The added 10 instructions consume **0x28 bytes** of already-unused H-COMP padding; padding is correspondingly reduced **0x80 -> 0x58**, so public `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788` and H-COMP size are intended to remain frozen.
- An intermediate local commit briefly used the wrong padding accounting; it was corrected immediately at **`f3266571...`** before this exact-head contract run. The executable host contract at **`ec81d68f...`** now explicitly requires the Sync Full + PIPE_BUSY wait sequence and the corrected padding, preventing accidental ABI drift.
- **Hypothesis:** the prior all-state `0x55AA` TS tag is an RDP writeback/readback race, not a failure of Z tagging itself.
- **Expected:** exact raw TS tags become `1400` (fixed), `1400` (Sub present), `0400` (Sub absent); source/HALF evidence remains `0100`, `0101`, `0002`; results remain `3C0F`, `01EF`, `7C1F`; Main/provenance/guards remain invariant; no TLUT crash returns.
- **Falsifiers:** build/ABI movement, PIPE_BUSY wait deadlock, DP-interrupt side effect, RDP crash recurrence, raw tag still sentinel, or any oracle mismatch.
- Exact-head runs **`36482932649`** (dedicated) and **`36482932589`** (generic) are queued/pending at this checkpoint. No semantic conclusion yet.



### FIRST-HAND ARTIFACT AUDIT — TS carrier is sampled before RDP writeback (2026-09-28 UTC)

- Downloaded and inspected all files from artifact **`10996369911`**. All three ares logs contain **zero** `RDP crashed`, zero multi-line-TLUT crash messages and zero cache-coherency diagnostics.
- Raw 14-word mailboxes:
  - fixed-half: `001F 03E0 3C0F 0001 0C00 0001 0041 0000 7C00 7C00 0000 0100 55AA 0001`;
  - sub-present-half: `001F 03E0 01EF 0001 0C00 0001 0041 0000 7C00 03E0 0002 0101 55AA 0001`;
  - sub-absent-half: `001F 56CA 2974 0001 0C00 0001 0041 0000 7C00 56CA 0002 0101 55AA 0001`.
- The compact Sub surface is correctly BG2-green in both present states (2048 active `07C1` pixels plus sentinel margins), but is entirely sentinel in the TS-disabled absent state. Main provenance remains correctly `0C00` across all three states.
- **Key discriminator:** raw saved TS tag is the untouched `0x55AA` sentinel in **all three** states. Therefore this is not a BG identity/tag encoding error and not a mailbox-only corruption after a successful tag sample.
- Code audit explains the failure: the TS->TM H-COMP helper immediately RSP-DMAs the compact Z sample after resident TS rendering, while `rdp_send` only waits for **DPC command-buffer busy (0x40)** before submission and does not fence completion of prior primitive writes. The final Main provenance read happens later and is valid; the mid-frame TS read has no RDP->RSP DRAM-read fence.
- SGI/N64 RDP documentation defines **Sync Full (opcode 0x29)** specifically to stall until prior frame/depth-buffer DRAM reads/writes finish before CPU-style reuse/readback; DPC status bit **0x20** is PIPE_BUSY.
- **Supported interpretation:** the TS winner carrier design remains plausible, but the current helper reads it too early. `0x55AA` being normalized as present is a downstream consequence, not valid presence evidence.
- **Next controlled experiment:** before the section0 TS Z DMA read, submit a single Sync Full and wait for DPC PIPE_BUSY to clear, then perform the unchanged Z sample. Keep the validated force-blank lifetime guard, exact Z addresses/tags, guest/oracle and Main/TM path unchanged. Preserve fixed public H-COMP switch/Mode7 entry addresses by consuming existing H-COMP padding only.
- **Falsifier:** raw tag remains `0x55AA`, RDP crash returns, fixed ABI moves, or Main/provenance/three-state results regress. A green result must still prove exact `1400/1400/0400` TS tags and exact source/HALF outputs; no oracle relaxation.



### CAUSE VALIDATED / SEMANTIC RUNG STILL OPEN — force-blank lifetime repair removes TLUT/RDP crash (2026-09-28 UTC)

- Exact workflow head **`b440d9f07f664c8e2c6386dfa4246b2e5fc67345`**, semantic runtime **`ba6c879a0bca10c2eee298cd49dd46c7b378d173`**, dedicated **Gate C H-COMP Transparent Sub Clean `36481355107 FAILURE`**, artifact **`10996369911`**, digest **`sha256:3919a6e73ad7ecdea5d810ec25773429d14cadae743fb87f51801b832398989a`**.
- **MEASURED / CAUSE VALIDATED:** all three deterministic guests now progress through warmup and reach the established fresh-frame capture fence. The prior `guest_counter 0 -> 1 -> stuck` / pinned-ares **TLUT hardware-bug RDP crash is gone** after moving proof OtherModes/Z_UPDATE arming out of startup force-blank frames and into nonblank section0.
- First-hand capture state is healthy in all three runs: one guest-frame advance, one renderer-frame reentry, RSP halted, `DP_CURRENT == DP_END == 0xC10`, RDP command buffer complete/not busy. Therefore the force-blank lifetime hypothesis is now supported by direct before/after runtime evidence, not merely code inspection.
- The semantic classifier still fails, but **later and for a different reason**: fixed-half mailbox ends with raw saved TS tag **`0x55AA` sentinel** and normalized presence `1`, whereas the strict oracle requires **`0x1400` BG2 tag + presence 1**. All earlier fields are correct: Main `001F`, Sub `03E0`, result `3C0F`, gate `1`, Main winner `0C00`, mask `1`, CGADSUB `41`, fixed/selected `7C00`, CGWSEL `0`, source/HALF `0100`.
- **Classification:** the crash/lifetime repair is **VALIDATED**, but transparent-Sub/HALF suppression remains **OPEN**. Do not accept `0x55AA != 0x0400` as proof of Sub presence; the sentinel must never be normalized as a valid real-Sub tag.
- **Next controlled action:** inspect all three first-hand capture files to determine whether (A) section0 TS Z was never written, (B) the TS->TM helper sampled the wrong time/address, or (C) the tag was written but mailbox publication/lifetime lost it. Preserve the now-validated nonblank-section0 lifetime guard; do not revert it and do not weaken the raw-tag oracle.



### HYGIENE CHECKPOINT — bounded transparent-Sub exact-head generic CI green (2026-09-28 UTC)

- Workflow-only repin head **`phase4/gate-c-hcomp-transparent-sub-clean@b440d9f07f664c8e2c6386dfa4246b2e5fc67345`** preserves semantic runtime **`ba6c879a0bca10c2eee298cd49dd46c7b378d173`** and changes only the dedicated ROM hash pin.
- Exact-head **Build and Validate `36481355316 SUCCESS`**: normal build, PROFILE build, host validation/branch-delay checks and pinned Mupen/LLE smoke are green.
- **Meaning:** general build/runtime hygiene is not blocking this candidate. This is **not** transparent-Sub semantic evidence and does not validate real-N64 RDP/RSP ownership.
- Dedicated run **`36481355107`** has already passed the exact runtime pin, deterministic guests, executable contract, ABI/branch-delay checks, guest wrapping and capture-fence discovery; pinned ares is still building at this checkpoint.
- **Immediate action:** interpret only the dedicated first-hand captures once available. Acceptance remains exact three-state TS tag/source/HALF/result invariants with unchanged Main/provenance/guards.



### MEASUREMENT CHECKPOINT — lifetime candidate builds; first dedicated run is stale-pin only (2026-09-28 UTC)

- Exact candidate **`ba6c879a0bca10c2eee298cd49dd46c7b378d173`**, dedicated run **`36481142950 FAILURE`**, artifact **`10996442893`**, digest **`sha256:0d3035dad05be98569ced2bd992449bf2c5e03f4030ef40798822dc5963da8e4`**.
- Deterministic guest/oracle self-test passed; exact build passed; **`HCOMP_TRANSPARENT_SUB_EXEC_CLEAN_CONTRACT_VALIDATED`** passed; branch-delay audit passed; ABI remained frozen at regular/Mode7 RSP **0x1000** and H-COMP **0x790**, with `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788`, resident IMEM growth zero.
- The job then failed **only** at the deliberately stale exact-ROM pin, before guest wrapping or pinned-ares execution. New dedicated-build authority: ROM **`be9c41a34d9a7b7f5245ca08955c04f0e3ba33a6820428403907cc1b64fff8da`**, ELF **`64191377203267aad158daaac3b144e45d6bced51ea7d63aa8c4156afc212911`**.
- **Classification: REJECTED AS SEMANTIC EVIDENCE / TOOLING-PIN ONLY.** The force-blank lifetime hypothesis remains untested at runtime.
- **Immediate action:** update only the dedicated workflow ROM pin to `be9c41a3...` and rerun the unchanged candidate/oracle. Do not modify proof commands, guest states or capture fence.



### CONTROLLED REPAIR CANDIDATE — transparent-Sub proof lifetime bounded to visible section0 (2026-09-28 UTC)

- Exact candidate **`phase4/gate-c-hcomp-transparent-sub-clean@ba6c879a0bca10c2eee298cd49dd46c7b378d173`** moves only the proof-lifetime arm from frame start to the already-decoded **non-force-blank section0** path, while preserving the existing proof commands/oracle and section0-only evidence lifetime.
- The renderer now keeps `RDP_FRAME`/palette load at frame start but does **not** submit `HCOMP_PROOF_RDP_CMDS` there. After section state is loaded, signed `STAT_FLAGS` distinguishes force blank; only `not_blank` with `k0==0` submits the proof list. Force-blank frames therefore cannot strand proof OtherModes/Z_UPDATE into the following frame's TLUT load.
- Host contract was tightened to reject proof arming before force-blank state and to require the nonblank-section0 ordering. Public H-COMP/render ABI is intended to remain frozen.
- **Hypothesis:** the pinned-ares TLUT/RDP crash was caused by proof OtherModes/Z_UPDATE surviving a startup force-blank frame because that path bypassed the TM-end baseline reset.
- **Expected evidence:** exact-head generic CI remains green; dedicated pinned-ares no longer reports the prior TLUT/RDP crash, all three guests reach the established capture fence, and the unchanged oracle proves exact TS tags/source/HALF/result invariants.
- **Falsifiers:** ABI/layout/build regression; same TLUT/RDP crash before capture; guest still stalls at counter 1; or any first-hand mailbox/oracle mismatch after capture.
- At checkpoint time, exact-head runs **Build and Validate `36481142959`** and **Gate C H-COMP Transparent Sub Clean `36481142950`** are **IN PROGRESS**. No semantic conclusion yet.



### SUPPORTED INTERPRETATION — force-blank lifetime can strand proof RDP state across frames (2026-09-28 UTC)

- Code/guest audit strengthens the lifetime hypothesis:
  - the discriminator guest explicitly writes **`INIDISP=$80` forced blank** during startup/VRAM/CGRAM/HDMA setup and only later writes **`INIDISP=$0F`** to enable display;
  - current same-frame renderer sends the proof `OtherModes + SetZ + absence-depth` list at **`draw_frame` before section state/force-blank is inspected**;
  - force blank is detected later from `STAT_FLAGS&0x80`; after backdrop fill the renderer branches directly to `next_section`, bypassing `next_layer` and therefore bypassing the TS/TM H-COMP traversal whose TM-end path restores baseline `RDP_INIT` OtherModes;
  - next frame's `RDP_FRAME` begins with palette Texture Image + **Load Block (palette/TLUT)**, exactly the operation pinned ares reports as the fatal hardware-bug path.
- This also explains why the rejected cross-frame carrier did **not** crash: its proof state was armed from H-COMP, a path force blank already skips.
- **Classification: SUPPORTED INTERPRETATION, not yet MEASURED cause.** We have not directly sampled RDP OtherModes across the frame boundary.
- **Next controlled repair design:** preserve the exact proof commands/oracle but arm the proof only after the current section is known non-force-blank, and only for section0. Avoid enabling it on startup blank frames; preserve first-section-only TS presence so later section splits cannot overwrite the evidence. Keep public renderer/H-COMP ABI frozen.



### REJECTED HYPOTHESIS — PipeSync does not cure same-frame RDP crash (2026-09-28 UTC)

- Exact-head dedicated run **`36479556754 FAILURE`** on workflow head `34b581def460036a32b099ec53a89d68f84a98fb` / semantic runtime `5c10b3b4065f8d54170afddc1b4abf586924e2b2` reached the pinned-ares first-hand capture path.
- Artifact **`10997016461`**, digest **`sha256:29a32aa0cd8ff5cde5ebd926d944fe21c911de05cb9199b4267fae78c52c9f39`**.
- The first fixed-half guest again advanced `guest_counter 0 -> 1` then remained at `1` through all 80 warmup probes. ares again emitted **`Load TLUT with height > 1 is not supported`** followed by **`RDP crashed ... Attempting to load multiple lines in TLUT`**, then repeated cache-coherency diagnostics with RSP PC `0xFAC`.
- This is materially the **same failure signature** as pre-PipeSync artifact `10993629590`. No semantic mailbox capture was reached.
- **REJECTED:** missing PipeSync before the proof-time OtherModes change is not a sufficient explanation for the crash. Keep the spec-derived sync requirement in mind for any future legal mode transition, but do not stack more sync commands as an empirical fix.
- **Next hypothesis to audit, not yet implemented:** proof Z/OtherModes is enabled at `draw_frame` before force-blank handling; force-blank sections skip TS/TM traversal and therefore can skip the H-COMP TM-end reset that normally cuts Z_UPDATE. Test whether proof state survives a startup/force-blank frame into the next frame's palette/TLUT load. If confirmed, move/guard only the proof enable lifetime so it exists exclusively around section0 TS/TM work.



### EXECUTION CHECKPOINT — PipeSync rerun passed all pre-ares gates (2026-09-28 UTC)

- Exact workflow head **`34b581def460036a32b099ec53a89d68f84a98fb`**, semantic runtime **`5c10b3b4065f8d54170afddc1b4abf586924e2b2`**, dedicated run **`36479556754`**.
- The run reproduced exact ROM pin **`ad96601b62d2104e6428da4c9186849376848595645acf7babb2b25ebbcfd073`**, passed the strict transparent-Sub self-test/executable ABI/branch-delay gates, wrapped all three deterministic guests, and located the established capture fence.
- The controlled PipeSync hypothesis is therefore finally past static/tooling gates and entering the pinned-ares laboratory. **No semantic conclusion yet.**
- Acceptance remains unchanged; do not treat mere guest progression/no-crash as closure without exact raw TS tags, source/HALF decisions, Main/provenance/guards and RGB555 outputs.



### RERUN CHECKPOINT — PipeSync runtime repinned without semantic change (2026-09-28 UTC)

- Workflow-only head **`phase4/gate-c-hcomp-transparent-sub-clean@34b581def460036a32b099ec53a89d68f84a98fb`** updates only the dedicated ROM pin from the pre-PipeSync runtime to **`ad96601b62d2104e6428da4c9186849376848595645acf7babb2b25ebbcfd073`**.
- Semantic/runtime source remains **`5c10b3b4065f8d54170afddc1b4abf586924e2b2`**; three-state guests, strict raw TS-tag/source/HALF/result oracle, current-frame binding, and PipeSync command table are unchanged.
- **Acceptance:** absence of the prior RDP/TLUT crash is necessary but not sufficient. Stage closure still requires all three first-hand captures with exact `0x0400/0x1400` TS tags, correct source code, HALF-effective decision, invariant Main/provenance/guards, and exact RGB555 result.



### MEASUREMENT CHECKPOINT — PipeSync candidate builds with frozen ABI; dedicated stale-pin measured (2026-09-28 UTC)

- Exact semantic head **`phase4/gate-c-hcomp-transparent-sub-clean@5c10b3b4065f8d54170afddc1b4abf586924e2b2`** now builds cleanly after removing only the zero-length pad directive.
- Dedicated run **`36479265878 FAILURE`** passed the deterministic oracle/guest self-test, exact build, **`HCOMP_TRANSPARENT_SUB_EXEC_CLEAN_CONTRACT_VALIDATED`**, and all RSP branch-delay checks, then stopped exactly at the deliberately stale pre-PipeSync ROM pin before guest wrapping/ares.
- Exact dedicated-build runtime authority measured: ROM **`ad96601b62d2104e6428da4c9186849376848595645acf7babb2b25ebbcfd073`**, ELF **`3919a0605bc9f005142d159dbf6d870a82c59f7abeff33860b681b35ab38237c`**.
- Frozen ABI still holds: regular RSP **0x1000**, Mode7 RSP **0x1000**, H-COMP **0x790**; no branch-delay control hazards.
- **Classification: REJECTED AS SEMANTIC EVIDENCE / TOOLING-PIN ONLY.** No pinned-ares capture ran, so the PipeSync hypothesis remains untested semantically.
- Same-head generic build and PROFILE jobs are green; emulator smoke is still completing at this checkpoint.
- **Immediate action:** update only the dedicated workflow ROM pin to `ad96601b...`, preserving semantic head `5c10b3...`, then rerun the unchanged three-state discriminator. Do not alter the oracle or proof commands.



### STATIC REPAIR — zero-length pad removed, PipeSync experiment preserved (2026-09-28 UTC)

- Follow-up branch head **`phase4/gate-c-hcomp-transparent-sub-clean@5c10b3b4065f8d54170afddc1b4abf586924e2b2`** removes only the invalid zero-repeat `.byte` directive after the eight-command proof table.
- Intended layout is unchanged: proof table **F30..F6F**, `VEC_DATA=F70`; no semantic command/oracle/H-COMP change from `9c566613...`.
- This repair exists solely to let the controlled PipeSync hypothesis reach build/runtime. Await exact-head generic + dedicated evidence; expect the dedicated ROM pin to be stale because runtime bytes changed relative to the pre-PipeSync candidate.



### STATIC FAILURE — first PipeSync candidate did not build; hypothesis not exercised (2026-09-28 UTC)

- Exact commit `9c5666138df3bec65fb55549f2060ce58bc8ef58` triggered dedicated run **`36479011275 FAILURE`** and generic **Build and Validate `36479011370 FAILURE`** before any runtime/pinned-ares execution.
- Exact assembler cause in both paths: `src/rsp_main.S:158: Warning: unresolvable or nonpositive repeat count; using 1`, promoted to error. The new eight-command proof table exactly fills **F30..F6F**, so the old trailing expression became `.byte 0:(F70-F70)` / zero repeat.
- **Classification: HYGIENE-BLOCKER / NOT SEMANTIC EVIDENCE.** The PipeSync hypothesis has not been tested and must neither be accepted nor rejected from these runs.
- **Immediate repair:** remove only the now-zero trailing pad directive. The table already ends exactly at frozen `VEC_DATA=F70`; no byte needs to be emitted. Then rebuild under the unchanged contract/oracle.



### CONTROLLED REPAIR CANDIDATE — PipeSync before same-frame proof OtherModes (2026-09-28 UTC)

- Exact branch commit **`phase4/gate-c-hcomp-transparent-sub-clean@9c5666138df3bec65fb55549f2060ce58bc8ef58`** changes only the bounded proof RDP command table/address contract: it prepends **PipeSync `0x2700000000000000`** before the proof-time `Set OtherModes`, shifts `HCOMP_PROOF_BG_DEPTH_CMDS` from `+0x18` to `+0x20`, and updates the source contract accordingly.
- Rationale is architectural, not guesswork: the N64 RDP programming/function reference requires **PipeSync before an RDP attribute/mode change** when prior pipeline work may still be active. The failing same-frame path issued `Set OtherModes` immediately after the frame-start palette/TMEM load and pinned ares then reported an RDP hardware-bug crash; the prior cross-frame carrier used the same Z/depth commands without that crash.
- The retired DMEM tail already had exactly one 8-byte slot free: the table now occupies **F30..F6F** and `VEC_DATA` remains frozen at **F70**. No new per-pixel surface, no new IMEM footprint, no change to the three-state oracle, no change to H-COMP arithmetic/source semantics, and no public renderer/H-COMP entrypoint is intended to move.
- **Hypothesis:** missing RDP attribute synchronization, not the bounded Z commands themselves, causes the current-frame crash.
- **Falsifiers:** exact build/ABI moves; pinned ares still reports the TLUT/RDP crash; guest still cannot reach warmup fence; or semantic captures reach the fence but fail raw TS-tag/source/HALF/result invariants.
- The existing dedicated workflow still carries the previous exact ROM pin by design. If the runtime hash changes, the first exact run is pin-measurement/tooling evidence only; repin only from that dedicated build and rerun without semantic changes.



### CAUSE NARROWED — stalled same-frame candidate crashes pinned-ares RDP before capture (2026-09-28 UTC)

- Inspection of exact artifact `10993629590` found a decisive line near the start of `captures/fixed-half/ares-n64.log`: pinned ares reports **`[RDP] software triggered a hardware bug; RDP crashed and will stop responding. Reason: Attempting to load multiple lines in TLUT.`**
- The same log then emits 252 cache-coherency diagnostics while the RSP is observed at PC `0xFAC` (resident `hcomp_cgram_pair_ready` vicinity), consistent with execution continuing around a dead RDP rather than reaching the established renderer-frame fence.
- Control comparison against the last validated CGADSUB artifact `10968609752` shows **zero** `RDP crashed` messages and **zero** `not cache coherent` diagnostics in all four successful captures. Therefore these messages are **not established baseline noise** for this lab/workload.
- **Supported interpretation:** the new same-frame proof integration causes/exposes an invalid RDP state before semantic capture. This is stronger than the earlier generic “runtime stall” diagnosis, but it does **not yet identify which proof command/order is causal**.
- **Next controlled action:** inspect the exact RDP command ordering/state around frame palette/TLUT load and the new same-frame proof list; design a one-variable ordering/state experiment that removes the RDP hardware-bug condition without weakening the transparent-Sub oracle or adding a new surface.



### REJECTED EXPERIMENT — same-frame TS-Z binding stalls before semantic capture (2026-09-28 UTC)

- Exact-head dedicated **Gate C H-COMP Transparent Sub Clean `36477073489 FAILURE`** on `phase4/gate-c-hcomp-transparent-sub-clean@7d68c4a2b1e0249fd6fab92cf134c1037c4ef0fd` passed deterministic guest/oracle self-test, the exact dedicated ROM pin `188bb47f...`, executable/ABI contract, RSP branch-delay audit, guest wrapping, fence-location checks, and pinned ares construction.
- The first first-hand case (**fixed-half**) did **not** reach the semantic capture fence: guest warmup advanced from counter `0` to `1` and then remained at `1` for all 80 warmup probes; capture aborted with `RuntimeError: guest did not reach warmup counter`.
- Evidence artifact **`10993629590`**, digest **`sha256:c2e12e2fc693124ebf5a74ec7b3541b1e3da4e57faf8baf05301d35208ed737f`**.
- **Classification: REJECTED AS SEMANTIC EVIDENCE / RUNTIME-INTEGRATION FAILURE.** This run says nothing yet about fixed-vs-Sub source choice or HALF suppression because no state reached the established fresh-frame fence.
- Same-head generic **Build and Validate `36477073413 SUCCESS`** is green, so the new failure is narrower than generic build/smoke hygiene and is introduced/exposed by the same-frame proof path under the pinned ares lab.
- **Next action:** inspect the uploaded fixed-half partial capture/ares log and exact RSP/RDP state to determine whether the same-frame proof command list causes an RDP/RSP ownership stall, a renderer return/control-flow fault, or a guest-specific progression issue. Do not weaken warmup or move to windows/clip/prevent. Fix one identified cause, then rerun the unchanged three-state discriminator.



### HYGIENE CHECKPOINT — same-frame transparent-Sub exact-head generic CI green (2026-09-28 UTC)

- Same-head **Build and Validate `36477073413 SUCCESS`** on `phase4/gate-c-hcomp-transparent-sub-clean@7d68c4a2b1e0249fd6fab92cf134c1037c4ef0fd`: normal build, PROFILE build, host validation/branch-delay checks and pinned Mupen/LLE smoke are green.
- **Meaning:** generic regression/hygiene is excluded for this exact candidate. This is not semantic transparent-Sub evidence and does not imply real-N64 performance; pinned-ares three-state capture remains the acceptance authority.
- Dedicated run `36477073489` has already passed the exact dedicated runtime pin and is building the pinned ares N64-only laboratory.



### CHECKPOINT — dedicated pin reproducibility confirmed before transparent-Sub captures (2026-09-28 UTC)

- Exact-head dedicated run **`36477073489`** on `phase4/gate-c-hcomp-transparent-sub-clean@7d68c4a2b1e0249fd6fab92cf134c1037c4ef0fd` reproduced the dedicated-authority ROM pin **`188bb47fe379c277dbad084c6e6c6e90015c9e5b80d76ecd8044df02e92473ea`** and passed the deterministic guest/oracle self-test, exact build, executable/ABI contract, RSP branch-delay audit and three guest wrapping steps.
- **REJECTED hypothesis:** workflow-only commits do not inherently create an unpinnable hash loop in this dedicated path. The prior mismatch came from seeding the semantic workflow with a ROM hash produced by the generic build path.
- The run is now beyond the pin gate and entering the pinned-ares laboratory. **No semantic result yet**; closure still requires all three first-hand captures and the strict TS-tag/presence/source/HALF/result oracle.



### RERUN CHECKPOINT — dedicated same-frame TS-Z runtime repinned from dedicated authority (2026-09-28 UTC)

- Workflow-only head **`phase4/gate-c-hcomp-transparent-sub-clean@7d68c4a2b1e0249fd6fab92cf134c1037c4ef0fd`** changes only the dedicated runtime pin/comment; semantic runtime remains the current-frame TS-Z candidate from `8a487570ce9053d6a49c4b97fdd7c8bfb9248840` plus the host-only regular/Mode7 contract repair `c65aff7911fc19501a4ed30004d769f4806b16ec`.
- The pin now uses **dedicated-workflow authority** ROM **`188bb47fe379c277dbad084c6e6c6e90015c9e5b80d76ecd8044df02e92473ea`**, measured by failed-pre-capture run `36475524327`; the generic-build hash `9f719b3b...` remains **REJECTED AS PIN AUTHORITY** for this workflow.
- No semantic source, guest, oracle, capture fence, ABI contract, or RSP layout changed in this batch. This is deliberately a one-variable rerun.
- **Acceptance remains unchanged:** all three pinned-ares captures must prove renderer-owned TS absence/presence (`0x0400` / `0x1400`), correct source code, pixel-local HALF-effective decision, invariant Main/provenance/guards, and exact RGB555 result. A build/pin pass alone is not semantic evidence.
- **Immediate action:** inspect the exact-head dedicated run triggered by `7d68c4a2...`; if it reaches captures, interpret only first-hand artifacts. If the exact dedicated hash changes again, treat that as a reproducibility/toolchain issue and investigate before semantics.



### CHECKPOINT — clean CGWSEL second-operand source selection VALIDATED (2026-09-28 UTC)

- **ARCHITECTURE PROOF / VALIDATED / STAGE CLOSED:** exact branch head `phase4/gate-c-hcomp-cgwsel-source-clean@762250a95c6d2ef4bda1b2f4d82e255c43889c83`.
- Semantic runtime change is `6786bf55c08d5ec689b234bc2759d4b3f37ba457`; later commits are host-only guest/oracle/workflow work and the exact ROM-hash pin. Runtime hashes: ROM **`f4d3c58ea6ae05ef89f8b78b66be3b4c1e8b8efdb4bcae52069f58161a49741a`**, ELF **`cf43093a37a979ee9c01b0a92402b772a82b2ae5fcb544035fe0c9b3c88a08aa`**.
- Dedicated **Gate C H-COMP CGWSEL Source Clean `36377395203 SUCCESS`**; artifact **`10951817024`**, digest **`sha256:483759afdb3fc719807c72c55c62095956dc580b57f6c6ba3b5114862a23c96e`**. Classifier: **`HCOMP_CGWSEL_SOURCE_SELECTION_VALIDATED`**, `passed=true`.
- Same-head generic **Build and Validate `36377395162 SUCCESS`**: normal build, PROFILE build, branch-delay audit and pinned Mupen/LLE smoke all green.
- Frozen controls held exactly across both captures: Main BG1 red `0x001F`, live Sub BG2 green `0x03E0`, provenance `0x0C00 -> mask1`, `CGADSUB=0x01`, compact ownership, TM-end Z cut and one-fresh-frame fence. `main_sub_provenance_identical_across_source_states=true`; provenance guards intact.
- **Fixed case:** `CGWSEL=0x00`, fixed blue `0x7C00`, selected addend `0x7C00`, exact E1f half-add result **`0x3C0F`**.
- **Subscreen case:** `CGWSEL=0x02`, selected addend live Sub `0x03E0`, exact E1f half-add result **`0x01EF`**.
- Appended source mailbox is consistent with the intended selector while the original first 16 B remains byte-compatible: fixed/source state `[fixed=7C00, selected=7C00, cgwsel=0000, source=0000]`; Sub state `[fixed=7C00, selected=03E0, cgwsel=0002, source=0001]`.
- ABI remained frozen: regular/Mode7 RSP text **0x1000**, H-COMP **0x790**, `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788`, resident IMEM growth zero.
- **Still NOT PROVEN:** add/sub/half mode selection, absent-Sub HALF suppression, mid-frame fixed-color history, brightness ordering below full brightness, color windows/clip/prevent, BG3/BG4/OBJ/backdrop provenance, production-safe real-N64 RDP->RSP fence, throughput and real-N64 cadence/performance.
- The earlier `36377226182 FAILURE` remains classified **REJECTED AS SEMANTIC EVIDENCE / TOOLING-PIN ONLY**: it stopped at the deliberately stale ROM pin before captures. The corrected exact-head run above is authority.

### CHECKPOINT — clean CGADSUB add/sub/half modes VALIDATED (2026-09-28 UTC)

- **GATE DRIVER / ARCHITECTURE PROOF / VALIDATED / STAGE CLOSED:** `phase4/gate-c-hcomp-cgadsub-modes-clean@73d9d08037151457e53c6150c8ebeeb5a176f4ac`.
- Semantic runtime commit **`dee7fdb10731cb059a985ea45e8642587c6a8143`** changes only `src/rsp_hcomp.S`; later commits add the deterministic guest/oracle/contract/workflow and the host-only exact ROM pin.
- Exact runtime hashes: ROM **`53df19d9d0b9f0996d1bb7aca15f744ab28e67525362656ef01f726eaa9e576c`**, ELF **`fa9e863fd4a7927e3591f86ad54154b1e8d156c3f6dc147cbca87bcea6ea8483`**.
- Dedicated **Gate C H-COMP CGADSUB Modes Clean `36419920887 SUCCESS`**; evidence artifact **`10968609752`**, digest **`sha256:3d11488928a2310e144fb4b2808ea72897eff016c8ff5d19f457a5d667e4108b`**. Classifier: **`HCOMP_CGADSUB_MODES_VALIDATED`**, `passed=true`.
- Controlled operands were identical in all four states: Main BG1 red RGB555 **`0x001F`**, live Sub BG2 green **`0x03E0`**, `CGWSEL=0x02`, winner tag **`0x0C00 -> mask 0x01`**, compact ownership/provenance and section geometry fixed.
- First-hand exact arithmetic matrix:
  - **ADD full:** `CGADSUB=0x01 -> 0x03FF`
  - **ADD half:** `CGADSUB=0x41 -> 0x01EF`
  - **SUB full:** `CGADSUB=0x81 -> 0x001F`
  - **SUB half:** `CGADSUB=0xC1 -> 0x000F`
- **`main_sub_provenance_identical_across_modes=true`**. Every state has exact Sub active pixels, exact canonical Main ownership, exact BG1 provenance, intact prefix/suffix guards, requested section-carried `CGADSUB`, selected live-Sub operand, and the exact precommitted RGB555 result.
- The runtime now decodes real `CGADSUB` bit7 (add/subtract) and bit6 (full/half) only after the already-validated winner eligibility gate and CGWSEL source selector. Packed saturating add/sub avoids cross-channel carry/borrow; E1f remains the half-add path.
- ABI remains frozen: regular/Mode7 RSP text **`0x1000`**, H-COMP **`0x790`**, `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788`, resident IMEM growth zero; all RSP branch-delay audits pass.
- Same-head generic **Build and Validate `36419921205 SUCCESS`**: normal build, PROFILE build, host validation and pinned Mupen/LLE smoke all green. Artifacts: build `10968648254`, profile `10969335882`, smoke `10968553528`.
- Earlier run **`36419660606 FAILURE`** is permanently **REJECTED AS SEMANTIC EVIDENCE / TOOLING-PIN ONLY**: source/binary/ABI and delay-slot gates passed, then the deliberately stale parent ROM pin stopped the run before captures. It measured the exact runtime hash used by the successful rerun.
- Branch audit against parent `762250a9...`: only `src/rsp_hcomp.S` plus the dedicated generator/oracle/contract/workflow differ; no lateral CPU/PPU/renderer changes entered this rung.
- **Still NOT PROVEN:** transparent/absent Sub fallback to fixed color and its HALF-suppression rule; direct-fixed HALF control outside the prior fixed-source E1f case; mid-frame fixed-color history; brightness ordering below full brightness; clip/prevent/color windows; BG3/BG4/OBJ/backdrop provenance; OBJ palette exception; production-safe real-N64 RDP->RSP fence; throughput and real-N64 cadence/performance.

### AUDIT CHECKPOINT — current Sub color sample is not a trustworthy coverage carrier (2026-09-28 UTC)

- **MEASUREMENT/REPRESENTATION FINDING:** the clean candidate's H-COMP sample reads only rendered Sub RGBA5551 color. Current palette conversion in `src/ppu.S` forces alpha bit `1` on converted CGRAM colors, so the sampled color word alone cannot prove whether a real Sub layer won that pixel versus backdrop/fallback state.
- **SUPPORTED INTERPRETATION:** do not infer Sub presence from RGB value or RGBA5551 alpha in the current clean path. Doing so would conflate color with coverage and could suppress HALF on the wrong pixels.
- **Historical evidence only:** E2g encoded the needed semantic boolean in a Z/depth carrier (`sub_present=true` for a real TS BG winner, false for backdrop). That branch remains **REJECTED as a cumulative solution**; only the representation idea is admissible for a new clean proof.
- **Next controlled change:** reuse/bound the smallest possible depth/coverage carrier around the already-validated compact Sub strip, capture presence before TM overwrites/repurposes provenance, and prove three states: direct-fixed+HALF, Sub-present+HALF, Sub-selected-but-absent fallback with HALF suppressed. No windows/clip/prevent work yet.
- **Falsifier:** if a bounded clean carrier cannot coexist with the current TM provenance lifetime/guards without new ownership ambiguity or ABI movement, stop and record the representation limitation instead of expanding the old compositor.

### CHECKPOINT — transparent-Sub first build measured; stale-pin run rejected as semantic evidence (2026-09-28 UTC)

- Dedicated **Gate C H-COMP Transparent Sub Clean `36450588298`** reached the deliberate stale parent ROM pin and failed there exactly as intended. Artifact **`10983087624`**, digest **`sha256:d31fa42a970a9f390f06b446c3a3c83829e113176622b2e7f40da3ed62857147`**.
- **Source/oracle gate passed:** deterministic three-guest generation and oracle self-test succeeded, including the negative fixture that rejects transparent fallback with HALF still active.
- **Executable/ABI gate passed:** `HCOMP_TRANSPARENT_SUB_EXEC_CLEAN_CONTRACT_VALIDATED`; regular/Mode7 RSP text **0x1000 / 0x1000**, H-COMP **0x790**; `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788`, resident IMEM growth zero; all RSP branch-delay audits pass.
- Exact runtime measured from semantic candidate: ROM **`998e2132bff4a65167f3a3c257e48c269715b00be2e74dc43d5e6ddffb26e808`**, ELF **`412416a2ea8217f0e7516624faf7ca6ff959e7836c6130e728415171108cbdff`**.
- This run is permanently **REJECTED AS SEMANTIC EVIDENCE / TOOLING-PIN ONLY** because it stopped before wrapping/capturing the three ares states. It does prove the candidate fits the frozen overlay ABI and compiles cleanly.
- **Immediate action:** update only the workflow ROM pin to `998e2132...`; semantic runtime stays at commit `42613980631a27925bd13b5b078f47a036169458`. Then require same-head generic hygiene plus first-hand pinned-ares captures before accepting the alpha coverage representation.

### REJECTED EXPERIMENT — RGBA5551 alpha cannot serve as clean absent-Sub coverage carrier (2026-09-28 UTC)

- Exact-head dedicated **Gate C H-COMP Transparent Sub Clean `36450859892`** reached all three first-hand captures but the semantic classifier correctly rejected the absent-Sub state. Evidence artifact **`10982779716`**, digest **`sha256:e93b36cd2d0479832b6d726134dbcdb44d869eca80cbe4ef62dae20734573d46`**.
- Fixed/direct and live-Sub controls were internally correct: fixed-half mailbox `001F,03E0,3C0F,0001,0C00,0001,0041,0000,7C00,7C00,0000,0100`; live-Sub-half `001F,03E0,01EF,0001,0C00,0001,0041,0000,7C00,03E0,0002,0101`.
- In the **Sub-absent** capture, every one of the 2,048 active compact-Sub words remained the seeded sentinel **`0x55AA`**; the 192 border words were also `0x55AA`. Therefore the alpha0 backdrop write did not establish real coverage/absence state in the target.
- H-COMP happened to read sentinel bit0=0 and produced the intended fallback mailbox `001F,56CA,7C1F,0001,0C00,0001,0041,0000,7C00,7C00,0002,0002`: fixed-color fallback selected, HALF suppressed, exact full-add result `0x7C1F`. **This is NOT semantic proof** because the absence decision was manufactured by harness sentinel state, not by renderer-owned data.
- **REJECTED:** using compact Sub RGBA5551 alpha as the clean coverage carrier under the current RDP state. Do not weaken the oracle to accept untouched memory and do not treat the numerically correct fallback as success.
- **SUPPORTED INTERPRETATION:** alpha0 primitive backdrop is discarded/not committed under the current renderer path in the pinned ares lab; real alpha1 texels still draw. The exact low-level RDP reason need not be guessed before choosing the already-supported bounded depth alternative.
- **Next action:** revert the proof-local alpha0 backdrop change and derive a clean bounded TS-presence depth tag using the already-owned compact Z/provenance arena, sampling it at TS→TM before that arena is cleared/reused for Main provenance. No new full-frame surface and no cumulative E2g/E3 compositor import.

### HYGIENE CHECKPOINT — exact-head generic CI green (2026-09-28 UTC)

- Same-head **Build and Validate `36450859788 SUCCESS`** on `33a3ec9bf642cf425fe6aa33b0796b54181ad9de`: normal build, PROFILE build, host validation/branch-delay checks and pinned Mupen/LLE smoke all green.
- Artifacts: build **`10984066380`** / `sha256:6cb81827cbe66cc3ee613ae3544cefa7f26f0c690030eae6dfe25dd86f9f366f`; PROFILE **`10983181976`** / `sha256:216e5c1d0f128037cdf80b917456f15b1ab38de5d5a0cc6e65a7e476aa2edf57`; emulator smoke **`10983676872`** / `sha256:5d752d30cd92262ebe6e9775a83abf74beceb7d794755fb0a59afd8729d88259`.
- **Meaning:** generic regression/hygiene is excluded for this exact candidate. This still does **not** validate transparent-Sub semantics, real-N64 RDP→RSP ownership, throughput or hardware performance; dedicated pinned-ares evidence remains pending authority.

### RERUN CHECKPOINT — exact transparent-Sub runtime pinned (2026-09-28 UTC)

- Workflow-only head **`phase4/gate-c-hcomp-transparent-sub-clean@33a3ec9bf642cf425fe6aa33b0796b54181ad9de`** pins the measured ROM hash **`998e2132bff4a65167f3a3c257e48c269715b00be2e74dc43d5e6ddffb26e808`**; semantic runtime remains **`42613980631a27925bd13b5b078f47a036169458`**.
- Exact-head dedicated run **`36450859892`** and generic **Build and Validate `36450859788`** are active. Dedicated self-test/build/ABI/wrapping/fence-location gates are already green and is building the pinned ares lab before first-hand captures.
- Same-head generic normal build and PROFILE build are green. Build artifact **`10984066380`**, digest **`sha256:6cb81827cbe66cc3ee613ae3544cefa7f26f0c690030eae6dfe25dd86f9f366f`**; PROFILE artifact **`10983181976`**, digest **`sha256:216e5c1d0f128037cdf80b917456f15b1ab38de5d5a0cc6e65a7e476aa2edf57`**. Pinned Mupen/LLE smoke is still running and remains hygiene-only.
- **Pending authority:** do not accept the alpha carrier until dedicated ares proves all three precommitted states. Do not infer performance from these CI results; this remains a Gate-C semantic proof.

### EXPERIMENT IN PROGRESS — alpha coverage carrier + transparent-Sub fallback (2026-09-28 UTC)

- **CANDIDATE:** `phase4/gate-c-hcomp-transparent-sub-clean@c080d141c4699b4243da1ad83f789364b5efb901` (runtime semantic changes are in `src/rsp_main.S` + `src/rsp_hcomp.S`; later files on the branch are deterministic guest/oracle/contract/workflow plumbing).
- **Controlled representation change:** the compact proof-only Sub backdrop fill no longer forces primitive alpha `0xFF`; its instruction slot is an inert `nop`, leaving backdrop alpha0 while real converted CGRAM texels retain RGBA5551 alpha1. No new per-pixel RDRAM surface was introduced.
- **H-COMP semantic candidate:** preserve raw Sub bit0 before RGB555 conversion; source code `0=direct fixed`, `1=live Sub`, `2=Sub-selected-but-absent fixed fallback`. Evidence word bit8 means HALF was actually applied. Source code 2 suppresses HALF while retaining fixed-color fallback.
- **ABI intent:** candidate adds exactly 20 RSP instructions / 80 B before the fixed switch and consumes existing H-COMP padding `0x5C -> 0x0C`; expected public addresses remain `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788`, resident IMEM growth zero.
- **Three precommitted states, all ADD with `CGADSUB=0x41`:** direct fixed + HALF -> selected blue `0x7C00`, result `0x3C0F`, flags `0x0100`; live Sub present + HALF -> selected green `0x03E0`, result `0x01EF`, flags `0x0101`; Sub selected but absent -> fallback blue `0x7C00`, HALF suppressed, full-add result `0x7C1F`, flags `0x0002`.
- **Dedicated run:** `36450588298` on exact candidate head. Workflow deliberately retains the parent ROM pin `53df19d9...` for the first pass, so the acceptable first-run outcome is: self-test + build + executable/ABI/delay-slot gates pass, exact new runtime hashes are measured, then the run stops at stale pin before ares captures. Any earlier failure rejects/fixes the candidate before semantic interpretation.
- **Decision:** if the alpha carrier does not show alpha1 for real Sub and alpha0/non-sentinel for absent Sub, reject this representation and return to a bounded depth carrier. If it does, repin exact runtime and require first-hand three-state capture before closure.

### EXPERIMENT IN PROGRESS — bounded compact-Z reuse for TS presence (2026-09-28 UTC)

- **Replacement candidate:** `phase4/gate-c-hcomp-transparent-sub-clean@830d381ac627cb76ec8004500661b6cd446e9277` supersedes the rejected alpha-carrier attempt on the same clean branch.
- **Representation:** no new per-pixel RDRAM surface. Reuse the already-owned compact Z16 arena `0xA00E2000` sequentially: section0 TS first records backdrop/absence vs real BG winner; at TS→TM H-COMP DMA-saves the sample tag; TM then overwrites the same arena with the already-validated Main winner provenance.
- **Bounded tags:** immutable proof RDP commands live in the audited retired DMEM tail `0xF30..` below frozen `VEC_DATA=0xF70`. Z update + compact Set-Z + backdrop primitive depth `0x0800 -> stored 0x0400`; BG1 `0x1800 -> 0x0C00`; BG2 `0x2800 -> 0x1400` (BG3/BG4 command slots are reserved only; downstream semantics remain NOT PROVEN).
- **Lifetime:** completed-frame H-COMP prepares only the next frame's controlled section0 TS carrier. TS→TM saves sample `0xA00E2018` into DMEM before Main reuse. TM end still sends baseline `RDP_INIT` OtherModes to disable Z update before any next-section work, preserving the previously validated spill boundary.
- **Source decision:** saved TS tag `0x0400` normalizes to absent; any exact validated real-BG tag normalizes present. `CGWSEL` direct fixed ignores presence; Sub+present selects live Sub; Sub+absent selects fixed and suppresses HALF. Mailbox grows from 24 B to 28 B only to expose raw TS tag + normalized presence first-hand.
- **Renderer ABI intent:** regular/Mode7 resident text remains unchanged in instruction count; `draw_bg` changes only the command-table base. H-COMP is currently source-balanced with provisional padding `0x74` to preserve `hcomp_screen_switch=0x1760` and `draw_mode7_entry=0x1788`; executable contract must prove exact sizes/addresses.
- **Precommitted discriminator remains:** fixed+HALF -> `0x3C0F`; Sub present+HALF -> `0x01EF`; Sub absent -> opaque backdrop color may remain present in Sub color target, but raw TS Z tag must be exactly `0x0400`, source must fall back fixed blue, HALF must be suppressed, result `0x7C1F`.
- **First bounded-Z workflow head:** `830d381a...` deliberately retains rejected-alpha ROM pin `998e2132...`. Acceptable first run is self-test/build/executable/ABI pass followed by stale-pin stop; any earlier failure is implementation/test failure. Only after repinning exact measured runtime may pinned-ares semantics be interpreted.

### CHECKPOINT — bounded-Z transparent-Sub candidate first build measured; stale-pin run rejected (2026-09-28 UTC)

- **CANDIDATE:** `phase4/gate-c-hcomp-transparent-sub-clean@2ab71b0adaa722271b88482280c3209317212823`; this supersedes the rejected alpha-carrier attempt while keeping the bounded compact-Z representation described below.
- Dedicated **Gate C H-COMP Transparent Sub Clean `36453965238`** passed deterministic guest/oracle self-test, exact build, executable contract and RSP branch-delay audit, then stopped at the deliberately stale rejected-alpha ROM pin before any ares semantic capture. Artifact **`10984457416`**, digest **`sha256:1df55665f13061f6b593a2ffd8a85403d1ff6a52b37e4bd383f4f6b12bfab173`**.
- Exact measured runtime: ROM **`c073800b3adeb19ebaa7b1d295f3fb47470f604d968942dcb89fd670c39bdc5d`**, ELF **`a359504775aa242457423ed0d702b32ccb354af6214efad4799b60e977ca32ce`**.
- Frozen executable ABI remains intact: regular/Mode7 text **0x1000 / 0x1000**, H-COMP **0x790**, `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788`, resident IMEM growth **0**.
- Same-head generic **Build and Validate `36453965099 SUCCESS`** is fully green: build artifact **`10984781439`**, PROFILE **`10984172549`**, pinned Mupen/LLE smoke **`10984252793`**.
- **Classification:** first dedicated run is **REJECTED AS SEMANTIC EVIDENCE / TOOLING-PIN ONLY**, not a bounded-Z failure. Source/oracle/ABI/hygiene gates support repinning this exact runtime.
- **Immediate action:** change only the dedicated workflow ROM pin to `c073800b...`; leave the semantic runtime untouched, rerun exact-head pinned ares, and require all three precommitted states plus raw TS Z tag/presence/source/HALF/result agreement before closure.

### RERUN CHECKPOINT — bounded-Z transparent-Sub exact runtime pinned (2026-09-28 UTC)

- Workflow-only head **`phase4/gate-c-hcomp-transparent-sub-clean@5b66d9c40c8c953f8d0d4d0ee8ef95b9604de26a`** changes only the dedicated ROM pin from the rejected-alpha hash to exact bounded-Z ROM **`c073800b3adeb19ebaa7b1d295f3fb47470f604d968942dcb89fd670c39bdc5d`**; semantic runtime is unchanged from the measured candidate.
- Dedicated rerun **`36471912947`** has passed oracle/guest self-test, exact build, executable/ABI/delay-slot gate, wrapping and fence-location gates. It is building the pinned ares laboratory before the three first-hand captures.
- Same-head generic **Build and Validate `36471912891`** has normal build and PROFILE build green; pinned Mupen/LLE smoke is still running and remains hygiene-only.
- **Pending authority:** require fixed-direct+HALF, live-Sub+HALF, and Sub-absent fallback captures to agree on raw TS tag, normalized presence, source code, HALF-effective bit, invariant Main/provenance and exact RGB555 result. Do not accept from CI setup/build alone.

### HYGIENE CHECKPOINT — bounded-Z exact-head generic CI green (2026-09-28 UTC)

- Same-head **Build and Validate `36471912891 SUCCESS`** on `5b66d9c40c8c953f8d0d4d0ee8ef95b9604de26a`: normal build, PROFILE build, host validation/branch-delay checks and pinned Mupen/LLE smoke all green.
- Artifacts: build **`10991592478`** / `sha256:be8a83cdc83d12c5fee63de24b3122f9d09da5f4fa393ed06b196e67f3c3936a`; PROFILE **`10992206487`** / `sha256:0934aaaab012ecf58bb27c92ce5d87ea00352a022638cecdfe6b5d8353b892e9`; smoke **`10992750740`** / `sha256:cbb0562ec8f99df3b53149a2a8d8eb23dab8851b25420e1da672810bce291ccf`.
- **Meaning:** generic regression/hygiene is excluded for this exact repinned head. Dedicated pinned-ares transparent-Sub semantics remain the authority still in progress; no performance/hardware claim follows from this green run.

### REJECTED EXPERIMENT — prior-frame bounded-Z setup does not establish TS presence (2026-09-28 UTC)

- Exact-head dedicated **Gate C H-COMP Transparent Sub Clean `36471912947 FAILURE`** on `5b66d9c40c8c953f8d0d4d0ee8ef95b9604de26a` passed oracle/build/ABI/wrapping/fence/pinned-ares construction, then failed only in the three first-hand semantic captures. Evidence artifact **`10991788461`**, digest **`sha256:3224ec230db7ed795ba8022931a5497fb3717cf2c333901b160a459855927692`**.
- **Fixed+HALF:** Main/Sub/math remain correct (`001F,03E0 -> 3C0F` with direct fixed blue), Main provenance is exact `0x0C00`, but the saved TS-presence word is untouched sentinel **`0x55AA`**, not expected BG2 tag `0x1400`.
- **Sub-present+HALF:** live Sub color is correctly green and arithmetic remains `0x01EF`, yet the saved TS Z word is again **`0x55AA`**. This is decisive: a real rendered TS BG2 pixel did **not** acquire the intended compact-Z tag.
- **Sub-absent:** compact Sub and provenance remain sentinel; current `tag != 0x0400` normalization therefore falsely reports presence from untouched memory. Do not weaken the oracle or treat sentinel inequality as coverage.
- All captures reached the established fresh-frame fence (one renderer reentry, RSP halted, DPC current=end, bufferBusy=false). Same-head generic **Build and Validate `36471912891 SUCCESS`** is green, so this is a representation/ownership failure rather than a generic build/smoke regression.
- **REJECTED:** relying on proof-Z state prepared by completed-frame H-COMP and carried across into the next frame's TS traversal. The bounded arena/reuse idea itself is not disproven; the timing/ownership point is.
- Historical E1/E2 evidence and the validated Main-provenance parent both point to a narrower next hypothesis: bind/enable the compact Z carrier **just in time in the current frame immediately before TS rendering**, analogous to the already-working TS→TM setup, then preserve the TS sample before TM reuse.
- **Next controlled experiment:** add only the smallest current-frame TS Z setup that fits the frozen resident ABI; retain the same three guests/oracle and require BG2 to overwrite the runtime-owned absence baseline. If this cannot be done without ownership ambiguity or resident-IMEM growth, record a representation limitation rather than reviving the old cumulative compositor.

### IMPLEMENTED — current-frame TS Z binding candidate (2026-09-28 UTC)

- New semantic candidate **`phase4/gate-c-hcomp-transparent-sub-clean@dae28945adbbd332440a15d0a8be3c7bcefc2b79`** tests the narrow hypothesis from the rejected run: bind/enable the compact Z16 carrier in **the same `draw_frame` immediately before section0 backdrop/TS**, rather than depending on RDP state prepared by the previous completed-frame H-COMP.
- Runtime change is deliberately bounded: three instructions send the existing immutable `HCOMP_PROOF_RDP_CMDS .. HCOMP_PROOF_BG_DEPTH_CMDS` setup; the resident budget is paid by filling the safe H-COMP overlay branch delay slot and consuming the former 8-byte inert pad before `draw_bg`. No new per-pixel surface or window semantics are introduced.
- The rejected cross-frame setup call was removed from H-COMP; its fixed external switch address is intended to remain unchanged by increasing internal padding `0x74 -> 0x80`.
- Executable contract now requires the same-frame TS-Z setup ordering and the compacted safe delay slot. **Expected invariant:** regular/Mode7 text remain 0x1000, H-COMP 0x790, `draw_bg=0x13A8`, `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788`, resident IMEM growth zero.
- Dedicated run **`36474172645`** and generic **Build and Validate `36474172555`** were triggered. The dedicated workflow intentionally still carries the previous exact ROM pin, so its first acceptable stop is a stale-pin measurement after source/binary/ABI gates; semantic capture is not authoritative until repinned to the newly measured runtime.
- **Falsifiers:** fixed ABI moves, branch-delay audit rejects the compaction, same-frame setup still leaves TS tag sentinel, BG2/presence differs from expected `0x1400`, absent baseline does not become renderer-owned `0x0400`, Main/provenance drifts, or generic CI regresses.

### REJECTED LAYOUT ATTEMPT — same-frame setup moved internal overlay return (2026-09-28 UTC)

- Candidate `dae28945adbbd332440a15d0a8be3c7bcefc2b79` did **not** reach ares semantics. Dedicated run **`36474172645 FAILURE`** passed guest/oracle self-test and compiled, then the executable ABI contract stopped it because resident `next_layer` moved **`0xA4001364 -> 0xA4001370`**.
- Evidence artifact **`10992159547`**, digest **`sha256:6adf99bcdc25bb7bdf32eaa902377376881e8c4d09fbad7f5ebe8af06aa90f10`**. Failure is **LAYOUT/CONTRACT ONLY**; it says nothing yet about whether same-frame TS Z binding fixes the semantic carrier.
- Cause is understood: the three setup instructions are before `next_layer`; the delay-slot + 8-byte padding compensation occurs after `next_layer`, so it preserves later `draw_bg` placement but cannot preserve that internal H-COMP return address.
- Audit found the branch candidate uses the literal `0x1364` only in the H-COMP return bridge and executable contracts; ordinary resident branches use the assembler label. Canonical frozen public entrypoints remain `draw_bg=0x13A8`, `hcomp_screen_switch=0x1760`, and `draw_mode7_entry=0x1788`.
- **Decision:** do not hide this by weakening the contract. Either preserve `next_layer` with a real pre-boundary size recovery, or explicitly move the internal bridge together with all contract/reference users after proving it is not an external ABI. No semantic conclusion is drawn from this run.

### IMPLEMENTED — pair internal next_layer bridge for current-frame TS Z candidate (2026-09-28 UTC)

- Follow-up candidate **`phase4/gate-c-hcomp-transparent-sub-clean@8a487570ce9053d6a49c4b97fdd7c8bfb9248840`** keeps the same-frame TS-Z hypothesis and explicitly pairs the H-COMP return bridge with the resulting resident layout.
- The added setup advances internal `next_layer` from `0xA4001364` to **`0xA4001370`**. Audit of the candidate found this numeric address is an internal overlay return consumed by H-COMP/contracts; assembler-resolved renderer branches use the label. H-COMP now returns to `0x1370`, and the executable contract still checks the address exactly rather than dropping the invariant.
- Public/frozen entries remain required unchanged: `draw_bg=0xA40013A8`, `hcomp_screen_switch=0xA4001760`, `draw_mode7_entry=0xA4001788`; regular/Mode7 0x1000, H-COMP 0x790 and zero resident-IMEM growth remain mandatory.
- Dedicated **`36475026226`** and generic **`36475026085`** triggered. Workflow ROM pin remains deliberately stale until this exact candidate passes source/binary/ABI/delay-slot gates and measures its runtime hash.
- **No semantic claim yet.** If layout/branch-delay gates pass, repin only the exact measured ROM and rerun the same strict three-state ares oracle.

### CONTRACT REPAIR — regular and Mode7 next_layer are intentionally distinct (2026-09-28 UTC)

- Dedicated `36475026226` on `8a487570...` stopped in the executable contract after proving the regular bridge at `0xA4001370`: the shared assertion incorrectly required Mode7 to move too. Actual Mode7 `next_layer` correctly remained **`0xA4001364`** because the same-frame TS-Z setup is regular-renderer-only.
- This is **REJECTED AS SEMANTIC EVIDENCE / CONTRACT FALSE NEGATIVE**, not a runtime failure. The run never reached ares.
- Host-only contract repair **`c65aff7911fc19501a4ed30004d769f4806b16ec`** now requires regular `next_layer=0x1370` and Mode7 `next_layer=0x1364` separately while retaining all shared frozen entrypoints and text-size checks.
- Semantic runtime source is unchanged from `8a487570...`; workflow pin remains stale by design until the corrected contract measures the exact ROM/ELF.

### MEASURED — exact same-frame TS-Z runtime ready for semantic rerun (2026-09-28 UTC)

- Generic **Build and Validate `36474172555 SUCCESS`** on semantic source `dae28945...` completed normal build, PROFILE build and pinned Mupen/LLE smoke green. Build artifact **`10993415178`**, digest **`sha256:f79f58187699b8bdc93be1fa1b4ef51358fca6fcace86e8d59e2b1693177492f`**.
- First-hand hashes from that exact build artifact: ROM **`9f719b3bc91d836e80ec8242a335eaa8cc979a3cac198a7c47f8075231922e35`**, ELF **`dec697edfe773009c6d8f074c8590901716babffcd5e2918672afa27fa140646`**.
- Host-only `c65aff7911fc19501a4ed30004d769f4806b16ec` changes only the regular-vs-Mode7 `next_layer` contract; semantic runtime source is unchanged. Therefore the measured ROM/ELF remain the exact runtime to pin.
- **Immediate action:** update only the dedicated workflow ROM pin from `c073800b...` to `9f719b3b...`, rerun pinned ares, and accept only if the three states prove renderer-owned `0x0400` absence, `0x1400` BG2 presence, correct source code/HALF-effective bit, invariant Main provenance and exact color result.

### RERUN CHECKPOINT — exact same-frame TS-Z runtime pinned (2026-09-28 UTC)

- Workflow-only head **`phase4/gate-c-hcomp-transparent-sub-clean@f50dff66145feb047832699e845835cae379a3c5`** pins exact ROM **`9f719b3bc91d836e80ec8242a335eaa8cc979a3cac198a7c47f8075231922e35`**; semantic runtime remains the current-frame TS-Z candidate from `8a487570...`.
- Dedicated **`36475524327`** and generic **Build and Validate `36475524281`** are running. The dedicated result is now allowed to reach first-hand ares semantics; there is no intentional stale-pin stop remaining.
- **Acceptance remains strict:** fixed-direct+HALF must preserve HALF; live Sub present+HALF must use BG2/live Sub; Sub absent+HALF must show renderer-owned absence tag `0x0400`, fixed fallback source code and pixel-local HALF suppression. Main/provenance/guards/fence/ABI must remain exact.

### PIN CORRECTION — generic artifact hash is not dedicated-build authority (2026-09-28 UTC)

- Exact-head dedicated **`36475524327 FAILURE`** passed the corrected executable contract, all frozen public entries, regular/Mode7 0x1000, H-COMP 0x790 and all branch-delay audits. It then stopped only at the ROM pin **before wrapping/capture**.
- That dedicated build measured ROM **`188bb47fe379c277dbad084c6e6c6e90015c9e5b80d76ecd8044df02e92473ea`** and ELF **`659214f3c8e01a553262cb43faa1dd19bebbe3324611dfe52f97511acd65e290`**. Evidence artifact **`10994070811`**, digest **`sha256:2e0dc6eb89a1bdbcf796bde824547eb29ef046b92c4ce2b074308a20134f1071`**.
- **REJECTED AS PIN AUTHORITY:** ROM `9f719b3b...` taken from the generic build artifact. Although useful as hygiene evidence for the same source, it is not byte-identical to the dedicated exact-build path and therefore must not seed this workflow's ROM pin.
- **Durable rule:** for dedicated semantic workflows, measure the exact runtime in that workflow after its source/binary/ABI gates; do not substitute a generic-build ROM hash even when semantic source is unchanged.
- **Immediate action:** repin only the dedicated workflow to `188bb47f...`. No semantic/runtime source changes are needed; first-hand ares semantics remain completely untested for this candidate.

### ACTIVE — transparent-Sub fixed-color fallback + HALF suppression discriminator (2026-09-28 UTC)

- **GATE DRIVER:** isolate the remaining second-operand/HALF interaction before moving to color windows. Hardware semantics distinguish **direct fixed-color selection** from **Sub selected but transparent at this pixel**: the latter falls back to fixed color and suppresses HALF.
- Start from exact validated parent **`73d9d08037151457e53c6150c8ebeeb5a176f4ac`**. Preserve the now-validated add/sub/half arithmetic, BG1 winner/eligibility, operands where applicable, compact provenance, section geometry, ABI and one-frame fence.
- First audit the current live-Sub representation to determine whether transparency/coverage survives in the RGBA5551 sample or another already-existing carrier. Do **not** invent a new per-pixel surface until evidence shows the current carrier cannot distinguish a real Sub pixel from transparency.
- Minimal intended discriminator, subject to that carrier audit:
  1. **Direct fixed + HALF** (`CGWSEL bit1=0`) as control: fixed color selected explicitly and HALF remains active.
  2. **Live Sub present + HALF** (`CGWSEL bit1=1`) as the already-validated normal-half control.
  3. **Sub selected but transparent + HALF**: second operand must fall back to fixed color **and HALF must be suppressed** for that pixel.
- Require the source/fallback decision, half-enable decision, Main winner/provenance, section carriers and exact RGB555 result to agree; keep add/sub operation itself fixed so only transparency/fallback semantics vary.
- Falsifiers: no trustworthy transparency carrier exists, present/transparent workloads alter Main/provenance unexpectedly, fallback chooses the wrong operand, HALF is not suppressed only in the transparent-Sub case, fixed-direct control is also suppressed, ABI/guards move, or generic build/smoke regresses.
- **Immediate action:** audit current Sub pixel coverage/transparency evidence and historical clean branches; then design the smallest present-vs-transparent test without importing the old cumulative compositor or beginning window semantics.


### Historical authority — prior CGADSUB operation-selection stage

This snapshot describes that earlier validated stage; the current candidate and next action are in the latest RESUME HERE checkpoint.

- **Phase:** M3 / **Gate C — base-system fidelity and compatibility**.
- **Integrated truth:** `master@7cc8facfe8643fb85888f301f79995575830521d`, merge of PR #18 (“preserve CGRAM epochs through RSP replay”).
- **Open PRs:** none at this checkpoint.
- **Current candidate:** `phase4/gate-c-hcomp-cgadsub-modes-clean@73d9d08037151457e53c6150c8ebeeb5a176f4ac`.
- **Semantic runtime commit:** `dee7fdb10731cb059a985ea45e8642587c6a8143`; later commits are host/oracle/workflow/exact-pin only.
- **Exact runtime hashes:** ROM `53df19d9d0b9f0996d1bb7aca15f744ab28e67525362656ef01f726eaa9e576c`; ELF `fa9e863fd4a7927e3591f86ad54154b1e8d156c3f6dc147cbca87bcea6ea8483`.
- **Classification:** **ARCHITECTURE PROOF / VALIDATED / STAGE CLOSED** for clean CGADSUB add/subtract/full/half selection on the validated live Main/Sub/provenance path.
- This candidate is **not merged** and is not yet production compositor authority.

### Final clean BG1/BG2 winner-provenance result — VALIDATED

- Same-head generic **Build and Validate `36373014434 SUCCESS`**: normal build, PROFILE build and pinned Mupen/LLE smoke all green.
- Dedicated **Gate C H-COMP Main Provenance Clean `36373014424 SUCCESS`** on exact head `ef1c3783...`.
- Final evidence artifact **`10949629224`**, digest **`sha256:3c8b5e660706cfccccbaebb5c8ea13689be112cd6c4fadd5271fd8aa015a5f50`**.
- Classifier: **`HCOMP_MAIN_BG12_PROVENANCE_GATING_VALIDATED`**, `passed=true`, `color_operands_stable_within_winner_pairs=true`, `provenance_stable_within_winner_pairs=true`.
- Exact executable contract remains:
  - `draw_bg=0xA40013A8`
  - `hcomp_screen_switch=0xA4001760`
  - `draw_mode7_entry=0xA4001788`
  - regular/Mode7 RSP text **0x1000 / 4096 B** each
  - H-COMP text **0x790 / 1936 B**
  - `resident_imem_growth=0`
  - provenance scratch `0xA00E2000..0xA00E317F`
  - sample `0xA00E2018`
  - Set-Z underflow base `0x000DFD00`
  - provenance lifetime **section0 TM only**
  - disable boundary **TM end before next section**.

#### Four-state first-hand matrix

| Case | Main winner / color | Sub color | Provenance | CGADSUB | Gate | Result |
|---|---|---|---|---|---|---|
| BG1×CG1 | BG1 red, RGB555 `0x001F` | green `0x03E0` | `0x0C00 -> mask 0x01` | `0x01` | ON | exact E1f half-add `0x01EF` |
| BG1×CG2 | BG1 red `0x001F` | green `0x03E0` | `0x0C00 -> mask 0x01` | `0x02` | OFF | raw Main `0x001F` |
| BG2×CG1 | BG2 green `0x03E0` | red `0x001F` | `0x1400 -> mask 0x02` | `0x01` | OFF | raw Main `0x03E0` |
| BG2×CG2 | BG2 green `0x03E0` | red `0x001F` | `0x1400 -> mask 0x02` | `0x02` | ON | exact E1f half-add `0x01EF` |

- Exact mailboxes:
  - BG1×CG1: `001F,03E0,01EF,0001,0C00,0001,0001,0000`
  - BG1×CG2: `001F,03E0,001F,0000,0C00,0001,0002,0000`
  - BG2×CG1: `03E0,001F,03E0,0000,1400,0002,0001,0000`
  - BG2×CG2: `03E0,001F,01EF,0001,1400,0002,0002,0000`
- In every state the compact provenance surface is exact: **2,048 active winner-tag words + 192 sentinel border words**, and **both prefix and suffix guards are intact**.
- BG1 states: semantic Main exact **2,048 red `0xF801` + 2,432 sentinel**; Sub exact **2,048 green `0x07C1` + 192 sentinel**.
- BG2 states: semantic Main exact **2,048 green `0x07C1` + 2,432 sentinel**; Sub exact **2,048 red `0xF801` + 192 sentinel**.
- Exactly one physical Main framebuffer is rendered in each independent capture; the other two are untouched. Physical slot identity may rotate between emulator processes and is not semantic identity.
- Both section queues independently carry the requested `TM/TS/CGADSUB/split` matrix.
- Every capture uses one fresh renderer-frame reentry with `guest_frame_delta=1`, **RSP HALT**, **DPC_CURRENT=DPC_END=0x000C58**, and `bufferBusy=false`. Pinned-ares `PIPE_BUSY=true` remains diagnostic only.

### What this proves

- **VALIDATED:** the clean regular-BG renderer can emit first-hand winner identity into a bounded per-pixel provenance carrier.
- **VALIDATED:** BG1 maps to stored winner tag `0x0C00` and native CGADSUB mask `0x01`; BG2 maps to `0x1400` / `0x02`.
- **VALIDATED:** H-COMP can consume that winner identity and gate the already-validated arithmetic path using the correct real CGADSUB bit, not a guest-hardcoded winner.
- **VALIDATED:** the compact provenance lifetime can be bounded to section0 TM and cut before any later-section RDP work.
- **VALIDATED:** the repair does not grow resident IMEM or move the frozen renderer/H-COMP public ABI.

### What this does NOT prove

- Overlapping BG priority arbitration beyond the controlled single-Main-BG workloads.
- BG3/BG4/OBJ/backdrop provenance.
- OBJ palette-group color-math exception.
- `CGWSEL` second-operand selection (Sub vs fixed color), clip/prevent/color-window semantics.
- General add/sub/half mode selection from `CGADSUB` bits; only the already-authoritative E1f half-add operation is exercised here.
- Full-band/full-frame compositor throughput.
- Production-safe real-N64 RDP→RSP ownership/fencing; the proof-time framebuffer/provenance DMA reads are architecture evidence under pinned ares.
- Real-N64 cadence/performance. Emulators remain laboratories, not final authority.

### RESUME NEXT — GATE DRIVER

**Implement CGWSEL clip/prevent on the now-isolated clean H-COMP path.**

1. Start from `phase4/gate-c-hcomp-color-window-clean@9a019599f3a5a5aafa4ffed7dd8b1135db42d809`, whose eleven-case exact-head lab result is fully inspected.
2. Freeze raw Main/Sub ownership, BG1 winner/eligibility, source selection, transparent-Sub fallback/HALF suppression, bounded 8/224 geometry, guards, ABI and one-frame fence.
3. Preserve the precommitted eight-state reference matrix: all five controls stay `01EF`; clip-inside becomes `03E0`, prevent-inside `001F`, both-inside `0000`. Require actual clip/main-effective, prevent/gate and HALF evidence, not just a coincidentally correct output.
4. Apply Main clipping before arithmetic; clipping must preserve BG winner eligibility and suppress HALF. Prevent math independently. Color-window selection is independent of TMW/TSW layer-window enables.
5. First audit loaded-slot budget and any resident helper call. Only `13A8..178F` is overwritten by H-COMP; leading ELF padding is not loaded. Reuse existing carrier/state where sufficient, preserve public entries and resident IMEM, and do not revive old cumulative branches.
6. Build exact runtime authority in the dedicated workflow, retain normal/PROFILE/delay-slot/smoke gates, and rerun all eight cases plus the three frozen source controls. The current green diagnostic explicitly validates bug reproduction, so create a strict repaired-semantic acceptance mode rather than relabeling it.
7. After this repair, expand remaining CGWSEL modes and W2/inversion/combine edge coverage; then use the SMW iris regression as the representative software target. ALttP rain/tree compositor follows per Road.

**STATUS: color-window isolation CLOSED / measured gap; clip/prevent runtime repair TODO; M3/Gate C remains ACTIVE.**

---

## Durable Gate-C chain retained in the live handoff

### 1. PR #18 CGRAM epoch transport/replay — MERGED

- `master@7cc8facf...` includes PR #18.
- Typed CGRAM events survive CPU capture → section queues → RSP replay/raw shadow.
- This is integrated truth and remains the representation source for later H-COMP work.

### 2. Clean first-hand Main/Sub color ownership — VALIDATED

- Final host-only head `phase4/gate-c-hcomp-main-sub-pixels-clean@4ec7fe3dbf2c0249221730dae0b2c7b06cf9fabe`.
- Dedicated `36356687503 SUCCESS`, artifact `10944247264`, digest `sha256:e3adf4e0eeb13f18054ca9615915fa76f48329039715e30df2a03de41737a544`.
- Compact Sub `0xA00E4000`: exact green active strip.
- Main: exact red active strip in **published physical rows8..15**, with rows0..7 untouched.
- **REJECTED:** old row0-only Main oracle; its failure was a host false negative, not a target-switch defect.

### 3. Clean live BG1 CGADSUB gating — VALIDATED

- Final host-only head `phase4/gate-c-hcomp-cgadsub-gating-clean@69c64fa09d22d71bb653701b0300da6f9ac1eb12`.
- Dedicated `36358604516 SUCCESS`, artifact `10944812755`, digest `sha256:fb5fdb747468ddc584d005851843e0b8f0818e4342166348e1e697c610113f1f`.
- Same rendered Main/Sub pair: CGADSUB BG1 disabled → raw Main; enabled → exact E1f `0x01EF`.
- **REJECTED:** requiring the same physical triple-buffer slot across independent emulator processes.

### 4. Clean BG1/BG2 winner provenance + CGADSUB eligibility — VALIDATED

- Current stage described above.
- First semantic attempt proved tags/gates but wrote Z beyond its owned arena.
- Final TM-end lifetime repair closes those bounds without weakening the oracle.

### 5. Clean CGWSEL second-operand source selection — VALIDATED

- Final head `phase4/gate-c-hcomp-cgwsel-source-clean@762250a95c6d2ef4bda1b2f4d82e255c43889c83`.
- Dedicated `36377395203 SUCCESS`, artifact `10951817024`.
- Same live Main/Sub/provenance yields fixed-color result `0x3C0F` at `CGWSEL=0x00` and live-Sub result `0x01EF` at `CGWSEL=0x02`.

### 6. Clean CGADSUB add/sub/full/half operation selection — VALIDATED

- Final host-only head `phase4/gate-c-hcomp-cgadsub-modes-clean@73d9d08037151457e53c6150c8ebeeb5a176f4ac`.
- Dedicated `36419920887 SUCCESS`, artifact `10968609752`.
- Exact four-state results: add-full `0x03FF`, add-half `0x01EF`, sub-full `0x001F`, sub-half `0x000F`, with invariant Main/Sub/provenance.

### 7. Transparent-Sub fixed fallback + HALF suppression — VALIDATED

- Final host-only head `phase4/gate-c-hcomp-transparent-sub-clean@5e84c8095bdce0385a8832cccec47d41521cc9b6`.
- Generic `36580550048 SUCCESS`; dedicated `36580550081 SUCCESS`, artifact `11039832437`, digest `sha256:5cc42461f6eddd9b508afea12d54e04f2b7b10ea11b237365c65055971fd66e6`.
- Exact source matrix: direct fixed+HALF -> `0x3C0F`; present live Sub+HALF -> `0x01EF`; transparent selected Sub -> fixed fallback with HALF suppressed -> `0x7C1F`.
- Existing compact Z16 TS tag distinguishes present `0x1400/1` from absent backdrop `0x0400/0`; no new per-pixel surface is required for this semantic rung.
- Final absent queue is bounded exactly at 8/224 with TS=0 throughout; the prior line-0 split was a guest WH0 reset bug, not a runtime requirement.

### 8. CGWSEL clip/prevent color-window isolation — CLOSED / MEASURED GAP

- Diagnostic head `9a019599f3a5a5aafa4ffed7dd8b1135db42d809`; generic `36629523185 SUCCESS`, dedicated `36629523682 SUCCESS`, artifact `11062067939`, digest `sha256:0abecf86f0a87b958cd261aefdf1c7b244d037afb4cea38083bf79ffe57e8fe8`.
- Eight coherent/fenced window captures keep the same `01EF` result despite correctly delivered window controls. Five reference controls agree; clip-inside/prevent-inside/both-inside should be `03E0/001F/0000`.
- All three transparent-Sub source/HALF controls still pass. Runtime is unchanged.
- This closes the reproduction/isolation question only; runtime clip/prevent repair and SMW correctness remain TODO.

---

## Rejected explanations / durable negative knowledge

- **REJECTED:** build green implies semantic correctness.
- **REJECTED:** host/emulator full speed implies N64 full speed.
- **REJECTED:** pinned-ares `PIPE_BUSY` must clear for a completed submitted list. In the pinned ares model it remains sticky without Sync Full; completion authority for this lab is RSP HALT + `bufferBusy=false` + `DPC_CURRENT==DPC_END`.
- **REJECTED:** GDB R4300 single-step at the prelaunch fence. It can cross the `jr` delay slot and clear SP HALT. The validated laboratory fence uses the two-breakpoint no-single-step protocol.
- **REJECTED:** semantic Main lives in published framebuffer rows0..7. Validated mapping is rows8..15 for this workload.
- **REJECTED:** physical FB1/FB2/FB3 slot identity is stable across independent ares processes.
- **REJECTED:** a compact Z arena is safe merely because intended color pixels occupy only the compact strip. Z-update lifetime is global RDP state and must be explicitly bounded.
- **REJECTED:** disabling Z in the *next* TS→TM switch is sufficient. Section backdrop work occurs before that switch; the cut must happen at **TM end before next_section work**.
- **REJECTED:** weakening guards or allocating a large full-frame provenance surface to hide the spill. The compact E1c-style ownership model won after correcting lifetime.
- **REJECTED:** importing the old cumulative E2g/E3/E4 compositor as the clean solution. Historical branches are concept/evidence references only unless a specific piece independently earns reintroduction.
- **REJECTED:** the `0ac4507...` all-sentinel absent Sub capture proves the strict blue Sub-surface oracle is wrong. The all-sentinel state was caused by a guest-only zero-height line-0 section; the corrected VBlank WH0 reset restores the exact blue absent Sub surface and passes the unchanged oracle.

---

## Laboratory / validation boundaries

- Pinned ares: `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`, N64-only, RSP recompiler forced off for the established proof lab.
- Mupen/LLE smoke is a generic hygiene check, not semantic color-math authority.
- Real N64 remains final authority for cache/TLB, RSP/RDP synchronization, DMA/bus behavior, VI/AI cadence and performance.
- Current proofs are synthetic architecture/measurement proofs. They are not broad software-compatibility claims.
- Do not upload commercial ROMs to the repo. Continue using deterministic/open diagnostic guests until a representative software rung is needed.

## Fixed engineering constraints carried forward

- Preserve frozen renderer/H-COMP overlay addresses unless a deliberate architecture change is separately justified and measured.
- Preserve the validated semantic screen order: low byte TS, high byte TM; shared-screen behavior must not be silently reintroduced from old workarounds.
- Preserve compact Sub ownership and current Main published row mapping as controls while testing color-math semantics.
- Prefer one semantic variable per experiment: `baseline → hypothesis → controlled change → measurement → interpretation → decision`.
- Keep proof-only provenance/fences classified as architecture evidence until a production-safe design wins on real hardware constraints.
- Every candidate must retain normal build + PROFILE build + branch-delay checks; pinned Mupen smoke is generic hygiene, pinned ares dedicated artifacts are experiment authority for these current synthetic discriminators.

## Road-to-1.0 direction

The target is unchanged: N64 real, correct native cadence, one SNES frame per corresponding native frame, frameskip 0, full-rate SPC700/APU and correct audio, high CPU/PPU/DMA/HDMA/timing fidelity, broad compatibility, no per-game manual modes, DSP-1 family, SuperFX/SuperFX2, SA-1, and final hardware validation.

Current Gate-C work is moving that road because it is replacing the inherited renderer's Main/Sub/color-math approximation with measured, bounded semantics. Do not let the proof harness become a second project; each next batch must close a compositor/fidelity uncertainty needed by the Road.
