# Native retired-frame bench on the integrated scalar core

This diagnostic-only extraction retains SC64 PI/USB, register-safe O64 calls,
retired-frame control/export and IPL3 return from d7a071a2's proven bridge. It
does not pull in the experimental renderer, recorder/SD sink, scene serializer,
DSP backend, audio algorithms or save-state support. Ordinary REMOTE=0 loaded
bytes are identical to the full-rate parent; two existing RSP banks stay4KiB.

Build with `make REMOTE=1`. The separate sodium64-usb-bench image requires the
paired menu's8MiB launch route. It selects APU21/fs0/audio4/precision8 before
guest execution, just as HW_PROFILE does. It counts guest boundaries, retired
renders, VI interrupts and actual VI-origin publications independently; these
software observations are not a display/DAC capture. No timer or SD writes are
added. Normal/profile builds remain distinct.

The linked static end must remain below0x800BE200, the original first CGRAM
owner. No cache, framebuffer, CGRAM arena or renderer address is moved. A new
explicit diagnostic lease occupies physical440000..442000, beyond all base4MiB
owners, disjoint from R61's full-DSP/snapshot owners and below IPL3's top64KiB.
It contains guarded register-save/stack/USB/parser/counter regions. It is not an
ELF load/BSS section. Exact IPL3-detected8MiB is captured before SP DMEM changes;
unknown/base4MiB boot stops before any upper access or VI enable. The bridge also
rejects such calls before touching its lease. Boot retires old cache lines and
clears only this lease; ordinary4MiB releases are unchanged.

The parser exposes hello/status, pause, pause-at, step, resume, buttons, release,
frame, audio and menu. Pause targets are absolute retired-frame numbers; step
durations and wrap are bounded. A failed acknowledgement cannot release a step.
Paused exports preserve the retired unpublished framebuffer, wait for final RDP
retirement and export the existing8KiB big-endian stereo ring with head/register
metadata. The ring is not complete sound or final DAC qualification. Menu return
quiesces natural RSP/RDP/SI/PI/AI ownership and reboots via the proven IMEM tail.
While the bridge owns PI, VI leaves a dirty guest SRAM pending rather than
starting a conflicting DMA. This covers a resume acknowledgement after paused
has cleared; the pending dirty flag is retained and committed after return.

Use `tools/sc64-bench/bench.py`'s Session with a private output directory and the
installed deployer. Do not use capture/sav/state commands: those components are
not part of this extraction. Match image checkpoints by absolute guest/render
IDs. Take before/after Count/counter observations around a quiet interval; do
not export images/audio or poll status during a performance interval. Report
this instrumented build's overhead and scope separately from ordinary runtime.

Commercial ROMs, SRAM, pictures, PCM, states and game-derived hashes stay local.
The paired menu requires diagnostic_saves1/diagnostic_continuous1, reserves
separate save paths and uses flashcart_load_save(NULL), disabling automatic
writeback to an original mutable save. Firmware/menu files are unchanged here.

Software gates execute the production parser (52 assertions/32000 malformed
packets), linked boot/upper-owner/register paths, emitted-code counterexamples,
disabled-image identity, RSP delay/layout checks and integrated CPU/APU/audio
regressions. Physical gates still require installation/readback, original-guest
control, pause/step/export/resume, verified return/menu restoration, then aligned
commercial comparisons. Host/linked checks are not native acceptance.
