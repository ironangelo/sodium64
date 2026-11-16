/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef SODIUM64_LIVE_RSP_SWAP_H
#define SODIUM64_LIVE_RSP_SWAP_H
#include <stdint.h>

#define LIVE_RSP_SWAP_REPORT 0x80555000u

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

#endif
