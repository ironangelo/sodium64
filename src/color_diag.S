/* Isolated native color/VI diagnostic. No code/data in other builds. */
#include "defines.h"
#ifdef SODIUM64_COLOR_DIAG
#ifndef SODIUM64_HW_PROFILE
#error COLOR_DIAG requires HW_PROFILE
#endif
#define CBASE UNCACHED(sram)
#define TRACE_START 0x100
#define TRACE_CAPACITY 320
#define TRACE_STRIDE 48
.globl color_diag_init
.globl color_diag_vi_entry
.globl color_diag_producer
.globl color_diag_finalize
.globl color_diag_phase_a
.globl color_diag_phase_b
.globl color_diag_saved
.data
.align 4
color_diag_metadata: .word 0:6 // seq,bounds per completed framebuffer
color_diag_sequence: .word 0
color_diag_irq_save: .dword 0:12 // at, t0..t9, ra; separate from producer
color_diag_colors: .hword 0x7BC1,0x07C1,0xF801,0x003F,0xFFFF,0x0001
.text
.set noreorder
.set at

color_diag_init:
    // The synthetic guests never use SRAM. Remove dirty cache aliases before
    // the uncached trace writes; all 32KB will be replaced by this diagnostic.
    la t0, sram
    la t1, sram + 0x8000
1:  cache 0x15, (t0)
    addiu t0, t0, 16
    bne t0, t1, 1b
    nop
    la t0, CBASE
    la t1, CBASE + 0x8000
2:  sw zero, (t0)
    addiu t0, t0, 4
    bne t0, t1, 2b
    nop
    la t0, CBASE
    li t1, 0x53363443 // S64C, deliberately not S64H/S64P
    sw t1, 0(t0)
    li t1, 1
    sw t1, 4(t0)
    li t1, 0x8000
    sw t1, 8(t0)
    li t1, TRACE_CAPACITY
    sw t1, 16(t0)
    li t1, TRACE_STRIDE
    sw t1, 20(t0)
    li t1, TRACE_START
    sw t1, 36(t0)
    li t1, 0x4200
    sw t1, 40(t0)
    li t1, 0x3D10
    sw t1, 44(t0)
    li t1, 0x0202
    sw t1, 48(t0)
    li t1, 0x3202
    sw t1, 52(t0)
    jr ra
    nop

color_diag_producer:
    // Called at update_menu entry: only t0..t3,t7..t9 are clobbered,
    // just as the original menu does. No HI/LO, ra, a0, t4/t5/t6 writes.
    la t0, color_diag_metadata
    li t1, FRAMEBUFFER1
    beq a0, t1, 1f
    nop
    addiu t0, t0, 8
    li t1, FRAMEBUFFER2
    beq a0, t1, 1f
    nop
    addiu t0, t0, 8
1:  lw t1, 0xA00F0000 // actual composed-section framebuffer authority
    lw t2, 0xA00F0004 // WH0,WH1 in upper halfword, no endian guessing
    beq t1, a0, 2f
    nop
    li t2, 0xFFFF0001 // explicit unknown ownership, never guest phase
2:  sw t2, 4(t0)
    lw t1, color_diag_sequence
    addiu t1, t1, 1
    sw t1, color_diag_sequence
    sync
    sw t1, 0(t0)
    // Six 40x16 reference swatches at x12..251, y200..215.
    // Old blue rows31..70 and original band8..15 are never touched.
    li t1, 200 * 560 + 24
    addu t0, a0, t1
    li t3, 16
3:  la t7, color_diag_colors
    li t8, 6
4:  lhu t1, (t7)
    sll t2, t1, 16
    or t1, t1, t2
    li t9, 20
5:  sw t1, (t0)
    addiu t0, t0, 4
    addiu t9, t9, -1
    bnez t9, 5b
    nop
    addiu t7, t7, 2
    addiu t8, t8, -1
    bnez t8, 4b
    nop
    // Marker: one white block then black during live / frozen A.
    li t1, 0xFFFFFFFF
    sw t1, 0(t0)
    sw t1, 4(t0)
    sw t1, 8(t0)
    sw t1, 12(t0)
    li t1, 0x00010001
    sw t1, 16(t0)
    sw t1, 20(t0)
    sw t1, 24(t0)
    sw t1, 28(t0)
    addiu t0, t0, 80 // finish 560B row: 480+80
    addiu t3, t3, -1
    bnez t3, 3b
    nop
    sync
    j color_diag_producer_return
    nop

color_diag_vi_entry:
    // Every VI exit (changed source, repeated source or no ready frame).
    // Before measurements only reserved k0/k1 are touched.
    lbu k0, hw_profile_phase
    addiu k0, k0, -1
    bnez k0, color_diag_vi_return
    nop
    la k0, color_diag_irq_save
    .set noat
    sd at, 0(k0)
    .set at
    sd t0, 8(k0)
    sd t1, 16(k0)
    sd t2, 24(k0)
    sd t3, 32(k0)
    sd t4, 40(k0)
    sd t5, 48(k0)
    sd t6, 56(k0)
    sd t7, 64(k0)
    sd t8, 72(k0)
    sd t9, 80(k0)
    sd ra, 88(k0)
    mfc0 t8, $9
    la t0, CBASE
    lw t1, 24(t0)
    addiu t1, t1, 1
    sw t1, 24(t0) // attempted monotonically, even overflow
    lw t2, 28(t0)
    sltiu t3, t2, TRACE_CAPACITY
    bnez t3, color_diag_vi_record
    nop
    lw t1, 32(t0)
    addiu t1, t1, 1
    b color_diag_vi_restore
    sw t1, 32(t0)
color_diag_vi_record:
    sll t3, t2, 5
    sll t4, t2, 4
    addu t3, t3, t4
    addu t3, t3, t0
    addiu t3, t3, TRACE_START
    sw t1, 0(t3)
    sw t8, 4(t3)
    lw t4, 0xA4400004
    sw t4, 8(t3)
    la t5, color_diag_metadata
    li t6, FRAMEBUFFER1 & 0x1FFFFFFF
    beq t4, t6, color_diag_vi_source
    nop
    addiu t5, t5, 8
    li t6, FRAMEBUFFER2 & 0x1FFFFFFF
    beq t4, t6, color_diag_vi_source
    nop
    addiu t5, t5, 8
    li t6, FRAMEBUFFER3 & 0x1FFFFFFF
    beq t4, t6, color_diag_vi_source
    nop
    // Never dereference an invalid VI origin; retain invalid record.
    lw t6, 172(t0)
    addiu t6, t6, 1
    sw t6, 172(t0)
    sw zero, 12(t3)
    li t6, 0xFFFF0002
    sw t6, 16(t3)
    sw zero, 36(t3)
    b color_diag_vi_state
    sw zero, 40(t3)
color_diag_vi_source:
    lw t6, 0(t5)
    sw t6, 12(t3)
    lw t6, 4(t5)
    sw t6, 16(t3)
    andi t7, t6, 0xFFFF
    beqz t7, 1f
    nop
    lw t7, 168(t0)
    addiu t7, t7, 1
    sw t7, 168(t0)
1:  li t7, 0xA0000000
    or t4, t4, t7
    srl t6, t6, 24 // owned window's left; clamp unknown metadata
    andi t6, t6, 127
    sll t6, t6, 1
    addu t6, t6, t4
    lhu t6, 8 * 560 + 24(t6) // inside window
    lhu t7, 8 * 560 + 24 + 255 * 2(t4) // outside, always yellow
    sll t7, t7, 16
    or t6, t6, t7
    sw t6, 36(t3)
    li t6, 64 * 560 + 24 + 128 * 2
    addu t6, t6, t4
    lhu t6, (t6) // old stripe area, should red
    li t7, 208 * 560 + 32 * 2
    addu t7, t7, t4
    lhu t7, (t7) // direct yellow reference
    sll t6, t6, 16
    or t6, t6, t7
    sw t6, 40(t3)
color_diag_vi_state:
    lw t4, 0xA4040010
    sw t4, 20(t3)
    lw t4, 0xA410000C
    sw t4, 24(t3)
    lw t4, 0xA4100008
    sw t4, 28(t3)
    lw t4, 0xA4100004
    sw t4, 32(t3)
    lhu t4, dsp_pointer
    sll t4, t4, 16
    lbu t5, enabled
    sll t5, t5, 8
    or t4, t4, t5
    lbu t5, frame_count
    or t4, t4, t5
    sw t4, 44(t3)
    addiu t2, t2, 1
    sw t2, 28(t0)
    mfc0 t1, $9
    subu t1, t1, t8
    lw t2, 116(t0)
    addu t2, t2, t1
    sw t2, 116(t0)
    lw t2, 112(t0)
    sltu t3, t2, t1
    beqz t3, color_diag_vi_restore
    nop
    sw t1, 112(t0)
color_diag_vi_restore:
    la k0, color_diag_irq_save
    .set noat
    ld at, 0(k0)
    .set at
    ld t0, 8(k0)
    ld t1, 16(k0)
    ld t2, 24(k0)
    ld t3, 32(k0)
    ld t4, 40(k0)
    ld t5, 48(k0)
    ld t6, 56(k0)
    ld t7, 64(k0)
    ld t8, 72(k0)
    ld t9, 80(k0)
    ld ra, 88(k0)
color_diag_vi_return:
    j input_update
    nop

color_diag_finalize:
    // Already EXL=1 after timed windows; hw_probe_capture saved S64V first.
    // Original PC statistics are deliberately not written to cart.
    la t9, CBASE
    lw t0, color_diag_sequence
    sw t0, 120(t9)
    la t0, hw_profile_header
    addiu t0, t0, 32
    addiu t1, t9, 128
    li t2, 5
1:  lw t3, (t0)
    sw t3, (t1)
    addiu t0, t0, 4
    addiu t1, t1, 4
    addiu t2, t2, -1
    bnez t2, 1b
    nop
    lbu t0, apu_clock
    sll t0, t0, 24
    lbu t1, audio_set
    sll t1, t1, 16
    or t0, t0, t1
    lbu t1, precision_set
    sll t1, t1, 8
    or t0, t0, t1
    lbu t1, skipped_set
    or t0, t0, t1
    sw t0, 148(t9)
    lw t0, 0xA4040010
    sw t0, 152(t9)
    lw t0, 0xA410000C
    sw t0, 156(t9)
    lw t1, 0x4200 + 16(t9) // S64V validity
    sw t1, 160(t9)
    addiu t1, t1, -7
    bnez t1, color_diag_abort
    andi t0, t0, 0x170 // includes source DMA_BUSY
    bnez t0, color_diag_abort
    nop
    lw t8, 0xA4400004
    sw t8, 72(t9)
    sw t8, 76(t9)
    li t0, 0xA0000000
    or t8, t8, t0
    // Actual control readback; no emulator software RGB is hue authority.
    lw t0, 0xA4400000
    sw t0, 48(t9)
color_diag_phase_a:
    mfc0 t0, $9
    sw t0, 56(t9)
    jal color_diag_reference_copy
    addiu t7, t9, 80
    jal color_diag_hold
    nop
    mfc0 t0, $9
    sw t0, 60(t9)
    li t0, 0x3202
    sw t0, 0xA4400000 // ONLY VI pixel advance changes
    lw t0, 0xA4400000
    sw t0, 52(t9)
    // Second white marker block; reference swatches and original band unchanged.
    li t0, 200 * 560 + 260 * 2
    addu t0, t0, t8
    li t1, 16
    li t2, 0xFFFFFFFF
2:  sw t2, 0(t0)
    sw t2, 4(t0)
    sw t2, 8(t0)
    sw t2, 12(t0)
    addiu t0, t0, 560
    addiu t1, t1, -1
    bnez t1, 2b
    nop
    sync
color_diag_phase_b:
    mfc0 t0, $9
    sw t0, 64(t9)
    jal color_diag_reference_copy
    addiu t7, t9, 92
    jal color_diag_hold
    nop
    mfc0 t0, $9
    sw t0, 68(t9)
    li t0, 3
    sw t0, 164(t9)
    b color_diag_write
    nop
color_diag_abort:
    li t0, 1
    sw t0, 164(t9) // failed drain: no comparisons claimed
color_diag_write:
    sync
    li t0, 1
    sw t0, 12(t9) // payload complete; drops/drain remain independent
    sync
    lui t0, 0xA460
1:  lw t1, 0x10(t0)
    andi t1, t1, 1
    bnez t1, 1b
    nop
    sw t9, 0(t0)
    li t1, 0x08000000
    sw t1, 4(t0)
    li t1, 0x41FF
    sw t1, 8(t0) // trace/header through0x41FF; S64V already saved
2:  lw t1, 0x10(t0)
    andi t1, t1, 1
    bnez t1, 2b
    nop
color_diag_saved:
    // Existing final red routine and done loop; no guest resumes.
    li t0, 3
    sb t0, hw_profile_phase
    j hw_profile_red_start
    nop

color_diag_reference_copy:
    // t8=uncached frozen source, t7=destination. Only t0..t3 clobber.
    li t0, 208 * 560 + 32 * 2
    addu t0, t0, t8
    li t1, 6
1:  lhu t2, (t0)
    sh t2, (t7)
    addiu t0, t0, 80
    addiu t7, t7, 2
    addiu t1, t1, -1
    bnez t1, 1b
    nop
    jr ra
    nop
color_diag_hold:
    // 2s at nominal N64 CP0 Count; measured elapsed ticks stored, no live work.
    mfc0 t0, $9
    li t1, 93750000
1:  mfc0 t2, $9
    subu t2, t2, t0
    sltu t3, t2, t1
    bnez t3, 1b
    nop
    jr ra
    nop
#endif
