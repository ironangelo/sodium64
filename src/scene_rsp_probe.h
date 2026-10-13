/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef SODIUM64_SCENE_RSP_PROBE_H
#define SODIUM64_SCENE_RSP_PROBE_H
#include <stdint.h>
typedef uint32_t (*scene_rsp_read)(uint32_t);
typedef void (*scene_rsp_write)(uint32_t,uint32_t);
typedef int (*scene_rsp_transfer)(uint32_t *,uint32_t,int);
typedef int (*scene_rsp_wait)(void);
/* 0: untouched/rejected backup; 1: rebound and memory restored/read back;
 * 2: changed hardware could not be fully recovered, menu-only lockout. */
uint32_t scene_rsp_probe_execute(uint32_t scratch[128],
    const uint32_t *program,unsigned words,unsigned queue,
    scene_rsp_read read,scene_rsp_write write,
    scene_rsp_transfer transfer,scene_rsp_wait wait);
#endif
