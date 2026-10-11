# R22 - Preserve the KOFF release tail (2026-10-11)

## Problem and correction

The original KOFF handler immediately removes selected active voices. This
cuts note tails instead of reducing their envelopes. `DSP_KOFF_RELEASE=1`
keeps those voices enabled while the envelope decreases by eight per generated
sample, clamped at zero. The step is independent of ADSR/GAIN rates, following
the release branch in
[Snes9x 1.63 SPC_DSP::run_envelope](https://github.com/snes9xgit/snes9x/blob/1.63/apu/bapu/dsp/SPC_DSP.cpp).

KOFF only latches the selected voice's release mode and schedules its next
sample. It does not immediately change the envelope or enabled mask. ADSR
writes cannot leave an already latched release. Existing KON state reset can
restart attack/gain. The flag defaults off and is independent of pitch/BRR
corrections. This is a bounded fidelity correction, not full DSP accuracy:
KON's five-sample delay and every-other-sample register latching remain open,
as do interpolation, echo, master volume, mixing and other envelope details.

With AUDIO_OBSERVER enabled, two diagnostic words count release steps and
record the last private voice/before/after transition. They add 12 executed
instructions per release step and are absent from ordinary production code.
Pause-only audio exports include those fields; audio-reset clears them with
the other diagnostic counters. They do not modify PCM, AI policy or guest RAM.

## Linked checks and failures caught

256 KOFF masks retain enabled/envelope/cache state while touching only the
selected mode/timer entries. 16,384 voice cases exhaust all 2,048 envelope
levels across eight voices. 2,064 calls execute the real DSP sample scheduler,
including timer wrap and progression to silence. 32 ADSR writes stay in release;
16 KON state-reset/dispatch cases can restart it. The latter stop before the
unchanged legacy rate handler, whose DIV is outside this scalar VM; they do
not qualify KON timing. Ten actual APU-port caller cases preserve its memory
tag/cycle debit, and 128 invalid register addresses do not write.

Two mutations must fail: a decrement of seven and the wrong timer-wrap period.
The preceding real handler demonstrates the immediate-disable defect.
The release handler executes at most 48 instructions without its diagnostic
words, or 60 with them. Production parsers pass 173/188 cases for release-only/
combined observers, plus 1,000 fuzz inputs each. The AI observer retains its
16 cases; recorder and reboot/framebuffer guards retain 102 and 12/5 cases.

The initial source put a symbol-based store in a branch delay slot; the
assembler correctly rejected its multi-instruction expansion. Moving the
store before the branch fixed it before any hardware install. An expanded KON
test then reached an unsupported legacy DIV in the scalar VM. Its qualification
was narrowed to the actual reset/dispatch boundary, explicitly excluding the
unchanged rate handler and KON timing; failed attempts are not evidence.

## Additional observer memory and CI failure

R21 da51d11 passes Ares Profile Validation 38172193035 and CGRAM Epoch Replay
38172193166. Build and Validate 38172187968 fails in the optional audio trace
link: `diagnostic static memory overlaps the CGRAM arena`. Ordinary, PROFILE,
native diagnostic/trace and smoke jobs pass. Local success with a different SDK
was insufficient to certify that CI configuration.

BRR_OBSERVER now selects Q1's arena at 0xD4000 in both CPU and RSP preprocessing
and uses a matching strict linker assertion. Other trace/PROFILE configurations
remain at 0xD2000; normal remains at 0xC2000. Event capacity, ROM slots, raw
palette shadows, framebuffers and upper surfaces are unchanged. This relocates
the optional owned region, rather than relaxing overlap checks.

The combined local candidate ends at 0xD25C8, below 0xD4000 by 0x1A38.
Q1 events end at 0xECE00 and remain disjoint from the consumed-section marker
and raw palettes. Ten arena regressions cover all three layouts, host/MIPS
preprocessors and the old-boundary negative. The exact combined build passes
41-owner bounds, 288 command/24 texture/24 palette/72 independent-DMA lifetime
cases and 1,792 compiled window cases with two mutations. Fresh CI at this
checkpoint must still be checked independently.

## Native qualification

The physical three-scene trial passes installation/readback, input
acknowledgements, full/checksummed captures, zero trace overflow and unchanged
settings. Four checkpoints compare 268,800 RGB pixels with zero differences.
The three 8,192-byte rings retain their heads, enabled masks and DSP registers;
PCM changes in 785/261/0 bytes for title/room/rain. Six native release endpoints
match the reference decrease/clamp. These are bounded checks, not a full
waveform comparison.

Title first-300 cadence is 54.319590 versus R20's 54.857498; room is 59.846049
versus 59.795169; rain is 32.461939 versus 32.294840. All single-window deltas
are below one percent; no speed win or zero-cost claim follows. Quiet audio
production is 94.80%, 99.57% and 53.92% of nominal AI respectively. Rain still
observes idle on every one of its 363 submissions. Its slow guest progress and
renderer wait remain separate from this note-tail correction.

[Curated evidence](evidence/koff-release-2026-10-11.json) contains the counts,
code identities, arithmetic guards and timing limits. The scene candidate has
BRR_OBSERVER=0. Its timing still includes the existing AI observer and the
disclosed 12 release-diagnostic instructions per step; AUDIO_OBSERVER=0
production timing is not measured here. The separately linked production
handler passes the same release checks with a maximum of 48 instructions.
Changed PCM is expected when preserving note tails; differences are not a
waveform quality score. Matching retired RGB frames does not qualify the
complete VI/HDMI/TV signal, and paused DSP rings do not certify DAC output.

Raw commercial inputs, images, PCM, DSP/transition records, captures and
transport/replay logs remain private. Only original source/tests, code identities
and curated numeric aggregates publish. Master stays unchanged; there is no
whole-audio, constant-60, game-matrix or Road 1.0 acceptance.

Coordinate8 was restored with verified readback and the paired menu responded
after the scene trial. A subsequent combined trace/relocated-arena trial was
installed with readback and reached an acknowledged pause at 600. During the
step toward 1380, emulator USB stopped responding; last acknowledged progress
was 790, with no reported transport/menu error. Both a status write and the
attempted return/restoration failed with `Debug data write dropped due to timeout`.
Firmware info still responded through COM3. The cause is unresolved: this is
not physical acceptance of the relocated observer or a proven arena root cause.

At this interruption, the last installed empty template is the combined
experimental observer, SHA256
b28f6a602a1ee9632478c04c73196658fb9d497cba467369e3add3f3774cd6c1,
ELF c2e1df941ac3ff38b8a243b149996db6f62a153d3e49a4bfad7298a1b7821a30.
Recovery to the menu and restoration of coordinate8 require a responsive
emulator or a physical Reset/power cycle. The user was asked for that action;
successful restoration after this second trial must not be claimed yet.
