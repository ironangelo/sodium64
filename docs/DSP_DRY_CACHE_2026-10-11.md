# R30 - Dry-mix cost and obsolete cache removal (2026-10-11)

## Measured cost of the fidelity correction

The R29 production dry candidate disables both sample observers while keeping
existing AI-block and release counters. Same acknowledged replay/settings and
quiet20-second windows preserve four268800 RGB pixels and valid full traces.
Its title first300 cadence falls54.319590 ->48.854496 (-10.061 percent), room
59.846049 ->54.202852 (-9.430 percent), rain32.461939 ->32.220722 (-0.743 percent).
These are single-window retired-boundary measurements, not TV FPS. Audio
production fractions are90.99/90.21/53.49 percent of nominal AI, with residual
endpoint overhead. Correct arithmetic/changed PCM does not meet the combined
fidelity-and60 target. Coordinate8 was restored after the measurement.

## Exact redundant work removed

The dry mixer reads full envelopes and signed VOLL/R directly, so its old
quantized product cache has no consumer. With DSP_DRY_MIX=1, update_vols now
returns without two multiplications or cache stores; all envelope/rate/mode,
register, BRR, input and guest-cycle behavior remain. With the flag0, the
legacy cache implementation is retained. The release handler's observed maximum
falls60 ->39 linked instructions. This is a work reduction, not an assumed
native speed gain.

The updated release proof explicitly checks unused cache preservation and its
smaller write owner rather than dropping those checks.16384 envelope/voice
cases,2064 real scheduler calls, real APU caller/tag/cycle guards and two
mutations pass.4096 actual VOLL/R dispatcher writes modify only the selected
register;128 full dry-sample cases seed garbage cache words and preserve them.
A paired linked regression executes2048 actual scheduler samples and2048
paired APU volume writes against R29, with identical PCM and active DSP state.
Unused cache bytes alone are excluded from that comparison. Dry arithmetic
16384/32768 cases and all seven mutations remain unchanged.

On the physical console, three201600 RGB pixels and both8192-byte PCM rings
match R29 exactly at title/room, including ring heads/registers/enabled voices.
The same replay and complete/checksummed/no-overflow/settings-matched captures
pass. Title first300 improves48.854496 ->50.035870 (+2.418 percent); room
54.202852 ->55.306802 (+2.037 percent). Audio fractions91.87/92.02 percent.
This recovers part of the cost; it does not restore prior room60 or qualify
constant60. One window per scene, remaining diagnostic cost and asynchronous
hardware timing limit the conclusion. Rain was not retested for this targeted
CPU investigation and remains a required later gate.

Native empty candidate131072B SHA256
9876e79ab2fb26bb2122703408c6daa21ef227ce3c99343f708cf09ae52a0011;
ELF4184c37dfdc7f35e7520da815be440bf45272e93297537c7f9c3ae0db1260295.
Reboot12/framebuffer5 and all41 memory owners pass, endD15C8 belowD2000.
USB return and coordinate8 restoration/readback pass; scanner menu retained.

[Curated evidence](evidence/dry-cache-2026-10-11.json) excludes commercial raw
inputs/outputs/hashes. The three-scene production reference remains distinct
from the two-scene optimization trial. Exact preceding4f3cadb Build38184026520,
CGRAM38184029950 and Ares38184029931 all succeed; fresh CI of this checkpoint
must be checked separately. Master is unchanged; PR21 draft. Next, reduce DSP
address/scheduling overhead while preserving PCM and the remaining full DSP
requirements. Complete sound/visual output and requested60fps matrix remain open.
