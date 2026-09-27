/*
    Proof-only third fixed-slot H-COMP overlay for Gate C.
    Coexistence/lifetime only; no compositor arithmetic or pixel output.
*/
#include <rsp.inc>
#include "defines.h"

.data
.byte 0

.text

// Publishable fixed slot begins at rsp_hcomp_text_start+0x3A8.
.byte 0:0x3A8

draw_bg:
    // Neutral H-COMP-resident fault surface for regular rendering.
    j 0xA4001F90
    move v0, t0

hcomp_entry:
    // First-hand execution marker, then preserve the historical HALT contract.
    li t0, 0x51
    sb t0, HCOMP_OVERLAY_PROOF_HCOMP
    li t0, 0x2
    mtc0 t0, COP0_SP_STATUS
    j 0xA400103C
    nop

// Keep the externally visible Mode7 entry at 0x1788.
.byte 0:0x3C0

draw_mode7_entry:
    // Neutral H-COMP-resident fault surface for Mode7 rendering.
    j 0xA4001F78
    li t9, 0x1788
