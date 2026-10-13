/* SPDX-License-Identifier: GPL-3.0-or-later
 * Pause-only context reconstruction hypothesis. CPU backs up/restores all
 * IMEM/DMEM and the halted PC. No DMA/RDP/guest work is issued here. */
#include <rsp.inc>
#include "defines.h"
.data
.word 0
.text
.set noreorder
.set noat
scene_rsp_rebind:
    .irp reg,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
    or $\reg,zero,zero
    .endr
    .irp vec,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31
    .word 0x4a00002c | (\vec << 16) | (\vec << 11) | (\vec << 6)
    .endr
    ctc2 zero,$0
    ctc2 zero,$1
    ctc2 zero,$2
    vmudl $v00,$v00,$v00,0
    lqv $v23,0,-0x90,zero
    lqv $v24,0,-0x80,zero
    lqv $v25,0,-0x70,zero
    lqv $v26,0,-0x60,zero
    lqv $v27,0,-0x50,zero
    lqv $v28,0,-0x40,zero
    lqv $v29,0,-0x30,zero
    lqv $v30,0,-0x20,zero
    lqv $v31,0,-0x10,zero
    lw sp,0(zero)
    break
    b scene_rsp_rebind
    nop
