# R37 - Existing sender marker on rain, 2026-10-12

Status: local preflight passed; native measurement pending. This is a bounded
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
One quiet20s native capture, four checkpoint pixels and paused PCM comparison,
then USB return/coordinate8 restoration/readback. Private fetch-r37-native.py,
fetch-r37-preflight.json and fetch-r37-physical.json retain recoverable state.

Do not design mixed CI8/RGBA16 multitexturing with TLUT enabled: libdragon's
primary validator explicitly requires TLUT off for non-CI tiles. A fused
palette/true-color shortcut would need a different representational proof:
[primary texture validation](https://github.com/DragonMinded/libdragon/blob/trunk/src/rdpq/rdpq_debug.c#L1286).
Commercial inputs, frame/PCM/SAV/replay/transport and hashes stay private.
