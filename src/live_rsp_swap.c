/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "live_rsp_swap.h"

#define STAGING 0x00550000u
#define BACKUP  0x00552000u
#define BANK_BYTES 4096u
#define DMA_TIMEOUT 93750u

enum { SP_MEM_ADDR, SP_DRAM_ADDR, SP_RD_LEN, SP_WR_LEN, SP_STATUS, SP_DMA_FULL, SP_DMA_BUSY };
static volatile uint32_t *const sp = (volatile uint32_t *)0xa4040000u;
static volatile uint32_t *const sp_mem = (volatile uint32_t *)0xa4000000u;
static volatile uint32_t *const sp_pc = (volatile uint32_t *)0xa4080000u;
static volatile uint32_t *const dp = (volatile uint32_t *)0xa4100000u;
static volatile uint32_t *const staging = (volatile uint32_t *)(0xa0000000u | STAGING);
static volatile uint32_t *const backup = (volatile uint32_t *)(0xa0000000u | BACKUP);
static struct rsp_swap_report *const stats = (struct rsp_swap_report *)LIVE_RSP_SWAP_REPORT;
static unsigned prepared;

static uint32_t ticks(void) {
    uint32_t count;
    __asm__ volatile("mfc0 %0,$9" : "=r"(count) :: "memory");
    return count;
}

static int dma_idle(void) {
    uint32_t start = ticks();
    while ((sp[SP_DMA_FULL] | sp[SP_DMA_BUSY]) != 0)
        if ((uint32_t)(ticks() - start) >= DMA_TIMEOUT) return 0;
    return 1;
}

static int bank_dma(unsigned phys, unsigned bank, int to_sp) {
    sp[SP_MEM_ADDR] = bank * BANK_BYTES;
    sp[SP_DRAM_ADDR] = phys + bank * BANK_BYTES;
    sp[to_sp ? SP_RD_LEN : SP_WR_LEN] = BANK_BYTES - 1;
    __asm__ volatile("sync" ::: "memory");
    return dma_idle();
}

static void setup(void) {
    *stats = (struct rsp_swap_report){0};
#ifdef SODIUM64_DSP_RSP_YIELD
    *(struct rsp_yield_report *)LIVE_RSP_YIELD_REPORT = (struct rsp_yield_report){0};
#endif
    for (unsigned i = 0; i < 2 * BANK_BYTES / 4; i++)
        staging[i] = (i < BANK_BYTES / 4) ? 0xa5365cc3u : 0;
#ifdef SODIUM64_DSP_RSP_YIELD_TASK
    // Two instructions, no use of live scalar or vector registers.
    staging[BANK_BYTES / 4] = 0xac000000u; // sw zero, 0(zero)
    staging[BANK_BYTES / 4 + 1] = 0x0000000du; // break
#endif
    __asm__ volatile("sync" ::: "memory");
    prepared = 1;
}

static void record(struct rsp_swap_totals *total, uint32_t elapsed) {
    if (!total->count || elapsed < total->min_ticks) total->min_ticks = elapsed;
    if (elapsed > total->max_ticks) total->max_ticks = elapsed;
    total->ticks += elapsed;
    ++total->count;
}

#ifdef SODIUM64_DSP_RSP_YIELD_TASK
static int run_marker(uint32_t pc) {
    struct rsp_yield_report *const metrics = (struct rsp_yield_report *)LIVE_RSP_YIELD_REPORT;
    if (sp_mem[0] != 0xa5365cc3u || sp_mem[BANK_BYTES / 4] != 0xac000000u ||
        sp_mem[BANK_BYTES / 4 + 1] != 0x0000000du) return 0;

    uint32_t start = ticks();
    *sp_pc = 0;
    sp[SP_STATUS] = 5u;
    __asm__ volatile("sync" ::: "memory");
    while ((sp[SP_STATUS] & 0x63) != 3 || *sp_pc != 8u) {
        if ((uint32_t)(ticks() - start) >= DMA_TIMEOUT) {
            sp[SP_STATUS] = 2u; // Stop the known two-instruction task.
            __asm__ volatile("sync" ::: "memory");
            return 0;
        }
    }
    uint32_t elapsed = ticks() - start;
    *sp_pc = pc;
    if (sp_mem[0]) return 0;
    ++metrics->task_count;
    metrics->task_ticks += elapsed;
    if (elapsed > metrics->task_max_ticks) metrics->task_max_ticks = elapsed;
    return 1;
}
#endif

static void exchange(unsigned banks, uint32_t status, uint32_t pc, int (*drain)(uint32_t)) {
    const unsigned words = banks * BANK_BYTES / 4;
    if (sp[SP_DMA_FULL] || sp[SP_DMA_BUSY]) {
        ++stats->busy;
        return;
    }
    if (dp[2] != dp[1] || (dp[3] & 0x770u)) {
        uint32_t start = ticks();
        int ready = drain(DMA_TIMEOUT);
        uint32_t elapsed = ticks() - start;
        if (ready <= 0 || dp[2] != dp[1] || (dp[3] & 0x770u)) {
            if (ready < 0) stats->failure = 7;
            ++stats->busy;
            return;
        }
        record(&stats->rdp_sync, elapsed);
    }

    const uint32_t saved_sp_addr = sp[SP_MEM_ADDR], saved_dram_addr = sp[SP_DRAM_ADDR];
    uint32_t first[2], last[2];
    for (unsigned bank = 0; bank < banks; bank++) {
        first[bank] = sp_mem[bank * BANK_BYTES / 4];
        last[bank] = sp_mem[(bank + 1) * BANK_BYTES / 4 - 1];
    }

    uint32_t start = ticks();
    for (unsigned bank = 0; bank < banks; bank++) {
        if (!bank_dma(BACKUP, bank, 0) || backup[bank * BANK_BYTES / 4] != first[bank] ||
            backup[(bank + 1) * BANK_BYTES / 4 - 1] != last[bank]) {
            stats->failure = 1;
            goto restore_registers;
        }
    }
    for (unsigned bank = 0; bank < banks; bank++) {
        if (!bank_dma(STAGING, bank, 1)) {
            stats->failure = 2;
            if (!dma_idle()) return;
            break;
        }
        if (sp_mem[bank * BANK_BYTES / 4] != staging[bank * BANK_BYTES / 4]) {
            stats->failure = 3;
            break;
        }
    }
#ifdef SODIUM64_DSP_RSP_YIELD_TASK
    if (banks == 2 && !stats->failure && !run_marker(pc)) {
        stats->failure = 9;
        if (!(sp[SP_STATUS] & 1u)) return;
    }
#endif
    // Return the renderer's banks even if staging readback failed.
    for (unsigned bank = 0; bank < banks; bank++) {
        if (!bank_dma(BACKUP, bank, 1)) {
            stats->failure = 4;
            return;
        }
    }

    const uint32_t elapsed = ticks() - start;
    for (unsigned i = 0; i < words; i++) {
        if (sp_mem[i] != backup[i]) {
            stats->failure = 5;
            break;
        }
    }
    if (*sp_pc != pc || sp[SP_STATUS] != status) stats->failure = 6;
    if (!stats->failure) record(banks == 1 ? &stats->dmem : &stats->both, elapsed);

restore_registers:
    sp[SP_MEM_ADDR] = saved_sp_addr;
    sp[SP_DRAM_ADDR] = saved_dram_addr;
}

#ifndef SODIUM64_DSP_RSP_YIELD
void live_rsp_swap(unsigned frame, int (*drain)(uint32_t)) {
    if (!prepared) setup();
    if (stats->failure) return;
    uint32_t status = sp[SP_STATUS], pc = *sp_pc;
    if ((status & 0x63) != 1 || (pc != 0xa90u && pc != 0xa94u) ||
        sp_mem[(BANK_BYTES + 0xa88u) / 4] != 0x24080002u ||
        sp_mem[(BANK_BYTES + 0xa8cu) / 4] != 0x40882000u) {
        ++stats->unrecognized;
        stats->bad_pc = pc;
        stats->bad_status = status;
        return;
    }
    exchange(1 + (frame & 1), status, pc, drain);
}
#else
#ifdef SODIUM64_DSP_RSP_RESIDENT_TEST
enum { RESIDENT_VECTORS = 4, RESIDENT_WORDS = 16, READ_PC = 20 };
static const unsigned owner[RESIDENT_VECTORS] = {9, 16, 17, 19};

static uint32_t lane_word(unsigned word) {
    return 0x81c47a30u ^ (word * 0x18372591u);
}

static int finish_resident(unsigned entry) {
    uint32_t started = ticks();
    unsigned stopped = entry + 4 * (RESIDENT_VECTORS + 1);
    *sp_pc = entry;
    sp[SP_STATUS] = 5;
    __asm__ volatile("sync" ::: "memory");
    while ((sp[SP_STATUS] & 0x63) != 3 || *sp_pc != stopped) {
        if ((uint32_t)(ticks()-started) >= DMA_TIMEOUT) {
            sp[SP_STATUS] = 2; // Halt the known fixed-size load/store program.
            __asm__ volatile("sync" ::: "memory");
            return 0;
        }
    }
    return 1;
}

static void probe_resident(struct rsp_yield_report *metrics) {
    const unsigned status = dp[3];
    // TEXTURE is transient renderer scratch. At a section boundary the RSP
    // owns no DMA there. An outstanding XBUS list must be beyond these 64B.
    if (sp[SP_DMA_BUSY] || sp[SP_DMA_FULL] ||
        ((status & 1) && ((status & 0x740u) || dp[2] != dp[1]) &&
         ((dp[2] & 0xfffu) < 64 || (dp[1] & 0xfffu) < 64 ||
          (dp[2] & 0xfffu) > (dp[1] & 0xfffu)))) {
        ++metrics->resident_skips;
        return;
    }

    uint32_t started = ticks();
    unsigned first = !metrics->resident_imem_installs;
    volatile uint32_t *imem = sp_mem + BANK_BYTES / 4;
    if (first) {
        // The initialization entry at [0,40) is dormant after the first
        // renderer section. Both mode overlay DMAs start at 0x3a8.
        for (unsigned i=0;i<RESIDENT_VECTORS;i++) {
            imem[i] = 0xc8002000u | (owner[i] << 16) | i; // LQV
            imem[READ_PC/4 + i] = 0xe8002000u | (owner[i] << 16) | i; // SQV
        }
        imem[RESIDENT_VECTORS] = 0x0000000du;
        imem[READ_PC/4 + RESIDENT_VECTORS] = 0x0000000du;
        ++metrics->resident_imem_installs;
    }

    uint32_t saved[RESIDENT_WORDS];
    for (unsigned i=0;i<RESIDENT_WORDS;i++) {
        saved[i] = sp_mem[i];
        // Complement every word first, so a missed store cannot pass.
        sp_mem[i] = first ? lane_word(i) : ~lane_word(i);
    }
    __asm__ volatile("sync" ::: "memory");
    if (!finish_resident(first ? 0 : READ_PC)) stats->failure = 10;
    if (!(sp[SP_STATUS] & 1)) return;
    for (unsigned i=0;i<RESIDENT_WORDS;i++) {
        if (!first && sp_mem[i] != lane_word(i) && !stats->failure) {
            metrics->resident_bad_lane = i + 1;
            stats->failure = 11;
        }
        sp_mem[i] = saved[i];
    }
    __asm__ volatile("sync" ::: "memory");

    if (!first && !stats->failure) {
        uint32_t elapsed = ticks() - started;
        metrics->resident_ticks += elapsed;
        if (elapsed > metrics->resident_max_ticks) metrics->resident_max_ticks = elapsed;
        ++metrics->resident_matches;
        if (status & 0x770u) ++metrics->resident_busy;
    }
}
#endif

void live_rsp_yield(unsigned frame, unsigned from_wait, unsigned borrow, int (*drain)(uint32_t)) {
    static uint32_t current_frame, section, resumed_at, last_running;
    static unsigned saw_running;
    uint32_t observed = ticks(), status = sp[SP_STATUS];
    if (current_frame != frame) {
        current_frame = frame;
        section = 0;
        saw_running = 0;
    }

    if ((status & 0x63) != 3) {
        if (!(status & 1u) && section) {
            last_running = observed;
            saw_running = 1;
        }
        return;
    }
    if (!prepared) setup();

    struct rsp_yield_report *const metrics = (struct rsp_yield_report *)LIVE_RSP_YIELD_REPORT;
    if (section) {
        uint32_t upper = ticks() - resumed_at;
        ++metrics->section_gaps;
        if (upper > metrics->section_upper_max) metrics->section_upper_max = upper;
        if (saw_running) {
            uint32_t lower = last_running - resumed_at;
            ++metrics->section_observed_running;
            if (lower > metrics->section_lower_max) metrics->section_lower_max = lower;
            if (lower >= 11719) ++metrics->section_lower_ge_250us;
            if (lower >= 46875) ++metrics->section_lower_ge_1ms;
        }
    }
    saw_running = 0;

    uint32_t pc = *sp_pc;
    // The linked proof checks that both banks have exactly one BREAK, at
    // the final instruction word. The following observed PC is recorded.
    if (sp_mem[(BANK_BYTES + 0xffcu) / 4] != 0x0000000du) {
        stats->bad_pc = pc;
        stats->bad_status = status;
        stats->failure = 8;
        return;
    }
    ++section;
    if (from_wait) ++metrics->in_frame_wait;
    else ++metrics->in_spc;
    ++metrics->matched;
    if (pc) metrics->bad_pc = pc;
    if (section > 1) ++metrics->after_first;

    // Borrow once after an already-completed renderer section.
    if (borrow && section == 2) exchange(1 + (frame & 1), status, pc, drain);
#ifdef SODIUM64_DSP_RSP_RESIDENT_TEST
    if (section == 2) probe_resident(metrics);
#endif
    if (stats->failure) return;
    uint32_t started = ticks();
    *sp_pc = 0xe8u; // hcomp_cgram_return, checked in both linked banks.
    sp[SP_STATUS] = 5u; // Clear HALT and BROKE, preserve renderer signals.
    __asm__ volatile("sync" ::: "memory");
    resumed_at = ticks();
    uint32_t elapsed = resumed_at - started;
    metrics->resume_ticks += elapsed;
    if (elapsed > metrics->resume_max_ticks) metrics->resume_max_ticks = elapsed;
}
#endif
