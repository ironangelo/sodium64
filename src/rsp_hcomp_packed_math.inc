hcomp_channels_start:
    // Drop the framebuffer alpha bit before packed arithmetic. All inputs
    // are <=7FFF, so addition fits unsigned16; subtraction's bit16 is
    // immaterial because the final guard mask removes it. HALF add must
    // average before saturation; HALF subtract halves saturated difference.
    vmudl $v08, $v00, $v16, 8
    vmudl $v09, $v01, $v16, 8
    andi t0, v1, 0x80
    beqz t0, hcomp_packed_add
    nop
    // d = x-y+8420; b = (d-((x^y)&8420))&8420;
    // full = (d-b)&(b-(b>>5)). Each guard selects its channel independently.
    vsubc $v10, $v08, $v09, 0
    vaddc $v10, $v10, $v19, 9
    vxor $v11, $v08, $v09, 0
    vand $v11, $v11, $v19, 9
    vsubc $v11, $v10, $v11, 0
    vand $v11, $v11, $v19, 9
    vsubc $v10, $v10, $v11, 0
    vmudl $v12, $v11, $v16, 10
    vsubc $v11, $v11, $v12, 0
    vand $v10, $v10, $v11, 0
    vand $v11, $v10, $v19, 10
    vmudl $v11, $v11, $v16, 8
    b hcomp_packed_select
    nop
hcomp_packed_add:
    // s=x+y; q=s-((x^y)&0421); c=q&8420;
    // full=(s-c)|(c-(c>>5)); half=q>>1.
    vaddc $v10, $v08, $v09, 0
    vxor $v11, $v08, $v09, 0
    vand $v11, $v11, $v19, 8
    vsubc $v11, $v10, $v11, 0
    vand $v12, $v11, $v19, 9
    vmudl $v11, $v11, $v16, 8
    vsubc $v10, $v10, $v12, 0
    vmudl $v14, $v12, $v16, 10
    vsubc $v12, $v12, $v14, 0
    vor $v10, $v10, $v12, 0
hcomp_packed_select:
    // Wrapping arithmetic leaves VCO carry/borrow bits. Retire them before
    // VEQ; otherwise equal zero HALF masks can inherit unrelated borrow.
    vge $v06, $v31, $v31, 0
    veq $v06, $v13, $v31, 0
    vmrg $v10, $v10, $v11, 0
    vmudn $v14, $v10, $v16, 11
    veq $v06, $v07, $v31, 0
    vmrg $v00, $v00, $v14, 0
