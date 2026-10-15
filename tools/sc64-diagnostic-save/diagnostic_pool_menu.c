/* SPDX-License-Identifier: GPL-3.0-or-later
 * Hardware/FAT adapter for the pinned menu. No FAT code runs inside Sodium64.
 */
#include <fatfs/ff.h>
#include <libdragon.h>
#include <libcart/cart.h>
#include <limits.h>
#include <string.h>
#include "flashcart/flashcart_utils.h"
#include "utils/fs.h"
#include "diagnostic_pool.h"

/* Linked libdragon55aac uses FatFs R0.16. Falling back to an installed R0.15
 * header silently reads FATFS.fsize as n_fatent and rejects valid clusters. */
_Static_assert(FF_DEFINED == 80386 && FFCONF_DEF == 80386, "pinned FatFs header ABI required");
_Static_assert(offsetof(FATFS, n_fatent) == 24, "pinned FATFS cluster-bound offset required");

#define SC64_SR 0x1fff0000u
#define SC64_DATA0 0x1fff0004u
#define SC64_DATA1 0x1fff0008u
#define SC64_IDENTIFIER 0x1fff000cu
#define SC64_BUFFER 0x1ffe0000u
#define SC64_BUSY 0x80000000u
#define SC64_ERROR 0x40000000u

void diagnostic_pool_menu_invalidate(void) {
    /* Before ANY SNES emulator upload, remove old session maps left in SDRAM.
     * Never access SC64 registers on another flashcart or an emulator. */
    if (cart_type == CART_SC) io_write(S64C_CART_ADDRESS, 0);
}

static bool command(unsigned id, uint32_t arg0, uint32_t arg1, uint32_t *rsp0) {
    uint32_t start = TICKS_READ();
    while (io_read(SC64_SR) & SC64_BUSY)
        if ((uint32_t)(TICKS_READ() - start) > TICKS_FROM_MS(2000)) return true;
    io_write(SC64_DATA0, arg0);
    io_write(SC64_DATA1, arg1);
    io_write(SC64_SR, id);
    start = TICKS_READ();
    uint32_t status;
    do {
        status = io_read(SC64_SR);
        if ((uint32_t)(TICKS_READ() - start) > TICKS_FROM_MS(2000)) return true;
    } while (status & SC64_BUSY);
    if (status & SC64_ERROR) return true;
    if (rsp0) *rsp0 = io_read(SC64_DATA0);
    return false;
}
static bool card_info(void *unused, unsigned char info[S64C_SD_INFO_BYTES]) {
    (void)unused;
    if (io_read(SC64_IDENTIFIER) != 0x53437632u) return true; /* SCv2 */
    /* SAVE_TYPE disables old writeback, so reject a pending operation before
     * reserving files or changing that configuration. Never cancel it blindly. */
    uint32_t pending;
    if (command('w', 0, 0, &pending) || pending) return true;
    if (command('i', 0, 1, NULL) || command('i', SC64_BUFFER, 3, NULL)) return true;
    pi_dma_read_data((void *)SC64_BUFFER, info, S64C_SD_INFO_BYTES);
    return false;
}
static bool file_sectors(void *unused, const char *path, uint32_t sectors[S64C_SECTORS],
                         uint32_t *first, uint32_t *end) {
    (void)unused;
    FIL input;
    FRESULT opened = f_open(&input, strip_fs_prefix((char *)path), FA_READ);
    if (opened != FR_OK) { diagnostic_pool_note("map_open", opened, 0); return true; }
    fatfs_fix_file_size(&input);
    FATFS *fs = input.obj.fs;
    uint64_t first64 = fs->database;
    uint64_t end64 = first64 + (uint64_t)(fs->n_fatent - 2) * fs->csize;
    bool invalid = f_size(&input) != S64C_SAVE_BYTES || fs->n_fatent < 3 ||
        !fs->csize || !first64 || end64 <= first64 || end64 > UINT32_MAX;
    uint32_t size = (uint32_t)f_size(&input);
    FRESULT closed = f_close(&input);
    if (closed != FR_OK) { diagnostic_pool_note("map_close", closed, 0); return true; }
    if (invalid) { diagnostic_pool_note("map_geometry", size, fs->csize); return true; }
    *first = (uint32_t)first64; *end = (uint32_t)end64;
    bool failed = fatfs_get_file_sectors((char *)path, sectors, ADDRESS_TYPE_MEM, S64C_SECTORS);
    if (failed) diagnostic_pool_note("map_sectors", *first, *end);
    return failed;
}
static bool publish(void *unused, const unsigned char *descriptor, size_t bytes) {
    (void)unused;
    if (bytes < S64C_HEADER_BYTES || bytes > S64C_CART_END - S64C_CART_OFFSET) return true;
    pi_dma_write_data((void *)descriptor, (void *)S64C_CART_ADDRESS, bytes);
    unsigned char check[64] __attribute__((aligned(8)));
    for (size_t i = 0; i < bytes; i += sizeof check) {
        size_t n = bytes - i < sizeof check ? bytes - i : sizeof check;
        pi_dma_read_data((void *)(S64C_CART_ADDRESS + i), check, n);
        if (memcmp(check, descriptor + i, n)) {
            diagnostic_pool_note("publish_readback", (uint32_t)i, (uint32_t)n);
            return true;
        }
    }
    return false;
}
bool diagnostic_pool_menu_prepare(const char *normal, const char *tag, unsigned count,
                                 uint32_t rom_offset, uint64_t emulator_bytes, char **initial) {
    diagnostic_pool_backend_t backend = { NULL, card_info, file_sectors, publish };
    return diagnostic_pool_prepare(normal, tag, count, rom_offset, emulator_bytes, &backend, initial);
}
bool diagnostic_pool_menu_load_initial(const char *path) {
    /* Caller first selects SRAM through flashcart_load_save(NULL, type), which
     * disables writeback. No W command or save-path auto-writeback is used. */
    uint32_t pending;
    if (io_read(SC64_IDENTIFIER) != 0x53437632u || command('w', 0, 0, &pending) || pending) return true;
    FIL input; UINT bytes;
    if (f_open(&input, strip_fs_prefix((char *)path), FA_READ) != FR_OK) return true;
    fatfs_fix_file_size(&input);
    if (f_size(&input) != S64C_SAVE_BYTES) { f_close(&input); return true; }
    FRESULT result = f_read(&input, (void *)0x08000000u, S64C_SAVE_BYTES, &bytes);
    FRESULT closed = f_close(&input);
    return result != FR_OK || closed != FR_OK || bytes != S64C_SAVE_BYTES;
}
