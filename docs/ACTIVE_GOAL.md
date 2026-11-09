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

PR32 is draft at `1e96c40c8c98038fd506109e8dd89155eeea8948`. All six
exact-head CI workflows passed. Native R17 and master reference launch and
autonomous return are requalified. A fresh faithful build with the working
local GCC 14.2.0 repeats the prior exact-CI failure after acknowledged menu
launch, before first emulator response. The SC64 USB device remained present
and firmware info responded. Both
native probe pairs now pass through the first guest boundary and frame
bridge. That first bridge runs before any RSP task. Bound the first actual
task submission/retirement and capture SP/DP state if it stalls, with a
qualified recovery route before the next hardware launch. Then qualify
aligned native image/audio and quiet combined cadence. R44/R45 retain
separate gates.
[First-boundary evidence](evidence/integration-faithful-first-boundary-2026-11-09.json).

The latest verified installation is habitual R17, restored and read back
remotely after both first-boundary probes. Exact 131,072-byte readback and
menu recovery 0 passed. No physical action is outstanding. R47's clean local port passes linked arithmetic and stereo
checks, but the standalone USB link exceeds the CGRAM owner by 4,080 bytes.
PR32 plus only the R47 DSP change fits locally with 66,832 bytes margin.
[Current traced startup and R47 evidence](evidence/integration-traced-native-startup-2026-11-09.json).

PR33 is DRAFT at1f34d1e3dbfccd6486fc5f5ddd265d2f74d361be: clean KOFF release
correction, no observer/flag/extra DSP state. Build/Owners/Ares pass; actual USB
link FAILS its unchanged CGRAM assertion by4080 bytes. Local normal/PROFILE/HW
and CI normal/PROFILE release/KON/caller proofs pass. All8 Ares profiles were
checked, six CPU-JIT>=800 samples; low virtual budgets remain explicit. These
are software scopes, not native waveform/cadence/DAC acceptance.

A bounded local pair of PR32 plus only PR33's DSP patch admits faithful USB
without owner/flag/assertion changes:66832-byte margin, owners/KOFF pass and12
unchanged RSP images. Qualify/promote PR32's layout, then rebase PR33 and rerun
its actual exact-head/native gates. This pair is not current-head combination
CI or native acceptance. Do not open another size campaign to fill the wait.
[Current KOFF evidence](evidence/integration-koff-release-2026-11-08.json).

The full objective remains ACTIVE and incomplete. Complete resident-DSP
integral native cost is NOT_MEASURED and follows the qualified faithful combined
baseline, before more isolated kernels. No1.0/full fidelity/chip/DAC acceptance.
