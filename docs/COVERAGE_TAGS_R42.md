# R42 - Coverage metadata physical feasibility

HYPOTHESIS: raster writes and Math input transfers may be reduced if RGB5551
can carry a semantic bit alongside unchanged RGB. Existing general renderer
uses separate16-bit Main winner and Sub presence depth streams. Rain still
needs27.10ms per completion; existing samples show Main submission waits and
Math residency are material. This is an architectural feasibility question,
not a promised speedup or a new profiler.

Primary references: [Nintendo programming manual, coverage/blending](https://ultra64.ca/files/documentation/nintendo/Nintendo_64_Programming_Manual_NU6-06-0030-001G_HQ.pdf)
and [libdragon RDP macros](https://github.com/DragonMinded/libdragon/blob/preview/include/rdpq_macros.h).
The framebuffer low bit represents coverage; alpha/coverage state can affect
it. Whether it can encode our flag while preserving painter RGB/transparency
is an inference requiring actual hardware evidence. No emulator verdict.

IMPLEMENTED: reuse the existing paused-only rdp-probe, add mode8; default
production builds still omit it. Original numeric RGBA16/CI8+TLUT pixels,
opaque black and transparent index0, old low bit0/1, primitive alpha63/255,
four coverage destinations,1024 pixel cases. Disable AA, Z and memory reads.
CPU reads actual retired pixels and reports RGB/tag/transparent differences.
Use already bounded immutable commands/retired winner scratch; existing
pause/ownership/DP/DMA checks and mandatory menu reboot after dirty probe.
No guest resume, ROM data inspection, new surfaces or firmware/save writes.

Local build fits D35C8 < D4000;41 owners, actual six CPU queue words/two embedded
banks/four backup sites/three negative guards and boot12/TV5 pass. The packet
stays below29 commands/256-byte staging slots, rows16..47 within retired FB.
Not MEASURED, no native speed/visual/audio claim. Next: fixture launch600,
mode8 physical readback, resume rejection, menu/coordinate8 restoration.
Only if RGB/transparency and tags all match may generic renderer design proceed;
otherwise reject this mechanism before broad CI.

Parallel R41 exact d10b79f Build38300923921/CGRAM38300930969 passed; Ares38300934335
failed, cause under inspection. No overall full-CI/integrability claim.
Master and retained renderer branches unchanged. Game data/hashes stay private.

First native probe28af46a completed safely: CLAMP/WRAP each RGB124/tag14/
transparent0 differences; ZAP/SAVE additionally cannot carry the tag. RGBA16
was the intact half; CI8 descriptor mistakenly encoded CI4 (size0). Fix the
two actual LoadTile/render descriptors to CI8(size1) before repeating. This
is an invalid fixture discriminant, not a renderer rejection. All first
receipts/artifacts retained; no game/throughput claim. Ares failure is SDL
KMSDRM source type error before Sodium64 execution, separate lab dependency.

CI8-corrected22f1860 native probe: CLAMP/WRAP tag0/transparent0 differences,
RGB124 differences remain; ZAP/SAVE tag124 fail. Presence encoding itself
is now correct, but RGB must pass too. Next controlled test enables the RGB
texture-conversion path for both fetch cycles and records first RGB mismatch
so a failed fixture can be diagnosed without accepting color loss. All probe
results/artifacts preserved, resume rejection/restoration pass. No renderer
change or native performance claim.

RGB-fetch control49b9a5d: TF1_RGB adds no benefit; same RGB124 mismatches.
First CI opaque black returnsF800, compatible with retained fixture palette.
CLAMP/WRAP tags/transparent still0. Next discriminant isolates palette loading:
use distinct immutable tile6 for TLUT plus explicit LoadSync/TileSync before
texture tile7. This tests a suspected descriptor/source ownership fixture
hazard. No stale-color result is accepted. Prior three receipts retained.

Separate tile/explicit palette retirementc4ae2e6 leaves the same RGB124/stale
F800 mismatch; ownership explanation is not confirmed. Final fixture control
uses the exact production four-copy2048-byte palette and LoadBlock descriptor
shape, instead of its unfamiliar LoadTLUT path. Expanded input/rounded read
end remains before command scratch. This is a bounded feasibility test, no
new profiling infrastructure or performance claim. If RGB still fails, stop
this fixture sequence and retain the mechanism as unqualified.
