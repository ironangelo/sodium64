// Experimental four-slot direct-mapped CI8 residency. Each miss loads only
// the admitted 64-byte character; neighboring cache entries are never read.
// v19 is dead in the regular-BG decoder. Its tags live only within one BG
// pass: get_offsets and every fresh decode invalidate v1, resetting all tags.
// Command scratch is retired before reuse, and decoded RDRAM updates retain
// the existing full source fence. The palette and painter order are unchanged.
tmem_atlas_draw:
    li t0, 0xFFFF
    bne v1, t0, tmem_resident_valid
    nop
    vnor $v19, $v31, $v31, 0
tmem_resident_valid:
    move v1, s8
    andi t2, s8, 3
    sll t2, t2, 1
    sqv $v19, 0, 0, zero
    lhu t3, 0(t2)
tmem_resident_tag_store:
    sh s8, 0(t2)
    lqv $v19, 0, 0, zero

    li t0, RDP_TILE + 24
    ldv $v18, 0, 0, t0
    ldv $v18, 8, 8, t0
    sdv $v18, 0, 0x28, zero
    sdv $v18, 8, 0x30, zero
    sll t0, t2, 7 // slot * 8 texels in Q5; original T mask5 covers all four.
    lhu t1, TEXTURE + 50
    add t0, t0, t1
tmem_resident_coord_store:
    sh t0, TEXTURE + 50
    beq s8, t3, tmem_resident_send
    li a0, TEXTURE + 40

    lui t0, 0x2800 // TileSync protects the load descriptor before mutation.
    sw t0, TEXTURE
    sw zero, TEXTURE + 4
    sll t0, t2, 2 // slot * 8 TMEM words (64 bytes).
    lui t1, 0x3550
    or t0, t0, t1
    sw t0, TEXTURE + 8
    lw t0, RDP_INIT + 28 // Original tile1 lower descriptor, unchanged.
    sw t0, TEXTURE + 12
    li t0, 0x3D500003
    sw t0, TEXTURE + 16
    sw a1, TEXTURE + 20
    lui t0, 0x2600
    sw t0, TEXTURE + 24
    sw zero, TEXTURE + 28
    lui t0, 0x3300
    sw t0, TEXTURE + 32
    li t0, 0x0101F800 // Original 64-byte LoadBlock/DXT swizzle.
    sw t0, TEXTURE + 36
    li a0, TEXTURE
tmem_resident_send:
    jal rdp_send
    li a1, TEXTURE + 56
    j finish_tile
    nop

// Restore tile1's TMEM origin before OBJ/Mode7/compositor loads. Tile2 was
// never mutated: its original mask5, origin, S and both gradients survive.
tmem_atlas_restore:
    move v1, ra
    li a0, RDP_WINDOW
    jal rdp_send
    li a1, RDP_WINDOW + 8
    li a0, RDP_INIT + 24
    jal rdp_send
    li a1, RDP_INIT + 32
    li a0, RDP_FILL + 8
    jal rdp_send
    li a1, RDP_FILL + 16
    jr v1
    nop
