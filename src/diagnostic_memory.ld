/* Linked alongside the toolchain script for diagnostic trace builds. */
ASSERT(__bss_end <= 0x800D2000,
       "diagnostic static memory overlaps the CGRAM arena")
