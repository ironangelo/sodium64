# S2 renderer context reconstruction probe

IMPLEMENTED experiment only. `SCENE_RSP_REBIND=1` requires `SCENE_STATE=1`.
There is still no serializer, state import or complete machine-state restore.
The bounded question is whether normal H-COMP frame retirement leaves only
queue parity and the established vector constants live into the next frame.

`state-rsp-rebind` requires a canonical parked frame, inactive recorder and
healthy transport. It rejects another RSP stop, single-step, BREAK IRQ or a
PC whose next instruction is not the normal resident draw-frame jump.
It backs up and reads back all8192 SP memory bytes in exclusive volatile USB
TX cart scratch, then rechecks the complete backup before any SP mutation.
A320-byte diagnostic program clears all scalar/vector registers, flags and
ACC, reloads the nine established vector constants and queue parity, then
BREAKs without DMA, RDP, AI or guest work. CPU restores and reads back all
IMEM/DMEM plus halted PC/status. No SD or ordinary save is accessed.

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
