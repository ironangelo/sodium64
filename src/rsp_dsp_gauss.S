/* SPDX-License-Identifier: GPL-3.0-or-later
 * Eight independent raw S-DSP Gaussian values, exact per-tap floors and
 * first-three signed16 wrap. Not a full DSP or a renderer scheduling path.
 * DMEM000..07F: four pairs of sample/unsigned(coefficient<<5) vectors.
 * DMEM080..08F: eight FFFE masks. DMEM090..09F: eight signed16 results.
 * Clobbers v00..v14/ACC/VCO. Caller must own and restore RSP context.
 */
#include <rsp.inc>
.data
.word 0
.text
.set noreorder
.set noat
    lqv $v00,0,0x00,zero
    lqv $v01,0,0x10,zero
    lqv $v02,0,0x20,zero
    lqv $v03,0,0x30,zero
    lqv $v04,0,0x40,zero
    lqv $v05,0,0x50,zero
    lqv $v06,0,0x60,zero
    lqv $v07,0,0x70,zero
    // Signed samples * unsigned shifted coefficients, high32-product half:
    // floor(sample * (coefficient<<5) / 65536) == floor(sample*coefficient/2048).
    vmudm $v08,$v00,$v01,0
    vmudm $v09,$v02,$v03,0
    vmudm $v10,$v04,$v05,0
    vmudm $v11,$v06,$v07,0
    vaddc $v12,$v08,$v09,0
    vaddc $v12,$v12,$v10,0
    ctc2 zero,$0
    vadd $v12,$v12,$v11,0
    lqv $v13,0,0x80,zero
    vand $v14,$v12,$v13,0
    sqv $v14,0,0x90,zero
    break
