/* Exact fixed-operand palette composition. The original palette is immutable;
 * three owned 2 KiB tables replace only winner scratch for this direct section.
 * Visible Sub, variable row fixed colors and nonflat COLOR keep packed Math.
 */
#include <rsp.inc>
#include "defines.h"
.data
.byte 0
.text
draw_bg:
    j 0xA4001F90
    move v0, t0
hcomp_tlut_generate:
    b hcomp_tlut_probe
    nop
hcomp_tlut_bind:
    b hcomp_tlut_bind_body
    nop
hcomp_tlut_restore:
    b hcomp_tlut_restore_body
    nop

hcomp_tlut_probe:
    lbu v0, CGWSEL
    andi t0, v0, 0xF1
    bnez t0, hcomp_tlut_reject
    lb t0, STAT_FLAGS
    bltz t0, hcomp_tlut_reject
    lw t0, HCOMP_DIAG_COMPOSE_LIMIT
    bnez t0, hcomp_tlut_reject
    slt t0, k0, k1
    beqz t0, hcomp_tlut_reject
    sltiu t0, k0, 256
    beqz t0, hcomp_tlut_reject
    sltiu t0, k1, 256
    beqz t0, hcomp_tlut_reject
    lbu v1, CGADSUB
    andi t0, v0, 2
    beqz t0, hcomp_tlut_fixed_rows
    lhu gp, SUB_COLOR
    lbu t0, TS
    andi t0, t0, 0x1F
    bnez t0, hcomp_tlut_reject
    move t1, zero // Absent Sub suppresses HALF, independent of row queue.
    b hcomp_tlut_constants
    nop
hcomp_tlut_fixed_rows:
    // The CPU's coalesced section can contain COLDATA writes. Prove all
    // owned rows equal rather than using SUB_COLOR or a live DMEM sample.
    li a0, TILE_TABLE
    lw a1, HCOMP_ROW_FIXED_SRC
    jal 0xA4001F40
    li a2, 511
    sll t2, k0, 1
    addi t2, t2, TILE_TABLE
    sll t3, k1, 1
    addi t3, t3, TILE_TABLE
    lhu gp, 0(t2)
hcomp_tlut_row_scan:
    lhu t0, 0(t2)
    bne t0, gp, hcomp_tlut_reject
    addi t2, t2, 2
    bne t2, t3, hcomp_tlut_row_scan
    nop
    andi t1, v1, 0x40
    sltu t1, zero, t1
    sub t1, zero, t1
hcomp_tlut_constants:
    mtc2 t1, $v13, 0
    vor $v13, $v31, $v13, 8
    mtc2 gp, $v01, 0
    vor $v01, $v31, $v01, 8
    vnor $v07, $v31, $v31, 0
    li t0, 1
    mtc2 t0, $v15, 0
    li t0, 0x8000
    mtc2 t0, $v16, 0
    li t0, 0x0800
    mtc2 t0, $v16, 4
    li t0, 2
    mtc2 t0, $v16, 6
    li t0, 0x0421
    mtc2 t0, $v19, 0
    li t0, 0x8420
    mtc2 t0, $v19, 2
    li t0, 0x7BDE
    mtc2 t0, $v19, 4
    // Retire every outstanding source reader before reusing winner scratch.
    li a0, HCOMP_TEXTURE_FENCE
    jal 0xA4001F5C
    addi a1, a0, 8
hcomp_tlut_workspace_wait:
    mfc0 t0, COP0_DP_STATUS
    andi t0, t0, 0x770
    bnez t0, hcomp_tlut_workspace_wait
    nop
    lw s0, PALETTE_PTR(sp)
    li s1, HCOMP_TLUT_BASE
    addi s2, s1, 0x800
    addi s3, s2, 0x800
    move s4, zero
hcomp_tlut_chunk:
    li a0, TILE_TABLE
    move a1, s0
    jal 0xA4001F40
    li a2, 511
    move a1, s1
    jal 0xA4001F08
    nop // Base table preserves source bits, including index0 alpha.
    li s5, TILE_TABLE
    li s6, TILE_TABLE + 512
hcomp_tlut_vector:
    lqv $v00, 0, 0, s5
    jal hcomp_tlut_apply_alpha
    nop
    sqv $v00, 0, 0, s5
    addi s5, s5, 16
    bne s5, s6, hcomp_tlut_vector
    nop
    bnez s4, hcomp_tlut_write_bg
    li a0, TILE_TABLE
    // Texture index0 is transparency, never the separately typed backdrop.
    move a1, s1
    jal 0xA4001F40
    li a2, 7
hcomp_tlut_write_bg:
    move a1, s2
    jal 0xA4001F08
    li a2, 511
    // OBJ palette groups0..3 never perform math; groups4..7 use CGADSUB10.
    li t0, 1536
    bne s4, t0, hcomp_tlut_obj_base
    andi t0, v1, 0x10
    bnez t0, hcomp_tlut_write_obj
    nop
hcomp_tlut_obj_base:
    move a1, s1
    jal 0xA4001F40
    li a2, 511
hcomp_tlut_write_obj:
    move a1, s3
    jal 0xA4001F08
    li a2, 511
    addi s0, s0, 512
    addi s1, s1, 512
    addi s2, s2, 512
    addi s3, s3, 512
    addi s4, s4, 512
    li t0, 2048
    bne s4, t0, hcomp_tlut_chunk
    nop
    // Main backdrop has its own typed color. Palette entry0 remains zero.
    andi t0, v1, 0x20
    beqz t0, hcomp_tlut_install
    lhu t0, MAIN_COLOR
    mtc2 t0, $v00, 0
    vor $v00, $v31, $v00, 8
    jal hcomp_tlut_apply_alpha
    nop
    mfc2 t0, $v00, 0
    sh t0, MAIN_COLOR
hcomp_tlut_install:
    // Retired bootstrap000..037 is the shared palette-class dispatcher.
    // DMA length55 rounds to56, preserving bootstrap038 and draw_frame03C.
    lw a1, OVERLAY_HCOMP_TLUT_SRC
    li t0, -8
    and a1, a1, t0
    addi a1, a1, (hcomp_tlut_bind_stub - draw_bg)
    li a0, 0x1000
    jal 0xA4001F40
    li a2, 55
    li t0, 0x80
    sb t0, HCOMP_TLUT_CLASS
    li t0, 3
    sw t0, HCOMP_BAND_RAW
    sw zero, HCOMP_OBJ_ADAPTIVE
    sw k1, HCOMP_FAST_END
hcomp_tlut_reject:
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, 0x1768

hcomp_tlut_apply_alpha:
    vand $v17, $v00, $v15, 8
#define hcomp_channels_start hcomp_tlut_kernel
#define hcomp_packed_add hcomp_tlut_packed_add
#define hcomp_packed_select hcomp_tlut_packed_select
#include "rsp_hcomp_packed_math.inc"
#undef hcomp_channels_start
#undef hcomp_packed_add
#undef hcomp_packed_select
hcomp_tlut_kernel_end:
    vor $v00, $v00, $v17, 0
    jr ra
    nop

hcomp_tlut_bind_body:
    lw t0, SCRN_DATA
    sb t0, HCOMP_TLUT_CLASS
    andi t0, t0, 3
    addi t0, t0, -1
    sll t0, t0, 11
    li a1, HCOMP_TLUT_BASE
    add a1, a1, t0
    addi s3, s3, -1 // No primitive drawn in this pass before the class gate.
    lw t5, OVERLAY_MAIN_SRC
    b hcomp_tlut_palette_submit
    li t6, 0x1370
hcomp_tlut_restore_body:
    sb zero, HCOMP_TLUT_CLASS
    lw a1, PALETTE_PTR(sp)
    lw t5, OVERLAY_HCOMP_SRC
    li t6, 0x1778
hcomp_tlut_palette_submit:
    sw a1, RDP_FRAME + 12
    li a0, HCOMP_PROOF_RDP_CMDS
    jal 0xA4001F5C
    addi a1, a0, 8 // PipeSync retires prior primitives before TMEM changes.
    li a0, RDP_FRAME + 8
    jal 0xA4001F5C
    li a1, RDP_FILL + 8 // TextureImage + SyncLoad + palette LoadBlock.
    move a1, t5
    j 0xA4001F7C
    move t9, t6

.balign 8
hcomp_tlut_bind_stub:
    // Copied to IMEM000. External relative branches use runtime PCs.
    lw a1, 4(a0)
    srl a1, a1, 28
    .word BEQ(ZERO, A1, ((0xF70 - 0x00C) >> 2))
    sltiu a1, a1, 5
    bnez a1, hcomp_tlut_stub_class_ready
    addi t0, t0, 1
    li t0, 3
hcomp_tlut_stub_class_ready:
    ori t0, t0, 0x80
    lbu a1, HCOMP_TLUT_CLASS
    .word BEQ(A1, T0, ((0xF70 - 0x028) >> 2))
    sw t0, SCRN_DATA
    lw a1, OVERLAY_HCOMP_TLUT_SRC
    j 0xA4001F7C
    li t9, 0x13B8
hcomp_tlut_bind_stub_end:

.org (0x788 - 0x3A8)
draw_mode7_entry:
    j 0xA4001F78
    li t9, 0x1788
