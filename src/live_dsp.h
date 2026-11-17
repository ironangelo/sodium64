#ifndef SODIUM64_LIVE_DSP_H
#define SODIUM64_LIVE_DSP_H

#define LIVE_DSP_RAM_WRITE 0
#define LIVE_DSP_RAM_READ  1
#define LIVE_DSP_REG_WRITE 2
#define LIVE_DSP_REG_READ  3
#define LIVE_DSP_PCM       4
#define LIVE_DSP_FETCH     5
#define LIVE_DSP_RENDER_YIELD 6

#define LIVE_DSP_SRAM         0x80500000
#define LIVE_DSP_SHADOW       0x80510000
#define LIVE_DSP_STATE        0x80520000
#define LIVE_DSP_STATS        0x80523000
#define LIVE_DSP_WRAPPER      0x80540000
#define LIVE_DSP_WRAPPER_END  0x80542000
#define LIVE_DSP_EPOCH_OFFSET 1364
#define LIVE_DSP_GUEST_CYCLE  21

#define LIVE_DSP_EFFECTS_BASE 0xA0600000u
#define LIVE_DSP_EFFECTS_BYTES 0x00100000u
#define LIVE_DSP_EFFECTS_ROM 0x10020000u
#define LIVE_DSP_EFFECTS_FIRST 0x000C0000u
#define LIVE_DSP_EFFECTS_TAIL 0x100F0000u
#define LIVE_DSP_EFFECTS_PACKED_MAX 0x000D2000u

#ifdef SODIUM64_DSP_LIVE_INPUT_QUEUE
#define LIVE_DSP_INPUT_CAPACITY 32
#define LIVE_DSP_INPUT_EVENT_SHIFT 3
#define LIVE_DSP_INPUT_SIZE 0
#define LIVE_DSP_INPUT_EXCLUSIVE_LIMIT 4
#define LIVE_DSP_INPUT_EVENTS 8
#define LIVE_DSP_INPUT_BYTES (LIVE_DSP_INPUT_EVENTS + (LIVE_DSP_INPUT_CAPACITY << LIVE_DSP_INPUT_EVENT_SHIFT))
#endif

#ifdef __ASSEMBLER__
.macro CALL_LIVE_DSP operation
    sw ra, LIVE_DSP_WRAPPER
    jal live_dsp_bridge
    addiu t0, zero, \operation
    lw ra, LIVE_DSP_WRAPPER
.endm
#else
#include <stdint.h>

struct live_dsp_stats {
    uint32_t ticks, calls, pcm, outputs, writes, echo_words, echo_opcode_changes;
    uint32_t sample_calls, renderer_busy, clock_errors, output_errors, cycles;
    uint32_t core_ticks, core_runs;
#ifdef SODIUM64_DSP_RSP_SWAP
    uint32_t required_reg, required_echo, required_le3, last_required_epoch, required_reg_busy;
#endif
#ifdef SODIUM64_DSP_LIVE_INPUT_QUEUE
    uint32_t queued_ram_writes;
#endif
#if SODIUM64_DSP_EFFECTS_MODE
    uint32_t effects_error, effects_rows;
#endif
};
#endif
#endif
