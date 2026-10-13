/* SPDX-License-Identifier: LGPL-2.1-or-later */
/* Opt-in Sodium64 probe: exact unsigned divisibility, no quotient/remainder. */
#ifndef SODIUM64_DSP_COUNTER_PREDICATE_H
#define SODIUM64_DSP_COUNTER_PREDICATE_H
// Each period is2^k times one of30721/1/3/5. The byte encodes odd group2,
// shift4 and offset group2 bits. floor(UINT_MAX/period)=odd_limit>>shift.
static const unsigned dsp_counter_inverse[4] = {0x383f8801u, 0x00000001u, 0xaaaaaaabu, 0xcccccccdu};
static const unsigned dsp_counter_limit[4] = {0x0002221du, 0xffffffffu, 0x55555555u, 0x33333333u};
static const unsigned dsp_counter_offset[4] = {0, 1, 536, 1040};
static const unsigned char dsp_counter_metadata[32] = {
    0x01, // period30721, offset1
    0x6c, // period2048, offset0
    0xa7, // period1536, offset1040
    0xe2, // period1280, offset536
    0x68, // period1024, offset0
    0xa3, // period768, offset1040
    0xde, // period640, offset536
    0x64, // period512, offset0
    0x9f, // period384, offset1040
    0xda, // period320, offset536
    0x60, // period256, offset0
    0x9b, // period192, offset1040
    0xd6, // period160, offset536
    0x5c, // period128, offset0
    0x97, // period96, offset1040
    0xd2, // period80, offset536
    0x58, // period64, offset0
    0x93, // period48, offset1040
    0xce, // period40, offset536
    0x54, // period32, offset0
    0x8f, // period24, offset1040
    0xca, // period20, offset536
    0x50, // period16, offset0
    0x8b, // period12, offset1040
    0xc6, // period10, offset536
    0x4c, // period8, offset0
    0x87, // period6, offset1040
    0xc2, // period5, offset536
    0x48, // period4, offset0
    0x83, // period3, offset1040
    0x44, // period2, offset0
    0x40, // period1, offset0
};
#endif
