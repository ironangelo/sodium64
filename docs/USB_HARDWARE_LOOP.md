# Native USB checkpoint build and qualification

This is the retained development configuration as of 2026-10-11, not Road 1.0
or a universally qualified release. Start from the code branch linked in
`docs/CONTINUITY.md` on the `continuity` branch. The repository's principal
branch is `master`; there is no `main` branch to rename.

## Reproduce the selected emulator

Use an installed N64 MIPS toolchain and fresh build directories. Do not reuse
objects across feature combinations. Underscores in BUILD_DIR are intentional:
the embedded RSP symbol names are derived from this path.

```sh
make -j4 BUILD_DIR=build_usb_tmem_coord8 PROJ_NAME=sodium64-tmem-coord8 \
  NATIVE_DIAG=1 NATIVE_DIAG_TRACE=1 REMOTE=1 SIGNAL_PROFILE=1 \
  WIDE_MATH=1 ELIGIBILITY_TAGS=1 MASK_SCAN=1 TLUT_SHADER=1 \
  FULL_ROW_MATH=1 RDP_HALF_MATH=1 FIXED_WINDOW_MATH=1 RDP_FIXED_MATH=1 \
  SECTION_OBSERVER=1 TMEM_ATLAS=1 TMEM_ATLAS_BITS=3 TMEM_COORD_ATLAS=1
```

Leave TLUT_FLAT_WINDOW, FETCH_SIGNAL and RDP_MATH_PROBE off. The selected
coordinate atlas is different from the rejected atlas with per-hit tile changes.
Visible Sub retains the original single-texture protocol. Most research flags
default to zero; `make` alone is not the selected hardware configuration.
SPARSE_VRAM is controlled by its source macro, enabled in the retained source.
Preserve precision=20, frameskip=0, APU=21, audio=4 and unrestricted layers for
the recorded comparisons. Do not silently reduce accuracy or disable audio.

Installed empty-emulator reference: 131072 bytes, SHA256
`a58d70518ae44b4998764f2866b8eb1997d40d173056f43bb224696d0d5c25e2`,
CRC32 `2d5daff8`; CPU ELF SHA256
`463df084e71b9525bbbd183018fcc2283e53acfc7bb1a2d92e250ac0212e9efa`.
These identify the archived native build, not a promise that another compiler
or build timestamp produces identical packaging. The subsequent PROFILE-only
arena correction does not alter this NATIVE_DIAG configuration.

## Paired menu

See `tools/sc64-diagnostic-save/usb-menu/README.md`. Preserve both pins:
N64FlashcartMenu `e28c26e1aeae3c18851fc24118080e23e5a86a9f`,
libdragon `55aac1355773169d87e45424b772faf0dfb9432a`.
FatFs headers, linked library and every object using FIL/FATFS must agree.
Use matching mkdfs, n64sym and asset converters; mixing SDK generations already
caused a boot assertion. A source checkout/host PASS does not prove a complete
paired-menu ROM was packaged correctly.

Installed menu reference: 1736704 bytes, SHA256
`803a716bb51ebef672c43a80671776fcae4a0330d5348aeeda8954666113a144`,
CRC32 `fddd021a`. Firmware 2.20.2 was not changed.

## Optional native audio production observer

The AUDIO_OBSERVER=1 configuration and physical outcomes are documented in
[the dated audio checkpoint](AUDIO_OBSERVER_2026-10-11.md). Keep SECTION_OBSERVER=0
for that measurement. It is not a sound algorithm correction. `audio` and
`audio-reset` require a retired pause; PCM/register exports remain private.
The final hardware session restored coordinate8 with verified readback and
a responsive menu.

## Checks and evidence gates

The source includes compiled MIPS/RSP guards for arithmetic, policy eligibility,
DMA owners, delayed fences, palette restoration, cache invalidation and
coordinates. Mutation tests reject missing fences/restores and stale groups.
Use the CLI help of each guard for its ELF/baseline arguments; baseline bank
images must come from the exact earlier feature combination, not any old build.

Key entry points:
- `scripts/check_remote_boot.py`, `test_remote_control.py`,
  `test_remote_sections.py`, `test_continuous_save_sink.py`,
  `test_native_diag_continuous.py`;
- `test_rsp_sparse_vram.py`, `test_rsp_signal_profile.py`,
  `test_rsp_math_dma.py`, `test_hcomp_eligibility_tags.py`,
  `test_rsp_math_masks.py`, `test_hcomp_tlut_candidate.py`,
  `test_rsp_math_fullrow.py`, `test_rsp_rdp_half.py`,
  `test_rsp_fixed_window.py`, `test_rsp_rdp_fixed.py`,
  `test_rsp_tmem_atlas.py`;
- `check_runtime_arena.py`, `check_event_arena.py` (use `--profile`
  for PROFILE layout), `check_rsp_branch_delay_slots.py`;
- `tools/sc64-diagnostic-save/test_save.py`,
  `tools/sc64-bench/test_bench.py` and the paired menu tests.

Prior local validation is recorded in the historical ledger. This synchronization
does not rerun every suite or qualify the new GitHub commit. Existing CI gates
remain intact. Ordinary builds, PROFILE builds and armed/native builds each
need their own checks; the selected flagged path is not covered by an unflagged
CI build alone. Do not merge the whole runtime into master merely because a
documentation or host-only check passed.

A physical trial needs: verified installation/readback; exact acknowledged
input/frame replay; quiet capture with no repeated USB queries/exports during
the timing interval; valid complete S64D with checksums, settings and no trace
overflow; like-for-like retired RGB comparison; and scene-specific timing.
Keep incomplete captures and failed reservations distinct from completed data.
All ROMs, SAVs, screenshots, replay logs and raw game-derived dumps stay private.

Completed-boundary cadence measures retired renderer work over full intervals.
It is not TV presentation FPS. Frame exports precede VI, cable, HDMI adapter
and TV processing; sampled PC/bank residency is not exclusive function time.
Full visual/audio output and sustained 60 for every scene remain unqualified.

`DSP_PITCH_CACHE=1` is an optional CPU candidate. Its raw pitch cache updates
on both VxPITCH byte writes, retaining the current PCM exactly in the tested
scenes. It defaults off and has additional cost for frequent pitch writes.
[Linked proof and native evidence](DSP_PITCH_CACHE_2026-10-11.md) record its
bounded improvements and remaining audio/renderer work.

`DSP_BRR_ACCURATE=1` independently enables the integer BRR fidelity candidate.
It fixes invalid ranges, signed filter rounding and sample saturation/storage.
[Decoder and native proof](DSP_BRR_ACCURACY_2026-10-11.md) distinguish matching
isolated arithmetic from unqualified full PCM/DAC fidelity. It defaults off;
native image checks preserve rendering and timing still requires qualification.

`BRR_OBSERVER=1` requires `AUDIO_OBSERVER=1` and defaults off. The pause-only
`audio-brr` command exports the last 32 complete decoder input/output records
for private reference checking. Each record is 16 bytes; the completion count
wraps at 2^32. The hooks add 40 scalar instructions per decoded chunk. Use
observer-free code for production timing comparisons. The
[native chunk proof](NATIVE_BRR_TRACE_2026-10-11.md) records physical agreement
without claiming complete SNES audio or DAC fidelity.

The current BRR_OBSERVER configuration relocates Q1's arena to 0xD4000 for
additional static diagnostic storage; both CPU and RSP use that definition.
Its strict runtime/event checks require `--diagnostic-trace --brr-observer`.
Other diagnostic/PROFILE layouts remain at 0xD2000. R21's physical decoder
proof used its earlier 0xD2000 layout; the later observer relocation has a
separate qualification boundary.

`DSP_KOFF_RELEASE=1` preserves note tails with an eight-unit envelope decrease
per generated sample. It defaults off. The
[release checkpoint](DSP_KOFF_RELEASE_2026-10-11.md) separates its arithmetic/
caller proofs from open register-latching, complete mixing and DAC accuracy.
With AUDIO_OBSERVER=1, private audio metadata also exports a release-step count
and last transition; the additional 12 instructions per release step must be
disclosed in timing comparisons.

After the R22 combined observer timeout, physical Reset recovered the menu.
R23 confirms coordinate8 installation/readback and responsive menu mode.
Use that known version for recovery; the combined observer remains unqualified.

## Current native menu and dry-mix diagnostic checkpoint

The installed scanner menu is1736704B, SHA256
1e5fd76febfe2405fbea0f855dad63514960502631af1a1cd081d1f907c2c6f5.
Its prior SD object is retained under a unique previous name. R28 verifies
warm boot, faster same-ROM launch and two USB-triggered SD captures.

DSP_DRY_MIX=1 selects the corrected dry arithmetic; it defaults0.
MIX_OBSERVER=1 additionally requires that flag and AUDIO_OBSERVER=1, uses
CPU/RSP arenaD4000 and enables pause-only audio-mix export. Use runtime/event
gates with --diagnostic-trace --mix-observer and the actual embedded DMA guard.
[Current proof/limits](DSP_DRY_MIX_2026-10-11.md) disclose per-sample hook cost.
Production timing must disable MIX_OBSERVER and BRR_OBSERVER. Coordinate8
is restored after the bounded diagnostic, not an accepted full-audio release.
# Capture boundary metadata for paired native traces

The capture ACK includes `accepted_guest_frame_id`, `accepted_render_frame_id`
and `arm_boundary=parked_retired_bridge`. The bridge keeps that boundary parked
through the successful ACK and recorder arming, before the next guest work.
The reply remains `outcome=pending`; only a sealed, checksummed capture proves
completion. Failed ACK does not arm. Existing pause/busy/sink guards remain.

S64D `completed_boundary_ordinal` is relative to that arming boundary. With
frameskip0 and equal guest/render progress, its absolute completed guest ID is
the ACK guest ID plus that ordinal (uint32 wrap). Compare shared absolute IDs,
retaining the initial partial interval exclusion and each record's full timing.
Earlier ACKs without these fields support only route-relative alignment.
This adds no running-frame profiler or machine-state serialization.

