/* Bounded Stage-2 capture. No code/data in normal or PROFILE-only builds. */
#include "defines.h"
#ifdef SODIUM64_HW_PROFILE
#define PROBE_OFFSET 0x4200
#define PROBE_SIZE 0x3D10
#define PROBE_BASE UNCACHED(sram + PROBE_OFFSET)
.globl hw_probe_capture
.text
.set noreorder
.align 5
hw_probe_capture:
    move s8, ra
    // Reuse the unused end of local SRAM, not a new renderer allocation.
    // Invalidate aliases before uncached writes, preventing later dirty eviction.
    la t0, sram + PROBE_OFFSET
    la t1, sram + PROBE_OFFSET + PROBE_SIZE
hw_probe_invalidate:
    cache 0x15, (t0)
    addiu t0, t0, 16
    bne t0, t1, hw_probe_invalidate
    nop
    la t0, PROBE_BASE
    la t1, PROBE_BASE + PROBE_SIZE
hw_probe_zero:
    sw zero, (t0)
    addiu t0, t0, 4
    bne t0, t1, hw_probe_zero
    nop
    la s7, PROBE_BASE
    li t0, 0x53363456 // S64V
    sw t0, 0(s7)
    li t0, 1
    sw t0, 4(s7)
    li t0, PROBE_SIZE
    sw t0, 8(s7)
    lw t0, 0xA4400004
    sw t0, 100(s7)
    lw t0, 0xA410000C
    sw t0, 104(s7)
    lw t0, 0xA4040010
    sw t0, 108(s7)
    // CPU is already in finalization with EXL set. Let current RSP/RDP work
    // finish naturally; do not force HALT to manufacture a valid snapshot.
    mfc0 t5, $9
    li t6, 9375000 // ~0.2 s on N64, only after measurements
    li s6, 0
hw_probe_drain:
    lw t0, 0xA4040010
    andi t1, t0, 1
    beqz t1, hw_probe_timeout_check
    nop
    lw t1, 0xA4040018
    bnez t1, hw_probe_timeout_check
    nop
    lw t1, 0xA4040014
    bnez t1, hw_probe_timeout_check
    nop
    lw t0, 0xA410000C
    andi t1, t0, 0x70 // TMEM, pipeline and command-buffer busy
    bnez t1, hw_probe_timeout_check
    nop
    lw t0, 0xA4100008
    lw t1, 0xA4100004
    bne t0, t1, hw_probe_timeout_check
    nop
    b hw_probe_drained
    li s6, 1
hw_probe_timeout_check:
    mfc0 t0, $9
    subu t0, t0, t5
    sltu t1, t0, t6
    bnez t1, hw_probe_drain
    nop
hw_probe_drained:
    lw t0, 0xA4040010
    sw t0, 20(s7)
    lw t0, 0xA410000C
    sw t0, 24(s7)
    lw t0, 0xA4100008
    sw t0, 28(s7)
    lw t0, 0xA4100004
    sw t0, 32(s7)
    lw t0, 0xA4040018
    sw t0, 36(s7)
    lw t0, 0xA4040014
    sw t0, 40(s7)
    lw s5, 0xA4400004
    sw s5, 44(s7)
    lw t0, 0xA4400000
    sw t0, 48(s7)
    lw t0, 0xA4400008
    sw t0, 52(s7)
    li t1, 280
    bne t0, t1, hw_probe_width_checked
    nop
    ori s6, s6, 4
hw_probe_width_checked:
    lw t0, 0xA4400010
    sw t0, 56(s7)
    lhu t0, dsp_pointer
    sw t0, 60(s7)
    lbu t0, enabled
    sw t0, 64(s7)
    lw t0, 0xA4500000
    sw t0, 68(s7)
    lw t0, 0xA4500004
    sw t0, 72(s7)
    lw t0, 0xA450000C
    sw t0, 76(s7)
    lw t0, 0xA4500010
    sw t0, 80(s7)
    lw t0, 0xA4500014
    sw t0, 84(s7)
    lbu t0, wram
    sw t0, 88(s7)
    lbu t0, frame_count
    sw t0, 92(s7)
    mfc0 t0, $14
    sw t0, 96(s7)
    la t0, dsp_buffer
    li t1, 0x1FFFFFFF
    and t0, t0, t1
    sw t0, 112(s7)
    li t0, FRAMEBUFFER1 & 0x1FFFFFFF
    sw t0, 116(s7)
    beq s5, t0, hw_probe_origin_ok
    nop
    li t0, FRAMEBUFFER2 & 0x1FFFFFFF
    beq s5, t0, hw_probe_origin_ok
    nop
    li t0, FRAMEBUFFER3 & 0x1FFFFFFF
    beq s5, t0, hw_probe_origin_ok
    nop
    b hw_probe_pixels_done
    nop
hw_probe_origin_ok:
    ori s6, s6, 2
    li t0, 0xA0000000
    or a0, s5, t0
    addiu a0, a0, 8 * 560 + 24
    addiu a1, s7, 0x80
    li t3, 16
hw_probe_row:
    jal hw_probe_copy
    li a2, 512
    addiu a0, a0, 48 // Skip left/right 12-pixel padding
    addiu t3, t3, -1
    bnez t3, hw_probe_row
    nop
hw_probe_pixels_done:
    li t0, FRAMEBUFFER2 & 0x1FFFFFFF
    sw t0, 120(s7)
    li t0, FRAMEBUFFER3 & 0x1FFFFFFF
    sw t0, 124(s7)
    sw s6, 16(s7)
    // Compare a first-row sample of all buffers; provenance is from the latest
    // completed renderer, which may differ from the VI-selected frame.
    li a0, FRAMEBUFFER1 + 8 * 560 + 24
    addiu a1, s7, 0x2080
    jal hw_probe_copy
    li a2, 512
    li a0, FRAMEBUFFER2 + 8 * 560 + 24
    jal hw_probe_copy
    li a2, 512
    li a0, FRAMEBUFFER3 + 8 * 560 + 24
    jal hw_probe_copy
    li a2, 512
    li a0, 0xA00E2000 + 24 // First Main-winner row
    jal hw_probe_copy
    li a2, 512
    li a0, 0xA00E6000 + 24 // First preserved TS-winner row
    jal hw_probe_copy
    li a2, 512
    li a0, 0xA00E4000 + 24 // First raw Sub row
    jal hw_probe_copy
    li a2, 512
    li a0, 0xA00F0000 // Existing consumed-section input record
    jal hw_probe_copy
    li a2, 16
    la a0, dsp_regs // CPU owns dirty cached DSP registers
    jal hw_probe_copy
    li a2, 128
    // Chronological previous 1024 stereo samples, ending at next-write offset.
    lhu t3, dsp_pointer
    addiu t3, t3, -4096
    andi t3, t3, 0x1FFF
    la t4, UNCACHED(dsp_buffer)
    li t5, 1024
hw_probe_pcm:
    addu t0, t4, t3
    lw t1, (t0)
    sw t1, (a1)
    addiu a1, a1, 4
    addiu t3, t3, 4
    andi t3, t3, 0x1FFF
    addiu t5, t5, -1
    bnez t5, hw_probe_pcm
    nop
    sync
    li t0, 1
    sw t0, 12(s7) // Complete, independently of timeout/invalid-source flags
    sync
    // Actual PI write to unused cart SRAM; original S64P/S64H follow afterward.
    lui t0, 0xA460
hw_probe_pi_idle:
    lw t1, 0x10(t0)
    andi t1, t1, 1
    bnez t1, hw_probe_pi_idle
    nop
    la t1, PROBE_BASE
    sw t1, 0(t0)
    li t1, 0x08000000 + PROBE_OFFSET
    sw t1, 4(t0)
    li t1, PROBE_SIZE - 1
    sw t1, 8(t0)
hw_probe_pi_wait:
    lw t1, 0x10(t0)
    andi t1, t1, 1
    bnez t1, hw_probe_pi_wait
    nop
    jr s8
    nop

hw_probe_copy: // a0 source/a1 dest advance; a2 byte count. Only t0/t1 clobbered.
    addu t0, a0, a2
hw_probe_copy_word:
    lw t1, (a0)
    sw t1, (a1)
    addiu a0, a0, 4
    bne a0, t0, hw_probe_copy_word
    addiu a1, a1, 4
    jr ra
    nop
#endif
