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
hcomp_math_sources:
    // Packed RGB555 uses unsigned wrapping lanes. VADD/VSUB would saturate
    // as signed16 and destroy channel carry guards; use VADDC/VSUBC below.
    // Keep the setup, winner/presence, masks and memory ownership unchanged.
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
    lw s1, HCOMP_BAND_BASES
    lw s2, HCOMP_BAND_BASES + 4
    lw s3, HCOMP_BAND_BASES + 8
    lw s7, HCOMP_BAND_ROWS
    sll s4, k0, 1
    addi s4, s4, TILE_TABLE + 512
hcomp_row:
    andi t0, v0, 0xF2
    bnez t0, hcomp_row_color_ready
    nop
    lhu gp, 0(s4)
    mtc2 gp, $v22, 0
    vor $v22, $v31, $v22, 8
hcomp_row_color_ready:
    li s6, 0
hcomp_batch:
    // Four 32-pixel inputs occupy only SCRN_DATA..CHAR_DATA+127.
    li a0, SCRN_DATA
    move a1, s0
    jal 0xA4001F40
    li a2, 63
    li a0, SCRN_DATA + 128
    move a1, s2
    jal 0xA4001F40
    li a2, 63
    andi t0, v0, 2
    beqz t0, hcomp_optional_sub_done
    lbu t0, HCOMP_EFFECTIVE_TS
    beqz t0, hcomp_optional_sub_done
    nop
    li a0, SCRN_DATA + 64
    move a1, s1
    jal 0xA4001F40
    li a2, 63
    li a0, SCRN_DATA + 192
    move a1, s3
    jal 0xA4001F40
    li a2, 63
hcomp_optional_sub_done:
    li s5, SCRN_DATA
hcomp_vector:
    // Eight independent pixels. Renderer constants v23..v31 stay intact.
    lqv $v00, 0, 0, s5
    lqv $v01, 0, 64, s5
    lqv $v02, 0, 128, s5
    lqv $v03, 0, 192, s5
    addi t1, s6, TILE_TABLE
    lqv $v04, 0, 0, t1
    andi t0, v0, 0xF2
    beqz t0, hcomp_uniform_math_mask
    nop
    lqv $v05, 0, 512, t1
    b hcomp_math_mask_ready
    nop
hcomp_uniform_math_mask:
    vor $v05, $v21, $v31, 0
hcomp_math_mask_ready:
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
hcomp_vector_math_test:
    // The exact winner/window mask is already resolved. If all eight pixels
    // forbid math, retain clipped Main without computing either operand.
    // Winner comparisons above have already retired VCO. VNE directly
    // reports eligible lanes without inverting the equality mask in scalar.
    vne $v06, $v07, $v31, 0
    cfc2 t0, $1
    andi t0, t0, 0xFF
    beqz t0, hcomp_vector_output
    nop
hcomp_vector_math_active:
    andi t0, v0, 2
    beqz t0, hcomp_vector_fixed
    nop
    lbu t0, HCOMP_EFFECTIVE_TS
    beqz t0, hcomp_vector_absent
    nop
    veq $v06, $v03, $v16, 9
    vmrg $v01, $v22, $v01, 0
    vmrg $v13, $v31, $v21, 0
    b hcomp_vector_half
    vand $v13, $v13, $v04, 0
hcomp_vector_absent:
    vor $v01, $v22, $v31, 0
    b hcomp_channels_start
    vand $v13, $v31, $v31, 0
hcomp_vector_fixed:
    vor $v01, $v22, $v31, 0
    vor $v13, $v04, $v31, 0
hcomp_vector_half:
    andi t0, v1, 0x40
    bnez t0, hcomp_channels_start
    nop
    vand $v13, $v31, $v31, 0
hcomp_channels_start:
    // Drop the framebuffer alpha bit before packed arithmetic. All inputs
    // are <=7FFF, so addition fits unsigned16; subtraction's bit16 is
    // immaterial because the final guard mask removes it. HALF add must
    // average before saturation; HALF subtract halves saturated difference.
    vmudl $v08, $v00, $v16, 8
    vmudl $v09, $v01, $v16, 8
    andi t0, v1, 0x80
    beqz t0, hcomp_packed_add
    nop
    // d = x-y+8420; b = (d-((x^y)&8420))&8420;
    // full = (d-b)&(b-(b>>5)). Each guard selects its channel independently.
    vsubc $v10, $v08, $v09, 0
    vaddc $v10, $v10, $v19, 9
    vxor $v11, $v08, $v09, 0
    vand $v11, $v11, $v19, 9
    vsubc $v11, $v10, $v11, 0
    vand $v11, $v11, $v19, 9
    vsubc $v10, $v10, $v11, 0
    vmudl $v12, $v11, $v16, 10
    vsubc $v11, $v11, $v12, 0
    vand $v10, $v10, $v11, 0
    vand $v11, $v10, $v19, 10
    vmudl $v11, $v11, $v16, 8
    b hcomp_packed_select
    nop
hcomp_packed_add:
    // s=x+y; q=s-((x^y)&0421); c=q&8420;
    // full=(s-c)|(c-(c>>5)); half=q>>1.
    vaddc $v10, $v08, $v09, 0
    vxor $v11, $v08, $v09, 0
    vand $v11, $v11, $v19, 8
    vsubc $v11, $v10, $v11, 0
    vand $v12, $v11, $v19, 9
    vmudl $v11, $v11, $v16, 8
    vsubc $v10, $v10, $v12, 0
    vmudl $v14, $v12, $v16, 10
    vsubc $v12, $v12, $v14, 0
    vor $v10, $v10, $v12, 0
hcomp_packed_select:
    // Wrapping arithmetic leaves VCO carry/borrow bits. Retire them before
    // VEQ; otherwise equal zero HALF masks can inherit unrelated borrow.
    vge $v06, $v31, $v31, 0
    veq $v06, $v13, $v31, 0
    vmrg $v10, $v10, $v11, 0
    vmudn $v14, $v10, $v16, 11
    veq $v06, $v07, $v31, 0
    vmrg $v00, $v00, $v14, 0
hcomp_vector_output:
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
    addi s4, s4, 2
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
