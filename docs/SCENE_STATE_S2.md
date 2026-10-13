# S2 renderer context reconstruction probe

IMPLEMENTED experiment only. `SCENE_RSP_REBIND=1` requires `SCENE_STATE=1`.
There is still no serializer, state import or complete machine-state restore.
The bounded question is whether normal H-COMP frame retirement leaves only
queue parity and the established vector constants live into the next frame.

`state-rsp-rebind` requires a canonical parked frame, inactive recorder and
healthy transport. It rejects another RSP stop, single-step, BREAK IRQ or a
PC outside the exact normal H-COMP HALT/jump/delay-slot sequence.
It backs up and reads back all8192 SP memory bytes in exclusive volatile USB
TX cart scratch, then rechecks the complete backup before any SP mutation.
A320-byte diagnostic program clears all scalar/vector registers, flags and
ACC, reloads the nine established vector constants and queue parity, then
BREAKs without DMA, RDP, AI or guest work. CPU restores and reads back all
IMEM/DMEM and status, then normalizes the pending jump to resident
draw-frame entry3C. No queued/emulated work is omitted by that jump. No SD or ordinary save is accessed.

An incomplete hardware recovery locks gameplay, steps, capture and further
probes; status/state-check/menu remain available. Successful probe remains
paused and advances no guest/render counter. This is a renderer hypothesis,
not a portable-state or fidelity claim. The existing render banks are exact
S1; option off CPU text/data remain exact too. Static owners retain the full
event capacity and ROM cache; no arena was widened.
[Local preflight](evidence/scene-state-s2-preflight.json).

First native gate uses the same replay at normal600, canonical park600,
explicit rebind, then normal601/660/1200. Compare images and complete paused
PCM plus ring heads/DSP regs/enabled; finally coordinate8/menu/readback.
Failing continuation rejects reconstruction before serializer work. A passing
title scene requires additional scenes/modes and owner closure before use.
Full native cadence, complete audio, corpus and production integration remain
open. Private images, PCM, ROM, state bytes and hashes remain local.

## First native gate: conservative stop guard

Runtime7a5712453a00fa16eef150659bca5211ea11c9be captured ordinary600 with
67200 pixels/8192 PCM bytes exact, then canonical park600 succeeded. Native
SP_PC=0x3C8/SP_STATUS=0x1801 identifies the delay-slot stop after the existing
H-COMP HALT and resident draw-frame jump. The probe expected the jump at PC;
its guard rejected before SP backup/mutation. Continuation is INCONCLUSIVE,
not a reconstruction failure. Menu/coordinate8 restore/readback passed.
[Guard evidence](evidence/scene-state-s2-native-guard.json).

Next recognize the exact HALT/jump/delay-slot sequence and restart directly at
the resident draw-frame entry after reconstruction. Merely copying a stopped
PC does not capture a pending branch. Re-run the linked transaction guards
and native1/60/600 continuation before accepting this canonicalization.

## Native pipeline admission repair

The repaired transaction admits only PC3C4/3C8 with the exact linked HALT,
jump and NOP words at3C0/3C4/3C8. Restart3C explicitly consumes the pending
resident-entry jump. Production transaction190 cases pass, including both
stop locations, three corrupted sequence words and invalid pipeline stops.
Actual linked RSP32 cases/four mutations plus HALT/entry ownership pass.
No renderer bank or ordinary frame work changes. The first native rejection
and its immutable artifact remain preserved. Native retry is still pending.

## Native pipeline retry: title continuation passed

MEASURED runtime `296aa4a3cbfef69d2b13ede9bae15c78030594e0`. Canonical park600 plus
explicit reconstruction completed SP memory restore/readback without guest or
render counter progress. Normal600/601/660/1200 match the frozen replay:
268800 pixels and32768 paused PCM bytes exact, including ring heads, DSP
registers and enabled state. Menu/coordinate8 install/readback passed.
[Native title evidence](evidence/scene-state-s2-native-title.json).

Only this continuation has been measured. No full-state file, import, complete
restore, cross-build compatibility, native cadence or full DSP/DAC fidelity is
qualified. Next expand to Mode7 and later scene states, then close the CPU/
guest memory/mapper/input/renderer/JIT/host-clock ownership rules. Replay
remains the control. First guard failure and artifacts remain preserved.

## Mode7 continuation reference captured

Frozen313642a flag0 completed the previously sampled F-Zero race route with
all ten old images/four paused PCM controls and exact input ACKs matching.
New ordinary checkpoints4500/4501/4560/5100 are captured; thirteen images and
seven paused PCM buffers total. Worker52638 terminal, coordinate8/menu/readback
passed. This is reference capture only; no reconstruction ran on this worker.
[Mode7 reference](evidence/scene-state-s2-mode7-reference.json).
Next S2runtime296aa4a follows the same route, parks/rebinds at4500, then compares
every image/PCM/head/register/enabled checkpoint. No timing capture is run.

## Mode7 candidate: reconstruction rejected

REJECTED runtime296aa4a3cbfef69d2b13ede9bae15c78030594e0. All14 ordinary
route controls match; canonical park/rebind4500 and SP memory readback pass.
Normal4501 image67200 pixels and8192 PCM bytes/head/register/enabled are exact.
At normal4560 (next60),2596 of67200 pixels differ. Stop immediately: no PCM4560,
5100 comparison or broad CI. Worker27620 terminal; menu/coordinate8 restore/
readback PASS. [Rejection evidence](evidence/scene-state-s2-mode7-rejected.json).

Thus this reset of GPR/vector/flags/ACC plus parity/initial constants is not
sufficient for a full state. Successful SP memory readback and one identical
frame do not close renderer ownership. The lost live context has not been
isolated. Preserve this opt-in probe and both failed/successful archives for
diagnosis, but never use it in state restore or gameplay. S1 natural park
continuation remains valid; subsequent work must preserve complete live RSP
state or prove a different reconstruction. Full save states remain open.

## GPR-only isolation hypothesis

SCENE_RSP_GPR_ONLY1 requires the existing opt-in rebind probe. Its140-byte
program clears only scalar registers and reloads queue parity, then BREAKs.
It issues no vector/flag/ACC operation; all of that original live context
remains untouched. The same SP memory transaction/pipeline admission/restart
and menu-only failure recovery apply. Default0 retains the rejected fullreset
for diagnosis; ordinary builds keep the entire feature off.
Actual linked program32 cases/two mutations, bridge16 and43 full-capacity
owners pass; all26 normal renderer extents match the frozen296aa4a artifact.
[Isolation preflight](evidence/scene-state-s2-gpr-preflight.json).

Native question: does this narrower change retain Mode7 normal4501/4560/5100
from the same exact race4500? Compare the existing reference and all route
image/PCM/ACK controls, finally coordinate8/menu/readback. A pass would isolate
necessary context to the preserved group in this control, not prove full state
restore or universal dead scalar registers. No new performance capture/CI.

## GPR-only Mode7 native continuation passed

MEASURED runtime0d2c9fb7f0f1efb09e8007684e8aea61df5d6b84. Same race4500
park/probe, then normal4501/4560/5100:all20 image/PCM controls pass, thirteen
images873600 pixels and seven PCM buffers57344 bytes exact, heads/registers/
enabled and input ACKs. Worker77698 terminal; coordinate8/menu/readback PASS.
[Native isolation](evidence/scene-state-s2-gpr-native.json).

Compared with rejected fullreset, preserving vector/flags/ACC removes the
Mode7 mismatch under this same control. Which individual member is necessary
is not isolated; preserve the entire group. This does not prove all scalar
registers dead universally, nor a complete machine restore. Full live context
capture/restore is the next gate, with no renderer work omitted.
