# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## Operating rule
Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**. Preserve material measurements, hypotheses, rejections, lab limitations, exact SHA/run/artifact identity and next action. Continue from repo/artifact evidence, not chat memory.

## Gate / authority
Current milestone: **M0 / ROADMAP Phase 1 — baseline and bottleneck map**.
Canonical hierarchy: `master:docs/ROAD_TO_1_0.md` -> `ROADMAP.md` -> `PROFILING.md` / `VALIDATION.md` -> this live handoff.
Perfect target remains real-N64 native cadence, no required frameskip/frame generation, full-rate APU/audio, high base-system fidelity, broad compatibility, DSP-1 family, Super FX/2 and SA-1. N64-alone first.

Integrated master: **`ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`**; PR #9 is **MERGED-CONSUMED**.

## Valid ares lab
Isolation run `35113184294`, artifact `10453682432` proved pinned ares RSP JIT is a **LAB LIMITATION**: every RSP-JIT mode collapsed while RSP-interpreter modes progressed. Valid high-density lab is **R4300 JIT + RSP interpreter**.

**REJECTED:** R4300 JIT as cause; missing semaphore semantics; dropped semaphore `MTC0`; RSP DMA-busy explanation; accidental OAM wall as primary cause. Old RSP-JIT profiling must not drive architecture.

Valid synthetic run `35114866448`, artifact `10454678803`: idle 60/60; cpu-alu 41/60; wram 47/60; ppu-registers 38/60; dma-vram 16/60; gameplay-balanced 61/60 with 51.5% VI wait. Synthetic results are causal controls, not real-game/N64 authority.

## Gothicvania representative workload
Open workload: `donth77/snes-homebrew:gothicvania`.
Pins: final source `119496e6a2f1e53b7704712fef8cb81814f1698a`; source-art history `913ea78a3b35d3dfb62d7b76a33598b02107a2e7`; PVSnesLib 4.5.0 SHA-256 `b69ff32ada19895b7ebfe02a1e3c08a44c80bd9c8132de05f5c356f86264ce32`; Kenney font commit `9d94d3b50c68036a740115c577598fa1a02723f0`, blob `e6978d7d6f6a91ca8cdd5515e338110d9977fe69`.

Diagnostic-only game edits: `ST_TITLE -> ST_PLAY` and `padsCurrent(0) -> KEY_RIGHT`; no physics/render/audio/timing simplification.

Source-build history preserved: first clean-clone attempt exposed frozen-converter mtimes; second exposed **REJECTED** parallel `make -j` plus intentionally removed source-art inputs. Upstream explicitly says pack is recoverable from history.

Validated source run `35121473665`, artifact `10458190844`: 524288-byte ROM SHA-256 **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**. Independent run `35122086605`, artifact `10458276218`, produced byte-identical ROM and patch. **VALIDATED / MEASUREMENT PROOF:** reproducible workload.

## Stable representative ares result
Run `35122086545`, artifact `10457627853`: 1312 samples, **48/60**, APU/audio 52.7%, S-CPU 30.4%, graphics/DMA/sync 16.3%, VI wait 0.5%.
Repeat `35122958028`, artifact `10457874257`: 1320 samples, **48/60**, APU/audio 52.9%, S-CPU 30.3%, graphics/sync 16.3%, VI wait 0.45%. Normal run `35122957981` green including Mupen.

Repeat `SP_PC=0x020F` was non-interpretable because pinned ares returns random SP_PC while RSP is running; **not** a new RSP anomaly.

**SUPPORTED INTERPRETATION:** representative lab pressure is not S-CPU alone. APU/audio aggregate is largest, S-CPU a large second, graphics/sync meaningful. `APU static` includes support/I-O/synchronization around the existing JIT. ares proportions are not real-N64 proportions.

**SUPPORTED FALSIFICATION:** do not begin 65C816 dynarec merely because synthetic CPU controls were heavy. Dynarec remains a strong candidate (~30% + SA-1 leverage), but hardware must choose the first M1 wall.

## LIVE — real-N64 M0 package
Temporary ares workflow/repeat trigger were removed. Active branch: **`phase1/open-homebrew-workload`**.
Current HEAD: **`1a505fafd48a01e55904f0ce8420a977b3a9dbd4`**.

Hardware design:
- `HW_PROFILE=1` implies current statistical `PROFILE=1`; normal builds unchanged.
- Before guest/APU-JIT execution, diagnostic sets frameskip 0, APU clock 21, audio 4, precision 8.
- No flashcart-specific runtime register or USB telemetry access. Historical SC64 runtime telemetry that froze hardware is **REJECTED**.
- Timer sampler observes 60-VI `fps_native` wraps: 2 full seconds warmup, reset sampler, then five complete measured 60-VI windows.
- `S64H` header records five `fps_display` budgets/settings/sample count/RSP context; canonical `S64P` snapshot stored at save offset 0x100.
- After measurement only, cache is written back and snapshot/header are sent through standard N64 PI cartridge SRAM at `0x08000000`.
- After both writes complete, RSP halts, framebuffer becomes solid red and diagnostic intentionally freezes. **RED = capture written.**
- `scripts/hw_profile_report.py` validates/extracts; six host tests cover canonical/word-swapped saves, incomplete capture, underclock and low density.
- Source-builder CI rebuilds exact Gothicvania and packages a self-contained `.z64` plus exact ELF/map/decoder/manifest.

### HW package build history
HEAD `d3fa62dce67d273a02814e8b80ba4470bdc9d650`:
- `Build and Validate` run **`35125720591` SUCCESS**, including normal, PROFILE and Mupen smoke.
- Open Homebrew run **`35125720562`** rebuilt Gothicvania successfully; `hw-profile-package` failed only at link.
- All 29 host tests passed; `profile.S` assembled successfully.
- Link error was undefined external `fps_native` from `profile.o`.

**CAUSE:** `fps_native` already existed in `main.S` but upstream had never exported it.
**REJECTED:** hardware-profiler assembly syntax, PI path and decoder as cause.
Controlled fix `2cd2245acfecf8cf051eeb3a8d2851716015d453`: add only `.globl fps_native`; no counter logic changed.

At `2cd2245a...`:
- `Build and Validate` run **`35126221380` SUCCESS**.
- Open Homebrew run **`35126221276`**: Gothicvania source build SUCCESS; HW profiler compile/link SUCCESS. This proves the symbol export fixed the sole linker blocker.
- Packaging then failed in `Verify workload and build self-contained hardware ROM` after the compile/link. The source workload artifact exists as `10458823883`.

**CAUSE:** package hashing used `sha256sum package/*`, which also matched the `package/wrap` directory. This was a packaging-only hygiene failure, not an emulator/runtime failure.
Controlled fix `81a3fe5bdd49f845c362bb00c96aedaee2b48c42`: hash only regular package files and exclude `SHA256SUMS.txt` itself.

At `81a3fe5...`:
- `Build and Validate` run **`35126591157` SUCCESS**.
- Open Homebrew run **`35126591058` FAILED** before HW packaging because Gothicvania's pinned source build nondeterministically reran `tools/adapt_moon.py`.
- The linker completed and printed `Build finished successfully!`; the workflow failed immediately afterward when the tracked-source cleanliness assertion detected an unexpected rewrite.

**HYGIENE-BLOCKER / CAUSE:** the workload workflow tried to preserve upstream frozen conversion outputs with bulk `touch` calls. Upstream explicitly treats committed converted outputs as source-of-truth, but Git checkout mtimes are not historical and bulk touching can make one frozen generated input newer than another in the same dependency chain. In that run `res/level/sky_coldata.bin` became newer than tracked `res/moon.png`, so `adapt_moon.py` ran; in the prior green source build it did not. This is source-build mtime nondeterminism, not a Sodium64 emulation regression.

**REJECTED:** `fps_native` export, HW profile link, Gothicvania guest logic, N64 runtime, and representative profile result as causes of run `35126591058`.

### Frozen-output experiment history
Commit `f545cd5c9b34b70c23002488936fdbc0df78434c` replaced bulk mtimes with explicit GNU make `-o/--old-file` handling. Run `35135773394` failed in the new preflight because `res/level/parallax_tiles.pic` was incorrectly treated as a tracked frozen output; it is an absent/generated product. **REJECTED:** parallax generation itself as a problem.

Commit `8fb23e7c2c48bab8a907e293e9feb3ae15f39e32` removed that generated product from the freeze set. Run `35136010741` passed frozen-output preflight but failed assembling `data.asm`: over-freezing `res/hero_a.bin` skipped the recipe that also creates required ignored companion `res/hero.pal`. **REJECTED:** PVSnesLib/gfx4snes as broken. Lesson: freeze only high-level committed source-of-truth outputs, never derived leaf products whose recipes create required companions.

Commit **`1a505fafd48a01e55904f0ce8420a977b3a9dbd4`** applies that narrower policy: high-level committed outputs are explicit old-files; `.pic/.pal`, split `.bin`, stream and other low-level products rebuild normally.

**VALIDATED:** Open Homebrew run **`35136266948`** is fully green.
- Gothicvania job `104929303313` SUCCESS.
- Exact guest SHA remains **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**; patch SHA remains `c2317550ee3a1654095b462e20553432918e7d6ee85caf30efaf11ba81e3842a`.
- Source artifact: **`10462359490`**.
- HW job `104929641790` SUCCESS: all 29 host tests, HW_PROFILE compile/link, exact guest verification, self-contained wrapping, embedded guest re-extraction/hash verification, package upload.
- Hardware package artifact: **`10463745031`**, artifact ZIP SHA-256 `857c9fb0e8be88583d168c32cbe9fae5e3f1a784f536174222c488a6711b5a9f`.
- Wrapped hardware ROM SHA-256: **`081c23df1d41101abad373aa1e53b30a34287a049640bd4f349546fd6920425d`**.
- `Build and Validate` run **`35136266981` SUCCESS**.

**PACKAGE INSPECTION:** downloaded artifact contains the expected ROM/ELF/map/reporters/manifest/test instructions, and the embedded Gothicvania payload re-verifies exactly. However, two user-facing hygiene issues remain before asking Iron to test:
1. `SHA256SUMS.txt` records paths as `package/<file>` even though GitHub strips the `package/` root inside the artifact, so `sha256sum -c SHA256SUMS.txt` from the extracted artifact root fails path lookup despite correct hashes.
2. The artifact also includes temporary `wrap/` staging files because wrapping currently happens under `package/wrap`.

These are **HYGIENE-BLOCKER** only; they do not invalidate the green compile/link or ROM-content verification. Do not hand this artifact to hardware yet.

### Immediate controlled experiment
Move wrapping scratch space to `$RUNNER_TEMP` outside `package/`, generate `SHA256SUMS.txt` from inside the final artifact root using relative filenames, rerun CI, download the emitted package, and require `sha256sum -c SHA256SUMS.txt` to pass directly after extraction. Expected package should contain only intended deliverables and the same exact guest SHA; wrapped ROM may remain byte-identical if no build content changes.

Falsifier: exact guest SHA changes, HW build/package verification regresses, extracted checksums still fail, or any new runtime-related failure appears.

Do **not** start M1 dynarec before the real-hardware M0 evidence chooses the first wall.

## Resume protocol
Read this file + Road/Profiling/Validation; inspect branch HEAD and CI. Clean the package staging/checksum paths, independently verify downloaded artifact, checkpoint again, then request one focused real-N64 session only after that verification passes.
