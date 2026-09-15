# Phase 1 baseline map

This document records the starting architecture and the measurements Phase 1 must establish before runtime optimization begins.

## Baseline commit

The fork began from upstream Sodium64 commit `a4c75d3819691f5fdb6de49712090c643f17abea` (`Implement manual controller reading`, 2025-07-11). Phase 0 added only project infrastructure and documentation; emulator runtime behavior remained unchanged.

## Current execution architecture

### S-CPU (65C816)

The SNES CPU is currently interpreted directly in MIPS assembly. Opcode dispatch uses mode-specific lookup tables and jumps to assembly handlers. CPU cycle counters are interleaved with APU and PPU event scheduling.

### APU / SPC700

The APU already uses a block JIT. Compiled blocks are cached through a lookup table and invalidated with memory tags when the underlying APU RAM changes. This existing machinery is an important reference for a future 65C816 translator, but it should not be copied blindly because the S-CPU memory/timing problem is different.

### DSP

DSP sampling is scheduled from the same master-cycle model as the CPU/APU events.

### PPU and frame construction

The CPU-side PPU tracks scanline events, frame sections, HDMA, OAM/VRAM/CGRAM state, and queues work for the RSP renderer.

### RSP renderer

The RSP renders queued frame data while the R4300 continues emulation work. CPU-side code waits for RSP completion when required before final frame handling. RSP IMEM/DMEM pressure is therefore a first-class resource constraint rather than spare compute that can be assumed available for future coprocessors.

### Existing enhancement-chip support

DSP-1 is the only explicit enhancement-chip implementation currently present in the source tree (`src/xcop_dsp1.S`). There is no current Super FX or SA-1 implementation.

## Existing performance/accuracy compromises that must be treated as baseline facts

- Frame skipping is available as a user setting.
- APU underclock is available and enabled by the current default settings.
- PPU precision is user-adjustable.
- Some timing behavior is explicitly approximate, including the pre-VBlank NMI timing workaround.

These mechanisms may remain useful as compatibility/debugging options, but they are not counted as success for the long-term performance target.

## Phase 1 measurement questions

The first instrumentation work should answer these questions with low overhead:

1. How much R4300 time is spent executing the S-CPU path per emulated frame?
2. How much is spent in APU block execution/compilation and DSP work?
3. How much is spent in CPU-side PPU events, HDMA, section generation, palette/VRAM preparation, and menu/frame bookkeeping?
4. How often and for how long does the R4300 wait for the RSP?
5. How frequently does the frame queue hit back-pressure (`frame_count` / framebuffer availability)?
6. Which memory-read/write paths dominate S-CPU execution?
7. How much headroom exists in the RSP program/data layout and in R4300 code/data caches?
8. How different are results with frame skip disabled and APU underclock disabled?

## Instrumentation design constraints

- Counters must be cheap enough not to materially change the bottleneck being measured.
- Instrumentation must compile out or be disabled for normal release builds.
- Measurements should be aggregated per frame rather than logging every event.
- Prefer hardware counters / CP0 Count deltas and compact numeric telemetry over printf-style logging.
- The measurement interface should work in an N64 emulator first and on real hardware later without changing core semantics.
- Instrumentation must distinguish active R4300 work from time spent waiting on RSP/frame availability.

## First milestone

Phase 1 is complete only when we can produce a per-frame budget that separates at least:

- S-CPU execution;
- APU/DSP work;
- CPU-side PPU/HDMA/frame preparation;
- RSP wait / synchronization;
- miscellaneous overhead.

Only then do we choose the first large runtime optimization. The 65C816 dynarec remains the leading hypothesis, not a foregone conclusion.
