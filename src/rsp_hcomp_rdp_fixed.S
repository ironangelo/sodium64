/* Exact full arithmetic for a fixed RGB5 operand <=16 in every component.
 * Native probe proves the RDP's full add/sub in this nonwrapping range.
 * Setup's COLOR mask becomes disjoint scissors; the original winner tags
 * gate math. No VRAM/OAM/mask/source rewrites. Unsupported epochs retain
 * the complete old fixed-window/packed Math fallback chain.
 */
#include <rsp.inc>
#include <rdpq_macros.h>
#include "defines.h"
#if !SODIUM64_HCOMP_RDP_FIXED_MATH || !SODIUM64_ELIGIBILITY_TAGS
#error "RDP_FIXED_MATH requires eligibility tags"
#endif
#define CMDS TILE_TABLE
#define CC_ADD (0x3C00000000000000 | (RDPQ_COMBINER2((TEX0,0,PRIM_ALPHA,ENV),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)) & 0x00FFFFFFFFFFFFFF))
#define CC_SUB (0x3C00000000000000 | (RDPQ_COMBINER2((TEX0,ENV,PRIM_ALPHA,0),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)) & 0x00FFFFFFFFFFFFFF))
.data
.word 0, 0 // Owned fallback descriptor exactly 1000 bytes after bank text.
.dword 0x2700000000000000
.dword 0x2F100CF000000214
.dword 0x3F10011700000000
.dword 0x3A000000FFFFFFFF
.dword 0x3B000000000000FF
.dword CC_ADD
.dword 0x3E00000000000000
.dword 0x2E00000010000000
.dword 0x2800000000000000
.dword 0x3D10011700000000
.dword 0x3510100007080200
.dword 0x3510100000080200
.dword 0x320000000007C0FC
.dword 0x2600000000000000
.dword 0x340000000707C0FC
.dword 0x2700000000000000
.dword 0x2D00000000000000
.dword 0x2400000000000000
.dword 0x0000000004000400
.dword 0x2700000000000000
.text
draw_bg:
    j 0xA4001F90
    move v0, t0
hcomp_entry:
    move s4, a1 // Inner bank must use its own loader source for fallback.
    andi t0, v0, 0xC1
    bnez t0, hcomp_rdp_fixed_fallback
    andi t0, v1, 0x40
    bnez t0, hcomp_rdp_fixed_fallback
    andi t0, v0, 0xF2
    beqz t0, hcomp_rdp_fixed_fallback // Variable per-row COLDATA remains old Math.
    andi t0, v0, 2
    beqz t0, hcomp_rdp_fixed_operand
    lbu t0, HCOMP_EFFECTIVE_TS
    bnez t0, hcomp_rdp_fixed_fallback
    nop
hcomp_rdp_fixed_operand:
    lw t0, HCOMP_DIAG_COMPOSE_LIMIT
    bnez t0, hcomp_rdp_fixed_fallback
    lhu gp, SUB_COLOR
    srl t0, gp, 11
    sltiu t0, t0, 17
    beqz t0, hcomp_rdp_fixed_fallback
    srl t0, gp, 6
    andi t0, t0, 31
    sltiu t0, t0, 17
    beqz t0, hcomp_rdp_fixed_fallback
    srl t0, gp, 1
    andi t0, t0, 31
    sltiu t0, t0, 17
    beqz t0, hcomp_rdp_fixed_fallback
    li a0, CMDS
    addi a1, s4, 1008
    jal 0xA4001F40
    li a2, 159
    lw t0, FRAMEBUFFER(sp)
    addi t0, t0, -4480
    sw t0, CMDS + 20
    lw t0, HCOMP_PROOF_RDP_CMDS + 20
    sw t0, CMDS + 52
    sw s0, CMDS + 76
    andi t0, gp, 0xF800
    sll t0, t0, 16
    andi t1, gp, 0x7C0
    sll t1, t1, 13
    or t0, t0, t1
    andi t1, gp, 0x3E
    sll t1, t1, 10
    or t0, t0, t1
    ori t0, t0, 0xFF
    sw t0, CMDS + 36
    andi t0, v1, 0x80
    beqz t0, hcomp_rdp_fixed_add
    lw t0, CMDS + 40
    li t1, ((CC_ADD ^ CC_SUB) >> 32)
    xor t0, t0, t1
    sw t0, CMDS + 40
    lw t0, CMDS + 44
    li t1, ((CC_ADD ^ CC_SUB) & 0xFFFFFFFF)
    xor t0, t0, t1
    sw t0, CMDS + 44
hcomp_rdp_fixed_add:
    // Image/combiner/tile formats remain invariant for this complete epoch.
    // Submit them once; each later tile retains LoadSync/PipeSync ordering.
    li a0, CMDS
    jal 0xA4001F5C
    li a1, CMDS + 96
    move s6, zero
hcomp_rdp_fixed_row:
    lw gp, HCOMP_BAND_ROWS
    sub gp, gp, s6
    sltiu t0, gp, 65
    bnez t0, hcomp_rdp_fixed_height
    nop
    li gp, 64
hcomp_rdp_fixed_height:
    addi t0, gp, -1
    sll t0, t0, 2
    lui t1, 7
    ori t1, t1, 0xC000
    or t0, t0, t1
    sw t0, CMDS + 100
    // The preceding tile ends in PipeSync, so its render tile has retired
    // before this row changes TileSize. Empty masks have no tile readers.
    li a0, CMDS + 96
    jal 0xA4001F5C
    li a1, CMDS + 104
    move s1, zero // Byte offset into Setup's immutable per-column math mask.
hcomp_rdp_fixed_find:
    sltiu t0, s1, 512
    beqz t0, hcomp_rdp_fixed_next_row
    nop
    lhu t0, TILE_TABLE + 512(s1)
    bnez t0, hcomp_rdp_fixed_start
    move s2, s1
    addi s1, s1, 2
    b hcomp_rdp_fixed_find
    nop
hcomp_rdp_fixed_start:
    addi s1, s1, 2
    sltiu t0, s1, 512
    beqz t0, hcomp_rdp_fixed_span
    nop
    lhu t0, TILE_TABLE + 512(s1)
    bnez t0, hcomp_rdp_fixed_start
    nop
hcomp_rdp_fixed_span:
    srl s2, s2, 1
    srl s3, s1, 1 // Exclusive end; x=255 remains a valid pixel.
    addi t0, s2, 12
    sll t0, t0, 14
    lui t1, 0x2D00
    or t0, t0, t1
    lw t1, HCOMP_BAND_Y
    sll t1, t1, 2
    or t0, t0, t1
    sw t0, CMDS + 128
    addi t0, s3, 12
    sll t0, t0, 14
    lw t2, HCOMP_BAND_ROWS
    sll t2, t2, 2
    add t2, t2, t1
    or t0, t0, t2
    sw t0, CMDS + 132
    andi s7, s2, 0xE0
hcomp_rdp_fixed_tile:
    sll t1, s7, 2
    sll t2, s6, 2
    sll t3, t1, 12
    or t3, t3, t2
    lui t4, 0x3400
    or t4, t4, t3
    sw t4, CMDS + 112
    addi t1, t1, 124
    addi t2, gp, -1
    add t2, t2, s6
    sll t2, t2, 2
    sll t1, t1, 12
    or t1, t1, t2
    lui t2, 0x0700
    or t1, t1, t2
    sw t1, CMDS + 116
    addi t1, s7, 12
    lw t2, HCOMP_BAND_Y
    add t2, t2, s6
    sll t3, t1, 14
    sll t4, t2, 2
    or t3, t3, t4
    sw t3, CMDS + 140
    addi t1, t1, 32
    add t2, t2, gp
    sll t1, t1, 14
    sll t2, t2, 2
    or t1, t1, t2
    lui t2, 0x2400
    or t1, t1, t2
    sw t1, CMDS + 136
    li a0, CMDS + 104
    jal 0xA4001F5C
    li a1, CMDS + 160
    // Command fetch retirement plus ordered PipeSync protect scratch/TMEM.
    // Repeated grid tiles under disjoint scissors only use untouched pixels.
    addi s7, s7, 32
    slt t0, s7, s3
    bnez t0, hcomp_rdp_fixed_tile
    nop
    b hcomp_rdp_fixed_find
    nop
hcomp_rdp_fixed_next_row:
    add s6, s6, gp
    lw t0, HCOMP_BAND_ROWS
    bne s6, t0, hcomp_rdp_fixed_row
    nop
    li a0, RDP_INIT
    jal 0xA4001F5C
    li a1, RDP_INIT + 64
    li a0, RDP_FRAME + 8
    jal 0xA4001F5C
    li a1, RDP_FILL + 8
    li a0, RDP_FILL + 40
    jal 0xA4001F5C
    li a1, RDP_FILL + 56
    li a0, HCOMP_TEXTURE_FENCE
    jal 0xA4001F5C
    addi a1, a0, 8
hcomp_rdp_fixed_restore_wait:
    mfc0 t0, COP0_DP_STATUS
    andi t0, t0, 0x770
    bnez t0, hcomp_rdp_fixed_restore_wait
    nop
    vand $v20, $v31, $v31, 0
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, 0x1778
hcomp_rdp_fixed_fallback:
    addi a1, s4, 1000
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
