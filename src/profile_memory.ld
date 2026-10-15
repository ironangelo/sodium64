/* Profiling may not push RSP blobs or DSP-1 tables into the CGRAM arena.
 * The profiler's admitted upper lease is initialized explicitly, never loaded.
 */
ASSERT(__bss_end <= 0x800BE200, "Profiler overlaps first fixed CGRAM owner")
