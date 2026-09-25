/*
    Proof-only third fixed-slot H-COMP overlay for Gate C.
    Dispatch/coexistence only; no compositor output is produced.
*/
#include <rsp.inc>
#include "defines.h"

.data
.byte 0

.text

// Publishable slot begins at rsp_hcomp_text_start+0x3A8.
.byte 0:0x3A8

draw_bg:
    // Neutral H-COMP-resident fault surface for regular rendering.
    j 0xA4001F90
    move v0, t0

hcomp_entry:
    // First-hand execution marker. Mode7 has already cleared F10 in its true
    // entry delay slot; publish F10..F17 to calibrated-good RDRAM before HALT.
    li t0, 0x51
    sb t0, HCOMP_OVERLAY_PROOF_HCOMP
    li a0, HCOMP_OVERLAY_PROOF_MODE7
    li a1, 0xA00F0000
    jal 0xA4001F08 // Common resident dma_write in both renderer payloads.
    li a2, 0x7
    li t0, 0x2
    mtc0 t0, COP0_SP_STATUS
    j 0xA400103C
    nop

// hcomp_entry grows only into pre-existing slot padding; external Mode7 entry
// remains fixed at 0x1788 and total payload remains 0x790.
.byte 0:0x3B0

draw_mode7_entry:
    // Neutral H-COMP-resident fault surface for Mode7 rendering.
    j 0xA4001F78
    li t9, 0x1788
