// Called only after RDRAM cache palette/version admission, or after a decode
// forcibly invalidates v1. Indices in neighboring entries are never used
// without their own cache admission; a later decode reloads the whole group.
// TEXTURE's 64-byte DMA has retired before it becomes command scratch.
#define ATLAS_MASK ((1 << SODIUM64_TMEM_ATLAS_BITS) - 1)
tmem_atlas_draw:
    li t0, RDP_TILE + 24
    ldv $v18, 0, 0, t0
    ldv $v18, 8, 8, t0
    sqv $v18, 0, 0x30, zero
    // Same validated character uses the existing render tile directly.
    // A decode invalidates v1, so palette/version changes cannot take this.
    beq s8, v1, tmem_atlas_send
    li a0, TEXTURE + 48
.globl tmem_atlas_group_shift
tmem_atlas_group_shift:
    srl t1, s8, SODIUM64_TMEM_ATLAS_BITS
    srl t3, v1, SODIUM64_TMEM_ATLAS_BITS
    andi t2, s8, ATLAS_MASK
    sll t2, t2, 3 // Render tile's TMEM offset, in 64-bit words.
    li t0, 0x35480200
    or t0, t0, t2
    sw t0, TEXTURE + 40
    li t0, 0x02054150
    sw t0, TEXTURE + 44
    lui t0, 0x2800
    sw t0, TEXTURE + 32
    sw zero, TEXTURE + 36
    move v1, s8 // Character plus its group identifies the current snapshot.
    beq t1, t3, tmem_atlas_send
    li a0, TEXTURE + 32
    sll t2, t2, 3
    sub t2, a1, t2 // Start of this cached RDRAM group.
    sw t2, TEXTURE + 12
    li t0, 0x3D500003
    sw t0, TEXTURE + 8
    lui t0, 0x2600
    sw t0, TEXTURE + 16
    sw zero, TEXTURE + 20
    lui t0, 0x3300
    sw t0, TEXTURE + 24
    li t0, (0x01000800 | (((32 << SODIUM64_TMEM_ATLAS_BITS) - 1) << 12))
    sw t0, TEXTURE + 28
    lui t0, 0x2800
    sw t0, TEXTURE
    sw zero, TEXTURE + 4
    li a0, TEXTURE
tmem_atlas_send:
    jal rdp_send
    li a1, TEXTURE + 64
    j finish_tile
    nop

// Restore tile2's original TMEM origin before OBJ/Mode7/general paths.
// Tile1's load format/origin and all palette bytes were never changed.
tmem_atlas_restore:
    move v1, ra
    lui t0, 0x2800
    sw t0, TEXTURE
    sw zero, TEXTURE + 4
    li t0, 0x35480200
    sw t0, TEXTURE + 8
    li t0, 0x02054150
    sw t0, TEXTURE + 12
    li t0, RDP_FILL + 8
    ldv $v18, 0, 0, t0
    sdv $v18, 0, 0x10, zero
    li a0, TEXTURE
    jal rdp_send
    li a1, TEXTURE + 24
    jr v1
    nop
