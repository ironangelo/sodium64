/* Slot images store only bytes DMA'd into 13A8..1790. Public RSP VMAs
 * remain fixed; retired leading padding is not carried in CPU RDRAM.
 */
OUTPUT_FORMAT("elf32-bigmips")
OUTPUT_ARCH(mips)
ENTRY(_start)
SECTIONS
{
    .text 0xA40013A8 : { KEEP(*(.text)) *(.text.*) }
    _start = ADDR(.text);
    .data 0xA4000000 : { KEEP(*(.data)) *(.data.*) }
    /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) }
}
ASSERT(SIZEOF(.text) == 0x3E8, "HCOMP image must fill the fixed 13A8..1790 slot")
