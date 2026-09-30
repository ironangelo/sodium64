# Stage 2 hardware investigation

The original candidate `b18ff622fe475c38207506d8fe7dc5207a2cfef4` recorded
60 guest frames per 60 VI in all five windows for both original guests on N64.
The returned videos show a green-looking band where the laboratory reference
is yellow, intermittent cyan/blue stripes below it, and final solid red.
Mixed DSP activity is measured; correct audible output remains unqualified.

## Confirmed profiling-build memory collision

Normal static runtime ends at physical `0xBC970`. The delivered HW_PROFILE
runtime ends at `0xC0A50`, but candidate boot-clear/CGRAM allocation started at
`0xBE200`. This destroys part of the stored Mode7 RSP source and DSP1 data.
The previous semantic runs used the normal build and did not reject the
profiling-build collision. The old real-hardware throughput measurements do
not certify correct composition, Mode7 or DSP1 with that binary.

Move the candidate Q1/base/sideband block to `0xC2000..0xC8E00`, preserving
Q2 at `0xD7000..0xDD000`, the compact surfaces and fixed RSP overlay ABI.
`scripts/check_runtime_arena.py` rejects any allocated ELF section intersecting
the complete boot-clear/renderer interval. It must run on normal and profiler
builds. The previous HW_PROFILE ELF is a real negative control.

This collision is a confirmed defect, not yet the demonstrated cause of the
mode0 image/audio observations. Do not claim all hardware symptoms fixed from
the layout repair alone.

## Publication observation

`scripts/capture_stage2_publication.py` runs the original HW_PROFILE guests
continuously until the existing five measurement windows finish. It stops
once before finalization/red-fill, reads the actual VI-selected framebuffer,
and checks the complete eight-row band against the independent color/window
reference. It does not seed memory, change guest state, single-step or stop
between guest frames. It also compares the stored Mode7 source to the linked
binary. The pinned ares lab runs old and repaired profiling variants.

This addresses a gap in the original per-frame capture. It remains emulator
evidence, not a substitute for real N64. Hardware color/publication/audio
diagnosis and matched stable-master measurements remain open.
