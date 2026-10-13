# R48 - Complete DSP non-alias compile discriminator

REJECTED without a native trial. The existing clocked complete-DSP cost exceeds
its64ms/2048-frame budget. This question asks whether external RAM/output alias
assumptions force redundant class-state reloads in the compiled run method.

A private source copy adds only the GCC member-function `__restrict__` qualifier
to `SPC_DSP::run`; the tracked pinned reference is unchanged. The installed N64
compiler uses the exact probe -O2/vr4300/o64/section/endianness flags for both.
All18 executable sections are byte-exact:9536 total text bytes in both,3440
run bytes in both. Object metadata is not used as instruction equality proof.
No emitted work changed, so no native run, behavioral claim, full CI or runtime
patch follows. This rejects this annotation as a cost remedy, not every possible
alias-aware redesign. The original probe and oracle remain preserved.

The qualifier follows [GCC's member-function documentation](https://gcc.gnu.org/onlinedocs/gcc/Restricted-Pointers.html).
No runtime correctness relies on its proposed memory contract because no
changed executable was installed. [Numeric receipt](evidence/dsp-alias-r48-codegen.json).

Next evaluate pure interpolation work whose result is discarded: the clocked
V3c core computes Gaussian even when NON replaces it or env0 makes its signal
zero. Keep exact PMON/KON/envelope/BRR/noise/echo/register timing and all state;
compare arbitrary clock slices, registers, full RAM and PCM against the pinned
core before the existing bounded synthetic native cost probe. This is a probe
variant, not another unchanged drop-in or a gameplay/full-speed claim. Worst
eight-voice and echo/FIR costs remain independent budget gates.
