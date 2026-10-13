# R45 - bounded Main backdrop rows hypothesis

HYPOTHESIS only. Preserve measured R44, master and every prior candidate.
Existing paused observer reproduced10 native DKC frames672000 pixels and
four paused PCM buffers32768 bytes exactly, then read97 retired sections at
guest/render4320. There are96 nonempty sections covering224 rows:84 single-row,
7 two-row,3 three-row,1 four-row and1 113-row. Of95 adjacent differences,
85 change only MAIN_COLOR,2 MAIN_COLOR plus BG scroll,1 scroll only and7 have
identical64-byte state except boundary. These records alone do not establish
CGRAM event or brightness equality. Raw section records stay private.

R44 quiet13.771777/s versus R43 13.778162, explicitRSPwait53.298928ms. Current
Main/Math work is repeated across these tiny real sections. Test a generic
row-backdrop representation with guarded CGRAM0 epoch coalescing; retain every
guest write, row color, geometry/window/OAM/brightness and nonzero palette
barrier. The [primary Snes9x tile renderer](https://github.com/snes9xgit/snes9x/blob/master/tileimpl.h)
separately renders the backdrop using color0 and tests indexed tile pixels
for transparency. This is a semantic cross-check, not a substitute for proving
Sodium64's actual producer/consumer chain.

Bound the first implementation to indexed Mode0/1, uniform fixed-color
selection without Main clipping/direct color/backdrop arithmetic. Keep Sub
color and every other section field unchanged. Scan all new typed events:
only entry0 may merge; markers/other entries/overflow/brightness/dirty OAM
reject. All events remain in the existing lossless stream; only their derived
rendering grouping changes. Main backdrop gets its captured color for every
row, with primitive fills grouped only for identical adjacent colors. A small
owned phase helper may borrow TILE_TABLE only with exact backup/restore and
completed RDP command leases; VRAM/OAM and resident ABI remain protected.
Default flag stays0 and no game identity enters admission.

First prove actual CPU row capture/epoch guards including negative tokens,
all packet/source bindings and exact row/RGB5/depth/scissor output with scratch
restoration and real mutations. Compile with strict fixed-slot/arena checks.
Then native short DKC replay must preserve10 images/four PCM buffers before
comparing the fixed first240 intervals and full quiet20s trace. Any mismatch
blocks promotion. No full CI until native material value; if useful, broaden
ALttP and Mode7 regression controls before relevant CI/integration acceptance.

Save states remain a useful bounded diagnostic follow-up. This newly measured
renderer mechanism has priority now; no serializer or restore has been built.
Native60/audio/full corpus and R44 wider compatibility remain open.
