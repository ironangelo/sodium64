# Faithful compositor integration

Status: CANDIDATE / draft PR32. Production defaults remain unchanged pending
qualification. `FAITHFUL_RENDERER=1` temporarily selects the extracted compositor
for comparison; this is not a second user-facing mode. Promotion must retire
that temporary legacy path after the physical gates pass.

The coherent source is R17 at
`238170abf956da705806f979f9cc256fbc565ac0`, derived from the A11/A13 visual work
for the dark ALttP house and rain/layer scenes. R44/R45 remain separate. Current
master CPU interpreter, APU, DSP, USB and profiler implementations are retained.
The original renderer's necessary ROM paging and CPU source bindings are explicit.

There are two bounded RSP differences from the frozen source: the integrated
PR29 decoder-return NOPs, and removal of seven old laboratory composition-limit
reads/branches. The latter folds their ordinary zero-limit behavior while
preserving fixed offsets and register effects. Only18 instruction words change
relative to the pre-cleanup port; every other loaded byte/address, all RSP data
and all CPU/APU/DSP/PPU bytes remain identical. Poisoned retired words cannot
reactivate that control. Historical macro names retained for fixture guards
allocate no storage and have no production reads.

The selected lower-memory plan reserves composition surfaces at384000..3e7000,
row queues at3e7000/3e7200 and Q2 events at3e8000..400000. Its194 ROM-cache pages
end exactly at384000; cartridge bytes still page from cart, with no ROM-size
truncation. Q1 begins atD2000 and the linker checks its actual CPU/RSP owner.
Existing upper diagnostic leases remain independently gated and excluded from
normal builds. Fixed residents are4KiB; demand-loaded slots are1000bytes.

Local proof, rechecked2026-11-08:

| Contract | Evidence and limit |
| --- | --- |
| Reference binding | All12 RSP text/data/extents equal a fresh frozen compile plus the declared repairs. Complete PPU object sections and688 normalized relocations (700 USB) match in all four configurations. |
| Removed laboratory limit | Seven sites,112 scalar state/read cases per configuration with poisoned retired words; no production limit load remains. Fixed bank extents and all ordinary register effects are preserved. |
| CPU publication and owners | Twelve actual writes under16 register cases; uncached descriptors and sixteen emitted fault rejections. Boot/ISR/snapshot67 cases, legacy27, full lower owner plan and independent upper admission. |
| ROM replacement |646 complete linked refills per build:194 cold,226 victim-present and226 victim-absent;20 actual instruction faults rejected across four builds. Ten TLBP model controls. Delayed PI, alias/map/register owners and composition sentinels pass. No CPU cache, bus-cycle or hazard model. |
| Window and OBJ execution |1792 compiled window cases/two mutants;28672 objects spanning19328 drawn and88192 culled rows. Independent geometry truth and caller/memory ownership. |
| Full-row Math/DMA |Twelve cases/70912 original numeric pixels match the independent arithmetic oracle and ordinary-row reference. VRAM backup/restore retires before Phase; OAM and other owners stay intact. Skip-restore, short-backup and overlap faults are rejected. Setup is seeded; RDP rasterization is not modeled. |
| Existing core and release |9984 decoder cases/four mutants, all12 delay-slot checks, integrated audio contracts and release admission remain applicable. Disabled normal rebuild equals all767064 measured integrated bytes/addresses. |

`scripts/replay_faithful_contracts.py` stages immutable original test interpreters
from the same source pin. One input adaptation removes the historical observer
bank tag from the synthetic Phase pointer, matching actual aligned production
CPU publications. No VM alignment/ownership assertion or pixel oracle is
weakened. The original failed control and its cause are retained in the receipt.
The first CI missing-header and legacy-wrapper failures are also preserved.
The pinned libdragon RDP header produces the same reference images.

The emulator build has no historical Git or modified-menu dependency. Only the
optional proof needs the immutable source object:
`git fetch --depth=1 origin 238170abf956da705806f979f9cc256fbc565ac0`.
Production release admission checks the actual normal ELF/ROM and two-file ZIP;
USB/reset/capture/profiler implementations are compiled only in laboratory builds.

Remaining promotion gates:

1. Complete exact-head CI for the cleaned runtime and new functional contracts.
2. On real N64, qualify RDP output and pager/cache behavior, then aligned faithful
   house/rain/SMW/DKC/Mode7 images against the proper visual reference. Compare
   APU/PCM and guest progression to the integrated core, preserving full rate.
3. Measure the combined native baseline with quiet windows, return and verified
   habitual restoration. Resolve differences before default promotion. Then
   resume the complete resident-DSP integral cost gate, independently of R44/R45.

No new native acceptance, presentation FPS or DAC claim is made here. Commercial
ROMs, saves, states, captures, audio and game-derived hashes stay local.
[Scoped original-program receipt](evidence/faithful-compositor-local.json).
