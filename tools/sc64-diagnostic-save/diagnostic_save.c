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

static bool valid_target(const char *normal_path, const char *tag) {
    if (!normal_path || !tag) return false;
    size_t tag_len = strlen(tag), len = strlen(normal_path);
    if (!tag_len || tag_len > 24 || len < 4 || len > 1024 || strcmp(normal_path + len - 4, ".sav")) return false;
    for (size_t i = 0; i < tag_len; i++) {
        char c = tag[i];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '_' || c == '-')) return false;
    }
    const char *base = strrchr(normal_path, '/');
    base = base ? base + 1 : normal_path;
    /* FAT long-name components cannot exceed 255 UTF-16 units. Byte count is
     * conservative for UTF-8, and rejects instead of silently truncating names. */
    return strlen(base) - 4 + tag_len + 17 <= 255;
}

static unsigned char ascii_lower(unsigned char c) {
    return c >= 'A' && c <= 'Z' ? c + ('a' - 'A') : c;
}

bool diagnostic_save_seed_cursor(const char *normal_path, const char *tag, unsigned *next_id) {
    if (!next_id || !valid_target(normal_path, tag)) return true;
    const char *normal = fat_path(normal_path), *slash = strrchr(normal, '/');
    const char *base = slash ? slash + 1 : normal;
    size_t prefix_len = strlen(base) - 4 + strlen(tag) + 7;
    char prefix[256];
    snprintf(prefix, sizeof prefix, "%.*s-diag-%s-", (int)(strlen(base) - 4), base, tag);
    size_t dir_len = slash ? (size_t)(slash - normal) : 1;
    if (slash == normal) dir_len = 1; /* Root path retains its slash. */
    char *directory = malloc(dir_len + 1);
    if (!directory) return true;
    memcpy(directory, slash ? normal : ".", dir_len);
    directory[dir_len] = 0;
    DIR dir;
    FRESULT result = f_opendir(&dir, directory);
    free(directory);
    if (result != FR_OK) return true;
    unsigned highest = 0;
    FILINFO info;
    for (;;) {
        result = f_readdir(&dir, &info);
        if (result != FR_OK || !info.fname[0]) break;
        if ((info.fattrib & AM_DIR) || strlen(info.fname) != prefix_len + 10) continue;
        size_t i = 0;
        while (i < prefix_len && ascii_lower((unsigned char)info.fname[i]) ==
                ascii_lower((unsigned char)prefix[i])) ++i;
        if (i != prefix_len) continue;
        unsigned id = 0;
        for (unsigned digit = 0; digit < 6; ++digit, ++i) {
            unsigned char c = (unsigned char)info.fname[i];
            if (c < '0' || c > '9') break;
            id = id * 10 + c - '0';
        }
        if (i != prefix_len + 6 || info.fname[i] != '.' ||
                ascii_lower((unsigned char)info.fname[i+1]) != 's' ||
                ascii_lower((unsigned char)info.fname[i+2]) != 'a' ||
                ascii_lower((unsigned char)info.fname[i+3]) != 'v') continue;
        if (id > highest) highest = id;
    }
    FRESULT closed = f_closedir(&dir);
    if (result != FR_OK || closed != FR_OK || highest == MAX_IDENT) return true;
    *next_id = highest + 1;
    return false;
}

bool diagnostic_save_reserve(const char *normal_path, const char *tag, char **output_path) {
    if (!output_path) return true;
    *output_path = NULL;
    unsigned next_id;
    if (diagnostic_save_seed_cursor(normal_path, tag, &next_id)) return true;
    return diagnostic_save_reserve_from(normal_path, tag, &next_id, output_path);
}

bool diagnostic_save_reserve_from(const char *normal_path, const char *tag,
                                 unsigned *next_id, char **output_path) {
    if (!output_path) return true;
    *output_path = NULL;
    if (!next_id || !*next_id || *next_id > MAX_IDENT || !valid_target(normal_path, tag)) return true;
    size_t tag_len = strlen(tag), len = strlen(normal_path);
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
    for (unsigned id = *next_id; id <= MAX_IDENT; id++) {
        snprintf(target, len + tag_len + 32, "%.*s-diag-%s-%06u.sav", (int)(len - 4), normal_path, tag, id);
        result = f_open(&output, fat_path(target), FA_WRITE | FA_CREATE_NEW);
        if (result == FR_EXIST) { *next_id = id + 1; continue; }
        if (result != FR_OK) goto failure;
        *next_id = id + 1; /* Retain failed reservations and skip them too. */
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
