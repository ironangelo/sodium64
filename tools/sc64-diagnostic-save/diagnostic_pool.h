/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef S64_DIAGNOSTIC_POOL_H
#define S64_DIAGNOSTIC_POOL_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "continuous_save_abi.h"
/* Callbacks return false on success. Platform errors retain every reservation.
 * The real menu adapter and host fault injection execute the same pool core. */
typedef struct {
    void *context;
    bool (*card_info)(void *, unsigned char[S64C_SD_INFO_BYTES]);
    bool (*file_sectors)(void *, const char *, uint32_t[S64C_SECTORS], uint32_t *, uint32_t *);
    bool (*publish)(void *, const unsigned char *, size_t);
} diagnostic_pool_backend_t;
bool diagnostic_pool_prepare(const char *, const char *, unsigned, uint32_t, uint64_t,
                             const diagnostic_pool_backend_t *, char **);
/* Real N64FlashcartMenu adapters: false on success, no automatic writeback. */
bool diagnostic_pool_menu_prepare(const char *, const char *, unsigned, uint32_t, uint64_t, char **);
bool diagnostic_pool_menu_load_initial(const char *);
void diagnostic_pool_menu_invalidate(void);
#endif
