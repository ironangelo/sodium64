# SMW exploration: shared full-height admission qualified

The working branches `phase4/gate-c-smw-exploration` and
`phase4/gate-c-stage2-color-diag` carry the same shared renderer repair.
The event-arena repair, HCOMP and the latest Gate C diagnostics remain included.
No commercial ROM has been run or committed to the repository or CI.

## Qualification authority

Executed source: `c2e3b3583142cb032d7e1555bca5328b8749884f`.
Runtime source last changed at `279f4f0f9b067a877f7e984d9ee8f81d2ddfaf94`.
Subsequent changes corrected synthetic guest setup and host capture/readout;
the final documentation commit preserves the qualified runtime files and
executed qualification scripts.

- [Dedicated Gate C run 36942594882](https://github.com/ironangelo/sodium64/actions/runs/36942594882).
- [Normal, PROFILE and Mupen64Plus LLE smoke run 36942594783](https://github.com/ironangelo/sodium64/actions/runs/36942594783).
- Qualification artifact: [11201360945](https://github.com/ironangelo/sodium64/actions/runs/36942594882/artifacts/11201360945).
- Artifact ZIP SHA256: `882256343a691b65e5a4f08dec2969f33857bd0ceb7a30eb7e7abc0ddaddbd9a`.
- Ordinary ELF SHA256: `2c73414b925817003906d897997d1cbfc881a5f6a937140452d014d209ff124f`.

The ordinary build has PROFILE=0, HW_PROFILE=0 and COLOR_DIAG=0. Compiled
checks verify that diagnostic hooks are absent, arena/cache owners remain
within the existing 4 MiB budget and fixed RSP dispatch/DMA interfaces survive.

## Shared repair

Geometry is admitted before the first RDP write. Real guest sections are
processed in owned bands of at most eight rows while retaining their section
state and Main/Sub controls. Short sections and force-blank use this same path.
Phase and math overlays each occupy the existing 1,000-byte renderer slot;
resident Main/Mode7 images remain 4,096 bytes. No enlarged framebuffer, compact
scratch surface, IMEM or Expansion Pak is required.

The taken branch delay slot preserves the real section end. Winner eligibility
decodes the actual nonlinear RDP Z representation, including BG4 and eligible
OBJ palettes. Main/Sub windows and OBJ palette eligibility feed ordinary HCOMP.

## Executed acceptance

All thirteen original synthetic guests pass in the ordinary profile. Each
accepted image checks all 57,344 pixels of the 256 × 224 game area: add/subtract,
half math, BG1–4 eligibility, overlapping windows, short HDMA sections,
force-blank, eligible/ineligible OBJ palettes and SRAM.

Acceptance requires exact delivered epoch controls, a natural RSP halt with
drained RDP commands and six unchanged compact-target guards. No framebuffer
seeding or guest-state debugger writes provide acceptance. The SRAM guest
imports an existing cartridge marker through ordinary startup load, echoes it,
writes its own marker and completes ordinary PI save. All 32 KiB are compared,
including the unchanged tail.

The original visual/mixed guests are byte-identical to their immutable parent.
Their uninterrupted 300-VI traces and separate frozen A/B images pass, along
with actual ROM paging and high palette pressure. Interrupted snapshots are
observations, not acceptance or performance authority.

Reproduce from the extracted complete qualification artifact:

```sh
python3 scripts/check_smw_probe_admission.py \
  --qualified /path/to/evidence/qualified \
  --captures /path/to/evidence/captures \
  --output /path/to/smw-probe-admission.json
```

The resulting `smw-probe-admission.json` reports
`smw_private_probe_ready=true`: shared geometry/color/SRAM prerequisites pass
synthetic acceptance and private SMW exploration can begin.

## Private game probe and remaining limits

The next input is the user's private SMW ROM. Keep the ROM and game saves out
of repository/CI assets. Wrap it with the qualified ordinary template and
retain instrumented variants for the established diagnostic probes.

SMW boot, gameplay and iris/color-math fidelity still require that game probe.
Inherited brightness ordering, per-section RDP palette replay, Mode0 palette
banking and remaining Mode7 fidelity are not closed by these fixtures.
Native hue and real-N64 cadence/performance remain open.

## Historical audit

`scripts/check_smw_normal_profile.py` is the immutable `01a5242` /
artifact `11180227088` audit. Its compact-geometry BLOCKED finding describes
that earlier renderer and is retained for reproduction. Use
`scripts/check_smw_probe_admission.py` with the new evidence for current admission.
