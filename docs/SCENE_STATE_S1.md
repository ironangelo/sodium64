# S1 scene-state continuation foundation

IMPLEMENTED experiment only. No serializer, import or restore is implemented.
The current goal requires native cadence and complete fidelity; this foundation
is useful only if it enables faithful, faster scene setup without omitted work.

`SCENE_STATE=1` adds `state-park` and `state-check`. From a normal exact paused
boundary, successful ACK schedules the existing queued frame's normal submit,
then waits for natural SP HALT, SP DMA/full retirement, DP and AI idle. A
separate O64 bridge parks after submission without another guest/render counter
increment. Full GPR64/HI/LO/EPC/Status and queue/continuation survive. No forced
SP HALT, DP freeze or skipped guest work. Failed ACK never leaves the pause;
retirement failure remains paused and cannot export a frame as canonical.

This drained frame is raw, preceding the following normal software UI update.
Its export says `scene_canonical_raw`; do not compare it with the same-numbered
ordinary UI boundary. After release, next1/60/600 normal retired frames and
paused PCM/DSP/head/enable must match full replay. These controls do not yet
prove serialized ownership, ROM/layout rejection or cross-build restoration.

Local production parser218 cases/1000 fuzz and linked16 post-submit/O64 cases
pass; missing submit and wrong bridge kind faults reject. Existing compiled
continuous102 cases, boot12/TV5 and43 disjoint owners pass. StaticD2A98<D4000.
All26 RSP text/data extents are exact frozen metadata R44; default-off whole
CPU text/data are exact too. The isolated option adds a conditional per-frame
hook; no ordinary production behavior is qualified from this prototype.
[Preflight](evidence/scene-state-s1-preflight.json).

First native question: does post-submit park preserve next1/60/600 guest frames
and paused audio from a known exact boundary? Baseline metadata R44 and S1
replay the same selected game/settings, pause600, capture ordinary600, then S1
parks and verifies counters remain600. Compare normal601/660/1200 after exact
step controls, full image/PCM/head/register/enabled, then menu/coordinate8
restore/readback. Private payloads and their hashes remain local. Failures
block serializer work until the continuation is understood; no broad CI yet.

## Native continuation result

MEASURED runtime `4ebdccd05e574e8cf1734ef20d8c8b05d59daaef`.
Post-submit canonical park at guest/render600 completed natural SP/DP/AI
retirement without advancing either counter. Normal600/601/660/1200 matched
the immutable replay control:268800 pixels and32768 paused PCM bytes exact,
including ring heads, DSP registers and enabled state. Menu/coordinate8
installation and readback passed. No worker remains live.
[Native evidence](evidence/scene-state-s1-native.json).

This qualifies continuation of the parked machine only. Serialization,
transactional restore, owner closure and cross-build rebinding remain open.
Keep the existing replay as control. Full60/audio/corpus acceptance remains
open; no broad CI or production integration is implied by this result.
