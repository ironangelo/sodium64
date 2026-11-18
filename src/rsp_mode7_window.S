/* Exact Mode7 BG1 windows. Same fixed renderer slot as the affine draw bank.
 * Decode geometry stays in the draw bank; this bank owns span iteration and
 * scissor restoration. No game identity, guest graphics or timing changes.
 */
#include <rsp.inc>
#include "defines.h"
.data
.byte 0
.text
draw_bg:
    j 0xA4001F90
    move v0, t0

mode7_window_begin:
    beqz t1, mode7_window_finish
    nop
    lbu t0, HCOMP_SCREEN
    addi t0, t0, TSW
    lbu t0, 0(t0)
    andi t0, t0, 1
    beqz t0, mode7_window_full
    nop
    lhu a0, WBGSEL
    andi a0, a0, 15
    lbu a1, WBGLOG
    andi a1, a1, 3
    jal 0xA4001CE4
    li a2, 0
    b mode7_window_ready
    nop
mode7_window_full:
    sh zero, WIN_BOUNDS
    li t0, 255
    sb t0, WIN_BOUNDS + 1
    li t0, 1
    sb t0, WIN_COUNT
mode7_window_ready:
    sb zero, MODE7_WINDOW_INDEX
    lbu t0, WIN_COUNT
    beqz t0, mode7_window_finish
    nop

mode7_window_span:
    // Copy section Y and replace only inclusive X bounds with half-open X.
    lw t0, RDP_FILL + 8
    andi t0, t0, 0xFFF
    lui t1, 0x2D00
    or t0, t0, t1
    lbu t2, MODE7_WINDOW_INDEX
    addi t2, t2, WIN_BOUNDS
    lbu t1, 0(t2)
    addi t1, t1, 12
    sll t1, t1, 14
    or t0, t0, t1
    sw t0, RDP_WINDOW + 8
    lw t0, RDP_FILL + 12
    andi t0, t0, 0xFFF
    lbu t1, 1(t2)
    addi t1, t1, 13
    sll t1, t1, 14
    or t0, t0, t1
    sw t0, RDP_WINDOW + 12
    li a0, RDP_WINDOW
    jal 0xA4001F5C
    li a1, RDP_WINDOW + 16
    // The renderer entry checks enable in t1. All other temporaries may die.
    li t1, 1
    lw a1, OVERLAY_MODE7_DRAW_SRC
    j 0xA4001F7C
    li t9, 0x1788

mode7_window_next:
    lbu t0, MODE7_WINDOW_INDEX
    addi t0, t0, 2
    sb t0, MODE7_WINDOW_INDEX
    lbu t1, WIN_COUNT
    sll t1, t1, 1
    bne t0, t1, mode7_window_span
    nop
mode7_window_finish:
    // Later OBJ layers must inherit the complete section, never BG1's span.
    li a0, RDP_FILL + 8
    jal 0xA4001F5C
    li a1, RDP_FILL + 16
    j 0xA4001370
    nop

.org (0x780 - 0x3A8)
mode7_window_continue:
    b mode7_window_next
    nop
.org (0x788 - 0x3A8)
draw_mode7_entry:
    b mode7_window_begin
    nop
