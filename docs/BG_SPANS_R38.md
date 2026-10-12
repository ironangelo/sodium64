# R38 - Identical regular-BG spans, 2026-10-12

Status: MEASURED, promising candidate; expanded native/regression/CI pending.
R37 observed75percent of sampled Main residency inside command submission/
fetch-retirement polling. R36 individual texture residency was marginal. This
experiment reduces actual rectangles/submissions for consecutive identical
8x8 BG map words within one window span, palette, priority and real epoch.
Large16x16 subdivisions retain individual draws. No game identity or skipped
guest emulation. All existing graphics/audio corrections remain enabled.

`BG_SPANS=1` requires `DECODE_BANK=1` and retained coordinate8. A dedicated
CI8 tile4 uses S mask3 without mirror and original T mask6/mirror; original
flip gradients and atlas T offsets remain. The row constructor stays byte
identical: only the final rectangle's upper-word tile selector changes from2
to4. Extending a legacy mask5/mirror rectangle, or changing the selector before
TEXREC_OFS arithmetic, would be incorrect. Vertex advancement matches skipped
individual draws; texture palette/cache/source fences and painter order survive.

RSP IMEM has no room for the helper. Move the unchanged bitplane decoder into
the unused tail of the existing object-cache overlay, loaded only on decode.
Restore the Main bank before returning, including original t9/RA/v1 and empty
check offset12. This can cost cold-cache time; the physical experiment must
earn that cost. Both options default0 and earlier branch/master are preserved.
Tile4 initializes after the existing unchanged sparse-snapshot/semaphore
instructions, once per frame, with no extra bank round trip or arena allocation.

Quick emitted-code checks:576 decoder cases (288 independently checked numeric
2/4/8bpp outputs,288 stale-carry differential cases),448 span cases/13180 visible
horizontal pixels/1433 individual rectangles removed in the numeric workload,
two post-snapshot initializer queues, four negative mutations. Exact worker
entry operands and frozen public PCs checked. Existing asynchronous command/
source leases, LoadSync/branch-delay/boot12/TV5/arena D15C8<D2000 gates pass.
The existing instruction model adds only LPV/SPV e0 used by these decoders.

The fixture initially used SNES little-endian plane-byte order against the
big-endian snapshot, then inherited its deliberately stale VCO defaults; both
were corrected, with stale differential coverage retained. Initial full-clean
snapshot fixture was unsuitable; the new initializer is tested directly after
the byte-identical snapshot/semaphore prefix. Production audits also corrected
the tile4 S mirror bit, restored the original decoder loop's v1 effect, and
kept row opcode arithmetic unchanged before hardware use. The branch-delay
gate caught the new helper call in the preceding empty-tile branch's delay
slot; moving it into the following former NOP preserves all addresses. This
was corrected before loading any R38 image on hardware. No native claim yet.

Actual N64 executable4c3764a: rain32.2889675 ->36.9560894 completed boundaries/s
(+14.454231percent), mean explicit CPU/RSP wait11.245405 ->7.529420ms. Same
acknowledged12944 route, skip0/APU21/audio4; quiet20s/full checksum/trace/settings.
Four physical checkpoints268800 RGB pixels and8192 paused PCM bytes, zero
differences; registers/heads/enabled equal. Actual ROM selection/launch, USB
menu return/coordinate8 restoration/readback pass. Atomic Main bank samples
4415/Math2394; transition139 includes added decoder loads, not exclusive cost.

This is a material gain but only36.96 completions/s (~27.06ms per completion)
versus the native16.7ms budget. No TV FPS, full waveform or whole-game claim.
Next: fresh equivalent ALttP title/story/room performance controls and expanded
pixel/PCM/cold/regression checks; full relevant CI before any promotion.
Keep candidate isolated until those pass. An unmeasured decoder-only control
may discriminate relocation costs if an expanded scene degrades; avoid a
redundant rain control when exact code/settings already qualify it. Private
spans-r38 artifacts/run preserve exact identities.
Commercial input/output data and their hashes stay private.
