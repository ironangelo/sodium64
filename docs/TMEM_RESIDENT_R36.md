# R36 - Individual texture residency, 2026-10-12

Status: MEASURED / REJECTED as a material performance improvement. No
full fidelity acceptance or integration. Default flag0 preserves the
retained coordinate8 path and all earlier audio corrections.

Rain has a material renderer deficit: prior R31 measured32.2849 completed
boundaries/s, mean explicit CPU/RSP wait11.255ms. Atomic bank residency in that
capture is predominantly Main, then Math; resident time includes helpers and
waits, not exclusive instruction cost. The global eight-neighbor atlas lost
7.08percent in rain. This experiment instead keeps four individually admitted
64-byte CI8 textures, with direct-mapped character tags. A hit needs only the
original rectangle with its T origin offset; a miss loads one character.

`TMEM_RESIDENT_CACHE=1` requires the existing atlas/coordinate configuration.
Tags in v19 are owned only within the regular BG pass. Every new BG and every
fresh decode resets all residency. Cache palette/version admission, empty
tiles, source retirement, painter order, windows and palette ownership survive.
Four slots fit original T mask5; tile1's load origin is restored before OBJ,
Mode7 and compositor work. No new arena allocation, game profile or skipped
emulation. The primary load protocol is consistent with libdragon's separate
load/render descriptors and nonzero TMEM origins:
[8bpp LoadBlock implementation](https://github.com/DragonMinded/libdragon/blob/trunk/src/rdpq/rdpq_tex.c#L204).

Quick linked preflight:772 draws/49408 numeric pixels,384 loads/388 hits,
36 palette/version refreshes, four mirrors, palette unchanged, three negative
mutations rejected. Ten other RSP banks/data unchanged and fixed public PCs
preserved. Existing asynchronous ownership288 command/24 texture/24 palette/
72 independent-DMA cases pass, LoadSync contract/branch-delay/runtime arena
checks pass (allocatedD15C8 < D2000). No cycle claim follows from these models.

Native measurement: fresh R33-corrected production control versus executable
73619d8 on actual N64, same acknowledged ALttP rain12944 route, precision20 /
skip0/APU21/audio4. One quiet20-second full-checksum capture per version:
32.2889675 ->32.4165279 completed boundaries/s (+0.395059percent), mean explicit
CPU/RSP wait11.245405 ->11.134105ms. Four physical checkpoints268800 RGB pixels,
zero differences;8192 paused PCM bytes plus registers/heads/enabled identical.
Both launch the actual selected ROM. Menu return, coordinate8 reinstall and
readback pass; firmware/saves/config preserved. This is no material gain and
does not justify an exhaustive CI or adjacent cache-size campaign. Neither
cadence nor a paused PCM ring establishes TV/DAC/full-game fidelity.

The final build restriction requires atlas bits3 so every admitted setting
executes tile1 restoration. That restriction does not change either measured
runtime. The rejected experiment stays isolated; retained phase4/master do
not include it. The next discriminant uses the existing FETCH_SIGNAL marker
on the unchanged retained renderer to separate sender/fetch residency from
other Main work. It marks submission and polling, not exclusive GPU execution.
Commercial frames/PCM/SAV/replay/transport and their hashes stay private.
