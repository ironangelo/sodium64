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

Current checkpoint, 2026-11-11. Eleven separate PRs
24/23/22/25/26/27/28/29/30/31/34 are integrated in master
`c232af87e046d41a468e3f2f1083fcf30f606385`. PR34 makes host-side USB debug
session shutdown graceful. The normal loaded image is unchanged. Latest
contains the same production ROM and converter as before. October's
commercial quiet controls and independent SMW capture retain their measured
scope. [PR34 evidence](evidence/integration-bench-eof-2026-11-09.json).

PR32 is draft at `3e1c9a99869063254dbc1c84453fd6cf06f78762`. The real-N64 startup stall was
fixed by repairing the shared C4C depth sender entry in two Main RSP words.
Ordinary startup/return and all six exact-head workflows pass. On N64, DKC1
matches exact RGB and PCM at two aligned checkpoints. All three approximately
matched polled DKC1 intro bands regress in completed guest boundary rate.
Windows removed the USB function during the quiet interval, before a closing
sample. ALttP house/rain, SMW, Mode 7 and paired quiet timing remain open.
PR32 is blocked for default promotion. R44 and R45 retain separate gates.
[DKC1 parity and throughput evidence](evidence/integration-faithful-dkc1-2026-11-09.json).

PR35 87d16156 is ready for review. All four exact-head CI workflows
and the real-N64 short boot/software-return gate passed. REMOTE places
three guest RAM owners in aligned BSS. The ordinary production ROM is
byte-identical. Review and integrate this prerequisite separately.

PR36 2109eb48 remains draft behind PR35. All four exact-head workflows
passed. Native PCM is byte-identical at boundary 200 on original eight-voice
filter-0 and four-filter fixtures. Short filtered windows complete 240
and 242 guest boundaries in about four seconds. The remaining promotion
work is the audio-only branch against the integrated prerequisite and
its exact-head checks. Combined representative cadence/fidelity and DAC
remain open.

PR33 e975c7a7 passes all four exact-head CI workflows and the scoped
real-N64 KOFF note-tail gate. Two aligned events each reproduce 252
nonzero PCM samples predicted by the independent envelope rule and the
existing mixer. The other channel remains byte-identical. Short cadence
windows are about four seconds. The local R47/KOFF pair fits with 504
bytes before CGRAM and passes linked audio. It is not the integrated
baseline. Keep both audio PRs draft until PR35 is integrated separately.

The earlier KOFF and R47 native trials restored habitual R17 with
recovery 0. [Native note-tail evidence](evidence/integration-native-koff-tail-2026-11-09.json).

PR37 f21f211f is the independent R19 pitch cache port. Its linked normal,
HW_PROFILE and USB proofs pass. CI USB admission leaves 16 bytes below
the original CGRAM owner. The exact-master native reference installed,
then lost the Windows USB device before launch acknowledgement. On
November 11 the link returned, the next reference booted, and software
returned to the menu and verified R17. A second reference load again
lost the USB device before acknowledgement. COM3 subsequently returned
and R17 install/readback and menu recovery 0 were verified. Qualify the
launch transport before resuming the candidate comparison.
[R19 port and interrupted reference evidence](evidence/integration-r19-pitch-port-2026-11-09.json).

PR38 86a1b5b6 is a standalone CGRAM epoch port. Its linked exact-color
cases and Gate C replay pass. Native paired image/PCM/cadence is pending.
A local PR35/KOFF/R47/R19/CGRAM combination retains 504 bytes before
CGRAM and passes linked audio, CGRAM, bench and release admission.
Review and integrate candidates separately before measuring the
representative combined baseline.
[CGRAM and combined source evidence](evidence/integration-cgram-identical-2026-11-09.json).

PR39 a4c8a2f2 corrects stale compiled SPC700 cycle debits on a menu
clock change. Its linked clock transitions, full reset and all five CI
workflows pass, including the 119-case compiled APU cycle suite. The
native menu check remains open. The correction fits the local queued
combination.
[Clock transition evidence](evidence/integration-apu-clock-invalidation-2026-11-09.json).

R43 `ebcf1c57` is draft PR40 against PR32. R44 `9f377fad` is draft PR41
against PR40. The byte-exact off control and the R44 linked Math and
RDP consumer replays pass. PR32 cadence, R43 and R44 paired native
comparisons, and R45 story/Mode 7 costs remain open.
[Drafts, linked consumers and restore evidence](evidence/integration-renderer-pr40-pr41-2026-11-11.json).

The full objective remains ACTIVE and incomplete. Complete resident-DSP
integral native cost is NOT_MEASURED and follows the qualified faithful combined
baseline, before more isolated kernels. No1.0/full fidelity/chip/DAC acceptance.
