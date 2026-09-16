# Statistical profiling

Phase 1 uses statistical R4300 PC sampling to identify where Sodium64 spends host CPU time without instrumenting every opcode, scanline, or hot memory path.

This document defines what the profiler measures, how CI captures it, and which conclusions are currently valid.

## Build mode

Normal release/runtime behavior remains unchanged:

```sh
make
```

Profiling is opt-in:

```sh
make PROFILE=1
```

`PROFILE=1` defines `SODIUM64_PROFILE` only for the R4300 assembly build. Normal `master` release artifacts do not enable the CP0 sampling path.

## Sampling method

The profiling build programs CP0 Count/Compare at an interval of **65,521 Count ticks**, deliberately not a power of two to reduce phase-locking with regular emulator loops.

Each profiling interrupt:

1. reads CP0 EPC;
2. stores the interrupted address in a fixed-size ring;
3. increments the total sample count;
4. schedules the next Compare event;
5. returns with `eret`.

The exception path only uses `k0`/`k1` and does not call normal subroutines or mutate emulator/JIT state.

The initial ring holds 4,096 EPCs (16 KiB). After wraparound, newer samples overwrite older entries while the monotonically increasing sample count continues.

## Host-side interpretation

`scripts/profile_report.py` combines the raw snapshot with the **exact matching ELF/linker map**. Classification stays host-side so the runtime sampling path remains cheap and future regrouping does not require rerunning the ROM.

Important buckets include:

- S-CPU interpreter;
- SNES memory/I-O;
- SPC700/APU static code;
- generated APU JIT code;
- DSP/audio;
- PPU/events/frame preparation;
- DMA/HDMA;
- `RSP/VRAM semaphore wait`;
- `rsp_wait`;
- `frame_wait` / VI back-pressure.

The first `0x10` bytes of `write_vmdatal` / `write_vmdatah` are classified separately as **RSP/VRAM semaphore wait** because those four instructions spin on `SP_SEMAPHORE`. From `+0x10` onward the functions remain classified as actual PPU/VRAM work.

This profiler measures where the **R4300** is sampled. It does not directly provide instruction-level RSP cost.

## Interpretation limits

Statistical samples approximate R4300 execution-time share only for the exact workload/settings/environment measured. They are not a cycle-accurate oracle.

Before using a result for an architecture decision, verify:

- exact SHA / ELF / map / artifact;
- workload and sample density;
- frameskip setting;
- APU clock and JIT reset state;
- audio setting;
- precision setting;
- emulator/hardware environment;
- virtual frame-budget signal.

Synthetic stress ROMs are **causal controls**, not commercial-game representatives. A CPU-heavy control being CPU-heavy does not by itself justify a dynarec, and a DMA stress result does not describe ordinary gameplay.

## Full-rate APU preparation

Sodium64 inherits an APU-underclock mode. Phase 1 decision measurements must not rely on it.

After warm-up the ares harness therefore:

1. patches `apu_clock` to `APU_CYCLE` (`21`);
2. invalidates the APU JIT lookup table;
3. resets `jit_pointer` to `JIT_BUFFER`;
4. forces frameskip setting `0`;
5. keeps audio enabled;
6. resets profiler and frame-budget state;
7. starts the measured interval.

Preparation cost is excluded from the measured profile.

## Automated laboratories

### Mupen64Plus

The main validation workflow builds a pinned Mupen64Plus debugger with an LLE RSP plugin and runs normal + profiling Sodium64 builds.

This is useful as an independent boot/runtime smoke path, but its timing distribution is **not** an N64 performance oracle.

### ares

`Ares Profile Validation` builds pinned N64-only ares at:

`17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`

The GDB harness warms the target, applies profiling-only settings, accumulates a bounded sample window, captures profiler memory plus selected runtime state, and decodes everything against the matching ELF.

### LAB LIMITATION — ares RSP recompiler

A controlled 2x2 experiment demonstrated that the pinned ares **RSP recompiler is not valid for Sodium64 custom RSP microcode under the gameplay workload**.

Run: `35113184294`

Artifact: `sodium64-ares-recompiler-isolation`, ID `10453682432`.

Same Sodium64 build/workload/settings:

| CPU engine | RSP engine | completed guest frames / 60 VI |
| --- | --- | ---: |
| JIT | JIT | **0/60** |
| interpreter | interpreter | **60/60** |
| JIT | interpreter | **60/60** |
| interpreter | JIT | **0/60** |

Both modes with RSP JIT enabled sampled essentially all R4300 time in `write_vmdatal` semaphore wait. With RSP JIT disabled the workload progressed normally, independently of whether the R4300 used JIT or interpreter.

At the collapsed capture the RSP was not DMA-busy. `SP_PC=0x0D90` maps to Sodium64 RSP `next_frame`, the intentional end-of-frame self-halt path. The exact defect inside ares is not currently relevant to a Road-to-1.0 gate and should not become a side project.

**Valid high-density ares decision-lab mode:**

- R4300 recompiler **ON**;
- RSP recompiler **OFF** / RSP interpreter **ON**.

Interpreter controls use both interpreters.

Old results collected with the ares RSP JIT are retained only as historical evidence of this laboratory limitation and must not be interpreted as Sodium64 or real-N64 performance.

## Deterministic workload matrix

`scripts/make_profile_workloads.py` currently generates six original SNES LoROM workloads:

- `idle` — minimal guest work;
- `cpu-alu` — continuous arithmetic/branch pressure;
- `wram` — continuous WRAM load/store pressure;
- `ppu-registers` — repeated PPU-register activity;
- `dma-vram` — deliberately heavy DMA-to-VRAM stress;
- `gameplay-balanced` — frame-paced `WAI`/NMI workload with bounded CPU/WRAM work, scroll, one visible OBJ, OAM DMA, modest VRAM DMA and small CGRAM DMA once per frame.

All are original deterministic diagnostics and contain no commercial ROM data.

Profiles are required to reach useful sample density rather than merely be nonzero. Current decision runs target at least 800 samples, bounded by maximum measurement duration.

## Superseded first matrix

The original full-rate matrix was useful for validating that controlled workloads changed the profiler in expected directions, but its PPU/DMA interpretation is now **SUPERSEDED** because the ares RSP JIT pathology and coarse symbol classification contaminated VRAM results.

In particular, the old statement that `dma-vram` spent about **96.7% in PPU/frame prep** is no longer valid. Most of those samples were the semaphore guard at the start of `write_vmdatal`.

Do not use the old matrix for architecture decisions.

## Current valid matrix — CPU JIT + RSP interpreter

Replacement run: `35114866448`

Artifact: `sodium64-ares-profile-matrix`, ID `10454678803`.

Road-to-1.0 measurement conditions include frameskip `0`, APU clock `21`, audio enabled, and precision setting `8`.

| workload | samples | S-CPU | APU JIT | APU static | DSP | PPU | DMA | VRAM/RSP wait | VI wait |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| idle | 1,303 | 49.8% | 5.1% | 31.5% | 1.4% | 2.3% | 0.2% | 0.0% | 9.7% |
| cpu-alu | 1,055 | 59.0% | 2.0% | 36.2% | 0.9% | 1.6% | 0.3% | 0.0% | 0.0% |
| wram | 1,474 | 56.7% | 3.3% | 36.8% | 0.5% | 2.3% | 0.4% | 0.0% | 0.0% |
| ppu-registers | 1,123 | 42.7% | 4.0% | 31.3% | 0.6% | 21.2% | 0.1% | 0.0% | 0.0% |
| dma-vram | 878 | 1.1% | 1.5% | 7.7% | 0.1% | 31.2% | 30.5% | 27.8% | 0.0% |
| gameplay-balanced | 930 | 6.3% | 7.5% | 27.3% | 0.6% | 4.3% | 2.0% | 0.3% | 51.5% |

The replacement matrix behaves causally as expected:

- CPU controls remain S-CPU-heavy;
- PPU-register churn raises PPU share;
- the DMA stress now separates actual PPU work, DMA execution and VRAM/RSP synchronization instead of collapsing them into one false PPU bucket;
- `gameplay-balanced` spends over half its sampled R4300 time in `frame_wait`, showing substantial virtual headroom under this synthetic game-shaped workload.

## Virtual frame budget

`frame_budget_report.py` reads Sodium64's own internal completed-frame count over a complete 60-VI interval. CI host wall-clock time is reported separately and **must never be interpreted as N64 FPS**.

Current valid run:

| workload | completed frames / 60 VI | interpretation |
| --- | ---: | --- |
| idle | 60/60 | at virtual target |
| cpu-alu | 41/60 | synthetic CPU stress below target |
| wram | 47/60 | synthetic WRAM stress below target |
| ppu-registers | 38/60 | synthetic PPU-register stress below target |
| dma-vram | 16/60 | heavy DMA/VRAM stress below target |
| gameplay-balanced | **61/60** | throughput is not limiting under this workload |

`61/60` must **not** be described as “better than perfect” or proof of correct cadence. It establishes that this synthetic workload is not throughput-bound in the valid ares lab. Exact temporal cadence remains a separate correctness question and ultimately requires appropriate emulator/hardware validation.

## What this currently proves

**MEASUREMENT PROOF:**

- the profiler distinguishes controlled CPU, PPU, DMA and wait-state pressure;
- the virtual frame-budget signal correlates with workload pressure;
- `gameplay-balanced` is not bottlenecked by the R4300/RSP path in the valid ares lab;
- the catastrophic prior gameplay collapse was an ares RSP-JIT laboratory artifact.

It does **not** prove:

- commercial-game performance;
- real-N64 frame rate;
- that S-CPU is the dominant bottleneck in representative software;
- that a 65C816 dynarec is already justified;
- exact SNES/N64 cadence correctness.

## Next Phase 1 step

Do not expand profiling infrastructure merely because more metrics are possible.

The synthetic controls and mixed workload have now done their main job. The next evidence should increase **representativeness or authority**: a more complex open/homebrew test workload and/or a focused real-N64 M0 milestone measurement package, chosen to answer whether the first major M1 architecture should target S-CPU, APU, PPU/RSP, memory/synchronization, or another measured cost.

Commercial ROMs may later be used locally for representativeness but must not be committed or distributed as project artifacts.
