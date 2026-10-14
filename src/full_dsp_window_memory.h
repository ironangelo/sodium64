/* Original experimental owner contract. No commercial inputs. */
#ifndef SODIUM64_FULL_DSP_WINDOW_MEMORY_H
#define SODIUM64_FULL_DSP_WINDOW_MEMORY_H
#include <stdint.h>

// All base renderer/ROM/event owners end at physical4MiB. Leave IPL3's
// top64KiB untouched. Every payload and guard owns complete32-byte lines.
#define DSP_WINDOW_OWNER_BEGIN 0x00400000u
#define DSP_WINDOW_GUARD_BYTES 32u
#define DSP_WINDOW_SHADOW_BEGIN (DSP_WINDOW_OWNER_BEGIN + DSP_WINDOW_GUARD_BYTES)
#define DSP_WINDOW_RAM_BYTES 65536u
#define DSP_WINDOW_REFERENCE_BEGIN (DSP_WINDOW_SHADOW_BEGIN + DSP_WINDOW_RAM_BYTES + DSP_WINDOW_GUARD_BYTES)
#define DSP_WINDOW_PRODUCER_BEGIN (DSP_WINDOW_REFERENCE_BEGIN + DSP_WINDOW_RAM_BYTES + DSP_WINDOW_GUARD_BYTES)
#define DSP_WINDOW_STATE_BEGIN (DSP_WINDOW_PRODUCER_BEGIN + DSP_WINDOW_RAM_BYTES + DSP_WINDOW_GUARD_BYTES)
#define DSP_WINDOW_STATE_BYTES 16384u
#define DSP_WINDOW_OWNER_END (DSP_WINDOW_STATE_BEGIN + DSP_WINDOW_STATE_BYTES + DSP_WINDOW_GUARD_BYTES)
// Separate persistent host diagnostic owner, not part of the temporary probe.
// native_diag.S binds this symbol; its arm paths require captured8MiB first.
#define DSP_WINDOW_SNAPSHOT_BEGIN 0x00438000u
#define DSP_WINDOW_SNAPSHOT_BYTES 32768u

typedef struct {
    uint32_t owner_begin, owner_end, shadow_begin, reference_begin, producer_begin, state_begin;
} full_dsp_window_memory_plan;

// Pure admission; never dereferences an upper-memory pointer. On rejection,
// erase a stale plan so a caller cannot reuse addresses admitted on another boot.
static inline int full_dsp_window_memory_select(uint32_t captured_rdram_bytes,
                                               full_dsp_window_memory_plan* plan) {
    if (!plan) return 0;
    plan->owner_begin=plan->owner_end=plan->shadow_begin=plan->reference_begin=plan->producer_begin=plan->state_begin=0;
    if (captured_rdram_bytes != 8388608u) return 0;
    plan->owner_begin=DSP_WINDOW_OWNER_BEGIN; plan->owner_end=DSP_WINDOW_OWNER_END;
    plan->shadow_begin=DSP_WINDOW_SHADOW_BEGIN; plan->reference_begin=DSP_WINDOW_REFERENCE_BEGIN;
    plan->producer_begin=DSP_WINDOW_PRODUCER_BEGIN;
    plan->state_begin=DSP_WINDOW_STATE_BEGIN;
    return 1;
}

typedef struct {
    uint32_t stage, clocks, state_checks, producer_reads, echo_writes, owner_bytes;
} full_dsp_window_memory_result;

#ifdef __cplusplus
extern "C" {
#endif
#ifdef SODIUM64_DSP_FULL_WINDOW
uint32_t full_dsp_window_memory_probe(uint32_t captured_rdram_bytes,
                                     full_dsp_window_memory_result*);
#endif
#ifdef __cplusplus
}
#endif
#endif
