/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef SODIUM64_FULL_DSP_PROBE_H
#define SODIUM64_FULL_DSP_PROBE_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
enum { FULL_DSP_PROBE_CASES=3, FULL_DSP_PROBE_FRAMES=2048 };
typedef struct {
    uint32_t frames, ticks, max_block_ticks, checksum, nonzero_samples;
} full_dsp_probe_result;
/* The callback exclusively owns a 64 KiB temporary cart buffer. A write
 * copies scratch to cart; a read copies cart to scratch. Never SD access. */
typedef int (*full_dsp_probe_transfer)(unsigned char *scratch, uint32_t offset, int write);
typedef uint32_t (*full_dsp_probe_clock)(void);
/* Return1: RAM restored/readback;0: backup failed before RAM changed;
 * 2: restore failed after RAM changed. Caller must deny gameplay on2. */
uint32_t full_dsp_probe_execute(unsigned char *ram, unsigned char *scratch,
    full_dsp_probe_transfer transfer, full_dsp_probe_clock clock,
    full_dsp_probe_result result[FULL_DSP_PROBE_CASES]);
#ifdef __cplusplus
}
#endif
#endif
