/* HCOMP arithmetic bank: every admitted band, add/sub/full/half,
 * exact color windows, backdrop/BG/OBJ eligibility and absent-Sub fallback.
 * The phase bank owns RDP fencing and band/section progression.
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
hcomp_output_start:
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
    srl gp, gp, 1
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
    li s1, 0xA00E4018
    li s2, 0xA00E2018
    li s3, 0xA00E6018
    lw s7, HCOMP_BAND_ROWS
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
    srl t2, t2, 10
    andi t2, t2, 31
    lbu t2, HCOMP_ELIGIBILITY_TABLE(t2)
    and t2, t2, v1
    sltu t2, zero, t2
    and t2, t2, t9
    beqz t2, hcomp_store
    move t3, t0
    // Fixed operand permits HALF; absent selected Sub suppresses it.
    move t7, gp
    andi t5, v1, 0x40
    sltu t5, zero, t5
    and t5, t5, t8
    andi t2, v0, 2
    beqz t2, hcomp_math
    nop
    lhu t2, 192(s5)
    li t4, 0x0400
    beq t2, t4, hcomp_absent_sub
    nop
    lhu t7, 64(s5)
    srl t7, t7, 1
    b hcomp_math
    nop
hcomp_absent_sub:
    move t5, zero
hcomp_math:
    andi t2, v1, 0x80
    bnez t2, hcomp_sub
    nop
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
    b hcomp_store
    or t3, t3, t4
hcomp_sub:
    li t4, 0x8420
    sub t3, t0, t7
    add t3, t3, t4
    xor t2, t0, t7
    and t2, t2, t4
    sub t2, t3, t2
    and t2, t2, t4
    sub t3, t3, t2
    srl t4, t2, 5
    sub t2, t2, t4
    and t3, t3, t2
    beqz t5, hcomp_store
    nop
    andi t3, t3, 0x7BDE
    srl t3, t3, 1
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
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, 0x1778
.org (0x760 - 0x3A8)
hcomp_screen_switch:
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, 0x1760
.org (0x788 - 0x3A8)
draw_mode7_entry:
    j 0xA4001F78
    li t9, 0x1788
