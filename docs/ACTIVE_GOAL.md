# Active goal - 2026-10-12

Sustained native emulation, visual fidelity and complete synchronized audio
together on real N64. NTSC60Hz/PAL50Hz as appropriate, one required guest frame
per intended native frame, frameskip0, full-rate SPC700/APU/DSP, audio enabled.
No omitted work, fabricated frames, per-game profiles or fidelity concessions.

## Decision and validation order

Prioritize the demonstrated material frame-budget blocker. Repair audio
immediately when it causes that blocker or invalidates measurement; otherwise
avoid an abstract audio-first priority. Once cadence is met, close remaining
visual/audio differences. Final acceptance requires all three simultaneously.

Evidence-backed hypothesis -> one controlled change -> local build and
indispensable quick integrity/ABI/known-regression gates -> short COM3 hardware
A/B -> decision -> expand fidelity/scenes if promising -> full relevant CI
before VALIDATED/integrable status. Semantic repairs retain necessary local
differential proofs before hardware. Reuse exact-SHA evidence; failed hardware
hypotheses do not earn exhaustive CI. Documentary checkpoints may skip CI.

Technical batch -> continuity checkpoint -> next batch. Use HYPOTHESIS,
IMPLEMENTED, MEASURED, VALIDATED, REJECTED, SUPERSEDED, BLOCKED, LAB LIMITATION.
Preserve hypotheses, SHAs, settings, before/after, failures, limits and next
decisions. Counts are not native cycles; CI and isolated scenes are not whole
game qualification. Existing tools should support the next decision without
growing another profiling project or emulator.

## Corpus and closure

Acceptance/diagnosis order: ALttP, DKC1, Super Metroid, combined SMAS+SMW (all
five games), Super Mario RPG, Super Mario Kart, Mortal Kombat1, Yoshi's Island,
Star Fox, Doom SNES. Use other games/test ROMs as demanding controls. Chip
implementation/functional gates are distinct from ordinary FPS gates; retain
SA-1/SuperFX/DSP-1 targets. N64 alone is primary; cart computation requires
quantified need. Cover gameplay, heavy effects, transitions, complex audio and
sustained routes; do not qualify a whole title from one easy scene.

Keep ROM/SAV/state/frame/PCM/replay/transport and commercial hashes private.
Preserve firmware, saves, configuration and earlier improvements/branches.
No destructive resets, needless force pushes or premature merges. Direct host
SD access requires power off; use the established menu-mediated COM3 loop.
Ask only for a real physical/access/irreversible-scope blocker. Continue other
useful work when one test is blocked. The continuous goal stays open until the
required native routes, complete emulation work, visual/audio behavior,
reproduced N64 evidence, regression/CI and publication/integration all qualify.

## Current evidence and priority

Master7cc8fac remains stable; phase4/usb-hardware-loop/PR21 retains the native
work and is draft. Historical homebrew Gate-B acceptance is scoped to its
corpus, not expanded to the commercial goal. R31 measured ALttP title51.86,
room57.67/rain32.28 completed boundaries/s at precision20/skip0/APU21/audio4;
these are not TV FPS or full audio qualification. R32 repairs a VR4300
contract; R33 physically repairs a GAIN accumulator owner defect.

Rain takes about31ms per completion versus16.7ms budget, with explicit mean
CPU/RSP wait11.255ms. CPU/RSP overlap and sampled DSP19.45 percent is not an
additive cost estimate. Prioritize a material renderer/source-resolution/
transfer-synchronization experiment in the reproducible rain route, retaining
the existing graphics and audio corrections. Do not repeat discarded packed/
presence/atlas hypotheses without new evidence.

R34's complete C++ DSP is REJECTED as a direct gameplay replacement: native
core fractions1.0656/1.4415/1.5116 at32000 frames/s,9 matching host checksums,
RAM/image/PCM restored. Retain it as behavior oracle; no general hardware
ceiling follows. R35 is preserved separately at
experiment/dsp-timer-r35-unmeasured,677c9d2140dd5177181f40516a1d4f832a6abda2:
IMPLEMENTED/local passes, not MEASURED or VALIDATED. Immediate priority is
SUPERSEDED: DIV count decreases, scalar count increases, no material native
benefit established. The active branch/master do not include R35.
