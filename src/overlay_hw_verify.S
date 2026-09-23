/*
    Real-N64 PR#13 fixed-slot renderer overlay correctness/stability verifier.

    Built only with OVERLAY_HW_VERIFY=1. The guest performs one visible-frame
    Mode1 -> Mode7 -> Mode1 transition. RSP-side diagnostic counters increment
    only after each overlay DMA returns. At a post-rsp_wait quiescent boundary
    this verifier records guest/RSP/slot state to SRAM and freezes GREEN/RED.

    This build is correctness/stability evidence only. It must not be used for
    cadence/performance conclusions because the verifier changes runtime work.
*/

#include "defines.h"

#ifdef SODIUM64_OVERLAY_HW_VERIFY

#define OVERLAY_HW_MAGIC       0x5336344F /* "S64O" */
#define OVERLAY_HW_VERSION     1
#define OVERLAY_HW_TEST_ID     0x4F564D31 /* "OVM1" */
#define OVERLAY_HW_RECORD_SIZE 0x80
#define OVERLAY_REGULAR_WORD   0x91670E64

#define OF_PASS          0x00000001
#define OF_GUEST_DONE    0x00000002
#define OF_SAME_FRAME    0x00000004
#define OF_BG_REGULAR    0x00000008
#define OF_SP_HALT       0x00000010
#define OF_DMA_IDLE      0x00000020
#define OF_SLOT_REGULAR  0x00000040
#define OF_LOADS_EXACT   0x00000080
#define OF_FB_VALID      0x00000100
#define OF_REQUIRED      0x000001FE

#define OR_MAGIC         0x00
#define OR_VERSION       0x04
#define OR_TEST_ID       0x08
#define OR_COMPLETE      0x0C
#define OR_FLAGS         0x10
#define OR_GUEST_COUNTER 0x14
#define OR_PHASE         0x18
#define OR_IRQ_COUNT     0x1C
#define OR_GUEST_MODE    0x20
#define OR_TEST_DONE     0x24
#define OR_IRQ1_FRAME    0x28
#define OR_IRQ2_FRAME    0x2C
#define OR_BG_MODE       0x30
#define OR_FRAME_COUNT   0x34
#define OR_SP_STATUS     0x38
#define OR_DMA_FULL      0x3C
#define OR_DMA_BUSY      0x40
#define OR_SP_PC         0x44
#define OR_SLOT_WORD     0x48
#define OR_MODE7_DONE    0x4C
#define OR_MAIN_DONE     0x50
#define OR_FRAMEBUFFER   0x54
#define OR_DP_STATUS     0x58
#define OR_EXPECT_SLOT   0x5C
#define OR_CHECKSUM      0x60
#define OR_SIZE          0x64
#define OR_END           0x68

.globl overlay_hw_verify_hook
.globl overlay_hw_call_spill

.data
.align 4
overlay_hw_call_spill: .word 0:7 // ra,t4,t5,t6,t7,t8,t9

.text
.set noreorder

/*
 * a0 = just-completed framebuffer pointer from DMEM(FRAMEBUFFER)(t6)
 *
 * Return until the guest has completed its same-frame IRQ chain. Once complete,
 * capture exactly once, commit SRAM, paint the captured framebuffer, and freeze.
 */
.align 5
overlay_hw_verify_hook:
    la t0, wram
    lbu t1, 4(t0)          // test_done
    li t2, 1
    bne t1, t2, overlay_hw_return
    nop
    lbu t1, 1(t0)          // phase
    li t2, 0x33
    bne t1, t2, overlay_hw_return
    nop

    // The hook itself is after rsp_wait, but re-check HALT before SP IMEM reads.
    lw t1, 0xA4040010
    andi t2, t1, 0x1
    beqz t2, overlay_hw_return
    nop

    // From here the diagnostic intentionally never returns.
    move s1, a0
    la s0, sram

    move t0, s0
    li t1, OVERLAY_HW_RECORD_SIZE / 4
overlay_hw_clear:
    sw zero, (t0)
    addiu t0, t0, 4
    addiu t1, t1, -1
    bnez t1, overlay_hw_clear
    nop

    li t0, OVERLAY_HW_MAGIC
    sw t0, OR_MAGIC(s0)
    li t0, OVERLAY_HW_VERSION
    sw t0, OR_VERSION(s0)
    li t0, OVERLAY_HW_TEST_ID
    sw t0, OR_TEST_ID(s0)
    li t0, OVERLAY_REGULAR_WORD
    sw t0, OR_EXPECT_SLOT(s0)
    li t0, OVERLAY_HW_RECORD_SIZE
    sw t0, OR_SIZE(s0)
    li t0, 0x454E4421    // END!
    sw t0, OR_END(s0)

    // Guest evidence.
    la t0, wram
    lbu t1, 0(t0)
    sw t1, OR_GUEST_COUNTER(s0)
    lbu t2, 1(t0)
    sw t2, OR_PHASE(s0)
    lbu t3, 2(t0)
    sw t3, OR_IRQ_COUNT(s0)
    lbu t4, 3(t0)
    sw t4, OR_GUEST_MODE(s0)
    lbu t5, 4(t0)
    sw t5, OR_TEST_DONE(s0)
    lbu t6, 5(t0)
    sw t6, OR_IRQ1_FRAME(s0)
    lbu t7, 6(t0)
    sw t7, OR_IRQ2_FRAME(s0)

    lbu t8, bg_mode
    sw t8, OR_BG_MODE(s0)
    lbu t9, frame_count
    sw t9, OR_FRAME_COUNT(s0)

    // Hardware state at the same post-rsp_wait boundary.
    lw t0, 0xA4040010
    sw t0, OR_SP_STATUS(s0)
    lw t1, 0xA4040014
    sw t1, OR_DMA_FULL(s0)
    lw t2, 0xA4040018
    sw t2, OR_DMA_BUSY(s0)
    lw t3, 0xA4080000
    sw t3, OR_SP_PC(s0)
    lw t4, 0xA40013A8
    sw t4, OR_SLOT_WORD(s0)
    lw t5, DMEM(OVERLAY_HW_MODE7_DONE)
    sw t5, OR_MODE7_DONE(s0)
    lw t6, DMEM(OVERLAY_HW_MAIN_DONE)
    sw t6, OR_MAIN_DONE(s0)
    sw s1, OR_FRAMEBUFFER(s0)
    lw t7, 0xA410000C
    sw t7, OR_DP_STATUS(s0)

    // Build validity flags from independently recorded observations.
    move t8, zero

    li t9, 0x33
    bne t2, t2, overlay_hw_guest_done_check // deterministic no-op branch target setup
    nop
overlay_hw_guest_done_check:
    lw t1, OR_PHASE(s0)
    bne t1, t9, overlay_hw_guest_bad
    nop
    lw t1, OR_IRQ_COUNT(s0)
    li t9, 2
    bne t1, t9, overlay_hw_guest_bad
    nop
    lw t1, OR_GUEST_MODE(s0)
    li t9, 1
    bne t1, t9, overlay_hw_guest_bad
    nop
    lw t1, OR_TEST_DONE(s0)
    bne t1, t9, overlay_hw_guest_bad
    nop
    ori t8, t8, OF_GUEST_DONE
overlay_hw_guest_bad:

    lw t1, OR_IRQ1_FRAME(s0)
    lw t2, OR_IRQ2_FRAME(s0)
    bne t1, t2, overlay_hw_not_same
    nop
    li t3, 30
    bne t1, t3, overlay_hw_not_same
    nop
    ori t8, t8, OF_SAME_FRAME
overlay_hw_not_same:

    lw t1, OR_BG_MODE(s0)
    li t2, 1
    bne t1, t2, overlay_hw_not_bg
    nop
    ori t8, t8, OF_BG_REGULAR
overlay_hw_not_bg:

    lw t1, OR_SP_STATUS(s0)
    andi t1, t1, 1
    beqz t1, overlay_hw_not_halt
    nop
    ori t8, t8, OF_SP_HALT
overlay_hw_not_halt:

    lw t1, OR_DMA_FULL(s0)
    bnez t1, overlay_hw_not_dma_idle
    nop
    lw t1, OR_DMA_BUSY(s0)
    bnez t1, overlay_hw_not_dma_idle
    nop
    ori t8, t8, OF_DMA_IDLE
overlay_hw_not_dma_idle:

    lw t1, OR_SLOT_WORD(s0)
    li t2, OVERLAY_REGULAR_WORD
    bne t1, t2, overlay_hw_not_slot
    nop
    ori t8, t8, OF_SLOT_REGULAR
overlay_hw_not_slot:

    lw t1, OR_MODE7_DONE(s0)
    li t2, 1
    bne t1, t2, overlay_hw_not_loads
    nop
    lw t1, OR_MAIN_DONE(s0)
    bne t1, t2, overlay_hw_not_loads
    nop
    ori t8, t8, OF_LOADS_EXACT
overlay_hw_not_loads:

    li t1, FRAMEBUFFER1
    beq s1, t1, overlay_hw_fb_ok
    nop
    li t1, FRAMEBUFFER2
    beq s1, t1, overlay_hw_fb_ok
    nop
    li t1, FRAMEBUFFER3
    bne s1, t1, overlay_hw_fb_bad
    nop
overlay_hw_fb_ok:
    ori t8, t8, OF_FB_VALID
overlay_hw_fb_bad:
    sw t8, OR_FLAGS(s0)

    andi t1, t8, OF_REQUIRED
    li t2, OF_REQUIRED
    bne t1, t2, overlay_hw_result_ready
    nop
    ori t8, t8, OF_PASS
    sw t8, OR_FLAGS(s0)

overlay_hw_result_ready:
    li t1, 1
    sw t1, OR_COMPLETE(s0)

    // XOR checksum over the entire record except OR_CHECKSUM.
    move t1, zero
    move t2, s0
    li t3, OVERLAY_HW_RECORD_SIZE / 4
    move t4, zero
overlay_hw_checksum:
    beq t4, OR_CHECKSUM, overlay_hw_checksum_skip
    nop
    lw t5, (t2)
    xor t1, t1, t5
overlay_hw_checksum_skip:
    addiu t2, t2, 4
    addiu t4, t4, 4
    addiu t3, t3, -1
    bnez t3, overlay_hw_checksum
    nop
    sw t1, OR_CHECKSUM(s0)

    // PI reads RDRAM: write back the exact record before cart DMA.
    move t1, s0
    addiu t2, s0, OVERLAY_HW_RECORD_SIZE
overlay_hw_flush:
    cache 0x19, 0(t1)
    addiu t1, t1, 0x10
    bne t1, t2, overlay_hw_flush
    nop

    lui t1, 0xA460
overlay_hw_pi_idle:
    lw t2, 0x0010(t1)
    andi t2, t2, 1
    bnez t2, overlay_hw_pi_idle
    nop
    sw s0, 0x0000(t1)
    li t2, 0x08000000
    sw t2, 0x0004(t1)
    li t2, OVERLAY_HW_RECORD_SIZE - 1
    sw t2, 0x0008(t1)
overlay_hw_pi_wait:
    lw t2, 0x0010(t1)
    andi t2, t2, 1
    bnez t2, overlay_hw_pi_wait
    nop

    // Evidence committed. Indicator is secondary; wait for RDP before painting.
    mtc0 zero, $12
overlay_hw_dp_wait:
    lw t1, 0xA410000C
    andi t1, t1, 0x70
    bnez t1, overlay_hw_dp_wait
    nop

    lw t1, OR_FLAGS(s0)
    andi t1, t1, OF_PASS
    beqz t1, overlay_hw_red
    nop
    li t2, 0x07C107C1
    b overlay_hw_fill
    nop
overlay_hw_red:
    li t2, 0xF801F801

overlay_hw_fill:
    move t0, s1
    li t3, 33600
overlay_hw_fill_loop:
    sw t2, (t0)
    addiu t0, t0, 4
    addiu t3, t3, -1
    bnez t3, overlay_hw_fill_loop
    nop

    lui t0, 0xA440
    sw s1, 0x0004(t0)

overlay_hw_done:
    b overlay_hw_done
    nop

overlay_hw_return:
    jr ra
    nop

#endif
