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
0. A subsequent 95-second idle menu USB check passed. No physical action is
outstanding. Pursue autonomous work with R17 available and avoid unattended
candidate launches that can strand the console. R47's clean local port passes
linked arithmetic and stereo checks. Its standalone USB link exceeds the CGRAM
owner by 4,080 bytes. PR32 plus the R47 DSP change fits locally with 66,832
bytes margin.
[Current traced startup and R47 evidence](evidence/integration-traced-native-startup-2026-11-09.json).

PR33 is DRAFT at1f34d1e3dbfccd6486fc5f5ddd265d2f74d361be: clean KOFF release
correction, no observer/flag/extra DSP state. Build/Owners/Ares pass; actual USB
link FAILS its unchanged CGRAM assertion by4080 bytes. Local normal/PROFILE/HW
and CI normal/PROFILE release/KON/caller proofs pass. All8 Ares profiles were
checked, six CPU-JIT>=800 samples; low virtual budgets remain explicit. These
are software scopes, not native waveform/cadence/DAC acceptance.

A bounded local pair of PR32 plus only PR33's DSP patch admits faithful USB
without owner/flag/assertion changes:66832-byte margin, owners/KOFF pass and12
unchanged RSP images. This pair lacks exact-head combination CI and native acceptance. With PR32
blocked, inspect the independent legacy alignment and memory gate. Any
prerequisite must preserve physical owners and runtime behavior before PR33
can rerun exact-head and native gates.
[Current KOFF evidence](evidence/integration-koff-release-2026-11-08.json).

The full objective remains ACTIVE and incomplete. Complete resident-DSP
integral native cost is NOT_MEASURED and follows the qualified faithful combined
baseline, before more isolated kernels. No1.0/full fidelity/chip/DAC acceptance.
