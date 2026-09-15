# Statistical profiling

Phase 1 needs to identify where the R4300 spends host time without perturbing the hot paths enough to invalidate the measurement. The first profiler therefore uses **statistical PC sampling** instead of timing every opcode, JIT block, or scanline.

## Build mode

Normal builds remain unchanged:

```sh
make
```

A profiling build is enabled explicitly:

```sh
make PROFILE=1
```

`PROFILE=1` defines `SODIUM64_PROFILE` only for the R4300 assembly build. The normal release build does not enable CP0 timer sampling or include active profiler state in runtime behavior.

CI compiles both configurations on development-branch pushes. Profiling artifacts are uploaded separately as `sodium64-profile-build` and are never used for the rolling release; only the normal `master` build feeds the rolling release.

## Sampling method

The R4300 CP0 Count/Compare timer generates an IP7 interrupt at an interval of **65,521 Count ticks**. The interval is deliberately not a power of two to reduce phase-locking with regular emulator and frame loops.

On each profiling interrupt, the handler:

1. reads CP0 EPC, which identifies the interrupted R4300 instruction stream;
2. stores that EPC in a fixed-size ring buffer;
3. increments a total sample count;
4. schedules the next Compare interrupt relative to the current Count;
5. returns with `eret`.

The exception-time path only clobbers `k0` and `k1`, matching the MIPS convention for registers reserved to exception handlers. It does not call normal subroutines or touch `ra`, `at`, emulator state registers, or JIT state.

## Profiler state

`src/profile.S` exposes these ELF symbols in profiling builds:

- `profile_magic` — `0x53363450` (`S64P`);
- `profile_version` — currently `1`;
- `profile_interval` — Count ticks between requested samples;
- `profile_capacity` — number of EPC entries in the ring;
- `profile_write_ptr` — address of the next ring entry;
- `profile_sample_count` — monotonically increasing total number of samples;
- `profile_last_epc` — most recently sampled EPC;
- `profile_sample_buffer` / `profile_sample_buffer_end` — ring-buffer bounds.

The initial capacity is 4,096 EPC samples (16 KiB). Once full, the newest samples overwrite the oldest while `profile_sample_count` continues increasing.

## Why raw EPC samples instead of runtime categories?

Categorizing samples inside the N64 runtime would require maintaining fragile address ranges for CPU/APU/PPU/DSP modules and would make every future code-layout change part of the profiler implementation.

Raw EPC samples are more useful. Host-side tooling can symbolicate them against the exact profiling ELF/linker map that produced the run. It can also classify generated APU JIT addresses specially, identify wait loops such as `rsp_wait` and `frame_wait`, and regroup symbols later without rerunning the N64 workload.

This makes profiling data forward-compatible with architecture changes.

## Intended interpretation

Over a sufficiently long representative run, the proportion of PC samples approximates the proportion of R4300 execution time spent in each code region. Examples of useful buckets include:

- S-CPU interpreter and addressing/ALU/control paths;
- SNES memory read/write paths;
- SPC700/APU static code;
- generated APU JIT buffer;
- DSP/audio work;
- PPU/HDMA/frame construction;
- `rsp_wait` (R4300 blocked waiting for the RSP);
- `frame_wait` (framebuffer/VI back-pressure);
- menu/input/interrupt/miscellaneous work.

This does **not** directly measure RSP instruction-level cost. RSP pressure appears indirectly as R4300 samples in synchronization/wait paths; RSP-specific profiling can be added separately if Phase 1 measurements show it is necessary.

## Bias and validation

Statistical sampling is intentionally approximate. Before using it to justify a major rewrite we should validate that:

- normal and profiling builds show no semantic/gameplay differences;
- profiling overhead is small enough that FPS/frame behavior is not materially changed;
- results are stable across repeated runs of the same workload;
- sample distributions change sensibly when settings such as APU underclock or frame precision change;
- obvious synthetic workloads produce obvious sample distributions.

The profiler is a decision tool, not a cycle-accurate oracle.

## Host-side report tool

`scripts/profile_report.py` consumes a raw big-endian dump beginning at `profile_magic` plus the exact matching profiling ELF. It reconstructs the ring buffer using the profiler symbols, handles wraparound, recognizes the generated APU JIT range, and reports the hottest sampled symbols/regions.

The extraction mechanism that produces that raw dump is intentionally separate. Emulator automation can provide it first; a hardware extraction path can be added later without changing the on-console profiler format.

## Next tooling step

The next layer is automated extraction of the profiler memory region from an N64 emulator run. That tooling should consume the profiling build's ELF/map rather than hard-coding static text addresses. Real-hardware extraction can be added later when it becomes useful for a milestone gate.
