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
#endif
