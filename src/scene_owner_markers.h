/* SPDX-License-Identifier: GPL-3.0-or-later
 * Zero-byte ELF owner boundaries. No pointers, memory or runtime instructions. */
#ifndef SODIUM64_SCENE_OWNER_MARKERS_H
#define SODIUM64_SCENE_OWNER_MARKERS_H
#ifdef __ASSEMBLER__
#ifdef SODIUM64_SCENE_STATE
#define SCENE_OWNER_BEGIN(name) .globl scene_owner_##name##_begin; scene_owner_##name##_begin:
#define SCENE_OWNER_END(name) .globl scene_owner_##name##_end; .equ scene_owner_##name##_end, .
#else
#define SCENE_OWNER_BEGIN(name)
#define SCENE_OWNER_END(name)
#endif
#endif
#endif
