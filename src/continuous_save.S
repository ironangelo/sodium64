/* SPDX-License-Identifier: GPL-3.0-or-later
 * C is isolated behind an O64 stack: Sodium's sp is normally the queue slot.
 * Caller ordinary GPRs retain all 64 bits; only v0 is the receipt result.
 */
#include "defines.h"
#if defined(SODIUM64_NATIVE_DIAG_TRACE)
.globl continuous_save_available, continuous_save_init_bridge
.globl continuous_save_capture_bridge
.data
.align 3
continuous_save_available: .word 0
.section .bss
.align 5
cs_bridge_saved: .space 272
.align 5
cs_bridge_stack: .space 2048
cs_bridge_stack_end:
.text
.set noreorder
continuous_save_init_bridge:
    la k1, continuous_save_init
    b cs_bridge_enter
    nop
continuous_save_capture_bridge:
    la k1, continuous_save_capture
cs_bridge_enter:
    la k0, cs_bridge_saved
    .set push
    .set noat
    sd $1, 0(k0)
    sd $2, 8(k0)
    sd $3, 16(k0)
    sd $4, 24(k0)
    sd $5, 32(k0)
    sd $6, 40(k0)
    sd $7, 48(k0)
    sd $8, 56(k0)
    sd $9, 64(k0)
    sd $10, 72(k0)
    sd $11, 80(k0)
    sd $12, 88(k0)
    sd $13, 96(k0)
    sd $14, 104(k0)
    sd $15, 112(k0)
    sd $16, 120(k0)
    sd $17, 128(k0)
    sd $18, 136(k0)
    sd $19, 144(k0)
    sd $20, 152(k0)
    sd $21, 160(k0)
    sd $22, 168(k0)
    sd $23, 176(k0)
    sd $24, 184(k0)
    sd $25, 192(k0)
    sd $28, 200(k0)
    sd $29, 208(k0)
    sd $30, 216(k0)
    sd $31, 224(k0)
    .set pop
    mfhi t0
    sd t0, 240(k0)
    mflo t0
    sd t0, 248(k0)
    mfc0 t0, $12
    sw t0, 256(k0)
    li t1, -2
    and t1, t0, t1
    mtc0 t1, $12
    nop
    nop
    la sp, cs_bridge_stack_end - 32
    jalr k1
    nop
    la k0, cs_bridge_saved
    ld t0, 240(k0)
    mthi t0
    ld t0, 248(k0)
    mtlo t0
    .set push
    .set noat
    ld $1, 0(k0)
    ld $3, 16(k0)
    ld $4, 24(k0)
    ld $5, 32(k0)
    ld $6, 40(k0)
    ld $7, 48(k0)
    ld $8, 56(k0)
    ld $9, 64(k0)
    ld $10, 72(k0)
    ld $11, 80(k0)
    ld $12, 88(k0)
    ld $13, 96(k0)
    ld $14, 104(k0)
    ld $15, 112(k0)
    ld $16, 120(k0)
    ld $17, 128(k0)
    ld $18, 136(k0)
    ld $19, 144(k0)
    ld $20, 152(k0)
    ld $21, 160(k0)
    ld $22, 168(k0)
    ld $23, 176(k0)
    ld $24, 184(k0)
    ld $25, 192(k0)
    ld $28, 200(k0)
    ld $29, 208(k0)
    ld $30, 216(k0)
    ld $31, 224(k0)
    .set pop
    lw k1, 256(k0)
    mtc0 k1, $12
    nop
    nop
    jr ra
    nop
#endif

