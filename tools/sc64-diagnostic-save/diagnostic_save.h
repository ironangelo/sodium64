/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef S64_DIAGNOSTIC_SAVE_H
#define S64_DIAGNOSTIC_SAVE_H
#include <stdbool.h>
/* False on success. Allocates a caller-owned path. Ordinary input is read-only;
 * all outputs are exclusively created, including incomplete reservations. */
bool diagnostic_save_reserve(const char *normal_path, const char *tag, char **output_path);
#endif
