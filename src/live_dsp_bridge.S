#include "defines.h"
#include "live_dsp.h"

#ifdef SODIUM64_DSP_LIVE_CORE
#include "dsp_rsp_deadlines.h"
#ifdef SODIUM64_DSP_LIVE_INPUT_QUEUE
.data
.align 3
.globl live_dsp_input
live_dsp_input:
    .byte 0:LIVE_DSP_INPUT_BYTES
#endif
.text
.set noreorder
.globl live_dsp_bridge
live_dsp_bridge:
    lui t1, 0x8054
    mfc0 t2,$9
    sw t2, 0x08(t1)
    sd v0, 0x10(t1)
    sd v1, 0x18(t1)
    sd a0, 0x20(t1)
    sd a1, 0x28(t1)
    sd a2, 0x30(t1)
    sd a3, 0x38(t1)
    sd t3, 0x40(t1)
    sd t4, 0x48(t1)
    sd t5, 0x50(t1)
    sd t6, 0x58(t1)
    sd t7, 0x60(t1)
    sd t8, 0x68(t1)
    sd t9, 0x70(t1)
    sd gp, 0x78(t1)
    sd sp, 0x80(t1)
    sd ra, 0x88(t1)
    mfhi t2
    sd t2, 0x90(t1)
    mflo t2
    sd t2, 0x98(t1)

    li sp, LIVE_DSP_WRAPPER_END - 32
    move a2, a1
    move a1, a0
    move a0, t0
    lw a3, DSP_GUEST_EPOCH_BIAS
    addiu a3, a3, LIVE_DSP_EPOCH_OFFSET
    subu a3, a3, s3
    // Raw RAM accesses and the fixture's opcode fetch precede their own
    // scheduler debit by one SPC cycle. The DSP port dispatch follows it.
    sltiu t2, a0, LIVE_DSP_REG_WRITE
    beqz t2, 1f
    nop
    b 2f
    addiu a3, a3, LIVE_DSP_GUEST_CYCLE
1:
    bne a0, LIVE_DSP_FETCH, 2f
    nop
    addiu a3, a3, LIVE_DSP_GUEST_CYCLE
2:
    jal live_dsp_access
    nop

    lui t1, 0x8054
    sw v0, 4(t1)
    ld v0, 0x10(t1)
    ld v1, 0x18(t1)
    ld a0, 0x20(t1)
    ld a1, 0x28(t1)
    ld a2, 0x30(t1)
    ld a3, 0x38(t1)
    ld t3, 0x40(t1)
    ld t4, 0x48(t1)
    ld t5, 0x50(t1)
    ld t6, 0x58(t1)
    ld t7, 0x60(t1)
    ld t8, 0x68(t1)
    ld t9, 0x70(t1)
    ld gp, 0x78(t1)
    ld sp, 0x80(t1)
    ld ra, 0x88(t1)
    ld t2, 0x90(t1)
    mthi t2
    ld t2, 0x98(t1)
    mtlo t2

    mfc0 t2,$9
    lw t0, 8(t1)
    subu t2, t2, t0
    li t0, LIVE_DSP_STATS
    lw t1, 4(t0)
    addiu t1, t1, 1
    sw t1, 4(t0)
    lw t1, 0(t0)
    addu t1, t1, t2
    jr ra
    sw t1, 0(t0)
#endif
