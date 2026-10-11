# R20 - Faithful integer BRR decoding (2026-10-11)

## Concrete problem and correction

Current BRR decoding differs from the pinned reference in5660 of7168 synthetic
blocks. Signed filter rounding subtracts a rounded positive product instead
of adding a rounded negative product. Invalid ranges13-15 use ordinary shifts,
and intermediate saturation/15-bit sample storage is missing.

`DSP_BRR_ACCURATE=1` corrects those three operations. Invalid input ranges
are handled once per four-sample chunk by selecting sign nibbles and range9.
Negative filter terms use arithmetic floor. The intermediate clamps to signed16;
the stored half-scaled sample then reproduces the signed16 doubling/wrap of the
reference by sign-extending15 bits. Existing mixing remains separate.

The flag defaults0 and is independent of pitch caching. Its disabled CPU
text/rodata/data is identical to the R19 pitch candidate. All24 RSP sections
remain identical. The correction adds CPU work; it is a fidelity change whose
native cost must be measured, not described as a speed optimization.

## Independent verification

The arithmetic oracle follows
[Snes9x1.63 SPC_DSP decode_brr](https://github.com/snes9xgit/snes9x/blob/1.63/apu/bapu/dsp/SPC_DSP.cpp).
Fetched source SHA256:
67d3fb722458227cf27d9cfcc8eee054b36dcaa2fa6484c64d46618540aac155.
The local source matches after newline normalization. A private adapter compiles
the unmodified primary method; its7168 outputs agree with the independent
Python oracle. The ordinary public test does not download or execute that
external method.

The Windows reference executable initially failed to load its MinGW DLLs.
Adding the existing mingw64/bin directory to the host PATH fixed the launch
before cross-checking; that failed launch provided no decoder evidence.

Linked execution checks57344 cases across eight voices, all ranges/filters,
signed nibbles, extreme history states and deterministic random blocks.
Four mutations must fail: signed rounding, invalid-range mask, saturation
and15-bit storage. The same test rejects the preceding decoder in the expected
5660 blocks. Only the current voice's address and8 sample bytes may be written;
unrelated GPRs, HI/LO and CP0 survive. No commercial audio is used.

The candidate also passes the linked pitch cache proof,16 AI-observer cases,
12 reboot/5 framebuffer cases,102 recorder cases and41-owner arena bounds.
Allocated-end0xD15C8 remains below arena0xD2000 by0xA38.
These are compiled/source checks, not physical audio acceptance.

## Native verification and limits

[Numeric evidence](evidence/brr-accuracy-2026-10-11.json) records actual native
timing and fixed-boundary RGB/PCM observations. Raw images, audio, captures
and transport/input replays remain private. Precision20,frameskip0,APU21,
audio4 and all layers remain unchanged.

This correction preserves the renderer and guest input recipe. Changed PCM
is expected; matching the old waveform would retain the known decoder error.
Native ring exports prove execution/output changes, while the compiled oracle
proves the isolated decoder arithmetic. They do not jointly prove the whole
SNES waveform or final DAC output.

Echo, Gaussian interpolation, master volumes, release, pitch modulation,
envelope/mixing accuracy and clock/AI scheduling still need qualification.
Rain's low guest progress remains an independent audio-undersupply problem.
A later opt-in BRR input/output trace can compare actual physical decoder
chunks against the independent oracle, avoiding reliance on a scalar VM for
that last step. Constant60 presentation and the whole game matrix remain open.

## Native outcome

Four image checkpoints compare268800 pixels with0 differences. All three
PCM ring heads, enabled-voice sets and DSP registers match the preceding
recipe. PCM changes in15579 of24576 bytes, confirming that the corrected
path executes and changes output; byte difference is not a quality score.

Title first300 boundaries measure54.857498 versus R19's55.009215; room
59.795169 versus59.854494; rain32.294840 versus32.233815. Differences below
one percent in a single window are not described as speed wins or proof of
zero cost. Quiet AI production is94.44%,99.45%,53.62% respectively. Rain
still observes idle on all361 submissions. Fidelity work does not remove
that guest-progress bottleneck.

The opt-in correction is retained for development. Coordinate8 is restored
with verified readback and the console is back in the responsive paired menu.
No whole-audio acceptance, release or constant60-FPS claim follows.

## CI and selected state

Preceding source84531758f4c70d7958d5267b740d4517f4a4c4f3 passes all three
workflows: Build and Validate38169210203, Ares Profile Validation38169213868,
CGRAM Epoch Replay38169213848. The observer job now enables this correction
and executes the linked BRR proof against its separately built legacy reference.
Fresh CI for the eventual R20 commit must be checked independently.

Master remains the stable reference; no merge or Road1.0 qualification follows.
