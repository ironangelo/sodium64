# R46 - Inline proven SPC700 RAM reads

IMPLEMENTED; native discrimination pending. `APU_RAM_READ=1` defaults off.
The latest complete rain CPU profile has 1525 APU samples out of 7110 (21.45%),
in addition to 1719 DSP samples. These are residency counts, not exclusive
timings. The JIT currently calls a general reader even for constant addresses
that cannot select a device or mapped ROM. This experiment removes that work
at translation time; it does not change SPC frequency or scheduler granularity.

Constant direct operands 00..EF admit both direct pages. F0..FF keep the general
reader because P can select I/O page zero. Constant absolute addresses outside
00F0..00FF and FFC0..FFFF admit ordinary RAM. The only mutable map entry is the
top ROM page; indexed/indirect addressing and writes keep their existing paths.
There is no game-specific admission and no new runtime memory allocation.

The emitted read retains the exact guest address in A0 for later RMW handlers,
loads the byte directly, then reads `apu_clock` and debits one bus cycle at the
same position as the general reader. It increments the compiler's worst-case
cycle budget without moving the debit to block exit. This preserves following
I/O timing and the independent source-byte/32-SPC-cycle scheduler bounds.

Local differential execution uses the unchanged general-reader native ELF:
512 direct cases, 68 absolute cases, 20 complete production JIT blocks and two
following timer-read positions. Guest values, addresses, RAM, tags, timers,
DSP registers, semantic GPRs and cycle budgets match. Two actual emitted faults
(wrong RAM byte and missing bus debit) reject. Representative actual scalar
instruction counts fall 23 to 12 for a direct read, 19 to 8 for an absolute read;
these counts are not native timings. The first test harness incorrectly used
the uncached region for JAL target reconstruction; it was corrected before
the successful run. No hardware result came from that fixture error.

Flag zero retains all 872964 allocated bytes of native source1990fb0 exactly.
All 15 linked RSP banks are byte-exact between flags. The candidate static end
is D58D8, below D6000; 43 concurrent owners, full24576 events and194 ROM slots
remain disjoint. Linked reboot12/TV5 cases pass. Parser, renderer, DSP and state
services are unchanged; their prior gates are reused instead of rerun.

The bounded native A/B uses the same source, differing only in this flag,
with the existing quiet-counter same-build scene bench configuration. No
save/load is used to transfer state between builds. At identical ALttP title
and room checkpoints, compare all image pixels and paused implemented PCM,
heads/registers/enabled and acknowledged input. Then quiet20-second captures
compare predeclared absolute title920..1219 and room2000..2599 intervals.
Check capture checksum/settings/frameskip and accepted boundary metadata;
always restore coordinate8 through the verified menu/install/readback path.

A 5% or larger gain on an uncapped fixed interval is promising and merits rain,
DKC and appropriate changed-CPU CI. Below2% in both scenes rejects this direction
as a material performance step; intermediate results need one confirmation,
not a chain of small patches. A capped baseline needs the timing/profile result
interpreted separately. Any image/implemented-PCM difference stops the trial.
Complete DSP/DAC fidelity, native60, wider corpus and master integration remain
open regardless of this read optimization. Direct C++ full-DSP replacement and
the Main-row run producer remain rejected; this does not repeat either trial.
