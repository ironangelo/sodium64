/* Optional Count accumulators in the existing zeroed, guarded 8 MiB USB lease.
 * The preceding transport words end at 0x80441c97. The high guard starts
 * at 0x80441fe0. Only the PPU producer writes these words after boot.
 */
#define REMOTE_RSP_WAIT_COUNT 0x80441c98
#define REMOTE_FRAME_WAIT_COUNT 0x80441c9c
