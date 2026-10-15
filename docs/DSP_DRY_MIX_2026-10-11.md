# R29 - Signed dry mixing and physical arithmetic proof (2026-10-11)

## Correction and remaining DSP scope

DSP_DRY_MIX=1 reconstructs the full selected signal from Sodium's half-scaled
BRR/noise storage. It uses the full eleven-bit envelope, clears output bit0,
applies signed voice volumes, saturates after each voice in order, then applies
signed master volumes and FLG mute. The previous path truncated the envelope
before multiplying cached coefficients, retained half-scale output, ignored
master volumes/mute and wrapped accumulated channels instead of saturating.

The arithmetic follows the envelope/voice_output and zero-echo master path in
[Snes9x1.63 SPC_DSP](https://github.com/snes9xgit/snes9x/blob/1.63/apu/bapu/dsp/SPC_DSP.cpp).
This corrects the dry stage given its selected samples/envelopes. Gaussian
interpolation, echo/FIR and its RAM feedback, pitch modulation, ENVX/OUTX/ENDX
feedback, envelope/KON/register timing and sample-clock scheduling remain open.
No full waveform/DAC or whole-SNES sound acceptance follows. The flag defaults0;
the existing cache updates remain, so redundant cache work is a later cost
candidate rather than an unmeasured performance claim in this checkpoint.

## Actual linked and native checks

16384 voice cases exhaust all2048 envelope levels over eight voice positions.
32768 signed-master/mute cases include boundary accumulators;128 calls execute
the actual sample scheduler, voice selection/load, stereo packing and buffer
advance. Seven mutations are rejected: envelope scale, even output, signed
voice coefficient, saturation, signed master coefficient, master scale and
mute. Arithmetic alone writes no state and preserves unrelated registers.
The production maxima are36 voice/21 output/641 full eight-voice sample
instructions in the tested cases. These are instruction counts, not cycle/FPS
measurements. A separate primary-method adapter executes unmodified compiled
voice_output/echo_output bodies and the envelope expression:16384 synthetic
eight-voice mixes/32768 values match the independent arithmetic oracle exactly.
Its echo inputs are explicitly zero.

MIX_OBSERVER=1 requires AUDIO_OBSERVER=1 and DSP_DRY_MIX=1. It records the
selected inputs and final PCM word at each1024th sample. Inactive/skipped-zero
voice records are cleared; eight records contain signal/env/signed channel
coefficients. The80-byte payload adds master/mute, output, ring offset and
enabled mask. Ready is committed last. Count wraps at2^32. The pause-only
audio-mix command refuses unavailable/partial/busy/invalid states, exports
read-only data and audio-reset clears count/ready.193/208 production-parser
cases for release+mix/all observers, plus1000 fuzz each pass.84 linked hook
cases preserve other registers/HI/LO/CP0 and restrict writes to owned bytes.
The eight-voice hook overhead is58 ordinary or193 selected instructions,
not just a once-per-block cost; observed timings must disclose it.

On the actual N64, the observed candidate installs/readbacks and follows the
same600/1380/1980 replay.67200 retired RGB pixels are unchanged. The room's
8192-byte PCM ring changes in7011 bytes, retaining its head/registers/enabled
state. That difference is not a quality score. The actual final eight-voice
sample captured by audio-mix matches the unmodified compiled primary methods
in both stereo values, and its packed word matches the corresponding native
PCM ring word. This is a conditional physical dry-mix proof for one sample,
not a continuous waveform or DAC comparison.

Return-to-menu and coordinate8 restoration/readback pass. The observed empty
archive SHA2569ad542d80828422b648294bca332e90895e1e6d06ae1f7723d826c39ebee9982;
ELF4e79a061f92cd4632f5cf77b84e63cfc3c60a7e6920fb7965e4fcf761fb624e8.
The separate production dry ELF is
d9f47db97b53829b9e44e32d65e47c5f932ec95042db39f2785608b2c2831bed.

## Memory, regression boundaries and failures

The first mixer-observer link correctly rejects static overlap atD2000 before
installation. Mixer and BRR observers now share the checked D4000 layout in
CPU/RSP and the strict linker guard; normal/other traces remain unchanged.
Both base flag assignments precede every feature append, preventing the R22
reset bug from recurring for the new macro. Actual embedded-bank/DMA ownership
passes all fourD4400 call sites and three negative mutations. Twelve arena
regressions cover host/MIPS and both observer selections;41 simultaneous
owners, runtime endD25C8/gap1A38, reboot12/framebuffer5, recorder102 and compiled
DMA/windows pass. The combined BRR+mix build also passes arithmetic/hooks and
release16384 cases/two mutations. Its fresh CI configuration exercises the
new flags and gates; a fresh GitHub result is still pending.

An initial patch's wrong linker-line terminator was rejected atomically before
changes. A host-preprocessor test lacked the compiler PATH and was rerun with
the intended GCC; all12 cases pass. These setup failures are not native hangs.
With both new flags0, a fresh build matches all855212 allocated coordinate8
bytes exactly. Default production receives no new DSP/observer behavior.

[Curated evidence](evidence/dry-mix-2026-10-11.json) publishes original code,
synthetic counts, identities and bounded native aggregates. Commercial inputs,
frames, PCM/voice records and hashes, replay and transport stay private. The
new scanner menu remains installed; coordinate8 is selected. Master is unchanged
and PR21 draft. Next, measure observer-free dry mixing in the three ALttP
scenes, then offset redundant work and implement the remaining DSP functions.
The active constant60/visual/audio/game-matrix goal remains unachieved.
