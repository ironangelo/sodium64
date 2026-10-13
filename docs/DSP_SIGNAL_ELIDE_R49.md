# R49 - Discarded interpolation work in the complete DSP probe

IMPLEMENTED; native cost pending. `DSP_SIGNAL_ELIDE=1` defaults0 and requires
FULL_DSP_PROBE1. It changes only the diagnostic clocked complete core. There is
no gameplay replacement or master integration; the current mixer stays intact.

The pinned core's V3c computes pure Gaussian interpolation even when latched
NON replaces its value with noise or envelope0 makes its contribution exactly0.
The opt-in variant selects noise directly and bypasses interpolation/product
only for env0. It still runs every voice phase, BRR/history/pitch, PMON, KON/KOFF,
envelope counter, register latch, noise and echo/FIR operation in original order.
No phase, sample or emulated deadline is removed. Interpolation has no state
write. Later envelope advancement remains after the same output/envx capture.

The default compiled core retains all18 executable sections byte-exact to the
pinned source. Only V3c and its compiled run caller differ with the flag1.
The reference source remains preserved on the parent/pinned branch and as a
flag0 compiled oracle. All13 RSP banks are byte-exact between flags. The
scene-context probe banks are absent from this complete-DSP configuration. Linked
text96624/data729716/bss45064 and staticD50A8<D6000 are equal, gapF58. Full
24576 events,194 ROM slots and43 simultaneous owners remain. Six CPU queue
words/two banks/four actual D6400 backup DMA sites and three faults pass;
all9 core functions/36 product writer sites satisfy the existing HI/LO spacing
gate. Boot12/TV5 pass.

The host differential passes12288 directed V3c cases (all256 Gaussian fractions,
eight voices, env0/1/2047, NON, KON delay, PMON and reset boundaries) and8192
arbitrary1..96-clock slices, producing11601 stereo frames. All20480 comparisons
check every core-state byte after normalizing host addresses only, full64KiB
APURAM, all128 registers and complete PCM extents. Internal extra output storage
is also exercised. Env1 and noise-selection mutations reject. The first fixture
compile duplicated the header's copier helper class; distinct test-only names
fix that collision. The initial preflight expected only V3c to differ; it now
records the compiler's run-caller change too. No runtime result came from either
fixture assumption, and no semantic/ABI/owner gate was relaxed.

The optimized existing transaction still matches all6144 synthetic PCM frames,
three original checksums/nonzero counts, full RAM backup/readback/restore,
16 failed backup positions, one corrupt backup, two restore faults and five
invalid inputs. No broad CI or unrelated suite is repeated before native value.

The native discriminator freezes same-source flag0/1 and runs the existing
three synthetic complete-DSP workloads three times each while ALttP is paused600.
Count covers only core32-frame calls; setup/checksums/USB/AI are excluded.
All host PCM checksums must match, each trial must restore/readback64KiB guest
RAM, and full live image/PCM/head/register/enabled state must remain unchanged.
Real guest stepping600->660 must succeed. No synthetic PCM goes to AI or SD.
Every terminal path restores coordinate8/menu/install/readback.

Before measurement: at least15% one-voice core saving with no material (>2%)
active-worst-case regression retains this as a limited complete-core reduction.
Below5% one-voice saving rejects this direction as material. Intermediate/noisy
results are reported without an open-ended tuning campaign. All three64ms
standalone budgets remain explicit; meeting a core-only budget does not pay for
guest CPU/APU/rendering or demonstrate gameplay60. In particular, all-active
eight-voice cases need not benefit from this redundancy rule and can still block
a replacement. This does not repeat the unmodified drop-in or qualify DAC/SNES
fidelity, native60, wider corpus or integration.
