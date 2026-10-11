// Cache admission and texture-source retirement precede this helper.
// The original render tile has TMEM0, line8, mirror/no-clamp and T mask5.
// Four textures fit in the original mask5 address space. Eight textures use
// mask6, restored to mask5 before the next layer. Only initial T changes;
// both gradients and the original S survive.
// HCOMP_EFFECTIVE_TS is constant for this complete band. Visible Sub keeps
// the original single-texture protocol and cannot suffer group overfetch.
tmem_atlas_draw:
    lbu t0, HCOMP_EFFECTIVE_TS
    bnez t0, tmem_coord_legacy
    nop
    li t0, RDP_TILE + 24
    ldv $v18, 0, 0, t0
    ldv $v18, 8, 8, t0
#if SODIUM64_TMEM_ATLAS_BITS == 3
    sdv $v18, 0, 0x28, zero
    sdv $v18, 8, 0x30, zero
#define TMEM_RECT_OFFSET 40
#define TMEM_LOAD_OFFSET 16
#else
    sqv $v18, 0, 0x20, zero
#define TMEM_RECT_OFFSET 32
#define TMEM_LOAD_OFFSET 8
#endif
    andi t2, s8, (1 << SODIUM64_TMEM_ATLAS_BITS) - 1
    sll t0, t2, 8 // (slot * 8) in signed Q5 texture coordinates.
    lhu t3, TEXTURE + TMEM_RECT_OFFSET + 10
    add t0, t0, t3
tmem_coord_store:
    sh t0, TEXTURE + TMEM_RECT_OFFSET + 10
.globl tmem_atlas_group_shift
tmem_atlas_group_shift:
    srl t1, s8, SODIUM64_TMEM_ATLAS_BITS
    srl t3, v1, SODIUM64_TMEM_ATLAS_BITS
    move v1, s8
    beq t1, t3, tmem_coord_send
    li a0, TEXTURE + TMEM_RECT_OFFSET
    sll t2, t2, 6
    sub t2, a1, t2
    sw t2, TEXTURE + TMEM_LOAD_OFFSET + 4
    li t0, 0x3D500003
    sw t0, TEXTURE + TMEM_LOAD_OFFSET
    lui t0, 0x2600
    sw t0, TEXTURE + TMEM_LOAD_OFFSET + 8
    sw zero, TEXTURE + TMEM_LOAD_OFFSET + 12
    lui t0, 0x3300
    sw t0, TEXTURE + TMEM_LOAD_OFFSET + 16
    li t0, 0x01000800 | (((32 << SODIUM64_TMEM_ATLAS_BITS) - 1) << 12)
    sw t0, TEXTURE + TMEM_LOAD_OFFSET + 20
#if SODIUM64_TMEM_ATLAS_BITS == 3
    li t0, 0x35480200
    sw t0, TEXTURE + 8
    li t0, 0x02058150 // Mirror T, mask6, unchanged line/origin/S.
tmem_coord_tile_mask:
    sw t0, TEXTURE + 12
#endif
    lui t0, 0x2800
    sw t0, TEXTURE
    sw zero, TEXTURE + 4
    li a0, TEXTURE
tmem_coord_send:
    jal rdp_send
    li a1, TEXTURE + TMEM_RECT_OFFSET + 16
    j finish_tile
    nop

tmem_coord_legacy:
    // Palette/version validation already happened. A fresh decode always
    // invalidates v1, so this validated character-only reuse stays exact.
    beq s8, v1, skip_upload
    move v1, s8
    sw a1, RDP_TILE + 4
    b skip_upload + 4
    li a0, RDP_TILE

#if SODIUM64_TMEM_ATLAS_BITS == 3
// Immutable command sources stay valid while the RDP reads them. Restore
// Tile2 before OBJ/general paths; no texture cache or palette owner changes.
tmem_atlas_restore:
    move v1, ra
    li a0, RDP_WINDOW
    jal rdp_send
    li a1, RDP_WINDOW + 8
    li a0, RDP_INIT + 32
    jal rdp_send
    li a1, RDP_INIT + 40
    li a0, RDP_FILL + 8
    jal rdp_send
    li a1, RDP_FILL + 16
    jr v1
    nop
#endif
