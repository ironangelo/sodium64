# Active operating direction - 2026-10-15

Consolidation and integration toward master come first. The destination remains
Sodium641.0 on real N64: native60/50 cadence, frameskip0, full-rate SPC700/APU,
faithful audio/graphics, broad compatibility, DSP-1, SuperFX and SA-1.

Use [the integration audit](INTEGRATION_AUDIT_2026-10-15.md), its finite queue and
the newest CONTINUITY checkpoint. Finish small clean PRs and their gates; do not
merge PR21 wholesale or move unresolved regressions into defaults. A useful
cycle ends with an integration/evidence checkpoint, not another experiment plan.

Implement and validate autonomously. Use bounded hardware to resolve a
named gate and preserve every fidelity, timing, ownership and recovery contract.
Each production extraction needs a concrete fidelity or stability fix or a
credible material cost reduction. Favor measured savings on representative
native workloads. Diagnostics and build changes earn integration by removing a
named blocker while preserving the production package.
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

Current master `7a6e3d75` includes PR39. The native menu repair and the
integrated DKC1, ALttP and SMW baseline bind to the exact test and merge
images. SMW remains below native cadence in the measured scene.
[Current integrated native baseline](evidence/integration-apu-clock-master-2026-11-16.json).

Earlier checkpoint, 2026-11-13. Seventeen separate PRs
24/23/22/25/26/27/28/29/30/31/34/35/36/33/43/38/44 are integrated in master
`c90ef5c983edb6e775d34676443f1e29ec48a9e2`. PR35 qualifies the isolated
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
matches exact RGB and PCM at two aligned later-intro checkpoints. The
early quiet comparison against its direct parent reproduces the
deficit, 59.56 to 42.82 guest frames/s from frame 3001. PCM and DSP
state match at two early-intro checkpoints. The corrected active images
match the independent Snes9x software reference pixel for pixel.
R43, R44 and R45 preserve both corrected images and PCM in this scene
at 43.22, 44.76 and 44.41 guest frames/s. ALttP house/rain, SMW and Mode 7
remain open. PR32 is blocked for default promotion. R44 and R45 retain
their individual gates.
[Early DKC1 hardware comparison](evidence/integration-pr32-native-dkc1-early-2026-11-13.json).
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

PR44 `027a1233` extracts nine 65C816 relative-branch tails from A12.
The normal, PROFILE and REMOTE linked checks pass. Matched normal
and REMOTE builds change 162 loaded bytes in the nine handlers while
retaining their addresses, allocation and both resident RSP banks.
All four exact-head PR checks pass. Run 43454365988 matches all 12 aligned
60-VI windows on two fresh boots of each version. PR44 is integrated
as `c90ef5c9`. The per-branch saving is measured in instructions.
DKC1 late intro, ALttP boot and SMW boot/demo match their earlier
integrated references in all six paired RGB/PCM/DSP captures. Quiet
guest rates are 59.85, 59.84 and 58.05/s at APU 21 and frameskip 0.
All three runs verify R17 restoration after a software return.
SMW still falls below native cadence over the measured interval.
Longer gameplay, analog output and an isolated PR44 performance
gain remain unmeasured.
[Linked 65C816 branch evidence](evidence/integration-cpu-relative-branches-2026-11-12.json).
[Combined master N64 evidence](evidence/integration-current-master-native-2026-11-13.json).

PR45 `85d1e3c5` fixes SPC700 address wrapping. All 770 linked cases
and five exact-head CI runs pass. Both paired DKC1 captures match
RGB, PCM and DSP state on N64. The tested candidate completes
1,197 guest frames over 1,197 VI ticks in 20.007 s. The reference
completes 1,198 over 1,197 in 20.016 s. Master `fe61d371` is
byte-identical to the tested REMOTE build. Its combined three-title
native baseline matches all six digital RGB/PCM/DSP captures against
`c90ef5c9`. Guest rates
are 59.829/s (DKC1 late intro), 59.842/s (ALttP boot) and 58.174/s
(SMW boot/demo). SMW is still below native cadence.
[Combined integrated baseline](evidence/integration-master-spc-wrap-native-2026-11-15.json).
[SPC700 wrap evidence](evidence/integration-spc-address-wrap-2026-11-13.json).

PR46 `1cbf8e8e` independently fixes seven SPC700 direct-page word
operations. The linked current master fails 580 of 996 cases.
The refreshed normal and REMOTE repair passes all 996, including
adjacent timer outputs. The refreshed linked layout retains all
1,291 original symbol/address pairs. On real N64, both launch
orders compare the same 1,200 SMW guest frames and retain all
four paired RGB/PCM/DSP observations. The candidate takes 7.543
and 7.031 ms longer. The short destination-RAM read is rejected
after adding 49.444 and 50.942 ms in the same native comparison.
The separate six-op candidate passes 854 linked cases. Two new N64
launches preserve aligned RGB/PCM/DSP, but elapsed time against
the earlier master controls varies from +10.388 to -4.439 ms.
Promotion stays blocked. Preserve both proofs and move to the next
qualified component or the complete resident DSP gate.
[Native attribution and six-operation split](evidence/integration-spc-movw-residual-2026-11-16.json).
[Layout-preserving fixed-work evidence](evidence/integration-spc-word-layout-2026-11-16.json).
The fused ordinary-RAM MOVW helper preserves the real destination read
and both cycle debits. It passes 1,006 linked word cases and 960 helper
cases, with 86 interpreted instructions versus the master's 88 for the
cached test block. The opposite-order native SMW pairs add 85.165 and
83.762 ms with exact captures. Reject this helper and retain the PR46
cadence blocker. [Fused helper evidence](evidence/integration-spc-movw-fused-2026-11-17.json).

PR47 `cd055b02` isolates selective SPC700 JIT invalidation.
Four linked variants pass publication, overflow/replay and clock-menu
checks. Both launch orders save about 1.27 s over the same 1,200 DKC1
startup frames with exact RGB/PCM/DSP captures. A third pair without
USB polling during timing repeats the gain. The separate SMW and ALttP
smoke pairs match both captures and take almost the same time.
PR47 is VALIDATED for the measured gate and integrated in `bcc8e463`.
The public Rolling Release matches the isolated production CI
artifact. The merged tree's native fixed-window repeat confirms
5.15 percent shorter DKC1 startup, with SMW and ALttP within 0.05
percent of the prior master. All paired RGB/PCM/DSP observations
match at APU 21 and frameskip 0. All three launches return to the
private menu in software and preserve the play slot. The synthetic
all-groups reset remains more expensive.
[Native JIT validation](evidence/integration-apu-selective-jit-2026-11-16.json).
[Merged baseline and release verification](evidence/integration-apu-selective-jit-master-2026-11-17.json).
[Combined native three-title and SMW evidence](evidence/integration-spc-combined-native-2026-11-15.json).
[Direct-page word evidence](evidence/integration-spc-direct-page-word-2026-11-13.json).

PR39 `43602e2e` is VALIDATED for the scoped correctness gate and
integrated in `7a6e3d75`. The real N64 settings menu executes both
clock changes and both unchanged-clock controls, using fixed raw
button samples at the edge detector. The preceding master leaves a
matching-tag block eligible after both clock changes. The repair
empties the entire lookup before guest execution resumes and
preserves it after both same-clock closes. All four exact-head PR
workflows, the branch build and the directed cycle proof pass.
[Physical menu and integrated baseline](evidence/integration-apu-clock-master-2026-11-16.json).
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
idle warmup before any aligned capture. R17 was verified after COM3
returned, before the new master trials.
The recorded bridge time is at most 1.48 percent of the comparable
earlier polled band. The quiet early-intro comparison completed for
master, PR32, R43, R44 and R45. The later R44 aligned fidelity check,
Use the refreshed paired story and Mode 7 evidence below.
[Retained DKC1 counters and next paired gate](evidence/integration-renderer-dkc1-poll-accounting-2026-11-12.json).
The DKC1 first-stage benefit reproduces on real N64 using six matched
inputs and precision 20. R44 and R45 reach 13.74 and 28.23 guest frames/s
from guest frame 4331. Both image/PCM comparisons match exactly and both
verify R17 restoration. The distinct zero-input intro regression stands.
The F-Zero Mode 7 R44/R45 pair now completes. Both run 134 guest
frames from 4501 to 4635 over 960 VI ticks. The single aligned RGB,
PCM and DSP capture matches exactly. R45 returns by software and
preserves the separate play slot. The bounded Mode 7 comparison
passes. The scene still runs at about 8.35 guest frames/s.
[Native R45 Mode 7 comparison](evidence/integration-r45-mode7-native-2026-11-15.json).
[DKC1 first-stage replay provenance](evidence/integration-renderer-dkc1-first-stage-2026-11-12.json).
[R17 transport and physical R45 evidence](evidence/integration-r45-native-dkc1-2026-11-12.json).
[Native launch and R17 restoration evidence](evidence/integration-r45-launch-transport-2026-11-12.json).
[Interrupted native run and bounded warmup rates](evidence/integration-r44-dkc1-interrupted-2026-11-12.json).
The timed native ALttP story pair repeats in both launch orders.
Over the same 1,000 guest intervals, R44 averages 56.37 and R45
54.58 guest frames/s, about 0.582 ms added per completed frame.
Three aligned RGB captures and the paused PCM/DSP match exactly.
The early DKC1 compositor deficit and the repeated ALttP story
regression block promotion.
[Repeated native story comparison](evidence/integration-r45-alttp-story-native-2026-11-15.json).
[Updated PR heads, controls and gates](evidence/integration-standalone-and-renderer-controls-2026-11-12.json).
[Port, draft and gate evidence](evidence/integration-r45-pr42-2026-11-11.json).

The full objective remains incomplete. Lab `95296f9c` qualifies a
matched Count comparison of CPU waits for RSP halt and framebuffer
availability. The legacy DKC1 control and the completed faithful
measurement both preserve their uninstrumented aligned RGB/PCM/DSP
captures. From guest frame 3001 the comparable window shifts 10.623
ms per completed frame into CPU RSP-halt wait and saves 4.317 ms
of framebuffer wait. Time outside the two wait sites and USB grows
0.066 ms. The blocker is graphics completion in this scene. The
counter does not identify which RSP/RDP/DMA subpath causes it.
[Matched native wait evidence](evidence/integration-pr32-bounded-wait-native-2026-11-15.json).
The measured integrated master is the comparator for complete resident
DSP cost. The legacy DSP path now has a sampled native budget for three
native scenes. The complete scalar R61 controller reproduces all four
PR30 fixture results and quantifies its logical flush demand. The
256-clock projection proof preserves the complete fixture results,
including exact producer reads, and reduces the nominal demand to
74–162 flushes per 512 stereo samples. The stress trace still needs
1,107. Native ALttP observes uninterrupted renderer ownership of at
least 12.230 ms. A batch capped at 256 SPC clocks cannot assume a
renderer halt at each deadline. The next gate is the end-to-end
resident cost with the live timestamped SPC producer, exact RAM/echo
publication and measured shared-SP handoffs. On native DKC1, 244 of
1,200 renderer jobs are still active at least 1 ms after a stable DSP
register read. The full controller now answers those reads independently
of dispatch, with exact results on all four reference fixtures. The
remaining urgent observations are ENVX/OUTX/ENDX and echo-sensitive
RAM/fetch, with real clock, cache/JIT and shared-SP handoffs in the
same native run. The original mixed load now measures mandatory
output reads while the renderer is busy. The stock JIT compresses
the directed read pair from three cycles to one. The private fixed
prefix restores the exact three cycles. A separate paused echo
publication proves the page tag is required for warm code entry.
The full scalar controller now runs an original mixed workload
with live audio and real echo publication visible through the
warm SPC JIT. R4300 cost is 53.168 ms per guest frame, with
29.659 ms inside the complete core and its echo callbacks in
the attribution run. Keep the bounded scalar bridge as a native
reference. Use the same workload to test a complete accelerated
architecture with bounded shared-SP handoffs. Native retired
exchange measures 40.359 us for DMEM and 76.771 us for both banks,
plus 10.787 us average RDP drain. Per-sample bank exchange exceeds
the frame budget at these transfer costs. Eight-sample service
cuts 21,272 calls to 2,659 with exact common samples on the
original workload. It leaves the critical register catches in
place. The private original guest now qualifies section-boundary
RSP pause/resume, verified memory restore and a staged marker in
the middle of a frame. It offers only two checkpoints per frame
in this workload. A private native proof retains 64 bytes across 40
renderer handoffs without bank exchange or RDP drain, with exact RGB
and captured PCM and 18.761 us mean service cost. The DSP still runs
on the CPU. Publication-aware output reads avoid 665 synchronous
catches in that same 40-frame workload. The renderer is still running
on 247 of the 1,993 remaining catches. Full accelerated compute needs
a compact code layout with a bounded deadline path during SP ownership
and exact native echo/fetch publication.
[Live SPC RAM input](evidence/integration-dsp-live-spc-input-queue-2026-11-16.json)
cuts the complete workload to 36.255–36.257 ms per guest frame from
40.024–40.031 ms. Native RGB and captured PCM match. The complete DSP
is still scalar and 282 synchronous output reads retain the renderer
ownership conflict over the measured 40 frames.
The integrated event dispatcher is rejected for a 3.23–3.31% native
slowdown with exact output. Keep segmented DSP execution and the
separately measured input queue for the next complete backend check.
[Native event-dispatch comparison](evidence/integration-dsp-window-events-2026-11-16.json).
Record/replay of actual DSP bus effects reaches 16.576 ms/frame on
the same native guest with exact RGB and PCM and no DSP arithmetic.
It spends 5.439 ms/frame waiting for a framebuffer on average, with
a 0.512 us minimum. The renderer owns SP at 1,128 of 1,993 synchronous
register reads. The complete backend now has a measured workload
budget and an explicit deadline test during renderer ownership.
[DSP headroom and deadline evidence](evidence/integration-dsp-effects-headroom-2026-11-16.json).
The saturated ENDX rule passes four reference replays and 130 local cases
with three rejected faults. Native A/B in both orders avoids 664 of 1,993
synchronous reads, with exact RGB and PCM. Elapsed time rises 0.40–0.42%.
The rule is available to the accelerated backend after a net timing win.
The scalar runtime retains the previous path.
[ENDX proof and native result](evidence/integration-dsp-sticky-endx-2026-11-17.json).
[Native register-publication deadlines](evidence/integration-dsp-output-publication-2026-11-16.json).
[Native resident-state handoff](evidence/integration-dsp-rsp-resident-state-2026-11-16.json).
[Native in-frame RSP handoff](evidence/integration-dsp-rsp-in-frame-yield-2026-11-16.json).
[Native transport and PCM service](evidence/integration-dsp-rsp-handoff-2026-11-16.json).
[Active whole-core native cost](evidence/integration-dsp-active-native-cost-2026-11-16.json).
[Native clock and echo-page proof](evidence/integration-dsp-live-spc-echo-2026-11-16.json).
[Live DSP reads and renderer contention](evidence/integration-dsp-live-rsp-deadlines-2026-11-16.json).
[Native budget and complete-controller replay](evidence/integration-dsp-budget-2026-11-15.json).
[Complete-controller and renderer ownership evidence](evidence/integration-dsp-batched-window-2026-11-15.json).
Wider compatibility, full fidelity, DAC and chip gates remain open.

The private menu, normal master and separate reference bench are
installed and byte-verified after the rear USB port restored
enumeration. Physical cold boot, separate reference launch and
software return pass. Normal browser gameplay remains unverified.
Recovery after complete USB disappearance still lacks a verified
independent path.
[Private menu and transport evidence](evidence/private-native-menu-split-2026-11-13.json).
