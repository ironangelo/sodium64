/* SPDX-License-Identifier: GPL-3.0-or-later
 * Private prototype envelope. It does not authorize copying any RAM address. */
#ifndef SODIUM64_SCENE_STATE_FORMAT_H
#define SODIUM64_SCENE_STATE_FORMAT_H
#include <stdint.h>
#define SCENE_STATE_MAGIC 0x53363453u
#define SCENE_STATE_VERSION 1u
#define SCENE_STATE_HEADER_BYTES 64u
#define SCENE_STATE_OWNER_LIMIT 32u
#define SCENE_STATE_MAX_BYTES 0x400000u
typedef struct {uint32_t rom_crc,code_crc,layout_crc,config_crc;} scene_state_binding;
typedef struct {uint32_t id,bytes;} scene_state_owner;
typedef struct {uint32_t guest,render;} scene_state_progress;
typedef int (*scene_state_read)(uint32_t offset,unsigned bytes,unsigned char *destination);
uint32_t scene_state_crc32(const unsigned char *data,unsigned bytes);
/* Descriptors: BE id/bytes/relative payload offset, in whitelist order.
 * CRC covers descriptor table and payload. Header CRC zeroes its own word48.
 * File has exact length64+12*owners+payload; words52..60 are reserved zero. */
int scene_state_header(unsigned char output[64],const scene_state_binding *binding,
    const scene_state_owner *owners,unsigned count,scene_state_progress progress,
    uint32_t body_crc);
/* All bindings/whitelist/bounds/checksums validate before output is changed.
 * 1 valid, 0 malformed/incompatible, -1 read error. Never mutates a machine.
 * Caller provides exclusive512-byte scratch and the actual available length. */
int scene_state_validate(scene_state_read read,unsigned char scratch[512],
    uint32_t available,const scene_state_binding *binding,
    const scene_state_owner *owners,unsigned count,scene_state_progress *progress);
#endif
