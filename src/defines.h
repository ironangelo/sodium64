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

#include <regdef.h>

// Opt-in hardware bank residency observer. Normal recorder builds retain BAN4.
#ifndef SODIUM64_SIGNAL_PROFILE
#define SODIUM64_SIGNAL_PROFILE 0
#endif
#ifndef SODIUM64_HCOMP_WIDE_MATH
#define SODIUM64_HCOMP_WIDE_MATH 0
#endif
// Opt-in: publish Main math eligibility through two exact compressed Z tags.
#ifndef SODIUM64_ELIGIBILITY_TAGS
#define SODIUM64_ELIGIBILITY_TAGS 0
#endif
#ifndef SODIUM64_HCOMP_MASK_SCAN
#define SODIUM64_HCOMP_MASK_SCAN 0
#endif
#ifndef SODIUM64_HCOMP_TLUT_SHADER
#define SODIUM64_HCOMP_TLUT_SHADER 0
#endif
#ifndef SODIUM64_HCOMP_TLUT_FLAT_WINDOW
#define SODIUM64_HCOMP_TLUT_FLAT_WINDOW 0
#endif

// Master cycle counts for CPU memory accesses
#define RAM_CYCLE 8
#define IO_CYCLE 6

// Approximate master cycle counts for APU components
#define APU_CYCLE 21 // 21477000Hz / 1024000Hz = 20.973632812
#define APU_TIMER1 2688 // 21477000Hz / 8000Hz = 2684.625
#define APU_TIMER2 336 // 21477000Hz / 64000Hz = 335.578125

// Approximate master cycle count for DSP samples
#define DSP_SAMPLE 672 // 21477000Hz / 32000Hz = 671.15625
#define DSP_AI_DAC_RATE (48681812 / (60 * 262 * 341 * 4 / DSP_SAMPLE) + 1)

// Maximum opcode bytes that can be compiled in an APU JIT block
#define BLOCK_SIZE 16

// The frame section data structure's size in bytes
#define SECTION_SIZE 0x40

// Flags for tracking JIT block state
#define FLAG_SX (1 << 0)
#define FLAG_SY (1 << 1)
#define FLAG_SA (1 << 2)
#define FLAG_SS (1 << 3)
#define FLAG_SF (1 << 4)
#define FLAG_LX (1 << 5)
#define FLAG_LY (1 << 6)
#define FLAG_LA (1 << 7)
#define FLAG_LS (1 << 8)
#define FLAG_LF (1 << 9)
#define FLAG_PC (1 << 10)
#define FLAG_NZ (1 << 11)

// Register values for emitting JIT code
#define ZERO 0
#define AT_ 1
#define V0 2
#define V1 3
#define A0 4
#define A1 5
#define A2 6
#define A3 7
#define T0 8
#define T1 9
#define T2 10
#define T3 11
#define T4 12
#define T5 13
#define T6 14
#define T7 15
#define S0 16
#define S1 17
#define S2 18
#define S3 19
#define S4 20
#define S5 21
#define S6 22
#define S7 23
#define T8 24
#define T9 25
#define K0 26
#define K1 27
#define GP 28
#define SP 29
#define S8 30
#define RA 31

// Opcode macros for emitting JIT code
#define ADD(rd, rs, rt) (0x00000020 | ((rd) << 11) | ((rs) << 21) | ((rt) << 16))
#define ADDI(rt, rs, imm) (0x20000000 | ((rt) << 16) | ((rs) << 21) | ((imm) & 0xFFFF))
#define AND(rd, rs, rt) (0x00000024 | ((rd) << 11) | ((rs) << 21) | ((rt) << 16))
#define ANDI(rt, rs, imm) (0x30000000 | ((rt) << 16) | ((rs) << 21) | ((imm) & 0xFFFF))
#define BEQ(rt, rs, ofs) (0x10000000 | ((rt) << 16) | ((rs) << 21) | ((ofs) & 0xFFFF))
#define BNE(rt, rs, ofs) (0x14000000 | ((rt) << 16) | ((rs) << 21) | ((ofs) & 0xFFFF))
#define DIV(rs, rt) (0x0000001A | ((rs) << 21) | ((rt) << 16))
#define LBU(rt, rb, ofs) (0x90000000 | ((rt) << 16) | ((rb) << 21) | ((ofs) & 0xFFFF))
#define LUI(rt, imm) (0x3C000000 | ((rt) << 16) | ((imm) & 0xFFFF))
#define MFHI(rd) (0x00000010 | ((rd) << 11))
#define MFLO(rd) (0x00000012 | ((rd) << 11))
#define MULT(rs, rt) (0x00000018 | ((rs) << 21) | ((rt) << 16))
#define OR(rd, rs, rt) (0x00000025 | ((rd) << 11) | ((rs) << 21) | ((rt) << 16))
#define ORI(rt, rs, imm) (0x34000000 | ((rt) << 16) | ((rs) << 21) | ((imm) & 0xFFFF))
#define SB(rt, rb, ofs) (0xA0000000 | ((rt) << 16) | ((rb) << 21) | ((ofs) & 0xFFFF))
#define SH(rt, rb, ofs) (0xA4000000 | ((rt) << 16) | ((rb) << 21) | ((ofs) & 0xFFFF))
#define SLL(rd, rt, sa) (0x00000000 | ((rd) << 11) | ((rt) << 16) | ((sa) << 6))
#define SLT(rd, rs, rt) (0x0000002A | ((rd) << 11) | ((rs) << 21) | ((rt) << 16))
#define SLTU(rd, rs, rt) (0x0000002B | ((rd) << 11) | ((rs) << 21) | ((rt) << 16))
#define SRL(rd, rt, sa) (0x00000002 | ((rd) << 11) | ((rt) << 16) | ((sa) << 6))
#define SUB(rd, rs, rt) (0x00000022 | ((rd) << 11) | ((rs) << 21) | ((rt) << 16))
#define XOR(rd, rs, rt) (0x00000026 | ((rd) << 11) | ((rs) << 21) | ((rt) << 16))
#define XORI(rt, rs, imm) (0x38000000 | ((rt) << 16) | ((rs) << 21) | ((imm) & 0xFFFF))

// Addresses of data in RDRAM that are shared between CPU and RSP
#define ROM_BUFFER 0xA0200000
// Full-section composition surfaces replace repeated eight-row redraws.
// Cartridge capacity is unchanged; ROM pages still use the ordinary pager.
#define ROM_CACHE_SLOTS 194
#define ROM_CACHE_END (ROM_BUFFER + ROM_CACHE_SLOTS * 0x2000)
#define JIT_BUFFER (ROM_BUFFER - 0x40000)
#define TILE_CACHE_BG (JIT_BUFFER - 0x40000)
#define TILE_CACHE_OBJ (TILE_CACHE_BG - 0x8000)
#define TILE_STATS_BG (TILE_CACHE_OBJ - 0x1000)
#define TILE_STATS_OBJ (TILE_STATS_BG - 0x200)
#define OBJECT_CACHE (TILE_STATS_OBJ - 0x800)
#define SECTION_QUEUE2 (OBJECT_CACHE - 0x5000)
#define SECTION_QUEUE1 (SECTION_QUEUE2 - 0x5000)
#define DIRTY_QUEUE2 (SECTION_QUEUE1 - 0x400)
#define DIRTY_QUEUE1 (DIRTY_QUEUE2 - 0x400)
#define OAM_QUEUE2 (DIRTY_QUEUE1 - 0x2200)
#define OAM_QUEUE1 (OAM_QUEUE2 - 0x2200)
#define PALETTE_QUEUE2 (OAM_QUEUE1 - 0x800)
#define PALETTE_QUEUE1 (PALETTE_QUEUE2 - 0x800)
#define VRAM_BUFFER (PALETTE_QUEUE1 - 0x10000)
#define MODE7_TEXTURE (VRAM_BUFFER - 0x2000)
#define FRAMEBUFFER3 (MODE7_TEXTURE - 0x20D00)
#define FRAMEBUFFER2 (FRAMEBUFFER3 - 0x20D00)
#define FRAMEBUFFER1 (FRAMEBUFFER2 - 0x20D00)

// Gate-C lossless CGRAM epoch stream. Diagnostic snapshots and USB helpers
// require a larger static arena. Keep both CPU and RSP on the same layout.
// Keep this boundary checked against every linked ELF; the raw shadows consume the
// audited guard below FRAMEBUFFER1.
#define HCOMP_RAW_PALETTE_QUEUE1 (FRAMEBUFFER1 - 0x3300)
#define HCOMP_RAW_PALETTE_QUEUE2 (HCOMP_RAW_PALETTE_QUEUE1 + 0x800)
#if defined(SODIUM64_FULL_DSP_PROBE)
#define HCOMP_CGRAM_ARENA 0xA00D6000
#elif defined(SODIUM64_BRR_OBSERVER) || defined(SODIUM64_MIX_OBSERVER)
#define HCOMP_CGRAM_ARENA 0xA00D4000
#elif defined(SODIUM64_NATIVE_DIAG_TRACE) || defined(SODIUM64_PROFILE)
#define HCOMP_CGRAM_ARENA 0xA00D2000
#else
#define HCOMP_CGRAM_ARENA 0xA00C2000
#endif
#define HCOMP_CGRAM_BASE_QUEUE1 HCOMP_CGRAM_ARENA
#define HCOMP_CGRAM_BASE_QUEUE2 (HCOMP_CGRAM_ARENA + 0x200)
#define HCOMP_CGRAM_SIDEBAND_QUEUE1 (HCOMP_CGRAM_ARENA + 0x400)
#define HCOMP_CGRAM_SIDEBAND_QUEUE2 (HCOMP_CGRAM_ARENA + 0x900)
#define HCOMP_CGRAM_EVENT_QUEUE1 (HCOMP_CGRAM_ARENA + 0xE00)
#define HCOMP_CGRAM_EVENT_QUEUE2 0xA03E8000
#define HCOMP_CGRAM_EVENT_CAPACITY 0x6000
#define HCOMP_CGRAM_EVENT_BYTES (HCOMP_CGRAM_EVENT_CAPACITY * 4)

#if HCOMP_CGRAM_EVENT_QUEUE1 + HCOMP_CGRAM_EVENT_BYTES > HCOMP_RAW_PALETTE_QUEUE1
#error Q1 CGRAM events overlap raw palette shadows
#endif

// Three disjoint 240-row surfaces, with alignment padding and guard lines.
// Their lifetime is one RSP-owned section; CPU writes only the row-color queues.
#define HCOMP_SURFACE_BYTES 0x21000
#define HCOMP_WINNER_ARENA 0xA0384000
#define HCOMP_SUB_ARENA (HCOMP_WINNER_ARENA + HCOMP_SURFACE_BYTES)
#define HCOMP_PRESENCE_ARENA (HCOMP_SUB_ARENA + HCOMP_SURFACE_BYTES)
#define HCOMP_WINNER_ORIGIN (HCOMP_WINNER_ARENA + 0x80)
#define HCOMP_SUB_ORIGIN (HCOMP_SUB_ARENA + 0x80)
#define HCOMP_PRESENCE_ORIGIN (HCOMP_PRESENCE_ARENA + 0x80)
#define HCOMP_ROW_FIXED_QUEUE1 0xA03E7000
#define HCOMP_ROW_FIXED_QUEUE2 0xA03E7200

#if ROM_CACHE_END != HCOMP_WINNER_ARENA
#error ROM cache must end before the composition surfaces
#endif
#if HCOMP_PRESENCE_ARENA + HCOMP_SURFACE_BYTES > HCOMP_ROW_FIXED_QUEUE1
#error Composition surfaces overlap row colors
#endif
#if HCOMP_ROW_FIXED_QUEUE2 + 512 > HCOMP_CGRAM_EVENT_QUEUE2
#error Row colors overlap the Q2 event arena
#endif
#if HCOMP_CGRAM_EVENT_QUEUE2 + HCOMP_CGRAM_EVENT_BYTES != 0xA0400000
#error Q2 event arena must fit within base 4 MiB RDRAM
#endif

// RSP addresses of data in DMEM; used to avoid setting the upper address
#define TEXTURE 0x000
// Decoder worker starts at object-cache overlay offset200. These fixed
// entries are checked against the linked worker before native use.
#define RSP_BANK_DECODE_START 0x15A8
#define RSP_BANK_DECODE256 0x15BC
#define RSP_BANK_DECODE16 0x15F4
#define RSP_BANK_DECODE4 0x1610
#define RSP_BANK_DECODE_RETURN 0x1AE8
#ifndef SODIUM64_TMEM_ATLAS
#define SODIUM64_TMEM_ATLAS 0
#endif
#ifndef SODIUM64_TMEM_COORD_ATLAS
#define SODIUM64_TMEM_COORD_ATLAS 0
#endif
#define TILE_TABLE (TEXTURE + 0x40)
#define VRAM_TABLE (TILE_TABLE + 0x400)
#define OAM (VRAM_TABLE + 0x400)
#define SCRN_DATA (OAM + 0x220)
#define CHAR_DATA (SCRN_DATA + 0x80)
#define MODE7_BOUNDS (CHAR_DATA + 0x80)
#define CACHE_BASES (MODE7_BOUNDS + 0x10)
// Start of section values
#define BGHOFS (CACHE_BASES + 0x10)
#define BGVOFS (BGHOFS + 0x8)
#define BGNBA (BGVOFS + 0x8)
#define OAMADD (BGNBA + 0x2)
#define M7HOFS (OAMADD + 0x2)
#define M7VOFS (M7HOFS + 0x2)
#define M7A (M7VOFS + 0x2)
#define M7B (M7A + 0x2)
#define M7C (M7B + 0x2)
#define M7D (M7C + 0x2)
#define M7X (M7D + 0x2)
#define M7Y (M7X + 0x2)
#define WBGSEL (M7Y + 0x2)
#define SUB_COLOR (WBGSEL + 0x2)
#define MAIN_COLOR (SUB_COLOR + 0x2)
#define BGXSC (MAIN_COLOR + 0x2)
#define WHX (BGXSC + 0x4)
#define OBSEL (WHX + 0x4)
#define M7SEL (OBSEL + 0x1)
#define WOBJSEL (M7SEL + 0x1)
#define WBGLOG (WOBJSEL + 0x1)
#define WOBJLOG (WBGLOG + 0x1)
#define CGWSEL (WOBJLOG + 0x1)
#define CGADSUB (CGWSEL + 0x1)
#define TS (CGADSUB + 0x1)
#define TM (TS + 0x1)
#define TSW (TM + 0x1)
#define TMW (TSW + 0x1)
#define BG_MODE (TMW + 0x1)
#define STAT_FLAGS (BG_MODE + 0x1)
#define SPLIT_LINE (STAT_FLAGS + 0x1)
// Start of frame values
#define MASK_SEL (SPLIT_LINE + 0x1)
#define FB_OFFSET (MASK_SEL + 0x8)
#define FRAME_END (FB_OFFSET + 0x8)
#define VRAM_ADDRS (FRAME_END + 0x8)
#define PALETTE_PTR (VRAM_ADDRS + 0x8)
#define OAM_PTR (PALETTE_PTR + 0x8)
#define DIRTY_PTR (OAM_PTR + 0x8)
#define SECTION_PTR (DIRTY_PTR + 0x8)
#define FRAMEBUFFER (SECTION_PTR + 0x8)
// End of frame values
#define RDP_INIT (FRAMEBUFFER + 0x8)
#define RDP_FRAME (RDP_INIT + 0x40)
#define RDP_FILL (RDP_FRAME + 0x18)
#define RDP_WINDOW (RDP_FILL + 0x38)
#define RDP_TILE (RDP_WINDOW + 0x10)
#define RDP_TILE7 (RDP_TILE + 0x28)
#define TILE_PARAMS (RDP_TILE7 + 0x78)
#define LAYER_CHART (TILE_PARAMS + 0x20)
#define OVERLAY_OBJECT_CACHE_SRC (LAYER_CHART + 7 * 16 + 8)
#define OBJ_SIZES (LAYER_CHART + 0x90)
#define FILL_JUMPS (OBJ_SIZES + 0x20)
#define TILE_JUMPS (FILL_JUMPS + 0x10)
#define SHARED_JUMPS (TILE_JUMPS + 0xC)
#define CACHE_RETS (SHARED_JUMPS + 0xC)
#define CACHE_PTRS (CACHE_RETS + 0x8)
#define SCRN_OFSV (CACHE_PTRS + 0x14)
#define SHIFT_TABLE (SCRN_OFSV + 0x8)
#define TEXREC_OFS (SHIFT_TABLE + 0x8)
#define FILLREC_MASK (TEXREC_OFS + 0x4)
#define LDBLK_BITS (FILLREC_MASK + 0x4)
#define MODE7_MASK (LDBLK_BITS + 0x4)
#define PRIO_CHECKS (MODE7_MASK + 0x4)
#define WIN_BOUNDS (PRIO_CHECKS + 0x8)
// Exact W1/W2 window results use up to three inclusive [lower,upper] spans
// in E84..E89. Keep the count out of the byte-coordinate domain so x=255
// remains an ordinary legal endpoint; E8B..E8F stay free before overlay ABI.
#define WIN_COUNT (WIN_BOUNDS + 0x6)
// Mode7 consumes these exact spans through a separate small slot image.
#define MODE7_WINDOW_INDEX (WIN_COUNT + 0x1)
// Three fixed-slot renderer/H-COMP source pointers. E8C..E8F is the
// already-audited free word; PR #18 replay state remains at E98 and above.
#define OVERLAY_MODE7_SRC 0xE8C
#define OVERLAY_MAIN_SRC 0xE90
#define OVERLAY_HCOMP_SRC 0xE94
#define HCOMP_RAW_PALETTE_PTRS 0xE98
// Typed CGRAM event cursor published by the CPU while the RSP is halted.
// EA0 lies in the audited retired DMEM interval below fixed VEC_DATA.
#define HCOMP_CGRAM_EVENT_CURSOR 0xEA0
#define OVERLAY_MODE7_DRAW_SRC 0xEA4
#define HCOMP_CGRAM_PAIR_SCRATCH 0xEA8
#define HCOMP_CGRAM_WRITE_SCRATCH 0xEB0
// Full-height band phase state in the previously retired DMEM tail.
#define OVERLAY_HCOMP_MATH_SRC 0xEB8
#define HCOMP_SECTION_END 0xEBC
#define HCOMP_BAND_Y 0xEC0
#define HCOMP_BAND_ROWS 0xEC4
#define HCOMP_SCREEN 0xEC8
// Per-epoch Sub mask; fixed-operand direct composition does not render TS.
#define HCOMP_EFFECTIVE_TS 0xEC9
// Diagnostic-only 16-bit seqlock: epoch[15:4], loading[3], bank[2:0].
#define NATIVE_DIAG_RSP_BANK 0xECA
#define NATIVE_DIAG_SIGNAL_MASKS 0xEFC // Eight immutable halfwords; retired eligibility LUT tail.
#define HCOMP_DIAG_COMPOSE_LIMIT 0xECC
#define HCOMP_FIXED_COLOR 0xED0
#define HCOMP_ROW_FIXED_SRC HCOMP_FIXED_COLOR
// Per-band compact pixel origins, including the 12-pixel left border.
// RDP image bases are 64-byte aligned even for scanline-sized sections.
#define HCOMP_BAND_BASES 0xED4
#define HCOMP_ELIGIBILITY_TABLE 0xEF8
#define HCOMP_TAG_ENABLE_LUT 0xF0C // Seven class bits; does not overlap SIG1 masks.
#define HCOMP_TLUT_CLASS 0xF13 // Active bit80, then base1/BG2/mixedOBJ3.
#define OVERLAY_HCOMP_TLUT_SRC 0xF14
#define HCOMP_TLUT_BASE HCOMP_WINNER_ARENA
#define HCOMP_TLUT_BG (HCOMP_TLUT_BASE + 0x800)
#define HCOMP_TLUT_OBJ (HCOMP_TLUT_BASE + 0x1000)
// The former scalar lookup table is unused by the vector compositor.
#define OVERLAY_HCOMP_SETUP_SRC HCOMP_ELIGIBILITY_TABLE
#define HCOMP_OBJ_DEPTH_CMDS 0xEE0
#define HCOMP_BAND_RAW 0xEF0
// Geometry of the last normalized OBJ cache, plus the current safe span.
// These words occupy existing zero padding; no resident ABI moves.
#define HCOMP_OBJ_GEOMETRY_KEY 0xEF4
#define HCOMP_FAST_END 0xF18
#define HCOMP_OBJ_ADAPTIVE 0xF1C
// Gate-C proof-only immutable RDP commands in the audited retired DMEM gap.
// Eight commands occupy F30..F6F; VEC_DATA remains frozen at F70.
// PipeSync is required before changing OtherModes while prior RDP work may
// still be in flight; the BG depth table therefore begins one command later.
#define HCOMP_TEXTURE_FENCE 0xF20
#define OVERLAY_HCOMP_FAST_SRC 0xF28
// Independent first-copy state. F28 remains the fast-bank source pointer;
// this last retired word is zero in the initial Main DMEM image.
#define HCOMP_VRAM_SNAPSHOT_READY 0xF2C
#define HCOMP_PROOF_RDP_CMDS 0xF30
#define HCOMP_PROOF_BG_DEPTH_CMDS (HCOMP_PROOF_RDP_CMDS + 0x20)
#define VEC_DATA 0xF70

// Macros that convert addresses between cached and uncached
#define CACHED(addr) ((addr) - 0x20000000)
#define UNCACHED(addr) ((addr) + 0x20000000)

// Macro that converts an RSP DMEM address to a CPU address
#define DMEM(addr) (0xA4000000 + (addr))

