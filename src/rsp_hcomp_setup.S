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
#if SODIUM64_ADAPTIVE_SPANS
    lbu t2, HCOMP_EFFECTIVE_TS
    sltu t2, zero, t2
    sub t4, zero, t2
    andi t4, t4, 0x52C // Original and worker decoders have identical spacing.
    lui t0, 0xA400
    ori t1, t0, 0x1B3C
    sub t1, t1, t4
    sw t1, SHARED_JUMPS
    ori t1, t0, 0x1B20
    sub t1, t1, t4
    sw t1, SHARED_JUMPS + 4
    ori t1, t0, 0x1AE8
    sub t1, t1, t4
    sw t1, SHARED_JUMPS + 8
    lw t3, OVERLAY_DECODER_ORIGINAL_SRC
    andi t0, t3, 1
    xor t3, t3, t0
    beqz t2, hcomp_context_dma
    move a1, t3
    lw a1, OVERLAY_MAIN_SRC
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    addi a1, a1, 0x727 // Strip known Main bank tag1, then reach AD0.
#else
    addi a1, a1, 0x728
#endif
hcomp_context_dma:
    li a0, 0x1AD0
    jal 0xA4001F40
    li a2, 183 // AD0..B88 includes immutable boundary delay-slot words.
    or t3, t3, t2
    sw t3, OVERLAY_DECODER_ORIGINAL_SRC
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, RSP_CONTEXT_PHASE_RETURN
#else
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
#endif

.org (0x628 - 0x3A8)
hcomp_vram_snapshot:
    // Each dirty byte owns one64-byte VRAM block. Keep only one bit per
    // 1KiB copy group in t8/t9, before TILE_TABLE becomes DMA scratch.
    // VRAM_TABLE retains the exact historical per-layer dirty-bit OR.
    li a0, TILE_TABLE
    lw a1, DIRTY_PTR(sp)
    jal 0xA4001F40
    li a2, 0x3FF
    li t1, VRAM_TABLE
    li t2, TILE_TABLE
    move t8, zero
    move t9, zero
    // A previous arithmetic bank may leave VCO; clear it before VNE so
    // clean zero lanes cannot inherit old subtraction carry/borrow bits.
    vge $v02, $v31, $v31, 0
hcomp_vram_dirty_bitmap:
    lqv $v00, 0, 0, t1
    lqv $v01, 0, 0, t2
    vor $v00, $v00, $v01, 0
    sqv $v00, 0, 0, t1
    vne $v02, $v01, $v31, 0
    cfc2 t0, $1
    andi t0, t0, 0xFF
    sltu t0, zero, t0
    srl t3, t8, 31
    sll t9, t9, 1
    or t9, t9, t3
    sll t8, t8, 1
    or t8, t8, t0
    addi t2, t2, 16
    li t3, VRAM_TABLE
    bne t2, t3, hcomp_vram_dirty_bitmap
    addi t1, t1, 16
    // Startup must initialize the complete snapshot even when every dirty
    // byte is zero. This state is independent of dirty bits and OAM caches.
    lw t0, HCOMP_VRAM_SNAPSHOT_READY
    bnez t0, hcomp_vram_snapshot_ready
    lw t4, VRAM_ADDRS + 4
    li t8, -1
    li t9, -1
hcomp_vram_snapshot_ready:
    lw t3, VRAM_ADDRS
    li t1, 0xFC00
    li a0, TILE_TABLE
    li a2, 0x3FF
hcomp_vram_copy_group:
    andi t0, t8, 1
    beqz t0, hcomp_vram_group_done
    add a1, t4, t1
    jal 0xA4001F40
    nop
    jal 0xA4001F08
    add a1, t3, t1
hcomp_vram_group_done:
    srl t8, t8, 1
    sll t0, t9, 31
    or t8, t8, t0
    srl t9, t9, 1
    bnez t1, hcomp_vram_copy_group
    addi t1, t1, -0x400
    li t0, 1
    sw t0, HCOMP_VRAM_SNAPSHOT_READY
    // The R4300 may write guest VRAM only after every selected copy retired.
    mtc0 zero, COP0_SEMAPHORE
#if SODIUM64_BG_SPANS
    // No cache/map lifetime is live yet. Initialize the dedicated wrapping
    // render tile once per frame, without an extra overlay round trip.
bg_span_initialize:
    li t0, 0x35480200
    sw t0, TEXTURE
    li t0, 0x04058030 // Tile4: T mask6/mirror; S mask3 without mirror.
    sw t0, TEXTURE + 4
    lui t0, 0x3200
    sw t0, TEXTURE + 8
    li t0, 0x0401F01F
    sw t0, TEXTURE + 12
    li a0, TEXTURE
    jal 0xA4001F5C
    li a1, TEXTURE + 16
#endif
    lw a1, OVERLAY_MAIN_SRC
    j 0xA4001F7C
    li t9, 0x109C

.org (0x760 - 0x3A8)
hcomp_screen_switch:
    b hcomp_setup_copy
    nop
.org (0x788 - 0x3A8)
draw_mode7_entry:
    j 0xA4001F78
    li t9, 0x1788
