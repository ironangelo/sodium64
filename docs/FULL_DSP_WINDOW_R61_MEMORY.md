# R61 - explicit expanded-RAM DSP window owners

Status: IMPLEMENTED and locally qualified; physical memory/coexistence result
pending. This is a prerequisite for complete resident DSP dataflow, not a speed
claim or a live SPC integration. Commercial inputs and derived data stay local.

R62's proven IPL3 capture is carried into this branch. Only exact8388608 admits
an upper-memory plan;4MiB/unknown/invalid values clear the plan and return before
pointer/cache access. The ordinary guest/renderer/cache arena stays below4MiB.

| Physical extent | Owner and lifetime |
| --- | --- |
| 0x400000..0x4340A0 | Temporary213152-byte probe: separate64KiB DSP shadow, immediate reference and producer RAM;16KiB core/event/PCM state; five32-byte guards |
| 0x438000..0x440000 | Persistent32768-byte host diagnostic snapshot; separate from temporary DSP state |

The extra code initially pushed BSS to0xD8DC0, beyond the existing0xD6000
CGRAM boundary. The snapshot now binds to cached0x80438000 instead of occupying
base BSS. Full recording capacity and all194 ROM slots/base caches are retained.
Loaded/zeroed ELF sections remain low; no IPL3/BSS store targets absent upper
memory. Manual arm, remote arm, direct snapshot copy and the full-DSP snapshot
lease reject unsupported memory sizes before upper access. Base4MiB gameplay
continues; these experimental diagnostic/window operations report unavailable.
The snapshot remains a host diagnostic owner, excluded from guest save states.

`audio-window-memory-probe` requires a healthy transport, paused published
frame, no active capture/arm and verified8MiB. It executes the existing full DSP
with the window controller against an independent immediate core for512 clocks,
48 serialized-state/three-RAM/PCM comparisons and64 producer reads.32 enabled
echo publications are expected. It releases CPU cache lines with WB/invalidate
and sync, verifies all guards and all64KiB views through uncached aliases, then
expires the temporary lease. It writes neither guest RAM, SP memory/registers,
DMA registers nor guest audio. Any failure requires menu recovery.

Local proof uses the actual probe with modeled cached/uncached aliases: eight
invalid size cases reject before pointer access; stale plans/null results reject;
a corrupted guard returns failure. Native cache/memory behavior remains pending.
Parser tests cover306 combined-context cases plus1000 fuzz, and a separate275
case configuration plus1000 fuzz proves the terminal window failure/menu gate
and full-probe rejection before using the relocated snapshot on unsupported RAM.

Actual linked proof covers43 base owners plus the two disjoint upper leases,
all below the top64KiB boot reservation;15 invalid arm/remote/copy cases produce
no upper writes or CP0 changes. The admitted32KiB snapshot loop copies exactly
and emits2048 correct cache operations. Existing16 init/manual-arm cases and
30 boot/reboot/RAM capture cases pass. CPU/RSP CGRAM words and four actual DMA
backup sites agree. Runtime ends0xD0DC0, gap0x5240 below CGRAM0xD6000.
Final ELF sizes:text111440,data731772,BSS10784. No broad CI or FPS claim.

The existing R61 complete state/RAM/PCM host proof and all eleven mutants remain
valid: window/core arithmetic and ordering source is unchanged by these owner
additions. No new live guest state is introduced. Before a live bridge, exact
within-JIT bus timestamps, echo CPU-cache/JIT-tag invalidation and complete save
ownership still need implementation; a complete resident RSP DSP kernel and its
native full-work discriminator remain open.

Next physical action: install/readback this frozen artifact, launch existing
private ALttP, pause/park600, compare image/PCM/heads/registers around two owner
probes, continue660, then perform one ordinary USB capture to qualify the moved
32KiB snapshot. Finally restore coordinate8/menu/install/readback. Record the
live process handle before waiting; root alone owns COM3. Report resource safety
and coexistence only; full DSP/DAC/native60/50/corpus/integration remain OPEN.
