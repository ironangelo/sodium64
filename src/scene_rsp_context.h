/* SPDX-License-Identifier: GPL-3.0-or-later
 * Temporary DMEM owners only; the caller preserves all original SP memory.
 * No reciprocal instruction exists in current banks; adding one opens a new
 * DIVIN/DIVOUT/DIVDP owner gate. This is not complete machine state. */
#ifndef SODIUM64_SCENE_RSP_CONTEXT_H
#define SODIUM64_SCENE_RSP_CONTEXT_H
#define SCENE_RSP_GPR 0x000
#define SCENE_RSP_VECTOR 0x080
#define SCENE_RSP_ACC_HI 0x280
#define SCENE_RSP_ACC_MID 0x290
#define SCENE_RSP_ACC_LO 0x2A0
#define SCENE_RSP_VCO 0x2B0
#define SCENE_RSP_VCC 0x2B4
#define SCENE_RSP_VCE 0x2B8
#define SCENE_RSP_CONTEXT_BYTES 0x2BC
/* CPU derives these helpers from saved HI/MID; never authoritative state.
 * NEG_HI lane=-(HI+(MID>>15)) mod16; ONE=1; NEG_HALF=0x8000. */
#define SCENE_RSP_NEG_HI 0x2C0
#define SCENE_RSP_ONE 0x2D0
#define SCENE_RSP_NEG_HALF 0x2E0
#define SCENE_RSP_WORK_END 0x2F0
#ifndef __ASSEMBLER__
#include "scene_rsp_probe.h"
extern volatile uint32_t scene_rsp_context_stage;
extern volatile uint32_t scene_rsp_context_mismatch_word;
/* 0 untouched/rejected; 1 exact context/memory readback; 2 unsafe/incomplete
 * hardware recovery, caller must permit menu recovery only. */
uint32_t scene_rsp_context_roundtrip(uint32_t scratch[128],
    const uint32_t *capture,unsigned capture_words,
    const uint32_t *restore,unsigned restore_words,
    scene_rsp_read read,scene_rsp_write write,scene_rsp_transfer transfer,
    scene_rsp_wait wait);
#endif
#endif
