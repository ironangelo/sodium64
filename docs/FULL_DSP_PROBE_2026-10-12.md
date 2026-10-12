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
Native results are below; no gameplay replacement was made.

The optional diagnostic uses CPU/RSP arenaD6000. All41 simultaneous owners,
full24576-event capacities,194 ROM slots and raw palette shadows remain
disjoint; the last event leaves512 bytes before raw palette. StaticendD4BE8
leaves5144 bytes before the arena. Six CPU queue words/two embedded banks/four
actual DMA sites agree atD6400; three stale/disagreement mutations fail.
Nine linked core functions/36 straight-line HI/LO writer sites satisfy the
VR4300 spacing contract. Boot12/TV5, frame bridge5 and RSP delay gates pass.
All855212 allocated bytes with the flag disabled equal coordinate8. No full
CFG/pipeline/DAC claim follows from the instruction check.

The first `-ffreestanding` compile failed because old header allocator names
are hidden by the SDK C++ wrapper. `-fno-builtin` with hosted declarations fixes
parsing; no malloc/free are linked or called. The first parser fixture expected
a failed-menu reply instead of the established pending ACK; corrected to the
actual contract. The linked-word scanner initially omitted the physical
address mask; corrected before native use. None was a hardware result.

R33 exact Build38190497219/CGRAM38190500533/Ares38190500532 all succeed.
New exact CI and native experiment remain independent. Master is preserved,
PR21 stays draft. All commercial artifacts and their hashes remain private.

[Curated evidence](evidence/full-dsp-probe-2026-10-12.json).

## Physical results and implementation decision

Executable source4715b8055c2e5a1201acd22959368d57852cafce,
ELF26a9264eed2cae89bccabca83d6cac39bf0d6af629bc5ce2176bbc413dca9ecd,
empty147456-byte ROM2ebc4bb72220432bad775f1e089dad564244e9b1104fdd294c3d720bff07e89f.
ALttP was selected normally through the menu and paused at600. Three bounded
repeats of all three original synthetic scenarios produced18432 stereo frames;
all nine sample checksums/nonzero counts match the PC's unmodified primary core.
Every trial backed up/read back/restored64KiB APU RAM.8192 live PCM bytes,
67200 RGB pixels, all128 DSP registers/head/enabled and guest/render boundary
are unchanged across the trials. Actual gameplay then steps60 frames to660,
with no transport/menu error. USB return and coordinate8 restoration/readback
pass; the menu responds without Reset or firmware/menu changes.

| Synthetic workload | Median core time for2048 frames | Fraction of64ms available |
| --- | ---: | ---: |
| One voice | 68.197ms | 106.557% |
| Eight high-pitch voices | 92.255ms | 144.148% |
| Eight with echo/FIR/feedback/PMON/noise | 96.740ms | 151.157% |

These Count spans exclude initialization, checksum, USB backup/restore, AI,
guest CPU/APU execution and concurrent renderer traffic. They are standalone
core cost at nominal46875000Hz Count, not presentation FPS or measured DAC
cadence. All three exceed the64ms budget for2048 frames at32000/s even before
the rest of the emulator. This compiled clocked C++ core is therefore rejected
as a direct gameplay replacement. It remains an independent behavior oracle.
This is not proof that every optimized assembly/vector implementation must
have the same cost. Next work must reduce actual DSP work while retaining the
reference behavior, alongside the already identified rain renderer constraints.

Exact4715b80 CGRAM38199991297 passes; Build38199987952 and Ares38199991280
were still running when this evidence was published. Fresh documentation head
CI is independent. Master stays unchanged, PR21 remains draft and the full
60FPS/visual/audio matrix objective remains open.
