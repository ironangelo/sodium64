/* Section mask/constants and preserved-Sub copies. Original SNES state only. */
#include <rsp.inc>
#include "defines.h"
.data
.byte 0
.text
draw_bg:
    j 0xA4001F90
    move v0, t0
hcomp_entry:
hcomp_output_start:
hcomp_setup_entry:
    // Minimal input ownership record for the complete-image oracle. Capture
    // this section's bounds, not the next section's/end-frame mutable state.
    lbu v1, CGADSUB
    lw t0, FRAMEBUFFER(sp)
    sw t0, SCRN_DATA
    lhu t0, WHX
    sh t0, SCRN_DATA + 4
    lhu t0, WHX + 2
    sh t0, SCRN_DATA + 6
    lbu t0, CGWSEL
    sh t0, SCRN_DATA + 8
    lbu t0, WOBJSEL
    sh t0, SCRN_DATA + 10
    lbu t0, WOBJLOG
    sh t0, SCRN_DATA + 12
    sh zero, SCRN_DATA + 14
    li a0, SCRN_DATA
    li a1, 0xA00F0000
    jal 0xA4001F08
    li a2, 15
    lbu a0, WOBJSEL
    srl a0, a0, 4
    lbu a1, WOBJLOG
    srl a1, a1, 2
    andi a1, a1, 3
    jal 0xA4001CE4
    li a2, 1
    lbu v0, CGWSEL
    lhu gp, SUB_COLOR
    li s6, 0
    li s5, TILE_TABLE
    andi t0, v0, 0xF2
    bnez t0, hcomp_mask_pixel
    nop
    // Exact uniform COLOR masks leave the upper half available for row colors.
    li a0, TILE_TABLE + 512
    lw a1, HCOMP_ROW_FIXED_SRC
    jal 0xA4001F40
    li a2, 511
    vnor $v21, $v31, $v31, 0
    li t0, TILE_TABLE
    li t1, TILE_TABLE + 512
hcomp_flat_mask:
    sqv $v21, 0, 0, t0
    addi t0, t0, 16
    bne t0, t1, hcomp_flat_mask
    nop
    b hcomp_vector_constants
    nop
hcomp_mask_pixel:
    lbu t9, WIN_COUNT
    li t2, WIN_BOUNDS
    move t6, zero
hcomp_mask_span:
    beqz t9, hcomp_mask_selected
    nop
    lbu t3, 0(t2)
    lbu t4, 1(t2)
    sltu t3, s6, t3
    sltu t4, t4, s6
    or t3, t3, t4
    xori t3, t3, 1
    or t6, t6, t3
    addi t9, t9, -1
    b hcomp_mask_span
    addi t2, t2, 2
hcomp_mask_selected:
    sll t6, t6, 2
    li t3, 0x35
    srl t4, v0, 6
    or t4, t4, t6
    srlv t8, t3, t4
    andi t8, t8, 1
    sub t8, zero, t8
    sh t8, 0(s5)
    srl t4, v0, 4
    andi t4, t4, 3
    or t4, t4, t6
    srlv t8, t3, t4
    andi t8, t8, 1
    sub t8, zero, t8
    sh t8, 512(s5)
    addi s6, s6, 1
    addi s5, s5, 2
    li t0, 256
    bne s6, t0, hcomp_mask_pixel
    nop
hcomp_vector_constants:
    li t0, 1
    mtc2 t0, $v15, 0
    li t0, 0x8000
    mtc2 t0, $v16, 0
    li t0, 0x0400
    mtc2 t0, $v16, 2
    li t0, 31
    mtc2 t0, $v19, 0
    vnor $v21, $v31, $v31, 0
    mtc2 gp, $v22, 0
    vor $v22, $v31, $v22, 8
    sll t0, v1, 31
    sra t0, t0, 31
    andi t0, t0, 0x0C00
    mtc2 t0, $v20, 0
    sll t0, v1, 30
    sra t0, t0, 31
    andi t0, t0, 0x1400
    mtc2 t0, $v20, 2
    sll t0, v1, 29
    sra t0, t0, 31
    andi t0, t0, 0x1C00
    mtc2 t0, $v20, 4
    sll t0, v1, 28
    sra t0, t0, 31
    andi t0, t0, 0x2800
    mtc2 t0, $v20, 6
    sll t0, v1, 27
    sra t0, t0, 31
    andi t0, t0, 0x5000
    mtc2 t0, $v20, 8
    sll t0, v1, 26
    sra t0, t0, 31
    andi t0, t0, 0x0400
    mtc2 t0, $v20, 10
    lw t0, HCOMP_BAND_Y
    addi t0, t0, -8
    sll t1, t0, 9
    sll t2, t0, 5
    add t1, t1, t2
    sll t2, t0, 4
    add t1, t1, t2
    lw s0, FRAMEBUFFER(sp)
    add s0, s0, t1
    addi s0, s0, 24
    lw a1, OVERLAY_HCOMP_MATH_SRC
    j 0xA4001F7C
    li t9, 0x13B0
hcomp_setup_copy:
    lw t6, HCOMP_BAND_BASES + 4
    addi t6, t6, -24
    lw t7, HCOMP_BAND_BASES + 8
    addi t7, t7, -24
    lw a3, HCOMP_BAND_ROWS
    sll t0, a3, 9
    sll t1, a3, 5
    add t0, t0, t1
    sll a3, a3, 4
    add a3, a3, t0
hcomp_copy_ts:
    // Main/OBJ reload their cache before using TILE_TABLE. Borrow its exact
    // 1024-byte extent after Sub is fenced; retain VRAM_TABLE at0x440.
    li a2, 1023
    slti t0, a3, 1024
    beqz t0, hcomp_copy_chunk
    li a0, TILE_TABLE
    addi a2, a3, -1
hcomp_copy_chunk:
    move a1, t6
    jal 0xA4001F40
    nop
    move a1, t7
    jal 0xA4001F08
    nop
    addi t0, a2, 1
    add t6, t6, t0
    add t7, t7, t0
    sub a3, a3, t0
    bnez a3, hcomp_copy_ts
    nop
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, 0x1770

.org (0x760 - 0x3A8)
hcomp_screen_switch:
    b hcomp_setup_copy
    nop
.org (0x788 - 0x3A8)
draw_mode7_entry:
    j 0xA4001F78
    li t9, 0x1788
