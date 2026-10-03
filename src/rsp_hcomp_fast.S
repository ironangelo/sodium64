/* Exact backdrop-only specialization. No game identity or content involved.
 * CGADSUB=20 (or30 with no potentially visible math-capable Main OBJ),
 * CGWSEL=02/12/22 (bit0 ignored only in Mode0), Main backdrop=black:
 * opaque Main -> Main; backdrop -> Sub/fixed inside the allowed COLOR set,
 * otherwise black. Draw fixed+Sub, black out the prevented set, then Main.
 * This policy needs no compact Z/presence/math buffers or eight-row splits.
 */
#include <rsp.inc>
#include "defines.h"
.data
.byte 0
.text
draw_bg:
    j 0xA4001F90
    move v0, t0
hcomp_fast_entry:
    b hcomp_fast_admit
    nop

hcomp_fast_admit:
    sw zero, HCOMP_BAND_RAW
    lb t0, STAT_FLAGS
    bltz t0, hcomp_fast_raw
    lbu t0, CGADSUB
    andi t1, t0, 0x3F
    bnez t1, hcomp_fast_probe
    lbu t1, CGWSEL
    andi t1, t1, 0xC0
    beqz t1, hcomp_fast_raw
    nop
    b hcomp_fast_return
    nop
hcomp_fast_probe:
    // Exact identity operations need neither a Sub pass nor pixel arithmetic.
    // Keep clipping and the diagnostic composed/raw split on the general path.
    lw t2, HCOMP_DIAG_COMPOSE_LIMIT
    bnez t2, hcomp_fast_return
    andi t2, t1, 0xC0
    bnez t2, hcomp_fast_return
    andi t2, t1, 0x30
    xori t2, t2, 0x30
    beqz t2, hcomp_fast_raw // COLOR prevents math everywhere
    lhu t2, SUB_COLOR
    andi t2, t2, 0xFFFE // Ignore the RGBA5551 alpha bit
    bnez t2, hcomp_fast_backdrop_probe
    andi t2, t1, 2
    beqz t2, hcomp_fast_fixed_zero
    lbu t2, TS
    andi t2, t2, 0x1F
    beqz t2, hcomp_fast_raw // Absent Sub uses fixed zero; HALF is suppressed
    nop
    b hcomp_fast_backdrop_probe
    nop
hcomp_fast_fixed_zero:
    andi t2, t0, 0x40
    beqz t2, hcomp_fast_raw // Main +/- fixed zero, with HALF off
    nop
hcomp_fast_backdrop_probe:
    // Other eligible winners, half/subtract and color stay fully general.
    andi t2, t0, 0xEF
    xori t2, t2, 0x20
    bnez t2, hcomp_fast_return
    nop
    lhu t0, MAIN_COLOR
    bnez t0, hcomp_fast_return
    lbu t0, CGWSEL
    // Always/inside/outside selected, with Sub operand and no Main clip.
    // NEVER was admitted above as an identity operation.
    andi t2, t0, 1
    beqz t2, hcomp_fast_color_selector
    lbu t2, BG_MODE
    // Mode0 contains only2bpp BGs; its direct-color control is inert.
    // Keep every other mode with that bit on the existing general path.
    andi t2, t2, 7
    bnez t2, hcomp_fast_return
    nop
hcomp_fast_color_selector:
    andi t0, t0, 0xCE
    xori t0, t0, 2
    bnez t0, hcomp_fast_return
    nop
    lbu t0, CGADSUB
    andi t0, t0, 0x10
    beqz t0, hcomp_fast_direct
    lbu t0, TM
    andi t0, t0, 0x10
    beqz t0, hcomp_fast_direct
    nop
    // The Main bank just rebuilt its OBJ cache only on this dirty flag.
    // Without it, cached Y/size may belong to older OBSEL/FB settings.
    lbu t0, STAT_FLAGS
    andi t0, t0, 0x40
    beqz t0, hcomp_fast_return
    nop
    // OBJ palettes0..3 never participate in color math. Scan the current
    // coherent OAM epoch, conservatively rejecting every high-palette OBJ
    // except one wholly above the frame under the renderer's own Y-wrap
    // and small/large size rules. X/windows/section visibility are deliberately
    // not used to broaden admission. This never changes OAM or its cache.
    lbu t6, OBSEL
    andi t6, t6, 0xE0
    srl t6, t6, 3
    lw t5, FB_OFFSET(sp)
    sll t5, t5, 1
    li t4, 255
    sub t5, t4, t5
    move t3, zero
hcomp_fast_obj_probe:
    lhu t0, OAM + 2(t3)
    andi t0, t0, 0x0800
    beqz t0, hcomp_fast_obj_next
    lbu t0, OAM(t3)
    slt t1, t5, t0
    sll t1, t1, 8
    sub t0, t0, t1
    srl t1, t3, 4
    lbu t1, OAM + 0x200(t1)
    srl t2, t3, 1
    andi t2, t2, 6
    srlv t1, t1, t2
    andi t1, t1, 2
    or t1, t1, t6
    lbu t1, OBJ_SIZES + 1(t1)
    add t0, t0, t1
    slt t0, zero, t0
    bnez t0, hcomp_fast_return
    nop
hcomp_fast_obj_next:
    addi t3, t3, 4
    sltiu t0, t3, 0x200
    bnez t0, hcomp_fast_obj_probe
    nop
hcomp_fast_direct:
    li t0, 2
    b hcomp_fast_return
    sw t0, HCOMP_BAND_RAW
hcomp_fast_raw:
    li t0, 1
    sw t0, HCOMP_BAND_RAW
hcomp_fast_return:
    lw a1, OVERLAY_HCOMP_SRC
    j 0xA4001F7C
    li t9, 0x1768

hcomp_fast_mask:
    lbu t0, CGWSEL
    andi t0, t0, 0x30
    beqz t0, hcomp_fast_main
    nop
    // BG/OBJ overwrite the span scratch. Recompute the prevented COLOR set
    // from this epoch, including inversion, XOR/XNOR and reversed endpoints.
    lbu a0, WOBJSEL
    srl a0, a0, 4
    lbu a1, WOBJLOG
    srl a1, a1, 2
    andi a1, a1, 3
    // Inside-math -> black complement; outside-math -> black selected set.
    srl a2, t0, 5
    jal 0xA4001CE4
    andi a2, a2, 1
    beqz t7, hcomp_fast_main
    move a3, t7
    // Retire prior primitives before changing the combiner/primitive color.
    li a0, HCOMP_PROOF_RDP_CMDS
    jal 0xA4001F5C
    addi a1, a0, 8
    li t0, 0xFF
    sw t0, RDP_FILL + 20
    li a0, RDP_FILL + 8
    jal 0xA4001F5C
    li a1, RDP_FILL + 32
    lw t5, FILLREC_MASK
    lw t6, RDP_FILL + 36
    and t6, t6, t5
    lw t8, RDP_FILL + 32
    and t8, t8, t5
    li t9, WIN_BOUNDS
hcomp_fast_black_span:
    lbu t0, 0(t9)
    addi t0, t0, 12
    sll t0, t0, 14
    or t0, t0, t6
    sw t0, RDP_FILL + 36
    lbu t0, 1(t9)
    // The helper is inclusive; one-cycle fill rectangles are half-open.
    addi t0, t0, 13
    sll t0, t0, 14
    or t0, t0, t8
    sw t0, RDP_FILL + 32
    li a0, RDP_FILL + 32
    jal 0xA4001F5C
    li a1, RDP_FILL + 40
    addi t9, t9, 2
    addi a3, a3, -1
    bnez a3, hcomp_fast_black_span
    nop
hcomp_fast_main:
    // Restore texture combiner and whole-band scissor even if Sub ended in
    // a narrowed BG/OBJ window. Main is drawn transparently, without a fill.
    li a0, RDP_WINDOW - 16
    jal 0xA4001F5C
    li a1, RDP_WINDOW
    li a0, RDP_FILL + 8
    jal 0xA4001F5C
    addi a1, a0, 8
    li t0, 1
    sb t0, HCOMP_SCREEN
    sw zero, PRIO_CHECKS
    sw zero, PRIO_CHECKS + 4
    lbu s3, BG_MODE
    andi s3, s3, 0xF
    sll s3, s3, 4
    lw a1, OVERLAY_MAIN_SRC
    j 0xA4001F7C
    li t9, 0x1370

.org (0x760 - 0x3A8)
hcomp_fast_screen_switch:
    b hcomp_fast_mask
    nop
.org (0x788 - 0x3A8)
draw_mode7_entry:
    j 0xA4001F78
    li t9, 0x1788
