# Scene state ownership gate

Owner gate after native S1 park and full architectural RSP title/Mode7 roundtrip. A complete
serializer/restore is not implemented. The linked baseline is S2 runtime
1b85b64b05ee47a4d5819749dfd3f953c01d55f5, existing renderer banks unchanged.
Read each range from its production owner; state input must never supply
arbitrary destination addresses. Keep private state payloads and ROM identities
outside Git. Do not replace deterministic replay before continuation gates.

| Owner | State required | Binding or exclusion rule |
| --- | --- | --- |
| S-CPU | Accumulator/X/Y/stack/data bank; saved MIPS guest PC/status/direct page and CPU/APU/DSP cycle budgets | Keep canonical continuation and GPR64/HI/LO/EPC/Status. Classify host opcode and return pointers; raw context requires exact code/layout. |
| WRAM/SRAM |128KiB WRAM, guest SRAM, WRAM I/O address latch and dirty/disable state | Save guest SRAM only. Diagnostic recorder SRAM and ordinary cart writeback are separate owners. |
| Mapper/pager | Memory map, ROM-cache cursor and tags/entries | Cartridge ROM is immutable and must match. Rebuild TLB or preserve all entries/CP0 ownership explicitly; host PFNs cannot cross layouts unchanged. |
| CPU I/O/DMA | Multiply/divide operands/results; DMA channel addresses/modes/counts; HDMA masks/progress | Preserve pending effects and event order. Immutable I/O handler tables stay bound to the current build. |
| DSP-1 | Command handler/count/status/toggle, input/output buffers, matrices and projection history | Bind handler IDs to current code. A state must reject an enhancement chip whose implemented owners have not been covered. |
| SPC700 |64KiB RAM, registers/PC/flags/stack, control/halt, ports, timers and relative deadlines | IPL bytes and I/O handlers are immutable. APU cycle budget also lives in the saved guest context. |
| APU JIT | Tags/lookup/live groups, cursor, compiled blocks and temporary state | Same-build raw retention requires matching code and cache coherence. Cross-build restore must invalidate/recompile or prove every code/pointer binding. |
| Implemented DSP | Register file, noise/timer, voice mode/envelope/counters/next deadlines/BRR addresses/history, sample ring/head and enabled mask | Handler pointers and pitch/volume caches need current bindings. Host audio observer Count values restart. Matching implemented state does not mean complete S-DSP fidelity. |
| PPU |64KiB VRAM, CGRAM/OAM, VRAM dirty/publication state, PPU registers/latches/counters, section/queue/event cursors and parity | Queue pointers have owner-relative meanings. Preserve any live historical section/palette/OAM data rather than reconstructing it from final registers alone. |
| Renderer | RDRAM VRAM shadow, texture/tile/object caches and validity tables, palettes/events/row queues, framebuffers and composition surfaces, SP DMEM/IMEM | Full GPR/vector/flags/ACC poison/restore/recapture700 bytes passes native title/Mode7; preserve that context and the qualified pipeline. New RSP source descriptors must bind to the current build. |
| Input | Guest controller latches/shifts, remote button mask and remaining guest-frame duration | Physical PIF/SI reply buffer is a host owner. Restore guest input atomically without replaying an old physical DMA transaction. |
| Host control | Presentation queue/origin, paused continuation, transport, recorder, Count/Compare, AI/DP/SI/PI state | Drain/fence before commit. Keep transport and C stack live; restart measurement clocks/recorder. Do not copy arbitrary hardware registers or stale deadlines from a prior session. |

The actual ELF separates these owners from font/menu strings, CPU/APU opcode
tables, embedded RSP banks, diagnostic snapshots and live remote stacks.
Whole RDRAM or whole linked `.data` copying would mix them. Hardware interrupts
continue while parked; export coherence must be proved for any host-mutated
owner, with bounded waits and without omitting emulated work.

The next functional gate should use one private same-build slot, with explicit
owner spans and full prevalidation before restore. This avoids designing a
general importer before the first machine restore works. Preserve/rebind the
canonical CPU continuation and RSP pipeline; validate ROM/configuration/layout,
owner sizes and complete checksum, then restore/read back transactionally.
Bind layer/precision/frameskip/audio/APU-clock settings and implementation
flags; incompatible current settings must fail before changing the machine.
Reject incompatibility without partial mutation; lock gameplay to menu recovery
after an incomplete commit. Test deliberately changed guest progress, restore,
then compare next1/60/600 frames, implemented memory/event state and PCM.

Only afterward qualify persistent file transfer and cross-build reuse. A
same-build slot can shorten repeated tests within one candidate, but cannot
replace A/B replay between changed builds. Comparable native measurements still
require identical warmup and fresh observer/recorder baselines. No cadence,
full audio, corpus or integration acceptance follows from this design.

## Linked static owner boundaries

SCENE_STATE1 exports zero-byte begin/end symbols for21 ranges covering559691
bytes: CPU, SPC/JIT, implemented DSP, DMA/input, WRAM/guest SRAM, mapper/I/O,
PPU producer state/cursors/epochs, DSP1 and presentation state. Ends use section
equates so GNU assembler's next alignment cannot move an end marker. No runtime
code or data changes: whole CPU text/data and allocated extents are byte-exact
the measured full-context artifact. The map verifier rejects overlaps, wrong
known sizes and inclusion of stacks, transport, observers or immutable tables.
[Linked owner map](evidence/scene-state-linked-owners.json).

These are static source owners, not complete state coverage. Add O64 guest
continuation/CP0/TLB, dynamic renderer/JIT/ROM-cache arenas, full SP memory/
register context and remote guest-input controls. Presentation/host clocks
need canonical commit rules. Prototype guest SRAM selection is only first8KiB;
reject larger SRAM requirements until its ownership is covered. Validate all
bindings/bounds/checksums before any load, read back the full commit, and
compare restored1/60/600 image/PCM/event state after deliberate guest progress.
