/*
    Copyright 2021-2025 Hydr8gon

    This file is part of sodium64.

    sodium64 is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published
    by the Free Software Foundation, either version 3 of the License,
    or (at your option) any later version.

    sodium64 is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with sodium64. If not, see <https://www.gnu.org/licenses/>.
*/

#include <rsp.inc>
#include "defines.h"

.data

// Empty values that are defined as macros
.byte 0:VRAM_ADDRS

// Frame values that aren't empty by default
vram_addrs: .word VRAM_BUFFER, 0 // Set by CPU
palette_ptr: .word PALETTE_QUEUE1, PALETTE_QUEUE2
oam_ptr: .word OAM_QUEUE1, OAM_QUEUE2
dirty_ptr: .word DIRTY_QUEUE1, DIRTY_QUEUE2
section_ptr: .word SECTION_QUEUE1, SECTION_QUEUE2
framebuffer: .word FRAMEBUFFER1, FRAMEBUFFER2

rdp_init:
    // RDP commands that only need to run once
    .dword 0x2F0088FF00040001 // Set Other Modes
    .dword 0x39000000FFFFFFFF // Set Blend Color
    .dword 0x3510810000000000 // Set Tile (palette)
    .dword 0x3550000001054150 // Set Tile (block)
    .dword 0x3548020002054150 // Set Tile (regular)
    .dword 0x320000000201F01F // Set Tile Size (regular)
    .dword 0x3548080003054150 // Set Tile (mode 7)
    .dword 0x320000000307F07F // Set Tile Size (mode 7)

rdp_frame:
    // RDP commands that run at the start of a frame
    .dword 0x3F10011700000000 // Set Color Image
    .dword 0x3D10000000000000 // Set Texture Image (palette)
    .dword 0x3300000000400000 // Load Block (palette)

rdp_fill:
    // RDP commands that run when filling the backdrop
    .dword 0x2800000000000000 // Sync Tile
    .dword 0x2D030020004303A0 // Set Scissor
    .dword 0x3A00000000000000 // Set Primitive Color
    .dword 0x3C080E10001D86C3 // Set Combine (primitive)
    .dword 0x3642F3A000030020 // Fill Rectangle
    .dword 0x2700000000000000 // Sync Pipe
    .dword 0x3C080E10001C8241 // Set Combine (texture)

rdp_window:
    // RDP commands that run when changing window segments
    .dword 0x2800000000000000 // Sync Tile
    .dword 0x2D030020004303A0 // Set Scissor

rdp_tile:
    // RDP commands that run when a regular tile is drawn
    .dword 0x3D50000300000000 // Set Texture Image (texture)
    .dword 0x2800000000000000 // Sync Tile
    .dword 0x330000000101F800 // Load Block (texture)
    .dword 0x2400000002000000 // Texture Rectangle 1
    .dword 0x0000000004000400 // Texture Rectangle 2

rdp_tile7:
    // RDP commands that run when a mode 7 tile is drawn
    .dword 0x3D50000300000000 // Set Texture Image (texture)
    .dword 0x2800000000000000 // Sync Tile
    .dword 0x330000000101F800 // Load Block (texture)
    .dword 0x0A83000000000000 // Texture Triangle 1
    .dword 0x0100000000000000 // Texture Triangle 2
    .dword 0x0000000000000000 // Texture Triangle 3
    .dword 0x0000000000000000 // Texture Triangle 4
    .dword 0x0010000040000000 // Texture Triangle 5
    .dword 0x0020000000000000 // Texture Triangle 6
    .dword 0x0000000000000000 // Texture Triangle 7
    .dword 0x0000000000000000 // Texture Triangle 8
    .dword 0x0200000000000000 // Texture Triangle 9
    .dword 0x0000000000000000 // Texture Triangle 10
    .dword 0x0000000000000000 // Texture Triangle 11
    .dword 0x0000000000000000 // Texture Triangle 12

tile_params:
    // S/T coordinates and gradients along X/Y
    .dword 0x0000000004000400 // No mirror
    .dword 0x00E00000FC000400 // X-mirror
    .dword 0x000000E00400FC00 // Y-mirror
    .dword 0x00E000E0FC00FC00 // XY-mirror

layer_chart:
    // Bit 7: object, bit 6: BG priority, bits 3-2: BG type, bits 1-0: index
    // BG type: 0 = rotscale, 1 = 4-color, 2 = 16-color, 3 = 256-color
    // Offset-per-tile, hi-res, and EXTBG are unimplemented
    .byte 0x07, 0x06, 0x80, 0x47, 0x46, 0x81, 0x05, 0x04, 0x82, 0x45, 0x44, 0x83, 0, 0, 0, 0 // Mode 0
    .byte 0x06, 0x80, 0x46, 0x81, 0x09, 0x08, 0x82, 0x49, 0x48, 0x83, 0x00, 0x00, 0, 0, 0, 0 // Mode 1 (BG3 normal)
    .byte 0x09, 0x80, 0x08, 0x81, 0x49, 0x82, 0x48, 0x83, 0x00, 0x00, 0x00, 0x00, 0, 0, 0, 0 // Mode 2
    .byte 0x09, 0x80, 0x0C, 0x81, 0x49, 0x82, 0x4C, 0x83, 0x00, 0x00, 0x00, 0x00, 0, 0, 0, 0 // Mode 3
    .byte 0x05, 0x80, 0x0C, 0x81, 0x45, 0x82, 0x4C, 0x83, 0x00, 0x00, 0x00, 0x00, 0, 0, 0, 0 // Mode 4
    .byte 0x05, 0x80, 0x08, 0x81, 0x45, 0x82, 0x48, 0x83, 0x00, 0x00, 0x00, 0x00, 0, 0, 0, 0 // Mode 5
    .byte 0x80, 0x08, 0x81, 0x82, 0x48, 0x83, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0, 0, 0, 0 // Mode 6
    .byte 0x80, 0x40, 0x81, 0x82, 0x83, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0, 0, 0, 0 // Mode 7
    .byte 0x06, 0x80, 0x81, 0x09, 0x08, 0x82, 0x49, 0x48, 0x83, 0x46, 0x00, 0x00, 0, 0, 0, 0 // Mode 1 (BG3 high)

obj_sizes:
    // Possible object sizes; bytes are small X, small Y, large X, large Y
    .word 0x08081010, 0x08082020, 0x08084040, 0x10102020
    .word 0x10104040, 0x20204040, 0x10202040, 0x10202020

fill_jumps: .word fill_backdrop, fill_win, fill_notwin, fill_main // Backdrop fill functions
tile_jumps: .word decode_tile4, decode_tile16, decode_tile256 // Tile decoding functions
shared_jumps: .word shared_decode4, shared_decode16, shared_decode256 // Shared decoding functions
cache_rets: .word get_offsets, start_objects // Return addresses after clearing cache
cache_ptrs: .word TILE_CACHE_BG, TILE_CACHE_OBJ, TILE_STATS_BG, TILE_STATS_OBJ, OBJECT_CACHE // RDRAM cache pointers
scrn_ofsv: .hword 0x0000, 0x0000, 0x0800, 0x1000 // Vertical screen address offsets
shift_table: .byte 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80 // Lookup table for (1 << i)

// 32-bit constants
texrec_ofs: .word 0x22020020
fillrec_mask: .word 0xFF000FFF
ldblk_bits: .word 0x01000200
mode7_mask: .word 0x0003FFFF

// Reserve three overlay source pointers without moving the raw pair or vectors.
.byte 0:(OVERLAY_MODE7_SRC - PRIO_CHECKS)
overlay_mode7_src: .word 0
overlay_main_src: .word 0
overlay_hcomp_src: .word 0
hcomp_raw_palette_ptrs: .word 0, 0

// Gate-C H-COMP resident-capacity proof. E8C/E90/E94 own Mode7/Main/H-COMP,
// E98/E9C remain the published raw palette pair, and preserve
// the fixed vector-constant start at EA0 plus VEC_DATA ABI at F70. The false-tag
// baseline itself comes from resident v24 lane5 (0x0400).
hcomp_vec_carrylo: .hword 0x0421, 0x0421, 0x0421, 0x0421, 0x0421, 0x0421, 0x0421, 0x0421
hcomp_vec_carryhi: .hword 0x8420, 0x8420, 0x8420, 0x8420, 0x8420, 0x8420, 0x8420, 0x8420
hcomp_vec_half:    .hword 0x7BDE, 0x7BDE, 0x7BDE, 0x7BDE, 0x7BDE, 0x7BDE, 0x7BDE, 0x7BDE
hcomp_vec_one:     .hword 0x0001, 0x0001, 0x0001, 0x0001, 0x0001, 0x0001, 0x0001, 0x0001
hcomp_vec_three:   .hword 0x0003, 0x0003, 0x0003, 0x0003, 0x0003, 0x0003, 0x0003, 0x0003
hcomp_vec_shr10:   .hword 0x0040, 0x0040, 0x0040, 0x0040, 0x0040, 0x0040, 0x0040, 0x0040
hcomp_vec_shr11:   .hword 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020, 0x0020
.byte 0:0x60

vec_data:
    // Constants that are always kept in vector registers
    .hword 0x0002, 0x0000, 0x0002, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000 // Tile increment
    .hword 0x8000, 0x4000, 0x2000, 0x1000, 0x0800, 0x0400, 0x0200, 0x0100 // Mask
    .hword 0x0100, 0x0100, 0x0100, 0x0100, 0x0100, 0x0100, 0x0100, 0x0100 // Shift byte
    .hword 0x0002, 0x0004, 0x0008, 0x0010, 0x0020, 0x0040, 0x0080, 0x0100 // Shift 1
    .hword 0x0004, 0x0008, 0x0010, 0x0020, 0x0040, 0x0080, 0x0100, 0x0200 // Shift 2
    .hword 0x0008, 0x0010, 0x0020, 0x0040, 0x0080, 0x0100, 0x0200, 0x0400 // Shift 3
    .hword 0x0010, 0x0020, 0x0040, 0x0080, 0x0100, 0x0200, 0x0400, 0x0800 // Shift 4
    .hword 0x0010, 0x0010, 0x0010, 0x0010, 0x0010, 0x0010, 0x0010, 0x0010 // Shift 5
    .hword 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000 // Zero

.text

main:
    // Load the constants for vector math
    lqv $v23, 0, -0x90, zero
    lqv $v24, 0, -0x80, zero
    lqv $v25, 0, -0x70, zero
    lqv $v26, 0, -0x60, zero
    lqv $v27, 0, -0x50, zero
    lqv $v28, 0, -0x40, zero
    lqv $v29, 0, -0x30, zero
    lqv $v30, 0, -0x20, zero
    lqv $v31, 0, -0x10, zero

    // Run the RDP initialization commands
    li t0, 0x2 // Use DMEM
    mtc0 t0, COP0_DP_STATUS
    li a0, RDP_INIT
    jal rdp_send
    li a1, RDP_FRAME
    li sp, 0 // Frame index

draw_frame:
    // Set initial values for copying VRAM
    li a0, TILE_TABLE
    li a2, 0x3FF
    lw t4, VRAM_ADDRS + 4
    lw t3, VRAM_ADDRS
    li t1, 0xFC00

vram_loop:
    // Copy VRAM for the current frame using RSP DMA for speed
    jal dma_read
    add a1, t4, t1
    jal dma_write
    add a1, t3, t1
    bnez t1, vram_loop
    addi t1, t1, -0x400
    mtc0 zero, COP0_SEMAPHORE

    // Load the VRAM dirty table for the current frame
    li a0, TILE_TABLE
    jal dma_read
    lw a1, DIRTY_PTR(sp)

    // Combine new dirty bits with the previous table
    li t1, VRAM_TABLE
    addi t2, t1, 0x400
table_loop:
    lqv $v00, 0, 0, t1
    lqv $v01, 0, 0, a0
    addi a0, a0, 16
    vor $v00, $v00, $v01, 0
    sqv $v00, 0, 0, t1
    bne t1, t2, table_loop
    addi t1, t1, 16

    // Update the RDP framebuffer and palette addresses
    lw t0, FRAMEBUFFER(sp)
    lw t1, PALETTE_PTR(sp)
    addi t0, t0, 280 * -16 // Underflow offset
    sw t0, RDP_FRAME + 4
    sw t1, RDP_FRAME + 12

    // Run the RDP to start the frame
    li a0, RDP_FRAME
    jal rdp_send
    li a1, RDP_FILL
    li k1, 0 // Section bound

next_section:
    // Finish the frame after the last section is done
    lw t0, FRAME_END(sp)
    beq k1, t0, next_frame

    // Load values for the next section
    li a0, BGHOFS
    lw a1, SECTION_PTR(sp)
    jal dma_read
    li a2, SECTION_SIZE - 1
    addi a1, a1, SECTION_SIZE
    sw a1, SECTION_PTR(sp)

    // Set the section bounds, then replay this section's typed CGRAM epoch.
    // Direct branch keeps the fixed pre-overlay instruction count unchanged.
    b hcomp_cgram_consume
    move k0, k1
hcomp_cgram_return:

    // Check if this section has an OAM update
    lbu t0, STAT_FLAGS
    andi t0, t0, 0x40
    beqz t0, oam_skip

    // Update OAM for the following sections
    li a0, OAM
    lw a1, OAM_PTR(sp)
    addi t0, a1, 0x220
    sw t0, OAM_PTR(sp)
    jal dma_read
    li a2, 0x21F

    // Get the index of the last object in rotation
    lhu t1, OAMADD
    andi v1, t1, 0x8000
    beqz v1, init_cache
    lw t0, FB_OFFSET(sp)
    andi v1, t1, 0xFE
    sll v1, v1, 1

init_cache:
    // Initialize values for building the object cache
    li t8, 239 + 16
    sll t0, t0, 1
    sub t8, t8, t0 // Y-bound
    li t7, 0x3000 // Priority

next_priority:
    // Reset indices for the next object priority
    li t6, TILE_TABLE + 0x200 // Cache index
    b start_cache
    move t9, v1 // OAM index

cache_object:
    // Read object data and skip if it doesn't match the current priority
    lw t1, OAM(t9)
    andi t0, t1, 0x3000
    bne t0, t7, cache_next

    // Read the 2 additional object bits
    srl t2, t9, 4
    lbu t2, OAM + 0x200(t2)
    srl t3, t9, 1
    andi t3, t3, 0x6
    srl t2, t2, t3

    // Get the object's size based on the large bit
    lbu t4, OBSEL
    andi t3, t2, 0x2 // Large
    andi t4, t4, 0xE0
    srl t4, t4, 3
    or v0, t3, t4
    lbu s0, OBJ_SIZES + 0(v0) // X-size
    lbu s1, OBJ_SIZES + 1(v0) // Y-size

    // Get the object's Y-coordinate, wrapped past screen bounds
    srl t3, t1, 24
    slt t4, t8, t3
    sll t4, t4, 31
    sra t4, t4, 23
    or s8, t3, t4

    // Skip the object if it doesn't occupy any visible scanlines
    add t4, s8, s1
    sle t5, t4, zero
    bnez t5, cache_next

    // Get the object's X-coordinate, wrapped past pixel 256
    srl t5, t1, 16
    andi t5, t5, 0xFF
    sll t0, t2, 31 // Upper X
    sra t0, t0, 23
    or s2, t5, t0

    // Skip the object if it doesn't occupy any visible pixels
    add t0, s2, s0
    and t0, t0, s2
    sra t0, t0, 8
    bnez t0, cache_next

    // Build and write a 32-bit cache value for the object
    sll t0, s8, 7 // Y-coordinate
    srl t3, t9, 2
    or t0, t0, t3 // OAM index
    sh t0, 0(t6)
    sll t0, s2, 7 // X-coordinate
    or t0, t0, v0 // Size index
    sh t0, 2(t6)
    addi t6, t6, 4

cache_next:
    // Move to the next object until finished
    beq t9, v1, finish_cache
start_cache:
    addi t9, t9, -4
    b cache_object
    andi t9, t9, 0x1FC

finish_cache:
    // Mark the end of the cache list
    addi t0, zero, -1
    sw t0, (t6)

    // DMA the current priority's cache list to RDRAM
    li a0, TILE_TABLE + 0x200
    lw a1, CACHE_PTRS + 16
    srl t0, t7, 3
    add a1, a1, t0
    jal dma_write
    li a2, 0x1FF

    // Move to the next priority until finished
    bnez t7, next_priority
    addi t7, t7, -0x1000

oam_skip:
    // Update the RDP scissor and fill bounds for the section
    lw t0, FB_OFFSET(sp)
    add t1, t0, k0
    sll t1, t1, 2
    sh t1, RDP_FILL + 10
    sh t1, RDP_FILL + 38
    add t2, t0, k1
    sll t2, t2, 2
    sh t2, RDP_FILL + 14
    sh t2, RDP_FILL + 34

    // Set some values for filling the backdrop
    lw t0, FILLREC_MASK
    lw t5, RDP_FILL + 36
    lw t6, RDP_FILL + 32
    and t5, t5, t0
    and t6, t6, t0
    li t7, 0 // Left bound
    li t8, 255 // Right bound
    li t9, 0 // Segment ordinal; zero means first segment

    // Clear the backdrop if force blank is enabled
    lbu t4, STAT_FLAGS
    andi t4, t4, 0x80
    beqz t4, not_blank
    lhu s0, SUB_COLOR
    b fill_backdrop
    li s0, 0

not_blank:
    // Check if the sub screen color should be applied to backdrop pixels
    lbu t0, CGADSUB
    beqz s0, fill_main
    andi t0, t0, 0x20 // Backdrop math
    beqz t0, fill_main

    // Apply the existing backdrop approximation on the exact SNES color-window
    // enable mask. The resident helper sets s0/s1 and alternating segment ends.
    jal calc_color_window_segments
    nop
    b fill_backdrop
    nop

fill_main:
    // No backdrop math: use Main across the whole section.
    b fill_backdrop
    lhu s0, MAIN_COLOR

hcomp_cgram_consume:
fill_win:
    // Reclaim the legacy 8-instruction padding without moving the fixed
    // renderer slot. EA0 is the CPU-published logical 4-byte record cursor.
    lw t6, HCOMP_CGRAM_EVENT_CURSOR
    andi t7, t6, 0x4
fill_notwin:
    bnez t7, hcomp_cgram_pair_ready
use_window:
    li a0, HCOMP_CGRAM_PAIR_SCRATCH
    move a1, t6
    jal dma_read
    li a2, 0x7
    b hcomp_cgram_pair_ready

fill_backdrop:
    // Update the RDP fill bounds for a window segment
    sltu t0, zero, t9
    addi t1, t7, 12
    add t1, t1, t0
    sll t1, t1, 14
    or t0, t5, t1
    sw t0, RDP_FILL + 36
    addi t1, t8, 13
    sll t1, t1, 14
    or t0, t6, t1
    sw t0, RDP_FILL + 32

    // Update the RDP primitive color for the segment
    andi t0, s0, 0x3E // B
    sll t0, t0, 10
    andi t1, s0, 0x7C0 // G
    sll t1, t1, 13
    or t0, t0, t1
    andi t1, s0, 0xF800 // R
    sll t1, t1, 16
    or t0, t0, t1
    ori t0, t0, 0xFF
    sw t0, RDP_FILL + 20

    // Run the RDP to fill the segment
    li a0, RDP_FILL
    jal rdp_send
    li a1, RDP_WINDOW

    // Swap the main and sub colors
    move t0, s0
    move s0, s1
    move s1, t0

    // Move to the next segment until the section is done
    addi t9, t9, 1
    move t7, t8
    bne t7, 255, fill_backdrop
    lbu t8, WIN_BOUNDS(t9)

    // Skip layers for force blank, or set the initial lookup offset
    lbu s3, BG_MODE
    bnez t4, next_section
    andi s3, s3, 0xF
    sll s3, s3, 4

    // Reset the background priority status
    sw zero, PRIO_CHECKS + 0
    sw zero, PRIO_CHECKS + 4

    // Create a layer mask based on main and sub masks, with shared layers on top
    // As a workaround for lack of blending, the order of the screens can be swapped
    lw t0, MASK_SEL(sp)
    lbu s7, TS(t0)
    xori t0, t0, 0x1
    lbu t0, TS(t0)
    and t1, t0, s7 // Shared
    sub s7, s7, t1
    sll t0, t0, 8
    or s7, s7, t0

next_layer:
    // Look up the next layer and check if it's BG or OBJ
    // Layers are drawn in an order that mimics priority without slow depth testing
    // This isn't fully accurate; OBJ priority effects like SMB3 pipes won't work
    lb t0, LAYER_CHART(s3)
    addi s3, s3, 1
    bltz t0, draw_obj
    li t1, 0x40
    beq t0, t1, draw_mode7_entry
    andi t1, s7, 0x1 // Enable
    bnez t0, draw_bg
    andi t3, t0, 0x3 // Index

    // Move to the next screen's layers until the section is finished
    srl s7, s7, 8
    beqz s7, next_section
    andi s3, s3, 0xF0
    b next_layer

    // Fixed renderer overlay begins on a 64-bit DMA boundary.
    .align 3
draw_bg:
get_offsets:
decode_tile4:
decode_tile16:
decode_tile256:
    // Fault stub: regular BG state has live t0. Preserve it across resident
    // dma_read in v0, then the loader restores it before re-entering draw_bg.
    b overlay_load_main
    move v0, t0


draw_mode7_impl:
    // Skip the layer if the BG is disabled
    // TODO: implement windows for mode 7
    beqz t1, next_layer
    move s1, k0 // Tile Y-coordinate

    // Calculate the initial screen X-coordinate
    lh t0, M7HOFS
    lh t2, M7X
    sub t0, t0, t2

    // Calculate the initial screen Y-coordinate
    lh t1, M7VOFS
    lh t3, M7Y
    add t1, t1, s1
    sub t1, t1, t3
    addi t1, t1, 1

    // Calculate the initial VRAM X-coordinate
    lh s2, M7A
    sll t2, t2, 8
    move a0, t0
    jal multiply
    move a1, s2
    add t2, t2, v0
    lh s4, M7B
    move a0, t1
    jal multiply
    move a1, s4
    add t8, t2, v0

    // Calculate the initial VRAM Y-coordinate
    lh s5, M7C
    sll t3, t3, 8
    move a0, t0
    jal multiply
    move a1, s5
    add t3, t3, v0
    lh s6, M7D
    move a0, t1
    jal multiply
    move a1, s6
    add t9, t3, v0

    // Update the RDP texture parameters with rotscale values
    sra t0, s2, 3
    sh t0, RDP_TILE7 + 64 // S-gradient along X (int)
    sra t1, s5, 3
    sh t1, RDP_TILE7 + 66 // T-gradient along X (int)
    sll t0, s2, 13
    sh t0, RDP_TILE7 + 80 // S-gradient along X (frac)
    sll t1, s5, 13
    sh t1, RDP_TILE7 + 82 // T-gradient along X (frac)
    sra t0, s4, 3
    sh t0, RDP_TILE7 + 88 // S-gradient along Y (int)
    sra t1, s6, 3
    sh t1, RDP_TILE7 + 90 // T-gradient along Y (int)
    sll t0, s4, 13
    sh t0, RDP_TILE7 + 96 // S-gradient along Y (frac)
    sll t1, s6, 13
    sh t1, RDP_TILE7 + 98 // T-gradient along Y (frac)

    // Draw 8-pixel or 16-pixel mode 7 tiles based on horizontal scaling
    addi t0, s2, 0x100
    sltiu t0, t0, 0x200
    addi t1, s5, 0x100
    sltiu t1, t1, 0x200
    and t0, t0, t1

    // Determine mode 7 tile height from the lower section bound
    sub a3, k1, s1
    addi a3, a3, -1
    bltu a3, 7, calc_bounds
    addi t7, t0, 3 // Width shift
    li a3, 7

calc_bounds:
    // Calculate the min and max X-offsets within a mode 7 tile
    move a0, a3
    jal multiply
    move a1, s4
    move a0, v0
    sll a1, s2, t7
    jal min_max
    sub a1, a1, s2
    sw v0, MODE7_BOUNDS + 0
    sw v1, MODE7_BOUNDS + 4

    // Calculate the min and max Y-offsets within a mode 7 tile
    move a0, a3
    jal multiply
    move a1, s6
    move a0, v0
    sll a1, s5, t7
    jal min_max
    sub a1, a1, s5
    sw v0, MODE7_BOUNDS + 8
    b bounds_skip
    sw v1, MODE7_BOUNDS + 12

draw_row7:
    // Recalculate bounds if the tile height can be reduced
    sub a3, k1, s1
    addi a3, a3, -1
    bltu a3, 7, calc_bounds

bounds_skip:
    // Set the initial tile X-coordinate
    li s0, 0

    // Update the RDP draw command with the tile's Y-coordinate
    lw t0, FB_OFFSET(sp)
    add t0, t0, s1
    sll t0, t0, 2
    addi t1, t0, 8 << 2
    sh t1, RDP_TILE7 + 26 // y3
    sh t0, RDP_TILE7 + 28 // y2
    sh t0, RDP_TILE7 + 30 // y1

next_tile7:
    // Update the RDP draw command with the tile's X-coordinate
    lbu t0, SHIFT_TABLE(t7)
    add t0, t0, s0
    addi t0, t0, 12
    sh t0, RDP_TILE7 + 32 // x1
    addi t1, s0, 12
    sh t1, RDP_TILE7 + 40 // x3
    sh t1, RDP_TILE7 + 48 // x2

    // Calculate the S-offset of the top-left tile within the texture
    lw t0, MODE7_BOUNDS + 0
    sra t1, t8, 11
    add t2, t0, t8
    sra t0, t2, 11
    sub s8, t1, t0

    // Calculate how many tiles wide the texture should be
    lw t0, MODE7_BOUNDS + 4
    add t3, t0, t8
    sra t0, t3, 11
    sub v0, t0, t1
    add v0, v0, s8
    blt v0, 4, calc_tofs
    addi v0, v0, 1
    li v0, 4 // Max

calc_tofs:
    // Calculate the T-offset of the top-left tile within the texture
    lw t0, MODE7_BOUNDS + 8
    sra t1, t9, 11
    add t4, t0, t9
    sra t0, t4, 11
    sub gp, t1, t0 // Offset T

    // Calculate how many tiles high the texture should be
    lw t0, MODE7_BOUNDS + 12
    add t5, t0, t9
    sra t0, t5, 11
    sub v1, t0, t1
    add v1, v1, gp
    blt v1, 4, check_wrap
    addi v1, v1, 1
    li v1, 4 // Max

check_wrap:
    // Check if areas out of bounds should be empty
    // TODO: handle this better and use screen flip bits
    lbu t0, M7SEL
    li t1, 0x80 // Empty
    andi t6, t0, 0xC0
    bne t6, t1, set_texels
    lw t1, MODE7_MASK

    // Skip the tile if it's out of bounds and empty
    or t2, t2, t4
    sltu t2, t1, t2
    or t3, t3, t5
    sltu t3, t1, t3
    and t0, t2, t3
    bnez t0, finish_tile7

set_texels:
    // Update the amount of texels the RDP should load to TMEM
    sll t1, v1, 7
    addi t1, t1, -1
    lw t0, LDBLK_BITS
    sll t1, t1, 12
    or t0, t0, t1
    sw t0, RDP_TILE7 + 20

    // Update the RDP texture parameters with current coordinates
    srl t4, t8, 3
    andi t4, t4, 0xFF
    sll t0, s8, 8
    add t4, t4, t0
    sh t4, RDP_TILE7 + 56 // S-coordinate (int)
    srl t4, t9, 3
    andi t4, t4, 0xFF
    sll t0, gp, 8
    add t4, t4, t0
    sh t4, RDP_TILE7 + 58 // T-coordinate (int)
    sll t4, t8, 13
    sh t4, RDP_TILE7 + 72 // S-coordinate (frac)
    sll t4, t9, 13
    sh t4, RDP_TILE7 + 74 // T-coordinate (frac)

    // Set some values for loading BG entries
    li a0, SCRN_DATA
    lw t1, VRAM_ADDRS
    li a2, 0x7
    move t5, v1

    // Calculate offsets for the texture's first tile row
    sra t2, t9, 3
    sll t0, gp, 8
    sub t2, t2, t0 // Y-offset
    sra t3, t8, 10
    sll t0, s8, 1
    sub t3, t3, t0 // X-offset

entry_row:
    // Load a row of mode 7 BG entries for the texture
    jal mode7_read
    sra t4, t2, 15
    addi a0, a0, 0x8
    jal mode7_read
    addi t3, t3, 0x8

    // Move to the next row and loop until complete
    addi t2, t2, 0x100
    addi t3, t3, -0x8
    addi t5, t5, -1
    bnez t5, entry_row
    addi a0, a0, 0x8

    // Set some values for building the texture
    andi a3, t3, 0x6 // DMA offset
    move t5, v0 // Row width
    sll t3, v1, 8 // Texture size

next_subrow:
    // Move to the next row within the texture
    addi v1, v1, -1

next_subtile:
    // Move to the next tile within the texture
    addi v0, v0, -1

    // Get the BG entry for the current tile
    sll t0, v0, 1
    sll t1, v1, 4
    add t0, t0, t1
    add t0, t0, a3
    lbu t6, SCRN_DATA + 1(t0)

    // Load the tile's character data from VRAM
    li a0, CHAR_DATA
    lw a1, VRAM_ADDRS
    sll t0, t6, 7
    add a1, a1, t0
    jal dma_read
    li a2, 0x7F

    // Copy the character data into vector registers
    lqv $v00, 0, 0x00, a0
    lqv $v01, 0, 0x10, a0
    lqv $v02, 0, 0x20, a0
    lqv $v03, 0, 0x30, a0
    lqv $v04, 0, 0x40, a0
    lqv $v05, 0, 0x50, a0
    lqv $v06, 0, 0x60, a0
    lqv $v07, 0, 0x70, a0

    // Get the tile's texture offset
    sll t0, v0, 3
    sll t1, v1, 8
    add t0, t0, t1

    // Copy bytes containing pixels into the texture
    spv $v00, 0, 0x00, t0
    spv $v01, 0, 0x20, t0
    spv $v02, 0, 0x40, t0
    spv $v03, 0, 0x60, t0
    spv $v04, 0, 0x80, t0
    spv $v05, 0, 0xA0, t0
    spv $v06, 0, 0xC0, t0

    // Loop through tiles until the texture is complete
    bnez v0, next_subtile
    spv $v07, 0, 0xE0, t0
    move v0, t5
    bnez v1, next_subrow

    // DMA the texture to alternating RDRAM locations
    li a0, TEXTURE
    li a1, MODE7_TEXTURE
    andi t0, s0, 0x18
    sll t0, t0, 8
    add a1, a1, t0
    sw a1, RDP_TILE7 + 4
    jal dma_write
    addi a2, t3, -1

    // Run the RDP to draw a tile
    li a0, RDP_TILE7
    jal rdp_send
    li a1, TILE_PARAMS

finish_tile7:
    // Move to the next tile, adjusting the VRAM coordinates
    lbu t0, SHIFT_TABLE(t7)
    sll t1, s2, t7
    add s0, s0, t0
    add t8, t8, t1
    sll t0, s5, t7
    blt s0, 256, next_tile7
    add t9, t9, t0

    // Move to the next row, adjusting the VRAM coordinates
    addi s1, s1, 8
    sll t0, s2, 8
    sub t8, t8, t0
    sll t0, s5, 8
    sub t9, t9, t0
    sll t0, s4, 3
    add t8, t8, t0
    sll t0, s6, 3
    blt s1, k1, draw_row7
    add t9, t9, t0
    b next_layer

    // Keep the externally visible Mode 7 entry fixed at the far edge of the
    // renderer slot; branch back into the variant-local implementation.
    .align 3
draw_mode7_entry:
    // Proof-only: zero F10 on actual Mode7 entry with no slot-size growth.
    b draw_mode7_impl
    sb zero, HCOMP_OVERLAY_PROOF_MODE7


draw_obj:
    // Skip the layer if objects are disabled
    andi t1, s7, 0x10
    beqz t1, next_layer
    andi a3, t0, 0x3 // Priority

    // Check if the object character base or gap changed
    lbu t1, OBSEL
    lhu t2, CACHE_BASES + 8
    andi t0, t1, 0x3 // Base
    sll t0, t0, 14
    andi t3, t1, 0x18 // Gap
    or t0, t0, t3
    beq t0, t2, load_objcache
    sh t0, CACHE_BASES + 8

    // Reset the tile cache if something changed
    j clear_cache
    lw ra, CACHE_RETS + 4

load_objcache:
    // Load the previous cache status if it's still valid
    li a0, TILE_TABLE
    lw a1, CACHE_PTRS + 12
    jal dma_read
    li a2, 0x1FF

start_objects:
    // DMA the current priority's object cache list from RDRAM
    li a0, TILE_TABLE + 0x200
    lw a1, CACHE_PTRS + 16
    sll t0, a3, 9
    add a1, a1, t0
    jal dma_read
    li a2, 0x1FF

    // Preserve the current combined Main/Sub screen-enable contract, but use
    // exact W1/W2 selection and OBJ OR/AND/XOR/XNOR logic when enabled.
    lbu t0, TMW
    lbu t1, TSW
    or t0, t0, t1
    andi t0, t0, 0x10
    beqz t0, obj_no_windows
    lbu a0, WOBJSEL
    andi a0, a0, 0xF
    lbu a1, WOBJLOG
    andi a1, a1, 0x3
    li a2, 0 // Return !selected = layer-visible pixels
    jal calc_window_spans
    nop

    lbu t2, WIN_COUNT
    beqz t2, obj_windows_done
    li t8, 0
    b obj_window_segment
    nop

obj_no_windows:
    // Negative bound index marks the unwindowed fast path at list completion.
    b obj_restart_objects
    li t8, -1

obj_window_segment:
    // Restrict RDP drawing to the current visible OBJ span while preserving
    // this section's Y bounds. RDP scissoring clips boundary-crossing tiles
    // without introducing a per-pixel RSP mask.
    lw t0, FILLREC_MASK
    lw t6, RDP_FILL + 8
    lw t7, RDP_FILL + 12
    and t6, t6, t0
    and t7, t7, t0
    lbu t2, WIN_BOUNDS + 0(t8)
    lbu t3, WIN_BOUNDS + 1(t8)

    // Explicit OBJ spans are already inclusive pixel coordinates. RDP scissor
    // uses an inclusive upper-left and exclusive lower-right, so only the
    // fixed framebuffer border offsets are needed here.
    addi t2, t2, 12
    sll t2, t2, 14
    or t0, t6, t2
    sw t0, RDP_WINDOW + 8
    addi t3, t3, 13
    sll t3, t3, 14
    or t0, t7, t3
    sw t0, RDP_WINDOW + 12

    li a0, RDP_WINDOW
    jal rdp_send
    li a1, RDP_TILE

obj_restart_objects:
    b next_object
    li a3, TILE_TABLE + 0x200 // Cache index

check_object:
    // Get the object's coordinates and size
    sra s8, t0, 7 // Y-coordinate
    sra s2, t1, 7 // X-coordinate
    andi t3, t1, 0x1E
    lbu s0, OBJ_SIZES + 0(t3) // X-size
    lbu s1, OBJ_SIZES + 1(t3) // Y-size

    // Skip the object if it doesn't intersect with the current section
    add t4, s8, s1
    slt t5, t4, k0
    sgt t6, s8, k1
    or t5, t5, t6
    bnez t5, next_object

    // Get the OAM index and read object data
    sll t9, t0, 2
    andi t9, t9, 0x1FC
    lw t1, OAM(t9)

    // Update mirroring using the shared function
    jal shared_mirror
    move t6, t1

    // Set initial values for drawing the object
    sll t3, t1, 3
    andi t3, t3, 0x7000
    addi t3, t3, 0x8000
    mtc2 t3, $v05, 0 // Palette offset
    move s4, s0 // X-size reload
    andi s5, t1, 0x1FF // Character number

    // Set initial values based on horizontal mirroring
    andi t7, t1, 0x4000 // X-mirror
    li s6, 8
    beqz t7, object_ymir
    move v0, s0
    add s2, s2, s0
    addi s2, s2, -8
    addi s6, zero, -8
    sub v0, zero, s0

object_ymir:
    // Set initial values based on vertical mirroring
    andi t7, t1, 0x8000 // Y-mirror
    beqz t7, next_objy
    li gp, 8
    add s8, s8, s1
    addi s8, s8, -8
    addi gp, zero, -8

next_objy:
    // Build a base value for the draw command with the row's Y-coordinate
    lw t7, FB_OFFSET(sp)
    lui t6, 0x0200 // Tile index
    add t7, t7, s8
    andi t7, t7, 0x1FF
    sll t7, t7, 2
    or t6, t6, t7 // Upper Y

next_objx:
    // Update the RDP draw command with the tile's coordinates
    addi t7, s2, 12
    andi t7, t7, 0x1FF
    sll t7, t7, 14
    or t0, t6, t7 // Upper X
    lw t7, TEXREC_OFS
    sw t0, RDP_TILE + 28
    add t0, t0, t7 // Lower X/Y
    sw t0, RDP_TILE + 24

    // Check if the tile's VRAM is dirty for objects
    lhu t0, CACHE_BASES + 8
    blt s5, 0x100, no_gap
    sll t4, s5, 5
    sll t2, t0, 10
    add t0, t0, t2
no_gap:
    add t5, t0, t4
    andi t5, t5, 0xFFE0
    srl t0, t5, 6
    lbu t2, VRAM_TABLE(t0)
    andi t4, t2, 0x10
    beqz t4, check_objcache

    // Clear the VRAM dirty bit and reset affected cache entries
    andi t2, t2, 0xF
    sb t2, VRAM_TABLE(t0)
    andi t1, s5, 0x1
    sub t1, s5, t1
    sh zero, TILE_TABLE(t1)

check_objcache:
    // Skip decoding if the tile is already cached with the same palette
    lbu t2, TILE_TABLE(s5)
    srl t4, t3, 7
    andi t4, t4, 0xE0 // Palette offset
    ori t0, t4, 0x1 // Cache bit
    beq t0, t2, skip_objdecode
    sb t0, TILE_TABLE(s5)

    // Load the tile's character data from VRAM
    li a0, CHAR_DATA
    lw a1, VRAM_ADDRS
    add a1, a1, t5
    jal dma_read
    li a2, 0x1F

    // Decode a tile using the shared 16-color path
    jal shared_decode
    lw t4, SHARED_JUMPS + 4

    // DMA the texture to the tile cache in RDRAM
    li a0, TEXTURE
    lw a1, CACHE_PTRS + 4
    sll t0, s5, 6
    add a1, a1, t0
    jal dma_write
    li a2, 0x3F

draw_objtile:
    // Update texture address and run the RDP to draw an object tile
    sw a1, RDP_TILE + 4
    li a0, RDP_TILE
    jal rdp_send
    li a1, RDP_TILE7

    // Loop through object tiles in the X-direction
    addi s0, s0, -8
    add s2, s2, s6
    addi s5, s5, 1
    bnez s0, next_objx
    andi s5, s5, 0x1FF

    // Loop through object tiles in the Y-direction
    move s0, s4
    sub s2, s2, v0
    srl t7, s0, 3
    sub s5, s5, t7
    addi s5, s5, 16
    andi s5, s5, 0x1FF
    addi s1, s1, -8
    bnez s1, next_objy
    add s8, s8, gp

next_object:
    // Move to the next object until the end of the list
    lh t0, 0(a3)
    lh t1, 2(a3)
    addi t2, zero, -1
    bne t1, t2, check_object
    addi a3, a3, 4

    // The unwindowed path is still a single object-list traversal.
    bltz t8, obj_finish_objects
    lbu t2, WIN_COUNT

    // Advance by explicit span count, never by an in-band coordinate sentinel.
    // This keeps x=255 available as an ordinary legal lower/upper endpoint.
    addi t8, t8, 2
    sll t2, t2, 1
    beq t8, t2, obj_windows_done
    nop
    b obj_window_segment
    nop

obj_windows_done:
    // Restore this section's full scissor bounds before later layers render.
    li a0, RDP_FILL
    jal rdp_send
    li a1, RDP_FILL + 16

obj_finish_objects:
    // Update the object tile cache status when finished
    li a0, TILE_TABLE
    lw a1, CACHE_PTRS + 12
    jal dma_write
    li a2, 0x1FF
    b next_layer

skip_objdecode:
    // Update the RDP texture address and draw a cached tile
    lw a1, CACHE_PTRS + 4
    sll t0, s5, 6
    b draw_objtile
    add a1, a1, t0


next_frame:
    // Load the third H-COMP slot at frame end. H-COMP performs HALT and leaves
    // a neutral two-renderer fault surface resident for the following frame.
    lw a1, OVERLAY_HCOMP_SRC
    li t9, 0x13B0
    b overlay_load_slot
    xori sp, sp, 4


clear_cache:
    // Clear the tile cache
    li t0, TILE_TABLE
    li t2, VRAM_TABLE
cache_loop:
    sqv $v31, 0, 0x00, t0
    addi t0, t0, 0x20
    bne t0, t2, cache_loop
    sqv $v31, 0, -0x10, t0
    jr ra


shared_mirror: // t6: parameter
    // Update the RDP texture parameters based on mirroring
    srl t2, t6, 11
    andi t2, t2, 0x18
    lw t3, TILE_PARAMS + 0(t2)
    lw t4, TILE_PARAMS + 4(t2)
    sw t3, RDP_TILE + 32 // S/T coordinates
    jr ra
    sw t4, RDP_TILE + 36 // Gradients along X/Y


shared_decode: // t4: decode jump
    // Set initial values for decoding a tile
    li t7, 0x40 // Texture offset
    li t1, CHAR_DATA + 0xE // Character offset
    vand $v10, $v10, $v31, 0 // Empty check
    jr t4
    vand $v20, $v20, $v31, 0

shared_decode256:
    // Decode the upper 4 bits of a 256-color tile line
    lpv $v08, 0, 0x20, t1 // Upper/lower byte 3 to lane 0/1, bits 8-15
    lpv $v18, 0, 0x30, t1 // Upper/lower byte 4 to lane 0/1, bits 8-15
    vand $v01, $v24, $v08, 9 // Mask out other lower bits
    vand $v02, $v24, $v08, 8 // Mask out other upper bis
    vmudl $v03, $v26, $v01, 0 // Shift lower bits to bit 0
    vmudl $v04, $v27, $v02, 0 // Shift upper bits to bit 1
    vor $v02, $v03, $v04, 0 // Combine bits to form partial indices
    vand $v11, $v24, $v18, 9 // Mask out other lower bits
    vand $v12, $v24, $v18, 8 // Mask out other upper bits
    vmudl $v13, $v28, $v11, 0 // Shift lower bits to bit 2
    vmudl $v14, $v29, $v12, 0 // Shift upper bits to bit 3
    vor $v12, $v13, $v14, 0 // Combine bits to form partial indices
    vor $v07, $v12, $v02, 0 // Combine partial indices
    vmudn $v20, $v07, $v30, 0 // Shift upper indices left

shared_decode16:
    // Decode the upper 2 bits of a 16-color tile line
    lpv $v13, 0, 0x10, t1 // Upper/lower byte 2 to lane 0/1, bits 8-15
    vand $v11, $v24, $v13, 9 // Mask out other lower bits
    vand $v12, $v24, $v13, 8 // Mask out other upper bits
    vmudl $v13, $v28, $v11, 0 // Shift lower bits to bit 2
    vmudl $v14, $v29, $v12, 0 // Shift upper bits to bit 3
    vor $v12, $v13, $v14, 0 // Combine bits to form partial indices
    vor $v20, $v20, $v12, 0 // Combine partial indices

shared_decode4:
    // Decode the lower 2 bits of a 4-color tile line
    lpv $v03, 0, 0x00, t1 // Upper/lower byte 1 to lane 0/1, bits 8-15
    vand $v01, $v24, $v03, 9 // Mask out other lower bits
    vand $v02, $v24, $v03, 8 // Mask out other upper bis
    vmudl $v03, $v26, $v01, 0 // Shift lower bits to bit 0
    vmudl $v04, $v27, $v02, 0 // Shift upper bits to bit 1
    vor $v02, $v03, $v04, 0 // Combine bits to form partial indices
    vor $v20, $v20, $v02, 0 // Combine partial indices
    vmudn $v01, $v20, $v25, 0 // Shift to upper byte

    // Add palette offset to non-zero indices and move to the next line
    veq $v00, $v01, $v31, 0
    addi t7, t7, -0x8
    vmrg $v00, $v01, $v05, 8
    addi t1, t1, -0x2
    vadd $v02, $v01, $v00, 0

    // Write the line to the texture buffer and loop until complete
    vand $v20, $v20, $v31, 0
    vor $v10, $v10, $v02, 0
    beqz t7, ret_jump
    spv $v02, 0, 0, t7
    jr t4


calc_color_window_segments:
    // Convert exact color-window truth into the legacy backdrop fill loop's
    // alternating inclusive segment-end list at WIN_BOUNDS+0..+6.
    // Preserve the live RDP fill word in t6 and the nested-call return in t9.
    move a3, t6
    move t9, ra

    lbu t0, CGWSEL
    srl t1, t0, 4
    andi t1, t1, 0x3
    beqz t1, color_window_all
    li t2, 3
    beq t1, t2, color_window_none
    lbu t0, WOBJSEL

    // Modes 1/2 are selected/complement of the OBJ color-window selector.
    srl a0, t0, 4
    lbu t0, WOBJLOG
    srl t0, t0, 2
    andi a1, t0, 0x3
    sltiu a2, t1, 2 // mode1=selected, mode2=complement
    jal calc_window_spans
    nop

    lbu t8, WIN_COUNT
    beqz t8, color_window_none
    lbu t0, WIN_BOUNDS + 0 // L1

    // Snapshot all possible span endpoints before overwriting E85 onward.
    lbu t1, WIN_BOUNDS + 1 // U1
    lbu t2, WIN_BOUNDS + 2 // L2
    lbu t3, WIN_BOUNDS + 3 // U2
    lbu t4, WIN_BOUNDS + 4 // L3
    lbu t7, WIN_BOUNDS + 5 // U3

    // The first segment uses Sub where math is enabled, Main otherwise.
    lhu s0, MAIN_COLOR
    lhu s1, SUB_COLOR
    bnez t0, color_window_initial_ready
    move a1, s0
    move s0, s1
    move s1, a1

color_window_initial_ready:
    li a0, WIN_BOUNDS

    // Every true span contributes its upper end; a nonzero lower bound first
    // contributes the preceding false segment end.
    beqz t0, color_window_first_upper
    addi a1, t0, -1
    sb a1, 0(a0)
    addi a0, a0, 1
color_window_first_upper:
    sb t1, 0(a0)
    addi a0, a0, 1
    li a1, 1
    beq t8, a1, color_window_tail
    addi a1, t2, -1
    sb a1, 0(a0)
    sb t3, 1(a0)
    addi a0, a0, 2
    li a1, 2
    beq t8, a1, color_window_tail
    addi a1, t4, -1
    sb a1, 0(a0)
    sb t7, 1(a0)
    addi a0, a0, 2
    move t1, t7

color_window_tail:
    // t1 is the final true upper bound for count1/2; select U2 when needed.
    li a1, 1
    beq t8, a1, color_window_tail_ready
    nop
    li a1, 2
    bne t8, a1, color_window_tail_ready
    nop
    move t1, t3
color_window_tail_ready:
    li a1, 255
    beq t1, a1, color_window_finish
    nop
    sb a1, 0(a0)
    b color_window_finish
    nop

color_window_all:
    lhu s0, SUB_COLOR
    lhu s1, MAIN_COLOR
    li t0, 255
    sb t0, WIN_BOUNDS + 0
    b color_window_finish
    nop

color_window_none:
    lhu s0, MAIN_COLOR
    lhu s1, SUB_COLOR
    li t0, 255
    sb t0, WIN_BOUNDS + 0

color_window_finish:
    // not_blank guarantees t4==0; restore the fill loop's live scalar state.
    move t6, a3
    li t4, 0
    li t7, 0
    lbu t8, WIN_BOUNDS + 0
    move ra, t9
    jr ra
    li t9, 0


calc_bg_window_spans:
    // Regular-BG wrapper kept in both RSP variants so resident suffix layout
    // remains byte-for-byte symmetric across overlay swaps.
    lhu t0, WBGSEL
    sll t1, s2, 1
    srl t0, t0, t1
    andi a0, t0, 0xF
    lbu t0, WBGLOG
    srl t0, t0, s2
    andi a1, t0, 0x3
    b calc_window_spans
    li a2, 0


calc_window_spans: // a0: selector, a1: logic, a2: 0=!selected / 1=selected
    // Emit up to three exact inclusive true spans in WIN_BOUNDS and their
    // out-of-band count in WIN_COUNT. Truth can only change at W1/W2 edges,
    // so scan those at most four transition coordinates rather than pixels.
    // Preserve s*, v0/v1, a3, t5, t9, gp, k0/k1 and ra for renderer callers.
    li t0, 0
    li t6, WIN_BOUNDS
    li t7, 0

window_span_loop:
    andi t2, a0, 0x2
    beqz t2, window_one_done
    move t2, zero
    lbu t8, WHX + 0
    sltu t2, t0, t8
    lbu t8, WHX + 1
    sltu t1, t8, t0
    or t2, t2, t1
    xori t2, t2, 1
    andi t1, a0, 0x1
    xor t2, t2, t1
window_one_done:

    andi t3, a0, 0x8
    beqz t3, window_two_done
    move t3, zero
    lbu t8, WHX + 2
    sltu t3, t0, t8
    lbu t8, WHX + 3
    sltu t1, t8, t0
    or t3, t3, t1
    xori t3, t3, 1
    srl t1, a0, 2
    andi t1, t1, 0x1
    xor t3, t3, t1
window_two_done:

    andi t1, a0, 0xA
    beqz t1, window_selected_done
    move t4, zero
    li t8, 0x2
    beq t1, t8, window_selected_one
    li t8, 0x8
    beq t1, t8, window_selected_two
    nop

    beqz a1, window_selected_or
    li t8, 1
    beq a1, t8, window_selected_and
    li t8, 2
    beq a1, t8, window_selected_xor
    xor t4, t2, t3
    xori t4, t4, 1
    b window_selected_done
    nop

window_selected_xor:
    b window_selected_done
    nop
window_selected_and:
    b window_selected_done
    and t4, t2, t3
window_selected_or:
    b window_selected_done
    or t4, t2, t3
window_selected_two:
    b window_selected_done
    move t4, t3
window_selected_one:
    move t4, t2

window_selected_done:
    xori t8, a2, 1
    xor t4, t4, t8
    li t1, 256

    lbu t8, WHX + 0
    sltu t2, t0, t8
    beqz t2, window_next_w1r
    sltu t2, t8, t1
    beqz t2, window_next_w1r
    nop
    move t1, t8
window_next_w1r:
    lbu t8, WHX + 1
    addi t8, t8, 1
    sltu t2, t0, t8
    beqz t2, window_next_w2l
    sltu t2, t8, t1
    beqz t2, window_next_w2l
    nop
    move t1, t8
window_next_w2l:
    lbu t8, WHX + 2
    sltu t2, t0, t8
    beqz t2, window_next_w2r
    sltu t2, t8, t1
    beqz t2, window_next_w2r
    nop
    move t1, t8
window_next_w2r:
    lbu t8, WHX + 3
    addi t8, t8, 1
    sltu t2, t0, t8
    beqz t2, window_emit
    sltu t2, t8, t1
    beqz t2, window_emit
    nop
    move t1, t8

window_emit:
    beqz t4, window_advance
    addi t8, t1, -1
    beqz t7, window_new_span
    nop
    lbu t2, -1(t6)
    addi t3, t2, 1
    bne t3, t0, window_new_span
    nop
    b window_advance
    sb t8, -1(t6)

window_new_span:
    sb t0, 0(t6)
    sb t8, 1(t6)
    addi t6, t6, 2
    addi t7, t7, 1

window_advance:
    li t8, 256
    beq t1, t8, window_spans_done
    move t0, t1
    b window_span_loop
    nop

window_spans_done:
    jr ra
    sb t7, WIN_COUNT


multiply: // a0: multiplicand, a1: multiplier - v0: product
    // Multiply 2 16-bit values to get a 32-bit value
    mtc2 a0, $v00, 0
    mtc2 a1, $v01, 0
    vmudh $v00, $v00, $v01, 0
    vsar $v00, COP2_ACC_MD
    vsar $v01, COP2_ACC_HI
    mfc2 v0, $v00, 0
    mfc2 v1, $v01, 0
    andi v0, v0, 0xFFFF
    sll v1, v1, 16
    jr ra
    or v0, v0, v1


min_max: // a0-a1: values - v0: min, v1: max
    // Create a third value by adding the first two
    add a2, a0, a1
    li t0, 1

find_min:
    // Find the minimum out of 4 values, including zero
    bgtz a0, min_skip1
    move v1, zero
    move v1, a0
min_skip1:
    bgt a1, v1, min_skip2
    sub a0, zero, a0
    move v1, a1
min_skip2:
    bgt a2, v1, find_max
    sub a1, zero, a1
    move v1, a2

find_max:
    // Repeat with inverse values to find the maximum
    beqz t0, set_max
    sub a2, zero, a2
    move v0, v1
    b find_min
    li t0, 0
set_max:
    jr ra
    sub v1, zero, v1


dma_write: // a0: RSP address, a1: DRAM address, a2: size
    // Transfer data from the RSP via DMA
    mtc0 a0, COP0_DMA_SPADDR
    mtc0 a1, COP0_DMA_RAMADDR
    b dma_wait
    mtc0 a2, COP0_DMA_WRITE

mode7_out:
    // Fill outside of bounds with tile 0, or wrap around if enabled
    andi t0, t6, 0x80
    beqz t0, dma_read
    sdv $v31, 0, 0, a0
    jr ra

mode7_read: // t1: base, t2: Y-offset, t3: X-offset, t4: Y-out, t6: wrap
    // Check bounds and build a DRAM address for mode 7 BG entries
    andi t0, t2, 0x7F00
    add a1, t1, t0
    andi t0, t3, 0xFF
    bne t0, t3, mode7_out
    add a1, a1, t0
    bnez t4, mode7_out

dma_read: // a0: RSP address, a1: DRAM address, a2: size
    // Transfer data to the RSP via DMA
    mtc0 a0, COP0_DMA_SPADDR
    mtc0 a1, COP0_DMA_RAMADDR
    mtc0 a2, COP0_DMA_READ

dma_wait:
    // Wait for the DMA to complete
    mfc0 t0, COP0_DMA_BUSY
    bnez t0, dma_wait
    nop
    jr ra


rdp_send: // a0: start address, a1: end address
    // Wait for the RDP to be ready and then send commands
    mfc0 t0, COP0_DP_STATUS
    andi t0, t0, 0x40 // Command busy
    bnez t0, rdp_send
    mtc0 a0, COP0_DP_START
    mtc0 a1, COP0_DP_END
ret_jump:
    jr ra
    nop

// Demand-load the missing renderer slot from resident suffix code.
overlay_load_mode7:
    lw a1, OVERLAY_MODE7_SRC
overlay_load_slot:
    li a0, 0x13A8
    jal dma_read
    li a2, 0x3E7
    jr t9
    nop

overlay_load_main:
    lw a1, OVERLAY_MAIN_SRC
    li a0, 0x13A8
    jal dma_read
    li a2, 0x3E7
    b draw_bg
    move t0, v0


hcomp_cgram_pair_ready:
    // Select word0/word1 from the cached aligned pair and advance logical cursor.
    add t0, a0, t7
    lw t8, 0(t0)
    addi t6, t6, 4
    sw t6, HCOMP_CGRAM_EVENT_CURSOR

    // Marker bit15 ends this section. Its raw RGBA5551 payload remains in t7
    // for the future H-COMP continuation, which is deliberately still frozen.
    andi t0, t8, 0x8000
    bnez t0, hcomp_cgram_marker
    srl t7, t8, 16

    // Color event: duplicate the raw RGBA5551 payload into one aligned 8-byte
    // palette entry and write it to the handed slot's owned raw shadow.
    sll t0, t7, 16
    or t7, t7, t0
    sw t7, HCOMP_CGRAM_WRITE_SCRATCH
    sw t7, HCOMP_CGRAM_WRITE_SCRATCH + 4
    andi t0, t8, 0x7F8
    lw a1, HCOMP_RAW_PALETTE_PTRS(sp)
    add a1, a1, t0
    li a0, HCOMP_CGRAM_WRITE_SCRATCH
    jal dma_write
    li a2, 0x7
    b hcomp_cgram_consume
    nop

hcomp_cgram_marker:
    b hcomp_cgram_return
    lbu k1, SPLIT_LINE
