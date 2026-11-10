// Called after current tile priority, mirror, VRAM and nonempty admission.
// Identical 16-bit map words share every character/palette/flip/priority bit.
// Merge only8x8 maps inside the current inclusive window span and real epoch.
// t1(cache state),t3(VRAM address),t6(map word),all other live owners survive.
bg_span_merge:
    bnez t5, bg_span_return // Large16x16 character subdivisions stay original.
    lui t2, 0x0200
    // Keep row generation/TEXREC_OFS unchanged: tile2 contributes to the
    // lower command opcode. Change only its final upper word to tile4.
    lw t0, RDP_TILE + 28
    add t2, t2, t0
    sw t2, RDP_TILE + 28
    lbu t0, WIN_BOUNDS + 1(t8)
    addi t0, t0, -7
bg_span_probe:
    slt t2, s0, t0
    beqz t2, bg_span_return
    add t2, s0, s6
    addi t2, t2, 8
    andi t2, t2, 0x1FF
    srl t2, t2, 2
    lhu t2, SCRN_DATA(t2)
    bne t2, t6, bg_span_return
    nop
    addi s0, s0, 8
    // v15 already holds the following tile's rectangle. Extend only the
    // original lower-right word, retaining its first upper-left and UV.
    sdv $v15, 0, 0x38, zero
    lw t2, TEXTURE + 56
    sw t2, RDP_TILE + 24
    b bg_span_probe
    vadd $v15, $v15, $v23, 0
bg_span_return:
    jr ra
    nop
