/* SPDX-License-Identifier: GPL-3.0-or-later
 * Exact ACC reconstruction first, then vectors, flags and scalar registers.
 * CPU supplies derived helper lanes and preserves original SP memory. */
#include <rsp.inc>
#include "scene_rsp_context.h"
.data
.word 0
.text
.set noreorder
.set noat
scene_rsp_restore:
    lqv $v00,0,SCENE_RSP_ACC_LO,zero
    lqv $v01,0,SCENE_RSP_ACC_MID,zero
    lqv $v02,0,SCENE_RSP_NEG_HI,zero
    lqv $v03,0,SCENE_RSP_ONE,zero
    lqv $v04,0,SCENE_RSP_NEG_HALF,zero
    // LO + signed(MID)<<16 + corrected HI<<32, modulo48.
    vmudn $v05,$v00,$v03,0
    vmadh $v05,$v01,$v03,0
    vmadh $v05,$v02,$v04,0
    vmadh $v05,$v02,$v04,0
    .irp vec,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
    .word 0xc8002000 | (\vec << 16) | (SCENE_RSP_VECTOR/16+\vec)
    .endr
    lw t0,SCENE_RSP_VCO(zero)
    ctc2 t0,$0
    lw t0,SCENE_RSP_VCC(zero)
    ctc2 t0,$1
    lw t0,SCENE_RSP_VCE(zero)
    ctc2 t0,$2
    .irp reg,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
    lw $\reg,(SCENE_RSP_GPR+4*\reg)(zero)
    .endr
    break
    b scene_rsp_restore
    nop
