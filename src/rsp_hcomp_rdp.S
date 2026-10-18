/* Exact binary HALF composition, opt-in. BG1-only Sub with a zero fixed fallback
 * and uniform COLOR masks only. Winner AND presence excludes absent Sub:
 * absent Sub suppresses HALF, and full Main +/- zero leaves Main unchanged.
 * Unsupported epochs enter the byte-identical packed Math bank.
 */
#include <rsp.inc>
#include <rdpq_macros.h>
#include "defines.h"
#define CMDS TILE_TABLE
.data
// CPU binds the immutable fallback pointer before starting the RSP. The CPU
// linked object must place this descriptor exactly 1000 bytes after its text.
.word 0, 0
// Both 32x32 RGBA16 operands fill the 4 KiB TMEM. Two-cycle RGB fetch and
// the measured 251/256 correction produce floor((a +/- b)/2) in RGB5.
.dword 0x2700000000000000
.dword 0x2F100CF000000214
.dword 0x3F10011700000000
.dword 0x2D03000000430000
.dword 0x3A000000FFFFFF80
.dword 0x3B000000FFFFFFFB
// The same official macro/formula used by the successful physical probe.
.dword (0x3C00000000000000 | (RDPQ_COMBINER2((TEX0,TEX1,PRIM_ALPHA,TEX1),(0,0,0,ONE),(COMBINED,0,ENV_ALPHA,0),(0,0,0,ONE)) & 0x00FFFFFFFFFFFFFF))
.dword 0x3E00000000000000
.dword 0x2E00000010000000
.dword 0x2800000000000000
.dword 0x3D10011700000000
.dword 0x3510100007080200
.dword 0x2600000000000000
.dword 0x340000000707C07C
.dword 0x2700000000000000
.dword 0x3510100000080200
.dword 0x320000000007C07C
.dword 0x2800000000000000
.dword 0x3D10011700000000
.dword 0x3510110007080200
.dword 0x2600000000000000
.dword 0x340000000707C07C
.dword 0x2700000000000000
.dword 0x3510110001080200
.dword 0x320000000107C07C
.dword 0x2400000000000000
.dword 0x0000000004000400
.dword 0x2700000000000000
.text
draw_bg:
    j 0xA4001F90
    move v0, t0
hcomp_entry:
    andi t0, v0, 0x53 // real Sub; neither direct color nor inside-only COLOR.
    li t1, 2
    bne t0, t1, hcomp_rdp_fallback
    andi t0, v1, 0x40
    beqz t0, hcomp_rdp_fallback
    lbu t0, WOBJSEL
    andi t0, t0, 0xA0
    bnez t0, hcomp_rdp_fallback
    lhu t0, SUB_COLOR
    andi t0, t0, 0xFFFE // zero RGB, independent of the opaque alpha bit.
    bnez t0, hcomp_rdp_fallback
    lbu t0, HCOMP_EFFECTIVE_TS
    addi t0, t0, -1 // BG1 presence is exactly 0400/0C00; other tags differ.
    bnez t0, hcomp_rdp_fallback
    lw t0, HCOMP_DIAG_COMPOSE_LIMIT
    bnez t0, hcomp_rdp_fallback
    lw s4, OVERLAY_HCOMP_MATH_SRC
    li t0, -8
    and s4, s4, t0
    // Setup has already fenced Main/Sub/Z. Only retired winner pixels are
    // rewritten; presence, VRAM table, OAM and palette history remain intact.
    lw s2, HCOMP_BAND_BASES + 4
    lw s3, HCOMP_BAND_BASES + 8
    lw s5, HCOMP_BAND_ROWS
hcomp_rdp_mask_row:
    li a0, TILE_TABLE + 512
    move a1, s3
    jal 0xA4001F40
    li a2, 511
    // A fully present BG1 row already has the correct winner gate. Avoid
    // reading and rewriting its entire depth row; absent rows retain AND.
    vge $v02, $v31, $v31, 0
    li t1, TILE_TABLE + 512
    li t2, TILE_TABLE + 1024
hcomp_rdp_presence_scan:
    lqv $v01, 0, 0, t1
    veq $v02, $v01, $v16, 9
    cfc2 t0, $1
    andi t0, t0, 0xFF
    bnez t0, hcomp_rdp_mask_needed
    addi t1, t1, 16
    bne t1, t2, hcomp_rdp_presence_scan
    nop
    b hcomp_rdp_mask_advance
    nop
hcomp_rdp_mask_needed:
    li a0, TILE_TABLE
    move a1, s2
    jal 0xA4001F40
    li a2, 511
    li t1, TILE_TABLE
    li t2, TILE_TABLE + 512
hcomp_rdp_mask_vector:
    lqv $v00, 0, 0, t1
    lqv $v01, 0, 512, t1
    vand $v00, $v00, $v01, 0
    sqv $v00, 0, 0, t1
    addi t1, t1, 16
    bne t1, t2, hcomp_rdp_mask_vector
    nop
    li a0, TILE_TABLE
    move a1, s2
    jal 0xA4001F08
    li a2, 511
hcomp_rdp_mask_advance:
    addi s2, s2, 560
    addi s3, s3, 560
    addi s5, s5, -1
    bnez s5, hcomp_rdp_mask_row
    nop
    li a0, CMDS
    addi a1, s4, 1008
    jal 0xA4001F40
    li a2, 223
    lw t0, FRAMEBUFFER(sp)
    addi t0, t0, -4480
    sw t0, CMDS + 20
    lw t0, HCOMP_PROOF_RDP_CMDS + 20
    sw t0, CMDS + 60
    sw s0, CMDS + 84
    lw t0, HCOMP_BAND_BASES
    sw t0, CMDS + 148
    andi t0, v1, 0x80
    beqz t0, hcomp_rdp_add
    lw t0, CMDS + 52
    lui t1, 2
    ori t1, t1, 0x8000 // C0 RGB D: TEX1(2) -> ZERO(7), bits15..17.
    or t0, t0, t1
    sw t0, CMDS + 52
hcomp_rdp_add:
    lw t1, HCOMP_BAND_Y
    sll t1, t1, 2
    sh t1, CMDS + 26
    lw t2, HCOMP_BAND_ROWS
    sll t2, t2, 2
    add t2, t2, t1
    sh t2, CMDS + 30
    move s6, zero // tile row, local to the compact band.
hcomp_rdp_tile_row:
    lw gp, HCOMP_BAND_ROWS
    sub gp, gp, s6
    sltiu t0, gp, 33
    bnez t0, hcomp_rdp_height_ready
    nop
    li gp, 32
hcomp_rdp_height_ready:
    addi t0, gp, -1
    sll t0, t0, 2
    lui t1, 7
    ori t1, t1, 0xC000
    or t0, t0, t1
    sw t0, CMDS + 132
    lui t1, 0x0100
    or t0, t0, t1
    sw t0, CMDS + 196
    move s7, zero
hcomp_rdp_tile:
    sll t1, s7, 2
    sll t2, s6, 2
    sll t3, t1, 12
    or t3, t3, t2
    lui t4, 0x3400
    or t4, t4, t3
    sw t4, CMDS + 104
    sw t4, CMDS + 168
    addi t1, t1, 124
    addi t2, gp, -1
    add t2, t2, s6
    sll t2, t2, 2
    sll t1, t1, 12
    or t1, t1, t2
    lui t2, 0x0700
    or t1, t1, t2
    sw t1, CMDS + 108
    sw t1, CMDS + 172
    addi t1, s7, 12
    lw t2, HCOMP_BAND_Y
    add t2, t2, s6
    sll t3, t1, 14
    sll t4, t2, 2
    or t3, t3, t4
    sw t3, CMDS + 204
    addi t1, t1, 32
    add t2, t2, gp
    sll t1, t1, 14
    sll t2, t2, 2
    or t1, t1, t2
    lui t2, 0x2400
    or t1, t1, t2
    sw t1, CMDS + 200
    li a0, CMDS
    jal 0xA4001F5C
    li a1, CMDS + 224
    // The resident sender retires every command fetch before scratch reuse.
    // PipeSync serializes GPU state/TMEM reuse in command order. Adjacent
    // tiles read disjoint, untouched Main words, so no per-tile CPU fence or
    // SyncFull is needed. The final palette fence retires the whole band.
    addi s7, s7, 32
    li t0, 256
    bne s7, t0, hcomp_rdp_tile
    nop
    add s6, s6, gp
    lw t0, HCOMP_BAND_ROWS
    bne s6, t0, hcomp_rdp_tile_row
    nop
    // TMEM was completely overwritten. Restore the painter's descriptors,
    // complete historical TLUT, and texture combiner before Phase can draw.
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
hcomp_rdp_restore_wait:
    mfc0 t0, COP0_DP_STATUS
    andi t0, t0, 0x770
    bnez t0, hcomp_rdp_restore_wait
    nop
    vand $v20, $v31, $v31, 0
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, 0x1778
hcomp_rdp_fallback:
    lw a1, OVERLAY_HCOMP_MATH_SRC
    li t0, -8
    and a1, a1, t0
    addi a1, a1, 1000
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
