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

    // Read the corresponding per-pixel Main winner tag from the bounded
    // E1c-style 280x8 Z16 scratch. Section0 global y=16..23 is retargeted to
    // physical scratch row0..7, so the matching active sample is row0,x12.
    li a0, SCRN_DATA + 16
    lui a1, 0xA00E
    ori a1, a1, 0x2018
    jal 0xA4001F40
    li a2, 0x7

    // Canonicalize the rendered Main RGBA5551 sample to SNES RGB555.
    lhu t0, SCRN_DATA + 8
    lhu t1, SCRN_DATA
    // Section0 TS saved its compact-Z winner tag at the TS->TM boundary,
    // before TM reused the same arena for Main provenance. Backdrop/absence
    // is the validated stored tag 0x0400; any real regular-BG winner differs.
    lhu t9, CHAR_DATA + 32
    li t4, 0x0400
    xor t4, t9, t4
    sltu t4, zero, t4
    sh t4, CHAR_DATA + 34
    move t9, t4
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

    // CGWSEL source-selection proof. Legacy section SUB_COLOR carries COLDATA
    // after brightness conversion. This controlled rung fixes full brightness
    // and constant COLDATA, so the same lossless N64->SNES adapter yields the
    // exact fixed RGB555 operand without introducing a new transport path.
    lhu t5, SUB_COLOR
    srl t2, t5, 11
    andi t3, t5, 0x07C0
    srl t3, t3, 1
    or t2, t2, t3
    andi t3, t5, 0x003E
    sll t3, t3, 9
    or t5, t2, t3

    // SNES CGWSEL bit1: 0=fixed color, 1=subscreen. When Sub is selected,
    // the saved TS winner tag distinguishes a real Sub pixel from backdrop.
    // Backdrop/absence falls back to fixed color. t9 becomes source code:
    // 0=direct fixed, 1=live Sub, 2=transparent-Sub fixed fallback.
    lbu t2, CGWSEL
    andi t3, t2, 0x2
    beqz t3, hcomp_source_fixed
    nop
    bnez t9, hcomp_source_sub
    nop
    move t7, t5
    li t9, 2
    b hcomp_source_ready
    nop
hcomp_source_sub:
    move t7, t1
    li t9, 1
    b hcomp_source_ready
    nop
hcomp_source_fixed:
    move t7, t5
    move t9, zero
hcomp_source_ready:
    sh t5, CHAR_DATA + 24
    sh t7, CHAR_DATA + 26
    sh t2, CHAR_DATA + 28

    // Convert validated primitive-Z winner tags directly to the corresponding
    // CGADSUB mask: BG1 0x0C00 >> 11 = 1, BG2 0x1400 >> 11 = 2.
    // This is the first clean rung where eligibility follows rendered winner
    // provenance rather than a guest-hardcoded BG identity.
    lhu t6, SCRN_DATA + 16
    srl t4, t6, 11
    andi t4, t4, 0x3
    // Preserve the semantic winner mask before E1f reuses t4 for its 0x0421
    // carry-correction term. This fixes evidence only; gate semantics below
    // still consume the live t4 value directly.
    sh t4, CHAR_DATA + 18
    lbu t8, CGADSUB
    and t2, t8, t4
    sltu t2, zero, t2
    move t3, t0
    beqz t2, hcomp_gate_store
    nop

    // Real CGADSUB operation selection on the already-selected live operand.
    // bit7: 0=add, 1=subtract. bit6: 0=full, 1=half.
    andi t4, t8, 0x80
    bnez t4, hcomp_math_sub
    nop
    andi t4, t8, 0x40
    beqz t4, hcomp_math_add_full
    nop
    li t5, 2
    beq t9, t5, hcomp_math_add_full
    nop
    // HALF remains effective for direct fixed selection and real Sub pixels.
    // Mark bit8 in the source/half evidence word only when it is actually used.
    ori t9, t9, 0x0100
    b hcomp_math_add_half
    nop

hcomp_math_add_full:
    // Packed per-channel saturating add, matching the established bsnes
    // RGB555 expression while avoiding cross-channel carry leakage.
    add t3, t0, t7
    xor t4, t0, t7
    andi t4, t4, 0x0421
    sub t4, t3, t4
    andi t4, t4, 0x8420
    sub t3, t3, t4
    srl t5, t4, 5
    sub t4, t4, t5
    or t3, t3, t4
    b hcomp_math_done
    nop

hcomp_math_add_half:
    // Authoritative E1f packed half-add.
    xor t3, t0, t7
    andi t4, t3, 0x0421
    add t3, t0, t7
    sub t3, t3, t4
    srl t3, t3, 1
    b hcomp_math_done
    nop

hcomp_math_sub:
    // Packed per-channel saturating subtract. If bit6 is also set, halve
    // the already-clamped difference; transparent-Sub HALF suppression is a
    // separate later semantic rung and is deliberately not folded in here.
    sub t3, t0, t7
    ori t4, zero, 0x8420
    add t3, t3, t4
    xor t4, t0, t7
    andi t4, t4, 0x8420
    sub t4, t3, t4
    andi t4, t4, 0x8420
    sub t3, t3, t4
    srl t5, t4, 5
    sub t4, t4, t5
    and t3, t3, t4
    andi t5, t8, 0x40
    beqz t5, hcomp_math_done
    nop
    li t4, 2
    beq t9, t4, hcomp_math_done
    nop
    ori t9, t9, 0x0100
    andi t3, t3, 0x7BDE
    srl t3, t3, 1

hcomp_math_done:

hcomp_gate_store:
    // Self-describing proof record. Keep the validated first 16 B stable
    // (Main/Sub/result/gate/tag/mask/CGADSUB/guard), then append fixed RGB555,
    // selected addend, raw CGWSEL and normalized source flag.
    sh t0, CHAR_DATA + 8
    sh t1, CHAR_DATA + 10
    sh t3, CHAR_DATA + 12
    sh t2, CHAR_DATA + 14
    sh t6, CHAR_DATA + 16
    lbu t5, CGADSUB
    sh t5, CHAR_DATA + 20
    sh zero, CHAR_DATA + 22
    // bits1:0 source code (0=fixed,1=Sub,2=fallback); bit8=HALF effective.
    // CHAR_DATA+32/+34 already hold raw TS tag / normalized presence.
    sh t9, CHAR_DATA + 30
    li a0, CHAR_DATA + 8
    li a1, 0xA00F0008
    jal 0xA4001F08
    li a2, 0x1B

    // The rejected cross-frame TS-Z preparation used to live here. Section0
    // now binds the bounded carrier in draw_frame immediately before its own
    // backdrop/TS work, so completed-frame H-COMP leaves no next-frame RDP
    // state dependency.

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
    // Section0 TS used the same bounded Z arena before TM. Save one first-hand
    // winner tag now, while it still means Sub presence; later sections must
    // not overwrite this evidence after Z updates have been disabled.
    bnez k0, hcomp_sub_presence_saved
    nop
    li a0, CHAR_DATA + 32
    lui a1, 0xA00E
    ori a1, a1, 0x2018
    jal 0xA4001F40
    li a2, 0x7
hcomp_sub_presence_saved:

    // Keep the already-validated semantic Color Image retarget. The immutable
    // per-BG depth table is shared by TS and TM, so no RDP_FRAME patching is
    // needed; TM simply overwrites the active Z tags with Main winner identity.
    lw t0, FRAMEBUFFER(sp)
    addi t0, t0, 280 * -16
    sw t0, RDP_FRAME + 4
    li a0, RDP_FRAME
    jal 0xA4001F5C
    li a1, RDP_FRAME + 8

    // Load regular BG/OBJ rendering back over this slot and resume at the
    // paired resident next_layer return for this exact renderer layout.
    lw a1, OVERLAY_MAIN_SRC
    li t9, 0x1370
    j 0xA4001F7C
    nop

// TM has just completed when the resident screen mask shifts to zero.
// Disable proof-only Z_UPDATE *before* resident next_section can submit its
// backdrop/fill commands. RDP_INIT[0] is the immutable baseline OtherModes
// command (0x2F0088FF00040001), so no borrowed RDP_FRAME state is involved.
hcomp_provenance_end:
    li a0, RDP_INIT
    jal 0xA4001F5C
    li a1, RDP_INIT + 8
    j 0xA40010C0
    nop

// Keep the fixed switch address while absorbing the new lifetime cut entirely
// out of previously unused H-COMP padding.
.byte 0:0x80

hcomp_screen_switch:
    beqz s7, hcomp_provenance_end
    nop
    b hcomp_provenance_switch_helper
    nop
    .byte 0:0x18

// Keep the externally visible Mode7 entry at 0x1788.
draw_mode7_entry:
    // H-COMP-resident fault surface for true Mode7 rendering.
    j 0xA4001F78
    li t9, 0x1788
