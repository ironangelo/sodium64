# Bounded native diagnostic v4

This is measurement infrastructure, not an FPS optimization. The ordinary
emulator is unchanged. Native captures are separately named builds with MAX
precision, frameskip 0 and full APU clock 21. Commercial input, SRAM and footage
stay private; only independently authored fixtures enter CI.

## What the recorder can distinguish

Each complete frame boundary stores Count elapsed time and the CPU's explicit
RSP and VI wait durations. All timer interrupts classify CPU work into linked
S-CPU, static/generated APU, DSP, DMA, PPU, RSP-wait, VI-wait and other domains.
The CPU can prepare N+1 while the RSP draws N; these intervals are completed
boundaries, not exclusive RSP render timings or measured presentation FPS.

All timer interrupts also classify the sampled RSP into halted, unknown/loading,
DMA wait, RDP wait, HCOMP phase / Mode7 window, general math, direct composition
and source draw / resident control. Linked RSP source and the matching bank ELF
identify the operation family. The diagnostic-only 16-bit DMEM tag bookends the
PC read with a 12-bit epoch, pending flag and bank ID. A changed/pending/invalid
bank or a read window of at least 1ms is unknown. A completed bank change performs
one 1000-byte IMEM DMA; 4096 such transfers cannot complete within the 1ms guard.
Resident DMA/list-fetch/texture-retirement loops have separately qualified PCs.
HCOMP's RDP fence is recognized only in its validated bank.

Observations every 125ms bind CPU and RSP sample counts to controls, band size,
sections and frame progress. PPU/control values are explicitly best-effort,
non-atomic observations. Exact arithmetic operands/per-pixel operations are not
logged. Per-frame waits show which boundary exceeded the nominal budget; nearby
source stages and EPCs guide an intervention. A comparison that changes one
suspected mechanism and preserves pixels is still needed to confirm causation.
Busy status shares are not exact RDP utilization and must not be added to CPU or
RSP shares. Unsupported or ambiguous observations remain visible.

## Retention

Guest SRAM is limited to 8 KiB and is preserved. A larger selected header is
rejected before any SRAM mutation. The remaining 24 KiB contain:

| Region | Contents |
| --- | --- |
| 0x2000–0x21FF | 512-byte header, tails, checksum and observer metadata |
| 0x2200–0x25FF | 256 CPU EPCs, every 32nd timer interrupt |
| 0x2600–0x61FF | 1280 completed-boundary records, 12 bytes each |
| 0x6200–0x7AFF | 160 workload observations, 40 bytes each |
| 0x7B00–0x7FFF | 20 second records, 64 bytes each |

The first partial boundary after manual arm is excluded. Buffers append only;
exhaustion and 8-bit observation saturation set explicit flags. The report checks
checksum, frame waits, progression and CPU/RSP count consistency. A 20-second
capture retains the whole interval; the decoder also reads earlier v1–v3 saves.
Measured ISR/frame-helper bodies are reported, but do not account for all cache,
bus and RSP tag-hook perturbation. Compare performance against the normal build.

## Repeat captures from one ROM

`tools/sc64-diagnostic-save` integrates a unique writeback target into the pinned
SummerCart menu. The same personal ROM can be reloaded repeatedly; every launch
reserves `<ROM-stem>-diag-<tag>-000001.sav`, etc., by exclusive FATFS creation.
Ordinary progress is imported read-only. Only that reserved file receives the
capture. This requires the paired menu/emulator and opt-in INI configuration.
Read its README for installation and reset behavior. An unarmed launch can leave
an incomplete reservation; only `CAPTURE SAVED` plus a valid checksum is evidence.

## Validation boundary

Compiled MIPS tests exercise register preservation, EXL/interrupt masking, Count
wrap, capacities, tag loading and PC classification. Original 20-second guests
validate arming, full retention, terminal capture and PI payload equality. Normal
pixel oracles and representative armed-diagnostic pixel oracles guard fidelity.
These establish laboratory correctness, not real N64 timing or SD writeback.
Hardware captures remain the source of performance evidence and menu qualification.
