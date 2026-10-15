# Stage 2 native color diagnostic

This pair diagnoses the difference between correct completed yellow pixels
and green physical output. It is not a proven hue fix, a Stage 2 acceptance,
or a baseline performance benchmark.

Build with `libdragon make COLOR_DIAG=1`; this implies HW_PROFILE and PROFILE.
The original visual/mixed guests, row repair, settings and all RSP binaries
are retained. Normal and HW_PROFILE-only CPU sections must match the qualified
row-repair parent exactly.

## On-screen procedure

1. Original animation runs with VI_CONTROL0x0202 (pixel advance0). Original
   yellow/black band remains at rows8..15.
2. Six reference swatches occupy rows200..215, columns12..251: composed yellow,
   green, red, blue, white, black. They are direct uncached CPU writes to the
   finished, unpublished frame at menu entry. One white block at the right.
3. After two warmup and five measured VI windows, naturally drain, preserve
   original S64V band/provenance/PCM and freeze the same displayed buffer
   for2seconds at0x0202. Motion stops, one white block.
4. Change only pixel advance to3 (CTRL0x3202); same source/band/references,
   another2seconds, two white blocks. No guest, SP or RDP work resumes.
5. Write versioned trace/header through PI, then original finalred screen.

Record the whole live/frozenA/frozenB transition if possible. Wait finalred
and preserve saves under separate filenames. Visual is silent; mixed uses
the original8sustained tones, not music. Frozen holds no longer feed audio.
On a failed natural drain, skip the comparison and retain invalid status;
the decoder must never call that a successful comparison.

## Save layout

32KB cart SRAM, all words big-endian (32bit-swapped files are normalized):

| Range | Content |
|---|---|
| 0..0xFF | S64C version1, validity/counts/holds/reference samples/budgets |
| 0x100..0x3CFF | Up to320 consecutive48byte VI records |
| 0x3D00..0x41FF | Reserved zero |
| 0x4200..0x7F0F | Unchanged S64V version1 final pixels/provenance/PCM |
| 0x7F10..0x7FFF | Reserved zero |

S64C deliberately replaces the statistical-PC S64H/S64P cart payload.
Use `scripts/decode_stage2_color.py`, not the old hardware-profile decoder.
There is no fabricated PC profile. CP0 sampler still schedules the existing
window finalization; cadence is instrumented and must be reported as such.

Each VI during the measured window is logged, including unchanged source:
VI index, CP0 Count, physical origin, owning producer sequence, consumed
WH0/WH1 plus explicit ownership error bits, SP_STATUS, DP_STATUS, DP_CURRENT,
DP_END, upper outside/inside pixels, lower old-stripe sample and direct
yellow reference, DSP pointer, enabled voices and ready depth. Producer
metadata derives from the consumed output-section record0xA00F0000, never
current WRAM phase. Record overflow is counted; no silent wrap or truncation.
Only reserved k0/k1 are touched before measurement; during recording all
additional clobbered GPRs are restored at full64bit width. HI/LO untouched.

Separate frozen captures boot independently atA andB; they never rely on
resuming from the first diagnostic breakpoint. Same-state large and1KBcart
reads are retained to classify debugger readback, not to repair save bytes.

Header fields (byte offsets):0magic,4version,8size,12complete,16capacity,
20stride,24attempted,28stored,32dropped,36traceoffset,40probeoffset,
44probesize,48/52actualCTRLA/B,56/60Astart/end,64/68Bstart/end,
72/76independentlyreadA/Borigin,80/92sixrawreference halfwordsA/B,
104/108rawupperoutsidepixelA/B,112maxhookbodyticks,
116totalhookbodyticks,120producercount,128fivebudget words,148settings,
152finalSP,156finalDP,160S64Vvalid,164phasecompletion,
168unknownownerevents,172invalidoriginevents. Remaining fields reserved.

## Evidence and limits

Host decoder validates format/counts/byteorder/completion and retains memory
color failures as diagnostic results. Lab qualifier requires yellow/black,
known references, original audio and forward producer motion, zero drops,
all300VI events within boundary margin, and unchanged original settings.
Qualification boots continuously to actual PI writes with a single final
stop. Separate A/B semantic captures check the complete original red region
except the explicitly reserved swatch rows and compare unchanged band/colors.

Sparse live samples cannot exclude every transient stripe elsewhere.
Hook-body timing excludes GPR save/restore and producer paint overhead.
Every-frame images or checksums are intentionally avoided.
Emulator scanout does not model pixel advance as physical N64 does; emulator
yellow and reference readbacks do not certify visible native hue.
Native A/B video is needed before calling0x3202 a fix. RDP command-source
lifetime and event arena pressure remain independent unresolved hazards.
