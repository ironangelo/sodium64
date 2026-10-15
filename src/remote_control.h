/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef SODIUM64_REMOTE_CONTROL_H
#define SODIUM64_REMOTE_CONTROL_H
#include <stdint.h>
#include <stddef.h>
#define REMOTE_REQUEST_MAX 256
#define REMOTE_COUNT_HZ 46875000u
#define REMOTE_FRAME_CONTROL_MAX 36000u
extern volatile uint32_t remote_guest_frames,remote_render_frames,remote_vi_count,remote_presentations;
extern volatile uint32_t remote_buttons,remote_button_frames,remote_paused;
extern volatile uint32_t remote_pause_pending,remote_pause_target;
extern uint32_t remote_boot_tv_type,remote_boot_ram_bytes;
void remote_control_init(void);
void remote_control_frame(uint32_t);
void remote_control_idle(uint32_t);
void remote_process_request(const unsigned char *,size_t,uint32_t);
#endif
