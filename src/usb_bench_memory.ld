/* All ordinary base caches and fixed CGRAM/RSP arenas remain in place. */
ASSERT(__bss_end <= 0x800BE200, "USB bench overlaps first fixed CGRAM owner")
