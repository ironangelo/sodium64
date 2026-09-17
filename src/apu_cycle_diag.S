/*
    Temporary M1 diagnostic state for proving SPC700 JIT cycle accounting.

    This file is PROFILE-only and lives on the phase2/apu-cycle-proof branch.
    It is not runtime architecture and is not intended for master.
*/

#include "defines.h"

#ifdef SODIUM64_PROFILE

.globl apu_cycle_diag_last_start
.globl apu_cycle_diag_last_end
.globl apu_cycle_diag_static_cycles
.globl apu_cycle_diag_span
.globl apu_cycle_diag_region_delta
.globl apu_cycle_diag_target
.globl apu_cycle_diag_sequence

.data

.align 4
apu_cycle_diag_last_start:    .hword 0
apu_cycle_diag_last_end:      .hword 0
apu_cycle_diag_static_cycles: .word 0
apu_cycle_diag_span:          .word 0
apu_cycle_diag_region_delta:  .word 0
apu_cycle_diag_target:        .hword 0
.align 4
apu_cycle_diag_sequence:      .word 0

#endif
