/* Original GPL-3.0-or-later sodium64 bitplane decoder, unchanged. */
#include <rsp.inc>
#include "defines.h"
.data
.byte 0
.text
.extern ret_jump
    sw t4, RDP_TILE + 36
original_shared_decode: // t4: decode jump
    // Set initial values for decoding a tile
    li t7, 0x40 // Texture offset
    li t1, CHAR_DATA + 0xE // Character offset
    vand $v10, $v10, $v31, 0 // Empty check
    jr t4
    vand $v20, $v20, $v31, 0

original_shared_decode256:
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

original_shared_decode16:
    // Decode the upper 2 bits of a 16-color tile line
    lpv $v13, 0, 0x10, t1 // Upper/lower byte 2 to lane 0/1, bits 8-15
    vand $v11, $v24, $v13, 9 // Mask out other lower bits
    vand $v12, $v24, $v13, 8 // Mask out other upper bits
    vmudl $v13, $v28, $v11, 0 // Shift lower bits to bit 2
    vmudl $v14, $v29, $v12, 0 // Shift upper bits to bit 3
    vor $v12, $v13, $v14, 0 // Combine bits to form partial indices
    vor $v20, $v20, $v12, 0 // Combine partial indices

original_shared_decode4:
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
    beqz t7, ret_jump
    spv $v02, 0, 0, t7
    jr t4
    move v1, ra
