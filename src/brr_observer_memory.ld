/* Additional static trace storage; CPU/RSP share the same conditional arena. */
ASSERT(__bss_end <= 0x800D4000,
       "Extended observer static memory overlaps the CGRAM arena")
