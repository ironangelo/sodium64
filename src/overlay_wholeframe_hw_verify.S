/*
    Real-N64 PR#13 whole-frame fixed-slot overlay verifier (OVM2).

    This is an R4300-side diagnostic only. RSP microcode is the exact PR#13
    candidate: no counters or proof instructions are inserted into either
    renderer overlay.

    The guest holds Mode1 for 60 NMIs, Mode7 for 60, then returns to Mode1.
    At post-rsp_wait quiescent boundaries we capture the physical SP IMEM
    renderer-slot signature during a stable Mode7 treatment phase and again
    after the stable return to Mode1. Only the second stage commits SRAM.
*/

#include "defines.h"

#ifdef SODIUM64_OVERLAY_WHOLEFRAME_HW_VERIFY

#define OW_MAGIC             0x5336344F /* S64O */
#define OW_VERSION           1
#define OW_TEST_ID           0x4F564D32 /* OVM2 */
#define OW_RECORD_SIZE       0x80
#define OW_MODE7_WORD        0x1000024E
#define OW_REGULAR_WORD      0x91670E64

#define OF_PASS              0x00000001
#define OF_TREAT_GUEST       0x00000002
#define OF_TREAT_BG          0x00000004
#define OF_TREAT_SP          0x00000008
#define OF_TREAT_DMA         0x00000010
#define OF_TREAT_SLOT        0x00000020
#define OF_TREAT_FB          0x00000040
#define OF_RETURN_GUEST      0x00000080
#define OF_RETURN_BG         0x00000100
#define OF_RETURN_SP         0x00000200
#define OF_RETURN_DMA        0x00000400
#define OF_RETURN_SLOT       0x00000800
#define OF_RETURN_FB         0x00001000
#define OF_REQUIRED          0x00001FFE

#define OR_MAGIC             0x00
#define OR_VERSION           0x04
#define OR_TEST_ID           0x08
#define OR_COMPLETE          0x0C
#define OR_FLAGS             0x10
#define OR_STAGE             0x14
#define OR_T_COUNTER         0x18
#define OR_T_GUEST_MODE      0x1C
#define OR_T_BG_MODE         0x20
#define OR_T_SP_STATUS       0x24
#define OR_T_DMA_FULL        0x28
#define OR_T_DMA_BUSY        0x2C
#define OR_T_SLOT            0x30
#define OR_T_FB              0x34
#define OR_T_DP_STATUS       0x38
#define OR_R_COUNTER         0x3C
#define OR_R_GUEST_MODE      0x40
#define OR_R_BG_MODE         0x44
#define OR_R_SP_STATUS       0x48
#define OR_R_DMA_FULL        0x4C
#define OR_R_DMA_BUSY        0x50
#define OR_R_SLOT            0x54
#define OR_R_FB              0x58
#define OR_R_DP_STATUS       0x5C
#define OR_EXPECT_MODE7      0x60
#define OR_EXPECT_REGULAR    0x64
#define OR_CHECKSUM          0x68
#define OR_SIZE              0x6C
#define OR_END               0x70

.globl overlay_wholeframe_verify_hook
.globl overlay_wholeframe_call_spill

.data
.align 4
overlay_wholeframe_state:       .word 0
overlay_wholeframe_call_spill:  .word 0:7
overlay_wholeframe_t_counter:   .word 0
overlay_wholeframe_t_guest:     .word 0
overlay_wholeframe_t_bg:        .word 0
overlay_wholeframe_t_sp:        .word 0
overlay_wholeframe_t_full:      .word 0
overlay_wholeframe_t_busy:      .word 0
overlay_wholeframe_t_slot:      .word 0
overlay_wholeframe_t_fb:        .word 0
overlay_wholeframe_t_dp:        .word 0

.text
.set noreorder

overlay_wholeframe_verify_hook:
    la t0, overlay_wholeframe_state
    lw t1, (t0)
    bnez t1, overlay_wholeframe_return_stage
    nop

    // Treatment capture: wait well inside the 60-frame Mode7 phase.
    la t2, wram
    lbu t3, 1(t2)
    li t4, 7
    bne t3, t4, overlay_wholeframe_return
    nop
    lbu t5, 0(t2)
    sltiu t6, t5, 70
    bnez t6, overlay_wholeframe_return
    nop
    lbu t6, bg_mode
    bne t6, t4, overlay_wholeframe_return
    nop

    // Capture only at a physically quiescent SP boundary.
    lw t7, 0xA4040010
    andi t8, t7, 1
    beqz t8, overlay_wholeframe_return
    nop
    lw t8, 0xA4040014
    bnez t8, overlay_wholeframe_return
    nop
    lw t9, 0xA4040018
    bnez t9, overlay_wholeframe_return
    nop

    la t2, overlay_wholeframe_t_counter
    sw t5, 0(t2)
    sw t3, 4(t2)
    sw t6, 8(t2)
    sw t7, 12(t2)
    sw t8, 16(t2)
    sw t9, 20(t2)
    lw t3, 0xA40013A8
    sw t3, 24(t2)
    sw a0, 28(t2)
    lw t3, 0xA410000C
    sw t3, 32(t2)

    li t1, 1
    sw t1, (t0)
    b overlay_wholeframe_return
    nop

overlay_wholeframe_return_stage:
    // Return capture: state1 guarantees this is the Mode1 phase *after* Mode7.
    la t2, wram
    lbu t3, 1(t2)
    li t4, 1
    bne t3, t4, overlay_wholeframe_return
    nop
    lbu t5, 0(t2)
    sltiu t6, t5, 5
    bnez t6, overlay_wholeframe_return
    nop
    lbu t6, bg_mode
    bne t6, t4, overlay_wholeframe_return
    nop

    lw t7, 0xA4040010
    andi t8, t7, 1
    beqz t8, overlay_wholeframe_return
    nop
    lw t8, 0xA4040014
    bnez t8, overlay_wholeframe_return
    nop
    lw t9, 0xA4040018
    bnez t9, overlay_wholeframe_return
    nop

    // From here C2 intentionally never returns.
    move s1, a0
    la s0, sram

    move t0, s0
    li t1, OW_RECORD_SIZE / 4
overlay_wholeframe_clear:
    sw zero, 0(t0)
    addiu t0, t0, 4
    addiu t1, t1, -1
    bnez t1, overlay_wholeframe_clear
    nop

    li t0, OW_MAGIC
    sw t0, OR_MAGIC(s0)
    li t0, OW_VERSION
    sw t0, OR_VERSION(s0)
    li t0, OW_TEST_ID
    sw t0, OR_TEST_ID(s0)
    li t0, 2
    sw t0, OR_STAGE(s0)
    li t0, OW_MODE7_WORD
    sw t0, OR_EXPECT_MODE7(s0)
    li t0, OW_REGULAR_WORD
    sw t0, OR_EXPECT_REGULAR(s0)
    li t0, OW_RECORD_SIZE
    sw t0, OR_SIZE(s0)
    li t0, 0x454E4421
    sw t0, OR_END(s0)

    // Persist treatment snapshot captured before the return transition.
    la t0, overlay_wholeframe_t_counter
    lw t1, 0(t0)
    sw t1, OR_T_COUNTER(s0)
    lw t1, 4(t0)
    sw t1, OR_T_GUEST_MODE(s0)
    lw t1, 8(t0)
    sw t1, OR_T_BG_MODE(s0)
    lw t1, 12(t0)
    sw t1, OR_T_SP_STATUS(s0)
    lw t1, 16(t0)
    sw t1, OR_T_DMA_FULL(s0)
    lw t1, 20(t0)
    sw t1, OR_T_DMA_BUSY(s0)
    lw t1, 24(t0)
    sw t1, OR_T_SLOT(s0)
    lw t1, 28(t0)
    sw t1, OR_T_FB(s0)
    lw t1, 32(t0)
    sw t1, OR_T_DP_STATUS(s0)

    // Persist return snapshot from this post-rsp_wait boundary.
    sw t5, OR_R_COUNTER(s0)
    sw t3, OR_R_GUEST_MODE(s0)
    sw t6, OR_R_BG_MODE(s0)
    sw t7, OR_R_SP_STATUS(s0)
    sw t8, OR_R_DMA_FULL(s0)
    sw t9, OR_R_DMA_BUSY(s0)
    lw t0, 0xA40013A8
    sw t0, OR_R_SLOT(s0)
    sw s1, OR_R_FB(s0)
    lw t0, 0xA410000C
    sw t0, OR_R_DP_STATUS(s0)

    // Recompute every pass bit from the recorded evidence.
    move t8, zero

    lw t0, OR_T_COUNTER(s0)
    sltiu t1, t0, 70
    bnez t1, overlay_wholeframe_treat_guest_bad
    nop
    lw t0, OR_T_GUEST_MODE(s0)
    li t1, 7
    bne t0, t1, overlay_wholeframe_treat_guest_bad
    nop
    ori t8, t8, OF_TREAT_GUEST
overlay_wholeframe_treat_guest_bad:

    lw t0, OR_T_BG_MODE(s0)
    li t1, 7
    bne t0, t1, overlay_wholeframe_treat_bg_bad
    nop
    ori t8, t8, OF_TREAT_BG
overlay_wholeframe_treat_bg_bad:

    lw t0, OR_T_SP_STATUS(s0)
    andi t0, t0, 1
    beqz t0, overlay_wholeframe_treat_sp_bad
    nop
    ori t8, t8, OF_TREAT_SP
overlay_wholeframe_treat_sp_bad:

    lw t0, OR_T_DMA_FULL(s0)
    bnez t0, overlay_wholeframe_treat_dma_bad
    nop
    lw t0, OR_T_DMA_BUSY(s0)
    bnez t0, overlay_wholeframe_treat_dma_bad
    nop
    ori t8, t8, OF_TREAT_DMA
overlay_wholeframe_treat_dma_bad:

    lw t0, OR_T_SLOT(s0)
    li t1, OW_MODE7_WORD
    bne t0, t1, overlay_wholeframe_treat_slot_bad
    nop
    ori t8, t8, OF_TREAT_SLOT
overlay_wholeframe_treat_slot_bad:

    lw t0, OR_T_FB(s0)
    li t1, FRAMEBUFFER1
    beq t0, t1, overlay_wholeframe_treat_fb_ok
    nop
    li t1, FRAMEBUFFER2
    beq t0, t1, overlay_wholeframe_treat_fb_ok
    nop
    li t1, FRAMEBUFFER3
    bne t0, t1, overlay_wholeframe_treat_fb_bad
    nop
overlay_wholeframe_treat_fb_ok:
    ori t8, t8, OF_TREAT_FB
overlay_wholeframe_treat_fb_bad:

    lw t0, OR_R_COUNTER(s0)
    sltiu t1, t0, 5
    bnez t1, overlay_wholeframe_return_guest_bad
    nop
    lw t0, OR_R_GUEST_MODE(s0)
    li t1, 1
    bne t0, t1, overlay_wholeframe_return_guest_bad
    nop
    ori t8, t8, OF_RETURN_GUEST
overlay_wholeframe_return_guest_bad:

    lw t0, OR_R_BG_MODE(s0)
    li t1, 1
    bne t0, t1, overlay_wholeframe_return_bg_bad
    nop
    ori t8, t8, OF_RETURN_BG
overlay_wholeframe_return_bg_bad:

    lw t0, OR_R_SP_STATUS(s0)
    andi t0, t0, 1
    beqz t0, overlay_wholeframe_return_sp_bad
    nop
    ori t8, t8, OF_RETURN_SP
overlay_wholeframe_return_sp_bad:

    lw t0, OR_R_DMA_FULL(s0)
    bnez t0, overlay_wholeframe_return_dma_bad
    nop
    lw t0, OR_R_DMA_BUSY(s0)
    bnez t0, overlay_wholeframe_return_dma_bad
    nop
    ori t8, t8, OF_RETURN_DMA
overlay_wholeframe_return_dma_bad:

    lw t0, OR_R_SLOT(s0)
    li t1, OW_REGULAR_WORD
    bne t0, t1, overlay_wholeframe_return_slot_bad
    nop
    ori t8, t8, OF_RETURN_SLOT
overlay_wholeframe_return_slot_bad:

    lw t0, OR_R_FB(s0)
    li t1, FRAMEBUFFER1
    beq t0, t1, overlay_wholeframe_return_fb_ok
    nop
    li t1, FRAMEBUFFER2
    beq t0, t1, overlay_wholeframe_return_fb_ok
    nop
    li t1, FRAMEBUFFER3
    bne t0, t1, overlay_wholeframe_return_fb_bad
    nop
overlay_wholeframe_return_fb_ok:
    ori t8, t8, OF_RETURN_FB
overlay_wholeframe_return_fb_bad:
    sw t8, OR_FLAGS(s0)

    andi t0, t8, OF_REQUIRED
    li t1, OF_REQUIRED
    bne t0, t1, overlay_wholeframe_result_ready
    nop
    ori t8, t8, OF_PASS
    sw t8, OR_FLAGS(s0)

overlay_wholeframe_result_ready:
    li t0, 1
    sw t0, OR_COMPLETE(s0)

    // XOR checksum over the exact record except OR_CHECKSUM.
    move t1, zero
    move t2, s0
    li t3, OW_RECORD_SIZE / 4
    move t4, zero
overlay_wholeframe_checksum:
    beq t4, OR_CHECKSUM, overlay_wholeframe_checksum_skip
    nop
    lw t5, 0(t2)
    xor t1, t1, t5
overlay_wholeframe_checksum_skip:
    addiu t2, t2, 4
    addiu t4, t4, 4
    addiu t3, t3, -1
    bnez t3, overlay_wholeframe_checksum
    nop
    sw t1, OR_CHECKSUM(s0)

    // PI reads RDRAM, so write back the record before SRAM DMA.
    move t1, s0
    addiu t2, s0, OW_RECORD_SIZE
overlay_wholeframe_flush:
    cache 0x19, 0(t1)
    addiu t1, t1, 0x10
    bne t1, t2, overlay_wholeframe_flush
    nop

    lui t1, 0xA460
overlay_wholeframe_pi_idle:
    lw t2, 0x0010(t1)
    andi t2, t2, 1
    bnez t2, overlay_wholeframe_pi_idle
    nop
    sw s0, 0x0000(t1)
    li t2, 0x08000000
    sw t2, 0x0004(t1)
    li t2, OW_RECORD_SIZE - 1
    sw t2, 0x0008(t1)
overlay_wholeframe_pi_wait:
    lw t2, 0x0010(t1)
    andi t2, t2, 1
    bnez t2, overlay_wholeframe_pi_wait
    nop

    // Evidence committed. Indicator is secondary.
    mtc0 zero, $12
overlay_wholeframe_dp_wait:
    lw t1, 0xA410000C
    andi t1, t1, 0x70
    bnez t1, overlay_wholeframe_dp_wait
    nop

    lw t1, OR_FLAGS(s0)
    andi t1, t1, OF_PASS
    beqz t1, overlay_wholeframe_red
    nop
    li t2, 0x07C107C1
    b overlay_wholeframe_fill
    nop
overlay_wholeframe_red:
    li t2, 0xF801F801

overlay_wholeframe_fill:
    move t0, s1
    li t3, 33600
overlay_wholeframe_fill_loop:
    sw t2, 0(t0)
    addiu t0, t0, 4
    addiu t3, t3, -1
    bnez t3, overlay_wholeframe_fill_loop
    nop

    lui t0, 0xA440
    sw s1, 0x0004(t0)
overlay_wholeframe_done:
    b overlay_wholeframe_done
    nop

overlay_wholeframe_return:
    jr ra
    nop

#endif
