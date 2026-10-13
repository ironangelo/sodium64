/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef SODIUM64_SCENE_SLOT_H
#define SODIUM64_SCENE_SLOT_H
#include "scene_state_format.h"
/* Board owns fixed IDs/addresses and source/destination IO. File contents
 * cannot select a destination. SP scratch uses board IO, not a CPU pointer. */
typedef int (*scene_slot_block)(uint32_t,unsigned char[512],int);
typedef int (*scene_slot_owner_io)(unsigned,uint32_t,unsigned,unsigned char *,int);
typedef struct {
    uint32_t bytes,stage;
    unsigned char block[512],piece[512];
} scene_slot_work;
/* Store: 1 committed and full validated readback, 0 invalid/failed slot.
 * Load: 0 rejected before machine mutation, 1 full owner readback,
 * 2 incomplete commit. The caller must latch menu-only recovery for 2. */
int scene_slot_store(scene_slot_work *work,scene_slot_block block,
    scene_slot_owner_io owner_io,const scene_state_binding *binding,
    const scene_state_owner *owners,unsigned count,scene_state_progress progress);
int scene_slot_load(scene_slot_work *work,scene_slot_block block,
    scene_slot_owner_io owner_io,const scene_state_binding *binding,
    const scene_state_owner *owners,unsigned count,scene_state_progress *progress);
#endif
