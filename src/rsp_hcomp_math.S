/* HCOMP arithmetic bank: every admitted band, add/sub/full/half,
 * exact color windows, backdrop/BG/OBJ eligibility and absent-Sub fallback.
 * The phase bank owns RDP fencing and band/section progression.
 */
#include <rsp.inc>
#include "defines.h"
#if SODIUM64_HCOMP_MASK_SCAN && !SODIUM64_HCOMP_WIDE_MATH
#error "HCOMP_MASK_SCAN requires HCOMP_WIDE_MATH"
#endif
#ifndef SODIUM64_HCOMP_FULL_ROW_MATH
#define SODIUM64_HCOMP_FULL_ROW_MATH 0
#endif
#if SODIUM64_HCOMP_FULL_ROW_MATH && (!SODIUM64_HCOMP_WIDE_MATH || !SODIUM64_ELIGIBILITY_TAGS)
#error "HCOMP_FULL_ROW_MATH requires HCOMP_WIDE_MATH and ELIGIBILITY_TAGS"
#endif
#if SODIUM64_HCOMP_FULL_ROW_MATH
// This currently dormant sideband extent is reserved exclusively for RSP
// Math's VRAM_TABLE backup. CPU sideband writers must not coexist with it.
#define HCOMP_MATH_VRAM_BACKUP HCOMP_CGRAM_SIDEBAND_QUEUE1
#if (HCOMP_MATH_VRAM_BACKUP & 7) || HCOMP_MATH_VRAM_BACKUP + 1024 > HCOMP_CGRAM_SIDEBAND_QUEUE2
#error "HCOMP Math backup must fit aligned in the reserved Q1 sideband"
#endif
#if VRAM_TABLE != TILE_TABLE + 1024 || OAM != VRAM_TABLE + 1024
#error "HCOMP full row requires the exact TILE/VRAM 2048-byte DMEM extent"
#endif
#endif
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
#if SODIUM64_HCOMP_WIDE_MATH
    // Uniform COLOR masks leave TILE_TABLE available after setup. Four
    // 256-byte streams fit exactly in 040..43F; VRAM_TABLE/OAM stay owned.
    lw s4, HCOMP_ROW_FIXED_SRC
    sll t0, k0, 1
    add s4, s4, t0
    li t6, 64
    li t7, SCRN_DATA
    andi t8, v0, 0xF0
#if SODIUM64_HCOMP_MASK_SCAN
    // F2==0 owns row colors in TILE_TABLE's upper half, so the unchanged
    // F0==0 fast path never scans it. F0!=0 owns two exact mask arrays.
    beqz t8, hcomp_masks_flat
    li t9, 63
    lhu t0, TILE_TABLE
    addi a0, t0, 1
    andi a0, a0, 0xFFFE // A mask lane is exactly 0000 or FFFF.
    bnez a0, hcomp_batch_mode_ready
    mtc2 t0, $v04, 0
    lhu t0, TILE_TABLE + 512
    addi a0, t0, 1
    andi a0, a0, 0xFFFE
    bnez a0, hcomp_batch_mode_ready
    mtc2 t0, $v05, 0
    vor $v04, $v31, $v04, 8
    vor $v05, $v31, $v05, 8
    li a0, TILE_TABLE
    li a1, TILE_TABLE + 512
    // VNE must start without inherited VCO; each comparison retires it.
    vge $v06, $v31, $v31, 0
hcomp_mask_scan:
    lqv $v00, 0, 0, a0
    lqv $v01, 0, 512, a0
    vxor $v00, $v00, $v04, 0
    vxor $v01, $v01, $v05, 0
    vor $v00, $v00, $v01, 0
    vne $v06, $v00, $v31, 0
    cfc2 t0, $1
    andi t0, t0, 0xFF
    bnez t0, hcomp_batch_mode_ready
    addi a0, a0, 16
    bne a0, a1, hcomp_mask_scan
    nop
    move t8, zero
    b hcomp_masks_wide
    nop
hcomp_masks_flat:
    vor $v04, $v21, $v31, 0
    vor $v05, $v21, $v31, 0
hcomp_masks_wide:
    li t6, 256
    li t7, TILE_TABLE
    li t9, 255
#else
    bnez t8, hcomp_batch_mode_ready
    li t9, 63
    li t6, 256
    li t7, TILE_TABLE
    li t9, 255
    vor $v04, $v21, $v31, 0
    vor $v05, $v21, $v31, 0
#endif
hcomp_batch_mode_ready:
    sll t0, t6, 1
    add t2, t7, t0 // Winner stream; batch-local pointer constants.
    add t3, t7, t6 // Sub stream and exclusive Main vector end.
    add t4, t2, t6 // Presence stream.
#if SODIUM64_HCOMP_FULL_ROW_MATH
hcomp_fullrow_admission:
    // Uniform masks are already broadcast. Variable Sub alone borrows the
    // dirty cache table, preserving it byte-exact before any stream DMA.
    bnez t8, hcomp_fullrow_mode_ready
    andi t0, v0, 2
    beqz t0, hcomp_fullrow_mode_ready
    lbu t0, HCOMP_EFFECTIVE_TS
    beqz t0, hcomp_fullrow_mode_ready
    li a0, VRAM_TABLE
    li a1, HCOMP_MATH_VRAM_BACKUP
    jal 0xA4001F08
    li a2, 1023
    li t6, 512
    li t9, 511
    // Winner remains +512; whole-row Sub/Presence occupy the borrowed table.
    addi t3, t7, 1024
    addi t4, t2, 1024
hcomp_fullrow_mode_ready:
    sub t5, t3, t7 // Uniform Sub offset: 256 wide, 1024 full row.
#endif
#else
    sll s4, k0, 1
    addi s4, s4, TILE_TABLE + 512
#endif
hcomp_row:
    andi t0, v0, 0xF2
    bnez t0, hcomp_row_color_ready
    nop
#if SODIUM64_HCOMP_WIDE_MATH
    // Preserve the former F2==0 row-fixed policy. Read the same queue row
    // through an aligned eight-byte DMA before wide winner data overwrites
    // setup's row-color staging. Source2+absent-Sub keeps section fixed.
    li a0, SCRN_DATA
    li t0, -8
    and a1, s4, t0
    jal 0xA4001F40
    li a2, 7
    andi t0, s4, 6
    lhu gp, SCRN_DATA(t0)
#else
    lhu gp, 0(s4)
#endif
    mtc2 gp, $v22, 0
    vor $v22, $v31, $v22, 8
hcomp_row_color_ready:
    li s6, 0
hcomp_batch:
    // Four 32-pixel inputs occupy only SCRN_DATA..CHAR_DATA+127.
#if SODIUM64_HCOMP_WIDE_MATH
    move a0, t7
#else
    li a0, SCRN_DATA
#endif
    move a1, s0
    jal 0xA4001F40
#if SODIUM64_HCOMP_WIDE_MATH
    move a2, t9
    move a0, t2
#else
    li a2, 63
    li a0, SCRN_DATA + 128
#endif
    move a1, s2
    jal 0xA4001F40
#if SODIUM64_HCOMP_WIDE_MATH
    move a2, t9
#else
    li a2, 63
#endif
    andi t0, v0, 2
    beqz t0, hcomp_optional_sub_done
    lbu t0, HCOMP_EFFECTIVE_TS
    beqz t0, hcomp_optional_sub_done
    nop
#if SODIUM64_HCOMP_WIDE_MATH
    move a0, t3
#else
    li a0, SCRN_DATA + 64
#endif
    move a1, s1
    jal 0xA4001F40
#if SODIUM64_HCOMP_WIDE_MATH
    move a2, t9
#if SODIUM64_SUB_ALPHA
    bnez s8, hcomp_optional_sub_done
    move a0, t4
#else
    move a0, t4
#endif
#else
    li a2, 63
    li a0, SCRN_DATA + 192
#endif
    move a1, s3
    jal 0xA4001F40
#if SODIUM64_HCOMP_WIDE_MATH
    move a2, t9
#else
    li a2, 63
#endif
hcomp_optional_sub_done:
#if SODIUM64_HCOMP_WIDE_MATH
    move s5, t7
#if SODIUM64_HCOMP_FULL_ROW_MATH
    add a3, t7, t6 // Main end is independent from the full-row Sub base.
#endif
#else
    li s5, SCRN_DATA
#endif
hcomp_vector:
    // Eight independent pixels. Renderer constants v23..v31 stay intact.
#if SODIUM64_HCOMP_WIDE_MATH
    bnez t8, hcomp_vector_narrow
    nop
#if SODIUM64_HCOMP_FULL_ROW_MATH
    lqv $v00, 0, 0, s5
    add a0, s5, t5
    lqv $v01, 0, 0, a0
    lqv $v02, 0, 512, s5
    lqv $v03, 0, 512, a0
#else
    lqv $v00, 0, 0, s5
    lqv $v01, 0, 256, s5
    lqv $v02, 0, 512, s5
    lqv $v03, 0, 768, s5
#endif
    b hcomp_math_mask_ready
    nop
hcomp_vector_narrow:
#endif
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
#if SODIUM64_SUB_ALPHA
    jal hcomp_alpha_inputs
#endif
    vand $v00, $v00, $v04, 0
    // Zero eligibility while retiring any incoming vector carry bits.
    vge $v07, $v31, $v31, 0
#if SODIUM64_ELIGIBILITY_TAGS
    // Main publishes only 0400 (forbidden) or 0C00 (permitted). The existing
    // absent-Sub constant v16[1]=0400 lets eligibility use one comparison
    // without changing Setup or the exact packed RGB555 kernel below.
    veq $v06, $v02, $v16, 9
    vmrg $v07, $v31, $v21, 0
#else
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
#endif
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
#include "rsp_hcomp_packed_math.inc"
hcomp_vector_output:
    vor $v00, $v00, $v15, 8
    sqv $v00, 0, 0, s5
    addi s6, s6, 16
    addi s5, s5, 16
#if SODIUM64_HCOMP_WIDE_MATH
#if SODIUM64_HCOMP_FULL_ROW_MATH
    bne s5, a3, hcomp_vector
#else
    bne s5, t3, hcomp_vector
#endif
#else
    li t0, SCRN_DATA + 64
    bne s5, t0, hcomp_vector
#endif
    nop
#if SODIUM64_HCOMP_WIDE_MATH
    move a0, t7
#else
    li a0, SCRN_DATA
#endif
    move a1, s0
    jal 0xA4001F08
#if SODIUM64_HCOMP_WIDE_MATH
    move a2, t9
    add s0, s0, t6
    add s1, s1, t6
    add s2, s2, t6
    add s3, s3, t6
#else
    li a2, 63
    addi s0, s0, 64
    addi s1, s1, 64
    addi s2, s2, 64
    addi s3, s3, 64
#endif
    li t0, 512
    bne s6, t0, hcomp_batch
    nop
    addi s0, s0, 48
    addi s1, s1, 48
    addi s2, s2, 48
    addi s3, s3, 48
#if !SODIUM64_SUB_ALPHA
    addi s4, s4, 2
#endif
    addi s7, s7, -1
    bnez s7, hcomp_row
#if SODIUM64_SUB_ALPHA
    addi s4, s4, 2
#else
    nop
#endif
hcomp_section_done:
    // shared_decode expects its upper-plane accumulator empty on entry.
    vand $v20, $v31, $v31, 0
#if SODIUM64_HCOMP_FULL_ROW_MATH
hcomp_fullrow_restore:
    // All normal Math exits restore the historical dirty bits before the
    // Phase loader can admit Main, Mode7, another band or frame completion.
    li t0, 512
    bne t6, t0, hcomp_return_phase
    li a0, VRAM_TABLE
    li a1, HCOMP_MATH_VRAM_BACKUP
    jal 0xA4001F40
    li a2, 1023
#endif
hcomp_return_phase:
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, 0x1778
.org (0x760 - 0x3A8)
hcomp_screen_switch:
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, 0x1760
#if SODIUM64_SUB_ALPHA
.org (0x76C - 0x3A8)
hcomp_alpha_inputs:
    beqz s8, hcomp_alpha_inputs_return
    nop
    vand $v03, $v01, $v15, 8
    vmudn $v03, $v03, $v16, 10
    vaddc $v03, $v03, $v16, 9
hcomp_alpha_inputs_return:
    jr ra
    nop
#endif
.org (0x788 - 0x3A8)
draw_mode7_entry:
    j 0xA4001F78
    li t9, 0x1788
