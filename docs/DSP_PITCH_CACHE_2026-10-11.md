# R19 - Exact pitch conversion cache and native comparison (2026-10-11)

## Change and scope

The opt-in `DSP_PITCH_CACHE=1` converts raw VxPITCH bytes after either byte
is written, rather than repeating the endian conversion and 14-bit mask for
every enabled voice/sample. It caches raw pitch, independently of host clock,
APU clock and DSP sample period. The ordinary build remains byte-identical
with this flag disabled. No interpolation, envelope, BRR, mixer or AI submission
policy is changed by this candidate.

The actual linked sample conversion is3 instructions instead of7. The
register-write path is26 instead of15: saving4 per voice/sample costs11 per
pitch-byte write. Frequent pitch writes can offset the saving; these native
scene observations do not establish universal improvement.

Both byte handlers dispatch after storing the raw register byte. Invalid
0x80-0xff writes return before the raw store or cache update; mirrored reads
continue returning raw bytes. Cache and registers initialize together at ROM
launch. The current tree has one raw-register writer and no in-session DSP
state restore. A future state loader must restore or rebuild this cache.

## Validation

Executed linked tests cover131072 writes,524288 cached loads,65536 uncached
reference conversions,128 invalid writes,80 ordinary writes,2048 interleaved
updates/readbacks and16 calls through the production APU port writer. The
caller retains memory-tag updates, master-cycle debit and registers outside
its established clobber set. A high-bit-mask mutation is rejected. Tests use
only original synthetic data; scalar execution is not timing evidence.

A disabled rebuild retains CPU .text/.rodata/.data bytes from the selected
coordinate8 build. All24 RSP text/data sections are identical. The candidate
passes the41-owner event arena check, runtime arena,12 reboot cases,
5 framebuffer cases,16 AI observer cases and102 compiled recorder cases.
Its arena remains0xD2000 with0xA38 separation after allocated data.

Native comparison uses the same guest-boundary inputs, precision20,
frameskip0, APU21, audio4 and all layers. Exported raw images and PCM rings
stay private. Each compared ring has matching head, enabled voices and all
128 DSP register bytes. A match proves preservation of current PCM; it does
not prove that the existing PCM is faithful to SNES output.

Native measurements and selected/restored binary hashes are in the
[aggregate evidence](evidence/pitch-cache-2026-10-11.json). Completed-boundary
cadence is not TV presentation FPS. Quiet USB-only windows exclude SD commit;
endpoint exports and deliberate paused FIFO drain remain outside/around the
window, so AI-idle observations are not a count of proven dropped samples.

## Native outcome

Four fixed-boundary RGB images compare268800 pixels with0 differences.
Three paused PCM rings compare24576 bytes with0 differences; heads and DSP
registers match. First300 title boundaries rise53.645934 to55.009215 (+2.541%).
Room rises59.515700 to59.854494 (+0.569%). Rain rises32.185454 to32.233815
(+0.150%), too small to claim a performance win from a single window.

The candidate quiet audio production fractions are94.45% for the mixed title
window,99.54% for room and53.52% for rain. Room was99.01% in the preceding
quiet observer window. In rain every one of361 submissions observed an idle
AI queue; slow guest progress is a concrete undersupply mechanism, alongside
the unimplemented DSP features. These are queue/production observations,
not analog-output or audible-defect acceptance.

The candidate is retained as opt-in development code. The selected coordinate8
emulator was restored with readback verification and the console returned to
the paired menu. No full60-FPS or full sound-fidelity qualification follows.

## Audio root-cause audit prepared for the next change

A separate synthetic audit executes the unchanged BRR decoder in7168 cases.
The independent arithmetic oracle is cross-checked against the unmodified
`decode_brr` method from
[Snes9x1.63](https://github.com/snes9xgit/snes9x/blob/1.63/apu/bapu/dsp/SPC_DSP.cpp),
whose fetched source matches the local reference after newline normalization.
All7168 oracle cases match the compiled reference method.

Current sodium64 differs in5660 of those7168 blocks:321/1763 filter0,
1730/1760 filter1,1778/1796 filter2 and1831/1849 filter3. Differences expose
invalid ranges13-15, signed filter rounding and sample saturation/wrapping.
This audit uses synthetic values, not commercial game audio. It establishes
a decoder discrepancy; it does not identify how much of the user's perceived
compression it causes. BRR correction is still separate work. Echo, master
volume, interpolation, release, PMON and final mixing remain unqualified.

## CI and integration status

The preceding source checkpoint d4cc32f0773cfa2764eea1143409785c9ec47476
passes all three workflows: Build and Validate38167286862, Ares Profile
Validation38167289602 and CGRAM Epoch Replay38167289552.
The dedicated observer job now builds both cache-disabled reference and
cache-enabled candidate, and executes the exhaustive linked cache test.
Fresh CI for this entry must be checked at its eventual commit SHA.

Stable master remains unchanged. This entry does not qualify ALttP title,
rain, constant60 presentation or full audio fidelity, and does not qualify
the remaining game matrix.
