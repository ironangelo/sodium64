# SMW exploration: ordinary profile verified, geometry admission blocked

Runtime authority: `01a524213cc414ee67b34362b50e115804caaede`.
The exploration branch retains the shared event-arena repair and all HCOMP
work. The diagnostic branch and master stay independent. No commercial ROM
has been run or placed in the repository or CI.

## Completed admission check

The qualified normal build uses PROFILE=0, HW_PROFILE=0 and COLOR_DIAG=0.
Its ELF SHA256 is
`f4e4a08cdf77a6537731b536684b12fa3d6b2f6eaa13363d32f4fb3a86a9e5ae`.
The audit of immutable artifact11180227088 establishes:

- No diagnostic or profiling entry points in the ordinary ELF; both
  instrumented variants are rejected as ordinary builds by negative controls.
- Startup, PI SRAM load/save, VI and controller instructions are byte-identical
  to the previous qualified normal build. This is instruction preservation,
  not an executed game SRAM round trip.
- Every RSP text/data section in all three variants is unchanged, including
  the fixed renderer/HCOMP dispatch addresses.
- Existing compiled arena/cache qualification and original frozen A/B
  image comparisons still pass. The original emulator evidence is retained;
  this host-only audit does not manufacture new emulator or hardware evidence.

Reproduce using extracted qualified and previous color evidence archives:

```sh
python3 scripts/check_smw_normal_profile.py \
  --qualified /path/to/arena-evidence/qualified \
  --parent /path/to/previous-color-evidence/qualified \
  --output /path/to/smw-normal-profile-audit.json
```

Its success means **the ordinary profile was correctly audited**. The JSON
explicitly says `game_ready=false` and `geometry_admission=BLOCKED`.

## Full-height blocker

The emitted `draw_frame` selects the compact Sub image before loading the
first section. `not_blank` enables the compact Z carrier for section0 without
checking its height. The eight-line check in `hcomp_provenance_end` runs only
after the RDP work has already used those targets. Thus flags alone cannot
make a full-height first section safe.

For SETINI=0, the CPU publishes border8 + offset8 = global y16. With a
280-pixel, 16-bit stride, the conservative whole-row envelopes are:

| Surface | Owned eight rows | Hypothetical 224 rows |
| --- | --- | --- |
| Sub color | E4000..E5180 | E4000..102A00 |
| Main winner Z | E2000..E3180 | E2000..100A00 |

End addresses are exclusive. The full-height envelopes cross preserved TS,
raw palette workspaces, the consumed-section record and FRAMEBUFFER1. These
are static address calculations for a hypothetical unsplit full-height
section, **not observed SMW writes**. Other section layouts and SETINI states
also need admission; simply capping this one envelope does not earn fidelity.

## Next implementation checkpoint

Establish target ownership and geometry admission **before the first RDP
write**, including startup/force-blank and border variants, then preserve the
existing supported eight-line output and its original acceptance. A useful
SMW candidate additionally needs an owned full-height Main/Sub/output route
with per-section state; rejecting overflow alone does not supply that route.
Do not silently bypass HCOMP, render only an eight-line game image, enlarge
buffers without a simultaneous memory budget, or present raw fallback output
as an iris/color-math repair.

Keep commercial ROMs and future game saves private and separate from
diagnostic outputs. Stable master may supply a separately labeled baseline,
but it is not the candidate containing the Gate-C work. Native hue, SMW
compatibility/iris and real-N64 cadence remain open.
