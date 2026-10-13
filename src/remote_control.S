/* SPDX-License-Identifier: GPL-3.0-or-later
 * Private O64 bridge. Sodium uses sp as a renderer queue index. All ordinary
 * GPR64, HI/LO, EPC and caller Status survive; only the recorder owns IM7.
 * The reboot tail is a no-cheats port of menu src/boot/reboot.S.
 */
#include "defines.h"
#ifdef SODIUM64_REMOTE
.globl remote_init_bridge, remote_frame_bridge, remote_saved_status
.globl remote_reboot_start, remote_reboot_end, remote_reboot_jump
#ifdef SODIUM64_SCENE_STATE
.globl remote_scene_bridge, remote_bridge_saved
#endif
.data
.align 3
remote_saved_status: .word 0
remote_bridge_kind: .word 0
.section .bss
.align 5
remote_bridge_saved: .space 272
.align 5
remote_bridge_stack: .space 4096
remote_bridge_stack_end:
.text
.set noreorder
remote_init_bridge:
    mfc0 k1, $12
    la k0, remote_saved_status
    sw k1, (k0)
    la k0, remote_bridge_kind
    sw zero, (k0)
    b remote_bridge_enter
    nop
remote_frame_bridge:
    li k1, 1
    la k0, remote_bridge_kind
    sw k1, (k0)
#ifdef SODIUM64_SCENE_STATE
    b remote_bridge_enter
    nop
remote_scene_bridge:
    li k1, 2
    la k0, remote_bridge_kind
    sw k1, (k0)
#endif
remote_bridge_enter:
    la k0, remote_bridge_saved
    .set push
    .set noat
    sd $1, 0(k0)
    sd $2, 8(k0)
    sd $3, 16(k0)
    sd $4, 24(k0)
    sd $5, 32(k0)
    sd $6, 40(k0)
    sd $7, 48(k0)
    sd $8, 56(k0)
    sd $9, 64(k0)
    sd $10, 72(k0)
    sd $11, 80(k0)
    sd $12, 88(k0)
    sd $13, 96(k0)
    sd $14, 104(k0)
    sd $15, 112(k0)
    sd $16, 120(k0)
    sd $17, 128(k0)
    sd $18, 136(k0)
    sd $19, 144(k0)
    sd $20, 152(k0)
    sd $21, 160(k0)
    sd $22, 168(k0)
    sd $23, 176(k0)
    sd $24, 184(k0)
    sd $25, 192(k0)
    sd $28, 200(k0)
    sd $29, 208(k0)
    sd $30, 216(k0)
    sd $31, 224(k0)
    .set pop
    mfhi t0
    sd t0, 240(k0)
    mflo t0
    sd t0, 248(k0)
    mfc0 t0, $14
    sw t0, 256(k0)
    la sp, remote_bridge_stack_end - 32
    lw t0, remote_bridge_kind
    bnez t0, remote_bridge_frame
    nop
    jal remote_control_init
    nop
    b remote_bridge_restore
    nop
remote_bridge_frame:
#ifdef SODIUM64_SCENE_STATE
    lw t0, remote_bridge_kind
    addiu t0, t0, -2
    bnez t0, remote_bridge_normal_frame
    nop
    jal remote_scene_parked
    nop
    b remote_bridge_pause_check
    nop
remote_bridge_normal_frame:
#endif
    jal remote_control_frame
    nop
remote_bridge_pause_check:
    lw t0, remote_paused
    beqz t0, remote_bridge_arm_check
    nop
    // A caller may be in the PPU's outer TLB exception (EXL). Temporarily
    // allow VI while paused, retaining original EPC for that outer exception.
    lw t0, remote_saved_status
    li t1, -7
    and t0, t0, t1
    ori t0, t0, 1
    mtc0 t0, $12
    nop
    nop
    la t0, remote_bridge_saved
    ld a0, 24(t0)
    jal remote_control_idle
    nop
    mfc0 t0, $12
    li t1, -2
    and t0, t0, t1
    mtc0 t0, $12
    nop
    nop
    b remote_bridge_pause_check
    nop
remote_bridge_arm_check:
    lw t0, remote_arm_pending
    beqz t0, remote_bridge_restore
    nop
    sw zero, remote_arm_pending
    jal native_diag_remote_arm
    nop
remote_bridge_restore:
    la k0, remote_bridge_saved
    ld t0, 240(k0)
    mthi t0
    ld t0, 248(k0)
    mtlo t0
    lw t0, 256(k0)
    mtc0 t0, $14
    nop
    // Preserve recorder's Compare mask changes, all other Status fields
    // return exactly to their caller value.
    mfc0 k1, $12
    andi k1, k1, 0x8000
    lw t0, remote_saved_status
    li t1, -32769
    and t0, t0, t1
    or k1, k1, t0
    .set push
    .set noat
    ld $1, 0(k0)
    ld $2, 8(k0)
    ld $3, 16(k0)
    ld $4, 24(k0)
    ld $5, 32(k0)
    ld $6, 40(k0)
    ld $7, 48(k0)
    ld $8, 56(k0)
    ld $9, 64(k0)
    ld $10, 72(k0)
    ld $11, 80(k0)
    ld $12, 88(k0)
    ld $13, 96(k0)
    ld $14, 104(k0)
    ld $15, 112(k0)
    ld $16, 120(k0)
    ld $17, 128(k0)
    ld $18, 136(k0)
    ld $19, 144(k0)
    ld $20, 152(k0)
    ld $21, 160(k0)
    ld $22, 168(k0)
    ld $23, 176(k0)
    ld $24, 184(k0)
    ld $25, 192(k0)
    ld $28, 200(k0)
    ld $29, 208(k0)
    ld $30, 216(k0)
    ld $31, 224(k0)
    .set pop
    mtc0 k1, $12
    nop
    nop
    jr ra
    nop

remote_reboot_jump:
    move s4, a0
    li s1, 1
    move s3, zero
    move s5, zero
    li s6, 0x3f
    li s7, 1
    beq s4, s7, remote_reboot_tv_ready
    nop
    li s7, 6
    beqz s4, remote_reboot_tv_ready
    nop
    li s7, 4
remote_reboot_tv_ready:
    move a0, zero
    li t3, 0x34000000
    mtc0 t3, $12
    ctc1 zero, $31
    nop
    // GNU as may choose a one-word li for a forward symbol difference and
    // silently drop its high address bits. Keep the hardware base explicit.
    lui t3, 0xa400
    ori t3, t3, 0x1000 + (remote_reboot_entry - remote_reboot_start)
    jr t3
    nop

// Receiver lives entirely in SP IMEM and runs after the cart is remapped.
// Original source: paired-menu src/boot/reboot.S (same logic without cheats).
.set push
.set noat
remote_reboot_start:
    lui $13, 0xbfc0
1:
    lw $8, 0x7fc($13)
    addiu $13, $13, 0x7c0
    andi $8, $8, 0x80
    bnel $8, $0, 1b
    lui $13, 0xbfc0
    lw $8, 0x24($13)
    lui $11, 0xb000
remote_reboot_entry:
    li $29, 0xa4001ff0
    li $8, 0xa0000000
    li $9, 0xa0400000
remote_reboot_clear:
    sw $0, 0($8)
    sw $0, 4($8)
    sw $0, 8($8)
    sw $0, 12($8)
    sw $0, 16($8)
    sw $0, 20($8)
    sw $0, 24($8)
    sw $0, 28($8)
    addiu $8, $8, 32
    bne $8, $9, remote_reboot_clear
    nop
    li $8, 0xa4700000
    sw $0, 0x10($8)
    sw $0, 0x0c($8)
    li $8, 1
    beq $20, $8, remote_reboot_ntsc
    nop
    li $31, 0xa4001554
    b remote_reboot_regs
    nop
remote_reboot_ntsc:
    li $31, 0xa4001550
remote_reboot_regs:
    move $1, $0
    move $2, $0
    move $3, $0
    move $4, $0
    move $5, $0
    move $6, $0
    move $7, $0
    move $8, $0
    move $9, $0
    li $10, 0x40
    move $12, $0
    move $13, $0
    move $14, $0
    move $15, $0
    move $16, $0
    move $17, $0
    move $18, $0
    move $24, $0
    move $25, $0
    move $26, $0
    move $27, $0
    move $28, $0
    move $30, $0
    li $11, 0xa4000040
    jr $11
    nop
remote_reboot_end:
.set pop
#endif

