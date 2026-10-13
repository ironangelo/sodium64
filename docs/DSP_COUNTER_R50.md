# R50 - Exact counter divisibility in the complete DSP probe

IMPLEMENTED; native cost pending. DSP_COUNTER_FAST1 defaults0, requires
FULL_DSP_PROBE1 and changes the diagnostic complete core only. The preserved
R49 signal-elision flag is1 in both native A/B variants. No gameplay replacement
or master integration follows. Eight active voices still exceed the64ms core
budget, so this asks whether their recurring integer divisions are material.

The linked V3c envelope and run noise path contain two variable DIVU sites.
The private read_counter has exactly two consumers, both asking whether its
remainder is0. This opt-in implementation preserves that zero/nonzero contract
for every unsigned32 counter numerator and all32 rates, without computing a
quotient or full remainder. Period1 returns0; all other rates use an exact
modular-inverse divisibility predicate. No counter tick, rate offset, envelope,
noise transition or DSP phase is skipped or delayed.

For d=2^k*u with odd u, p=n*inverse(u) modulo2^32. Rotate p right by k and
compare it to floor((2^32-1)/d). A successful comparison forces the low k bits
of p to0 and bounds p*u below2^32, hence n=p*u is divisible by d. Conversely
if n=q*d, the rotated product is q within that bound. This also covers unsigned
wrap and shift0; both variable shifts are masked to0..31. The four odd factors
are30721/1/3/5, with four possible offsets. Their80-byte constant table encodes
group/shift/offset in one byte per rate. This is an independently derived
specialization of the integer-inverse approach discussed in the
[Granlund-Montgomery paper](https://gmplib.org/~tege/divcnst-pldi94.pdf), not a
native speed claim from that paper.

Local differential:1114496 predicate cases, including every30720-period counter
position for all32 rates, full-width numerator boundaries and131072 random
counter bit patterns.12288 V3c cases/8192 arbitrary clock slices/11601 stereo
frames/20480 complete-state comparisons preserve64KiB RAM/all128 DSP registers/
all PCM bytes after host-address normalization only. Limit and rotation faults
reject alongside the two inherited signal faults. A test-only external method
exposes the actual inline predicate; the initial fixture lacked a linkable
inline symbol, corrected without changing native code. It is absent in N64 builds.
The original6144-frame transaction/three PCM checksums/backup/restore/fault
controls also pass with both flags1.

The first384-byte per-rate table crossed the text+rodata alignment page and
failed the full-DSP arena linker assertion. It was never installed. Compact
factor/offset metadata restores the original data page without changing any
arena or capacity. Candidate text96816/data729540/bss45064; staticD50A8<D6000,
gapF58. Full24576 events/194 ROM slots/43 owners remain. Baseline allocated
bytes and executable core sections match the frozen native R49 signal1 control.
All13 RSP banks match between flags. Ten core functions/36 HI/LO writer sites,
boot12/TV5 and CPU6 words/two banks/fourD6400 DMA sites/three faults pass.
The compiled complete-core division sites fall2->0; this is not timing evidence.

Before native measurement: >=8% active-eight-voice core saving is promising;
below3% in both active scenarios rejects this as the next material direction.
Intermediate results are retained explicitly without an open-ended small-patch
campaign. Any PCM mismatch or >2% cost regression stops promotion. Use the
same frozen source, flag0/1, original three2048-frame synthetic workloads three
times each; Count covers only core32-frame calls. Mandatory host checksums,
64KiB RAM backup/readback/restore, unchanged live image/PCM/state, step600->660
and final coordinate8/menu/install/readback. No synthetic AI or SD writes.
Full active budgets, guest CPU/APU/rendering cost, DAC/SNES/game fidelity,
native60/corpus and integration remain open regardless of this discriminator.
