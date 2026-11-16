/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef SODIUM64_LIVE_RSP_SWAP_H
#define SODIUM64_LIVE_RSP_SWAP_H
#include <stdint.h>

#define LIVE_RSP_SWAP_REPORT 0x80555000u
#define LIVE_RSP_YIELD_REPORT 0x80555080u

struct rsp_yield_report {
    uint32_t in_spc, in_frame_wait, matched, after_first, bad_pc;
    uint32_t resume_ticks, resume_max_ticks;
    uint32_t section_gaps, section_observed_running, section_lower_max, section_upper_max;
    uint32_t section_lower_ge_250us, section_lower_ge_1ms;
    uint32_t task_count, task_ticks, task_max_ticks;
};

struct rsp_swap_totals {
    uint32_t count, ticks, min_ticks, max_ticks;
};
struct rsp_swap_report {
    struct rsp_swap_totals dmem, both;
    uint32_t busy, unrecognized, bad_pc, bad_status, failure;
    struct rsp_swap_totals rdp_sync;
};

/* The caller runs at the naturally retired renderer boundary and owns 8 MiB. */
void live_rsp_swap(unsigned frame, int (*drain)(uint32_t));
#ifdef SODIUM64_DSP_RSP_YIELD
void live_rsp_yield(unsigned frame, unsigned from_wait, unsigned borrow, int (*drain)(uint32_t));
#endif

#endif
