/*
    Experimental profiling support for the ironangelo/sodium64 fork.

    This file is compiled into useful code/data only for PROFILE=1 builds.
    Normal release builds do not enable the CP0 timer or sampling buffer.
*/

#include "defines.h"

#ifdef SODIUM64_PROFILE

#define PROFILE_SAMPLE_INTERVAL 65521
#define PROFILE_SAMPLE_CAPACITY 4096

#ifdef SODIUM64_HW_PROFILE
#define HW_PROFILE_MAGIC 0x53363448 /* "S64H" */
#define HW_PROFILE_VERSION 2
#ifndef HW_PROFILE_WARMUP_SECONDS
#define HW_PROFILE_WARMUP_SECONDS 2
#endif
#if HW_PROFILE_WARMUP_SECONDS < 2 || HW_PROFILE_WARMUP_SECONDS > 60
#error HW_PROFILE_WARMUP_SECONDS must be in 2..60
#endif
#define HW_PROFILE_MEASURE_SECONDS 5
#define HW_PROFILE_HEADER_SIZE 0x80
#define HW_PROFILE_SNAPSHOT_OFFSET 0x100
#endif

.globl profile_init
.globl profile_interrupt
.globl profile_magic
.globl profile_version
.globl profile_interval
.globl profile_capacity
.globl profile_write_ptr
.globl profile_sample_count
.globl profile_last_epc
.globl profile_sample_buffer
.globl profile_sample_buffer_end

#ifdef SODIUM64_HW_PROFILE
.globl hw_profile_phase
.globl hw_profile_header
.globl hw_profile_header_end
#endif

// Absolute, never ELF-loaded. 448000..44D000 is disjoint from base4MiB,
// R61's 400000..4340A0/438000..440000 and USB bench440000..442000 owners.
// Low/high32-byte guards bound this20KiB profiler lease.
.equ profile_magic,         0x80448020
.equ profile_version,       profile_magic + 4
.equ profile_interval,      profile_magic + 8
.equ profile_capacity,      profile_magic + 12
.equ profile_write_ptr,     profile_magic + 16
.equ profile_sample_count,  profile_magic + 20
.equ profile_last_epc,      profile_magic + 24
.equ profile_reserved,      profile_magic + 28
.equ profile_sample_buffer, profile_magic + 32
.equ profile_sample_buffer_end, profile_sample_buffer + PROFILE_SAMPLE_CAPACITY * 4

.section .rodata
.align 3
profile_header_template:
    .word 0x53363450,1,PROFILE_SAMPLE_INTERVAL,PROFILE_SAMPLE_CAPACITY
    .word profile_sample_buffer,0,0,0

#ifdef SODIUM64_HW_PROFILE
// Real-N64 M0 capture header. The payload written to cart SRAM is:
//   0x0000..0x007F: this fixed-width header
//   0x0100..       : canonical S64P statistical snapshot
// All fields are 32-bit big-endian words so the host decoder can also recover
// flashcart save files that expose N64 words byte-swapped.
.equ hw_profile_phase,       0x8044c040 // 0=warmup, 1=measure, 3=saved/frozen
.equ hw_profile_second,      hw_profile_phase + 1
.equ hw_profile_last_native, hw_profile_phase + 2
.equ hw_profile_pad,         hw_profile_phase + 3
.equ hw_profile_header,      0x8044c060
.equ hw_profile_header_end,  hw_profile_header + 0x80
.equ hw_profile_hdr_samples,    hw_profile_header + 16
.equ hw_profile_hdr_budget,     hw_profile_header + 32
.equ hw_profile_hdr_skipped,    hw_profile_header + 52
.equ hw_profile_hdr_apu_clock,  hw_profile_header + 56
.equ hw_profile_hdr_audio,      hw_profile_header + 60
.equ hw_profile_hdr_precision,  hw_profile_header + 64
.equ hw_profile_hdr_frame_count,hw_profile_header + 68
.equ hw_profile_hdr_sp_status,  hw_profile_header + 72
.equ hw_profile_hdr_sp_dma_full,hw_profile_header + 76
.equ hw_profile_hdr_sp_dma_busy,hw_profile_header + 80
.equ hw_profile_hdr_sp_pc,      hw_profile_header + 84
.equ hw_profile_hdr_complete,   hw_profile_header + 88
.equ hw_profile_hdr_guards_ok,  hw_profile_header + 100
.align 3
hw_profile_header_template:
    .word HW_PROFILE_MAGIC
    .word HW_PROFILE_VERSION
    .word HW_PROFILE_WARMUP_SECONDS
    .word HW_PROFILE_MEASURE_SECONDS
    .word 0
    .word PROFILE_SAMPLE_INTERVAL
    .word profile_sample_buffer_end - profile_magic
    .word HW_PROFILE_SNAPSHOT_OFFSET
    .word 0:5
    .word 0:10
    .word 0x00448000,0x0044d000,0 // lease bounds and verified guards
    .word 0:6
#endif

.text
.set noreorder

.globl profile_boot_prepare
.align 5
profile_boot_prepare:
    // Retire cached lines before clearing via KSEG1, including warm reboot.
    li t0, 0x80448000
    li t1, 0x8044d000
1:
    cache 0x15, (t0)
    addiu t0, t0, 16
    bne t0, t1, 1b
    nop
    sync
    li t0, 0xa0448000
    li t1, 0xa044d000
2:
    sd zero, (t0)
    addiu t0, t0, 8
    bne t0, t1, 2b
    nop
    la t0, profile_header_template
    li t1, 0xa0448020
    li t2, 32
3:
    ld t3, (t0)
    sd t3, (t1)
    addiu t0, t0, 8
    addiu t1, t1, 8
    addiu t2, t2, -8
    bnez t2, 3b
    nop
#ifdef SODIUM64_HW_PROFILE
    la t0, hw_profile_header_template
    li t1, 0xa044c060
    li t2, 128
4:
    ld t3, (t0)
    sd t3, (t1)
    addiu t0, t0, 8
    addiu t1, t1, 8
    addiu t2, t2, -8
    bnez t2, 4b
    nop
#endif
    li t0, 0xa0448000
    li t1, 0xa044cfe0
    li t2, 0x50363447 // P64G
    li t3, 8
5:
    sw t2, (t0)
    sw t2, (t1)
    addiu t0, t0, 4
    addiu t1, t1, 4
    addiu t3, t3, -1
    bnez t3, 5b
    nop
    sync
    jr ra
    nop

.align 5
profile_init:
    // Reset the ring-buffer metadata. The sample buffer itself does not need to
    // be cleared because sample_count/write_ptr define which entries are valid.
    la t0, profile_sample_buffer
    la t1, profile_write_ptr
    sw t0, (t1)
    la t1, profile_sample_count
    sw zero, (t1)
    la t1, profile_last_epc
    sw zero, (t1)

#ifdef SODIUM64_HW_PROFILE
    // Hardware M0 measurements start with the Road-to-1.0 settings already in
    // force before guest execution or APU JIT compilation begins.
    li t0, APU_CYCLE
    sb t0, apu_clock
    sb zero, underclk_set
    sb zero, skipped_set
    li t0, 4
    sb t0, audio_set
    li t0, 8
    sb t0, precision_set

    la t0, hw_profile_phase
    sb zero, 0(t0)
    sb zero, 1(t0)
    sb zero, 2(t0)
    la t0, hw_profile_hdr_complete
    sw zero, (t0)
    // Make a previous terminal capture unparseable before this run starts.
    sw zero, 0xa8000000
    sync
    mfc0 t3, $9
    li t4, 4687500
6:
    lw t0, 0xa4600010
    andi t0, t0, 3
    beqz t0, 7f
    nop
    mfc0 t0, $9
    subu t0, t0, t3
    sltu t0, t0, t4
    bnez t0, 6b
    nop
    b hw_profile_guard_failed
    nop
7:
#endif

    // Schedule the first CP0 Compare interrupt. Count increments continuously;
    // using a relative period avoids any dependency on startup timing.
    mfc0 t0, $9 // Count
    li t1, PROFILE_SAMPLE_INTERVAL
    addu t0, t0, t1
    mtc0 t0, $11 // Compare (also clears any pending timer interrupt)
    jr ra
    nop

.align 5
profile_interrupt:
    // IMPORTANT: exception-time code may only clobber k0/k1. The interrupted
    // emulator path can have every normal GPR live, including ra and at.

    // Preserve the sampled EPC in the profiler header while k0/k1 are reused.
    mfc0 k0, $14 // EPC
    la k1, profile_last_epc
    sw k0, (k1)

    // Store EPC at the current ring-buffer position.
    la k1, profile_write_ptr
    lw k0, (k1)
    la k1, profile_last_epc
    lw k1, (k1)
    sw k1, (k0)
    addiu k0, k0, 4

    // Wrap at the end of the fixed-size sample buffer.
    la k1, profile_sample_buffer_end
    bne k0, k1, profile_no_wrap
    nop
    la k0, profile_sample_buffer

profile_no_wrap:
    la k1, profile_write_ptr
    sw k0, (k1)

    // Keep a monotonically increasing total sample count. Consumers use the
    // lower capacity samples when this count has exceeded the ring size.
    la k1, profile_sample_count
    lw k0, (k1)
    addiu k0, k0, 1
    sw k0, (k1)

#ifdef SODIUM64_HW_PROFILE
    // Detect the once-per-60-VI fps_native wrap without adding work to the VI
    // path or any emulator hot path. The timer samples ~12x per VI on real N64,
    // so observing current < previous robustly detects each 59->0 transition.
    la k1, hw_profile_last_native
    lbu k0, (k1)
    lbu k1, fps_native
    sltu k0, k1, k0
    beqz k0, hw_profile_no_second
    nop

    // Save the new fps_native value before handling the second boundary.
    la k0, hw_profile_last_native
    sb k1, (k0)

    // Phase 0: allow two complete one-second windows for deterministic warmup.
    la k0, hw_profile_phase
    lbu k1, (k0)
    bnez k1, hw_profile_measure_second
    nop
    la k0, hw_profile_second
    lbu k1, (k0)
    addiu k1, k1, 1
    sb k1, (k0)
    li k0, HW_PROFILE_WARMUP_SECONDS
    bne k1, k0, profile_schedule_next
    nop

    // Begin the measured window exactly on a 60-VI boundary. Discard warmup
    // samples while keeping the timer cadence running, just like the ares lab.
    la k0, hw_profile_phase
    li k1, 1
    sb k1, (k0)
    la k0, hw_profile_second
    sb zero, (k0)
    la k0, profile_write_ptr
    la k1, profile_sample_buffer
    sw k1, (k0)
    la k0, profile_sample_count
    sw zero, (k0)
    la k0, profile_last_epc
    sw zero, (k0)
    b profile_schedule_next
    nop

hw_profile_measure_second:
    // Ignore boundaries after measurement (normally unreachable because the
    // diagnostic intentionally freezes once its SRAM snapshot is complete).
    li k0, 1
    bne k1, k0, profile_schedule_next
    nop

    // Record Sodium64's own completed-frames-per-60-VI value for this second.
    la k0, hw_profile_second
    lbu k1, (k0)
    addiu k1, k1, 1
    sb k1, (k0)
    addiu k1, k1, -1
    sll k1, k1, 2
    la k0, hw_profile_hdr_budget
    addu k0, k0, k1
    lbu k1, fps_display
    sw k1, (k0)

    la k0, hw_profile_second
    lbu k1, (k0)
    li k0, HW_PROFILE_MEASURE_SECONDS
    bne k1, k0, profile_schedule_next
    nop

    // Five complete VI windows are captured. From this point onward timing no
    // longer matters: populate the header, write snapshot+header through the
    // standard N64 PI SRAM path, then visibly freeze the diagnostic.
    b hw_profile_finalize
    nop

hw_profile_no_second:
    la k0, hw_profile_last_native
    lbu k1, fps_native
    sb k1, (k0)
#endif

profile_schedule_next:
    // Schedule the next sample relative to the time this interrupt was handled.
    // 65521 is deliberately not a power of two to reduce phase-locking with
    // regular emulator/frame loops.
    mfc0 k0, $9 // Count
    li k1, PROFILE_SAMPLE_INTERVAL
    addu k0, k0, k1
    mtc0 k0, $11 // Compare

    eret
    nop

#ifdef SODIUM64_HW_PROFILE
.align 5
hw_profile_finalize:
    // Timing has ended. All normal GPRs can be used by this terminal path.
    li t0, 0xa0448000
    li t1, 0xa044cfe0
    li t2, 0x50363447
    li t3, 8
8:
    lw t4, (t0)
    bne t4, t2, hw_profile_guard_failed
    nop
    lw t4, (t1)
    bne t4, t2, hw_profile_guard_failed
    nop
    addiu t0, t0, 4
    addiu t1, t1, 4
    addiu t3, t3, -1
    bnez t3, 8b
    nop
    li t0, 1
    sw t0, hw_profile_hdr_guards_ok
    // Dynamic measurement metadata.
    la k0, profile_sample_count
    lw k1, (k0)
    la k0, hw_profile_hdr_samples
    sw k1, (k0)

    lbu k1, skipped_set
    la k0, hw_profile_hdr_skipped
    sw k1, (k0)
    lbu k1, apu_clock
    la k0, hw_profile_hdr_apu_clock
    sw k1, (k0)
    lbu k1, audio_set
    la k0, hw_profile_hdr_audio
    sw k1, (k0)
    lbu k1, precision_set
    la k0, hw_profile_hdr_precision
    sw k1, (k0)
    lbu k1, frame_count
    la k0, hw_profile_hdr_frame_count
    sw k1, (k0)

    // RSP state is diagnostic context only. SP_PC is meaningful only when the
    // status says HALT; host tooling enforces that interpretation.
    lui k0, 0xA404
    lw k1, 0x0010(k0)
    la k0, hw_profile_hdr_sp_status
    sw k1, (k0)
    lui k0, 0xA404
    lw k1, 0x0014(k0)
    la k0, hw_profile_hdr_sp_dma_full
    sw k1, (k0)
    lui k0, 0xA404
    lw k1, 0x0018(k0)
    la k0, hw_profile_hdr_sp_dma_busy
    sw k1, (k0)
    lui k0, 0xA408
    lw k1, 0x0000(k0)
    la k0, hw_profile_hdr_sp_pc
    sw k1, (k0)
    la k0, hw_profile_hdr_complete
    li k1, 1
    sw k1, (k0)

    // PI reads RDRAM, not dirty D-cache lines. Write back both regions before
    // sending them to cartridge SRAM. This happens after measurement is over.
    la k0, profile_magic
    la k1, profile_sample_buffer_end
hw_profile_flush_snapshot:
    cache 0x19, 0x00(k0)
    addiu k0, k0, 0x10
    bne k0, k1, hw_profile_flush_snapshot
    nop

    la k0, hw_profile_header
    la k1, hw_profile_header_end
hw_profile_flush_header:
    cache 0x19, 0x00(k0)
    addiu k0, k0, 0x10
    bne k0, k1, hw_profile_flush_header
    nop

    // Wait for PI idle, then write the large S64P snapshot first. The validity
    // header is written second, so a visible completed capture cannot point at a
    // snapshot that was never transferred.
    lui k0, 0xA460
hw_profile_pi_idle1:
    lw k1, 0x0010(k0)
    andi k1, k1, 0x1
    bnez k1, hw_profile_pi_idle1
    nop
    la k1, profile_magic
    sw k1, 0x0000(k0) // PI_DRAM_ADDR
    li k1, 0x08000000 + HW_PROFILE_SNAPSHOT_OFFSET
    sw k1, 0x0004(k0) // PI_CART_ADDR
    li k1, profile_sample_buffer_end - profile_magic - 1
    sw k1, 0x0008(k0) // PI_RD_LEN: RDRAM -> cart
hw_profile_pi_wait_snapshot:
    lw k1, 0x0010(k0)
    andi k1, k1, 0x1
    bnez k1, hw_profile_pi_wait_snapshot
    nop

    la k1, hw_profile_header
    sw k1, 0x0000(k0)
    li k1, 0x08000000
    sw k1, 0x0004(k0)
    li k1, HW_PROFILE_HEADER_SIZE - 1
    sw k1, 0x0008(k0)
hw_profile_pi_wait_header:
    lw k1, 0x0010(k0)
    andi k1, k1, 0x1
    bnez k1, hw_profile_pi_wait_header
    nop

    la k0, hw_profile_phase
    li k1, 3
    sb k1, (k0)

    // Halt RSP and paint the currently displayed framebuffer solid red. From
    // here the build intentionally never returns: RED SCREEN = SRAM capture done.
    lui k0, 0xA404
    li k1, 0x00000002
    sw k1, 0x0010(k0)

    lw t0, framebuffer
    li t1, 0xF801F801
    li t2, 560 * 224
    addu t2, t2, t0
hw_profile_red_fill:
    sw t1, (t0)
    addiu t0, t0, 4
    bne t0, t2, hw_profile_red_fill
    nop

    lw t0, framebuffer
    li t2, 560 * 224
    addu t2, t2, t0
hw_profile_red_flush:
    cache 0x19, 0x00(t0)
    addiu t0, t0, 0x10
    bltu t0, t2, hw_profile_red_flush
    nop

hw_profile_done:
    b hw_profile_done
    nop
.globl hw_profile_guard_failed
hw_profile_guard_failed:
    // Boot invalidated the old SRAM magic. Never publish a completed header
    // after an owner/PI failure, and never resume the guest from this path.
    mtc0 zero, $12
    b hw_profile_guard_failed
    nop
#endif

#endif // SODIUM64_PROFILE
