/* SPDX-License-Identifier: GPL-3.0-or-later
 * Opt-in save reservation for the pinned N64FlashcartMenu integration.
 * There is one new 32 KiB capture target per launch, with no ROM copies.
 */
#include <fatfs/ff.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "diagnostic_save.h"

#define GUEST_BYTES 8192
#define SAVE_BYTES 32768
#define MAX_IDENT 999999

static const char *fat_path(const char *path) {
    const char *prefix = strstr(path, ":/");
    return prefix ? prefix + 1 : path;
}

bool diagnostic_save_reserve(const char *normal_path, const char *tag, char **output_path) {
    *output_path = NULL;
    if (!normal_path || !tag) return true;
    size_t tag_len = strlen(tag), len = strlen(normal_path);
    if (!tag_len || tag_len > 24 || len < 4 || len > 1024 || strcmp(normal_path + len - 4, ".sav")) return true;
    for (size_t i = 0; i < tag_len; i++) {
        char c = tag[i];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '_' || c == '-')) return true;
    }
    const char *base = strrchr(normal_path, '/');
    base = base ? base + 1 : normal_path;
    /* FAT long-name components cannot exceed 255 UTF-16 units. Byte count is
     * conservative for UTF-8, and rejects instead of silently truncating names. */
    if (strlen(base) - 4 + tag_len + 17 > 255) return true;
    char *target = malloc(len + tag_len + 32);
    unsigned char *data = malloc(SAVE_BYTES);
    if (!target || !data) { free(target); free(data); return true; }
    memset(data, 0xff, GUEST_BYTES);
    memset(data + GUEST_BYTES, 0, SAVE_BYTES - GUEST_BYTES);
    FIL input, output;
    UINT count;
    FRESULT result = f_open(&input, fat_path(normal_path), FA_READ);
    if (result == FR_OK) {
        result = f_read(&input, data, GUEST_BYTES, &count);
        FRESULT closed = f_close(&input);
        /* A short existing save is not silently treated as new progress. */
        if (result != FR_OK || closed != FR_OK || count != GUEST_BYTES) goto failure;
    } else if (result != FR_NO_FILE) goto failure;
    for (unsigned id = 1; id <= MAX_IDENT; id++) {
        snprintf(target, len + tag_len + 32, "%.*s-diag-%s-%06u.sav", (int)(len - 4), normal_path, tag, id);
        result = f_open(&output, fat_path(target), FA_WRITE | FA_CREATE_NEW);
        if (result == FR_EXIST) continue;
        if (result != FR_OK) goto failure;
        result = f_write(&output, data, SAVE_BYTES, &count);
        FRESULT synced = f_sync(&output);
        FRESULT closed = f_close(&output);
        if (result != FR_OK || synced != FR_OK || closed != FR_OK || count != SAVE_BYTES) goto failure;
        /* Failed reservations are deliberately retained. A later launch skips
         * them; an incomplete recorder never passes the decoder's checksum. */
        free(data);
        *output_path = target;
        return false;
    }
failure:
    free(target);
    free(data);
    return true;
}
