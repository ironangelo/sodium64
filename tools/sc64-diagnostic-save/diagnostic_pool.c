/* SPDX-License-Identifier: GPL-3.0-or-later
 * Reserve a bounded, disjoint set of 32 KiB files and publish its read-only ABI.
 */
#include <stdlib.h>
#include <string.h>
#include "diagnostic_save.h"
#include "diagnostic_pool.h"

static void put32(unsigned char *p, uint32_t value) {
    p[0] = value >> 24; p[1] = value >> 16; p[2] = value >> 8; p[3] = value;
}
static uint32_t get32(const unsigned char *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | ((uint32_t)p[2] << 8) | p[3];
}
static unsigned reservation_id(const char *path) {
    size_t n = strlen(path);
    if (n < 10 || strcmp(path + n - 4, ".sav")) return 0;
    unsigned id = 0;
    for (size_t i = n - 10; i < n - 4; ++i) {
        if (path[i] < '0' || path[i] > '9') return 0;
        id = id * 10 + (unsigned)(path[i] - '0');
    }
    return id;
}

bool diagnostic_pool_prepare(const char *normal, const char *tag, unsigned count,
        uint32_t rom_offset, uint64_t emulator_bytes,
        const diagnostic_pool_backend_t *backend, char **initial_path) {
    if (!initial_path) return true;
    *initial_path = NULL;
    if (!count || count > S64C_MAX_SLOTS || rom_offset != S64C_CART_END ||
        !emulator_bytes || emulator_bytes > S64C_CART_OFFSET || !backend ||
        !backend->card_info || !backend->file_sectors || !backend->publish) return true;
    size_t bytes = S64C_HEADER_BYTES + count * S64C_SLOT_BYTES;
    if (bytes > S64C_CART_END - S64C_CART_OFFSET) return true;
    unsigned char *descriptor = calloc(1, bytes);
    char *paths[S64C_MAX_SLOTS] = {0};
    bool failed = true;
    if (!descriptor) return true;
    if (backend->card_info(backend->context, descriptor + S64C_OFF_SD_INFO)) goto done;
    unsigned any = 0, not_ff = 0;
    for (unsigned i = 0; i < S64C_SD_INFO_BYTES; ++i) {
        any |= descriptor[S64C_OFF_SD_INFO + i];
        not_ff |= descriptor[S64C_OFF_SD_INFO + i] ^ 0xff;
    }
    if (!any || !not_ff) goto done;
    /* Close/sync ALL file allocations before resolving any final FAT mapping. */
    for (unsigned slot = 0; slot < count; ++slot)
        if (diagnostic_save_reserve(normal, tag, &paths[slot]) || !paths[slot]) goto done;
    uint32_t first = 0, end = 0;
    for (unsigned slot = 0; slot < count; ++slot) {
        uint32_t sectors[S64C_SECTORS] = {0}, this_first = 0, this_end = 0;
        unsigned char *entry = descriptor + S64C_HEADER_BYTES + slot * S64C_SLOT_BYTES;
        if (backend->file_sectors(backend->context, paths[slot], sectors, &this_first, &this_end)) goto done;
        if (!this_first || this_end <= this_first) goto done;
        if (!slot) { first = this_first; end = this_end; }
        if (this_first != first || this_end != end) goto done;
        unsigned id = reservation_id(paths[slot]);
        if (!id) goto done;
        for (unsigned old = 0; old < slot; ++old)
            if (get32(descriptor + S64C_HEADER_BYTES + old * S64C_SLOT_BYTES) == id) goto done;
        put32(entry + S64C_SLOT_OFF_ID, id);
        for (unsigned i = 0; i < S64C_SECTORS; ++i) {
            uint32_t lba = sectors[i];
            if (lba < first || lba >= end) goto done;
            for (unsigned old_slot = 0; old_slot <= slot; ++old_slot) {
                unsigned stop = old_slot == slot ? i : S64C_SECTORS;
                const unsigned char *old = descriptor + S64C_HEADER_BYTES + old_slot * S64C_SLOT_BYTES + S64C_SLOT_OFF_LBA;
                for (unsigned j = 0; j < stop; ++j)
                    if (get32(old + j * 4) == lba) goto done;
            }
            put32(entry + S64C_SLOT_OFF_LBA + i * 4, lba);
        }
    }
    put32(descriptor + S64C_OFF_MAGIC, S64C_MAGIC);
    put32(descriptor + S64C_OFF_VERSION, S64C_VERSION);
    put32(descriptor + S64C_OFF_BYTES, (uint32_t)bytes);
    put32(descriptor + S64C_OFF_COUNT, count);
    put32(descriptor + S64C_OFF_SECTORS, S64C_SECTORS);
    put32(descriptor + S64C_OFF_SAVE_BYTES, S64C_SAVE_BYTES);
    put32(descriptor + S64C_OFF_ROM_OFFSET, rom_offset);
    put32(descriptor + S64C_OFF_DATA_FIRST, first);
    put32(descriptor + S64C_OFF_DATA_END, end);
    uint32_t sum = 0;
    for (size_t i = 0; i < bytes; i += 4) sum += get32(descriptor + i);
    put32(descriptor + S64C_OFF_CHECKSUM, 0u - sum);
    if (backend->publish(backend->context, descriptor, bytes)) goto done;
    *initial_path = paths[0]; paths[0] = NULL;
    failed = false;
done:
    for (unsigned slot = 0; slot < count; ++slot) free(paths[slot]);
    free(descriptor);
    return failed;
}
