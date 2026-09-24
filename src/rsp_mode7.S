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

// Reserve renderer overlay source pointers without moving vector data.
.byte 0:(OVERLAY_MAIN_SRC - PRIO_CHECKS)
overlay_main_src: .word 0
overlay_mode7_src: .word 0
hcomp_raw_palette_ptrs: .word 0, 0
