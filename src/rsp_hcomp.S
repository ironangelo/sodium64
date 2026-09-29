/* Stage 1: bounded first-section output, full brightness, regular BG1/BG2.
 * Scalar RGB555 math uses a permuted channel order (RGBA5551 >> 1); packed
 * formulas are channel symmetric. Only the declared half-add workload is
 * published here. Other operations remain outside this bounded output gate.
 */
#include <rsp.inc>
#include "defines.h"
.data
.byte 0
.text
.byte 0:0x3A8
draw_bg:
    j 0xA4001F90
    move v0, t0
hcomp_entry:
    // All readback/writeback has finished before publishing this queue slot.
    xori sp, sp, 4
    li t0, 2
    mtc0 t0, COP0_SP_STATUS
    j 0xA400103C
    nop

hcomp_fence:
    // SyncFull is required before either TS provenance or Main pixels are read.
    lui t0, 0x2900
    sw t0, SCRN_DATA
    sw zero, SCRN_DATA + 4
    li a0, SCRN_DATA
    jal 0xA4001F5C
    li a1, SCRN_DATA + 8
hcomp_fence_wait:
    mfc0 t0, COP0_DP_STATUS
    andi t0, t0, 0x20
    bnez t0, hcomp_fence_wait
    nop
    jr t8
    nop

hcomp_provenance_switch_helper:
    bnez k0, hcomp_sub_presence_saved
    li t8, %lo(hcomp_copy_ts_start)
hcomp_copy_ts_fence:
    b hcomp_fence
    nop
hcomp_copy_ts_start:
    // Preserve all 280x8 rendered tags, not a uniform-presence assumption.
    li t6, 0xA00E2000
    li t7, 0xA00E6000
    li a3, 70
hcomp_copy_ts:
    li a0, SCRN_DATA
    move a1, t6
    jal 0xA4001F40
    li a2, 63
    move a1, t7
    jal 0xA4001F08
    li a2, 63
    addi t6, t6, 64
    addi t7, t7, 64
    addi a3, a3, -1
    bnez a3, hcomp_copy_ts
    nop
hcomp_sub_presence_saved:
    lw t0, FRAMEBUFFER(sp)
    addi t0, t0, 280 * -16
    sw t0, RDP_FRAME + 4
    li a0, RDP_FRAME
    jal 0xA4001F5C
    li a1, RDP_FRAME + 8
    lw a1, OVERLAY_MAIN_SRC
    li t9, 0x1370
    j 0xA4001F7C
    nop

hcomp_provenance_end:
    // Later sections are untouched. Reject other geometry and operations.
    bnez k0, hcomp_section_done
    li t0, 8
    bne k1, t0, hcomp_section_done
    lbu v1, CGADSUB
    li t0, 0x41
    bne v1, t0, hcomp_section_done
    li t8, %lo(hcomp_output_start)
    b hcomp_fence
    nop
hcomp_output_start:
    lbu a0, WOBJSEL
    srl a0, a0, 4
    lbu a1, WOBJLOG
    srl a1, a1, 2
    andi a1, a1, 3
    jal 0xA4001CE4
    li a2, 1
    lbu v0, CGWSEL
    lhu gp, SUB_COLOR
    srl gp, gp, 1
    lw s0, FRAMEBUFFER(sp)
    addi s0, s0, 0x1198
    li s1, 0xA00E4018
    li s2, 0xA00E2018
    li s3, 0xA00E6018
    li s7, 8
hcomp_row:
    li s6, 0
hcomp_batch:
    // Four 32-pixel inputs occupy only SCRN_DATA..CHAR_DATA+127.
    li a0, SCRN_DATA
    move a1, s0
    jal 0xA4001F40
    li a2, 63
    li a0, SCRN_DATA + 64
    move a1, s1
    jal 0xA4001F40
    li a2, 63
    li a0, SCRN_DATA + 128
    move a1, s2
    jal 0xA4001F40
    li a2, 63
    li a0, SCRN_DATA + 192
    move a1, s3
    jal 0xA4001F40
    li a2, 63
    li s5, SCRN_DATA
hcomp_pixel:
    // Exact inclusive span membership, including semantic x=255.
    lbu t9, WIN_COUNT
    li t2, WIN_BOUNDS
    move t6, zero
hcomp_span:
    beqz t9, hcomp_selected
    nop
    lbu t3, 0(t2)
    lbu t4, 1(t2)
    sltu t3, s6, t3
    sltu t4, t4, s6
    or t3, t3, t4
    xori t3, t3, 1
    or t6, t6, t3
    addi t9, t9, -1
    b hcomp_span
    addi t2, t2, 2
hcomp_selected:
    sll t6, t6, 2
    li t3, 0x35
    srl t4, v0, 6
    or t4, t4, t6
    srlv t8, t3, t4
    andi t8, t8, 1
    srl t4, v0, 4
    andi t4, t4, 3
    or t4, t4, t6
    srlv t9, t3, t4
    andi t9, t9, 1
    lhu t0, 0(s5)
    srl t0, t0, 1
    bnez t8, hcomp_main_ready
    nop
    move t0, zero
hcomp_main_ready:
    lhu t2, 128(s5)
    srl t2, t2, 11
    and t2, t2, v1
    and t2, t2, t9
    beqz t2, hcomp_store
    move t3, t0
    // Fixed operand permits HALF; absent selected Sub suppresses it.
    move t7, gp
    andi t2, v0, 2
    beqz t2, hcomp_add
    move t5, t8
    lhu t2, 192(s5)
    li t4, 0x0400
    beq t2, t4, hcomp_add
    move t5, zero
    lhu t7, 64(s5)
    srl t7, t7, 1
    move t5, t8
hcomp_add:
    beqz t5, hcomp_add_full
    add t3, t0, t7
    xor t4, t0, t7
    andi t4, t4, 0x0421
    sub t3, t3, t4
    b hcomp_store
    srl t3, t3, 1
hcomp_add_full:
    xor t4, t0, t7
    andi t4, t4, 0x0421
    sub t4, t3, t4
    andi t4, t4, 0x8420
    sub t3, t3, t4
    srl t5, t4, 5
    sub t4, t4, t5
    or t3, t3, t4
hcomp_store:
    sll t3, t3, 1
    ori t3, t3, 1
    sh t3, 0(s5)
    addi s6, s6, 1
    addi s5, s5, 2
    li t0, SCRN_DATA + 64
    bne s5, t0, hcomp_pixel
    nop
    li a0, SCRN_DATA
    move a1, s0
    jal 0xA4001F08
    li a2, 63
    addi s0, s0, 64
    addi s1, s1, 64
    addi s2, s2, 64
    addi s3, s3, 64
    li t0, 256
    bne s6, t0, hcomp_batch
    nop
    addi s0, s0, 48
    addi s1, s1, 48
    addi s2, s2, 48
    addi s3, s3, 48
    addi s7, s7, -1
    bnez s7, hcomp_row
    nop
hcomp_section_done:
    li a0, RDP_INIT
    jal 0xA4001F5C
    li a1, RDP_INIT + 8
    j 0xA40010C0
    nop

// Fixed dispatch ABI. The assembler fails rather than silently moving it.
.org 0x760
hcomp_screen_switch:
    beqz s7, hcomp_provenance_end
    nop
    b hcomp_provenance_switch_helper
    nop
.org 0x788
draw_mode7_entry:
    j 0xA4001F78
    li t9, 0x1788
