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
    for (unsigned i = 0; i < 2 * BANK_BYTES / 4; i++)
        staging[i] = (i < BANK_BYTES / 4) ? 0xa5365cc3u : 0;
    __asm__ volatile("sync" ::: "memory");
    prepared = 1;
}

void live_rsp_swap(unsigned frame) {
    if (!prepared) setup();
    if (stats->failure) return;

    const unsigned banks = 1 + (frame & 1);
    const unsigned words = banks * BANK_BYTES / 4;
    const uint32_t status = sp[SP_STATUS], pc = *sp_pc;

    // Both shipping overlays have the same natural retirement address.
    if ((status & 0x63) != 1 || (pc != 0xa90u && pc != 0xa94u) ||
        sp_mem[(BANK_BYTES + 0xa88u) / 4] != 0x24080002u ||
        sp_mem[(BANK_BYTES + 0xa8cu) / 4] != 0x40882000u) {
        ++stats->unrecognized;
        stats->bad_pc = pc;
        stats->bad_status = status;
        return;
    }
    if (dp[2] != dp[1] || (dp[3] & 0x170u) || sp[SP_DMA_FULL] || sp[SP_DMA_BUSY]) {
        ++stats->busy;
        return;
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
    if (!stats->failure) {
        struct rsp_swap_totals *total = banks == 1 ? &stats->dmem : &stats->both;
        if (!total->count || elapsed < total->min_ticks) total->min_ticks = elapsed;
        if (elapsed > total->max_ticks) total->max_ticks = elapsed;
        total->ticks += elapsed;
        ++total->count;
    }

restore_registers:
    sp[SP_MEM_ADDR] = saved_sp_addr;
    sp[SP_DRAM_ADDR] = saved_dram_addr;
}
