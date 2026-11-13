# Active operating direction - 2026-10-15

Consolidation and integration toward master come first. The destination remains
Sodium641.0 on real N64: native60/50 cadence, frameskip0, full-rate SPC700/APU,
faithful audio/graphics, broad compatibility, DSP-1, SuperFX and SA-1.

Use [the integration audit](INTEGRATION_AUDIT_2026-10-15.md), its finite queue and
the newest CONTINUITY checkpoint. Finish small clean PRs and their gates; do not
merge PR21 wholesale or move unresolved regressions into defaults. A useful
cycle ends with an integration/evidence checkpoint, not another experiment plan.

Implement and validate autonomously. Use bounded hardware only to resolve a
named gate; preserve every fidelity, timing, ownership and recovery contract.
Measure the combined integrated baseline on representative native workloads;
never add percentages from independent branches. Then resume complete resident
DSP with a representative integral architectural cost proof before more kernels.

Prior conversations and old "next" paragraphs are historical evidence. They
do not reactivate questions about FPU/RSP/Expansion Pak or grant new scope.
The previous goal text is preserved in ACTIVE_GOAL_2026-10-12_ARCHIVE.md.
ROM/SAV/state/frame/PCM/replay/raw capture/game-derived hashes stay private.
Ask only for an actual physical/access/irreversible-scope blocker; continue
independent useful work while blocked. Never claim a failed/skipped/zero-test
gate as PASS, or laboratory cadence as presentation FPS/native acceptance.

Current checkpoint, 2026-11-12. Sixteen separate PRs
24/23/22/25/26/27/28/29/30/31/34/35/36/33/43/38 are integrated in master
`b012b6b665ede6a9c537bf0e491dfdb8867835e1`. PR35 qualifies the isolated
USB bench layout. PR36 integrates the separately qualified BRR recurrence.
PR33 integrates the KOFF release tail. DKC1 exposes its cached SPC700
accumulator regression. PR43 `adf9f02e` corrects it and passed the
linked normal and REMOTE proofs, the paired DKC1 register check, both
exact native release tails and all four exact-head CI workflows. The
new master ROM matches the tested repair and the public release was
verified against the exact normal CI artifact.
[DKC1 comparison and accumulator regression](evidence/integration-koff-accumulator-dkc1-2026-11-11.json).
The published BRR archive was verified byte for byte against the master
CI artifact and contains the two production payloads only.
[SMW physical comparison and BRR merge](evidence/integration-br-r47-master-smw-pair-2026-11-11.json).

PR32 is draft at `ae59e6b774168564444352066273a9e4025aa800`. The real-N64 startup stall was
fixed by repairing the shared C4C depth sender entry in two Main RSP words.
The refreshed head passes all six workflows, including Ares and the
enabled renderer. The earlier qualified ROM's startup/return passed. On N64, DKC1
matches exact RGB and PCM at two aligned checkpoints. All three approximately
matched polled DKC1 intro bands regress in completed guest boundary rate.
Windows removed the USB function during the quiet interval, before a closing
sample. ALttP house/rain, SMW, Mode 7 and paired quiet timing remain open.
PR32 is blocked for default promotion. R44 and R45 retain separate gates.
[Refreshed review chain and gates](evidence/integration-renderer-refresh-2026-11-12.json).
[DKC1 parity and throughput evidence](evidence/integration-faithful-dkc1-2026-11-09.json).

PR33 `1c68ff36` passed four exact-head CI workflows. On physical N64 it
reproduced both 252-sample KOFF release tails and all 16,384 bytes of the
other channel against the exact BRR master. The reference and candidate
both verified R17 restoration. A fresh bench ROM of the merge matches
the tested candidate. Its SMW boot/demo captures match the prior audio
reference and both quiet windows stay below 60 guest boundaries/s.
The prior integrated master `dc0c49d1` has a paired three-workload
N64 baseline. Quiet
20-second guest rates are 59.833 for DKC1 intro, 59.866 for ALttP boot
and 58.017 for SMW boot/demo. All six images and DSP snapshots match.
The DKC1 release remains the single scoped PCM delta. A wider gameplay
baseline, sustained native cadence and analog DAC remain open.
[Integrated N64 baseline and paired observations](evidence/integration-combined-master-native-2026-11-12.json).
[Native KOFF comparison and BRR release evidence](evidence/integration-native-koff-brr-master-2026-11-11.json).
[SMW physical comparison and BRR merge](evidence/integration-br-r47-master-smw-pair-2026-11-11.json).

The earlier KOFF and R47 native trials restored habitual R17 with
recovery 0. [Native note-tail evidence](evidence/integration-native-koff-tail-2026-11-09.json).

PR37 `392b8bd0` is the independent R19 pitch cache port against `dc0c49d1`.
Linked normal and REMOTE pitch, KOFF and BRR pass. The physical SMW
comparison preserves aligned RGB, PCM and DSP state, but drops from
58.017 to 55.411 guest frames/s in matched-start quiet windows. That
blocks promotion. The repeat lost COM3 before capture. After COM3
returned, the existing menu verified recovery 0 and R17 was restored.
Earlier launch interruptions remain recorded.
[R19 physical comparison and R45 build evidence](evidence/integration-r19-native-r45-preflight-2026-11-12.json).
[R19 port and interrupted reference evidence](evidence/integration-r19-pitch-port-2026-11-09.json).

PR38 `b9c5ab72` is VALIDATED and integrated as `b012b6b6`. Linked
exact-color cases, Gate C replay and five exact-head workflows passed.
Its loaded RSP banks match the prior master byte for byte. On N64,
aligned DKC1 RGB, PCM and DSP state match, with both completing 1,198
guest frames over the same quiet interval in about 20.02 seconds.
The merged tree and a fresh local REMOTE ROM match the tested head and
physical installation receipt. Six post-merge workflows and the byte-exact
production Latest package pass. R17 restoration passed
on this run. ALttP and SMW timings still bind to the previous master.
[CGRAM native evidence and merge](evidence/integration-cgram-native-dkc1-2026-11-12.json).
[Updated PR heads, controls and gates](evidence/integration-standalone-and-renderer-controls-2026-11-12.json).
[CGRAM and combined source evidence](evidence/integration-cgram-identical-2026-11-09.json).

PR39 `3bf54854` keeps the APU clock correction against `b012b6b6`.
The negative control reproduces stale lookup on that master. Normal,
HW_PROFILE and REMOTE pass the linked APU and CGRAM checks. All four
exact-head PR workflows and the directed 119-case APU cycle suite pass.
The physical menu transitions 21 to 42 and back to 21 remain pending.
[Refreshed APU clock proof and gate](evidence/integration-apu-clock-current-2026-11-12.json).
[Menu input evidence](evidence/integration-apu-menu-input-2026-11-11.json).
[Clock transition evidence](evidence/integration-apu-clock-invalidation-2026-11-09.json).

R43 `a6dd6082` is draft PR40 against PR32. R44 `4859b8c5` is draft PR41
against PR40. The byte-exact off control and the R44 linked Math and
RDP consumer replays pass. PR32 cadence, R43 and R44 paired native
comparisons remain open.
[Drafts, linked consumers and restore evidence](evidence/integration-renderer-pr40-pr41-2026-11-11.json).

R45 `e12ae12e` is draft PR42 against PR41. Sub and Modes 2–7 bypass a
redundant helper load. The linked row, packet and dispatch proofs pass.
Local R43, R44 and R45 controls on `dc0c49d1` share their audio source
and ROM header title. The linked replays, owner and delay-slot checks
pass. A fresh exact PR42 ROM matches the prepared binary. The faithful
RDP restart check passes on Main and Mode 7 of all four variants.
The workflow-only head passes Ares with the full R45 stack. The exact
profile artifact confirms the enabled bank and the default CI payloads
match production master byte for byte.
[Exact enabled artifact and CI evidence](evidence/integration-r45-enabled-ci-2026-11-12.json).
R44 reached DKC1 frame 3214 before COM3 disappeared. The R17 transport
control passed and the exact R45 repeat with idle warmup completed.
At frames 4330 and 4346, images and PCM match master. Both complete
1,198 guest frames from 4347 to 5545 in about 20 seconds. Earlier
polled throughput of the R45 stack is below master. R17 is restored.
The subsequent R44 retry reached hello but Windows lost COM3 during
idle warmup before any aligned capture. R17 is now pending restoration.
The recorded bridge time is at most 1.48 percent of the comparable
early band. A fixed-start quiet intro comparison is prepared for
master, R44 and R45. The later R44 aligned fidelity check, ALttP story
and Mode 7 remain open.
[Retained DKC1 counters and next paired gate](evidence/integration-renderer-dkc1-poll-accounting-2026-11-12.json).
The historical DKC1 first-stage benefit used six recorded inputs and
precision 20. The matched first-stage replay is prepared separately
from the recent zero-input boot. Its physical result is pending.
[DKC1 first-stage replay provenance](evidence/integration-renderer-dkc1-first-stage-2026-11-12.json).
[R17 transport and physical R45 evidence](evidence/integration-r45-native-dkc1-2026-11-12.json).
[Native launch and R17 restoration evidence](evidence/integration-r45-launch-transport-2026-11-12.json).
[Interrupted native run and bounded warmup rates](evidence/integration-r44-dkc1-interrupted-2026-11-12.json).
DKC1, ALttP story and Mode 7 still block promotion.
[Updated PR heads, controls and gates](evidence/integration-standalone-and-renderer-controls-2026-11-12.json).
[Port, draft and gate evidence](evidence/integration-r45-pr42-2026-11-11.json).

The full objective remains incomplete. The last completed native run
returned by software and verified the habitual R17 installation. The
following R44 attempt left its trial installation pending restoration.
Complete resident-DSP integral native cost follows the qualified faithful
combined baseline. Wider compatibility, full fidelity, DAC and chip gates
remain open.
