# Consolidation and integration audit - 2026-10-15

Operational authority: the user's current consolidation/integration request.
Earlier CONTINUITY entries are evidence/history, not a queue of live requests.
Read ROAD_TO_1_0 from master (it was absent in the continuity checkout), ROADMAP,
PROFILING, VALIDATION and the current handoff. Master was freshly fetched at
7cc8facfe8643fb85888f301f79995575830521d (PR18, September27). Its five recorded
CI workflows succeeded; that historical result does not qualify new ports.

PR21 is a draft at de30c75782843ef7c113177fa272f9cdd0310d5a: 275 commits,
310 changed files. Never merge it wholesale. The latest successful Build/Ares/
CGRAM receipts cover workflow head238170ab and its unchanged runtime; they are
not unexplained green status for every later commit or opt-in configuration.
The [branch inventory](evidence/integration-branches-2026-10-15.json) records all
34 relevant current experimental/retained/master tips, divergence and actual
runtime deltas. Legacy phase2 branches already represented in master are not
new candidates. [CI inventory](evidence/integration-ci-audit-2026-10-15.json).

Status means suitability of the component, not whole-title/1.0 acceptance:
VALIDATED = all applicable stated gates passed for that exact scope;
CANDIDATE = useful result with a finite remaining qualification/port;
BLOCKED = a named gate currently prevents integration;
REJECTED = its stated value/correctness gate failed;
SUPERSEDED = retained evidence replaced by a later qualified implementation.
Diagnostic tools are identified separately from production runtime changes.

| Component / retained authority | Status | Integration disposition and exact remaining gate |
| --- | --- | --- |
| Master PR18 / integrated M1 | VALIDATED (historical scope) | Stable integration base; historical homebrew GateB is not the expanded commercial corpus. |
| Complete unrolled APU JIT reset, f4e061c6 subset | CANDIDATE, PR22 | Clean master extraction implemented; every lookup entry still invalidated. Normal/PROFILE builds, exact coverage/owners and three mutants pass. New-SHA CI/APU cycle-span execution outstanding. No native FPS claim. |
| R33 GAIN accumulator owner,5b0cb2f3 subset | CANDIDATE, PR23 | Clean master repair implemented for the legacy mixer. 2048 handler and2048 independent scheduled stereo cases pass on normal/PROFILE; native historical handler16 failures to0. New-SHA CI outstanding. |
| Live-group JIT invalidation,ca3f6f59 | CANDIDATE | Separate from PR22: prove publication of every nonzero lookup owner, cold/stale/reset/cache replay on clean master; do not smuggle it into the full-clear extraction. |
| CPU branch/ROM-cache maintenance and section coalescing in A13 | CANDIDATE | Port with exact bank/event/branch-delay guards, then representative combined baseline. Dependencies are not already in master. |
| OBJ culled-row continuation30da21c8/990ad7c5 | BLOCKED as standalone master patch | Master lacks the added row-cull predicates/labels. Carry both predicates and continuation as one bounded renderer component with compiled progression and fixed-slot gates; do not copy only the tail fix. |
| A1..A13 exact compositor/window/epoch work,b4206144 | CANDIDATE | Split source/consumer/geometry/ownership components. Preserve fixed .org slots, DMA retirement and primary/reference pixels. Existing native scene evidence remains scoped; no bulk275-commit merge. |
| A14 packed math/direct Sub-presence,018630ff | SUPERSEDED for immediate integration | Retain exact arithmetic/native negative history. R44 changes the same presence representation; select one consistent renderer stack, not additive percentages. |
| TMEM atlas/coordinate and R36 resident cache | REJECTED as standalone gain | Global atlas rain loss and R36 +0.395% fail material gates. Retain any prerequisite code only if a selected later component proves it necessary and passes its own gates. |
| R38 decoder relocation/span-only | REJECTED / superseded by R40/R43 | Native story regression is diagnosed; do not reintroduce relocated decoder on the no-Sub path. |
| R40 adaptive spans plus paired diagnostic arenas | CANDIDATE runtime; diagnostic arena prerequisite separate | R43 removes no-Sub hot dispatch. Reuse exact RSP/producer proof; qualify the clean-master dependency chain before R44. |
| R41 Ares SDL lab dependency fix,794b5530 | CANDIDATE tooling | Lab infrastructure only. Reuse the corrected upstream SDL pin if the unchanged lab build fails; no emulator performance credit. |
| R42 coverage-tag feasibility | VALIDATED diagnostic primitive / SUPERSEDED production direction | Original1024 rectangles establish a bounded alpha/coverage property. It is not an independent runtime speedup; R44 is the production candidate. |
| R43 adaptive no-span,4382ae80 | CANDIDATE prerequisite | Rain36.804 vs32.289 corrected control; story residual remains explicit. Port coherent immutable overlay plus guards; broader native/clean-head CI before integration. |
| R44 Sub-alpha,7a83d498 / CI02392af | BLOCKED for production integration | Material ALttP rain40.540954 vsR43 36.804012; story56.089884 vs corrected56.149815 leaves0.106735% residual. DKC10 images/4PCM pass, no material DKC gain. Build38337117404, repaired CGRAM38337797903/Ares38337800049 pass. Missing clean-master renderer dependencies, a discriminating resolution of the residual and native Mode7 against an appropriate predecessor (R45's on/off race does not prove R44 vsR43). |
| R45 dense row backdrop,313642af / retainedfa77692e | BLOCKED | Same240 absolute DKC endpoints13.753867 to28.702821Hz, exact images/PCM; full CI38354690610/38354693122/38354695628 succeeds. Story1000 absolute endpoints56.162905 to55.910416 (-0.449566%,80.408us); Mode7 -0.135081%. These unresolved costs block promotion. Correct scissor adoption is mandatory. |
| First R45 missing-scissor implementation,9e1194f | SUPERSEDED (incorrect) | Native27-pixel failure preserved; repaired1fcc940 and scalar/metadata lineage replace it. Never integrate the defective artifact. |
| R45 run producer,c623d918 | REJECTED cost remedy | Story55.888611 vs dense55.910416; does not recover loss. Preserved on experiment/main-row-runs-r45, dense source restored on R45. No renewed micro-tuning loop. |
| R46 constant APU RAM read | REJECTED material performance direction | Both fixed native routes below the declared2% threshold; preserve code/proof, no broader port campaign. |
| R19 pitch cache,84531758 | CANDIDATE | Independent bounded native image/PCM/performance proof. Port both write handlers and cache lifecycle to clean master, run linked byte/address/caller tests and new-SHA CI. It is not an audio-completeness fix. |
| R20 BRR arithmetic,bbe46447 | CANDIDATE | Primary numeric decoder/57344 linked cases and actual native observed chunks support correction. Extract signed floors, invalid ranges, clamp/wrap together; legacy mixing is separate. Clean-master port/CI and cost check pending. Do not demand the defective old PCM as oracle. |
| R22 KOFF release,1b123980 | CANDIDATE | Native six release endpoints plus directed envelope/caller checks. Port release/ADSR/KON interactions together; full latch/KON-delay accuracy remains open. Clean-master proof/CI pending. |
| R23 dry mixer,4f3cadb2; cache/basec77634ae/36883ee5 | BLOCKED as default integration | Arithmetic correction is useful, but complete dry scheduler/layout/cost must include R32+R33 and retain known timing/echo/Gaussian limitations. Port as a separate coherent component, not a flagged diagnostic package. |
| R32 dry-master HI/LO,0675f15a | VALIDATED within corrected dry path | Required correctness prerequisite when dry mixing is selected. Master lacks that multiply sequence; no standalone master patch exists. Preserve linked/dynamic spacing and native owner proof. |
| R34 complete C++ DSP direct gameplay replacement | REJECTED; VALIDATED bounded behavior oracle | Native106.56/144.15/151.16% standalone audio budget and9 checksum matches. Keep primary reference and source/license; it cannot become a gameplay default. |
| R35 timer experiment,677c9d21 | SUPERSEDED priority / CANDIDATE unmeasured code | No physical result. Do not treat fewer DIV instructions as an integration gain. |
| R47 BRR history recurrence,849412ee | CANDIDATE | Two physical pairs reproduce title~3%/room~4% gains with exact image/PCM. Needs BRR-accurate base, rain/DKC and changed-DSP CI on clean extraction. Limited value does not invalidate its finite integration queue entry. |
| R48 non-alias annotation | REJECTED | All18 emitted executable sections identical. No work removed; no runtime patch or native rerun. |
| R49 signal elision,68667b74 | CANDIDATE oracle optimization; BLOCKED gameplay | One-voice17.29% cost saving; eight voices small0.317% loss within declared guard, echo1.076% saving. Active standalone budget still144/149%. Retain oracle optimization separately from gameplay backend, pending changed-core CI. |
| R50 counter; R52 full-BRR regroup; R53 sample dispatch; R54 cache placement; R55 Gaussian CPU batch | REJECTED retained cost directions | Their physical cost gates fail; semantic/codegen/cache findings remain. R51 function residency is a diagnostic, not additive execution cost. No broadCI or kernel tuning for rejected implementations. |
| R56 Gaussian PIO; R57 thin Gaussian DMA | REJECTED backends | R57 physical restoration passes, but PIO7.311333us vsDMA7.576333us and13.482667us max fail the7.8125us window. Correct arithmetic/restoration does not qualify transfer cost. |
| R58 batched BRR backend | REJECTED backend; VALIDATED bounded arithmetic/window primitive | Native32-output CPU~14.54us vsPIO21.924/DMA22.281us including preparation; exact samples and restoration pass. No whole-resident-DSP cost result follows. |
| R59 preparation-only repair | REJECTED | Even hypothetical free preparation leaves3.72%/1.26% savings, below40% and engineering window. Preserve attribution. |
| R60 resident standalone BRR DMA | REJECTED standalone backend | Scalar14.567us vs15.103667us, max23.232us; protocol improves R59 but loses to scalar. Carry knowledge only into a representative whole-DSP test. |
| Scene-state continuation/S1, d7a071a2 | CANDIDATE diagnostic | Native ordinary/Mode7 continuation and owners are useful for bounded validation; not user-facing state support or proof of arbitrary cross-build state transfer. |
| R61 full-DSP window/controller/upper owners | CANDIDATE architectural prerequisite | Host full-state/echo/order proof and native8MiB owner/restore pass; actual SPC pre-access/fetch/echo/cache/JIT interaction remains unintegrated. No whole-resident-DSP backend/cost yet. |
| R62 FPU/RSP/memory inventory,481ded29 | VALIDATED bounded diagnostic facts | Preserve verified8MiB/ownership and existing resource-use inventory. No spare independent CPU or inferred game speedup. No new FPU/RSP/Expansion Pak campaign without a quantitative gate hypothesis. |
| R63 bus clock/fetch/address/DBNZ | BLOCKED | Directed semantic repairs are retained default-off; incomplete256-opcode/runtime-fetch/pre-access/echo invalidation bridge. A partial bridge or incorrect cost control cannot become default. |
| R63 eager/lazy opcode guards | REJECTED cost direction; CANDIDATE correctness prototype | Eager adds0.966007ms; lazy recovers0.346673ms, below declared0.483004ms gate. Stop guard tuning, preserve exact dirty/NZ/tag proofs. |
| USB menu/transport/recorder/scene observers | CANDIDATE diagnostic infrastructure | Separate source/tooling PRs after paired-menu rebuild, ABI/owners/readback/recovery gates. Do not count tools as integrated emulation gains. |
| Pinned SDK CI repair,PR24 | CANDIDATE infrastructure | Unblocks missing GHCR image; verified release SHA256 plus fixed upstream source. Normal/PROFILE and CGRAM have already executed successfully; complete clean-commit lab gates pending. |

## Execution queue and stop conditions

1. Finish PR24's intact build/emulator gates, then qualify PR22/23 on the fixed
   SDK. Resolve actual failures rather than relabel historical green runs.
2. PR22/23 already have clean-master source extractions and a local combined
   baseline917b160. Qualify their combined build/state/image/audio behavior;
   publish exact artifacts and gates. No sum of historical percentages.
3. Select the next independent audio correctness port from R20/R22, then R19/
   R47, with bounded clean-head proofs. In parallel planning only, decompose the
   R44 renderer dependencies; R45 cannot merge while its costs remain unresolved.
4. A real native baseline requires the exact integration source and compatible
   diagnostic transport/settings, not substitution of R44/R45 results. The clean
   baseline currently has no remote bridge. Decide its bounded measurement path
   before loading a non-returnable image; power-cycle recovery requires a human.
5. Only after useful integration and representative combined evidence, resume
   resident full DSP with one integral cost proof: full8-voice/BRR/Gaussian/
   envelopes/noise/PMON/echo/FIR/clock/latch work, SPC-visible RAM/register barriers,
   CPU preparation/cache/DMA/synchronization, renderer coexistence and restoration.
   Compare the complete path to scalar on equal work. No more isolated kernels.

All private ROMs/SAVs/states/images/PCM/raw captures/game-derived hashes remain
local. The classification preserves failures and prior artifacts. There is no
new presentation60/50Hz, complete DSP/DAC, title/corpus or chip-support claim.
