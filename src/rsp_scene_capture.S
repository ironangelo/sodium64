/* SPDX-License-Identifier: GPL-3.0-or-later
 * Export architectural scalar/vector/flag/ACC state without changing it.
 * Caller stages/restores IMEM/DMEM, halted PC/status and pipeline ownership. */
#include <rsp.inc>
#include "scene_rsp_context.h"
.data
.word 0
.text
.set noreorder
.set noat
    // CPU PC writes can leave the stopped renderer's pending target3C.
    // Entry0 consumes its delay slot with NOP; both paths reach this body.
    .space 0x3c
scene_rsp_capture:
    .irp reg,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
    sw $\reg,(SCENE_RSP_GPR+4*\reg)(zero)
    .endr
    .irp vec,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
    .word 0xe8002000 | (\vec << 16) | (SCENE_RSP_VECTOR/16+\vec)
    .endr
    vsar $v00,COP2_ACC_HI
    sqv $v00,0,SCENE_RSP_ACC_HI,zero
    vsar $v00,COP2_ACC_MD
    sqv $v00,0,SCENE_RSP_ACC_MID,zero
    vsar $v00,COP2_ACC_LO
    sqv $v00,0,SCENE_RSP_ACC_LO,zero
    cfc2 t0,$0
    sw t0,SCENE_RSP_VCO(zero)
    cfc2 t0,$1
    sw t0,SCENE_RSP_VCC(zero)
    cfc2 t0,$2
    sw t0,SCENE_RSP_VCE(zero)
    lqv $v00,0,SCENE_RSP_VECTOR,zero
    lw t0,SCENE_RSP_GPR+32(zero)
    break
    b scene_rsp_capture
    nop
