/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef SODIUM64_REMOTE_CONTROL_H
#define SODIUM64_REMOTE_CONTROL_H
#include <stdint.h>
#include <stddef.h>
#define REMOTE_PROTOCOL 1
#define REMOTE_REQUEST_MAX 256
#define REMOTE_COUNT_HZ 46875000u
#define REMOTE_FRAME_CONTROL_MAX 36000u
#ifndef SODIUM64_REMOTE_SECTION_OBSERVER
#define SODIUM64_REMOTE_SECTION_OBSERVER 0
#endif
extern volatile uint32_t remote_guest_frames, remote_render_frames;
extern volatile uint32_t remote_boot_ram_bytes;
extern volatile uint32_t remote_vi_count, remote_presentations;
extern volatile uint32_t remote_buttons, remote_button_frames;
extern volatile uint32_t remote_paused, remote_arm_pending;
extern volatile uint32_t remote_pause_pending, remote_pause_target;
#ifdef SODIUM64_SCENE_STATE
extern volatile uint32_t remote_scene_pending, remote_scene_canonical, remote_scene_error;
extern volatile uint32_t remote_scene_framebuffer, remote_scene_origin_guest;
void remote_scene_parked(uint32_t framebuffer);
#endif
void remote_control_init(void);
void remote_control_frame(uint32_t retired_framebuffer);
void remote_control_idle(uint32_t retired_framebuffer);
/* The production parser is also compiled by the synthetic host fixture. */
void remote_process_request(const unsigned char *request, size_t bytes,
                            uint32_t retired_framebuffer);
#if SODIUM64_REMOTE_SECTION_OBSERVER && defined(REMOTE_CONTROL_HOST)
/* Synthetic read model only. Production reads the halted owner and RDRAM. */
uint32_t remote_host_section_queue_id(void);
int remote_host_section_read(uint32_t address, unsigned bytes, uint32_t *value);
#endif
#endif
