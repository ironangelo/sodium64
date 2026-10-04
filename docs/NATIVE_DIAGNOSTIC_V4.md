# Bounded native diagnostic v4

This is measurement infrastructure, not an FPS optimization. Native captures are
separately named builds with MAX precision, frameskip 0 and full APU clock 21.
Commercial input, SRAM and footage stay private; only independently authored
fixtures enter CI.

Current reference is A13 `b4206144fefe1d77b05397be154115d6328a2965`; A11 remains
the regression control. The bounded physical-console batch has been analyzed:
13 complete captures, six A11/A13 scene pairs and one unpaired A13 ALttP intro.
The named A11 ALttP intro capture was unavailable. The initial cross-game
measurement gate is met. See the curated evidence and remaining limits in
[the causal diagnosis plan](GATE_C_CAUSAL_PROFILING_PLAN.md) and
[Continuity](CONTINUITY.md).

Two independent experiments now have compiled contract passes: packed arithmetic
`3a0c7fc` and Sub-presence dataflow `76f3f9`. Complete image qualification has passed;
their physical-console comparisons remain pending. Neither is included in A13,
and neither establishes constant native 60 FPS.

Both candidates passed exact-head Build and full Gate qualification: 94 normal complete images (5,390,336 pixels) and 12 armed v4 images (688,128 pixels) per candidate, with all compact guards passing. Manual and v4 original-guest recorders completed approximately 20 seconds, retained the whole v4 interval without overflow, and preserved cartridge PI payload bytes. Physical-console speed, normal output and audio comparisons remain pending.

## What the recorder can distinguish

Each complete frame boundary stores Count elapsed time and the CPU's explicit
RSP and VI wait durations. All timer interrupts classify CPU work into linked
S-CPU, static/generated APU, DSP, DMA, PPU, RSP-wait, VI-wait and other domains.
The CPU can prepare N+1 while the RSP draws N; these intervals are completed
boundaries, not exclusive RSP render timings or measured presentation FPS.
CPU EPC attribution requires the exact linked ELF/map for the captured build.

The recorder also retains candidate RSP bank/stage classifications and
best-effort PPU controls from live DMEM reads. These reads, including the
diagnostic 16-bit bank tag and other subword fields, are not qualified for real
N64 hardware. [Libdragon's RSP documentation](https://libdragon.dev/ref/rsp_8h.html)
documents direct DMEM access as 32-bit reads/writes while the RSP is stopped.
Epoch/pending bookends detect some inconsistent observations; they do not
validate the shipped access mechanism or establish precise overlay identity.
The decoder therefore marks overlay identity and PPU controls as unvalidated
candidates. Do not use their percentages to assert that a drawing or color
arithmetic operation caused a slowdown. Completed boundaries, explicit CPU
waits and exact CPU EPC symbols remain the reliable evidence.

Observations every 125 ms retain candidate controls and CPU sample counts
alongside section and frame progress. Exact arithmetic operands and per-pixel
operations are not logged. Per-frame waits identify completed intervals that
exceed the nominal budget; exact CPU EPCs and source-proven repeated work can
guide an intervention. A controlled comparison that preserves pixels and
repeats on N64 is needed to establish causation. Concurrent CPU/RSP sample
shares and explicit waits overlap and must not be added. Latched RDP busy bits
are not exact utilization. Unsupported or ambiguous observations remain visible.

Precise internal RSP attribution, if a decision requires it, needs a separately
audited RSP-owned publication mechanism and observer-cost qualification. That
instrumentation is not a prerequisite for the current controlled experiments.

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
Read its README for installation and reset behavior. No duplicated or aliased
game files are required.

A reservation is created before the game launches, so an unarmed launch can
leave an empty or incomplete diagnostic reservation. Existing reservations are
retained and later launches choose the next available identifier. A numbered
filename alone is not evidence of a capture: require `CAPTURE SAVED`, a complete
record and a valid checksum. The current physical batch confirms usable recorder
transport and saved-file recovery on the tested setup; it does not qualify every
menu, firmware, storage device or guest SRAM configuration.

## Validation boundary

Compiled MIPS tests exercise register preservation, EXL/interrupt masking, Count
wrap, capacities and the intended tag/PC-classifier behavior. Original 20-second
guests validate arming, full retention, terminal capture and PI payload equality.
Normal and armed-diagnostic pixel oracles guard tested output. A13's laboratory
qualification includes 94 normal complete images and 12 armed v4 images.

These establish laboratory contracts; they do not validate live DMEM attribution
or physical N64 cadence. The current physical batch establishes complete
checksummed capture retention under the tested settings. It does not measure
clean-release presentation FPS or total observer perturbation. Physical cadence,
normal-build output, progression and audio remain necessary when qualifying a
performance change. Keep commercial inputs, raw saves, state, footage and hashes
private; publish only original controls and curated aggregate conclusions.
