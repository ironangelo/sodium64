# Codex native hardware history, 2026-10-04 through 2026-10-11

This ledger reconstructs the local work since the last published A14 checkpoint
`018630ffb8944f22dcdfd3dcafb427a7b2e4cd42`. The reconstruction is published
as a current coherent source snapshot; it does not invent intermediate Git
commits or claim historical CI ran against this new commit. The private journal,
build archives, verified installation receipts and benchmark summaries were
read to assemble these decisions. Raw commercial material is excluded.

The working target remains full fidelity and sustained 60 in all selected
ALttP scenes, then DKC1 and SMW. No iteration in this ledger completes Road 1.0.
A13 DKC/ALttP 000002/000003/000004 map to scenes 1/2/3. A11/A13 filenames and
build provenance retain their previously documented interpretation.

## 2026-10-04 to 2026-10-08: recorder and physical control

**H01 — A14 recording failure.** The user pressed Start, saw no OK, and found
more SAVs than presses. The inspected A14-labelled files were menu reservations
without completed S64D captures; the earlier batch of 80 cannot measure FPS.
Each launch reserves up to 16 fresh 32 KiB targets. A filename/size/magic alone
does not validate a capture. The extra reservations are expected capacity,
not spontaneous measurements. Do not delete or reuse them automatically.
Direct PC access to SD while the N64 owns it is unsupported, but that fact
alone did not explain all recorder failures.

**H02 — continuous sink and error attribution.** Retain the first SC64/PI error,
DATA0 response and phase instead of losing them to another register read.
Initialize/check SD/card state, serialize PI/SC64 unlock/register access, bound
waits, verify the descriptor and globally disjoint reserved sectors. Measurements
seal at cutoff and persist after a natural retired boundary. Header complete=0,
readback every body sector, then commit/readback complete=1 before OK. A fully
sealed immutable USB snapshot is separate from mutable guest SRAM. Two
successive physical SD captures sealed with valid checksums and resumed gameplay.
The notice now expires with an active bit: a 32-bit deadline wrap no longer
re-displays old OK. Start during a capture is ignored, exhaustion/failure is
explicit, and slots never wrap. Tests include actual bridges, SD failure phases,
post-seal races and transport mocks; mocks remain distinct from physical proof.

**H03 — USB ownership on a powered N64.** Queries and messages responded in
the stock menu and A14 while the user confirmed normal SMW operation. A unique
scratch file sent through the running menu was independently read after power
off and removed. This proves menu-mediated writes, not concurrent PC filesystem
ownership. Runtime transport initialization first disabled USB after boot;
serializing PI ownership and preserving first errors corrected the failure.
S64R mailbox attribution, bounded polling and application receipts were retained.

**H04 — paired menu and actual game launch.** Running an empty emulator or the
synthetic fixture is not running the user's selected game. Launch must resolve
the game path and call the existing cart_load_emulator/INI/save/pool pipeline,
including the injected ROM offset 0x104000 and supported copier-header offset.
The fixed path API avoids relying on a currently selected browser entry.
Host tests execute the real parser and loader with synthetic files; loader,
pool and acknowledgement failures are covered. Early black screens and a pink
fixture were not accepted as real-game captures.

**H05 — packaging/ABI failures.** ASSERTION FAILED: File not found:
rom:/cursorsound.wav64 was a menu DFS/assets mismatch. Preserve original assets
and match libdragon tools to the linked library; do not repair by removing
sounds. FatFs FIL/FATFS layout differed between new headers and old library.
Pin FatFs R0.16 revision 80386 and rebuild all eight consumers, including
flashcart_utils and USB/menu diagnostics. POSIX rename is unsupported here:
use f_rename, verify the closed temporary file, retain the previous destination,
and rollback on commit failure. The paired asset guard has 16 host cases;
menu protocol/loader recorded 52 checks and host transport 17 at that checkpoint.
Failed or frozen menu instances could not service USB and required power off.

**H06 — cooperative return to the menu.** First return stalled the bootloader:
wait boundedly for VI_CURRENT=0 before stopping output and preserve H/V sync.
Another return answered USB while TV remained black: the runtime read TV type
from RDRAM 0xA0000300, an iQue path. Modern IPL3 passes it at DMEM+9, which RSP
uploads overwrite. Capture it before RSP, retain valid 0/1/2, use NTSC1 fallback
for invalid input, and pass it through the owned bootstrap. On October 8 SMW
returned over USB and the user confirmed the normal menu, without Reset.
Boot checks: 12 cases plus five TV cases; recorder 102 compiled cases, parser
45 plus 1000 fuzz at that milestone. A responsive runtime can return; an
unresponsive CPU/bootloader may still need a human power cycle.

**H07 — loop actually available.** Menu: hello/status/list/listdir/launch/install.
Emulator: pause, future pause-at, step, resume, bounded acknowledged buttons/
release, capture, frame, sav, profile, menu and optional retired sections.
Pause/export use retired RSP/DP ownership; sections are read from the completed
queue, not guest registers already describing the next frame. Permanent
emulator/menu replacements go through the running menu, with CRC and closed-file
readback, temporary name, retained previous file and rollback. This is a
compile → cooperative return → install → launch game → replay → measure loop.
It is not live source editing, arbitrary hard reset or power control.
Only one host owns COM3. A launch acknowledgement precedes emulator USB
initialization; wait for mode=emu before frame commands. Late status timeouts
after successful measurements must be separated from measurement failures.

## 2026-10-08 to 2026-10-10: renderer experiments

All rates below are **completed-boundary cadence**, using full retained intervals,
not physical TV FPS. Keep scene/replay identity and measurement scope: early
intro-attract is not the later first-300-interval title measurement. Retained
comparisons used precision 20, skip 0, APU 21, audio 4 and unrestricted layers.

| ID / hypothesis | Native observation | Decision and limits |
|---|---|---|
| R00 baseline USB build | intro-attract 30.794/s; room 30.340/s; rain 21.665/s; RSP waits 17.656/19.258/26.201 ms | Baseline, not completed 60. |
| R01 sparse 1 KiB dirty VRAM snapshots | paired room 30.294→30.691/s (+1.31%); rain 21.721/s | Retain exact ownership/copy path; reject VRAM-copy-as-main-bottleneck hypothesis. Two 1057-case guards each compared 69,271,552 bytes. |
| R02 atomic SP SIG4–6 bank residency | room Math 65.73%, Main 32.41%; rain Math 51.89%, Main 46.44% | Retain opt-in profiler. Resident helpers and DMA count with their bank; not exclusive cost/instruction tracing. Old non-atomic PC/DMEM bank labels are unsuitable attribution. |
| R03 128-pixel wide Math, uniform policy | room 30.729→34.255/s (+11.47%); rain 21.767/s vs21.882 | Retain safe admission and old 32-pixel fallback; rain improvement not established. Exact RGB555 kernel retained. |
| R04 compact Main eligibility tags | room 39.495/s; rain 23.842/s | Retain. Actual Main/Mode7/phase/backdrop producer-consumer guards and forbidden-winner cases; operands/kernel unchanged. |
| R05 pre-scan effective Math masks | room about39.428/s; rain 26.989/s | Retain uniform-vector batching including COLOR windows; mixed policies fall back. Preserve fixed-row operand semantics. |
| R06 TLUT unary color transform | room 59.841/s, wait about0.001524 ms; user reported TV60 | Retain only fixed operand or absent-Sub, uniform policy classes and exact palette transform. Not a general Sub replacement. |
| R07 full-row exact Math DMA | rain 26.989→27.391/s (+1.49%) | Retain full Main/Winner/Allow streaming with VRAM/OAM save/restore; three row DMAs replace 24 narrow transfers. 12 cases/70,912 pixels plus three negative mutations. |
| R08 RDP half arithmetic, v4→v6 | rain30.918→31.733/s; v6 +15.85% over R07 | Retain narrowly admitted BG1 half/real Sub/fixed0 path. ENV_ALPHA251/256 and presence∩winner depth gates; final palette/FullSync retirement and source leases preserved. Five native checkpoints,336000 pixels,0 differences. |
| R09 no-input scene characterization | title first30052.668/s, wait0.0023 ms; story36.175/s, wait12.921 ms | Title CPU-side limitation; story still RSP-heavy. CPU/APU/DSP sampled buckets are not exclusive function timings. Do not label a20s title/story mixture as title. |
| R10 direct full RDP add/sub probes | seeded probe fullADD144/fullSUB128 mismatches; half-then-double368/272 | Reject general direct full arithmetic. Correct texture copies do not prove correct combiner arithmetic. Native synthetic data, not game golden output. |
| R11 full fixed operand with per-column COLOR allowance | paired story36.176→42.116/s (+16.42%); wait12.919→8.905 ms | Retain exact packed fixed-window bank/fallback; do not globally admit nonuniform COLOR windows into the older unary path. Five336000 native pixels,0 differences. |
| R12 bounded small fixed RDP operand | synthetic all544 pairs with fixed0..16 correct; outside range fullADD240/fullSUB240 mismatches | Admit only each RGB5 component≤16, exact spans/clip restrictions; unrestricted full math stays rejected. |
| R13 RDP fixed bank and command batching | story52.295/s; batchv2 52.399/s, wait4.055 ms | Retain scoped fixed-bank path. Batchv2 +0.199% alone is not convincing new FPS gain. Scissor/coalesced allow spans, palette restore and retirement remain required. |
| R14 generic TMEM atlas32/atlas8 | 32-entry variants50.376/50.767/s; atlas8 story54.196 but rain32.118→29.844/s (-7.08%) | Reject global selection despite story gain. Four268800 native pixels,0 differences; baseline restored/readback verified. |
| R15 flat COLOR-window TLUT admission | corrected isolated story52.407 vs52.399/s (~0.014%) | Reject performance case; default off. Initial selector1/2 oracle inversion caught before hardware by original compiled Setup and Snes9x clip semantics. Corrected4480 policies/1,146,880 truth checks plus960 old-Setup cases/245760 masks. |
| R16 coordinate atlas4 | story52.020/s (-0.72%); five336000 native pixels,0 differences | Reject performance case. A smaller group alone does not guarantee lower runtime cost. |
| R17 coordinate atlas8 with visible-Sub fallback | story55.635/s (+6.176%), wait2.847 ms; title52.698,room58.008,rain32.107/s | Retain selected candidate. Nine native checkpoints604800 pixels,0 differences; title/room/rain use previously measured same-config baselines, not simultaneous pairs. Still no60 qualification. |

R17 fetches 512-byte groups, changes maskT to6 only on miss and offsets the
rectangle's T by (character&7)<<8. S, gradients and other coordinates are
preserved. Restore maskT5 and the original scissor before other paths.
Visible Sub uses the legacy single-texture protocol; fresh decode invalidates
the cached group, and palette/version/source-fence rules precede both paths.
No foreign VRAM/OAM metadata or upper TLUT scratch is borrowed. Host guard:
64 object cases,1832 draws/117248 numeric pixels, four mirrors,120 invalidations
and six negative mutations. Default-off CPU text and ten RSP text/data images
match the preceding best checkpoint. Public entry ABI remains fixed.

## October 10: supporting fixes and fidelity findings

**H08 — reservation cursor.** Repeated FA_CREATE_NEW scans restarted from1 for
every slot, making a launch take up to216s. A shared next-ID cursor scans old
names once per pool:112 attempts for96 existing names plus16 new reservations.
26 pool cases pass; native launch30.328s, first checkpoint unchanged. Finite
reservations are still not completed captures; no wrap/deletion was introduced.

**H09 — PROFILE arena.** Strict checks caught PROFILE allocated end0xC2B10
crossing old0xC2000 by0xB10. PROFILE now uses0xD2000 consistently in CPU/RSP
preprocessing and --profile arena checks. New build gap0xF4F0;40 simultaneous
owners, lastDMA8,24576-byte cap and six event tests including the old-boundary
negative pass. Normal/native layouts stay intact; PROFILE was not installed
for physical acceptance. Selected native end0xD15C8 leaves0xA38 before arena.
The gate was not loosened or suppressed.

**H10 — Uncle sprite / bed flicker.** Retired-frame samples were stable.
Independent local Snes9x1.63 RGB5 comparison matched783/783 Uncle pixels,
1680/1680 bed and17664/17664 room pixels. This is an independent software
reference, not SNES hardware authority. The user reconnected N64 video and
confirmed both distorted sprite edges and minute bed flashes disappeared,
without an emulator change. Do not change palettes/VI to fix that resolved
connection problem. USB exports end before VI/analog/HDMI/TV and cannot alone
certify the final signal or audio.

## Selected state and remaining work

The current installed empty emulator is R17 coordinate8, SHA256
a58d70518ae44b4998764f2866b8eb1997d40d173056f43bb224696d0d5c25e2,
CRC2d5daff8,131072B; paired menu803a716bb51ebef672c43a80671776fcae4a0330d5348aeeda8954666113a144,
CRCfddd021a,1736704B; firmware2.20.2 unchanged. These describe the last verified
installation, not a fresh live query during this documentation synchronization.
The October7 user package still contains the earlier28360985 emulator; it
must not be mistaken for this later candidate. Rejected builds and prior best
are retained privately for recovery. No commercial payload is published.

Final R17 comparisons:
- story52.3992954235→55.6354620925/s, +6.175974%;
- title52.7329916818→52.6975906984/s, -0.067%;
- room57.9848488623→58.0084232870/s, +0.041%;
- rain32.1184701245→32.1067679697/s, -0.036%.

Quiet captures are complete/checksummed, full trace/no overflow, same fidelity
settings. These three near-zero deltas are not meaningful FPS improvements.
Nine identical sampled frames do not prove every frame of every game correct.
Do not repeat R10/R14/R15/R16 unchanged; reopen only with a changed mechanism
and a scoped physical comparison that can overturn the rejection.

User's approximate manual backlog was from a version before the latest work:
ALttP title improved below60, automatic story about30, rain unfinished;
DKC1 logos about60, Cranky/DK intro improved below60, stage1≤20; SMW similar.
Mario Kart menus about60 but character selection layers and race timer/items
wrong, races≤20. Super Metroid averaged about40 with some near60/fewer glitches.
All-Stars+SMW freezes after Welcome/world message; Mario RPG does not boot.
These are user observations, not revalidated R17 results. Keep as backlog,
not a detour from finishing ALttP before DKC/SMW.

Next investigations remain proposals: title/room APU/DSP CPU costs (e.g. pitch
conversion caching only after register-write invalidation is proved), and
story/rain submission/texture traffic. No pitch cache or audio change has been
implemented. Resume from the selected build recipe and these rejected cases;
a sampled instruction/function label is a hypothesis, not a speedup.

## R18 - Audio observation and CI selection repair

The next bounded checkpoint is recorded in
[the native audio observations](AUDIO_OBSERVER_2026-10-11.md): three valid SD
captures, a subsequent USB-only room capture, AI queue observations, invalid
DAC-rate read discarded, absent sound features identified, current observer
guards and source-oracle/arena portability repairs. This does not implement
an audio algorithm change. Coordinate8 was restored; the menu responded.
The expanded qualification queue includes visual and audio fidelity.

## R19 - Exact pitch cache, preserved PCM and native measurements

[Pitch cache evidence](DSP_PITCH_CACHE_2026-10-11.md) records the opt-in cache,
exhaustive linked byte/voice tests, four unchanged images and three unchanged
PCM rings. Title improves modestly, room approaches its nominal cadence and
rain remains around32 completed boundaries/s. Quiet AI production exposes
rain undersupply. The selected coordinate8 emulator is restored. A separate
synthetic BRR audit against the pinned reference identifies signed-rounding,
invalid-range and saturation discrepancies for the next fidelity change.
The preceding d4cc32f source checkpoint passes all three GitHub workflows.

## R20 - BRR integer fidelity correction

[BRR proof and physical observations](DSP_BRR_ACCURACY_2026-10-11.md) records
the corrected invalid ranges, signed filter rounding and saturating15-bit
sample storage.57344 linked voice cases and four independent mutations pass;
the public arithmetic oracle also matches the unmodified compiled primary
method. Four native images remain identical, while PCM changes as expected.
Single-window cadence differences remain below1%; no universal cost or speed
claim follows. Coordinate8 is restored. Full mixing, echo, interpolation and
other DSP work remain open. Preceding8453175 workflows all pass.

## R21 - Physical BRR input/output proof

[Native BRR trace](NATIVE_BRR_TRACE_2026-10-11.md) records an opt-in 32-record
ring and pause-only export. The actual N64 produces 128 half-scaled samples
matching the unmodified compiled primary reference, with zero differences.
The room's 67,200 pixels and 8,192 PCM bytes remain unchanged by tracing.
The sampled physical case covers seven voices, filter 2 and three ranges;
57,344 synthetic voice cases cover the broader arithmetic space. Trace hooks
add 40 instructions per chunk, so no observer-free speed claim follows.
Coordinate8 is restored and the paired menu responds. Full mixing/DAC and
constant-60 qualification remain open. R20's three exact-commit workflows pass.

## R22 - KOFF note tails and additional observer memory

[Release correction and limits](DSP_KOFF_RELEASE_2026-10-11.md) records the
opt-in eight-unit per-sample release, preserving selected voices until silence.
16,384 envelope/voice cases, actual sample/APU callers, protected ADSR writes,
KON reset/dispatch and two mutations pass. Four native checkpoints preserve
268,800 pixels; 785/261/0 PCM bytes change across title/room/rain. All six native
release endpoints match the decrease/clamp. Single-window cadence differences
remain below one percent and rain still produces about 54% of nominal AI.
Coordinate8 was restored after this trial. Full audio and constant-60 remain open.

R21's optional observer CI fails its strict static-memory assertion, while the
other build jobs and both independent workflows pass. BRR_OBSERVER now shares
a 0xD4000 Q1 arena between CPU/RSP and a matching strict linker check. Other
layouts remain unchanged; 10 arena regressions and all 41 owners pass. The
relocated observer's hardware qualification is separate from R21's earlier
0xD2000-layout result. Failed assembler delay-slot expansion and unsupported
legacy DIV in an expanded test are recorded with the repaired scope.

The subsequent combined/relocated trace trial reaches pause600, then loses
emulator USB during step1380; last acknowledged progress790. Status and
restoration writes time out while firmware info still responds. Cause remains
unresolved. The combined experimental template is last installed; coordinate8
restoration after this second trial is pending physical Reset/power-cycle
recovery. This failed trial does not invalidate the completed release-only
three-scene evidence, and it does not qualify the relocated observer.

## R23 - Recovery after the combined observer timeout

Physical Reset returned the paired menu. COM3 hello and status confirm menu
mode; coordinate8 installation/readback matches its known empty-template hash
and CRC. The interruption recorded at R22 is resolved. The combined observer
still lacks physical qualification. Next, isolate relocated BRR with KOFF off.

## R24 - Relocated observer without KOFF

[Distinct native trial](BRR_OBSERVER_ISOLATION_2026-10-11.md) reaches the room
and returns/restores coordinate8 without Reset.67200 RGB pixels,8192 PCM bytes
and128 decoder half samples have zero differences. Both KOFF and USB polling
differ from the preceding failure, so its cause remains unresolved. Exact1b
Build/CGRAM pass; Ares cancelled is not PASS. Next: exact combined with quiet
USB replay. Full audio/constant60 remain open.

## R25 - Observer macro discarded and USB-state overlap

[Actual binary fault](BRR_ARENA_BUILD_FIX_2026-10-11.md) records the second
combined timeout despite quiet20s. Make resets the RSP flag after appending
BRR_OBSERVER: compiled backups stillD2400, overlapping combined USB BSS.
R24 no-KOFF comparison remains valid, but its unified-layout claim is corrected.
The fresh fix changes exactly four loaded bytes; a new CPU/embedded-RSP/DMA
regression rejects the old binary and three mutations. Corrected native trial
awaits physical recovery; no restoration is claimed after this interruption.

## R26 - Remove repeated exclusive-open filename probing

[Single directory scan](POOL_DIRECTORY_SCAN_2026-10-11.md) retains exclusive
creation and all save/sector ownership rules. The real helper uses one scan
and16 creates for96 old files, versus112 creates previously. Scan failures,
name noise/case/exhaustion and a creation race pass;26 prior pool cases remain.
Pinned menu build, FatFs ABI, unchanged DFS,52 USB host/16 asset checks pass.
Native installation and timing remain pending menu recovery; no FPS effect
is claimed. Previous measured launches203.703/209.703s are not fully attributed
to probing without a physical timing comparison.

## R27 - Corrected RSP arena native cycle verified

[Physical correction](BRR_ARENA_NATIVE_2026-10-11.md) passes600/1380/1980
replay with quiet20s, zero67200 RGB/8192 PCM differences and128 BRR samples
matching the primary compiled method. USB return and coordinate8 restoration
readback pass without Reset. The preceding blocker is cleared. Exact7d83886
Build/CGRAM/Ares all succeed. No speed, full DAC or60fps matrix claim follows.

## Publication and workflow boundary

Code goes on a development branch; continuity keeps the newest dated entry at
the top and preserves the entire cloud Work history below it. A draft integration
PR makes the snapshot reviewable. Master remains the stable reference while
whole-image/armed/audio and exact branch CI qualification are outstanding.
Documentation synchronization is not a release, a merge qualification or a
Road1.0 completion. Before every further physical iteration record the source/
flags/empty binary identity, hypothesis, private evidence location, outcome,
retained/restored version and next condition that would justify reopening it.
Update continuity after each bounded result so future sessions need not replay
this reconstruction.
