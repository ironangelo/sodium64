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

Current checkpoint, 2026-11-09. Eleven separate PRs
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

Habitual R17 was restored and verified with 131,072-byte readback and recovery
0. A 95-second idle menu USB check and a later read-only status both passed.
No physical action is outstanding. Keep R17 available and avoid unattended
candidate launches that can strand the console after a USB removal.

PR35 9bdd82c6 is the isolated USB bench status compaction. The
normal production ROM is identical to master. PR36 539ca2ca is the
R47 BRR history recurrence audio candidate with PR35 as a separate
prerequisite. R47 now passes its local standalone layout gate without
PR32. The paired REMOTE image has 16 bytes of static CGRAM margin.
Normal, HW_PROFILE and REMOTE each pass 57,344 linked decoder cases and
six emitted faults, plus 2,048 scheduled stereo cases on REMOTE.
Both PRs are draft. Complete exact-head CI and qualify native matched
PCM/cadence and safe recovery before promotion.
[Local audio and ownership evidence](evidence/integration-usb-status-r47-2026-11-09.json).

PR33 is DRAFT at1f34d1e3dbfccd6486fc5f5ddd265d2f74d361be: clean KOFF release
correction, no observer/flag/extra DSP state. Build/Owners/Ares pass; actual USB
link FAILS its unchanged CGRAM assertion by4080 bytes. Local normal/PROFILE/HW
and CI normal/PROFILE release/KON/caller proofs pass. All8 Ares profiles were
checked, six CPU-JIT>=800 samples; low virtual budgets remain explicit. These
are software scopes, not native waveform/cadence/DAC acceptance.

A bounded local pair of PR32 plus only PR33's DSP patch admits faithful USB
with 66,832 bytes margin. That pair lacks exact-head CI and native evidence.
PR35 alone does not unblock KOFF. It remains 32 bytes past the pre-data
page threshold, which leaves a 4,080-byte CGRAM owner overlap. Keep PR33
blocked on an independent layout fix and exact-head/native requalification.
[Current KOFF evidence](evidence/integration-koff-release-2026-11-08.json).

The full objective remains ACTIVE and incomplete. Complete resident-DSP
integral native cost is NOT_MEASURED and follows the qualified faithful combined
baseline, before more isolated kernels. No1.0/full fidelity/chip/DAC acceptance.
