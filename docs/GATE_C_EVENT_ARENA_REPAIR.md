# Shared CGRAM event-arena repair

The event counter admits `0x6000` records of four bytes. Each full slot needs
`0x18000` bytes. Original Q1 `C2E00..DAE00` overlapped Q2 `D7000..EF000`;
Q2 also crossed the live Main winner, Sub color and preserved TS surfaces.

Q1 and all bounded HCOMP surfaces retain their addresses. Q2 now occupies
`3E8000..400000`, within base 4 MiB RDRAM. The cart ROM is paged in 8 KiB
blocks: the resident ROM cache now uses 244 slots, ending exactly at `3E8000`.
The exception handler explicitly wraps slot 243 to zero and still invalidates
the evicted virtual mapping. Cart ROM size, event capacity, APU JIT capacity,
tile caches, framebuffer addresses and every RSP overlay are unchanged.

This reserves 96 KiB from the former resident ROM cache. Workloads using more
than 244 pages may incur additional PI cache misses. This is a resource tradeoff,
not a claim of unchanged game performance or full SMW compatibility. Q2 does
not require zero initialization: the handed stream has explicit section
markers and DMA-pair bounds; unwritten bytes are not valid records.

Validation requires full simultaneous owner extents and linked ELF checks,
negative controls rejecting the old queue/cache layouts, the emitted CPU wrap,
unchanged all RSP text/data against exact parent `780645a`, real paging reads
and reloads across the new cache boundary, and real active-display palette DMA
in both queues. Separate original visual/mixed tests must retain their exact
guest bytes and pass continuous PI saves and fresh frozen A/B full-frame
oracles. The pressure guest changes palette colors deliberately and certifies
transport only; it has no displayed-color or cadence authority.

Keep the historical `780645a` wrappers/saves/decoder available. SMW exploration
and the diagnostic branch share this general fix, while compilation flags keep
gameplay and diagnostic outputs separate. Native green appearance, broader
RDP source lifetime, full-screen HCOMP and SMW iris remain separate open work.
