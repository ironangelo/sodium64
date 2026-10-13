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
#ifdef SODIUM64_DSP_FULL_CACHE_PROBE
    uint32_t core_cache_index, output_cache_index, core_scratch_offset, output_scratch_offset;
    uint32_t gauss_cache_index, gauss_scratch_offset;
#endif
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
#ifdef SODIUM64_DSP_FULL_CACHE_PROBE
/* Bits1/2/4 select fixed colors for core/PCM/immutable Gaussian copy within
 * the owned snapshot. Only modes0..7 exist; no arbitrary address selector. */
uint32_t full_dsp_probe_execute_mode(unsigned char *ram, unsigned char *scratch,
    full_dsp_probe_transfer transfer, full_dsp_probe_clock clock,
    full_dsp_probe_result result[FULL_DSP_PROBE_CASES], uint32_t mode);
const short *full_dsp_probe_gauss_lease(short *owner);
const short *full_dsp_probe_gauss_current(void);
#endif
#ifdef __cplusplus
}
#endif
#endif
