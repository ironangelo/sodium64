/* The faithful compositor owns Q1 CGRAM at physical D2000, with independent
 * surfaces and Q2 events below 4 MiB. Reject every normal/USB/profiler link that
 * reaches that first owner. CPU clear and embedded RSP bindings require emitted
 * address checks against src/renderer/defines.h before promotion.
 */
ASSERT(__bss_end <= (0x80000000 + renderer_cgram_owner_begin), "Runtime overlaps faithful compositor CGRAM owner")
