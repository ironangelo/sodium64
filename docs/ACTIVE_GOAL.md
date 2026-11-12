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

Current checkpoint, 2026-11-11. Thirteen separate PRs
24/23/22/25/26/27/28/29/30/31/34/35/36 are integrated in master
`b3b0a0610e6aec9fb0b634fca3124ac22db34b04`. PR35 qualifies the isolated
USB bench layout. PR36 integrates the separately qualified BRR recurrence.
The master release and follow-up CI for PR36 are tracked separately.
[SMW physical comparison and BRR merge](evidence/integration-br-r47-master-smw-pair-2026-11-11.json).

PR32 is draft at `3e1c9a99869063254dbc1c84453fd6cf06f78762`. The real-N64 startup stall was
fixed by repairing the shared C4C depth sender entry in two Main RSP words.
Ordinary startup/return and all six exact-head workflows pass. On N64, DKC1
matches exact RGB and PCM at two aligned checkpoints. All three approximately
matched polled DKC1 intro bands regress in completed guest boundary rate.
Windows removed the USB function during the quiet interval, before a closing
sample. ALttP house/rain, SMW, Mode 7 and paired quiet timing remain open.
PR32 is blocked for default promotion. R44 and R45 retain separate gates.
[DKC1 parity and throughput evidence](evidence/integration-faithful-dkc1-2026-11-09.json).

PR33 `1c68ff36` is draft against master with BRR integrated. The tree
matches the combined candidate tested on the original four-filter fixture
and SMW. KOFF previously reproduced 252 release samples per event on
two aligned cuts and preserved the other channel. Fresh CI is active.
The SMW boot/demo captures match and both quiet windows stay below 60.
The representative integrated baseline and DAC remain open.
[SMW physical comparison and BRR merge](evidence/integration-br-r47-master-smw-pair-2026-11-11.json).

The earlier KOFF and R47 native trials restored habitual R17 with
recovery 0. [Native note-tail evidence](evidence/integration-native-koff-tail-2026-11-09.json).

PR37 f21f211f is the independent R19 pitch cache port. Its linked normal,
HW_PROFILE and USB proofs pass. CI USB admission leaves 16 bytes below
the original CGRAM owner. The exact-master native reference installed,
then lost the Windows USB device before launch acknowledgement. On
November 11 the link returned, the next reference booted, and software
returned to the menu and verified R17. A second reference load again
lost the USB device before acknowledgement. COM3 subsequently returned
and R17 install/readback and menu recovery 0 were verified. A bounded
launch using R17 already installed lost COM3 again before the menu
acknowledgement. Windows recorded surprise removal. Two subsequent
synthetic launches completed over COM3 and restored R17. R17 remains the
last verified installation. The R19 candidate comparison remains open.
[R19 port and interrupted reference evidence](evidence/integration-r19-pitch-port-2026-11-09.json).

PR38 86a1b5b6 is a standalone CGRAM epoch port. Its linked exact-color
cases and Gate C replay pass. Native paired image/PCM/cadence is pending.
A local PR35/KOFF/R47/R19/CGRAM combination retains 504 bytes before
CGRAM and passes linked audio, CGRAM, bench and release admission.
Review and integrate candidates separately before measuring the
representative combined baseline.
[CGRAM and combined source evidence](evidence/integration-cgram-identical-2026-11-09.json).

PR39 `46447580` keeps the APU clock correction from `a4c8a2f2` and
adds coverage from linked menu input through SPC700 dispatch. Normal,
HW_PROFILE and USB pass locally. The prior runtime passed the 119-case
compiled APU cycle suite. The current head's four CI workflows passed. The physical menu check
remains pending. The correction fits the local queued
combination. [Menu input evidence](evidence/integration-apu-menu-input-2026-11-11.json).
[Clock transition evidence](evidence/integration-apu-clock-invalidation-2026-11-09.json).

R43 `ebcf1c57` is draft PR40 against PR32. R44 `9f377fad` is draft PR41
against PR40. The byte-exact off control and the R44 linked Math and
RDP consumer replays pass. PR32 cadence, R43 and R44 paired native
comparisons remain open.
[Drafts, linked consumers and restore evidence](evidence/integration-renderer-pr40-pr41-2026-11-11.json).

R45 `dab7e228` is draft PR42 against PR41. Sub and Modes 2–7 bypass a
redundant helper load. The linked row, packet and dispatch proofs pass.
Paired DKC1, ALttP story and Mode 7 checks block promotion.
[Port, draft and gate evidence](evidence/integration-r45-pr42-2026-11-11.json).

The full objective remains ACTIVE and incomplete. Complete resident-DSP
integral native cost is NOT_MEASURED and follows the qualified faithful combined
baseline, before more isolated kernels. No1.0/full fidelity/chip/DAC acceptance.
