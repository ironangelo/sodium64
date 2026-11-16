#ifndef SODIUM64_LIVE_DSP_H
#define SODIUM64_LIVE_DSP_H

#define LIVE_DSP_RAM_WRITE 0
#define LIVE_DSP_RAM_READ  1
#define LIVE_DSP_REG_WRITE 2
#define LIVE_DSP_REG_READ  3
#define LIVE_DSP_PCM       4
#define LIVE_DSP_FETCH     5

#define LIVE_DSP_SRAM         0x80500000
#define LIVE_DSP_SHADOW       0x80510000
#define LIVE_DSP_STATE        0x80520000
#define LIVE_DSP_STATS        0x80523000
#define LIVE_DSP_WRAPPER      0x80540000
#define LIVE_DSP_WRAPPER_END  0x80542000

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
    uint32_t required_reg, required_echo, required_le3, last_required_epoch;
#endif
};
#endif
#endif
