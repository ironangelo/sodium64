# Consolidation and integration audit - 2026-10-15

Renderer drafts, 2026-11-11. R43 is PR40 against PR32. R44 is PR41
against PR40. Both are opt-in. Linked Math and RDP consumer replays
pass on R44. Paired native ALttP, Mode 7 and PR32 DKC1 intro cadence
remain open. COM3 returned and R17 install/readback and menu recovery 0
passed. The reference-launch transport gate remains pending.
[Current renderer and hardware evidence](evidence/integration-renderer-pr40-pr41-2026-11-11.json).

Latest APU gate, 2026-11-09. PR39 corrects the actual stale lookup and
old cycle debit after changing the APU clock in the menu. Full linked
reset and both clock directions pass, with exact CI USB admission.
[Clock transition evidence](evidence/integration-apu-clock-invalidation-2026-11-09.json).

Latest renderer extraction, 2026-11-09. PR38 has exact-head Gate C
replay, linked identical-write tests and USB admission. The local queued
combination fits and passes its linked software checks. The
November 11 R17 restoration passed.
[CGRAM and combined source evidence](evidence/integration-cgram-identical-2026-11-09.json).

Latest R19 gate, 2026-11-09. Draft PR37 ports the pitch cache directly
to master and passes linked arithmetic and exact CI USB admission. The
native attempt lost the cart on the master reference before launch
acknowledgement. R19 native comparison remains pending.
[R19 evidence](evidence/integration-r19-pitch-port-2026-11-09.json).

Latest audio gate, 2026-11-09. PR35 is ready for review. Both audio
drafts pass their four exact-head CI workflows and scoped native audio
comparisons. PR33 matches 252 release samples per event at two aligned
cuts with the other channel identical. PR36 matches aligned PCM across
all four BRR filters. Separate bench integration and audio-only review
precede sustained representative combined measurements.
[Native KOFF evidence](evidence/integration-native-koff-tail-2026-11-09.json).

Latest DKC1 gate, 2026-11-09. PR32 exact aligned native RGB and PCM pass at
two checkpoints. DKC1 intro polled boundary throughput is lower across three
approximately matched bands. The separate quiet 20-second interval stopped
without a closing sample after Windows removed the USB function. Exact R17
restoration and 95 seconds of idle menu USB passed. PR32 stays draft and
blocked for default promotion. House/rain, SMW, Mode 7 and paired quiet
timing remain open.
[DKC1 evidence](evidence/integration-faithful-dkc1-2026-11-09.json).

Previous native gate, 2026-11-09. The first actual task captured a Main
RSP call to the C4C window delay instruction that clobbered its return.
PR32 at 3e1c9a99 fixes the shared entry in two Main words. The fixed
task naturally halts and the ordinary local build starts, progresses and
returns by software. R17 readback passed. All six exact-head workflows passed. ALttP load lost USB before menu
acknowledgement and habitual restore/readback passed after reconnect.
Broader native fidelity and cadence remain pending.
[Depth-entry evidence](evidence/integration-faithful-depth-entry-2026-11-09.json).

First checkpoint, 2026-11-09. PR34 is merged at master `c232af87`. Its host
EOF shutdown and real-cart session close are qualified. The published Latest
still contains the same two production payloads. The exact habitual R17 backup
is restored and verified from the PC. PR32 remains blocked at native startup.
Its no-USB capture header failed validation after recovery, and the previously
qualified master reference also lost USB during paired-menu launch. The USB bus loss was pending a traced reference control.
[PR34 and restoration evidence](evidence/integration-bench-eof-2026-11-09.json).
[PR32 physical evidence](evidence/integration-faithful-compositor-2026-11-08.json).

Follow-up, 2026-11-09. R17 and the master reference requalified autonomous
launch and menu return. A faithful build with the working local GCC 14.2.0
repeated the first-hello failure after launch acknowledgement, while Windows
and SC64 firmware stayed responsive. The exact habitual R17 was restored
after physical OFF/ON. The older preflight paragraphs retain their
historical scope. [Traced evidence](evidence/integration-traced-native-startup-2026-11-09.json).

Current hardware update2026-11-08: second OFF/ON and exact backup restoration
verified. Same-fixture exact-CI no-USB HW_PROFILE control installed/launched;
worker terminal0 without SRAM read. Terminal red-screen or console-OFF
confirmation is pending before safe read, then final recovery/restoration.
This supersedes the old recovery blocker; no cadence/fidelity result exists yet.

Second native control2026-11-08: exact habitual restoration passed between
runs, but the same CI USB ELF with pinned CI-source packaging repeats first-hello
failure. Packaging alone is insufficient. Second restoration PENDING; next use
the existing exact-CI no-USB profiler on the same original fixture, with terminal
confirmation before any SRAM read. No image/audio/timing acceptance or merge.

Material update2026-11-08: PR32 head1e96c40c passes all six exact-head
workflows and the full functional PI/TLB/window/OBJ/Math/DMA gates. First native
preflight FAILED before emulator hello after verified install and acknowledged
launch; no native image/audio/timing result. Promotion is BLOCKED on this startup
gate and subsequent aligned native fidelity/cadence controls. Root cause remains
unresolved. Candidate is installed; habitual restoration PENDING physical OFF/ON
and verified readback. October restoration entries below are historical.
[Nov8 evidence](evidence/integration-faithful-compositor-2026-11-08.json).

Material update2026-10-18: ten separate PRs24/23/22/25/26/27/28/29/30/31 are merged
into masterbac1a4df. PR30 is a host reference prerequisite only; loaded runtime images match measured48b01127. [Integration receipt](evidence/integration-master-2026-10-15.json),
[scoped native controls](evidence/integration-native-controls-2026-10-15.json),
[bridge qualification](evidence/integration-native-usb-2026-10-15.json) and
[minimal renderer repair](evidence/integration-rsp-cursor-2026-10-18.json).
PR29 is integrated after all five exact-head gates and independent native SMW
measurement; four commercial controls pass. Broader fidelity remains open.
Old profiler controls never qualify overwritten Mode7/DSP-1 banks. Retain
original failures and PC interruptions as separate outcomes.

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
| Complete unrolled APU JIT reset, f4e061c6 subset | VALIDATED and integrated, PR22 | Masterabaec99d. Exact f0618fef Build38768160265, Ares38768160462, CGRAM38795951402 and APU38768159112 pass. Normal/PROFILE/HW_PROFILE coverage/owners plus three mutants pass. All65536 entries are cleared;119 directed APU cases and halt/cache groups pass. Structural instruction reduction is not a measured native FPS gain. |
| R33 GAIN accumulator owner,5b0cb2f3 subset | VALIDATED and integrated, PR23 | Master c41631e5 contains the legacy mixer repair. Normal/PROFILE handler2048 plus independent scheduled stereo2048 cases pass; old master1792 scheduled failures become0. Six instruction words change; all other loaded bytes/extents are unchanged. Build38764135169, CGRAM38764135122 and Ares38764135187 pass on exact head93e0e0af. Historical native16 handler failures become0; broader waveform qualification remains separate. |
| Full-rate startup/menu defaults,10662795 subset | VALIDATED and integrated, PR26 | Exact587d1ac9 Build38797939600/Ares38797939482/APU38797939962 pass; merged7c3a7634. Only apu_clock42to21 and menu4to0 change; all other loaded bytes/instructions/extents match. Existing native controls ran at21. |
| APU clock change and live JIT entries | CANDIDATE, independent draft PR39 | Reproduced both stale first-block debits on master. Shared full clear fixes both transitions before menu resume and retains unchanged-clock cache hits. The runtime head passed the dedicated 119-case APU CI. Current head 46447580 adds linked controller-driven menu coverage and reproduces stale lookup on master. Physical menu behavior remains open. |
| Live-group JIT invalidation,ca3f6f59 | CANDIDATE | Separate from PR22: prove publication of every nonzero lookup owner, cold/stale/reset/cache replay on clean master; do not smuggle it into the full-clear extraction. |
| A13 identical CGRAM write, ca3f6f59 subset | CANDIDATE, independent draft PR38 | Exact raw comparison preserves bus/latch/store and backdrop behavior. Linked normal/HW/USB, exact Gate C and USB pass. Native images, PCM and cadence remain open. |
| Faithful ROM cache and S-CPU scope | Layout prerequisite; existing probe integrated | The TLB probe is already in master. PR32 adds the 194-slot cursor wrap for its compositor memory. Its S-CPU core file matches master. Keep the capacity change with its owners. |
| OBJ culled-row continuation30da21c8/990ad7c5 | BLOCKED as standalone master patch | Master lacks the added row-cull predicates/labels. Carry both predicates and continuation as one bounded renderer component with compiled progression and fixed-slot gates; do not copy only the tail fix. |
| A1..A13 exact compositor/window/epoch work, b4206144 | CANDIDATE for fidelity; BLOCKED for production | PR32 head 3e1c9a99 fixes native RSP startup and passes exact-head CI. Native DKC1 passes two exact aligned RGB/PCM checkpoints. Polled intro boundary rate falls from 48.56/58.48/59.41 to 38.72/44.84/41.33 across approximately matched bands. USB loss interrupted the paired quiet interval. ALttP house/rain, SMW, Mode 7 and paired quiet timing remain. R44/R45 stay separate. |
| A14 packed math/direct Sub-presence,018630ff | SUPERSEDED for immediate integration | Retain exact arithmetic/native negative history. R44 changes the same presence representation; select one consistent renderer stack, not additive percentages. |
| TMEM atlas/coordinate and R36 resident cache | REJECTED as standalone gain | Global atlas rain loss and R36 +0.395% fail material gates. Retain any prerequisite code only if a selected later component proves it necessary and passes its own gates. |
| R38 decoder relocation/span-only | REJECTED / superseded by R40/R43 | Native story regression is diagnosed; do not reintroduce relocated decoder on the no-Sub path. |
| R40 adaptive spans plus paired diagnostic arenas | CANDIDATE runtime; diagnostic arena prerequisite separate | R43 removes no-Sub hot dispatch. Reuse exact RSP/producer proof; qualify the clean-master dependency chain before R44. |
| R41 Ares SDL lab dependency fix,794b5530 | CANDIDATE tooling | Lab infrastructure only. Reuse the corrected upstream SDL pin if the unchanged lab build fails; no emulator performance credit. |
| R42 coverage-tag feasibility | VALIDATED diagnostic primitive / SUPERSEDED production direction | Original1024 rectangles establish a bounded alpha/coverage property. It is not an independent runtime speedup; R44 is the production candidate. |
| R43 adaptive no-span,4382ae80 | CANDIDATE prerequisite | Rain36.804 vs32.289 corrected control; story residual remains explicit. PR40 ports the immutable overlay with linked guards onto PR32. Paired native checks and PR32 acceptance precede integration. |
| R44 Sub-alpha,7a83d498 / CI02392af | BLOCKED for production integration | Material ALttP rain40.540954 vsR43 36.804012; story56.089884 vs corrected56.149815 leaves0.106735% residual. DKC10 images/4PCM pass, no material DKC gain. Build38337117404, repaired CGRAM38337797903/Ares38337800049 pass. PR41 ports R44 onto PR40 and passes linked Math/RDP consumer replay. PR32 acceptance, the story residual and paired native Mode 7 against R43 remain open. |
| R45 dense row backdrop,313642af / retainedfa77692e | BLOCKED | Same240 absolute DKC endpoints13.753867 to28.702821Hz, exact images/PCM; full CI38354690610/38354693122/38354695628 succeeds. Story1000 absolute endpoints56.162905 to55.910416 (-0.449566%,80.408us); Mode7 -0.135081%. Draft PR42 ports the scissor repair and removes the scalar Sub and non-indexed helper load. Linked proof passes. Clean-head DKC1, story and Mode 7 paired checks block promotion. |
| First R45 missing-scissor implementation,9e1194f | SUPERSEDED (incorrect) | Native27-pixel failure preserved; repaired1fcc940 and scalar/metadata lineage replace it. Never integrate the defective artifact. |
| R45 run producer,c623d918 | REJECTED cost remedy | Story55.888611 vs dense55.910416; does not recover loss. Preserved on experiment/main-row-runs-r45, dense source restored on R45. No renewed micro-tuning loop. |
| R46 constant APU RAM read | REJECTED material performance direction | Both fixed native routes below the declared2% threshold; preserve code/proof, no broader port campaign. |
| R19 pitch cache, 84531758 | CANDIDATE, independent draft PR37 | Direct master port. Normal, HW_PROFILE and REMOTE linked arithmetic and caller checks pass. All four exact-head CI workflows pass. USB has 16 bytes before CGRAM. Prior native gains belong to the original runtime. Current N64 test was interrupted on the master reference before the R19 launch. Restore R17, then rerun aligned native comparison. |
| R20 BRR arithmetic,bbe46447 | VALIDATED and integrated, PR25 | Master8da020c3. Exact19a1fbeb Build38768166170, Ares38768166071 and CGRAM38795957122 pass;57344 linked voice cases, four instruction mutants and owner guards pass. Old master disagrees on5660/7168 blocks. Combined original mixed8 retains60/60x5 natively; complete waveform/DAC/corpus qualification stays open. |
| R22 KOFF release, 1b123980 | CANDIDATE, native note-tail scope passes | PR33 exact CI and USB KOFF gate pass. Real-N64 comparison validates two aligned 252-sample release tails and all 16,384 compared right-channel bytes. R17 restore passes. Integrate PR35 separately and rerun exact-head audio-only checks. Sustained cadence, KON delay and DAC remain open. |
| R23 dry mixer,4f3cadb2; cache/basec77634ae/36883ee5 | BLOCKED as default integration | Arithmetic correction is useful, but complete dry scheduler/layout/cost must include R32+R33 and retain known timing/echo/Gaussian limitations. Port as a separate coherent component, not a flagged diagnostic package. |
| R32 dry-master HI/LO,0675f15a | VALIDATED within corrected dry path | Required correctness prerequisite when dry mixing is selected. Master lacks that multiply sequence; no standalone master patch exists. Preserve linked/dynamic spacing and native owner proof. |
| R34 complete C++ DSP direct gameplay replacement | REJECTED; VALIDATED bounded behavior oracle | Native106.56/144.15/151.16% standalone audio budget and9 checksum matches. Keep primary reference and source/license; it cannot become a gameplay default. |
| R35 timer experiment,677c9d21 | SUPERSEDED priority / CANDIDATE unmeasured code | No physical result. Do not treat fewer DIV instructions as an integration gain. |
| R47 BRR history recurrence, 849412ee | CANDIDATE, native PCM scope passes | PR36 exact CI and linked audio pass. Real-N64 PCM/register parity at the same boundary on original filter-0 and four-filter guests. Short progress and clean R17 restore pass. Integrate PR35 separately, then check the audio-only diff and rerun exact-head gates. |
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
| Optional native USB bench, PR2799008adf | VALIDATED diagnostic integration, merged | Master b40d47ca. Exact CI and native original mixed8 quiet20s/pause/step/frame/PCM/resume/menu/readback pass. Ordinary loaded bytes and both RSP banks unchanged. Scene-state continuation remains separate, not generic save-state support. |
| Pinned SDK CI repair,PR24 | VALIDATED and integrated infrastructure | Master104639bb contains the source-based SDK setup. Exact afc31351 Build38763990140, CGRAM38763990359 and Ares38763990499 pass. Compared with local reference toolchain: all executable instructions and loaded data identical except one unused empty TLS alignment metadata byte. No runtime source or performance claim. |
| Existing PROFILE/HW_PROFILE static storage | REJECTED diagnostic layout | Old actual boot destroys1156 Mode7 code and395 data bytes inside the CGRAM clear. Ordinary M1 counts do not qualify these overwritten banks. |
| PR28 profiler upper-owner repair,939aed0e | VALIDATED diagnostic integration, merged | Master d876ea29; normal bytes unchanged, all five exact CI gates pass. Linked27 owner cases/nine reader checks and native guarded capture qualify storage integrity; stalled SMW is not gameplay acceptance. |
| Decoder cursor repair, PR29 48b01127 | VALIDATED targeted repair and integrated | Master9cb13d43. Linked9984 cases/zero failures, four mutants, unchanged37 vector words and4KiB banks. All five exact CI gates pass. Native independent SMW57/58/58/60/60 replaces five0/60 windows; four commercial progress/menu/readback controls pass. Aligned PCM/head/registers exact;285 image pixels change and full fidelity remains open. |
| Complete-DSP reference corpus, PR30 31ba6429 | VALIDATED host prerequisite and integrated | Four regenerable original full-core fixtures, full-state/RAM/PCM replay and mutation controls pass locally and in Linux CI. No runtime linkage, live SPC bridge, complete resident backend or native cost result. |
| Production/laboratory release isolation, PR31 7ee13d15 | VALIDATED and integrated tooling | Masterbac1a4df. Four exact-head and four post-merge CI workflows pass. Mandatory ELF/ROM/ZIP admission and actual-laboratory rejection are integrated. Republished Latest contains exactly the two unchanged normal payloads; no runtime change or native performance claim. |
| Host USB bench EOF shutdown, PR34 87b06233 | VALIDATED diagnostic tooling and integrated | Master c232af87. All four head workflows passed, including 19 client tests on Windows and Linux. Real cart closes a debug session with CIC off and in menu. Normal loaded bytes/addresses and released payloads match. The common USB disappearance during launch remains open. |

## Execution queue and stop conditions

1. PR24/23/22/25/26/27/28/29/30/31/34 are merged. Startup selects APU 21.
   PR30 and PR34 are host tooling. PR31 enforces the normal-only release.
   Older HW_PROFILE controls bind to 8da before the separately qualified
   two-byte full-rate default change.
2. Four historical original-guest controls retain their scoped measured-ROM
   binding and owner limitations. Four new commercial controls plus an independent
   no-USB SMW capture bind to the identical current master tree; complete visual/
   audio acceptance remains separate from those completed cadence measurements.
   Exact historical Gothicvania/SRS-v5/Nova2 inputs are unavailable locally and
   their ROM handoff artifacts expired; this does not reopen the old boot-asset
   dependency in the119-case APU proof. Do not substitute corpus labels.
3. PR27/28 tools and PR29 minimal runtime repair are integrated. Four commercial
   controls and an independent no-USB SMW measurement bind to the identical
   master tree. Terminal physical recovery and final readback are VERIFIED; retain open fidelity gates.
   Scene continuation remains a distinct scoped component; no generic
   cross-build save-state claim. Current paired-menu source already reserves
   diagnostic saves separately and disables automatic mutable-file writeback.
4. PR35 is ready for review. Integrate it separately before the audio-only
   PR33 and PR36 review and exact-head checks. Native audio passes the
   stated short scopes for both. PR32 exact-head CI and two
   aligned DKC1 fidelity checkpoints passed. Its intro throughput and
   broader native fidelity/cadence block default promotion. Review the R43
   and R44 source drafts separately. R44 still needs its story and Mode 7
   comparisons against R43. R45 needs aligned story and Mode 7 costs.
   Qualify the launch transport before resuming PR37 native comparison.
5. After combined representative evidence, resume whole resident DSP via an
   integral cost proof including all8 voices, BRR/Gaussian/envelopes/noise/PMON/
   echo/FIR/clock/latch work, RAM/register barriers, preparation/cache/DMA/sync,
   renderer coexistence and restoration. No more standalone kernels.

All private ROMs/SAVs/states/images/PCM/raw captures/game-derived hashes remain
local. The classification preserves failures and prior artifacts. There is no
new presentation60/50Hz, complete DSP/DAC, title/corpus or chip-support claim.
