/* CPU, C and RSP select D6000 only for the private experimental slot. */
ASSERT(__bss_end <= 0x800D6000,
       "Private scene slot static memory overlaps the CGRAM arena")
