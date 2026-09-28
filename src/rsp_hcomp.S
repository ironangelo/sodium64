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

    // Gate-C clean CGADSUB discriminator. Read one already-rendered active
    // sample from compact semantic Sub (row0,x12) and the corresponding
    // current semantic Main sample (published row8,x12) while this handed
    // queue slot still owns FRAMEBUFFER(sp). This is proof plumbing only:
    // pinned ares consumes submitted RDP lists synchronously; real-N64-safe
    // RDP->RSP ownership/fencing remains a separate production requirement.
    li a0, SCRN_DATA
    li a1, 0xA00E4018
    jal 0xA4001F40
    li a2, 0x7

    li a0, SCRN_DATA + 8
    lw a1, FRAMEBUFFER(sp)
    addi a1, a1, 0x1198
    jal 0xA4001F40
    li a2, 0x7

    // Read the corresponding per-pixel Main winner tag. The proof-only Z16
    // logical surface begins at 0xA00F0000 but Main lands in published rows
    // 8..15 exactly like the owned color target; x12,row8 is 0xA00F1198.
    li a0, SCRN_DATA + 16
    lui a1, 0xA00F
    ori a1, a1, 0x1198
    jal 0xA4001F40
    li a2, 0x7

    // Canonicalize the rendered Main RGBA5551 sample to SNES RGB555.
    lhu t0, SCRN_DATA + 8
    lhu t1, SCRN_DATA
    srl t2, t0, 11
    andi t3, t0, 0x07C0
    srl t3, t3, 1
    or t2, t2, t3
    andi t3, t0, 0x003E
    sll t3, t3, 9
    or t0, t2, t3

    // Canonicalize the rendered Sub RGBA5551 sample to SNES RGB555.
    srl t4, t1, 11
    andi t5, t1, 0x07C0
    srl t5, t5, 1
    or t4, t4, t5
    andi t5, t1, 0x003E
    sll t5, t5, 9
    or t1, t4, t5

    // Convert validated primitive-Z winner tags directly to the corresponding
    // CGADSUB mask: BG1 0x0C00 >> 11 = 1, BG2 0x1400 >> 11 = 2.
    // This is the first clean rung where eligibility follows rendered winner
    // provenance rather than a guest-hardcoded BG identity.
    lhu t6, SCRN_DATA + 16
    srl t4, t6, 11
    andi t4, t4, 0x3
    lbu t2, CGADSUB
    and t2, t2, t4
    sltu t2, zero, t2
    move t3, t0
    beqz t2, hcomp_gate_store
    nop

    // Reuse the authoritative E1f packed half-add on the live rendered pair.
    xor t3, t0, t1
    andi t4, t3, 0x0421
    add t3, t0, t1
    sub t3, t3, t4
    srl t3, t3, 1

hcomp_gate_store:
    // Self-describing proof record. Keep the validated first 8 B stable, then
    // append the exact provenance tag/mask and carried CGADSUB value in row0,
    // which is disjoint from the provenance surface's authoritative rows8..15.
    sh t0, CHAR_DATA + 8
    sh t1, CHAR_DATA + 10
    sh t3, CHAR_DATA + 12
    sh t2, CHAR_DATA + 14
    sh t6, CHAR_DATA + 16
    sh t4, CHAR_DATA + 18
    lbu t5, CGADSUB
    sh t5, CHAR_DATA + 20
    sh zero, CHAR_DATA + 22
    li a0, CHAR_DATA + 8
    li a1, 0xA00F0008
    jal 0xA4001F08
    li a2, 0xF

    // Disable the proof-only primitive-Z update before the next frame begins,
    // then restore the two RDP_FRAME palette commands temporarily borrowed by
    // the TM provenance pass. draw_frame rewrites the palette address word.
    lui t5, 0x2F00
    ori t5, t5, 0x88FF
    sw t5, RDP_FRAME + 8
    lui t5, 0x0004
    ori t5, t5, 0x0001
    sw t5, RDP_FRAME + 12
    li a0, RDP_FRAME + 8
    jal 0xA4001F5C
    li a1, RDP_FRAME + 16

    lui t5, 0x3D10
    sw t5, RDP_FRAME + 8
    sw zero, RDP_FRAME + 12
    lui t5, 0x3300
    sw t5, RDP_FRAME + 16
    lui t5, 0x0040
    sw t5, RDP_FRAME + 20

    // Preserve queue ownership through the bridge. Only now select the next
    // slot, then keep the historical halt/resume -> draw_frame contract.
    xori sp, sp, 4
    li t0, 0x2
    mtc0 t0, COP0_SP_STATUS
    j 0xA400103C
    nop

// Mid-frame clean Main provenance helper. This lives in H-COMP's otherwise
// unused fixed-slot tail so the externally visible switch entry remains 0x1760.
hcomp_provenance_switch_helper:
    // First keep the already-validated semantic Color Image retarget.
    lw t0, FRAMEBUFFER(sp)
    addi t0, t0, 280 * -16
    sw t0, RDP_FRAME + 4
    li a0, RDP_FRAME
    jal 0xA4001F5C
    li a1, RDP_FRAME + 8

    // After frame-start palette upload is consumed, borrow its two command
    // slots to enable primitive-depth Z updates without Z compare and bind the
    // proof-only Z16 provenance surface. The underflow mirrors Main geometry:
    // logical 0x00F0000 - 16*560 = 0x000EDD00.
    lui t0, 0x2F00
    ori t0, t0, 0x88FF
    sw t0, RDP_FRAME + 8
    lui t0, 0x0004
    ori t0, t0, 0x0025
    sw t0, RDP_FRAME + 12
    lui t0, 0x3E00
    sw t0, RDP_FRAME + 16
    lui t0, 0x000E
    ori t0, t0, 0xDD00
    sw t0, RDP_FRAME + 20
    li a0, RDP_FRAME + 8
    jal 0xA4001F5C
    li a1, RDP_FILL

    // Reuse those same 16 bytes as two immutable per-layer depth commands for
    // the regular overlay. Historical E1b dynamically validated these exact
    // primitive-depth codes as stored winner tags 0x0C00 (BG1) / 0x1400 (BG2).
    lui t0, 0x2E00
    lui t1, 0x1800
    sw t0, RDP_FRAME + 8
    sw t1, RDP_FRAME + 12
    sw t0, RDP_FRAME + 16
    lui t1, 0x2800
    sw t1, RDP_FRAME + 20

    // Load regular BG/OBJ rendering back over this slot and resume at the
    // already-validated resident next_layer address.
    lw a1, OVERLAY_MAIN_SRC
    li t9, 0x1364
    j 0xA4001F7C
    nop

// Keep the fixed switch address while absorbing the new frame-end/provenance
// machinery entirely out of previously unused H-COMP padding.
.byte 0:0x158

hcomp_screen_switch:
    b hcomp_provenance_switch_helper
    nop
    .byte 0:0x20

// Keep the externally visible Mode7 entry at 0x1788.
draw_mode7_entry:
    // H-COMP-resident fault surface for true Mode7 rendering.
    j 0xA4001F78
    li t9, 0x1788
