# 2026-10-11 - Native audio observations and CI repair

The active goal includes native speed, visual fidelity and audio fidelity, in
this order: ALttP, DKC1, Super Metroid, SMAS+SMW, Super Mario RPG, Super Mario
Kart, Mortal Kombat1, Yoshi's Island, Star Fox and Doom. This is a qualification
queue, not a current compatibility claim. No DSP sound algorithm changed in
this checkpoint; Road1.0 remains unqualified.

## Physical results and limits

COM3 responded in the paired menu. Observer installation and restoration used
menu-mediated CRC/length/readback receipts. Three ALttP20-second SD captures
had valid S64D checksums, full trace, zero overflow and precision20/skip0/APU21/
audio4/all layers. Initial600/title900/room1980/rain12944 retired images matched
coordinate8:268800 pixels,zero differences. Raw PCM, DSP registers, SAVs,
images and replay inputs remain private.

Before each1024-frame stereo submission, AI was idle on359/587 submissions in
the title/automatic-intro window,179/623 in the room,336/336 in rain. FULL was
never observed. Intentional pauses and post-cutoff SD commits affect these
counts: they are queue-status observations, not exact lost-sample counts.
Maximum gaps near1.89s in this SD workflow must not be presented as ordinary
gameplay gaps. The SD commit is synchronous with guest execution.

A subsequent USB-only room capture excluded SD commit. Its67200-pixel image
again matched coordinate8; the quiet capture had a valid immutable snapshot,
phase6/result2. Endpoint-bracketed duration21.614605s produced682296 stereo
frames,31566.434/s. Programmed AI divider1526 implies nominal NTSC demand
48681812/1527=31880.689/s:99.014% generation,168/666 idle observations,0 FULL,
maximum submission gap42.217ms. Endpoint overhead and initial paused FIFO
drain remain. No final DAC waveform, exact underrun duration or audible
acceptance is claimed.

ALttP requested echo and non-unity master volume at the observed endpoints.
Source inspection found no echo/FIR mix or master-volume application, nearest
sample selection instead of Gaussian interpolation, immediate KOFF disable,
and16-bit wrapping instead of final saturation. Pitch modulation is also
absent, but was not requested at these sampled endpoints. Register intent
does not establish the importance of each missing feature to a specific sound.

Measurements use SECTION_OBSERVER=0 versus the selected historical1. They are
not an audio-optimization speedup. Completed-boundary cadences: title
first300=53.645934/s,room=59.495833/s,rain=32.185454/s; USB-only room59.515700/s.
These are not TV presentation FPS. The per-block observer executes28 scalar
instructions; host instruction counts do not quantify its native cache cost.

Both sessions restored coordinate8 with readback verification:
131072B,CRC2d5daff8,SHA256
a58d70518ae44b4998764f2866b8eb1997d40d173056f43bb224696d0d5c25e2.
The console remained on and responded in the menu. Menu/firmware were
unchanged; no diagnostic build was retained as an audio fix.

## Observer contract and unsuccessful attempts

Add AUDIO_OBSERVER=1 to the retained renderer flags in USB_HARDWARE_LOOP.md,
leaving SECTION_OBSERVER off for this measurement. REMOTE/native trace are
required. The flag defaults0. DSP samples, BRR, envelopes and AI submission
policy remain unchanged. Five counters observe submissions, idle/FULL and
modulo-Count gaps; one constant describes the existing initialization divider.

`audio` requires a retired pause, available frame, no active/armed capture and
an aligned8192-byte ring pointer. It exports an8192-byte s16be stereo ring and
metadata. This is a paused ring, not continuous sound or final analog output.
`audio-reset` clears only the five counters under the same gates. Count is
sampled before PCM export. Only AI_LENGTH and AI_STATUS are read.

The first observer read AI_DAC_RATE and received zero on hardware; its derived
frequency/fraction was invalid and is discarded. The current API exports the
programmed divider, tested against actual linked AI initialization stores.
An early absolute-load pseudo instruction in a branch delay slot was rejected
by fatal assembler warnings before installation. The corrected explicit-base
hook preserves registers outside t1..t4; the original AI_LENGTH overwrites t1.

Corrected USB-only candidate:131072B,SHA256
673efa208739906a5d6ff98ece9192062d0d75ba84d162ac43256235120f4a8d;
CPU ELF97cc6b3a7cf54c797c02bcbfd869b4d31a11adac81d3ff6ce9a08f0a965b996e.
The earlier SD observer used empty emulator
46ca22b54c594657fa8302fd6eb52d36201171c2b9218174aaec0468144db739,
CPU ELF604702ff3d34f92560d0078a28ca9d5a5365755cf2d37a1e3dddf5a6a1797333.
Do not symbolize that earlier capture with the newer ELF.

## Local proof and CI repair

- Production parser171 audio cases+1000 fuzz;153 default+1000 fuzz. MMIO mocked.
- Actual linked observer16 cases plus FULL/BUSY mutation and Count/counter wrap;
  only20 owned counter bytes written. Linked initialization divider1526,
  control1,bitrate15. Recorder/caller102 cases; reboot12+5 cases.
- All12 RSP banks have identical text/data to coordinate8:24 matches. With
  AUDIO_OBSERVER=0 and original flags, CPU text/rodata/data are byte-identical
  too. ELF symbols/alternate ROM titles are not claimed identical.
- Native runtime end0xD15C8<0xD2000;41 owners pass. Fresh unflagged PROFILE
  end0xC15E0;40 owners pass. Eight arena tests cover host/N64 preprocessing,
  unsupported-include rejection and194-slot ROM-cache eviction.
-106 host unit tests pass; window helper1792 compiled cases/two negative
  selector mutations; delayed DPC288 command/24 texture/24 palette/72
  independent DMA cases. Normal4096-byte RSP/fixed-entry binary proof passes.

The exact c82e5d4 checkpoint's three workflows ended with failures:
Build and Validate38160821885 checked normal0xC2000 for native trace using
0xD2000; Ares Profile Validation38160840370 attempted a Windows compiler path
on Linux before SDK setup; Gate C CGRAM Epoch Replay38160840350 expected an
obsolete publication comment/order and later source strings.

The repair evaluates actual conditional macros with an available N64 or host
preprocessor. A host strips only the exact MIPS alias include and rejects
additional includes. Trace/PROFILE/HW_PROFILE/color workflow gates select their
actual arena; no extent assertion is skipped or relaxed.

CGRAM publication proves Main/Mode7 window/draw bindings after DMEM upload,
before raw shadows/SP_PC reset. Independent-slot ordering is allowed; missing,
late, wrong-source and store-before-load mutations fail. The current29-core
replay instructions,3-instruction marker bridge and raw-palette SyncFull fence
are checked. Obsolete color-window peephole strings refer to replaced code:
their footprint/truth claims are replaced by strict4096-byte/fixed-entry
binary checks and actual execution of both current window helpers, preserving
registers/memory and rejecting complement mutations.

A dedicated CI job builds the retained renderer flags plus AUDIO_OBSERVER and
executes parser, linked DSP/AI init, recorder/caller, reboot, arena, delay-slot,
lifetime and window guards. Local PASS does not invent a fresh GitHub PASS.
The draft PR stays unmerged until exact-head CI and integration qualification.

## Next condition

Room CPU residency is largely DSP/APU; buckets include helper/cache/interrupt
effects and are not exclusive costs. Rain retains substantial RSP waits.
Investigate exact DSP work reduction before adding faithful missing features,
using native PCM/image/configuration checks and quiet timing. Pitch-conversion
caching remains a proposal until clock/register-write invalidation, full-range
equivalence and native evidence are proved. No pitch cache or sound correction
is implemented by this entry.

Private evidence remains in the dated2026-10-11 USB bench beside the older
journal. [Aggregate evidence](evidence/native-audio-observer-2026-10-11.json).
