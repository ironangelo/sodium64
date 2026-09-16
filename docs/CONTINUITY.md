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
Current HEAD: **`26545b209c7657c98ffc22cdd7a954e688ac8c07`**.

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

Commit `1a505fafd48a01e55904f0ce8420a977b3a9dbd4` applies that narrower policy: high-level committed outputs are explicit old-files; `.pic/.pal`, split `.bin`, stream and other low-level products rebuild normally.

Open Homebrew run `35136266948` was fully green and produced hardware package artifact `10463745031`, but independent package inspection found two user-facing hygiene problems: checksum paths included stripped `package/` prefixes and temporary `wrap/` staging files leaked into the artifact. Both were packaging-only; ROM/content verification itself was green.

### READY FOR HARDWARE — validated package
Commit **`26545b209c7657c98ffc22cdd7a954e688ac8c07`** moves wrap scratch space to `$RUNNER_TEMP`, emits only intended deliverables, writes artifact-root-relative checksums, and self-runs `sha256sum --check SHA256SUMS.txt` before upload.

**VALIDATED:** all gates for the M0 hardware handoff are green.
- `Build and Validate` run **`35136729624` SUCCESS**.
- Open Homebrew run **`35136729628` SUCCESS**.
- Gothicvania job **`104930862059` SUCCESS**; exact guest SHA remains **`634fe02f981880ccea7b46bdaae7191264c724e86a492f9a85dfdb60c17a5fff`**.
- Source artifact: **`10463845969`**.
- HW package job **`104931318025` SUCCESS**: all 29 host tests, HW_PROFILE compile/link, exact workload verification, embedded guest verification, artifact-root checksum self-check and upload.
- Final hardware package artifact: **`10463541468`**.
- GitHub artifact ZIP SHA-256: **`fa39d94499156a206983ffd4dc3c0771c5a6641c350c34776c5e3843dc3a9a92`**; local downloaded ZIP independently hashes identically.
- Wrapped N64 ROM SHA-256: **`081c23df1d41101abad373aa1e53b30a34287a049640bd4f349546fd6920425d`**, byte-identical to the prior green candidate because only packaging hygiene changed.
- Emulator base ROM SHA-256 recorded by manifest: `54039dca813356bd8976aa2761214520ef6460b157ada27e05ff055c126496a9`.
- Independent post-download extraction contains exactly 11 intended top-level files and **no directories/staging files**.
- Independent `sha256sum -c SHA256SUMS.txt` passes for every file after extraction.
- Independent re-extraction of the 512 KiB embedded SNES guest from offset `0x104000` hashes exactly to **`634fe02f...c17a5fff`**.

**STATUS: VALIDATED / READY FOR REAL-N64 M0 SESSION.** This does not yet validate profiler capture transport or performance on hardware; those are exactly what the next session tests.

### Immediate next action — one focused real-N64 session
Run only `sodium64-m0-gothicvania.z64` from artifact `10463541468` on the real N64/SummerCart64. Do not press controls or enter settings. Benchmark auto-enters gameplay and holds SNES Right. It performs 2 seconds warmup plus five complete 60-VI measurement windows. **Solid red screen = capture written.** After red, wait ~2 seconds, then use the normal reset/return-to-cart-menu flow so SRAM can persist; do not power off first. Recover the SRAM/save associated with this ROM and return it with a short observation of whether gameplay/video/audio looked sane before red.

Expected evidence: valid `S64H` + `S64P`, five frame-budget windows, full-rate settings, sufficient sample density and a real-N64 subsystem profile. This will decide which M1 optimization/architecture experiment moves the gate first.

Falsifiers/branches:
- No red / hang before red -> diagnose hardware-only runtime or measurement path before trusting profile.
- Red but no/invalid save -> isolate standard PI SRAM persistence/capture transport; performance remains unknown.
- Valid capture -> decode first real-N64 bottleneck map and choose M1 work from evidence.

Do **not** start M1 dynarec before the real-hardware M0 evidence chooses the first wall.

## Resume protocol
Read this file + Road/Profiling/Validation; verify master/branch/CI state. Current resume point is the single real-N64 M0 Gothicvania session using exact SHA/artifact above. Decode the returned save with the packaged `hw_profile_report.py` + exact ELF/map, checkpoint result, then choose the first M1 architecture experiment from hardware evidence.
