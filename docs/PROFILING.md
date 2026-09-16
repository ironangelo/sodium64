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

The main CI workflow compiles both configurations on development-branch pushes. Profiling artifacts are uploaded separately as `sodium64-profile-build` and are never used for the rolling release; only the normal `master` build feeds the rolling release.

A separate **Ares Profile Validation** workflow runs for pull requests targeting `master`, pushes to `master`, and manual dispatches. It builds its own `PROFILE=1` artifact so the existing build/release workflow remains independent.

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

`scripts/profile_report.py` consumes a raw dump beginning at `profile_magic` plus the exact matching profiling ELF. It reconstructs the ring buffer using the profiler symbols, handles wraparound, recognizes the generated APU JIT range, and reports the hottest sampled symbols/regions.

The decoder accepts canonical big-endian N64 memory and the 32-bit word-swapped representation exposed by some debuggers. Extraction remains separate from the on-console profiler format, so emulator and future hardware paths can share the same report tooling.

When supplied with the exact GNU linker map, the reporter also classifies static sampled addresses by the object that owns them. `scripts/profile_matrix.py` then groups those objects into broad Phase 1 buckets such as S-CPU, APU, DSP, PPU/frame preparation, DMA/HDMA and wait states. Classification stays host-side; it adds no work to the emulated N64 hot paths.

## Automated extraction paths

### Mupen64Plus smoke

The main validation workflow builds a pinned Mupen64Plus debugger with an LLE RSP plugin, runs both normal and profiling Sodium64 builds, dumps the profiler memory region resolved from the matching ELF, and decodes it host-side.

This is useful as an independent boot/runtime check, but its timing distribution is not treated as an N64 performance oracle. The original tiny synthetic workload exposed emulator-specific behavior, including repeated SI/PIF DMA warnings and a profile dominated by `rsp_wait`.

### ares profiling

The separate Ares Profile Validation workflow builds a pinned N64-only ares revision and launches the profiling Sodium64 ROM under its GDB remote server. `scripts/gdb_rsp_dump.py` performs the minimal RSP sequence needed by CI:

1. send the initial acknowledgement required by ares' TCPText GDB guard;
2. negotiate `qSupported` and query the initial stop state;
3. use `QPassSignals` so normal emulated N64 CPU exceptions, including Sodium64's intentional TLB handling, continue to the guest instead of stopping the debugger;
4. warm the target before any measurement-only patches are applied;
5. continue execution for one or more measured sampling windows;
6. halt explicitly with Ctrl-C when needed, with a longer stop-response timeout for graphics-heavy workloads;
7. read the ELF-resolved profiler region in bounded chunks;
8. detach and decode the snapshot with the matching profiling ELF.

The first successful short ares validation produced only eight samples distributed across `cpu_execute`, `apu_read8`, and `cpu_bra`. That run proved the end-to-end capture path but was deliberately not treated as enough evidence for a bottleneck ranking.

## Full-rate APU preparation

Sodium64 inherits an APU-underclock setting whose default `apu_clock` is twice `APU_CYCLE`. Phase 1 performance decisions must not rely on that concession.

The ares profiling harness therefore prepares a full-rate measurement only **after warm-up**:

1. patch `apu_clock` to `APU_CYCLE` (`21` master cycles);
2. invalidate the existing APU block lookup table;
3. reset `jit_pointer` to `JIT_BUFFER`, matching the semantic requirement that SPC700 blocks be recompiled for the new timing;
4. reset `profile_sample_count`, `profile_write_ptr`, and `profile_last_epc`;
5. begin the measured interval.

The profiler ring is reset after the preparation work, so the cost of changing the diagnostic condition itself is not counted in the workload profile. These patches exist only in the profiling session; they do not change normal Sodium64 defaults or release runtime behavior.

## Deterministic workload matrix

`scripts/make_profile_workloads.py` generates five original SNES LoROM workloads without commercial ROM data:

- `idle` — minimal guest loop plus normal surrounding emulator activity;
- `cpu-alu` — deliberately CPU/ALU-heavy 65C816 work;
- `wram` — repeated guest WRAM-oriented load/store work;
- `ppu-registers` — repeated PPU register activity;
- `dma-vram` — DMA-driven VRAM traffic.

The ares N64 recompiler is used for decision-lab runs because it advances the emulated N64 far more quickly per CI wall-clock second than `ForceInterpreter=true`. One interpreter idle run remains as a control.

Profiles are not accepted merely because they are non-zero. Recompiler workloads accumulate repeated measured windows until they reach a minimum useful sample count (currently 200) or a bounded maximum measurement duration. This avoids comparing a dense profile against a twelve-sample accident.

### First successful matrix

The first fully green full-rate matrix produced:

| workload | samples | S-CPU | APU JIT | APU static | DSP | PPU/frame prep | DMA/HDMA | frame/VI wait |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| idle | 2,138 | 49.2% | 4.1% | 33.6% | 1.4% | 2.0% | 0.1% | 9.5% |
| cpu-alu | 1,923 | 61.3% | 1.7% | 35.1% | 0.5% | 1.1% | 0.3% | 0.0% |
| wram | 1,594 | 59.2% | 2.9% | 35.1% | 0.8% | 1.9% | 0.1% | 0.0% |
| ppu-registers | 1,030 | 52.3% | 3.7% | 24.9% | 0.6% | 18.4% | 0.1% | 0.0% |
| dma-vram | 948 | 0.1% | 0.3% | 0.7% | 0.0% | 96.7% | 2.1% | 0.0% |

The PPU-register and DMA-VRAM profiles required two three-second measured windows to reach sufficient density; the other recompiler workloads reached it in one.

These distributions are useful because they move in the expected direction when the guest workload changes: CPU-heavy code increases S-CPU representation, PPU-register churn substantially increases PPU/frame-preparation samples, and DMA-to-VRAM drives the profile overwhelmingly into the corresponding PPU/VRAM path.

This validates the **measurement harness and classification sensitivity**. It does not prove that a commercial game spends these percentages in the same places.

## Synthetic workload limitations

Synthetic workloads are causal controls, not representative gameplay benchmarks.

A deliberately CPU-heavy ROM producing an S-CPU-heavy profile does not by itself justify a 65C816 dynarec. Likewise, the DMA-VRAM control being dominated by `write_vmdatal` does not mean ordinary games spend 96% of their time there.

The ares recompiler is also a laboratory accelerator, not the performance model of a real 93.75 MHz R4300. Sample proportions can be useful for identifying which Sodium64 code is active under controlled guest workloads, but wall-clock throughput inside ares must never be reported as real-N64 FPS or headroom.

Commercial-game profiles and real-hardware measurements remain required before a major architecture is accepted as the answer to the Road-to-1.0 performance problem.

## Next Phase 1 measurement step

The synthetic workload matrix establishes that the profiler can distinguish controlled S-CPU, PPU and DMA pressure at useful sample density with full-rate APU timing.

The next step is no longer more synthetic-profiler plumbing. Phase 1 should now obtain representative gameplay-oriented profiles and quantify frame-budget/deadline behavior under the Road-to-1.0 conditions: no required frameskip and full-rate audio.

Those measurements should determine whether the proposed 65C816 dynarec enters Phase 2, or whether PPU/RSP, APU, memory, synchronization or another measured subsystem deserves the first major architecture batch.
