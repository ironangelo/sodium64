/*
    Copyright 2021-2025 Hydr8gon

    This file is part of sodium64.

    sodium64 is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published
    by the Free Software Foundation, either version 3 of the License,
    or (at your option) any later version.

    sodium64 is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with sodium64. If not, see <https://www.gnu.org/licenses/>.
*/

#include "defines.h"

#ifdef SODIUM64_DSP_VOICE_BASE
// Sampling uses a pointer to the existing16-byte voice structure. Envelope
// handlers retain their original index ABI, and a0 is restored after calls.
// All fields below are in this same data section; no new storage is needed.
#define VOICE_FIELD(symbol) %lo(symbol - mode_funcs)(t8)
#else
#define VOICE_FIELD(symbol) symbol(t8)
#endif

.globl dsp_sample
.globl read_dspaddr
.globl read_dspdata
.globl write_dspaddr
.globl write_dspdata

#if defined(SODIUM64_HW_PROFILE) || defined(SODIUM64_NATIVE_DIAG)
.globl dsp_buffer
.globl dsp_regs
.globl dsp_pointer
.globl enabled
#endif

.data

.align 4
dsp_buffer: .word 0:0x800
dsp_regs: .byte 0:0x80

#ifdef SODIUM64_DSP_PITCH_CACHE
// Same 16-byte voice stride as the existing register/voice arrays. These are
// raw 14-bit pitches, independent of the host clock and DSP_SAMPLE setting.
.globl dsp_pitches, dsp_pitch_load_begin, dsp_pitch_load_end, write_pitch
.align 4
dsp_pitches: .word 0:0x20
#define PITCH_WRITE write_pitch
#else
#define PITCH_WRITE write_reg
#endif

#ifdef SODIUM64_AUDIO_OBSERVER
.globl dsp_audio_blocks, dsp_audio_idle, dsp_audio_full
.globl dsp_audio_gap_max, dsp_audio_last_count
dsp_audio_blocks: .word 0
dsp_audio_idle: .word 0
dsp_audio_full: .word 0
dsp_audio_gap_max: .word 0
dsp_audio_last_count: .word 0
.globl dsp_audio_dac_rate
dsp_audio_dac_rate: .word DSP_AI_DAC_RATE
#ifdef SODIUM64_DSP_KOFF_RELEASE
.globl dsp_release_steps, dsp_release_last
dsp_release_steps: .word 0
// Private last transition: voice8/before12/after12. No PCM payload here.
dsp_release_last: .word 0
#endif
#endif

#ifdef SODIUM64_BRR_OBSERVER
.globl dsp_brr_next, dsp_brr_count, dsp_brr_records
.globl dsp_brr_trace_begin, dsp_brr_trace_input_done
.globl dsp_brr_trace_end, dsp_brr_trace_output_done
dsp_brr_next: .word 0
dsp_brr_count: .word 0
.align 4
// 32 complete records: voice/header/nybbles, prior halves, output halves.
dsp_brr_records: .word 0:128
#endif

#ifdef SODIUM64_MIX_OBSERVER
.globl dsp_mix_records, dsp_mix_parameters, dsp_mix_output, dsp_mix_ring_offset
.globl dsp_mix_enabled, dsp_mix_count, dsp_mix_ready
.align 4
// Private inputs from the last complete AI-block-ending DSP sample.
// Eight records: full signal16/env16/signed volumes8+8/zero16.
dsp_mix_records: .word 0:16
dsp_mix_parameters: .word 0 // MVOLL8/MVOLR8/zero8/FLG8
dsp_mix_output: .word 0 // Final left16/right16 PCM, before AI.
dsp_mix_ring_offset: .word 0
dsp_mix_enabled: .word 0
dsp_mix_count: .word 0
dsp_mix_ready: .word 0
#endif

.align 4
noise_sample: .hword 0x4000
noise_step: .hword 0x8000
dsp_timer: .hword 0
dsp_pointer: .hword 0
dsp_addr: .byte 0
enabled: .byte 0

.align 4
mode_funcs: .word 0
cached_vols: .word 0
counters: .hword 0
envelopes: .hword 0
next_steps: .hword 0
cur_addrs: .hword 0

.align 4
voice_dups: .dword 0:14
cur_samples: .dword 0:8

.align 4
filter_jumps: .word filter_end, filter_1, filter_2, filter_3
gain_jumps: .word linear_dec, expon_dec, linear_inc, bent_inc

.align 4
write_iomap:
    .word write_vol, write_vol, PITCH_WRITE, PITCH_WRITE // 0x00-0x03
    .word write_reg, write_adsr, write_reg, write_reg // 0x04-0x07
    .word write_reg:(0x0F - 0x07) // 0x08-0x0F
    .word write_vol, write_vol, PITCH_WRITE, PITCH_WRITE // 0x10-0x13
    .word write_reg, write_adsr, write_reg, write_reg // 0x14-0x17
    .word write_reg:(0x1F - 0x17) // 0x18-0x1F
    .word write_vol, write_vol, PITCH_WRITE, PITCH_WRITE // 0x20-0x23
    .word write_reg, write_adsr, write_reg, write_reg // 0x24-0x27
    .word write_reg:(0x2F - 0x27) // 0x28-0x2F
    .word write_vol, write_vol, PITCH_WRITE, PITCH_WRITE // 0x30-0x33
    .word write_reg, write_adsr, write_reg, write_reg // 0x34-0x37
    .word write_reg:(0x3F - 0x37) // 0x38-0x3F
    .word write_vol, write_vol, PITCH_WRITE, PITCH_WRITE // 0x40-0x43
    .word write_reg, write_adsr, write_reg, write_reg // 0x44-0x47
    .word write_reg:(0x4B - 0x47) // 0x48-0x4B
    .word write_kon, write_reg, write_reg, write_reg // 0x4C-0x4F
    .word write_vol, write_vol, PITCH_WRITE, PITCH_WRITE // 0x50-0x53
    .word write_reg, write_adsr, write_reg, write_reg // 0x54-0x57
    .word write_reg:(0x5B - 0x57) // 0x58-0x5B
    .word write_koff, write_reg, write_reg, write_reg // 0x5C-0x5F
    .word write_vol, write_vol, PITCH_WRITE, PITCH_WRITE // 0x60-0x63
    .word write_reg, write_adsr, write_reg, write_reg // 0x64-0x67
    .word write_reg:(0x6B - 0x67) // 0x68-0x6B
    .word time_noise, write_reg, write_reg, write_reg // 0x6C-0x6F
    .word write_vol, write_vol, PITCH_WRITE, PITCH_WRITE // 0x70-0x73
    .word write_reg, write_adsr, write_reg, write_reg // 0x74-0x77
    .word write_reg:(0x7F - 0x77) // 0x78-0x7F

.align 4
timer_rates: // Lookup table for timer rates and offsets
    .hword -1, 0x8000,  2048, 0,  1536, 1040
    .hword 1280, 536,  1024, 0,  768, 1040
    .hword 640, 536,  512, 0,  384, 1040
    .hword 320, 536,  256, 0,  192, 1040
    .hword 160, 536,  128, 0,  96, 1040
    .hword 80, 536,  64, 0,  48, 1040
    .hword 40, 536,  32, 0,  24, 1040
    .hword 20, 536,  16, 0,  12, 1040
    .hword 10, 536,  8, 0,  6, 1040
    .hword 5, 536,  4, 0,  3, 1040
    .hword 2, 0,  1, 0

.text
#ifdef SODIUM64_NATIVE_DIAG_TRACE
.globl native_diag_dsp_start
native_diag_dsp_start:
#endif
.set noreorder

.align 5
dsp_sample:
    // Check if audio is enabled and schedule the next sample
    lbu t0, audio_set
    beqz t0, apu_execute
    addi a3, a3, -DSP_SAMPLE

    // Decrement the global timer once per sample
    lhu t0, dsp_timer
    bnez t0, not_zero
    addi gp, t0, -1
    addi gp, gp, 0x7800
not_zero:
    sh gp, dsp_timer

    // Handle a noise step if the timer matches
    lhu t0, noise_step
    bne t0, gp, skip_noise
    nop
    jal make_noise
    nop

skip_noise:
#ifdef SODIUM64_DSP_VOICE_BASE
.globl dsp_voice_base
dsp_voice_base:
    la a0, mode_funcs
#endif
    // Set initial values for generating a sample
    li t6, -1 // Voice count
    li t5, 0 // Left sample
    li t4, 0 // Right sample
    lbu sp, enabled
#ifdef SODIUM64_MIX_OBSERVER
.globl dsp_mix_init_begin, dsp_mix_init_end
dsp_mix_init_begin:
    lhu t0, dsp_pointer
    andi t0, t0, 0xFFF
    li t1, 0xFFC
    bne t0, t1, dsp_mix_init_end
    nop
    sw zero, dsp_mix_ready
    sw sp, dsp_mix_enabled
    la t0, dsp_mix_records
    li t1, 8
dsp_mix_clear:
    sd zero, (t0)
    addiu t0, t0, 8
    addiu t1, t1, -1
    bnez t1, dsp_mix_clear
    nop
dsp_mix_init_end:
#endif

next_voice:
    // Check if a voice is enabled
    addi t6, t6, 1
    srl t0, sp, t6
    beqz t0, write_sample
    andi t0, t0, 0x1
    beqz t0, next_voice

    // Handle an envelope step if the timer matches
    sll t8, t6, 4
#ifdef SODIUM64_DSP_VOICE_BASE
    addu t8, t8, a0
#endif
    lhu t0, VOICE_FIELD(next_steps)
    bne t0, gp, get_pitch
    nop
    lw t0, VOICE_FIELD(mode_funcs)
#ifdef SODIUM64_DSP_VOICE_BASE
.globl dsp_voice_envelope_index
dsp_voice_envelope_index:
    sll t8, t6, 4
#endif
    jalr t0
    nop
#ifdef SODIUM64_DSP_VOICE_BASE
.globl dsp_voice_restore_base
dsp_voice_restore_base:
    la a0, mode_funcs
    addu t8, t8, a0
#endif

get_pitch:
    // Get the pitch scaler for the current voice
#ifdef SODIUM64_DSP_PITCH_CACHE
dsp_pitch_load_begin:
    lhu t0, VOICE_FIELD(dsp_pitches)
dsp_pitch_load_end:
#else
    lhu t0, VOICE_FIELD(dsp_regs + 0x2) // VxPITCH(L/H)
    sll t1, t0, 8
    srl t0, t0, 8
    or t0, t0, t1
    andi t0, t0, 0x3FFF
#endif

    // Increase the voice's position counter by the scaler
    lhu t9, VOICE_FIELD(counters)
    addu t2, t9, t0
    sh t2, VOICE_FIELD(counters)

    // Decode a new 4-sample BRR chunk if the counter overflows
    xor t9, t9, t2
    srl t9, t9, 14
    bnez t9, decode_chunk
    nop

mix_sample:
    // Load the noise sample if enabled for the voice
    lbu t0, dsp_regs + 0x3D // NON
    srl t0, t0, t6
    andi t0, t0, 0x1
    beqz t0, load_sample
    nop
    lh t0, noise_sample
    b skip_sample

load_sample:
    // Load the current sample from the voice's buffer
    sll t1, t6, 3
    srl t3, t2, 11
    andi t3, t3, 0x6
    xori t3, t3, 0x6
    add t1, t1, t3
    lh t0, cur_samples(t1)
    beqz t0, next_voice
    nop

skip_sample:
#ifdef SODIUM64_DSP_DRY_MIX
.globl dsp_dry_voice_begin, dsp_dry_voice_end
dsp_dry_voice_begin:
    // BRR samples are half-scaled; noise keeps its unsigned15-bit LFSR.
    // Doubling with signed16 wrap recovers the full selected signal in both.
    sll t0, t0, 17
    lhu t1, VOICE_FIELD(envelopes)
    sra t0, t0, 16
    mult t0, t1
    lb t2, VOICE_FIELD(dsp_regs + 0x0)
    lb t3, VOICE_FIELD(dsp_regs + 0x1)
#ifdef SODIUM64_MIX_OBSERVER
.globl dsp_mix_input_begin, dsp_mix_input_end
dsp_mix_input_begin:
    lhu t7, dsp_pointer
    andi t7, t7, 0xFFF
    li t9, 0xFFC
    bne t7, t9, dsp_mix_input_end
    nop
    la t7, dsp_mix_records
    sll t9, t6, 3
    addu t7, t7, t9
    sh t0, 0(t7)
    sh t1, 2(t7)
    sb t2, 4(t7)
    sb t3, 5(t7)
dsp_mix_input_end:
#endif
    mflo t0
    sra t0, t0, 11
    // The DSP clears bit0 after applying the full eleven-bit envelope.
    sra t0, t0, 1
    sll t0, t0, 1

    mult t0, t2
    mflo t1
    sra t1, t1, 7
    addu t5, t5, t1
    // Saturate after each voice in hardware order, before master volume.
    sll t7, t5, 16
    sra t7, t7, 16
    beq t7, t5, dsp_dry_left_ready
    sra t9, t5, 31
    xori t5, t9, 0x7FFF
dsp_dry_left_ready:
    beq t2, t3, dsp_dry_same_volume
    nop
    mult t0, t3
    mflo t1
    sra t1, t1, 7
dsp_dry_same_volume:
    addu t4, t4, t1
    sll t7, t4, 16
    sra t7, t7, 16
    beq t7, t4, dsp_dry_voice_end
    sra t9, t4, 31
    xori t4, t9, 0x7FFF
dsp_dry_voice_end:
    b next_voice
    nop
#else
    // Get the cached volumes for each channel
    lh t2, cached_vols + 0(t8)
    lh t3, cached_vols + 2(t8)

    // Mix the sample on the left channel
    mult t0, t2
    mflo t1
    sra t1, t1, 14
    beq t2, t3, same_volume
    addu t5, t5, t1

    // Mix the sample on the right channel
    mult t0, t3
    mflo t1
    sra t1, t1, 14
same_volume:
    b next_voice
    addu t4, t4, t1
#endif

.align 5
write_sample: // t5: left, t4: right
#ifdef SODIUM64_DSP_DRY_MIX
.globl dsp_dry_output_begin, dsp_dry_output_end
dsp_dry_output_begin:
    // Signed master volume applies to each already saturated dry accumulator.
    // Echo/FIR, Gaussian selection and DSP register timing remain separate.
    lb t0, dsp_regs + 0x0C
    lb t1, dsp_regs + 0x1C
    mult t5, t0
    lbu t2, dsp_regs + 0x6C
    mflo t5
    sra t5, t5, 7
    // NEC requires two intervening instructions from MFLO to the next MULT.
    // Move the existing left signed16 cast here; arithmetic/cost is unchanged.
    sll t5, t5, 16
    sra t5, t5, 16
    mult t4, t1
    mflo t4
    sra t4, t4, 7
    // Reference dry contributions cast to signed16 before adding echo.
    sll t4, t4, 16
    sra t4, t4, 16
    andi t2, t2, 0x40
    beqz t2, dsp_dry_output_end
    nop
    move t5, zero
    move t4, zero
dsp_dry_output_end:
#endif
    // Write a sample to the buffer
    andi t4, t4, 0xFFFF
    sll t5, t5, 16
    or t0, t4, t5
    lhu t1, dsp_pointer
    sw t0, UNCACHED(dsp_buffer)(t1)
#ifdef SODIUM64_MIX_OBSERVER
.globl dsp_mix_commit_begin, dsp_mix_commit_end
dsp_mix_commit_begin:
    andi t7, t1, 0xFFF
    li t9, 0xFFC
    bne t7, t9, dsp_mix_commit_end
    nop
    sw t0, dsp_mix_output
    sw t1, dsp_mix_ring_offset
    lbu t2, dsp_regs + 0x0C
    lbu t3, dsp_regs + 0x1C
    lbu t7, dsp_regs + 0x6C
    sll t2, t2, 24
    sll t3, t3, 16
    or t2, t2, t3
    or t2, t2, t7
    sw t2, dsp_mix_parameters
    lw t2, dsp_mix_count
    addiu t2, t2, 1
    sw t2, dsp_mix_count
    li t2, 1
    sw t2, dsp_mix_ready
dsp_mix_commit_end:
#endif

    // Increment the sample pointer
    addi a0, t1, 4
    andi t0, a0, 0x1FFF
    sh t0, dsp_pointer

    // Submit a buffer to the AI when one is ready
    andi t0, a0, 0xFFF
    bnez t0, apu_execute
    lui t0, 0xA450 // AI register upper address
    la t1, dsp_buffer - 0x1000
    add t1, t1, a0 // Buffer address
    sw t1, 0x0000(t0) // AI_DRAM_ADDR
#ifdef SODIUM64_AUDIO_OBSERVER
.globl dsp_audio_observe_begin, dsp_audio_observe_end
dsp_audio_observe_begin:
    // Observe once per 1024 stereo frames, never alter AI submission policy.
    // FULL/BUSY are libdragon audio.c bits31/30. These are observations,
    // not counts of proven dropped samples. No sample or guest state changes.
    // t1 is overwritten by AI_LENGTH below; explicit base avoids $at writes.
    la t2, dsp_audio_blocks
    lw t3, 0x000C(t0)
    srl t4, t3, 31
    lw t1, 8(t2)
    addu t1, t1, t4
    sw t1, 8(t2)
    srl t4, t3, 30
    andi t4, t4, 1
    xori t4, t4, 1
    lw t1, 4(t2)
    addu t1, t1, t4
    sw t1, 4(t2)
    mfc0 t3, $9
    lw t4, 0(t2)
    beqz t4, dsp_audio_observe_gap_done
    nop
    lw t4, 16(t2)
    subu t4, t3, t4
    lw t1, 12(t2)
    sltu t1, t1, t4
    beqz t1, dsp_audio_observe_gap_done
    nop
    sw t4, 12(t2)
dsp_audio_observe_gap_done:
    sw t3, 16(t2)
    lw t4, 0(t2)
    addiu t4, t4, 1
    sw t4, 0(t2)
dsp_audio_observe_end:
#endif
    li t1, 0x00001000 // Buffer length
    j apu_execute
    sw t1, 0x0004(t0) // AI_LENGTH

.align 5
decode_chunk: // t2: counter, t6: voice, t8: index or voice pointer
    // Stay in the same BRR block until the counter overflows
    lhu t0, VOICE_FIELD(cur_addrs)
    srl t3, t2, 16
    beqz t3, decode_samples
    nop

    // Move to the next 9-byte BRR block based on current flags
    lbu t9, apu_ram(t0) // Header
    andi t3, t9, 0x1 // End
    beqz t3, decode_samples
    addi t0, t0, 9
    andi t3, t9, 0x2 // Loop
    beqz t3, end_voice
    nop

    // Get the address of the voice's sample table entry
    lbu t0, dsp_regs + 0x5D // DIR
    lbu t3, VOICE_FIELD(dsp_regs + 0x4) // VxSRCN
    sll t0, t0, 8
    sll t3, t3, 2
    add t0, t0, t3

    // Load the loop address and start decoding from there
    lhu t0, apu_ram + 0x2(t0)
    sll t3, t0, 8
    srl t0, t0, 8
    or t0, t0, t3
    andi t0, t0, 0xFFFF

decode_samples:
    // Get the address of the voice's sample buffer
    la t3, cur_samples
    sll v1, t6, 3
    add v1, v1, t3

    // Configure things based on the BRR block header
    sh t0, VOICE_FIELD(cur_addrs)
    lbu t9, apu_ram(t0) // Header
    srl t1, t9, 4 // Shift
    andi t9, t9, 0xC // Filter
    lw t9, filter_jumps(t9)

    // Load 4 4-bit BRR samples at once to be decoded
    srl t3, t2, 13
    andi t3, t3, 0x6
    add t0, t0, t3
    lbu t3, apu_ram + 1(t0)
    lbu s0, apu_ram + 2(t0)
    sll t3, t3, 8
    or s0, s0, t3
#ifdef SODIUM64_BRR_OBSERVER
dsp_brr_trace_begin:
    // Only existing decoder scratch; record raw input before range transform.
    lw t7, dsp_brr_next
    sll t7, t7, 4
    la t3, dsp_brr_records
    addu t7, t7, t3
    lhu t0, VOICE_FIELD(cur_addrs)
    lbu t0, apu_ram(t0)
    sll t3, t6, 8
    or t0, t0, t3
    sll t0, t0, 16
    or t0, t0, s0
    sw t0, 0(t7)
    lw t0, 0(v1)
    sw t0, 4(t7)
dsp_brr_trace_input_done:
#endif
#ifdef SODIUM64_DSP_BRR_ACCURATE
    // Invalid ranges13-15 decode as0/-2048. Transform all four nybbles to
    // 0/-8 once, then use range9 in the existing sample loop.
    sltiu t3, t1, 13
    bnez t3, brr_range_ready
    nop
    andi s0, s0, 0x8888
    li t1, 9
brr_range_ready:
#endif
    li s1, 8

next_sample:
    // Pass the next sample, sign-extended and shifted, to the filter
    addi s1, s1, -2
    sll t3, s1, 1
    srl t0, s0, t3
    sll t0, t0, 28
    sra t0, t0, 28
    sll t0, t0, t1
    jr t9
    sra t0, t0, 1

filter_1:
    // Apply the old sample, multiplied by 0.9375
    addi t7, s1, 2
    andi t7, t7, 0x6
    add t3, v1, t7
    lh t7, (t3)
    add t0, t0, t7
#ifdef SODIUM64_DSP_BRR_ACCURATE
    // Arithmetic floor of the negative term differs from subtracting floor.
    subu t7, zero, t7
    sra t7, t7, 4
    b filter_end
    add t0, t0, t7
#else
    sra t7, t7, 4
    b filter_end
    sub t0, t0, t7
#endif

filter_2:
    // Apply the old sample, multiplied by 1.90625
    addi t7, s1, 2
    andi t7, t7, 0x6
    add t3, v1, t7
    lh t7, (t3)
    sll t3, t7, 1
    add t0, t0, t3
    sll t3, t7, 1
    add t3, t3, t7
#ifdef SODIUM64_DSP_BRR_ACCURATE
    subu t3, zero, t3
    sra t3, t3, 5
    add t0, t0, t3
#else
    sra t3, t3, 5
    sub t0, t0, t3
#endif

    // Apply the older sample, multiplied by -0.9375
    addi t7, s1, 4
    andi t7, t7, 0x6
    add t3, v1, t7
    lh t7, (t3)
    sub t0, t0, t7
    sra t3, t7, 4
    b filter_end
    add t0, t0, t3

filter_3:
    // Apply the old sample, multiplied by 1.796875
    addi t7, s1, 2
    andi t7, t7, 0x6
    add t3, v1, t7
    lh t7, (t3)
    sll t3, t7, 1
    add t0, t0, t3
    sll t3, t7, 3
    add t3, t3, t7
    sll t7, t7, 2
    add t3, t3, t7
#ifdef SODIUM64_DSP_BRR_ACCURATE
    subu t3, zero, t3
    sra t3, t3, 6
    add t0, t0, t3
#else
    sra t3, t3, 6
    sub t0, t0, t3
#endif

    // Apply the older sample, multiplied by -0.8125
    addi t7, s1, 4
    andi t7, t7, 0x6
    add t3, v1, t7
    lh t7, (t3)
    sub t0, t0, t7
    sll t3, t7, 1
    add t3, t3, t7
    sra t3, t3, 4
    add t0, t0, t3

filter_end:
#ifdef SODIUM64_DSP_BRR_ACCURATE
    // Reference BRR clamps the intermediate to signed16, doubles with
    // signed16 wrap, then stores it. This mixer keeps half-scaled samples:
    // that operation is exactly sign-extension of15 bits after the clamp.
    sll t3, t0, 16
    sra t3, t3, 16
    beq t0, t3, brr_clamped
    sra t7, t0, 31
    xori t0, t7, 0x7FFF
brr_clamped:
    sll t0, t0, 17
    sra t0, t0, 17
#endif
    // Store the sample and loop until all 4 are done
    add t3, v1, s1
    bnez s1, next_sample
    sh t0, (t3)
#ifdef SODIUM64_BRR_OBSERVER
dsp_brr_trace_end:
    // All four stores are complete; publish the ring only after both words.
    lw t7, dsp_brr_next
    sll t7, t7, 4
    la t3, dsp_brr_records
    addu t7, t7, t3
    lw t0, 0(v1)
    sw t0, 8(t7)
    lw t0, 4(v1)
    sw t0, 12(t7)
    lw t7, dsp_brr_next
    addiu t7, t7, 1
    andi t7, t7, 31
    sw t7, dsp_brr_next
    lw t7, dsp_brr_count
    addiu t7, t7, 1
    sw t7, dsp_brr_count
dsp_brr_trace_output_done:
#endif
    j mix_sample

end_voice:
    // Disable the voice if it ends without loop
    li t0, 1
    sll t0, t0, t6
    xori t0, t0, 0xFF
    and sp, sp, t0
    sb sp, enabled
    j next_voice
    nop

.align 5
make_noise:
    // Generate a new noise sample based on the old one
    lh t0, noise_sample
    sll t1, t0, 14
    sll t2, t0, 13
    xor t1, t1, t2
    andi t1, t1, 0x4000
    srl t0, t0, 1
    or t0, t0, t1
    sh t0, noise_sample
    j time_noise
    nop

.align 5
time_noise:
    // Schedule the next step using the noise rate
    lbu t0, dsp_regs + 0x6C // FLG
    andi a0, t0, 0x1F
    sll a0, a0, 2
    j update_step
    li t6, 8 // Noise

.align 5
attack_mode: // t6: voice, t8: offset
    // Increase the envelope by 32
    lhu t0, envelopes(t8)
    addi t0, t0, 32
    sh t0, envelopes(t8)

    // Switch to decay mode at level 0x7E0 and clip to 0x7FF
    blt t0, 0x7E0, attack_time
    nop
    la t3, decay_mode
    sw t3, mode_funcs(t8)
    li t1, 0x7FF
    blt t0, t1, decay_time
    nop
    sh t1, envelopes(t8)
    j decay_time
    nop

.align 5
attack_time: // t6: voice
    // Schedule the next step using the attack rate
    sll t1, t6, 4
    lbu t0, dsp_regs + 0x5(t1) // VxADSR1
    andi a0, t0, 0xF
    sll a0, a0, 3
    j update_step
    addi a0, a0, 4

.align 5
decay_mode: // t6: voice, t8: offset
    // Decrease the envelope by an exponential amount
    lhu t0, envelopes(t8)
    addi t2, t0, -1
    srl t2, t2, 8
    addi t2, t2, 1
    sub t0, t0, t2
    sh t0, envelopes(t8)

    // Calculate the sustain level boundary
    lbu t1, dsp_regs + 0x6(t8) // VxADSR2
    andi t1, t1, 0xE0
    sll t1, t1, 3
    addi t1, t1, 0x100

    // Switch to sustain mode at the boundary and clip to zero
    bgt t0, t1, decay_time
    nop
    la t3, sustain_mode
    sw t3, mode_funcs(t8)
    bgtz t0, sustain_time
    nop
    sh zero, envelopes(t8)
    j sustain_time
    nop

.align 5
decay_time: // t6: voice
    // Schedule the next step using the decay rate
    sll t1, t6, 4
    lbu t0, dsp_regs + 0x5(t1) // VxADSR1
    andi a0, t0, 0x70
    srl a0, a0, 1
    j update_step
    addi a0, a0, 64

.align 5
sustain_mode: // t6: voice, t8: offset
    // Decrease the envelope by an exponential amount
    lhu t0, envelopes(t8)
    addi t2, t0, -1
    srl t2, t2, 8
    addi t2, t2, 1
    sub t0, t0, t2
    sh t0, envelopes(t8)

    // Disable the voice if its envelope decreases to zero
    bgtz t0, sustain_time
    li t0, 1
    sll t0, t0, t6
    xori t0, t0, 0xFF
    and sp, sp, t0
    sb sp, enabled
    jr ra
    nop

.align 5
sustain_time: // t6: voice
    // Schedule the next step using the sustain rate
    sll t1, t6, 4
    lbu t0, dsp_regs + 0x6(t1) // VxADSR2
    andi a0, t0, 0x1F
    j update_step
    sll a0, a0, 2

.align 5
gain_mode: // t6: voice, t8: offset
    // Jump to the handler for the current gain mode
    lbu t0, dsp_regs + 0x7(t8) // VxGAIN
    andi t1, t0, 0x60
    srl t1, t1, 3
    lw t0, gain_jumps(t1)
    jr t0
    nop

linear_dec:
    // Decrease the envelope by a fixed amount and clip to zero
    lhu t0, envelopes(t8)
    addi t0, t0, -32
    sh t0, envelopes(t8)
    bgtz t0, gain_time
    nop
    sh zero, envelopes(t8)
    j gain_time
    nop

expon_dec:
    // Decrease the envelope by an exponential amount and clip to zero
    lhu t0, envelopes(t8)
    addi t2, t0, -1
    srl t2, t2, 8
    addi t2, t2, 1
    sub t0, t0, t2
    sh t0, envelopes(t8)
    bgtz t0, gain_time
    nop
    sh zero, envelopes(t8)
    j gain_time
    nop

linear_inc:
    // Increase the envelope by a fixed amount and clip to 0x7FF
    lhu t0, envelopes(t8)
    addi t0, t0, 32
    sh t0, envelopes(t8)
    li t1, 0x7FF
    blt t0, t1, gain_time
    nop
    sh t1, envelopes(t8)
    j gain_time
    nop

bent_inc:
    // Increase the envelope by an amount bent at 0x600 and clip to 0x7FF
    lhu t0, envelopes(t8)
    slti t1, t0, 0x600
    sll t1, t1, 1
    li t2, 8
    sll t1, t2, t1
    add t0, t0, t1
    sh t0, envelopes(t8)
    li t1, 0x7FF
    blt t0, t1, gain_time
    nop
    sh t1, envelopes(t8)
    j gain_time
    nop

.align 5
gain_time: // t6: voice
    // Check whether direct or custom gain is selected
#ifdef SODIUM64_DSP_DRY_MIX
.globl dsp_gain_preserve_accumulators
dsp_gain_preserve_accumulators:
    // t4/t5 hold the current stereo accumulators when called by dsp_sample.
    // Use existing handler scratch rather than erasing earlier right voices.
    sll t1, t6, 4
    lbu t0, dsp_regs + 0x7(t1) // VxGAIN
    andi t2, t0, 0x80
    beqz t2, direct_gain
#else
    sll t4, t6, 4
    lbu t0, dsp_regs + 0x7(t4) // VxGAIN
    andi t1, t0, 0x80
    beqz t1, direct_gain
#endif

    // Schedule the next step using the custom gain rate
    andi a0, t0, 0x1F
    sll a0, a0, 2
    j update_step

direct_gain:
    // Set a fixed volume for direct gain
    sll t0, t0, 4
#ifdef SODIUM64_DSP_DRY_MIX
    sh t0, envelopes(t1)
    li t0, 0xFFFF
    sh t0, next_steps(t1)
#else
    sh t0, envelopes(t4)
    li t0, 0xFFFF
    sh t0, next_steps(t4)
#endif
    j update_vols
    nop

.align 5
update_step: // a0: rate, t6: voice
    // Get values for updating a step timer
    lhu t2, dsp_timer
    lw t0, timer_rates(a0)
    addi t2, t2, -1 // Base
    srl t1, t0, 16 // Rate
    bgez t2, calc_step
    andi t0, t0, 0xFFFF // Offset
    addi t2, t2, 0x7800

calc_step:
    // Calculate the timer value of the next step
    add t0, t0, t2
    div t0, t1
    mfhi t3
    sub t2, t2, t3
    bgez t2, set_step
    nop
    addi t2, t2, 0x7800

set_step:
    // Update a voice's step timer and cached volume
    bge t6, 8, set_noise
    sll t1, t6, 4
    sh t2, next_steps(t1)
    j update_vols
    nop

set_noise:
    // Update the noise step timer
    sh t2, noise_step
    jr ra
    nop

.align 5
update_vols: // t6: voice
#ifdef SODIUM64_DSP_DRY_MIX
.globl dsp_dry_skip_vol_cache
dsp_dry_skip_vol_cache:
    // The exact dry path reads the full envelope and signed register bytes.
    // Its quantized legacy product cache has no consumer in this build.
    jr ra
    nop
#else
    // Get a voice's envelope and channel volumes
    sll t1, t6, 4
    lhu t0, envelopes(t1)
    lb t2, dsp_regs + 0x0(t1) // VxVOLL
    lb t3, dsp_regs + 0x1(t1) // VxVOLR
    srl t0, t0, 4

    // Cache the multiplied volumes to save a step during mixing
    mult t2, t0
    mflo t2
    sh t2, cached_vols + 0(t1)
    mult t3, t0
    mflo t3
    sh t3, cached_vols + 2(t1)
    jr ra
    nop
#endif

#ifdef SODIUM64_DSP_KOFF_RELEASE
.globl release_mode
.align 5
release_mode: // t6: voice, t8: stride, gp: current DSP timer
    // The reference release decreases by8 per generated sample, independent
    // of ADSR/GAIN rates. Keep the voice audible until its envelope reaches0.
    lhu t0, envelopes(t8)
#ifdef SODIUM64_AUDIO_OBSERVER
    move t1, t0
#endif
    addiu t0, t0, -8
    bgtz t0, release_store
    nop
    li t0, 1
    sll t0, t0, t6
    xori t0, t0, 0xFF
    and sp, sp, t0
    sb sp, enabled
    move t0, zero
release_store:
    sh t0, envelopes(t8)
#ifdef SODIUM64_AUDIO_OBSERVER
    sll t1, t1, 12
    or t1, t1, t0
    sll t2, t6, 24
    or t1, t1, t2
    sw t1, dsp_release_last
    lw t1, dsp_release_steps
    addiu t1, t1, 1
    sw t1, dsp_release_steps
#endif
    // Match the next sample's decrement, including the0x7800 timer wrap.
    addiu t0, gp, -1
    bgez t0, release_timer_ready
    nop
    addiu t0, t0, 0x7800
release_timer_ready:
    sh t0, next_steps(t8)
    j update_vols
    nop
#endif

.align 5
read_dspaddr: // v0: value
    // Read the DSP register address
    lbu v0, dsp_addr
    jr ra
    nop

.align 5
read_dspdata: // v0: value
    // Read a value from a DSP register
    lbu t0, dsp_addr
    andi t0, t0, 0x7F // Mirror
    lbu v0, dsp_regs(t0)
    jr ra
    nop

.align 5
write_dspaddr: // a1: value
    // Write the DSP register address
    sb a1, dsp_addr
    jr ra
    nop

.align 5
write_dspdata: // a1: value
    // Write a value to a DSP register if within bounds
    lbu t0, dsp_addr
    andi t1, t0, 0x80
    bnez t1, write_reg
    sll t1, t0, 2
    sb a1, dsp_regs(t0)

    // Jump to the register's handler function
    lw t1, write_iomap(t1)
    jr t1
    nop

write_reg:
    // Do nothing extra for regular register writes
    jr ra
    nop

#ifdef SODIUM64_DSP_PITCH_CACHE
.align 5
write_pitch: // t0: address; the raw byte has already been stored
    // Both pitch-byte handlers update the cache before returning to the APU.
    // Invalid DSP addresses branch to write_reg before either store/handler.
    andi t0, t0, 0x70
    lhu t1, dsp_regs + 0x2(t0)
    sll t2, t1, 8
    srl t1, t1, 8
    or t1, t1, t2
    andi t1, t1, 0x3FFF
    sh t1, dsp_pitches(t0)
    jr ra
    nop
#endif

.align 5
write_vol: // t0: address
    // Update a voice's cached volumes when changed
    j update_vols
    srl t6, t0, 4

.align 5
write_adsr: // t0: address
#ifdef SODIUM64_DSP_KOFF_RELEASE
    // A register write cannot exit an already latched release. KON below
    // explicitly restarts the voice and selects attack/gain again.
    andi t4, t0, 0xF0
    lw t1, mode_funcs(t4)
    la t2, release_mode
    bne t1, t2, adsr_not_releasing
    nop
    jr ra
    nop
adsr_not_releasing:
#endif
    // Switch a voice's envelope to gain if selected
    lbu t1, dsp_regs(t0) // VxADSR1
    andi t4, t0, 0xF0
    srl t6, t0, 4
    andi t0, t1, 0x80
    beqz t0, use_gain
    nop
    jr ra
    nop

.align 5
write_kon: // a1: value
    // Set voices to enabled
    lbu t0, enabled
    move t5, ra
    or t0, t0, a1
    sb t0, enabled
    li t6, -1

next_on:
    // Check if a voice was just enabled
    addi t6, t6, 1
    srl t0, a1, t6
    beqz t0, kon_end
    andi t0, t0, 0x1
    beqz t0, next_on
    nop

    // Get the address of the voice's sample table entry
    lbu t0, dsp_regs + 0x5D // DIR
    sll t4, t6, 4
    lbu t1, dsp_regs + 0x04(t4) // VxSRCN
    sll t0, t0, 8
    sll t1, t1, 2
    add t0, t0, t1

    // Load the start address and reset the voice
    lhu t0, apu_ram(t0)
    sll t1, t0, 8
    srl t0, t0, 8
    or t0, t0, t1
    sh t0, cur_addrs(t4)
    sh zero, counters(t4)
    sh zero, envelopes(t4)
    sll t1, t6, 3
    sd zero, cur_samples(t1)

    // Check whether the voice uses ADSR or gain
    lbu t1, dsp_regs + 0x5(t4) // VxADSR1
    la ra, next_on
    andi t1, t1, 0x80
    beqz t1, use_gain
    nop

    // Set the voice to attack mode and schedule the first step
    la t0, attack_mode
    sw t0, mode_funcs(t4)
    j attack_time
    nop

use_gain:
    // Set the voice to gain mode and schedule the first step
    la t0, gain_mode
    sw t0, mode_funcs(t4)
    j gain_time
    nop

kon_end:
    // Return from the function
    jr t5
    nop

.align 5
write_koff: // a1: value
#ifdef SODIUM64_DSP_KOFF_RELEASE
    // Latch release on the selected voices; preserve enabled/envelope now.
    la t2, release_mode
    lhu t3, dsp_timer
    addiu t3, t3, -1
    bgez t3, koff_timer_ready
    nop
    addiu t3, t3, 0x7800
koff_timer_ready:
    andi t7, a1, 0xFF
    li t6, -1
koff_next_voice:
    addiu t6, t6, 1
    srl t0, t7, t6
    beqz t0, koff_return
    andi t0, t0, 1
    beqz t0, koff_next_voice
    sll t1, t6, 4
    sw t2, mode_funcs(t1)
    sh t3, next_steps(t1)
    b koff_next_voice
    nop
koff_return:
    jr ra
    nop
#else
    // Set voices to disabled
    lbu t0, enabled
    xori t1, a1, 0xFF
    and t0, t0, t1
    sb t0, enabled
    jr ra
    nop
#endif


#ifdef SODIUM64_NATIVE_DIAG_TRACE
.globl native_diag_dsp_end
native_diag_dsp_end:
#endif

#ifdef SODIUM64_DSP_GAIN_PROBE
// Pause-only synthetic register-owner probe. It never generates/submits audio.
// C uses the ordinary ABI; the enclosing remote bridge protects guest GPR/HI/LO.
.globl remote_dsp_gain_probe
remote_dsp_gain_probe: // a0:voice, a1:synthetic GAIN, a2:left/right result pointer
    sltiu t0, a0, 8
    beqz t0, dsp_gain_probe_invalid
    nop
    sltiu t0, a1, 256
    beqz t0, dsp_gain_probe_invalid
    nop
    daddiu sp, sp, -64
    sd ra, 0(sp)
    sd s0, 8(sp)
    sd s1, 16(sp)
    move s0, a2
    sll s1, a0, 4
    lbu t0, dsp_regs + 7(s1)
    sw t0, 24(sp)
    lw t0, cached_vols(s1)
    sw t0, 28(sp)
    lhu t0, envelopes(s1)
    sw t0, 32(sp)
    lhu t0, next_steps(s1)
    sw t0, 36(sp)
    sb a1, dsp_regs + 7(s1)
    li t4, 0x2468
    li t5, 0x1357
    move t6, a0
    jal gain_time
    nop
    sw t5, 0(s0)
    sw t4, 4(s0)
    // Restore every field the existing handler can write before returning.
    lw t0, 24(sp)
    sb t0, dsp_regs + 7(s1)
    lw t0, 28(sp)
    sw t0, cached_vols(s1)
    lw t0, 32(sp)
    sh t0, envelopes(s1)
    lw t0, 36(sp)
    sh t0, next_steps(s1)
    // Independent readback makes a failed restoration an explicit failure.
    lw t1, 24(sp)
    lbu t0, dsp_regs + 7(s1)
    xor t9, t0, t1
    lw t1, 28(sp)
    lw t0, cached_vols(s1)
    xor t0, t0, t1
    or t9, t9, t0
    lw t1, 32(sp)
    lhu t0, envelopes(s1)
    xor t0, t0, t1
    or t9, t9, t0
    lw t1, 36(sp)
    lhu t0, next_steps(s1)
    xor t0, t0, t1
    or t9, t9, t0
    sltiu v0, t9, 1
    ld ra, 0(sp)
    ld s0, 8(sp)
    ld s1, 16(sp)
    jr ra
    daddiu sp, sp, 64
dsp_gain_probe_invalid:
    jr ra
    move v0, zero
#endif
