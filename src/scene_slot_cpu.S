/* SPDX-License-Identifier: GPL-3.0-or-later
 * 32-bit address mode, explicit indexed TLB and cache owners. Kernel C stack
 * remains live. EXL/ERL and FPU/64-bit address modes are rejected by caller. */
#include "defines.h"
#ifdef SODIUM64_SCENE_SLOT
.text
.set noreorder
.globl scene_slot_tlb_save,scene_slot_tlb_load,scene_slot_cache_sync
scene_slot_tlb_save:
    mfc0 t0, $0
    sw t0, 0(a0)
    mfc0 t0, $10
    sw t0, 4(a0)
    mfc0 t0, $2
    sw t0, 8(a0)
    mfc0 t0, $3
    sw t0, 12(a0)
    mfc0 t0, $5
    sw t0, 16(a0)
    move t0, zero
    addiu t1, a0, 20
1:
    mtc0 t0, $0
    nop
    nop
    nop
    tlbr
    nop
    nop
    nop
    mfc0 t2, $10
    sw t2, 0(t1)
    mfc0 t2, $2
    sw t2, 4(t1)
    mfc0 t2, $3
    sw t2, 8(t1)
    mfc0 t2, $5
    sw t2, 12(t1)
    addiu t0, t0, 1
    addiu t1, t1, 16
    sltiu t2, t0, 32
    bnez t2, 1b
    nop
    b scene_slot_tlb_regs
    nop
scene_slot_tlb_load:
    move t0, zero
    addiu t1, a0, 20
2:
    mtc0 t0, $0
    lw t2, 0(t1)
    mtc0 t2, $10
    lw t2, 4(t1)
    mtc0 t2, $2
    lw t2, 8(t1)
    mtc0 t2, $3
    lw t2, 12(t1)
    mtc0 t2, $5
    nop
    nop
    nop
    tlbwi
    nop
    nop
    nop
    addiu t0, t0, 1
    addiu t1, t1, 16
    sltiu t2, t0, 32
    bnez t2, 2b
    nop
scene_slot_tlb_regs:
    lw t0, 0(a0)
    mtc0 t0, $0
    lw t0, 4(a0)
    mtc0 t0, $10
    lw t0, 8(a0)
    mtc0 t0, $2
    lw t0, 12(a0)
    mtc0 t0, $3
    lw t0, 16(a0)
    mtc0 t0, $5
    nop
    nop
    jr ra
    nop
scene_slot_cache_sync:
    li t0, 0x80000000
    li t1, 0x80002000
3:
    cache 0x01, 0(t0) // Index writeback/invalidate all D-cache lines.
    addiu t0, t0, 16
    bne t0, t1, 3b
    nop
    sync
    li t0, 0x80000000
    li t1, 0x80004000
4:
    cache 0x00, 0(t0) // Index invalidate I-cache for restored APU JIT code.
    addiu t0, t0, 32
    bne t0, t1, 4b
    nop
    sync
    jr ra
    nop
#endif
