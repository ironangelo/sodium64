OUTPUT_FORMAT("elf32-bigmips")
OUTPUT_ARCH(mips)
ENTRY(_start)
SECTIONS
{
    .text 0xA4001AD0 : { KEEP(*(.text)) *(.text.*) }
    _start = ADDR(.text);
    ret_jump = 0xA4001F70;
    .data 0xA4000000 : { KEEP(*(.data)) *(.data.*) }
    /DISCARD/ : { *(.reginfo) *(.MIPS.abiflags) *(.pdr) *(.comment) }
}
ASSERT(SIZEOF(.text) == 184, "Original decoder island must match AD0..B88")
