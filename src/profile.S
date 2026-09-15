/*
    Experimental profiling support for the ironangelo/sodium64 fork.

    This file is compiled into useful code/data only for PROFILE=1 builds.
    Normal release builds do not enable the CP0 timer or sampling buffer.
*/

#include "defines.h"

#ifdef SODIUM64_PROFILE

#define PROFILE_SAMPLE_INTERVAL 65521
#define PROFILE_SAMPLE_CAPACITY 4096

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

.data

.align 4
// Header values are intentionally simple so emulator-side tooling can locate and
// sanity-check a profile snapshot before interpreting the sample ring buffer.
profile_magic:        .word 0x53363450 // "S64P"
profile_version:      .word 1
profile_interval:     .word PROFILE_SAMPLE_INTERVAL
profile_capacity:     .word PROFILE_SAMPLE_CAPACITY
profile_write_ptr:    .word profile_sample_buffer
profile_sample_count: .word 0
profile_last_epc:     .word 0
profile_reserved:     .word 0

.align 5
profile_sample_buffer: .word 0:PROFILE_SAMPLE_CAPACITY
profile_sample_buffer_end:

.text
.set noreorder

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

    // Schedule the next sample relative to the time this interrupt was handled.
    // 65521 is deliberately not a power of two to reduce phase-locking with
    // regular emulator/frame loops.
    mfc0 k0, $9 // Count
    li k1, PROFILE_SAMPLE_INTERVAL
    addu k0, k0, k1
    mtc0 k0, $11 // Compare

    eret
    nop

#endif // SODIUM64_PROFILE
