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

PR32 is draft at `1e96c40c8c98038fd506109e8dd89155eeea8948`. All six exact-head
workflows and the PI/TLB/window/OBJ/Math/delayed-DMA contracts passed. Both
exact-CI USB builds failed at first hello. The no-USB profiler reached a red
screen, then a guarded SRAM read after recovery could not validate the capture
header. A launch of the previously qualified master runtime also lost the USB
device before the host received a launch acknowledgement. Native acceptance
remains blocked and the common transport failure is unresolved.

The latest verified installation is the habitual R17, restored from the exact
131,072-byte backup with readback and menu recovery 0 verified remotely. No
controller or physical request remains active. Use the existing autonomous
return-to-menu path when the game bridge responds. Use passive checks first
when the USB link is absent. The user wants PC-side control whenever possible.

Before another launch, bound the common failure that also occurred on the
known reference. Use that reference to verify launch, bridge and autonomous
return before repeating the faithful candidate. Then qualify native house/rain,
SMW/DKC/Mode 7, aligned APU/PCM and combined quiet cadence. R44/R45 retain
separate gates. [Current compositor evidence](evidence/integration-faithful-compositor-2026-11-08.json).

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
