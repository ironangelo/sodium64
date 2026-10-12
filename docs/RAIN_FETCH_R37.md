# R37 - Existing sender marker on rain, 2026-10-12

Status: MEASURED, diagnostic discriminant completed. This is a bounded
diagnostic on the retained renderer, not another optimization or profiling
framework. R36's four-slot residency gave only0.395percent and is rejected.

Use existing `FETCH_SIGNAL=1`: SIG0 marks entry, submission and polling until
the complete DMEM list is fetched. It preserves all other control/status bits.
It is not a GPU execution timer, an exclusive instruction cost or source-fence
marker. The raw20Hz events retain SIG0; SIG1 still supplies atomic bank
residency. First discriminate whether most observed Main residency occurs in
this sender. High residency directs work toward command/consumer costs; low
residency directs it toward production, cache updates and other resident work.

The baseline is the fresh R36 corrected production control:32.2889675 completed
boundaries/s, explicit CPU/RSP wait11.245405ms, same acknowledged rain12944
route, skip0/APU21/audio4. Reuse its exact code/settings and private images/PCM;
do not run another equivalent control merely for chronology. Measure marker
overhead and describe samples as sampled residency, never independent costs.

Quick checks:144 asynchronous sender cases and one premature-retirement
negative mutation; fixed entries/status bits; boot12/TV5; D15C8 < D2000 arena;
no control transfer in delay slots. Existing marker changes only its audited
resident ranges. No full CI is justified for this diagnostic before the result.
Native quiet20.015s capture:32.2884095 completed boundaries/s versus fresh
control32.2889675/s (-0.00173percent, no established marker overhead). Four
checkpoints268800 RGB pixels and8192 paused PCM bytes show zero differences;
registers/heads/enabled equal. USB return/coordinate8 restoration/readback pass.
Among running raw20Hz samples, Main84/112 and Math32/43 were SIG0-marked. This
is sampled sender/submission/fetch-retirement residency, not exact GPU active
time. IRQ bank sampling separately remains Main68.48percent/Math29.21percent.
Both major banks spend most observed time in command consumption/backpressure.

Next: materially reduce RDP primitives/submissions while preserving every
pixel, source lease and priority/window epoch. Investigate merging adjacent
identical regular-BG tiles into wrapped rectangles; retained render tile's
32-texel mirror mask cannot simply be stretched. An explicit8-texel S wrap
and unchanged mirror/gradient/atlas T semantics need a differential proof.
No adjacent cache-size campaign or scalar decoder microoptimization justified.
Private fetch-r37-native.py,
fetch-r37-preflight.json and fetch-r37-physical.json retain recoverable state.

Do not design mixed CI8/RGBA16 multitexturing with TLUT enabled: libdragon's
primary validator explicitly requires TLUT off for non-CI tiles. A fused
palette/true-color shortcut would need a different representational proof:
[primary texture validation](https://github.com/DragonMinded/libdragon/blob/trunk/src/rdpq/rdpq_debug.c#L1286).
Commercial inputs, frame/PCM/SAV/replay/transport and hashes stay private.
