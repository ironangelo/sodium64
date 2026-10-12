/* The complete reference is opt-in. CPU and RSP must select the same arena. */
ASSERT(__bss_end <= 0x800D6000,
       "Full DSP probe static memory overlaps the CGRAM arena")
