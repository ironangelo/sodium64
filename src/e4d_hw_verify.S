/*
    Real-N64 E4d resident color-math correctness verifier.

    This file is built only with E4D_HW_VERIFY=1. It deliberately runs after
    rsp_wait observes SP HALT and before update_menu touches the completed
    framebuffer. Correctness evidence is written to cartridge SRAM; timing from
    this build is not a performance/cadence measurement.
*/

#include "defines.h"

#ifdef SODIUM64_E4D_HW_VERIFY

#define E4D_HW_MAGIC          0x53363445 /* "S64E" */
#define E4D_HW_VERSION        1
#define E4D_HW_TEST_ID        0x45344431 /* "E4D1" */
#define E4D_HW_RECORD_SIZE    0x80

#define E4D_FLAG_PASS         0x00000001
#define E4D_FLAG_FRESH        0x00000002
#define E4D_FLAG_SP_HALT      0x00000004
#define E4D_FLAG_DP_IDLE      0x00000008
#define E4D_FLAG_FB_VALID     0x00000010

#define E4D_SENTINEL          0x294B
#define E4D_BLUE              0x001F
#define E4D_RED               0x7801
#define E4D_YELLOW            0x7BC1

#define REC_MAGIC             0x00
#define REC_VERSION           0x04
#define REC_TEST_ID           0x08
#define REC_COMPLETE          0x0C
#define REC_FLAGS             0x10
#define REC_BASELINE_COUNTER  0x14
#define REC_FINAL_COUNTER     0x18
#define REC_COUNTER_DELTA     0x1C
#define REC_SP_STATUS         0x20
#define REC_DP_STATUS         0x24
#define REC_FRAMEBUFFER       0x28
#define REC_ACTIVE_MISMATCH   0x2C
#define REC_BORDER_MISMATCH   0x30
#define REC_BLUE_COUNT        0x34
#define REC_RED_COUNT         0x38
#define REC_YELLOW_COUNT      0x3C
#define REC_OTHER_COUNT       0x40
#define REC_FIRST_ACTIVE_XY   0x44
#define REC_FIRST_ACTIVE_AE   0x48
#define REC_FIRST_BORDER_XY   0x4C
#define REC_FIRST_BORDER_AE   0x50
#define REC_SEED_SP_STATUS    0x54
#define REC_SEED_DP_STATUS    0x58
#define REC_SEED_COUNTER      0x5C
#define REC_EXPECT_ACTIVE     0x60
#define REC_EXPECT_BORDER     0x64
#define REC_SEED_STAGE        0x68
#define REC_RESERVED          0x6C
#define REC_CHECKSUM          0x70
#define REC_SIZE              0x74
#define REC_SENTINEL          0x78
#define REC_END               0x7C

.globl e4d_hw_verify_hook

.data
.align 4
e4d_hw_state:       .word 0
e4d_hw_baseline:    .word 0
e4d_hw_seed_sp:     .word 0
e4d_hw_seed_dp:     .word 0

.text
.set noreorder

/*
 * a0 = completed framebuffer pointer from DMEM(FRAMEBUFFER)(t6)
 *
 * Stage 0: after guest counter >= 5 at a quiescent post-rsp_wait boundary,
 * seed physical rows 0..23 in all three framebuffers with E4D_SENTINEL and
 * remember the guest counter.
 *
 * Stage 1: at the very next completed frame, capture quiescence/freshness,
 * validate the exact 4096 active + 2624 border pixels, write S64E to SRAM,
 * paint PASS green / FAIL red, and freeze.
 */
.align 5
e4d_hw_verify_hook:
    la t0, e4d_hw_state
    lw t1, (t0)
    bnez t1, e4d_hw_verify_frame
    nop

    // Warmup gate: deterministic guest NMI counter lives at WRAM $7E0000.
    la t0, wram
    lbu t1, (t0)
    sltiu t2, t1, 5
    bnez t2, e4d_hw_return
    nop

    // Seed only at the same quiescent conditions required by the ares oracle.
    lw t2, 0xA4040010 // SP_STATUS
    andi t3, t2, 0x1
    beqz t3, e4d_hw_return
    nop
    lw t3, 0xA410000C // DP_STATUS
    andi t0, t3, 0x70
    bnez t0, e4d_hw_return
    nop

    la t0, e4d_hw_baseline
    sw t1, (t0)
    la t0, e4d_hw_seed_sp
    sw t2, (t0)
    la t0, e4d_hw_seed_dp
    sw t3, (t0)

    // Seed rows 0..23 (280 * 24 RGB16 pixels) in all three framebuffers.
    li t0, FRAMEBUFFER1
    li t1, 3
    li t2, 0x294B294B
e4d_hw_seed_fb:
    move t8, t0
    li t9, 3360 // (280 * 24 * 2) / 4
e4d_hw_seed_words:
    sw t2, (t8)
    addiu t8, t8, 4
    addiu t9, t9, -1
    bnez t9, e4d_hw_seed_words
    nop
    li t3, FRAMEBUFFER2 - FRAMEBUFFER1
    addu t0, t0, t3
    addiu t1, t1, -1
    bnez t1, e4d_hw_seed_fb
    nop

    la t0, e4d_hw_state
    li t1, 1
    sw t1, (t0)

e4d_hw_return:
    jr ra
    nop

e4d_hw_verify_frame:
    // From here the milestone intentionally never returns.
    move s1, a0

    // Clear the local SRAM record before populating it.
    la s0, sram
    move t0, s0
    li t1, E4D_HW_RECORD_SIZE / 4
e4d_hw_clear_record:
    sw zero, (t0)
    addiu t0, t0, 4
    addiu t1, t1, -1
    bnez t1, e4d_hw_clear_record
    nop

    li t0, E4D_HW_MAGIC
    sw t0, REC_MAGIC(s0)
    li t0, E4D_HW_VERSION
    sw t0, REC_VERSION(s0)
    li t0, E4D_HW_TEST_ID
    sw t0, REC_TEST_ID(s0)

    // Capture provenance before any verifier-side waiting or framebuffer writes.
    lw t0, 0xA4040010
    sw t0, REC_SP_STATUS(s0)
    lw t1, 0xA410000C
    sw t1, REC_DP_STATUS(s0)
    sw s1, REC_FRAMEBUFFER(s0)

    la t2, e4d_hw_seed_sp
    lw t2, (t2)
    sw t2, REC_SEED_SP_STATUS(s0)
    la t2, e4d_hw_seed_dp
    lw t2, (t2)
    sw t2, REC_SEED_DP_STATUS(s0)

    la t2, e4d_hw_baseline
    lw t2, (t2)
    sw t2, REC_BASELINE_COUNTER(s0)
    sw t2, REC_SEED_COUNTER(s0)
    la t3, wram
    lbu t3, (t3)
    sw t3, REC_FINAL_COUNTER(s0)
    subu t4, t3, t2
    andi t4, t4, 0xFF
    sw t4, REC_COUNTER_DELTA(s0)

    // Build validity flags. Pixel pass is added only after the full scan.
    move t5, zero
    beqz t4, e4d_hw_no_fresh
    nop
    ori t5, t5, E4D_FLAG_FRESH
e4d_hw_no_fresh:
    andi t6, t0, 0x1
    beqz t6, e4d_hw_no_halt
    nop
    ori t5, t5, E4D_FLAG_SP_HALT
e4d_hw_no_halt:
    andi t6, t1, 0x70
    bnez t6, e4d_hw_no_dp_idle
    nop
    ori t5, t5, E4D_FLAG_DP_IDLE
e4d_hw_no_dp_idle:

    li t6, FRAMEBUFFER1
    beq s1, t6, e4d_hw_fb_valid
    nop
    li t6, FRAMEBUFFER2
    beq s1, t6, e4d_hw_fb_valid
    nop
    li t6, FRAMEBUFFER3
    bne s1, t6, e4d_hw_fb_invalid
    nop
e4d_hw_fb_valid:
    ori t5, t5, E4D_FLAG_FB_VALID
e4d_hw_fb_invalid:
    sw t5, REC_FLAGS(s0)

    li t0, 4096
    sw t0, REC_EXPECT_ACTIVE(s0)
    li t0, 2624
    sw t0, REC_EXPECT_BORDER(s0)
    li t0, 1
    sw t0, REC_SEED_STAGE(s0)
    li t0, E4D_HW_RECORD_SIZE
    sw t0, REC_SIZE(s0)
    li t0, E4D_SENTINEL
    sw t0, REC_SENTINEL(s0)
    li t0, 0x454E4421 // "END!"
    sw t0, REC_END(s0)

    // Invalid framebuffer pointers are recorded without dereferencing them.
    andi t0, t5, E4D_FLAG_FB_VALID
    beqz t0, e4d_hw_invalid_fb_counts
    nop

    move s2, zero // active mismatches
    move s3, zero // border mismatches
    move s4, zero // blue count
    move s5, zero // red count
    move s6, zero // yellow count
    move s7, zero // other count
    li t8, -1
    sw t8, REC_FIRST_ACTIVE_XY(s0)
    sw t8, REC_FIRST_BORDER_XY(s0)

    // Top border: physical rows 0..7, all 280 pixels.
    move t0, s1
    li t1, 2240
    move t2, zero // linear pixel index for x/y reconstruction
e4d_hw_top_border:
    lhu t3, (t0)
    li t4, E4D_SENTINEL
    beq t3, t4, e4d_hw_top_ok
    nop
    addiu s3, s3, 1
    lw t5, REC_FIRST_BORDER_XY(s0)
    li t6, -1
    bne t5, t6, e4d_hw_top_ok
    nop
    // y = index / 280, x = index % 280 (slow path only on first mismatch).
    li t5, 280
    divu t2, t5
    mflo t6
    mfhi t7
    sll t6, t6, 16
    or t6, t6, t7
    sw t6, REC_FIRST_BORDER_XY(s0)
    sll t3, t3, 16
    ori t3, t3, E4D_SENTINEL
    sw t3, REC_FIRST_BORDER_AE(s0)
e4d_hw_top_ok:
    addiu t0, t0, 2
    addiu t2, t2, 1
    addiu t1, t1, -1
    bnez t1, e4d_hw_top_border
    nop

    // Rows 8..23: left 12px border, 256px active, right 12px border.
    li t1, 8 // physical y
e4d_hw_row_loop:
    // Left border.
    li t2, 12
    move t3, zero // x
e4d_hw_left_border:
    lhu t4, (t0)
    li t5, E4D_SENTINEL
    beq t4, t5, e4d_hw_left_ok
    nop
    addiu s3, s3, 1
    lw t6, REC_FIRST_BORDER_XY(s0)
    li t7, -1
    bne t6, t7, e4d_hw_left_ok
    nop
    sll t6, t1, 16
    or t6, t6, t3
    sw t6, REC_FIRST_BORDER_XY(s0)
    sll t4, t4, 16
    ori t4, t4, E4D_SENTINEL
    sw t4, REC_FIRST_BORDER_AE(s0)
e4d_hw_left_ok:
    addiu t0, t0, 2
    addiu t3, t3, 1
    addiu t2, t2, -1
    bnez t2, e4d_hw_left_border
    nop

    // Active 256 pixels. Tile state comes from the frozen synthetic guest:
    // rows 8..15: (tile ^ 3) & 3
    // rows16..23: (tile ^ 1) & 3
    li t2, 256
    li t3, 12 // x
e4d_hw_active:
    lhu t4, (t0)
    addiu t6, t3, -12
    srl t6, t6, 3 // tile 0..31
    sltiu t7, t1, 16
    beqz t7, e4d_hw_row_xor1
    li t7, 3
    b e4d_hw_state_ready
    xor t6, t6, t7
e4d_hw_row_xor1:
    li t7, 1
    xor t6, t6, t7
e4d_hw_state_ready:
    andi t6, t6, 3
    li t7, E4D_BLUE
    li t8, 3
    beq t6, t8, e4d_hw_expect_yellow
    nop
    li t8, 1
    beq t6, t8, e4d_hw_expect_red
    nop
    b e4d_hw_expected_ready
    nop
e4d_hw_expect_yellow:
    li t7, E4D_YELLOW
    b e4d_hw_expected_ready
    nop
e4d_hw_expect_red:
    li t7, E4D_RED
e4d_hw_expected_ready:

    // Histogram actual active colors.
    li t8, E4D_BLUE
    beq t4, t8, e4d_hw_count_blue
    nop
    li t8, E4D_RED
    beq t4, t8, e4d_hw_count_red
    nop
    li t8, E4D_YELLOW
    beq t4, t8, e4d_hw_count_yellow
    nop
    addiu s7, s7, 1
    b e4d_hw_hist_done
    nop
e4d_hw_count_blue:
    addiu s4, s4, 1
    b e4d_hw_hist_done
    nop
e4d_hw_count_red:
    addiu s5, s5, 1
    b e4d_hw_hist_done
    nop
e4d_hw_count_yellow:
    addiu s6, s6, 1
e4d_hw_hist_done:

    beq t4, t7, e4d_hw_active_ok
    nop
    addiu s2, s2, 1
    lw t8, REC_FIRST_ACTIVE_XY(s0)
    li t9, -1
    bne t8, t9, e4d_hw_active_ok
    nop
    sll t8, t1, 16
    or t8, t8, t3
    sw t8, REC_FIRST_ACTIVE_XY(s0)
    sll t4, t4, 16
    or t4, t4, t7
    sw t4, REC_FIRST_ACTIVE_AE(s0)
e4d_hw_active_ok:
    addiu t0, t0, 2
    addiu t3, t3, 1
    addiu t2, t2, -1
    bnez t2, e4d_hw_active
    nop

    // Right border.
    li t2, 12
e4d_hw_right_border:
    lhu t4, (t0)
    li t5, E4D_SENTINEL
    beq t4, t5, e4d_hw_right_ok
    nop
    addiu s3, s3, 1
    lw t6, REC_FIRST_BORDER_XY(s0)
    li t7, -1
    bne t6, t7, e4d_hw_right_ok
    nop
    sll t6, t1, 16
    or t6, t6, t3
    sw t6, REC_FIRST_BORDER_XY(s0)
    sll t4, t4, 16
    ori t4, t4, E4D_SENTINEL
    sw t4, REC_FIRST_BORDER_AE(s0)
e4d_hw_right_ok:
    addiu t0, t0, 2
    addiu t3, t3, 1
    addiu t2, t2, -1
    bnez t2, e4d_hw_right_border
    nop

    addiu t1, t1, 1
    sltiu t2, t1, 24
    bnez t2, e4d_hw_row_loop
    nop

    sw s2, REC_ACTIVE_MISMATCH(s0)
    sw s3, REC_BORDER_MISMATCH(s0)
    sw s4, REC_BLUE_COUNT(s0)
    sw s5, REC_RED_COUNT(s0)
    sw s6, REC_YELLOW_COUNT(s0)
    sw s7, REC_OTHER_COUNT(s0)
    b e4d_hw_finish_result
    nop

e4d_hw_invalid_fb_counts:
    li t0, -1
    sw t0, REC_ACTIVE_MISMATCH(s0)
    sw t0, REC_BORDER_MISMATCH(s0)
    sw t0, REC_FIRST_ACTIVE_XY(s0)
    sw t0, REC_FIRST_BORDER_XY(s0)

e4d_hw_finish_result:
    // PASS requires fresh guest progress, HALT, DP idle, valid framebuffer and
    // exact active+border pixels. Expected color histogram is implied by the
    // exact spatial oracle but retained for diagnosis.
    lw t0, REC_FLAGS(s0)
    andi t1, t0, 0x1E
    li t2, 0x1E
    bne t1, t2, e4d_hw_result_ready
    nop
    lw t1, REC_ACTIVE_MISMATCH(s0)
    bnez t1, e4d_hw_result_ready
    nop
    lw t1, REC_BORDER_MISMATCH(s0)
    bnez t1, e4d_hw_result_ready
    nop
    ori t0, t0, E4D_FLAG_PASS
    sw t0, REC_FLAGS(s0)

e4d_hw_result_ready:
    li t1, 1
    sw t1, REC_COMPLETE(s0)

    // XOR checksum over all record words except REC_CHECKSUM itself.
    move t1, zero
    move t2, s0
    li t3, E4D_HW_RECORD_SIZE / 4
    li t4, 0
e4d_hw_checksum:
    beq t4, REC_CHECKSUM, e4d_hw_checksum_skip
    nop
    lw t5, (t2)
    xor t1, t1, t5
e4d_hw_checksum_skip:
    addiu t2, t2, 4
    addiu t4, t4, 4
    addiu t3, t3, -1
    bnez t3, e4d_hw_checksum
    nop
    sw t1, REC_CHECKSUM(s0)

    // PI reads RDRAM, so write back the exact 128-byte record first.
    move t1, s0
    addiu t2, s0, E4D_HW_RECORD_SIZE
e4d_hw_flush_record:
    cache 0x19, 0(t1)
    addiu t1, t1, 0x10
    bne t1, t2, e4d_hw_flush_record
    nop

    lui t1, 0xA460
e4d_hw_pi_idle:
    lw t2, 0x0010(t1)
    andi t2, t2, 0x1
    bnez t2, e4d_hw_pi_idle
    nop
    sw s0, 0x0000(t1) // PI_DRAM_ADDR
    li t2, 0x08000000
    sw t2, 0x0004(t1) // PI_CART_ADDR
    li t2, E4D_HW_RECORD_SIZE - 1
    sw t2, 0x0008(t1) // PI_RD_LEN: RDRAM -> cart
e4d_hw_pi_wait:
    lw t2, 0x0010(t1)
    andi t2, t2, 0x1
    bnez t2, e4d_hw_pi_wait
    nop

    // Evidence is committed. From here the screen is only a completion signal.
    mtc0 zero, $12 // disable interrupts
    li t1, 0x00000002
    sw t1, 0xA4040010 // force RSP HALT

    // If the captured DP state was busy, allow it to drain only after recording
    // that fact so the indicator fill cannot race an in-flight RDP command.
e4d_hw_indicator_dp_wait:
    lw t1, 0xA410000C
    andi t1, t1, 0x70
    bnez t1, e4d_hw_indicator_dp_wait
    nop

    lw t1, REC_FLAGS(s0)
    andi t1, t1, E4D_FLAG_PASS
    beqz t1, e4d_hw_indicator_red
    nop
    li t2, 0x07C107C1
    b e4d_hw_indicator_fill
    nop
e4d_hw_indicator_red:
    li t2, 0xF801F801

e4d_hw_indicator_fill:
    move t0, s1
    li t3, 33600 // (280 * 240 * 2) / 4
e4d_hw_indicator_loop:
    sw t2, (t0)
    addiu t0, t0, 4
    addiu t3, t3, -1
    bnez t3, e4d_hw_indicator_loop
    nop

    lui t0, 0xA440
    sw s1, 0x0004(t0) // VI_ORIGIN = verified framebuffer

e4d_hw_done:
    b e4d_hw_done
    nop

#endif
