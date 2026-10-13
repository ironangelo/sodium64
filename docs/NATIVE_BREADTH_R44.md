# R44 native breadth controls - 2026-10-13

HYPOTHESIS/preflight. R44 relevant qualification is preserved in
[SUB_ALPHA_R44.md](SUB_ALPHA_R44.md); this batch adds native compatibility
coverage before selecting the next material optimization/state experiment.

Use the frozen empty emulator R43 runtime4382ae80 and R44 runtime7a83d49;
no new runtime code or rebuilt artifact. DKC1 Rev1 matches the revision of
historical A11/A13 captures; those captures are not equivalent current scene
baselines. Establish exact completed guest/render boundaries and acknowledged
input replay from a fresh launch. Compare intro/title/gameplay frame images
and paused8192-byte PCM/head/register/enabled state, then one quiet20s USB
capture from the same pre-capture guest boundary. Full checksum/settings,
frameskip0/APU21/audio4 and menu/coordinate8 readback restoration are mandatory.
Ordinary guest save writeback is disabled by the diagnostic build/menu return.

The root is sole COM3 owner. Private native run `r43-dkc-route` is the route
control; `r44-dkc-route` will replay its acknowledged guest inputs and compare
artifacts. The control initially inspects frames600/1200/1800, Start8 at1800,
then2100 to determine the shortest reproducible first-stage route. No polling
or export during the capture. If a native image/PCM/control difference appears,
stop promotion and characterize it before claiming benefit. Keep all private
game payloads, SD paths, state, images, PCM and hashes outside Git.

Mode7 remains a separate open native gate: old Z input is retained and numeric
fallback controls pass, but this DKC route does not establish Mode7 coverage.
Neither matched sampled images nor completed-boundary cadence prove sustained
presentation60Hz, complete audio fidelity or whole-title compatibility.
Save-state feasibility remains a bounded hypothesis in
[SAVE_STATE_FEASIBILITY_2026-10-12.md](SAVE_STATE_FEASIBILITY_2026-10-12.md).
