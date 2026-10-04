/* SPDX-License-Identifier: GPL-3.0-or-later
 * Paired menu/emulator ABI. All words and the additive checksum are big-endian.
 * Read-only cart descriptor, beyond conventional IPL3 checksum and before SNES.
 */
#ifndef S64_CONTINUOUS_SAVE_ABI_H
#define S64_CONTINUOUS_SAVE_ABI_H
#define S64C_MAGIC             0x53363443u /* S64C */
#define S64C_VERSION           1u
#define S64C_CART_OFFSET       0x102000u
#define S64C_CART_END          0x104000u
#define S64C_CART_ADDRESS      0x10102000u
#define S64C_MAX_SLOTS         16u
#define S64C_HEADER_BYTES      72u
#define S64C_SLOT_BYTES        264u
#define S64C_SECTOR_BYTES      512u
#define S64C_SECTORS           64u
#define S64C_SAVE_BYTES        32768u
#define S64C_GUEST_BYTES       8192u
#define S64C_MAX_BYTES         (S64C_HEADER_BYTES + S64C_MAX_SLOTS * S64C_SLOT_BYTES)
#define S64C_OFF_MAGIC         0u
#define S64C_OFF_VERSION       4u
#define S64C_OFF_BYTES         8u
#define S64C_OFF_COUNT         12u
#define S64C_OFF_SECTORS       16u
#define S64C_OFF_SAVE_BYTES    20u
#define S64C_OFF_ROM_OFFSET    24u
#define S64C_OFF_CHECKSUM      28u /* sum of all descriptor words is zero */
#define S64C_OFF_SD_INFO       32u /* raw 16-byte CSD followed by 16-byte CID */
#define S64C_SD_INFO_BYTES     32u
#define S64C_OFF_DATA_FIRST    64u
#define S64C_OFF_DATA_END      68u /* exclusive filesystem data region limit */
#define S64C_SLOT_OFF_ID       0u
#define S64C_SLOT_OFF_RESERVED 4u /* must be zero */
#define S64C_SLOT_OFF_LBA       8u /* 64 nonzero, unique sector addresses */
#endif
