/*
    Proof-only Gate C bridge from integrated PR #18 CGRAM replay state into
    authoritative E1f half-add arithmetic.

    This proves representation/ownership/arithmetic execution only. It is not
    a production compositor and does not claim Main/Sub provenance, color-math
    gating, final pixels, cadence, or game correctness.
*/
#include <rsp.inc>
#include "defines.h"

.data
.byte 0

.text

// Publishable fixed slot begins at rsp_hcomp_text_start+0x3A8.
.byte 0:0x3A8

draw_bg:
    // H-COMP-resident fault surface for regular rendering.
    j 0xA4001F90
    move v0, t0

hcomp_entry:
    // Read four aligned RGBA5551 shadow entries (two operand pairs) from the
    // just-rendered queue slot. PR #18 has already replayed this frame's CGRAM
    // epochs into this owned shadow before next_frame dispatches H-COMP.
    li a0, SCRN_DATA
    lw a1, HCOMP_RAW_PALETTE_PTRS(sp)
    jal 0xA4001F40
    li a2, 0x1F

    li s0, SCRN_DATA
    li s1, CHAR_DATA
    li s2, 2
    sw zero, 4(s1)

hcomp_pair_loop:
    lhu t0, 0(s0)
    lhu t1, 8(s0)

    // Lossless N64 RGBA5551 -> canonical SNES RGB555, operand A.
    srl t2, t0, 11
    andi t3, t0, 0x07C0
    srl t3, t3, 1
    or t2, t2, t3
    andi t3, t0, 0x003E
    sll t3, t3, 9
    or t0, t2, t3

    // Lossless N64 RGBA5551 -> canonical SNES RGB555, operand B.
    srl t4, t1, 11
    andi t5, t1, 0x07C0
    srl t5, t5, 1
    or t4, t4, t5
    andi t5, t1, 0x003E
    sll t5, t5, 9
    or t1, t4, t5

    // Authoritative E1f packed half-add:
    // (a + b - ((a ^ b) & 0x0421)) >> 1.
    xor t2, t0, t1
    andi t2, t2, 0x0421
    add t3, t0, t1
    sub t3, t3, t2
    srl t3, t3, 1
    sh t3, 0(s1)

    addi s0, s0, 16
    addi s1, s1, 2
    addi s2, s2, -1
    bnez s2, hcomp_pair_loop
    nop

    // Proof-only first-hand mailbox: two RGB555 results plus a zero guard.
    li a0, CHAR_DATA
    li a1, 0xA00F0000
    jal 0xA4001F08
    li a2, 0x7

    // Preserve queue ownership through the bridge. Only now select the next
    // slot, then keep the historical halt/resume -> draw_frame contract.
    xori sp, sp, 4
    li t0, 0x2
    mtc0 t0, COP0_SP_STATUS
    j 0xA400103C
    nop

// Mid-frame Main/Sub ownership helper. Its fixed entry 0x1760 is loaded
// only after semantic TS has completed. Patch Color Image back to the current
// queue-owned Main framebuffer, publish that one command through resident
// rdp_send, then reload the regular fixed slot and resume at resident next_layer.
.byte 0:0x300

hcomp_screen_switch:
    lw t0, FRAMEBUFFER(sp)
    addi t0, t0, 280 * -16
    sw t0, RDP_FRAME + 4
    li a0, RDP_FRAME
    jal 0xA4001F5C
    li a1, RDP_FRAME + 8
    lw a1, OVERLAY_MAIN_SRC
    li t9, 0x1368
    j 0xA4001F7C
    nop

// Keep the externally visible Mode7 entry at 0x1788.
draw_mode7_entry:
    // H-COMP-resident fault surface for true Mode7 rendering.
    j 0xA4001F78
    li t9, 0x1788
