# R47 - Four-sample BRR register recurrence

IMPLEMENTED; native discrimination pending. `DSP_BRR_GROUP=1` defaults off
and requires `DSP_BRR_ACCURATE=1`. No change is integrated into master.

The complete native room profile contains 2889 DSP residency samples out of
7155 (40.38%). Its separate retained PC tail prominently includes BRR decode
and filter routines. This is evidence for a bounded decoder experiment, not
an exclusive BRR cost measurement. The previous R46 constant APU read change
failed its material native performance threshold and remains isolated.

The decoder dispatches the filter once per existing four-sample chunk. It
keeps the two half-scaled history samples in registers instead of recalculating
ring indices and reloading history for every sample. The same packed bytes
are read at the same guest phase, with unchanged filters, integer floors,
signed16 saturation and signed15 storage wrap. Four stores descend through
6/4/2/0; the aligned voice-buffer base is restored before the observer. Pitch,
voice scheduling, stereo accumulators, HI/LO and SPC/DSP clocking are retained.
There is no whole-block batching, skipped sample or per-game admission.

The first fully unrolled implementation crossed a linker page boundary and
exceeded the scene-slot static arena. It failed linking and was never installed.
The bounded four-sample loop adds 160 bytes of CPU text and leaves static end
D58D8 below D6000, gap728. Arena boundaries, full24576 events,194 ROM slots and
43 concurrent owners are retained. Flag0 retains all872964 allocated bytes of
native source1990fb0; all15 RSP banks are byte-exact between flags. Boot12/TV5
checks pass.

Local differential execution passes 57344 voice cases against independent BRR
arithmetic and the compiled scalar decoder. Actual decoder instructions total
8554552 to7185608; worst case190 to160. Six emitted faults reject: signed floor,
invalid-range mask, saturation, signed15 storage, history recurrence and store
extent. The existing actual DSP scheduler comparison passes2048 samples,
all256 voice masks, envelope/noise cases, all64 range/filter pairs, end/loop
flags and both AI halves, preserving672 guest cycles per sample and active PCM
state. Its instruction total is2095557 to1924069; maximum2259 to2069.

A separate BRR observer smoke passes512 voice cases, record ownership/wrapping,
the six faults, CPU queue words and actual embedded RSP backup DMA owners.
This smoke uses an instrumented candidate and an uninstrumented scalar control;
its instruction counts do not establish a performance comparison. The first
smoke erroneously applied that comparison assertion; the harness was corrected
without relaxing semantic, ABI or ownership checks. Observer-only static end
D2A88 is below its D4000 arena; this artifact is not the native A/B candidate.

The native discriminator uses same-source flags0/1 in the existing quiet
SCENE_SLOT1 bench, full-rate clock21/audio4/frameskip0, SUB_ALPHA1 and
BACKDROP_ROWS0. It replays ALttP separately for each build, without cross-build
state transfer. All pixels and paused implemented PCM/head/register/enabled
state at600/900/1980 and acknowledged input1380 must match. Quiet20-second
captures compare predeclared absolute title920..1219 and room2000..2599
intervals, with accepted boundary/checksum/settings/full-retention checks.
Every terminal path restores coordinate8/menu/install/readback.

A gain of at least5% on an uncapped fixed interval merits representative rain,
DKC and appropriate changed-DSP CI. Below2% in both scenes rejects this as the
next material performance direction. Intermediate results need one confirmation;
a capped baseline is interpreted separately. Any image or implemented PCM delta
stops the trial. These thresholds are fixed before native measurement. Full
DSP features, DAC/SNES fidelity, native60, wider corpus and integration remain
open. The rejected direct C++ full-DSP drop-in is not repeated.
