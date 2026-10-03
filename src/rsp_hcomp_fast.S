/* Exact backdrop-only specialization. No game identity or content involved.
 * CGADSUB=20, CGWSEL=02/12, Main backdrop=black, normal nonblank rendering:
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
    xori t0, t0, 0x20
    bnez t0, hcomp_fast_return
    nop
    lhu t0, MAIN_COLOR
    bnez t0, hcomp_fast_return
    lbu t0, CGWSEL
    // Mode 0 (always) and 1 (inside selected), with Sub operand and no clip.
    andi t0, t0, 0xEF
    xori t0, t0, 2
    bnez t0, hcomp_fast_return
    nop
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
    andi t0, t0, 0x10
    beqz t0, hcomp_fast_main
    nop
    // BG/OBJ overwrite the span scratch. Recompute the COLOR complement
    // from this epoch, including inversion, XOR/XNOR and reversed endpoints.
    lbu a0, WOBJSEL
    srl a0, a0, 4
    lbu a1, WOBJLOG
    srl a1, a1, 2
    andi a1, a1, 3
    jal 0xA4001CE4
    move a2, zero
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
