/* Object-list construction moved intact to an owned fixed overlay.
 * This makes room for bounded TMEM reuse in the resident prefix.
 */
#include <rsp.inc>
#include "defines.h"
.data
.byte 0
.text
    // Update OAM for the following sections
    li a0, OAM
    lw a1, OAM_PTR(sp)
    addi t0, a1, 0x220
    sw t0, OAM_PTR(sp)
    jal 0xA4001F40
    li a2, 0x21F

    // Get the index of the last object in rotation
    lhu t1, OAMADD
    andi v1, t1, 0x8000
    beqz v1, init_cache
    lw t0, FB_OFFSET(sp)
    andi v1, t1, 0xFE
    sll v1, v1, 1

init_cache:
    // Initialize values for building the object cache
    li t8, 239 + 16
    sll t0, t0, 1
    sub t8, t8, t0 // Y-bound
    li t7, 0x3000 // Priority

next_priority:
    // Reset indices for the next object priority
    li t6, TILE_TABLE + 0x200 // Cache index
    b start_cache
    move t9, v1 // OAM index

cache_object:
    // Read object data and skip if it doesn't match the current priority
    lw t1, OAM(t9)
    andi t0, t1, 0x3000
    bne t0, t7, cache_next

    // Read the 2 additional object bits
    srl t2, t9, 4
    lbu t2, OAM + 0x200(t2)
    srl t3, t9, 1
    andi t3, t3, 0x6
    srl t2, t2, t3

    // Get the object's size based on the large bit
    lbu t4, OBSEL
    andi t3, t2, 0x2 // Large
    andi t4, t4, 0xE0
    srl t4, t4, 3
    or v0, t3, t4
    lbu s0, OBJ_SIZES + 0(v0) // X-size
    lbu s1, OBJ_SIZES + 1(v0) // Y-size

    // Get the object's Y-coordinate, wrapped past screen bounds
    srl t3, t1, 24
    slt t4, t8, t3
    sll t4, t4, 31
    sra t4, t4, 23
    or s8, t3, t4

    // Skip the object if it doesn't occupy any visible scanlines
    add t4, s8, s1
    sle t5, t4, zero
    bnez t5, cache_next

    // Get the object's X-coordinate, wrapped past pixel 256
    srl t5, t1, 16
    andi t5, t5, 0xFF
    sll t0, t2, 31 // Upper X
    sra t0, t0, 23
    or s2, t5, t0

    // Skip the object if it doesn't occupy any visible pixels
    add t0, s2, s0
    and t0, t0, s2
    sra t0, t0, 8
    bnez t0, cache_next

    // Build and write a 32-bit cache value for the object
    sll t0, s8, 7 // Y-coordinate
    srl t3, t9, 2
    or t0, t0, t3 // OAM index
    sh t0, 0(t6)
    sll t0, s2, 7 // X-coordinate
    or t0, t0, v0 // Size index
    sh t0, 2(t6)
    addi t6, t6, 4

cache_next:
    // Move to the next object until finished
    beq t9, v1, finish_cache
start_cache:
    addi t9, t9, -4
    b cache_object
    andi t9, t9, 0x1FC

finish_cache:
    // Mark the end of the cache list
    addi t0, zero, -1
    sw t0, (t6)

    // DMA the current priority's cache list to RDRAM
    li a0, TILE_TABLE + 0x200
    lw a1, CACHE_PTRS + 16
    srl t0, t7, 3
    add a1, a1, t0
    jal 0xA4001F08
    li a2, 0x1FF

    // Move to the next priority until finished
    bnez t7, next_priority
    addi t7, t7, -0x1000
    lw a1, OVERLAY_MAIN_SRC
    j 0xA4001F7C
    li t9, 0x121C // Original oam_skip resident entry.
#if SODIUM64_DECODE_BANK
.org 0x200
bank_shared_decode: // t4: decode jump
    // Set initial values for decoding a tile
    li t7, 0x40 // Texture offset
    li t1, CHAR_DATA + 0xE // Character offset
    vand $v10, $v10, $v31, 0 // Empty check
    jr t4
    vand $v20, $v20, $v31, 0

bank_shared_decode256:
    // Decode the upper 4 bits of a 256-color tile line
    lpv $v08, 0, 0x20, t1 // Upper/lower byte 3 to lane 0/1, bits 8-15
    lpv $v18, 0, 0x30, t1 // Upper/lower byte 4 to lane 0/1, bits 8-15
    vand $v01, $v24, $v08, 9 // Mask out other lower bits
    vand $v02, $v24, $v08, 8 // Mask out other upper bis
    vmudl $v03, $v26, $v01, 0 // Shift lower bits to bit 0
    vmudl $v04, $v27, $v02, 0 // Shift upper bits to bit 1
    vor $v02, $v03, $v04, 0 // Combine bits to form partial indices
    vand $v11, $v24, $v18, 9 // Mask out other lower bits
    vand $v12, $v24, $v18, 8 // Mask out other upper bits
    vmudl $v13, $v28, $v11, 0 // Shift lower bits to bit 2
    vmudl $v14, $v29, $v12, 0 // Shift upper bits to bit 3
    vor $v12, $v13, $v14, 0 // Combine bits to form partial indices
    vor $v07, $v12, $v02, 0 // Combine partial indices
    vmudn $v20, $v07, $v30, 0 // Shift upper indices left

bank_shared_decode16:
    // Decode the upper 2 bits of a 16-color tile line
    lpv $v13, 0, 0x10, t1 // Upper/lower byte 2 to lane 0/1, bits 8-15
    vand $v11, $v24, $v13, 9 // Mask out other lower bits
    vand $v12, $v24, $v13, 8 // Mask out other upper bits
    vmudl $v13, $v28, $v11, 0 // Shift lower bits to bit 2
    vmudl $v14, $v29, $v12, 0 // Shift upper bits to bit 3
    vor $v12, $v13, $v14, 0 // Combine bits to form partial indices
    vor $v20, $v20, $v12, 0 // Combine partial indices

bank_shared_decode4:
    // Decode the lower 2 bits of a 4-color tile line
    lpv $v03, 0, 0x00, t1 // Upper/lower byte 1 to lane 0/1, bits 8-15
    vand $v01, $v24, $v03, 9 // Mask out other lower bits
    vand $v02, $v24, $v03, 8 // Mask out other upper bis
    vmudl $v03, $v26, $v01, 0 // Shift lower bits to bit 0
    vmudl $v04, $v27, $v02, 0 // Shift upper bits to bit 1
    vor $v02, $v03, $v04, 0 // Combine bits to form partial indices
    vor $v20, $v20, $v02, 0 // Combine partial indices
    vmudn $v01, $v20, $v25, 0 // Shift to upper byte

    // Add palette offset to non-zero indices and move to the next line
    veq $v00, $v01, $v31, 0
    addi t7, t7, -0x8
    vmrg $v00, $v01, $v05, 8
    addi t1, t1, -0x2
    vadd $v02, $v01, $v00, 0

    // Write the line to the texture buffer and loop until complete
    vand $v20, $v20, $v31, 0
    vor $v10, $v10, $v02, 0
    beqz t7, bank_decode_done
    spv $v02, 0, 0, t7
    jr t4
    nop // Caller RA/v1 is restored after reloading Main, not the DMA's RA.
bank_decode_done:
    lw a1, OVERLAY_MAIN_SRC
    j 0xA4001F7C
    li t9, RSP_BANK_DECODE_RETURN
#endif
.org 0x3E8
