# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating rule

Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**.

Checkpoint whenever branch/PR/HEAD, measured result, interpretation, rejected cause, lab limitation, next experiment, long-running CI experiment, hardware need, merge/reject/supersede, or Road/phase direction changes.

Do not rely on chat history or hidden reasoning. A new session must continue from this file + referenced repo/CI evidence.

## Project hierarchy

1. `master:docs/ROAD_TO_1_0.md` = destination / gates.
2. `master:docs/ROADMAP.md` = technical route.
3. `master:docs/PROFILING.md` = measurement methodology/limits.
4. `master:docs/VALIDATION.md` = validation authority.
5. `continuity:docs/CONTINUITY.md` = current position / live investigation.

Current milestone: **M0 / ROADMAP Phase 1 — baseline and bottleneck map**.

Perfect target remains real-N64 native cadence, no required frameskip/frame generation, full-rate APU/audio, high CPU/PPU/DMA/HDMA/timing fidelity, broad compatibility, DSP-1 family, Super FX / Super FX 2 and SA-1. N64-alone first; cartridge assistance only after a quantified hardware-budget gap.

## Stable master

Master before active PR: `798ebcb9969d94eda3eba4592eae2792d6304cb5`.

Integrated: PR #1 foundation, #2 baseline, #3 statistical profiler, #4 branch CI, #5 ares GDB profiling, #6 synthetic matrix, #7 Road to 1.0, #8 virtual-N64 frame-budget correlation.

Leading future hypothesis remains 65C816 -> R4300 MIPS dynarec, but **do not start M1 merely from CPU-heavy synthetic controls**.

## RESUME HERE — PR #9

PR: `#9 Phase 1: add balanced gameplay-like profiling workload`

- branch: `phase1/gameplay-mixed-workload`
- base: master `798ebcb9969d94eda3eba4592eae2792d6304cb5`
- current HEAD: `2fbd83d6a2491e2a663b21f545fff5b8323aa50f`
- state: **OPEN / mergeable / NOT MERGED**
- do **not** merge this HEAD: it contains temporary diagnostic workflow `.github/workflows/ares-recompiler-isolation.yml`.

`gameplay-balanced` is a cleaned deterministic game-shaped workload: `WAI`/NMI pacing, bounded CPU/WRAM logic, bounded OAM/VRAM/CGRAM work, BG1+OBJ enabled, one visible sprite, remaining sprites hidden, frameskip 0, full-rate APU (21) with JIT invalidation, audio enabled.

## MEASUREMENT PROOF — ares CPU/RSP JIT isolation

Diagnostic run: **`35113184294`** on HEAD `2fbd83d6a2491e2a663b21f545fff5b8323aa50f`.

Artifact: **`sodium64-ares-recompiler-isolation`**, artifact ID **`10453682432`**.

Same Sodium64 profiling build, same cleaned `gameplay-balanced` ROM, same settings for all modes.

| ares mode | samples | frames / 60 VI | SP_STATUS | DMA busy/full | SP_PC | result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| CPU JIT ON / RSP JIT ON | 3583 | **0/60** | 1 | 0 / 0 | `0x0D90` | collapsed |
| CPU JIT OFF / RSP JIT OFF | 1242 | **60/60** | 1 | 0 / 0 | `0x0D98` | good |
| CPU JIT ON / RSP JIT OFF | 2477 | **60/60** | 1 | 0 / 0 | `0x0D98` | good |
| CPU JIT OFF / RSP JIT ON | 1872 | **0/60** | 1 | 0 / 0 | `0x0D90` | collapsed |

Both modes with **RSP JIT ON** sampled **100% in `write_vmdatal` -> RSP/VRAM semaphore wait**. Both modes with **RSP JIT OFF** progressed normally.

### Interpretation

**MEASURED:** the catastrophic gameplay collapse follows the **ares RSP recompiler** independently of the R4300 recompiler.

**REJECTED:** R4300 JIT as the cause of this collapse. CPU JIT ON + RSP interpreter reaches 60/60.

**LAB LIMITATION:** the pinned ares RSP recompiler is not valid as a performance/synchronization laboratory for Sodium64's custom RSP microcode under this workload.

Do **not** attribute the previous 0/60 or 1/60 recompiler gameplay result to Sodium64 or real N64 hardware.

The useful ares profiling configuration going forward is therefore **R4300 recompiler ON + RSP interpreter OFF/JIT disabled**. This mode retained high sample density (2477 samples in the diagnostic run) while producing 60/60.

## SP_PC / semaphore finding

Exact profiling ELF disassembly maps `SP_PC=0x0D90` to Sodium64 RSP label `next_frame`:

- `li t0, 2`;
- `mtc0 t0, SP_STATUS` — intentional self-halt;
- branch back toward `draw_frame` after restart.

Therefore **REJECTED:** “RSP is stuck in DMA wait.” At bad capture the RSP has reached intentional end-of-frame halt; DMA is idle while R4300 spins on VRAM semaphore.

This interleaving is produced by the ares RSP JIT path; interpreter RSP does not reproduce the collapse.

## Other rejected / superseded explanations

Do not rediscover these:

- **REJECTED:** ares lacks SP semaphore semantics. It implements them.
- **REJECTED:** ares RSP JIT simply drops semaphore-clearing `MTC0`; its emitted MTC0 calls the same `RSP::MTC0` helper as interpreter.
- **REJECTED as simple explanation:** CPU polling trivially starves RSP; `CPU::synchronize()` explicitly advances `rsp.main()`.
- **REJECTED:** accidental OAM/sprite wall as primary cause; clean OAM did not remove JIT collapse.
- **SUPERSEDED:** old `dma-vram ~=98% PPU` interpretation. Most samples were actually `write_vmdatal` semaphore wait; profiler now classifies `RSP/VRAM semaphore wait` separately.
- **SOURCE FACT:** Sodium64 RSP copies 64 KiB VRAM in synchronous 1 KiB DMA blocks at frame start, then clears semaphore.
- **SOURCE FACT:** `fps_display` represents completed SNES frames over a complete 60-VI interval.

## Immediate next batch

1. Remove temporary `.github/workflows/ares-recompiler-isolation.yml` from PR #9 before merge.
2. Adjust the normal ares profiling laboratory minimally so the pinned ares build uses **R4300 JIT + RSP interpreter** rather than the known-bad RSP JIT. Keep this explicitly documented as a lab workaround, not a Sodium64 change.
3. Re-run the existing workload matrix + cleaned `gameplay-balanced` under that configuration.
4. Verify `gameplay-balanced` remains ~60/60 and collect its representative subsystem distribution at useful sample density.
5. Re-evaluate earlier PPU/DMA synthetic numbers under the valid RSP-interpreter lab configuration; supersede any numbers materially changed by the old RSP-JIT limitation.
6. Update `PROFILING.md` with the ares RSP-JIT `LAB LIMITATION` only after the replacement run is validated.
7. Then decide whether Phase 1 has enough representative emulator evidence for a real-N64 M0 milestone package or needs one more workload.

Do not spend another branch debugging ares RSP JIT internals unless it becomes necessary for a Road gate. The 2x2 already answered the Sodium64 decision question.

## Hardware status

**No real-N64 request yet.** First rebuild the emulator-lab evidence using the valid CPU-JIT/RSP-interpreter configuration. Then decide whether hardware is the next authority needed.

## Guardrails

- No game-specific modes as strategy.
- No frameskip/APU underclock/audio omission counted as performance.
- No endless profiler/tooling expansion.
- No diagnostic code merged merely because it produced knowledge.
- `master` remains best integrated state.
- Important rejected explanations survive here.

## Resume protocol

1. Read this file.
2. Inspect PR #9 and current HEAD.
3. If temporary isolation workflow still exists, remove it only after preserving run `35113184294` result.
4. Continue with valid-lab R4300-JIT + RSP-interpreter matrix.
5. Read Road/Roadmap and Profiling/Validation before architecture decisions.
6. Repair this file immediately if repo/CI evidence is newer.
