/* Fixed full arithmetic with exact COLOR windows. Setup's per-column allow
 * mask is retained while whole Main and winner rows use three DMAs per row.
 * The temporarily borrowed dirty-cache table is restored before every exit.
 * Unsupported bands enter the existing Math/RDP HALF fallback unchanged.
 */
#include <rsp.inc>
#include "defines.h"
#define BACKUP HCOMP_CGRAM_SIDEBAND_QUEUE1
#if (BACKUP & 7) || BACKUP + 1024 > HCOMP_CGRAM_SIDEBAND_QUEUE2
#error "Fixed-window backup exceeds its retired sideband owner"
#endif
#if VRAM_TABLE != TILE_TABLE + 1024 || OAM != VRAM_TABLE + 1024
#error "Fixed-window scratch requires the audited TILE/VRAM DMEM layout"
#endif
.data
.word 0, 0
.text
draw_bg:
    j 0xA4001F90
    move v0, t0
hcomp_entry:
    move s4, a1 // Resident loader retains this bank's masked RDRAM source.
    andi t0, v0, 0xC1 // No Main clipping and no direct-color mode.
    bnez t0, hcomp_fixed_window_fallback
    andi t0, v1, 0x40 // HALF and its absent-Sub semantics stay in old Math.
    bnez t0, hcomp_fixed_window_fallback
    andi t0, v0, 0xF2
    beqz t0, hcomp_fixed_window_fallback // Raw00 owns variable row colors.
    andi t0, v0, 2
    beqz t0, hcomp_fixed_window_operand_ready
    lbu t0, HCOMP_EFFECTIVE_TS
    bnez t0, hcomp_fixed_window_fallback
    nop
hcomp_fixed_window_operand_ready:
    lw t0, HCOMP_DIAG_COMPOSE_LIMIT
    bnez t0, hcomp_fixed_window_fallback
    nop
    // This sideband is retired and reserved exclusively for Math scratch.
    li a0, VRAM_TABLE
    li a1, BACKUP
    jal 0xA4001F08
    li a2, 1023
    li t1, TILE_TABLE + 512
    li t2, TILE_TABLE + 1024
hcomp_fixed_window_mask_copy:
    lqv $v03, 0, 0, t1
    sqv $v03, 0, 512, t1
    addi t1, t1, 16
    bne t1, t2, hcomp_fixed_window_mask_copy
    nop
    li t0, 0x0421
    mtc2 t0, $v19, 0
    li t0, 0x8420
    mtc2 t0, $v19, 2
    li t0, 0x7BDE
    mtc2 t0, $v19, 4
    li t0, 0x0800
    mtc2 t0, $v16, 4
    li t0, 2
    mtc2 t0, $v16, 6
    vor $v01, $v22, $v31, 0
    vand $v13, $v31, $v31, 0
    lw s2, HCOMP_BAND_BASES + 4
    lw s7, HCOMP_BAND_ROWS
hcomp_fixed_window_row:
    li a0, TILE_TABLE
    move a1, s0
    jal 0xA4001F40
    li a2, 511
    li a0, TILE_TABLE + 512
    move a1, s2
    jal 0xA4001F40
    li a2, 511
    li s5, TILE_TABLE
    li s6, TILE_TABLE + 512
hcomp_fixed_window_vector:
    lqv $v00, 0, 0, s5
    lqv $v02, 0, 512, s5
    addi a0, s5, 1024
    lqv $v05, 0, 0, a0
    vge $v07, $v31, $v31, 0
    veq $v06, $v02, $v16, 9
    vmrg $v07, $v31, $v21, 0
    vand $v07, $v07, $v05, 0
    vne $v06, $v07, $v31, 0
    cfc2 t0, $1
    andi t0, t0, 0xFF
    beqz t0, hcomp_fixed_window_output
    nop
#define hcomp_channels_start hcomp_fixed_window_kernel
#define hcomp_packed_add hcomp_fixed_window_add
#define hcomp_packed_select hcomp_fixed_window_select
#include "rsp_hcomp_packed_math.inc"
#undef hcomp_channels_start
#undef hcomp_packed_add
#undef hcomp_packed_select
hcomp_fixed_window_output:
    vor $v00, $v00, $v15, 8
    sqv $v00, 0, 0, s5
    addi s5, s5, 16
    bne s5, s6, hcomp_fixed_window_vector
    nop
    li a0, TILE_TABLE
    move a1, s0
    jal 0xA4001F08
    li a2, 511
    addi s0, s0, 560
    addi s2, s2, 560
    addi s7, s7, -1
    bnez s7, hcomp_fixed_window_row
    nop
hcomp_fixed_window_restore:
    li a0, VRAM_TABLE
    li a1, BACKUP
    jal 0xA4001F40
    li a2, 1023
    vand $v20, $v31, $v31, 0
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, 0x1778
hcomp_fixed_window_fallback:
    move a1, s4 // The outer RDP HALF descriptor is not our fallback owner.
    li t0, -8
    and a1, a1, t0
    addi a1, a1, 1000
    li a0, SCRN_DATA
    jal 0xA4001F40
    li a2, 7
    lw a1, SCRN_DATA
    j 0xA4001F7C
    li t9, 0x13B0
.org (0x760 - 0x3A8)
hcomp_screen_switch:
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, 0x1760
.org (0x788 - 0x3A8)
draw_mode7_entry:
    j 0xA4001F78
    li t9, 0x1788
