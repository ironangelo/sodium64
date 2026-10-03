/* Full-height HCOMP phase bank. Real section epochs are consumed once;
 * virtual <=8-row bands reuse owned Sub/Z/presence surfaces. Every target
 * is rebased before the first draw, including blank and short sections.
 */
#include <rsp.inc>
#include "defines.h"
.data
.byte 0
.text
draw_bg:
    j 0xA4001F90
    move v0, t0
hcomp_entry:
    b hcomp_fence
    li t8, %lo(hcomp_publish)
hcomp_publish:
    xori sp, sp, 4
    li t0, 2
    mtc0 t0, COP0_SP_STATUS
    j 0xA400103C
    nop

hcomp_fence:
    lui t0, 0x2900
    sw t0, SCRN_DATA
    sw zero, SCRN_DATA + 4
    li a0, SCRN_DATA
    jal 0xA4001F5C
    li a1, SCRN_DATA + 8
hcomp_fence_wait:
    mfc0 t0, COP0_DP_STATUS
    andi t0, t0, 0x70
    bnez t0, hcomp_fence_wait
    nop
    jr t8
    nop

hcomp_band_begin:
    sw k1, HCOMP_SECTION_END
    // Resident admission avoids two slot DMAs for a proven common case.
    // Other epochs and OBJ-sensitive spans keep the full bank admission.
    j 0xA400122C
    nop
    nop
hcomp_band_start:
    lw t0, HCOMP_SECTION_END
    slt t1, k0, t0
    // The taken transition must retain the real epoch end in k1. An ADDI
    // in this delay slot would skip FRAME_END and read beyond the section queue.
    beqz t1, hcomp_real_section_done
    move k1, t0
    lw t1, HCOMP_BAND_RAW
    beqz t1, hcomp_general_bounds
    lw t0, HCOMP_FAST_END
    b hcomp_band_bounds_ready
    move k1, t0
hcomp_general_bounds:
    addi k1, k0, 8
    slt t1, t0, k1
    beqz t1, hcomp_band_bounds_ready
    nop
    move k1, t0
hcomp_band_bounds_ready:
    sub t0, k1, k0
    sw t0, HCOMP_BAND_ROWS
    lw t0, FB_OFFSET(sp)
    add t2, t0, k1
    add t0, t0, k0
    sw t0, HCOMP_BAND_Y
    // Palette/stat section format admits at most 255 scanlines. CPU border
    // is 0/8; the published viewport must stay inside its 240-row framebuffer.
    sltiu t1, t0, 8
    bnez t1, hcomp_bad_geometry
    nop
    sltiu t1, t2, 249
    beqz t1, hcomp_bad_geometry
    nop
    sll t1, t0, 2
    sh t1, RDP_FILL + 10
    sh t1, RDP_FILL + 38
    sll t1, t2, 2
    sh t1, RDP_FILL + 14
    sh t1, RDP_FILL + 34
    // 560-byte stride: y * (512+32+16). Round the displacement up to
    // 64 bytes, so both image bases stay aligned at arbitrary section Y.
    // Move the compact pixel origins back by the same padding; consumers
    // must use those origins rather than fixed E2000/E4000/E6000 addresses.
    sll t1, t0, 9
    sll t2, t0, 5
    add t1, t1, t2
    sll t2, t0, 4
    add t1, t1, t2
    sll t3, t0, 4
    andi t3, t3, 63
    add t1, t1, t3
    li t2, 0xE2000
    sub t2, t2, t1
    sw t2, HCOMP_PROOF_RDP_CMDS + 20
    li t2, 0xE4000
    sub t2, t2, t1
    sw t2, RDP_FRAME + 4
    li t2, 0xA00E4018
    sub t2, t2, t3
    sw t2, HCOMP_BAND_BASES
    li t2, 0xA00E2018
    sub t2, t2, t3
    sw t2, HCOMP_BAND_BASES + 4
    li t2, 0xA00E6018
    sub t2, t2, t3
    sw t2, HCOMP_BAND_BASES + 8
hcomp_band_targets_ready:
    sb zero, HCOMP_SCREEN
    lw t0, HCOMP_DIAG_COMPOSE_LIMIT
    beqz t0, hcomp_dispatch_policy
    sltu t1, k0, t0
    bnez t1, hcomp_dispatch_policy
    nop
    li t0, 1
    sw t0, HCOMP_BAND_RAW
hcomp_dispatch_policy:
    lw t0, HCOMP_BAND_RAW
    beqz t0, hcomp_compact_band
    li t1, 1
    beq t0, t1, hcomp_raw_band
    nop
    // Direct Sub/black-mask/Main composition writes the final target with Z
    // disabled. Aligned compact bases above remain unused in this policy.
    lw t0, FRAMEBUFFER(sp)
    addi t0, t0, 280 * -16
    b hcomp_screen_masks
    sw t0, RDP_FRAME + 4
hcomp_compact_band:
    li a0, HCOMP_PROOF_RDP_CMDS
    jal 0xA4001F5C
    li a1, HCOMP_PROOF_BG_DEPTH_CMDS
hcomp_screen_masks:
    lbu s7, HCOMP_EFFECTIVE_TS
    lbu t0, TM
    sll t0, t0, 8
    b hcomp_fill_target
    or s7, s7, t0
hcomp_raw_band:
    li t0, 1
    sb t0, HCOMP_SCREEN
    sw t0, HCOMP_BAND_RAW
    lw t0, FRAMEBUFFER(sp)
    addi t0, t0, 280 * -16
    sw t0, RDP_FRAME + 4
    li a0, RDP_INIT
    jal 0xA4001F5C
    li a1, RDP_INIT + 8
    lbu s7, TM
hcomp_fill_target:
    li a0, RDP_FRAME
    jal 0xA4001F5C
    li a1, RDP_FRAME + 8
    // Direct Sub starts with fixed color, the exact absent-Sub operand.
    // The general and Main-only policies keep the ordinary Main backdrop.
    lw t0, HCOMP_BAND_RAW
    sltiu t0, t0, 2
    sll t0, t0, 1
    lhu s0, SUB_COLOR(t0)
    lb t4, STAT_FLAGS
    bgez t4, hcomp_backdrop_color
    nop
    move s0, zero
hcomp_backdrop_color:
    li a0, HCOMP_PROOF_RDP_CMDS + 24
    jal 0xA4001F5C
    li a1, HCOMP_PROOF_BG_DEPTH_CMDS
    andi t0, s0, 0x3E
    sll t0, t0, 10
    andi t1, s0, 0x7C0
    sll t1, t1, 13
    or t0, t0, t1
    andi t1, s0, 0xF800
    sll t1, t1, 16
    or t0, t0, t1
    ori t0, t0, 0xFF
    sw t0, RDP_FILL + 20
    lw t0, FILLREC_MASK
    lw t1, RDP_FILL + 36
    and t1, t1, t0
    lui t2, 3
    or t1, t1, t2
    sw t1, RDP_FILL + 36
    lw t1, RDP_FILL + 32
    and t1, t1, t0
    li t2, 268 << 14
    or t1, t1, t2
    sw t1, RDP_FILL + 32
    li a0, RDP_FILL + 8
    jal 0xA4001F5C
    li a1, RDP_WINDOW
    bltz t4, hcomp_band_done
    nop
    sw zero, PRIO_CHECKS
    sw zero, PRIO_CHECKS + 4
    lbu s3, BG_MODE
    andi s3, s3, 0xF
    sll s3, s3, 4
    lw a1, OVERLAY_MAIN_SRC
    j 0xA4001F7C
    li t9, 0x1370

hcomp_screen_end:
    lbu t0, HCOMP_SCREEN
    bnez t0, hcomp_main_end
    lw t0, HCOMP_BAND_RAW
    addi t0, t0, -2
    beqz t0, hcomp_fast_main
    li t8, %lo(hcomp_copy_ts_start)
    b hcomp_fence
    nop
hcomp_fast_main:
    lw a1, OVERLAY_HCOMP_FAST_SRC
    j 0xA4001F7C
    li t9, 0x1760
hcomp_copy_ts_start:
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
    li t0, 1
    sb t0, HCOMP_SCREEN
    lw t0, FRAMEBUFFER(sp)
    addi t0, t0, 280 * -16
    b hcomp_fill_target
    sw t0, RDP_FRAME + 4
hcomp_main_end:
    lw t0, HCOMP_BAND_RAW
    bnez t0, hcomp_band_done
    li t8, %lo(hcomp_math_start)
    b hcomp_fence
    nop
hcomp_math_start:
    lw a1, OVERLAY_HCOMP_MATH_SRC
    j 0xA4001F7C
    li t9, 0x13B0
hcomp_band_done:
    // Disable Z before the next epoch/target or final palette load.
    li a0, HCOMP_PROOF_RDP_CMDS
    jal 0xA4001F5C
    li a1, HCOMP_PROOF_RDP_CMDS + 8
    li a0, RDP_INIT
    jal 0xA4001F5C
    li a1, RDP_INIT + 8
    move k0, k1
    lw t0, HCOMP_OBJ_ADAPTIVE
    beqz t0, hcomp_band_start
    lw a1, OVERLAY_HCOMP_FAST_SRC
    j 0xA4001F7C
    li t9, 0x1740
hcomp_real_section_done:
    j 0xA40010C0
    nop
hcomp_bad_geometry:
    // Fail closed on a corrupt viewport instead of corrupting framebuffer RAM.
    break
    b hcomp_bad_geometry
    nop

.org (0x760 - 0x3A8)
hcomp_screen_switch:
    b hcomp_screen_end
    nop
.org (0x768 - 0x3A8)
hcomp_policy_return:
    b hcomp_band_start
    nop
.org (0x778 - 0x3A8)
hcomp_math_return:
    b hcomp_band_done
    nop
.org (0x780 - 0x3A8)
hcomp_band_entry:
    b hcomp_band_begin
    nop
.org (0x788 - 0x3A8)
draw_mode7_entry:
    j 0xA4001F78
    li t9, 0x1788

