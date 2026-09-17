# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating rule
Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**. Preserve material measurements, hypotheses, rejections, lab limitations, exact SHA/run/artifact identity and next action. Continue from repo/artifact evidence, not chat memory.

Authority: current Iron instruction > repo/artifact evidence > canonical docs > continuity > chats/memory/inference. `master` is integrated truth; a phase branch is only a candidate until merged.

## Captain / live lab-notebook protocol
Iron delegates technical direction of Sodium64 toward the Road to 1.0 to the assistant, within Iron's current goals and constraints. The assistant should choose architecture, experiment order, implementation detail, profiling strategy, Git/CI flow and validation without asking Iron for low-level technical decisions unless a choice materially changes product scope, hardware requirements, risk or the stated destination.

**Continuity is a live scientific log, not an end-of-batch summary.** After every material result, discovery, changed hypothesis, falsification, new risk, lab limitation, meaningful CI/artifact result, branch/HEAD transition or next-action change, update this file immediately before moving on to the next technical step. Do not allow material knowledge to live only in chat until a large execution finishes. For long-running experiments, checkpoint the exact SHA/run/question and result branches before leaving the experiment running.

Transparency to Iron should expose useful technical reasoning continuously: current hypothesis; evidence; what the evidence demonstrates; what it does **not** demonstrate; rejected explanations and why; next controlled change; expected result; falsifier; and why other subsystems are not being touched yet. Do not expose or reconstruct private chain-of-thought verbatim; provide the decision-relevant reasoning and evidence instead.

Every technical batch must reduce a concrete Road-to-1.0 uncertainty. If new evidence contradicts continuity or canonical docs, repair the stale documentation rather than rationalizing around it.

## Gate / current refs
Current milestone: **M0 ACHIEVED / M1 — faster base core, APU/audio first**.
Perfect target remains real-N64 native cadence, one required SNES frame per corresponding native frame, no required frameskip/frame generation, full-rate SPC700/APU and correct audio, high CPU/PPU/DMA/HDMA/timing fidelity, broad compatibility, no per-game manual modes, DSP-1 family, Super FX/2 and SA-1. N64-alone first.

Integrated `master`: **`ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`**.
Completed M0 measurement branch: `phase1/open-homebrew-workload`; representative M0 HEAD **`89df64192d622bfa12e4bb53e0f41ceab928efe6`**.
Active M1 branch: **`phase2/apu-audio-first`**.
M1 paired ares baseline: **`c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`** (`BLOCK_SIZE=16`).
Current M1 branch HEAD: **`a758629014d0ecada6358c57eaf77c60afc80cad`** (`m1: isolate 32-byte APU JIT block test`).
Open PRs: **none** as of this checkpoint. Diagnostic/candidate work is not implicitly integrated.

**DOC DRIFT / TODO:** `master:docs/ROAD_TO_1_0.md` and `master:docs/ROADMAP.md` still carry the older pre-M0/dynarec-first framing. Newer hardware/artifact evidence below supersedes that framing. Repair those canonical docs after the current controlled APU block experiment is cleanly resolved; do not weaken the 1.0 destination.

## Valid ares decision lab
Isolation run **`35113184294`**, artifact **`10453682432`** proved pinned ares RSP JIT is a **LAB LIMITATION**: every RSP-JIT mode collapsed while RSP-interpreter modes progressed. Valid high-density lab is **R4300 JIT + RSP interpreter**.

**REJECTED:** R4300 JIT as the cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy explanation; accidental OAM wall as primary cause. Old RSP-JIT profiling must not drive architecture.

Valid synthetic control run **`35114866448`**, artifact **`10454678803`**: idle 60/60; cpu-alu 41/60; wram 47/60; ppu-registers 38/60; dma-vram 16/60; gameplay-balanced 61/60 with 51.5% VI wait. Synthetic results are causal controls, not real-game/N64 authority.

Stable representative ares M0 repeats were **48/60**: run `35122086545` artifact `10457627853` and run `35122958028` artifact `10457874257`. `SP_PC=0x020F` observations from pinned ares are non-interpretable while RSP is running and are **not** evidence of a real RSP anomaly.

## Gothicvania representative workload
Open workload: `donth77/snes-homebrew:gothicvania`.
Final source pin: `119496e6a2f1e53b7704712fef8cb81814f1698a`; source-art history `913ea78a3b35d3dfb62d7b76a33598b02107a2e7`; PVSnesLib 4.5.0 SHA-256 `b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`; Kenney font commit `9d94d3b50c68036a740115c577598fa1a02723f0`, blob `e6978d7d6f6a91ca8cdd5515e338110d9977fe69`.

Deterministic controls: `ST_TITLE -> ST_PLAY`; `padsCurrent(0) -> KEY_RIGHT`. Survivability variant additionally initializes local `playState` health to `255`; enemy/spike collision, damage, hurt/knockback, SFX, rendering, physics, streaming and audio remain active. Only death is made unreachable during the short profiling window. No Sodium64 core code is changed for survivability.

Original benchmark SHA-256: `634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`.
Survivability benchmark SHA-256: **`5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`**.
Benchmark patch SHA-256: **`ab1ec83925571e916be9ae0a3abf3d2bb84b5f9efb1aae9fd2ac608ecc0f0bc9`**.

Source-build hygiene knowledge:
- **REJECTED:** parallel make/PVSnesLib as root cause of frozen-source failures.
- **REJECTED:** parallax generation itself as a problem.
- **REJECTED:** gfx4snes/PVSnesLib as broken.
- Actual cause: checkout-mtime interaction with upstream committed/frozen conversion outputs. Freeze only high-level committed source-of-truth outputs; let low-level products/companions rebuild.
- Package scratch/checksum-path leaks were packaging-only hygiene and did not change ROM/runtime.

## Real-N64 M0 measurement proof
`HW_PROFILE=1` implies `PROFILE=1`; normal builds unchanged. Diagnostic forces frameskip 0, APU clock 21, audio 4, precision 8. Sampler uses 2 complete 60-VI warmup seconds, then five complete measured 60-VI windows. `S64H` stores frame budgets/settings/sample count/RSP context and canonical `S64P` lives at save offset 0x100; after measurement, data is persisted through standard N64 PI SRAM. Historical SummerCart runtime-register telemetry that froze hardware is **REJECTED**.

First hardware capture proved transport/profiler end-to-end but its aggregate is **SUPERSEDED FOR ARCHITECTURE DECISION** because later windows occurred after `GAME OVER`. Preserve it as transport proof only: save `sodium64-m0-gothicvania.sav`, SHA-256 `c9862cc3ec821a783e2a79f38f01b4e4fd5377d9f8683a05eb429122a1bdaf2a`, 3580 samples, frame windows 48/60, 49/60, 52/60, 60/60, 60/60.

### M0 closure — representative real-N64 survivability capture
Exact candidate:
- HEAD **`89df64192d622bfa12e4bb53e0f41ceab928efe6`**.
- Open Homebrew run **`35145447113` SUCCESS**; source artifact `10466504920`; hardware package artifact **`10467585906`**.
- Build and Validate run **`35145447039` SUCCESS**.
- artifact ZIP SHA-256 `db187230e8728c22b5acebbeabd99489af538994c79eece0a6d4f2a054415086`.
- wrapped N64 ROM SHA-256 `7bb79d25168a73a9e539a1ced17c0e4073f3c8fb321ed7552db7a48a64ed217f`.
- emulator base ROM SHA-256 `54039dca813356bd8976aa2761214520ef6460b157ada27e05ff055c126496a9`.

Returned save `sodium64-m0-gothicvania-survivability.sav`: 32768 bytes, SHA-256 **`3316bd99dc26224050153c5a10c167b0e0b520aa9e4b85699b8ab45911f1f395`**. Complete canonical `S64H`/`S64P`; settings frameskip 0, APU clock 21, audio 4, precision 8; 3581 valid samples; queue 0; SP DMA full/busy 0/0; frame windows **48/60, 49/60, 48/60, 50/60, 50/60**, mean **49.0/60**. Hardware video confirms active gameplay through measurement with no GAME OVER before the solid-red completion marker.

Representative R4300 sample split:
- APU/SPC700 static 24.91%
- APU JIT generated 19.18%
- DSP/audio 17.73%
- **combined APU/audio 61.83%**
- S-CPU interpreter 22.12%
- PPU/events/frame prep 7.99%
- DMA/HDMA 6.67%
- RSP/VRAM semaphore wait 1.31%
- frame/VI wait 0 samples

Hot regions include APU JIT generated 19.18%, `apu_execute` 11.56%, `cpu_execute` 8.99%, `apu_read8` 6.03%, `skip_sample` 4.05%, `get_pitch` 3.52%, `apu_write8` 2.88%, `load_sample` 2.40%.

**MEASURED / M0 ACHIEVED:** representative real N64 is stably throughput-bound near 49 completed SNES frames per 60 VI with no frameskip, full-rate APU and active audio, essentially no VI idle headroom.

**SUPPORTED INTERPRETATION:** from 49/60 to 60/60 requires roughly 18.3% less total host time/frame if cost scales approximately linearly. APU/audio owns 61.83%, so closing the whole gap only there would require roughly 29.7% reduction of that aggregate. S-CPU owns 22.12%, so closing it only there would require roughly 82.9% reduction of the whole S-CPU bucket. Therefore hardware evidence rejects a 65C816 dynarec as the *first* M1 attack. Dynarec remains strategically valuable later, especially for base-core work and SA-1 leverage.

## M1 paired ares baseline — 16-byte APU JIT blocks
**MEASURED / MEASUREMENT PROOF:** `phase2/apu-audio-first` at **`c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`** restores the exact survivability input and valid ares lab.

- Build and Validate run **`35148379354` SUCCESS**.
- Open Homebrew Ares Profile run **`35148379400` SUCCESS**.
- profiling artifact **`10467972587`**, digest `5471854958404c63bba8ee70ae5ead236f02b220881a4b8dfeaee60cdcd559a4`.
- exact guest input SHA-256 **`5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`**.
- settings: frameskip 0, APU clock 21, audio 4, precision 8; pinned ares R4300 JIT + RSP interpreter.
- **2000 valid samples**.
- last complete virtual frame budget: **44/60**; partial state `fps_native=48`, `fps_emulate=39`, queue 1.
- APU static 36.60%, APU JIT 3.30%, DSP 14.50% => combined APU/audio **54.40%**.
- S-CPU 30.85%, PPU/events 7.45%, DMA/HDMA 4.40%, RSP/VRAM wait 2.55%, VI wait 0.35%.
- `apu_execute` 13.10%; `cpu_execute` 15.85%; `apu_read8` 2.90%.

This is the local comparison baseline only; real N64 remains performance authority.

## M1 experiment 1 — original 32-byte candidate was confounded
Branch SHA **`3b39523c637ac5d076ddfb3714c6023e8d1106f4`** was intended to test `BLOCK_SIZE 16 -> 32`.

CI/artifacts:
- Build and Validate run **`35152788659` SUCCESS**: normal build, profiling build and Mupen emulator smoke all passed.
- Open Homebrew Ares Profile run **`35152788588` SUCCESS** (latest successful attempt 3).
- latest profile artifact **`10470457219`**, digest `d23787bf0dc60de8ce8718b824f83dc38e69d0b1939a47152b6089ab1c8577f0`.
- preceding same-SHA profile artifact **`10470355647`**, digest `4a98d90f9ebcbb213db7804dd48027a40d9de51894d17740b56bbc759dcad1b8`.

Observed same-SHA candidate results:
- repeat A: **48/60**, 1183 valid samples; APU static 32.54%, JIT 4.14%, DSP 12.93% => APU/audio 49.61%; `apu_execute` 11.07%; VI wait 0.34%.
- repeat B: **48/60**, 915 valid samples; APU static 34.86%, JIT 5.57%, DSP 13.22% => APU/audio 53.65%; `apu_execute` 11.91%; VI wait 0%.
- both retain frameskip 0, APU clock 21, audio 4, precision 8 and queue 0 at capture.

**MEASURED:** this SHA repeatedly reports a 48/60 complete virtual window versus the 16-byte baseline's 44/60. That is a promising signal, but it is **not causal evidence for 32-byte blocks**.

**EXPERIMENTAL CONFOUND / SUPERSEDED CANDIDATE:** compared directly with `c55b6b...`, commit `3b395...` changes `BLOCK_SIZE`, reformats license text and materially changes runtime layout macros in `src/defines.h`: `TEXREC_OFS` moves from `SHIFT_TABLE+0x8` to `+0x4`, shifting `FILLREC_MASK`, `LDBLK_BITS`, and `MODE7_MASK` four bytes earlier; `PRIO_CHECKS` changes from `MODE7_MASK+0x4` to `+0x8`. Therefore its 44->48 movement cannot be attributed to APU block size. This candidate is retained only as historical evidence and must not drive architecture or hardware testing.

The lower sample counts (915/1183 versus baseline 2000) also make percentage composition noisier. Frame-budget repetition is stronger evidence than the exact subsystem-share deltas, but ares remains only a lab.

## M1 experiment 1b — clean 32-byte candidate
**IMPLEMENTED / CONTROLLED EXPERIMENT READY:** active branch HEAD **`a758629014d0ecada6358c57eaf77c60afc80cad`** restores `src/defines.h` to the exact `c55b6b...` baseline content except for `#define BLOCK_SIZE 16 -> 32`.

Direct compare `c55b6b... -> a758629...` reports exactly **one modified file (`src/defines.h`), 1 addition, 1 deletion**. The license text and all runtime layout macros/offsets are restored to baseline. This removes the known confound before performance interpretation.

**HYPOTHESIS:** increasing the maximum APU JIT block from 16 to 32 opcode bytes reduces block-boundary/dispatch overhead enough to produce a reproducible improvement on the representative workload.

**What the clean diff proves:** any reproducible behavioral/performance delta against `c55b6b...` can now be attributed to the block-size change at source level, subject to the known ares lab limitations and run noise.

**What it does not prove:** no performance gain has yet been measured for this clean SHA; it does not establish real-N64 speed, audio correctness, SPC700 timing correctness or broad compatibility.

**Falsifier:** if the clean candidate returns to baseline-like throughput, regresses, or shows runtime/timing/correctness anomalies, the earlier 48/60 signal was not safely attributable to 32-byte blocks and this path should be rejected or bounded further.

## Immediate next action / RESUME HERE
1. Let Build and Validate plus Open Homebrew Ares Profile execute for exact clean candidate **`a758629014d0ecada6358c57eaf77c60afc80cad`** on the unchanged Gothicvania survivability ROM/settings and valid ares lab mode.
2. Before interpreting subsystem percentages, verify build/smoke success, exact guest SHA/settings, complete virtual frame budget, sample density and runtime state.
3. Compare clean32 first against baseline `c55b6b...` (44/60, 2000 samples), then use `3b395...` only as historical/confounded context. Compare `apu_execute`, generated-JIT/static/DSP aggregate, S-CPU/PPU/DMA and VI wait.
4. If clean32 reproduces a material gain without lower-level/runtime regression, repeat the same-SHA profile to separate signal from run noise; then checkpoint. Do not request hardware or merge solely from one ares run.
5. If clean32 is neutral/negative or semantically suspicious, mark 32-byte granularity **REJECTED**, restore 16 and move to the next bounded measured APU path (`apu_read8`/`apu_write8` specialization, then DSP inner-loop work if warranted).
6. Once experiment 1b is cleanly resolved, repair `master` Road/Roadmap to reflect M0 closure and evidence-driven APU/audio-first M1. Before merge/hardware, explicitly assess APU/DSP interleave and audio-correctness risk.
7. No second emulator or unbounded JIT/tooling project. Every batch reduces a concrete Road-to-1.0 uncertainty.

Resume summary: M0 is closed by real-hardware save SHA `3316bd99...` at 48/49/48/50/50 with 3581 samples, APU/audio 61.83%, S-CPU 22.12%, no VI wait. M1 baseline `c55b6b...` is 44/60 in the valid ares lab. Original `3b395...` repeated 48/60 but is **SUPERSEDED as a causal candidate** because of unrelated layout changes. Clean candidate `a758629...` now differs from baseline only by `BLOCK_SIZE 16->32`. **Next move is CI/profile on that exact SHA, then evidence-based accept/reject.**