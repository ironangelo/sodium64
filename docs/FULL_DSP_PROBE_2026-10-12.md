# R34 - Complete S-DSP cost probe (2026-10-12)

R31 physical production results still fall short: ALttP title51.86, room57.67,
rain32.28 completed boundaries/s; the dry path still lacks Gaussian history,
KON priming/latching, pitch modulation and echo/FIR. These are not60 FPS or
full audio qualification. R33 corrects a separate GAIN accumulator defect.

The primary reference uses three decoded groups during KON setup and
interpolates before advancing pitch. Sodium's current four-sample buffer is
cleared at KON and first decodes after a counter carry, using the new counter
as the BRR byte offset. A skipped first group/different phase is a hypothesis
to test, not an attribution of the user's audio symptoms or a shipped repair.

To choose a complete DSP implementation with measured cost, FULL_DSP_PROBE=1
links unmodified snes_spc0.9.0 source, pinnedec8ee2b, LGPL-2.1-or-later. Its
clocked core includes history/KON/Gaussian/envelopes/PMON/noise/echo/FIR. The
author documents its behavior validation on SNES. That upstream claim does
not qualify this wrapper, guest scheduler integration or N64 audio output.
Sources: [author](https://slack.net/~ant/libs/audio.html),
[pinned code](https://github.com/blarggs-audio-libraries/snes_spc/tree/ec8ee2bbe30451614c1d02a83f7af1c97d497d45/snes_spc),
[Snes9x1.63 phase reference](https://github.com/snes9xgit/snes9x/blob/1.63/apu/bapu/dsp/SPC_DSP.cpp).

The pause-only audio-full-dsp-probe command accepts no arguments. It backs up
and reads back all64KiB of APU RAM to exclusive volatile cart USB TX scratch,
using the established PI/configuration path, then runs three original
synthetic workloads: one voice; eight high-pitch voices; eight voices with
echo/FIR/feedback/PMON/noise. Each produces2048 stereo frames. Count spans only
each32-frame core call; setup, checksum and USB backup/restore are excluded.
No synthetic PCM is submitted to AI. Guest DSP fields, PCM ring, renderer and
guest deadlines are untouched. All APU RAM is restored/read back before reply.
No SD engine/file/save is used. A restore failure denies gameplay/capture and
further probes while retaining a menu escape; it cannot silently resume.

Host tests execute the unmodified full core and transaction:6144 frames,
128 backup/readback +128 restore blocks,16 failed backup positions, one
corrupted backup, two restore faults, five invalid inputs. Parser201 cases
+1000 fuzz includes paused/capture/arity guards and failed-restore lockout.
Native cost and cross-architecture sample checksums are still pending.

The optional diagnostic uses CPU/RSP arenaD6000. All41 simultaneous owners,
full24576-event capacities,194 ROM slots and raw palette shadows remain
disjoint; the last event leaves512 bytes before raw palette. StaticendD4BE8
leaves5144 bytes before the arena. Six CPU queue words/two embedded banks/four
actual DMA sites agree atD6400; three stale/disagreement mutations fail.
Nine linked core functions/36 straight-line HI/LO writer sites satisfy the
VR4300 spacing contract. Boot12/TV5, frame bridge5 and RSP delay gates pass.
All855212 allocated bytes with the flag disabled equal coordinate8. No full
CFG/pipeline/DAC claim follows from the instruction check.

The first ff-reestanding compile failed because old header allocator names
are hidden by the SDK C++ wrapper. fno-builtin with hosted declarations fixes
parsing; no malloc/free are linked or called. The first parser fixture expected
a failed-menu reply instead of the established pending ACK; corrected to the
actual contract. The linked-word scanner initially omitted the physical
address mask; corrected before native use. None was a hardware result.

R33 exact Build38190497219/CGRAM38190500533/Ares38190500532 all succeed.
New exact CI and native experiment remain independent. Master is preserved,
PR21 stays draft. All commercial artifacts and their hashes remain private.

[Curated evidence](evidence/full-dsp-probe-2026-10-12.json).
