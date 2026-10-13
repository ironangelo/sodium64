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

## Implemented local preflight

Opt-in BACKDROP_ROWS1 requires SUB_ALPHA1; default0. Two512-byte Main row
queues3E7400/3E7600 stay in the existing pre-Q2 guard, now counted explicitly
in all43 simultaneous owners. CPU records each original live Main color at
the same line-before-HDMA point as the existing fixed-operand queue. Only
eligible indexed Mode0/1 epochs may ignore MAIN_COLOR differences after all
new typed records prove entry0. Every record remains in the lossless stream;
late nonzero entries/markers, overflow, OAM, brightness and every other state
byte reject. Full arithmetic requires unchanged Sub; HALF retains its prior
per-row fixed-input semantics. Checked records advance the CPU proof cursor
without writing/dropping their payload.

An owned1000-byte phase-family helper emits original primitive/scissor/fill
packets for exact equal-color row runs, then restores band geometry and the
entire1024-byte TILE_TABLE before returning to layers. VRAM/OAM stay disjoint.
It keeps scalar Sub/blank/clipped/Mode7/backdrop-math fallbacks and their source
bindings. The initial isolated implementation adds a helper load on those
policies too; measure representative controls before keeping any overhead.
No source arena, fixed .org or memory guard is relaxed.

Local PASS:488 row-bound cases,160 epoch barriers (all64 bytes plus late typed
records),2 actual CPU source publications,40 delayed-DMA/retired-packet cases,
2304 colored rows589824 pixels. Four genuine faults (short restore, pending
RDP latch, wrong queue parity, Main alpha) reject. The existing directed CPU
fixture gained DSLL64 support for the actual compiled exclusion instruction;
the field mutations prove its relevant64-bit behavior. All14 bank delay slots,
12 boot/5 TV cases,43 owners and six inherited CPU words/two banks/fourD4400
backup sites plus three mutations pass. Static endD1E88<D4000. Twelve inherited
RSP text/data banks are exact R44; with flag0 all13 banks and CPU text/data
are exact R44. Reuse those qualified unchanged consumers; no duplicate full CI.

Next freeze source/artifact and run private r45-dkc-route as the recorded
ten-image/four-PCM replay against frozen R44. If those fail, recover menu and
characterize the difference before measuring. Otherwise compare the previously
declared first240 intervals and report the full quiet20s segment separately;
faster emulation can advance farther in that wall-time window. Relevant broader
ALttP/Mode7/default CI follows only if native material value is demonstrated.
