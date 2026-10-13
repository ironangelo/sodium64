/* Lossless Main backdrop rows. All scalar/nonindexed/clipped/math-backdrop
 * policies retain the old fill. TILE_TABLE is restored before any layer;
 * RDP lists remain in their original owned commands, never borrowed scratch.
 */
#include <rsp.inc>
#include "defines.h"
#if !SODIUM64_BACKDROP_ROWS || !SODIUM64_SUB_ALPHA
#error "Backdrop rows require the isolated Sub-alpha renderer"
#endif
#define BACKUP HCOMP_CGRAM_SIDEBAND_QUEUE1
#if BACKUP + 1024 > HCOMP_CGRAM_SIDEBAND_QUEUE2
#error "Backdrop TILE_TABLE backup must fit the retired Q1 sideband"
#endif
.data
.word 0, 0 // CPU publishes the current phase source, never an old build address.
.text
draw_bg:
    j 0xA4001F90
    move v0, t0
hcomp_entry:
    move s4, a1
    lb t0, STAT_FLAGS
    bltz t0, hcomp_backdrop_scalar
    lbu t0, HCOMP_SCREEN
    beqz t0, hcomp_backdrop_scalar
    lbu t0, CGWSEL
    andi t0, t0, 0xF3
    bnez t0, hcomp_backdrop_scalar
    lbu t0, CGADSUB
    andi t0, t0, 0x20
    bnez t0, hcomp_backdrop_scalar
    lbu t0, BG_MODE
    andi t0, t0, 7
    sltiu t0, t0, 2
    beqz t0, hcomp_backdrop_scalar
    lw t0, HCOMP_DIAG_COMPOSE_LIMIT
    bnez t0, hcomp_backdrop_scalar
    sltu t0, k0, k1
    beqz t0, hcomp_backdrop_scalar
    sltiu t0, k1, 241
    beqz t0, hcomp_backdrop_scalar
    sltiu t0, k0, 240
    beqz t0, hcomp_backdrop_scalar
    nop
    // A previous epoch may retain decoded cache tags here. Preserve all of
    // them; the dirty VRAM table and OAM remain outside this exact extent.
    li a0, TILE_TABLE
    li a1, BACKUP
    jal 0xA4001F08
    li a2, 1023
    li a0, TILE_TABLE
    li a1, HCOMP_ROW_MAIN_QUEUE1
    sll t0, sp, 7 // queue parity0/4 selects the two512-byte owners.
    add a1, a1, t0
    jal 0xA4001F40
    li a2, 511
    move s5, k0
hcomp_backdrop_run:
    sll t0, s5, 1
    lhu gp, TILE_TABLE(t0)
    addi s6, s5, 1
hcomp_backdrop_find_end:
    beq s6, k1, hcomp_backdrop_emit_run
    sll t0, s6, 1
    lhu t0, TILE_TABLE(t0)
    bne t0, gp, hcomp_backdrop_emit_run
    nop
    b hcomp_backdrop_find_end
    addi s6, s6, 1
hcomp_backdrop_emit_run:
    andi t0, gp, 0x3E
    sll t0, t0, 10
    andi t1, gp, 0x7C0
    sll t1, t1, 13
    or t0, t0, t1
    andi t1, gp, 0xF800
    sll t1, t1, 16
    or t0, t0, t1
    ori t0, t0, 0xFF
    sw t0, RDP_FILL + 20
    lw t2, FB_OFFSET(sp)
    add t0, s5, t2
    add t1, s6, t2
    sll t0, t0, 2
    sll t1, t1, 2
    sh t0, RDP_FILL + 10
    sh t1, RDP_FILL + 14
    sh t0, RDP_FILL + 38
    sh t1, RDP_FILL + 34
    li a0, RDP_FILL + 8
    jal 0xA4001F5C
    li a1, RDP_WINDOW
    bne s6, k1, hcomp_backdrop_run
    move s5, s6
    // Restore the complete band scissor/fill geometry for its layer/window
    // consumers. Each list has retired before these command writes.
    lw t2, FB_OFFSET(sp)
    add t0, k0, t2
    add t1, k1, t2
    sll t0, t0, 2
    sll t1, t1, 2
    sh t0, RDP_FILL + 10
    sh t1, RDP_FILL + 14
    sh t0, RDP_FILL + 38
    sh t1, RDP_FILL + 34
    li a0, TILE_TABLE
    li a1, BACKUP
    jal 0xA4001F40
    li a2, 1023
    b hcomp_backdrop_layers
    nop
hcomp_backdrop_scalar:
    li a0, RDP_FILL + 8
    jal 0xA4001F5C
    li a1, RDP_WINDOW
hcomp_backdrop_layers:
    lb t4, STAT_FLAGS
    bltz t4, hcomp_backdrop_blank_done
    nop
    sw zero, PRIO_CHECKS
    sw zero, PRIO_CHECKS + 4
    lbu s3, BG_MODE
    andi s3, s3, 0xF
    sll s3, s3, 4
    lw a1, OVERLAY_MAIN_SRC
    j 0xA4001F7C
    li t9, 0x1370
hcomp_backdrop_blank_done:
    li a0, SCRN_DATA
    addi a1, s4, 1000
    jal 0xA4001F40
    li a2, 7
    lw a1, SCRN_DATA
    j 0xA4001F7C
    li t9, 0x1778 // existing phase Math-return entry branches to band_done.
.org 1000
