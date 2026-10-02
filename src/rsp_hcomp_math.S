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
    li s6, 0
    li s5, TILE_TABLE
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
hcomp_math_sources:
    lw s1, HCOMP_BAND_BASES
    lw s2, HCOMP_BAND_BASES + 4
    lw s3, HCOMP_BAND_BASES + 8
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
hcomp_vector:
    // Eight independent pixels. Renderer constants v23..v31 stay intact.
    lqv $v00, 0, 0, s5
    lqv $v01, 0, 64, s5
    lqv $v02, 0, 128, s5
    lqv $v03, 0, 192, s5
    addi t1, s6, TILE_TABLE
    lqv $v04, 0, 0, t1
    lqv $v05, 0, 512, t1
    vand $v00, $v00, $v04, 0
    // Zero eligibility while retiring any incoming vector carry bits.
    vge $v07, $v31, $v31, 0
    veq $v06, $v02, $v20, 8
    vmrg $v06, $v21, $v31, 0
    vor $v07, $v07, $v06, 0
    veq $v06, $v02, $v20, 9
    vmrg $v06, $v21, $v31, 0
    vor $v07, $v07, $v06, 0
    veq $v06, $v02, $v20, 10
    vmrg $v06, $v21, $v31, 0
    vor $v07, $v07, $v06, 0
    veq $v06, $v02, $v20, 11
    vmrg $v06, $v21, $v31, 0
    vor $v07, $v07, $v06, 0
    veq $v06, $v02, $v20, 12
    vmrg $v06, $v21, $v31, 0
    vor $v07, $v07, $v06, 0
    veq $v06, $v02, $v20, 13
    vmrg $v06, $v21, $v31, 0
    vor $v07, $v07, $v06, 0
    vand $v07, $v07, $v05, 0
    andi t0, v0, 2
    beqz t0, hcomp_vector_fixed
    nop
    veq $v06, $v03, $v16, 9
    vmrg $v01, $v22, $v01, 0
    vmrg $v13, $v31, $v21, 0
    b hcomp_vector_half
    vand $v13, $v13, $v04, 0
hcomp_vector_fixed:
    vor $v01, $v22, $v31, 0
    vor $v13, $v04, $v31, 0
hcomp_vector_half:
    andi t0, v1, 0x40
    bnez t0, hcomp_channels_start
    nop
    vand $v13, $v31, $v31, 0
hcomp_channels_start:
    // Extract, saturate and halve each 5-bit channel independently.
    // Packed carry tricks lose low-channel bits for mixed-color subtraction.
    vand $v14, $v31, $v31, 0
    li t1, 0x8000
    li t2, 3
    li t3, 2
hcomp_channel:
    mtc2 t1, $v16, 4
    vmudl $v08, $v00, $v16, 10
    vand $v08, $v08, $v19, 8
    vmudl $v09, $v01, $v16, 10
    vand $v09, $v09, $v19, 8
    andi t0, v1, 0x80
    beqz t0, hcomp_channel_add
    nop
    vsub $v10, $v08, $v09, 0
    vge $v10, $v10, $v31, 0
    vmudl $v11, $v10, $v16, 8
    b hcomp_channel_pack
    nop
hcomp_channel_add:
    vadd $v11, $v08, $v09, 0
    vlt $v10, $v11, $v19, 8
    vmudl $v11, $v11, $v16, 8
hcomp_channel_pack:
    veq $v06, $v13, $v31, 0
    vmrg $v10, $v10, $v11, 0
    mtc2 t3, $v16, 6
    vmudn $v10, $v10, $v16, 11
    vor $v14, $v14, $v10, 0
    srl t1, t1, 5
    addi t2, t2, -1
    bnez t2, hcomp_channel
    sll t3, t3, 5
    veq $v06, $v07, $v31, 0
    vmrg $v00, $v00, $v14, 0
    vor $v00, $v00, $v15, 8
    sqv $v00, 0, 0, s5
    addi s6, s6, 16
    addi s5, s5, 16
    li t0, SCRN_DATA + 64
    bne s5, t0, hcomp_vector
    nop
    li a0, SCRN_DATA
    move a1, s0
    jal 0xA4001F08
    li a2, 63
    addi s0, s0, 64
    addi s1, s1, 64
    addi s2, s2, 64
    addi s3, s3, 64
    li t0, 512
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
    // shared_decode expects its upper-plane accumulator empty on entry.
    vand $v20, $v31, $v31, 0
hcomp_return_phase:
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
