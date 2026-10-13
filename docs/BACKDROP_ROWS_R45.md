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

## Native first trial: image gate stops before performance

Frozen9e1194f:8 initial images537600 pixels and one paused8192-byte PCM buffer
match R44 (heads/registers/enabled too). At stage4200,27 of67200 pixels differ,
all in one horizontal row. The route stops before the second PCM comparison,
frame4320 or any quiet capture. Worker88106 is terminal; coordinate8/menu
restoration/readback PASS. No speed result and no full CI follows this trial.
[Curated discrepancy](evidence/backdrop45-native-difference.json).

Next compare the row's effective retired-section Main color against its new
captured row input/epoch boundary. A live row capture can differ from the
existing section renderer's effective timing; primitive adoption and palette
grouping also remain candidates. Local packet tests do not prove this complete
producer timing. The difference blocks promotion; do not label the baseline
wrong or accept a regression without a matching semantic/reference proof.
Use a bounded source/retired-state control, retain original frozen evidence,
repair or reject the mechanism, then repeat the same frame/image/PCM gates.

## Bounded paused producer-state diagnostic preflight

663ef49 adds16-row paging to the existing section observer, only when both
SECTION_OBSERVER and BACKDROP_ROWS are selected. It reuses the complete paused,
HALT/SP-DMA/DP/retired-frame/queue/end-geometry checks; never accepts arbitrary
addresses or changes any guest/renderer/transport state.177 synthetic controls
include the original142 and row cursor/truncation/ownership/busy/read failure
cases. No new running profiling hook. Raw rows remain private.

The diagnostic binary retains all14 RSP text/data banks byte-exact to9e1194f,
43 owners, staticD2E88<D4000, actualD4400 backups/mutations and linked boot
controls pass. Frozen private rows plan/archive. Read sections at4200 in the
existing R44 observer, then R45 sections and all224 captured Main rows. The
R45 observer compares images against its original discrepant9e1194f artifact
to prove observation isolation; that comparison is not fidelity acceptance.
Paused audio still compares against R44. Native run names
r44-dkc4200-sections/r45-dkc4200-rows, sole rootCOM3, no performance capture,
finallycoordinate8/menu readback. Determine whether row inputs themselves
disagree with the effective legacy section colors before changing rendering.

## Paired native state excludes color-phase fault; scissor repair preflight

Both paired diagnostics complete and restore coordinate8/menu/readback. The
R45 observer reproduces its original discrepant image and retains R44 paused
PCM at4200. All224 Main row values equal the effective R44 retired-section
colors:0 differences. Sections97->28. The synthetic actual CPU line/section
control also matches224 rows under two settings; its existing directed fixture
needed SRLV32 support, not a guest/renderer change. Raw colors remain private.
[Curated paired diagnosis](evidence/backdrop45-scissor-diagnosis.json).

The helper restored RDP_FILL scissor bytes after row fills but never submitted
that restored state. The first no-window BG thus inherited the last row-run
scissor; later OBJ/window cleanup could hide the mistake for later layers.
Memory restoration alone was an incomplete oracle. The repair sends the owned
full-band SetScissor and waits for its command adoption before any layer.
Original source/color/geometry barriers and every row remain intact.

The40 delayed packet cases/589824 pixels now also require the final adopted
full-band scissor. A fifth genuine mutation removes that send and rejects,
alongside short restore/latch/queue/alpha controls.488 row bounds/160 epochs/
2 CPU bindings pass. Bank still1000 bytes, delay slots clean, staticD1E88<D4000.
No duplicated full CI or performance claim. Freeze repaired source/artifact,
then private r45-dkc-scissor reruns the same10-image/four-PCM gates against R44
before quiet20s and the predeclared first240 comparison. First discrepant9e1194f
artifact/report and original no-performance result stay preserved.

## Repaired native DKC: material value measured

Frozen1fcc940 passes all10 images672000 pixels and four paused8192-byte PCM
buffers32768 bytes,0 differences; heads/registers/enabled and all guest input
acknowledgements match. Full checksum/settings/trace and coordinate8/menu
restoration/readback PASS. Worker13682 terminal. Original27-pixel/no-performance
trial remains preserved, superseded for this exact route by the repaired run.

Predeclared same first240 complete guest intervals:13.754889
->28.710314 completions/s (+108.728065percent), explicitwait
53.346966->15.343220ms. Separately, full quiet trace787
intervals39.197267/s and wait6.787748ms; baseline wall-time trace had276 intervals,
so this longer guest-progress segment must not replace the matched comparison.
[Curated native receipt](evidence/backdrop45-dkc-native.json). No presentation
60Hz, full-title/complete sound or corpus qualification follows.

Native material value now justifies broader ALttP image/PCM/cadence and Mode7
controls, then relevant candidate/default CI. The added helper loads on scalar
policies remain a possible regression; repair any permanent loss before
promotion. Full original replay remains available; state serializer still
pending. Master/R44/R43 untouched and BACKDROP_ROWS remains default0.

## ALttP story control and CI cadence correction

Same frozen1fcc940:3 images201600 pixels and8192 pausedPCM/heads/registers/
enabled match, full checksum/settings and coordinate8/menu/readback PASS.
Worker24170 terminal. Cadence55.874278 vsR4456.089884/s
(-0.384394percent), wait2.844090ms. Preserve this small loss as unresolved;
do not claim complete non-regression from matching images. Rain control next
using immutable scissor artifact and existing historical golden replay.
[Story receipt](evidence/backdrop45-alttp-story.json).

Build workflow was automatically triggered on every experimental/doc push.
Earlier statements of no CI dispatch describe manual dispatch only; automatic
default runs are not R45 opt-in qualification. Push now excludes experiment/**
and documentation-only changes, with full master PR/workflow_dispatch gates
retained. CGRAM/Ares already use master/PR/manual and remain unchanged.
Build now explicitly compiles/tests BACKDROP_ROWS1 plus its177 paused observer
guards, fixed slot/arena/backups/boot and inherited/default variants. Dispatch
relevant CI once the native regression decision is resolved; no gate weakened.
