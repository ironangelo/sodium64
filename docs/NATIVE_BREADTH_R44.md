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

## R43 first-stage control measured

Ten retired snapshots now define the route through logos/Cranky/DK intro,
copyright/file/one-player/world/regional map and Jungle Hijinxs. Frame1800 is
the DK/Cranky intro, not a title. Start8 at1800; A8 at2400/2700/3300/3600;
Right120 at4200 gives the pre-capture frame4320. The quiet20s segment then has
no injected inputs. Full trace276 intervals:13.778162 completions/s, explicit
wait53.264726ms; CPU samples73.319357percent at RSP wait. Main residency62.865129
and Math26.275332percent are bank residency, not exclusive instruction costs.
No Mode7 samples. The resulting guest segment is bounded first-stage activity,
not whole-title or fixed sustained presentation FPS.

All checksum/trace/settings controls and menu/coordinate8 readback restoration
pass. Freeze the first240-interval comparison before R44 as an additional
matched guest-progress control; full quiet window remains reported. Replay the
same route in R44 and require all ten images/four paused PCM buffers exact.
[Curated control receipt](evidence/r44-dkc-breadth-control.json). Private paths,
hashes and payloads remain local. This deficit prioritizes renderer architecture
for DKC over marginal CPU tuning; R44 effect is not measured yet.
