# R24 - Relocated BRR observer isolation (2026-10-11)

## Distinct native trial

After R23 verified manual recovery, this trial keeps BRR_OBSERVER=1 and the
new Q1 arena0xD4000, with DSP_KOFF_RELEASE=0. Other renderer, pitch and BRR
arithmetic flags match the preceding candidate. The unchanged code revision
is1b12398077ad804874af42fcdc6be34be2793794; later documentation does not
change its instructions. It additionally leaves USB quiet20s after step780,
so the result does not isolate KOFF alone from USB polling cadence.

Linked decoder57344 voice cases and four negative mutations pass, preserving
unrelated registers and writing only voice/trace owners. Static end0xD15C8
is below0xD4000 by0x2A38. All41 simultaneous owners remain disjoint; linked
reboot12/framebuffer5 and delayed-RDP command288/texture24/palette24/DMA72
cases pass. These are compiled guards, separately from the physical result.

The actual N64 installs/readbacks the empty template, launches the selected
ALttP ROM through its ordinary menu path, reaches acknowledged600/1380/1980
retired boundaries and accepts START at1380. The room compares67200 RGB
pixels and8192 PCM bytes with the earlier R20 room: zero differences, with
identical ring head, DSP registers and enabled mask. All32 native BRR records
(128 half-scaled samples) match the unmodified compiled Snes9x1.63 decoder.
Seven voices, filter2, ranges5/6/7 are observed. No full DAC/waveform or speed
qualification follows from this paused checkpoint.

Return-to-menu, coordinate8 installation/readback and subsequent menu status
all pass without physical Reset. Empty template identity:
780186a1508f5bc814c8102f1f1cb41abef0ebf4c9bbb745786454c6b816159f;
ELF f25e0460a66500fd6ec2d86e1e7ba958a5aad735c3b97c0714974888975c1b77.

The combined R22 failure remains unresolved. This result demonstrates a
responsive relocated observer in this run; it does not establish KOFF or
polling as the cause. Next, test the exact combined archive with the same
quiet interval and compare with R22 release-only room PCM.

## Exact CI and evidence limits

Exact1b12398 Build and Validate38174698283 passes all required jobs, including
usb-audio-observer-build, whose predecessor failed its strict arena assertion.
CGRAM38174701186 passes. Ares38174701176 was cancelled after a later branch
push and is not PASS. Later exact commits need their own workflow results.
Master remains unchanged; PR21 stays draft/unmerged.

[Curated evidence](evidence/brr-observer-isolation-2026-10-11.json) contains only
code identities and numeric counts. All commercial images, PCM, register and
chunk contents/hashes, ROM paths and transport/replay logs stay private. Full
visual/audio output, all requested games and constant60 remain unqualified.

## R25 correction to the layout qualification

Actual binary inspection now finds CPU arena0xD4000 but both RSP backups still
at0xD2400, because Make discarded the observer macro. R24 static end0xD15C8
is below that old backup, so its successful native comparisons are valid but
do not qualify a unified layout. The earlier41-owner check was source-selected
and missed this compiled writer. [R25](BRR_ARENA_BUILD_FIX_2026-10-11.md) adds
an actual binary regression and the corrected build; physical trial is pending.
