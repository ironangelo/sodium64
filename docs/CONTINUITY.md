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
Perfect target: real-N64 native cadence, no required frameskip/frame generation, full-rate APU/audio, high CPU/PPU/DMA/HDMA/timing fidelity, broad compatibility, DSP-1 family, Super FX / Super FX 2 and SA-1. N64-alone first; cartridge assistance only after a quantified hardware-budget gap.

## Stable master
Integrated master: **`ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`**.
PR #9 is **MERGED-CONSUMED**. Integrated foundation includes workflow/baseline/statistical profiler/ares lab/synthetic matrix/Road/frame-budget correlation/gameplay-like workload.

## Valid ares decision laboratory
Isolation run `35113184294`, artifact `10453682432`:

| R4300 | RSP | frames / 60 VI |
| --- | --- | ---: |
| JIT | JIT | 0 |
| interpreter | interpreter | 60 |
| JIT | interpreter | 60 |
| interpreter | JIT | 0 |

**LAB LIMITATION:** pinned ares RSP recompiler collapses Sodium64 custom RSP microcode/synchronization.
**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP stuck in DMA wait; accidental OAM wall primary cause.
`SP_PC=0x0D90` at bad capture maps to intentional RSP `next_frame` self-halt.

Valid high-density lab: **R4300 JIT + RSP interpreter**. Do not debug ares RSP JIT further unless a Road gate requires it.

Valid synthetic/mixed replacement matrix: run `35114866448`, artifact `10454678803`, frameskip 0 / APU 21 / audio on / precision 8:
- idle 60/60;
- cpu-alu 41/60;
- wram 47/60;
- ppu-registers 38/60;
- dma-vram 16/60;
- gameplay-balanced 61/60, 51.5% VI wait, 0.3% VRAM/RSP wait.

**MEASURED:** synthetic `gameplay-balanced` has throughput headroom in valid ares lab. `61/60` is not cadence proof.
**SUPERSEDED:** old `dma-vram ~=98% PPU` interpretation.
**NOT PROVEN by synthetic matrix:** commercial performance, real-N64 FPS, representative S-CPU dominance, dynarec justification.

## Representative workload — Gothicvania
Selected `donth77/snes-homebrew` -> `gothicvania` as the open-game Phase 1 step.

Pins:
- final game source: **`119496e6a2f1e53b7704712fef8cb81814f1698a`**;
- historical CC0 source-pack input: **`913ea78a3b35d3dfb62d7b76a33598b02107a2e7`**;
- PVSnesLib 4.5.0 Linux SHA-256: **`b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`**;
- Kenney font mirror commit: `9d94d3b50c68036a740115c577598fa1a02723f0`, `Kenney Pixel.ttf` blob `e6978d7d6f6a91ca8cdd5515e338110d9977fe69` (CC0).

Why representative: real original no-chip LoROM game; Mode 1; 4800px scrolling; HDMA parallax + per-scanline color math; VRAM page streaming; hero/enemies/sprite streaming/collision; SNESMod looping music/SFX. First skeleton activates near start; spike hazards are much later.

Diagnostic-only gameplay changes:
1. initial `ST_TITLE -> ST_PLAY`;
2. gameplay `padsCurrent(0) -> KEY_RIGHT`.

Do not alter physics, enemies, renderer, HDMA, streaming, audio, collision, timing, or Sodium64 runtime to make workload easier.

### Reproducibility knowledge
Attempt 1 (`e72566dd`, run `35119197827`) failed because clean Git mtimes caused frozen converters to run.
Attempt 2 (`c7d60a98`, run `35119454457`) exposed two deeper issues: **REJECTED** parallel `make -j` for upstream hand-written dependencies, and final source tree intentionally lacks the historical source-art pack.

Upstream `968b618...` explicitly says removed CC0 pack is recoverable from Git history; `913ea78...` is last feature-complete source-pack state. Host-specific audio/font paths are handled as pinned build inputs/intermediates, not gameplay changes.

Validated source build:
- run **`35121473665` SUCCESS**, artifact **`10458190844`**;
- ROM size **524,288 bytes**;
- ROM SHA-256 **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**;
- patch SHA-256 **`c2317550ee3a1654095b462e20553432918e7d6ee85caf30efaf11ba81e3842a`**;
- exact patch contains only the two declared C edits.

Independent repeat source build run **`35122086605` SUCCESS**, artifact `10458276218`: downloaded ROM and patch are **byte-identical** to first artifact.

**VALIDATED / MEASUREMENT PROOF:** benchmark ROM is deterministic and reproducible from explicit pinned provenance.

## MEASURED — stable open-game ares profile
Temporary workflow `.github/workflows/open-homebrew-profile.yml` reuses existing sampler/reporters and is diagnostic-only; remove before merge.

### Run 1
Run **`35122086545` SUCCESS**, artifact **`10457627853`**.
Input artifact/hash verified: source artifact `10458190844`, ROM SHA `634fe02f...c17a5fff`.

State: 1,312 samples; frameskip 0; APU 21; audio 4; precision 8; R4300 JIT + RSP interpreter; RSP halted at capture (`SP_STATUS=1`, `SP_PC=0x0D98`), DMA idle.

Primary shares:
- APU static 35.4%;
- S-CPU 30.4%;
- DSP 13.6%;
- PPU 8.1%;
- DMA 5.0%;
- APU JIT 3.7%;
- VRAM/RSP wait 3.2%;
- VI wait 0.5%.

Major groups: audio/APU **52.7%**, S-CPU **30.4%**, PPU+DMA+VRAM sync **16.3%**, VI wait **0.5%**.
Virtual frame budget: **48/60**.

### Stability repeat
Repeat HEAD **`1568a8c6ab2f4d655094fcefe5c40aaba4464844`** only added inert trigger `.github/phase1-gothicvania-repeat-trigger.txt`; no Sodium64/workload/profiler changes.

Run **`35122958028` SUCCESS**, artifact **`10457874257`**.
Normal `Build and Validate` run **`35122957981` SUCCESS** including build, profile-build and Mupen smoke.

State: **1,320 samples**; frameskip 0; APU 21; audio 4; precision 8; R4300 JIT + RSP interpreter; DMA idle.

Primary shares:
- APU static **36.2%**;
- S-CPU **30.3%**;
- DSP **12.4%**;
- PPU **8.0%**;
- DMA **5.5%**;
- APU JIT **4.2%**;
- VRAM/RSP wait **2.9%**;
- VI wait **0.45%**.

Major groups: audio/APU **52.9%**, S-CPU **30.3%**, PPU+DMA+VRAM sync **16.3%**, VI wait **0.45%**.
Virtual frame budget: **48/60** again. Partial capture: 52/60 VI, 38 guest frames, queue 0.

At repeat capture `SP_STATUS=0`; pinned ares `ares/n64/rsp/io.cpp` intentionally returns **random data for SP_PC while the RSP is running**. Therefore observed `SP_PC=0x020F` is non-interpretable by design and is **not** evidence of a new RSP anomaly. The first halted-capture `0x0D98` remains valid; repeat DMA idle + stable frame/profile data support a normal running capture.

**VALIDATED / MEASUREMENT PROOF:** the Gothicvania ares result is stable across two independent runs. Exact frame budget repeated 48/60 and major-group shares changed by at most ~0.2 percentage points for the headline groups.

### Interpretation
**MEASURED:** unlike synthetic `gameplay-balanced`, representative open-game Gothicvania exposes material base-system pressure and almost no VI-wait headroom in the valid ares lab.

**SUPPORTED INTERPRETATION:** representative cost is not “S-CPU alone.” Audio/APU-related R4300 work is the largest aggregate (~53%), S-CPU is a large second (~30%), graphics/DMA/synchronization is meaningful (~16%).

**IMPORTANT:** ares proportions are not real-N64 proportions. `APU static` includes APU support/I-O/synchronization around the existing JIT; do not describe it as simple SPC700 interpreter cost.

**SUPPORTED FALSIFICATION:** a 65C816 dynarec is not justified as an automatic sole first M1 architecture from synthetic evidence. It remains a strong candidate because ~30% is substantial and has SA-1 leverage, but APU/DSP now has equally important architecture evidence that must be checked on hardware.

## RESUME HERE — REAL-N64 M0 MILESTONE PACKAGE
Active experimental branch: **`phase1/open-homebrew-workload`** at/after `1568a8c6...`.
Integrated master remains `ee86d339...` until a reviewed/cleaned PR is merged.

**Cheap M0 representativeness work is complete.** Do not add more synthetic/profile metrics merely because possible.

Immediate technical batch:
1. clean diagnostic-only branch files before merge (`open-homebrew-profile.yml`, inert repeat trigger); preserve reproducible Gothicvania workload builder/provenance and durable findings in docs/continuity;
2. prepare one focused real-N64 M0 build/package using the exact Gothicvania ROM/hash and full-rate settings;
3. the hardware session must answer whether ares ranking/deficit transfers to real N64 strongly enough to select the first M1 architecture;
4. collect only decision-relevant signals: native cadence/frame budget, audio behavior, visual/gameplay sanity, and low-overhead cost evidence feasible on hardware without turning instrumentation into the project.

Decision after hardware:
- if real N64 confirms substantial S-CPU share and enough recoverable budget, proceed to a bounded 65C816 dynarec POC;
- if audio/APU/DSP is clearly the larger actionable real-hardware cost, prioritize that architecture batch first or in tandem;
- if graphics/RSP/DMA/sync materially differs from ares, investigate that measured gap before choosing dynarec;
- if hardware evidence is ambiguous, design one discriminating experiment, not another broad tooling phase.

Do **not** start 65C816 dynarec before this milestone measurement.

## Hardware status
**Hardware milestone is now justified**, but no test should be requested until the exact build, ROM/hash, settings, procedure, observables and decision table are packaged so Iron can perform one concise session.

## Guardrails
No game-specific emulator modes. No frameskip/APU underclock/audio omission counted as performance. No endless profiler/tooling expansion. No diagnostic code merged merely because it produced knowledge. `master` remains best integrated state. Preserve rejected explanations.

## Resume protocol
1. Read this file and Road/Profiling/Validation.
2. Verify master and active branch/HEAD/CI.
3. Clean the experimental branch and persist durable profiling findings.
4. Build the real-N64 M0 package before asking Iron to test anything.
5. Maintain batch -> checkpoint cadence.
