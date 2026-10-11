/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef S64_DIAGNOSTIC_SAVE_H
#define S64_DIAGNOSTIC_SAVE_H
#include <stdbool.h>
/* False on success. Allocates a caller-owned path. Ordinary input is read-only;
 * all outputs are exclusively created, including incomplete reservations. */
bool diagnostic_save_reserve(const char *normal_path, const char *tag, char **output_path);
/* Scan the parent directory once for this exact stem/tag and select one above
 * its highest six-digit ID. Failure leaves the cursor unchanged. No writes. */
bool diagnostic_save_seed_cursor(const char *normal_path, const char *tag, unsigned *next_id);
/* A pool shares the seeded cursor across reservations; exclusive creation
 * remains authoritative when an entry appears after the directory scan. */
bool diagnostic_save_reserve_from(const char *normal_path, const char *tag,
                                 unsigned *next_id, char **output_path);
#endif
