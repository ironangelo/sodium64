/* Real-console flight recorder. No code/data in ordinary builds.
 * S64D owns cart SRAM only in this separately named NATIVE_DIAG build.
 * Guest SRAM is limited to <=8 KiB; the recorder uses the remaining 24 KiB.
 * No guest ROM/WRAM bytes are compiled into this file. Captured saves are private.
 */
#include "defines.h"
#ifdef SODIUM64_NATIVE_DIAG
#define DIAG_HZ 46875000
#define DIAG_SAMPLE 131071
#ifdef SODIUM64_NATIVE_DIAG_TRACE
#define DIAG_TICK 5859375
#else
#define DIAG_TICK 2343750
#endif
#define DIAG_STALL 93750000
#define DIAG_LIMIT 937500000
#define DBASE UNCACHED(sram)
#define DHDR UNCACHED(sram + 0x2000)
#define DPCS UNCACHED(sram + 0x2200)
#ifdef SODIUM64_NATIVE_DIAG_TRACE
// v4: exact completed-boundary timings for the full interval, plus 8 Hz
// workload observations and all-IRQ module / resident-wait attribution.
// All buffers append only; each overflow is explicit. Exact 24 KiB layout:
// 512 header + 256 EPCs + 1280*12 frames + 160*40 observations + 20*64 seconds.
#define DFRAMES UNCACHED(sram + 0x2600)
#define DEVENTS UNCACHED(sram + 0x6200)
#define DSECONDS UNCACHED(sram + 0x7B00)
#else
#define DPPU UNCACHED(sram + 0x3200)
#define DEVENTS UNCACHED(sram + 0x4200)
#define DSECONDS UNCACHED(sram + 0x7200)
#define DCOUNTERS UNCACHED(sram + 0x7800)
#endif
.globl native_diag_init, native_diag_arm, native_diag_interrupt, native_diag_state
.globl native_diag_done, native_diag_saved, native_diag_save_failed
.globl native_diag_wait_stall_rsp, native_diag_wait_stall_frame
.globl native_diag_ready_text, native_diag_active_text
.data
.align 5
native_diag_state: .word 0:80
.globl native_diag_guest_sram_exp
native_diag_guest_sram_exp: .word 0
.align 5
native_diag_irq_save: .dword 0:12
#ifdef SODIUM64_NATIVE_DIAG_TRACE
native_diag_title: .string "SODIUM64 TRACE 20S"
#else
native_diag_title: .string "SODIUM64 DIAGNOSTIC"
#endif
native_diag_saved_text: .string "CAPTURE SAVED"
native_diag_failed_text: .string "SAVE FAILED"
native_diag_stall_text: .string "FRAME STALL"
native_diag_limit_text: .string "TIME LIMIT"
native_diag_cpu_text: .string "CPU"
native_diag_rsp_text: .string "RSP"
native_diag_dp_text: .string "DP"
native_diag_end_text: .string "END"
native_diag_current_text: .string "CUR"
native_diag_reset_text: .string "RESET TO SAVE FILE"
native_diag_unsupported_text: .string "DIAGNOSTIC UNSUPPORTED"
native_diag_sram_text: .string "GUEST SRAM ABOVE 8KB"
native_diag_normal_text: .string "USE NORMAL EMULATOR"
native_diag_ready_text: .string "START N64: CAPTURE 20S"
native_diag_active_text: .string "RECORDING 20S        "
.text
.set noreorder
.align 5
native_diag_init:
    // Generic template: memory_init records the selected header's SRAM size.
    // Refuse before touching ANY SRAM when the guest needs the recorder area.
    lw t0, native_diag_guest_sram_exp
    sltiu t0, t0, 4
    beqz t0, native_diag_unsupported
    nop
    // Preserve guest SRAM; invalidate recorder aliases before uncached use.
    la t0, sram + 0x2000
    la t1, sram + 0x8000
1:  cache 0x15, (t0)
    addiu t0, t0, 16
    bne t0, t1, 1b
    nop
    la t0, DHDR
    la t1, DBASE + 0x8000
2:  sw zero, (t0)
    addiu t0, t0, 4
    bne t0, t1, 2b
    nop
    la t0, native_diag_state
    la t1, native_diag_state + 320
3:  sw zero, (t0)
    addiu t0, t0, 4
    bne t0, t1, 3b
    nop
    li t0, 20 // Match the MAX normal hardware comparison.
    sb t0, precision_set
    sb zero, skipped_set
    sb zero, layer_set
    sb zero, underclk_set
    li t0, 4
    sb t0, audio_set
    sb t0, counter_set
    li t0, APU_CYCLE
    sb t0, apu_clock
    // Manual capture stays dormant until N64 Start. Timer sampling and wait
    // watchdogs are disabled while navigating to the target scene.
    jr ra
    nop


.align 5
native_diag_unsupported:
    lw s2, framebuffer
    li t0, 0xA0000000
    or s2, s2, t0
    move t0, s2
    li t1, 0x00010001
    li t2, 560 * 240
    addu t2, t2, t0
native_diag_unsupported_clear:
    sw t1, (t0)
    addiu t0, t0, 4
    bne t0, t2, native_diag_unsupported_clear
    nop
    la a0, native_diag_unsupported_text
    li a1, 32 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
    la a0, native_diag_sram_text
    li a1, 48 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
    la a0, native_diag_normal_text
    li a1, 64 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
    b native_diag_done
    nop

native_diag_arm:
    // Called at the completed-frame UI boundary. Only t0..t3/k0/k1 are borrowed;
    // a0 and the renderer's t4/t5/t6 survive. No guest state is reset.
    mfc0 t3, $12
    li t0, -2
    and t0, t3, t0
    mtc0 t0, $12
    nop
    nop
    la t0, native_diag_state
    lw t1, 112(t0)
    bnez t1, native_diag_arm_return
    nop
    la t1, native_diag_state + 320
native_diag_arm_clear:
    sw zero, (t0)
    addiu t0, t0, 4
    bne t0, t1, native_diag_arm_clear
    nop
    la t0, native_diag_state
    mfc0 t1, $9
    sw t1, 0(t0)
    sw t1, 36(t0)
    li t2, DIAG_TICK
    addu t2, t1, t2
    sw t2, 16(t0)
    li t2, DIAG_HZ
    addu t2, t1, t2
    sw t2, 20(t0)
    li t2, DIAG_SAMPLE
    addu t1, t1, t2
    mtc0 t1, $11
    li t1, 1
    sw t1, 112(t0)
native_diag_arm_return:
    ori t3, t3, 0x8000 // Enable Compare only once the capture is armed
    mtc0 t3, $12
    nop
    nop
    jr ra
    nop

// The fast path uses only reserved k0/k1, no HI/LO, at or ordinary GPRs.
// The slower observation path explicitly saves all additional registers it touches.
.align 5
native_diag_interrupt:
    mfc0 k0, $9
    la k1, native_diag_state
    sw k0, 108(k1)
    mfc0 k0, $14
    sw k0, 4(k1)
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    // Keep one of 32 EPCs; every IRQ still enters module / occupancy counters.
    // All occupancy buckets below still count EVERY timer interrupt.
    lw k0, 8(k1)
    andi k0, k0, 31
    bnez k0, native_diag_pc_sampled
    nop
    lw k0, 12(k1)
    sltiu k0, k0, 1024
    beqz k0, native_diag_pc_full
    nop
    lw k0, 12(k1)
    la k1, DPCS
    addu k0, k0, k1
    mfc0 k1, $14
    sw k1, (k0)
    la k1, native_diag_state
    lw k0, 12(k1)
    addiu k0, k0, 4
    sw k0, 12(k1)
    b native_diag_pc_sampled
    nop
native_diag_pc_full:
    la k1, DHDR + 0x12C
    lw k0, (k1)
    ori k0, k0, 2
    sw k0, (k1)
    la k1, native_diag_state
native_diag_pc_sampled:
#else
    lw k0, 12(k1)
    la k1, DPCS
    addu k0, k0, k1
    mfc0 k1, $14
    sw k1, (k0)
    la k1, native_diag_state
    lw k0, 12(k1)
    addiu k0, k0, 4
    andi k0, k0, 0xFFF
    sw k0, 12(k1)
#endif
#ifdef SODIUM64_NATIVE_DIAG_TRACE
native_diag_sample_bookkeeping:
#endif
    lw k0, 8(k1)
    addiu k0, k0, 1
    sw k0, 8(k1)
    lw k0, 64(k1)
    addiu k0, k0, 1
    sw k0, 64(k1)
    // CPU waits are counted independently of RSP/RDP sampled activity.
    lw k0, 4(k1)
    la k1, native_diag_rsp_wait
    subu k0, k0, k1
    sltiu k0, k0, native_diag_rsp_wait_size
    bnez k0, native_diag_bucket_rsp
    nop
    mfc0 k0, $14
    la k1, native_diag_frame_wait
    subu k0, k0, k1
    sltiu k0, k0, native_diag_frame_wait_size
    bnez k0, native_diag_bucket_frame
    nop
    mfc0 k0, $14
    li k1, 0x801C0000
    subu k0, k0, k1
    li k1, 0x40000
    sltu k0, k0, k1
    bnez k0, native_diag_bucket_jit
    nop
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    // VRAM semaphore waits remain a subset of CPU-other for v3 compatibility.
    // Classify EPC only: reading SP_SEMAPHORE here would change ownership.
native_diag_classify_vram:
    mfc0 k0, $14
    la k1, write_vmdatal
    subu k0, k0, k1
    sltiu k0, k0, 16
    bnez k0, native_diag_bucket_vram
    nop
    mfc0 k0, $14
    la k1, write_vmdatah
    subu k0, k0, k1
    sltiu k0, k0, 16
    beqz k0, native_diag_vram_counted
    nop
native_diag_bucket_vram:
    la k1, native_diag_state + 128
    lw k0, (k1)
    addiu k0, k0, 1
    sw k0, (k1)
native_diag_vram_counted:
#endif
    la k1, native_diag_state + 80
    b native_diag_bucket_add
    nop
native_diag_bucket_rsp:
    la k1, native_diag_state + 68
    b native_diag_bucket_add
    nop
native_diag_bucket_frame:
    la k1, native_diag_state + 72
    b native_diag_bucket_add
    nop
native_diag_bucket_jit:
    la k1, native_diag_state + 76
native_diag_bucket_add:
    lw k0, (k1)
    addiu k0, k0, 1
    sw k0, (k1)
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    // Reuse the already selected wait/JIT bucket before static module lookup.
    la k0, native_diag_state + 68
    beq k0, k1, native_diag_module_rsp
    nop
    la k0, native_diag_state + 72
    beq k0, k1, native_diag_module_vi
    nop
    la k0, native_diag_state + 76
    beq k0, k1, native_diag_module_apu
    nop
    b native_diag_module_static
    nop
#endif
native_diag_sp_sample:
    lui k1, 0xA404
    lw k0, 16(k1)
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    la k1, native_diag_state
    sw k0, 300(k1)
    sw zero, 264(k1)
#endif
    andi k0, k0, 1
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    bnez k0, native_diag_rsp_halted_sample
#else
    bnez k0, native_diag_sp_counted
#endif
    nop
    la k1, native_diag_state + 84
    lw k0, (k1)
    addiu k0, k0, 1
    sw k0, (k1)
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    // A stable epoch excludes a concurrent overlay DMA. Slow (>1ms) reads
    // are discarded as unknown, preventing 12-bit epoch wrap ambiguity.
    la k1, native_diag_state
    mfc0 k0, $9
    sw k0, 248(k1)
    lhu k0, DMEM(NATIVE_DIAG_RSP_BANK)
    sw k0, 256(k1)
    lw k0, 0xA4080000
    andi k0, k0, 0xFFF
    sw k0, 260(k1)
    sw k0, 264(k1)
    lhu k0, DMEM(NATIVE_DIAG_RSP_BANK)
    lw k1, 256(k1)
    bne k0, k1, native_diag_rsp_classify
    nop
    andi k0, k0, 8
    bnez k0, native_diag_rsp_classify
    nop
    mfc0 k0, $9
    lw k1, native_diag_state + 248
    subu k0, k0, k1
    li k1, 46875
    sltu k0, k0, k1
    beqz k0, native_diag_rsp_classify
    nop
    lw k0, native_diag_state + 256
    andi k0, k0, 7
    addiu k1, k0, -1
    sltiu k1, k1, 7
    beqz k1, native_diag_rsp_classify
    nop
    sll k0, k0, 12
    lw k1, native_diag_state + 260
    or k0, k0, k1
    la k1, native_diag_state
    sw k0, 264(k1)
native_diag_rsp_classify:
    // Invariant resident waits are identifiable even while a bank is loading.
    lw k0, native_diag_state + 260
    addiu k0, k0, -0xF4C
    sltiu k0, k0, 12
    bnez k0, native_diag_rsp_dma_sample
    nop
    lw k0, native_diag_state + 260
    addiu k0, k0, -0x2D8
    sltiu k0, k0, 24
    bnez k0, native_diag_rsp_fetch_sample
    nop
    lw k0, native_diag_state + 260
    addiu k0, k0, -0x31C
    sltiu k0, k0, 16
    bnez k0, native_diag_rsp_texture_sample
    nop
    // Shared resident helpers are source-known control/drawing, irrespective
    // of which 1000-byte bank currently occupies 0x3A8..0x78F.
    lw k0, native_diag_state + 260
    addiu k0, k0, -0x3A8
    sltiu k0, k0, 0x3E8
    beqz k0, native_diag_rsp_draw_sample
    nop
    lw k0, native_diag_state + 264
    srl k0, k0, 12
    beqz k0, native_diag_rsp_unknown_sample
    nop
    addiu k0, k0, -3
    beqz k0, native_diag_rsp_phase_sample
    nop
    addiu k0, k0, -1
    beqz k0, native_diag_rsp_direct_sample
    nop
    addiu k0, k0, -1
    beqz k0, native_diag_rsp_math_sample
    nop
    addiu k0, k0, -1
    beqz k0, native_diag_rsp_prepare_sample
    nop
    addiu k0, k0, -1
    beqz k0, native_diag_rsp_prepare_sample
    nop
    b native_diag_rsp_draw_sample
    nop
native_diag_rsp_phase_sample:
    lw k0, native_diag_state + 260
    addiu k0, k0, -0x3E4
    sltiu k0, k0, 16
    bnez k0, native_diag_rsp_rdp_sample
    nop
native_diag_rsp_prepare_sample:
    la k1, native_diag_state + 284
    b native_diag_rsp_stage_add
    nop
native_diag_rsp_direct_sample:
    la k1, native_diag_state + 292
    b native_diag_rsp_stage_add
    nop
native_diag_rsp_math_sample:
    la k1, native_diag_state + 288
    b native_diag_rsp_stage_add
    nop
native_diag_rsp_draw_sample:
    la k1, native_diag_state + 296
    b native_diag_rsp_stage_add
    nop
native_diag_rsp_unknown_sample:
    la k1, native_diag_state + 272
    b native_diag_rsp_stage_add
    nop
native_diag_rsp_halted_sample:
    la k1, native_diag_state + 268
    b native_diag_rsp_stage_add
    nop
native_diag_rsp_dma_sample:
    la k1, native_diag_state + 236
    lw k0, (k1)
    addiu k0, k0, 1
    sw k0, (k1)
    la k1, native_diag_state + 276
    b native_diag_rsp_stage_add
    nop
native_diag_rsp_fetch_sample:
    la k1, native_diag_state + 240
    b native_diag_rsp_resident_rdp_sample
    nop
native_diag_rsp_texture_sample:
    la k1, native_diag_state + 244
native_diag_rsp_resident_rdp_sample:
    lw k0, (k1)
    addiu k0, k0, 1
    sw k0, (k1)
native_diag_rsp_rdp_sample:
    la k1, native_diag_state + 280
native_diag_rsp_stage_add:
    lw k0, (k1)
    addiu k0, k0, 1
    sw k0, (k1)
#endif
native_diag_sp_counted:
    lui k1, 0xA410
    lw k0, 12(k1)
    andi k0, k0, 0x40
    beqz k0, native_diag_cmd_counted
    nop
    la k1, native_diag_state + 88
    lw k0, (k1)
    addiu k0, k0, 1
    sw k0, (k1)
native_diag_cmd_counted:
    lui k1, 0xA410
    lw k0, 12(k1)
    andi k0, k0, 0x20
    beqz k0, native_diag_pipe_counted
    nop
    la k1, native_diag_state + 92
    lw k0, (k1)
    addiu k0, k0, 1
    sw k0, (k1)
native_diag_pipe_counted:
    lui k1, 0xA410
    lw k0, 12(k1)
    andi k0, k0, 0x10
    beqz k0, native_diag_tmem_counted
    nop
    la k1, native_diag_state + 96
    lw k0, (k1)
    addiu k0, k0, 1
    sw k0, (k1)
native_diag_tmem_counted:
    la k1, native_diag_state
    mfc0 k0, $9
    lw k1, 16(k1)
    subu k0, k0, k1
    bltz k0, native_diag_schedule
    nop
    la k0, native_diag_irq_save
    .set push
    .set noat
    sd $1, 0(k0)
    .set pop
    sd t0, 8(k0)
    sd t1, 16(k0)
    sd t2, 24(k0)
    sd t3, 32(k0)
    sd t4, 40(k0)
    sd t5, 48(k0)
    sd t6, 56(k0)
    sd t7, 64(k0)
    sd t8, 72(k0)
    sd t9, 80(k0)
    sd ra, 88(k0)
    b native_diag_tick
    nop

native_diag_irq_restore:
    la k0, native_diag_irq_save
    .set push
    .set noat
    ld $1, 0(k0)
    .set pop
    ld t0, 8(k0)
    ld t1, 16(k0)
    ld t2, 24(k0)
    ld t3, 32(k0)
    ld t4, 40(k0)
    ld t5, 48(k0)
    ld t6, 56(k0)
    ld t7, 64(k0)
    ld t8, 72(k0)
    ld t9, 80(k0)
    ld ra, 88(k0)
native_diag_schedule:
    // Report observer cost instead of presenting diagnostic FPS as ordinary FPS.
    la k1, native_diag_state
    mfc0 k0, $9
    lw k1, 108(k1)
    subu k0, k0, k1
    la k1, native_diag_state
    lw k1, 100(k1)
    sltu k1, k1, k0
    beqz k1, native_diag_max_done
    nop
    la k1, native_diag_state
    sw k0, 100(k1)
native_diag_max_done:
    la k1, native_diag_state
    lw k1, 104(k1)
    addu k0, k0, k1
    la k1, native_diag_state
    sw k0, 104(k1)
    mfc0 k0, $9
    li k1, DIAG_SAMPLE
    addu k0, k0, k1
    mtc0 k0, $11
    eret
    nop

native_diag_tick:
    la t0, native_diag_state
    mfc0 t1, $9
    li t2, DIAG_TICK
    addu t2, t1, t2
    sw t2, 16(t0)
    // Watch completed emulated frames, not the potentially stale FPS overlay.
    lw t2, 24(t0)
    lw t3, 32(t0)
    beq t2, t3, native_diag_no_progress
    nop
    sw t2, 32(t0)
    sw t1, 36(t0)
native_diag_no_progress:
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    jal native_diag_trace_event
    nop
#else
    lw t2, 40(t0)
    andi t3, t2, 63
    sll t3, t3, 6
    la t4, DEVENTS
    addu t4, t4, t3
    addiu t2, t2, 1
    sw t2, 40(t0)
    sw t2, 0(t4)
    lw t2, 0(t0)
    subu t2, t1, t2
    sw t2, 4(t4)
    lw t2, 4(t0)
    sw t2, 8(t4)
    lw t2, 24(t0)
    sw t2, 12(t4)
    lw t2, 28(t0)
    sw t2, 16(t4)
    lw t2, 0xA4040010
    sw t2, 20(t4)
    lw t2, 0xA410000C
    sw t2, 24(t4)
    lw t2, 0xA4100000
    sw t2, 28(t4)
    lw t2, 0xA4100004
    sw t2, 32(t4)
    lw t2, 0xA4100008
    sw t2, 36(t4)
    lw t2, 0xA4040018
    sw t2, 40(t4)
    lw t2, 0xA4040014
    sw t2, 44(t4)
    lhu t2, cur_line
    sw t2, 48(t4)
    lw t2, DMEM(HCOMP_BAND_Y)
    sw t2, 52(t4)
    lw t2, DMEM(HCOMP_SCREEN)
    sw t2, 56(t4)
    lw t2, 56(t0)
    sw t2, 60(t4)
    // Best-effort live RSP state alongside each event, without halting it.
    // These samples can straddle an epoch transition; the final halted DMEM
    // remains the authoritative coherent snapshot. Only renderer registers,
    // geometry and policy are added, with no guest WRAM/ROM capture.
    la t4, DPPU
    addu t4, t4, t3
    li t5, DMEM(0xBA0)
    li t6, 32
native_diag_ppu_copy:
    lw t2, (t5)
    sw t2, (t4)
    addiu t5, t5, 4
    addiu t4, t4, 4
    addiu t6, t6, -4
    bnez t6, native_diag_ppu_copy
    nop
    lw t2, DMEM(HCOMP_BAND_RAW)
    sw t2, 0(t4)
    lw t2, DMEM(HCOMP_SECTION_END)
    sw t2, 4(t4)
    lw t2, DMEM(HCOMP_BAND_Y)
    sw t2, 8(t4)
    lw t2, DMEM(HCOMP_BAND_ROWS)
    sw t2, 12(t4)
    lw t2, DMEM(HCOMP_SCREEN)
    sw t2, 16(t4)
    lw t2, DMEM(HCOMP_CGRAM_EVENT_CURSOR)
    sw t2, 20(t4)
    lw t2, section_ptr
    sw t2, 24(t4)
    lw t2, DMEM(FB_OFFSET)
    sw t2, 28(t4)
    // Read actual 24-bit DP cycle counters alongside each status sample. They
    // are not the latched busy status bits, and reads do not reset counters.
    srl t3, t3, 2
    la t4, DCOUNTERS
    addu t4, t4, t3
    lw t2, 0xA4100010
    sw t2, 0(t4)
    lw t2, 0xA4100014
    sw t2, 4(t4)
    lw t2, 0xA4100018
    sw t2, 8(t4)
    lw t2, 0xA410001C
    sw t2, 12(t4)
#endif
    // Full-second cumulative progress plus per-window occupancy. Partial final
    // windows remain explicitly partial and are never labelled whole-second FPS.
    lw t2, 20(t0)
    subu t2, t1, t2
    bltz t2, native_diag_second_done
    nop
    li t2, DIAG_HZ
    addu t2, t1, t2
    sw t2, 20(t0)
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    jal native_diag_trace_second
    nop
#else
    lw t2, 44(t0)
    sll t3, t2, 6
    la t4, DSECONDS
    addu t4, t4, t3
    addiu t2, t2, 1
    sw t2, 44(t0)
    sw t2, 0(t4)
    lw t2, 0(t0)
    subu t2, t1, t2
    sw t2, 4(t4)
    lw t2, 52(t0)
    sw t2, 8(t4)
    lw t2, 24(t0)
    sw t2, 12(t4)
    lw t2, 28(t0)
    sw t2, 16(t4)
    li t2, 0
native_diag_second_copy:
    addu t3, t0, t2
    lw t3, 64(t3)
    addu t5, t4, t2
    sw t3, 20(t5)
    addu t3, t0, t2
    sw zero, 64(t3)
    addiu t2, t2, 4
    bne t2, 36, native_diag_second_copy
    nop
    lw t2, 56(t0)
    sw t2, 56(t4)
    lw t2, 104(t0)
    sw t2, 60(t4)
#endif
native_diag_second_done:
    lw t2, 28(t0)
    beqz t2, native_diag_check_limit
    nop
    lw t2, 36(t0)
    subu t2, t1, t2
    li t3, DIAG_STALL
    sltu t2, t2, t3
    bnez t2, native_diag_check_limit
    nop
    b native_diag_finalize
    li t8, 1
native_diag_check_limit:
    lw t2, 0(t0)
    subu t2, t1, t2
    li t3, DIAG_LIMIT
    sltu t2, t2, t3
    bnez t2, native_diag_irq_restore
    nop
    b native_diag_finalize
    li t8, 2

// Independent wait-path watchdog, including execution with EXL already set.
// Record the real wait-site separately from EPC (which can belong to an outer
// TLB exception), then enter the same terminal capture without ever resuming.
native_diag_wait_stall_rsp:
    la k0, native_diag_state
    la k1, native_diag_rsp_wait
    sw k1, 120(k0)
    b native_diag_poll_finalize
    nop
native_diag_wait_stall_frame:
    la k0, native_diag_state
    la k1, native_diag_frame_wait
    sw k1, 120(k0)
native_diag_poll_finalize:
    mfc0 k1, $12
    sw k1, 124(k0)
    ori k1, k1, 2
    mtc0 k1, $12
    nop
    nop
    la k0, native_diag_irq_save
    .set push
    .set noat
    sd $1, 0(k0)
    .set pop
    sd t0, 8(k0)
    sd t1, 16(k0)
    sd t2, 24(k0)
    sd t3, 32(k0)
    sd t4, 40(k0)
    sd t5, 48(k0)
    sd t6, 56(k0)
    sd t7, 64(k0)
    sd t8, 72(k0)
    sd t9, 80(k0)
    sd ra, 88(k0)
    b native_diag_finalize
    li t8, 1


#ifdef SODIUM64_NATIVE_DIAG_TRACE
// 8 Hz observations bound all-IRQ CPU / RSP stage counts to about eight frames.
// Per-frame wait measurements below supply the precise completed boundaries.
.align 5
native_diag_trace_event:
    lw t2, 40(t0)
    sltiu t3, t2, 160
    beqz t3, native_diag_trace_full
    nop
    sll t3, t2, 5
    sll t4, t2, 3
    addu t3, t3, t4
    la t4, DEVENTS
    addu t4, t4, t3
    addiu t2, t2, 1
    sw t2, 40(t0)
    lw t2, 0(t0)
    subu t2, t1, t2
    sw t2, 0(t4)
    lw t2, 24(t0)
    sh t2, 8(t4)
    lw t2, 56(t0)
    sw t2, 4(t4)
    lw t2, 264(t0) // bookended PC / bank from this IRQ, not a second PC read
    sh t2, 10(t4)
    lw t2, 300(t0)
    sb t2, 12(t4)
    lw t2, 0xA410000C
    sh t2, 14(t4)
    lbu t3, DMEM(BG_MODE)
    andi t3, t3, 15
    lw t2, DMEM(HCOMP_BAND_RAW)
    andi t2, t2, 3
    sll t2, t2, 4
    or t3, t3, t2
    lbu t2, DMEM(STAT_FLAGS)
    andi t2, t2, 0x80
    or t3, t3, t2
    lbu t2, DMEM(HCOMP_SCREEN)
    sll t2, t2, 6
    or t2, t2, t3
    sb t2, 13(t4)
    lw t2, DMEM(CGADSUB)
    srl t3, t2, 24
    sb t3, 17(t4)
    srl t3, t2, 16
    sb t3, 18(t4)
    srl t3, t2, 8
    sb t3, 19(t4)
    sb t2, 20(t4)
    lbu t2, DMEM(CGWSEL)
    sb t2, 16(t4)
    lbu t2, DMEM(TMW)
    sb t2, 21(t4)
    lw t2, DMEM(HCOMP_BAND_ROWS)
    sh t2, 22(t4)
    li t2, 0
native_diag_trace_module_copy:
    addu t3, t0, t2
    lw t5, 136(t3)
    sw zero, 136(t3)
    sltiu t6, t5, 256
    bnez t6, native_diag_trace_module_fits
    nop
    li t5, 255
    la t6, DHDR + 0x12C
    lw t7, (t6)
    ori t7, t7, 16
    sw t7, (t6)
native_diag_trace_module_fits:
    srl t6, t2, 2
    addu t6, t4, t6
    sb t5, 24(t6)
    addiu t2, t2, 4
    bne t2, 32, native_diag_trace_module_copy
    nop
    li t2, 0
native_diag_trace_rsp_copy:
    addu t3, t0, t2
    lw t5, 268(t3)
    sw zero, 268(t3)
    sltiu t6, t5, 256
    bnez t6, native_diag_trace_rsp_fits
    nop
    li t5, 255
    la t6, DHDR + 0x12C
    lw t7, (t6)
    ori t7, t7, 16
    sw t7, (t6)
native_diag_trace_rsp_fits:
    srl t6, t2, 2
    addu t6, t4, t6
    sb t5, 32(t6)
    addiu t2, t2, 4
    bne t2, 32, native_diag_trace_rsp_copy
    nop
    jr ra
    nop
native_diag_trace_full:
    la t3, DHDR + 0x12C
    lw t2, (t3)
    ori t2, t2, 1
    sw t2, (t3)
    jr ra
    nop

.align 5
native_diag_trace_second:
    lw t2, 44(t0)
    sltiu t3, t2, 20
    beqz t3, native_diag_trace_second_full
    nop
    sll t3, t2, 6
    la t4, DSECONDS
    addu t4, t4, t3
    addiu t2, t2, 1
    sw t2, 44(t0)
    sh t2, 30(t4)
    lw t2, 0(t0)
    subu t2, t1, t2
    sw t2, 0(t4)
    lw t2, 24(t0)
    sw t2, 4(t4)
    lw t2, 56(t0)
    sw t2, 8(t4)
    li t2, 0
native_diag_trace_second_copy:
    addu t3, t0, t2
    lw t3, 64(t3)
    srl t5, t2, 1
    addu t5, t4, t5
    sh t3, 12(t5)
    addu t3, t0, t2
    sw zero, 64(t3)
    addiu t2, t2, 4
    bne t2, 36, native_diag_trace_second_copy
    nop
    li t2, 0
native_diag_trace_second_modules:
    addu t3, t0, t2
    lw t5, 168(t3)
    sw zero, 168(t3)
    srl t3, t2, 1
    addu t3, t4, t3
    sh t5, 32(t3)
    addiu t2, t2, 4
    bne t2, 32, native_diag_trace_second_modules
    nop
    lw t2, 128(t0)
    sh t2, 48(t4)
    sw zero, 128(t0)
    lw t2, 236(t0)
    sh t2, 50(t4)
    sw zero, 236(t0)
    lw t2, 240(t0)
    sh t2, 52(t4)
    sw zero, 240(t0)
    lw t2, 244(t0)
    sh t2, 54(t4)
    sw zero, 244(t0)
    lw t2, 104(t0)
    sw t2, 56(t4)
    lw t2, 228(t0)
    sw t2, 60(t4)
    jr ra
    nop
native_diag_trace_second_full:
    la t3, DHDR + 0x12C
    lw t2, (t3)
    ori t2, t2, 4
    sw t2, (t3)
    jr ra
    nop
#endif


#ifdef SODIUM64_NATIVE_DIAG_TRACE
.globl native_diag_frame_complete
.align 5
native_diag_frame_complete:
    mfc0 t1, $9
    mfc0 t3, $12
    li t0, -2
    and t2, t3, t0
    mtc0 t2, $12
    nop
    nop
    la t0, native_diag_state
    sw t1, 224(t0)
    lw t2, 24(t0)
    addiu t2, t2, 1
    sw t2, 24(t0)
    lw t2, 112(t0)
    beqz t2, native_diag_frame_return
    nop
    lw t2, 216(t0)
    bnez t2, native_diag_frame_append
    nop
    li t2, 1
    sw t2, 216(t0)
    lw t2, 0(t0)
    subu t2, t1, t2
    sw t2, 220(t0)
    lw t2, 24(t0)
    sw t2, 252(t0)
    b native_diag_frame_update
    nop
native_diag_frame_append:
    lw t2, 212(t0)
    sltiu k0, t2, 1280
    beqz k0, native_diag_frames_full
    nop
    sll k0, t2, 3
    sll k1, t2, 2
    addu k0, k0, k1
    la k1, DFRAMES
    addu k0, k0, k1
    lw k1, 0(t0)
    subu k1, t1, k1
    sw k1, 0(k0)
    lw k1, 204(t0)
    sw k1, 4(k0)
    lw k1, 208(t0)
    sw k1, 8(k0)
    addiu t2, t2, 1
    sw t2, 212(t0)
    b native_diag_frame_update
    nop
native_diag_frames_full:
    la k0, DHDR + 0x12C
    lw k1, (k0)
    ori k1, k1, 8
    sw k1, (k0)
native_diag_frame_update:
    sw t1, 200(t0)
    sw zero, 204(t0)
    sw zero, 208(t0)
native_diag_frame_return:
    mfc0 k0, $9
    lw k1, 224(t0)
    subu k0, k0, k1
    lw k1, 228(t0)
    addu k1, k1, k0
    sw k1, 228(t0)
    lw k1, 232(t0)
    sltu k1, k1, k0
    beqz k1, native_diag_frame_max_done
    nop
    sw k0, 232(t0)
native_diag_frame_max_done:
    mtc0 t3, $12
    nop
    nop
    jr ra
    nop

native_diag_module_static:
    mfc0 k0, $14
    la k1, native_diag_cpu_start
    sltu k0, k0, k1
    bnez k0, native_diag_module_after_cpu
    nop
    mfc0 k0, $14
    la k1, native_diag_cpu_end
    sltu k0, k0, k1
    bnez k0, native_diag_module_cpu
    nop
native_diag_module_after_cpu:
    mfc0 k0, $14
    la k1, native_diag_apu_start
    sltu k0, k0, k1
    bnez k0, native_diag_module_after_apu
    nop
    mfc0 k0, $14
    la k1, native_diag_apu_end
    sltu k0, k0, k1
    bnez k0, native_diag_module_apu
    nop
native_diag_module_after_apu:
    mfc0 k0, $14
    la k1, native_diag_dsp_start
    sltu k0, k0, k1
    bnez k0, native_diag_module_after_dsp
    nop
    mfc0 k0, $14
    la k1, native_diag_dsp_end
    sltu k0, k0, k1
    bnez k0, native_diag_module_dsp
    nop
native_diag_module_after_dsp:
    mfc0 k0, $14
    la k1, native_diag_dma_start
    sltu k0, k0, k1
    bnez k0, native_diag_module_after_dma
    nop
    mfc0 k0, $14
    la k1, native_diag_dma_end
    sltu k0, k0, k1
    bnez k0, native_diag_module_dma
    nop
native_diag_module_after_dma:
    mfc0 k0, $14
    la k1, native_diag_ppu_start
    sltu k0, k0, k1
    bnez k0, native_diag_module_after_ppu
    nop
    mfc0 k0, $14
    la k1, native_diag_ppu_end
    sltu k0, k0, k1
    bnez k0, native_diag_module_ppu
    nop
native_diag_module_after_ppu:
    b native_diag_module_other
    nop
native_diag_module_cpu:
    la k1, native_diag_state + 136
    b native_diag_module_add
    nop
native_diag_module_apu:
    la k1, native_diag_state + 140
    b native_diag_module_add
    nop
native_diag_module_dsp:
    la k1, native_diag_state + 144
    b native_diag_module_add
    nop
native_diag_module_dma:
    la k1, native_diag_state + 148
    b native_diag_module_add
    nop
native_diag_module_ppu:
    la k1, native_diag_state + 152
    b native_diag_module_add
    nop
native_diag_module_rsp:
    la k1, native_diag_state + 156
    b native_diag_module_add
    nop
native_diag_module_vi:
    la k1, native_diag_state + 160
    b native_diag_module_add
    nop
native_diag_module_other:
    la k1, native_diag_state + 164
    b native_diag_module_add
    nop
native_diag_module_add:
    lw k0, (k1)
    addiu k0, k0, 1
    sw k0, (k1)
    lw k0, 32(k1)
    addiu k0, k0, 1
    sw k0, 32(k1)
    b native_diag_sp_sample
    nop
#endif

// Finalization is terminal and deliberately intrusive, only after trigger.
// Pre-stop registers and CPU EPC are captured before SET_HALT/SET_FREEZE.
// No unsafe timeout ever returns to the renderer or reuses its owned surfaces.
native_diag_finalize:
#ifndef SODIUM64_NATIVE_DIAG_TRACE
    la k0, DBASE + 0x7C00
    .set push
    .set noat
    sd $0, 0(k0)
    sd $1, 8(k0)
    sd $2, 16(k0)
    sd $3, 24(k0)
    sd $4, 32(k0)
    sd $5, 40(k0)
    sd $6, 48(k0)
    sd $7, 56(k0)
    sd $8, 64(k0)
    sd $9, 72(k0)
    sd $10, 80(k0)
    sd $11, 88(k0)
    sd $12, 96(k0)
    sd $13, 104(k0)
    sd $14, 112(k0)
    sd $15, 120(k0)
    sd $16, 128(k0)
    sd $17, 136(k0)
    sd $18, 144(k0)
    sd $19, 152(k0)
    sd $20, 160(k0)
    sd $21, 168(k0)
    sd $22, 176(k0)
    sd $23, 184(k0)
    sd $24, 192(k0)
    sd $25, 200(k0)
    sd $26, 208(k0)
    sd $27, 216(k0)
    sd $28, 224(k0)
    sd $29, 232(k0)
    sd $30, 240(k0)
    sd $31, 248(k0)
    .set pop
    mfhi k1
    sd k1, 0x100(k0)
    mflo k1
    sd k1, 0x108(k0)
    // Restore the original values of ordinary GPRs borrowed by the slow IRQ.
    la t0, native_diag_irq_save
    ld t1, 0(t0)
    sd t1, 8(k0)
    ld t1, 8(t0)
    sd t1, 64(k0)
    ld t1, 16(t0)
    sd t1, 72(k0)
    ld t1, 24(t0)
    sd t1, 80(k0)
    ld t1, 32(t0)
    sd t1, 88(k0)
    ld t1, 40(t0)
    sd t1, 96(k0)
    ld t1, 48(t0)
    sd t1, 104(k0)
    ld t1, 56(t0)
    sd t1, 112(k0)
    ld t1, 64(t0)
    sd t1, 120(k0)
    ld t1, 72(t0)
    sd t1, 192(k0)
    ld t1, 80(t0)
    sd t1, 200(k0)
    ld t1, 88(t0)
    sd t1, 248(k0)
#endif
    la s0, DHDR
    la s1, native_diag_state
    sw t8, 12(s0)
    li t0, 0x53363444
    sw t0, 0(s0)
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    li t0, 4
#else
    li t0, 2
#endif
    sw t0, 4(s0)
    li t0, 0x8000
    sw t0, 16(s0)
    li t0, DIAG_HZ
    sw t0, 20(s0)
    li t0, DIAG_SAMPLE
    sw t0, 24(s0)
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    li t0, 256
#else
    li t0, 1024
#endif
    sw t0, 28(s0)
    lw t0, 8(s1)
    sw t0, 32(s0)
    lw t0, 12(s1)
    sw t0, 36(s0)
    lw t0, 40(s1)
    sw t0, 40(s0)
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    li t0, 160
#else
    li t0, 64
#endif
    sw t0, 44(s0)
    lw t0, 44(s1)
    sw t0, 48(s0)
    mfc0 t0, $9
    sw t0, 76(s0)
    lw t1, 0(s1)
    sw t1, 72(s0)
    subu t0, t0, t1
    sw t0, 52(s0)
    lw t0, 24(s1)
    sw t0, 56(s0)
    lw t0, 28(s1)
    sw t0, 60(s0)
    lw t0, 52(s1)
    sw t0, 64(s0)
    lw t0, 56(s1)
    sw t0, 68(s0)
    lw t0, 36(s1)
    sw t0, 80(s0)
    lbu t0, precision_set
    sw t0, 84(s0)
    lbu t0, skipped_set
    sw t0, 88(s0)
    lbu t0, apu_clock
    sw t0, 92(s0)
    lbu t0, audio_set
    sw t0, 96(s0)
    lbu t0, layer_set
    sw t0, 100(s0)
    mfc0 t0, $14
    sw t0, 104(s0)
    mfc0 t0, $13
    sw t0, 108(s0)
    mfc0 t0, $12
    lw t1, 120(s1)
    sw t1, 244(s0)
    beqz t1, native_diag_status_ready
    nop
    lw t0, 124(s1)
native_diag_status_ready:
    sw t0, 112(s0)
    lw t0, 0xA4040010
    sw t0, 116(s0)
    lw t0, 0xA4040018
    sw t0, 120(s0)
    lw t0, 0xA4040014
    sw t0, 124(s0)
    lw t0, 0xA410000C
    sw t0, 128(s0)
    lw t0, 0xA4100000
    sw t0, 132(s0)
    lw t0, 0xA4100004
    sw t0, 136(s0)
    lw t0, 0xA4100008
    sw t0, 140(s0)
    lw t0, 0xA430000C
    sw t0, 172(s0)
    lw t0, 0xA4400004
    sw t0, 176(s0)
    lw t0, 0xA4400008
    sw t0, 180(s0)
    lw t0, 0xA450000C
    sw t0, 184(s0)
    lw t0, 0xA4500004
    sw t0, 188(s0)
    lhu t0, dsp_pointer
    sw t0, 192(s0)
    lbu t0, enabled
    sw t0, 196(s0)
    lw t0, section_ptr
    sw t0, 200(s0)
    lhu t0, cur_line
    sw t0, 204(s0)
    lbu t0, queue_id
    sw t0, 208(s0)
    lw t0, 0xA4040000
    sw t0, 212(s0)
    lw t0, 0xA4040004
    sw t0, 216(s0)
    lw t0, 104(s1)
    sw t0, 220(s0)
    lw t0, 100(s1)
    sw t0, 224(s0)
    lw t0, 0xA4600010
    sw t0, 236(s0)
    // Save the partial final interval's occupancy separately in header+0x100.
    la t0, native_diag_state + 64
    addiu t1, s0, 0x100
    li t2, 36
native_diag_partial_copy:
    lw t3, (t0)
    sw t3, (t1)
    addiu t0, t0, 4
    addiu t1, t1, 4
    addiu t2, t2, -4
    bnez t2, native_diag_partial_copy
    nop
#ifdef SODIUM64_NATIVE_DIAG_TRACE
    li t0, 32
    sw t0, 0x128(s0) // Retained EPC stride; overflow flags stay intact.
    li t0, 40
    sw t0, 0x130(s0)
    li t0, 64
    sw t0, 0x134(s0)
    li t0, 0x46524D34 // FRM4: full-interval completed-boundary records.
    sw t0, 0x138(s0)
    lw t0, 212(s1)
    sw t0, 0x13C(s0)
    li t0, 1280
    sw t0, 0x140(s0)
    li t0, 12
    sw t0, 0x144(s0)
    lw t0, 220(s1)
    sw t0, 0x148(s0)
    lw t0, 228(s1)
    sw t0, 0x14C(s0)
    lw t0, 232(s1)
    sw t0, 0x150(s0)
    li t0, 0
native_diag_partial_modules:
    addu t1, s1, t0
    lw t2, 168(t1)
    addu t3, s0, t0
    sw t2, 0x158(t3)
    lw t2, 136(t1)
    sw t2, 0x198(t3)
    lw t2, 268(t1)
    sw t2, 0x1B8(t3)
    addiu t0, t0, 4
    bne t0, 32, native_diag_partial_modules
    nop
    lw t0, 128(s1)
    sw t0, 0x178(s0)
    lw t0, 236(s1)
    sw t0, 0x17C(s0)
    lw t0, 240(s1)
    sw t0, 0x180(s0)
    lw t0, 244(s1)
    sw t0, 0x184(s0)
    li t0, DIAG_TICK
    sw t0, 0x188(s0)
    lw t0, native_diag_guest_sram_exp
    sw t0, 0x18C(s0)
    lw t0, 252(s1)
    sw t0, 0x190(s0)
    li t0, 46875
    sw t0, 0x1D8(s0)
    li t0, 0x42414E34 // BAN4: bank bookending / epoch protocol
    sw t0, 0x1DC(s0)
#endif
    // Read PC only AFTER HALT is acknowledged. All these waits are bounded.
    li t0, 2
    sw t0, 0xA4040010
    mfc0 t5, $9
    li t6, 2343750
native_diag_halt_wait:
    lw t0, 0xA4040010
    andi t1, t0, 1
    bnez t1, native_diag_halted
    nop
    mfc0 t1, $9
    subu t1, t1, t5
    sltu t1, t1, t6
    bnez t1, native_diag_halt_wait
    nop
    b native_diag_halt_record
    li t1, -1
native_diag_halted:
    li t1, 1
    sw t1, 228(s0)
    lw t1, 0xA4080000
native_diag_halt_record:
    sw t0, 144(s0)
    sw t1, 148(s0)
    // Freeze DP only after pre-trigger state and halted-PC context are saved.
    li t0, 8
    sw t0, 0xA410000C
    mfc0 t5, $9
native_diag_dma_wait:
    lw t0, 0xA4040018
    lw t1, 0xA4040014
    or t2, t0, t1
    beqz t2, native_diag_dma_settled
    nop
    mfc0 t2, $9
    subu t2, t2, t5
    sltu t2, t2, t6
    bnez t2, native_diag_dma_wait
    nop
    b native_diag_dma_record
    nop
native_diag_dma_settled:
    li t2, 1
    sw t2, 232(s0)
native_diag_dma_record:
    sw t0, 152(s0)
    sw t1, 156(s0)
    lw t0, 0xA410000C
    sw t0, 160(s0)
    lw t0, 0xA4100004
    sw t0, 164(s0)
    lw t0, 0xA4100008
    sw t0, 168(s0)
#ifndef SODIUM64_NATIVE_DIAG_TRACE
    // CPU reads the halted RSP's resident memories; never read its semaphore.
    li t0, 0xA4000000
    la t1, DBASE + 0x5200
    li t2, 0x2000
native_diag_rsp_copy:
    lw t3, (t0)
    sw t3, (t1)
    addiu t0, t0, 4
    addiu t1, t1, 4
    addiu t2, t2, -4
    bnez t2, native_diag_rsp_copy
    nop
#endif
#ifndef SODIUM64_NATIVE_DIAG_TRACE
    // v2 terminal palette storage overlaps v3 whole-interval second records.
    la t0, cgram
    la t1, DBASE + 0x7E00
    li t2, 512
native_diag_cgram_copy:
    lw t3, (t0)
    sw t3, (t1)
    addiu t0, t0, 4
    addiu t1, t1, 4
    addiu t2, t2, -4
    bnez t2, native_diag_cgram_copy
    nop
#endif
    // Body integrity checksum excludes the 512-byte header committed last.
    la t0, DBASE
    la t1, DHDR
    move t4, zero
native_diag_sum_guest:
    lw t2, (t0)
    addu t4, t4, t2
    addiu t0, t0, 4
    bne t0, t1, native_diag_sum_guest
    nop
    la t0, DBASE + 0x2200
    la t1, DBASE + 0x8000
native_diag_sum_body:
    lw t2, (t0)
    addu t4, t4, t2
    addiu t0, t0, 4
    bne t0, t1, native_diag_sum_body
    nop
    sw t4, 240(s0)
    sync
    // Header is last; "CAPTURE SAVED" means PI finished every transfer.
    la a0, DBASE
    li a1, 0x08000000
    li a2, 0x2000 - 1
    jal native_diag_pi_write
    nop
    beqz v0, native_diag_save_failed
    nop
    la a0, DBASE + 0x2200
    li a1, 0x08002200
    li a2, 0x5E00 - 1
    jal native_diag_pi_write
    nop
    beqz v0, native_diag_save_failed
    nop
    li t0, 1
    sw t0, 8(s0)
    sync
    la a0, DHDR
    li a1, 0x08002000
    li a2, 0x200 - 1
    jal native_diag_pi_write
    nop
    beqz v0, native_diag_save_failed
    nop
native_diag_saved:
    la s4, native_diag_saved_text
    b native_diag_screen
    nop
native_diag_save_failed:
    la s4, native_diag_failed_text
native_diag_screen:
    // Freeze is diagnostic completion. This overlay is CPU drawn after DP freeze.
    lw s2, framebuffer
    li t0, 0xA0000000
    or s2, s2, t0
    move t0, s2
    li t1, 0x00010001
    li t2, 560 * 240
    addu t2, t2, t0
native_diag_screen_clear:
    sw t1, (t0)
    addiu t0, t0, 4
    bne t0, t2, native_diag_screen_clear
    nop
    la a0, native_diag_title
    li a1, 32 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
    move a0, s4
    li a1, 48 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
    la a0, native_diag_stall_text
    lw t0, 12(s0)
    beq t0, 1, native_diag_reason_text
    nop
    la a0, native_diag_limit_text
native_diag_reason_text:
    li a1, 64 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
    la a0, native_diag_cpu_text
    li a1, 88 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
    lw a0, 244(s0)
    bnez a0, native_diag_cpu_screen
    nop
    lw a0, 104(s0)
native_diag_cpu_screen:
    li a1, 88 * 560 + 112
    addu a1, a1, s2
    jal native_diag_hex
    nop
    la a0, native_diag_rsp_text
    li a1, 104 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
    lw a0, 148(s0)
    li a1, 104 * 560 + 112
    addu a1, a1, s2
    jal native_diag_hex
    nop
    la a0, native_diag_dp_text
    li a1, 120 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
    lw a0, 128(s0)
    li a1, 120 * 560 + 112
    addu a1, a1, s2
    jal native_diag_hex
    nop
    la a0, native_diag_end_text
    li a1, 136 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
    lw a0, 136(s0)
    li a1, 136 * 560 + 112
    addu a1, a1, s2
    jal native_diag_hex
    nop
    la a0, native_diag_current_text
    li a1, 152 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
    lw a0, 140(s0)
    li a1, 152 * 560 + 112
    addu a1, a1, s2
    jal native_diag_hex
    nop
    la a0, native_diag_reset_text
    li a1, 192 * 560 + 32
    addu a1, a1, s2
    jal draw_string
    nop
native_diag_done:
    // Leave PRE-NMI/reset handling available. Timer is masked and VI disabled;
    // no interrupted guest or renderer code is resumed.
    li t0, 0x1001
    mtc0 t0, $12
    nop
    nop
    b native_diag_done
    nop

// Only finalization calls this. Both PI idle and transfer waits have ~1 s limits.
native_diag_pi_write:
    lui t0, 0xA460
    mfc0 t5, $9
    li t6, DIAG_HZ
native_diag_pi_idle:
    lw t1, 16(t0)
    andi t2, t1, 3
    beqz t2, native_diag_pi_start
    nop
    mfc0 t2, $9
    subu t2, t2, t5
    sltu t2, t2, t6
    bnez t2, native_diag_pi_idle
    nop
    jr ra
    move v0, zero
native_diag_pi_start:
    sw a0, 0(t0)
    sw a1, 4(t0)
    sw a2, 8(t0)
    mfc0 t5, $9
native_diag_pi_wait:
    lw t1, 16(t0)
    andi t2, t1, 3
    beqz t2, native_diag_pi_complete
    nop
    mfc0 t2, $9
    subu t2, t2, t5
    sltu t2, t2, t6
    bnez t2, native_diag_pi_wait
    nop
    jr ra
    move v0, zero
native_diag_pi_complete:
    andi t1, t1, 4
    sltiu v0, t1, 1
    jr ra
    nop

native_diag_hex:
    move s5, ra
    move s6, a0
    li s7, 8
native_diag_hex_loop:
    srl a0, s6, 28
    sltiu t0, a0, 10
    bnez t0, native_diag_hex_digit
    addiu a0, a0, 48
    addiu a0, a0, 7
native_diag_hex_digit:
    jal draw_char
    nop
    sll s6, s6, 4
    addiu s7, s7, -1
    bnez s7, native_diag_hex_loop
    addiu a1, a1, 16
    jr s5
    nop
#endif

