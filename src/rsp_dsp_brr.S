/* SPDX-License-Identifier: GPL-3.0-or-later
 * Eight independent BRR groups, four successive samples per voice.
 * Input000..05F: encodedABCD, history1, history2, rangeQ16, rawscale, filter0..3.
 * Constants060..11F: zero,one,minusone,half,F000,two,three,F800,F400,E600,1000,3000.
 * Output120..15F: four eight-lane signed16 sample vectors, always even.
 * Caller owns/restores all vectors/ACC/VCO/VCC/SP memory. No DMA/RCP/DIV.
 */
#include <rsp.inc>
.data
.word 0
.text
.set noreorder
.set noat
    .irp vec,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17
    .word 0xc8002000 | (\vec << 16) | \vec
    .endr
    vand $v18,$v06,$v06,0
    vand $v19,$v06,$v06,0
    vand $v20,$v06,$v06,0
    vand $v21,$v06,$v06,0
    vand $v22,$v06,$v06,0
    ctc2 zero,$0
    // One-time per-lane filter selection; all initial flags are irrelevant.
    veq $v23,$v05,$v07,0
    vmrg $v18,$v13,$v18,0
    vmrg $v19,$v07,$v19,0
    vmrg $v20,$v08,$v20,0
    veq $v23,$v05,$v11,0
    vmrg $v18,$v14,$v18,0
    vmrg $v21,$v08,$v21,0
    vmrg $v22,$v16,$v22,0
    veq $v23,$v05,$v12,0
    vmrg $v18,$v15,$v18,0
    vmrg $v21,$v08,$v21,0
    vmrg $v22,$v17,$v22,0
    .irp sample,0,1,2,3
    vand $v28,$v00,$v10,0
    vmudm $v24,$v01,$v18,0
    vmudm $v25,$v01,$v09,0
    vmudm $v26,$v02,$v09,0
    vmudm $v27,$v26,$v22,0
    vmudm $v29,$v28,$v03,0
    // Range<=12: rangeQ16=2^(range+3), rawscale1.
    // Invalid range: rangeQ16=1 yields sign(-1/0), rawscale2048.
    vmudh $v30,$v29,$v04,0
    // Preserve full48-bit ACC across partial sums; saturate only final VD.
    vmadh $v30,$v24,$v07,0
    vmadh $v30,$v25,$v19,0
    vmadh $v30,$v01,$v20,0
    vmadh $v30,$v26,$v21,0
    vmadh $v30,$v27,$v07,0
    vaddc $v31,$v30,$v30,0
    .word 0xe8002000 | (31 << 16) | (0x12+\sample)
    .if \sample < 3
    vand $v02,$v01,$v01,0
    vand $v01,$v31,$v31,0
    vaddc $v00,$v00,$v00,0
    vaddc $v00,$v00,$v00,0
    vaddc $v00,$v00,$v00,0
    vaddc $v00,$v00,$v00,0
    .endif
    .endr
    break
