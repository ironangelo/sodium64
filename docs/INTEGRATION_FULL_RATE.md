# Full-rate APU startup and menu default

Extract the two defaults from10662795: start with APU_CYCLE21 and the matching
underclock menu index0. Previously normal startup used42, and closing the menu
could reapply42 after a diagnostic had selected21. No instructions, event
ordering, cycle table, DSP arithmetic or renderer code change.

This makes the ordinary startup match ROAD_TO_1_0 and its measured M1/Gate-B
contract. Existing Ares profiling explicitly selects21; HW_PROFILE also selects
21 before guest execution. The integration native captures at8da020c3 therefore
already exercise the selected full-rate path, not this default-value change.
They remain bounded original-workload measurements, not expanded corpus or
complete sound acceptance. Underclock selection remains a legacy manual option;
an underclocked run cannot be credited toward Road-to-1.0 performance.

Validation compares linked images with the immediate parent: only the two
initialized data bytes may differ, at apu_clock and underclk_set. All executable
instructions, other loaded bytes and allocated extents must remain identical.
Normal/PROFILE linked reset, GAIN and BRR gates plus the existing emulator/APU
cycle proofs remain applicable. Rollback is a direct revert.
