# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

## RESUME HERE — current audited state (2026-09-21 UTC)

- **2026-09-21 E1a guest-control batch 34 — pinned ares pixel-level Z-test explanation pre-rejected:** source review of pinned paraLLEl-RDP `depth_test.h`/`memory_interfacing.h` shows that when `DEPTH_TEST/Z_COMPARE` is false (as in E1), `depth_test()` sets `depth_pass=true` unconditionally; normal `depth_blend()` performs `write_color(...)` first and only then performs Z writeback when `z_update` is enabled. Therefore, if control run `35609056650` restores full color by clearing primitive-depth/Z-update bits, the mechanism is **not** an ordinary depth-test rejection. Follow-up must inspect state/surface/coherency or command interaction rather than claiming fragments failed Z compare.

- **2026-09-21 E1a guest-control batch 33 — no-Z color control Build/Validate GREEN:** exact control head `ffee373fcecbc032b9f8b7776fe0ddd26cd8bb86`, standard **Build and Validate run `35609056653 SUCCESS`**, including normal build, PROFILE build and Mupen/LLE emulator smoke. Therefore restoring master OtherModes while retaining all proof capture/fence machinery causes no generic build/boot regression. Semantic run **`35609056650`** remains in pinned-ares build at this checkpoint; its framebuffer artifact is the pending discriminator, while its unchanged Z classifier is expected to report failure because depth update is intentionally disabled.

- **2026-09-21 E1a guest-control batch 32 — one-variable no-Z color control IMPLEMENTED:** proof branch advanced to **`ffee373fcecbc032b9f8b7776fe0ddd26cd8bb86`**. Exactly one runtime dword changed: `rdp_init` OtherModes restored from E1 `0x2F0088FF00040025` to integrated/master `0x2F0088FF00040001`. This disables only primitive-depth selection (bit2) and depth update (bit5); the pre-existing alpha compare bit remains unchanged. Guest ROM, regular tile path, Set Z/Set Prim commands, end-frame Sync Full/marker, deterministic breakpoint capture and section diagnostics remain identical. **Controlled discriminator:** if framebuffer expands from the reproducible 56 black pixels to the intended full checkerboard, E1 depth state is causally responsible for color corruption; if it remains 56, Z state is exonerated and next test targets repeated-tile/render behavior. Existing Z classifier is expected to fail in this control because no depth updates should occur; framebuffer artifact, not workflow conclusion, is the authority.

- **2026-09-21 E1a guest-control batch 31 — section-state cause REJECTED by stable artifact:** exact diagnostic head `ada4d6f799bf40e5ff2f8d14182e0d7d28bfb11f`; Build/Validate **`35607852835 SUCCESS`** including Mupen/LLE smoke. Semantic diagnostic **`35607852747 FAILURE`** only because the unchanged Z classifier still fails; evidence artifact **`10642649811`** is valid. At the same deterministic second RSP-halted boundary, both section queues have active record #0 `BG1SC=0`, `BG_MODE=0`, `BGNBA=1`, `TM=1`, `STAT_FLAGS=0x40` (OAM dirty only; force-blank 0), `SPLIT_LINE=224`. Since RSP initializes `k1=0`, consumes record #0 and then exits when `k1==FRAME_END(224)`, later stale records are not rendered. Thus **REJECT** section-queue/force-blank/TM truncation as the cause of the 16×7 visible checkerboard. Diagnostic did not perturb behavior: framebuffer SHA256 remains `d593f8b68fb074e8c7d6b1fbdd5d55c5d9ff7217c3907ca8e50da4d7a355ae18`; depth SHA256 remains `12631c951e33b50f8c64f192b165d330bf1ee216ffd92da5417d274b83618c9a`. **Next discriminator:** keep the exact ROM and all capture/fence machinery, but restore only RDP OtherModes from proof `0x...0025` to integrated/master `0x...0001` (disabling primitive-depth selection + depth update while leaving existing alpha compare unchanged). If full checkerboard returns, E1 Z state itself corrupts color draw; if 56 pixels remain, move downstream to regular repeated-tile/render control rather than Z.

- **2026-09-21 E1a guest-control batch 30 — section-queue artifact capture IMPLEMENTED:** proof branch advanced to **`ada4d6f799bf40e5ff2f8d14182e0d7d28bfb11f`**. Only `scripts/gate_c_h_comp_e1_z_tag_capture_n64.py` changed; guest, RSP renderer, Z state and classifier semantics are unchanged. At the existing second RSP-halted/DP-idle breakpoint the harness now captures first 16×64-byte records from fixed `SECTION_QUEUE1=0xA016C600` and `SECTION_QUEUE2=0xA0171600`, saves both raw binaries, and decodes per record `BGNBA@+0x10`, `BG1SC@+0x2A`, `TM@+0x3A`, `BG_MODE@+0x3D`, `STAT_FLAGS@+0x3E`, `SPLIT_LINE@+0x3F` into `result.json`. **Purpose:** determine whether the stable rendered queue actually restricts BG1/force-blank state to the first ~7 scanlines before changing the guest. Any semantic run from this head is diagnostic even if the old Z classifier remains red.

- **2026-09-21 E1a guest-control batch 29 — diagnostic discriminator chosen before code change:** current proof head remains `d2c19ae1...`; no source change yet. Generator register/VRAM setup is internally coherent (Mode0, BG1SC=0, BG12NBA=1, VMAIN=0x80, 2 KiB zero tilemap at VRAM $0000, 16-byte tile0 at $1000, TM=1). The observed exact 7-scanline height strongly implicates section state, while the exact 16-pixel width could also implicate repeated-tile fast path. **Next controlled measurement:** do not alter guest or Z. Extend the existing frame-coherent artifact to dump the first 16 records of both fixed section queues (`SECTION_QUEUE1=0xA016C600`, `SECTION_QUEUE2=0xA0171600`). Each 64-byte record has `TM@+58`, `BG_MODE@+61`, `STAT_FLAGS@+62`, `SPLIT_LINE@+63`; also decode BG1SC/BGNBA. If the rendered/stable queue shows TM=1 through full frame bounds, section-state explanation is rejected and next control will alternate tile IDs to bypass `skip_upload`; if TM/blank changes at line 7, fix the guest initialization epoch first.

- **2026-09-21 E1a block-end checkpoint — capture authority FIXED; guest visual control now the blocker:** integrated truth remains `master@5b7134930a0ca859f6aa24e54102de116948e3ed`; proof branch **`phase4/gate-c-h-comp-e1-z-tag-proof@d2c19ae1f41b71531e4460d438f6935911026481`**; no master/PR merge. Exact Build/Validate `35605068047 SUCCESS`. Frame-coherent semantic run **`35605068290 FAILURE`**, evidence artifact **`10641414443`**, is authoritative for current E1a and proves the new harness works: exact ELF breakpoint `0x8000AAF4`, two RSP-halted boundaries, one fresh guest frame, DP busy bits clear, exact completed framebuffer identity distinct from display pointer. Yet new framebuffer and depth are byte-for-byte identical to prior run, so REJECT “mid-frame capture caused the 56-pixel checkerboard.” Current deterministic guest/runtime yields only a 16×7 checkerboard fragment (56 opaque-black pixels) on otherwise backdrop-filled active area; therefore E1a cannot yet prove transparent holes across the intended full BG. Z evidence remains strong but bounded: guards intact, only expected encoded `0x0C00`/sentinel values, active 256×224 exactly tagged. Source also supports that Cycle1 backdrop can inherit persistent primitive depth, but this is not yet dynamically isolated because the guest color control is wrong. **Immediate next action on resume:** do NOT implement E1b or color-math kernel; first build the smallest guest/render control that demonstrates a full active-area repeated BG pattern under the existing regular tile path, inspecting initial VRAM dirty/cache semantics and tilemap/tile setup. Once the color control is valid, rerun E1a; only then, if backdrop depth remains, give backdrop a distinct primitive tag (`0x0800 -> stored 0x0400`) and prove BG opaque texels overwrite it while transparent texels preserve it. This block's corrected knowledge and discarded capture-race explanation must be preserved.

- **2026-09-21 E1a batch 28 — frame-coherent rerun falsifies “mid-frame capture caused the 56-pixel guest pattern”; prior interpretation corrected:** exact head `d2c19ae1...`, semantic run **`35605068290`**, job `106350146689`, reached both deterministic breakpoints successfully and failed only the existing classifier. Capture authority is now explicit: `capture_ready=0x8000AAF4`, first clean-epoch breakpoint hit, single-step hit, second fenced breakpoint hit; `baseline_counter=10`, `guest_counter=11` (`delta=1`), `SP_STATUS=1` (HALT), `DP_STATUS=0x81` with busy mask `0x70==0`, marker correct, exact completed framebuffer from RSP marker `0xA00F2300`, CPU display pointer separately `0xA0113000`. Artifact **`10641414443`** uploaded. Crucially, its `framebuffer.rgba5551` SHA256 is **identical** to prior artifact `10620176581` (`d593f8b6...`), and `depth.bin` is also byte-identical (`12631c95...`): framebuffer remains 57,288 backdrop + 9,856 border + only 56 checkerboard-black pixels; depth remains exactly 57,344×`0x0C00` + 9,856×sentinel. Therefore **REJECT** the earlier supported interpretation that those 56 pixels were caused by a mid-next-frame host capture. Batch16's measurement flaw was real in principle and is now repaired, but it did not cause this observed topology. **New blocker:** the deterministic guest/runtime itself produces only the tiny 16×7 checkerboard region, so current color↔Z classifier cannot prove transparent-hole semantics. Next: isolate guest BG setup/render path (VRAM tilemap/tile base, scroll/tile iteration/cache semantics) with a control that proves full active-area checkerboard before changing Z/background tagging. The source-supported backdrop inherited-Z mechanism remains plausible but is not yet dynamically isolated because the guest color control is wrong.

- **2026-09-21 E1a batch 27 — proof-branch hygiene reverified:** compare `master@5b713493...` → `phase4/gate-c-h-comp-e1-z-tag-proof@d2c19ae1...` is ahead by 9 commits / behind 0 and still changes only four files: added `.github/workflows/gate-c-h-comp-e1-z-tag.yml`, added deterministic guest generator, added E1 capture/classifier, and validation-only `src/rsp_main.S`. No CPU/PPU source, master workflow, integrated branch or unrelated subsystem change has entered the proof. **Decision:** keep this branch disposable and architecture-only; do not merge it as production code merely because it generates evidence.

- **2026-09-21 E1a batch 26 — breakpoint/step harness semantics SOURCE-VALIDATED against pinned ares GDB server:** `Z0` stores logical breakpoint PCs (hardware/software treated equivalently) and invokes N64 recompiler cache invalidation on insertion; it does not patch guest instruction bytes. `reportPC` halts when current PC matches the breakpoint. `s` sets `singleStepActive`, resumes, allows the current instruction to execute, then forces the following PC to halt; therefore E1a's `remove breakpoint -> single-step -> reinsert behind current PC -> continue` sequence advances off the first frame boundary and cannot immediately retrigger the same breakpoint. Ares desktop loop also stops emulation while GDB `isHalted()`, confirming polling for producer progress while stopped would have been invalid. **MEASUREMENT PROOF:** the new boundary-capture method is source-grounded in the exact pinned debugger implementation.

- **2026-09-21 E1a batch 25 — backdrop inherited-Z mechanism SOURCE-SUPPORTED end-to-end:** Sodium64 `rdp_fill` uses `Set Primitive Color` then combine `0x3C080E10001D86C3` and `Fill Rectangle`, finally restores texture combine. Decoding the single-cycle combiner against pinned ares enums gives RGB `(Combined-Combined)*Zero + Primitive` and alpha `(CombinedAlpha-CombinedAlpha)*Zero + PrimitiveAlpha`; Sodium64 loads primitive alpha `0xFF`. With global alpha threshold `0xFF`, backdrop passes alpha-test (`alpha_reference < threshold` rejects only lower values). Because OtherModes remains Cycle1 + primitive-depth + depth-update and ares `draw_flat_primitive -> draw_shaded_primitive` uses persistent `constants.prim_depth`, the next frame's backdrop has a complete source-level route to write inherited BG depth. **SUPPORTED HYPOTHESIS, still awaiting dynamic separation:** if frame-coherent run shows full checkerboard colors but `57,344` active `0x0C00` tags, this mechanism is confirmed strongly enough to justify the next controlled distinct-backdrop-tag proof.

- **2026-09-21 E1a batch 24 — prior partial framebuffer topology quantifies the race:** raw artifact `10620176581` was reclassified by coordinates, not just histogram. Its 56 opaque-black pixels are exactly seven checkerboard rows across a 16-pixel span: y=`8..14`, x=`12..27`, 8 alternating black pixels per row (56 total). This is the start of the expected tiled checkerboard at the active-area origin, not a random alpha/TLUT pattern. **SUPPORTED INTERPRETATION:** the earlier framebuffer was captured after only ~2 tile-columns × 7 scanlines of the next render had replaced backdrop, independently corroborating batch16's frame-coherency defect. This does not itself classify the shared Z buffer, which is why exact-head between-frame run `35605068290` remains necessary.

- **2026-09-21 E1a batch 23 — exact artifact confirms breakpoint identity/layout:** exact-head Build artifact `10641637625` for `d2c19ae1...` was inspected directly. ELF symbols: `rsp_wait=0x8000AAE4`, therefore workflow-derived capture PC is **`0x8000AAF4`**; `menu_return=0x8000AB0C`, CPU global `framebuffer=0x800686A0`, guest WRAM base `wram=0x80071000`. Linker `end=0x800B9E20`, unchanged from previous proof build. This independently confirms the frame-boundary breakpoint is exactly the first instruction after the four-instruction `rsp_wait` loop and that the proof changes did not move the previously validated RDRAM scratch layout.

- **2026-09-21 E1a batch 22 — precommitted frame-coherent signatures:** deterministic guest active region is exactly `256×224 = 57,344` pixels with 50/50 checkerboard, plus `280×240 - 256×224 = 9,856` border pixels. Therefore a correct completed framebuffer must contain **28,672 opaque-black `0x0001` + 28,672 visible-backdrop `0x8001` + 9,856 zero border**. Two depth signatures are predeclared before seeing rerun output: **alpha-presence contract without backdrop depth** → `0x0C00 tag=28,672`, `0x55AA sentinel=38,528`; **persistent primitive-depth backdrop inheritance** → `0x0C00 tag=57,344`, `0x55AA sentinel=9,856` while framebuffer still shows the full 50/50 checkerboard. Any other topology must be separately classified rather than forced into either explanation.

- **2026-09-21 E1a batch 21 — frame-coherent proof Build/Validate GREEN:** exact head `d2c19ae1f41b71531e4460d438f6935911026481`, standard **Build and Validate run `35605068047 SUCCESS`**: normal build, PROFILE build and pinned Mupen/LLE emulator smoke all succeeded (`update-release` skipped). Thus the 8-byte RSP marker and breakpoint-capable harness/workflow introduce no generic build/boot/smoke regression. Semantic run `35605068290` has already passed guest generation, exact runtime build, wrapping and exact-ELF `rsp_wait+0x10` resolution; it remains in pinned-ares build at this checkpoint. Only that semantic run can decide the current E1a discriminator.

- **2026-09-21 E1a batch 20 — backdrop-Z inheritance HYPOTHESIS source-supported, intentionally not patched yet:** proof OtherModes `0x2F0088FF00040025` has CycleType bits `(word0>>20)&3 == 0` = Cycle1, so Sodium64's `Fill Rectangle` backdrop command is **not** in special RDP Fill cycle. Pinned ares `op_fill_rectangle` calls `draw_flat_primitive`, which calls ordinary `draw_shaded_primitive`; when `constants.use_prim_depth` and `DEPTH_UPDATE` are enabled, ordinary draw setup uses persistent `constants.prim_depth` and marks depth write pending. E1 proof sets primitive depth `0x1800` for BG and never resets it before the following frame's backdrop. Therefore a later Cycle1 backdrop can plausibly inherit BG tag and stamp `0x0C00` across the whole active area. This exactly predicts the prior 256×224 uniform-Z topology, but remains **HYPOTHESIS** because prior capture was not frame-coherent. Do not patch it before exact-head frame-boundary run `35605068290`; that run cleanly separates capture race from persistent backdrop-depth state.

- **2026-09-21 E1a batch 19 — frame-coherent proof head complete and DISPATCHED:** validation branch head **`d2c19ae1f41b71531e4460d438f6935911026481`** now contains the full capture-authority repair: RSP publishes exact completed framebuffer in 8-byte fenced status; host uses ares software breakpoint at exact ELF `rsp_wait+0x10`, initializes scratch only at first RSP-halted/DP-idle boundary, single-steps past the breakpoint, and captures only at the next RSP-halted/DP-idle boundary with fresh guest counter/marker. Workflow derives `rsp_wait` from matching ELF and passes `CAPTURE_READY_ADDR`; no address is build-hardcoded. Exact-head runs: **Build/Validate `35605068047`** and **E1a semantic `35605068290`**, both pending at checkpoint. Intermediate heads `3ec31afc...` and `fa82c39b...` are SUPERSEDED and their auto-runs must not be interpreted. **Discriminator:** a frame-coherent pass should expose the intended full checkerboard and decide whether transparent texels preserve prior Z; if active area remains uniformly tagged under this quiescent capture, next investigate backdrop Fill Rectangle running in Cycle1 with persistent primitive depth rather than revisiting timing.

- **2026-09-21 E1a batch 18 — deterministic between-frame capture harness IMPLEMENTED, workflow wiring pending:** proof branch `fa82c39b3b73dae01a16e6837072838bc56f6b3f` updates only `scripts/gate_c_h_comp_e1_z_tag_capture_n64.py` on top of batch17. Ares source confirms GDB halt stops the emulator loop globally, so the previously considered “poll SP_STATUS while stopped” method is REJECTED. New harness uses ares-supported software breakpoint `Z0` at CPU `rsp_wait+0x10`, the first instruction after Sodium64's SP-HALT wait. First hit establishes a deterministic RSP-halted/DP-idle boundary; scratch/status are initialized there. Harness removes breakpoint, single-steps one CPU instruction, reinstalls it, then continues to the next hit and captures only if SP HALT, DP idle, fresh guest counter and fresh 8-byte marker are all valid. It reads the exact framebuffer address from the RSP-published marker; CPU display pointer is diagnostics only. **IMPLEMENTED, not yet runnable:** current workflow does not yet pass `--capture-ready-address`, so runs from `fa82c39b...` are superseded. Next: derive `rsp_wait+0x10` from exact ELF in workflow and dispatch final exact-head validation.

- **2026-09-21 E1a batch 17 — exact completed-frame identity IMPLEMENTED:** validation proof branch advanced to `3ec31afc8c4e53767ae0fec3348ccfd6e48d256f`. Only `src/rsp_main.S` changed: after existing `Sync Full` + DP-idle fence, proof status payload at `0xA00E1000` is extended from 4 to 8 bytes and now contains `{0xE1F00D01, FRAMEBUFFER(sp)}`. The framebuffer word is read before the RSP self-halt and before `sp` toggles, so it names the exact color target just completed rather than the CPU VI/display pointer. **IMPLEMENTED, not yet validated.** This intermediate head may auto-dispatch CI but is intentionally incomplete because the host still reads only the old 4-byte marker; any run from `3ec31afc...` is superseded by the upcoming host-capture change and must not be interpreted semantically.

- **2026-09-21 E1a batch 16 — capture-authority flaw found; prior classifier is NOT frame-coherent:** the 56 `0x0001` pixels in artifact `10620176581` form a single partial checkerboard near top-left (x≈12..27, y≈8..14), while the rest of active 256×224 is backdrop `0x8001`. Source review shows CPU `rsp_frame` waits for RSP HALT, then prepares/unhalts the next RSP frame; the host GDB interrupt stops the R4300 but does not establish that the RSP is halted. E1 marker is persistent after completion, so `marker==E1F00D01` only proves a prior fenced frame completed, not that the framebuffer/Z being read are from that fenced frame or currently quiescent. CPU global `framebuffer` is the VI/display pointer under triple buffering, not the exact RSP target identity. **MEASUREMENT DEFECT:** artifact topology is consistent with a mid-next-frame capture and cannot decide transparent-hole semantics. **Next controlled change:** keep guest/Z/backdrop semantics unchanged; extend marker payload with the exact `FRAMEBUFFER(sp)` rendered address, then while R4300 is stopped require memory-mapped `SP_STATUS.HALT=1` and DPC busy bits `0x70==0` before reading that exact buffer and Z. Only after a frame-coherent rerun may backdrop/depth-state behavior be interpreted.

- **2026-09-21 E1a batch 15 — failure topology strongly SUPPORTS Z channel; alpha-input assumption is now the blocker:** artifact `10620176581` from run `35555509521` was inspected. Post-warmup ownership epoch is valid (`warmup_counter=12`, baseline=12, fresh capture counter=22, marker `0xE1F00D01`), prefix/suffix guards are intact, and depth contains **only two words**: expected tag `0x0C00` at **57,344 pixels = exactly 256×224 active area**, sentinel `0x55AA` at **9,856 pixels = remaining 280×240 border**. Cross-correlation is exact: every captured `fb!=0` pixel has `0x0C00`; every `fb==0` pixel retains `0x55AA`; there are no unexpected Z words. The original classifier failed because it expected checkerboard palette-index-0 holes within the active area to remain sentinel, but the captured active area is almost entirely backdrop-color `0x8001` plus 56 black `0x0001`, all tagged. Pinned ares Fill path calls `fill_color()` and does **not** modify depth, while normal shading performs alpha-test before returning `ShadedData` and before `depth_blend` Z-write. Therefore the full-area tag cannot be blamed on backdrop Fill in this backend; it means the regular BG path is not presenting the intended transparent-alpha holes to the alpha test in this diagnostic. **SUPPORTED INTERPRETATION:** primitive-depth encoding (`0x0C00`), bounded Z address, producer fence, guard integrity and accepted-fragment stamping all behave exactly as designed in pinned ares. **OPEN QUESTION:** why diagnostic palette index 0 is accepted across the active BG rectangle (TLUT/palette queue/combiner alpha vs guest/cache behavior). Do not declare full alpha-presence proof or start E1b until that input-side issue is isolated.

- **2026-09-21 E1a batch 14 — corrected semantic run reached real discriminator and FAILED; evidence classification pending:** exact proof head `d5db9d04e9e6237aaf21bf8f04f9cd2e24cf6f48`, Gate C H-COMP E1a run **`35555509521`**, job `106198279283`, completed FAILURE. Deterministic guest, exact runtime build, wrap/identity, symbol location, pinned-ares dependency install and pinned N64-only ares build all succeeded; failure is confined to `Run fenced primitive-Z / alpha-presence proof`. Evidence artifact **`10620176581`** uploaded successfully. Standard Build/Validate on the same SHA remains `35555509531 SUCCESS`. **Do not yet reject primitive-Z:** immediate next action is exact failed-step log + artifact/result classification (guard integrity, post-warmup initialization, guest/marker freshness, framebuffer histogram, depth histogram and mismatch topology) before any runtime/architecture change.

- **2026-09-21 E1a block-end checkpoint — corrected semantic experiment ACTIVE:** integrated truth remains `master@5b7134930a0ca859f6aa24e54102de116948e3ed`; no master/PR13/PR14 change in this block. Validation-only proof head is **`phase4/gate-c-h-comp-e1-z-tag-proof@d5db9d04e9e6237aaf21bf8f04f9cd2e24cf6f48`**. Standard Build/Validate **`35555509531 SUCCESS`**. Semantic E1a **`35555509521`**, job `106198279283`, has passed deterministic guest, exact runtime build, wrap/identity, symbol location and dependencies; at checkpoint it is still in `Build pinned N64-only ares in established valid lab mode`, before the semantic step. **Question:** after a post-warmup fenced clean epoch, do opaque-black BG fragments write encoded depth `0x0C00` while transparent holes preserve sentinel `0x55AA`, with guards intact? **Pass:** validates the basic regular-rectangle primitive-Z/alpha-presence/fence contract and unlocks bounded E1b (two tags, then within-frame strip rebasing). **Failure before classifier:** classify harness/lab and do not reject Z. **Classifier failure:** inspect exact depth histogram/mismatches/guards before architecture change. Pinned ares GDB source confirms KSEG1 arbitrary-size RDRAM writes/reads use direct byte bus access; therefore unsupported GDB bulk-write semantics are not a current explanation. **HYPOTHESIS only:** the superseded pre-warmup failure may have been concurrent startup RDP activity mutating the underflow region while the CPU debug stop was observed; the corrected post-Sync-Full epoch is the discriminator. Exact proof artifact also validates no static RDRAM collision: linker end `0x800B9E20`, E1 prefix `0x800BEE80`, Z `0x800C0000..0x800E0CFF`, marker `0x800E1000`, FB1 `0x800F2300`. **Resume:** inspect `35555509521` to completion; do not implement E1b or the color-math kernel until E1a's actual evidence is classified.

- **2026-09-21 E1a batch 13 — exact-head RDRAM ownership map MEASURED from build artifact:** exact `d5db9d04...` Build/Validate artifact `10620525160` (`sodium64-build`) gives linker `end=0x800B9E20`. E1 prefix begins cached-equivalent `0x800BEE80`, leaving **0x5060 = 20,576 B** after program/data. Z payload is `280*240*2 = 0x20D00` B at `0x800C0000..0x800E0CFF`; next address `0x800E0D00`. Proof marker is `0x800E1000`, leaving **0x300 = 768 B** after Z. Exact `defines.h` chain places `FRAMEBUFFER1=0xA00F2300` (cached `0x800F2300`), leaving **0x112FC = 70,396 B** after the 4-byte marker before FB1. **VALIDATED layout constraint:** current E1a prefix/Z/marker do not overlap linked program/data or framebuffer pool on the exact proof SHA. This removes scratch-address collision as a plausible explanation for the prior pre-warmup harness failure, while not proving runtime ownership against other transient users.

- **2026-09-21 E1a batch 12 — corrected-head Build/Validate GREEN:** exact proof head `d5db9d04e9e6237aaf21bf8f04f9cd2e24cf6f48`, standard **Build and Validate run `35555509531` SUCCESS** across normal build, PROFILE build and pinned Mupen/LLE emulator smoke (`update-release` skipped). This confirms the harness-only warmup change did not introduce generic build/boot/runtime regression. It does not validate Z semantics; semantic run `35555509521` remains in pinned-ares build at checkpoint and is the only current authority for E1a.

- **2026-09-21 E1b prep — bounded design only, NOT IMPLEMENTED pending E1a:** if E1a validates the basic rectangle-path tag/presence contract, use two explicit primitive depths rather than overloading one code: `prim_depth 0x1800 -> stored depth 0x0C00` and `0x2800 -> 0x1400` under the pinned oracle, with host sentinel `0x55AA`. First prove two overlapping BG source tags/winner order with transparent holes; separately prove true strip reuse by rebasing Set-Z-Image so two different global-Y bands map onto the same 280-wide scratch allocation, with different occupancy, edge X coverage, guard bytes and a short final band. **Do not accept frame-to-frame scratch reuse as equivalent to within-frame strip rebasing.** No E1b runtime/workflow change until E1a passes.

- **2026-09-21 E1a batch 11 — original guest semantic control rechecked:** deterministic E1a ROM is a Mode0 BG1 2bpp checkerboard; tile plane0 alternates palette indices 0/1, CGRAM0 is visible red backdrop, CGRAM1 is RGB black, TM enables BG1 only, TS/math are off, brightness is full. This specifically distinguishes palette-index-0 transparent holes from nonzero-index opaque black without involving H-COMP or brightness ordering. No guest-side confound was found that warrants changing the active rerun. **SUPPORTED INTERPRETATION:** if corrected E1a reaches classification, framebuffer correlation between `0x0001` opaque black and sentinel-preserving visible backdrop is a valid bounded alpha-presence discriminator for the regular BG rectangle path.

- **2026-09-21 E1a batch 10 — static proof contract rechecked; no second blocker found:** master framebuffer underflow is `280 * -16` **bytes**, i.e. 4480 B = eight RGB16 rows; diagnostic Z command address `0x0BEE80` is exactly `0x0C0000 - 0x1180`, so the prefix mapping matches the existing color-image convention. Pinned ares `op_set_prim_depth` consumes `(word1>>16)&0xffff`; renderer stores `(prim_depth&0x7fff)<<16`, and depth memory writeback stores `(z_compress(z)<<2)|(dz>>2)`. This reaffirms the encoded-word oracle used by E1a and finds no source-level reason to alter `TAG_WORD=0x0C00` before dynamic evidence. Runtime fence remains `Sync Full` + DP status `0x70` idle + RSP DMA marker. **Meaning:** do not broaden the patch while exact-head rerun `35555509521` is active; next decision comes from the corrected dynamic discriminator.

- **2026-09-21 E1a batch 9 — corrected ownership-epoch rerun DISPATCHED:** validation-only proof head is now `d5db9d04e9e6237aaf21bf8f04f9cd2e24cf6f48`, one-script delta from prior head: remove only the pre-warmup `initialize_proof_memory()` call and warm on guest progress + post-DP-fence marker before creating/verifying the clean scratch epoch. Exact-head runs auto-dispatched: **Gate C H-COMP E1a `35555509521`** and **Build and Validate `35555509531`**, both in progress at checkpoint. No production/master change; runtime proof instrumentation is otherwise unchanged. **Expected discriminator:** if post-warmup scratch initialization verifies, prior failure is fully confirmed as startup harness instability and semantic Z evidence can proceed; if the same write/read check still fails while stopped after a fenced guest frame, investigate debugger-memory ownership/overlap before any RDP conclusion.

- **2026-09-21 E1a batch 8 — failure classified as PRE-WARMUP HARNESS FAILURE; KSEG alias rejected:** failed job log shows the run stopped inside the *first* `initialize_proof_memory()` before any guest warm-up, at immediate prefix write/read verification (`0xA00BEE80..0xA00BFFFF`). No Z classifier or producer-frame evidence was reached. Pinned ares N64 GDB hook masks debugger addresses with `address & 0x1fffffff`, so `0xA...` vs `0x8...` aliases are not the cause. The pre-warmup initialization is unnecessary for the experiment: guest counter + runtime post-`Sync Full` marker can establish stable execution first, then the stopped target can be initialized once to create the clean ownership epoch. **Decision:** classify run `35554249281` as harness/setup failure, not architecture evidence. Next controlled change: remove only the pre-warmup scratch initialization, retain warmup counter+fence wait, then initialize/verify scratch while stopped and require a subsequent fresh frame+marker before readback.

- **2026-09-21 E1a batch 7 — semantic run FAILED at discriminator, classification pending:** exact corrected proof head `d123d7bd45de63fffd8f2bf8720407001214356a`, Gate C H-COMP E1a run `35554249281`, job `106194705880`, completed FAILURE. Deterministic guest, exact proof-runtime build, wrapping/identity, symbol location, pinned-ares dependencies and pinned N64-only ares build all succeeded; only step `Run fenced primitive-Z / alpha-presence proof` failed, while evidence upload succeeded. This narrows the failure to the actual runtime/harness discriminator rather than generic build/setup. **Do not yet interpret this as primitive-Z architecture rejection.** Immediate next action: inspect exact failed-step log/evidence and classify command encoding vs expected Z representation vs fence/ownership vs framebuffer correlation vs actual tag semantics before changing runtime.

- **2026-09-21 E1a batch 6 — same-head Build/Validate GREEN:** exact corrected proof head **`d123d7bd45de63fffd8f2bf8720407001214356a`** completed standard **Build and Validate run `35554249266 SUCCESS`**: normal build, PROFILE build and emulator-smoke all succeeded (`update-release` skipped). This does not validate primitive-Z semantics and does not make the proof branch production-worthy (Mode7 is intentionally stubbed), but it rules out a generic build/boot/smoke regression from the E1a instrumentation. Semantic run `35554249281` remains the authority for the current discriminator.

- **2026-09-21 E1a batch 5 — exact proof build/wrap VALIDATED on corrected head:** semantic run `35554249281` at **`d123d7bd45de63fffd8f2bf8720407001214356a`** has passed deterministic guest generation, exact proof-runtime build, guest wrapping/embedded-ROM identity, and runtime-symbol location. Therefore the validation-only Mode7 stub + reused fixed DMEM command slot + added Z/fence helpers fit and assemble; there is no IMEM/layout/build blocker in this bounded proof. The run is now progressing through pinned-ares setup; **no semantic Z-tag conclusion yet**. This narrows any later failure to lab/runtime/harness semantics rather than compile capacity.

- **2026-09-21 E1a batch 4 — startup-stale harness flaw found and REPAIRED before interpretation:** review of the first dispatched harness found that pre-filling Z only before guest boot could allow a transient startup render to seed tags that later look like stale metadata, confounding E1's ownership question. This is a **measurement/harness defect**, not runtime evidence. Capture was corrected at proof head **`d123d7bd45de63fffd8f2bf8720407001214356a`**: first wait for guest counter ≥5 plus the post-DP-fence marker, then while the target is stopped after that fence reinitialize prefix guard, full Z sentinel surface, suffix guard and status marker; only after at least one subsequent guest frame and a new fenced marker is evidence read. Previous exact-head Build run `35554170926` was cancelled by the new push; its paired semantic run `35554170986` is superseded even if it finishes and must not be interpreted. New exact-head runs: Build/Validate **`35554249266`** and E1a semantic **`35554249281`**. **Meaning:** the proof now has an explicit clean ownership epoch and can detect real stale writes rather than boot history.

- **2026-09-21 E1a batch 3 — exact dynamic discriminator DISPATCHED:** proof branch head **`phase4/gate-c-h-comp-e1-z-tag-proof@91562e8555740c52a5bb07b574044ab6681bc851`** contains only the validation runtime instrumentation plus deterministic original guest/capture workflow. Build/Validate run **`35554170926`** and semantic **Gate C H-COMP E1a Z-Tag Proof run `35554170986`** were queued from that exact SHA. Guest uses Mode0 BG1 checkerboard with palette index0 transparent, palette index1 RGB-black-but-opaque, visible red backdrop, no color math, and a WRAM NMI counter. Host initializes logical 280×240 Z scratch `0xA00C0000..0xA00E0CFF` to sentinel word `0x55AA`, the 8-row underflow/prefix region to `0xC3`, and a 64-byte suffix guard to `0x3C`; it waits for both fresh guest frames and the RSP marker published only after Sync Full + `DP_STATUS&0x70==0`. Classifier correlates actual framebuffer pixels rather than assuming checkerboard orientation: RGBA5551 opaque black `0x0001` must have exact Z word `0x0C00`; every visible backdrop pixel must retain `0x55AA`; no other depth word or guard mutation is allowed. **Pass:** establishes encoded primitive-Z + alpha-presence + explicit producer fence for the real regular texture-rectangle command path. **Fail:** inspect whether cause is compile/layout, command encoding, framebuffer freshness, Z word representation, or semantic tag failure before changing architecture. This E1a intentionally does not yet test two-source ordering or strip reuse; those are E1b only after E1a passes.

- **2026-09-21 E1a batch 2 — validation-only Z-tag runtime IMPLEMENTED, not yet validated:** created `phase4/gate-c-h-comp-e1-z-tag-proof` from exact integrated `master@5b7134930a0ca859f6aa24e54102de116948e3ed`; proof runtime commit **`177406fc0bd4a036b12978c2704d3f21cacd3d59`** changes only `src/rsp_main.S`. It preserves the existing regular CI/TLUT texture-rectangle renderer but deliberately stubs Mode7 **only in this proof child** to free IMEM without consuming PR #13. The now-unused 0x78-byte Mode7 RDP command slot is reused at the same DMEM address for Set-Z-Image / Set-Prim-Depth / Sync-Full commands, so the resident DMEM layout after the slot does not move. Z image uses physical command address `0x0BEE80`, corresponding to logical scratch `0xA00C0000` after the same 280×8-row underflow convention as the production color image. Regular BG fragments get primitive depth `0x1800`; pinned-ares math predicts 18-bit z=`0xC000`, compressed depth=`0x0300`, and with prim_dz=0 the visible RDRAM depth word is **`0x0C00`** because depth storage is `(compressed_z<<2)|(compressed_dz>>2)`. The proof does **not** attempt to stamp backdrop with Fill mode; instead the host will prefill scratch with a distinct sentinel, because pinned parallel-RDP fill path bypasses ordinary depth_blend/Z-update on separate depth surfaces. At frame end the proof submits Sync Full, waits until `DP_STATUS & 0x70 == 0` (TMEM/pipe/buffer idle), then RSP-DMA-publishes marker `0xE1F00D01` at `0xA00E1000`; capture must not read Z before that marker. **Scope:** rectangle-path architecture proof only; no production compositor, no Mode7 claim, no PR13 merge dependency. **Next:** add deterministic original checkerboard guest where palette index0 is transparent and palette index1 is opaque black, plus host capture/classifier and guard-byte checks; then run CI. A compile or semantic failure falsifies this exact proof implementation, not H-COMP itself.

- **2026-09-21 E1 batch 1 — exact RDP Z command contract SOURCE-VALIDATED against pinned ares `17813a3c...`:** `op_set_mask_image` (RDP opcode `0x3E`) supplies the 24-bit depth-buffer address; `op_set_prim_depth` (opcode `0x2E`) supplies `prim_depth:prim_dz`; current Sodium64 `Set Other Modes` is `0x2F0088FF00040001`, where alpha-test bit0 is already enabled. For the diagnostic, set word1 bits **2 (primitive depth)** and **5 (depth update)** while leaving bit4 **Z compare disabled**, i.e. diagnostic low word `0x00040025`. Pinned ares writes `z_compress(z)` to depth memory only after the fragment survives alpha/coverage; primitive depth enters the rasterizer as `(prim_depth & 0x7fff)<<16`, producing the RDP 18-bit Z domain before compression. Therefore E1 will use deliberately separated primitive-depth codes and compute their expected **compressed 14-bit RDRAM words**; raw depth words are not layer IDs. `Sync Full` is opcode `0x29`; a completion handshake must also observe DP busy/pipe/tmem state rather than relying on Sodium64's current command-busy-only `rdp_send`. **SUPPORTED INTERPRETATION:** the exact hardware command contract needed for a bounded dynamic tag proof is now specified. Next: build a validation-only child from current master that preserves the regular CI8/TLUT texture-rectangle path, frees proof-only IMEM by disabling Mode7 in that child, stamps backdrop/layer tags, and captures depth memory; no production architecture decision yet.

- **2026-09-21 E1 batch 0 — exact-path source wiring confirmed / IMPLEMENTATION NOT STARTED:** integrated `master@5b7134930a0ca859f6aa24e54102de116948e3ed` uses a **280-pixel color-image pitch** (`Set Color Image` width field and `280 * -16` underflow addressing). Current `rsp_main.S:rdp_send` waits only for DP command-busy (`DP_STATUS & 0x40`) before writing `DP_START/DP_END`; that is command-submission serialization, **not proof that prior RDP framebuffer/Z writes are complete in RDRAM**. Current master command tables have no Z-image/primitive-depth metadata path. **Meaning:** E1 must add its own bounded diagnostic command sequence plus an explicit DP-completion/readback handshake before checking or reusing scratch; do not treat `rdp_send` as the ownership fence. This independently confirms Astra's audit risk and narrows the proof contract before any math kernel. Next: pin exact Set Z Image / primitive-depth / OtherModes encoding against the ares RDP implementation and then build the validation-only E1 branch.

- **2026-09-21 focused audit COMPLETE — batches 1–5 persisted; M3/Gate C active.** Audited master `5b7134930a0ca859f6aa24e54102de116948e3ed`; #13 remains open at `84ecafad7cc3505d82f134b2672d9ed1146fedc0`, #14 merged-consumed. **Immediate next action: E1 exact-command RDP tag/sub-validity/fenced-strip proof**, before kernel work. Key risks: compressed Z/280-wide scratch ownership; raw-color/brightness and independent-mask semantics; unmeasured integration/overlay/fence cost. #13 is reasonable but not hardware-qualified, and its current same-frame test does not prove transition-frame pixel bands. #14 stays closed with a concrete cooldown-coupling follow-up. See final checkpoint below for conclusions, three ordered experiments, falsifiers and limits. Only this file changed.

- **2026-09-21 audit batch 4 complete.** Accurate/performance ares agree on ordinary low-resolution math and half-suppression policy. A CPU post-pass can prove semantics without PR #13; RSP resident/third-overlay placement requires a complete compiled size/DMEM/ABI proof. Forty free bytes do not establish fit or impossibility. No production location selected by intuition.

- **2026-09-21 audit checkpoint 4A — limit the RDP rejection to what was tested.** Texture RGB5 expansion and framebuffer-memory RGB5 input differ in the pinned RDP model. The earlier naive HALF surrogate failure does not reject every possible RDP sequence. Keep exact RGB5 oracle, reject unproven blender substitution, and avoid an open-ended RDP optimization search.

- **2026-09-21 audit batch 3 complete.** Strips remain a reasonable bounded direction; primitive-Z and framebuffer-alpha validity are still conditional. At the existing 280-pixel pitch, a conservative 8-row sub+two-tag design is 13,440 B; a one-Z reuse design is 8,960 B but adds a validity/ownership obligation. Define raw-color/brightness epochs and DP→SP ownership before kernel work. See batch 3 COMPLETE.

- **2026-09-21 audit checkpoint 3B — raw operands and brightness are prerequisites.** Current palette/backdrop conversion applies brightness before composition; a final exact path must preserve raw colors and apply brightness after math. Separate TM/TS targets must also separate TMW/TSW. A Z tag records current draw order, not proof of SNES priority. See batch 3B.

- **2026-09-21 audit checkpoint 3A — H-COMP metadata contract first.** Z readback is compressed, shares the color-image pitch (currently 280), and needs an explicit DP-completion fence. Prove encoded tags, sub-validity, and reused-strip bounds before implementing the math kernel. This narrows the previous kernel-first direction; it does not reject strips or primitive-Z. See batch 3A below.

- **Focused audit batch2 COMPLETE:** PR14 remains correctly closed for changed-WH line retention. New concrete scope issue: urgent snapshots still increment adaptive cooldown, so later non-WH state latency is not proved unchanged; use burst→generic-register control if needed. WH224/224 does not validate color-state epochs or pixel phase. Next: H-COMP metadata/readback architecture.

- **Focused audit batch1 COMPLETE:** PR13 loader/tail-entry ABI appears coherent; no fatal source defect found. Hardcoded slot invariants need compiled guards; same-frame proof still lacks transition-frame pixel assertions. Safe as experimental infrastructure with explicit ABI, not hardware-qualified or automatically ready for a third math overlay. Next audit: PR14.

- **Focused audit batch1 finding — same-frame proof is narrower than its shorthand:** job106139474289 captures at frame37 after IRQs in frame30; asserts final slot/recovery, not mixed-mode frame pixels. Preserve as LAB LIMITATION/evidence scope; add exact transition-frame band check before relying on pixel correctness. Audit ongoing; no runtime change.

- **2026-09-21 focused auditor / checkpoint 0 — IN PROGRESS:** master5b713493 verified; PR14 integrated; PR13 open at84ecafad. Five requested batches will be persisted sequentially below under “Gate-C focused audit 2026-09-21”. Source-disjoint PR13/14 is not combined-runtime validation. Next: PR13 loader/ABI and semantic evidence. Only this file changes.

- **2026-09-21 master post-merge Ares discrepancy — LAB LIMITATION / exact rerun GREEN:** original push Ares run `35543805220` had one collapsed `recompiler-gameplay-balanced` instance (0 samples/0 frames, `SP_PC=0`) after all preceding workloads progressed. Exact failed job was re-run **without any source/workflow change**; replacement `ares-smoke` job **`106184119278 SUCCESS`** completed the entire matrix. On the previously collapsed workload it produced **1015 valid samples**, `fps_display=60/60`, partial `fps_native=24`, `fps_emulate=25`, `frame_count=2`, `SP_PC=3480`, at frameskip0/APU21/audio4/precision8. The rerun's frame-budget report classifies gameplay-balanced at the virtual target. **Decision:** original zero-state instance is a **LAB LIMITATION / runner-emulator boot flake**, not reproduced evidence of a PR14/WH regression. Do not change runtime for it. Integrated `master@5b713493...` remains best-known state. This unblocks H-COMP architecture work.

- **2026-09-21 H-COMP resume point — next proof, no runtime branch yet:** H-COMP is dynamically VALIDATED both as ADD/SUB arithmetic omission and as general BG main/sub operand loss. Full-frame extra-surface design is capacity-constrained; strip compositor with primitive-Z metadata has source-level proof against pinned ares that transparent texture texels fail alpha-test before Z write while opaque texture rectangles can use primitive depth and Z-update with Z-compare disabled. Exact math oracle is pinned ares `sfc/ppu-performance/dac.cpp`. **Immediate next action:** prototype/validate the smallest exact strip math kernel and command sequence, preferably on a validation/architecture-proof branch, before touching integrated runtime. Required proof questions: (1) dynamic RDP primitive-Z metadata readback using Sodium64's exact texture/alpha command mode; (2) exact ADD/SUB/HALF BGR555 kernel against all oracle pairs; (3) IMEM fit — master RSP has only 40 B spare, so if the exact kernel cannot fit resident, evaluate it specifically as an overlay consumer on PR13's fixed-slot architecture rather than bloating monolithic master; (4) only after semantic proof, measure mixed BG/OBJ/DMA budget. Do not merge PR13 solely to obtain space; architecture proof may use a validation child/integration candidate while PR13's L4 hardware boundary remains explicit.

- **2026-09-21 H-COMP strip metadata proof 1 — SOURCE-VALIDATED against pinned ares RDP:** exact `ares@17813a3c...` N64 pipeline establishes the required primitive-Z metadata behavior without a Sodium64 runtime change. `op_texture_rectangle` enters `Renderer::draw_shaded_primitive`; when primitive-depth is enabled, the renderer injects `constants.prim_depth` as the primitive Z. In `shading.h`, RGBA texture alpha/alpha-test rejection returns **before** `ShadedData` is emitted; therefore a transparent texel does not reach framebuffer/Z writeback. In `depth_test.h`, with Z-compare disabled the depth test returns pass unconditionally, while depth write remains a separate state bit. In `memory_interfacing.h`, Z is written only after the pixel survived coverage/alpha tests and only when `DEPTH_UPDATE` is enabled. **SUPPORTED ARCHITECTURE PROPERTY:** a small reusable Z strip can encode main-winner/source-or-math metadata during the normal main texture-rectangle pass: opaque winner texels stamp the layer's primitive-Z code; transparent texels leave the prior winner code untouched. Initialize the strip to the backdrop source code before each strip. This avoids a second main-layer mask pass and avoids a full-frame metadata buffer. **Limit:** this is pinned-ares/source L0/L2 evidence, not real-N64 authority; before final architecture acceptance, a tiny dynamic RDP readback control should still confirm primitive-Z/alpha-test behavior on the actual command encoding used by Sodium64. Next proof: compact RSP BGR555 strip math kernel against the pinned ares oracle and IMEM/overlay capacity.

- **2026-09-21 H-COMP exact-math / strip compositor design batch — HYPOTHESIS narrowed, no runtime change:** pinned SNES oracle was read directly from `ares@17813a3c.../ares/sfc/ppu-performance/dac.cpp`. Required per-pixel contract is explicit: independent main/sub winners; main source determines CGADSUB enable; color window can force main black / disable math; blendMode chooses real subscreen vs fixed color; when subscreen winner is backdrop/transparent, operand falls back to fixed color and half is suppressed; add/sub/half use packed BGR555 channel-safe formulas. Pinned ares N64 RDP source confirms RGBA5551 texels expand 5→8 as `(v<<3)|(v>>2)`, final RGBA5551 writeback keeps the upper 5 RGB bits, and the Color Combiner uses signed 9-bit intermediate/clamp behavior. A host exhaustive sanity check over all **32×32 single-channel pairs** shows the straightforward expanded-8-bit route reproduces full ADD and clamped SUB after 5-bit writeback, but a naive 50% average is **not** an exact SNES HALF-ADD surrogate (224/1024 pairs differ due 5→8 replication). Therefore **REJECT** “use generic 50% RDP blend for HALF and call color math solved”; exact packed math remains required unless a later RDP-specific proof establishes an equivalent formulation. New memory-efficient architecture candidate: process the compositor in **small scanline strips** rather than storing full-frame main/sub/metadata surfaces. Render subscreen winner for a strip into RGB16 scratch (backdrop alpha/coverage representing no real sub winner where usable), render main winner to output while writing a small strip metadata surface (candidate: primitive-Z/source or math-enable code), then run exact vector BGR555 math over contiguous main/sub/metadata strips and reuse scratch for the next strip. For 8 scanlines, RGB16 sub scratch is ~4 KiB and a 16-bit metadata/Z strip another ~4 KiB, avoiding the full-frame two-scratch capacity failure. This also preserves current layer identity until metadata is stamped and allows separate `TSW`/`TMW` instead of today's OR-combination. **Open proof requirements before implementation:** (1) validate texture-rectangle opaque pixels can stamp primitive-Z/source metadata while transparent texels leave prior metadata untouched; (2) prove a compact RSP strip kernel against the pinned ares packed formulas; (3) quantify RDP/RSP command/bus cost on the mixed Gate-C workload. Do not modify master or choose this architecture until those proofs win.

- **2026-09-21 H-COMP compositor capacity/architecture audit — SUPPORTED CONSTRAINTS / no runtime fix yet:** exact integrated normal-build artifact `10616265014 sodium64-build` was inspected; linker `end=0x800BA180`, while fixed `FRAMEBUFFER1=0xA00F2300` (cached `0x800F2300`), leaving **`0x38180 = 229,760 B`** of currently unused address space below the framebuffer pool. One active SNES RGB16 surface at 256×224 costs **`0x1C000 = 114,688 B`**. Two additional RGB16 active surfaces cost `0x38000 = 229,376 B` and would leave only **384 B**, so a stable design requiring two new full 16-bit surfaces is **REJECTED as capacity-unsafe** before any added code/data. One RGB16 scratch plus an 8-bit 256×224 metadata mask costs `0x2A000 = 172,032 B`, leaving ~57.7 KiB and is capacity-plausible. Source audit identifies the exact information-loss point in `rsp_main.S`: `TS/TM` are reduced into an ordered `s7` screen/layer mask and then both screens are drawn sequentially into the same `Set Color Image` target; current `TMW/TSW` are also OR-combined. Existing triple framebuffers are presentation buffers and rotating one into permanent scratch would reduce/change buffering semantics, so do not assume `FRAMEBUFFER3` is free. RDP special Blender ADD was also rejected as a complete exact SNES-math solution: official N64 documentation states that mode adds pixel to framebuffer memory color **without clamping the final result**, whereas SNES add/sub math requires defined saturated/underflow behavior. Repurposing RGBA5551 alpha as main-layer math eligibility is not a free metadata channel either: current palette conversion sets alpha=1 for real colors while transparent color 0 relies on alpha=0, and RDP alpha participates in coverage/alpha compare. **Current architectural direction (HYPOTHESIS, not chosen):** preserve one real subscreen RGB16 operand and either (a) carry compact winner/math metadata, or (b) perform exact arithmetic while each main winner/layer identity is still known. Avoid a second software renderer and avoid two-extra-RGB16 designs. Next discriminator after the master Ares rerun: prototype/host-model the smallest exact add/sub/half path using current RDP/RSP primitives, with an explicit memory and frame-budget contract before core integration.

- **2026-09-21 master post-merge Ares discrepancy — CONTROLLED RERUN DISPATCHED / no source change:** repo audit found `master@5b7134930a0ca859f6aa24e54102de116948e3ed` has Build/Validate `35543805198 SUCCESS` but push-triggered **Ares Profile Validation `35543805220 FAILURE`**. `profile-build 106166066003` succeeded; `ares-smoke 106166244816` failed only in the workload-matrix step after interpreter-idle/gameplay and recompiler idle/cpu-alu/wram/ppu-registers/dma-vram all produced valid samples/progress with Road-valid settings. The sole collapsed case was **`recompiler-gameplay-balanced`**: 0 samples for 60 s, `fps_display=255` sentinel, `fps_native=fps_emulate=frame_count=0`, `SP_STATUS=1`, DMA idle, **`SP_PC=0`**. This looks like an instance/boot/lab collapse rather than a measured WH-cost regression, but it is not yet classified as flake. Exact artifacts: `10616535480 sodium64-ares-profile-matrix` (`sha256:858aa2883b7fb9544c564e1810ff4c8beebc8ff89ff14afbf4659473657a8796`) and `10616110183 sodium64-ares-profile-build` (`sha256:c1ee32318f0c1edcb2cbb1bb7fcc3bbae24b7b499f419edcdeeb6c073ddaa818`). **Action:** re-ran the exact failed job `106166244816` with no code/workflow change. If rerun succeeds, classify original as LAB LIMITATION/runner-instance flake; if it reproduces the same zero-state gameplay collapse, investigate push-vs-PR/environment before any H-COMP runtime prototype. H-COMP architecture work is paused only until this discrepancy is classified.

- **2026-09-21 H-COMP BG main/sub color math — VALIDATED general compositor omission:** exact validation-only head `phase4/gate-c-h-comp-bg-diagnostic@79bf1ae45eb247c3cc2804d7cd041d03805cf367`; **Gate C H-COMP BG Main-Sub Diagnostic `35549088629 SUCCESS`**, semantic job **`106180372990`**, evidence artifact **`10617004819 gate-c-h-comp-bg-main-sub-evidence`** (`sha256:442492b0565169585ae5be408a0b8290f4049f080e002d727aebf6a4916577fe`). Same-head Build/Validate **`35549088591 SUCCESS`**. Live phase state was exact and stable: RAW `CGADSUB=0x00`, ADD `0x01`, HALF-ADD `0x41`; all phases `CGWSEL=0x02`, `TM=1`, `TS=1`, `BG_MODE=0`, `precision_set=8`. The opaque nonblank BG center is RGBA5551 **16385** in all phases. Full framebuffer SHA256 is byte-identical across RAW/ADD/HALF: **`c2d096fc30454282840b9fc2669e8ff10c185b1656a0ab6c154f8da77fcefb6b`**. Classification **`H_COMP_CONFIRMED_BG_MAIN_SUB_MATH_IGNORED`**. Correct SNES relation for this same opaque BG pixel on main+sub is `RAW == HALF`, with full ADD different/brighter; Sodium64 instead collapses all three. Together with backdrop ADD/SUB run `35548491441`, H-COMP is now dynamically validated both for arithmetic omission and for **general BG main/sub operand loss**. **Meaning:** a backdrop-only or one-bit arithmetic patch is insufficient; current single-surface/layer-order compositor loses the second per-pixel operand before math. **Next action:** source/architecture audit for the smallest compositor representation that preserves a second operand and supports layer-selected add/sub/half without building a second emulator; no runtime patch until that design is constrained by current RDP/RSP/framebuffer resources and a falsifiable prototype plan.

- **2026-09-21 block-end checkpoint — RESUME HERE / H-COMP BG control active:** integrated truth is **`master@5b7134930a0ca859f6aa24e54102de116948e3ed`** with PR #14 merged; PR #13 remains open/mergeable and intentionally unmerged pending its real-N64 overlay DMA/bus/cadence milestone. H-COMP backdrop/fixed-color arithmetic is now dynamically **VALIDATED defective** by run `35548491441`: live OFF/ADD/SUBTRACT `CGADSUB=0x00/0x20/0xA0`, stable `CGWSEL=0`, `precision=8`, distinct main/sub fixed colors, OFF framebuffer SHA `5c479e6c...`, and byte-identical ADD/SUB SHA `9a383e56...`; artifact `10616913040`, guest SHA `5f02b17e...`. Source audit independently shows `CGADSUB` is consumed only as `&0x20` and the renderer collapses main/sub drawing into one color surface/order workaround. **Active long experiment:** validation-only sibling **`phase4/gate-c-h-comp-bg-diagnostic@79bf1ae45eb247c3cc2804d7cd041d03805cf367`**; same-head Build/Validate **`35549088591 SUCCESS`**. Semantic run **`35549088629`**, job **`106180372990`**, has passed script determinism, exact unchanged core build, exact guest wrap, symbol location and dependency setup; at checkpoint it is still in **`Build pinned N64-only ares in valid lab mode`** with no failure. The guest uses opaque moderate-red BG1 on both main+sub (`TM=TS=1`, `CGWSEL=0x02`) and phases RAW `0x00`, ADD `0x01`, HALF-ADD `0x41`. **Question:** does Sodium64 collapse all three frames despite correct SNES relation RAW==HALF and ADD differing? **If all three identical with expected live registers/nonblank BG:** validate general BG main/sub color-math omission and then design the smallest compositor architecture that preserves a second operand; do not patch only backdrop arithmetic. **If RAW==HALF and ADD differs:** this path already behaves correctly and architecture assumptions must be revised. **Any other relation:** classify workload/harness before runtime changes. Resume by inspecting run `35549088629` to completion.

- **2026-09-21 H-COMP BG diagnostic same-head validation — GREEN:** exact validation-only head `phase4/gate-c-h-comp-bg-diagnostic@79bf1ae45eb247c3cc2804d7cd041d03805cf367`; **Build and Validate `35549088591 SUCCESS`** with normal build, PROFILE build and pinned Mupen/LLE emulator-smoke all successful (`update-release` skipped). Branch remains three validation files only over integrated master; no runtime/core changes. Therefore any outcome in paired BG semantic run `35549088629` is not a generic build/boot divergence introduced by diagnostic plumbing.

- **2026-09-21 H-COMP BG main/sub diagnostic — DISPATCHED / runtime untouched:** created sibling validation-only branch **`phase4/gate-c-h-comp-bg-diagnostic@79bf1ae45eb247c3cc2804d7cd041d03805cf367`** directly from integrated `master@5b7134930a0ca859f6aa24e54102de116948e3ed`. Exact delta is three added validation files only: `.github/workflows/gate-c-h-comp-bg.yml`, `scripts/gate_c_h_comp_bg_capture_n64.py`, `scripts/make_gate_c_h_comp_bg.py`; **no emulator/core file differs**. Deterministic original 32 KiB guest uses Mode0 BG1 with an opaque moderate-red 2bpp tile across the screen, enables BG1 on both main (`TM=1`) and sub (`TS=1`) screens, and sets `CGWSEL=0x02` so color math uses the real subscreen BG/OBJ pixel. Stable phases: raw `CGADSUB=0x00`, BG1 ADD `0x01`, BG1 HALF-ADD `0x41`. Correct SNES relation for the same nontransparent red BG1 pixel on main+sub is **raw == half, add differs/brighter**. Current compositor source predicts all three equal because BG1 math enable/half bits are never consumed and shared main/sub layers are collapsed to one draw. Workflow captures fresh framebuffers plus live `TM/TS/CGWSEL/CGADSUB/BG_MODE/precision_set` and classifies relationally; it also verifies exact guest identity after wrapping. Dispatched **Gate C H-COMP BG Main-Sub Diagnostic `35549088629`** and same-head **Build and Validate `35549088591`**. **Pass/confirm defect:** all three framebuffers byte-identical with live expected register values and nonblank BG center. **Falsifier:** raw==half but ADD differs. Any other relation is INDETERMINATE and requires harness/workload diagnosis before architecture work.

- **2026-09-21 H-COMP ADD/SUB arithmetic omission — VALIDATED dynamically:** exact validation-only head `phase4/gate-c-h-comp-diagnostic@ad2508189e00107f2242e86e18ec7e293b6990e5`; **Gate C H-COMP Add-Subtract Diagnostic `35548491441 SUCCESS`**, semantic job `106178715238`, evidence artifact **`10616913040 gate-c-h-comp-add-sub-evidence`** (`sha256:ef73283d6ab4e9b49a28e7e4449e73629586ebd1297a7eacc746932cdb5c3267`). Deterministic original guest SHA256 **`5f02b17e2cf6487c436121eb404e50ebd159a943afe3fe8ed73669028f005adc`** was generated twice byte-identically and survived wrapping exactly. Live state at all captures: `CGWSEL=0`, `precision_set=8`, stable distinct runtime colors `MAIN_COLOR=63488`, `SUB_COLOR=62`. Phase states were exact: disabled `CGADSUB=0x00`, ADD `0x20`, SUBTRACT `0xA0`. Fresh framebuffer relation: disabled center RGBA5551 **63489**, ADD **63**, SUBTRACT **63**; disabled framebuffer SHA **`5c479e6ceea2a993300d59f444673c612a18aaf079ecd0988f9356b2e01f2cd1`**; ADD and SUBTRACT are byte-identical with SHA **`9a383e562f1f7e7e70ac7b00ce997b6cd9344d9b08388df3e4c4c0c2284da686`**. Classification **`H_COMP_CONFIRMED_ADD_SUB_IGNORED`**. The disabled→ADD change proves the configured math path is active; ADD==SUB despite live bit7 difference proves subtract semantics are ignored in the current compositor, matching the source audit. For chosen red main + blue fixed colors, correct SNES relation is disabled==subtract while ADD differs; Sodium64 shows the opposite relevant relation. **Meaning:** H-COMP arithmetic is a validated Gate-C fidelity defect, not merely an ALttP/SMW symptom. **Does NOT yet choose a repair architecture:** current renderer also discards general main/sub separation, so do not patch only the backdrop special case and declare color math solved. Next controlled batch should dynamically characterize non-backdrop main/sub BG composition (including half/add) before selecting compositor architecture.

- **2026-09-21 H-COMP compositor architecture audit — SUPPORTED CONSTRAINT / no fix chosen:** integrated renderer `master@5b713493...` configures one RDP `Set Color Image` target per frame and does **not** preserve main and sub screens as separate color surfaces. After backdrop fill it constructs one combined layer mask from `TS/TM`, removes shared layers, packs the two screen masks into drawing order, and explicitly comments that screen order can be swapped `As a workaround for lack of blending`. Therefore a complete SNES main/sub color-math repair cannot be assumed to be a one-bit RDP-mode change: the second color operand is generally discarded by the current single-surface layer-order architecture. This does **not** yet choose between an extra surface, targeted RDP blending, RSP composition, or narrower special cases. Keep anti-second-project discipline: first close the dispatched ADD/SUB dynamic discriminator; then design the smallest architecture that satisfies demonstrated Gate-C cases and measure its cost.

- **2026-09-21 H-COMP diagnostic same-head validation — GREEN:** exact validation-only head `phase4/gate-c-h-comp-diagnostic@ad2508189e00107f2242e86e18ec7e293b6990e5`; **Build and Validate `35548491407 SUCCESS`** with normal build, PROFILE build and pinned Mupen/LLE emulator-smoke all successful (`update-release` skipped). Exact branch delta from integrated master remains only one workflow + two scripts; no runtime/core files differ. Therefore any result from paired semantic run `35548491441` is not attributable to a compile/boot divergence introduced by diagnostic plumbing.

- **2026-09-21 H-COMP add/subtract diagnostic — DISPATCHED / runtime untouched:** created validation-only branch **`phase4/gate-c-h-comp-diagnostic@ad2508189e00107f2242e86e18ec7e293b6990e5`** directly from integrated `master@5b7134930a0ca859f6aa24e54102de116948e3ed`. Exact delta is **three added validation files only**: `.github/workflows/gate-c-h-comp.yml`, `scripts/gate_c_h_comp_capture_n64.py`, `scripts/make_gate_c_h_comp.py`; **no `src/`, Makefile or emulator/runtime file differs**. Deterministic original 32 KiB guest cycles three 40-frame phases over identical red backdrop + blue fixed color: math disabled (`CGADSUB=0x00`), backdrop ADD (`0x20`), backdrop SUBTRACT (`0xA0`), with `CGWSEL=0`. Workflow builds the unchanged integrated core, wraps/verifies exact guest bytes, runs pinned N64 ares in established RSP-interpreter lab mode, captures fresh framebuffers for all three phases plus live `CGADSUB/CGWSEL/MAIN_COLOR/SUB_COLOR/precision_set`, and classifies the **relation** rather than a hardcoded pixel. Correct SNES semantics for the chosen colors require `disabled == subtract` and `add` different. Current source omission predicts `add == subtract`, both different from disabled. Strong confirmation therefore requires: math-disabled framebuffer differs from ADD (path is active), ADD and SUBTRACT are byte-identical despite live `CGADSUB=0x20/0xA0`, and disabled differs from SUBTRACT. Dispatched **Gate C H-COMP Add-Subtract Diagnostic `35548491441`** plus same-head **Build and Validate `35548491407`**. Any setup failure or non-distinguished disabled/add state is INDETERMINATE and must be fixed in harness only; do not modify compositor yet.

- **2026-09-20 H-COMP source audit — VALIDATED semantic omission / dynamic discriminator designed:** on integrated `master@5b7134930a0ca859f6aa24e54102de116948e3ed`, `src/rsp_main.S` references **`CGADSUB` exactly once** (section backdrop path) and immediately masks it with **`0x20`** labelled `Backdrop math`; therefore add/subtract, half-result and non-backdrop layer-selection bits are not consumed by the RSP compositor. `CGWSEL` is also referenced exactly once and reduced to the math-window selection path. The renderer source explicitly says `TODO: implement color math properly if possible` and later constructs a combined main/sub layer mask `As a workaround for lack of blending, the order of the screens can be swapped`. **MEANING:** H-COMP is no longer merely inferred from game symptoms; current source demonstrably lacks full SNES color-math semantics. **Next controlled dynamic test:** validation-only branch from current master, deterministic original ROM cycling three stable phases with identical backdrop/fixed colors: math disabled (`CGADSUB=0x00`), backdrop ADD (`0x20`), backdrop SUBTRACT (`0xA0`). Use red main backdrop + blue fixed color so correct SNES add and subtract outputs must differ. Capture fresh N64 framebuffers plus live `CGADSUB/CGWSEL/MAIN_COLOR/SUB_COLOR`. Strong defect signature: disabled differs from ADD (proves setup hits math path) while ADD and SUB framebuffers are byte-identical despite live `CGADSUB` differing only in bit7. This isolates ignored add/sub semantics without commercial ROM data or visual judgement. No runtime change until that discriminator runs.

- **2026-09-20 PR #13 re-audit after PR #14 merge — CLEAN / hardware boundary unchanged:** with integrated truth now `master@5b7134930a0ca859f6aa24e54102de116948e3ed`, PR #13 remains **open, unmerged, mergeable=true** at frozen head `84ecafad7cc3505d82f134b2672d9ed1146fedc0`. Relative to current master it is **4 commits ahead / 1 behind** and its delta remains exactly `src/defines.h`, `src/main.S`, `src/rsp_main.S`, `src/rsp_mode7.S`; merged WH repair `src/ppu.S` is source-disjoint and creates no conflict. Prior semantic/CI evidence for #13 therefore remains applicable to its exact technical bytes, but its declared **real-N64 L4 overlay DMA/bus/cadence** question is still open. **Decision:** do not merge #13 merely because it remains mergeable; carry it as a clean hardware-milestone candidate while Gate C continues on independent base-system fidelity work.

- **2026-09-20 PR #14 integrated — MERGED / master advanced:** PR #14 `Gate C: preserve per-line window edges at medium precision` is now **MERGED**. Integrated truth is **`master@5b7134930a0ca859f6aa24e54102de116948e3ed`** with commit message `Gate C: preserve per-line window edges at medium precision`. Exact compare against prior master `9441818dd8457a27bbd617a0f32c6d484550661f` is **1 commit ahead / 0 behind / exactly one modified file `src/ppu.S` (+12/-4)**, matching the frozen audited candidate; no validation-only files entered master. PR-triggered Ares Profile Validation **`35541991618 SUCCESS`**: `profile-build 106161197161 SUCCESS`, `ares-smoke 106161350023 SUCCESS`; artifacts `10614913990 sodium64-ares-profile-build` (`sha256:e7a08d2d132ceb34e6ab59ad99e62fe5e5abb7e09b538a7fadcf13c759f4d9f9`) and `10615477058 sodium64-ares-profile-matrix` (`sha256:d60af750695b2768eb5008e9a206dbba7ce12bdf84a2e517a3b6f8dcc05e7e8c`). **Integrated result:** Road-valid MEDIUM now preserves the validated WH0..WH3 per-line window-edge path without globally switching precision to MAX. Real-N64 cadence remains milestone authority, but no dedicated pre-merge hardware session was required under `VALIDATION.md` for this narrow reversible PPU repair. **Immediate next action:** re-audit open PR #13 against new master, preserve its L4 hardware boundary, then choose the next Gate-C fidelity discriminator from the remaining known PPU/compositor issues rather than returning to performance optimization.

- **2026-09-20 H-COMP attempt 2 fixed-color discriminator — DISPATCHED / validation-only:** branch advanced to **`phase4/gate-c-h-comp-half-diagnostic@a7b894fa22fd3208397a8e8e28160991374c0fcc`**; exact delta from integrated master remains one workflow + six scripts, **zero `src/`/runtime changes**. Replaced invalid two-BG source construction with known-working BG1 main solid RGB5 `(16,0,0)` plus explicit fixed-color green RGB5 `(0,16,0)` via COLDATA `$2132=0x50`; no subscreen layers. `TM=0x01`, `TS=0`, `CGWSEL=0` selects fixed color. Phases differ only in `CGADSUB`: **`0x01` full add** vs **`0x41` half add**, with exact expected outputs `(16,16,0)` vs `(8,8,0)`. Pinned ares reference source confirms fixed-color mode honors `colorHalve`; the transparent-sub exception does not apply. Wrapped-state guard now also requires `coldata=0x0200` in both phases, proving the fixed-green operand reached Sodium64. Dispatched **Gate C H-COMP Half-Add Diagnostic `35544919724`** and same-head **Build and Validate `35544919754`**. **Pass/support H-COMP:** direct SNES establishes the two-level oracle and Sodium64 raw output is equal/wrong despite verified `CGADSUB/CGWSEL/TM/TS/COLDATA`; **falsifier:** Sodium64 matches exact `(16,16,0)->(8,8,0)`. If direct SNES again lacks the two-level output, reject guest/harness before any core change.

- **2026-09-20 H-COMP attempt 1 — REJECTED / INDETERMINATE_GUEST_SETUP, no H-COMP conclusion:** exact diagnostic head `79017d12e...`, run `35544095847`. The original two-BG guest booted and produced video in both labs, but did **not** exercise the intended main-red + sub-green pair. Direct-SNES job `106166849563` built/captured successfully then failed its oracle because screenshots show a large **green** guest field rather than the expected yellow full/half states; reference artifact **`10615746652 gate-c-h-comp-half-snes-reference`** (`sha256:682e497fffb9886763b6ffbbb8a96a8fcb4dae18d7adf44213d86fe8809da62d`). Wrapped Sodium64 job `106166849633 SUCCESS` observed the intended register tuple (`TM=2`, `TS=1`, `CGWSEL=2`, `BGMODE=1`, `CGADSUB 0x02→0x42`) yet raw central output was **RGB5 `(0,16,0)` in both phases**, artifact **`10616031151 gate-c-h-comp-half-sodium64-evidence`** (`sha256:ee1c3968101af82c23f85b95f81913d6176eb253474ac6c9b2ace90cc27e9934`). Because the direct SNES itself lacks the intended red-main contribution, the equal Sodium64 phases cannot validate H-COMP. **Decision:** reject this guest construction, do not tune thresholds or alter core. Next controlled guest uses known-working BG1 as the single main source and SNES fixed color as the second operand, isolating only `CGADSUB` half. Independent main/sub-winner behavior remains a later discriminator.

- **2026-09-20 H-COMP transport/capacity pre-audit — SUPPORTED / no ABI-input omission:** current 64-byte section/DMEM layout already transports `WBGSEL`, `SUB_COLOR`, `MAIN_COLOR`, `WOBJSEL`, `CGWSEL`, `CGADSUB`, `TS`, `TM`, `TSW`, `TMW`, mode/flags and split line. `make_section` copies that whole state verbatim. Therefore the directed half bit is not lost at the producer/queue boundary. The renderer instead constructs a flattened layer order from `TS/TM` and sends layers directly to RDP; it has no persisted pair of independent per-pixel main/sub winners for later arithmetic. `MAIN_COLOR/SUB_COLOR` are backdrop/fixed-fill colors, not general winner buffers. **Supported architectural reading if runtime confirms H-COMP:** repair will require consumer/intermediate representation work, not merely adding a missing section field or changing precision. No such repair implemented yet.

- **2026-09-20 H-COMP diagnostic same-head Build/Validate — GREEN:** exact validation-only head `phase4/gate-c-h-comp-half-diagnostic@79017d12e538633fd5baddacbe3efae23a5cc8c4`; **Build and Validate `35544095820 SUCCESS`** with normal build, PROFILE build and emulator-smoke successful (`update-release` skipped). Branch still differs from integrated master only by diagnostic workflow/scripts. Therefore any semantic outcome in `35544095847` is not a generic build/boot regression from the H-COMP harness.

- **2026-09-20 H-COMP static consumer audit — SUPPORTED / dynamic proof pending:** exact integrated `master@5b713493...` source has only one renderer-side `CGADSUB` consumer, in `src/rsp_main.S` backdrop handling. That path tests only bit `0x20` (backdrop math), then dispatches fill/window workaround logic under an explicit `TODO: implement color math properly`; no source path reads `CGADSUB` bit6 half, bit7 subtract, or performs general main+sub per-pixel arithmetic. `write_cgadsub` in `ppu.S` only stores the register and marks the section dirty. Therefore there is no hidden later half implementation elsewhere in the audited master. **SUPPORTED INTERPRETATION:** if the directed runtime phases render identically or otherwise miss the exact two RGB5 targets, the defect is genuinely in compositor semantics rather than a missing observation of an existing half stage. Await direct-SNES + wrapped dynamic evidence before promoting H-COMP to VALIDATED.

- **2026-09-20 H-COMP diagnostic guest identity — MEASURED:** diagnostic-build `106166835686 SUCCESS` generated the 32 KiB original ROM twice byte-identically; exact guest SHA256 is **`898e8928583d0e2a02101068870d0103ea12c98fe74057fd232ff70fd91d89dc`**. Original diagnostic artifact **`10615835930 gate-c-h-comp-half-diagnostic`** has digest `sha256:ae1265e78b7b7735129adf43428109d3e4f430261fdb66b2d581098800ceffbd`. This freezes the asset-free oracle input before either SNES-reference or wrapped Sodium64 interpretation.

- **2026-09-20 H-COMP half-add diagnostic — DISPATCHED / runtime untouched:** validation-only branch is now **`phase4/gate-c-h-comp-half-diagnostic@79017d12e538633fd5baddacbe3efae23a5cc8c4`**, 7 commits ahead / 0 behind integrated `master@5b713493...`. Exact delta is one branch-only workflow plus six `scripts/` files; **no `src/`, Makefile or emulator/runtime file differs**. Workflow runs three guards: (1) deterministic guest/tool tests; (2) wrapped Sodium64 raw RGBA5551 synchronized capture of `CGADSUB=0x02` full-add versus `0x42` half-add with live `CGWSEL/TM/TS/BGMODE` observations; (3) pinned direct-SNES ares screenshot sequence proving the same original guest has two half-dependent color levels. Sodium64 analyzer treats exact expected `(16,16,0)->(8,8,0)` as falsifying this half-path defect, equal outputs as `H_COMP_HALF_SUPPORTED_NO_HALF_EFFECT`, and other differing wrong outputs as `H_COMP_HALF_SUPPORTED_WRONG_ARITHMETIC`; recognized semantic outcomes do not fail merely for disagreeing with the hypothesis. Direct-SNES reference must establish the two-state oracle or the experiment is indeterminate. Dispatched **Gate C H-COMP Half-Add Diagnostic `35544095847`** and same-head **Build and Validate `35544095820`**. No compositor fix is authorized until both reference and wrapped-state guards are interpreted.

- **2026-09-20 H-COMP diagnostic batch 1 — IMPLEMENTED validation-only generator/tests:** created `phase4/gate-c-h-comp-half-diagnostic@4b8afdfd482d91681fcce1ccd101928d072bc0c7` directly from integrated `master@5b713493...`. Exact delta is only `scripts/make_gate_c_h_comp_half.py` + `scripts/test_gate_c_h_comp_half.py`; **no `src/`, Makefile, workflow or runtime/core file differs**. The original 32 KiB LoROM is designed to isolate only `CGADSUB` half: Mode1, BG2 main solid RGB5 `(16,0,0)`, BG1 sub solid `(0,16,0)`, `TM=0x02`, `TS=0x01`, `CGWSEL=0x02`, no windows/OBJ/HDMA; phases alternate `CGADSUB=0x02` full-add expected `(16,16,0)` and `0x42` half-add expected `(8,8,0)`. Tests assert deterministic 32 KiB structure, vectors, palette/map source identity, and even/non-saturating expected math. Branch Build/Validate `35543994476` dispatched automatically. Next batch: add synchronized raw Sodium64 framebuffer capture + exact RGB5 analyzer and pinned direct-SNES ares reference capture; still no core change.

- **2026-09-20 H-COMP half-add discriminator — DESIGNED / no core change:** after merged WH repair, next Gate-C uncertainty is compositor arithmetic, especially ALttP's documented `CGADSUB 0x32↔0x72` half toggle. Selected one-variable original ROM: Mode1, no OBJ/windows/HDMA/IRQ raster changes; BG2 is the only main-screen source with solid RGB5 `(16,0,0)`, BG1 is the only subscreen source with solid RGB5 `(0,16,0)`, `TM=0x02`, `TS=0x01`, `CGWSEL=0x02` (subscreen operand). Two long NMI-separated phases differ only in `CGADSUB`: control `0x02` = full add, treatment `0x42` = same add with half bit. For these even, non-saturating channels the exact expected SNES outputs are control `(16,16,0)` and treatment `(8,8,0)`. Build a pinned direct-SNES ares reference plus wrapped Sodium64 raw-RGBA5551 capture using the already-proven H-OBJ synchronization pattern. **Support H-COMP:** reference shows both expected phase colors while Sodium64 control/treatment are equal or otherwise fail exact expected RGB5 despite verified register state. **Falsifier for this half path:** Sodium64 raw central field matches both exact expected RGB5 values under the correct phase/register tuple. No compositor repair is authorized until this discriminator runs.

- **2026-09-20 WH urgent repair — MERGED-CONSUMED / master advanced:** PR #14 `Gate C: preserve per-line window edges at medium precision` was merged by squash with expected head pinned to `8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec`. New integrated truth is **`master@5b7134930a0ca859f6aa24e54102de116948e3ed`**. Post-merge verification: `master:src/ppu.S` blob is exactly **`1085f2a253e1522268c6ebb430086fd318ddfa6e`**, byte-identical to the fully validated candidate. PR #14 is closed/merged. The integrated repair therefore preserves all 224 directed WH0 states at Road-valid MEDIUM in the validated path, with directed and mixed virtual frame-budget controls at 60/60; real-N64 cadence remains milestone authority. PR #13 remains open/unmerged at `84ecafad...`; immediately after master moved GitHub reports its old-base mergeability false, so treat that state as stale/needs refreshed integration audit rather than a new semantic failure. Do **not** merge PR #13 from this state; its separate real-hardware overlay DMA/bus/cadence boundary still applies.

- **2026-09-20 PR #14 standard PR CI — CLOSED GREEN:** exact frozen head `8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec`; **Ares Profile Validation `35541991618 SUCCESS`**. Jobs: `profile-build 106161197161 SUCCESS`, `ares-smoke 106161350023 SUCCESS`. Artifacts: **`10614913990 sodium64-ares-profile-build`** (`sha256:e7a08d2d132ceb34e6ab59ad99e62fe5e5abb7e09b538a7fadcf13c759f4d9f9`) and **`10615477058 sodium64-ares-profile-matrix`** (`sha256:d60af750695b2768eb5008e9a206dbba7ce12bdf84a2e517a3b6f8dcc05e7e8c`). GitHub reports PR #14 **open, unmerged, mergeable=true**, 1 commit / 1 file / +12 -4. Together with exact-head Build/Validate `35539917561`, directed semantic `35539983428`, directed virtual-budget `35540459680`, and mixed rendering semantic+budget `35541332012`, there is no remaining standard CI or lower-level semantic blocker for the narrow WH repair. **Remaining limitation:** real-N64 cadence is still milestone authority, but `VALIDATION.md` does not require a dedicated pre-merge hardware session for every narrow reversible non-low-level PPU repair. Next action: apply merge policy and integrate PR #14 if no new repo conflict/state change appears.

- **2026-09-20 PR #14 post-open CI — RUNNING / mergeable:** GitHub now reports **PR #14 mergeable=true** at unchanged head `8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec`. Opening the PR triggered **Ares Profile Validation `35541991618`** on the exact candidate; `profile-build 106161197161 SUCCESS`, `ares-smoke 106161350023` currently in progress (dependency setup at checkpoint). Exact-head Build/Validate `35539917561` and all dedicated H-SAMPLE/mixed semantic+budget evidence remain green. **Pass reading:** PR-triggered ares workflow completes SUCCESS, leaving no standard pre-integration CI blocker for this narrow PPU repair. **Fail reading:** classify the first failing ares step before any source change; do not conflate lab/harness failures with the already-validated WH semantics. Under `VALIDATION.md`, real hardware is still milestone authority for final cadence but a dedicated pre-merge L4 session is not required for this reversible non-low-level PPU change.

- **2026-09-20 WH-urgent promotion — PR #14 OPEN / exact frozen candidate:** opened **PR #14 `Gate C: preserve per-line window edges at medium precision`** from `phase4/gate-c-h-sample-wh-urgent` to `master`, preserving head exactly **`8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec`** and base `9441818dd8457a27bbd617a0f32c6d484550661f`. GitHub reports 1 commit / 1 changed file / +12 -4, matching the audited source-only delta. PR body records causality (MEDIUM32 vs MAX224), repaired MEDIUM224 semantics, directed virtual60/60, mixed BG/OBJ/DMA + WH 224/224 + virtual60/60, guest SHA and limits. Validation-only branches/files are excluded. Initial creation response reports mergeable=false while GitHub computes mergeability; **do not interpret that initial value as conflict yet**. PR #13 remains separate and source-disjoint. **Immediate next action:** inspect PR-triggered checks and refreshed mergeability for exact head; if standard PR CI is green, decide integration under `VALIDATION.md` merge policy without inventing a dedicated hardware test for this narrow reversible PPU repair.

- **2026-09-20 WH-urgent final promotion audit — PASS / PR-ready:** integrated base remains exactly `master@9441818dd8457a27bbd617a0f32c6d484550661f`. Frozen technical candidate `phase4/gate-c-h-sample-wh-urgent@8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec` is **1 commit ahead / 0 behind** and changes exactly one file, `src/ppu.S` (+12/-4). Candidate and all semantic/budget validation descendants (`658d961e...`, `9cc69e0c...`, `e49b8331...`) carry the exact same `ppu.S` blob **`1085f2a253e1522268c6ebb430086fd318ddfa6e`**. Candidate Build/Validate `35539917561 SUCCESS`; direct H-SAMPLE semantics `35539983428 SUCCESS`; directed 224-line budget `35540459680 SUCCESS` at virtual 60/60; mixed BG/OBJ/DMA + 224-line WH semantics/budget `35541332012 SUCCESS` at 224/224 WH and virtual 60/60; mixed validation-child Build/Validate `35541331985 SUCCESS`. PR #13 changes only `src/defines.h`, `src/main.S`, `src/rsp_main.S`, `src/rsp_mode7.S`; WH candidate changes only `src/ppu.S`, so source deltas are disjoint. Only open PR is #13. **Decision:** WH candidate is PR-ready under `VALIDATION.md` merge policy: narrow, reversible PPU semantic repair with strong L1/L2 evidence; real-N64 cadence remains milestone authority but does not require a dedicated pre-PR hardware session. Next action: open PR from the frozen technical branch to master, preserving exact SHA and excluding all validation-only files.

- **2026-09-20 WH-urgent mixed rendering validation — VALIDATED 224-state semantics + virtual 60/60:** exact validation head `phase4/gate-c-h-sample-wh-mixed-validation@e49b833100bc9ce4094db68350f0eb22d5cc4556`; **Gate C WH Mixed Rendering Validation `35541332012 SUCCESS`**, job `106159437587`, evidence artifact **`10614608059 gate-c-wh-mixed-rendering-evidence`** (`sha256:b3fd3147180c59657b24432bbbab617878f90b2e3221d41d047bb6bbd1b61961`). Same-head Build/Validate **`35541331985 SUCCESS`**. Deterministic 32 KiB original guest was generated twice byte-identically, SHA256 **`0deb02458757f7d4bb86057b441949c16fa269bd3b1ee042632174817b2f9146`**, and exact guest identity survived wrapping. Workload retains gameplay-balanced Mode1 BG1 + visible OBJ + frame-paced logic + scroll + OAM/VRAM/CGRAM DMA and adds only channel-3 HDMA WH0 `0..223` plus BG1 windowing. Semantic capture on exact candidate at initialized **MEDIUM `precision_set=8`** produced **224 records / 224 unique WH0**, exact `0..223`, `max_end_line_step=1`. Fresh budget instance at verified Road-valid settings (`frameskip=0`, `APU=21`, `audio=4`, `precision=8`) produced completed **`fps_display=60/60`**; partial stop window was `15/60` VI with 15 guest frames. **SUPPORTED INTERPRETATION:** the narrow WH0..WH3 urgent-section repair preserves full per-line window state and still meets the virtual N64 frame target when combined with deterministic BG/OBJ rendering and ordinary per-frame DMA work. This is materially stronger than the earlier blank/simple WH stress. **Still not real-N64 authority** and not a claim of full SMW iris/color-math correctness. Candidate remains frozen `phase4/gate-c-h-sample-wh-urgent@8be82f5f...` with one `src/ppu.S` change only. **Decision:** candidate is technically PR-ready under current merge policy; perform final exact-head/master/PR13/disjointness audit, then open a PR from the frozen technical branch only (no validation plumbing).

- **2026-09-20 WH mixed validation-child Build/Validate — GREEN:** exact validation head `phase4/gate-c-h-sample-wh-mixed-validation@e49b833100bc9ce4094db68350f0eb22d5cc4556`; **Build and Validate `35541331985 SUCCESS`** with normal build, PROFILE build and emulator-smoke successful (`update-release` skipped). Its `src/ppu.S` blob is byte-identical (`1085f2a2...`) to frozen technical candidate `8be82f5f...`. Therefore any outcome in mixed semantic/budget run `35541332012` is not a generic build/boot divergence introduced by validation plumbing.

- **2026-09-20 WH-urgent mixed rendering validation — DISPATCHED / candidate untouched:** created validation child **`phase4/gate-c-h-sample-wh-mixed-validation@e49b833100bc9ce4094db68350f0eb22d5cc4556`** directly over frozen technical candidate `8be82f5f...`. Exact delta from candidate is validation-only: `.github/workflows/gate-c-wh-mixed-validation.yml`, `scripts/gate_c_wh_mixed_capture_n64.py`, `scripts/make_gate_c_wh_mixed.py`; **no runtime/core file differs**. The new deterministic ROM is derived from existing `gameplay-balanced` and retains Mode1 BG1, one visible OBJ, frame-paced game logic, scroll, OAM DMA, VRAM DMA and CGRAM DMA while adding dedicated HDMA channel 3 (`WH0=0..223`) plus BG1 main-screen windowing. Its NMI is isolated at `$8200` so the added setup cannot collide with the original fixed `$8100` gameplay handler; HDMA table is at `$9400`. Workflow generates the guest twice and byte-compares it for determinism, wraps/verifies exact 32 KiB guest identity, then runs two fresh pinned-ares controls on the exact candidate: **semantic guard** requires initialized MEDIUM `precision_set=8`, full WH0 set `0..223`, final section and max end-line gap <=1; **budget guard** applies frameskip0/APU21/audio4/precision8 and requires Sodium64 internal `fps_display >= 60` over a completed 60-VI window. Dispatched **Gate C WH Mixed Rendering Validation `35541332012`** and same-head **Build and Validate `35541331985`**. If budget fails after semantic exercise is proven, run the identical guest on unchanged `master@9441818d...` before attributing regression.

- **2026-09-20 WH-urgent mixed-render discriminator — DESIGNED / no runtime change:** after the directed 224-line WH stress sustained virtual `60/60`, the next validation step is a more representative deterministic control built from existing `gameplay-balanced`: retain Mode1 BG1, one visible OBJ, frame-paced game logic, scroll, 544-byte OAM DMA, 128-byte VRAM DMA and 32-byte CGRAM DMA; add only **HDMA channel 3** writing `WH0=0..223` once per visible line, plus BG1 main-screen window enable. Channels 0-2 remain dedicated to the workload's existing per-frame DMA, so the added variable is raster windowing rather than replacing its normal rendering work. Validation must use a child branch from frozen candidate `8be82f5f...`, not modify the technical branch. Two guards in one lab: (1) capture completed section queue at initialized MEDIUM `precision_set=8` and require all WH0 values `0..223` to prove the mixed workload really exercises per-line urgent sections; (2) fresh ares instance at frameskip0/APU21/audio4/precision8 must complete an internal `fps_display=60/60` window. If candidate misses budget, run the identical guest on unchanged `master` before attributing cost. This remains L2/lab evidence; real N64 is final cadence authority.

- **2026-09-20 H-SAMPLE WH urgent directed frame-budget — MEASURED 60/60 in virtual N64 lab:** exact budget sibling `phase4/gate-c-h-sample-wh-urgent-budget-validation@9cc69e0cf5d8521e2f7e2c8bf16a330e50db4284`; **Gate C H-SAMPLE WH Urgent Budget `35540459680 SUCCESS`**, job `106157040393`, evidence artifact **`10614806573 gate-c-h-sample-wh-urgent-budget`** (`sha256:02f5a215d0b13d3c4798b9abb8eed53f0fd04b5996069f4e7586fdfa679e9764`). Same-head Build/Validate **`35540459595 SUCCESS`** with build/profile/emulator-smoke green. The exact repaired candidate was run in pinned ares valid lab mode with explicitly verified Road-valid settings: `skipped_set=0`, `apu_clock=21`, `audio_set=4`, `precision_set=8`. After settle/reset, Sodium64's internal frame-budget counter reports a completed **`fps_display=60/60`** VI window; current partial window at stop was `fps_native=24/60`, `fps_emulate=24`, queue=1. This guest changes WH0 every visible line and the semantic proof shows the repair preserves 224 per-line states, so the run is a directed high-section-count stress. **SUPPORTED INTERPRETATION:** the narrow WH correctness repair does not create an obvious virtual-N64 frame-budget deficit even when exercised every visible line. **Not hardware authority:** ares host wall time is irrelevant and real N64 remains final performance authority. **Limitation:** the current H-SAMPLE guest is graphically simple, so this does not yet bound the cost of 224 sections carrying representative BG/OBJ rendering work. **Decision / next batch:** before promotion/hardware milestone, add one deterministic mixed rendering+WH workload (actual BG + OBJ + per-line window changes) and measure candidate at the same Road-valid settings; compare against unchanged baseline if a deficit appears so cost is attributed before any redesign.

- **2026-09-20 H-SAMPLE WH urgent cadence lab — DISPATCHED / virtual budget, not hardware authority:** created sibling `phase4/gate-c-h-sample-wh-urgent-budget-validation@9cc69e0cf5d8521e2f7e2c8bf16a330e50db4284` directly from frozen technical candidate `8be82f5f...`. Exact delta from candidate is one budget workflow + two deterministic guest scripts; no extra runtime/core files. Workflow builds exact candidate normal runtime, regenerates/verifies guest SHA `347e177c...`, runs pinned ares in valid R4300-JIT/RSP-interpreter mode, explicitly applies Road-valid **frameskip0, APU clock21, audio4, precision8**, settles, resets Sodium64's internal FPS interval counters, then measures and requires a completed 60-VI interval with `fps_display >= 60`. This workload changes WH0 every visible line; after the validated repair it exercises ~224 section states/frame and is therefore a directed worst-case section-count stress, not a representative commercial game. Dispatched **Gate C H-SAMPLE WH Urgent Budget `35540459680`** plus same-head Build/Validate `35540459595`. **Interpretation:** 60/60 is useful L2 lab evidence that the correctness repair does not create an obvious virtual N64 budget deficit in this directed stress; below target requires baseline comparison before blaming the repair. Neither outcome replaces real-N64 performance authority.

- **2026-09-20 H-SAMPLE WH urgent repair — VALIDATED semantic fix at Road-valid MEDIUM:** frozen technical candidate `phase4/gate-c-h-sample-wh-urgent@8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec`; validation head `phase4/gate-c-h-sample-wh-urgent-validation@658d961ed896032d0af186b72f71e6a7ceadcdaf` carries the exact same `src/ppu.S` blob `1085f2a2...`. **Gate C H-SAMPLE WH Urgent Validation `35539983428 SUCCESS`**, job `106155774210`, evidence artifact **`10614436889 gate-c-h-sample-wh-urgent-evidence`** (`sha256:243e2b26e9eae4e6c086e0f2f54a3307ecc400f9e98604b079665762967154b6`). At default initialized **`precision_set=8` (MEDIUM)** the exact deterministic guest now yields **224 records / 224 unique WH0 states**, `unique_wh0_exact_0_to_223=true`, `max_end_line_step=1`, classification **`H_SAMPLE_WH_URGENT_PASS`**. Before repair, the unchanged core produced 32 unique states under MEDIUM; diagnostic MAX produced 224. Therefore the narrow WH0..WH3 urgent-section path recovers full per-line window-edge state **without globally switching precision to MAX**. Candidate Build/Validate `35539917561 SUCCESS` is also green. **What this proves:** H-SAMPLE's demonstrated WH-edge coalescing defect is repaired at the section producer/consumer boundary under Road-valid MEDIUM. **What this does NOT prove:** full SMW iris/color-math correctness, other raster-sensitive PPU registers, commercial-game compatibility, or real-N64 cadence cost. **Next gate-relevant batch:** measure virtual N64 frame budget for the repaired worst-case 224-line WH workload at frameskip0/APU21/audio on/precision8; if no virtual deficit appears, then decide whether to add a more representative mixed rendering+WH workload before promotion/hardware milestone.

- **2026-09-20 H-SAMPLE WH urgent validation-child Build/Validate — GREEN:** exact validation head `phase4/gate-c-h-sample-wh-urgent-validation@658d961ed896032d0af186b72f71e6a7ceadcdaf`; **Build and Validate `35539983290 SUCCESS`** with normal build, PROFILE build and emulator-smoke green (`update-release` skipped). Validation child uses the exact same `src/ppu.S` blob `1085f2a2...` as frozen technical candidate `8be82f5f...`; only workflow/scripts differ. Therefore the remaining semantic run `35539983428` is testing the exact candidate bytes, not a divergent runtime.

- **2026-09-20 H-SAMPLE WH urgent footprint — MEASURED / negligible and outside RSP IMEM:** exact candidate Build job `106155605941` reports final ROM still **98,304 bytes**, ELF **794,796 bytes**, and `rsp_main.elf` text still **4056/4096 bytes**. The unchanged-master reference previously measured ELF 794,760 bytes, so this one-file CPU-side helper adds only **36 ELF bytes** while packaged ROM allocation remains unchanged. Crucially, it consumes **no additional RSP IMEM**, so it does not worsen the 40-byte master RSP headroom problem addressed separately by PR #13. This is footprint evidence only, not runtime-cost authority.

- **2026-09-20 H-SAMPLE WH urgent candidate Build/Validate — GREEN:** exact source-only head `phase4/gate-c-h-sample-wh-urgent@8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec`; **Build and Validate `35539917561 SUCCESS`** with normal build, PROFILE build and pinned Mupen/LLE emulator-smoke all successful (`update-release` skipped). This removes compile/boot/smoke as blockers for the one-file WH urgent repair. It does **not** establish semantic correctness or real-N64 cadence; those remain separate. Active semantic authority is validation-child run `35539983428`.

- **2026-09-20 H-SAMPLE WH urgent semantic validation — DISPATCHED / candidate hygiene preserved:** frozen technical candidate remains `phase4/gate-c-h-sample-wh-urgent@8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec` with only `src/ppu.S` changed. Created validation child **`phase4/gate-c-h-sample-wh-urgent-validation@658d961ed896032d0af186b72f71e6a7ceadcdaf`**; exact delta from candidate is one branch-only workflow plus three H-SAMPLE scripts, no additional runtime/core changes. Workflow regenerates exact original guest SHA `347e177c...`, builds the exact candidate, wraps/verifies guest identity, runs pinned N64 ares with RSP interpreter, captures the completed section queue at default initialized `precision_set=8`, and asserts: final section reached, end-line gaps <=1, and the set of queued WH0 values is **exactly `0..223`**. Evidence uploads even on failure. Dispatched **Gate C H-SAMPLE WH Urgent Validation `35539983428`** and validation-child Build/Validate `35539983290`. Candidate's own Build/Validate `35539917561` remains separate. **Pass:** establishes the narrow WH repair recovers per-line window state at Road-valid MEDIUM without globally selecting MAX. **Fail:** reject or refine the one-variable repair before any PR/promotion.

- **2026-09-20 H-SAMPLE WH urgent-section repair — IMPLEMENTED candidate / validation pending:** created independent technical branch **`phase4/gate-c-h-sample-wh-urgent@8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec`** directly from integrated `master@9441818d...`, not from PR #13. Exact delta is **one commit, one file `src/ppu.S`, +12/-4**. Added `update_window_frame`, which writes exact `0x0100` to `sect_status` (dirty high byte + zero countdown low byte), and changed only `write_wh0`, `write_wh1`, `write_wh2`, `write_wh3` changed-value branches to use that helper. `WOBJSEL`, window logic selection, other PPU writes and generic `update_frame` remain untouched. This is deliberately narrower than MAX precision: only changed window edges request the next section immediately; normal MEDIUM adaptation resumes afterward. **Expected proof:** exact H-SAMPLE guest at default `precision_set=8` should preserve all/near-all 224 distinct WH0 states rather than the validated 32-state recurrence. **Falsifier:** queue still coalesces under MEDIUM, or unrelated behavior/build regresses. Build and Validate **`35539917561`** dispatched automatically. Next batch: freeze this source-only candidate and create a validation child carrying only the H-SAMPLE harness; do not add diagnostic files to the technical branch.

- **2026-09-20 H-SAMPLE cooldown causality — VALIDATED:** exact diagnostic head `phase4/gate-c-h-sample-precision-control@40ec0c445936401c2bba8ba0f1f096e65fcccf79`; **Gate C H-SAMPLE Precision Control `35539461721 SUCCESS`**, semantic job `106154392705`, evidence artifact **`10614685621 gate-c-h-sample-precision-control`** (`sha256:4c4c43c333f23e71b7f7739dd0880f7cae4625bad424d19246cfbf10357693e0`). Same unchanged Sodium64 core + same deterministic guest were captured under two precision states. MEDIUM initialized at `precision_set=8` and reproduced the exact adaptive fingerprint: **32 records / 32 unique WH0 states**. MAX initialized at 8, was patched post-init and verified at **`precision_set=20`**, then produced **225 records / 224 unique WH0 states** after additional complete frames. Comparator reports **`PRECISION_CONTROL_SUPPORTS_H_SAMPLE_COALESCING`**, `medium_exact_cooldown_fingerprint=true`, `unique_gain=192`. This independently isolates precision cooldown as the cause of lost semantically distinct per-line window states; the rejected WRAM mirror is no longer needed for attribution. **Meaning:** Road-valid MEDIUM can collapse distinct WH0 raster states; MAX preserves all 224 distinct values in this directed path. **Does NOT prove:** that MAX is globally required/desirable, that all PPU state needs urgent sections, or that the eventual correctness repair is free on real N64. **Decision:** promote H-SAMPLE from hypothesis to VALIDATED and proceed with the previously-audited minimal repair: only changed `WH0..WH3` writes force `sect_status=0x0100`, leaving generic MEDIUM adaptation intact. Candidate should branch independently from `master` because `src/ppu.S` is untouched by PR #13.

- **2026-09-20 H-SAMPLE block-end checkpoint — ACTIVE CONTROL / resume here:** integrated truth remains `master@9441818dd8457a27bbd617a0f32c6d484550661f`; PR #13 remains separate/open. H-SAMPLE precision-control attempt 1 was correctly rejected as a pre-init harness timing error. Repaired diagnostic sibling is **`phase4/gate-c-h-sample-precision-control@40ec0c445936401c2bba8ba0f1f096e65fcccf79`**, still validation-only versus clean runtime; same-head **Build and Validate `35539461720 SUCCESS`**. Active long experiment is **Gate C H-SAMPLE Precision Control `35539461721`**, job **`106154392705`**. At this checkpoint: diagnostic-build SUCCESS; exact unchanged Sodium64 build SUCCESS; exact guest wrap/hash SUCCESS; state symbols SUCCESS; pinned ares dependencies SUCCESS; current step **`Build pinned N64-only ares in valid lab mode`** remains in progress. After that the workflow will capture default MEDIUM then post-init forced MAX and compare completed section queues. **Interpretation gate:** if MEDIUM reproduces the exact 32-section recurrence and MAX preserves ~224 distinct WH0 states with captured `precision_set=20`, promote cooldown causality to VALIDATED and implement the already-audited minimal WH0..WH3 urgent-section repair from `master`; if MAX is only marginal/intermediate, investigate before any core change; if the post-init precision patch still fails/sticks only in debugger memory, repair the control (potential fallback: diagnostic build with only default precision initializer changed) rather than touching runtime semantics. Minimal repair source contract is pinned above: generic `update_frame` preserves countdown; WH-only urgent path should set exact `sect_status=0x0100`, forcing next-line snapshot while retaining MEDIUM adaptation elsewhere.

- **2026-09-20 H-SAMPLE precision-control attempt 2 same-head validation — GREEN:** exact head `phase4/gate-c-h-sample-precision-control@40ec0c445936401c2bba8ba0f1f096e65fcccf79`; **Build and Validate `35539461720 SUCCESS`** with normal build, PROFILE build and emulator-smoke all successful (`update-release` skipped). The post-init precision-patch repair therefore introduces no compile/smoke regression and still leaves runtime/core bytes unchanged. Semantic precision-control run `35539461721` remains the sole active discriminator.

- **2026-09-20 H-SAMPLE minimal-repair source audit — READY IF CONTROL PASSES:** exact `master` PPU layout confirms `sect_status` is a big-endian halfword whose high byte is dirty and low byte is current countdown. Generic `update_frame` executes `sb 1, sect_status`, preserving the low-byte countdown; `run_line` only emits when the resulting halfword reaches exactly `0x0100`. Therefore a changing WH register can remain dirty while old cooldown delays emission. Minimal one-variable repair is a new raster-urgent helper that writes exact **`0x0100`** to `sect_status` and routing only `write_wh0..write_wh3` changed-value branches through it. This preserves generic MEDIUM adaptation for every other PPU register and only forces the next scanline snapshot after window-edge changes. Expected diagnostic result at Road-valid `precision=8`: same H-SAMPLE guest should move from the current 32-section recurrence to per-line preservation (target ~224 distinct WH0 states, subject to first-line/end-frame semantics). **HYPOTHESIS only; do not implement unless precision-control attempt 2 validates cooldown causality.**

- **2026-09-20 H-SAMPLE precision-control attempt 2 — DISPATCHED / patch timing repaired only:** sibling advanced to **`phase4/gate-c-h-sample-precision-control@40ec0c445936401c2bba8ba0f1f096e65fcccf79`**. Delta versus frozen clean core remains validation-only: two workflows + five scripts; **no `src/`, Makefile or emulator/runtime file differs**. Capture helper now first releases the Boot/AwaitGDB stop, warms Sodium64 until runtime `.data` is initialized, records initialized precision, then (MAX case only) patches `precision_set=20`, verifies immediate readback, runs an additional warm/settle interval and captures the completed queue. Guest ROM/hash, clean core, MEDIUM case, queue parser and comparison logic are unchanged. Dispatched **Gate C H-SAMPLE Precision Control `35539461721`** and same-head **Build and Validate `35539461720`**. **Pass:** initialized precision should be 8; forced MAX should read back/stay 20 and produce a materially denser queue than the exact 32-section MEDIUM fingerprint. **Fail:** if post-init patch still cannot stick, classify debugger memory-write semantics before changing any core code.

- **2026-09-20 H-SAMPLE precision-control attempt 1 — HARNESS TIMING FAILURE / MEDIUM reproduced:** exact branch `phase4/gate-c-h-sample-precision-control@5c7cc25eae27c3e2695185c7a2ee9b52bedd150d`; run **`35536320835 FAILURE`**, job `106145908436`, artifact **`10613312504 gate-c-h-sample-precision-control`** (`sha256:4b6d9f875fa77aa4e545ce6944c163ff018945a73ff9ea177e20331496cb42a8`). MEDIUM control booted and again captured a complete **32-record** queue at `precision=8`, reproducing the prior fingerprint. MAX case failed before guest execution: at the initial `Boot/AwaitGDBClient` stop, `precision_set` reads `0` (runtime `.data` not initialized yet); the helper attempted the diagnostic patch at that pre-init stop and immediate readback remained `0`, raising `precision patch failed: expected 20, got 0`. **REJECTED:** interpreting this run as evidence about MAX or H-SAMPLE. Root cause is harness patch timing. Controlled repair: first allow Sodium64 to initialize/execute to a normal warm stop, then patch `precision_set=20`, verify readback, run additional complete frames, and only then capture the completed queue. Guest/core/queue parser/comparison logic remain unchanged.

- **2026-09-20 H-SAMPLE block-end checkpoint — RESUME HERE:** integrated truth is still `master@9441818dd8457a27bbd617a0f32c6d484550661f`; PR #13 remains separate/open as previously recorded. H-SAMPLE diagnosis has advanced materially: two MEDIUM captures on unchanged core independently reproduce the exact 32-section adaptive cooldown fingerprint; the auxiliary WRAM mirror guard is REJECTED because GDB observes 224 zero bytes and therefore cannot serve as source authority in this lab; the exact recurrence match remains strong supported evidence. Independent control is now **`phase4/gate-c-h-sample-precision-control@5c7cc25eae27c3e2695185c7a2ee9b52bedd150d`**, with no runtime/source delta and same-head Build/Validate **`35536320805 SUCCESS`**. Active long experiment: **Gate C H-SAMPLE Precision Control `35536320835`**, job **`106145908436`**; at checkpoint `diagnostic-build` is SUCCESS and `precision-control` is still in `Build pinned N64-only ares in valid lab mode` after unchanged core build, exact guest wrap, symbol location and dependency setup all passed. **Question:** does same guest/core at diagnostic MAX `precision_set=20` produce a materially denser/per-line WH0 section queue than Road-valid MEDIUM `8`? **Pass/support:** MEDIUM exact fingerprint + MAX materially denser (ideally near full 224 unique states) => promote H-SAMPLE cooldown causality to VALIDATED and implement the staged independent `WH0..WH3` urgent-section repair from `master`. **Fail:** MAX similar to MEDIUM => reject/simple-cooldown attribution and inspect producer/HDMA mapping before any core change. **If harness precision patch does not stick:** repair only capture timing/patch placement and rerun. Do not touch runtime until this control is interpreted.

- **2026-09-20 H-SAMPLE repair staging audit — INDEPENDENT / HYPOTHESIS only:** `src/ppu.S` blob is exactly identical on `master@9441818d...` and clean overlay candidate `84ecafad...` (`a88f89d3...`). Therefore a future H-SAMPLE repair does not need to stack on PR #13 and can be developed from `master` as an independent candidate, then combined without touching the overlay/H-OBJ files. Smallest falsifiable repair if precision control confirms causality: add a raster-sensitive dirty path that marks `sect_status=0x0100` (dirty + zero current countdown) and route only `WH0..WH3` changes through it first. Because HDMA runs after the current line snapshot, this should force the changed window state into the next scanline section while leaving adaptive precision behavior for unrelated PPU writes unchanged. **Not implemented yet.** Required proof before promotion: MEDIUM-vs-MAX control must first validate H-SAMPLE; then exact queue regression must show per-line WH preservation at MEDIUM, followed by Build/Validate and cadence/regression checks. If the control does not support cooldown causality, discard this repair hypothesis.

- **2026-09-20 H-SAMPLE precision-control same-head validation — GREEN:** exact sibling head `phase4/gate-c-h-sample-precision-control@5c7cc25eae27c3e2695185c7a2ee9b52bedd150d`; **Build and Validate `35536320805 SUCCESS`** with normal build, PROFILE build and emulator smoke green (`update-release` skipped). This confirms the diagnostic precision override/workflow additions did not alter or break the unchanged clean runtime. Semantic precision-control run `35536320835` remains the only active question.

- **2026-09-20 H-SAMPLE attempt 2 — WRAM mirror guard REJECTED / queue fingerprint reproduced exactly:** exact head `phase4/gate-c-h-sample-diagnostic@bee00d3354986cc5b805da24f785eea4752369d5`; run **`35535930849 FAILURE`**, semantic job `106144860421`, preserved evidence artifact **`10613121296 gate-c-h-sample-sodium64-evidence`** (`sha256:f1359c20680f6db5a9b75e103064519011b175df23e4fb2483e49931c98e8172`). All pre-capture gates passed. Capture again reports `frame_counter=2`, `cur_line=150`, `precision_set=8`, complete previous-frame queue and **exactly the same 32-record MEDIUM fingerprint** as attempt 1. New probe diagnostics show `probe_length=224`, **`probe_mismatch_count=223`**, and both head/tail are all zeros; only index0 matches trivially because expected byte0 is also zero. Therefore the WRAM-mirror guard is **REJECTED as an observation mechanism** for this lab: GDB did not observe the channel-1 WMDATA mirror at all. This does not falsify channel-0 WH0 HDMA, whose queued values/boundaries independently reproduce the exact adaptive cooldown recurrence twice. Likely explanations include cached-WRAM visibility or the auxiliary channel path; do not turn either into a side project. **Decision:** stop using WRAM mirror as authority. The correct independent discriminator is the already-dispatched same-guest MEDIUM-vs-MAX section-queue control `35536320835`. Attempt 2 remains red by design because its old assertion requires the rejected guard; do not treat it as core failure.

- **2026-09-20 H-SAMPLE diagnostic core-identity audit — PASS:** frozen candidate and both active H-SAMPLE branches have byte-identical technical blobs: `src/defines.h 2e4a318a...`, `src/main.S 3d793d18...`, `src/rsp_main.S bfbceb81...`, `src/rsp_mode7.S 8e6ab79a...`. This holds for clean `84ecafad...`, observability branch `phase4/gate-c-h-sample-diagnostic`, and precision-control sibling `phase4/gate-c-h-sample-precision-control`. Therefore neither active experiment has silently changed the emulator/core bytes under test; differences are diagnostic plumbing / precision setting only.

- **2026-09-20 H-SAMPLE MEDIUM-vs-MAX control — DISPATCHED on sibling / no runtime delta:** created `phase4/gate-c-h-sample-precision-control@5c7cc25eae27c3e2695185c7a2ee9b52bedd150d` from the observability diagnostic lineage while leaving attempt-2 branch/run untouched. Compared with frozen clean core `84ecafad...`, the sibling differs only by two H-SAMPLE workflows plus five scripts; **no `src/`, Makefile or emulator/runtime file differs**. Capture helper gains only a diagnostic `--force-precision` byte patch, verified through GDB before guest execution. New workflow runs the exact same deterministic guest/core twice against one pinned ares build: default **MEDIUM `precision_set=8`** and diagnostic-only **MAX `precision_set=20`**, then compares completed section queues. Queue capacity is 320 records, so a 224-line MAX control cannot overflow by design. It records the exact MEDIUM recurrence fingerprint and whether MAX materially increases unique WH0 states; WRAM mirror remains captured but is not required for this independent control. Dispatched **Gate C H-SAMPLE Precision Control `35536320835`** and same-head **Build and Validate `35536320805`**. **Interpretation:** exact MEDIUM fingerprint + substantially denser MAX queue supports cooldown causality; similar MEDIUM/MAX density weakens it; this experiment does not propose shipping MAX and does not modify Road-valid runtime settings.

- **2026-09-20 H-SAMPLE attempt-1 recurrence audit — EXACT MATCH / supported interpretation strengthened:** independent reconstruction of the clean `MEDIUM` section algorithm (`cooldown` base starts at 16; after each emitted dirty section the current base contributes `base >> 2`, then base increments by 1) predicts section terminal lines **`1,5,9,13,17,22,27,32,37,43,49,55,61,68,75,82,89,97,105,113,121,130,139,148,157,167,177,187,197,208,219`** before final frame flush at 224. Attempt-1 capture produced exactly those boundaries, and its queued WH0 sequence `0,1,5,9,...,208,219` exactly matches the prior boundary/source state expected from HDMA-after-snapshot ordering. **SUPPORTED INTERPRETATION:** the 32-record queue is not a generic parser artifact; it is precisely the fingerprint of the adaptive MEDIUM cooldown operating on continually changing WH0 state. This materially strengthens H-SAMPLE causality. **Still not promoted to VALIDATED** because the independent WRAM source guard failed and remains under attempt-2 investigation; retain the formal requirement for an independent dynamic control (fixed mirror or MEDIUM-vs-MAX).

- **2026-09-20 H-SAMPLE attempt 2 same-head validation — GREEN:** exact diagnostic head `phase4/gate-c-h-sample-diagnostic@bee00d3354986cc5b805da24f785eea4752369d5`; **Build and Validate `35535930772 SUCCESS`** with `build`, `profile-build`, and `emulator-smoke` all successful (`update-release` skipped). The only delta from frozen clean core remains one workflow + five scripts. Therefore any semantic outcome in paired H-SAMPLE run `35535930849` is not attributable to a compile/smoke/runtime regression introduced by the observability edits.

- **2026-09-20 H-SAMPLE fallback discriminator — SOURCE-VALIDATED design, not yet dispatched:** exact clean source confirms a stronger control is available if the WRAM mirror proves debugger/cache-confounded. Each section record is `SECTION_SIZE=0x40` and each queue is `0x5000`, so one queue holds **320 records**, enough for all 224 visible per-line states plus framing records without capacity pressure. `precision_set` values are menu index×4; Road-valid default MEDIUM is `8` and selects `section_vals=0x021001` (shift2/min16/inc1), while MAX is `20` and selects `0x000100` (shift0/min1/inc0). Therefore the same deterministic HDMA guest can be run twice on unchanged core: MEDIUM treatment versus a debugger-patched MAX control. If MAX preserves the near/full per-line WH0 sequence while MEDIUM reproduces the 32-state adaptive pattern, cooldown causality is established without relying on cached WRAM observation. If both coalesce similarly, H-SAMPLE attribution to precision cooldown is weakened and the producer/HDMA path must be re-examined. This is a diagnostic setting override only, not a proposal to ship MAX or change Road-valid settings.

- **2026-09-20 H-SAMPLE attempt 2 observability repair — DISPATCHED / harness-only:** diagnostic branch advanced to **`phase4/gate-c-h-sample-diagnostic@bee00d3354986cc5b805da24f785eea4752369d5`**. Exact clean-parent delta remains only `.github/workflows/gate-c-h-sample.yml` plus five `scripts/` files; **no `src/`, Makefile or runtime file differs**. Changes from attempt 1 are observability-only: analyzer now reports probe length, total mismatch count, first 32 `(index, expected, actual)` mismatches and probe head/tail bytes; evidence upload now uses `if: always()` so capture/analysis survive a failed semantic assertion. Guest generator/ROM SHA, clean core bytes, HDMA tables, queue parser and expected classification are unchanged. Dispatched **Gate C H-SAMPLE Diagnostic `35535930849`** and same-head **Build and Validate `35535930772`**. **Question:** why did the WRAM mirror guard fail while the queue showed a 32-state adaptive pattern? Next reading must come from exact probe bytes, not inference. If probe mismatch is a harness/address/phase artifact, repair only that; if probe proves guest HDMA itself is not producing the intended sequence, redesign the guard before any H-SAMPLE conclusion.

- **2026-09-20 H-SAMPLE attempt 1 — INDETERMINATE guard failure / strong coalescing signal, not yet authority:** exact diagnostic `phase4/gate-c-h-sample-diagnostic@8f818364023347e594c2b59e1b865358e8d96ebc`; run **`35535273374 FAILURE`**, semantic job **`106143083705`**. All construction/runtime preconditions passed: harness tests, deterministic guest SHA, unchanged clean Sodium64 build, wrapped-guest identity, symbol location, pinned N64 ares build and GDB capture. Capture stopped with `frame_counter=2`, `cur_line=150`, `precision_set=8` and successfully parsed a complete previous-frame queue ending at line 224. That completed queue contains only **32 records / 32 unique WH0 values** rather than 224; sequence begins `(end,WH0)=(1,0),(5,1),(9,5),(13,9),(17,13),(22,17)...` and ends `(208,197),(219,208),(224,219)`, with **192 source WH0 values absent**, `max_end_line_step=11`, `max_wh0_forward_step=11`. This shape is strongly consistent with the statically predicted adaptive section cooldown/coalescing. However the independent WRAM HDMA mirror did **not** equal exact bytes `0..223`, so analyzer correctly classified **`INDETERMINATE_HDMA_SOURCE_SEQUENCE`** and CI failed rather than overclaiming H-SAMPLE. **Decision:** do NOT promote the 32-record pattern to validated core evidence yet. First diagnose the mirror itself. Next controlled harness-only change: preserve/upload evidence even on assertion failure and expose exact probe mismatch indices/values; if needed synchronize capture to a completed guest frame. No `src/` or runtime change is justified from attempt 1.

- **2026-09-20 H-SAMPLE same-head general validation — GREEN / semantic run still active:** exact diagnostic head `phase4/gate-c-h-sample-diagnostic@8f818364023347e594c2b59e1b865358e8d96ebc`; **Build and Validate `35535273325 SUCCESS`** with normal `build`, PROFILE `profile-build`, and pinned Mupen/LLE `emulator-smoke` all successful (`update-release` skipped as expected). This confirms the validation-only additions do not break standard clean-core build/smoke behavior. H-SAMPLE run `35535273374` has already passed generator/tests/original artifact and unchanged Sodium64 build/wrap/symbol-location stages; current long step is pinned N64 ares build before queue capture. **Do not interpret H-SAMPLE yet**; the discriminator remains pending until exact WRAM mirror + completed queue evidence exists.

- **2026-09-20 PR #13 standard PR validation — CI CLOSED GREEN / hardware boundary remains:** **Ares Profile Validation `35534690728 SUCCESS`** completed for PR #13 / frozen head `84ecafad7cc3505d82f134b2672d9ed1146fedc0`. Jobs: `profile-build 106141487391 SUCCESS`, `ares-smoke 106141685985 SUCCESS`. Artifacts: **`10612029401 sodium64-ares-profile-build`** (`sha256:a67394ff6f2bc43502cec95dd283d173f3057cdd86ea02f555fe875fd01f7cfa`) and **`10611714767 sodium64-ares-profile-matrix`** (`sha256:448554708a640049590897df29f64551966ae29796c8e02367a3fb3e14777570`). GitHub reports PR #13 **open, unmerged, mergeable=true**. Together with exact-head Build/Validate `35530189781` and the three clean semantic regressions, standard CI is no longer a blocker. **Remaining authority boundary:** the PR explicitly requires real-N64 L4 validation for renderer-overlay DMA/bus/cadence behavior before treating that hardware question as closed; host/emulator green does not supply that authority. Do not merge merely because CI is green unless Iron's current merge policy allows integrating a hardware-milestone candidate before that L4 check.

- **2026-09-20 H-SAMPLE harness batch 2 — DISPATCHED / hygiene preserved:** validation branch is now `phase4/gate-c-h-sample-diagnostic@8f818364023347e594c2b59e1b865358e8d96ebc`, 6 commits ahead / 0 behind frozen clean core `84ecafad...`. Exact delta is **one branch-only workflow + five `scripts/` files**; there are still zero `src/`, Makefile or runtime changes. GitHub parsed the new workflow and dispatched **Gate C H-SAMPLE Diagnostic run `35535273374`**; same-SHA **Build and Validate `35535273325`** is also queued/running. The workflow rebuilds the unchanged clean candidate, regenerates guest ROM SHA `347e177c...`, verifies the exact 32 KiB guest survives wrapping, locates section-queue/runtime symbols from the exact ELF, runs pinned N64 ares in the established RSP-interpreter lab mode, captures the completed queue, and requires the WRAM HDMA mirror to equal exact bytes `0..223` before classifying any sampler result. **Possible readings:** (a) mirror exact + <224 unique queued WH0 states => H-SAMPLE dynamically confirmed at the section producer/consumer boundary; (b) mirror exact + all 224 unique queued states => H-SAMPLE falsified for this path; (c) mirror/config/queue incomplete => harness/HDMA evidence indeterminate and must be repaired without changing core. Build failure must be classified separately. Do not infer a visual/game regression or hardware cadence effect from this diagnostic alone.

- **2026-09-20 H-SAMPLE harness batch 1 — IMPLEMENTED / runtime untouched:** created validation-only child `phase4/gate-c-h-sample-diagnostic` from exact clean core `84ecafad...`. Current branch is 5 commits ahead / 0 behind its clean parent and differs only by five new `scripts/` files: deterministic ROM generator + generator tests + N64 GDB capture + queue analyzer + analyzer tests; **no `src/`, build-system, workflow or emulator/runtime file differs yet**. The original 32 KiB guest ROM is deterministic (`sha256:347e177ceef12a04b51b7e6958bb81b09d741acf4db8edb5aea2bea8fa82af8e`) and uses two direct-HDMA channels with identical 224-line source tables: channel 0 writes `WH0=0..223`; channel 1 writes the same bytes through SNES WMDATA into WRAM `$7E0100..$7E01DF`. That WRAM mirror is a falsification guard: analysis refuses to interpret section loss unless the full 0..223 probe exists. Capture identifies the inactive/completed double-buffered section queue from live `section_ptr`, parses 0x40-byte records (`WH0` offset `0x2E`, end-line byte `0x3F`), and records precision/current-line/cooldown/status/frame state. Analyzer distinguishes complete 224-state preservation from fewer unique queued WH0 states and has synthetic exact/coalesced/invalid-probe unit cases. **Next batch:** add a branch-only CI workflow that builds the unchanged clean core, wraps the exact original guest, locates runtime symbols, runs pinned N64 ares in the already-valid RSP-interpreter lab mode, captures the completed queue, and asserts only the diagnostic classification. Before interpreting any result, verify the branch delta still contains no runtime files.

- **2026-09-20 H-SAMPLE next discriminator — DESIGNED / no runtime change yet:** after H-OBJ closure, the next autonomous Gate-C question is whether Road-valid default `precision_set=2<<2` (`MEDIUM`) drops semantically distinct per-line PPU state. Exact clean core source confirms the mechanism: `write_wh0..3` mark `sect_status` dirty whenever a window edge changes; `run_line` decides whether to emit a section **before** calling `trigger_hdma`; at frame start MEDIUM loads minimum cooldown `16`, and after a dirty snapshot computes an effective cooldown with shift `2`, so later distinct line states can remain dirty while section emission is deferred. `make_section` copies exactly `SECTION_SIZE=0x40` bytes from `bghofs`; `WH0..WH3` occupy bytes `0x2E..0x31` of each section record and the prior record's terminal visible line is stored at byte `0x3F`. **Controlled experiment selected:** original 32 KiB SNES ROM, no commercial data, Mode1/simple display, direct HDMA channel writes a different `WH0` value every visible scanline; then a pinned-ares N64 lab captures the completed Sodium64 section queue directly over GDB and compares each queued `(end_line, WH0)` against the deterministic per-line source sequence. This avoids conflating H-SAMPLE with OBJ, color math, final framebuffer analysis or game-specific behavior. **Pass/falsifier:** if every semantically distinct source line reaches the section consumer with correct effective-line mapping, reject H-SAMPLE for this path; if queued records skip/hold multiple distinct source WH0 states under MEDIUM while the guest HDMA sequence is verified, H-SAMPLE is dynamically confirmed. Keep this on a validation-only child branch from clean `84ecafad...`; no emulator/core file may change in the diagnostic batch.

- **2026-09-20 PR #13 post-open CI — RUNNING / mergeable:** GitHub now reports **PR #13 mergeable=true** at unchanged head `84ecafad7cc3505d82f134b2672d9ed1146fedc0`. The already-authoritative exact-head Build/Validate jobs remain green (`build`, `profile-build`, `emulator-smoke` from run `35530189781`). Opening the PR triggered **Ares Profile Validation run `35534690728`**, currently in progress (`pull_request` event; current active check `profile-build`). **Question:** does the clean four-file runtime candidate preserve the standard PR profiling/ares regression harness? **Pass reading:** workflow completes success; this is additional integration/regression confidence, not real-N64 overlay-DMA authority. **Fail reading:** classify the first failing job before changing runtime; a harness/profile-specific failure must not be conflated with H-OBJ/overlay semantic evidence. **Next action:** inspect run `35534690728` to completion, then decide whether any remaining pre-merge blocker is purely the explicitly declared L4 hardware milestone.

- **2026-09-20 Clean overlay promotion — PR OPEN / exact candidate preserved:** opened **PR #13 `Gate C: integrate fixed-slot RSP renderer overlays`** from `phase4/gate-c-rsp-overlay-clean` to `master`, with head exactly **`84ecafad7cc3505d82f134b2672d9ed1146fedc0`** and base `master@9441818dd8457a27bbd617a0f32c6d484550661f`. GitHub reports 4 commits / 4 changed files / +1505 -335, matching the audited source-only delta. PR body records exact Build/Validate, H-OBJ, whole-frame Mode7 and same-frame Mode7 authorities plus the real-N64 hardware milestone boundary; no validation-only files were copied into the candidate. **State:** `CANDIDATE`, not merged. **Immediate next action:** inspect PR-triggered CI/checks and GitHub mergeability for the exact head; do not merge from the creation response alone.

- **2026-09-20 Clean overlay final promotion audit — PASS / PR-ready:** frozen technical candidate is still exactly `phase4/gate-c-rsp-overlay-clean@84ecafad7cc3505d82f134b2672d9ed1146fedc0`, **4 commits ahead / 0 behind** `master@9441818d...`, with exactly four technical files in the delta: `src/defines.h`, `src/main.S`, `src/rsp_main.S`, new `src/rsp_mode7.S`. Exact blob SHAs for all four files are identical across the frozen core and each semantic validation child (`...-validation`, `...-mode7-validation`, `...-midframe-validation`): `defines.h 2e4a318a...`, `main.S 3d793d18...`, `rsp_main.S bfbceb81...`, `rsp_mode7.S 8e6ab79a...`. Therefore H-OBJ, whole-frame Mode7 and same-frame Mode7 results all exercised the exact technical bytes proposed for integration. Source hygiene rescan of the four-file candidate finds no `OVERLAY_PROOF`, `overlay_proof`, `rsp_slot_proof`, `rsp_swap`, semantic-twin/diagnostic vocabulary or `rsp_upload_slot`; proof plumbing remains excluded. Exact-head Build/Validate has a successful authority run **`35530189781 SUCCESS`**; later same-head push runs were cancelled, not failures. No open PR currently targets `phase4/gate-c-rsp-overlay-clean`. **Decision:** candidate is PR-ready. Next action is open a PR from the frozen four-file branch to `master`, preserving this exact SHA; do not copy validation-only workflows/scripts into the PR branch.

- **2026-09-20 Clean mid-frame Mode7 regression — VALIDATED / semantic closure:** exact validation head `phase4/gate-c-rsp-overlay-clean-midframe-validation@cd371a9fb3f64324540c86a19ed0719830173037`; Gate C Mode7 Midframe Overlay run **`35533933132 SUCCESS`**, N64 semantic job **`106139474289`**, evidence artifact **`10612013950 gate-c-mode7-midframe-sodium64-evidence`** (`sha256:09a1413252793be5b58fcdbeec66de52da889a11efe918fe278c04c63edc5b7f`). Same-SHA Build/Validate run **`35533933137 SUCCESS`**. Fresh control capture: `phase=0x01`, guest counter `11`, host/guest Mode1, `irq_count=0`, `test_done=0`, fixed slot word `0x91670E64`, framebuffer `0xA0113000`. Permanent post-test capture: `phase=0x33`, guest counter `37`, host/guest Mode1, `irq_count=2`, `test_done=1`, **`irq1_frame=30`, `irq2_frame=30`**, fixed slot restored to `0x91670E64`, framebuffer `0xA00F2300`. Final workflow assertion prints `Gate-C clean Mode7 mid-frame PASS: irq_count=2 irq_frames=30/30 final_slot=0x91670E64 framebuffer=0xA00F2300 guest_counter=37`. Because both IRQs occurred in the same guest frame interval and display publication changed afterward, the clean proof-free core survives regular→Mode7→regular demand-overlay switching within one visible frame and continues publishing frames. Together with clean H-OBJ run `35530449506` and clean whole-frame direct-IMEM run `35530604792`, all semantic regressions required for frozen core `phase4/gate-c-rsp-overlay-clean@84ecafad...` are now closed. **What this does NOT prove:** Mode7 pixel fidelity, exact scanline timing, overlay DMA cost/cadence on real N64, or all mixed-mode compositor semantics. **Immediate next action:** final exact-head/source-delta/CI audit of frozen clean core, then promote that four-file branch to a PR if identity and hygiene still hold.

- **2026-09-20 Clean overlay self-DMA source-safety audit — SUPPORTED / no obvious self-overwrite race:** in both clean RSP variants the rewritten IMEM target is exactly `0x13A8..0x178F`; resident `dma_read` is at offset `0xC94` (IMEM ~`0x1C94`) and fault loaders at `0xCCC/0xCE4`, entirely outside the target. `dma_read` programs SP/RAM/read registers then spins on `COP0_DMA_BUSY` until zero before `jr ra`; only after that return does the loader branch into newly loaded `draw_mode7_entry` or `draw_bg`. Therefore the source contract neither executes from the overwritten slot during DMA nor enters it before DMA completion. **What this does NOT prove:** real-N64 SP DMA/bus timing, undocumented hazards, or performance cost; L4 remains authority for those. This audit removes an obvious software race as a pre-PR blocker, not the hardware milestone requirement.

- **2026-09-20 Clean overlay IMEM capacity result — MEASURED / material architecture gain:** exact master artifact `10596806694` has `rsp_main .text=0xFD8 = 4056`, leaving only **40 bytes** below the 4096-byte IMEM ceiling. Exact clean artifact `10611052622` has both regular and Mode7 RSP `.text=0xD00 = 3328`, leaving **768 bytes** each. The fixed-slot/fault-loader architecture therefore recovers **728 bytes of active IMEM headroom** versus current master while retaining both renderers as demand-loadable ROM blobs. This is the architectural capacity benefit; it is separate from runtime DMA-cost/performance authority, which remains L4/hardware-milestone work.

- **2026-09-20 Clean overlay artifact footprint — MEASURED / expected:** compare exact master artifact `10596806694` (`master@9441818d...`) against clean artifact `10611052622` (`overlay-clean@84ecafad...`). Final `sodium64.z64` remains exactly **98,304 bytes** in both builds; only content/hash changes (`master fc3ef060...`, clean `3259cee1...`). ELF grows **794,760 → 801,680 bytes (+6,920)**, consistent with embedding the second RSP image/symbols. Build metrics move from 25→26 source files and 2→3 map files; the only added map is `rsp_mode7.map` (2,808 bytes). `sodium64.map` grows only 374 bytes. **Interpretation:** dual-renderer integration does not enlarge the packaged ROM footprint at its current fixed N64 ROM allocation and introduces the expected single RSP payload rather than accidental diagnostic/proof baggage.

- **2026-09-20 Clean overlay promotion audit — SOURCE PASS / Road docs unchanged:** frozen candidate `phase4/gate-c-rsp-overlay-clean@84ecafad...` remains exactly four technical files ahead of `master`; no open PR currently targets this branch. Audit finds no `proof`, `diagnostic`, semantic-twin or proof-bit vocabulary/code in `defines.h`, `main.S`, `rsp_main.S` or `rsp_mode7.S`. Normal layer dispatch still selects fixed `draw_bg` / `draw_mode7_entry` entries, and overlay loads occur only through inactive-renderer fault stubs. Direct comparison to the last proof core confirms cleanup intentionally removes `OVERLAY_PROOF`/`rsp_slot_proof` and the earlier CPU-only `rsp_upload_slot` helper while retaining the validated RSP-side demand loader and H-OBJ repair. **Docs decision:** do not update `ROAD_TO_1_0.md` or `ROADMAP.md` for this candidate; M3/Gate C remains active and no gate/milestone/scope changed. Promotion to PR is gated only by the active clean mid-frame semantic rerun plus final exact-head audit.

- **2026-09-20 Clean mid-frame Mode7 attempt 2 — WORKFLOW KEY REPAIR / dispatched:** current validation head `phase4/gate-c-rsp-overlay-clean-midframe-validation@cd371a9fb3f64324540c86a19ed0719830173037`. Only `.github/workflows/gate-c-mode7-midframe-clean.yml` changed from attempt 1: final publication assertion/print now use capture schema key `framebuffer_pointer` instead of nonexistent `framebuffer`. Frozen clean core `84ecafad...`, original guest bytes, IRQ schedule, capture helper, slot oracle and all semantic assertions are unchanged. Await exact-head semantic rerun; if it passes, clean core has H-OBJ + whole-frame Mode7 + same-frame Mode7 regression all closed without proof instrumentation.

- **2026-09-20 Clean mid-frame Mode7 attempt 1 — HARNESS FALSE NEGATIVE / semantic state already consistent:** validation sibling `phase4/gate-c-rsp-overlay-clean-midframe-validation@a3fc60f57f768f5dc69ac331b5f398921cf9ecde`; run **`35530712038 FAILURE`**, N64 job `106130703339`. All pre-runtime gates PASS. Capture reaches permanent post-test phase and records clean semantic state: control `phase=0x01`, guest counter `5`, host/guest BGMODE1, IRQ count 0, regular slot word `0x91670E64`; post `phase=0x33`, guest counter `40`, host/guest BGMODE1, **`irq_count=2`**, done 1, **`irq1_frame=30`, `irq2_frame=30`**, final slot word **`0x91670E64`**. Capture log also explicitly observes a displayed-buffer transition in post-test (`0xA0133D00 -> 0xA00F2300`). The workflow then crashes only on `KeyError: 'framebuffer'`: capture state schema stores the pointer as `framebuffer_pointer`, while the final Python assertion incorrectly indexes `framebuffer`. **REJECTED:** treating this run as a renderer/overlay failure. Controlled repair is workflow-only key correction to `framebuffer_pointer`; generator, guest, capture helper and frozen clean core remain unchanged.

- **2026-09-20 Clean whole-frame Mode7 switching — VALIDATED by direct SP IMEM observation:** validation sibling `phase4/gate-c-rsp-overlay-clean-mode7-validation@1e46666e92d88fc48bd6b5eb81d5257061d59f49` differs from frozen clean core `84ecafad...` only by diagnostic/capture/workflow files; no proof bits or runtime instrumentation exist. Gate C run **`35530604792 SUCCESS`**, evidence artifact **`10610963951 gate-c-mode7-fault-sodium64-evidence`**. Direct GDB reads of fixed SP IMEM word `0xA40013A8` show: fresh control Mode1 at guest counter `7`, `bg_mode=1`, `frame_count=2`, framebuffer `0xA00F2300`, slot **`0x91670E64`** (compiled regular `draw_bg`); fresh Mode7 treatment at guest counter `72`, `bg_mode=7`, `frame_count=1`, framebuffer `0xA0133D00`, slot **`0x1000024E`** (compiled Mode7 `draw_bg` fault-stub word, proving the Mode7 payload is resident); fresh returned Mode1 at guest counter `14` after wrap, `bg_mode=1`, `frame_count=2`, framebuffer `0xA0113000`, slot restored to **`0x91670E64`**. Workflow assertion prints `Gate-C clean Mode7 whole-frame PASS: control_slot=0x91670E64 treatment_slot=0x1000024E return_slot=0x91670E64`. **Meaning:** proof-instrumentation removal did not break either demand-driven overlay direction; real Mode7 slot replacement and regular restoration are directly observed in the clean candidate.

- **2026-09-20 Clean H-OBJ regression — VALIDATED against direct SNES reference:** validation child `phase4/gate-c-rsp-overlay-clean-validation@19bb7bb4162b94b0476002e250596487ababfae8` differs from frozen clean core `84ecafad...` only by seven harness/workflow files; no runtime/source bytes differ. Gate C OBJ Window run **`35530449506`** completed with diagnostic-build PASS, direct-SNES reference job PASS and Sodium64 N64 semantic job PASS. Direct reference classification is exactly **`REFERENCE_CONFIRMS_OUTER_OBJ_MASK_2_TO_0`**. Sodium64 classification is exactly **`H_OBJ_FALSIFIED_SODIUM64_MASKS_OUTER_OBJ`** (the validated repaired behavior): fresh control capture at guest NMI counter `7` has `TMW=0x01`, `WOBJSEL=0x03`, `WHX=0x000040BF`, `TM=0x11`, `TS=0`, framebuffer `0xA00F2300`, and two outer red OBJ components; fresh treatment at guest counter `227` has `TMW=0x11` with the same common registers, framebuffer `0xA0113000`, and the outer OBJ pair masked as required. Sodium64 evidence artifact **`10611360939 gate-c-obj-window-sodium64-evidence`**; direct-SNES artifact `10610858765`. **Meaning:** stripping proof instrumentation and integrating the dual renderer architecture did not regress the H-OBJ correctness repair. This semantic gate for clean core `84ecafad...` is closed.

- **2026-09-20 Clean semantic regression pre-runtime gates — PASS / ares capture pending:** all three validation siblings remain source-isolated from clean core `84ecafad...`. H-OBJ run `35530449506`: diagnostic-build PASS, exact Sodium64 compile/link PASS, exact H-OBJ guest generation/wrap PASS, symbol location PASS; pinned N64 ares build/capture and direct-SNES reference capture remain active. Whole-frame clean Mode7 run `35530604792`: diagnostic-build PASS, generator host tests PASS, exact candidate compile/link PASS, exact original guest generation/wrap PASS, symbol location PASS; pinned N64 ares build/capture active. Mid-frame clean Mode7 run `35530712038`: diagnostic-build PASS, all six host tests PASS, exact candidate compile/link PASS, exact original guest generation/wrap PASS, symbol location PASS; pinned ares dependency/build/capture active. **Interpretation boundary:** any later failure is no longer attributable to diagnostic construction, host-test encoding, candidate compilation, wrong wrapped guest, or missing state symbols; classify only from the first failing ares/capture/assertion step.

- **2026-09-20 Clean visible mid-frame Mode7 validation — DISPATCHED / core identity preserved:** sibling `phase4/gate-c-rsp-overlay-clean-midframe-validation@a3fc60f57f768f5dc69ac331b5f398921cf9ecde`, forked exactly from frozen clean core `84ecafad...`; compare clean→validation contains only six added diagnostic/capture/workflow files and no runtime/source changes. Active semantic run **`35530712038`**; child Build/Validate `35530712023`. Clean workflow has no proof-bit symbols. It requires pre-test regular slot word `0x91670E64`, exactly two V-count IRQs with `irq1_frame=irq2_frame=30` (same NMI interval), final host+guest Mode1, final slot restored to regular `0x91670E64`, and a different post-test framebuffer pointer to prove publication continued after the mixed-mode frame. This is a clean regression of same-frame switching/survival; direct transient Mode7 residency is independently covered by the sibling whole-frame direct-IMEM oracle `35530604792`.

- **2026-09-20 Clean Mode7 whole-frame validation attempt 2 — DIRECT-IMEM ORACLE / dispatched:** sibling `phase4/gate-c-rsp-overlay-clean-mode7-validation@1e46666e92d88fc48bd6b5eb81d5257061d59f49`, still forked from frozen clean core `84ecafad...`; only validation files differ. Added missing shared generator helper after attempt-1 plumbing failure; no runtime/core byte changed. Active Gate C run **`35530604792`**. Workflow has no proof-bit symbols and observes fixed SP IMEM word `0xA40013A8` directly: control Mode1 must equal clean compiled regular word `0x91670E64`; Mode7 treatment must equal clean compiled Mode7 fault-stub word `0x1000024E`; returned Mode1 must restore `0x91670E64`. Guest `bg_mode`/phase progression and fresh NMI synchronization remain required. This is the clean whole-frame authority for both overlay directions without reintroducing instrumentation.

- **2026-09-20 Clean Mode7 whole-frame validation attempt 1 — HARNESS FALSE NEGATIVE / no runtime evidence:** sibling `phase4/gate-c-rsp-overlay-clean-mode7-validation@fbef7f3f677defc4e97d6e64301301b45fcb7948`; run **`35530537886 FAILURE`** stops in `diagnostic-build` before ROM generation because `scripts/make_gate_c_mode7_switch.py` imports shared `Assembler`/ROM helpers from `make_gate_c_obj_window.py`, which was not copied into this isolated validation branch. Compare to clean core contains only validation files and the workflow has no proof-bit references; direct IMEM oracle itself was not exercised. **REJECTED:** any interpretation about overlay switching. Controlled repair: add the unchanged shared helper script only; keep clean core `84ecafad...`, Mode7 generator, capture helper, workflow assertions and IMEM signatures unchanged.

- **2026-09-20 Clean overlay semantic child branch — H-OBJ DISPATCHED / core identity preserved:** `phase4/gate-c-rsp-overlay-clean-validation@19bb7bb4162b94b0476002e250596487ababfae8` is forked from frozen clean core `84ecafad...`. Compare clean→validation contains exactly seven added files: the original H-OBJ generator/tests/capture/analyzers plus `.github/workflows/gate-c-obj-window.yml`; **no `src/`, Makefile or runtime file differs**. Clean H-OBJ workflow run **`35530449506`** and child Build/Validate `35530449663` are dispatched. Workflow retains direct-SNES reference authority and now requires Sodium64 framebuffer classification exactly `H_OBJ_FALSIFIED_SODIUM64_MASKS_OUTER_OBJ`, not merely non-indeterminate. This child is validation plumbing only and is not the merge candidate; technical candidate remains frozen `phase4/gate-c-rsp-overlay-clean@84ecafad...`.

- **2026-09-20 Clean overlay Build/Validate — VALIDATED at build/smoke level:** exact clean head `phase4/gate-c-rsp-overlay-clean@84ecafad7cc3505d82f134b2672d9ed1146fedc0`; Build/Validate **`35530189781 SUCCESS`**. Normal build PASS, PROFILE build PASS, pinned Mupen64Plus debugger + LLE RSP smoke PASS. Together with artifact `10611052622` this establishes the clean four-file candidate compiles, links, embeds both renderer blobs, preserves fixed-slot/common ABI, boots and progresses in the existing L2 lab after proof instrumentation removal. **Still required before merge-candidate status:** semantic regression from a child validation branch against the exact same core bytes: H-OBJ pixel oracle, clean whole-frame regular↔Mode7 slot switching without proof bits, and visible mid-frame switching regression. Keep `phase4/gate-c-rsp-overlay-clean` frozen at `84ecafad...` while validation plumbing lives only on a child branch.

- **2026-09-20 Clean overlay compiled layout — MEASURED / EXACT PASS:** exact clean head `phase4/gate-c-rsp-overlay-clean@84ecafad7cc3505d82f134b2672d9ed1146fedc0`; Build/Validate run `35530189781`, normal artifact **`10611052622 sodium64-build`**. Final `build/sodium64.elf` embeds both renderer images without special proof-artifact exposure: `rsp_main_text_size=rsp_mode7_text_size=0xD00 = 3328`, data size `0x1000 = 4096`, leaving **768 bytes IMEM headroom**. Embedded starts are `rsp_main_text_start=0x800B76D8`, `rsp_mode7_text_start=0x800B93D8`; fixed slot sources (`+0x3A8`) are both 8-byte aligned. Direct extraction of embedded blobs proves regular↔Mode7 text has **935 differing bytes / 247 differing words**, first byte `0x3A8`, last `0x78B`, with **zero differences outside `[0x3A8,0x790)`**. Fixed/common offsets therefore remain: `draw_bg=0x3A8` (IMEM `0x13A8`), `draw_mode7_entry=0x788`, `draw_obj=0x790`, `start_objects=0x7D4`; resident `dma_read=0xC94`, `ret_jump=0xCC4`, clean `overlay_load_mode7=0xCCC`, `overlay_load_main=0xCE4`. Complete regular↔Mode7 DMEM differs only at the previously audited four regular-BG code-pointer words **`0xE28/0xE2C/0xE30/0xE40`**; overlay source words `0xE90..0xE97` are byte-identical zero in both compiled payloads. **Meaning:** removing proof instrumentation preserved the validated fixed-slot ABI exactly while shrinking each RSP text by 24 bytes from proof build `0xD18→0xD00`; no new resident-code or DMEM ABI divergence was introduced. General emulator-smoke from the same run remains the next build-level authority before semantic child-branch regression.

- **2026-09-20 Clean Gate-C overlay integration core — IMPLEMENTED / source hygiene PASS, compile pending:** `phase4/gate-c-rsp-overlay-clean@84ecafad7cc3505d82f134b2672d9ed1146fedc0`, forked from `master@9441818d...`. Compare to master contains exactly **four files**: `src/defines.h` (+ two overlay-source addresses `0xE90/0xE94`), `src/main.S` (+ initialization of regular/Mode7 fixed-slot source pointers), `src/rsp_main.S` (validated fixed-slot regular renderer + H-OBJ repair + resident fault loader), and new `src/rsp_mode7.S` (real Mode7 fixed-slot variant + same common/H-OBJ/fault-loader contract). `src/ppu.S` is byte-identical to master. Repository/source audit finds no `OVERLAY_PROOF`, `overlay_proof`, `rsp_slot_proof`, `rsp_swap`, semantic-twin, diagnostic workflow/script, or proof-artifact plumbing in the branch delta. Clean DMEM reserves only `OVERLAY_MAIN_SRC=0xE90`, `OVERLAY_MODE7_SRC=0xE94`, then pads from `0xE98` to invariant `VEC_DATA=0xF70`. Fault loaders now only load source -> DMA exactly `0x3E8` bytes to IMEM `0x13A8` -> re-enter fixed renderer entry; Mode7→regular still restores saved live `t0`. **Next authority:** exact-head Build/Validate plus compiled ELF extraction must prove <=4 KiB text, fixed entries/common suffix invariant, resident prefix/suffix identity between regular/Mode7, and all variant text differences confined to `[0x3A8,0x790)` before semantic regression is attached.

- **2026-09-20 Clean Gate-C overlay integration candidate — BASELINE CONFIRMED / branch reserved:** `phase4/gate-c-rsp-overlay-clean` already exists and compares **identical** to audited `master@9441818dd8457a27bbd617a0f32c6d484550661f` (0 commits ahead/behind, no file delta). It is therefore suitable as the fresh integration branch requested by the validated mid-frame decision. **Allowed integration surface for first clean technical batch:** validated H-OBJ repair plus real regular/Mode7 fixed-slot fault-overlay runtime only. Explicitly exclude proof-only `rsp_swap.S`, `OVERLAY_PROOF`, exported CPU `rsp_slot_proof`, semantic-twin/readback instrumentation, diagnostic workflows/scripts, and autobuild artifact exposure. Preserve source pointers `OVERLAY_MAIN_SRC=0xE90` / `OVERLAY_MODE7_SRC=0xE94` and downstream `VEC_DATA=0xF70` layout by padding from `0xE98`. Re-run compiled-layout, H-OBJ, whole-frame/mid-frame Mode7 and general Build/Validate before treating this branch as a merge candidate.

- **2026-09-20 Visible mid-frame real Mode7 fault overlay — VALIDATED switching primitive in pinned N64 lab:** exact head `phase4/gate-c-rsp-mode7-midframe-proof@14c29dd6e63ac0663cfc71faa38b9e7dda0c073a`; Build/Validate **`35528410621 SUCCESS`** (normal + PROFILE + pinned Mupen/LLE smoke); Gate C Mode7 Midframe Overlay run **`35528410633`**, N64 semantic job `106124562202`, capture assertion **PASS**; evidence artifact **`10610716383 gate-c-mode7-midframe-sodium64-evidence`**. Exact state: pre-test control `phase=0x01`, guest NMI counter **10**, host/guest BGMODE1, IRQ count 0, done 0, `rsp_slot_proof=0x00`, framebuffer `0xA00F2300`; permanent post-test state `phase=0x33`, guest NMI counter **36**, host/guest BGMODE1, IRQ count **2**, done 1, **`irq1_frame=30` and `irq2_frame=30`**, `rsp_slot_proof=0x03`, framebuffer `0xA0133D00`. Guest has no BGMODE writes after IRQ #2. Therefore both demand-driven RSP fault DMAs (regular→real Mode7 at V-count ~80 and Mode7→regular at ~160) completed between the **same two V-blanks**, i.e. within one visible SNES frame, and execution/render publication continued afterward. Section-coalescing was independently rejected before runtime. **Validated meaning:** the fixed 1000-byte renderer slot + resident demand loader can service real regular/Mode7 transitions in both directions at visible mid-frame section boundaries in the pinned N64 lab. **Does NOT prove:** Mode7 pixel correctness, exact scanline timing, overlay DMA performance/cadence on real N64, or all mixed-mode compositor semantics. **Decision:** the architecture primitive is sufficiently proven to stop extending the accumulated proof branch. Next engineering step is a clean master-based integration candidate containing only H-OBJ repair + dual renderer/fault-loader architecture, with proof instrumentation stripped, followed by compiled-layout, H-OBJ, whole-frame/mid-frame Mode7 and Build/Validate regression before any merge.

- **2026-09-20 Clean-integration proof-instrumentation removal contract — MEASURED / TODO after mid-frame closure:** proof candidate DMEM reserves `OVERLAY_MAIN_SRC=0xE90`, `OVERLAY_MODE7_SRC=0xE94`, `OVERLAY_PROOF=0xE98`, then pads to fixed `VEC_DATA=0xF70`. Final clean architecture does not need `OVERLAY_PROOF` or CPU `rsp_slot_proof`. Removing the proof word can preserve every downstream DMEM address by keeping the two required source words at `0xE90/0xE94` and padding directly from `0xE98` to `VEC_DATA=0xF70` identically in both RSP images. Resident fault loaders then become `load source -> dma_read 0x3E8 to 0x13A8 -> branch back`, with Mode7->regular still restoring saved live `t0`; no proof OR/store instructions remain. This is the exact cleanup contract to verify by compiled artifacts on a fresh master-based candidate if the active mid-frame proof passes; do not implement it on the proof branch.

- **2026-09-20 Fault-overlay integration-surface audit — MEASURED / current proof branch is not mergeable as-is:** compare `master@9441818d...` to real fault core proof `2352bc734...` spans 43 experimental commits and includes diagnostic-only `.github/workflows/gate-c-obj-window.yml`, OBJ-window scripts/tests, autobuild artifact exposure, `src/rsp_swap.S`, and proof-only `OVERLAY_PROOF`/exported `rsp_slot_proof` plumbing in addition to the actual architecture. `rsp_swap.S` is the semantic-twin proof artifact and is not required by the real regular↔Mode7 runtime; final binary uses `rsp_main` + `rsp_mode7`. **Decision if mid-frame proof passes:** do not merge/promote the accumulated proof branch. Build a clean candidate from current master containing only the validated H-OBJ repair + fixed-slot dual renderer/fault-loader architecture and any intentionally retained regression tests; strip semantic-twin/proof-bit instrumentation and diagnostic artifact exposure unless independently useful. Re-run compiled layout, H-OBJ, Mode7 switching and general Build/Validate on that clean candidate before PR/merge.

- **2026-09-20 Visible mid-frame diagnostic identity — MEASURED / pinned:** artifact **`10610123164 gate-c-mode7-midframe-diagnostic`** from run `35528410633` contains exact original guest ROM **32768 bytes**, SHA-256 **`af360b61901aa77034f9e0572a6e48bc5397ff53b6d51c1c8e3f254a3a1ea345`**. Manifest binds it to source head `14c29dd6...`, pre-test/final BGMODE1, mid-frame BGMODE7, pretest 30 NMIs, VIRQ lines 80/160, oracle `two V-count IRQs in same NMI interval + RSP completed-fault bits`, pixel semantics non-authoritative. N64 workflow independently re-extracts and `cmp`s the embedded 32 KiB guest after wrapping before execution, so eventual runtime evidence refers to these exact bytes.

- **2026-09-20 Visible mid-frame Mode7 exact-head Build/Validate — VALIDATED at build/smoke level:** head `phase4/gate-c-rsp-mode7-midframe-proof@14c29dd6e63ac0663cfc71faa38b9e7dda0c073a`; Build/Validate run **`35528410621 SUCCESS`**. Normal build PASS, PROFILE build PASS, and pinned Mupen64Plus debugger + LLE RSP smoke PASS. Core/RSP is inherited unchanged from the already compiled/validated real fault-overlay architecture; this exact branch adds only original diagnostic/tests/workflow. Therefore the mid-frame experiment itself does not introduce a compile/link/boot/smoke regression. Gate C Midframe run `35528410633` remains the semantic authority and is still building pinned ares at checkpoint.

- **2026-09-20 Visible mid-frame Mode7 run 2 — BUILD/WRAP PASS / runtime pending:** exact head `14c29dd6e63ac0663cfc71faa38b9e7dda0c073a`. Gate C Midframe run `35528410633` N64 job has passed host tests, exact Sodium64 compile/link, original diagnostic generation, ROM wrapping, embedded 32 KiB guest byte-for-byte comparison, and symbol-location step. Build/Validate `35528410621` normal and PROFILE compile jobs are also SUCCESS; emulator-smoke is still running. Pinned ares dependencies/build and semantic capture remain pending. Therefore any subsequent failure is no longer attributable to generator tests, candidate compilation, wrapping or wrong guest bytes.

- **2026-09-20 Mid-frame section-materialization audit — MEASURED / coalescing explanation rejected:** in current `ppu.S`, `write_bgmode` stores the new mode and branches to `update_frame` when it changes; `update_frame` writes byte `1` at big-endian `sect_status`, producing the dirty halfword state `0x0100`. On the next visible `run_line`, low-byte cooldown decrement leaves `0x0100` unchanged, `bne t0,0x100` falls through and `make_section(cur_line)` executes immediately, after which normal cooldown is applied. Therefore diagnostic BGMODE writes at V-count lines 80 and 160 are separated by ~80 scanlines and cannot plausibly be collapsed solely by section cooldown. If runtime guest records both IRQs but overlay proof misses a direction, investigate demand/renderer/overlay processing rather than re-opening “changes were too close to create sections” without new evidence.

- **2026-09-20 Visible mid-frame Mode7 run 2 — DIAGNOSTIC BUILD PASS / runtime pending:** exact head `phase4/gate-c-rsp-mode7-midframe-proof@14c29dd6e63ac0663cfc71faa38b9e7dda0c073a`; Gate C Midframe run `35528410633`. `diagnostic-build` SUCCESS: all six host tests pass, deterministic original 32 KiB LoROM generates successfully and artifact upload completes. Therefore the run is no longer blocked on vectors, V-count schedule, test encoding or ROM construction. N64 semantic job has started; authoritative next gates are exact Sodium64 build/wrap, pinned ares lab, then pre/post state assertions. No runtime result yet.

- **2026-09-20 Visible mid-frame Mode7 run 2 — TEST REPAIRED / CI dispatched:** current head `phase4/gate-c-rsp-mode7-midframe-proof@14c29dd6e63ac0663cfc71faa38b9e7dda0c073a`. Only `scripts/test_gate_c_mode7_midframe.py` changed from run-1 head: evidence-slot store counts now correctly expect startup initialization + one IRQ write for each `$7E0005/$7E0006`. Generator bytes, V-count IRQ schedule, workflow, core and RSP fault overlay are unchanged. Await exact-head diagnostic host tests before any runtime interpretation.

- **2026-09-20 Mid-frame Mode7 run 1 — HOST-TEST FALSE NEGATIVE / no runtime evidence:** exact head `phase4/gate-c-rsp-mode7-midframe-proof@9b18e33f6f42b63c98457ac49c9515c5445e72b0`; Gate C Mode7 Midframe Overlay run **`35528369617 FAILURE`** stops in `diagnostic-build` before ROM generation/wrap/runtime. Five of six tests pass; only `test_same_frame_evidence_slots_are_distinct` fails because it expected the `STA long $7E0005/$7E0006` byte sequence once, while each evidence slot is intentionally written **twice**: once during startup zero-initialization of `$7E0000..06` and once by its designated IRQ. Generator/vector/VIRQ/mode tests all pass. **REJECTED:** treating this as any evidence about V-count IRQ behavior, overlay DMA or mid-frame switching. Controlled repair changes the test expectation from one to two stores; generator/core/RSP/workflow semantics remain unchanged.

- **2026-09-20 Visible mid-frame Mode7 semantic workflow — DISPATCHED:** current head `phase4/gate-c-rsp-mode7-midframe-proof@9b18e33f6f42b63c98457ac49c9515c5445e72b0`. Added branch-only `.github/workflows/gate-c-mode7-midframe.yml`; emulator/core/RSP source remains unchanged. Workflow builds/tests the deterministic guest, wraps the exact Sodium64 SHA, runs pinned ares N64 with RSP interpreter, and captures pre-test phase `0x01` then permanent post-test phase `0x33` with guest-frame freshness while allowing static/blank display because pixels are not the oracle. Observed state includes host `bg_mode`, `rsp_slot_proof`, guest IRQ count/mode/done, and the NMI frame sampled at each IRQ. Strict pass requires pre-test regular/proof0 and post-test `irq_count=2`, `done=1`, `irq1_frame=irq2_frame=30`, final BGMODE1, and exact `rsp_slot_proof=0x03`. Artifact upload preserves state/log evidence. Build/Validate also triggers independently on the exact head. Interpret generator/host-test failures as diagnostic plumbing; interpret overlay semantics only after exact build/wrap succeeds.

- **2026-09-20 Visible mid-frame Mode7 guest — IMPLEMENTED / workflow pending:** branch `phase4/gate-c-rsp-mode7-midframe-proof@d3a45f3d4cd1b944e1f8137a1d8ab84d5cd260db` (generator `d61b21f8...`, tests `d3a45f3d...`). Only new `scripts/make_gate_c_mode7_midframe.py` and `scripts/test_gate_c_mode7_midframe.py` were added; core/RSP remains byte-for-byte inherited from validated whole-frame fault-overlay head. Original 32 KiB LoROM holds Mode1 for `PRETEST_FRAMES=30`, then NMI arms V-count IRQ at line 80. Native IRQ #1 records current NMI counter to `$7E0005`, writes BGMODE7 and moves VTIME to line 160; IRQ #2 records current NMI counter to `$7E0006`, writes BGMODE1, disables further V-IRQ, sets permanent post-test phase `0x33` and done flag. Guest state also exposes NMI counter `$7E0000`, phase `$7E0001`, IRQ count `$7E0002`, BGMODE mirror `$7E0003`, done `$7E0004`. Reset explicitly executes `CLI`; vectors target NMI `$8200` and native IRQ `$8300` (`$FFEA/$FFEE`, mirrored emulation vectors as guard). Host tests cover deterministic LoROM, vectors, exactly one Mode7 interval, line-80/160 VIRQ chain, evidence slots and visible-line bounds. **Pass criterion once workflow is attached:** pre-test proof=0; post-test IRQ count=2, done=1, host+guest BGMODE1, `irq1_frame == irq2_frame == 30`, and `rsp_slot_proof==0x03`. Because no BGMODE changes occur after IRQ #2, both overlay proof bits must have been earned inside that one visible frame.

- **2026-09-20 Visible mid-frame Mode1→Mode7→Mode1 proof — STARTED:** new non-candidate branch `phase4/gate-c-rsp-mode7-midframe-proof` forked exactly from measurement-validated whole-frame head `7f51fc318ac5dd474999f693120c518e94b05be4`; core/RSP fault-loader bytes are therefore unchanged from validated real overlay candidate `e24f6a99...`. **Controlled question:** can the already-validated demand-driven regular↔Mode7 fault overlay switch both directions within one visible SNES frame? Planned original guest holds Mode1 for a pre-test window, then enables V-count IRQ at ~line 80; IRQ #1 writes BGMODE7 and reprograms VTIME to ~160; IRQ #2 writes BGMODE1 and disables further V-IRQ. Guest records IRQ count plus the NMI frame counter sampled at each IRQ. Pass requires exactly two IRQs, identical `irq1_frame == irq2_frame` (same V-blank interval), final guest/host BGMODE1, and `rsp_slot_proof==0x03` after the test, with no later BGMODE changes available to set missing proof bits. Pixel fidelity/cadence remains non-authoritative in this architecture discriminator. No master change.

- **2026-09-20 Whole-frame real Mode7 fault overlay — VALIDATED switching primitive in pinned N64 lab:** exact measurement head `phase4/gate-c-rsp-mode7-fault-proof@7f51fc318ac5dd474999f693120c518e94b05be4`; Build/Validate **`35523084315 SUCCESS`** (normal + PROFILE + pinned Mupen/LLE smoke) and Gate C Mode7 Fault Overlay **`35523084251 SUCCESS`**. Core/RSP/guest bytes are unchanged from real fault-overlay candidate `e24f6a99...`; `7f51fc31...` only relaxes the visual-freshness requirement for this architecture proof and observes extra state. Evidence artifact **`10608709113 gate-c-mode7-fault-sodium64-evidence`** gives: initial Mode1 control `bg_mode=1`, `rsp_slot_proof=0x00`, guest NMI counter `10`, `framebuffer=0xA00F2300`, `frame_count=2`; Mode7 treatment `bg_mode=7`, **`rsp_slot_proof=0x02`**, guest counter `69`, `framebuffer=0xA0133D00`, `frame_count=1`; returned Mode1 `bg_mode=1`, **`rsp_slot_proof=0x03`**, `framebuffer=0xA00F2300`, `frame_count=2`. Workflow assertions require treatment bit1 and exact return `0x03`, so both demand-driven RSP-side fault DMAs completed: regular→real Mode7 slot and Mode7→regular slot. Guest/NMI execution survives both transitions. The treatment framebuffer differs from control and return, showing at least one Mode7-era publication occurred; however this state-only proof does **not** establish correct Mode7 pixels or continuous display cadence within the 60-frame phase. **SUPERSEDED interpretation:** run `35522337130`'s static-pointer rejection was a measurement failure for the switching question, not evidence that the fault loader itself failed. **Decision:** whole-frame demand switching primitive is now VALIDATED in the pinned lab. Next controlled discriminator may proceed to the already-audited visible mid-frame `Mode1→Mode7→Mode1` switch, while keeping pixel fidelity/performance claims separate.

- **RESUME HERE — active measurement-only Mode7 fault diagnosis:** branch head `phase4/gate-c-rsp-mode7-fault-proof@7f51fc318ac5dd474999f693120c518e94b05be4`. Core/RSP/guest bytes are unchanged from real fault-overlay candidate `e24f6a99...`; only capture/workflow measurement changed. Active Gate C Mode7 Fault Overlay run **`35523084251`**; active exact-head Build/Validate **`35523084315`**. At checkpoint, diagnostic-build PASS and N64 semantic job has passed host tests and is building exact Sodium64; prior run `35522337130` is closed as runtime divergence: Mode1 control valid/proof=0; guest enters and progresses through Mode7 for ~54 NMIs but global VI framebuffer pointer remains static, causing the visual-freshness helper to reject treatment before reading proof bits. Source audit shows static global framebuffer means no new VI buffer publication, **not** automatically an RSP hard stall; continuing guest NMIs argue against a simple hard stall. New run uses opt-in `--allow-static-display` while preserving +3 guest-frame freshness, observes internal `bg_mode`, `frame_count`, and `rsp_slot_proof`, and still requires treatment Mode7 bit1 plus return-control exact `0x03`. Interpret next result as: treatment proof lacks bit1 -> fault-to-Mode7 did not complete; bit1 present but VI remains static -> fault DMA succeeded and divergence is downstream in Mode7 render/frame publication; return lacks bit0 -> fault-back-to-regular fails; treatment bit1 + return 0x03 + guest progression -> whole-frame demand switching primitive VALIDATED even if Mode7 display publication remains a separate bug. Do not implement the already-designed V-count mid-frame `Mode1→Mode7→Mode1` discriminator until this run closes. Current audited master remains `9441818dd8457a27bbd617a0f32c6d484550661f`; master was not modified in this batch.

- **2026-09-20 Mode7 static-display diagnostic rerun — MEASUREMENT-ONLY PATCH / dispatched:** current head `phase4/gate-c-rsp-mode7-fault-proof@7f51fc318ac5dd474999f693120c518e94b05be4` (`3bacc912...` helper + workflow commit `7f51fc31...`). No emulator/RSP/loader/payload/guest bytes changed from failed run `35522337130`; only measurement plumbing changed. Capture helper adds opt-in `--allow-static-display`: default remains strict and H-OBJ still requires guest freshness + a displayed-buffer transition, while this architecture proof may accept +3 guest NMI frames with static VI pointer and then read state. Workflow now observes internal `bg_mode`, host `frame_count`, and mirrored `rsp_slot_proof`; it still requires Mode7 fault bit during treatment and exact `0x03` after return to Mode1. **Decision discriminator:** treatment proof missing -> fault load itself did not complete; treatment proof bit1 present but VI static -> switching succeeded and divergence is downstream in Mode7 render/publication; return proof missing bit0 -> fault-back path fails. Do not modify core until this exact rerun resolves which case applies.

- **2026-09-20 Mode7 static-display interpretation refinement — SUPPORTED / measurement plan:** source audit shows global `main.S:framebuffer` advances only in the VI interrupt path when `frame_count > 0`; that path both writes `VI_ORIGIN` and stores the next framebuffer pointer before decrementing `frame_count`. Therefore the run-1 observation “guest NMI counter advances but framebuffer pointer never changes during BGMODE7” proves **no new framebuffer is being published to VI**, but does not by itself prove an RSP hard stall. A hard stall is in tension with ~54 guest NMIs continuing through treatment because `rsp_frame` normally waits for RSP HALT. **Next discriminator remains measurement-only:** add an opt-in state-freshness mode that requires guest NMI progress but not a displayed-buffer transition, observe internal `bg_mode`, mirrored `rsp_slot_proof`, and host `frame_count` during control/treatment/return. Readings distinguish: proof bit1 absent -> Mode7 fault not completing; bit1 present but no frames published -> fault DMA succeeded and divergence lies in/after Mode7 rendering or publication; return bit0 absent -> regular fault-back path fails. Keep renderer/loader byte-for-byte unchanged.

- **2026-09-20 Whole-frame real Mode7 fault-overlay run 1 — RUNTIME DIVERGENCE / diagnosis required, not yet architecture rejection:** exact head `phase4/gate-c-rsp-mode7-fault-proof@e24f6a99eb94ad36af8c23d874e1c7703e164c7f`; Gate C Mode7 Fault Overlay run **`35522337130 FAILURE`**, N64 job `106108478422`. All pre-runtime gates PASS: diagnostic generator/tests, exact Sodium64 build, exact wrap/embedded guest comparison, state-symbol location, pinned ares N64 build. Fresh Mode1 control is valid at guest NMI counter **10**, `phase=0x01`, internal `bg_mode=1`, `rsp_slot_proof=0`, framebuffer advanced `0xA0113000 -> 0xA00F2300`. Guest then reaches Mode7 phase and **continues executing NMIs for the full 60-frame treatment window**: freshness samples advance from baseline counter `0x3F` through `0x45,0x4B,...,0x75` (~54 frames) before phase wraps back to `0x01`. However the displayed framebuffer pointer does **not transition once** during that Mode7 window, so the existing freshness helper refuses semantic capture and eventually raises `RuntimeError: did not observe 3 fresh guest frames plus a displayed-buffer transition for phase 0x07`. The same pattern repeats across occurrences until attempts exhaust. **Meaning:** CPU/guest/NMI progression survives the Mode7 request, but render/display progression becomes stuck or ceases to publish buffers during Mode7. This is stronger than a generic timeout, but current evidence cannot distinguish (A) fault DMA never/completely fails, (B) fault DMA completes then real Mode7 renderer stalls, or (C) render completes but framebuffer publication/display path has a Mode7-specific issue. The harness only records `bg_mode/rsp_slot_proof` after freshness succeeds, so treatment proof bits and RSP PC/status are still UNKNOWN. **Next controlled discriminator:** change measurement only—sample internal `bg_mode`, `rsp_slot_proof`, SP_STATUS and SP_PC while guest phase 0x07 is progressing even without framebuffer transitions; keep core/loader/payload unchanged. Do not proceed to mixed-BGMODE or modify renderer until the first stuck point is localized.

- **2026-09-20 Mode7+OBJ resident-DMEM safety audit — MEASURED / closes a broader ABI risk:** although compiled main↔Mode7 DMEM intentionally differs at regular-only `TILE_JUMPS[0..2]` and `CACHE_RETS[0]=get_offsets`, the common `draw_obj` path does **not** consume those entries. OBJ cache invalidation jumps through `CACHE_RETS+4 = start_objects`, whose target is invariant; OBJ character decoding calls resident `shared_decode` directly with `SHARED_JUMPS+4` (and common shared decoder addresses), not `TILE_JUMPS`. Therefore enabling OBJ while the Mode7 slot is resident does not route through overwritten regular BG decoder addresses. This strengthens the resident-main-DMEM contract beyond the current BG1-only whole-frame guest. **REJECTED:** the concern that ordinary Mode7+OBJ rendering would inherently require patching/reloading the four regular-only DMEM code pointers. Other Mode7 compositor/OBJ semantics remain separately unvalidated.

- **2026-09-20 Whole-frame Mode7 fault diagnostic workload identity — MEASURED / pinned:** artifact `10609026903 gate-c-mode7-fault-diagnostic` from run `35522337130` contains exact original guest ROM **32768 bytes**, SHA-256 **`d5fe534c72f809951da98d189d799d9fbcc24340f1103b517843fa2e1add58dd`**. Manifest binds it to source SHA `e24f6a99...`, control `BGMODE=0x01`, treatment `BGMODE=0x07`, `phase_frames=60`, oracle `guest progression + BGMODE state + RSP completed-fault bits`, with pixel semantics explicitly non-authoritative and mid-frame switching explicitly not tested. The N64 workflow additionally `cmp`s the 32 KiB guest re-extracted from wrapped N64 ROM against this generated source, so any eventual runtime result refers to these exact bytes.

- **2026-09-20 Real fault-loader live-register ABI audit — MEASURED / no code change:** dispatcher-to-renderer requirements are compatible with the resident loader. Mode7 dispatch reaches `draw_mode7_entry` with `t1 = (s7 & 1)` established in the branch delay slot; resident `overlay_load_mode7`/`dma_read` uses `a0/a1/a2/t0` and does not clobber `t1`, so re-entry into real `draw_mode7_impl` retains its enable predicate. Regular BG dispatch reaches `draw_bg` with live layer descriptor `t0`, index `t3`, and `s7`; Mode7's fault stub saves `t0 -> v0`, `dma_read` does not touch `v0` or `t3`, and `overlay_load_main` restores `t0` in the re-entry branch delay slot. Therefore the obvious live-register-clobber explanations are **REJECTED** before runtime. If the whole-frame proof fails, investigate actual control/DMA/renderer behavior rather than re-opening these specific register dependencies without new evidence.

- **2026-09-20 Mid-frame follow-up discriminator audit — SUPPORTED DESIGN / not implemented:** source audit shows V-count IRQ is the cleanest next stimulus if whole-frame real Mode7 fault switching passes. `write_bgmode` updates `bg_mode` and calls `update_frame` when changed, marking the current frame section dirty; the scanline loop subsequently materializes a new section. `vcount_irq` invokes the normal guest IRQ vector via `trigger_nmi(a1=4)` (`$FFFE` emulation / `$FFEE` native), and guest writes to `$4209/$420A` update Sodium64's `VTIME` immediately. Therefore one original ROM can start visible rendering in Mode1, take a V-count IRQ around line ~80–112, write `$2105=7` and reprogram VTIME, then take a second visible IRQ later (~160–176), write `$2105=1`, and restore the first VTIME for the next frame. That would demand **regular→Mode7→regular within one visible frame** without introducing HDMA as a second subsystem variable. This is only a staged design; do not implement or interpret it until current whole-frame fault proof closes.

- **2026-09-20 Whole-frame Mode7 fault-proof exact-head Build/Validate — VALIDATED at build/smoke level:** head `phase4/gate-c-rsp-mode7-fault-proof@e24f6a99eb94ad36af8c23d874e1c7703e164c7f`; Build/Validate run **`35522337096 SUCCESS`**. Normal build, PROFILE build and pinned Mupen64Plus debugger + LLE RSP smoke all PASS. This SHA differs from the compiled-layout core evidence only by diagnostic/capture/workflow files, so the already-proven 3352-byte fixed-slot geometry remains the core contract while the exact complete branch also boots/smokes. Dispatcher audit independently confirms BGMODE 7's `LAYER_CHART` contains descriptor `0x40 -> draw_mode7_entry`, whereas Mode1 uses regular BG descriptors -> `draw_bg`; therefore the active whole-frame guest is sufficient to demand both renderer classes. Remaining open authority is Gate C Mode7 Fault Overlay run `35522337130`, specifically runtime treatment/return proof bits and guest progression.

- **2026-09-20 Whole-frame Mode1↔Mode7 diagnostic generation — MEASUREMENT PROOF / PASS:** Gate-C Mode7 Fault Overlay run `35522337130` on exact head `e24f6a99eb94ad36af8c23d874e1c7703e164c7f` has completed `diagnostic-build SUCCESS`; generator host tests pass both in the standalone diagnostic job and the N64 semantic job. The deterministic original 32 KiB guest is generated/uploaded successfully, so the active run is no longer blocked on ROM construction or host validation. Sodium64 N64 semantic job is compiling the exact candidate; runtime fault-switch evidence remains pending and must not be inferred from this generator pass.

- **2026-09-20 Whole-frame real Mode7 fault-overlay semantic workflow — DISPATCHED:** current branch head `phase4/gate-c-rsp-mode7-fault-proof@e24f6a99eb94ad36af8c23d874e1c7703e164c7f`. Added dedicated `.github/workflows/gate-c-mode7-fault.yml`; core/runtime remains the compiled+smoke-validated real regular/Mode7 fault-overlay candidate from `2352bc734...`. The workflow validates/generates the original 32 KiB `Mode1 -> Mode7 -> Mode1` guest, builds/wraps the exact Sodium64 SHA, runs pinned ares N64 with R4300 JIT + required RSP interpreter lab mode, and reuses the guest-NMI fresh-frame capture with targets `0x01 -> 0x07 -> 0x01` plus state-only `--allow-blank`. Authority is deliberately architectural rather than pixel-semantic: observed `bg_mode` must match each phase; treatment must show completed Mode7 fault bit (`rsp_slot_proof & 0x02` with no unexpected bits); returned Mode1 must show **exact `rsp_slot_proof=0x03`**, proving both demand-driven fault DMA directions completed while the guest continued. No direct-SNES visual reference is claimed by this workflow; Mode7 fidelity and mid-frame BGMODE switching remain later discriminators. Await exact-head jobs before interpretation.

- **2026-09-20 Fresh-frame capture generalized for Mode7 proof — IMPLEMENTED:** `phase4/gate-c-rsp-mode7-fault-proof@c6c9b78170d7826aa97623c52f0fb1a67d599743`. `scripts/gate_c_obj_window_capture_n64.py` retains H-OBJ defaults (`control=0x01`, `treatment=0x11`) but now accepts configurable `--control-target`, `--treatment-target`, and optional `--capture-return-control`. The same guest-NMI freshness authority, framebuffer-transition requirement, stale-frame rejection and arbitrary `--observe` state capture remain unchanged. This lets the new whole-frame renderer proof capture `Mode1 -> Mode7 -> Mode1` without forking a weaker synchronization harness. No emulator/RSP source changed in this batch. Next immediate action: add a dedicated workflow that builds/wraps `make_gate_c_mode7_switch.py`, observes `bg_mode` and `rsp_slot_proof`, and requires Mode7 fault completion before treatment plus `0x03` after return to Mode1.

- **2026-09-20 Whole-frame Mode1↔Mode7 guest diagnostic — IMPLEMENTED / harness pending:** branch `phase4/gate-c-rsp-mode7-fault-proof@598f94c0b2b2ef269ffb7e53f467bd625ada1a46` (generator `c8fe80be...`, tests `598f94c0...`). Added original/homebrew-only 32 KiB LoROM `scripts/make_gate_c_mode7_switch.py`: deterministic visible Mode1 setup, NMI frame counter `$7E0000`, BGMODE mirror `$7E0001`, 60-frame control `BGMODE=1`, 60-frame treatment `BGMODE=7`, then wrap to Mode1. This deliberately asks only whether actual renderer demand can alternate across complete frames; Mode7 pixel fidelity is not an oracle here. Host tests verify deterministic LoROM generation and exact BGMODE/mirror writes for values 1 and 7. No core/RSP source changed in this batch. Next batch generalizes the existing fresh-frame capture helper to configurable target values and an optional return-control capture so runtime proof can require Mode7 fault bit first and `0x03` after the return-to-regular fault.

- **2026-09-20 Real Mode7 fault-overlay Build/Validate — VALIDATED at build/smoke level:** exact corrected head `phase4/gate-c-rsp-mode7-fault-proof@2352bc734358fa08c4747c8f278874da35e3d381`; Build/Validate run **`35521939323 SUCCESS`**. Normal build PASS, PROFILE build PASS, and pinned Mupen64Plus debugger + LLE RSP emulator smoke PASS. This validates compile/link/boot/smoke for the actual regular+Mode7 fault-stub architecture and agrees with the separate compiled-layout proof (3352-byte equal text, fixed slot/prefix/suffix invariants, resident loader addresses stable, only four previously-audited regular-only DMEM pointer differences). **Still UNKNOWN:** whether a guest that requests Mode7 causes regular `draw_mode7_entry` to fault-load the real Mode7 slot, whether returning to regular causes Mode7 `draw_bg` to fault-load main while preserving live `t0`, and whether both directions can repeat without stall. Next authority is the staged whole-frame BGMODE 1↔7 diagnostic; mixed-BGMODE within one visible frame remains a later discriminator.

- **2026-09-20 Real Mode7 fault-overlay compiled layout — MEASURED / EXACT PASS:** corrected head `phase4/gate-c-rsp-mode7-fault-proof@2352bc734358fa08c4747c8f278874da35e3d381`, Build/Validate run `35521939323`, normal artifact **`10608941558 sodium64-build`**. `rsp_main.elf`, `rsp_mode7.elf`, and `rsp_swap.elf` each compile to `.text=0xD18 = 3352 bytes` and `.data=0x1000`, leaving **744 bytes IMEM headroom**. Critical addresses are invariant in all three: `draw_bg=A40013A8`, `draw_mode7_entry=A4001788`, `draw_obj=A4001790`, `start_objects=A40017D4`, `dma_read=A4001C94`, `ret_jump=A4001CC4`, `overlay_load_mode7=A4001CCC`, `overlay_load_main=A4001CF0`; explicit metadata labels are `overlay_main_src=A4000E90`, `overlay_mode7_src=A4000E94`, `overlay_proof=A4000E98`. Direct byte extraction proves main↔Mode7 resident prefix `[0,0x3A8)` identical and resident suffix `[0x790,0xD18)` identical; all **935 differing text bytes / 247 words** are confined strictly to fixed slot `[0x3A8,0x790)` (first `0x3A8`, last `0x78B`). Main↔Mode7 DMEM differs only at the already-audited four regular-only code-pointer words `0xE28/0xE2C/0xE30/0xE40`; overlay metadata words at `0xE90/0xE94/0xE98` are identical zero in both compiled payloads. The resident-regular-DMEM strategy therefore remains exactly the prior validated contract: Mode7 does not consume those four regular-only entries, while common/shared targets and new metadata are invariant. Fixed fault encodings are as intended: main `draw_mode7_entry` branches to resident Mode7 loader; Mode7 `draw_bg` branches to resident main loader with `move v0,t0`. **Meaning:** real renderer fault-overlay geometry/ABI is compile-proven; remaining authorities are Build/Validate smoke and a guest workload that actually demands both renderer directions.

- **2026-09-20 Real Mode7 fault-overlay first Build/Validate — HYGIENE FALSE START / superseded:** run **`35521809094 FAILURE`** on intermediate head `f80b67ce821377152df8e1881ab5495c4724dafc`. Normal and PROFILE jobs fail during RSP assembly before final link/runtime because `rsp_main.S:139` and `rsp_swap.S:139` still use the removed `OVERLAY_SWAP_SRC` in a `.byte 0:(...)` repeat expression; assembler reports `unresolvable or nonpositive repeat count` and fatal-warnings stops the build. `rsp_mode7.elf` independently reached `.text=3352`, `.data=4096`, but that partial compile is not architecture evidence. **REJECTED:** interpreting this run as fault-stub/DMA failure. The issue is fully superseded by explicit identical metadata reservation in current head `2352bc734...`; authoritative Build/Validate is `35521939323`.

- **2026-09-20 Real Mode7 fault-overlay DMEM ABI normalization — IMPLEMENTED / current head `2352bc734358fa08c4747c8f278874da35e3d381`:** audit caught a stale proof-only padding expression (`OVERLAY_SWAP_SRC`) in `rsp_main.S`/`rsp_swap.S` and implicit-zero metadata in `rsp_mode7.S`. All three RSP images now explicitly reserve the same words at `OVERLAY_MAIN_SRC=0xE90`, `OVERLAY_MODE7_SRC=0xE94`, and `OVERLAY_PROOF=0xE98`, then zero-fill through `VEC_DATA=0xF70`. This both fixes the removed-symbol compile blocker and makes overlay metadata part of the explicit compiled DMEM ABI rather than an accidental zero gap. No renderer slot code, loader semantics, CPU proof mirror, guest ROM, or workflow changed in this batch. The earlier run on `f80b67ce...` may fail from the stale symbol and must be classified as a hygiene false start if so; authority moves to Build/Validate for this corrected exact head.

- **2026-09-20 Real Mode7 fault-overlay proof plumbing — IMPLEMENTED / compile-layout gate next:** current head `phase4/gate-c-rsp-mode7-fault-proof@f80b67ce821377152df8e1881ab5495c4724dafc`. `ppu.S` no longer reads the semantic-twin IMEM discriminator word. At the existing frame HALT it mirrors raw `DMEM(OVERLAY_PROOF)` into exported RDRAM `rsp_slot_proof`; resident RSP loaders set bit0 only after completed regular-slot DMA and bit1 only after completed Mode7-slot DMA. Therefore eventual `rsp_slot_proof==0x03` directly means both demand-driven renderer faults have completed at least once. No pixel/guest diagnostic has been added yet. **Decision order:** first inspect Build/Validate + compiled RSP layout for this exact head; only if fixed slot/ABI/branch targets remain valid create the whole-frame BGMODE 1↔7 ROM and runtime oracle. Do not debug guest behavior on an unproven binary layout.

- **2026-09-20 Real Mode7 fault stubs + resident loader — IMPLEMENTED / intermediate checkpoint:** branch `phase4/gate-c-rsp-mode7-fault-proof@5b7bb19dd4f63b0827541b56c65de3960d5bfc28` (regular `d74d5a83...`, unused twin build-compat `3e09c3d0...`, Mode7 `5b7bb19d...`). Regular fixed entry `draw_mode7_entry@0x788` is now an 8-byte fault stub to resident `overlay_load_mode7`; Mode7 fixed `draw_bg@0x3A8` is an 8-byte fault stub to `overlay_load_main` with delay-slot `move v0,t0` to preserve the live regular layer descriptor across `dma_read`, restoring `t0` on re-entry. `next_frame` in regular/twin is restored to the original four-instruction HALT/resume footprint, so overlays persist until demanded rather than swapping every frame. Identical resident loaders are appended after existing code in regular/twin/Mode7 source: each DMA-loads exactly `0x3E8` bytes to IMEM `0x13A8`, waits through the already-validated `dma_read`, sets `OVERLAY_PROOF` bit1 (Mode7) or bit0 (regular) only after completion, then re-enters the same fixed slot entry. Existing slot endpoints are source-intent unchanged. This SHA is intermediate because CPU proof plumbing still reads the old semantic-twin discriminator word; next batch mirrors `DMEM(OVERLAY_PROOF)` instead, then compile/layout proof must verify branch targets and resident ABI before runtime use.

- **2026-09-20 Real Mode7 fault-overlay metadata — IMPLEMENTED / intermediate non-runnable checkpoint:** branch `phase4/gate-c-rsp-mode7-fault-proof@e07564d0e8eb47cce0977f66d8c76c32a736df30` (defines commit `5540775e...`). Reserved `OVERLAY_MAIN_SRC=0xE90`, `OVERLAY_MODE7_SRC=0xE94`, and `OVERLAY_PROOF=0xE98` in the already-audited DMEM gap. Boot now publishes aligned `rsp_main_text_start+0x3A8` and **real** `rsp_mode7_text_start+0x3A8` sources and clears proof state; this explicit reference also prevents the Mode7 blob from being garbage-collected from final Sodium64. No RSP stub/loader behavior changed yet, so this SHA is intentionally an intermediate checkpoint rather than evidence. Next atomic batch converts regular/Mode7 fixed 8-byte stubs and the resident loader while preserving validated slot endpoints and resident label addresses.

- **2026-09-20 Next Mode7 overlay discriminator — DESIGN DECISION / staged before implementation:** after self-overlay semantic-twin validation, do **not** jump directly to mixed-BGMODE sections. First prove demand-driven **regular↔real-Mode7 fault switching across whole frames**. New candidate should fork `1fc54f17...`, retain the validated 1000-byte slot, resident loader location and DMEM source metadata mechanism, replace `OVERLAY_SWAP_SRC` with real `OVERLAY_MODE7_SRC`, restore normal frame HALT (remove unconditional semantic-twin self-swap), and use the existing invariant 8-byte slot stubs as faults: regular `draw_mode7_entry@0x788 -> resident load_mode7`; Mode7 `draw_bg@0x3A8 -> resident load_main` while preserving live `t0` through `v0` as previously audited. Reserve a proof byte in the audited DMEM gap so successful completed fault loads set bit0 regular / bit1 Mode7; CPU mirrors that proof for the harness. **First oracle:** a new original 32 KiB SNES diagnostic alternates entire frames between BGMODE 1 and 7 and exposes guest frame/phase state; pass requires both fault bits observed (`0x03`), sustained guest progression, no mismatch/stall, compiled fixed-slot ABI preserved, and existing H-OBJ guard still passes separately in Mode1. **Only after this passes** advance to a second diagnostic that changes BGMODE within one visible frame. This stages renderer-payload correctness separately from intra-frame switching timing.

- **2026-09-20 RSP self-overlay semantic-twin proof — VALIDATED in pinned N64 lab:** exact head `phase4/gate-c-rsp-self-overlay-proof@1fc54f171a891a34da132bbeee7845b66d692367`; Build/Validate **`35520693859 SUCCESS`** and Gate-C semantic run **`35520693846 SUCCESS`**. Compiled/layout evidence remains exact: main/swap `.text=0xD08=3336`, `.data=4096`, identical DMEM, fixed renderer ABI preserved, appended resident `self_swap`, and exactly one inert slot-word difference at text offset `0x78C` (`0x00000000` vs `0x00000025`). Runtime evidence independently proves RSP-initiated self-DMA actually alternated both payloads: fresh control capture at guest NMI counter **6** and treatment at counter **139** both report `rsp_slot_proof=0x03` with no mismatch bit. Registers remain expected (`TMW=0x01/0x11`, `WOBJSEL=0x03`, `WHX=0x000040BF`, `TM=0x11`, `TS=0`). Direct-SNES reference classified **`REFERENCE_CONFIRMS_OUTER_OBJ_MASK_2_TO_0`**; Sodium64 control has **2 outer red OBJ / both present**, treatment **0 / both absent**, classification **`H_OBJ_FALSIFIED_SODIUM64_MASKS_OUTER_OBJ`**. Evidence artifact: `10608206057 gate-c-obj-window-sodium64-evidence`. **Validated meaning:** an executing RSP resident common core can DMA-replace only the exact 1000-byte fixed renderer slot `[0x3A8,0x790)` from RDRAM, repeatedly, while preserving guest progression, resident IMEM/DMEM ABI and repaired H-OBJ semantics in the pinned decision lab. CPU is no longer required as DMA initiator. **Does NOT yet prove:** real regular↔Mode7 fault-stub switching, mixed-BGMODE sections, or real-N64 overlay cost. **Decision:** freeze this semantic-twin branch as architecture evidence; next controlled experiment may introduce the actual Mode7 payload and demand-driven fixed-entry fault stubs, keeping the proven resident loader/metadata mechanism and avoiding unconditional per-frame swaps.

- **2026-09-20 RSP self-overlay Build/Validate — VALIDATED at build/smoke level:** exact head `phase4/gate-c-rsp-self-overlay-proof@1fc54f171a891a34da132bbeee7845b66d692367`; Build/Validate run **`35520693859 SUCCESS`**. Normal build PASS, PROFILE build PASS, and pinned Mupen64Plus debugger + LLE RSP emulator smoke PASS. This is consistent with the exact compiled-layout artifact proof (`rsp_main/rsp_swap .text=0xD08`, one inert slot-word difference, identical DMEM, appended resident loader). **Meaning:** executing a build containing the RSP-side self-DMA mechanism does not break compile/link/boot/smoke in the existing L2 lab. It still does NOT prove both self-DMA payloads actually appeared or preserve H-OBJ under sustained runtime; Gate-C run `35520693846` remains the semantic authority and is still running pinned ares.

- **2026-09-20 RSP self-overlay compiled layout — MEASURED / EXACT PASS:** exact head `phase4/gate-c-rsp-self-overlay-proof@1fc54f171a891a34da132bbeee7845b66d692367`, Build/Validate run `35520693859`, normal artifact **`10608024222 sodium64-build`**. Direct ELF extraction proves `rsp_main.elf` and `rsp_swap.elf` each have `.text=0xD08 = 3336 bytes` and `.data=0x1000`, leaving **760 bytes IMEM headroom**. All pre-existing ABI addresses remain invariant despite the loader: `draw_bg=A40013A8`, `get_offsets=A4001420`, `draw_mode7_entry=A4001788`, `draw_obj=A4001790`, `start_objects=A40017D4`, `next_frame=A4001A84`, shared decode targets unchanged, `dma_read=A4001C94`, `ret_jump=A4001CC4`; appended `self_swap=A4001CCC` lies entirely after previous text. Explicit metadata labels resolve to `overlay_main_src=A4000E90` / `overlay_swap_src=A4000E94`; complete main/swap DMEM remains byte-identical and both words are zero in compiled payload before CPU initialization. Complete main/swap text still differs at exactly **one byte in one word**, text word offset `0x78C`: regular `0x00000000`, swap `0x00000025`; no extra loader/layout difference exists. Final embedded blobs are retained and aligned: `rsp_main_text_start=0x800B76E8`, `rsp_swap_text_start=0x800B93F0`; adding `0x3A8` gives 8-byte-aligned slot sources. **Meaning:** source/compiled one-variable isolation and fixed-slot ABI survive the CPU→RSP DMA transition. Remaining authority is emulator smoke and runtime proof that RSP self-DMA actually produces both discriminator words while preserving guest/H-OBJ semantics.

- **2026-09-20 RSP self-overlay source isolation — MEASURED / PASS before compile:** exact current head `1fc54f171a891a34da132bbeee7845b66d692367`. Direct full-source comparison of `src/rsp_main.S` and `src/rsp_swap.S` still finds exactly **one differing line**, now source line 884: regular assembler `nop` versus swap `or zero,zero,zero` inside fixed slot. The new explicit DMEM metadata reservation, layout-preserving `next_frame` trampoline and appended `self_swap` loader are byte-for-byte source-identical across both images. This establishes one-variable isolation at source level; compiled text/DMEM artifact remains authority for actual layout and encoding.

- **2026-09-20 RSP self-overlay proof validation plumbing — DISPATCHED:** current exact head `phase4/gate-c-rsp-self-overlay-proof@1fc54f171a891a34da132bbeee7845b66d692367`. Core experiment is repaired `22830cfe...`; only subsequent change retargets existing `.github/workflows/gate-c-obj-window.yml` from the frozen CPU-partial branch to this self-overlay branch. Diagnostic generator, guest ROM hash, fresh-frame capture, direct-SNES reference and semantic assertions are unchanged, including strict `rsp_slot_proof==0x03` for both control/treatment. Build/Validate also runs on this push. **Validation order remains:** compiled RSP geometry/isolation -> smoke -> runtime IMEM readback -> H-OBJ semantics. Do not interpret semantic green before compiled layout is checked.

- **2026-09-20 RSP self-overlay branch tree repair — HYGIENE FALSE START / repaired before evidence:** first atomic commit `0a7e6e95a088ea7a43cde485989e40c751f55a1c` accidentally used an empty Git tree base because the connector commit wrapper did not expose the parent tree SHA in the assumed field; its diff therefore showed mass deletion of unrelated repository files. **REJECTED as build/runtime evidence and never interpreted.** Rather than rewrite history, child commit `22830cfea5dfa3da54f25cf2ec382692b3670fad` rebuilt the tree from the authoritative parent tree `dcd85e6cf631d39b1093ebf5f3052d43a260970d` and reapplied only the five intended experiment blobs. Verified compare `cb4df864... -> 22830cfe...` now contains exactly `src/defines.h`, `src/main.S`, `src/ppu.S`, `src/rsp_main.S`, and `src/rsp_swap.S`; no unrelated add/delete remains. **Operational lesson:** for future Git Data API tree creation, obtain `tree.sha` from `/git/commits/<sha>` explicitly; do not infer it from the higher-level commit wrapper. Current technical experiment head is `22830cfe...`; the prior malformed tree is superseded plumbing only.

- **2026-09-20 RSP self-overlay semantic-twin proof — IMPLEMENTED / build pending:** `phase4/gate-c-rsp-self-overlay-proof@0a7e6e95a088ea7a43cde485989e40c751f55a1c`, forked from validated host-partial head `cb4df864...`. One atomic core commit changes `defines.h`, `main.S`, `ppu.S`, `rsp_main.S`, and `rsp_swap.S`. Named DMEM words `OVERLAY_MAIN_SRC=0xE90` and `OVERLAY_SWAP_SRC=0xE94` are explicitly reserved inside the previously audited zero-filled gap; CPU initializes them after boot-time DMEM upload with aligned `rsp_*_text_start+0x3A8` addresses, which also retains both blobs under GC. CPU frame-boundary logic no longer performs any SP DMA: after observing HALT it reads only IMEM word `0x178C` and records regular/swap/mismatch bits independent of queue expectation. Both semantic-twin RSP images make the same layout-preserving change: four-word `next_frame` becomes `b self_swap` + three nops, and identical `self_swap` is appended after all existing code. Loader selects opposite payload from current `sp`, DMA-reads exactly 1000 bytes to `0x13A8` using existing resident `dma_read`, waits for completion, then executes the original HALT/resume/toggle sequence. Existing renderer slot contents and the sole inert `rsp_main`/`rsp_swap` difference at `0x78C` are unchanged by source intent. **Required before runtime interpretation:** compiled artifact must prove fixed entries/common labels remain at prior addresses, main/swap equal size <=4096, DMEM identity, and exactly one text word difference still confined to the slot. Gate-C workflow has not yet been retargeted; build evidence comes first.

- **2026-09-20 RSP self-overlay semantic-twin proof — STARTED:** new non-candidate branch `phase4/gate-c-rsp-self-overlay-proof` forked exactly from validated CPU-driven partial-slot evidence head `cb4df864adab9f6f28376bac5fbbbada08a3b044`. **Single controlled variable:** move the same 1000-byte regular/semantic-twin slot alternation from CPU-initiated SP DMA to RSP-initiated DMA; keep renderer semantics, fixed slot geometry, one-word `0x78C` discriminator, guest ROM and H-OBJ oracle unchanged. Planned proof preserves every existing common label by keeping `next_frame` at the same 16-byte footprint and appending an identical resident loader after existing text. CPU will initialize aligned slot-source pointers in the audited DMEM gap and, at frame HALT, perform readback only. Pass requires compiled layout isolation, both IMEM discriminator values observed, guest progression and the exact validated H-OBJ result. Real Mode7/fault-stub semantics remain explicitly out of scope.

- **2026-09-20 CPU-driven fixed-slot replacement — VALIDATED in pinned N64 lab:** exact evidence head `phase4/gate-c-rsp-partial-slot-proof@cb4df864adab9f6f28376bac5fbbbada08a3b044`; Build/Validate run **`35519876382 SUCCESS`** (normal + PROFILE + pinned Mupen/LLE smoke); Gate-C semantic run **`35519876375 SUCCESS`**. Compiled artifact **`10607968318 sodium64-build`** proves `rsp_main`/`rsp_swap` text are both 3280 bytes, DMEM is byte-identical, and the complete IMEM images differ at exactly one 32-bit word inside the fixed slot, text offset `0x78C`: `0x00000000 -> 0x00000025`. Runtime readback then independently proves both partial payloads actually reached SP IMEM: fresh control capture at guest NMI counter **8** and treatment at counter **131** both report `rsp_slot_proof=0x03` with no mismatch bit, while preserving `WOBJSEL=0x03`, `WHX=0x000040BF`, `TM=0x11`, `TS=0`, and expected `TMW=0x01/0x11`. Direct-SNES reference remained `REFERENCE_CONFIRMS_OUTER_OBJ_MASK_2_TO_0`; Sodium64 framebuffer evidence artifact **`10607824101 gate-c-obj-window-sodium64-evidence`** reports control outer OBJ `[true,true]` / 2 red components and treatment `[false,false]` / 0 red components, classification `H_OBJ_FALSIFIED_SODIUM64_MASKS_OUTER_OBJ`. **Validated meaning:** while RSP is halted at the existing frame boundary, CPU-initiated replacement of only the exact 1000-byte fixed renderer slot `[0x3A8,0x790)` at IMEM `0x13A8` is functionally safe in the pinned decision lab, preserves resident IMEM/DMEM ABI and guest progression, and the byte-distinct swap is not a no-op false positive. **Does NOT prove:** RSP-initiated self-DMA, real Mode7 payload switching, mixed-BGMODE sections, overlay transfer cost on real N64, or final architecture correctness. **Decision:** freeze this proof branch as evidence; next controlled discriminator changes only the DMA initiator CPU→RSP while retaining the same semantic-twin payloads and H-OBJ oracle.

- **2026-09-20 Next discriminator refinement — TODO ONLY IF current host-partial proof PASSES:** do **not** combine first RSP self-DMA with real Mode7/fault semantics. The next controlled experiment should keep `rsp_main`/`rsp_swap` semantically equivalent and change only the DMA initiator from CPU to RSP. Safe/layout-preserving construction: current common `next_frame` lies in resident suffix and is exactly four instructions (`li halt; mtc0 halt; b draw_frame; xori sp`). Replace those four words with `b self_swap` plus three explicit nops so every following existing common label retains its address; append identical `self_swap` loader code after current final text so no validated address moves. Loader selects regular/swap slot source from explicit DMEM pointers, issues existing RSP `dma_read` to `IMEM 0x13A8` for `0x3E8` bytes, waits completion, then performs the original HALT/resume/toggle sequence. CPU at `rsp_wait` performs **readback only**, classifying IMEM word `0x178C` as regular `0`, swap `0x25`, or mismatch and requiring both values before semantic acceptance; CPU must no longer write the slot in this discriminator. Keep exact H-OBJ guest/oracle unchanged. **Pass would validate RSP self-overlay mechanics while renderer semantics remain constant.** Only after that should replace semantic twin with actual Mode7 + fault stubs. This ordering better satisfies one-variable-at-a-time discipline than jumping directly to Mode7 self-overlay.

- **2026-09-20 Fault-stub register-preservation correction — MEASURED / supersedes one detail of prior design note:** audit of resident dispatch + regular renderer shows `t0` is still live across `next_layer -> draw_bg`: it holds the `LAYER_CHART` descriptor and regular `draw_bg` later consumes bit `0x40` for priority. Existing RSP `dma_read` clobbers `t0` in `dma_wait`. Therefore the earlier shorthand that an overlay loader could freely use/clobber `t0` before regular re-entry is **REJECTED**. Minimal compatible design remains available without enlarging the fixed 8-byte fault stub: in the Mode7 payload's `draw_bg` fault stub, branch to resident loader with delay slot `move v0,t0`; loader may use current `dma_read`, then restore `move t0,v0` before branching back to fixed `draw_bg`, now replaced by regular payload. Mode7 re-entry does not depend on the old layer-descriptor `t0`, but can use the same preservation convention if desired. **Additional layout refinement:** append the common loader after the current final resident text rather than inserting it into the existing suffix; with current `.text=0xCD0` and 816 bytes IMEM headroom, this can add substantial loader code while keeping every already-validated common label/DMEM code pointer at its existing address. This is design evidence only; do not implement until host-side partial-slot semantic proof closes.

- **2026-09-20 Embedded overlay-source alignment audit — MEASURED / future self-overlay prerequisite supported:** exact final `build/sodium64.elf` from artifact `10607968318` places referenced RSP text blobs at `rsp_main_text_start=0x800B76E8` and `rsp_swap_text_start=0x800B93B8`; both are 8-byte aligned, and adding fixed slot offset `0x3A8` preserves 8-byte alignment for SP DMA sources. The Makefile's RSP binary embedding explicitly sets `.data` section alignment to 8, so the same contract applies when another RSP blob is retained. **Important current-proof nuance:** `rsp_mode7.elf` is built/exposed as an independent artifact but its embedded blob is garbage-collected from the final Sodium64 ELF because current runtime does not reference `rsp_mode7_text_start`. A future self-overlay candidate must explicitly reference its Mode7 slot source (e.g. when initializing DMEM overlay pointers), which both retains the blob under `--gc-sections` and supplies the required source address. Do not mistake independent `rsp_mode7.elf` existence for current ROM residency.

- **2026-09-20 Partial-slot attempt 2 Build/Validate — VALIDATED at build/smoke level:** exact head `phase4/gate-c-rsp-partial-slot-proof@cb4df864adab9f6f28376bac5fbbbada08a3b044`; Build/Validate run **`35519876382 SUCCESS`**. Normal build PASS, PROFILE build PASS, and pinned Mupen64Plus debugger + LLE RSP smoke PASS for both normal/profile artifacts. Compiled-artifact isolation is separately exact (main/swap 3280-byte text, identical 4096-byte DMEM, one intended word difference at `0x78C`). **Meaning:** the fixed 1000-byte host-side slot DMA + CPU IMEM readback guard does not break compile/link/boot/smoke in the current emulator lab. This still does NOT prove that both byte-distinct payloads are actually observed at runtime or that H-OBJ remains semantically correct; Gate-C run `35519876375` is the remaining authority and is still running.

- **2026-09-20 Partial-slot attempt 2 compiled binary isolation — MEASURED / EXACT PASS:** exact normal artifact `10607968318 sodium64-build` from Build/Validate run `35519876382`, head `cb4df864adab9f6f28376bac5fbbbada08a3b044`. Direct extraction of `.text`/`.data` from `build/src/rsp_main.elf`, `rsp_swap.elf`, and `rsp_mode7.elf` proves: `rsp_main` and `rsp_swap` text are both **3280 bytes (`0xCD0`)**, DMEM is **4096 bytes and byte-for-byte identical**, and their complete text differs at exactly **one byte / one 32-bit word**, text offset **`0x78C`**: regular `0x00000000`, swap `0x00000025`. That word is strictly inside fixed slot `[0x3A8,0x790)` and corresponds exactly to CPU readback address `SP IMEM 0x178C`; no other byte differs anywhere. Re-audit against compiled `rsp_mode7` independently reconfirms resident prefix `[0,0x3A8)` identical, resident suffix `[0x790,0xCD0)` identical, all **935** regular-vs-Mode7 text differences confined to the slot (first `0x3A8`, last `0x78B`), and the same four expected regular-only DMEM words at `0xE28/0xE2C/0xE30/0xE40`. **Meaning:** experiment isolation and readback discriminator are now compiled-artifact proven. Remaining authorities are general emulator smoke, runtime `rsp_slot_proof==0x03`, and fresh H-OBJ semantic result.

- **2026-09-20 Partial-slot attempt 2 compile checkpoint — COMPILE PASS / smoke+semantics pending:** exact head `phase4/gate-c-rsp-partial-slot-proof@cb4df864adab9f6f28376bac5fbbbada08a3b044`; Build/Validate run `35519876382`. Normal build job and PROFILE build job both completed SUCCESS; exact Gate-C N64 semantic candidate also compiled, linked and wrapped successfully. General emulator-smoke is still running, so do not yet mark L2 validation complete. Normal build artifact `10607968318 sodium64-build` exposes all RSP ELFs. Preliminary ELF inspection confirms `rsp_main.elf` and `rsp_swap.elf` both retain `.text=0xCD0=3280`, `.data=0x1000=4096`; fixed ABI labels remain identical (`draw_bg=A40013A8`, `draw_mode7_entry=A4001788`, `draw_obj=A4001790`, `start_objects=A40017D4`, shared decode targets unchanged). Next immediate measurement is exact byte diff of compiled main/swap text+DMEM before interpreting runtime semantics.

- **2026-09-20 Partial-slot readback guard attempt 2 — IMPLEMENTED / CI dispatched:** `phase4/gate-c-rsp-partial-slot-proof@cb4df864adab9f6f28376bac5fbbbada08a3b044`. Only `src/ppu.S` proof plumbing changed from `ced2456e...`: each `rsp_slot_proof` byte store now executes before the unconditional branch, and both branch delay slots are explicit `nop`; no pseudo-instruction remains in those delay slots. Partial DMA helper (`0x13A8`, `0x3E8` bytes), `rsp_main`/`rsp_swap` payloads, IMEM readback word `0x178C`, H-OBJ renderer logic and semantic workflow are unchanged. Await exact-head Build/Validate first; only if compile/layout passes should runtime readback/H-OBJ be interpreted.

- **2026-09-20 Partial-slot readback guard attempt 1 — HARNESS/ASSEMBLY FALSE NEGATIVE:** exact head `phase4/gate-c-rsp-partial-slot-proof@ced2456e25d97bc7c4bee1b0d4edd24705a7e235`; Build/Validate run `35518944250 FAILURE`; Gate-C diagnostic run `35518944194 FAILURE`. Both normal/profile builds stop before final link/runtime in `src/ppu.S` because proof-only `sb t0,rsp_slot_proof` pseudo-instructions were placed in branch delay slots at source lines 599 and 607; assembler warns each macro expands to multiple instructions and warnings are fatal. The semantic N64 job fails at the same compile step, while direct-SNES reference still passes. All three RSP sources independently reached assembly and report unchanged `.text=3280`, `.data=4096`. **REJECTED:** interpreting these runs as evidence against partial-slot DMA, IMEM readback, H-OBJ, or renderer ABI. Controlled repair is proof-plumbing only: move the `sb` stores before their branches and use explicit `nop` delay slots; keep the DMA primitive, payloads, slot geometry and semantic oracle unchanged.

- **RESUME HERE — active Gate-C experiment / CI result not yet observable from current tool session:** branch head `phase4/gate-c-rsp-partial-slot-proof@ced2456e25d97bc7c4bee1b0d4edd24705a7e235`. Both branch workflows are configured to trigger on this push, but the available GitHub connector exposes only PR-filtered commit-run lookup and returns no push-run IDs; public Actions/API fallback is blocked in this environment. **Do not infer PASS/FAIL from that tooling limitation.** On next resume, inspect the exact-head Build/Validate and Gate C OBJ Window runs/artifacts if now available. Required decision order: (1) compile/smoke and artifact proof that `rsp_main`/`rsp_swap` remain equal-size/ABI and differ exactly at the intended slot word; (2) runtime `rsp_slot_proof==0x03` with no bit7 mismatch, proving both partial payloads actually reached IMEM; (3) fresh H-OBJ control/treatment retains the validated SNES 2→0 oracle. Only if all three pass should the next controlled experiment implement the separately documented RSP-side fault-stub self-overlay. `master` remains untouched.

- **2026-09-20 Fault-stub self-overlay design — SUPPORTED INTERPRETATION / preferred next architecture if partial DMA validates:** fixed-slot source/compiled geometry already provides two 8-byte inactive-renderer stubs at invariant slot entries: regular image `draw_mode7_entry=0x788` is `branch+nop`; Mode7 image `draw_bg=0x3A8` (with regular-only aliases) is likewise `branch+nop`. These can become **fault stubs** of the same size: when the currently loaded payload lacks the requested renderer, branch out of `[0x3A8,0x790)` into a common resident loader in the suffix, DMA the opposite 1000-byte slot using the existing resident RSP `dma_read`, then jump back to the same fixed entry now containing the real renderer. This keeps the validated slot endpoints/prefix unchanged and naturally switches only on actual renderer demand. No explicit current-overlay state is required: the loaded payload itself determines which entry is real versus faulting. Existing dispatch context is compatible with a resident loader using only `a0/a1/a2/t0`: regular re-entry needs `t3/s7`; Mode7 re-entry needs `t1/s7`; existing `dma_read` clobbers `t0` but not those required values. The audited DMEM candidate `0xE90...` need only hold the two RDRAM source pointers. **Advantage over an unconditional section-boundary selector:** no CPU mid-frame intervention, no new prefix code, no DMA for sections/layers that never enter the absent renderer, and BGMODE changes are still handled naturally through existing per-section layer dispatch. **Still HYPOTHESIS until current host-side partial-slot proof passes and a separate RSP self-DMA discriminator validates it; real-N64 transfer cost remains a later authority question.**

- **2026-09-20 Partial-slot runtime readback guard — IMPLEMENTED / CI redispatched:** current proof head `phase4/gate-c-rsp-partial-slot-proof@ced2456e25d97bc7c4bee1b0d4edd24705a7e235` (runtime guard commit `b0b9864f8a814399024bc4448ed0c1812e6d613c`, workflow assertion `ced2456e...`). Identified a proof weakness: the H-OBJ ROM never executes the inactive `draw_mode7_entry` word that distinguishes `rsp_main` and `rsp_swap`, so semantic PASS alone could not prove the byte-distinct payload actually reached IMEM. Controlled guard now reads uncached SP IMEM word `0xA400178C` immediately after each 1000-byte DMA while RSP remains halted. Expected regular word is `0x00000000`; expected swap word is semantic-NOP `0x00000025`. Proof-only RDRAM byte `rsp_slot_proof` records bit0 regular verified, bit1 swap verified, bit7 any mismatch and is deliberately placed outside the 0x40-byte section state. Gate-C capture now observes this symbol and requires **exactly `0x03` in both fresh control and treatment captures**. Therefore a final semantic PASS will establish both actual alternation of the byte-distinct partial payload and preservation of the H-OBJ oracle; a mismatch cannot masquerade as a renderer PASS. No RSP renderer/DMEM source or Mode7 policy changed.

- **2026-09-20 RSP DMEM overlay-metadata capacity audit — MEASURED / candidate ABI space, no code change:** current DMEM macro geometry places `PRIO_CHECKS=0xE7C` (8 live bytes), `WIN_BOUNDS=0xE84`, and `VEC_DATA=0xF70`. Source-wide audit of `rsp_main.S`, `rsp_mode7.S`, `rsp_swap.S`, `ppu.S`, and `main.S` finds window-bound generation/consumption confined to `WIN_BOUNDS+0..+4`; no symbolic or raw-address references were found in the remainder before `VEC_DATA`. Therefore `0xE89..0xF6F` is presently unreferenced by audited code, with a clean 8-byte-aligned candidate block **`0xE90..0xF6F` = 224 bytes**. **Supported use:** future RSP-side self-overlay can reserve two RDRAM slot-source pointers plus current-overlay state in this existing zero-filled DMEM gap without shifting section/frame/RDP/table addresses or touching compiled jump-table ABI. This is source-level reachability evidence, not yet a runtime/compiled overwrite proof; when implemented, reserve explicit named offsets and add an artifact/sentinel check so future scratch growth cannot silently overlap them.

- **2026-09-20 Per-section Mode7 selector audit — MEASURED / architecture support, no code change:** `SECTION_SIZE=0x40`. CPU `make_section` copies the contiguous 0x40-byte PPU state block beginning at `bghofs` into each queued section; that block includes `TMW`, `BG_MODE`, `STAT_FLAGS` and `SPLIT_LINE`. RSP `next_section` DMA-loads exactly `SECTION_SIZE` bytes into DMEM before drawing the section, then already reads `BG_MODE` to select `LAYER_CHART` using its low nibble. Therefore the information needed to choose regular versus Mode7 renderer is already present **per section inside the running RSP**, including frames with mid-frame BGMODE changes. **Supported architecture consequence:** if the current host-side partial-slot DMA primitive validates, the final selector should be investigated as an RSP-side overlay transition at section boundaries keyed from loaded `BG_MODE & 0xF`, rather than a frame-only CPU selector or a new side-channel. This does not yet validate self-DMA cost/correctness, mixed-mode rendering, or real N64 behavior.

- **2026-09-20 Partial-slot source isolation — MEASURED / PASS before compile:** exact head `a6e02d070a0a0a0880cc53c6e0094735f96a6328`. Direct source comparison of `src/rsp_main.S` and new `src/rsp_swap.S` finds exactly **one differing line**, at source line 880: regular `nop` versus swap `or zero,zero,zero` in the delay slot of the inactive `draw_mode7_entry` stub. No label, instruction count, renderer logic, DMEM source, OBJ repair, or shared helper differs between the twins. Compare from structural-proof head `bf388685...` to current head shows core delta limited to `src/main.S` (dedicated partial DMA helper), `src/ppu.S` (slot selector), and new `src/rsp_swap.S`; the other changes are validation plumbing only. **This proves experiment isolation at source level, not compiled binary geometry.** Artifact proof must still establish equal text/DMEM sizes and exactly one word difference within `[0x3A8,0x790)`.

- **2026-09-20 Partial renderer-slot proof validation plumbing — IMPLEMENTED / CI dispatched:** experimental head `phase4/gate-c-rsp-partial-slot-proof@a6e02d070a0a0a0880cc53c6e0094735f96a6328`. Core/runtime remains exactly the partial-slot implementation checkpointed at `1e1621ca...`; subsequent commits only synchronize the already-validated guest-frame semantic capture (`da8c4931...`), retarget the existing Gate-C OBJ-window workflow to this proof branch (`28c68b4f...`), and expose `build/src/rsp_swap.elf` beside the existing RSP ELFs in Build/Validate artifacts (`a6e02d07...`). **Validation order:** (1) Build/Validate and compiled artifact geometry/diff; (2) H-OBJ direct-SNES reference + Sodium64 fresh-frame oracle. Do not interpret semantic results if layout/diff isolation fails first.

- **2026-09-20 Partial renderer-slot runtime proof — IMPLEMENTED / build pending:** branch `phase4/gate-c-rsp-partial-slot-proof@1e1621caa41239e853bd4987f0a0881a58647c10` (sequential source commits `49b2cd0f...` main helper, `37fe21fb...` selector, `1e1621ca...` semantic twin). Added `rsp_upload_slot`, a dedicated SP DMA helper with fixed `SP_RD_LEN=0x3E7` (1000 bytes), leaving boot-time `rsp_upload` as full 4096-byte DMA. At the existing frame-boundary RSP HALT, `ppu.S` now alternates by queue bit between `rsp_main_text_start+0x3A8` and `rsp_swap_text_start+0x3A8`, DMA destination `0x13A8`; no DMEM reload and no prefix/suffix IMEM transfer occurs. New `rsp_swap.S` is a source copy of the validated fixed-slot regular renderer and differs intentionally only in the `draw_mode7_entry` delay slot (`nop` vs `or zero,zero,zero`), which is semantically equivalent and strictly inside `[0x3A8,0x790)`. **Required next check before semantic interpretation:** Build/Validate must prove `rsp_main`/`rsp_swap` equal text/DMEM sizes and binary differences confined to exactly that slot/word; smoke must pass. Then attach the existing Gate-C H-OBJ oracle. No Mode7 policy is selected by this proof.

- **2026-09-20 Partial renderer-slot runtime proof — STARTED / branch created:** new non-candidate branch `phase4/gate-c-rsp-partial-slot-proof` forked exactly from fixed-slot evidence head `bf388685a06c301d553a0791e4e5b43255a1c122` (structural source `41a2c990...`). No emulator/runtime changes yet. **Controlled question:** can Sodium64 alternate a byte-distinct but semantically equivalent **1000-byte fixed renderer slot** at the already-validated frame-boundary HALT point while leaving resident prefix/suffix and DMEM untouched? Canonical geometry is text offset `[0x3A8,0x790)`, SP destination `0x13A8`, transfer size `0x3E8` bytes (`SP_RD_LEN=0x3E7`). Planned discriminator keeps the regular renderer semantics in both slot payloads and introduces one semantic-NOP encoding difference strictly inside the slot; pass requires general Build/Validate plus the already-validated Gate-C H-OBJ semantic oracle. Real Mode7 selection remains out of scope until this primitive passes.

- **2026-09-20 Fixed renderer-slot structural proof — MEASURED / VALIDATED:** structural source `phase4/gate-c-rsp-fixed-slot-proof@41a2c990777862f653f39a2ee8b3d3999512d0d3` passed complete Build/Validate run **`35515622537 SUCCESS`**, including normal/profile builds and Mupen LLE smoke. Evidence-only workflow SHA `bf388685a06c301d553a0791e4e5b43255a1c122` exposed the individual RSP ELFs; normal build artifact **`10607290461`** gives exact compiled facts. Both regular and Mode7 RSP texts are **3280 bytes (`0xCD0`)**, leaving **816 bytes IMEM headroom**. Local labels are invariant where required: `draw_bg=0x3A8` (`A40013A8`), `draw_mode7_entry=0x788` (`A4001788`), `draw_obj=0x790` (`A4001790`), so the exact renderer overlay slot is **`[0x3A8,0x790)` = 1000 bytes (`0x3E8`)**, 8-byte aligned at both endpoints. The dispatcher branch words resolve identically in both images: `bltz -> draw_obj 0x790`, `beq -> draw_mode7_entry 0x788`, `bnez -> draw_bg 0x3A8`. Byte comparison proves the resident prefix **`[0,0x3A8)` is identical** and the common suffix **`[0x790,0xCD0)` is identical**; all text differences are confined to the fixed slot (935 differing bytes, first `0x3A8`, last `0x78B`). DMEM differences collapse from the previous 8 words to exactly the predicted **4 regular-only words**: `TILE_JUMPS[0..2]` at `0xE28..0xE30` and `CACHE_RETS[0]=get_offsets` at `0xE40`. Shared/common references are now invariant: `SHARED_JUMPS={A4001B34,A4001B18,A4001AE0}` in both images and `CACHE_RETS[1]=start_objects=A40017D4` in both. Mode7-side regular-only entries point to its `draw_bg` stub and remain unconsumed by the audited Mode7 renderer path. **This compiled evidence SUPERSEDES the earlier design-only offsets `0x3C0/0x7A0/0x7A8` and predicted 3292-byte text.** Runtime partial-DMA candidate geometry is therefore source offset `+0x3A8`, SP destination `0x13A8`, length **1000**, `SP_RD_LEN` logical length-1 **`0x3E7`**. **Next controlled proof:** validate partial-slot replacement itself with byte-distinct but semantically equivalent images before introducing real BGMODE-driven regular/Mode7 policy.

- **2026-09-20 Fixed-slot proof artifact exposure — IMPLEMENTED / CI pending:** `phase4/gate-c-rsp-fixed-slot-proof@bf388685a06c301d553a0791e4e5b43255a1c122`. Only `.github/workflows/autobuild.yml` changed from structural source SHA `41a2c990...`; validation artifacts now include the already-generated `build/src/rsp_main.elf` and `build/src/rsp_mode7.elf` for both normal/profile jobs. No build flags, source code, linker layout, renderer semantics, or runtime behavior changed. Purpose is solely to make exact local-label and byte-layout validation inspectable; remove/avoid carrying this diagnostic artifact plumbing into an eventual integration unless independently useful.

- **2026-09-20 Fixed-slot first compile — COMPILE PASS / artifact limitation:** exact branch `phase4/gate-c-rsp-fixed-slot-proof@41a2c990777862f653f39a2ee8b3d3999512d0d3`, Build/Validate run `35515622537`. Normal and profile compile jobs PASS. Their individual RSP linker maps both report `.text=0xCD0 = 3280 bytes` and `.data=4096`, so the two renderer variants are equal-sized after alignment; this falsifies the design arithmetic expectation of 3292 bytes but is compatible with a potentially cleaner layout. **Do not yet call structural ABI PASS:** the normal Sodium64 final link garbage-collects unreferenced `rsp_mode7.o` (visible in `sodium64.map` as discarded `.data 0x1CD0`), so the uploaded final ELF contains only the regular RSP blob. The current artifact therefore cannot compare the two compiled text blobs byte-for-byte or resolve local renderer labels. **Next controlled measurement:** expose the already-built `build/src/rsp_main.elf` and `build/src/rsp_mode7.elf` in this proof branch's validation artifact, then inspect exact label offsets, resident prefix/suffix identity, and the targeted DMEM pointer words. This is a measurement plumbing fix only; no renderer/runtime semantics change.

- **2026-09-20 Fixed renderer-slot structural proof — IMPLEMENTED / CI pending:** new non-candidate branch `phase4/gate-c-rsp-fixed-slot-proof@41a2c990777862f653f39a2ee8b3d3999512d0d3`, forked from dual-image proof `e8df4c0e...`. One atomic source-only commit changes only `src/rsp_main.S` and `src/rsp_mode7.S`. Both dispatchers now target invariant `draw_mode7_entry`; both align the overlay start before `draw_bg` to 8 bytes. Regular image leaves the full BG renderer directly at `draw_bg`, aligns its inactive Mode7 stub to the far slot edge, and renames that stub `draw_mode7_entry`. Mode7 image keeps the aligned regular-BG skip stub at slot start, renames the real renderer `draw_mode7_impl`, then places fixed `draw_mode7_entry` after the body and branches backward into the local implementation. No CPU selector, BGMODE policy, partial DMA helper, runtime swapping, or master change is included. **Exact build discriminator:** compiled regular and Mode7 text must be equal size; `draw_bg`, `draw_mode7_entry`, and `draw_obj` offsets must match; bytes before the slot and after `draw_obj` must be identical; proposed target is slot `[0x3C0,0x7A8)` = 1000 bytes and full text 3292 bytes. If compiler output disagrees, adjust/reject layout before any runtime overlay work.

- **2026-09-20 Byte-distinct full-IMEM swap semantic discriminator — VALIDATED in pinned N64 lab:** exact candidate `phase4/gate-c-obj-window-diagnostic@513502a761e5ab2a306a88bcdb23dcb147515576`; Build/Validate `35514980885 SUCCESS`; Gate C semantic run **`35514980884 SUCCESS`**. Direct-SNES reference job passed the pinned `REFERENCE_CONFIRMS_OUTER_OBJ_MASK_2_TO_0` oracle. Repaired guest-frame synchronization captured genuinely fresh Sodium64 states: control at guest NMI counter **10**, framebuffer `0xA00F2300`, `phase=0x01`, `TMW=0x01`; treatment at guest counter **150**, framebuffer `0xA0133D00`, `phase=0x11`, `TMW=0x11`; both retained `WOBJSEL=0x03`, `WHX=0x000040BF` (`64/191`), `TM=0x11`, `TS=0`. Artifact **`10606333036 gate-c-obj-window-sodium64-evidence`** reports control **3 red OBJ components / both outer present** and treatment **1 central component / both outer absent**, classification `H_OBJ_FALSIFIED_SODIUM64_MASKS_OUTER_OBJ`. **Validated meaning:** at the existing frame-boundary HALT point, repeated replacement of complete RSP IMEM with a byte-distinct but semantically equivalent image preserves guest progression, renderer state, and the repaired H-OBJ observable. The previous stale-capture 3→3 reading is definitively superseded as a measurement false negative. **Does NOT prove:** Mode7 renderer selection/correctness, partial-slot DMA, intra-frame BGMODE switching, mixed regular/Mode7 sections, or real-N64 DMA cost. **Decision:** raw distinct-code replacement is no longer the blocker; advance to the fixed-slot structural build proof before any runtime partial-overlay policy.

- **2026-09-20 Fixed-slot layout v2 — SUPPORTED INTERPRETATION / SUPERSEDES adjacent-entry 1008-byte candidate:** a lower-overhead invariant geometry falls directly out of the compiled body sizes. Keep overlay start aligned at **`0x3C0`**, but place fixed `draw_bg_entry` at `0x3C0` and fixed `draw_mode7_entry` at **`0x7A0`** rather than adjacent. Regular image: start the 988-byte regular BG body directly at `0x3C0` (no extra hot-path trampoline), ending `0x79C`; add 4 bytes invariant padding, then an 8-byte Mode7 skip stub at `0x7A0`. Mode7 image: put the existing 8-byte regular-BG skip stub at `0x3C0`, start the 984-byte real Mode7 body at `0x3C8`, which ends **exactly `0x7A0`**; fixed `draw_mode7_entry` there branches backward to `0x3C8` with a delay-slot nop. Both variants therefore end the overlay at **`draw_obj=0x7A8`**, giving a fixed **1000-byte / `0x3E8`** slot, 8-byte-aligned start/end/length. Common 1332-byte suffix yields equal full text size **3292 bytes**, leaving **804 bytes IMEM headroom**. Runtime cost is minimized: regular BG remains direct; regular's Mode7 skip and Mode7's BG skip keep one branch as today; only active Mode7 gains one local branch from its fixed entry to the real body. Back-branch displacement (~-247 instructions) is safely within MIPS branch range. Proposed partial DMA becomes IMEM `0x13C0`, length 1000 (`SP_RD_LEN` logical length-1 `0x3E7`), source `rsp_*_text_start+0x3C0`. **This supersedes the earlier 1008-byte adjacent-entry design before implementation; artifact proof remains mandatory and may still falsify exact offsets due assembler/link layout.**

- **2026-09-20 Fixed-entry reference audit — MEASURED / closed transformation surface:** source-wide reference scan of both current RSP variants shows `draw_bg` is referenced only by the single `bnez t0,draw_bg` dispatcher branch plus its label, and `draw_mode7` only by the single `beq t0,t1,draw_mode7` dispatcher branch plus its label. `draw_obj` likewise has one dispatcher entry reference (`bltz t0,draw_obj`; separate `draw_objtile` is unrelated). No hidden caller elsewhere depends on the variant-specific renderer entry addresses. **Meaning:** replacing those two dispatcher targets with invariant fixed slot-entry labels is a locally closed structural transformation; the subsequent artifact proof can attribute any prefix divergence to layout/relocation rather than unknown call sites.

- **2026-09-20 Fixed-slot concrete layout candidate — SUPPORTED INTERPRETATION / build proof not yet implemented:** compiled attempt-3 geometry permits a clean 64-bit-aligned slot without exceeding IMEM. Current common prefix ends at old `draw_bg=0x3BC`; insert one invariant 4-byte pad so overlay begins at text offset **`0x3C0`**. Reserve two 8-byte fixed entry trampolines (`draw_bg_entry` and `draw_mode7_entry`) in the first 16 bytes. Current regular renderer body excluding its 8-byte Mode7 stub is **988 bytes**; current Mode7 renderer body excluding its 8-byte regular-BG stub is **984 bytes**. Therefore regular overlay payload is `16+988=1004` bytes (pad 4) and Mode7 is `16+984=1000` bytes (pad 8), yielding one fixed **1008-byte / `0x3F0` slot** ending at **`draw_obj=0x7B0`**. Common suffix is already 1332 bytes in both compiled images, so both full texts would become **3300 bytes**, leaving **796 bytes IMEM headroom**. The proposed DMA destination is `IMEM 0x13C0`, transfer length 1008 (`SP_RD_LEN` logical length-1 `0x3EF`); because RSP text blobs are embedded with 8-byte section alignment, `rsp_*_text_start + 0x3C0` is also source-aligned. **Important ABI nuance:** do not require complete DMEM identity. Keep regular compiled DMEM resident; regular-only `TILE_JUMPS` / `CACHE_RETS[0]` may point into regular overlay and are safe only because the audited Mode7 path never consumes them. Structural proof must instead verify (1) fixed entry offsets, (2) byte-identical resident prefix, (3) byte-identical common suffix, (4) invariant shared/common DMEM targets including `CACHE_RETS[1]=start_objects`, and (5) regular-only table reachability remains absent in Mode7. These numbers are a design target until compiler artifact proves them exactly.

- **2026-09-20 Fixed-slot DMA contract — MEASURED / REQUIRED SUPPORT:** current compiled renderer slot begins at IMEM text offset `0x3BC`, which is 4-byte but **not 8-byte aligned**. The already-recorded SGI/N64 overlay contract requires 64-bit-aligned IMEM/RDRAM DMA endpoints, so `0x3BC` cannot be the final overlay DMA start. Current CPU helper `rsp_upload` in `src/main.S` also hardcodes `SP_RD_LEN=0x00000FFF`, i.e. a full 4096-byte transfer regardless of destination; it cannot be reused unchanged for a partial renderer overlay. **Structural requirement before runtime overlay:** move the fixed overlay start to an 8-byte-aligned IMEM offset (e.g. by keeping invariant padding in the resident prefix), reserve invariant BG/Mode7 entry trampolines inside that aligned slot, make the slot end/common `draw_obj` address invariant, and choose a fixed transfer length satisfying RSP DMA alignment/length rules. Only then add a bounded overlay-DMA primitive; do not turn the existing full-IMEM proof helper into the final architecture by accident.

- **2026-09-20 Fixed renderer-slot entry-point audit — MEASURED / architecture refinement:** direct extraction of attempt-3 compiled IMEM blobs (Build/Validate `35494205081`, artifact `10600257127`) proves that equalizing only the slot *end* is insufficient to make the resident prefix binary-invariant. Both variants enter `draw_bg` at IMEM text offset `0x3BC`. The common pre-slot `bltz t0,draw_obj` at `0x394` encodes target `0x7A0` in regular vs `0x79C` in Mode7, exactly the known 4-byte slot-length delta; padding Mode7 by 4 bytes before `draw_obj` can stabilize this and the common suffix. However the pre-slot `beq t0,t1,draw_mode7` at `0x39C` encodes `0x110900FE` in regular (target `0x798`, its end-of-slot Mode7 stub) versus `0x11090009` in Mode7 (target `0x3C4`, its real Mode7 renderer). Therefore the prefix is not truly resident-byte-identical until **renderer entry addresses themselves are fixed**. Preferred structural proof: reserve fixed `draw_bg_entry` and `draw_mode7_entry` trampolines at invariant offsets at the start of the overlay slot; each overlay may branch from those fixed entries to its own local implementation/stub, then pad the variant so `draw_obj` begins at the same address. Internal overlay branch encodings may differ; resident prefix and common suffix must not. This also preserves the prior DMEM strategy: regular-only `TILE_JUMPS` / `CACHE_RETS[0]` may remain resident because Mode7 does not consume them, while shared/common targets become address-stable. **Do not implement runtime self-overlay until the active byte-distinct semantic swap discriminator closes.**

- **2026-09-20 Gate-C guest-frame freshness repair — IMPLEMENTED / CI pending:** `phase4/gate-c-obj-window-diagnostic@513502a761e5ab2a306a88bcdb23dcb147515576`. Only `scripts/gate_c_obj_window_capture_n64.py` changed from `87c4e093...`; emulator/RSP/PPU/guest ROM are unchanged. The capture harness now treats the diagnostic's `$7E0000` NMI counter (immediately before phase mirror `$7E0001`) as freshness authority: after observing the target phase it requires at least **+3 guest frames** and at least one displayed-framebuffer pointer change, then records `guest_frame_counter` in semantic state. This replaces the invalid assumption that three distinct VI framebuffer-pointer transitions must fit inside every sampled 120-frame phase. **Pass discriminator:** direct reference remains 2→0 and Sodium64 control/treatment complete with verified registers and repaired H-OBJ result. **Fail interpretation:** inspect the first failing condition; do not attribute a harness synchronization failure to renderer semantics.

- **2026-09-20 Gate-C semantic freshness rerun — MEASUREMENT LIMITATION, not semantic failure:** exact run `35513233767` on `phase4/gate-c-obj-window-diagnostic@87c4e093ededb0a02509feafb3e4857069e3fc3d` completed with the direct-SNES reference job PASS but Sodium64 semantic capture FAIL in the harness before analysis/artifact upload. Control `phase=0x01` successfully observed three framebuffer-pointer transitions (`0xA0113000 → 0xA00F2300 → 0xA0113000`) and captured. Treatment `phase=0x11` repeatedly produced only two transitions within each active phase window (first observed `0xA00F2300`, then `0xA0133D00`) before the guest returned to `0x01`; the harness eventually raised `RuntimeError: did not observe 3 displayed-frame transitions while phase 0x11 remained active`. **Meaning:** the previous stale-frame false-negative remains rejected, but the new three-transition rule is too strong for the diagnostic's treatment-phase duration and therefore supplies no H-OBJ or swap semantic verdict. The run does show guest execution continues cycling between control/treatment under the byte-distinct swap. **Next controlled repair:** use the diagnostic's guest NMI/frame counter at `$7E0000` as the freshness authority (phase at `$7E0001`), requiring capture from a later guest frame rather than assuming three VI framebuffer rotations can occur inside one phase. Keep emulator/RSP sources unchanged so the discriminator remains isolated.

- **2026-09-20 Gate-C semantic-capture freshness repair — IMPLEMENTED / rerun dispatched:** `phase4/gate-c-obj-window-diagnostic@87c4e093ededb0a02509feafb3e4857069e3fc3d`. Emulator/RSP sources are unchanged from byte-distinct attempt 4; only `scripts/gate_c_obj_window_capture_n64.py` changed. After observing control or treatment WRAM phase, the harness now requires **3 actual displayed-framebuffer pointer transitions while that phase remains active** before accepting semantic pixels. Three transitions deliberately flush Sodium64's three-buffer/display backlog rather than equating “nonzero buffer” with “frame rendered after phase change.” If the phase rolls over before settling, the helper waits for the next occurrence and restarts the transition count. **Expected discriminator:** if the byte-distinct swap is semantically safe, the refreshed run must recover the validated repaired H-OBJ control/treatment result; if it still yields 3→3 after fresh display transitions, treat that as genuine swap/runtime evidence. No renderer code, OBJ logic, IMEM payload or guest ROM changed.

- **2026-09-20 Distinct-IMEM attempt 4 first semantic read — MEASUREMENT FALSE NEGATIVE / harness freshness bug:** Gate-C run `35512578619` completed `SUCCESS`; direct SNES reference remained `REFERENCE_CONFIRMS_OUTER_OBJ_MASK_2_TO_0`. Sodium64 reached verified control `phase=0x01,TMW=0x01` and treatment `phase=0x11,TMW=0x11` without stall, but both captures used the **same displayed framebuffer pointer `0xA0113000`**; treatment was accepted on `render_attempt=1` and classified old 3→3 behavior. Audit of `scripts/gate_c_obj_window_capture_n64.py` shows that after `wait_for_phase` it accepts any non-zero framebuffer while the WRAM phase matches; it does **not** require a framebuffer transition or any newly rendered/displayed frame after the phase change. Therefore a nonblank control-era triple-buffer can be mislabeled as treatment. **REJECTED:** interpreting this 3→3 capture as an H-OBJ or distinct-swap semantic regression. **Controlled repair:** change only the N64 capture harness to require multiple displayed-framebuffer pointer transitions while the target phase remains active before semantic capture, enough to flush the triple-buffer pipeline; then rerun exact SHA semantics. Emulator/RSP source must remain unchanged for this discriminator.

- **2026-09-20 Fixed renderer-slot ABI consequence — SUPPORTED INTERPRETATION:** source comparison of the validated-size regular/H-OBJ and Mode7/common/H-OBJ variants shows an identical prefix through the dispatch immediately before `draw_bg:`, a single variant region from `draw_bg:` through the code immediately before `draw_obj:`, and an identical common suffix beginning at `draw_obj:`. Source instruction-line counts for that variant region are 244 regular versus 241 Mode7, while linked total text differs by only 4 bytes (3284 vs 3280 in current common-trampoline builds). The compiled-DMEM audit explains the needed invariant: common-suffix targets such as `SHARED_JUMPS` and `CACHE_RETS[1]=start_objects` must retain identical addresses. A **fixed-size renderer slot padded to the larger variant** would make `draw_obj` and every common suffix label address-stable; resident regular DMEM can then keep regular-only `TILE_JUMPS` / `CACHE_RETS[0]` addresses because the audited Mode7 renderer region does not reference `TILE_JUMPS`, `CACHE_RETS`, `SHARED_JUMPS`, `clear_cache`, `shared_decode`, or `get_offsets`. **Implication:** the cleaner architecture target is one resident common RSP core + one fixed renderer slot, not two independent full-IMEM/DMEM ABIs. This is not yet implemented or runtime-validated; after attempt 4 closes, first prove by build artifact that padding yields byte-identical common prefix/suffix and stable shared-table targets before attempting partial/self-overlay DMA.

- **2026-09-20 RSP split ABI audit — MEASURED / compiled DMEM is NOT identical:** artifact from attempt 3 Build/Validate run `35494205081` (artifact `10600257127`) contains both RSP variants. Although their `.data` source text is the same, direct extraction of the linked 4096-byte DMEM payloads shows **12 differing bytes**, all in code-address tables: `TILE_JUMPS` at DMEM `0xE28`, `SHARED_JUMPS` at `0xE34`, and `CACHE_RETS` at `0xE40`. Examples: regular `TILE_JUMPS={0xA40016A0,0xA4001694,0xA400168C}` versus Mode7-proof aliases all `0xA40013BC`; regular/shared return targets are also shifted by 4 bytes or more. **Interpretation:** full text-only swapping between differently laid-out renderer images while retaining the boot-time regular DMEM leaves stale cross-image code pointers. This is an independent confound in attempt 3 in addition to the intentionally stubbed regular renderer, and it invalidates the earlier shorthand claim that source-DMEM identity proved ABI identity. **Architecture requirement:** a final fixed-slot overlay must keep all addresses referenced from resident DMEM tables stable across variants (preferred via equal-size fixed overlay slot/padding and common post-slot layout), or explicitly patch/reload the affected table entries together with an overlay. Reloading all 4 KiB DMEM per swap would destroy persistent renderer/cache state and is not acceptable by default. Attempt 4 remains a clean discriminator because `rsp_main` and `rsp_swap` have identical code layout, so their compiled jump-table targets are expected identical; its semantic run remains pending.

- **2026-09-20 Distinct-IMEM attempt 4 binary isolation — MEASURED / exact:** Build artifact `sodium64-build` from run `35512578706` (artifact `10605417482`, digest `sha256:e675e687ea777d3f7440186d14fafbf883e00d7251058d33103e4a87a4618c19`) contains `rsp_main` and `rsp_swap` text blobs of exactly 3284 bytes each. Direct binary comparison shows exactly **one 32-bit word differs**, at text byte offset 64: regular image `0x00000000` versus swap image `0x00000025`; this corresponds to the intended startup semantic-NOP encoding and lies before the common halted-frame resume path. Thus the active discriminator is genuinely byte-distinct while holding size, layout, renderer logic and DMEM ABI constant. Runtime/semantic authority remains Gate-C run `35512578619`; binary identity evidence alone does not validate swapping.

- **2026-09-20 Distinct-IMEM attempt 4 build/smoke — VALIDATED at L1/L2, semantic oracle pending:** exact SHA `291230685303576652a20f98d4dc487b0ca498b5`; Build/Validate run `35512578706 SUCCESS`, including normal build, PROFILE build and pinned Mupen/LLE emulator smoke. `rsp_main` and byte-distinct semantic twin `rsp_swap` both measure exactly 3284-byte text / 4096-byte DMEM; `rsp_mode7` remains 3280 bytes but is not selected by this test. **Meaning:** adding and alternating the semantic-twin image does not break link/boot/smoke and preserves equal layout/size. This still does not prove correct repeated distinct-IMEM resume under the Gate-C observable; run `35512578619` is the remaining authority for this discriminator.

- **2026-09-20 Distinct-IMEM attempt 4 compile/layout checkpoint — MEASURED / PASS, runtime pending:** exact SHA `291230685303576652a20f98d4dc487b0ca498b5`; Build/Validate run `35512578706`. Normal and PROFILE compile jobs pass. Measured RSP text sizes: `rsp_main.elf = 3284` bytes, `rsp_swap.elf = 3284` bytes, `rsp_mode7.elf = 3280` bytes; therefore the byte-distinct regular proof image preserves identical text size to the validated regular image and both remain well below 4096-byte IMEM. The only intended semantic difference between main/swap remains none; the source change is one startup semantic-NOP encoding and the selector target. **Still UNKNOWN:** runtime distinct-image resume and exact H-OBJ oracle until emulator-smoke + Gate-C diagnostic complete. Do not infer swap success from compilation alone.

- **2026-09-20 Distinct-IMEM swap attempt 4 — RUNNING, confound removed:** branch `phase4/gate-c-obj-window-diagnostic@291230685303576652a20f98d4dc487b0ca498b5`. This preserves the address-stable common HALT trampoline from attempt 3 but replaces the amputated Mode7 proof image in the alternating selector with new `src/rsp_swap.S`: a byte-for-byte semantic copy of the validated regular/H-OBJ renderer except for one startup delay-slot instruction encoded as `or zero,zero,zero` instead of assembler `nop`. Code layout, DMEM ABI, renderer functionality and H-OBJ semantics are therefore intended identical while IMEM bytes are genuinely distinct. `rsp_mode7.S` remains present but unused by this discriminator. **Question:** can the halted RSP repeatedly resume correctly after full-IMEM replacement with a different binary when renderer semantics are held constant? **Pass:** Build/Validate succeeds and exact Gate-C diagnostic again produces reference 2→0 plus Sodium64 repaired control/treatment semantics. **Fail:** distinct-image replacement still has a lower-level PC/state/ABI issue and must be diagnosed before returning to regular/Mode7 switching. This experiment does not validate Mode7 selection, in-frame switching, DMA cost, H-SAMPLE or H-COMP.

- **2026-09-20 Distinct-IMEM swap attempt 3 — PARTIAL ARCHITECTURE PASS / semantic oracle CONFOUNDED by proof image:** exact SHA `0e25de92b5992b188268fde10acb3da88603061f`; Build/Validate run `35494205081 SUCCESS`; Gate-C diagnostic run `35494205033 FAILURE`. Unlike attempt 2, the guest now progresses through both diagnostic phases: control captured at `0x01` and treatment reached/captured at `0x11`. This supports the address-stable common `frame_halt` trampoline hypothesis and rejects the earlier interpretation that any distinct-image swap necessarily stalls execution. The visual failure is **not a valid H-OBJ regression result**: the proof alternates into `rsp_mode7.S`, which intentionally stubs normal `draw_bg`, while the diagnostic guest is SNES Mode 1. The failed control framebuffer had no green BG at all and red 8x8 components at unrelated coordinates (e.g. x=12/y=30, x=12/y=62, x=74/y=62, x=12/y=114), rather than the known H-OBJ probes; treatment happened to capture the expected single central probe. Therefore `INDETERMINATE_CONTROL_OUTER_[False, False]` is a **proof-design confound**, not evidence against the validated OBJ repair. **Decision:** preserve the common HALT trampoline, but stop using an intentionally amputated renderer as the second image for raw swap validation. Next discriminator: alternate between two byte-distinct but semantically equivalent copies of the validated regular/H-OBJ image with identical code layout/ABI; a single semantically neutral instruction encoding difference is sufficient to prove distinct IMEM replacement. Pass must restore the exact H-OBJ oracle in both phases. Only after raw distinct swap is isolated should Mode7 selection semantics be tested.

- **2026-09-20 Distinct-IMEM swap proof attempt 3 — RUNNING with address-stable HALT trampoline:** branch `phase4/gate-c-obj-window-diagnostic@0e25de92b5992b188268fde10acb3da88603061f`. Evidence before change: regular and Mode7 RSP source are identical from `.text` through the start of `draw_bg`; attempt 2 stalls after control `0x01` only when swapping distinct binaries. Controlled repair changes both RSP images identically: startup branches over a new common `frame_halt` block placed in the shared prefix; variant-local `next_frame` now only branches to `frame_halt`. The common block issues SP HALT, then on unhalt branches to common `draw_frame` while toggling the frame slot. **Hypothesis:** attempt 2 halted with a layout-sensitive resume PC inside/after variant code; forcing the halt/resume instruction sequence into an address-identical prefix will restore guest progression across distinct-image swaps. **Pass:** exact Gate-C oracle reaches both phases and H-OBJ remains correct while general build/smoke passes. **Fail:** PC-layout explanation is falsified or incomplete; inspect explicit SP_PC/state before any further overlay work.

- **2026-09-20 Distinct-IMEM swap proof attempt 2 — RUNTIME FAIL / architecture discriminator:** exact candidate `phase4/gate-c-obj-window-diagnostic@1bc2c3821695764427fe42c8c6126390fb7d7526`. Build/Validate run `35493615555 SUCCESS` including normal, PROFILE and pinned Mupen/LLE smoke. Gate C OBJ Diagnostic run `35493615540 FAILURE`: pinned direct-SNES reference still passed, and Sodium64 reached/captured the control state correctly at phase `0x01` with expected `TMW=0x01`, `WOBJSEL=0x03`, `WH0/WH1=64/191`, `TM=0x11`, `TS=0`; after the first distinct-image alternation, however, guest phase remained `0x01` through all 50 treatment polls and never reached `0x11`. **MEASURED meaning:** repeatedly replacing full IMEM with distinct binaries at the current HALT boundary is NOT yet safe even though same-image reload was validated and both images independently compile/smoke. This is not evidence against H-OBJ semantics. **Primary next hypothesis:** the halted RSP resumes from its current SP_PC, while post-variant labels/instruction offsets can differ between `rsp_main` and `rsp_mode7`; same-image reload hides that problem. **Next discriminator:** obtain exact `draw_frame`/`next_frame` symbol offsets (and, if possible, halted SP_PC), compare both images, then test an explicit known-common resume PC only if evidence supports the mismatch. Do not start self-overlay or H-SAMPLE/H-COMP until this runtime stall is explained.

- **2026-09-20 RSP overlay architecture research — SUPPORTED by platform documentation:** SGI's Nintendo 64 RSP Programmer's Guide explicitly distinguishes (1) a host-CPU microcode **swap** that loads full IMEM while RSP is halted and (2) a dynamic **overlay** initiated by currently executing RSP microcode to replace part of IMEM. The guide states IMEM is explicitly managed, overlay DMA source/destination must be 64-bit aligned, and because IMEM is single-ported, simultaneous instruction fetch + DMA share access so dynamic overlay transfer can approach only ~50% of peak DMA bandwidth; overlay load cost is therefore real and should be minimized. Nintendo/SGI examples also use microcode overlays in shipping graphics paths. **Impact:** a resident RSP loader + regular/Mode7 overlay is now a hardware-supported architecture candidate rather than an invented workaround, and it can in principle handle BGMODE changes between visible sections without CPU intervention. **Still UNKNOWN:** exact partition/ABI, overlay target range, self-DMA correctness in Sodium64, switch frequency/cost, ares-vs-real-N64 behavior and cadence. Do not select this architecture solely from documentation; first close current distinct-image swap proof, then build the smallest self-overlay experiment and measure it.

- **2026-09-20 Distinct-IMEM swap proof attempt 2 — RUNNING:** repaired branch `phase4/gate-c-obj-window-diagnostic@1bc2c3821695764427fe42c8c6126390fb7d7526`. Only change from attempt 1 is delay-slot legality: selector branch now has explicit `nop`, with `la rsp_mode7_text_start` executed only after the branch decision. Experimental question, two RSP images and frame-alternating selector are unchanged. Build/Validate run `35493615555`; Gate C OBJ Diagnostic run `35493615540`. Pass/fail interpretation remains exactly as previously recorded.

- **2026-09-20 Distinct-IMEM swap proof attempt 1 — HARNESS/ASSEMBLY FALSE NEGATIVE:** `phase4/gate-c-obj-window-diagnostic@2d7fbcf09b462c93c67825853a9d89107d1f156c`, Build/Validate run `35493499986 FAILURE`. Both normal/profile builds stop in `src/ppu.S:569` before linking/runtime: assembler warns that pseudo-instruction `la a1,rsp_mode7_text_start` expands to multiple instructions in a branch delay slot; warnings are fatal. No swap or semantic result occurred. **REJECTED as evidence about distinct-image switching.** Controlled repair: keep the same selector and images, put an explicit `nop` in the branch delay slot and perform each `la` only on its selected path. Gate-C diagnostic run `35493500005` was still running/expected to encounter the same compile defect; do not interpret it semantically.

- **2026-09-20 Gate-C distinct-IMEM swap proof — RUNNING:** canonical diagnostic branch advanced to `phase4/gate-c-obj-window-diagnostic@2d7fbcf09b462c93c67825853a9d89107d1f156c`. Added the validated-size `rsp_mode7.S` image (full Mode7, regular BG stub, exact H-OBJ repair) and replaced the prior same-image reload with frame-alternating selection at the already-validated SP-HALT boundary: queue bit 2 chooses `rsp_main_text_start` vs `rsp_mode7_text_start`. Both images share identical source DMEM and the common `draw_frame` resume prefix. **Question:** can Sodium64 repeatedly replace IMEM with genuinely different binaries while preserving execution and the H-OBJ observable? **Pass:** Build/Validate succeeds and Gate-C OBJ diagnostic still yields pinned reference 2→0 plus repaired Sodium64 outer-OBJ suppression with verified register state. **Expected limitation:** the Mode7-side image intentionally has regular BG stubbed, so this proof cannot validate general image fidelity and must never merge; it only proves binary swap/ABI safety. **Fail:** reject the distinct-image switching primitive or locate state/PC/ABI mismatch before any BGMODE policy work.

- **2026-09-20 Gate-C dual-image compile proof — VALIDATED at build/smoke level:** Build/Validate run `35493369275 SUCCESS` for `phase4/gate-c-rsp-dual-image-proof@e8df4c0e40cdf99bfae3b2d29ee4179743c3e75f`; normal build, PROFILE build and pinned Mupen/LLE RSP smoke all passed. Measured RSP sizes remain regular/H-OBJ `3268/4096` and Mode7/common/H-OBJ `3264/4096`; source DMEM regions are identical. **Meaning:** both renderer images can coexist in one Sodium64 binary without linker/boot/smoke failure. This still does not prove runtime switching between them or Mode7 correctness. Proceed to distinct-image HALT-boundary swap proof with the exact Gate-C H-OBJ semantic oracle as guardrail.

- **2026-09-20 Gate-C dual-image compile proof — MEASURED / COMPILE PASS, smoke pending:** `phase4/gate-c-rsp-dual-image-proof@e8df4c0e40cdf99bfae3b2d29ee4179743c3e75f`, Build/Validate run `35493369275`. Both normal/profile compile+link jobs passed with two simultaneous RSP images: regular/H-OBJ `rsp_main.elf .text=3268` bytes and Mode7/common/H-OBJ `rsp_mode7.elf .text=3264` bytes, each with `4096` bytes DMEM. Their source `.data` regions are byte-for-byte identical (6178 source chars, no divergence), supporting a shared DMEM ABI; the resume entry `draw_frame` lies in their common pre-variant prefix. **Interpretation:** the 4 KiB IMEM limit no longer prevents shipping both renderer variants as RDRAM-resident images; each leaves ~828/832 bytes of IMEM headroom for Gate-C fidelity. This is compile/capacity evidence only. Emulator-smoke job in run `35493369275` was still running at checkpoint; do not claim runtime pass yet. **Next after smoke:** prove actual replacement between distinct images at the already-validated HALT boundary while preserving the H-OBJ observable; do not add BGMODE-driven policy until raw distinct-image swapping is validated.

- **2026-09-20 Gate-C dual-image compile proof — RUNNING:** new non-candidate branch `phase4/gate-c-rsp-dual-image-proof@e8df4c0e40cdf99bfae3b2d29ee4179743c3e75f`, forked from the validated halted-reload proof `15e423db...`. Added `src/rsp_mode7.S` as a second independently linked RSP image derived from the symmetric Mode7/common proof: full Mode7 path retained, regular BG path intentionally stubbed, and the exact semantically validated H-OBJ W1 repair transplanted into its OBJ path. Existing `rsp_main.S` remains the regular-renderer image with Mode7 stubbed and validated H-OBJ repair. **Question:** can both corrected images coexist in the N64 binary while each remains <=4096-byte IMEM and preserves the same DMEM ABI? Build/Validate run `35493369275` is pending at checkpoint. **Pass:** both RSP images compile/link under 4096; then inspect text/data sizes and verify DMEM payload compatibility before any runtime alternating-image test. **Fail:** do not add selector logic; repair partition/build layout first. This branch is architecture proof only and intentionally lacks full rendering in either individual image; never merge as-is.

- **2026-09-20 Gate-C halted-IMEM reload primitive — VALIDATED in emulator lab:** exact branch `phase4/gate-c-obj-window-diagnostic@15e423db41437a70038cbee4069df5b30d25a039`. Build/Validate run `35490736875 SUCCESS`; Gate C OBJ Diagnostic run `35490736879 SUCCESS`. Controlled change reloads the same complete RSP IMEM image only after `ppu.S:rsp_wait` observes SP HALT. Pinned direct-SNES reference remains `REFERENCE_CONFIRMS_OUTER_OBJ_MASK_2_TO_0`; Sodium64 still classifies `H_OBJ_FALSIFIED_SODIUM64_MASKS_OUTER_OBJ` with verified control `TMW=0x01` and treatment `TMW=0x11`, `WOBJSEL=0x03`, `WH0/WH1=64/191`, `TM=0x11`, `TS=0`. **VALIDATED meaning:** full 4 KiB IMEM replacement at the existing halted frame boundary is functionally safe in the pinned N64 emulator decision lab and does not disturb the repaired H-OBJ oracle. **Does NOT prove:** switching between distinct renderers, switching inside a frame, Mode7 correctness, or acceptable real-N64 DMA/performance cost. **Decision:** the raw upload primitive is no longer the architecture uncertainty. Next batch should prove two distinct IMEM images can be built and alternated while preserving common ABI/entrypoints and observable rendering, before adding BGMODE-driven selection. A frame-only selector remains insufficient as a final architecture because SNES software may change BGMODE between visible sections.

- **2026-09-20 Gate-C halted-IMEM reload primitive — RUNNING:** active diagnostic branch advanced to `phase4/gate-c-obj-window-diagnostic@15e423db41437a70038cbee4069df5b30d25a039` from semantically validated H-OBJ regular image `dc8ba5e4...`. Controlled proof change only: export existing `main.S:rsp_upload` and, after `ppu.S:rsp_wait` observes SP HALT, DMA the **same current 4 KiB IMEM image** back to SP IMEM before UI/update/unhalt. No renderer selection, Mode7 restoration, section ABI, window semantics, game logic or RSP code is changed. **Question:** is full-IMEM replacement at the already-existing halted frame boundary functionally safe enough to serve as the primitive for a future regular/Mode7 image switch? **Pass:** Build/Validate green and the exact Gate-C OBJ oracle remains reference 2→0 / Sodium64 repaired outer-OBJ suppression with verified state. **Fail:** any build/runtime/oracle divergence rejects or relocates this upload point before designing dual images. This proof does not address mixed-BGMODE within one frame and does not measure real-N64 DMA cost; those remain separate future questions. If pass, next batch may construct two renderer images or a smaller overlay-slot proof without changing semantics.

- **2026-09-20 H-OBJ semantic discriminator — VALIDATED repair semantics / monolithic integration still BLOCKED:** exact candidate `phase4/gate-c-obj-window-diagnostic@dc8ba5e4e8037a6c72d785c41bae9d8a651f7e87`; Gate C OBJ Diagnostic run `35488675648 SUCCESS`; Build/Validate `35488675644 SUCCESS`. Pinned direct-SNES reference independently classified `REFERENCE_CONFIRMS_OUTER_OBJ_MASK_2_TO_0`: the two outer OBJ probes visible in control disappear when only TMW bit4 is enabled. On the repaired Sodium64 regular-renderer proof image, synchronized state was control `TMW=0x01`, treatment `TMW=0x11`, `WOBJSEL=0x03`, `WH0/WH1=64/191`, `TM=0x11`, `TS=0`; framebuffer analysis changed from 3 total red OBJ components to 1 central component and classified `H_OBJ_FALSIFIED_SODIUM64_MASKS_OUTER_OBJ`, i.e. outer OBJ are correctly masked after the generic W1 repair. **Interpretation:** the previously proposed OBJ-window repair is semantically capable of matching the isolated SNES oracle; the old baseline omission is a real correctness defect. This does **not** yet attribute Iron's exact SMW iris symptom solely to H-OBJ and does not validate Mode7 or mixed-renderer behavior. The candidate is intentionally non-mergeable because Mode7 is stubbed solely to recover IMEM. Build reports RSP text 3268 bytes / 828 bytes free; the same repair overflowed the monolithic image by 148 bytes. **Decision:** stop questioning the H-OBJ repair logic. The next uncertainty is integration architecture: preserve both regular BG and Mode7 while fitting the corrected OBJ/window semantics without returning to a near-full 4 KiB monolithic RSP image. Use the already-measured symmetric ~3.1 KiB regular-vs-Mode7 split evidence to design the smallest runtime/common-core overlay proof; do not start H-SAMPLE/H-COMP in parallel until that integration question is resolved or explicitly deferred.

- **2026-09-20 H-OBJ regular-image proof — COMPILE PASS / semantic jobs still running:** exact diagnostic SHA `dc8ba5e4e8037a6c72d785c41bae9d8a651f7e87` compiles successfully; Build/Validate run `35488675644` records RSP `.text = 3268 bytes`, leaving **828 bytes** free in 4096-byte IMEM. This is the same H-OBJ repair that overflowed the monolithic image by 148 bytes, now fitting comfortably once only Mode7 is excluded. Therefore the earlier failure is confirmed as an IMEM-capacity/integration failure, not a compile defect in the repair itself. **Still UNKNOWN:** semantic correctness until Gate C OBJ Diagnostic run `35488675648` completes the pinned direct-SNES 2→0 reference and Sodium64 control/treatment capture. At checkpoint time both reference and N64-lab jobs had built the exact guest/candidate and were compiling pinned ares; do not infer oracle outcome yet.

- **2026-09-20 H-OBJ semantic/capacity proof dispatched on canonical diagnostic branch:** `phase4/gate-c-obj-window-diagnostic@dc8ba5e4e8037a6c72d785c41bae9d8a651f7e87`. This advances the existing diagnostic branch without rewriting history and copies byte-for-byte the RSP source from `phase4/gate-c-obj-window-regular-proof@940876d...`: validated generic W1 OBJ repair from `9d41bcd...` plus the compile-proof-only Mode7 stub from `07f011d2...`. Reason for using this branch is only that the already-validated Gate C OBJ workflow is intentionally scoped to it; no workflow was changed. **Authority boundary:** exact 2→0 oracle may validate H-OBJ repair semantics in a regular-renderer image; this SHA can never be a merge candidate because Mode7 is intentionally disabled. Await Build/Validate + Gate C OBJ Diagnostic on this exact SHA. Pass requires compile <=4096, reference still 2→0, Sodium64 control=2 and treatment=0 with verified TMW/WOBJSEL/WH state.

- **2026-09-20 H-OBJ semantic-vs-capacity discriminator — RUNNING:** `phase4/gate-c-obj-window-regular-proof@940876d781551f233de5bc213845b9b4a5ebd3f2`, based on the measured no-Mode7 capacity proof `07f011d2...`. Controlled change applies exactly the previously oversized generic W1 OBJ-window repair from rejected monolithic candidate `9d41bcd...` to the regular/no-Mode7 proof image; no other renderer semantics are changed. **Question:** was `9d41` semantically capable of fixing the validated 2→0 H-OBJ oracle once the independent IMEM-capacity blocker is removed? **Pass:** RSP compiles <=4096 and the exact Gate-C diagnostic changes Sodium64 control/treatment outer probes from 2→0, matching pinned SNES reference -> repair semantics SUPPORTED/VALIDATED within this regular-image proof, while integration architecture remains open. **Fail semantic:** compiles but remains 2→2 -> repair design itself is wrong. **Fail compile:** even ~1 KiB recovered is insufficient -> split partition needs revision. Mode7 is deliberately absent, so this branch is NEVER a merge candidate and provides no Mode7/performance evidence.

- **2026-09-20 Gate-C symmetric RSP-IMEM capacity proof — MEASURED / PASS:** repaired proof `phase4/gate-c-rsp-imem-mode7-proof@80ea5c63eed3fd6337d5637de0e9519b753b88c7`, run `35488563485`, compiles both normal and PROFILE builds with RSP `.text = 3076 bytes` while retaining Mode7 + OBJ and stubbing only regular `draw_bg`. Complementary no-Mode7 proof measured 3080 bytes. Relative to monolithic base 4056 bytes, the two sides recover **980 bytes** and **976 bytes** respectively, leaving ~1020/1016 bytes free in the 4096-byte IMEM. **SUPPORTED INTERPRETATION:** regular-BG and Mode7 render paths are sufficiently symmetric in code footprint that a common-core + mutually exclusive renderer split has meaningful capacity on both sides. Still **NOT VALIDATED**: runtime overlay switching, mixed-BGMODE frames, DMA/synchronization cost, and real-N64 cadence. Both stub branches remain non-merge proof artifacts.

- **2026-09-20 Gate-C raster-descriptor capacity audit — HYPOTHESIS / feasible storage envelope:** current section queues are `0x5000` bytes each and section records are `0x40` bytes. `write_setini` selects V-blank at line 225 (224-line mode) or 240 (overscan path), so an aligned `0x50` / 80-byte section record still holds **256 records**, enough for the ~<=241-record worst-case frame lifecycle (initial state + visible-line splits + final close) without enlarging the existing queues. This exposes **16 bytes/section** that could carry a R4300-precomputed horizontal window descriptor while preserving raw PPU state locally. A promising encoding is <=5 horizontal spans (the partition induced by W1/W2 boundaries), each with compact main/sub layer visibility + color-window policy, moving W1/W2/OR-AND-XOR-XNOR decode out of saturated RSP IMEM. **Not selected/implemented:** exact ABI, endpoint encoding, worst-case section count, and runtime DMA cost still require a dedicated proof. This candidate is complementary to, not evidence for, a renderer overlay split and could later address screen-specific TMW/TSW + W2/color-window semantics. H-SAMPLE still requires preserving semantically distinct per-line state; merely enlarging records does not fix cooldown coalescing.

- **2026-09-20 Symmetric IMEM proof attempt 2 — RUNNING:** `phase4/gate-c-rsp-imem-mode7-proof@80ea5c63eed3fd6337d5637de0e9519b753b88c7`. Only proof-harness change from failed attempt: `get_offsets` and `decode_tile4/16/256` remain as aliases to the same two-instruction disabled-BG stub so retained DMEM jump tables link; no regular BG code was restored. Expected pass remains a measured Mode7/common RSP text in the ~3.1 KiB class. Any semantic/runtime result from this intentionally amputated branch remains invalid; only linker/code-size output is authoritative.

- **2026-09-20 Symmetric IMEM proof attempt 1 — HARNESS/PROOF FALSE NEGATIVE, not architecture evidence:** run `35488482799` for `phase4/gate-c-rsp-imem-mode7-proof@17adf9f1...` failed at RSP link because the controlled source-range excision also removed labels still referenced by static DMEM tables: `decode_tile4`, `decode_tile16`, `decode_tile256`, and `get_offsets`. No IMEM-capacity result was produced and no runtime executed. **REJECTED as evidence about split viability.** Controlled repair: add only alias/stub labels for those table targets at the proof stub so the intentionally disabled regular-BG path remains disabled while the linker can measure the retained Mode7/common image. Do not restore any regular BG implementation and do not change expected interpretation.

- **2026-09-20 Gate-C symmetric IMEM proof — RUNNING:** temporary non-candidate branch `phase4/gate-c-rsp-imem-mode7-proof@17adf9f1f63bfdb168d04ae33ef2cb0125e56f0c`, based on validated diagnostic head `39e3d206...`. Controlled change stubs only regular `draw_bg` while retaining the existing Mode7 + OBJ paths. **Purpose:** measure the complementary IMEM budget for a prospective Mode7-side renderer; branch is intentionally incorrect for ordinary BG rendering and MUST NOT merge. **Pass reading:** RSP text falls into the same ~3.1 KiB class as the no-Mode7 proof -> both sides have roughly ~1 KiB growth room, supporting a common-core + mutually exclusive regular/Mode7 renderer overlay concept. **Fail reading:** Mode7-side image remains near 4 KiB -> overlay split is asymmetric/insufficient and should not be chosen without another partition. No runtime correctness/performance conclusion is permitted from this compile-only experiment.

- **2026-09-20 Gate-C RSP-IMEM capacity proof — MEASURED / PASS:** compile-only branch `phase4/gate-c-rsp-imem-proof@07f011d2fc32c1b777cdee00b972cb6eae8e4993` stubs only `draw_mode7` and is intentionally not a correctness candidate. Build and PROFILE jobs in run `35488385054` both compile successfully with RSP `.text = 3080 bytes` versus **4056 bytes** on validated base `39e3d206...`: **976 bytes of physical IMEM headroom recovered** (1016 bytes free of 4096 total). This validates the capacity premise behind separating the large regular/Mode7 render paths; it does **not** validate a runtime overlay architecture, Mode7 correctness, or performance. The result exceeds the naive H-OBJ candidate's 148-byte deficit by a large margin. **Decision:** stop trying to squeeze Gate-C fidelity into the last 40 bytes of the monolithic microcode as the default strategy. Next architecture proof should test the symmetric side (retain Mode7, stub regular `draw_bg`) to establish that both prospective variants have useful headroom, then design the smallest safe common-core/overlay switch experiment. The stub branch remains REJECTED for merge by construction.

- **2026-09-20 Gate-C RSP split feasibility audit — SUPPORTED INTERPRETATION, not selected architecture:** on validated diagnostic base `39e3d206...`, static instruction-range count is ~239 instructions in `draw_mode7` and ~242 in regular `draw_bg`; both large render paths coexist inside the 4056-byte/4096-byte IMEM image. A split therefore has a plausible ~0.9 KiB class of recoverable capacity per variant/overlay. Existing runtime already uploads a full 4 KiB RSP IMEM image through `rsp_upload` at startup, and `ppu.S:rsp_frame` explicitly waits for SP HALT before preparing/unhalting the next frame, so IMEM DMA/synchronization primitives already exist. **This does NOT prove runtime overlay switching is correct or cheap.** A correct design must preserve OBJ/common compositor code in both modes and handle the SNES-legal case where BGMODE changes between visible sections; a frame-level-only selector cannot be assumed sufficient. Credible future proof direction if the code-capacity experiment passes: fixed common RSP core plus regular-BG/Mode7 overlay slot, loading only when the required renderer changes, with a resident safe DMA trampoline and measured swap cost. Falsifiers: insufficient measured freed IMEM, inability to switch safely without overwriting executing code/state, mixed-mode correctness failure, or measured RSP/DMA cost that destroys cadence. Do not implement this architecture yet; await the compile-only capacity result first.

- **2026-09-20 Gate-C RSP-IMEM architecture proof — RUNNING:** temporary non-candidate branch `phase4/gate-c-rsp-imem-proof@07f011d2fc32c1b777cdee00b972cb6eae8e4993`, based on validated H-OBJ diagnostic head `39e3d206bc2105045ce83ad5633130312de53fa6`. Controlled change removes only the ~239-instruction `draw_mode7` body from RSP microcode and replaces it with a stub that skips the layer. **Purpose is code-capacity measurement only; this branch is intentionally incorrect for Mode 7 and MUST NOT merge.** Baseline RSP text is 4056/4096 bytes; naive H-OBJ repair overflowed by 148 bytes. Question: would a future regular/Mode7 microcode split recover enough physical IMEM to make Gate-C fidelity additions architecturally viable? **Pass reading:** compile succeeds and measured RSP text frees roughly the static ~0.9 KiB expected -> split/overlay becomes a credible architecture candidate requiring runtime-switch cost/correctness proof. **Fail reading:** little/no usable headroom -> reject this direction and favor R4300/section-descriptor offload. Regardless of result, this experiment is not emulator correctness or performance evidence and does not alter H-OBJ/H-SAMPLE/H-COMP status.

- **2026-09-20 Gate-C H-OBJ repair batch 4 — naive RSP repair REJECTED on IMEM size, semantics not yet judged:** exact candidate `phase4/gate-c-obj-window-diagnostic@9d41bcd19809c4b502fc9d3820a8c813f86e9b72` fails both normal and PROFILE builds before runtime. Build run `35487655353` and the Sodium64 semantic job in run `35487655354` fail at RSP link with `.text` / `rom_imem` / `ram_text` overflow **148 bytes**. The immediately prior validated diagnostic head `39e3d206bc2105045ce83ad5633130312de53fa6` builds an RSP text of **4056 / 4096 bytes**, leaving only **40 bytes (10 instructions)** of IMEM headroom. The candidate duplicated W1 span/scissor control into `draw_obj`; it therefore cannot be accepted even if conceptually correct. **Interpretation:** H-OBJ remains a VALIDATED semantic defect, but the first implementation is **REJECTED as an integration architecture**, not falsified semantically. Upstream Hydr8gon master has the same OBJ-window TODO and provides no ready fix. **Next controlled question:** find a code-size-neutral/near-neutral representation before editing again. Favor sharing existing BG window/scissor machinery or moving reusable window-span derivation out of saturated RSP IMEM; do not delete unrelated correctness paths merely to make room and do not weaken H-OBJ semantics. Static acceptance threshold: projected RSP text <=4096 with preserved no-window fast path; runtime validation remains the exact 2→0 OBJ oracle after it compiles.

- **2026-09-20 Gate-C H-OBJ repair batch 3 — IMPLEMENTED candidate, validation pending:** `phase4/gate-c-obj-window-diagnostic@9d41bcd19809c4b502fc9d3820a8c813f86e9b72` changes only `src/rsp_main.S` on top of the validated diagnostic/harness branch. The repair removes the explicit OBJ-window TODO and adds generic W1 clipping to `draw_obj` using the existing `calc_windows` span semantics plus RDP scissor commands. **Performance intent:** when OBJ windows are disabled, the existing single-traversal path remains fast (one extra TMW/TSW enable check); when enabled, the RSP reuses the already-built object list/tile cache and redraws only per visible W1 span under RDP scissor rather than introducing per-pixel RSP masking. Section scissor is restored after windowed OBJ rendering. **Scope boundary:** this controlled repair deliberately follows the renderer's existing combined `TMW|TSW` contract and W1-only `calc_windows`; it does **not** claim to solve screen-specific main/sub masking, W2/OR-AND-XOR-XNOR, H-SAMPLE, H-COMP, or the full SMW iris. Those remain separate Gate-C debts. **Expected validation:** exact diagnostic must change Sodium64 from outer-probe 2→2 to reference 2→0 while the no-window control remains 2 and Build/Validate remains green. If it fails or causes unrelated build/runtime issues, reject or revise before any merge.

- **2026-09-20 Gate-C H-OBJ semantic defect — VALIDATED:** clean run `35487180187 SUCCESS` at `phase4/gate-c-obj-window-diagnostic@39e3d206bc2105045ce83ad5633130312de53fa6`, still based on integrated `master@9441818dd8457a27bbd617a0f32c6d484550661f`; exact original guest SHA256 `b91fdcd4a4ec7c4dce3b49946e054e4847f86bad03f8da56083c6757b13f6f77`. **Reference oracle VALIDATED:** pinned ares Super Famicom `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff` reports `REFERENCE_CONFIRMS_OUTER_OBJ_MASK_2_TO_0`: with the diagnostic's only alternating PPU variable `TMW bit4`, the two outer OBJ probes are visible in the control state and both disappear when OBJ window masking is enabled. Reference artifact `10597802518`, digest `sha256:ffee44acedf0ce8fd0ca3f57c0728a57d2a0f276879a72dd18589d96d1374288`. **Sodium64 defect VALIDATED:** the N64 decision lab (R4300 JIT + required RSP interpreter LAB LIMITATION) synchronized on guest WRAM and rejected blank startup buffers; control captured two outer probes and treatment also captured the same two outer probes, classification `H_OBJ_SUPPORTED_SODIUM64_IGNORES_OBJ_WINDOW`. Treatment state is directly verified: phase=`0x11`, `TMW=0x11`, `WOBJSEL=0x03`, observed WH state `0x000040BF` (= W1 64..191 in this transport representation), `TM=0x11`, `TS=0`; BG1 is correctly clipped to the W1 span while both outer 8×8 OBJ probes remain at x=28..35 and x=236..243. Thus register/state delivery and W1 bounds are functioning for BG while the OBJ draw path fails to apply the requested mask, matching the explicit `rsp_main.S:draw_obj` TODO. Sodium64 evidence artifact `10597981412`, digest `sha256:ceaeeed6c1ef6680a292448871f8b31efe9180cf2fb5badcb678c9ac886989d8`. General Build and Validate for the exact SHA also succeeded. **Decision:** H-OBJ moves from SUPPORTED INTERPRETATION to **VALIDATED semantic defect**. This validates the missing generic OBJ-window behavior, not Iron's full SMW iris symptom; H-SAMPLE and H-COMP remain independent open hypotheses. **Next technical batch:** implement the smallest generic OBJ-window repair in the RSP renderer, reusing existing W1 span/scissor machinery and preserving the windows-disabled fast path; rerun this exact oracle and then measure regression risk before any SMW claim.

- **2026-09-20 Gate-C H-OBJ diagnostic batch 2a — first semantic run produced useful evidence but harness expectation was wrong; NOT YET FINAL:** run `35486639341` on diagnostic branch exposed two **LAB LIMITATION / harness** issues, not emulator conclusions. (1) The original diagnostic's center OBJ uses low priority and sits behind opaque BG1, so the direct-SNES oracle is outer-probe **2→0**, not the initially assumed 3→1; pinned direct ares-SFC capture itself succeeded and showed frames with two outer red probes and frames with zero, while the analyzer incorrectly required 3→1. (2) The first Sodium64 control capture read a cleared startup framebuffer; treatment was nonblank. Treatment nevertheless supplied strong preliminary H-OBJ evidence with verified PPU state: phase=`0x11`, `TMW=0x11`, `WOBJSEL=0x03`, `TM=0x11`, `TS=0`, observed WH state value `0x000040BF`, green W1 span present, and both outer 8×8 OBJ probes still rendered at framebuffer x=28..35 and x=236..243. This is **SUPPORTED INTERPRETATION**, not final VALIDATED H-OBJ, because the paired control capture was blank and the reference job intentionally failed its stale oracle assertion. Harness repaired without changing the guest ROM/SHA: raw-FB classifier now keys on the two outer probes, direct-SNES oracle accepts the observed 2↔0 states, WH assertion matches observed transport representation, and N64 capture rejects all-zero startup buffers until a nonblank frame is obtained within the requested phase. Clean rerun is based on `phase4/gate-c-obj-window-diagnostic@39e3d206bc2105045ce83ad5633130312de53fa6`; exact guest SHA remains `b91fdcd4a4ec7c4dce3b49946e054e4847f86bad03f8da56083c6757b13f6f77`. **Next decision:** only promote H-OBJ to VALIDATED if the clean pinned SNES reference establishes outer 2→0 while Sodium64 shows control outer probes present and treatment outer probes still present with matching state.

- **2026-09-20 Gate-C H-OBJ diagnostic batch 1 — IMPLEMENTED / generator VALIDATED, semantic experiment not yet run:** technical branch `phase4/gate-c-obj-window-diagnostic@22aadc6a6a51df75ea8ffbf6d22a9dc4474291fd`, based on `master@9441818dd8457a27bbd617a0f32c6d484550661f`. Branch diff is diagnostic-only: added `scripts/make_gate_c_obj_window.py`, `scripts/test_gate_c_obj_window.py`, and `.github/workflows/gate-c-obj-window.yml`; **no emulator/core/runtime source changed**. The original 32 KiB LoROM diagnostic contains no commercial assets and isolates one variable: Mode1 BG1+OBJ, W1=[64,191], W12SEL/WOBJSEL=`0x03`, TM=`0x11`, TS/TSW/color-math/HDMA disabled, three opaque OBJ probes at x=16/96/224,y=96, and two 120-frame phases that change only PPU `TMW` from control `0x01` to treatment `0x11`; WRAM `$7E0001` mirrors phase for debugger synchronization. Deterministic ROM SHA256 is `b91fdcd4a4ec7c4dce3b49946e054e4847f86bad03f8da56083c6757b13f6f77`. Dedicated CI run **35486072884 SUCCESS** validates generator/tests/hash and uploads only this original diagnostic. **What this proves:** the discriminator itself is reproducible and asset-safe. **What it does NOT prove:** H-OBJ rendering failure has not yet been executed against a SNES reference or Sodium64, so no semantic result is claimed. **Next technical batch:** run this exact ROM directly in a pinned SNES reference and wrapped through exact branch Sodium64 in the valid N64 lab, synchronize on control/treatment phase, compare raw/cropped probe pixels and verify transported TMW/WOBJSEL/WH state. Support H-OBJ only if reference masks outer OBJ in treatment while Sodium64 preserves them with matching state; otherwise follow the first divergent stage. Do not implement the renderer fix before that result.

- **Independent review of Astra Gate-C audit — ACCEPTED WITH CAUSALITY BOUNDARY:** independently re-read `master@9441818dd8457a27bbd617a0f32c6d484550661f`, Astra's A1–A3 continuity report, and the pinned public SMW/zelda3 source. **VALIDATED source facts:** `rsp_main.S:draw_obj` explicitly says `TODO: implement windows for objects`; BG rendering ORs `TMW|TSW` instead of preserving screen-specific window masks; `calc_windows` explicitly supports only W1 and lacks W2/combine logic; Mode7 explicitly lacks windows; backdrop composition explicitly uses a workaround because proper color math/blending is absent. At Road setting `precision8` the menu maps to MEDIUM and the section cooldown can retain/coalesce changed per-line state, so H-SAMPLE is a real architectural risk. `rom-converter.py` copies the guest ROM verbatim into the wrapped N64 image at offset `0x104000`; any wrapped commercial Z64 must therefore be protected as a commercial-bearing asset. **SUPPORTED external intent:** pinned public SMW source builds the iris via scanline HDMA WH0/WH1 and sets player-iris object/color window mirror to decimal 51 (`0x33`); pinned zelda3 source configures rain/forest overlay TM=`0x16`, TS=`1`, CGWSEL=`0x82`, and alternates CGADSUB `0x32/0x72`, so missing half-add/main-sub semantics is strongly relevant to that family. **Causality boundary:** H-OBJ is the best first isolated discriminator, not yet the demonstrated cause of Iron's exact SMW visual failure; H-SAMPLE may independently affect iris geometry and H-COMP is broader. Accept Astra's proposed two-phase original TMW bit4 diagnostic as the next highest-information batch because it isolates one known semantic omission without commercial assets or HDMA/math confounders. Do not implement an OBJ fix before the diagnostic, and do not infer that passing/fixing H-OBJ closes SMW iris or ALttP. After the diagnostic checkpoint, choose the next test/fix from the first divergence and preserve Gate-B cadence controls.

- **2026-09-20 FINAL Gate-C technical audit — source audit complete, no implementation/experiment:** audited `master@9441818dd8457a27bbd617a0f32c6d484550661f`; **M0/M1/M2 achieved, M3/Gate C active**. Read the appended **Gate-C audit 2026-09-20 batches A1–A3** as one final report. This final entry supersedes the A1/A2 “IN PROGRESS” audit entries immediately below; earlier hardware-pending chronology remains historical.
- **Principal candidate / first discriminator:** **H-OBJ — SUPPORTED INTERPRETATION**: `src/rsp_main.S:draw_obj` explicitly omits OBJ windows; public SMW iris requests inverted W1 for OBJ. Game causality is still **HYPOTHESIS**. Next technical batch: original static two-phase diagnostic with TMW0x01→0x11, TM0x11/TS0, W1[64,191], no HDMA/math; verify section/RSP state and outside OBJ pixel suppression against SNES reference. **Falsifier:** exact audited binary correctly clips those sprites with verified identical state. Do not launch a compositor rewrite in parallel.
- **Other findings / limits:** precision8=MEDIUM can coalesce HDMA line states (**H-SAMPLE**); main/sub flattened passes and backdrop fill do not implement SNES add/sub/half (**H-COMP**); TMW/TSW are ORed, W2/boolean and Mode7 windows omitted, palette/resource epochs incomplete. SMW inspected iris uses W1, so W2 absence alone is **REJECTED** for it. ALttP public rain/forest requests subscreen half-add; common cause with Iron's SMW scene is **UNKNOWN**. No ROM, matched game trace or new timing measurement exists here. Correctness→measure→profile→optimize→recover60/60, preserving frameskip0/APU21/audio enabled/precision8 and Gothicvania/SRS/Nova2 controls.
- **Private-ROM direction — PROPOSED only:** asset-free public CI; separate private trusted controller, reviewed source SHA, private asset store/repo and least-privilege retrieval, ephemeral execution, SHA validation, no caches/raw logs, cleanup before allowlisted derived outputs. `rom-converter.py` embeds guest bytes at0x104000 in .z64: wrappers are private assets too. Existing open-homebrew upload of workload/ must not be reused for commercial assets. Private storage is not automatic copyright permission. A1 commit `9a1b9c262a5e6db052022463e5c2452fea1ab9ae` and A2 `df6dc1fa3bf831a15631322d9782c682a4cdc8f9` were read back exactly and each changes only this file; final batch is this checkpoint. No other repository file/branch, PR, workflow, token or infrastructure was changed.

- **2026-09-20 Gate-C audit / batch A2 persisted — IN PROGRESS:** full R4300→section→RSP→RDP→VI path and candidate/falsifier matrix are recorded below. Public SMW player/title iris uses **W1 indirect HDMA channel7→WH0/WH1**; W2 absence is not its demonstrated cause. Prioritize OBJ-window omission, lost per-line sections and incomplete math as separate hypotheses. Public ALttP rain/forest uses TM0x16/TS1 and CGADSUB0x72/0x32, strongly implicating missing main/sub half-add for that family, but common cause with SMW is **UNKNOWN**. Native ports are register-intent references, not timing oracles. A1 commit `9a1b9c262a5e6db052022463e5c2452fea1ab9ae` read back exactly and changes only this file. Next checkpoint: generic repairs, performance budget, controlled experiment, validation and private-ROM lab threat model.

- **2026-09-20 Gate-C read-only audit / batch A1 persisted — IN PROGRESS:** audited `master@9441818dd8457a27bbd617a0f32c6d484550661f`, starting `continuity@1914269d0279e50787c6a49536fd9d10c08976dd`. M0/M1/M2 achieved; M3/Gate C active. Exact-head Build and Validate 35483428361 and Ares Profile Validation 35483428330 succeeded; no open PRs at inspection. Source inspection finds explicit window-2/combination and OBJ-window omissions, combined TMW/TSW, and a backdrop-only color-window workaround in the RSP→RDP renderer. These are **SUPPORTED INTERPRETATION of implementation gaps**, not a measured explanation of Iron's SMW/ALttP observations. No commercial ROM, new runtime experiment, implementation or workflow change. See “Gate-C audit 2026-09-20 — batch A1” below. Next: verify public SMW iris register use and SNES reference semantics, then save the next batch.

- **Road convergence checkpoint — M2/Gate B closed, M3/Gate C active and canonical docs synchronized:** `master@9441818dd8457a27bbd617a0f32c6d484550661f`. `ROAD_TO_1_0.md` marks M0/M1/M2 achieved and M3/Gate C active; `ROADMAP.md` now also marks Phase 3 / Gate B **ACHIEVED** and Phase 4 / Gate C **ACTIVE**. These master changes are documentation-only; no emulator/runtime source changed. The three Gate-B workloads are regression controls. Immediate Gate-C direction: reproduce and isolate the known **SMW iris/window/color-math** and **ALttP rain/tree layer-compositor** fidelity failures using deterministic/reference evidence before touching performance architecture again. After Gate C, the route remains Gate D / DSP-1-family (including Super Mario Kart), then Super FX / Super FX 2 (including Star Fox and Yoshi's Island), then SA-1.

- **M2 / Gate-B real-N64 corpus performance VALIDATED — both remaining hardware captures are 60/60 × 5:** Iron returned raw 32 KiB SRAM captures from the exact delivered wrapped identities. Nova2 save SHA256 `7892465a939e339e90488609bbdfa4a5977c1f623f753796e71238a2f94bffd9`; SRS save SHA256 `21d5241c820e9c80d0642a381fe289af6fa9ecf6f0cf5e8a27c0951b1abae6af`. Both parse as canonical big-endian complete S64H v1 captures with 2 warmup + 5 measured windows, frameskip `0`, APU clock `21`, audio `4`, precision `8`, and exact frame-budget vectors **[60,60,60,60,60]**. Nova2: 3,583 valid samples; profile = frame/VI wait 51.21%, RSP wait 14.37%, S-CPU 9.46%, APU static 8.71%, PPU 6.92%, DMA 4.30%, APU JIT 3.40%, DSP/audio 1.45%. SRS: 3,582 valid samples; profile = frame/VI wait 38.36%, APU static 26.07%, DSP/audio 13.54%, APU JIT 7.62%, S-CPU 6.56%, PPU 5.81%, DMA 1.84%. Together with Gothicvania's prior real-N64 60/60 ×5, the defined three-workload base-system performance corpus now sustains native cadence on real hardware with no frameskip and full-rate APU. **Nova2 silence in Iron's video is NOT currently a demonstrated Sodium64 audio regression:** the exact pinned upstream `levels/firstlevel.json` used by the route explicitly sets `"Music": null`; its capture still shows APU/DSP execution and audio setting 4. SRS video contains clearly audible signal and its capture shows substantial DSP/audio work. Treat Nova2 audio as workload-design-consistent unless a reference run demonstrates missing expected SFX. **Decision:** M2 / Gate B is achieved for the defined measured corpus; advance active work to M3 / Gate C base-system fidelity and compatibility. First Gate-C targets remain the already-known SMW iris/window-color-math and ALttP rain/tree layer/compositor regressions; do not resume performance optimization absent a new measured blocker.

- **Gate-B real-N64 visual completion OBSERVED / SRAM authority pending:** Iron ran the delivered exact Gate-B hardware ROMs on real N64/SummerCart64 and supplied two videos. `1000140641.mp4` (~23.0 s) is Nova the Squirrel 2 and shows authored gameplay followed by the expected solid-red completion screen; `1000140642.mp4` (~17.3 s) is Space Rescue Squad and likewise shows authored gameplay followed by solid-red completion. This is useful observational evidence that both exact hardware workloads booted, progressed and reached the HW_PROFILE completion path, but **does not establish 60/60 x5** until the corresponding raw 32 KiB SRAM captures are decoded. **OPEN QUESTION / fidelity signal:** Iron reports Nova2 produced no game audio during this hardware run, while SRS did. Treat this separately from Gate-B throughput: do not infer cause yet, and do not discard it if performance passes. Next action remains decoding each SRAM against the exact wrapped identity and matching master-derived ELF/map; then decide Gate B. At this checkpoint the SRAM files were not yet visible in the chat runtime, so no counter/profile claim has been made.

- **Gate-B private ROM handoff VALIDATED / no raw ROM uploaded to GitHub:** temporary delivery branch `phase3/gate-b-hardware-handoff@c16ddbd7ff9b059eae4458fc52e624290117612d`, based on validated hardware-prep head `faf5f0b50a553c721c5c9bf02b1037179a1b94d8`. Handoff run **`35474152074` SUCCESS** rebuilt the exact qualified SRS-v5 and Nova2 guests, hard-checked the canonical wrapped identities, encrypted both wrapped Z64s to an ephemeral local-only certificate, and uploaded only ciphertext in one-day artifact `10593362366`; no Sodium64 core/runtime source changed and no plaintext guest/wrapped ROM bytes were uploaded. The ciphertext was downloaded and decrypted locally for Iron's hardware session. Final delivered identities independently rechecked: SRS `58cc069fd5e78f27cbaf464341cfb2d32c992168356412ff6a482577f6069ffc`; Nova2 `74039aafafd17d17dc7bf6c8bb1084c5fb8e7367eeab766a70c5381cd4f78975`. **Gate-B authority is unchanged:** real-N64 SRAM captures for these two exact identities remain the sole next gate action.

**Read this entry and the final "Independent autonomy, corpus and oracle audit" before older RESUME HERE entries.** The chronology below retains superseded snapshots as evidence.

- **Gate-B hardware prep durability VALIDATED / tooling work STOP:** `phase3/gate-b-hardware-milestone@faf5f0b50a553c721c5c9bf02b1037179a1b94d8`; Hardware Prep run **`35470824053` SUCCESS**, same-head Build/Validate **`35470824138` SUCCESS**. The workflow still self-validates the exact local reconstruction helper before upload, so current-head prep retains the previously proven SRS/Nova2 source/patch/guest/wrapped identity chain and no-ROM-upload boundary. New non-ROM artifact **`10591984283`** `gate-b-hardware-milestone-prep`, digest `sha256:0fcdadd28803eab5344b81d7fb733c48df9bceff142bfefd93b33551d8908d1f`, expires **2026-12-18T21:34:38Z** (~90 days). Branch-vs-`master@ac1ce747...` remains infrastructure-only: `.github/workflows/gate-b-hardware-milestone.yml` plus `scripts/rebuild_gate_b_hardware_roms.py`; no emulator/runtime source difference. **Decision:** stop Gate-B harness/tooling work here. The package is reproducible, locally reconstructable, hash-guarded and durable enough for an unscheduled hardware session. **SOLE NEXT GATE-B ACTION:** on real N64/SummerCart64, reconstruct the two exact wrapped ROMs from artifact `10591984283`, launch each separately from clean state with no input/settings changes, wait for solid red, retrieve each raw 32 KiB SRAM before launching the other workload, preserve wrapped-Z64 + SRAM SHA256, then decode with `scripts/hw_profile_report.py` and the matching ELF/map from the artifact. Both valid `60/60 × 5` captures => M2 / Gate B achieved; any sub-60 or invalid capture => retain that workload as the measured blocker and resume technical work from its exact profile. Do **not** begin Gate-C/core optimization before this real-hardware authority result unless Iron explicitly redirects priority.
- **Gate-B prep-artifact retention extension CANDIDATE:** `phase3/gate-b-hardware-milestone@faf5f0b50a553c721c5c9bf02b1037179a1b94d8`. Only `.github/workflows/gate-b-hardware-milestone.yml` changed: upload retention from 14 to **90 days**. No source, workload, route, hash, settings, runtime, helper semantics or asset boundary changed. **Pass reading:** Hardware Prep + same-head Build/Validate remain green and the resulting non-ROM artifact reports an expiry ~90 days out -> preparation durability VALIDATED. **Fail reading:** treat only as workflow/artifact-retention configuration; revert or choose the repository-supported maximum without touching emulator/workload evidence. After a pass, stop Gate-B tooling work: real-N64 SRS/Nova2 SRAM captures are the sole remaining authority needed for Gate B.
- **Gate-B local hardware-ROM reconstruction path VALIDATED:** `phase3/gate-b-hardware-milestone@8199b4fbb9f3513add9ae31e0416518c2802f103`; Hardware Prep run **`35470478869` SUCCESS**, same-head Build/Validate **`35470478867` SUCCESS** including emulator smoke. The self-validation step rebuilt both public-source workloads from clean pinned clones using the non-ROM prep inputs and reproduced every hard identity: base Sodium64 `8546b5fb7928b0d69d46dc9387bdaf926b2688fffc08579919a8f89f76d3df41`; SRS release `d5bd7b17...`, route patch `b21d55df...`, route guest `2455da2b...`, wrapped `58cc069fd5e78f27cbaf464341cfb2d32c992168356412ff6a482577f6069ffc`; Nova2 normalized base `fc9f9c98...`, deterministic patch `c33a2f6f...`, route patch `8c691e66...`, route guest `4a996af6...`, wrapped `74039aafafd17d17dc7bf6c8bb1084c5fb8e7367eeab766a70c5381cd4f78975`. The helper printed `All pinned hashes matched.` and then CI deleted the reconstructed guest/wrapped bytes before artifact upload, preserving the no-ROM-upload boundary. New non-ROM prep artifact `10592278271`, digest `sha256:e3963f67057cdae5d5873f7012cdee156879428e17533ee95539bed4d0f1a7ae`, currently expires 2026-10-03. Branch-vs-master audit remains clean: only `.github/workflows/gate-b-hardware-milestone.yml` and `scripts/rebuild_gate_b_hardware_roms.py` differ; no emulator/runtime source changed. **Decision:** local reconstruction friction is closed; do not spend more Gate-B time on route/tooling unless hardware exposes a concrete problem. **Next micro-batch:** extend prep-artifact retention beyond 14 days and verify one green rerun. After that, the only unresolved Gate-B action is the real-N64 SRAM session for SRS + Nova2; do not begin Gate-C/core work before that authority result.
- **Gate-B local reconstruction self-validation CANDIDATE:** `phase3/gate-b-hardware-milestone@8199b4fbb9f3513add9ae31e0416518c2802f103`. The existing hardware-prep workflow now triggers on the local rebuild helper as well, records the exact Python 3.8 executable used for Nova2, restores Python 3.12 before exercising SRS through the helper, then runs `scripts/rebuild_gate_b_hardware_roms.py` against the same just-generated non-ROM prep inputs. It hard-checks the already-validated wrapped identities `58cc069fd5e78f27cbaf464341cfb2d32c992168356412ff6a482577f6069ffc` (SRS) and `74039aafafd17d17dc7bf6c8bb1084c5fb8e7367eeab766a70c5381cd4f78975` (Nova2), requires the local rebuild manifest, and deletes the reconstructed guest/wrapped bytes before artifact upload. **Pass reading:** helper reproduces both exact Z64 identities and the normal Build/Validate remains green -> local reconstruction path VALIDATED, with no new emulator evidence. **Fail reading:** classify as helper/environment bug and repair without changing any expected source/patch/ROM/wrapper hash. After a pass, increase non-ROM prep artifact retention from 14 days and rerun once; real-N64 SRAM remains the only Gate-B authority still missing.
- **Gate-B local hardware-ROM reconstruction helper CANDIDATE:** `phase3/gate-b-hardware-milestone@e721258d904dd37619c7ef6cdbdbced2c368fc71`. Added `scripts/rebuild_gate_b_hardware_roms.py`, a host-side Ubuntu/WSL helper only; no Sodium64 core/runtime or guest route change. It consumes the already-validated non-ROM prep artifact, verifies its HW_PROFILE manifest/settings and exact route/build patch hashes, reclones pinned public SRS/Nova2 source + exact submodules, rebuilds the unmodified/reference guest identities, applies the already-qualified patches, rebuilds the exact qualified guest ROMs, wraps them with the artifact's exact HW_PROFILE Sodium64 runtime, and emits `gate-b-srs-v5.z64` / `gate-b-nova2.z64` only if the previously validated wrapped hashes match byte-for-byte. Nova2 retains Python 3.8 + Pillow 7.1.2 + `PYTHONHASHSEED=0` + serial make; SRS retains its current-Python toolchain. **Purpose:** remove manual transcription from the one remaining real-N64 session while preserving the no-ROM-upload asset boundary. **Next immediate check:** validate this exact helper against prep artifact `10591508256` from run `35467296099`; success requires both wrapped hashes `58cc069f...` and `74039aaf...` exactly. Any failure is a helper/environment issue to repair without weakening expected hashes or changing workload/runtime semantics. After helper validation, extend prep artifact retention beyond 14 days so hardware timing is not coupled to artifact expiry.
- **Gate-B aggregated real-N64 milestone package PREP VALIDATED / hardware captures still TODO:** technical candidate `phase3/gate-b-hardware-milestone@fde9c7fbe5b1d7c9619bf9d0a74158554a2c0798`, derived from integrated `master@ac1ce74740d974b70206fcb6ba842e492b5d7272`. Hardware Prep run **`35467296099` SUCCESS** end-to-end: strict HW decoder test; clean `HW_PROFILE=1` Sodium64 build; exact qualified SRS-v5 source/route reproduction; exact qualified Nova2 deterministic source/route reproduction; both wrappers produced with the **same** master-derived HW runtime; manifest/checksums/procedure emitted; non-guest artifact uploaded. Same-head Build/Validate run **`35467296041` SUCCESS** (`build`, `profile-build`, `emulator-smoke`; release update skipped as expected). Artifact **`10591508256`** `gate-b-hardware-milestone-prep`, digest `sha256:f62fdddb1e1accf17428961bc71a31462783de0e84a16dacc7e0f3b9c1ee9d7a`, expires 2026-10-03. Exact identities: base HW Sodium64 Z64 `8546b5fb7928b0d69d46dc9387bdaf926b2688fffc08579919a8f89f76d3df41`; SRS route patch `b21d55df2d5fb949646c9a2124d5c062fa5e7f312264dabb2f354fdc67a27935`, guest ROM `2455da2b775a04b0e07775b39327d98b1de6a26f2da50bb1a8080e6e2ffffc46`, wrapped Z64 `58cc069fd5e78f27cbaf464341cfb2d32c992168356412ff6a482577f6069ffc`; Nova2 normalized base `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`, deterministic-build patch `c33a2f6f2f39ca4328d702dab087dfb98bd1005d83feae897a7ace7b9b0b2e51`, route patch `8c691e664976ccef3f299bb52530a626520a49c60c51a264fca29dce74797b4a`, guest ROM `4a996af6a93e997fdedf8ccd3d26ee4756b3ec12abb06ce023928a2519e20be6`, wrapped Z64 `74039aafafd17d17dc7bf6c8bb1084c5fb8e7367eeab766a70c5381cd4f78975`. Manifest confirms `HW_PROFILE=1`, frameskip `0`, APU `21`, audio `4`, precision `8`; master hardware logic performs **2 warmup + 5 measured 60-VI windows**, saves SRAM, then solid-red freeze. The branch differs from master only by the hardware-milestone workflow; **no Sodium64 core/runtime optimization or semantic change was introduced.** Asset boundary remains intentional: CI verifies exact guest/wrapped bytes but does not upload them because both upstream projects restrict game assets to use within their own games and prior project practice is no guest-ROM artifacts. The two earlier prep failures are fully classified as harness false negatives (SRS accidentally under Python 3.8; Nova2 missing `PYTHONHASHSEED=0`) and are not emulator evidence. **Gate B remains OPEN:** package construction is validated, but SRS and Nova2 still require real-N64 SRAM captures. Immediate next action is one aggregate hardware session using wrapped identities above: clean launch each workload separately, no input/settings changes, wait for solid red, retrieve each raw 32 KiB SRAM before launching the other, preserve save SHA256 + wrapped SHA256, then decode with `scripts/hw_profile_report.py` and matching ELF/map. Both valid `60/60 × 5` captures => M2 / Gate B ACHIEVED; any sub-60/invalid capture => retain that workload as the measured Gate-B blocker and profile it. Do not start Gate-C/core work before this hardware decision.\n- **Gate-B hardware prep attempt `59cdd58c...`: SRS reproduction VALIDATED, Nova2 base-hash harness mismatch isolated:** Hardware Prep **`35467063339` FAILED** after the repaired SRS stage completed successfully; this validates the Python-environment split and reproduces the exact qualified SRS-v5 route under hard source/patch/ROM guards. Failure then occurred in Nova2 immediately after the unmodified deterministic build because the normalized base ROM SHA did not equal expected `fc9f9c...`; route patching/wrapping never ran. Comparison against all three previously validated Nova2 workflows (`build-repro`, `direct-reference`, `matched`) shows they consistently pin **`PYTHONHASHSEED=0`**, which the aggregated workflow omitted. That seed is part of the known reproducible-build environment, not a guest/runtime change. Controlled repair is `phase3/gate-b-hardware-milestone@fde9c7fbe5b1d7c9619bf9d0a74158554a2c0798`: apply `PYTHONHASHSEED=0` **only to the Nova2 rebuild step** so the already-validated SRS environment remains unchanged, and print the computed normalized base hash before enforcing the same expected hash. No expected hash is weakened or updated. **Expected:** Nova2 returns to `fc9f9c...`, then exact route patch `8c691e66...` and route ROM `4a996af6...`; any different value remains a harness/reproducibility issue to investigate, not Sodium64 evidence.\n- **Gate-B hardware prep attempt `3b908b36...` = HARNESS-ONLY FALSE NEGATIVE / Python environment split repaired:** Hardware Prep **`35466854831` FAILED** only in the SRS source rebuild; same-head Build/Validate **`35466854792` SUCCESS** including normal build, PROFILE build and emulator smoke, and the workflow had already passed decoder validation plus clean `HW_PROFILE=1` compilation. Failure occurred in upstream SRS `tools/gen-movement-table.py` at `values: list[TableValue]` with `TypeError: type object is not subscriptable`: the combined workflow selected **Python 3.8 for Nova2 before building SRS**, while SRS tooling requires Python >=3.9 syntax. No SRS benchmark patch, guest execution, Nova2 build, wrapper, or Sodium64 hardware execution occurred. **REJECTED as Sodium64/SRS evidence.** Controlled repair is `phase3/gate-b-hardware-milestone@59cdd58cf8d41d54874e7ac951cc44ac7e9cbacf`: build SRS first with the runner current Python, then select Python 3.8 and Pillow 7.1.2 only for the already-qualified Nova2 deterministic build. No runtime/core, route logic, hard hash, settings or asset-boundary change. Await exact same-head CI; if SRS then reaches its patch/ROM hash guards, this specific harness explanation is validated.\n- **Gate-B hardware prep candidate corrected / prior head SUPERSEDED before guest execution:** current technical head is `phase3/gate-b-hardware-milestone@3b908b36e46f54515766dfbb6f945e2f8cbeaac9`; new Hardware Prep run **`35466854831` PENDING** and same-head Build/Validate **`35466854792` PENDING** at checkpoint. While the previous head `1a1bb4e8...` was still compiling the common HW runtime, source review caught that the newly transcribed SRS-v5 generator had condensed two **comment-only** lines relative to the already-qualified generator. That would leave guest machine code unchanged but necessarily change the hard textual route-patch SHA, recreating a known provenance false negative. The current head restores those validated comment lines byte-for-byte; no executable route logic, Sodium64 source, settings, workload identity or expected ROM hash changed. **Interpretation:** `1a1bb4e8...` is superseded as package candidate regardless of its eventual CI disposition; do not weaken the patch guard. Current experiment question and pass/fail readings remain those in the hardware-milestone checkpoint below, now against `3b908b36...`.\n- **Gate-B aggregated real-N64 milestone prep IN PROGRESS / checkpoint:** technical branch `phase3/gate-b-hardware-milestone@1a1bb4e8dd2557955bab448888ffe9782871dfe9`, based directly on integrated `master@ac1ce74740d974b70206fcb6ba842e492b5d7272`. New workflow `.github/workflows/gate-b-hardware-milestone.yml`; Gate B Hardware Milestone Prep run **`35466777011` IN PROGRESS**, same-head Build/Validate **`35466776938` IN PROGRESS**. The workflow first validates the existing hardware decoder, builds a clean `HW_PROFILE=1` runtime, then independently rebuilds the exact qualified **SRS v5** route (`guest 2455da2b...`, patch `b21d55df...`) and **Nova2** route (`guest 4a996af6...`, patch `8c691e66...`, deterministic-build patch `c33a2f6f...`) behind hard hash guards, wraps both with the same hardware runtime, and records the resulting wrapped-Z64 hashes plus exact N64 procedure. `HW_PROFILE=1` is already integrated in master and forces Road settings before guest execution (`frameskip 0`, APU `21`, audio `4`, precision `8`), performs exactly **2 complete 60-VI warmup + 5 measured windows**, writes the S64H/S64P payload to 32 KiB SRAM, and freezes on a solid-red completion screen. **Asset boundary preserved:** SRS and Nova2 source trees both restrict game assets to use within their own games; consistent with prior project practice, CI may build and hash guest/wrapped ROMs but does not upload those ROM bytes. Artifact is planned to contain Sodium64 base HW runtime/symbols, route patches, provenance, manifest, checksums and procedure only. **Question:** can one clean master-derived hardware package reproduce both already-qualified guest identities and wrapper builds without importing experimental Sodium64 runtime changes? **Pass reading:** prep workflow + same-head Build/Validate green and hard hashes exact -> package construction VALIDATED; next unresolved action is the private/local delivery/reconstruction path for the two wrapped ROMs followed by one real-N64 SRAM session. **Fail reading:** classify as harness/source-reproduction failure before changing Sodium64 core or guest routes. No Gate-B closure claim until real-N64 captures exist.\n- **Gate-B corpus boundary RECONCILED / four-slot search SUPERSEDED:** the principal autonomous performance corpus is now **Gothicvania + Space Rescue Squad + Nova the Squirrel 2**. All three are qualified workloads and all three reach Road-valid **60/60 × 5 windows** in their strongest completed measurement level: Gothicvania on real N64; SRS and Nova2 in the matched ares decision lab with deterministic qualified gameplay routes and direct-SNES semantic checks. The former fixed “4/4 including an ALttP-like slot” requirement was an operational corpus-diversity heuristic, **not a requirement of `ROAD_TO_1_0.md`**, and is now superseded after Sure Instinct was rejected at the predeclared tooling limit and further top-down-homebrew search showed diminishing gate value. This does **not** declare Gate B achieved: SRS and Nova2 still lack real-N64 performance authority. **Next immediate batch:** prepare one aggregated real-N64 milestone package for SRS + Nova2 using the existing `HW_PROFILE=1`/SRAM authority path where practical, preserving their exact qualified guest identities/routes and Road-valid settings (`frameskip 0`, APU `21`, audio `4`, precision `8`). If both sustain native cadence with valid captures, close M2 / Gate B and move to Gate C fidelity regressions (including SMW iris/window-color-math and ALttP rain/tree layer-compositor behavior). If either fails, keep it in the corpus and treat its measured blocker as the next Gate-B driver. No Sodium64 core optimization is justified before that hardware result.
- **Sure Instinct principal-corpus audition REJECTED at strict one-shim limit:** `phase3/gate-b-sureinstinct-audition@23f6c1d97062d71dff1b6f99be493f1afdefcaf0`; Gate B Sure Instinct Audition **`35465526126` FAILED**, same-head Build/Validate **`35465526092` SUCCESS**. Artifact `10591196169`, digest `sha256:3b5341777bb4f20a4a9595105b442a50772a6d83a27aa6a74686dd82b2a87bc8`. The permitted guarded `ScriptMemorySymbolMap::addEmulatorBreakpoint(SymbolReferencePtr→ReferencePtr)` host-tool shim applied successfully and compilation advanced, but Aoba then hit a **second independent README-pinned FMA API mismatch**: Sure Instinct `ScriptMemoryBlock::write(void *data, uint32_t size) override` does not override pinned FMA `MemoryBlock::write(const void *data, uint32_t size)`. The resulting class remains abstract. Exact upstream source at Sure Instinct `90d70d4...` and FMA `1df2842...` confirms the signature mismatch; this is not a missing package, path, warning-only failure, or Sodium64 issue. **Decision:** honor the predeclared stop condition—do not add another shim, do not resurrect FMA/Aoba further, and do not admit Sure Instinct as a principal autonomous Gate-B corpus workload. Preserve the build-provenance work as rejected knowledge. **Next immediate batch:** reconcile the now-completed Nova2 matched result and current corpus slots, then perform a bounded replacement search for the remaining uncovered role rather than spending more time on Sure Instinct tooling. No Sodium64 core change.
- **Sure Instinct one-shim compatibility audition CANDIDATE:** `phase3/gate-b-sureinstinct-audition@23f6c1d97062d71dff1b6f99be493f1afdefcaf0`. Exact upstream Sure Instinct/FMA pins and GCC12 FMA build remain unchanged. Added exactly one mechanical host-tool compatibility patch: `ScriptMemorySymbolMap::addEmulatorBreakpoint` parameter type changes from `SymbolReferencePtr` to the README-pinned FMA interface `ReferencePtr` in the declaration and matching empty/no-op definition only. Workflow asserts both exact source anchors, permits exactly those two tracked files to differ, stores `sureinstinct-fma-api-compat.patch` + SHA, and at ROM-build completion re-derives the diff and requires the same patch SHA; no other tracked upstream mutation is allowed. **Strict stop condition:** any further independent FMA/Aoba API/source compatibility repair required after this shim causes Sure Instinct to be downgraded/rejected for the principal corpus rather than accumulating patches. **Question:** with the published API drift mechanically bridged, can the existing host toolchain and exact public assets reach a deterministic NTSC ROM?
- **Sure Instinct prefix exposure VALIDATED; upstream release/FMA API drift isolated:** `phase3/gate-b-sureinstinct-audition@92268ddb30d1edc20390f4ed6f2fde88d033a479`, Gate B Sure Instinct Audition **`35465144498` FAILED** later in `aoba-build`; same-head Build/Validate **`35465144503` SUCCESS**. Artifact `10590473522`, digest `sha256:89aea78f7047432f02c0c005fc872ae2c14719d895b26ea91ef66f4436ccd401`. Exact pinned FMA builds/installs under GCC12, Sure Instinct exact source/license passes, private-prefix exposure works: `aoba-libsft`, `libaobaaudio`, the main `libaoba`, and other host code compile past the former missing-FMA-header boundary to ~55%. The new failure is a real upstream source/API mismatch: Sure Instinct `ScriptMemorySymbolMap::addEmulatorBreakpoint` declares/defines `SymbolReferencePtr`, but README-pinned FMA `1df2842d...` requires the override signature `ReferencePtr`; therefore the method does not override and the class remains abstract. Historical audit shows FMA still used `SymbolReferencePtr` in 2021, while the exact README pin is dated 2024-08-10 and Sure Instinct source release 2024-08-12, so the published release and its documented pin are internally inconsistent. The Sure Instinct method body is empty/no-op; changing only this parameter type in its declaration+definition is therefore a mechanical host-build compatibility adaptation, not guest/gameplay logic. **Decision / strict limit:** permit one guarded two-line compatibility patch (`SymbolReferencePtr`→`ReferencePtr` only for this method), record its diff+SHA, and allow no further independent upstream source repairs in this audition. If another substantive FMA/Aoba API drift appears afterward, downgrade/reject Sure Instinct rather than building a patch stack. No Sodium64 core change.
- **Sure Instinct prefix-exposure retry CANDIDATE:** `phase3/gate-b-sureinstinct-audition@92268ddb30d1edc20390f4ed6f2fde88d033a479`. Assertion-only repair over `1065cc65...`: verify installed `<prefix>/lib/liblibfma.so` rather than nonexistent `libfma.so`. All substantive experiment variables remain unchanged: exact FMA/Sure Instinct pins, GCC12 FMA build, no warning suppressions/source edits, and the same private-prefix exposure through `CPATH`, `LIBRARY_PATH`, `LD_LIBRARY_PATH`, `PKG_CONFIG_PATH`, plus FMA bin on PATH. **Question remains:** does Aoba now compile/link against the exact installed FMA interface and progress beyond the previous missing-header boundary?
- **Sure Instinct prefix-exposure attempt 6 — assertion-only BUILD-HARNESS FALSE NEGATIVE:** `phase3/gate-b-sureinstinct-audition@1065cc65fd0848e8f4fddb77a84cd5ee5264900f`, Gate B Sure Instinct Audition **`35464952873` FAILED** before cloning Sure Instinct; same-head Build/Validate remains independent. GCC12 again built and installed exact FMA successfully, including `DynamicBuffer.hpp`. The new harness assertion incorrectly expected `<prefix>/lib/libfma.so`; exact FMA's CMake target is named `libfma`, so GNU library naming installs **`liblibfma.so`** (confirmed in install log), while downstream Aoba's `TARGET_LINK_LIBRARIES(... libfma ...)` correspondingly asks the linker for `-llibfma`. Therefore no FMA/Aoba compatibility result was produced in this run. **Controlled repair:** change only the asserted filename to `liblibfma.so`; retain the same private-prefix environment exposure and all pins/toolchains. The actual question—whether CPATH/LIBRARY_PATH/LD_LIBRARY_PATH lets Aoba consume installed FMA—remains unanswered.
- **Sure Instinct private-FMA-prefix exposure CANDIDATE:** `phase3/gate-b-sureinstinct-audition@1065cc65fd0848e8f4fddb77a84cd5ee5264900f`. Single harness-only repair over `47242db...`: after exact pinned FMA builds/installs under GCC12, assert the installed `DynamicBuffer.hpp` and `libfma.so` exist, then expose that same private prefix to later host builds via `CPATH`, `LIBRARY_PATH`, `LD_LIBRARY_PATH`, and `PKG_CONFIG_PATH` while retaining `<prefix>/bin` on `PATH`. No upstream FMA or Sure Instinct source mutation, no warning suppression, no pin/compiler/procedure change. **Question:** does Aoba now consume the installed FMA interface and progress beyond the prior missing-header boundary? **Acceptance:** `aoba-build` gets past FMA headers/linkage and reaches either successful host-tool build or a genuinely new independent incompatibility. **Falsifier:** same missing FMA header/library despite verified installed files, which would mean the assumed environment exposure is insufficient and requires a narrower build-system diagnosis rather than source patching. Sure Instinct ROM build remains unproven at this checkpoint.
- **Sure Instinct build attempt 5 — GCC12 FMA strategy VALIDATED; private-prefix exposure HYGIENE-BLOCKER:** `phase3/gate-b-sureinstinct-audition@47242db6f61b298c0431d17d02f152eeb7a1603b`, Gate B Sure Instinct Audition **`35462131364` FAILED**, same-head Build/Validate **`35462131199` SUCCESS**. Exact pinned FMA `1df2842d...` configures, compiles and installs successfully under Ubuntu GCC/G++12 with **no warning suppressions or source edits**, closing the GCC13 warning cascade as a toolchain-compatibility issue rather than an FMA semantic defect. Sure Instinct exact source `90d70d4...` then clones/license-checks cleanly; `aoba-libsft` builds 100%. `aoba-build` fails at its first FMA header use: `fatal error: fma/output/DynamicBuffer.hpp: No such file or directory`. Source audit shows that exact FMA does install this header under `<prefix>/include/fma/output/DynamicBuffer.hpp`, while Aoba does not `find_package(FMA)` and directly links names such as `libfma`/`fmamemory`, matching an assumption that FMA is installed on normal compiler/linker search paths. Our CI intentionally installed it into `$RUNNER_TEMP/fma-prefix` but exposed only `<prefix>/bin`, so this is a **BUILD-HARNESS FALSE NEGATIVE / HYGIENE-BLOCKER**, not candidate evidence. Artifact `10588979906`, digest `sha256:a9963b2931c0d2c2c8eeba6975431ec3be1b6bbdce8f9aa733718c18202af4ee`. **Controlled repair:** keep exact FMA/Sure Instinct pins and GCC12 FMA build unchanged; expose the already-installed private prefix to subsequent host builds through compiler include, link and runtime search paths (`CPATH`, `LIBRARY_PATH`, `LD_LIBRARY_PATH`; optionally pkg-config path as provenance hygiene) without patching either upstream tree. If Aoba then reaches a new independent source/compiler incompatibility, classify that separately rather than broadening flags pre-emptively.
- **Sure Instinct build attempt 4 — modern-GCC warning-shim strategy SUPERSEDED:** `phase3/gate-b-sureinstinct-audition@05b67b0a99e0e4af81a4d57854308fe5fce7ec42`, Gate B Sure Instinct Audition **`35462004197` FAILED** still within exact pinned FMA. The narrow `-Wno-error=overloaded-virtual` shim worked and compilation advanced from ~23% to ~40%, but GCC 13 then introduced a second independent fatal warning, `-Werror=dangling-reference`, on legacy `DataBlock.cpp`. Accumulating warning suppressions would become toolchain archaeology and risks hiding real diagnostics. **Decision:** supersede the per-warning-shim approach. Reconstruct a saner historical-compatible compiler environment by building exact FMA with Ubuntu-packaged **GCC/G++ 12** and no added warning suppressions; retain exact FMA SHA and all public dependencies. If GCC12 cannot build FMA without source edits or exposes substantive incompatibilities, downgrade/reject Sure Instinct rather than turning FMA resurrection into a second project. Sure Instinct itself has still not been built; no candidate/runtime conclusion yet.
- **Sure Instinct build attempt 3 — FMA MODERN-COMPILER COMPATIBILITY LIMITATION:** `phase3/gate-b-sureinstinct-audition@16226d400a48cdfbc8ed48c740561b5a0b130f1c`, Gate B Sure Instinct Audition **`35461896690` FAILED** while compiling exact FMA with GCC 13. The controlled `libfl-dev` repair succeeded; FMA config/generation completes and compilation reaches ~23%. Failure is `-Werror=overloaded-virtual` on legacy classes that intentionally expose static `dump(...)` methods alongside a base virtual `dump(string)`. This is a modern warning promoted to error, not a missing symbol or demonstrated assembler semantic defect. Sure Instinct itself remains untouched/not built. **Controlled compatibility shim:** configure exact FMA with only `-Wno-error=overloaded-virtual`; do not patch FMA source and do not suppress all warnings/errors. If further independent warning classes cascade, reassess candidate/toolchain cost rather than accumulating broad flags.
- **Sure Instinct build attempt 2 — BUILD-HARNESS FALSE NEGATIVE:** `phase3/gate-b-sureinstinct-audition@7c79c9fa1d918e26ef039f71628c433512478197`, Gate B Sure Instinct Audition **`35461780591` FAILED** still inside exact pinned FMA configuration. The one-variable Boost repair worked: CMake now finds Boost 1.83 with all requested components plus Bison/Flex/ICU/Zlib/PNG. Generate then fails because `FL_LIBRARY` is NOTFOUND for target `libfma`; Ubuntu separates the Flex runtime development library into `libfl-dev`. Sure Instinct has still not been cloned/built, so this remains pure harness dependency evidence. **Controlled repair:** add only `libfl-dev`; no source changes, pins or procedure changes. If the next run passes FMA, the actual candidate build gate begins.
- **Sure Instinct build attempt 1 — BUILD-HARNESS FALSE NEGATIVE:** `phase3/gate-b-sureinstinct-audition@888cdd27a1bcd66da126ce9211e8de84884f83b8`, Gate B Sure Instinct Audition **`35461705960` FAILED** before cloning/building Sure Instinct. Public dependency install succeeded; exact pinned FMA cloned at `1df2842d...`, then CMake stopped because Boost development components `program_options`, `filesystem`, `locale`, and `thread` were absent. This is a workflow dependency omission, not candidate/runtime evidence and requires no source patch. **Controlled repair:** add Ubuntu `libboost-all-dev` only; keep Sure Instinct pin, FMA pin, compiler, build procedure, no-bsnes boundary and all acceptance criteria unchanged. If FMA then builds, continue to the first actual Sure Instinct build boundary; do not broaden repairs pre-emptively.
- **Sure Instinct source-build audition CANDIDATE:** new branch `phase3/gate-b-sureinstinct-audition@888cdd27a1bcd66da126ce9211e8de84884f83b8`, created directly from integrated `master`. Added only `.github/workflows/gate-b-sureinstinct-audition.yml`; no Sodium64 runtime/core code. The workflow clones exact `BenjaminSchulte/SureInstinct@90d70d4bfbf2921b2f8fee0c652523e2365598a7`, verifies upstream MIT license, builds the exact README-pinned `BenjaminSchulte/fma@1df2842d5746639fe4bb1492dfd20a363fbf6e98`, builds `aoba-libsft` + `aoba-build` with public Ubuntu/Qt5/yaml-cpp/libsamplerate/freetype dependencies, runs the upstream Aoba CLI for the NTSC target, compiles the audio engine and final 65816 ROM, and intentionally stops before upstream `bsnes` launch. It uploads logs/provenance only, **never ROM bytes**. Tracked upstream mutations are forbidden. **Question:** can this complete MIT source release reproduce a non-empty NTSC ROM autonomously from pinned public inputs? **Acceptance:** build reaches a deterministic identity candidate (size+SHA) with clean tracked tree. **Falsifier/classification:** dependency/compiler drift before ROM production is a BUILD/HARNESS issue; required proprietary/local input or source repair substantial enough to become a side project rejects/downgrades the candidate. Even a successful build does not yet lock the ALttP-like slot; meaningful route/representativeness remains a later gate.
- **ALttP-like search / Sure Instinct selected for controlled build audition, not yet a corpus slot:** candidate `BenjaminSchulte/SureInstinct@90d70d4bfbf2921b2f8fee0c652523e2365598a7` is an independently authored complete SNES homebrew with explicit **MIT LICENSE** and full source/assets in-repo. Source audit shows materially more than a single-screen demo: tutorial + three authored stages; scene/stage loading and transitions; a threaded/event-script engine; camera/composer/HDMA/fade infrastructure; dynamic tile changes; pixel/collision and movement logic; item purchase/use, bombs/switches and interactive tiles; multiple sprites/effects; active custom SPC/audio pipeline and streamed samples. Its top-down puzzle design is not literally an RPG, but its area/state/tilemap/interaction/transitions profile is materially closer to the intended ALttP-like architectural slot than `unnamed-snes-engine`. Build lineage is also independent from Gothicvania/SRS/Nova2: FMA macro assembler + Aoba engine/tooling. **Caveat:** upstream README explicitly warns the 2024 source release may be difficult to compile and documents a Linux/Qt5 build with exact FMA pin `1df2842d5746639fe4bb1492dfd20a363fbf6e98`; therefore do not lock it from source inspection alone. **Next controlled gate:** source-build/provenance audition only. Reproduce exact source + exact FMA pin on Ubuntu, compile `aoba-libsft`, `aoba-build` CLI, assets/audio and an NTSC ROM while deliberately omitting the final bsnes launch. Acceptance is a non-empty deterministic ROM from public dependencies with no tracked upstream mutation; build-environment failures are harness evidence, not Sodium64 evidence. If autonomous build succeeds, only then design a deterministic meaningful top-down route and evaluate whether the workload is representative enough for the final slot.
- **ALttP-like candidate recheck / Furry RPG remains ELIGIBILITY BLOCKED:** current public `Ramsis-SNES/furryrpg` state still points to `35b4eb22e665064d5bf679c7984205cc99a4ee57` (2026-08-29), GitHub license metadata remains `null`, and the repository root still has no explicit `LICENSE` file. README prose calls it an “open-source freeware project,” but that does not define redistribution/automation rights for the code/assets with enough precision for a principal autonomous Gate-B dependency. **Technical suitability remains strong** (top-down area/event logic, scrolling, world map/Mode 7, IRQ/NMI work, audio), but eligibility is still an **OPEN QUESTION / BLOCKED**. Do not consume, redistribute, upload, or build it into the principal corpus unless explicit licensing appears. Continue search for an independently authored ALttP-like workload with clear license/provenance rather than lowering the legal/autonomy standard merely to reach 4/4.
- **Nova the Squirrel 2 — LOCKED / GATE-B CORPUS SLOT / SMW-LIKE SCROLLING PLATFORMER:** qualification authority is `phase3/gate-b-nova2-reference@6ca2bf7b9a6454274447f96d7e45441dcf27e102` plus the exact qualified guest route `4a996af6a93e997fdedf8ccd3d26ee4756b3ec12abb06ce023928a2519e20be6`. It earns the principal SMW-like slot because it is independently authored from Gothicvania/SRS; has large scrolling authored levels, collision/object/enemy logic, dynamic per-frame player/camera state, generated tile/map resources, background effects/PPU uploads, SPC700/audio content and a separate Mode-7 path; builds autonomously from pinned public source under the documented normalized build recipe; has a deterministic fixed-cost gameplay route with meaningful cold-boot progression beyond the full matched interval; and reproduces three identical Road-valid matched ares-lab runs at `[60,60,60,60,60]` with phase-aware guest-state agreement inside the direct-SNES `gf→gf+1` envelope at **7/7** boundaries. This does **not** establish real-N64 60 FPS, full-game compatibility, audiovisual fidelity, or broad Gate-B closure. **Current four-workload Gate-B corpus state is now 3/4:** (1) Gothicvania — representative regression/M1 workload; (2) Space Rescue Squad — LOCKED DKC-like/heavy-platformer slot; (3) Nova the Squirrel 2 — LOCKED SMW-like slot; (4) **ALttP-like top-down/scripted-area slot — OPEN**. **Next technical uncertainty:** select and audition that final ALttP-like workload using legal/autonomous source+asset provenance → reproducible build → deterministic meaningful route → direct/reference semantics where possible → matched emulator-lab progression/cadence. Do not optimize Sodium64 from Nova2; do not request hardware until the four-slot autonomous corpus is assembled.
- **Nova2 phase-aware matched rerun VALIDATED; host-lab qualification CLOSED:** exact technical head `phase3/gate-b-nova2-reference@6ca2bf7b9a6454274447f96d7e45441dcf27e102`; Gate B Nova2 Matched **`35460221847` SUCCESS**, same-head Build/Validate **`35460221865` SUCCESS**. Matched artifact `10589748597`, digest `sha256:7cccee511e679e72174c5be32d0b5f10dff2c65e1843428ceabc0559a28ce052`. Qualified guest identity remained exact: normalized base `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`, deterministic build patch `c33a2f6f...`, route patch `8c691e664976ccef3f299bb52530a626520a49c60c51a264fca29dce74797b4a`, route ROM `4a996af6a93e997fdedf8ccd3d26ee4756b3ec12abb06ce023928a2519e20be6`. Three independent matched repeats were identical at all seven guest-state boundaries and all measured vectors were **[60,60,60,60,60]**, each with **3584/3584 valid samples**. Profile was exactly repeatable: S-CPU **11.5%**, APU static **11.4%**, APU JIT **2.7%**, DSP **0.9%**, PPU **5.7%**, DMA/HDMA **4.2%**, VRAM/RSP semaphore wait **0.2%**, VI wait **63.3%**, other ~0.1%. Phase-aware semantic rerun reproduced the audited model exactly: same-frame exact counts `PlayerX 7/7`, `PlayerY 6/7`, `PlayerVY 7/7`, `ScrollX 1/7`, `ScrollY 7/7`, health `7/7`; next-frame `ScrollX 7/7`; and **all six compared fields lie inside the direct-SNES game-frame `gf→gf+1` envelope at 7/7 boundaries**. **VALIDATED interpretation:** the former combined `1/7` exact headline was a measurement-phase false alarm caused by comparing Sodium64 `update_fps` entry against direct-SNES post-render state, not demonstrated gameplay divergence. This exact Nova2 segment is not throughput-bound in the valid ares lab and has large virtual headroom, but ares is not real-N64 FPS authority. **Decision:** no further Nova2 route, comparator, or core tuning. Nova2 is ready for Gate-B corpus-slot consolidation and eventual real-N64 milestone measurement. Next batch should consolidate the versioned corpus contract/slot evidence rather than extend Nova2 tooling.
- **Nova2 phase-aware rerun IN PROGRESS / checkpoint:** exact technical head `phase3/gate-b-nova2-reference@6ca2bf7b9a6454274447f96d7e45441dcf27e102`. Same-head **Build and Validate `35460221865` SUCCESS**, including emulator smoke; no general regression from the analysis-only change. Gate B Nova2 Matched **`35460221847` remains IN PROGRESS** at this checkpoint, currently in the pinned ares-N64 valid-lab build path. The experiment changes only the host-side semantic summarizer; qualified guest patch/ROM hashes, Sodium64 runtime/core, Road settings, 2+5 exact 60-VI contract and three-repeat design are unchanged. **Question:** does the rerun reproduce the prior deterministic [60,60,60,60,60] vectors and confirm the audited phase pattern formally? **Expected reading:** same-frame exact counts PlayerX=7/7, PlayerY=6/7, PlayerVY=7/7, ScrollY=7/7, health=7/7, ScrollX=1/7; ScrollX matches direct `gf+1` at all seven because boundary1 is stationary; all six phase fields within direct `gf→gf+1` envelope at 7/7 boundaries. **If reproduced:** close the old 1/7 combined-exact headline as a measurement-phase false alarm, mark Nova2 host-lab qualification closed, and move to corpus-slot consolidation rather than further Nova2 tuning. **If any boundary leaves the one-tick envelope or route/cadence changes:** treat that as new evidence and investigate before corpus promotion. Branch remains diagnostic-only relative to master: compare shows five added harness/workflow files and **no Sodium64 production core change**.
- **Nova2 phase-aware semantic summarizer CANDIDATE:** `phase3/gate-b-nova2-reference@6ca2bf7b9a6454274447f96d7e45441dcf27e102`. Harness-analysis-only change: no qualified Nova2 guest bytes, Sodium64 runtime/core, settings, or matched-window measurement contract changed. The matched workflow no longer headlines a combined all-fields-exact `1/7` score that conflates two observer phases. It now reports per-field exact agreement with direct `gf`, per-field exact agreement with direct `gf+1`, and a one-game-tick **same→next phase envelope** for `PlayerX`, `PlayerY`, `PlayerVY`, `ScrollX`, `ScrollY`, and health. It records whether all six fields lie inside that envelope at each of the seven boundaries; no semantic mismatch is converted into CI failure because divergence remains evidence to interpret, not something to hide. **Expected from the already audited run:** PlayerX/PlayerVY/ScrollY/health same-frame 7/7, PlayerY same-frame 6/7 with jump-boundary intermediate value, ScrollX same-frame 1/7 and next-frame 7/7, all six fields within `gf→gf+1` at 7/7 boundaries. **Falsifier:** rerun changes route/cadence/state despite no guest/runtime change, or any boundary falls outside the one-tick direct phase envelope. Same exact route hashes and 60/60x5 repeatability remain required. No core change; ares remains lab-only performance evidence.
- **Nova2 matched Sodium64 ares characterization MEASURED; naive 1/7 exact comparator is a phase artifact, not demonstrated gameplay divergence:** `phase3/gate-b-nova2-reference@c5602f07d8f796d5e7930fb247ad3b2409e2cabe`; Gate B Nova2 Matched run **`35459327333` SUCCESS**, same-head Build/Validate **`35459327323` SUCCESS**. Matched artifact `10589243087`, digest `sha256:a603343248aa147f1ce56acb5afb05665370d57c0e0d0815f2c1ccb45620dc8f`. Exact qualified guest provenance passed hard guards: normalized base `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`, deterministic build patch `c33a2f6f...`, route patch `8c691e66...`, route ROM `4a996af6...`. Three independent safe matched repeats were byte-for-byte identical at all seven warmup/measured guest-state boundaries and had identical measured vectors **[60,60,60,60,60]**. Each repeat captured **3584/3584 valid samples**. ares-N64 profile was exactly repeatable: S-CPU 11.5%, APU static 11.4%, APU JIT 2.7%, DSP 0.9%, PPU 5.7%, DMA 4.2%, VRAM/RSP semaphore wait 0.2%, VI wait **63.3%**, other ~0.1%. **MEASURED interpretation:** this exact Nova2 segment is not throughput-bound in the valid ares laboratory and has large virtual headroom; this is NOT real-N64 FPS authority and does not close Gate B. The workflow's initial direct-SNES spatial comparator reported only **1/7 exact combined spatial matches**, but field-level audit shows a consistent intra-frame observation-phase offset rather than a different gameplay path: at all 7 boundaries Sodium64 `PlayerX`, `PlayerVY`, `ScrollY`, and health match direct-SNES at the same game-owned `framecount`; `PlayerY` matches same-frame direct at 6/7 and at jump frame209 lies between direct frame209 and frame210 (`6664` vs `6740→6592`); `ScrollX` is same-frame at boundary1 and exactly direct `framecount+1` at the other six. Every compared scalar lies within the direct frame `gf→gf+1` envelope at all seven boundaries. **SUPPORTED INTERPRETATION:** Sodium64 is sampling WRAM at host `update_fps` entry while the direct tracer samples after a rendered SNES frame, so mixed player/camera update phase makes all-fields-exact comparison too strict. No evidence here justifies a Sodium64 core fix. **Next immediate batch:** repair only the host-side semantic summarizer to report phase-aware field agreement/envelope instead of the misleading 1/7 combined-exact headline, then rerun/validate without changing guest bytes or runtime core. After that, decide whether Nova2 is ready to join the Gate-B milestone corpus for eventual real-N64 measurement.
- **Nova2 matched provenance repair VALIDATED through identity/symbol gate:** `phase3/gate-b-nova2-reference@c5602f07d8f796d5e7930fb247ad3b2409e2cabe`, Gate B Nova2 Matched run **`35459327333`** has passed exact qualified-route rebuild and linked WRAM-symbol resolution. Therefore deterministic build patch `c33a2f6...`, normalized base ROM `fc9f9c...`, qualified textual route patch `8c691e66...` and qualified route ROM `4a996af6...` all match the direct-SNES authority before Sodium64 execution. The prior `d82c1d0...` failure is closed as comment-only provenance hygiene. Run is now in Sodium64 PROFILE/runtime setup; no cadence/semantic result yet at this checkpoint.
- **Nova2 matched provenance-repair CANDIDATE:** `phase3/gate-b-nova2-reference@c5602f07d8f796d5e7930fb247ad3b2409e2cabe`. Single harness-only change over failed `d82c1d0...`: restore the two exact validated `src/main.s` benchmark comment lines around `C_BenchmarkInput`. No generated instructions/table data or emulator/runtime source changes. Expected: normalized base `fc9f9c...`, textual route patch `8c691e66...` and route ROM `4a996af6...` all pass hard identity guards, allowing the matched run to reach Sodium64. Falsifier: any remaining hash mismatch; do not weaken guards.
- **Nova2 matched attempt 1 HARNESS-ONLY FALSE NEGATIVE / HYGIENE-BLOCKER:** candidate `d82c1d0968a8307970d56dd09ec3ac445de15d0b`, Gate B Nova2 Matched run **`35459233493` FAILED** in the exact-route rebuild step before any Sodium64 execution. Normalized base ROM matched `fc9f9c...` and the rebuilt qualified benchmark ROM matched the validated **`4a996af6a93e997fdedf8ccd3d26ee4756b3ec12abb06ce023928a2519e20be6` exactly**, proving guest executable bytes were reproduced. The textual route patch hash was `5dd4548e...` instead of validated `8c691e66...` because the matched workflow shortened two benchmark comment lines in the generated `src/main.s`; comments do not affect ROM bytes, but the hard textual-provenance guard correctly rejected it. No Sodium64/runtime measurement occurred. **Repair:** restore the exact validated comment text in the generated table source so both patch and ROM identity match; do not relax the patch guard. Failed evidence artifact `10589152616`, digest `sha256:39c7156e39c82f501d9d8ce163410c415e8d9d8a71bb7cd88f94bf0f611b0298`. No route/core change justified.
- **Nova2 safe matched Sodium64 CANDIDATE:** `phase3/gate-b-nova2-reference@d82c1d0968a8307970d56dd09ec3ac445de15d0b`. Added `.github/workflows/gate-b-nova2-matched.yml` on top of observer `783bc045...`; no emulator/runtime core file changed. Workflow independently rebuilds pinned Nova2 `94385f...` with the validated normalization and hard-asserts deterministic build patch `c33a2f6...`, normalized base ROM `fc9f9c...`, qualified route patch `8c691e66...` and route ROM `4a996af6...` before Sodium64 runs. It resolves linked Nova2 low-WRAM symbols from `nova-the-squirrel-2.dbg`, observes them through guest virtual `7E:xxxx` byte reads, builds current Sodium64 PROFILE runtime, uses pinned ares N64 with R4300 JIT + forced RSP interpreter, wraps the ROM locally without uploading guest bytes, and runs three repeats using the already validated safe contract: first `cpu_execute` configuration, frameskip0/APU21/audio4/precision8, 2 exact warmup 60-VI windows, then 5 exact measured 60-VI windows with profile snapshot at measured boundary5. It also downloads qualified direct-SNES non-ROM artifact `10589106753` and compares the seven Sodium boundary states against the direct cold-boot trace at the same `framecount` and ±1 guest tick for spatial-phase tolerance. **Questions:** exact-route identity, deterministic route semantics across repeats, direct-SNES semantic agreement, five-window cadence vector and profile distribution. **Interpretation guard:** below-target cadence or semantic divergence is evidence, not CI failure; real N64 remains performance authority. CI pending at this checkpoint.
- **Nova2 safe matched-window observer CANDIDATE:** `phase3/gate-b-nova2-reference@783bc0458277df1ba03ad437360a7bd3c8fac840`. Added harness-only `scripts/gdb_matched_nova2.py`, derived from the already validated SRS safe matched contract rather than a new profiler. It configures Sodium64 at the first `cpu_execute` before guest CPU/APU work, sets frameskip0/APU21/audio4/precision8 and resets the APU JIT lookup/pointer there, warms exactly 2 complete `update_fps` 60-VI windows, resets only the statistical ring at that exact boundary, then captures exactly 5 measured 60-VI windows. Read-only Nova2 guest state is designed to be sampled byte-wise from WRAM virtual bank 7E at each boundary: `framecount`, PlayerX/Y/VY, ScrollX/Y, health, keynew, JumpGracePeriod, PlayerWantsToJump and PlayerOnGround. **Purpose:** align Sodium64 boundary states against the already qualified direct-SNES trace by game-owned `framecount` while preserving the established M1/SRS measurement methodology. No workflow invokes this script yet at this checkpoint; no emulator/runtime core change. **Next batch:** add the exact-route Nova2 matched workflow that rebuilds normalized base + qualified fixed-cost route with hard patch/ROM hashes, resolves linked WRAM symbols, wraps locally, and runs three safe repeats. Falsifier: any need to change guest route bytes or production runtime to make the harness work.
- **Nova2 grace-jump f208 VALIDATED; direct-SNES route now measurement-qualified:** `phase3/gate-b-nova2-reference@0283536386e972bea99620152b406852f1ebfcbf`; direct-SNES run **`35458267948` SUCCESS**, same-head Build/Validate **`35458267933` SUCCESS**. Artifact `10589106753`, digest `sha256:840027b5275108a336f51baccf278510ef954d61b2314ace44ce14968315e3bc`. Canonical normalized base remains `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`; route patch `8c691e664976ccef3f299bb52530a626520a49c60c51a264fca29dce74797b4a`; route ROM `4a996af6a93e997fdedf8ccd3d26ee4756b3ec12abb06ce023928a2519e20be6`. Relative to the f209 observer run, only `.github/workflows/gate-b-nova2-reference.yml` changed; the fixed-cost driver/table structure is retained and the controlled route data advances the release/fresh-B handoff by one frame (B release f207; 16-frame targeted hold f208-223). **MEASURED mechanism:** cold boot f208 has `keynew=32768`, `jump_grace=1`, `wants_jump=3`; by f209 `PlayerVY=-76`, proving the grace jump fired. The resulting first cold-boot attempt remains continuous through game frame **639**, reaches max `PlayerX=20184`, and therefore exceeds the previously required ~420 progressing game-frame contract (2 warmup + 5x60 measured windows) without a checkpoint reset inside that clean interval. At f240 it lands on the authored next platform (`PlayerPY=6144`, `on_ground=1`), later periodic inputs continue normal progression; route behavior is no longer the limiting uncertainty. **VALIDATED decision:** stop route tuning. Nova2 firstlevel now has a clean direct-SNES reference segment long enough for matched-window qualification. **Next immediate batch:** build the exact-route Sodium64 matched harness using this ROM provenance and the established Road-valid settings/window contract; compare progression/cadence on the exact SHA/artifact before making any core-performance claim. Real N64 remains final performance authority. No Sodium64 core change yet.
- **Nova2 grace-jump edge f208 CANDIDATE:** `phase3/gate-b-nova2-reference@0283536386e972bea99620152b406852f1ebfcbf`. Controlled route-data change relative to the validated f209-mechanism run: keep the fixed-cost 512-word driver/table contract, firstlevel entry, periodic B, targeted 166-181 hold, and validated Right release 199-201; only advance the post-Pier release/edge pattern by one game frame. Table frame207 explicitly clears B, then frames208-223 hold B for the same 16-frame targeted duration. This preserves a full release frame while creating the fresh `KEY_B` edge at f208, when the prior trace measured `JumpGracePeriod=1` after player update. **Source-backed expectation:** f208 begins with grace=2, countdown leaves 1, fresh `keynew` sets `PlayerWantsToJump=3`, and `OfferJumpFromGracePeriod` should set `PlayerVY=-$50`; the observed trajectory should turn upward on the next position update and cold-boot progression should move beyond the frame235/X7994 endpoint. **Acceptance:** same benchmark structure/provenance discipline, negative `PlayerVY` attributable to the f208 edge, upward Y reversal, and improved cold-boot survival/progression. **Falsifier:** no jump state, any pre-edge route regression beyond the intentional B release at f207, or no improvement in cold endpoint. No Sodium64 core change; matched profiling remains deferred.
- **Nova2 f209 missing-jump mechanism VALIDATED / observer batch closed:** `phase3/gate-b-nova2-reference@f252f089613124f0ab852b3edf10c7181e82bbb1`; direct-SNES run **`35457997362` SUCCESS**, same-head Build/Validate **`35457997373` SUCCESS**. Artifact `10589210777`, digest `sha256:a978c7e646a63846fc6a669cc2a0d79df199f8b74192362aed9d703e95e46925`. Build provenance is unchanged from `74ceb6e...`: normalized base ROM `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`, route patch `fe3c44cd1e9777c7dc1d4281fa886ccabff5bd33df3d958bb88225ca594c7387`, route ROM `04e4a989fc517e0e7297e5f41d4164de5f9011c69b423672ac5226a5f0c28901`. Linked observer symbols resolve in low WRAM and the trace remains read-only. **MEASURED cold-boot mechanism:** f202 lands (`PlayerPY=6656`, `PlayerVY=0`, `on_ground=1`); f203 remains grounded with `jump_grace=6`; then grace counts down f204=5, f205=4, f206=3, f207=2, f208=1. At f209 the B edge is real (`keynew=32768`) and `PlayerWantsToJump` becomes 3, but `JumpGracePeriod` has already been decremented to **0 at RunPlayer entry**, so `OfferJumpFromGracePeriod` cannot fire and `PlayerVY` remains positive. This **rejects** both “missing fresh edge” and “input-driver failure” explanations. The same B209 edge on a post-checkpoint diagnostic attempt arrives with `jump_grace=6` and produces the expected jump (`PlayerVY` becomes negative on the following observed frame), confirming the source path. **Next controlled experiment:** advance the release/fresh-B handoff by exactly one game frame while keeping the fixed-cost driver/table shape and 16-frame targeted hold unchanged: force frame207 to release B, then hold B on frames208-223. Source-backed expectation: at f208 grace is still nonzero after countdown, so the fresh B edge should set `PlayerWantsToJump` and `OfferJumpFromGracePeriod` should set `PlayerVY=-$50`; first route-state effect should be the jump state at/after f208. Falsifier: no negative `PlayerVY` / no upward reversal or route regresses before the new edge. No Sodium64 core change; matched profiling remains deferred.
- **Nova2 second-Pier jump-state observer CANDIDATE:** `phase3/gate-b-nova2-reference@f252f089613124f0ab852b3edf10c7181e82bbb1`. Controlled change is observation-only: the brake+B209 route data and fixed-cost guest input driver are unchanged. The direct-SNES workflow now resolves linked low-WRAM addresses from the build-generated `nova-the-squirrel-2.dbg` instead of source-layout arithmetic and adds read-only capture of `keynew`, `PlayerVY`, `JumpGracePeriod`, `PlayerWantsToJump`, and `PlayerOnGround` alongside the existing semantic state. **Question:** why do table words 209-224 produce no cold-boot jump despite the source-supported grace-jump path? Distinguish three concrete cases at/around f209: no fresh `keynew`, `JumpGracePeriod==0`, or a fresh request/grace state that is suppressed later. **Acceptance:** exact linked symbols resolve below `$2000`, benchmark ROM/route patch provenance remains identical to `74ceb6e...`, trace remains 900 frames/read-only, and the added state makes the missing jump mechanism observable. **Falsifier / repair trigger:** symbol resolution/build failure, ROM/route-data drift, or observer state still insufficient to distinguish the mechanism. No Sodium64 core change; matched profiling remains deferred.
- **Nova2 post-Pier grace-jump at f209 REJECTED for cold boot; unexpected mechanism remains OPEN QUESTION:** `phase3/gate-b-nova2-reference@74ceb6e3b1145557a238a3825e8dc48efe37eb99`; direct-SNES run **`35457078186` SUCCESS**, same-head Build/Validate **`35457078204` SUCCESS**. Base ROM `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`; route patch `fe3c44cd1e9777c7dc1d4281fa886ccabff5bd33df3d958bb88225ca594c7387`; route ROM `04e4a989fc517e0e7297e5f41d4164de5f9011c69b423672ac5226a5f0c28901`; artifact `10587874975`, digest `sha256:57407f8c57ca6161b81f28eee58825a8db59e287d224455aef25cdd7c86205ec`. **Cold-boot authority is byte-for-byte semantically identical to the validated brake route for the entire first attempt**: same second-Pier landing at f202-203, same fall trajectory, same reset/death endpoint around game frame235, same cold max PlayerX7994. Therefore the added B table words 209-224 have no observable effect on the first attempt and the grace-jump hypothesis at f209 is **REJECTED**. The overall 900-frame max PlayerX8142 comes from a post-checkpoint attempt and remains diagnostic only, not route authority. Source still makes the no-effect result non-obvious: `countdown JumpGracePeriod` runs at player-update entry, a fresh B edge sets `PlayerWantsToJump=3`, and `OfferJumpFromGracePeriod` can set `PlayerVY=-$50`; however the current trace does not observe `JumpGracePeriod`, `PlayerWantsToJump`, `keynew`, `PlayerVY`, or `PlayerOnGround`, so do **not** infer the exact failure mechanism yet. **Next immediate batch:** extend the read-only direct-SNES observer with those existing WRAM state variables (no guest writes, no route-data change), rerun the current brake+B209 candidate, and determine whether f209 lacks a fresh edge, grace has already expired, or another player-state condition suppresses the jump. Only after that evidence should the B edge be moved earlier. No Sodium64 core change; matched profiling remains deferred.
- **Nova2 post-Pier grace-jump CANDIDATE:** `phase3/gate-b-nova2-reference@74ceb6e3b1145557a238a3825e8dc48efe37eb99`. Controlled variable relative to validated brake route `186f27c...`: add `KEY_B` only for table frames **209-224**; preserve the fixed-cost driver, 512-word table contract, periodic B, frames166-181 B, and validated Right release 199-201. Source-backed mechanism: the brake route lands on the second Pier at f202-203, where `OfferJump` refreshes `JumpGracePeriod=7`; after stepping off, that countdown should still be nonzero at f209. A fresh B edge at f209 should set `PlayerWantsToJump`, and `OfferJumpFromGracePeriod` should set `PlayerVY=-$50`. **Acceptance:** first semantic divergence at/after f209 with a clear upward Y reversal and cold-boot survival/progression beyond frame235. **Falsifier:** no upward reversal or essentially the same fall/reset endpoint. No other route data, guest code, or Sodium64 core change.
- **Nova2 second-Pier brake window VALIDATED as a cold-boot route improvement:** `phase3/gate-b-nova2-reference@186f27c8907dba09e7acfc9a5b293874f614fec9`; direct-SNES run **`35456756766` SUCCESS**, same-head Build/Validate **`35456756797` SUCCESS**. Base ROM `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`; route patch `36c501f028b9b8a1a21f9c7993b8cd9722d6012362f69d6501070b1adfaab130`; route ROM `864e4f9fbdd0b73c998f05bd2d9a9fad3113b9d30a0dbea5f8b0266e3d8f10a5`; artifact `10588740140`, digest `sha256:8eb67bda13b9fefb237865ac1984e7da13d2bfef7a74cde0ab3986c2f8e5d749`. First semantic divergence from fixed-cost v2 is exactly the intended frame199 X change. Measured X follows the physics prediction: baseline/candidate frame199 `6896→6892`, f200 `6928→6916`, f201 `6960→6936`, f202 `6992→6958` (−34). At frame202 the candidate's PlayerPY **snaps to 6656** instead of falling through at 6696, and remains 6656 at frame203: the intended X24-26 Pier landing is therefore **VALIDATED**. Cold boot now survives to game frame **235** with max PlayerX **7994**, versus frame225/X7728 for fixed-cost v2. It then runs off and falls because B remains continuously held from the periodic 192-207 window and no fresh jump edge occurs at the landing. **Next controlled hypothesis:** add only the previously tested B table words 209-224 on top of this validated brake route. Source-backed expectation: ground contact around f202-203 refreshes `JumpGracePeriod=7`; after leaving the edge, the countdown should still be nonzero at f209, so a fresh B edge at 209 should set `PlayerWantsToJump` and `OfferJumpFromGracePeriod` should set `PlayerVY=-$50`, turning the formerly ineffective v3 input into a real coyote-time jump. Falsifier: no upward trajectory / same frame235 fall. Keep the 199-201 Right release unchanged and change only B data 209-224.
- **Nova2 second-Pier brake-window CANDIDATE:** `phase3/gate-b-nova2-reference@186f27c8907dba09e7acfc9a5b293874f614fec9`. Controlled variable relative to validated fixed-cost v2 `47a3bc8...`: table words for game frames **199-201** release `KEY_RIGHT`; all B data and all other controller words remain unchanged, and the executed fixed-cost driver/table size remain identical. Physics-backed expectation: starting from full +32 horizontal speed, three no-Right frames decelerate 32→28→24→20; when Right resumes at frame202 speed should recover to ~22, leaving PlayerPX about **34 position units left** of baseline. Baseline frame202 had PlayerPX6992, PlayerPY6696 and missed the X24-26 Pier because the left foot was ~16 units beyond its right edge. Expected candidate frame202 PlayerPX≈6958 so the left foot should overlap the Pier and ground collision should snap PlayerPY near **6656** rather than continue falling. **Acceptance:** clear landing signature / endpoint change. **Falsifier:** continued monotonic fall to the same frame225 reset. Do not add a fresh B edge yet; if the landing is proven, the next batch will test the jump independently. No Sodium64 core change or profiling.
- **Nova2 fixed-cost/table-driven input isolation VALIDATED:** fixed-cost v2 control `phase3/gate-b-nova2-reference@47a3bc8642a5f30ec6d0a102a50b74565fb1e7ec`; direct-SNES run **`35456437487` SUCCESS**, same-head Build/Validate **`35456437385` SUCCESS**. Base ROM remained `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`; v2 patch `a692a61770e5a204503f3917dc84f5a821b3bb076a047c2470b9ba98b61a554e`; v2 ROM `eacef0dde5bd84a28cf15caffd87b0fcd18f3e6901edefd103a0362949e57cc0`; artifact `10588178512`, digest `sha256:6ab24a309b06e9be72d91b4fc822b790f55a01fe2b3d572ce2892d3d9d14fedf`. Compared with fixed-cost v3 artifact `10587789135`: the emitted `nova2-firstlevel-benchmark.patch` files have identical executed driver/source structure and differ only in the table words covering frames **209-224** (`RIGHT` vs `RIGHT|B`; diff metadata aside). Cold-boot semantic traces have **zero differences through frame208 and in fact zero differences for the entire first attempt**, both dying/resetting at game frame225 with max PlayerX7728. **VALIDATED interpretation:** schedule data can now change without altering pre-change guest timing; the earlier conditional-injection contamination is removed. The frame209 B hold is additionally **REJECTED as a cold-boot control input** because changing those words causes no observable semantic effect before death. **Next route hypothesis from cold trace + player physics:** at frame201 PlayerPX=6960 / PlayerPY=6632; at frame202 gravity crosses the Pier top (PlayerPY=6696) but the left foot is already just beyond the X24-26 Pier by ~16 position units, so Nova misses the landing by a very small horizontal margin. Test one controlled change first: remove RIGHT for a short 3-frame window 199-201 while leaving B schedule unchanged. Player horizontal deceleration is 4 units/frame, so the expected frame202 X shift is ~34 units left—enough to put the left foot back over the Pier when Y crosses its top. Acceptance: PlayerPY snaps to the Pier top (~6656) / trajectory shows a real landing and cold endpoint changes; falsifier: still falls through with essentially the same frame225 endpoint. Do not add a fresh B edge in the same experiment; if landing is proven, test the subsequent jump separately.
- **Nova2 fixed-cost v2 control CANDIDATE:** `phase3/gate-b-nova2-reference@47a3bc8642a5f30ec6d0a102a50b74565fb1e7ec`. Controlled variable relative to fixed-cost v3 baseline `1c828b3...`: remove only the B-active table data for game frames **209-224**; retain the same fixed-cost driver, same 512-word/1024-byte `C_BenchmarkInput` segment contract, same firstlevel entry, Right, periodic B, and frames166-181 hold. Workflow comments/route metadata change, but the generated guest benchmark source is expected to differ only in those table words. **Acceptance test:** direct-SNES cold-boot semantic rows must be identical through frame208; the first possible semantic divergence is frame209 or later. Also compare the two emitted `nova2-firstlevel-benchmark.patch` artifacts to verify no executed driver/instruction change slipped in. **Falsifier:** any guest-source difference outside table data or any semantic divergence before frame209. No Sodium64 core change; matched profiling remains deferred.
- **Nova2 fixed-cost v3 baseline VALIDATED as runnable harness, not yet schedule-isolation proof:** `phase3/gate-b-nova2-reference@1c828b349e21826e786f52396d997dacee5926d5`; direct-SNES run **`35456136093` SUCCESS**, same-head Build/Validate **`35456136004` SUCCESS**. Normalized base remained `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`; fixed-cost v3 patch `a39793a17906cb8c9b02ad922cc09701466ee6368b5fb00ad5a9b7bafb14d1f2`; ROM `d74b91de061528f6030dad5a7833813248e048e5dbdf562ce3c413f4c5b6378b`; artifact `10587789135`, digest `sha256:3d9bc997e68760f351d375d70cd49532e18d9c7dde2b339387fe13dd5457c1de`. The 1024-byte auto-packed input table compiles and executes correctly. Cold-boot authority remains game frame **225**, max PlayerX **7728**; post-checkpoint attempts again reach farther and remain diagnostic only. Comparing the entire cold-boot semantic trace against the old conditional v3 harness shows first divergence already at game frame **69** (`ScrollX` differs while route input data is nominally the same), despite the same eventual cold endpoint. **SUPPORTED INTERPRETATION:** changing the harness implementation changes guest timing, exactly as suspected; therefore old-v3 vs fixed-cost-v3 is not an equivalence oracle. **Next controlled batch:** generate fixed-cost v2 by changing only table words 209-224 from `RIGHT|B` to `RIGHT`, keep driver and 512-word table contract identical, run it, then require fixed-cost v2/v3 traces to be semantically identical before frame209. This comparison is the actual harness-isolation proof.
- **Nova2 fixed-cost route harness CANDIDATE / IMPLEMENTED:** `phase3/gate-b-nova2-reference@1c828b349e21826e786f52396d997dacee5926d5`. Replaced the accumulating per-frame route `cmp/bcc` chain with one constant executed sequence: preserve X, read `framecount`, mask to 0..511, convert to a word index, load one 16-bit controller word via long-indexed ROM access, restore X, and store `keydown`. A dedicated auto-packed `C_BenchmarkInput` segment holds exactly 512 controller words (1024 bytes); current data re-encodes Right + periodic B + the prior 166-181 and 209-224 holds. **Design intent:** future route variants must keep the driver code and table size/layout contract fixed and change only table words, eliminating the earlier pre-input cycle-shape contamination. The table repeats modulo 512, comfortably beyond the ~420-frame clean qualification threshold. **Question:** does this compile/run cleanly, and can two schedules using this identical driver remain semantically identical until the first table word intentionally changed? **Falsifier:** build/layout failure, trace divergence before the intended changed frame, or any need to change executed driver structure between route schedules. CI result pending at this checkpoint; no Sodium64 core change and no matched profiling yet.
- **PPU fidelity debt / concrete Gate-B visual cases AUDITED:** current `master` still contains deliberate SNES compositor approximations in `src/rsp_main.S`. The renderer draws layers in a fixed order that only *mimics* SNES priority and explicitly notes it is not fully accurate; it builds a main/sub layer mask with shared layers forced on top as a workaround for missing blending; BG window handling ORs `TMW|TSW` with a TODO to do better; `calc_windows` supports only window 1 and explicitly lacks window 2 + combine logic; OBJ windows and Mode-7 windows are unimplemented; backdrop/window handling says it exists so effects such as **SMW transitions** work but color math itself remains TODO/incomplete. Upstream issue `Hydr8gon/sodium64#20` independently reports the exact **A Link to the Past** symptom Iron remembers: intro rain/night effect rendered on the wrong layer, behind sprites/trees. **SUPPORTED INTERPRETATION:** these visual errors have not been fixed by the M1/APU work or current Gate-B Nova2 route work. SMW's circular reveal is strongly implicated in the incomplete window/color-math path; ALTTP rain is strongly implicated in the approximate priority/main-sub compositor, but the exact per-register cause is not yet isolated and should not be claimed without a targeted trace. **Decision:** retain SMW title circular reveal and ALTTP intro rain/tree ordering as named fidelity regression targets for the base-system corpus / Phase-4 PPU convergence. Do not interrupt the current Nova2 route-harness batch unless one of these becomes the measured Gate-B blocker.
- **Nova2 route-v3 RESULT / cold-boot route improvement REJECTED; post-checkpoint progress is not benchmark-authoritative:** `phase3/gate-b-nova2-reference@3c023963cbd26891968d0ab1953ae3e3d5cb2d0a`; direct-SNES run **`35454434732` SUCCESS**, same-head Build/Validate **`35454434695` SUCCESS**. Provenance remained normalized: base ROM `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`, determinism patch `c33a2f6f2f39ca4328d702dab087dfb98bd1005d83feae897a7ace7b9b0b2e51`; route-v3 patch `4a2345181b42c7818719a841f351634f75359f916f2f16e5bff74b58b1fb7cee`; route-v3 ROM `aabc36254e69250ce09c93b10cbf18560bc1e65aa6e570ba67a64eb164144210`. Artifact `10588500317`, digest `sha256:8c5febf2ea9d6aea336f812cb0f176cb8e7fe2a85d9d01d27f4957fd9b9d0276`. The added frame209-224 B edge works on a post-checkpoint attempt: it launches at frame209, reaches an apex near X tile29.8 / Y tile23.0, then collides/clamps near X≈8142 (tile31.8) against the authored solid wall at X32 and that attempt dies around game frame270. However the **cold-boot first attempt remains max X=7728 and dies/resets at game frame225, the same endpoint as route-v2 cold boot**, so v3 is **REJECTED as a cold-boot route improvement**. Do not use the longer post-checkpoint attempt to qualify the benchmark.
- **Nova2 checkpoint-repeatability assumption REJECTED / source cause VALIDATED:** upstream `ResumeLevelFromCheckpoint` restores only `GameStateStart..GameStateEnd` (which at this revision contains inventory state) plus the high bytes `PlayerPX+1` and `PlayerPY+1`; it does **not** restore `keydown`, `keylast`, `keynew`, `PlayerVX`, low/subpixel position bytes, or the broader player physics state. `GameMainLoop` only `stz framecount` on entry before computing `keynew=(~keylast)&keydown`. Therefore attempts after a death inherit input/physics residue from the prior attempt and are not independent repeats of the cold-boot workload. V3 demonstrates this directly: one death occurs at frame225 with B released, so the next attempt gets a fresh initial B edge and reaches frame270/X8142; that death occurs while the periodic B is held (`270 & 63 = 14`), so the following attempt inherits B-held state and loses that initial edge, diverging from frame1. **Decision:** for route qualification, authority is the first cold-boot attempt until a route survives past the clean measurement window; post-checkpoint attempts are diagnostic only.
- **Nova2 route-injection timing LAB LIMITATION discovered:** v2 and v3 cold-boot primary traces first diverge at game frame **130**, long before v3's new frame209 input can fire. The only route-source difference is extra per-frame comparison/branch logic added for the later input window, so changing route logic also changes guest CPU cycles/timing before the nominal input change. This means repeatedly appending `cmp/bcc` blocks is not a clean one-variable input experiment. **Next immediate batch:** replace the accumulating conditional route logic with a **fixed-cost/table-driven deterministic input driver** whose executed code path/cycle shape remains constant while route schedules change only data bytes. Re-encode v2/v3 schedules in that table, verify cold-boot baseline equivalence/stability, then tune the cold-boot route from evidence. Do not add a route-v4 timing tweak before this harness repair. Route remains below the ~420-frame clean threshold; matched Sodium64 profiling remains deferred. No emulator core change.
- **Nova2 route-v3 direct-SNES experiment CANDIDATE:** `phase3/gate-b-nova2-reference@3c023963cbd26891968d0ab1953ae3e3d5cb2d0a`. Controlled variable relative to validated v2 only: retain normalized build provenance, firstlevel entry, Right, periodic B, and targeted frames166-181; add one additional B hold at game frames **209-224** after the verified frame208 release. This creates a fresh `keynew` while Nova is still on/just leaving Pier X24-26. Expected: jump toward Pier X28-30 / the X32 ledge and move endpoint beyond frame241 / PlayerX8028. Falsifier: same endpoint or earlier regression. No Sodium64 core change; do not matched-profile unless route survives/progresses past the ~420-frame clean threshold.
- **Nova2 route-v2 VALIDATED as incremental route improvement, not yet measurement-qualified:** `phase3/gate-b-nova2-reference@b176ecb4fc32afc7722151ec169c6fc2b4b5da27`; direct-SNES run **`35453926408` SUCCESS**, same-head Build/Validate **`35453926520` SUCCESS**. Canonical normalized unmodified ROM `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`; determinism patch `c33a2f6f2f39ca4328d702dab087dfb98bd1005d83feae897a7ace7b9b0b2e51`; route-v2 patch `47eb3650165b9df9d883e7786bd940088e963f0cca4c7339e5fda51f370da639`; route-v2 ROM `819896e5c5dba33eac50fd61a99b92d7d609f8f0dfc8483c51e5c35c04f714a8`. Artifact `10587577349`, digest `sha256:bd959fd5dc9efc0b2b49a9456c3cf7fbc977fe28aaaacafacd643c02be96f6b6`. Across 900 host frames: 3 resets (v1 had 4), max PlayerX **8028** (v1 6940), X span 7260. Attempts 2 and 3 are exactly identical for primary semantic state (`game_frame`, PlayerX/Y, ScrollY, health) and both die/reset at game frame **241**. **SUPPORTED INTERPRETATION:** the targeted B edge at frames166-181 works: Nova lands on Pier X20-22, jumps, reaches/lands on Pier X24-26 around frames202-203, then falls because the periodic B hold began in mid-air at frame192 and is still held through frame207; no fresh `keynew` exists on landing. Frame208 is a clean B release; at frame209 PlayerX≈7004 / tile27.36, PlayerY remains on the Pier at y=26, and falling starts at frame210. **Next controlled route experiment:** preserve all v2 input and add exactly one new 16-frame B hold at frames **209-224**, creating a fresh edge after the frame208 release. Expected: jump from the second Pier toward the X28-30 Pier / X32 ledge and move the endpoint beyond frame241/X8028. Falsifier: same endpoint or earlier regression. Route remains below the ~420-frame clean measurement threshold; do not build the Sodium64 matched harness yet. No core change.
- **Nova2 route-v2 normalized direct-reference CANDIDATE:** `phase3/gate-b-nova2-reference@b176ecb4fc32afc7722151ec169c6fc2b4b5da27`. Controlled build-only change: direct-SNES reference now applies the already validated cross-runner normalization before any gameplay patch (`PYTHONHASHSEED=0`, sorted globs in `levelconvert.py` / `encodepalettes.py` / `encodeportraits.py`, determinism patch SHA-256 `c33a2f6...`, serial `make -j1`) and hard-asserts normalized unmodified ROM SHA-256 `fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`. The route-v2 gameplay patch itself is unchanged: normal firstlevel entry, Right + v1 periodic B, plus only B at frames166-181. The workflow now permits exactly four tracked diffs (three build-only normalization files + `src/main.s`) while preserving a separate `nova2-firstlevel-benchmark.patch` containing only gameplay-source changes. **Question:** with benchmark provenance now deterministic, does route-v2 move the direct-SNES progression/death endpoint beyond v1? No Sodium64 core change.
- **Nova2 cross-runner deterministic build VALIDATED:** `phase3/gate-b-nova2-reference@9e97482c1b9d93590e893d2dc5b6ba5fb274c7a6`; run **`35453412562` SUCCESS**, same-head Build/Validate **`35453412574` SUCCESS**. Three independent Ubuntu runners each used pinned `NovaTheSquirrel2@94385f1812f3b322f939f79a29502a1a3ee6d87f`, Python 3.8/Pillow 7.1.2/cc65/lz4, `PYTHONHASHSEED=0`, serial `make -j1`, plus a build-only determinism patch that sorts build-relevant globs in `tools/levelconvert.py`, `tools/encodepalettes.py`, and `tools/encodeportraits.py`. All 3 produced byte-identical 1 MiB ROM SHA-256 **`fc9f9c984ea840b19847a80357cf5043eb686cc4e2a84a74843e1a451df4b60a`** and identical determinism-patch SHA-256 **`c33a2f6f2f39ca4328d702dab087dfb98bd1005d83feae897a7ace7b9b0b2e51`**. Aggregation job `compare-replicas` passed; proof artifact `10587686407`, digest `sha256:6e86ecb0b2accfed58e7ae635df3e86b82f051358974ab4e710e73e0101aa23e`. **MEASURED interpretation:** the normalized build recipe is reproducible across runners. The previous `ecc61b...` / `a4094d...` hashes remain evidence of the un-normalized upstream build and must not be used as canonical matched provenance. Sorting/PYTHONHASHSEED/build serialization are build-lab normalization only; they do not modify gameplay source. **Next action:** apply this exact normalization before both unmodified and route-patched Nova2 builds in the direct-SNES workflow, then rerun route-v2 without changing its input schedule. Once a route qualifies, mirror the same normalization into the Sodium64 audition/matched workflow so both sides use byte-identical benchmark ROM provenance.
- **Nova2 cross-runner deterministic-build proof IN PROGRESS:** `phase3/gate-b-nova2-reference@9e97482c1b9d93590e893d2dc5b6ba5fb274c7a6`, run **`35453412562`**. Three independent Ubuntu runners each rebuild pinned Nova2 with `PYTHONHASHSEED=0`, serial `make -j1`, and a build-only determinism patch that sorts the build-relevant unsorted globs in `tools/levelconvert.py`, `tools/encodepalettes.py`, and `tools/encodeportraits.py`. A fourth aggregation job will fail unless all three final ROM SHA-256 values and determinism-patch hashes are identical. **Evidence motivating this:** `levelconvert.py` iterates `glob.glob("levels/*.json")` unsorted while level ordering changes generated level-bank layout; encodepalettes/encodeportraits also consume unsorted globs; several generators use Python sets. Same-runner clones can therefore agree while different runners/filesystem directory order diverges. **Question:** does explicit glob ordering + fixed Python hash seed + serial make produce cross-runner byte-identical ROMs? If yes, this becomes canonical Nova2 build provenance; if no, continue generator audit rather than weakening equality.
- **Nova2 route-v2 build-environment isolation CANDIDATE:** `phase3/gate-b-nova2-reference@061e5c5728ae74861622ee06226d9ba02b1d134e`. After serial `-j1` alone still produced `a4094d...` inside the broad reference job while the isolated serial proof produced `ecc61b...` 3/3, the workflow now matches the proof environment during ROM construction: install only build-essential/cc65/git/lz4 + Python 3.8/Pillow 7.1.2, build unmodified + route-v2 ROM serially, then install ccache/cmake/graphics/Qt/ares dependencies **after the ROM bytes and hashes are fixed**. **Question:** does the pre-build environment account for the remaining `a409...` vs `ecc61...` split? Route input itself remains unchanged (only targeted B frames166-181 beyond v1). If unmodified hash still differs, do not weaken the assert; isolate remaining environment/state difference. No core change.
- **Nova2 route-v2 serial-build retry IN PROGRESS:** `phase3/gate-b-nova2-reference@1438ada0cc8f948b941fb461e632d5c2fb6c6e1c`, direct run **`35453092572`**, same-head Build/Validate `35453092649`. Both the unmodified pinned build and incremental route-v2 rebuild now use canonical `make -j1`; unmodified ROM remains hard-asserted to deterministic `ecc61b...`. Route input is unchanged from the earlier v2 candidate: Right + v1 periodic B plus only the targeted frame166-181 B hold. This retry tests route behavior after removing the upstream parallel-build defect; no emulator/core variable changed.
- **Nova2 serial ROM reproducibility VALIDATED / full-tree equality criterion REJECTED as over-strict:** run **`35453000795`** built three independent clean clones of pinned `NovaTheSquirrel2@94385f...` with `make -j1`. All three produced the **identical 1 MiB ROM SHA-256 `ecc61b2367a9261fe48131a61e5cf787b6409083827556109099a46a637d9b2f`**, with zero tracked-source diffs. The workflow nevertheless reported FAILURE because it additionally required byte-identical manifests of *all* non-git files; those manifests differ at line 5, i.e. some auxiliary/generated/build product differs even though final ROM bytes are identical. For benchmark reproducibility the relevant authority is ROM identity, so the full-tree-equality gate was over-strict and is **REJECTED**. **SUPPORTED INTERPRETATION:** serializing the pinned upstream build is sufficient to make the unmodified ROM deterministic across three independent clones under the tested toolchain. Artifact `10587815685`, digest `sha256:c65bda936af19ea59e048c3a0630a76a39ead06fe7b0733f165a8b13d0d47f25`. **Decision:** use `make -j1` as canonical Nova2 benchmark build procedure in direct-SNES and Sodium64 workflows; keep explicit ROM hash provenance. The parallel `make -j` procedure is a LAB/BUILD HARNESS DEFECT for this upstream revision and must not be used for semantic matching.
- **Nova2 parallel-build race HYPOTHESIS strengthened by source/log evidence:** upstream Makefile has a normal multi-target rule for `hubworld/fg.bin`, `bg.bin`, `metatiles.bin`, `palettes.bin`, and `hubworld.chrsfc` whose single recipe is `python3 tools/hubworld.py`. In the failed parallel v2 build log, `tools/hubworld.py` is visibly invoked **five concurrent times** while those shared outputs are being generated. This provides a concrete mechanism for nondeterministic generated bytes / link image under `make -j$(nproc)`. It is not yet proven to be the *only* race; the serial three-clone experiment `35453000795` is the falsification test. If serial manifests match, treat upstream parallel generation as the build-lab defect and keep Nova2 benchmark builds serial rather than patching upstream game source.
- **Nova2 serial build reproducibility experiment IN PROGRESS:** `phase3/gate-b-nova2-reference@6d2c9a46a1c3e7b8e4a65a42238f779e3e6070f0`, workflow `.github/workflows/gate-b-nova2-build-repro.yml`, run **`35453000795`**. This is intentionally isolated from route/Sodium64 semantics: three independent clean clones of pinned `NovaTheSquirrel2@94385f...`, identical Python 3.8/Pillow 7.1.2/cc65/lz4 environment, each built **serially with `make -j1`**. The run compares all three ROM SHA-256 values and complete non-git tree SHA manifests; it succeeds only if both ROMs and resulting trees are identical. **Question:** does serializing upstream generation eliminate the observed unmodified-ROM nondeterminism? If yes, adopt serial build as canonical Nova2 benchmark provenance in both direct-SNES and Sodium64 audition workflows; if no, diff the manifests to isolate the nondeterministic generator/output before route work resumes. No emulator/core or input change is part of this experiment.
- **Nova2 upstream build nondeterminism DISCOVERED / prior sole-cause reading SUPERSEDED:** route-v2 run `35452851491` on `phase3/gate-b-nova2-reference@d7f015a8719c7254546d977f40e1ab625441e1af` failed **before applying the v2 source patch**. The pinned unmodified `NovaTheSquirrel2@94385f...` parallel build produced ROM SHA-256 **`a4094d6b2ca793d80c0464380255784baca7a1a55d29a5ba590df6eb5e1bc549`**, whereas the audition and exact-route-v1 rerun had both produced `ecc61b2367a9261fe48131a61e5cf787b6409083827556109099a46a637d9b2f`. Therefore the earlier statement that clean-vs-incremental build order *fully caused* the ROM mismatch is **SUPERSEDED**: build order explained one observed mismatch path, but the pinned upstream build itself is not proven deterministic under the current parallel `make -j$(nproc)` procedure. Logs visibly show generated targets such as `hubworld.py` invoked concurrently multiple times, making a build-race hypothesis plausible but not yet proven. **Decision:** stop route-v2 qualification until the public-source build is made reproducible. Next controlled experiment: build the unmodified pinned source serially in independent clean clones/repeats, compare ROM + generated-file hashes, then adopt the deterministic procedure in both direct-SNES and Sodium64 audition workflows. Do not change route timing or emulator core from this failure.
- **Nova2 route qualification criterion for matched Gate-B measurement:** the existing validated matched-window contract uses **2 warmup + 5 measured complete 60-VI windows**, i.e. 420 VI boundaries after guest execution begins. Therefore a deterministic Nova2 route that resets/dies before roughly **420 progressing game frames** is still route-discovery evidence, not yet a clean matched-measurement segment. Prefer a route that survives/progresses beyond this interval before spending CI on matched Sodium64 repeatability. This criterion is measurement hygiene, not a claim that 420 frames proves compatibility.
- **Nova2 route-v2 direct-SNES experiment IN PROGRESS:** `phase3/gate-b-nova2-reference@d7f015a8719c7254546d977f40e1ab625441e1af`; direct run **`35452851491`**, same-head Build/Validate `35452851456`. Controlled variable: retain Right plus the entire route-v1 periodic B pattern, and add only one B hold at game frames **166-181** (`firstlevel-right-periodic-b-plus-f166-v2`) after the validated landing on Pier X20-22. No player/camera/entity state writes. Expected result: bridge toward Pier X24-26 and move max X/death endpoint beyond route-v1's X=6940/frame207; falsifier: same endpoint or earlier regression. The workflow retains the now-validated unmodified-build-then-incremental-patch sequence and asserts v2 hashes differ from route-v1; v2 patch/ROM hashes will be recorded by the run. Added persistent ccache for the pinned SFC ares tracer to accelerate subsequent route-only iterations without changing emulator semantics. No Sodium64 core change.
- **Nova2 route-v1 direct-SNES qualification VALIDATED on exact Sodium64 benchmark ROM:** `phase3/gate-b-nova2-reference@33feaae4d447e295014fcf608974373b43b81bce`, direct-reference run **`35452464735` SUCCESS**; same-head Build/Validate `35452464720` SUCCESS. The reference hard-verified unmodified ROM `ecc61b2367a9261fe48131a61e5cf787b6409083827556109099a46a637d9b2f`, route patch `476d426dff8ccd356f12a7be26809cee396d07b97a3d2dd32b7a5003d3715cf2`, and patched ROM **`cb59431f095c4f02b495b099022cc28a0ee1fe6c84470835754d7f0544d6466e`**, exactly matching the Sodium64 audition. The 900-frame exact-ROM direct trace reproduces the previous reference's semantic trajectory **exactly for `game_frame`, `PlayerPX`, `PlayerPY`, `ScrollY`, and health across all 900 samples**: 4 resets, 882 meaningful rows, max X=6940, X span=6172. Therefore route-v1 is now admissible direct-SNES evidence: it performs substantial authored gameplay progress but reproducibly falls below the level near game frame 207. Per-frame `ScrollX` still has minor transient nondeterminism and should remain secondary. **Decision:** do not matched-profile route-v1 inside Sodium64 as the final representative segment because its repeated checkpoint-death loop is avoidable route quality debt. Next experiment is route-v2 on direct SNES only, changing one input variable: add a 16-frame B hold at game frames **166-181** after the verified landing on Pier X20-22; keep Right and all existing periodic pulses unchanged. Expected result: cross toward Pier X24-26 and move the failure/progress endpoint rightward; falsifier: same fall endpoint or earlier regression. No core change.
- **Nova2 route-v1 death cause VALIDATED / enemy-health explanation REJECTED:** upstream `src/main.s` kills non-vertical levels when `PlayerPY >= (512+32)*16 = 8704`, independently of health. The direct trace reaches `PlayerPY=8784` at the repeated endpoint while health is still **3**, then `ResumeLevelFromCheckpoint` restores the spawn/health. Therefore the repeated reset is a **fall below the level**, not depletion of health or an enemy-combat failure. Combined with the geometry/trajectory audit, this strengthens the timing-only hypothesis: Nova walks off Pier X20-22 and the next B edge at frame 192 is too late to recover. Do not investigate enemy damage as the cause of this route failure again unless new evidence changes the endpoint.
- **Nova2 route-v1 repeatability characterization (previous direct trace) REFINED:** attempts 2-4 each contain 217 host-frame samples and have **identical `game_frame`, `PlayerPX`, `PlayerPY`, `ScrollY`, and health trajectories**, including the same death/reset endpoint. They differ only in two transient `ScrollX` samples (game frames 140 and 142); player/game state is unchanged. Therefore future matched-state assertions should prioritize frame/player/health progression and treat per-frame camera equality as secondary unless a camera discrepancy persists, because exact scroll transients are not fully repeatable even in the direct-SNES lab. The route failure geometry remains repeatable: landing on Pier X20-22 near frame 164, walking off, then B arriving too late at frame 192. This refinement does not change the pending exact-ROM rerun requirement.
- **Nova2 ROM reproducibility CAUSE VALIDATED / direct trace still running:** in rerun `35452464735` on `phase3/gate-b-nova2-reference@33feaae4d447e295014fcf608974373b43b81bce`, the step `Rebuild exact Nova2 firstlevel route from public source` completed **SUCCESS** while containing hard assertions for all three identities: unmodified ROM `ecc61b2367a9261fe48131a61e5cf787b6409083827556109099a46a637d9b2f`, route patch `476d426dff8ccd356f12a7be26809cee396d07b97a3d2dd32b7a5003d3715cf2`, and patched ROM **`cb59431f095c4f02b495b099022cc28a0ee1fe6c84470835754d7f0544d6466e`**, exactly matching the Sodium64 audition. Therefore the prior `caf38d...` mismatch was caused by the reference workflow building the patched source from a clean tree instead of reproducing the audition's unmodified-build-then-incremental-patch sequence. **REJECTED explanation:** source patch mismatch; the patch was identical. **Knowledge:** this upstream build is order-sensitive enough that benchmark provenance must include build sequence, not just source + patch hashes. Current stage: pinned direct-SNES ares tracer is building; semantic capture is still pending. No emulator/core conclusion is drawn until that exact-ROM trace completes.
- **Nova2 route-v1 failure geometry HYPOTHESIS (from previous direct trace, awaiting exact-ROM confirmation):** repeated attempts land on the authored `Pier` spanning tiles X20-22 around game frame 164, then walk off its right edge around frames 176-180. The next periodic B edge begins only at frame 192, by which point PlayerY has already fallen from tile ~27 to ~29 and the jump cannot start; death follows near X tile 27 / game frame 207. If the exact-ROM trace reproduces this, the next route-only experiment should add/shift one B edge to roughly frame 166-170 after landing, then re-qualify on direct SNES before changing Sodium64 matched measurements. This is a route timing hypothesis, not a core bug.
- **Nova2 matched-state address audit COMPLETE / source-verified:** on Sodium64 candidate `aaaca65...`, `src/memory.S` allocates a 128 KiB `wram` backing store and maps SNES banks **`0x7E-0x7F`** to it for both LoROM and HiROM; `read_wmdata` / `write_wmdata` explicitly access `0x7E0000 + wmadd`. Therefore the Nova2 source-derived low-WRAM offsets from the direct reference are valid GDB guest virtual addresses inside Sodium64 by adding the `0x7E0000` bank base: `framecount=0x7E001A`, `ScrollX=0x7E0022`, `ScrollY=0x7E0024`, `PlayerPX=0x7E003E`, `PlayerPY=0x7E0040`, `PlayerHealth=0x7E005B`. This matches the already-used SRS matched-harness method of reading WRAM guest virtual addresses byte-wise. **Meaning:** if the exact-ROM reproducibility rerun passes, a Nova2 matched guest-time observer can read these fields without modifying guest state or guessing host RDRAM locations. This audit does not itself prove runtime state equivalence; it only establishes the address contract.
- **Nova2 direct-reference reproducibility rerun IN PROGRESS:** `phase3/gate-b-nova2-reference@33feaae4d447e295014fcf608974373b43b81bce`; direct-reference run **`35452464735`**, same-head Build/Validate **`35452464720`**. Controlled change only: reference workflow now reproduces the audition's exact source-build order (pinned unmodified ROM first, then identical `src/main.s` patch and incremental rebuild) and hard-asserts unmodified ROM SHA-256 `ecc61b2367a9261fe48131a61e5cf787b6409083827556109099a46a637d9b2f`, patch SHA-256 `476d426dff8ccd356f12a7be26809cee396d07b97a3d2dd32b7a5003d3715cf2`, and patched ROM SHA-256 `cb59431f095c4f02b495b099022cc28a0ee1fe6c84470835754d7f0544d6466e` **before** building/running the direct-SNES tracer. **Question:** was the previous `caf38d...` ROM mismatch caused solely by clean-patched vs incremental-patched build order? If yes, the same-ROM reference becomes admissible; if no, stop and isolate build nondeterminism rather than compare semantics. No controller or Sodium64 core code changed.
- **Nova2 direct-SNES reference RESULT / HASH MISMATCH blocks matched claim:** run **`35449900596` SUCCESS**, branch `phase3/gate-b-nova2-reference@0d146662b4da9c5f75265051e6998dbcac43b1b4`, job `105915122738`, artifact `10586189610` digest `sha256:456f1e9e937b2cff50b09181b96af47107b77e506afc6f23059b04c3d5d3ca31`. The route patch hash **matches** the Sodium64 audition exactly: `476d426dff8ccd356f12a7be26809cee396d07b97a3d2dd32b7a5003d3715cf2`; however the direct-reference ROM hash is **`caf38d4bf9cbe8b37bdce4b05801fba645886585a9c1c815b7b3205b409939ec`**, while the Sodium64 audition used **`cb59431f095c4f02b495b099022cc28a0ee1fe6c84470835754d7f0544d6466e`**. Therefore a matched semantic comparison is **BLOCKED** until the build-sequence difference is removed and ROM identity is exact. This is currently a harness/build-reproducibility issue, not emulator evidence. The direct trace itself is deterministic and informative: after startup, attempts 2-4 are identical, each reaching `PlayerX=6940`, `game_frame=207`, then resetting; health falls from 4 to 3 before the death/reset. Across 900 host frames there are four game-frame resets and five attempts, with the final partial attempt ending at X=1440. Thus Right + periodic B is **not a stalled route**; it makes substantial repeatable authored progress but reliably dies near the same point. **Next controlled batch:** reproduce the Sodium64 audition's exact build order in the direct-reference workflow (unmodified pinned build first, then apply the identical one-file patch and incremental rebuild), assert the rebuilt ROM hash equals `cb59431...` before tracing, and rerun. If identity then matches, treat the repeated death as route evidence and design a timing-only input change; if identity still differs, isolate generated-build nondeterminism before any semantic/core conclusion.
- **LONG EXPERIMENT checkpoint — Nova2 direct-SNES run `35449900596` IN PROGRESS:** branch `phase3/gate-b-nova2-reference@0d146662b4da9c5f75265051e6998dbcac43b1b4`, job `105915122738`. Completed successfully: checkout/dependencies, exact public-source rebuild of the same firstlevel route, and source-derived read-only WRAM offset resolution. Current stage at checkpoint: **building pinned ares SFC with the read-only tracer**; semantic capture has not run yet. Main Sodium64 candidate route identity is ROM SHA-256 **`cb59431f095c4f02b495b099022cc28a0ee1fe6c84470835754d7f0544d6466e`** and patch SHA-256 **`476d426dff8ccd356f12a7be26809cee396d07b97a3d2dd32b7a5003d3715cf2`**; once the reference run finishes, verify its route/ROM hashes match before comparing semantics. **Resume action:** inspect run `35449900596`; if SUCCESS, read `nova2-direct-snes.json` summary and classify sustained progress vs fixed tail/death resets. If harness fails, inspect only the failed observer/build step and repair the reference harness; do not change Sodium64 or controller timing from a tracer failure. If direct route stalls/dies, revise controller timing only and qualify direct-SNES first. If it progresses, next technical batch is matched guest-time Nova2 state sampling inside Sodium64 (canonical WRAM mirror `7E:offset` should be source-verified before use), then repeatability. No core change is justified from the current host-lab success alone.
- **Nova2 firstlevel Sodium64 audition MEASURED / Gate-B host-lab success:** candidate `phase3/gate-b-nova2-audition@aaaca65dbc66d7acae5c9b884eccb5c3cc85d28a`; Gate B run **`35449637373` SUCCESS**, job `105914440962`; same-head Build/Validate `35449637414` SUCCESS. The pinned authored `firstlevel` benchmark built, wrapped, booted and completed the Sodium64 profiling contract at frameskip **0**, APU clock **21**, audio **4**, precision **8**. Measurement captured **1166/1166 valid samples** and the last complete internal VI window was **60/60 = 100% virtual budget**; the partial following window was 37/60 with 38 partial guest frames and queue 2, so do not read the raw `fps_native=37`/`fps_emulate=38` observation as a completed-window FPS result. Profile: **61.84% frame/VI wait**, **12.52% S-CPU interpreter**, **10.55% APU/SPC700 static**, **5.66% PPU/events/frame prep**, **4.37% DMA/HDMA**, **3.34% APU JIT**, **1.20% DSP/audio**, **0.51% RSP/VRAM semaphore wait**. Compared with the earlier Nova2 hubworld control, this fuller level shifts more time into S-CPU/DMA while still retaining substantial VI wait. Artifact **`10585769543`**, digest `sha256:f2243df53e9640c57796e2f69bd1be8e8fe4a6b5783a1af9ea9c88adab4d48da`; source-build proof artifact `10586518587`, digest `sha256:d4e53934b339efa1d993ca5fdec560f43b8503ee8d4de2752282fee15515cbde`. **SUPPORTED INTERPRETATION:** this is materially stronger open-source compatibility/performance evidence than the hubworld audition because normal level load, collision/actors/camera/rendering are in the path and the host lab still meets its internal 60/60 budget. **NOT PROVEN:** real-N64 60 FPS, correctness of every firstlevel semantic, sustained authored route progress, or audio-bearing guest workload; the pinned game revision still has game-audio boot disabled. The parallel direct-SNES trace `phase3/gate-b-nova2-reference@0d146662b4da9c5f75265051e6998dbcac43b1b4` is the next authority for route quality before any controller/core change.
- **Nova2 firstlevel direct-SNES route trace STARTED / MEASUREMENT PROOF:** `phase3/gate-b-nova2-reference@0d146662b4da9c5f75265051e6998dbcac43b1b4`. This branch is split from the active Sodium64 audition so its push cannot cancel `35449637373`. It rebuilds the **same** pinned firstlevel patch/input route, derives `framecount`, `PlayerPX/PY`, `ScrollX/Y` and health WRAM offsets from the pinned linker config + `src/memory.s` layout (no guessed addresses), then patches pinned ares SFC only as a read-only 900-rendered-frame observer. It uses the already-validated `std::_Exit(0)` tracer termination to avoid the known ares teardown LAB HARNESS DEFECT and uploads no ROM bytes. **Question:** does Right + periodic bounded B produce sustained authored gameplay progress on a direct SNES reference, or settle into a geometry/death loop? **Possible readings:** sustained progress => route is a stronger candidate for matched Sodium64 semantics/performance; fixed-position tail => controller route needs timing-only revision before any core conclusion; repeated frame resets/deaths => route needs timing-only revision; tracer/build failure => fix observer/harness only. No Sodium64 core change is part of this branch.
- **Same-head baseline CI VALIDATED for Nova2 firstlevel candidate:** `phase3/gate-b-nova2-audition@aaaca65dbc66d7acae5c9b884eccb5c3cc85d28a`, Build and Validate **`35449637414` SUCCESS**. Normal build, PROFILE build and emulator-smoke all completed green. This preserves the integrated Sodium64 baseline while the dedicated Gate-B Nova2 run `35449637373` continues. It does not add gameplay evidence by itself; it rules out a regression in the repository's standard build/smoke gates at this SHA.
- **Nova2 firstlevel benchmark BUILD-VALIDATED / execution still IN PROGRESS:** exact candidate `phase3/gate-b-nova2-audition@aaaca65dbc66d7acae5c9b884eccb5c3cc85d28a`; Gate B run **`35449637373`**, job `105914440962`. The pinned unmodified Nova2 source build succeeded, then the new one-file `src/main.s` firstlevel benchmark step also **succeeded**, followed by a successful Sodium64 PROFILE build. This closes the immediate construction question: `level_firstlevel` resolves, the exact 24-bit `LevelHeaderPointer` routing through `StartLevel` assembles/links, and the deterministic Right + bounded B input patch is syntactically/build valid. It does **not** yet prove the level boots/progresses through Sodium64 or meets a frame budget; the job is currently in ares-lab setup before wrapped execution. Same-head Build/Validate `35449637414` has normal `build` and `profile-build` jobs green; emulator-smoke is still running. **Interpretation:** no harness/source-build blocker has appeared, so preserve this exact candidate and await its execution result before changing controller timing or emulator core.
- **Nova2 firstlevel gameplay audition IN PROGRESS / CANDIDATE:** `phase3/gate-b-nova2-audition@aaaca65dbc66d7acae5c9b884eccb5c3cc85d28a`. Controlled change from the validated hubworld candidate: the workflow now rebuilds pinned `NovaSquirrel/NovaTheSquirrel2@94385f1812f3b322f939f79a29502a1a3ee6d87f` and patches **only `src/main.s`**. Entry routing sets the exact 24-bit `LevelHeaderPointer` to generated `level_firstlevel` and jumps through upstream `StartLevel`; the normal `DecompressLevel -> AutotileLevel -> UploadLevelGraphics -> MakeCheckpoint -> GameMainLoop` path remains intact. Inside `GameMainLoop`, only physical controller sampling is replaced with deterministic normal input: Right held continuously plus a bounded 16-frame B hold every 64 game frames; player/camera/entity state is not written. Sodium64 runtime, Road settings and ares N64 lab configuration are unchanged. **Question:** does this materially fuller authored level build/boot under Sodium64 and remain within the host-lab frame budget, and can the deterministic route be qualified as real gameplay progression rather than a geometry stall? **Possible readings:** build/boot failure => isolate benchmark/upstream/Sodium64 before optimization; green throughput with route stall => adjust controller timing only, using direct-SNES semantic tracing; green throughput plus qualified direct-SNES progress => promote this as stronger Gate-B compatibility/performance evidence. **No core fix is justified yet.** CI for this exact SHA is the next evidence to inspect.
- **Nova2 fuller gameplay route source audit COMPLETE / next experiment designed:** pinned source `NovaSquirrel/NovaTheSquirrel2@94385f1812f3b322f939f79a29502a1a3ee6d87f` contains normal overworld-connected platforming levels, not just the hubworld. `WorldDemo.tmx` maps slot 1 to **`firstlevel`**; generated level tooling exports **`level_firstlevel`**. `StartLevel` then executes the normal `DecompressLevel -> AutotileLevel -> UploadLevelGraphics -> MakeCheckpoint -> GameMainLoop` path. Exact `levels/firstlevel.json` is a 256x32 authored level with **233 foreground objects**, **23 actor entries**, and a normal `PLAYER_START_R` at tile (3,29); its geometry includes platforms, slopes/springs/spikes/ladders/bridges and other interactive blocks. `GameMainLoop` reads the normal controller state before `RunPlayer`, actor update, collision, camera, rendering and vblank. **Next controlled audition design:** replace the current hubworld benchmark with a one-file `src/main.s` benchmark that points `LevelHeaderPointer` to generated `level_firstlevel`, enters through `StartLevel`, and substitutes only controller input with deterministic normal buttons (Right plus bounded periodic B holds). Do not write player/camera/entity state. First run is route discovery: verify actual progress and whether it stalls on authored geometry; if it does, adjust controller timing only, exactly as with SRS. This materially increases representativeness by exercising level decompression, collision, actors and normal gameplay loop while remaining autonomous/open-source. Audio remains a known coverage limit because this upstream revision compiles its game-audio boot block out. No core change yet.
- **Nova2 hubworld audition MEASURED / useful diversity control, not a new core blocker:** `phase3/gate-b-nova2-audition@7eff4c9e24a3ea2180bba0281c7a16ac8b221f8c`. Gate B run **`35427157957` SUCCESS**, job `105854985883`; same-head Build/Validate **`35427157950` SUCCESS**. Exact Road settings were observed as frameskip0/APU21/audio4/precision8. The clean capture has **945 valid samples** and last complete virtual frame window **59/60 (98.3%)**; profile: VI/frame wait **67.30%**, APU static 11.43%, S-CPU 7.83%, PPU 5.93%, APU JIT 2.86%, DMA/HDMA 1.69%, VRAM/RSP semaphore wait 1.59%, DSP 1.38%. The immediately preceding same benchmark execution at `fd366f6...` reached **60/60** before a Python-3.8-only reporter failure, with essentially the same **67.15% frame_wait** profile shape. **SUPPORTED INTERPRETATION:** the 59↔60 single-window variation from this generic wall-time harness is not evidence of a throughput bottleneck, especially with ~67% observed VI wait; do not optimize Sodium64 from it. This route successfully diversifies Gate-B coverage toward scrolling/PPU/OAM/VRAM-DMA behavior, but it is **not a final representative Nova2 workload** because it free-walks the authored hubworld, lacks collision/enemy gameplay, and the pinned upstream revision has its game-audio boot disabled. Artifact **`10579337285`**, digest `sha256:532f68c8327b399ce7fec47390a3e899ce9bf7a28e2633b7de6499ab5dda5943`; source-build artifact `10578074856`, digest `sha256:f68b814f3651d68d88a9ee5df6c07c09ae101244bebd216e087549149b2d1bb3`. **Next action:** inspect pinned Nova2 source for the smallest deterministic authored level/gameplay route that preserves normal collision/entities and can become the next controlled audition; no Sodium64 core change is justified yet.
- **Nova2 reporting rerun IN PROGRESS:** exact candidate `phase3/gate-b-nova2-audition@7eff4c9e24a3ea2180bba0281c7a16ac8b221f8c`. One controlled workflow-only change from `fd366f6...`: after the pinned Nova2 source + benchmark build completes under required Python 3.8/Pillow 7.1.2, switch to Python 3.12 for Sodium64 host tests/reporters. Benchmark source patch, Sodium64 runtime, Road settings and ares lab configuration are unchanged. Expected result is the same successful execution/capture plus completed profile JSON/category and frame-budget report; any materially different runtime profile/frame observation would require investigation rather than attribution to this host-tool fix.
- **Nova2 first Sodium64 execution MEASURED; run red only after capture due host Python mismatch:** `phase3/gate-b-nova2-audition@fd366f6ff18e1647b2c59d07fac2726c8f9129cf`, Gate B run **`35426859911`**, job `105854222880`. Pinned-source build, deterministic hubworld benchmark build, Sodium64 PROFILE build, pinned ares valid-lab build, ROM wrapping and GDB capture all succeeded. Actual Sodium64 execution produced **1044 valid samples in the first 3 s measured interval**, Road settings observed as frameskip0/APU21/audio4/precision8, and `fps_display=60`; sampled hot symbols begin **frame_wait 67.15%, apu_execute 6.13%, cpu_execute 3.45%, APU JIT 3.26%, cpu_io 2.49%**, consistent with substantial host-lab headroom for this route. The job failed only when `scripts/profile_report.py` reached Python's `zip(..., strict=True)`: the workflow was still using upstream-era Python 3.8 selected for Nova2/Pillow, so reporter raised `TypeError: zip() takes no keyword arguments`. Artifact **`10579262034`**, digest `sha256:f3a9b4bb88ecc2030cfb792a87d167e77d1790058b7455d96de86dc4c861ded2`, contains the capture/state/logs and benchmark provenance; no ROM bytes are uploaded. **SUPPORTED INTERPRETATION:** Nova2 hubworld boots/progresses and is not throughput-bound in this ares host lab; the red conclusion is REJECTED as Sodium64/Nova2 failure. **Next controlled change:** keep exact benchmark/runtime and switch to current Python only after the Nova2 source/benchmark build, then rerun to complete JSON/category/frame-budget reporting before deciding whether this route is merely a diversity control or needs deeper direct-SNES validation.
- **Nova2 hubworld benchmark construction VALIDATED; execution still in progress:** exact candidate `phase3/gate-b-nova2-audition@fd366f6ff18e1647b2c59d07fac2726c8f9129cf`, Gate B run **`35426859911`**. The run has successfully completed pinned-source checkout, palette inspection, the unmodified Nova2 build, provenance upload, and the controlled deterministic hubworld benchmark build; Sodium64 PROFILE build is now running. This proves the two-file route patch is syntactically/build valid and does not require additional upstream-source hacks. It does **not** yet prove Nova2 boots/progresses through Sodium64 or any frame budget. Continue this exact run to the wrapped execution/profile stage before changing the route or core.
- **Nova2 audition hygiene failure REJECTED as emulator evidence:** first candidate `0811f6c78db7451a8237dc49da4fa6302c1617c2` produced Gate B run **`35426802095` FAILURE before any job started**. Cause is the workflow YAML itself: multiline Python string payload lines escaped the YAML block indentation, so GitHub could not parse the workflow. No Nova2 ROM execution occurred; this says nothing about Sodium64. Corrected candidate is now `phase3/gate-b-nova2-audition@fd366f6ff18e1647b2c59d07fac2726c8f9129cf`, replacing those multiline literals with indentation-safe joined strings only. Same benchmark question/scope as the in-progress entry below; await the new exact run before interpretation.
- **Nova2 hubworld audition IN PROGRESS / DISCOVERY:** `phase3/gate-b-nova2-audition@0811f6c78db7451a8237dc49da4fa6302c1617c2`. This is the first execution batch after the already-resolved pinned-source build proof. The workflow now rebuilds pinned Nova2, creates a controlled benchmark by changing only `src/main.s` entry routing (direct to the authored hubworld) and `src/hubworld.s` controller source (continuous normal Right input), then wraps that ROM through Sodium64 and profiles it in the valid ares lab (R4300 JIT + RSP interpreter) at frameskip0/APU21/audio4/precision8. It preserves Nova2 hubworld initialization, player drawing, camera/scrolling, row/column rendering, OAM/VRAM DMA and WaitVblank; it does **not** yet exercise authored collision/enemy gameplay and this pinned Nova2 revision has game audio boot disabled upstream. **Question:** does this independent PPU/DMA/scroll-heavy open-source workload progress under Sodium64 and meet the virtual 60-VI budget, and where does host time concentrate if not? **Possible readings:** green+60 => qualify it as a useful subsystem-diversity control then seek a fuller level route; below-60 => profile distribution becomes a Gate-B lead; crash/stall/build failure => isolate workload/harness/Sodium64 before any core optimization. **No core fix is justified yet.** Await exact CI run/result before advancing.
- **M0/M1 ACHIEVED; M2 / Gate B OPEN.** Integrated master remains `ac1ce74740d974b70206fcb6ba842e492b5d7272`. No M1/APU work is reopened by the current Gate B investigation.
- **SRS safe Sodium64 authority:** `phase3/gate-b-srs-audition@075068af92da1802aa3a2677c3d44f393215cc44`; Gate B SRS Audition `35416459569` SUCCESS and Build/Validate `35416459565` SUCCESS. Three repeats measured `[60,60,60,60,60]/60` with identical semantic boundary sequence, but the old deterministic **Right+Run route is REJECTED for representativeness** because it spends most of the horizon blocked by authored geometry. Retain it only as a deterministic collision/enemy/regression probe; do not generalize its 60/60 to SRS.
- **Direct-SNES route authority:** `phase3/gate-b-srs-reference@c5f4c0310cc2334d3f4784517a24e27addfc9e96`, run `35418629393` / job `105832026639`. Pinned accurate ares emitted the complete **600-row** trace through guest `frameCounter=594`: it reaches the same wall state `room=1 player=(4250,4259) camera=(4122,4096)`, shows the same retreat/return pattern, and finishes on that wall. A fixed 60-guest-frame sampling starting at game frame 37 matches **6/7** safe Sodium boundary states exactly; the seventh differs only by 2 px of camera and reaches the exact state one guest frame later. This closes the old-route ambiguity: the stall is normal authored gameplay, not Sodium64-specific. The run is red only because ares SIGSEGVs during `std::exit` teardown **after** row 600; artifact upload was skipped.
- **Direct-SNES harness cleanup VALIDATED:** `phase3/gate-b-srs-reference@dd05ba502a6c4c6b7c4de2da1384207d23ea5a2d`. The only semantic-neutral harness change from `c5f4c031...` is tracer termination `std::exit(0) -> std::_Exit(0)`. Direct-reference run **`35419188132` SUCCESS**, job `105833513437`, emitted exactly 600 trace rows and finished at `host_frame=600 game_frame=594 room=1 player=(4250,4259) camera=(4122,4096)`, identical to the previous complete trace. Artifact **`10577226179`**, digest `sha256:9e08567f7995096fe69cb1bfe2357c1514be8c5622f1df569ef5a6278f7ac715`. Same-head Build/Validate **`35419188123` SUCCESS** (normal, PROFILE and emulator-smoke green). The previous SIGSEGV is therefore **REJECTED as guest/SRS evidence** and retained as a **LAB HARNESS DEFECT** caused by ares teardown after trace completion.
- **SRS representative route v1 PARTIAL / REJECTED as final workload:** `phase3/gate-b-srs-representative@c0652c7007ccb9886ff014af74f0c057b51ff18f`. Direct-SFC run **`35420037005` SUCCESS**, Build/Validate **`35420037006` SUCCESS**. Exact route identities: patch `sha256:6f01fb57b557b4426af7fc3290b3677e2a1c1d3b3effeb5006374655187e2a3b`, ROM `sha256:597caa5ef963bea4fed7991b8d1634e8d4c23ead5aabcfd3105926c892ebaa49`; artifact **`10577706765`**, digest `sha256:3bd49aa60e2bfdff8407e641664694030455e8f289e4b22f20e204a7644069d4`. Correctly filtered dynamic trace has 587 gameplay rows from `host_frame=14/game_frame=6`; it crosses the old x=4250 wall at gf95 and advances to **x=4554**, but then stalls there from about gf378 through gf594 and never leaves room1. Therefore v1 proves the old obstacle is traversable with normal input and gives a materially richer route, but is **REJECTED as the final representative workload** because it still spends ~216 guest frames blocked. Next action: derive v2 from the observed approach to the x4554 barrier, changing controller timing only; direct SFC first. The workflow's old `plausible-gameplay` summary filter also misclassified startup garbage (`room=110`, huge frameCounter) as gameplay; raw 600-row trace is sound, but fix this summary filter in the next read-only harness revision.
- **SRS representative route v2 REJECTED as final workload:** `phase3/gate-b-srs-representative@982f7b1058b09077a47ad069efa03751ffadfc9e`. Direct-SFC run **`35420515333` SUCCESS**, Build/Validate **`35420515316` SUCCESS**. Exact route identities: patch `sha256:175ed8495cfdf8a53a0b3906269b4096b1c2f43b428a37618414eed63ba64b5c`, ROM `sha256:d534bbc62286304edfe6871621f3ee569acb51d811a36486fecf6cd8c293eee2`; artifact **`10576927974`**, digest `sha256:b2fb8708d6fdf2ebcc51803b3fda6a312c3e58dc5487ed237513e688a559ea61`. Corrected summary reports 587 gameplay rows, max/final `x=4554`, room1 only. v2 reaches the same barrier later (first x4554 at gf402) and never exceeds it. Therefore global phase shift `0x08 -> 0x20` is **REJECTED** as the needed fix; next route must be informed by the exact barrier geometry/approach rather than another blind whole-pattern phase shift.
- **SRS representative route v3 REJECTED, but geometry hypothesis validated:** `phase3/gate-b-srs-representative@d3a101e4f0166bcdd3d0af68641cdfa3d0c074de`; direct-SFC `35421458128` SUCCESS, Build/Validate `35421458147` SUCCESS. Patch `e6cbc9478c79e21084fa748c1761068db23bb841fafbc39c25fd878cc584bc63`, ROM `354100d8f6dc14465cd8d06ba6bc9ba558c8d28c188a4387182569a37b6568a8`, artifact `10576984161` digest `sha256:4940fe564e9acbbbd85e81b480facf14517acc08835455e9b5f5374038ed1120`. Suppressing gf352 successfully makes the player land on the intended lower platform: y=4195 from gf377..384 while moving right. The targeted gf374 B edge expired just before standing state, so v3 still maxes at x4554. This **validates the lower-platform route concept** and isolates timing rather than geometry as the remaining issue.
- **SRS representative route v4 SUCCESS for wall traversal / PARTIAL for final route:** `phase3/gate-b-srs-representative@7932bc0cf44722990815685ed0f1d1e4e1951d92`. Direct-SFC **`35422018484` SUCCESS**, Build/Validate **`35422018496` SUCCESS**. Exact identities: patch `sha256:e47e1fa2bc5aaeba290a5a9fea367b9abdc35146f708b15b4afdd15800f71250`, ROM `sha256:b5a5e7cba7a8560264e39cab10727974dc5330f0500400ff2b2d3fa53c1e8391`, artifact **`10576884824`**, digest `sha256:6d52b4853c04cd9cf33165ff9231cf2be93dd81e301895bfa56135d52418c0ef`. The gf378 B edge produces an immediate authentic jump from lower-platform y4195: gf378 y4192, then sustained upward motion. It crosses the former x4554 wall at **gf403 x4556** and continues to **max/final x4810** by gf572/594, room1. This validates the lower-platform route mechanism and yields +256 px beyond the old hard stall. Route qualification is not closed yet because no room transition occurs inside 600 frames; inspect the final door approach before matched Sodium64 measurement.
- **SRS representative route v5 QUALIFIED on direct SNES:** current direct-reference branch `phase3/gate-b-srs-representative@d4c7d6ba1ca7a9a6233973560bfd2c7268fad661`. v5 changes only controller timing relative to v4 by suppressing the periodic gf544..559 B hold at the authored right-door approach; all player/physics/collision/room state remains untouched. Exact route identities are patch `sha256:b21d55df2d5fb949646c9a2124d5c062fa5e7f312264dabb2f354fdc67a27935`, ROM `sha256:2455da2b775a04b0e07775b39327d98b1de6a26f2da50bb1a8080e6e2ffffc46`. The 600-frame v5 direct run `35424126162` SUCCESS proves descent to the door floor and reaches x4815; Build/Validate `35424126115` SUCCESS. A read-only horizon extension to 720 frames at `d4c7d6ba...` changes no route ROM/input and produces direct run **`35424563879` SUCCESS**, Build/Validate **`35424563888` SUCCESS**, artifact **`10578072520`**, digest `sha256:98375a8b9b1ed8df9b3899ec246e531f51360d0776b0783dc8d8040c42b284cf`. It observes the authored transition from room1 to **room2/a1b_stairway at host_frame=621, game_frame=616**, then the new room initializes and progresses. **Route qualification is closed.** This exact v5 route is now also validated through Sodium64 as recorded in the next bullet.
- **SRS representative matched Sodium64 = VALIDATED HOST-LAB Gate-B evidence:** `phase3/gate-b-srs-v5-matched@4ece04a4430b99f7ea00d26967cfa601812e8d15`. Gate B SRS v5 Matched **`35425597914` SUCCESS**, job `105850864586`; same-head Build/Validate **`35425597920` SUCCESS**. The workflow rebuilt the exact qualified patch/ROM identities above, then ran three safe repeats with Road-valid settings before guest execution. All three measured vectors are **[60,60,60,60,60]/60**, 3584 profile samples each, and identical semantic boundary sequences. Four post-profile state-only windows prove the same authored room1→room2 transition. Same-`frameCounter` direct-SNES comparison is exact at 4/11 boundaries and differs only 1–3 px at the others; searching ±1 guest tick yields **10/11 exact spatial matches**, with the remaining first boundary only 1 px different. Final room2 state is byte-exact at the same `frameCounter=520`. **SUPPORTED INTERPRETATION:** deterministic route semantics match the direct SNES reference; residual pre-transition differences are consistent with observation-phase placement around `frameCounter`, not route divergence. Do not claim intraframe byte-perfect equivalence. Profile is identical across repeats: S-CPU 8.1%, Memory/I-O 0.1%, APU JIT 4.5%, APU static 30.5%, DSP 14.3%, PPU 5.1%, DMA 1.5%, VRAM/RSP wait 0.1%, RSP wait 0.0%, VI wait **35.7%**, other 0.1%. Artifact **`10579185638`**, digest `sha256:7e2a046ba6de1f147cd169d62203571966641b90bbf07947c9722e664ffbc6b6`. **LIMIT:** ares host-lab 60/60 is not real-N64 FPS authority. **Next Gate-B action: Nova2 gameplay audition; do not optimize Sodium64 from this non-failing SRS route.**
- **Nova2 remains resolved at source-build level:** `phase3/gate-b-nova2-audition@156b928191c130f13a19868e634c519647d91d59`, source-build run `35410418476` SUCCESS. Gameplay audition remains pending; do not repeat resolved Pillow/source-build troubleshooting.
- Continue the autonomous open/homebrew corpus path; no commercial ROM upload or always-on Iron PC dependency. Commercial software and real N64 remain later representativeness/final-authority milestones, not daily CI prerequisites.

## Operating protocol
Authority: **current Iron instruction > repo/artifact evidence > canonical docs > continuity > chats/memory/inference**. `master` is integrated truth; phase branches are candidates only.

Cadence: **technical batch -> continuity checkpoint -> technical batch -> continuity checkpoint**. Checkpoint every material result, changed hypothesis, falsification, risk, lab limitation, meaningful CI/artifact result, branch/HEAD transition or next-action change **before advancing**. For long experiments record exact SHA/run/question/possible readings before leaving them running.

Iron delegates technical direction toward Road to 1.0 to the assistant. Expose useful technical reasoning in chat (hypothesis, evidence, what it proves/does not, rejects, next controlled change, expected result, falsifier) without exposing private chain-of-thought verbatim.

## Historical opening snapshot — SUPERSEDED by current RESUME HERE
Current milestone: **M0 ACHIEVED / M1 — faster base core, APU/audio first**.
Perfect target: real N64, correct native cadence, no required frameskip/frame generation, full-rate SPC700/APU and correct audio, high CPU/PPU/DMA/HDMA/timing fidelity, broad compatibility, no per-game modes, DSP-1 family, SuperFX/2 and SA-1. N64-alone first; cartridge assistance only after a quantified N64 ceiling.

Integrated `master`: **`a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`**.
Completed M0 representative HEAD: **`89df64192d622bfa12e4bb53e0f41ceab928efe6`**.
Safe M1 BLOCK16 authority: **`c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`**; safe branch tree before experiment 2: **`225859b1d8fc0eb477a624ac76f8237667379f59`**, tree-equivalent to baseline.
Active M1 branch `phase2/apu-audio-first`: **`989e1f5ba8d592f6efb8e593d7a83fc5b51f3f89`** = experiment 2A layout-control attempt 2.
Diagnostic branch `phase2/apu-interleave-diagnostic`: **`8805fd6128a183ce2259dd4d85ef146f42f00d47`**.

### Canonical docs
PR **#10 MERGED-CONSUMED**: docs head `90fafc89...` merged as master `a2270699...`. Exactly `ROAD_TO_1_0.md`, `ROADMAP.md`, `PROFILING.md`; no code/workflows. Build/Validate `35225126989` SUCCESS; Ares Profile Validation `35225221616` SUCCESS. Master now canonically states M0 achieved and M1 APU/audio-first; 65C816 dynarec is evidence-gated later work, not the current assumed route.

## Laboratory authority / known limitations
- ares pinned RSP JIT is a **LAB LIMITATION** for Sodium64 custom microcode. Isolation run `35113184294`, artifact `10453682432`: RSP-JIT modes collapse; RSP-interpreter modes progress. Valid high-density lab = **R4300 JIT + RSP interpreter**.
- **REJECTED causes** from that investigation: R4300 JIT itself, missing semaphore semantics, dropped semaphore `MTC0`, RSP DMA-busy, accidental OAM wall primary cause. Old RSP-JIT profiles must not drive architecture.
- valid synthetic matrix run `35114866448`, artifact `10454678803`: idle60/60, cpu-alu41, wram47, ppu-registers38, dma-vram16, gameplay-balanced61/60 with 51.5% VI wait. Synthetic workloads are causal controls only.

## Representative workload / M0 real hardware
Gothicvania source `donth77/snes-homebrew:gothicvania`, source pin `119496e6...`; survivability ROM SHA-256 `5519d51f...`, patch SHA `ab1ec839...`. Health255 only prevents death during short capture; gameplay/audio/rendering/collisions/damage path remain active.

M0 hardware save SHA `3316bd99...`: frameskip0/APU21/audio4/precision8, 3581 samples, windows **48,49,48,50,50 /60**, mean **49.0/60**, queue0, VI wait0. Split: **APU/audio61.83%**, S-CPU22.12, PPU7.99, DMA6.67, RSPwait1.31. **M0 ACHIEVED.** Approx. 18.3% total host-time reduction needed for 60 if locally linear. This rejected 65C816 dynarec as first M1 attack; APU/audio is gate driver.

## M1 baseline16
SHA `c55b6b...`, ares run `35148379400`, artifact `10467972587`: **44/60**, 2000 samples. APU/audio54.40%, SCPU30.85, PPU7.45, DMA4.40, RSPwait2.55, VI0.35; `apu_execute`13.10. Real-N64 M0 sampled `apu_read8`6.03% and `apu_write8`2.88%; ares baseline included `read_unk`7.75% and `apu_read8`2.90%.

## M1 experiment 1 — BLOCK_SIZE 32 — REJECTED
Confounded SHA `3b39523...` is **SUPERSEDED**. Clean one-variable SHA `a758629...` changed only BLOCK_SIZE16->32 and measured **48/60 twice** in ares (artifacts `10477834229`, `10478782129`), proving block/dispatch overhead matters locally.

Paired DSP-lateness diagnostic then falsified acceptability:
- BLOCK32 diagnostic `7f8faeff...`, run `35183376105`, artifact `10481267575`: 35,965 due events, avg128.338 cycles, max1218, `>=672` 377 (1.048241%).
- BLOCK16 paired `8805fd61...`, run `35190371200`, artifact `10483348244`: 35,982 due, avg119.073, max651, `>=672` 0.
Event counts differ only ~0.047%; BLOCK32 materially worsens the tail/interleave. **REJECTED despite throughput gain.** Do not merge/hardware-test 32. Knowledge retained: reduce dispatch overhead without lengthening scheduler return intervals.

Timer2 side issue from superseded diagnostic `6921055...`: proposed `stamp_timer2 t1->t0` is **REJECTED**. `t0` holds `apu_control`; baseline `t1` correctly holds `apu_cycle2` before subtracting cycles-to-overflow. No source fix needed.

## M1 experiment 2 — low/direct-page APU read fast path
### Hypothesis
`apu_map` only has a runtime-relevant nonzero entry at index `0x3FF`; `write_control` updates only that entry for IPL ROM mapping at `0xFFC0–0xFFFF`. Direct-page generators produce `0x0000–0x01FF`; pointer second-byte reads reach at most `0x0200`. Therefore those reads can omit `apu_map` safely while preserving I/O and guest-cycle semantics.

### Design
Local `apu_read8_nomap` is appended to `apu_address.S`, not `apu.S`. It checks `0x00F0–0x00FF`; I/O tail-jumps to generic `apu_read8`. Non-I/O low reads load RAM, load `apu_clock`, decrement `s3` exactly once and return. Scheduler return frequency, BLOCK_SIZE and write paths stay unchanged.

Use paired layout control:
1. **2A:** helper present but unreachable; zero call targets changed. Measure layout-only effect.
2. **2B:** on exact 2A layout, redirect only proven-low call targets. Initial scope: direct, direct+X/Y, `(X)`, `(X)+`, the two low pointer-byte reads in `[dp+X]` and `[dp]+Y`, `dp,dp` low read, `(X),(Y)` low read. Leave final indirect/absolute reads, `apu_drb`13-bit, ALU operation-level reads, stack/transfer reads, writes and BLOCK_SIZE untouched.

### 2A attempt 1 — COMPILE FAILURE / NO PERFORMANCE EVIDENCE
SHA **`e2b1979a...`**. Build/Validate `35226731916` FAILED normal+PROFILE; Open Homebrew `35226731941` failed profile-build and skipped Gothicvania. Exact assembler cause: `lbu v0, apu_ram(a0)` pseudo-instruction expanded into multiple instructions in a branch delay slot; warnings-as-errors. This SHA has **no performance evidence**.

### 2A attempt 2 — original in-progress checkpoint (completion audited below)
SHA **`989e1f5ba8d592f6efb8e593d7a83fc5b51f3f89`**. Minimal correction from attempt1 is exactly **+1/-0**: branch delay slot is `nop`, then the same `lbu` follows. Direct compare from safe `225859b1...` remains exactly one file `src/apu_address.S`, **+11/-0**. Helper is still unreachable; no existing read call target changed.

Exact runs: **Build and Validate `35227136991` SUCCESS** — normal build, PROFILE build and emulator-smoke all green. **Open Homebrew Ares Profile `35227136832`** — profile-build green; at this checkpoint `ares-gothicvania` is still in progress building pinned ares in valid lab mode. Experimental question remains: does helper-only code/layout alter the Gothicvania baseline? Expected sane reading is ~44/60. Material movement means layout itself is a confound and this 2A SHA becomes the paired baseline for 2B.

**What this proves now:** the corrected unreachable helper is acceptable to assembler/linker and does not break the independent Mupen smoke path. **What it does NOT prove:** any performance equivalence or benefit; no Gothicvania result exists yet for 2A attempt2.

If 2A is sane/equivalent, 2B keeps exact helper/layout and changes only the enumerated proven-low call targets. **Expected:** lower APU-read cost, possibly modest frame-budget gain. **Falsifier:** neutral result, semantic/build regression, or evidence any redirected call can reach IPL space / lose I/O semantics.

## Previous RESUME HERE — SUPERSEDED by the audit below
1. Read completion of **Open Homebrew `35227136832`** for exact `989e1f5b...`. If successful, record exact artifact/frame budget immediately. Any material movement in 2A is layout-only by construction.
2. If 2A is sane, implement 2B changing only enumerated call targets; verify 2A->2B diff is target substitutions only and checkpoint exact SHA before interpretation.
3. Profile 2B on identical Gothicvania settings. Compare complete virtual frame budget first, then sampling shares; repeat same SHA if ambiguous.
4. Reject any semantic/timing regression even if faster. Hardware is final authority only for candidates that survive lab validation.

Resume summary: master `a2270699...`; M0 hardware mean49/60 with APU/audio61.83%. BLOCK32 local speedup was REJECTED by paired DSP-lateness. Experiment2 2A attempt1 failed assembly with no measurement; corrected helper-only layout control `989e1f5b...` now passes build + Mupen smoke, while exact Gothicvania run `35227136832` is still in progress.
## Independent read-only direction audit — 2026-09-17

Scope: architecture/direction red-team, not implementation. Only this continuity file is changed by the audit. No runtime/workflow/other doc edits, PRs, merges or experiment launches. The full 1.0 target and N64-alone priority are unchanged.

### Evidence identity and audit limits

- Integrated master verified at `a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`; current master Build/Validate `35226256321` and Ares Profile Validation `35226256322` both SUCCESS.
- Active candidate remains `phase2/apu-audio-first@989e1f5ba8d592f6efb8e593d7a83fc5b51f3f89`; Build/Validate `35227136991` SUCCESS. No open PR at audit time.
- Diagnostic remains `8805fd6128a183ce2259dd4d85ef146f42f00d47`. Direct forward diff `7f8faeff6efa1d94c421ad0369938d8c0d077195 -> 8805fd61...` is ONLY BLOCK_SIZE32->16. Logs independently verify the recorded due counts/sums/maxima/tails. BLOCK32 rejection stands.
- `c55b6b44... -> 225859b1...` has zero changed files. `225859b1... -> 989e1f5b...` is ONLY the +11-line unreachable helper in apu_address.S.
- Read all five canonical docs, historical M0 closure at continuity commit `5ebe300ed7907970ca9f99ef4fac5a2620143c03`, APU generator/runtime modules, DSP, scheduler, relevant PPU/memory/coprocessor paths, profiler/harness/workflows and pinned ares reference paths.
- M0 artifact `10467585906` independently matches run `35145447113`, HEAD `89df64192d622bfa12e4bb53e0f41ceab928efe6`, ZIP digest `db187230e8728c22b5acebbeabd99489af538994c79eece0a6d4f2a054415086`. Original returned SRAM save `3316bd99dc26224050153c5a10c167b0e0b520aa9e4b85699b8ab45911f1f395` was NOT re-decoded in this audit; its measurements remain previously recorded hardware evidence, not new measurements.
- Artifact metadata and decoded CI logs were accessible; attempting to read the ZIP download bytes in this environment returned HTTP403. Consequently no claim of independent ELF disassembly/raw-snapshot decoding here. This audit's new runtime observations come from exact job logs; source conclusions are distinguished from dynamic validation.
- Gothicvania ROM remains `5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`, frameskip0/APU21/audio4/precision8, ares pin `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`, R4300 JIT + RSP interpreter.

### A. MEASURED: 2A completed, and the baseline has a material A/A discrepancy

Open Homebrew `35227136832` SUCCESS, job `105221944468`, artifact `10499991568`, digest `10b4fbac88be8c04fa47bbcdac2f7812099fa8c8d5001b2098030741ad772996`:
- exact SHA `989e1f5b...`, **52/60**, 1092 samples, partial VI32/60, partial guest27, queue1;
- APU static31.32%, generated4.95%, DSP14.38%, S-CPU31.04%, PPU9.07%, DMA6.41%, RSP/VRAM wait2.47%, VIwait0.37%;
- `apu_execute`7.23%, `apu_read8`1.83%; helper still never called.

The SAME baseline SHA `c55b6b44334fcaa22c59bf9d3bdac26dca38ed9c`, SAME run `35148379400`, has distinct attempts:
- attempt1 job `104970584720`, artifact `10467972587`: **44/60**, 2000 samples; `apu_execute`13.10%, APU aggregate54.40%.
- attempt2 job `104987346877`, artifact `10470371683`: **48/60**, 1288 samples; `apu_execute`14.13%, APU static36.34 + generated4.43 + DSP12.66 =53.43%; digest `7fd939959855f1389560f4d2db45fb439f334aa7648d21c027cdbd9f33ddf7ca`.
Both have identical reported guest ROM/settings and download the same profile-build artifact digest `6b2986bae04ae0c7efe8218e18ff37eb7fe3073a83064fcc79f6609b7a4fdc8e`.

**SUPPORTED INTERPRETATION:** the 4-frame baseline A/A movement is as large as the historical claimed BLOCK32 gain. The old statement “44->48 proves dispatch overhead” is too strong. Preserve the actual 44 and 48 observations; causal magnitude and mechanism are **UNKNOWN** until comparable windows/repeats establish an effect. This does NOT rehabilitate BLOCK32: its independently paired guest-cycle lateness regression still justifies rejection.

**REJECTED inference:** 2A's 52 proves map-elimination speedup (helper is unreachable). Also reject “any 2A movement must be layout-only by construction”: only the SOURCE difference is layout-only; measurement-phase/host-stop/sampling variation remains a competing cause.

**LAB LIMITATION / source evidence:** open-homebrew-profile.yml warms for 1 host second, patches APU clock/JIT, settles 1 host second, then gdb_rsp_dump.py stops every 3 host seconds until >=800 samples. It captures the last complete VI window, not a fixed guest checkpoint sequence; profile samples cover a broader interval than that single last window. Deterministic entropy and a fixed ROM do not make wall-time-selected guest segments identical. Changing clock/JIT at an arbitrary stop can also leave an in-flight old generated block and old cycle state; resetting lookup/pointer alone does not prove a clean temporal transition. Magnitude of this risk remains UNKNOWN. Pin settings before guest execution or at a proven safe scheduler boundary in a future measurement repair.

### B. SUPPORTED INTERPRETATION: verify effective SPC700 timing BEFORE a major JIT optimization

This is a direction issue: `apu_clock=21` proves the configured inherited rate, not correct instruction throughput or full SPC700 timing.

Source accounting at audited candidate:
- `jit_read8` subtracts one apu_clock from compile-time `s2` for each opcode/operand byte.
- `apu_read8/apu_write8` subtract one apu_clock from runtime `s3` per data access.
- `finish_block` emits the accumulated fetch debit at block exit.
- `apu_mul`, `apu_div`, `apu_bra` and conditional branch generators contain no additional internal/taken-branch cycle charge; NOP dispatches straight to next_opcode.

For isolated instruction accounting, source predicts NOP1, MUL1, DIV1 and BRA2 inherited clock units, versus 2,9,12,4 in the pinned independent ares SPC700 reference (`ares/component/processor/spc700/instruction.cpp` plus `instructions.cpp`, same ares pin above; reference fetch + read/idle calls). This is static accounting/reference disagreement, NOT a freshly run cycle test. Arbitrary MIPS execution time does not automatically debit Sodium64's guest `s3`.

**HYPOTHESIS:** part of the APU burden is excess SPC700 instructions executed per emulated time because internal cycles are undercharged. Correct timing could reduce host work while improving fidelity, but direction/magnitude on Gothicvania is UNKNOWN. Synchronization-sensitive drivers can change behavior; no speedup percentage is claimed.

**Direction change:** a small instruction-cycle and I/O-order proof now outranks broad memory/dispatch work. Do not “fix” this by global clock scaling or a game-specific mode. If confirmed, a bounded guest timing correction must be measured separately from optimization, then establish a new baseline. Baseline-equivalence remains useful for performance-only changes but is not proof of SNES fidelity.

**Additional source-backed risk:** BLOCK_SIZE is not an unconditional maximum. Opcode0x00 (NOP) maps directly to `next_opcode`, bypassing `finish_opcode` and its a0<t9 limit test. A long NOP sequence can cross nominal block and 64-byte tag-region limits before a terminating/checking opcode. This undermines generic claims “16 bytes guarantees interleave” and “only two endpoint tags always cover a block.” Runtime consequences and prevalence in Gothicvania are UNKNOWN. Test long NOP spans and mutation of a middle covered region before assuming bounded dispatch/SMC safety. Existing absolute-write self-modification handling in apu_absa does not establish safety for all indirect writes or changes later in an executing block.

### C. Architecture ranking and profiler interpretation

**SUPPORTED INTERPRETATION:** APU/audio remains the right first subsystem. Historical hardware: static24.91%, generated19.18%, DSP17.73%=61.83%; roughly18.3% total time reduction (29.7% of that aggregate) would close Gothicvania's 49->60 gap under fixed-cost linear assumptions. This is workload-local, not a 1.0 corpus/hardware ceiling. The 6.03% named apu_read8 share cannot by itself justify a plan to recover18.3%; the eligible mapping subpath is only part of that region, and attribution/cache cross-effects prevent treating 6.03 as an exact hard bound.

- **Memory specialization:** current 2A helper's low-address/map argument is supported by source. Only IPL entry0x3FF changes; proposed direct addresses are0..0x1FF, pointer second-byte reaches0x200. I/O tail fallback preserves existing semantics and exactly one data-cycle debit. However low-page is NOT synonymous with ordinary RAM: 0xF0..FF includes timers/DSP/CPU ports. The new helper adds a guard before the generic guard for those accesses. Net benefit depends on actual eligible RAM/I/O mix. Preserve P-page changes, index wrapping, second-byte behavior, register-clobber contract and unchanged final indirect reads. Do not silently turn this optimization into an addressing-correctness repair.
- **Generated code:** load_reg_* already load lazily, finish_block already spills only dirty state, and NZ updates are already deferred. “Add register caching/lazy flags” is not a new architecture. Remaining opportunity: repeated full_address LUI+access sequences, address generation, helper jal/jr, repeated apu_clock reads, and spills/reloads across short blocks. A compact state-base convention / selective generated RAM loads may reduce these without longer blocks; payoff and register-pressure/I-cache effects are HYPOTHESIS. Full memory-read inlining is not automatically a win.
- **Dispatch/invalidation:** apu_execute performs lookup plus two endpoint-tag validations per cached entry, even when both refer to the same64-byte region. Single-region specialization is a bounded candidate after the block-span proof. Keep DSP/CPU checks at the same logical boundaries and preserve invalidation. Do not remove checks based on a single game's apparent code immutability.
- **Write path:** every APU write increments a64-byte region tag, including data-only regions. Avoiding needless invalidation/updates could help, but executable-region ownership and code/data mixing are unproven. No hot-path “writes cannot be code” assumption; first establish write mix/recompile causes, only if samples justify it.
- **Compilation/cache maintenance:** emit_op invalidates I/D-cache aliases for each emitted word; line-batched maintenance could save compile cost. In read CI profiles apu_emitter.o is0–0.39%, so this is NOT a first optimization absent contrary representative evidence. Lookup table is256KiB, tags4KiB, generated buffer256KiB; these are allocated sizes, not measured hot working sets. Hardware cache savings require hardware evidence, not size arithmetic.
- **DSP:** historical get_pitch3.52% / DSP aggregate17.73% justify an independent bounded proof now, not an obligatory long queue of read-helper variants. Pitch endian/mask conversion happens per active voice/sample; cache the derived base pitch at register writes as one candidate. Do not cache future modulation/envelope-dependent results or defer observable writes. Existing volume products are already cached. Another larger path may win later; evidence does not yet justify RSP offload.
- **Scheduler:** cpu_execute includes APU/PPU checks yet is classified as S-CPU solely by object; apu_execute includes the DSP-due check as well as JIT validation. Bucket totals are not clean functional attribution to interpreters vs scheduling.
- **Symbol labels:** apu.S read_unk is also the ordinary non-I/O read return; write_unk likewise. High read_unk samples do NOT establish unknown-register polling. profile_report.py aggregates base symbol names without object qualification; local duplicate names need address/object context. Attribute raw EPC ranges and branch-delay effects before using tiny regions as optimization budgets.
- **LAB LIMITATION:** N64 hardware generated-code share19.18% versus baseline ares3.30% (repeat4.43%, 2A4.95%) means ranking generated-code/layout work solely by ares percentages can mislead. Cause is UNKNOWN: workload phase, cache/timing model and interrupt attribution compete. Pinned ares cpu.cpp/recompiler.cpp contain deferred cycle flushing and interrupt/synchronization boundaries plus actual I/D-cache modeling. Do not claim ares “has no cache”; do not claim its sample distribution is hardware-equivalent. A small CPU-interpreter control can test attribution sensitivity when needed, without reopening the rejected RSP-JIT investigation.

### D. Fidelity and 1.0 convergence risks

**SUPPORTED INTERPRETATION (source):** current DSP/audio budget excludes work required by the target. dsp.S selects stored BRR samples directly (no Gaussian interpolation path in this source), and contains no echo/FIR or pitch-modulation processing comparable to pinned ares sfc/dsp/{dsp,voice,echo,gaussian}. Its global output/timing behavior also needs reference validation. This is not a demand to transplant a second DSP/emulator; preserve Sodium64 and add only required behavior with tests. Near-term work should favor invariant access/dispatch/state costs that survive fidelity recovery.

“Audio enabled/full-rate setting” and “no lateness >=672” do not prove correct PCM, correct register visibility, AI delivery without underflow, or correct native cadence. BLOCK16's measured max651 is a local baseline, not an accuracy specification or universal bound.

Other recorded target debt: approximate APU/DSP integer cycle constants, fixed NTSC-oriented VI/262-line assumptions, PPU pre-VBlank timing workaround; DSP-1 has explicit unimplemented paths and SuperFX/SA-1 are absent. Do not infer GateB/C/D/E/F completion from one homebrew at60. Cost after accuracy recovery can increase or decrease; no quantitative N64-alone ceiling or cartridge-assistance rationale exists.

Keep M1 APU-first, but bring a SMALL timing/PCM reference contract forward from later accuracy work. Follow a credible first gain with a second meaningfully different audio driver/workload before a large architectural commitment. Do not grow an unbounded corpus/tooling project. Do not start 65C816 dynarec, SuperFX translation, or SA-1 infrastructure simply to avoid the current unresolved measurement/timing questions.

### E. Five prioritized experiments (proposals only; none run by this audit)

**E1 — comparable A/A and layout control (immediate; GateA / M1 measurement prerequisite).**
- Hypothesis/evidence: wall-time-selected phases and/or layout explain44/48/52; baseline same-build discrepancy and unreachable-helper result directly motivate it.
- Minimal change: unchanged existing binaries first, same boot/settings and a defined guest checkpoint/segment; collect several complete sequential VI windows, not only the last. Use an existing safe stop if sufficient; otherwise only the smallest measurement-boundary repair. Fix build/toolchain/ELF/ROM identities. Obtain baseline A/A then alternate safe-tree vs2A comparisons. Do not activate helper.
- Measure: guest checkpoint/state, each complete VI budget, total guest frames and virtual Count delta over same segment, sample count/window, queue/audio state, symbol addresses/layout. Pair aggregate cost with shares; do not multiply a whole-profile share by an unrelated last-frame budget.
- Expected/falsifier: repeated identical-build variation shrinks at matched checkpoints; a stable remaining safe-vs2A shift supports a layout mechanism. Persistent A/A spread comparable to candidate effect falsifies the lab's ability to rank small optimizations; no repeated safe-vs2A difference falsifies layout-gain attribution.
- Does NOT prove: any helper benefit, real-N64 gain, exact SNES timing or commercial representativeness.
- Environment: valid ares first; CPU-interpreter control only if needed to separate attribution. No immediate hardware ritual; real N64 for a material layout-sensitive candidate.

**E2 — SPC700 cycle/exit contract (highest architectural uncertainty; GatesA/C and M1/B).**
- Hypothesis/evidence: missing internal/taken-branch charges cause over-execution; NOP bypass also defeats nominal block limits. Source/reference ledger above.
- Minimal change: isolated original SPC snippets for NOP/MUL/DIV, taken/not-taken branches and one timer/port loop; compare existing Sodium64 state/cycle deltas and ordered accesses against an independent pinned reference. Include a long NOP span crossing64-byte regions and later mutation of a middle region. Begin with observation; any timing correction is a SEPARATE one-variable candidate, no memory-helper/dispatch rewrite.
- Measure: guest PC/registers, logical elapsed SPC/master cycles, instruction count per timer interval, ordered I/O timestamps, DSP due/late distribution, actual guest-byte span per block, re-entry after mutation. Then determine how frequent relevant opcodes are in Gothicvania before projecting savings.
- Expected/falsifier: original runtime exhibits the predicted per-op deficit / oversize span; an omitted charging/exit mechanism demonstrated dynamically falsifies that interpretation. If confirmed but rare in representative execution, it falsifies the predicted large performance relevance, not the correctness issue.
- Does NOT prove: how much FPS a timing repair gains, full SPC correctness, correct final audio, or acceptability of simply lengthening scheduler intervals.
- Environment: deterministic reference + valid ares; independent Mupen semantic check where feasible. N64 confirms subsequent candidate cadence/audio at milestone.

**E3 — finish controlled low-read proof (after E1, with E2 accounting explicit; GatesB/C / M1).**
- Hypothesis/evidence: map-lookup overhead on proven-low non-I/O reads exceeds helper/fallback costs; hardware read cost and source mapping invariant motivate it.
- Minimal change: exact2A->2B call-target substitutions only. No BLOCK_SIZE/write/final-indirect/ALU changes. Establish ABI and instruction expansion from ELF; exercise P0/P1, index wrap,0xEF/F0/FF/100/1FF/200, timers clear-on-read, CPU/DSP ports, IPL on/off.
- Measure: matched complete-frame/Count cost; selected non-I/O vs I/O access mix (bounded diagnostic only if necessary); combined generic/helper/I/O/return regions; unchanged guest state, cycle debits and event ordering. Use separate timing-instrumented pair rather than instrumented FPS.
- Expected/falsifier: reproducible absolute cost reduction beyond A/A spread and semantic equivalence. No useful net gain, fallback dominating, address proof failure or any timing/state mismatch rejects this narrow candidate.
- Does NOT prove: that direct generated loads cannot work if this helper is neutral, that all low-page reads are RAM, or that memory work alone closes49->60.
- Environment: valid ares + targeted semantic checks; N64 final for a candidate worth retaining, especially given JIT/cache-share discrepancy.

**E4 — short-block validation specialization (conditional, not bigger blocks; GatesB/C / M1).**
- Hypothesis/evidence: duplicate endpoint checks for blocks provably within one64-byte tag region materially cost dispatch; apu_execute and short-block source motivate it.
- Minimal change: specialize only validation for a proven single-region block; retain original two-region fallback, block/event boundaries, spill contract and invalidation. Do not combine chaining, permanent-register ABI or new cycle batching. E2 must first establish actual spans.
- Measure: single-vs-two-region entry frequency, absolute entry+generated+frame cost, code/header footprint, recompile counts, DSP/I/O ordering, SMC/IPL/boundary/rollover tests; paired layout control.
- Expected/falsifier: same correct entry decisions with lower representative cost. Rare eligibility, added branch/layout cost cancelling savings, stale execution or event-order divergence rejects it.
- Does NOT prove: longer blocks/chaining are safe, invalidation can be omitted, compiler-cache maintenance is hot, or real-N64 gain.
- Environment: ares/Mupen for semantics; N64 for cache/dispatch payoff. If supported, a later SEPARATE proof may reduce repeated state-address materialization in existing short generated blocks.

**E5 — hoist one DSP invariant (alternative to a long JIT micro-optimization series; GatesB/C / M1).**
- Hypothesis/evidence: derived base pitch can be computed on register writes instead of endian/mask work per voice/sample; historical hardware get_pitch3.52%, total DSP17.73%.
- Minimal change: cache only derived PITCHL/PITCHH base value, updated on either byte write with identical existing visibility; unchanged voice order, BRR, mixing and DSP schedule. No resampling/voice disabling/echo redesign in the same experiment.
- Measure: exact PCM and voice state against baseline for controlled pitch writes/KON/BRR boundaries and representative segment; compare reference behavior separately so baseline-equivalence is not called accuracy. Measure write-side cost, sample-side cost and absolute frame budget.
- Expected/falsifier: identical baseline state/output with a repeatable net saving. High write frequency, stale partial-register updates, changed visibility or no absolute gain rejects it.
- Does NOT prove: existing DSP is accurate, missing interpolation/echo is free, this is enough to close the remaining gap, or offload is justified.
- Environment: ares/Mupen lower-level execution and pinned SNES reference; N64 validates retained gain/audio. Future sub-sample DSP fidelity may require latching individual pitch bytes; do not freeze a combined cache into the fidelity contract.

### Audit decision

**Material immediate-route change is justified; subsystem direction is retained.** First stabilize measurement interpretation and falsify the inherited instruction-timing/block-span assumptions. Keep2B as a bounded candidate, not the automatic next implementation. DSP invariant work and same-boundary validation/generated-code improvements remain viable Sodium64-native routes. No quantified evidence justifies abandoning N64-alone or building a second emulator.

Master canonical docs still contain the stronger “44->48 proves overhead” interpretation; record this correction here and schedule a future authorized doc sync. They were deliberately NOT edited in this read-only audit.


## RESUME HERE

1. **Read the independent audit above before implementing2B.** Master remains `a2270699...`, active M1 remains `989e1f5b...`, diagnostic remains `8805fd61...`; no code was changed by the audit.
2. **2A is completed, not running:** `35227136832` / job `105221944468` / artifact `10499991568`:52/60,1092 samples. Record it as a helper-unreachable observation. Baseline same SHA/build also has44/60 AND48/60 attempts. Do not assert a mapping speedup or a proven layout cause.
3. Execute a bounded **E1 A/A and matched-window comparison** before ranking small changes. Preserve the historical observations but replace the unsupported causal reading; do not reopen BLOCK32, which remains REJECTED for timing.
4. Execute **E2 cycle-accounting/block-span proof** before a major JIT investment. Distinguish configured apu_clock21 from instruction-accurate full rate; verify NOP exit/invalidation assumptions. Any correction becomes its own measured timing candidate and fresh baseline.
5. With those uncertainties resolved, select the next bounded implementation from E3 low-read helper, E4 same-boundary validation, or E5 DSP invariant hoisting based on expected absolute savings and correctness. Keep one important variable per experiment.
6. Graduate retained candidates to one real-N64 milestone session with exact build/ROM/settings, frame windows, audio/cadence and decision criteria. No scope reduction, cartridge assistance, second emulator or unbounded tooling.

Resume summary: **M0 remains achieved as a measurement milestone; M1 remains APU/audio-first.** This audit changes the immediate order because previously unrecorded A/A variation and source-backed guest-cycle/block-span gaps undermine blind optimization of the inherited baseline. Current APU full-rate setting and BLOCK16 are diagnostic configurations, not universal timing/fidelity proofs.

## E1 execution checkpoint / E2 setup — 2026-09-17

### E1 — MEASUREMENT PROOF / current harness limitation confirmed
The rerun of `Open Homebrew Ares Profile` run **`35227136832`** reused the exact profile-build artifact rather than rebuilding it. Shared build artifact **`10499232867`**, digest **`dac80a1f3911e30e53a7e56e116916977540969035cc8530400776c089996668`**, exact source SHA **`989e1f5ba8d592f6efb8e593d7a83fc5b51f3f89`**.

- attempt1 job **`105221944468`**, result artifact `10499991568`: final state `vi_count=52`, `guest_frame_count=52`, `sample_count=1092`, partial VI `32/60`, partial guest `27`, `frame_wait_count=4`, `queue_count=1`.
- rerun attempt2 job **`105254633842`**, result artifact **`10503143461`**: final state `vi_count=63`, `guest_frame_count=61`, `sample_count=2100`, partial VI `9/60`, partial guest `8`, `frame_wait_count=0`, `queue_count=0`. Settings remain APU21/frameskip0/audio4/precision8.

**SUPPORTED INTERPRETATION:** this is a cleaner binary A/A than previously known because ROM/ELF/map build input is identical, but it is NOT a matched guest-window performance comparison. The two attempts stop at different VI/guest phases and radically different sample counts. The apparent 52-vs-61 totals therefore cannot be interpreted as performance drift or layout gain. It demonstrates that the current wall-time/sample-target stop condition is insufficient authority for ranking small 4–8-frame changes.

**REJECTED inference:** do not call the 2A `52/60` an optimization result; do not use attempt1-vs-attempt2 totals as a measured nine-frame A/A spread; and do not resurrect the historical BLOCK32 causal gain from these numbers. BLOCK32 remains independently REJECTED by paired DSP-lateness.

**Immediate measurement requirement:** before E3/E4/E5 performance ranking, repair or add the smallest possible matched-window boundary: same binary identity, same proven guest checkpoint, several complete sequential VI windows and comparable Count/sample windows. This is a bounded Gate-A measurement repair, not a profiling subproject.

### E2 — cycle-accounting/block-span proof in progress
Branch **`phase2/apu-cycle-proof`** starts from safe tree `225859b1d8fc0eb477a624ac76f8237667379f59`. Current HEAD **`f0159bf9fe6583b106798f2ce4a04708bd6930d2`**, commit `diag: add APU cycle proof capture state`; Build and Validate **`35237136742` SUCCESS**. The commit only adds PROFILE-only diagnostic state and changes no production behavior.

Source inspection sharpened the E2 hypothesis:
- `jit_read8` subtracts one `apu_clock` from compile-time `s2` for each opcode/operand byte; runtime memory accesses debit separately through `apu_read8`/`apu_write8`.
- `apu_alu.S` contains no additional `s2` debit for MUL/DIV internal cycles.
- opcode `0x00` NOP dispatches directly to `next_opcode`, bypassing `finish_opcode`; therefore a sufficiently long NOP run can ignore the nominal `BLOCK_SIZE=16` check until a later opcode reaches `finish_opcode`.
- cache validation records/checks endpoint 64-byte tags. If a generated block can span three or more regions through the NOP bypass, an intermediate-region mutation may be missed. This is **source-supported risk, not yet dynamic proof**.

Pinned ares SPC700 reference at `17813a3c...` independently models total NOP/MUL/DIV/taken-BRA timing as 2/9/12/4 SPC cycles. Sodium64 source currently appears to account isolated fetch units as 1/1/1/2 respectively before data accesses. **HYPOTHESIS:** inherited APU timing undercharges internal instruction cycles, potentially executing excess SPC700 work per emulated time. Magnitude and representative frequency remain UNKNOWN.

The dynamic E2 test must now prove or falsify two things separately: (1) actual generated static debit for BRA-only, NOP+BRA, MUL+BRA and DIV+BRA snippets; (2) actual long-NOP generated span/header behavior, including a middle-region mutation check. No timing fix or optimization is authorized until observation is complete.

## RESUME HERE — E1/E2 checkpoint 2026-09-17

1. Integrated `master` is still `a2270699...`; 2A remains `989e1f5b...`; diagnostic BLOCK16 remains `8805fd61...`; E2 branch is `phase2/apu-cycle-proof@f0159bf9...` and Build/Validate `35237136742` is green.
2. E1 has established a **LAB LIMITATION in the current stopping/measurement boundary**, not a quantified A/A slowdown: exact build artifact `10499232867` was reused, but attempt1 stopped at 52 VI/1092 samples and attempt2 at 63 VI/2100 samples. Small frame-total differences are not causal evidence until matched guest windows exist.
3. Continue E2 with a bounded dynamic proof script/workflow. Observe original JIT only; test BRA, NOP+BRA, MUL+BRA, DIV+BRA and a >128-byte NOP span. Decode generated block static debit and start/end tag regions; then mutate a middle region and test cache re-entry.
4. Falsifiers: any hidden debit that restores reference cycle totals rejects the under-accounting hypothesis; an observed enforced stop before crossing the nominal span rejects the NOP-span hypothesis; a middle-region change that invalidates/recompiles through another mechanism rejects the missed-intermediate-tag hypothesis.
5. If E2 confirms timing under-accounting, make the correction a separate correctness candidate and establish a fresh baseline before optimizing. If E2 falsifies it, return to E3/E4/E5 selection. Separately make the minimal matched-window E1 harness repair before using small ares throughput deltas to rank candidates.
6. 2B remains **DEFERRED, not REJECTED**. Do not merge diagnostic code, reopen BLOCK32, start 65C816 dynarec, move work to RSP, reduce fidelity, or build a second emulator to bypass these questions.

## E2 dynamic proof — CONFIRMED 2026-09-17

Diagnostic branch advanced from the setup checkpoint to **`phase2/apu-cycle-proof@e2ac0c29f5ca4d80b737f714d2d4ae30e91da897`**. Commit `c1e22e9e72dcb7d369113df6cb3ce0d07b04f97f` added the bounded GDB-RSP proof script; `e2ac0c29...` added the branch-only workflow. No production fix was applied.

Exact CI:
- **APU Cycle And Span Proof `35245970304` SUCCESS**, profile-build job `105286137431`, cycle-proof job `105286577504`.
- **Build and Validate `35245970309` SUCCESS** on the same exact SHA.
- proof artifact **`10508131011`**, digest **`sha256:3b6c2a6d1dcfba6f9bc5c89730b23b31a5c12bde366eb6671ae9ccf3bc2a61d0`**.
- exact proof-build artifact **`10507975608`**, digest **`sha256:5bd82c795c02e089ba600f14df4d2bc9a5cc385a88487b30e079491a236ff49a`**.
- pinned ares remains `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`, R4300 JIT + RSP interpreter; Gothicvania source/provenance/settings remain the validated diagnostic substrate.

### E2A — MEASURED: inherited SPC700 cycle under-accounting is real

The proof stops at a safe `apu_execute` scheduler boundary, injects isolated SPC700 snippets, forces a clean JIT lookup entry, stops at `compile_block`, then inspects the exact generated block and its unique emitted `ADDI s3,s3,imm` cycle debit.

| case | source bytes | measured debit | measured source clock units | pinned-reference SPC cycles |
| --- | ---: | ---: | ---: | ---: |
| BRA | 2 | -42 | **2** | **4** |
| NOP + BRA | 3 | -63 | **3** | **6** |
| MUL + BRA | 3 | -63 | **3** | **13** |
| DIV + BRA | 3 | -63 | **3** | **16** |

All measured debits exactly match Sodium64 source prediction and materially disagree with the pinned independent SPC700 reference totals.

**VALIDATED / correctness finding:** for these isolated instructions, Sodium64 is not merely configured with `apu_clock=21`; it actually undercharges guest instruction time. There is no hidden debit restoring NOP/MUL/DIV/BRA reference timing. The previous under-accounting hypothesis is therefore **CONFIRMED for the tested instruction classes**.

**SUPPORTED INTERPRETATION:** inherited timing can execute excess SPC700 instruction work per emulated interval. Correcting timing may therefore improve both fidelity and host cost, but Gothicvania magnitude is still UNKNOWN and no speedup percentage is claimed. Do not globally rescale `apu_clock`: the missing amount is instruction/path dependent.

### E2B — MEASURED: nominal BLOCK_SIZE and endpoint-only invalidation can fail

A controlled `126×NOP + DBNZ Y,-128` source sequence compiled as **128 source bytes** from PC `0x0200` despite `BLOCK_SIZE=16`.

Measured generated header:
- start tag region **8**;
- end tag region **10**;
- source clock units **128**;
- therefore the generated block spans at least **three 64-byte tag regions**.

The proof then changed an actually covered byte in middle region **9** (`0x0240`) from NOP to CLRC and incremented that region's tag exactly as `apu_write8` would. Start/end tags were untouched.

Measured re-entry:
- middle tag **0 -> 1**;
- lookup pointer before/after remained **`2149318676`**;
- JIT pointer before/after remained **`2686189652`**;
- breakpoint on the old generated-code entry was hit with SIGTRAP;
- **`old_block_reentered = true`**.

**VALIDATED / correctness finding:** NOP's direct dispatch to `next_opcode` can bypass the nominal block bound, and the current two-endpoint tag validation can then miss a mutation in an intermediate region and execute stale generated code. This is no longer a source-only risk.

**What E2 does NOT prove:** prevalence in Gothicvania, magnitude of real-game performance impact, or that all SPC700 opcodes have the same timing error. It also does not authorize merging the diagnostic harness.

### Decision after E2

1. **Timing correctness now outranks E3/E4/E5 performance optimization.** Build a separate bounded timing-correction candidate; establish a fresh baseline after semantic validation before attributing any throughput change.
2. Keep timing correction instruction/path-specific. First derive the minimum trustworthy cycle contract from the pinned reference and Sodium64's existing split: opcode/operand fetches are compile-time debits, runtime memory accesses already debit through `apu_read8/apu_write8`, and only the missing internal/taken-branch cycles should be added.
3. Fix the independently confirmed NOP block-bound/invalidation defect as a separate one-variable correctness candidate. The smallest candidate is to route NOP through the normal `finish_opcode` boundary, then rerun the >128-byte span + middle-tag mutation proof. Do not bundle this with timing correction.
4. E1 matched-window repair remains required before ranking small ares throughput deltas. Correctness tests can proceed independently.
5. 2B low-read helper remains **DEFERRED**, not rejected. BLOCK32 remains **REJECTED**.

## RESUME HERE — E2 confirmed 2026-09-17

1. Integrated `master` remains `a2270699...`; active performance 2A remains `989e1f5b...`; E2 diagnostic HEAD is now **`e2ac0c29...`** with both Build/Validate and APU Cycle/Span Proof green. No open PR is implied.
2. Treat E2 as two validated correctness findings: **instruction-cycle under-accounting for tested NOP/MUL/DIV/BRA paths**, and **NOP-driven overlong blocks that can miss intermediate tag invalidation and re-enter stale code**.
3. Next technical batch: create a **separate NOP-bound correctness candidate** from the safe BLOCK16 tree, change only NOP dispatch to obey `finish_opcode`, rerun the long-NOP span/middle-tag proof, and reject if it alters unrelated semantics or still permits >2 tag regions.
4. After that checkpoint, derive and implement the **smallest instruction/path-specific timing correction candidate** supported by the pinned SPC700 reference. Do not globally change `apu_clock`; do not combine timing correction with memory/JIT optimizations.
5. Before performance-ranking any resulting candidate, add the minimal matched-window E1 measurement boundary and establish a fresh baseline. Fidelity/cycle equivalence is required before any speed claim.
6. E3 low-read helper, E4 validation specialization and E5 DSP invariant hoist remain candidates only after timing semantics are on firmer ground. No second emulator, no RSP offload, no scope reduction, no cartridge-assistance pivot.


## NOP-bound candidate running — checkpoint 2026-09-17

Clean one-variable candidate **`phase2/apu-nop-bound-fix@fe5fcc0ca7b817a99095dcde40dc9d37d54d4a18`** starts from safe BLOCK16 tree `225859b1...`. Its only runtime change is opcode `0x00` NOP dispatch in `src/apu_emitter.S`: `next_opcode -> finish_opcode`. No cycle-timing correction is bundled.

Diagnostic child branch **`phase2/apu-nop-bound-proof@0eb17e80fc255bca61c021936b1d040abd87ceb4`** contains only the directed proof script/workflow on top of the clean candidate.

Runs currently in progress:
- candidate Build/Validate **`35283138453`** on exact `fe5fcc0c...`;
- child Build/Validate **`35283273619`** on exact `0eb17e80...`;
- directed **APU NOP Bound Proof `35283273808`** on exact `0eb17e80...`.

Directed question: starting at PC `0x0238` with a long NOP stream, does the clean candidate stop compilation after exactly 16 source bytes at PC `0x0248`, track only tag regions 8->9, and then reject/recompile the old block after an actually covered byte in region 9 is mutated and its tag incremented?

Acceptance requires all three:
- `nop_bound_enforced=true`;
- `bounded_block_tracks_only_two_regions=true`;
- `covered_end_tag_prevents_stale_reentry=true`.

Falsifier: any >16-byte compiled span, unexpected tag-region coverage, or re-entry into the old generated block after the covered end-region tag mutation. If falsified, do not broaden the fix until the exact mechanism is identified.

Do not merge or performance-rank this candidate while the proof is running. Cycle-timing design may proceed from the already-confirmed E2 evidence but remains a separate future candidate.


## SPC700 timing-contract design checkpoint — 2026-09-17

Source audit after E2 establishes the implementation boundary for the future timing correction:

- Across `apu_emitter.S`, `apu_address.S`, `apu_alu.S`, `apu_control.S` and `apu_transfer.S`, the inherited JIT has no general cycle debit beyond:
  1. `jit_read8`: one `apu_clock` per opcode/operand byte fetched at compile time into `s2`;
  2. runtime `apu_read8/apu_write8`: one `apu_clock` per emitted data access into `s3`.
  This explains the E2 measurements structurally: internal/dummy cycles are not hidden elsewhere.

- The pinned ares reference distinguishes several kinds of additional cycles. Many are `idle()`, but many are actual dummy `read(...)` operations (for example NOP performs `read(PC)`; multiple write/implied/control forms also issue reads). A cycle-only debit is therefore not automatically full bus/I/O fidelity. Future work must distinguish **fetch / real data read-write / dummy read / idle**, and preserve ordering when I/O can be touched.

- Conditional branch timing cannot be represented solely by a compile-time fixed debit. In the pinned reference, generic Branch fetches displacement and adds two `idle()` only when taken. Any Sodium64 correction must therefore put taken-only cycles on the emitted taken path rather than charging both outcomes.

- **OPEN QUESTION / source-supported risk:** `menu_close` changes `apu_clock` and sets `jit_pointer = ROM_BUFFER` but does not immediately clear `jit_lookup`. Existing generated blocks already embed their fetch-cycle debit, so a cached block may retain the prior clock value until a later JIT miss reaches `reset_buffer` and clears lookup. This predates the proposed timing work. Do not conflate it with the cycle correction; test/fix separately if the timing candidate depends on clock-setting transitions.

**Architecture direction:** do not use a global `apu_clock` scale and do not add one fixed “cycles per opcode” table that erases bus semantics. Build the timing contract from the exact pinned reference and Sodium64's emitted-access behavior, with constant internal cycles and runtime-conditional cycles represented separately. Dummy reads that can have observable I/O effects require semantic treatment, not just time debit.


## Correction — timed GDB SIGTRAP is not breakpoint identity (2026-09-17)

The first NOP-bound proof exposed a flaw in the diagnostic interpretation used by both the old E2 middle-region probe and the new candidate probe.

ares returns `S05` both for the directed software-breakpoint stops **and for the debugger Ctrl-C stop generated by `continue_then_interrupt()`**. The proof logs themselves demonstrate this: the warmup stop, which is explicitly a timed debugger interrupt, reports `S05`. Therefore `signal_number(reply) == 5` after `continue_then_interrupt(0.5)` does **not** prove that the armed code-entry breakpoint was hit.

**SUPERSEDED:** the earlier literal claim that E2 dynamically proved stale-block re-entry *because* the old-code breakpoint returned SIGTRAP. That breakpoint-identity criterion was invalid.

What remains valid from E2:
- **MEASURED:** the inherited long-NOP block compiled 128 source bytes and spanned header tag regions 8->10.
- **MEASURED:** mutating only covered middle region 9 left start/end tags untouched.
- **STATIC + MEASURED SUPPORT:** `apu_execute` validates only the two header endpoint tags, so this state is sufficient for the old block to pass current validation. Lookup/JIT-pointer also remained unchanged across the old timed probe, but the old SIGTRAP field itself is not authority.
- Final dynamic re-entry confirmation will be rerun without timed-stop ambiguity: after mutation, continue from the safe `apu_execute` boundary to the **first `cpu_execute` return**, then inspect whether lookup/JIT pointer changed. Unchanged means the old block executed; changed means recompilation occurred.

The clean NOP-bound candidate itself was **not falsified** by run `35283273808`; its first two directed properties passed:
- `source_clock_units = 16`;
- PC after block `0x0248`;
- header regions **8->9**.

After mutating the tracked end region 9, the same run measured:
- lookup changed `2149318676 -> 2149318708`;
- JIT pointer advanced `2686189620 -> 2686319648`.

Those measurements are consistent with successful invalidation/recompilation. The run failed only because the invalid `sig==5` criterion marked the timed debugger stop as old-block re-entry. **HYPOTHESIS:** `fe5fcc0c...` fixes the NOP-bound/invalidation defect as intended. Rerun with a first-`cpu_execute` boundary before promoting to VALIDATED.


## Deterministic invalidation reruns running — checkpoint 2026-09-17

The ambiguous timed-SIGTRAP criterion has been removed from both directed probes.

### NOP-bound candidate rerun
Diagnostic child HEAD: **`phase2/apu-nop-bound-proof@200aef5e9d90d739dc00f9250678eb31919a3512`**.
Clean runtime candidate remains unchanged: **`phase2/apu-nop-bound-fix@fe5fcc0ca7b817a99095dcde40dc9d37d54d4a18`**.

Current runs:
- APU NOP Bound Proof **`35283857525`** IN PROGRESS;
- Build and Validate **`35283857526`** IN PROGRESS.

New invalidation method: mutate the tracked end-tag at a safe `apu_execute` boundary, then continue to the **first `cpu_execute` return**. At that boundary exactly one APU block has completed. Lookup/JIT-pointer changed = recompilation before execution return; unchanged = cached block reused. No wall-time/SIGTRAP identity is used.

### Original E2 middle-tag rerun
Corrected diagnostic HEAD: **`phase2/apu-cycle-proof@30be54899133f518b52ca3ba1ddce00070ac812f`**.

Current runs:
- APU Cycle And Span Proof **`35283897586`** QUEUED;
- Build and Validate **`35283897497`** QUEUED.

It repeats the inherited 128-byte long-NOP case, mutates only middle tag region 9 while endpoint tags 8/10 remain untouched, then continues to the first `cpu_execute` return. Unchanged lookup/JIT pointer at that deterministic boundary dynamically confirms stale reuse; changed values falsify the prior dynamic interpretation.

Do not promote/reject the NOP candidate or restate dynamic stale re-entry as VALIDATED until these corrected runs finish.


## SPC700 timing scope sharpened — 2026-09-17

Independent cycle-count cross-check:
- pinned ares implementation remains the primary instruction/bus-sequence reference: `ares@17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`;
- second source checked: `gufranco/sony-spc700-python@50fbd2fb8f4ad8743fc1bca090a7968e25d30a9e`, MIT, whose `conformance/hardware.json` transcribes the Nintendo development-manual Appendix C instruction tables.
- machine check of that pinned hardware table: **17 tables, 256 rows, 256 unique opcode codes, zero duplicates, zero missing opcodes**.
- **28 opcodes have conditional cycle totals**: the eight normal conditional branches, BBS/BBC families, CBNE forms and DBNZ forms. The other **228 opcodes have fixed total cycle counts** in the hardware table.
- `gilyon/snes-tests@5ecdf555da920f0bd7b157542141965a8120186d` is MIT and comprehensive for SPC700 opcode/register/memory semantics, but its own README explicitly says it does **not** test cycle count, dummy reads, S-SMP I/O registers or DSP. Use it later as a semantic-regression guard, not as timing authority.
- SingleStepTests/ProcessorTests contains cycle-by-cycle bus vectors but declares no repository license; do not vendor or make CI depend on its data without a licensing decision.

### Two timing layers must not be conflated

**Layer 1 — total instruction-cycle correctness.**
This is the immediate correction target. Sodium64 currently charges instruction/operand fetch bytes at compile time plus emitted data reads/writes at runtime and omits other cycles. Fixed internal cycles can be represented by compiler-side debit; the 28 conditional branch families need taken-path runtime debit. Existing E2 snippets are an excellent architecture proof: after correction, BRA must be 4 units, NOP+BRA 6, MUL+BRA 13, DIV+BRA 16.

**Layer 2 — intra-block bus/I/O temporal ordering.**
This is a separate accuracy problem. Sodium64 batches `jit_read8` fetch-cycle debt into the generated block-end `ADDI s3,s3,imm`, while runtime data accesses debit `s3` at the access point. Timer reads `read_t0out/read_t1out/read_t2out` compare overflow timestamps directly against current `s3`. Therefore even correct *total* instruction cycles do not automatically prove exact timer/I/O timing inside a multi-instruction JIT block. Dummy reads also need semantic treatment when they can touch I/O.

**Decision:** implement/validate total-cycle correctness first and measure its effect, but label it honestly. Do not claim full SPC700 cycle-accurate I/O until Layer 2 has its own directed tests and solution. This is accuracy debt within Sodium64, not a reason to build a second emulator.


## Layer-1 total-cycle architecture proof running — checkpoint 2026-09-17

Separate experimental runtime branch **`phase2/apu-total-cycle-proof@b268b98b9cf83a9d13a5c59c49c0bd4c585caef8`** was created from the clean NOP-bound candidate `fe5fcc0c...`. It is contingent on the corrected NOP-bound proof and must not be promoted if that parent is falsified.

Runtime changes are deliberately limited to the four already-measured E2 paths:
- compiler-side primitive `jit_debit_cycles` subtracts `apu_clock` from compile-time block debt `s2` once per requested extra guest cycle;
- NOP charges +1 extra cycle;
- BRA charges +2 extra cycles;
- MUL charges +8 extra cycles beyond opcode fetch;
- DIV charges +11 extra cycles beyond opcode fetch.

This is **Layer-1 total-cycle accounting only**. It deliberately does not model NOP/MUL/DIV dummy `read(PC)` bus activity or exact intra-block timer/I/O ordering.

Diagnostic child branch **`phase2/apu-total-cycle-validate@215dc67722462f1fd768e58471ca599cdaf699cf`** adds only the directed GDB proof/workflow.

Current runs:
- APU Total Cycle Proof **`35284371466`** QUEUED;
- child Build and Validate **`35284371446`** PENDING.
(The intermediate child Build/Validate `35284345625` may be superseded/cancelled by the final workflow commit.)

Acceptance is exact and inherited from E2:
- BRA must debit **4** guest cycle units;
- NOP+BRA must debit **6**;
- MUL+BRA must debit **13**;
- DIV+BRA must debit **16**;
- all four must be observed from the exact generated JIT block at the first `cpu_execute` return.

Falsifier: any total differs, generated block lacks a unique `ADDI s3,s3,imm` debit, or Build/Validate fails. A pass validates only the debit primitive and these four paths, not the remaining 252 opcodes and not Layer-2 bus/I/O timing.


## Deterministic invalidation proofs complete — VALIDATED 2026-09-17

The corrected first-`cpu_execute` reruns removed the old timed-SIGTRAP ambiguity and now dynamically settle both sides of the NOP block-bound defect.

### Inherited baseline defect — VALIDATED

Exact diagnostic HEAD: **`phase2/apu-cycle-proof@30be54899133f518b52ca3ba1ddce00070ac812f`**.

Exact CI:
- **APU Cycle And Span Proof `35283897586` SUCCESS**;
- **Build and Validate `35283897497` SUCCESS**.

Inherited long-NOP block:
- 128 source clock units;
- header tag regions **8 -> 10**;
- therefore exceeds nominal `BLOCK_SIZE=16` and spans three 64-byte tag regions.

After changing an actually covered byte in middle region 9 and incrementing only tag 9, while endpoint tags 8/10 remained untouched, then continuing from a safe `apu_execute` boundary to the **first `cpu_execute` return**:
- lookup before/after: **2149318676 -> 2149318676** (unchanged);
- JIT pointer before/after: **2686189652 -> 2686189652** (unchanged);
- `recompiled_before_first_cpu_return = false`;
- `stale_block_reused_without_recompile = true`.

**VALIDATED:** the inherited NOP path can exceed the nominal block bound; endpoint-only validation then misses a covered intermediate-tag mutation and executes the cached stale generated block.

### One-line NOP-bound fix — VALIDATED

Clean runtime candidate remains **`phase2/apu-nop-bound-fix@fe5fcc0ca7b817a99095dcde40dc9d37d54d4a18`**, based on safe `225859b1...`. Its sole runtime change is opcode 0x00 dispatch `next_opcode -> finish_opcode`.

Exact corrected diagnostic HEAD: **`phase2/apu-nop-bound-proof@200aef5e9d90d739dc00f9250678eb31919a3512`**.

Exact CI:
- **APU NOP Bound Proof `35283857525` SUCCESS**;
- child **Build and Validate `35283857526` SUCCESS**;
- clean candidate Build/Validate had already passed on `fe5fcc0c...`.

Measured:
- test PC `0x0238`;
- long source payload remains 128 bytes, but generated block debits exactly **16 source clock units**;
- PC after block **0x0248**;
- header regions **8 -> 9**;
- `nop_bound_enforced = true`;
- `bounded_block_tracks_only_two_regions = true`.

After mutating an actually covered byte at `0x0240` in tracked end region 9 and incrementing tag 9, then continuing to the first `cpu_execute` return:
- lookup **2149318676 -> 2149318708**;
- JIT pointer **2686189620 -> 2686189672**;
- `recompiled_before_first_cpu_return = true`;
- `stale_block_reused_without_recompile = false`;
- `covered_end_tag_prevents_stale_reentry = true`.

**VALIDATED:** `fe5fcc0c...` fixes this specific internal JIT block-bound/invalidation defect with the intended one-line runtime change.

**Scope:** this does not prove every possible generated block is limited to at most two tag regions; other opcode generators can still terminate/bypass differently and require separate reasoning if future evidence points there. It does prove the concrete NOP bypass defect found by E2 and its stale-invalidation consequence.

### Decision

- Promote `fe5fcc0c...` from HYPOTHESIS/CANDIDATE to **VALIDATED** for this defect.
- Keep it separate from SPC700 timing corrections; do not bundle the correctness proof harness into the runtime commit.
- The Layer-1 total-cycle architecture proof may now legitimately use `fe5fcc0c...` as its parent.
- No throughput gain is claimed; E1 matched-window repair remains mandatory before performance ranking.


## Integration hygiene correction — NOP fix rebased cleanly onto master (2026-09-17)

Attempted integration PR **#11** from historical branch `phase2/apu-nop-bound-fix@fe5fcc0c...` exposed a Git-history problem before merge: GitHub reported **27 commits / 8 changed files / +1353 -1** versus current `master@a2270699...`. The runtime NOP change itself remained the validated one-line fix, but the historical safe-tree branch is not a clean integration base relative to current master.

**PR #11 was CLOSED / SUPERSEDED without merge.** Nothing from it entered master.

A new clean integration candidate was created directly from exact current master:
- branch **`phase2/apu-nop-bound-master`**;
- candidate SHA **`eaad08de0f0cc09bada7fe5093c9e8bd5fe3455b`**;
- base **`master@a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`**.

GitHub compare is exact:
- ahead by **1**;
- behind by **0**;
- total commits **1**;
- changed files **1**: `src/apu_emitter.S`;
- diff **+1/-1** only: opcode 0x00 dispatch `next_opcode -> finish_opcode`.

**State:** `fe5fcc0c...` remains the SHA on which the corrected directed proof established the behavior, but it is **SUPERSEDED FOR INTEGRATION** by `eaad08de...`. Because code layout/base changed, rerun the directed NOP proof on a diagnostic child of `eaad08de...` before opening the replacement PR. Do not merge based solely on equivalence of the one source line.


## Active reruns after clean-master integration correction — checkpoint 2026-09-17

### Clean-master NOP fix
Runtime candidate: **`phase2/apu-nop-bound-master@eaad08de0f0cc09bada7fe5093c9e8bd5fe3455b`** (exactly one +1/-1 source line over `master@a2270699...`).

Diagnostic child: **`phase2/apu-nop-bound-master-proof@b89345498664f126049c482c5d54b49c3268bfdd`**.

Current runs:
- clean candidate Build and Validate **`35284543571`** IN PROGRESS;
- directed APU NOP Bound Proof **`35284584269`** IN PROGRESS;
- diagnostic-child Build and Validate **`35284584261`** pending/in progress as GitHub schedules it.

Question/acceptance is unchanged from the already-validated historical-tree proof: exact 16-unit block from PC 0x0238, header 8->9, and tracked end-tag mutation must cause recompilation before first `cpu_execute`. Only after this passes should a replacement integration PR be opened.

### Layer-1 total-cycle proof
Runtime architecture candidate **`phase2/apu-total-cycle-proof@b268b98b9cf83a9d13a5c59c49c0bd4c585caef8`** has now passed **Build and Validate `35284214442` SUCCESS**.

Diagnostic child remains **`phase2/apu-total-cycle-validate@215dc67722462f1fd768e58471ca599cdaf699cf`**:
- child Build and Validate **`35284371446` SUCCESS**;
- directed APU Total Cycle Proof **`35284371466` IN PROGRESS**.

Do not generalize the timing mechanism until the directed totals are observed as exactly BRA=4, NOP+BRA=6, MUL+BRA=13, DIV+BRA=16.


## Layer-1 total-cycle architecture proof — VALIDATED for four paths 2026-09-17

Experimental runtime HEAD: **`phase2/apu-total-cycle-proof@b268b98b9cf83a9d13a5c59c49c0bd4c585caef8`**.
Diagnostic child HEAD: **`phase2/apu-total-cycle-validate@215dc67722462f1fd768e58471ca599cdaf699cf`**.

Exact CI:
- runtime **Build and Validate `35284214442` SUCCESS**;
- child **Build and Validate `35284371446` SUCCESS**;
- **APU Total Cycle Proof `35284371466` SUCCESS**.

Exact generated-block measurements at `apu_clock=21`:
- BRA: debit **-84 = 4 guest cycle units**, expected 4;
- NOP+BRA: debit **-126 = 6 units**, expected 6;
- MUL+BRA: debit **-273 = 13 units**, expected 13;
- DIV+BRA: debit **-336 = 16 units**, expected 16;
- `all_total_cycle_cases_match = true`.

**VALIDATED / ARCHITECTURE PROOF:** a compiler-side extra-cycle debit can represent the missing Layer-1 total guest cycles for the tested fixed/taken paths without changing memory fast paths. The four E2 mismatches are corrected exactly by this mechanism.

**Not proven / scope:** this does not validate the remaining 252 opcodes, conditional branch taken/not-taken handling, dummy-read bus effects, timer/I/O ordering, or any performance gain. It is Layer-1 total-cycle accounting only.

**Integration hygiene:** `b268b98b...` descends from the historical safe-tree NOP candidate `fe5fcc0c...`, whose Git history was later shown not to be a clean current-master integration base. Therefore `b268b98b...` is **VALIDATED AS AN ARCHITECTURE PROOF ONLY / NOT AN INTEGRATION CANDIDATE**. Reapply the mechanism on the clean current-master line after the clean NOP candidate `eaad08de...` is revalidated/merged, then rerun this proof before any PR.

### Next timing batch

Generalize Layer-1 timing by **semantic families**, not 256 ad-hoc fixes:
1. preserve fixed-cycle totals with compiler-side debt;
2. implement the 28 conditional opcode families with taken-path-only extra debit;
3. keep existing runtime data-access debits intact;
4. separately preserve/defer dummy-read and intra-block I/O semantics as Layer 2;
5. validate against the complete 256-opcode Nintendo cycle table, with targeted dynamic proof before performance interpretation.

Do not performance-rank until E1 matched-window measurement is repaired.


## Compatibility finding from 256-opcode audit — 2026-09-17

Crossing current `master`'s `jit_opcodes` table against the complete 256-opcode hardware table exposed a separate non-timing compatibility hole:

- opcode **0xBE = DAS A** maps to `apu_unk`;
- opcode **0xDF = DAA A** maps to `apu_unk`;
- `apu_unk` explicitly emits code that leaves the SPC700 PC on the unimplemented opcode, effectively looping there.
- opcodes **0xEF = SLEEP** and **0xFF = STOP** also map to `apu_unk`, but these are special control states and need their own semantics; do not conflate them with DAA/DAS.

**VALIDATED / static source finding:** DAA and DAS are legal SPC700 instructions but are currently unimplemented in Sodium64. This is a **COMPATIBILITY PROOF / REQUIRED SUPPORT** issue for the 1.0 accuracy target, independent of the current Layer-1 timing correction.

Do not bundle DAA/DAS implementation into the active NOP-bound integration or four-path total-cycle proof. Add directed semantic tests before implementation, using pinned ares plus an independent opcode semantic reference where licensing permits.


## E2 dynamic proof — CONFIRMED 2026-09-17

**MEASUREMENT PROOF / ARCHITECTURE PROOF.** The source-backed SPC700 timing and JIT-span risks were dynamically reproduced without modifying the APU core.

Authority run: **APU Cycle And Span Proof `35283897586`**, exact diagnostic SHA **`30be54899133f518b52ca3ba1ddce00070ac812f`**, jobs `105411838100` + `105412186149`, result artifact **`10523267264`** (digest `sha256:cdd4f4f47d23a59c47b851ea520dc169d59610cd5cea2412805f85c344bcdc69`). Exact proof build artifact **`10523307069`** (digest `sha256:300306b450239f895f20fad59483b5be801cba5d1f0e57280eef7849a124699c`).

Direct compare `225859b1... -> 30be5489...` is diagnostic-only: `.github/workflows/apu-cycle-proof.yml`, `scripts/apu_cycle_proof.py`, and `src/apu_cycle_diag.S`. **No APU/JIT production source is changed by the measured SHA.**

### E2-A — MEASURED: inherited SPC700 instruction timing under-accounting is real

Dynamic generated-code inspection reproduced the exact source-predicted debit at `apu_clock=21`:

| snippet | Sodium64 charged clock units | independent SPC700 reference cycles |
| --- | ---: | ---: |
| BRA | 2 | 4 |
| NOP + BRA | 3 | 6 |
| MUL + BRA | 3 | 13 |
| DIV + BRA | 3 | 16 |

Exact emitted debits were BRA `-42`, NOP+BRA `-63`, MUL+BRA `-63`, DIV+BRA `-63`. The generated blocks returned to the expected PCs and the emitted `ADDI s3,s3,imm` matched the static accounting prediction in every case.

**CONFIRMED:** configured `apu_clock=21` is NOT equivalent to instruction-accurate full-rate SPC700 timing. The inherited JIT omits instruction-internal/taken-branch timing work for the tested opcodes. This is a correctness defect, not merely a profiler attribution issue.

**SUPPORTED INTERPRETATION:** correcting guest timing can plausibly reduce excess SPC700 host work while improving fidelity, because Sodium64 currently advances more SPC700 instructions per emulated-time budget than these reference timings permit. The magnitude on Gothicvania remains UNKNOWN until a correctness candidate exists and is measured. Do not apply a single global clock multiplier; the discrepancy is instruction-specific.

### E2-B — MEASURED: BLOCK_SIZE=16 is not a universal generated-block bound

The long diagnostic snippet `126*NOP + DBNZ Y,-128` compiled as one **128-source-byte** block. Header coverage was region **8 -> 10**, despite nominal `BLOCK_SIZE=16`. Emitted debit was `-2688` = 128 configured clock units.

This dynamically confirms the NOP bypass: opcode `0x00` dispatches directly to `next_opcode` and therefore skips the `finish_opcode` limit check.

### E2-C — MEASURED: endpoint-only tag validation can reuse stale generated code

After compiling the three-region block, the proof mutated an actually covered byte in middle region **9** and incremented that region's JIT tag exactly as `apu_write8` would. Start/end region tags were left unchanged.

On the next safe APU re-entry:
- lookup pointer unchanged;
- JIT pointer unchanged;
- no recompile occurred before the first `cpu_execute` return;
- **stale generated block was reused.**

Therefore the inherited two-endpoint validation is insufficient whenever a generated block spans an untracked intermediate 64-byte region.

### Decision

**E2 is closed as CONFIRMED, not hypothesis.** The immediate M1 route changes again:

1. First make a **minimal block-bound correctness candidate** so every ordinary NOP also passes the existing `finish_opcode` boundary check. Before accepting it, prove no other opcode path can similarly bypass the bound and rerun the long-span/middle-tag proof.
2. Then design an instruction-accurate SPC700 timing model. Do not patch only NOP/MUL/DIV/BRA as a permanent architecture and do not globally scale `apu_clock`; derive/validate the missing internal and conditional cycles systematically against an independent reference.
3. After timing correction, establish a fresh correctness/performance baseline; old 44/48/52/61 ares totals are not directly comparable as “full-rate” performance because the guest timing contract was wrong.
4. E3 low-read, E4 validation specialization and E5 DSP invariant work remain **DEFERRED** until the corrected timing/block contract exists. A performance optimization of an over-executing guest is currently lower value than fixing the guest-time definition itself.

The current diagnostic branch moved after the authority run for additional PROFILE-only cross-check instrumentation; do not confuse those later diagnostic commits with the measured authority SHA `30be5489...`.

## RESUME HERE — E2 confirmed / correctness-first pivot 2026-09-17

1. Integrated `master` remains **`a2270699...`**. Safe M1 tree remains **`225859b1...`**. E2 authority is diagnostic SHA **`30be5489...`**, run **`35283897586`**, not the later diagnostic HEAD.
2. **CONFIRMED:** tested SPC700 opcodes are undercharged in guest cycles; `apu_clock=21` alone does not prove full-rate timing.
3. **CONFIRMED:** long NOP sequences can bypass `BLOCK_SIZE=16`, span 3 tag regions, and a middle-region tag mutation can reuse stale generated code because cached validation checks only endpoint tags.
4. Next controlled change: prove the NOP path is the only direct `next_opcode` bypass, then test a minimal NOP->`finish_opcode` block-bound fix on the diagnostic harness. If it restores <=16-byte span and removes the middle-region stale-reuse condition without semantic regression, recreate it as a clean code-only candidate from the safe tree.
5. In parallel, map the complete SPC700 missing-cycle contract from the pinned independent reference before implementing timing correction. Prefer a systematic model of internal/conditional cycles over per-game or global-clock hacks.
6. After correctness candidates, create a fresh matched-window baseline (E1 repair remains required) before ranking small throughput deltas.
7. 2B/E3, E4, E5 are **DEFERRED**. BLOCK32 remains REJECTED. No 65C816 dynarec/RSP offload/second emulator/cartridge assist is justified by this evidence.


## M1 block-bound correction — dynamic validation 2026-09-17

**VALIDATED in diagnostic harness.** The one-variable core change maps SPC700 NOP opcode `0x00` from direct `next_opcode` dispatch to the existing `finish_opcode` path, so NOP now obeys the same `BLOCK_SIZE` check as every other ordinary opcode.

Diagnostic branch HEAD for the proof: **`9880e2e146d3e48f9f7819654e792ae302bee275`**. The production-semantic change itself is commit **`31ad646a1221e7b55cc9a1efa4f2c74354049f73`**; later commits only adjust the proof expectations/reporting. Build and Validate **`35287658874` SUCCESS**.

Dynamic authority: **APU Cycle And Span Proof `35287658903` SUCCESS**, cycle-proof job **`105423781476`**, result artifact **`10525480018`** digest `sha256:2d7d1d311cf38bd9b5a2d7e82a70ae4cca63ed07d9795d8c197b0170731a4c5c`; exact proof-build artifact **`10524349509`** digest `sha256:c185e321272c28dc2ded529863e6a1521c52ea3d2e07073e617d640a04ecafc2`.

The same 128-byte source probe that previously compiled across regions 8->10 now produced:
- `cycle_debit=-336` = **16 configured clock units**;
- `apu_count_after_block=0x0210`, exactly 16 source bytes after `TEST_PC=0x0200`;
- JIT header start/end region **8 -> 8**;
- generated block 20 bytes;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`;
- middle-region mutation probe **not applicable**, because the bounded block no longer contains an untracked intermediate tag region.

BRA/NOP+BRA/MUL+BRA/DIV+BRA retained their previous under-accounted timing observations, proving the block-bound fix did not accidentally alter the separate timing defect.

Source-wide search found no other opcode-table/generator path that directly jumps to `next_opcode`; NOP was the only opcode bypassing `finish_opcode`. Therefore the narrow fix closes the dynamically demonstrated multi-region endpoint-tag stale-code condition for the audited path without changing tag architecture.

**Decision:** preserve this as a clean code-only candidate from safe tree `225859b1...`; do not carry PROFILE instrumentation/workflow changes into the candidate. Timing correctness remains the next gate driver.

## RESUME HERE — block bound validated / timing contract next

1. `master` remains `a2270699...`. E2 under-accounting authority remains `30be5489...` / run `35283897586`.
2. NOP block-bound fix is **VALIDATED in diagnostic harness** by run `35287658903`: 128-byte source probe is now bounded to 16 bytes/one tag region; the previously reproduced middle-tag stale-code condition cannot arise in that probe.
3. Create/verify a clean branch from `225859b1...` containing ONLY the NOP table mapping `next_opcode -> finish_opcode`; normal Build/Validate must pass. Keep diagnostic machinery out of the code candidate.
4. Then continue timing correctness. Current evidence says the inherited timing model undercharges not only internal idles but also dummy bus cycles; a global `apu_clock` scale is REJECTED as architecture.
5. Preferred timing direction: retain current data-access timing initially, add missing guest-cycle charges systematically by shared addressing/operation/control families, and emit conditional extra cycles for taken branches. Validate total cycles first, then refine I/O/timer cycle placement where needed.
6. A pinned independent cycle table agrees with ares for audited NOP/BRA/MUL/DIV values and can serve as host-test oracle/supporting evidence; ares dynamic semantics remain the primary independent reference.
7. E1 matched-window repair remains required before small performance ranking. E3/E4/E5 remain DEFERRED until timing contract is corrected enough to establish a new baseline.


## Clean block-bound candidate — CI validated 2026-09-17

Clean candidate branch **`phase2/apu-block-bound-fix@7e48bcc994483e7aaf7cc2793b03fe0ebf13ee84`** was recreated directly from safe tree `225859b1d8fc0eb477a624ac76f8237667379f59`.

Direct compare is exactly one file, **`src/apu_emitter.S +1/-1`**: opcode `0x00` NOP maps from `next_opcode` to `finish_opcode`. No diagnostic source, workflow, profiler or other runtime code is present.

**Build and Validate `35288085787` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.
Normal build artifact ID `10524987296`; PROFILE build artifact ID `10524444940`.

Combined with dynamic ares proof `35287658903`, this candidate is **VALIDATED** for the demonstrated block-bound/stale-middle-tag defect. It is not yet merged; keep it as the clean base for APU timing-correctness work so timing can be tested without reintroducing the NOP span bug.

### Timing-model design constraint learned during the same batch

Pinned ares reference confirms the missing timing is structurally regular, not just MUL/DIV special cases:
- indexed addressing introduces idle cycles;
- pure stores perform dummy/read-before-write cycles;
- many implied/register operations perform a dummy `read(PC)`;
- conditional taken branches add two cycles;
- MUL/DIV/XCN and similar operations have internal cycles.

Sodium64 currently batches opcode/operand fetch debits in compile-time `s2` and emits that debit at block end, while `apu_read8/apu_write8` debit data accesses at runtime. Timer/control paths observe `s3`; therefore the first correction should **preserve existing data-access debit placement** and add only missing guest cycles. This minimizes semantic movement while making total instruction timing correct. Exact intra-instruction bus-cycle placement remains a later fidelity refinement, not something to silently claim from the first timing candidate.

## RESUME HERE — clean block fix validated; timing proof mechanism next

1. `master` remains `a2270699...`. Clean block-bound candidate is **`phase2/apu-block-bound-fix@7e48bcc9...`**, one-line core diff, Build/Validate `35288085787` SUCCESS.
2. Dynamic authority for the block fix remains diagnostic run `35287658903`: long probe bounded to 16 source bytes / one tag region.
3. Next technical batch: on diagnostic `phase2/apu-cycle-proof`, introduce one shared compile-time mechanism for **missing guest cycles** and exercise it only on the already-audited NOP/BRA/MUL/DIV cases. Expected corrected sequence totals: BRA4, NOP+BRA6, MUL+BRA13, DIV+BRA16; 16 NOPs should debit32 cycles while still ending after16 source bytes.
4. This four-opcode step is a **mechanism proof, not the permanent timing coverage**. If validated, recreate the mechanism cleanly from `7e48bcc9...` and expand systematically by shared addressing/operation/control families plus runtime conditional charges for taken branches.
5. Do not remove `apu_read8/write8` timing debits yet. Do not globally scale `apu_clock`. Do not claim exact intra-instruction I/O timing until dedicated timer/port tests prove it.
6. E1 matched-window repair remains necessary before ranking small performance changes. E3/E4/E5 remain DEFERRED.


## Timing mechanism proof in progress — checkpoint 2026-09-17

Diagnostic branch **`phase2/apu-cycle-proof@842a14127669ce176c808ddcd718d0987d351223`** now contains a bounded mechanism proof for missing SPC700 guest cycles. This is NOT full timing coverage and is not a merge candidate.

Controlled semantic changes relative to the prior bounded-NOP diagnostic:
- shared compile-time helper `jit_charge_cycles(t0)` converts a count of missing SPC700 cycles into `apu_clock` master-cycle debit accumulated in JIT compiler `s2`;
- NOP charges +1 missing cycle then reaches `finish_opcode`;
- BRA charges +2 missing cycles;
- MUL charges +8 missing cycles;
- DIV charges +11 missing cycles;
- existing `apu_read8/apu_write8` runtime data-access debits are unchanged.

Expected audited totals at `apu_clock=21`:
- BRA: 4 guest cycles / debit `-84`;
- NOP+BRA: 6 / `-126`;
- MUL+BRA: 13 / `-273`;
- DIV+BRA: 16 / `-336`;
- 16 compiled NOPs from the 128-byte source probe: 32 guest cycles / `-672`, while source span must remain exactly 16 bytes and header region 8->8.

**Build and Validate `35288358663` SUCCESS** for exact SHA `842a1412...`: normal build, PROFILE build and pinned Mupen emulator smoke all green.

**Long experiment in progress:** APU Cycle And Span Proof **`35288358655`**, profile-build already SUCCESS; cycle-proof job **`105425907529`** is currently building pinned ares before executing the dynamic cases.

Question: does one shared compile-time missing-cycle mechanism reproduce independent SPC700 total cycles for the four already-audited fixed-cycle cases without undoing the validated NOP block bound?

Readings:
- all exact debits + 16-byte bound pass => mechanism **VALIDATED only for these audited fixed-cycle cases**; proceed to one separate addressing-family timing batch;
- debit mismatch => inspect helper/accounting composition, do not expand coverage;
- PC/span/header mismatch => reject mechanism as semantically intrusive;
- smoke/proof regression => reject candidate.

Do not interpret performance from this run. E1 matched-window measurement repair remains required for later throughput comparison.


## SPC700 missing-cycle mechanism — VALIDATED for audited fixed-cycle cases 2026-09-17

Exact diagnostic SHA: **`842a14127669ce176c808ddcd718d0987d351223`**.

**Build and Validate `35288358663` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.

Dynamic authority: **APU Cycle And Span Proof `35288358655` SUCCESS**, cycle-proof job **`105425907529`**.
- proof result artifact **`10525930543`**, digest `sha256:93adfb95e6ea06efa38d5ed2723f562b229544ec47d8d62e17930528b0a78832`;
- exact proof-build artifact **`10524814779`**, digest `sha256:48d4ac8e9d9a85b99aaa8a7478b9b2397b325f4fc8ec7b4066aa63eed11f022c`.

Measured generated JIT debit at `apu_clock=21`:
- BRA: **`-84` = 4 guest cycles**, reference 4;
- NOP+BRA: **`-126` = 6**, reference 6;
- MUL+BRA: **`-273` = 13**, reference 13;
- DIV+BRA: **`-336` = 16**, reference 16;
- 16 compiled NOPs from the 128-byte source probe: **`-672` = 32 guest cycles**, PC `0x0200 -> 0x0210`, header 8->8.

All static debit expectations and all span expectations passed. Middle-region stale-code probe remained not applicable because the block stayed within one tag region.

**VALIDATED scope:** the shared compile-time `jit_charge_cycles` mechanism can add missing fixed guest cycles without disturbing the demonstrated JIT block bound for these audited cases.

**NOT YET PROVEN:** complete SPC700 cycle coverage, taken/not-taken conditional timing, exact intra-instruction I/O/timer bus timing, or performance impact. Do not merge a four-opcode-only timing correction as if it were complete.

### Decision
Proceed with timing coverage by **shared addressing families first**, using the same mechanism and preserving existing runtime `apu_read8/apu_write8` data-access debits. For that batch, measure the actual R4300 `s3` delta from `compile_block` entry to the first `cpu_execute` return, so reference totals include both compile-time debit and runtime memory-helper debit.

Representative matrix should cover at least:
- direct read vs direct write;
- direct indexed read vs write;
- (X) read vs write;
- (X)+ read/write;
- absolute read vs write;
- absolute indexed read vs write;
- indexed-indirect read vs write;
- indirect-indexed read vs write.

Expected missing-cycle rule from pinned ares reference:
- unindexed direct/absolute read: +0; write: +1 dummy read;
- indexed read: +1; indexed write: +2;
- (X) read: +1; (X) write: +2;
- (X)+ read/write: +2;
- indexed/indirect read: +1; write: +2.

Keep branch conditional +2 timing as a separate later batch.

## RESUME HERE — mechanism validated; addressing-family timing next

1. `master` remains `a2270699...`. Clean block-bound candidate `phase2/apu-block-bound-fix@7e48bcc9...` remains VALIDATED and unmerged.
2. Missing-cycle mechanism proof `842a1412...`, run `35288358655` is **VALIDATED for NOP/BRA/MUL/DIV only**; exact cycle totals match pinned independent reference.
3. Next batch on diagnostic branch: extend proof harness to read GDB R4300 register **s3 = GPR19 / RSP packet `p13`** at `compile_block` and first `cpu_execute` return. Pinned ares N64 hook returns each GPR as a 16-hex-digit u64, so this can measure total master-cycle debit including runtime memory helpers.
4. Apply one controlled class of timing corrections: addressing-family missing cycles only. Validate representative read/write pairs against reference totals and semantics. Do not include conditional branch timing in this batch.
5. If addressing-family proof passes, checkpoint and recreate timing mechanism + validated addressing rules cleanly from `7e48bcc9...`; then proceed to conditional branches as a separate variable.
6. E1 matched-window repair remains required before performance ranking. E3/E4/E5 remain DEFERRED until timing baseline is meaningfully corrected.


## Addressing-family timing proof in progress — checkpoint 2026-09-17

Exact diagnostic SHA: **`19b3d6cfe7c042109fe08bc08e44eac0a9abb510`**, one commit ahead of validated mechanism SHA `842a1412...`.

Controlled class under test: **SPC700 addressing-family missing guest cycles only**. No conditional branch timing changes are included.

Core diagnostic changes:
- direct pure-write address path: +1 dummy destination-read cycle;
- direct X/Y indexed: +1 for reads/modifies, +2 for pure writes;
- `(X)`: +1 for reads, +2 for pure writes;
- `(X)+`: +2 for read and write directions;
- absolute pure stores use a new `apu_absw` wrapper with +1, while CALL/JMP retain uncharged `apu_absa`;
- absolute X/Y indexed: +1 read, +2 write;
- `[dp+X]` and `[dp]+Y`: +1 read, +2 write.
Existing runtime `apu_read8/apu_write8` data-access debits remain unchanged.

The proof harness now reads ares R4300 **GPR19 / s3 using RSP `p13`** at `compile_block` and at the first `cpu_execute` return. Pinned ares N64 debug hook returns GPRs as 16-hex-digit u64 values, so the signed delta measures total generated-block master-cycle debit including runtime memory helpers.

Representative matrix adds 16 cases:
direct read/write; direct+X read/write; `(X)` read/write; `(X)+` read/write; absolute read/write; absolute+X read/write; `[dp+X]` read/write; `[dp]+Y` read/write. Each checks static debit, total `s3` debit vs independent reference cycles, PC/header span, and a semantic postcondition (A/X or written RAM).

Direct compare `842a1412... -> 19b3d6cf...` is exactly:
- `.github/workflows/apu-cycle-proof.yml` +16/-6;
- `scripts/apu_cycle_proof.py` +179/-2;
- `src/apu_address.S` +54/-0;
- `src/apu_emitter.S` +3/-3.

Runs launched for exact SHA:
- **Build and Validate `35289165618`** — queued at checkpoint.
- **APU Cycle And Span Proof `35289165637`** — queued at checkpoint.

Acceptance requires ALL of:
1. normal + PROFILE build + Mupen smoke green;
2. existing BRA/NOP/MUL/DIV and NOP-span regressions remain green;
3. all 16 addressing cases match exact static expected debit;
4. measured total `s3` debit equals pinned independent reference cycle total ×21;
5. semantic postconditions and one-region block bound remain correct.

Any mismatch rejects or narrows the family rule; do not paper over a failure by adjusting the reference expectation without reconciling the pinned ares instruction sequence.


## Addressing proof attempt 1 — harness false negative 2026-09-17

Exact diagnostic SHA **`19b3d6cfe7c042109fe08bc08e44eac0a9abb510`**:
- Build and Validate **`35289165618` SUCCESS**: normal build, PROFILE build, pinned Mupen smoke all green.
- APU Cycle And Span Proof **`35289165637` FAILURE**, cycle-proof job `105428441273`.

The failure is **REJECTED as core evidence**. It occurred before any of the 16 new addressing-family cases ran.

Measured legacy regression cases before the stop all passed total-cycle measurement through R4300 `s3`:
- BRA: `s3 1064 -> 980`, delta **-84 = 4 cycles**;
- NOP+BRA: delta **-126 = 6**;
- MUL+BRA: delta **-273 = 13**;
- DIV+BRA: delta **-336 = 16**;
- long bounded NOP probe: delta **-672 = 32**, header 8->8, static debit -672, PC after block **0x0210**.

Harness bug: the newly added generic semantic check assumed every case must return `apu_count == TEST_PC (0x0200)`. That is wrong for the bounded long-NOP regression case, whose correct postcondition since the validated block-bound fix is `0x0210` after compiling/executing exactly 16 NOPs. The harness therefore raised `long_nop_dbnzy: semantic postcondition mismatch` despite its cycle/span result being correct.

**Decision:** fix only the diagnostic expected-PC postcondition for the long probe and rerun the exact addressing batch. Do not change core timing rules or reference cycle expectations based on this failure. The 16 addressing-family cases remain **UNMEASURED** by this attempt because execution stopped before reaching them.


## SPC700 addressing-family timing — VALIDATED 2026-09-17

Exact diagnostic SHA **`e78b3c47989359c3796887d00da9dcca56740e2b`** (core timing rules identical to `19b3d6cf...`; final commit only fixes the bounded-NOP diagnostic expected-PC postcondition).

**Build and Validate `35294386630` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

Dynamic authority: **APU Cycle And Span Proof `35294386627` SUCCESS**, cycle-proof job **`105444053413`**.
- result artifact **`10527331782`**, digest `sha256:3ddaf910afbb446093aa9fe154756f8e507d52633a05a18b29b96aba31e51f0b`;
- exact proof-build artifact **`10526324943`**, digest `sha256:92d3fcd835b0bebc9f4e7b662baa2216557a4c0cd1554b50f23cb1d3f75046c5`.

All 16 representative addressing cases matched:
- compile-time/static debit prediction;
- total runtime R4300 `s3` debit against pinned ares SPC700 cycles × `apu_clock=21`;
- expected register or RAM semantics;
- expected one-region JIT span.

Measured total sequence cycles (tested instruction + corrected 4-cycle BRA loop):
- direct read/write: **7 / 8**;
- direct+X read/write: **8 / 9**;
- `(X)` read/write: **7 / 8**;
- `(X)+` read/write: **8 / 8**;
- absolute read/write: **8 / 9**;
- absolute+X read/write: **9 / 10**;
- `[dp+X]` read/write: **10 / 11**;
- `[dp]+Y` read/write: **10 / 11**.

The measured total `s3` debit was exact in every case; e.g. direct read -147 (7), direct write -168 (8), absolute+X write -210 (10), indexed/indirect writes -231 (11).

Existing fixed-cycle regressions BRA/NOP/MUL/DIV and bounded 16-NOP block also remained green. Summary flags all true:
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`all_semantics_match_expected`,
`all_header_spans_match_source_prediction`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

### Interpretation / scope

**VALIDATED:** the shared missing-cycle mechanism plus audited addressing-family rules correctly reconstruct total SPC700 guest timing for the tested ordinary byte read/write paths while retaining existing runtime memory-helper timing.

**NOT PROVEN:** every opcode that happens to reuse one of these address generators is fully cycle-correct. Special operations such as word operations, read-modify-write, stack/control and other multi-access instructions may have additional operation-specific cycles and need their own family proof. Addressing correction is a component of their timing, not automatic proof of the whole instruction.

The previous attempt `35289165637` is retained as **HARNESS FALSE NEGATIVE / REJECTED AS CORE EVIDENCE**: it stopped on the long-NOP expected-PC bug before any addressing case ran.

### Decision

Recreate the validated semantic core cleanly from **`phase2/apu-block-bound-fix@7e48bcc9...`**:
- shared fixed-cycle charge mechanism;
- NOP dummy-cycle timing while retaining block bound;
- BRA fixed +2;
- MUL +8 / DIV +11;
- validated addressing-family rules including pure absolute-store wrapper.
No PROFILE diagnostic state, GDB harness or proof workflow belongs in the clean candidate.

Then run normal Build/Validate on the clean candidate. Conditional taken-branch timing remains the next separate variable and must use a runtime-only debit on the taken path, not compile-time `s2`.

## RESUME HERE — addressing validated; clean timing candidate next

1. `master` remains `a2270699...`.
2. Clean block-bound base: `phase2/apu-block-bound-fix@7e48bcc9...`, VALIDATED.
3. Fixed-cycle mechanism: `842a1412...` / run `35288358655`, VALIDATED for NOP/BRA/MUL/DIV.
4. Addressing timing: `e78b3c47...` / run `35294386627`, VALIDATED for 16 representative byte read/write cases with exact total `s3` timing and semantics.
5. Immediate action: create a clean timing-correctness branch from `7e48bcc9...` containing only validated semantic core changes; verify diff and Build/Validate.
6. Next controlled timing batch after that: conditional branches. Emit the +2 taken-cycle debit in generated MIPS only on the taken path. Test both taken and not-taken for ordinary condition flags, bit branches, CBNE, DBNZ memory and DBNZ Y.
7. Special operation families (word/RMW/implied/stack/call/return/XCN/etc.) remain TODO and must not be declared corrected by addressing validation alone.
8. E1 matched-window repair remains required before performance ranking. E3/E4/E5 remain DEFERRED.


## Clean SPC700 timing candidate — checkpoint 2026-09-17

Clean branch **`phase2/apu-timing-correctness@1248bc98e9f71e37d3f384bf3f8aef243022e4e4`** was created directly from validated clean block-bound base `7e48bcc994483e7aaf7cc2793b03fe0ebf13ee84`.

It is exactly one commit ahead of that base and modifies only four production core files:
- `src/apu_address.S` +47;
- `src/apu_alu.S` +8;
- `src/apu_control.S` +4;
- `src/apu_emitter.S` +23/-4.

Explicit audit found **zero** `SODIUM64_PROFILE` or `apu_cycle_diag` references in the clean emitter. No workflow, harness, diagnostic state or profiling source is present.

Included semantic scope is only already-validated work:
- retained NOP BLOCK_SIZE bound from the base;
- shared compile-time missing-cycle helper;
- NOP dummy cycle;
- unconditional BRA +2;
- MUL +8 / DIV +11;
- validated ordinary addressing-family fixed cycles;
- pure absolute-store wrapper so CALL/JMP do not inherit store timing.

Exact clean CI launched: **Build and Validate `35294889292`** for SHA `1248bc98...`. An earlier run `35294839654` belongs to the transient branch-creation base SHA `7e48bcc9...` and is not authority for the clean timing commit.

Next action remains conditional taken-branch timing only after `35294889292` is green.


## Clean SPC700 timing candidate — CI VALIDATED 2026-09-17

Clean production candidate **`phase2/apu-timing-correctness@1248bc98e9f71e37d3f384bf3f8aef243022e4e4`** passed **Build and Validate `35294889292` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

The candidate remains exactly one clean semantic commit over `7e48bcc9...`, touching only `apu_address.S`, `apu_alu.S`, `apu_control.S`, and `apu_emitter.S`. It carries no diagnostic workflow/state.

This candidate is therefore **CANDIDATE / CI-VALIDATED**, backed by the independent ares dynamic proofs already recorded for its included timing rules. It is not yet merged because SPC700 timing coverage is intentionally continuing before integration.

### Conditional-branch design refinement

Static comparison to pinned ares shows the next branch batch must not be modeled as a uniform “taken +2 only” rule:

- ordinary flag branches (BPL/BMI/BVC/BVS/BCC/BCS/BNE/BEQ): base 2 cycles, **+2 only if taken**;
- BBC/BBS: base includes **+1 fixed idle** beyond existing fetch/data accounting, then **+2 if taken**;
- CBNE direct/direct+X: operation contributes **+1 fixed idle** beyond the addressing timing already validated, then **+2 if taken**;
- DBNZ memory: base is already composed by fetch/read/write/fetch accounting, then **+2 if taken**;
- DBNZ Y: **+2 fixed** (dummy PC read + idle) beyond fetch accounting, then **+2 if taken**.

Architecture for the taken surcharge: emit one generated MIPS `ADDI s3,s3,-(2*apu_clock)` only on the taken path. Compute its immediate at JIT compile time from configured `apu_clock`; do not add a runtime helper call per branch.

Efficient control-flow shape: branch on the **not-taken** condition over the taken-only debit/PC assignment, using the branch delay slot to set the fallthrough SPC PC. Taken path then executes one timing `ADDI` and overwrites SPC PC with the target. This avoids charging not-taken paths and avoids a runtime call.

## RESUME HERE — clean timing core green; conditional branches next

1. Clean current candidate: `phase2/apu-timing-correctness@1248bc98...`, Build/Validate `35294889292` SUCCESS.
2. Diagnostic addressing authority remains `e78b3c47...` / ares proof `35294386627` SUCCESS.
3. Next technical batch should be diagnostic first: add an emitter helper that emits a runtime cycle-debit `ADDI`, then update conditional branch generators with fixed family charges plus taken-only +2.
4. Proof both taken and not-taken paths. Minimum coverage: all eight ordinary condition branches, BBC/BBS, CBNE direct and direct+X, DBNZ memory, DBNZ Y. Check total `s3` cycles, resulting PC, and memory/Y side effects where applicable.
5. Only after that proof passes, port the validated branch timing into the clean `apu-timing-correctness` candidate.
6. Special non-branch operation families remain TODO. E1 matched-window repair still gates performance ranking.


## Conditional branch timing proof in progress — checkpoint 2026-09-17

Exact diagnostic SHA: **`a435d8f8af05db4e155304812161adb295adf130`**, one conceptual commit over validated addressing diagnostic `e78b3c47...`.

Question: can Sodium64 reproduce SPC700 conditional branch timing exactly while charging the **+2 taken cycles only on the runtime-taken path**, without adding a runtime helper call or disturbing PC/side effects?

Controlled diagnostic changes:
- add generated-MIPS `BNE` encoding;
- add `jit_emit_runtime_cycles`, which emits one generated `ADDI s3,s3,-cycles*apu_clock`; it does not execute a timing helper from generated code;
- ordinary BPL/BMI/BVC/BVS/BCC/BCS/BNE/BEQ: base unchanged, generated -2-cycle surcharge only on taken path;
- BBC/BBS: +1 fixed compile-time cycle plus taken-only +2;
- CBNE direct/direct+X: +1 fixed operation cycle beyond already-validated addressing plus taken-only +2;
- DBNZ memory: taken-only +2;
- DBNZ Y: +2 fixed plus taken-only +2.

Generated control-flow uses the MIPS branch delay slot to establish fallthrough SPC PC, skips the surcharge on not-taken paths, and overwrites PC with target only on taken paths.

Proof matrix: **28 cases** — taken + not-taken for all 8 ordinary conditional branches, BBC/BBS, CBNE direct and direct+X, DBNZ memory, DBNZ Y. Each case checks:
- block-final static debit;
- presence/shape of exactly one generated conditional runtime debit `-42`;
- actual total R4300 `s3` delta vs pinned ares reference;
- final SPC PC;
- Y/RAM side effects where applicable;
- inherited block-span invariants.

Exact runs launched:
- **Build and Validate `35295336043`** for `a435d8f8...`;
- **APU Cycle And Span Proof `35295336130`** for `a435d8f8...`.

At checkpoint both are still compiling exact SHA.

Acceptance: both CI and all 28 path-specific dynamic cases must pass. A compile-only green result is insufficient. Any not-taken path executing the -42 debit, any taken path missing it, wrong PC, wrong DBNZ side effect, or disagreement with pinned ares cycles rejects/narrows the branch implementation.


## SPC700 addressing-family timing — VALIDATED 2026-09-17/18

Exact diagnostic SHA **`e78b3c47989359c3796887d00da9dcca56740e2b`**. This SHA differs from `19b3d6cf...` only by the harness correction for the already-validated bounded long-NOP expected PC; core timing rules are unchanged.

**Build and Validate `35294386630` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.

Dynamic authority: **APU Cycle And Span Proof `35294386627` SUCCESS**, cycle-proof job **`105444053413`**.
- proof result artifact **`10527331782`**, digest `sha256:3ddaf910afbb446093aa9fe154756f8e507d52633a05a18b29b96aba31e51f0b`;
- exact proof-build artifact **`10526324943`**, digest `sha256:92d3fcd835b0bebc9f4e7b662baa2216557a4c0cd1554b50f23cb1d3f75046c5`.

All required summary invariants were true:
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `all_semantics_match_expected=true`;
- `all_header_spans_match_source_prediction=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

### MEASURED representative addressing totals

Each case includes the already-corrected 4-cycle BRA loop. Total `s3` debit matched pinned ares reference exactly at `apu_clock=21`:

- direct read: **7 cycles**, total debit -147;
- direct write: **8**, -168;
- direct+X read: **8**, -168;
- direct+X write: **9**, -189;
- `(X)` read: **7**, -147;
- `(X)` write: **8**, -168;
- `(X)+` read: **8**, -168;
- `(X)+` write: **8**, -168;
- absolute read: **8**, -168;
- absolute write: **9**, -189;
- absolute+X read: **9**, -189;
- absolute+X write: **10**, -210;
- `[dp+X]` read: **10**, -210;
- `[dp+X]` write: **11**, -231;
- `[dp]+Y` read: **10**, -210;
- `[dp]+Y` write: **11**, -231.

All semantic postconditions passed: read cases produced the expected accumulator/X state, write cases wrote the expected RAM byte, and all tested blocks remained in the expected tag region.

**VALIDATED scope:** fixed missing-cycle charges for the audited direct/indexed/indirect addressing families, while preserving existing runtime data-access debit placement. This materially expands timing correctness beyond the four-opcode mechanism proof.

**NOT YET COMPLETE:** conditional branch taken-path cycles, implied/stack/call/return/bit/word/special instruction families, and exact intra-instruction I/O/timer bus-cycle placement remain open.

### Decision

Create a **clean code-only timing foundation branch from `phase2/apu-block-bound-fix@7e48bcc9...`** containing:
- shared compile-time missing-cycle helper;
- corrected NOP/BRA/MUL/DIV fixed timing;
- validated addressing-family charges and absolute-store wrapper;
- NO PROFILE diagnostic capture;
- NO GDB proof script/workflow changes.

Then Build/Validate the clean branch. After that, conditional branch timing is the next isolated batch. Conditional +2 cycles must be charged at runtime only on the taken path; compile-time `jit_charge_cycles` is not appropriate for that variable.

## RESUME HERE — addressing timing validated; clean timing foundation next

1. `master` remains `a2270699...`.
2. Clean block-bound branch `phase2/apu-block-bound-fix@7e48bcc9...` is the base for the next clean candidate.
3. Diagnostic authority for fixed timing/addressing is `e78b3c47...`, Build/Validate `35294386630`, ares proof `35294386627`; all 16 representative addressing cases match total reference cycles and semantics.
4. Recreate only validated core changes cleanly from `7e48bcc9...`. Do not copy `apu_cycle_diag.S`, diagnostic finish-block capture, workflow or proof script.
5. Next isolated timing variable after clean CI: conditional branches. Add +2 guest cycles only on the taken runtime path; keep not-taken timing unchanged. Validate taken/not-taken pairs for ordinary flag branch, bit branch, CBNE, DBNZ Y and DBNZ memory.
6. Remaining fixed-cycle families come after conditional branches. Exact I/O/timer cycle placement remains a later fidelity contract.
7. E1 matched-window repair remains required before ranking performance. E3/E4/E5 remain DEFERRED.


## Clean SPC700 timing foundation — candidate created 2026-09-17/18

Clean branch: **`phase2/apu-timing-foundation@a62e95b1764d296dc74e711903c2431c343a54c2`**, created directly from validated block-bound candidate `7e48bcc994483e7aaf7cc2793b03fe0ebf13ee84`.

This is a **CANDIDATE** code-only recreation of the dynamically validated fixed-timing/addressing work. Direct compare `7e48bcc9... -> a62e95b1...` is exactly one commit and exactly four core files:
- `src/apu_address.S` +54/-0;
- `src/apu_alu.S` +8/-0;
- `src/apu_control.S` +4/-0;
- `src/apu_emitter.S` +23/-4.

No diagnostic workflow, GDB script, `apu_cycle_diag.S`, PROFILE capture, profiler code or documentation is present in the candidate.

Included validated semantics:
- NOP uses shared fixed-cycle helper and still routes through `finish_opcode`;
- BRA +2 fixed internal cycles;
- MUL +8 missing cycles;
- DIV +11 missing cycles;
- validated direct/indexed/indirect addressing-family fixed charges;
- `apu_absw` wrapper only for pure absolute stores so CALL/JMP do not inherit store dummy-read timing.

Build and Validate run for exact candidate SHA: **`35296376545`**, currently PENDING at checkpoint. Branch creation itself triggered an earlier redundant run `35296360910` for base SHA `7e48bcc9...`; do not confuse that base run with candidate validation.

**Acceptance:** candidate remains unmerged until exact SHA `a62e95b1...` completes normal build, PROFILE build and pinned Mupen smoke successfully. The independent dynamic semantic authority remains diagnostic SHA `e78b3c47...` / ares proof `35294386627`.

### Next isolated variable after clean CI

Conditional branch timing remains next. Static/reference audit confirms:
- ordinary conditional branch: not taken = fetch-only base timing; taken adds **+2 cycles**;
- bit branch, CBNE, DBNZ memory/Y each have their own fixed pre-branch bus/idle work, but the **taken-path delta itself is +2 cycles**.
Because the decision is runtime-dependent, these +2 cycles must be emitted on the generated taken path, not added through compile-time `jit_charge_cycles`.

Do not modify the clean timing foundation until `35296376545` finishes.


## Clean SPC700 timing foundation — CI VALIDATED 2026-09-17/18

Clean candidate **`phase2/apu-timing-foundation@a62e95b1764d296dc74e711903c2431c343a54c2`** completed **Build and Validate `35296376545` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

The earlier branch-creation run `35296360910` for base SHA `7e48bcc9...` was cancelled by concurrency after the real candidate push; it is not relevant to candidate validity.

Combined authority for this candidate:
- clean code diff: exactly four APU core files, no diagnostics;
- exact candidate CI: `35296376545` SUCCESS;
- independent dynamic semantic/cycle authority: diagnostic `e78b3c47...`, ares proof `35294386627` SUCCESS.

State: **VALIDATED CANDIDATE**, not merged.

### Conditional branch timing design selected

The existing generated branch layout has two orientations:
- for conditions where the emitted MIPS branch corresponds to **SNES taken**, charge +2 cycles statically and emit one **+2-cycle refund** instruction only on the sequential SNES-not-taken path; increase branch skip from 2 to 3 emitted instructions;
- for conditions where the emitted MIPS branch corresponds to **SNES not-taken**, leave static timing unchanged and emit one **-2-cycle debit** instruction only on the sequential SNES-taken path; likewise increase skip from 2 to 3.

This preserves one extra runtime MIPS instruction on only the path needing adjustment and avoids new runtime helper calls.

Additional fixed branch-family timing from pinned ares reference:
- ordinary flag branches: +0 fixed, +2 only when taken;
- BBC/BBS: +1 fixed idle, +2 when taken;
- CBNE direct/direct+X: +1 fixed idle beyond addressing-family timing, +2 when taken;
- DBNZ Y: +2 fixed cycles, +2 when taken;
- DBNZ memory: +0 fixed beyond existing read/write/fetches, +2 when taken.

Next diagnostic matrix must exercise taken/not-taken pairs for BCC and BCS (both branch orientations), BBC/BBS, CBNE direct and direct+X, DBNZ Y and DBNZ memory; verify total `s3` delta, resulting PC and register/RAM postconditions. Do not modify clean `a62e95b1` until this diagnostic batch passes.


## SPC700 conditional branch timing — VALIDATED 2026-09-17/18

Diagnostic authority SHA: **`a435d8f8af05db4e155304812161adb295adf130`**.

CI:
- **Build and Validate `35295336043` SUCCESS**.
- **APU Cycle And Span Proof `35295336130` SUCCESS**, cycle-proof job **`105446873166`**.
- proof-build artifact **`10528215894`**, digest `sha256:25964401ec72a5c41e8edbfe86cfe718fc901da5686dbce52885865b30801149`;
- proof result artifact **`10527812627`**, digest `sha256:f1adacc4ecb5b64fc9384d000f9d080d6fd0b81ad4fca97e6020533260d3b64c`.

Implementation pattern validated:
- new compile-time helper emits one runtime `ADDI s3,s3,-cycles*apu_clock` into generated code;
- ordinary conditional branches choose fallthrough in the delay slot and execute the -2-cycle runtime debit only on the SNES-taken path;
- BNE opcode macro was added for the clear-condition branch orientation;
- BBC/BBS add +1 fixed cycle;
- CBNE adds +1 fixed cycle beyond its addressing work;
- DBNZ Y adds +2 fixed cycles;
- DBNZ memory adds no extra fixed cycles beyond existing read/write/fetch accounting;
- all conditional families add +2 cycles only when taken.

Dynamic matrix validated taken/not-taken semantics and total cycles for:
- BPL/BMI/BVC/BVS/BCC/BCS/BNE/BEQ: **2 not taken / 4 taken**;
- BBC/BBS: **5 / 7**;
- CBNE direct: **5 / 7**;
- CBNE direct+X: **6 / 8**;
- DBNZ memory: **5 / 7**;
- DBNZ Y: **4 / 6**.

All summary invariants passed:
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

The generated code contains the -42 master-cycle runtime instruction in both variants, but GDB `s3` delta proves it executes only on the taken path. Example ordinary branch: static debit remains 2 cycles; measured total is 4 taken and 2 not-taken.

**Decision:** consume only core changes from `a435d8f8...` into clean `phase2/apu-timing-foundation@a62e95b1...`: `apu_control.S`, runtime cycle helper in clean `apu_emitter.S`, and BNE encoding in `defines.h`. Do NOT copy diagnostic script/workflow/PROFILE capture.

After clean CI, proceed to remaining fixed-cycle SPC700 families (implied/flag/stack/call/return/bit/word/XCN/BRK/etc.) as the next timing-coverage batch. Performance ranking remains deferred until timing coverage is broad enough for a new honest baseline.


## Clean conditional-branch timing candidate — checkpoint 2026-09-17/18

Clean branch advanced to **`phase2/apu-timing-foundation@fe53aa5fe574baa5a4dba141e8c34ea8ce5996bc`**, one commit on top of CI-validated fixed/addressing foundation `a62e95b1...`.

Direct clean diff `a62e95b1... -> fe53aa5f...`:
- `src/apu_control.S` +78/-36;
- `src/apu_emitter.S` +17/-0;
- `src/defines.h` +1/-0.
No diagnostics, scripts, workflows or PROFILE capture.

Included semantics are exactly the dynamically validated `a435d8f8...` conditional timing changes:
- runtime conditional cycle-debit emitter;
- BNE encoding;
- taken-only +2 timing for all audited conditional branches;
- fixed +1/+2 family timing for BranchBit / CBNE / DBNZ Y.

Exact clean Build and Validate run: **`35296688540`**, QUEUED at checkpoint.

Authority split:
- dynamic timing/semantic proof: diagnostic `a435d8f8...`, ares run `35295336130` SUCCESS;
- clean integration candidate: `fe53aa5f...`, awaiting its own normal/PROFILE/Mupen CI.

Do not modify clean `fe53aa5f...` until run `35296688540` completes. Next work is read-only mapping of remaining fixed-cycle SPC700 instruction families.


## Clean conditional timing foundation — CI VALIDATED 2026-09-17/18

Clean **`phase2/apu-timing-foundation@fe53aa5fe574baa5a4dba141e8c34ea8ce5996bc`** completed **Build and Validate `35296688540` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

Combined authority:
- clean code-only branch `fe53aa5f...`;
- dynamic conditional timing/semantics authority `a435d8f8...` / ares proof `35295336130`;
- clean exact-SHA CI `35296688540`.

State: **VALIDATED CANDIDATE**, unmerged.

### New stack correctness question before next timing batch

Static audit of inherited POP generators shows a potentially material ordering issue:
`apu_ppa/ppx/ppy/ppp` increment S, mask to low 8 bits, call `apu_read8`, and only **after the read returns** execute `ORI A0,A0,0x100`. PUSH generators construct `0x01xx` before `apu_write8`.

**OPEN QUESTION / HYPOTHESIS:** POP may therefore read direct-page `0x00xx` instead of stack-page `0x01xx`. Do not infer a bug solely from the static sequence; prove it dynamically before adding stack timing charges.

Next controlled experiment: on diagnostic `phase2/apu-cycle-proof`, test PUSH/POP semantics with distinct sentinel bytes at `00xx` and `01xx`, initially without changing stack semantics. If POP observes the direct-page sentinel, classify as CONFIRMED correctness defect and repair stack addressing before timing it. If it observes the stack-page sentinel, reject the hypothesis and continue the planned implied/flags/transfers/stack timing batch.


## POP stack-page semantic proof in progress — checkpoint 2026-09-17/18

Diagnostic-only SHA **`410985f0ba2fbf22c1d8341890bbf5fd1dba2d32`** adds only harness/workflow support for `apu_stack` and one directed POP-A semantic case. No APU core source is changed.

Runs:
- **Build and Validate `35296994425`** — queued at checkpoint.
- **APU Cycle And Span Proof `35296994473`** — in progress at checkpoint.

Directed case:
- initial `S=0x7F`;
- `RAM[0x0080]=0xAA` direct-page sentinel;
- `RAM[0x0180]=0xBB` correct stack-page sentinel;
- program `POP A; BRA back`;
- expected postcondition: `S=0x80`, `A=0xBB`.

This experiment deliberately does **not** judge POP timing yet (`reference_cycles=None`). It only separates the static-addressing hypothesis.

Readings:
- `A=0xBB, S=0x80` => REJECT the suspected stack-page bug; proceed to timing charges.
- `A=0xAA, S=0x80` => CONFIRM inherited POP reads page `0x00xx` because `0x0100` is ORed into A0 after `apu_read8`; repair semantics before timing stack family.
- other value/state => inspect harness/JIT state before attributing a core defect.

Clean timing foundation remains frozen at **`fe53aa5f...`**, Build and Validate **`35296688540` SUCCESS**.


## Static compatibility debt surfaced during timing audit — DEFERRED 2026-09-17/18

**MEASURED STATIC / REQUIRED SUPPORT, but not current M1 variable:** the current SPC700 opcode table maps **0xBE (DAS)** and **0xDF (DAA)** to `apu_unk`. The pinned independent SPC700 reference implements both decimal-adjust instructions.

This is a real base-SPC700 compatibility/accuracy gap, not a missing-cycle-only issue. Do not silently include it in the current timing batch. Track it for a later Gate C/base-core completeness pass after the timing contract is stabilized, unless representative software proves it is an earlier blocker.

The active experiment remains POP stack-page semantics at `410985f0...` / run `35296994473`.


## POP stack-page hypothesis — REJECTED dynamically 2026-09-17/18

Diagnostic-only SHA **`410985f0ba2fbf22c1d8341890bbf5fd1dba2d32`** changed only the proof harness/workflow; no APU core source changed.

Authorities:
- **Build and Validate `35296994425` SUCCESS**.
- **APU Cycle And Span Proof `35296994473` SUCCESS**, cycle-proof job **`105451729667`**.
- proof result artifact **`10528910419`**, digest `sha256:a47ce297dace8fe48385fffcfadb07de141091dd12ee1e3900c635220c4611e8`;
- exact proof-build artifact **`10528369355`**, digest `sha256:b61b722699a915de1cb57d77ec0e6e9e2987c4a400b2c200e024790647a38c53`.

Directed sentinel case:
- initial `S=0x7F`;
- direct page `RAM[0x0080]=0xAA`;
- stack page `RAM[0x0180]=0xBB`;
- source `POP A; BRA back`;
- measured **A=0xBB**, **S=0x80**, semantic check true.

Therefore the suspected inherited POP stack-page bug is **REJECTED**.

Why the static sequence looked wrong: the generator calls `emit_jal` to emit a runtime MIPS `JAL apu_read8`; the immediately following emitted `ORI A0,A0,0x100` occupies that runtime JAL's **delay slot**. It executes before control enters `apu_read8`, so the read correctly sees `0x01xx`. This discarded explanation is now preserved so the code is not “fixed” incorrectly later.

The proof intentionally did not judge POP timing (`reference_cycles=None`). Its observed block had static 5 units and total 6 units including runtime read because the trailing validated BRA contributes 4 cycles; stack-family timing correction remains the next variable.

## RESUME HERE — fixed implied/flags/transfers/stack timing next

1. Clean timing foundation remains **`phase2/apu-timing-foundation@fe53aa5f...`**, Build/Validate `35296688540` SUCCESS, unmerged.
2. POP stack-page suspicion is REJECTED by `410985f0...` / proof `35296994473`; do not change POP addressing.
3. Next controlled diagnostic batch on `phase2/apu-cycle-proof`: add only fixed missing cycles for implied ALU/register operations, flag operations, register transfers and PUSH/POP.
4. Expected missing charges from pinned ares:
   - implied A/X/Y modify and register transfers: +1;
   - CLRC/SETC/CLRP/SETP/CLRV: +1;
   - DI/EI and NOTC: +2;
   - XCN: +4;
   - PUSH/POP family: +2 beyond existing opcode fetch + runtime stack read/write.
5. Validate representative semantics + total `s3` cycles before consuming anything cleanly.
6. Keep CALL/TCALL/PCALL/RET/RET1/BRK, word operations, bit operations and decimal-adjust support as separate later batches.
7. DAA/DAS remain MEASURED STATIC / REQUIRED SUPPORT / DEFERRED Gate C debt.


## Fixed implied/flags/transfers/stack timing proof in progress — checkpoint 2026-09-17/18

Exact diagnostic SHA: **`62e661b62a177c5b1c087226e589153c29e439fe`**, one commit after the POP semantic-only authority `410985f0...`.

Controlled timing class:
- implied A/X/Y register modify operations: +1 missing cycle;
- register transfers A/X/Y/SP: +1;
- CLRC/SETC/CLRV and CLRP/SETP: +1;
- NOTC: +2;
- DI/EI: +2;
- XCN: +4;
- PUSH A/X/Y/PSW and POP A/X/Y/PSW: +2 beyond existing opcode fetch + runtime stack access.

No CALL/TCALL/PCALL/RET/RET1/BRK, word, bit, decimal-adjust or other special-family timing changes are included.

Direct compare `410985f0... -> 62e661b6...` is one commit:
- `src/apu_alu.S` +60/-0;
- `src/apu_control.S` +16/-0;
- `src/apu_transfer.S` +56/-0;
- `scripts/apu_cycle_proof.py` +46/-2.

Representative dynamic cases added:
- INC A + BRA: expected total 6 cycles;
- MOV X,A + BRA: 6;
- MOV SP,X + BRA: 6;
- CLRC + BRA: 6;
- DI + BRA: 7;
- EI + BRA: 7;
- NOTC + BRA: 7;
- XCN + BRA: 9;
- PUSH A + BRA: static 7 cycles + runtime write = total 8;
- existing directed POP A stack sentinel now also expects static 7 + runtime read = total 8.

Each case checks static debit, total R4300 `s3` delta, PC/span and relevant A/X/SP/flags/RAM postcondition.

Runs for exact SHA:
- **Build and Validate `35297695310`** — in progress at checkpoint.
- **APU Cycle And Span Proof `35297695313`** — in progress at checkpoint.

Acceptance:
1. normal + PROFILE build + Mupen smoke green;
2. all previous timing/addressing/branch/span regressions remain green;
3. every new representative case matches pinned ares total cycles exactly;
4. PUSH/POP preserve proven stack-page semantics and expected S/RAM/A state;
5. no unexpected runtime debit instruction appears for these fixed-cycle-only families.

A mismatch narrows/rejects the specific family rule; do not adjust the reference expectation without reconciling the pinned ares instruction sequence.


## Fixed-family timing proof attempt 1 — harness false negative on 0xED 2026-09-17/18

Exact core/harness SHA **`62e661b62a177c5b1c087226e589153c29e439fe`**:
- **Build and Validate `35297695310` SUCCESS**, including normal build, PROFILE build and pinned Mupen smoke.
- **APU Cycle And Span Proof `35297695313` FAILURE**, cycle-proof job `105453803356`.
- failed proof result artifact **`10528981437`**, digest `sha256:d0ea14cfc5f171b9d6900bf7d977602d65271d079e01113ec464eb4910767a0b`;
- exact proof-build artifact **`10528736287`**, digest `sha256:2684ab8874f58050c4a5441ab722400b35a5ebb7000fdd9dadf681c3d03312a1`.

The failure is **REJECTED as core/timing evidence**. All prior regression cases remained green, POP A now matched 8 total cycles with correct stack semantics, and the new cases completed successfully through:
- INC A + BRA = **6 cycles**, semantic pass;
- MOV X,A + BRA = **6**, X semantic pass;
- MOV SP,X + BRA = **6**, SP semantic pass;
- CLRC + BRA = **6**, flags semantic pass;
- DI + BRA = **7**, flags semantic pass;
- EI + BRA = **7**, flags semantic pass.

Execution stopped while arming `notc_fixed`, before compiling or executing NOTC. The injected source bytes are `ED 2F FD`. Shared `RSPClient.read_memory()` currently treats **any** reply beginning with ASCII `E` as a GDB error. A valid memory reply `ED2FFD` therefore triggered:
`target rejected memory read ...: ED2FFD`.

This is a diagnostic-protocol parser defect, not an emulator result. GDB RSP errors have the shape `E` + two hex digits (normally exactly 3 ASCII bytes), while a memory/register hex payload can legitimately begin with hexadecimal E.

**Decision:** fix only RSP error recognition (and the identical single-register-read check) to recognize actual 3-byte `Ehh` error packets, then rerun the unchanged core timing candidate. Do not alter cycle charges or reference expectations.


## Fixed-family timing rerun after RSP parser fix — checkpoint 2026-09-17/18

Diagnostic HEAD **`2e01d323f458575fcaac8602331a87a36854c081`** has the **same APU core timing implementation as `62e661b6...`**. The only changes are diagnostic protocol parsing:
- `scripts/gdb_rsp_dump.py`: memory reads classify an error only when the reply is exactly a 3-byte `Ehh` packet;
- `scripts/apu_cycle_proof.py`: single GPR reads use the same exact `Ehh` rule.

This removes the false collision where valid hex payload `ED2FFD` was misread as a GDB error.

Exact rerun workflows:
- **Build and Validate `35298264597`** — queued at checkpoint.
- **APU Cycle And Span Proof `35298264479`** — queued at checkpoint.

Core acceptance criteria are unchanged from `62e661b6...`. In particular, NOTC/XCN/PUSH A and the already corrected POP timing must now be reached and judged without any change to their expected cycles.


## Fixed implied/flags/transfers/stack timing — VALIDATED 2026-09-17/18

Exact diagnostic core authority remains **`62e661b62a177c5b1c087226e589153c29e439fe`**. Exact rerun SHA **`2e01d323f458575fcaac8602331a87a36854c081`** changes only diagnostic GDB-RSP error parsing; APU core timing is identical to `62e661b6...`.

Authorities:
- **Build and Validate `35298264597` SUCCESS**.
- **APU Cycle And Span Proof `35298264479` SUCCESS**, cycle-proof job **`105455473977`**.
- proof result artifact **`10529235434`**, digest `sha256:11065dc6adc72c36c1af3d5c405214a9de6e6a1d265545ec2a23f69f38e63962`;
- exact proof-build artifact **`10529166425`**, digest `sha256:834ad7453b358ed56c18c3ab0cbb40e08e42c0e2c704bfd632b7613db38a338e`.

All required summary invariants are true:
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `all_runtime_cycle_debits_match_expected=true`;
- `all_semantics_match_expected=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

Representative newly validated totals, each combined with the already validated trailing BRA loop:
- INC A + BRA: **6 cycles**;
- MOV X,A + BRA: **6**;
- MOV SP,X + BRA: **6**;
- CLRC + BRA: **6**;
- DI + BRA: **7**;
- EI + BRA: **7**;
- NOTC + BRA: **7**;
- XCN + BRA: **9**;
- PUSH A + BRA: **8**, writes expected byte to stack page and updates S correctly;
- POP A + BRA: **8**, reads expected stack-page sentinel `0xBB` and updates S correctly.

The prior `62e661b6...` proof failure on source bytes beginning `ED...` is **REJECTED as core evidence**: exact rerun with parser-only correction passes unchanged timing implementation.

**VALIDATED scope:** fixed missing-cycle rules for implied A/X/Y modify operations, A/X/Y/SP register transfers, CLRC/SETC/CLRV/CLRP/SETP, DI/EI, NOTC, XCN, and PUSH/POP A/X/Y/PSW families.

**Decision:** consume only APU core changes from `62e661b6...` into clean `phase2/apu-timing-foundation@fe53aa5f...`: `src/apu_alu.S`, `src/apu_control.S`, `src/apu_transfer.S`. Do NOT copy proof script/workflow or GDB parser changes.

Next timing families remain isolated: CALL/TCALL/PCALL/RET/RET1/BRK first, then word/bit/special operations. DAA/DAS remain Gate-C REQUIRED SUPPORT debt, not part of timing-only changes.


## Clean implied/flags/transfers/stack timing candidate — checkpoint 2026-09-17/18

Clean branch advanced to **`phase2/apu-timing-foundation@46230daa7ac66b7b400ce6d2105e3834a15ed4ec`**, one commit on top of clean conditional foundation `fe53aa5f...`.

Direct compare `fe53aa5f... -> 46230daa...` is exactly:
- `src/apu_alu.S` +60/-0;
- `src/apu_control.S` +16/-0;
- `src/apu_transfer.S` +56/-0.

No diagnostic scripts/workflows, GDB parser fixes, PROFILE capture or `apu_cycle_diag` code are present.

This clean commit consumes the dynamically validated fixed-family timing rules from diagnostic core SHA `62e661b6...` / rerun authority `2e01d323...`.

Exact clean Build and Validate run: **`35301478900`**, QUEUED at checkpoint.

Acceptance remains normal build + PROFILE build + pinned Mupen smoke green on exact SHA `46230daa...`. Dynamic semantic/cycle authority remains ares proof `35298264479`.

While clean CI runs, next work is READ-ONLY mapping of CALL/TCALL/PCALL/RET/RET1/BRK timing and semantics against pinned ares. Do not modify clean `46230daa...` until its exact CI completes.


## Clean fixed-family timing foundation — CI VALIDATED 2026-09-17/18

Clean **`phase2/apu-timing-foundation@46230daa7ac66b7b400ce6d2105e3834a15ed4ec`** completed **Build and Validate `35301478900` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged. Dynamic cycle/semantic authority remains diagnostic `62e661b6...` with parser-only rerun `2e01d323...` / ares proof `35298264479`.

## CALL/TCALL/PCALL/RET/RET1/BRK timing proof in progress — checkpoint 2026-09-17/18

Exact diagnostic SHA: **`044009a4c8bc34ffa8314ddcb99fbe2b31099de5`**, based on `2e01d323...`.

Controlled core timing changes, only in `src/apu_control.S`:
- CALL +3 fixed cycles;
- TCALL +3;
- PCALL +2;
- RET +2;
- RET1 +2;
- BRK +2.

Reference-derived accounting:
- CALL absolute: opcode+2 operand fetches +3 fixed +2 stack writes = **8 total**;
- PCALL: opcode+operand +2 fixed +2 stack writes = **6**;
- TCALL0: opcode +3 fixed +2 stack writes +2 vector reads = **8**;
- RET: opcode +2 fixed +2 stack reads = **5**;
- RET1: opcode +2 fixed +3 stack reads = **6**;
- BRK: opcode +2 fixed +3 stack writes +2 vector reads = **8**.

The proof also:
- forces `apu_map[0x3FF]=0` so FFDE/FFDF vectors come deterministically from RAM, not inherited IPL-ROM mapping;
- validates final PC and S;
- validates pushed return-PC bytes for CALL/PCALL/TCALL;
- validates RET/RET1 stack reconstruction;
- validates RET1 PSW restore;
- validates BRK pushed PC/PSW and post-BRK flags.

Exact workflows:
- **Build and Validate `35301687790`** — QUEUED at checkpoint.
- **APU Cycle And Span Proof `35301687777`** — IN PROGRESS at checkpoint.

Expected readings:
- all six exact cycle totals + semantic postconditions pass => VALIDATE this timing family and consume only `apu_control.S` core timing changes cleanly on `46230daa...`;
- cycle mismatch with semantic pass => narrow/reject only the affected fixed-cycle rule against pinned ares;
- semantic mismatch with matching cycles => treat as pre-existing CALL/RET/BRK correctness defect, do not hide it with timing charges;
- harness/vector mismatch => repair diagnostic setup only after proving the mismatch is not core behavior.

**Known limitation preserved:** TCALL/BRK bus-access ordering in Sodium64 differs statically from pinned ares (vector vs stack access order). This batch tests total guest cycles and end-state semantics only; exact intra-instruction I/O/timer ordering remains separate fidelity work.


## CALL/PCALL proof exposed inherited PCALL target bug — 2026-09-17/18

Diagnostic SHA **`044009a4c8bc34ffa8314ddcb99fbe2b31099de5`**:
- Build and Validate **`35301687790` SUCCESS** (normal, PROFILE, pinned Mupen smoke all green).
- APU Cycle And Span Proof **`35301687777` FAILURE**, cycle-proof job **`105465701875`**.
- exact proof-build artifact **`10529863114`**, digest `sha256:219d6d9dae8d5dc860be1dd8a1e3ac7154fd9a06df751291d9e6759f27a01384`;
- failed-proof diagnostics artifact **`10529489052`**, digest `sha256:b697eab9d4d9d6c394e382ae3189fe15a75bad35030be96005f27afe95a89a98`.

The proof reached the new CALL/return family after all prior required timing cases continued to pass.

### MEASURED

**CALL absolute** passed completely:
- static debit -126 = 6 SPC cycles before runtime stack accesses;
- total debit -168 = **8 cycles**, matching pinned ares;
- final PC **0x1234**;
- S **0x80 -> 0x7E**;
- return bytes correctly pushed: `RAM[0x0180]=0x02`, `RAM[0x017F]=0x03`;
- semantic postcondition true.

**PCALL** timing and stack writes passed, but target semantics failed:
- static debit -84 = 4 cycles;
- total debit -126 = **6 cycles**, matching pinned ares;
- S **0x80 -> 0x7E**;
- return bytes correctly pushed: `RAM[0x0180]=0x02`, `RAM[0x017F]=0x02`;
- expected PC `0xFF34`, observed **`0xD475`**;
- semantic postcondition false; proof stopped here, so TCALL/RET/RET1/BRK are **NOT YET MEASURED** in this run.

### SUPPORTED CAUSE

This is an inherited PCALL semantic defect, not evidence against the +2 timing rule:
- `apu_pcall` computes target `0xFF00 | operand` into compile-time scratch `t2`;
- it then calls `load_stack`;
- `load_stack -> full_address` explicitly writes `t2 = low16(apu_stack)`;
- exact build symbol `apu_stack=0x8001D475`;
- observed wrong PC is exactly **0xD475**.

CALL does not suffer this because its destination is already carried in generated runtime `A0` and copied directly to S0.

State:
- **VALIDATED:** CALL total timing + end-state semantics for directed case.
- **MEASURED / SUPPORTED:** PCALL total timing 6 cycles.
- **CONFIRMED CORRECTNESS DEFECT:** PCALL target clobbered by volatile compile-time `t2`.
- **UNKNOWN:** TCALL/RET/RET1/BRK until proof advances past PCALL.

### Next controlled change

On diagnostic `phase2/apu-cycle-proof`, move `ori t2,v0,0xFF00` to immediately after `load_stack`, where `v0` still holds the fetched PCALL operand and before target emission. Do not change PCALL timing, stack sequence, harness expectations, or any other opcode.

Falsifier: if rerun still does not reach PC=0xFF34 with correct stack/timing, reject this cause and inspect the generated target instruction rather than broadening the patch.


## PCALL target-clobber diagnostic fix in progress — checkpoint 2026-09-17/18

Exact diagnostic SHA: **`f4da303dc3cd901672f923d476284b3f05372e38`**, parent `044009a4...`.

Controlled change: **only `src/apu_control.S` PCALL compile-time target lifetime**.
- Before: `t2 = 0xFF00 | operand` was computed before `load_stack`, then overwritten by `full_address`.
- Now: fetched operand remains in `v0` across `load_stack`, and `t2 = 0xFF00 | v0` is formed immediately afterward, before emitting S0 target.
- PCALL fixed timing (+2), stack sequence and all harness expectations are unchanged.

Exact workflows:
- **APU Cycle And Span Proof `35302251443`** — IN PROGRESS at checkpoint.
- **Build and Validate `35302251447`** — IN PROGRESS at checkpoint.

Question: does this single lifetime fix restore PCALL target `0xFF34` while preserving measured 6-cycle total and correct return-stack bytes, allowing the unchanged proof to advance to TCALL/RET/RET1/BRK?

Conditional next actions:
- PCALL passes and later cases pass => validate timing family plus PCALL semantic fix, then consume only validated core changes cleanly on `phase2/apu-timing-foundation@46230daa...`;
- PCALL still fails => inspect emitted target opcode/register value; do not broaden patch;
- later opcode fails => preserve PCALL as fixed and isolate only that later instruction.


## CALL/TCALL/PCALL/RET/RET1/BRK timing + PCALL semantic fix — VALIDATED 2026-09-17/18

Exact diagnostic authority: **`f4da303dc3cd901672f923d476284b3f05372e38`**.

CI:
- **Build and Validate `35302251447` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35302251443` SUCCESS**, cycle-proof job **`105467368408`**.
- proof-build artifact **`10529948912`**, digest `sha256:38d213c8e1727cef9310728d982975dc8bef202f7f2688729e843cebb7a5ef89`;
- proof result artifact **`10530423530`**, digest `sha256:9834d8846aa1b135a3e4b1e2f443d3a8a089e7a7d363b83be2fecdfbb0b13e50`.

All global proof invariants are true:
- `all_header_spans_match_source_prediction=true`;
- `all_runtime_cycle_debits_match_expected=true`;
- `all_semantics_match_expected=true`;
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

### MEASURED / VALIDATED directed control-flow cases

- **CALL absolute:** 8 total cycles; PC `0x1234`; S `0x80 -> 0x7E`; return bytes `0x02,0x03` pushed at `0x0180,0x017F`.
- **PCALL:** 6 total cycles; corrected PC **`0xFF34`**; S `0x80 -> 0x7E`; return bytes `0x02,0x02` correct.
- **TCALL0:** 8 total cycles; vector target PC `0x1234`; S `0x80 -> 0x7E`; return bytes correct.
- **RET:** 5 total cycles; PC `0x1234`; S `0x7E -> 0x80`.
- **RET1:** 6 total cycles; PC `0x1234`; S `0x7D -> 0x80`; PSW restored to `0x04`.
- **BRK:** 8 total cycles; vector PC `0x1234`; S `0x80 -> 0x7D`; pushed PC/PSW correct; post-BRK PSW `0x10` (I clear, B set).

The previous PCALL failure at `044009a4...` is now fully explained and superseded:
- old wrong PC `0xD475` exactly matched low16 of `apu_stack=0x8001D475`;
- `load_stack -> full_address` clobbered compile-time scratch `t2`;
- **validated fix:** preserve fetched PCALL operand in `v0` across `load_stack`, then form `t2=0xFF00|v0` immediately before target emission;
- rerun restores `0xFF34` while retaining exact 6-cycle total and stack semantics.

### Timing rules validated

- CALL +3 fixed missing cycles;
- TCALL +3;
- PCALL +2;
- RET +2;
- RET1 +2;
- BRK +2.

**Important remaining limitation:** these tests validate total guest cycles and directed end-state semantics. They do **not** validate exact intra-instruction bus-cycle ordering. Static comparison still shows Sodium64 TCALL/BRK vector-vs-stack access ordering differs from pinned ares. Preserve this as timing/fidelity debt for later timer/I/O-sensitive validation.

### Decision

Consume only validated core changes from diagnostic `f4da303d...` into clean `phase2/apu-timing-foundation@46230daa...`:
- `src/apu_control.S` fixed-cycle charges for CALL/TCALL/PCALL/RET/RET1/BRK;
- PCALL compile-time target lifetime fix.
Do NOT copy `apu_map` proof setup, scripts, workflows or diagnostics.

After exact clean CI, next isolated timing batch is word/bit coverage. Current read-only hypotheses:
- word: ADDW, SUBW, MOVW YA,dp likely +1 fixed each; CMPW/INCW/DECW/MOVW dp,YA likely already match total cycles;
- bit: OR1 variants, EOR1, MOV1 mem.bit,C and TSET1/TCLR1 likely each miss one cycle; AND1/MOV1 C,mem/NOT1/SET1/CLR1 likely already match.
These remain **HYPOTHESIS** until dynamic proof.


## Clean CALL/return/BRK + PCALL candidate — checkpoint 2026-09-17/18

Clean branch advanced to **`phase2/apu-timing-foundation@fafc08478bcf918bca4e17e04b9b6c9b4e7a62c8`**, one commit on top of `46230daa...`.

Direct compare `46230daa... -> fafc0847...` is exactly one file:
- `src/apu_control.S` +27/-2.

Patch contents are limited to validated core behavior:
- CALL +3 fixed cycles;
- TCALL +3;
- PCALL +2;
- RET +2;
- RET1 +2;
- BRK +2;
- PCALL target formation moved after `load_stack` so volatile compile-time `t2` is not clobbered.

No scripts, workflows, `apu_map` diagnostic setup, GDB code or PROFILE diagnostics are present.

Exact clean Build and Validate run: **`35302765614`**, IN PROGRESS at checkpoint.

Dynamic authority remains diagnostic `f4da303d...` / ares proof `35302251443` SUCCESS. Accept clean candidate only after normal build + PROFILE build + pinned Mupen smoke succeed on exact SHA `fafc0847...`.

Next technical batch after exact clean CI: dynamically prove the already-mapped word/bit timing hypotheses on diagnostic branch. Keep known H-flag semantic TODOs and TCALL/BRK intra-instruction bus-order debt explicit; do not conflate total-cycle correctness with those unresolved contracts.


## Clean CALL/return/BRK + PCALL foundation — CI VALIDATED 2026-09-17/18

Clean **`phase2/apu-timing-foundation@fafc08478bcf918bca4e17e04b9b6c9b4e7a62c8`** completed **Build and Validate `35302765614` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

Combined authority:
- dynamic timing + semantic proof: diagnostic `f4da303d...`, ares proof `35302251443` SUCCESS;
- clean integration diff: one core file only, `src/apu_control.S`;
- exact clean SHA CI: `35302765614` SUCCESS.

Next isolated variable: SPC700 word-instruction total-cycle coverage. Do not fold bit-family timing into the same experiment.


## SPC700 word timing proof in progress — checkpoint 2026-09-17/18

Exact diagnostic SHA: **`90c700a404f7d5a5abdc65d92e4869a431e7ad2d`**, parent `f4da303d...`.

Controlled core changes:
- `apu_addw`: +1 fixed cycle;
- `apu_subw`: +1 fixed cycle;
- `apu_movwya` (MOVW YA,dp): +1 fixed cycle.
No changes to CMPW, INCW, DECW or MOVW dp,YA controls.

Directed matrix:
- ADDW YA,dp + closing BRA: expected **9 total cycles**, verifies YA result;
- SUBW YA,dp + BRA: **9**, verifies YA result;
- MOVW YA,dp + BRA: **9**, verifies YA load;
- CMPW control + BRA: **8**;
- DECW control + BRA: **10**, verifies two output bytes;
- INCW control + BRA: **10**, verifies two output bytes;
- MOVW dp,YA control + BRA: **9**, verifies two output bytes.

Known semantic limitation intentionally not hidden: ADDW/SUBW source still has `TODO: set the H flag`. This proof validates total timing and chosen data-result postconditions; it does not claim full flag correctness.

Exact workflows:
- **Build and Validate `35302988477`** — IN PROGRESS at checkpoint.
- **APU Cycle And Span Proof `35302988483`** — IN PROGRESS at checkpoint.

Decision rules:
- all seven cases pass => validate the three +1 timing rules and consume only `apu_alu.S` / `apu_transfer.S` core changes cleanly on `fafc0847...`;
- corrected case cycle mismatch => reject/narrow the +1 rule for that opcode;
- control mismatch => stop and repair the timing model before consuming any word changes;
- data semantic mismatch with correct cycles => isolate inherited word-operation correctness separately from timing.

Bit-family hypotheses remain DEFERRED until this word batch closes.


## SPC700 word timing — VALIDATED 2026-09-18

Exact diagnostic authority: **`90c700a404f7d5a5abdc65d92e4869a431e7ad2d`**.

CI:
- **Build and Validate `35302988477` SUCCESS**: normal build, PROFILE build, pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35302988483` SUCCESS**, cycle-proof job **`105469587489`**.
- proof result artifact **`10531230748`**, digest `sha256:d4c061fd78f3e8ae99e8e358e6d51063ed79a953a623358c91a019f22d5baa68`;
- exact proof-build artifact **`10530635328`**, digest `sha256:96cdb5bfce147f4a4ba22535ae1266759380cdbd69a12b5c2c8d9b26a88e8e5e`.

All global proof invariants are true:
- `all_runtime_cycle_debits_match_expected=true`;
- `all_semantics_match_expected=true`;
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

### MEASURED / VALIDATED word cases

Corrected families:
- ADDW YA,dp + BRA: **9 total cycles**, expected YA result passed;
- SUBW YA,dp + BRA: **9**, expected YA result passed;
- MOVW YA,dp + BRA: **9**, expected YA load passed.

Controls with NO timing change required:
- CMPW + BRA: **8 total cycles**;
- DECW + BRA: **10**, both result bytes correct;
- INCW + BRA: **10**, both result bytes correct;
- MOVW dp,YA + BRA: **9**, both written bytes correct.

Therefore the validated fixed rules are exactly:
- `apu_addw`: +1;
- `apu_subw`: +1;
- `apu_movwya`: +1.

Do NOT add timing to CMPW/INCW/DECW/MOVW dp,YA based on this family.

Known semantic debt remains explicit: ADDW/SUBW source still contains `TODO: set the H flag`; this batch validates total timing and selected data results, not full flag fidelity.

### Decision
Consume only the three validated core timing additions into clean `phase2/apu-timing-foundation@fafc0847...`:
- `src/apu_alu.S` ADDW/SUBW +1;
- `src/apu_transfer.S` MOVW YA,dp +1.
Do NOT copy proof script/harness changes.

After exact clean CI, proceed to a separate bit-family timing batch. Current bit hypotheses remain unvalidated until dynamic proof.


## Clean word-timing candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@4a3cf13a54213b401b82bd715a07732b4b8dc66f`**, one commit on top of `fafc0847...`.

Direct clean diff `fafc0847... -> 4a3cf13a...` is exactly:
- `src/apu_alu.S` +8/-0 (ADDW +1, SUBW +1);
- `src/apu_transfer.S` +4/-0 (MOVW YA,dp +1).

No diagnostic scripts/workflows or unrelated core edits.

Exact clean Build and Validate run: **`35306811545`**, QUEUED at checkpoint.

Dynamic word timing/semantic authority remains diagnostic `90c700a4...` / ares proof `35302988483` SUCCESS.

Do not modify clean `4a3cf13a...` until exact CI completes. Next work is read-only mapping of bit-family timing and semantics.


## Clean SPC700 word timing foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@4a3cf13a54213b401b82bd715a07732b4b8dc66f`** completed **Build and Validate `35306811545` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

Combined authority:
- dynamic word timing/semantics: diagnostic `90c700a4...` / ares proof `35302988483` SUCCESS;
- clean integration: exactly `apu_alu.S` +8 and `apu_transfer.S` +4;
- exact clean CI `35306811545` SUCCESS.

## Next isolated variable — bit-family timing

Pinned ares/static mapping yields these hypotheses:

Likely +1 fixed timing:
- OR1 C,mem.bit;
- OR1 C,/mem.bit;
- EOR1 C,mem.bit;
- MOV1 mem.bit,C.

Likely cycle-complete controls:
- AND1 C,mem.bit;
- AND1 C,/mem.bit;
- MOV1 C,mem.bit;
- NOT1 mem.bit;
- SET1 dp.bit;
- CLR1 dp.bit.

Special case:
- TSET1/TCLR1 each need one additional **bus read** before write in pinned ares. A simple +1 fixed debit can validate total cycles for ordinary RAM but is NOT bus-semantically exact for I/O/timer side effects. If timing proof uses +1 fixed, preserve this as explicit fidelity debt and do not claim those opcodes are fully cycle/bus exact.

Next diagnostic batch should validate corrected cases and no-change controls separately, checking total `s3`, carry/RAM postconditions and block span.


## SPC700 bit timing proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`1958dff26eefdafffa849cd2d1b5ca83045230d2`**, one commit after validated word authority `90c700a4...`.

Direct compare is exactly:
- `src/apu_alu.S` +26/-0;
- `scripts/apu_cycle_proof.py` +60/-0.

Controlled timing candidates:
- OR1 C,mem.bit +1 fixed cycle;
- OR1 C,/mem.bit +1;
- EOR1 C,mem.bit +1;
- MOV1 mem.bit,C +1;
- TSET1 +1 total-cycle debit for ordinary RAM;
- TCLR1 +1 total-cycle debit for ordinary RAM.

No-change controls:
- AND1 C,mem.bit;
- AND1 C,/mem.bit;
- MOV1 C,mem.bit;
- NOT1 mem.bit;
- SET1 dp.bit;
- CLR1 dp.bit.

Directed proof checks carry/RAM semantics plus exact total `s3`, static debit and span.

Important limitation for TSET1/TCLR1: pinned ares performs a **second real bus read** before write. This diagnostic uses a fixed +1 debit, which can match ordinary-RAM total cycles but is not I/O/timer side-effect exact. Even if these two cases pass, do not classify them as fully bus-cycle-exact or consume them cleanly without an explicit decision on that semantic debt.

Exact workflows:
- **APU Cycle And Span Proof `35307039329`** — IN PROGRESS at checkpoint.
- **Build and Validate `35307039426`** — IN PROGRESS at checkpoint.

Acceptance:
1. previous regression matrix remains green;
2. corrected OR1/EOR1/MOV1 mem,C cases match reference totals and semantics;
3. no-change controls remain exact without added charges;
4. TSET/TCLR ordinary-RAM cases may establish total timing only, not bus fidelity.


## Bit timing attempt 1 — timing matched, pre-existing carry-persistence bug exposed 2026-09-18

Exact diagnostic SHA **`1958dff26eefdafffa849cd2d1b5ca83045230d2`**:
- **Build and Validate `35307039426` SUCCESS**: normal, PROFILE and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35307039329` FAILURE**, cycle-proof job **`105481467236`**.
- failed proof result artifact **`10532800207`**, digest `sha256:c2c56b360156d1a057f92e8fd0a057ee5fabc15ea480c35a98fa91f27d30e55a`;
- exact proof-build artifact **`10532056467`**, digest `sha256:d45aebc00ea68d6fb321608233ad49196d6c4816af9ac925d81c376e6b680539`.

The proof stopped on the **first new bit case, OR1 C,mem.bit**. Its timing evidence PASSED:
- static debit **-168 = 8 units**, exactly expected;
- total `s3` debit **-189 = 9 cycles**, exactly pinned-reference total;
- span/header checks passed.

The failure was semantic only:
- source bit = 1, initial C=0;
- expected persisted C=1;
- observed `apu_flags_after_block=0`;
- `semantics_match_expected=false`.

### Root cause — SUPPORTED STATIC + dynamic symptom

Inherited carry-modifying bit generators load PSW but do not mark it dirty in compiler state:
- `apu_mov1b` (MOV1 C,mem.bit);
- `apu_or1a`;
- `apu_or1b`;
- `apu_and1a`;
- `apu_and1b`;
- `apu_eor1`.

They call `load_flags` but omit `ori s1,s1,FLAG_SF`. Consequently generated code can modify runtime S1/C inside the block while `finish_block` is not told that PSW must be persisted. OR1's correct timing plus failed persisted carry is consistent with this defect.

State: **CONFIRMED semantic defect for OR1 persistence; HYPOTHESIS for the same missing-dirty cause across the sibling carry-bit generators until rerun.**

Decision:
1. Do NOT change the validated OR1 +1 timing rule based on this failure.
2. Add only the missing `FLAG_SF` dirty marking to all six carry-modifying bit generators.
3. Rerun the same bit matrix unchanged. This will simultaneously test OR1/EOR1/AND1/MOV1 C,bit persistence and continue into the timing/control cases that attempt 1 never reached.
4. TSET/TCLR remain separate: their +1 fixed debit is still diagnostic total-timing only; a bus-exact second-read implementation is planned after the carry persistence rerun.


## Bit carry persistence repair — rerun in progress 2026-09-18

Exact diagnostic HEAD: **`2602249fafb0084b3cbf45d352720e4e1ba73af9`**, one commit after failed bit attempt `1958dff2...`.

Controlled change is exactly one file, **`src/apu_alu.S +6/-6`**:
for `apu_mov1b`, `apu_or1a`, `apu_or1b`, `apu_and1a`, `apu_and1b`, `apu_eor1`, replace the `load_flags` delay-slot `nop` with:
`ori s1, s1, FLAG_SF`.

No timing charge, opcode dispatch, addressing or proof expectation changed.

Hypothesis: this marks PSW dirty so carry modifications that already occur correctly in generated runtime S1 are persisted at block exit. It directly addresses the observed OR1 symptom from `1958dff2...`.

Exact rerun workflows:
- **Build and Validate `35307619439`** — QUEUED at checkpoint.
- **APU Cycle And Span Proof `35307619471`** — QUEUED at checkpoint.

Readings:
- OR1 carry now persists and matrix advances => confirms dirty-flag root cause; continue judging unchanged bit timing rules.
- OR1 still returns C=0 => reject/narrow dirty-flag explanation and inspect generated spill path before further timing work.
- sibling AND/EOR/MOV1 C,bit failure after OR1 passes => family is not uniform; isolate that generator rather than broadening changes.
- TSET/TCLR remain total-timing-only in this rerun; their planned second-real-read repair is separate.


## Bit timing rerun — carry family VALIDATED; TSET/TCLR semantic defect isolated 2026-09-18

Exact diagnostic SHA **`2602249fafb0084b3cbf45d352720e4e1ba73af9`**:
- **Build and Validate `35307619439` SUCCESS**: normal, PROFILE and pinned Mupen smoke green.
- **APU Cycle And Span Proof `35307619471` FAILURE**, cycle-proof job **`105483171401`**.
- failed proof result artifact **`10532446373`**, digest `sha256:871961a769fce9d5fe79913bd4bce0f29687775a01981c3eaeea4ff66369a32f`;
- exact proof-build artifact **`10532302018`**, digest `sha256:03af6d1b7c3862113968eef5449939dec54fd0019d3f6acdde3b7f0a0077be71`.

### VALIDATED before the stop

Carry-persistence repair is confirmed:
- OR1 C,mem.bit: **9 cycles**, C persisted =1, semantic pass;
- OR1 C,/mem.bit: **9**, pass;
- EOR1 C,mem.bit: **9**, pass;
- MOV1 mem.bit,C: **10**, memory write pass;
- AND1 C,mem.bit control: **8**, C persistence pass;
- AND1 C,/mem.bit control: **8**, pass;
- MOV1 C,mem.bit control: **8**, pass;
- NOT1 control: **9**, memory pass;
- SET1 dp.bit control: **8**, memory pass;
- CLR1 dp.bit control: **8**, memory pass.

Thus the missing `FLAG_SF` dirty marking was the cause of the OR1 persistence defect and the six-generator family repair is **VALIDATED** for the reached carry-modifying cases.

Timing rules validated by these cases:
- OR1 normal/inverted +1 fixed;
- EOR1 +1 fixed;
- MOV1 mem.bit,C +1 fixed;
- AND1 variants / MOV1 C,mem / NOT1 / SET1 / CLR1 require no added fixed timing.

### TSET1 result — timing correct, flags wrong

`tset1_ram_total` measured:
- static debit **-168 = 8 units**, expected;
- total debit **-210 = 10 cycles**, exact reference total;
- RAM `0x0F -> 0xFF`, correct;
- observed PSW **0x02 (Z=1)**, expected **0x80 (N=1)** for `A=0xF0, data=0x0F`;
- semantic check failed, so TCLR1 was not reached.

**SUPPORTED ROOT CAUSE:** current generated order computes `SUB T0,T7,V0` in the delay slot of runtime `JAL apu_write8`; `apu_write8` then clobbers T0 before the subsequently emitted `queue_nz` instruction reads it. The comparison used for N/Z is therefore not preserved.

### Decision — repair TSET/TCLR semantically and bus-correctly

Do NOT consume the diagnostic fixed +1 TSET/TCLR charge.

Next controlled change:
1. remove TSET/TCLR fixed +1 charge;
2. compute A-first-read comparison and emit `queue_nz` **before** any helper call that can clobber T0;
3. emit the pinned-reference **second real `apu_read8`** to the same address;
4. preserve final write data through that read in A1 (all audited APU read paths do not touch A1; A2 used by queued NZ is also untouched);
5. emit the write using the first read's data;
6. update TSET/TCLR expected static debit from -168 to **-147**, while total remains **10 cycles** via 3 runtime memory accesses.

Expected: TSET PSW becomes N=1/Z=0, TCLR semantic case runs, both totals remain 10. Falsifier: changed total, wrong RAM/flags, or evidence A1/A2 are clobbered by a read path.


## TSET/TCLR bus-exact repair — proof in progress 2026-09-18

Exact diagnostic HEAD: **`df5fd66c76d5b3898a6c5d6020aacfff38e8daf5`**, one commit after carry-persistence authority `2602249f...`.

Controlled change:
- remove TSET/TCLR fixed +1 synthetic debit;
- preserve the first-read comparison into queued NZ before helper calls;
- emit the pinned-reference **second real `apu_read8`** to the same address;
- derive write data from the first read in that JAL delay slot and preserve it in A1;
- emit `apu_write8` afterward;
- A1/A2 preservation was statically audited across all current APU read paths.

Proof expectations change only for TSET/TCLR static debit:
- **-168 -> -147** (8 -> 7 static units);
- total reference remains **10 cycles**, now from three runtime memory accesses rather than two accesses + synthetic fixed cycle;
- RAM and PSW semantic expectations are unchanged.

Direct compare `2602249f... -> df5fd66c...`:
- `src/apu_alu.S` +29/-21;
- `scripts/apu_cycle_proof.py` +4/-5.

Exact workflows:
- **Build and Validate `35308254510`** — IN PROGRESS at checkpoint.
- **APU Cycle And Span Proof `35308254504`** — IN PROGRESS at checkpoint.

Acceptance:
1. all previously validated bit/carry/control cases remain green;
2. TSET1 total remains 10, RAM remains correct, PSW becomes N=1/Z=0 for directed case;
3. TCLR1 reaches execution and passes 10-cycle/RAM/PSW case;
4. no synthetic runtime cycle-debit instruction is needed for these instructions.


## SPC700 bit-family timing + semantics — VALIDATED 2026-09-18

Exact diagnostic authority: **`df5fd66c76d5b3898a6c5d6020aacfff38e8daf5`**.

CI:
- **Build and Validate `35308254510` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke green.
- **APU Cycle And Span Proof `35308254504` SUCCESS**, cycle-proof job **`105484997903`**.
- proof result artifact **`10531889516`**, digest `sha256:e51ef26ec7ccab0f85f1c4c2b6992bc554cf596d24854f408744deaaccb71427`;
- exact proof-build artifact **`10532298069`**, digest `sha256:a9d5fe5a8c2137b7b47fd900263c97a0d0388e5ce10071ec0a2ab86e52636a41`.

All global proof invariants are true:
- `all_runtime_cycle_debits_match_expected=true`;
- `all_semantics_match_expected=true`;
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

### VALIDATED bit-family cases

Added timing:
- OR1 C,mem.bit = **9 total cycles**, C persistence correct;
- OR1 C,/mem.bit = **9**, correct;
- EOR1 C,mem.bit = **9**, correct;
- MOV1 mem.bit,C = **10**, memory correct.

No-added-timing controls remain exact:
- AND1 C,mem.bit = **8**;
- AND1 C,/mem.bit = **8**;
- MOV1 C,mem.bit = **8**;
- NOT1 mem.bit = **9**;
- SET1 dp.bit = **8**;
- CLR1 dp.bit = **8**.

Carry-modifying bit generators now correctly mark PSW dirty via `FLAG_SF`; OR1/AND1/EOR1/MOV1 C,mem persistence passes.

TSET1/TCLR1 are now both timing- and bus-semantics-correct for the audited access pattern:
- TSET1: static **7 units**, three runtime memory accesses, **10 total cycles**, RAM `0x0F -> 0xFF`, PSW **0x80** (N=1/Z=0);
- TCLR1: static **7 units**, three runtime accesses, **10 total cycles**, RAM `0xFF -> 0xF0`, PSW **0x00**.

The previous synthetic +1 TSET/TCLR debit is **SUPERSEDED**. The validated implementation performs the second real `apu_read8` required by the pinned reference and preserves first-read-derived data/NZ across helper calls.

### Clean-consumption proof
`src/apu_alu.S` at clean foundation `4a3cf13a...` and diagnostic pre-bit authority `90c700a4...` have the **same blob SHA `ec2fbd2a00da7512f11b7a1ca89c807ced891b16`**. Diagnostic target blob `df5fd66c...` is `6bf7db555f2adf4a38c76b9b637cd4aae670ec5c` and contains no diagnostic/PROFILE references.

Decision: consume exactly that one core file into clean `phase2/apu-timing-foundation@4a3cf13a...`, then require exact clean Build/Validate before the next timing family.


## Clean bit timing/state candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@0fe8c45f9b1b1c719d52490d8f233950b4d4c489`**, one commit on top of clean word foundation `4a3cf13a...`.

Direct clean diff is exactly one core file:
- `src/apu_alu.S` +51/-17.

No diagnostic script/workflow changes.

Included validated bit work:
- OR1 normal/inverted +1 timing;
- EOR1 +1;
- MOV1 mem.bit,C +1;
- PSW dirty persistence for carry-modifying bit generators;
- TSET1/TCLR1 second real read, preserved first-read data/NZ, exact 10-cycle behavior.

Exact clean Build and Validate run: **`35308801632`**, QUEUED at checkpoint.

Dynamic semantic/cycle authority remains `df5fd66c...` / ares proof `35308254504` SUCCESS.

Do not modify clean `0fe8c45f...` until exact CI completes.

### Next read-only mapped timing family

Static comparison against pinned ares identifies a bounded remaining operand-form cluster:
- CMP dp,dp: likely +1 trailing idle;
- CMP dp,#imm: likely +1 trailing idle;
- `(X),(Y)` modifying ops: likely +1 dummy PC read;
- CMP `(X),(Y)`: likely +1 dummy PC read plus +1 trailing idle;
- MOV dp,#imm: missing a real dummy destination read before write; should prefer emitting the real `apu_read8` rather than a synthetic +1 debit.

JMP [abs+X] appears already covered by the validated indexed-addressing +1 and two runtime reads; treat as a no-change control, not a candidate fix.


## Clean bit timing/state foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@0fe8c45f9b1b1c719d52490d8f233950b4d4c489`** completed **Build and Validate `35308801632` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

Combined authority:
- dynamic bit timing/state/bus semantics: diagnostic **`df5fd66c76d5b3898a6c5d6020aacfff38e8daf5`**, APU Cycle And Span Proof **`35308254504` SUCCESS**;
- clean core consumption: `0fe8c45f...`;
- exact clean CI: `35308801632` SUCCESS.

Do not reopen the superseded synthetic TSET/TCLR +1 implementation: the validated path performs the real second read.

## Next controlled timing cluster — operand forms

Static comparison against pinned ares plus current generator structure yields a bounded three-rule experiment:

1. **CMP memory-form trailing idle**
   - `CMP dp,dp` (0x69) needs +1 trailing idle;
   - `CMP dp,#imm` (0x78) needs +1;
   - `CMP (X),(Y)` (0x79) needs the same +1 in addition to the addressing dummy cycle below.
   - Natural implementation point: `apu_cmpm`, because all three forms share it and modifying siblings do not.

2. **`(X),(Y)` dummy-PC cycle**
   - modifying forms OR/AND/EOR/ADC/SBC `(X),(Y)` need +1 dummy PC read cycle;
   - CMP `(X),(Y)` needs this +1 plus the CMP trailing idle.
   - Natural implementation point: `apu_bxy`.
   - This is a timing debit, consistent with the already validated treatment of dummy PC reads elsewhere; no claim of a separately observable bus read is made.

3. **MOV dp,#imm destination dummy read**
   - opcode 0x8F requires a real destination read before write;
   - opcode 0xFA MOV dp,dp is a no-change control and must NOT gain the extra read.
   - Use a dedicated `apu_movmi` handler for 0x8F rather than changing generic `apu_movm`.
   - Generated sequence: preserve immediate in A1 in the dummy-read JAL delay slot; `apu_read8` preserves A0/A1; then `apu_write8` to the same A0.
   - This reproduces the actual helper/bus access instead of a synthetic +1.

Directed proof matrix should include:
- CMP dp,dp;
- CMP dp,#imm;
- CMP (X),(Y);
- OR (X),(Y) modifying control for `apu_bxy`;
- MOV dp,#imm candidate;
- MOV dp,dp no-change control.

Expected totals including the existing 4-cycle BRA loop:
- CMP dp,dp: 10;
- CMP dp,#imm: 9;
- CMP (X),(Y): 9;
- OR (X),(Y): 9;
- MOV dp,#imm: 9;
- MOV dp,dp: 9.

Falsifiers: any shared-generator control overcharges, total `s3` differs, destination/data semantics differ, or new real-read path clobbers state.


## SPC700 operand-form timing proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`1dc544fa64a0d0fd9984bc94c492d0306766bf7a`**, one commit after validated bit-family authority `df5fd66c...`.

Direct compare `df5fd66c... -> 1dc544fa...` is exactly:
- `scripts/apu_cycle_proof.py` +32/-0;
- `src/apu_address.S` +4/-0;
- `src/apu_alu.S` +4/-0;
- `src/apu_emitter.S` +1/-1;
- `src/apu_transfer.S` +17/-0.

Controlled core rules:
- `apu_cmpm`: +1 trailing internal idle for memory-form CMP;
- `apu_bxy`: +1 dummy-PC timing cycle for `(X),(Y)` forms;
- opcode **0x8F MOV dp,#imm** dispatches to dedicated `apu_movmi`, which performs a real destination `apu_read8` before `apu_write8`; opcode 0xFA remains on generic `apu_movm`.

Directed cases and expected totals including the validated 4-cycle BRA loop:
- CMP dp,dp = 10;
- CMP dp,#imm = 9;
- CMP (X),(Y) = 9;
- OR (X),(Y) = 9;
- MOV dp,#imm = 9;
- MOV dp,dp no-change control = 9.

Exact workflows:
- **APU Cycle And Span Proof `35313083578`** — IN PROGRESS at checkpoint.
- **Build and Validate `35313083584`** — IN PROGRESS at checkpoint.

Acceptance:
1. previous complete regression matrix remains green;
2. three CMP cases match total timing and C/N/Z semantics;
3. OR `(X),(Y)` proves the shared `apu_bxy` +1 without overcharging a modifying sibling;
4. MOV dp,#imm gains exactly one real read and writes the immediate correctly;
5. MOV dp,dp remains exact and unchanged.

Falsifier: any total/static debit mismatch, shared-handler control overcharge, data/flags mismatch, or state clobber from the added real read.


## SPC700 operand-form timing — VALIDATED 2026-09-18

Exact diagnostic authority: **`1dc544fa64a0d0fd9984bc94c492d0306766bf7a`**.

CI:
- **Build and Validate `35313083584` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke green.
- **APU Cycle And Span Proof `35313083578` SUCCESS**, cycle-proof job **`105499188711`**.
- proof result artifact **`10533722861`**, digest `sha256:6f82bc03c9cc813facf2466f8c875540fa400f3f7e650444e850c731e642ba96`;
- exact proof-build artifact **`10533672483`**, digest `sha256:cb3d1956b9812f95ad76f7bf346309116bef745e444621ea48151cade3ecb22b`.

All global proof invariants remain true:
- `all_runtime_cycle_debits_match_expected=true`;
- `all_semantics_match_expected=true`;
- `all_static_debits_match_source_prediction=true`;
- `all_total_debits_match_reference=true`;
- `compiled_long_probe_is_bounded_to_one_tag_region=true`.

### VALIDATED cases

- CMP dp,dp: static **8 units**, **10 total cycles**, C/N/Z postcondition correct.
- CMP dp,#imm: static **8**, **9 total**, flags correct.
- CMP (X),(Y): static **7**, **9 total**, flags correct.
- OR (X),(Y): static **6**, **9 total**, destination RAM correct; validates shared `apu_bxy` +1 without overcharge.
- MOV dp,#imm: static **7**, **9 total**, destination receives immediate correctly with the added real dummy read.
- MOV dp,dp control: static **7**, **9 total**, unchanged generic path remains correct.

Therefore the validated core rules are:
- `apu_cmpm`: +1 trailing internal idle;
- `apu_bxy`: +1 dummy-PC timing cycle;
- opcode 0x8F uses dedicated `apu_movmi` with a real destination read then write;
- opcode 0xFA remains on generic `apu_movm`.

### Clean-consumption note

Clean `0fe8c45f...` and diagnostic base `df5fd66c...` are byte-identical for:
- `src/apu_address.S`;
- `src/apu_alu.S`;
- `src/apu_transfer.S`.

`src/apu_emitter.S` differs only because the diagnostic branch carries a PROFILE-only cycle-proof observation block around block finalization. The direct diagnostic-base -> validated-target emitter change is exactly one opcode-table substitution:
- 0x8F `apu_movm -> apu_movmi`.

Decision: consume the three validated core blobs directly into clean foundation and apply only the single 0x8F table substitution to the clean emitter. Do NOT copy the diagnostic PROFILE block or proof script.


## Clean operand-form timing candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@68958b689750cbcdb2d703679b1a975858186637`**, one commit on top of clean bit foundation `0fe8c45f...`.

Direct clean diff is exactly four core files:
- `src/apu_address.S` +4/-0;
- `src/apu_alu.S` +4/-0;
- `src/apu_emitter.S` +1/-1;
- `src/apu_transfer.S` +17/-0.

No diagnostic script/workflow changes. Clean `apu_emitter.S` contains no `SODIUM64_PROFILE` / `apu_cycle_diag` references.

Included validated operand-form work:
- `apu_cmpm` +1 trailing idle;
- `apu_bxy` +1 dummy-PC timing cycle;
- dedicated 0x8F `apu_movmi` destination real-read + write;
- 0xFA remains on generic `apu_movm`.

Dynamic authority: diagnostic `1dc544fa...`, APU Cycle And Span Proof `35313083578` SUCCESS.
Diagnostic Build and Validate `35313083584` SUCCESS.

Exact clean Build and Validate run: **`35313761832`**, QUEUED at checkpoint.

Do not modify clean `68958b68...` until exact CI completes.


## Clean operand-form timing foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@68958b689750cbcdb2d703679b1a975858186637`** completed **Build and Validate `35313761832` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

Combined authority:
- dynamic operand-form timing/semantics: diagnostic **`1dc544fa64a0d0fd9984bc94c492d0306766bf7a`**, APU Cycle And Span Proof **`35313083578` SUCCESS**;
- clean core consumption: `68958b68...`;
- exact clean CI: `35313761832` SUCCESS.

## RESUME HERE — 2026-09-18 current authoritative state

### Phase / gate
- Road phase: **M1 faster/correcter base core**, APU/SPC700 timing foundation remains the active gate driver.
- This work primarily advances **Gate A / Gate C correctness prerequisites** and changes the validity of future Gate B performance measurements: configured `apu_clock=21` is no longer being treated as sufficient proof of effective full-rate SPC700 timing.

### Exact repo state
- `master`: **`a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`** — integrated truth, unchanged by this timing series.
- clean candidate: **`phase2/apu-timing-foundation@68958b689750cbcdb2d703679b1a975858186637`**.
- diagnostic authority: **`phase2/apu-cycle-proof@1dc544fa64a0d0fd9984bc94c492d0306766bf7a`**.
- no claim that the clean candidate is merged into master.

### Validated timing/state foundation now includes
- bounded JIT block behavior / NOP boundary repair already consumed earlier in this branch;
- fixed implied/register-transfer/stack timing;
- conditional/taken branch timing;
- CALL/TCALL/PCALL/RET/RET1/BRK timing and PCALL target repair;
- ADDW/SUBW/MOVW YA,dp word timing;
- absolute bit timing and carry-PSW persistence;
- bus-exact TSET1/TCLR1 second read + flags/data preservation;
- CMP memory-form trailing idle;
- `(X),(Y)` dummy-PC timing;
- bus-real MOV dp,#imm destination read;
- no-change controls for sibling/shared paths.

### Exact latest authorities
- bit-family proof `df5fd66c...` / run `35308254504` SUCCESS;
- clean bit foundation `0fe8c45f...` / run `35308801632` SUCCESS;
- operand-form proof `1dc544fa...` / run `35313083578` SUCCESS;
- clean operand foundation `68958b68...` / run `35313761832` SUCCESS.

### What this proves
- the directed SPC700 families above now match pinned-reference **total guest cycle debit** and the checked register/RAM/PSW semantics in the ares laboratory;
- all historical cases in the growing regression matrix still pass together;
- the latest clean candidate compiles and survives independent pinned Mupen smoke.

### What this does NOT prove
- complete 256-opcode SPC700 semantic/timing correctness;
- correct DSP PCM/echo/FIR/pitch-modulation fidelity;
- native cadence or performance improvement on real N64;
- that Gothicvania now reaches a higher frame budget;
- Gate B/C completion.

### Immediate next uncertainty
Before re-baselining performance, determine whether any **material SPC700 opcode/timing holes remain outside the validated families**. In particular inspect:
- opcode-table entries still mapped to `apu_unk`;
- explicit APU TODOs affecting arithmetic flags/semantics;
- any remaining pinned-reference dummy reads/idles not represented by existing addressing/operation generators.

Decision rule:
- if remaining gaps are bounded REQUIRED SUPPORT / correctness items, finish them first and then establish a new matched performance baseline;
- if the remaining gaps are only low-priority edge semantics that do not affect the current representative workload, record/defer them and re-baseline `68958b68...` before further optimization.

Do not resume Experiment 2B memory-helper optimization until this timing foundation has a new trustworthy baseline.


## Remaining SPC700 semantic inventory — 2026-09-18

Read-only scan of clean `phase2/apu-timing-foundation@68958b68...` found concrete remaining base-core gaps.

### REQUIRED SUPPORT — unimplemented opcodes
Opcode table still maps exactly four base SPC700 opcodes to `apu_unk`:
- **0xBE DAS A**;
- **0xDF DAA A**;
- **0xEF SLEEP/WAIT**;
- **0xFF STOP**.

Current `apu_unk` intentionally loops forever, so these are real compatibility holes, not minor timing approximations.

### OPEN semantic TODOs — Half-Carry / arithmetic
Seven explicit `TODO: set the H flag` sites remain:
- `apu_adca` — ADC accumulator forms;
- `apu_adcm` — ADC memory-modify forms;
- `apu_sbca` — SBC accumulator forms;
- `apu_sbcm` — SBC memory-modify forms;
- `apu_addw`;
- `apu_subw`;
- `apu_div`.

These are not one uniform change:
- ADC/SBC 8-bit share one nibble half-carry/borrow rule;
- ADDW/SUBW use the 16-bit word half-carry rule;
- DIV has special S-SMP H/V/result behavior and current simple MIPS DIV path needs separate semantic validation.

### Decision / order
Do NOT re-baseline performance yet; the remaining gaps are bounded base-SPC700 correctness work and therefore qualify as REQUIRED SUPPORT before declaring the timing foundation representative.

Proceed one semantic family at a time:
1. ADC/SBC 8-bit H flag proof + repair;
2. ADDW/SUBW H flag proof;
3. DIV semantic proof/repair;
4. DAA/DAS implementation once H/C prerequisites are trustworthy;
5. SLEEP/STOP scheduler semantics separately.

Each family must retain the full existing cycle/address/state regression matrix. Do not bundle WAIT/STOP scheduler behavior with arithmetic work.


## SPC700 ADC/SBC 8-bit Half-Carry proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`29aba03ab3eb07401cd521092e11aedc3436582e`**, one commit after operand-form proof authority `1dc544fa...`.

Direct compare `1dc544fa... -> 29aba03a...` is exactly:
- `src/apu_alu.S` +22/-4;
- `scripts/apu_cycle_proof.py` +28/-0.

Controlled semantic change only; **no guest cycle charge/addressing/dispatch change**.

Pinned ares reference:
- ADC: `HF = (x ^ y ^ result) & 0x10`;
- SBC reuses ADC with `~y`.

Candidate implementation updates exactly:
- `apu_adca`;
- `apu_adcm`;
- `apu_sbca`;
- `apu_sbcm`.

Directed matrix explicitly tests:
- ADC immediate H set;
- ADC immediate H clear from an initially-set H;
- SBC immediate H set;
- SBC immediate H clear from an initially-set H;
- ADC direct-page memory-modify H set;
- SBC direct-page memory-modify H set.

Timing expectations are unchanged. Any `s3`/static debit movement is a regression.

Exact workflows:
- **Build and Validate `35314192559`** — IN PROGRESS at checkpoint.
- **APU Cycle And Span Proof `35314192576`** — IN PROGRESS at checkpoint.

Acceptance:
1. H sets and clears exactly per pinned reference;
2. C/N/Z/V and data/register postconditions remain correct in directed cases;
3. accumulator and memory-modify generators agree;
4. exact guest cycle debit is unchanged;
5. entire existing timing/address/state regression matrix stays green.

Falsifiers:
- H remains stale when expected clear;
- SBC half-borrow polarity differs;
- accumulator vs memory form diverges;
- any total/static debit changes;
- any prior regression case fails.


## SPC700 ADC/SBC 8-bit Half-Carry — VALIDATED 2026-09-18

Exact diagnostic authority: **`29aba03ab3eb07401cd521092e11aedc3436582e`**.

CI:
- **Build and Validate `35314192559` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35314192576` SUCCESS**, cycle-proof job **`105502513799`**.
- proof result artifact **`10534743489`**, digest `sha256:fb25c9d2a9a71bd9a7117f953e95c9b42742011feb602e5a474eedfff50abe34`;
- exact proof-build artifact **`10533703688`**, digest `sha256:c90c229be2631974237d128427a73aba816acbf63a36d5e09ebbe662d5aab7d5`.

Directed cases all passed with unchanged timing:
- ADC immediate H set: A=0x10, H=1, **6 cycles**;
- ADC immediate H clear from initial H=1: A=0x02, H=0, **6 cycles**;
- SBC immediate H set: A=0x10, C/H=1, **6 cycles**;
- SBC immediate H clear from initial H=1: A=0x0F, C=1/H=0, **6 cycles**;
- ADC dp,#imm memory-modify: RAM result 0x10, H=1, **9 total cycles**;
- SBC dp,#imm memory-modify: RAM result 0x10, C/H=1, **9 total cycles**.

All global proof invariants remained true:
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

Validated core rule:
- ADC: H from bit 4 of `x ^ y ^ result`;
- SBC: equivalent half-borrow polarity using the existing complemented-operand subtraction path.

No guest timing changes were introduced.

### Decision
Consume only `src/apu_alu.S` core changes into clean timing foundation. Then run exact clean CI. Next isolated arithmetic semantic family: ADDW/SUBW H flag.


## Clean ADC/SBC Half-Carry candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@c2f2ecc1dfd521be724a832761db45d514ce2265`**, one commit on top of `68958b68...`.

Direct clean diff is exactly:
- `src/apu_alu.S` +22/-4.

No timing charge, addressing, dispatch, diagnostic script or workflow changes.

Dynamic semantic authority:
- diagnostic `29aba03a...`;
- Build and Validate `35314192559` SUCCESS;
- APU Cycle And Span Proof `35314192576` SUCCESS.

Exact clean Build and Validate run: **`35314885462`**, IN PROGRESS at checkpoint.

Do not modify clean `c2f2ecc1...` until exact CI completes. Next diagnostic work is isolated ADDW/SUBW H semantics on `phase2/apu-cycle-proof`.


## Clean ADC/SBC Half-Carry foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@c2f2ecc1dfd521be724a832761db45d514ce2265`** completed **Build and Validate `35314885462` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

## SPC700 ADDW/SUBW Half-Carry proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`06edb6afb10bc54dd79f6539c7484aad1b0d3469`**, one commit after ADC/SBC H authority `29aba03a...`.

Direct compare is exactly:
- `src/apu_alu.S` +13/-4;
- `scripts/apu_cycle_proof.py` +29/-0.

Controlled semantic change only; timing/addressing/dispatch unchanged.

Pinned reference semantics:
- ADW is two chained ADCs; final H is the high-byte nibble half-carry, equivalent to whole-word bit 12 of `x ^ y ^ result`.
- SBW is two chained SBCs; final H is the inverted whole-word bit-12 half-borrow relation.

Directed matrix:
- ADDW H set via low-byte carry into high byte;
- ADDW H clear from initially-set H;
- SUBW H set via low-byte borrow path;
- SUBW H clear via low-byte borrow path.

All four retain the already validated **9 total guest cycles**. Any s3/static debit movement is a regression.

Exact workflows:
- **Build and Validate `35315076872`** — QUEUED at checkpoint.
- **APU Cycle And Span Proof `35315076871`** — IN PROGRESS at checkpoint.

Acceptance:
1. A/Y results exact;
2. H set/clear exact;
3. C/N/Z/V remain correct for directed cases;
4. total/static cycles unchanged;
5. entire prior regression matrix remains green.


## SPC700 ADDW/SUBW Half-Carry — VALIDATED 2026-09-18

Exact diagnostic authority: **`06edb6afb10bc54dd79f6539c7484aad1b0d3469`**.

CI:
- **Build and Validate `35315076872` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35315076871` SUCCESS**, cycle-proof job **`105505142348`**.
- proof result artifact **`10535525484`**, digest `sha256:1389cc5dde25b485506c3e35e5e1e3af4b69ec2bf395ad761fd6657437098ef0`;
- exact proof-build artifact **`10535025192`**, digest `sha256:0d6597be2a80960cdcc8dc8eeda88b2c4da7e37bf90a6ea631201da9617b2d85`.

Directed word-H cases all passed at unchanged **9 total guest cycles**:
- ADDW H set via low-byte carry: YA 0x0FFF + 0x0001 -> **0x1000**, H=1;
- ADDW H clear from initial H=1: 0x0100 + 0x0100 -> **0x0200**, H=0;
- SUBW H set via low-byte borrow path: 0x1100 - 0x0001 -> **0x10FF**, C/H=1;
- SUBW H clear via low-byte borrow path: 0x1000 - 0x0001 -> **0x0FFF**, C=1/H=0.

All global invariants remained true:
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

Validated rules:
- ADDW H = whole-word bit 12 of `x ^ y ^ result`;
- SUBW H = inverted whole-word bit-12 half-borrow relation.

No timing changes were introduced.

### Decision
Consume only `src/apu_alu.S` core changes into clean timing foundation. Then exact clean CI. Next semantic family: DIV YA,X, which requires full result/H/V behavior proof, not just a flag patch.


## Clean ADDW/SUBW Half-Carry candidate — checkpoint 2026-09-18

Clean branch is **`phase2/apu-timing-foundation@74455bb8ae15b7b654eef7f9812a65db7ccdd964`**, consuming only validated `src/apu_alu.S` changes from diagnostic `06edb6af...`.

Exact clean Build and Validate run: **`35315787073`**, IN PROGRESS at checkpoint.

Dynamic authority remains:
- `06edb6af...`;
- Build and Validate `35315076872` SUCCESS;
- APU Cycle And Span Proof `35315076871` SUCCESS.

## DIV YA,X semantic defect — dynamic baseline before repair

Existing regression case `div_bra` on diagnostic run `35315076871` provides a direct pre-repair observation with default injected state:
- X = **0x04**;
- Y = **0x5A**;
- A = **0x11**;
- inherited DIV+BRA total timing = **16 cycles**, correctly measured.

Observed inherited Sodium64 result:
- A = **0x84**;
- Y = **0x01**;
- PSW = **0xC0**.

Pinned ares/S-SMP reference for the same DIV input:
- H = `(Y & 0x0F) >= (X & 0x0F)` => 1;
- V = `Y >= X` => 1;
- because `Y >= 2*X`, DIV must use the S-SMP overflow branch, not ordinary integer division;
- expected A = **0xAC**;
- expected Y = **0x61**;
- expected N=1, Z=0, H=1, V=1 => PSW arithmetic bits **0xC8**.

Therefore the inherited DIV implementation is **CONFIRMED semantically wrong**, not merely missing H:
- normal MIPS DIV is used unconditionally;
- overflow-branch A/Y behavior is absent;
- H is absent;
- X=0 behavior is also not safely modeled by the inherited direct MIPS DIV path.

Timing itself (12-cycle DIV + 4-cycle BRA) is already validated and must remain unchanged.

### Next controlled DIV repair
Use a dedicated runtime assembly helper called by generated DIV JIT code. It will:
- preserve C/I/B/P and clear/recompute H/V;
- set H and V from original Y/X;
- use normal quotient/remainder only when `Y < 2*X`;
- otherwise reproduce the S-SMP overflow formula;
- handle X=0 through the overflow formula, avoiding undefined divide-by-zero behavior;
- leave N/Z to the existing queued-A mechanism.

Directed proof cases must cover:
1. normal branch, V/H clear;
2. normal branch with quotient >255 and V/H set;
3. known failing overflow case X=4,Y=0x5A,A=0x11;
4. overflow case with H clear;
5. X=0;
6. unchanged **16 total cycles** and full historical regression matrix.


## Clean ADDW/SUBW Half-Carry foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@74455bb8ae15b7b654eef7f9812a65db7ccdd964`** completed **Build and Validate `35315787073` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

## SPC700 DIV semantic repair proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`18c25ce797ff49957da99cb0a31aef30a661fdfc`**, one commit after ADDW/SUBW H authority `06edb6af...`.

Direct compare is exactly:
- `src/apu_alu.S` +64/-17;
- `scripts/apu_cycle_proof.py` +32/-0.

Controlled repair:
- retain existing validated DIV timing: opcode fetch + 11 extra cycles = **12-cycle DIV**;
- replace unconditional normal MIPS division with one generated JAL to a dedicated runtime helper;
- helper recomputes H/V from original Y/X;
- normal arithmetic only when `Y < 2*X`;
- otherwise reproduce the S-SMP overflow formula;
- X=0 necessarily takes the special path, avoiding undefined divide-by-zero;
- N/Z still use the existing queued-A mechanism;
- C/I/B/P are preserved.

Directed semantic matrix, all still **16 cycles including trailing BRA**:
1. normal branch with H/V clear and preserved C;
2. normal branch with 9-bit quotient and H/V set;
3. known inherited failure X=4,Y=0x5A,A=0x11;
4. overflow branch with H clear;
5. X=0;
6. zero-result N/Z path.

Exact workflows:
- **APU Cycle And Span Proof `35316149582`** — IN PROGRESS at checkpoint.
- **Build and Validate `35316149675`** — IN PROGRESS at checkpoint.

Acceptance:
- all six A/Y outputs match pinned reference;
- H/V/N/Z exact and C preserved where directed;
- static/total guest debit unchanged;
- full historical regression matrix remains green;
- normal/PROFILE build and Mupen smoke remain green.


## DIV repair attempt 1 — helper arithmetic correct; MIPS JAL delay-slot bug in N/Z queue 2026-09-18

Exact diagnostic SHA **`18c25ce797ff49957da99cb0a31aef30a661fdfc`**:
- **Build and Validate `35316149675` SUCCESS**: normal, PROFILE and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35316149582` FAILURE**, cycle-proof job `105508379053`.
- failed proof result artifact **`10535217649`**, digest `sha256:276e5c96276ee443e4861154e3871b55cd0ac73fcdba21afb99bd601d16f7b0a`;
- exact proof-build artifact **`10534902330`**, digest `sha256:049ea06b575bd18a044b68ca550049e03b1bff850dcfdeeede36608de1175a43`.

### What passed before the failure

The runtime helper fixed the previously confirmed DIV arithmetic defect for the historical default case:
- X=0x04, Y=0x5A, A=0x11;
- repaired A=**0xAC**, Y=**0x61**;
- H/V=1/1;
- total timing remains **16 cycles including BRA**.

Directed normal case also passed:
- X=4, Y=1, A=8 -> A=0x42, Y=0;
- expected preserved C, H/V/N/Z clear;
- exact 16-cycle total.

Attempt stopped on `div_normal_9bit_quotient`:
- actual A=0x40, Y=0: arithmetic is correct;
- H/V are correct;
- total/static timing is correct;
- observed PSW **0x4A** vs expected **0x48**, i.e. Z remained set incorrectly.

### Root cause — CONFIRMED from generated-code ordering

The provisional interpretation that N/Z were being derived from Y is **REJECTED**.

`apu_div` emitted:
1. JAL to `apu_div_runtime`;
2. immediately afterward the instruction generated by `queue_nz`: `ANDI A2,T7,0xFF`.

On MIPS, instruction #2 is the **JAL delay slot** and therefore executes *before* entering the runtime helper. It queues the **old A**, not repaired A.

This exactly explains both observations:
- default old A=0x11 -> neither N nor Z, producing H/V-only 0x48 instead of expected 0xC8 despite repaired A=0xAC;
- 9-bit case old A=0x00 -> Z=1, producing 0x4A despite repaired A=0x40.

The runtime helper does not clobber A2; the defect is purely emitted instruction ordering.

### Decision

Keep the runtime DIV arithmetic helper unchanged. Insert one generated MIPS NOP (`SLL ZERO,ZERO,0`) immediately after emitted helper JAL so the JAL delay slot is neutral. Then `queue_nz` executes after helper return and snapshots new T7/A.

Do not change guest cycle accounting or proof expectations. Rerun the identical six-case DIV matrix plus full regression suite.


## DIV repair attempt 2 — delay-slot correction in progress 2026-09-18

Exact diagnostic SHA: **`f3bad9af878b94e7be3a2f3f1d0d04fa8db103ec`**, one commit after failed-but-informative DIV helper SHA `18c25ce...`.

Direct compare `18c25ce... -> f3bad9af...` is exactly:
- `src/apu_alu.S` +2/-0.

Controlled change:
- emit one runtime MIPS NOP (`SLL ZERO,ZERO,0`) immediately after the generated JAL to `apu_div_runtime`;
- no guest timing, arithmetic, flags formula, dispatch or harness expectation change.

Question: does neutralizing the JAL delay slot make queued N/Z sample repaired T7/A after helper return while leaving the already-correct A/Y/H/V and 16-cycle DIV+BRA total unchanged?

Exact workflows:
- **Build and Validate `35317084579`** — QUEUED at checkpoint.
- **APU Cycle And Span Proof `35317084547`** — IN PROGRESS at checkpoint.

Acceptance:
- all six directed DIV cases pass A/Y/H/V/N/Z;
- known overflow case becomes A=0xAC,Y=0x61,PSW arithmetic=0xC8;
- 9-bit normal case becomes A=0x40,Y=0,PSW H/V=0x48 with Z clear;
- X=0 passes without divide-by-zero;
- all total/static timing remains unchanged;
- complete historical regression matrix remains green.


## SPC700 DIV semantic repair — VALIDATED 2026-09-18

Final diagnostic authority: **`f3bad9af878b94e7be3a2f3f1d0d04fa8db103ec`**.

CI:
- **Build and Validate `35317084579` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35317084547` SUCCESS**, cycle-proof job **`105511291125`**.
- proof result artifact **`10535762581`**, digest `sha256:eccf0a9ad14818f32097858126ba015805eec458de3413ab2ca3fa1960197da6`;
- exact proof-build artifact **`10535992426`**, digest `sha256:9a452e37cb0d70ed2b2d5f903b1886822a3f5cb7945281dfc8cf23bc6067726e`.

The inherited unconditional MIPS DIV behavior is superseded.

Validated repair:
- dedicated runtime DIV helper reproduces the S-SMP normal and overflow branches;
- H = `(Y & 0x0f) >= (X & 0x0f)`;
- V = `Y >= X`;
- normal quotient/remainder path only when `Y < 2*X`;
- overflow formula used otherwise;
- X=0 is handled by the special path, avoiding undefined divide-by-zero;
- C/I/B/P preserved;
- N/Z queue reads repaired A after helper return by neutralizing the generated JAL delay slot with one MIPS NOP;
- already-validated guest timing remains exactly **12-cycle DIV**, or **16 total with the trailing BRA test loop**.

Directed results include:
- normal H/V-clear case: A=0x42,Y=0, PSW preserves C, **16 cycles**;
- 9-bit-quotient normal case: A=0x40,Y=0, H/V=1/1, Z clear, **16 cycles**;
- inherited failing overflow case X=4,Y=0x5A,A=0x11 now produces **A=0xAC,Y=0x61**, H/V=1/1 with correct N/Z;
- X=0 case passes without divide-by-zero and produces the pinned-reference state;
- zero-result case queues Z from repaired A correctly.

All global invariants remain true:
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

### Discarded explanation preserved
Attempt 1's N/Z mismatch was NOT caused by the runtime helper clobbering A2 or by sampling Y. The generated `queue_nz` instruction occupied the runtime JAL delay slot and therefore sampled old A before the helper ran. That explanation is REJECTED and should not be revisited.

### Decision
Consume only validated `src/apu_alu.S` DIV repair into clean timing foundation if clean/base blob identity is confirmed. Then exact clean CI.

Next REQUIRED SUPPORT arithmetic work: implement and prove **DAA (0xDF) / DAS (0xBE)** now that H/C semantics are trustworthy. SLEEP/STOP remain separate scheduler-state work.


## Clean DIV semantic candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@7f1d7f52c320ea065699f92737d1b320140f8141`**, one commit on top of validated ADDW/SUBW-H foundation `74455bb8...`.

Direct clean diff is exactly:
- `src/apu_alu.S` +66/-17.

No diagnostic script/workflow changes.

Dynamic semantic/timing authority:
- final diagnostic `f3bad9af...`;
- Build and Validate `35317084579` SUCCESS;
- APU Cycle And Span Proof `35317084547` SUCCESS.

Exact clean Build and Validate run: **`35345349822`**, IN_PROGRESS at checkpoint.

Do not modify clean `7f1d7f52...` until exact CI completes. Next diagnostic family is DAA/DAS only; SLEEP/STOP remain separate scheduler work.


## SPC700 DAA/DAS implementation proof in progress — checkpoint 2026-09-18

Exact diagnostic SHA: **`35a983e7e0d8f9161d599e498acbf8b004f2d6e5`**, one commit after validated DIV authority `f3bad9af...`.

Controlled core additions:
- `apu_daa` / `apu_das` handlers;
- runtime helpers implementing pinned S-SMP decimal-adjust semantics;
- opcode 0xDF maps to DAA;
- opcode 0xBE maps to DAS.

Guest timing:
- opcode fetch already charged;
- each instruction adds +2 fixed cycles for dummy PC read + idle;
- expected instruction total = **3 cycles**, or **7 with trailing validated BRA loop**.

Pinned semantics reproduced:
- DAA: if C or A>0x99, add 0x60 and set C; then if H or low nibble>9, add 0x06;
- DAS: if !C or A>0x99, subtract 0x60 and clear C; then if !H or low nibble>9, subtract 0x06;
- H and V preserved;
- N/Z recomputed from adjusted A;
- other PSW bits preserved.

Directed cases:
- DAA low-only;
- DAA high-only;
- DAA both adjustments with wrap to zero;
- DAS low-only;
- DAS high-only;
- DAS both adjustments to negative result.

Exact workflows are the newest runs for SHA `35a983e7...` on the diagnostic branch. Acceptance requires exact A/C/N/Z/H/V semantics, 7-cycle total with BRA, and all historical regression cases green.

SLEEP/STOP are deliberately excluded and remain separate scheduler-state work.


## Clean DIV semantic foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@7f1d7f52c320ea065699f92737d1b320140f8141`** completed **Build and Validate `35345349822` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

State: **VALIDATED CANDIDATE**, unmerged.

Combined authority:
- dynamic DIV semantic/timing proof: diagnostic `f3bad9af...`, ares run `35317084547` SUCCESS;
- clean consumption: exactly `src/apu_alu.S`;
- exact clean CI `35345349822` SUCCESS.

Next active diagnostic remains DAA/DAS at `35a983e7...`; SLEEP/STOP stay separate scheduler-state work.


## DAA/DAS proof attempt 1 — harness false negative 2026-09-18

Exact diagnostic SHA **`35a983e7e0d8f9161d599e498acbf8b004f2d6e5`**:
- **Build and Validate `35345543217` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35345543241` FAILURE**, cycle-proof job **`105601488300`**.
- failed proof artifact **`10547251142`**, digest `sha256:ae7405a8b48078ef8dc42be5fb941258ae429ae8c0597afcc14a79e59a739392`;
- exact proof-build artifact **`10547145095`**, digest `sha256:07c466993c6bdee4859f95f92106b76038ee348413e3cc7b44b61fcaa84c8c2c`.

The failure is **REJECTED as core evidence**. The entire historical regression matrix, including final DIV repair cases, passed before the harness reached the new decimal-adjust cases.

Traceback:
`TypeError: compile_one_case() missing 1 required keyword-only argument: 'y_value'`.

Cause: all six new `decimal_adjust_cases` omitted the harness-only `y_value` parameter. No DAA/DAS case executed, so DAA/DAS dynamic semantics/timing remain **UNMEASURED** by attempt 1.

Decision:
- do NOT modify DAA/DAS core code;
- do NOT alter cycle or semantic expectations;
- add only `y_value=0x06` to the six diagnostic case dictionaries;
- rerun the identical proof.


## DAA/DAS proof attempt 2 — harness-only rerun in progress 2026-09-18

Exact rerun SHA: **`db4137947d17403c81948c98907b16d424958181`**.

Direct compare `35a983e7... -> db413794...` is harness-only:
- `scripts/apu_cycle_proof.py` +6/-6;
- each decimal case now supplies required `y_value=0x06`.

No APU core source, timing expectation, semantic expectation or dispatch changed.

Exact workflows:
- **Build and Validate `35346467855`** — QUEUED at checkpoint.
- **APU Cycle And Span Proof `35346467906`** — IN PROGRESS at checkpoint.

Interpretation rules:
- all six decimal cases + historical regression matrix pass => DAA/DAS core at `35a983e7...` VALIDATED;
- any decimal semantic/timing failure => inspect that case as core evidence;
- any new harness/setup failure => fix only harness after proving it is not core behavior.


## SPC700 DAA/DAS — VALIDATED 2026-09-18

Core diagnostic authority: **`35a983e7e0d8f9161d599e498acbf8b004f2d6e5`**.
Harness-only rerun authority: **`db4137947d17403c81948c98907b16d424958181`**.

CI:
- **Build and Validate `35346467855` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35346467906` SUCCESS**, cycle-proof job **`105604478664`**.
- proof result artifact **`10547176802`**, digest `sha256:8867600f6a186efd91f8f60525aa3577789979eb1c6b072f2d80773f604ae3f3`;
- exact proof-build artifact **`10547940108`**, digest `sha256:5587c8a5c1d3384656bcd55e91e343ef7891aad74b8b19bacbfe7a6217d06bc4`.

All global invariants are true:
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

Directed results, each DAA/DAS followed by the validated 4-cycle BRA:
- DAA low-only: A=0x10, PSW V preserved, **7 cycles**;
- DAA high-only: A=0x75, C/V preserved/set correctly, **7**;
- DAA both adjustments with wrap: A=0x00, C/H/V/Z correct, **7**;
- DAS low-only: A=0x0F, C/V preserved, **7**;
- DAS high-only: A=0x15, H/V preserved and C cleared as reference requires, **7**;
- DAS both adjustments: A=0x9A, N/V correct, **7**.

Validated implementation:
- opcode 0xDF DAA is now implemented;
- opcode 0xBE DAS is now implemented;
- each charges +2 fixed guest cycles beyond fetch;
- runtime helper semantics match pinned ares;
- H/V and unrelated PSW bits are preserved; C/N/Z change per reference.

Attempt 1 failure is permanently classified **HARNESS FALSE NEGATIVE / REJECTED as core evidence**.

Decision: consume only DAA/DAS core into clean `phase2/apu-timing-foundation@7f1d7f52...`; then exact clean CI. Remaining unimplemented base SPC700 opcodes are only SLEEP/STOP and require scheduler-state design, not a normal opcode patch.


## Clean DAA/DAS candidate — checkpoint 2026-09-18

Clean branch advanced to **`phase2/apu-timing-foundation@9f070faeb6e9ea20012601d3eff1947658cfb93f`**, one commit on top of clean DIV foundation `7f1d7f52...`.

Direct clean diff is exactly:
- `src/apu_alu.S` +95/-0;
- `src/apu_emitter.S` +2/-2.

Clean emitter contains no `SODIUM64_PROFILE` / `apu_cycle_diag` references.

Dynamic authority:
- DAA/DAS core `35a983e7...`;
- harness-only rerun `db413794...`;
- Build and Validate `35346467855` SUCCESS;
- APU Cycle And Span Proof `35346467906` SUCCESS.

Exact clean Build and Validate run: **`35347334777`**, IN PROGRESS at checkpoint.

Remaining unimplemented base SPC700 opcodes after this candidate are only:
- 0xEF SLEEP/WAIT;
- 0xFF STOP.

Do not implement them as normal returning JIT handlers. Pinned ares models each as a persistent processor state repeatedly consuming `read(PC)+idle` until external synchronization/reset semantics release it. Next work is scheduler/state design and proof, isolated from arithmetic/timing work.


## SLEEP/STOP scheduler design — pre-implementation checkpoint 2026-09-18

Pinned ares SFC behavior:
- SMP main checks `r.wait` / `r.stop` before decoding another opcode;
- WAIT and STOP each latch persistent state and repeatedly execute `read(PC) + idle`;
- pinned source clears these state bits in SPC700 power/reset; no ordinary CPU->APU port write wake path was found.

Sodium64 scheduler fit:
- `cpu_execute` hands control to `apu_execute` according to `s3`;
- `apu_execute` already checks DSP deadline before entering JIT;
- APU timers are derived from the same advancing `s3` timeline.

Selected diagnostic architecture:
1. add `apu_halt` byte: 0=RUN, 1=WAIT, 2=STOP;
2. `apu_execute` keeps the existing DSP-deadline check first, then if halted performs a real `apu_read8(apu_count)` plus one idle-cycle debit and returns to `cpu_execute`; PC does not advance;
3. SLEEP/STOP generated handlers set their distinct latch and immediately perform the **first** real read of next PC + one idle before block return, avoiding a one-iteration scheduler/interleave delay;
4. normal finish-block stores the already-incremented next PC;
5. CPU->APU communication must not clear the latch.

Expected timing:
- entry block containing SLEEP or STOP: opcode fetch + first read + idle = **3 SPC cycles**;
- each subsequent halted scheduler service = **2 SPC cycles**;
- halt PC remains instruction-after-opcode.

This is a scheduler-state proof, not a normal fixed-cycle opcode patch. Acceptance must show distinct WAIT/STOP latch values, exact entry/tick debits, stable PC, and no JIT/decode advance while halted. Reset/power initialization remains `apu_halt=0`.


## Clean DAA/DAS foundation — CI VALIDATED 2026-09-18

Clean **`phase2/apu-timing-foundation@9f070faeb6e9ea20012601d3eff1947658cfb93f`** completed **Build and Validate `35347334777` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen emulator smoke SUCCESS.

Artifacts:
- normal build `10547931294`, digest `sha256:5c98696cb55d7c824f0b19b0bac0cecdd2f28f31b801223be7587365b620ce27`;
- profile build `10547173242`, digest `sha256:0caa0a0e92f4b7ab85c5324c82e6205c0479d9862887237ad3a6a2702d994597`;
- emulator smoke `10547383323`, digest `sha256:684d663493aa48b7d38bd5d37a5a9aa11cb97f40378493129cf5fb55c4d47676`.

State: **VALIDATED CANDIDATE**, unmerged.

The diagnostic and clean branches are byte-unchanged from their recorded DAA/DAS checkpoints; no SLEEP/STOP implementation exists yet. The next technical batch is the already-designed isolated SLEEP/STOP scheduler-state proof. Do not re-baseline Gothicvania or resume memory-helper optimization before this bounded base-SPC700 correctness item is resolved.


## SPC700 SLEEP/STOP scheduler-state proof — checkpoint 2026-09-18

Exact diagnostic SHA: **`e7cc3cf27f10bd5e3310a158bd56cf9965b7166e`**, one atomic commit after validated DAA/DAS diagnostic authority `db413794...`.

Direct compare `db413794... -> e7cc3cf...` is exactly:
- `src/apu.S` +20/-0;
- `src/apu_emitter.S` +39/-2;
- `scripts/apu_cycle_proof.py` +116/-0;
- `.github/workflows/apu-cycle-proof.yml` +8/-2.

### Controlled architecture under test
- add persistent `apu_halt`: 0=RUN, 1=WAIT/SLEEP, 2=STOP;
- keep the existing DSP-deadline test ahead of halt servicing;
- halted `apu_execute` performs real `apu_read8(apu_count)` + one idle-cycle debit and returns to `cpu_execute`, without changing PC or entering JIT/decode;
- opcode 0xEF and 0xFF now latch distinct states;
- the entry JIT block immediately performs the first real read of the instruction-after-opcode PC + idle before returning;
- normal `finish_block` remains authoritative for storing that next PC;
- ordinary proof setup clears `apu_halt` so persistent state cannot contaminate historical cases.

Expected guest timing:
- SLEEP/STOP entry = opcode fetch + real read(next PC) + idle = **3 SPC cycles**;
- each subsequent halted scheduler service = real read(same PC) + idle = **2 SPC cycles**;
- PC remains `TEST_PC+1`;
- halt state remains latched;
- JIT pointer remains unchanged on halted service.

### Dynamic proof additions
Directed proof requires separately for SLEEP and STOP:
1. entry total = 3 cycles and state = 1/2 respectively;
2. two consecutive halted scheduler services each debit exactly 2 cycles;
3. the real bus read address equals the stable instruction-after-opcode PC;
4. PC and halt state remain unchanged;
5. JIT pointer does not advance, proving no further decode/compile during halted service;
6. the full historical timing/address/semantic regression matrix remains green.

The proof runs halt cases last so their persistent state cannot affect earlier cases.

### Exact workflows now running
- **Build and Validate `35349865989` SUCCESS** — normal build, PROFILE build and pinned Mupen emulator smoke all green.
- **APU Cycle And Span Proof `35349866045`** — IN PROGRESS; profile-build is already SUCCESS and the dynamic ares proof is still running.

Acceptance: both workflows green and all new halt invariants true.

Falsifiers:
- compile/PROFILE/Mupen regression;
- entry debit != 3 cycles;
- any persistent tick != 2 cycles;
- read address differs from stable PC;
- PC advances, latch changes, or JIT pointer moves while halted;
- any prior regression case fails.

If accepted, consume only the runtime core files `src/apu.S` and `src/apu_emitter.S` into clean `phase2/apu-timing-foundation@9f070fae...`, then run exact clean CI. Do **not** copy diagnostic script/workflow into the clean branch.

Do not re-baseline Gothicvania or resume the memory-helper experiment until this last base-SPC700 scheduler correctness item is resolved.


## SPC700 SLEEP/STOP scheduler-state proof — VALIDATED 2026-09-18

Exact diagnostic authority: **`e7cc3cf27f10bd5e3310a158bd56cf9965b7166e`**.

CI:
- **Build and Validate `35349865989` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Cycle And Span Proof `35349866045` SUCCESS**, cycle-proof job **`105615549216`**.
- proof result artifact **`10549793093`**, digest `sha256:16ecb1d8f86c6045b11d2999c9562c0d166081826ab0583cb7cbbe204cb7a111`;
- exact proof-build artifact **`10548992246`**, digest `sha256:3be016038bb0f209d5528499f6d997b55edb18c8475e54568e950b90f469295a`;
- normal Build and Validate artifact **`10548652376`**, digest `sha256:07679ab4051faff12658e86600898f508c542e5e6285e3fb88732cee66bfdc44`.

Dynamic results at `apu_clock=21`:
- SLEEP entry: PC 0x0200 -> **0x0201**, latch=**1**, static debit=-42, total debit=**-63 = 3 SPC cycles**;
- STOP entry: PC 0x0200 -> **0x0201**, latch=**2**, static debit=-42, total debit=**-63 = 3 SPC cycles**;
- SLEEP halted tick 1: real read address **0x0201**, PC remains 0x0201, latch remains 1, JIT pointer unchanged, debit **-42 = 2 cycles**;
- SLEEP halted tick 2: same invariants, **2 cycles**;
- STOP halted tick 1: real read address **0x0201**, PC remains 0x0201, latch remains 2, JIT pointer unchanged, debit **2 cycles**;
- STOP halted tick 2: same invariants, **2 cycles**.

All proof summary invariants are true:
`all_halt_scheduler_ticks_match_expected`,
`all_header_spans_match_source_prediction`,
`all_runtime_cycle_debits_match_expected`,
`all_semantics_match_expected`,
`all_static_debits_match_source_prediction`,
`all_total_debits_match_reference`,
`compiled_long_probe_is_bounded_to_one_tag_region`.

Pinned ares authority also confirms SMP dispatch checks persistent `r.wait`/`r.stop` before decoding another opcode and each state repeatedly performs `read(PC)+idle`; power/reset clears both states.

### Decision
SLEEP/STOP scheduler semantics are **VALIDATED** in the ares laboratory. This closes the previously enumerated `apu_unk` base-opcode holes: 0xEF and 0xFF are no longer unimplemented in the validated diagnostic core.

Consume only runtime core changes from `src/apu.S` and `src/apu_emitter.S` into clean `phase2/apu-timing-foundation@9f070fae...`. Do not copy diagnostic proof/workflow changes. Then run exact clean Build and Validate before any re-baseline.

This does **not** prove Gate B performance or real-N64 behavior. The added normal `apu_execute` halt-state check is a correctness cost that must be included in the new matched performance baseline rather than assumed negligible.


## Clean SLEEP/STOP consumption — checkpoint 2026-09-18

Clean candidate advanced atomically from validated DAA/DAS `9f070fae...` to **`phase2/apu-timing-foundation@9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`** with message `fix: implement SPC700 SLEEP STOP scheduler state`.

Direct clean compare is exactly two runtime files:
- `src/apu.S` +20/-0;
- `src/apu_emitter.S` +39/-2.

No diagnostic script or workflow changes were consumed.

The clean `src/apu.S` blob is exactly the dynamically validated diagnostic runtime blob `6f7a8f2015f588dd7b8773a28c22e57ed6cb82a7`. The clean emitter carries the same SLEEP/STOP runtime logic while retaining the clean branch's absence of PROFILE-only cycle diagnostics.

Exact clean validation:
- **Build and Validate `35350851813`** — QUEUED at checkpoint.

Acceptance: normal build, PROFILE build and pinned Mupen emulator smoke all SUCCESS on exact SHA `9204ad2f...`.

If green: mark SLEEP/STOP clean candidate VALIDATED and the enumerated base-SPC700 opcode/semantic foundation complete enough to move to a fresh matched APU/audio performance baseline. If red: diagnose clean-integration failure; do not reinterpret the already-green dynamic diagnostic proof.


## Clean SLEEP/STOP foundation — VALIDATED 2026-09-18

Exact clean candidate: **`phase2/apu-timing-foundation@9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`**.

**Build and Validate `35350851813` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen normal/profile emulator smoke and profile decode SUCCESS.

Artifacts:
- normal build **`10549768562`**, digest `sha256:31c0a7c41d74c75c7661de03d4b021736c9e9e4e420ea8ab5c51ed87bfb14705`;
- PROFILE build **`10548818655`**, digest `sha256:9d08f44a06ef252732221b33e9b7154340f6e2e5d709bae6dcded607370490ca`;
- emulator smoke **`10548888744`**, digest `sha256:6bddf2a328b3be20da8bbd6e38e5587ee9624386c55b03761cb22922f1c0092f`.

State: **VALIDATED CANDIDATE**, unmerged.

The clean branch now contains the validated DAA/DAS, Half-Carry, DIV, timing/address/bus corrections and persistent SLEEP/STOP scheduler state without diagnostic-only proof code.

### Immediate next action
Do **not** resume the old memory-helper experiment from pre-foundation measurements. First establish a **fresh matched, repeated APU/audio baseline on this exact clean SHA**. The audit demonstrated same-SHA ares A/A spread (44/60 vs 48/60), so single-run deltas of a few FPS are not attribution-quality evidence.

Baseline design must preserve:
- same exact `9204ad2f...` build/artifact;
- same Gothicvania workload and pinned ares configuration;
- CPU JIT + RSP interpreter laboratory mode;
- frameskip 0, full-rate APU and audio path intact;
- repeated independent observations sufficient to characterize run-to-run variance;
- paired DSP-lateness / audio-timing evidence, not FPS alone.

Only after that baseline should a new optimization hypothesis be selected from the corrected profile distribution.


## E1 matched-window baseline repair — running 2026-09-18

Measurement-only branch: **`phase2/apu-matched-baseline@d20258be3f783728b500cfd95065abc185b14f2b`**, created directly from validated clean core **`9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`**.

Direct compare `9204ad2f... -> d20258be...` is exactly two added diagnostic files and **zero emulator-core changes**:
- `.github/workflows/apu-matched-baseline.yml` +463;
- `scripts/gdb_matched_profile.py` +309.

### Measurement contract under test

The old open-homebrew harness is not attribution-grade for small deltas because it patches settings after host-time warmup/settle and terminates on host-time/sample targets, producing unmatched guest phases.

The new bounded E1 harness instead:
1. stops at the **first `cpu_execute` before any guest CPU/APU execution**;
2. there sets APU clock=21, frameskip=0, audio=4, precision=8, zeros APU JIT lookup and resets JIT pointer;
3. uses local `update_fps` as an exact guest boundary. At its entry exactly 60 VI have elapsed and `fps_emulate` still contains completed SNES frames for that just-finished interval;
4. warms for exactly **2 complete 60-VI windows**;
5. resets only profiler-ring metadata at that exact boundary;
6. captures exactly **5 consecutive complete 60-VI windows**;
7. repeats the whole process **3 times from fresh ares processes** while reusing one exact PROFILE binary, one exact Gothicvania ROM and one pinned ares build;
8. captures one statistical profile per repeat over the same five-window guest interval.

Pinned lab remains:
- Gothicvania source artifact `10466504920`, SNES ROM SHA-256 `5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`;
- ares `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`;
- R4300 JIT ON, RSP interpreter forced due documented ares RSP-JIT LAB LIMITATION;
- deterministic entropy;
- frameskip0 / APU21 / audio4 / precision8.

The script uses the already-proven ares software-breakpoint mechanism from the SPC700 proof harness. Between repeated `update_fps` boundaries it advances through `check_frame` so the same breakpoint cannot immediately re-hit.

### Exact runs
- **APU Matched Baseline `35351837163`** — IN PROGRESS at checkpoint.
- **Build and Validate `35351837019`** — PENDING/starting at checkpoint.

### Acceptance
This is a **MEASUREMENT PROOF**, not a speedup experiment. Accept the repair if:
- the exact branch compiles and ordinary Build/Validate remains green;
- all three fresh repeats reach the first-guest configuration boundary;
- every warmup/measured `update_fps` stop observes `fps_native=59`, confirming an exact 60-VI boundary;
- settings remain 21/0/4/8 through all measured windows;
- each repeat yields five complete windows and >=800 statistical samples;
- the artifact exposes the actual repeat/window distribution rather than reducing it to one host-time-selected total.

### Falsifiers / failure classes
- cannot reliably breakpoint `cpu_execute`, `update_fps` or `check_frame`;
- settings are not safely writable/retained before first guest execution;
- `fps_native` does not equal 59 at the claimed boundary;
- profiler sample count does not advance monotonically;
- build/Mupen regression despite no core changes indicates branch/harness integration error;
- repeated exact-window vectors remain materially phase-incomparable for a reason not controlled by the contract.

Do not require the three repeats to be numerically identical: variation itself is evidence. The goal is to make the **guest interval identical in definition**, so its observed variation becomes measurable instead of being conflated with different stop phases.

If accepted, this exact-window harness becomes the laboratory authority for a fresh baseline on clean `9204ad2f...`. Only then rank E3 low-read, E4 same-boundary validation or E5 DSP-invariant hypotheses. ares results remain laboratory evidence; real N64 remains final performance/timing authority.


## E1 matched-window baseline repair — VALIDATED 2026-09-18

Measurement-only authority: **`phase2/apu-matched-baseline@d20258be3f783728b500cfd95065abc185b14f2b`**, tree-equivalent in emulator core to clean timing foundation **`9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`**.

CI:
- **APU Matched Baseline `35351837163` SUCCESS**, matched job `105621983942`;
- **Build and Validate `35351837019` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green;
- matched diagnostics artifact **`10550167013`**, digest `sha256:0127fdbe1823fa40aa18fbbff0a4b99d82a32ee2bbd226d9ae1e2a1c5c2843d7`;
- exact matched PROFILE build **`10550355610`**, digest `sha256:99d8c6e0e4cd208f036db934a6b00d6b4c1c3404685ba09ad6fbfd2deafcb185`.

All three fresh ares processes produced the identical five-window vector:
**61, 60, 59, 61, 59 /60**, mean **60.00/60**, range **59..61**, with exactly **3582 samples** per repeat. Every warmup/measured boundary had `fps_native=59` and settings remained APU21 / frameskip0 / audio4 / precision8.

The statistical profile was also identical across all three repeats:
- S-CPU **23.5%**;
- APU generated **2.5%**;
- APU static **22.1%**;
- DSP/audio **23.2%**;
- PPU **10.9%**;
- DMA **6.1%**;
- VRAM/RSP wait **1.9%**;
- VI wait **9.7%**.

**MEASUREMENT PROOF:** the exact guest-window harness removes the prior same-binary phase ambiguity for this deterministic workload. Host wall time varied materially across repeats while guest frame vectors, sample counts and profiles remained identical, confirming host wall time is irrelevant to the guest-frame result.

**SUPPORTED INTERPRETATION:** on the corrected timing foundation, Gothicvania is no longer throughput-bound in the valid ares laboratory and has measurable VI idle headroom. This is a major change from pre-foundation ares observations, but it is NOT yet real-N64 performance evidence and does not prove Gate B.

**REJECTED inference:** do not rank E3/E4/E5 by ares FPS while this workload is already at the laboratory ceiling. Small speedups can be hidden inside VI wait.

### Immediate next action
Before promoting this corrected foundation to a real-N64 milestone, run one **separate PROFILE-only matched-window DSP-lateness diagnostic** on the exact core:
- reuse the previously validated due-count / late-sum / late-max / multi-due counters;
- measure the same exact five 60-VI windows;
- require **multi-due count = 0** (no lateness >= one 672-cycle DSP period);
- record due count, average and max as timing evidence;
- do not use the instrumented run for throughput comparison.

If DSP scheduling remains bounded, the next gate-relevant action is a milestone real-N64 measurement of exact clean `9204ad2f...` (or a byte-equivalent release artifact), because ares has ceased to be discriminative for this workload's performance.


## Matched DSP-lateness diagnostic — running 2026-09-18

Diagnostic child branch: **`phase2/apu-matched-dsp-lateness@a8c56301d3bc3d65b100b5cbb702f043ec6126de`**, based on measurement-only E1 authority `d20258be...`. Clean runtime candidate `9204ad2f...` is unchanged.

Direct compare from E1 measurement branch is exactly four diagnostic files:
- `src/apu.S` +37/-0, all scheduler observation under `SODIUM64_PROFILE`;
- `src/profile.S` +28/-0, PROFILE-only counters outside the canonical S64P snapshot;
- `scripts/gdb_matched_profile.py` +25/-0;
- `.github/workflows/apu-matched-baseline.yml` +29/-4.

Question: does the corrected timing foundation's exact-window 60/60-class ares result preserve DSP scheduling without ever becoming at least one full DSP sample period late?

Measurement contract:
- same exact first-guest configuration boundary and 2-warmup + 5-measured 60-VI windows as validated E1;
- counters reset at the exact measurement boundary;
- record DSP due count, lateness sum/average, max lateness and events with lateness >= `DSP_SAMPLE=672`;
- instrumented run is timing evidence only, **not** throughput evidence.

Acceptance:
- `dsp_due_count > 0`;
- `dsp_multi_due_count == 0`;
- `dsp_late_max < 672`;
- exact-window/settings contract still passes;
- ordinary Build and Validate remains green.

Falsifier: any >=672-cycle event, max >=672, settings/window-contract regression, or core/build regression.

Exact HEAD runs:
- **Build and Validate `35353207712`** — running;
- **APU Matched Baseline `35353207814`** — running; exact PROFILE build already SUCCESS, artifact `10550441933`, digest `sha256:6492d5e5c45661f0ba6772c637aade4c1a968bcad92fac3dfcb7f62a20a8d9f5`.

Decision map:
- if accepted, do not merge diagnostic instrumentation; promote exact clean `9204ad2f...` to a prepared real-N64 milestone because ares already has 9.7% VI idle and is no longer discriminative for Gothicvania performance;
- if lateness fails, treat 60/60 as cadence-invalid and repair scheduler/interleave before any hardware performance claim;
- if only harness/workflow fails, repair the diagnostic harness without changing clean core semantics.


## M1 hardware-package guard attempt 1 — HARNESS FALSE NEGATIVE 2026-09-18

Measurement-package branch was created from clean core `9204ad2f...` as **`phase2/apu-hardware-milestone`**. Its only intended repo change is the hardware-package workflow; emulator runtime files remain from the clean candidate.

First package SHA `d86de54b113ca18bdf56e61240ed9868ffdaed7a`, run **`35353828653`**, failed before compilation in the runtime-identity guard with:
`fatal: bad object 9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`.

Cause: `actions/checkout@v4` defaulted to `fetch-depth: 1`, so the clean parent commit object was absent locally. This is **HARNESS FALSE NEGATIVE / REJECTED as core evidence**.

No build, ROM, hardware result or Sodium64 behavior was tested by the failed attempt.

Workflow-only fix: package branch advanced to **`e0dfe19b59cd4b86ee96eb250c9ad4bfda437a3b`**, adding only `fetch-depth: 0` so the guard can compare against exact clean core `9204ad2f...`. Runtime core remains unchanged.


## Matched DSP-lateness diagnostic — FAILED CADENCE GATE / VALID EVIDENCE 2026-09-18

Exact diagnostic authority: **`phase2/apu-matched-dsp-lateness@a8c56301d3bc3d65b100b5cbb702f043ec6126de`**.

CI:
- **Build and Validate `35353207712` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Matched Baseline `35353207814`** completed all three exact-window repeats successfully, then intentionally FAILED the final acceptance assertion because DSP lateness exceeded the allowed period.
- diagnostic artifact **`10550684126`**, digest `sha256:50dcdc3c80aa8f834df8c13eb6aa5c0f0dc3ef374afe60e92f165af785fe54a6`;
- exact PROFILE build artifact **`10550441933`**, digest `sha256:6492d5e5c45661f0ba6772c637aade4c1a968bcad92fac3dfcb7f62a20a8d9f5`.

All three fresh ares processes were bit-for-bit deterministic at the reported measurement level:
- measured frame vector: **60,60,60,60,60 /60** in every repeat;
- final samples: **3581** in every repeat;
- DSP due count: **159849**;
- DSP late sum: **20846385** master cycles;
- average lateness: **130.4129835 master cycles = 6.210 SPC cycles**;
- maximum lateness: **1029 master cycles = 49 SPC cycles**;
- events with lateness >= one DSP period (`672 = 32 SPC cycles`): **1420**, about **0.8883%** of due events.

**VALIDATED correctness finding:** the corrected timing foundation can report 60/60 completed frames while violating the required DSP scheduler cadence. Therefore the current ares 60/60 result is **NOT cadence-valid Gate-B evidence**.

**REJECTED inference:** do not treat ares VI headroom or 60/60 as proof that the clean candidate is ready for real-N64 performance graduation. Throughput and event cadence are now explicitly separated.

The lateness counters are diagnostic-only and read `a3-s3` before their own logging work, so the observed lateness is not created by the counter instructions themselves. The repeated exact values across three fresh processes strengthen the scheduler/interleave interpretation.

### Hardware package status
A measurement-only branch **`phase2/apu-hardware-milestone@e0dfe19b59cd4b86ee96eb250c9ad4bfda437a3b`** successfully built the real-N64 M1 package after fixing a shallow-checkout guard false negative:
- package run **`35353932617` SUCCESS**;
- artifact **`10550379275`**, digest `sha256:8fff13c90307f90d21cab84afb2c6ecb4766ff3f3f3d3b0617efd4b1d6c28c8a`;
- runtime identity guard proved `src`/build inputs are exact clean core `9204ad2f...`, with workflow-only packaging changes.

State: **BLOCKED / DO NOT HARDWARE-TEST YET**. Preserve the artifact but do not ask Iron to run it while DSP cadence is invalid.

### Immediate next controlled experiment
Test whether JIT block interleave, rather than an individual instruction or DSP scheduler bug, causes the >672 tail:
- create a diagnostic child of `a8c56301...`;
- change only `BLOCK_SIZE 16 -> 1`, which forces one SPC700 instruction per generated block after the already-validated NOP-bound repair;
- keep identical matched-window lateness instrumentation and workload;
- accept as causal proof if `dsp_multi_due_count` falls to 0 and max <672;
- if lateness remains >=672, block aggregation is insufficient as the explanation and the next investigation must inspect individual-instruction / scheduler-event semantics.

This one-op mode is a **causal control only**, not a proposed permanent architecture. Its throughput cost is secondary to isolating the mechanism.


## One-op APU JIT interleave causal proof — running 2026-09-18

Diagnostic child branch: **`phase2/apu-one-op-interleave-proof@c1548c21e4764a1827ebe1af8980ec319f560bbb`**, based on matched-lateness authority `a8c56301...`.

Direct diff from `a8c56301...` is exactly:
- `src/defines.h`: **one runtime line**, `BLOCK_SIZE 16 -> 1`;
- `.github/workflows/apu-matched-baseline.yml`: one trigger-line addition for this diagnostic branch.

Production-semantic test variable: one SPC700 instruction per generated block. No timing charges, opcode semantics, scheduler checks, DSP logic, profiler counters or workload settings changed.

Purpose: causal isolation only. This is **not** a proposed permanent performance architecture.

Hypothesis: the validated >672 DSP lateness tail is produced by aggregating several now-correctly-timed SPC700 instructions inside one JIT block before returning to the scheduler.

Acceptance as causal proof:
- exact matched-window contract completes;
- `dsp_multi_due_count == 0`;
- `dsp_late_max < 672`.

Interpretation:
- if accepted, block aggregation/interleave is the demonstrated mechanism; next design must retain multi-op performance while adding a bounded guest-cycle return contract;
- if >=672 remains, multi-op aggregation alone is insufficient and investigation moves to individual-instruction / scheduler-event semantics.

Exact HEAD runs:
- **APU Matched Baseline `35354324333`** — queued/running;
- **Build and Validate `35354324334`** — queued/running.

Do not merge BLOCK_SIZE=1. Do not use throughput from this diagnostic as a performance target; frame counts only show the cost of the causal control.


## One-op APU JIT interleave proof — VALIDATED CAUSAL RESULT 2026-09-18

Exact diagnostic authority: **`phase2/apu-one-op-interleave-proof@c1548c21e4764a1827ebe1af8980ec319f560bbb`**.
Runtime test variable from matched-lateness authority `a8c56301...`: exactly **`BLOCK_SIZE 16 -> 1`**. Workflow has one trigger-line addition only.

CI:
- **Build and Validate `35354324334` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Matched Baseline `35354324333` SUCCESS**.
- diagnostic artifact **`10551701393`**, digest `sha256:109da718606b3d01332dfd65aff321f6b5a0ed26ef88fd3f4bdae4edc16e38b8`;
- exact PROFILE build artifact **`10550643405`**, digest `sha256:4bd6cdbbe58086d675f31c1adeff199d83d41f77ffb5f6286e94213b31beb1b9`.

All three fresh ares repeats were identical:
- measured windows: **48,49,49,51,50 /60**;
- mean **49.4/60**, range **48..51**;
- samples **3580**;
- DSP due count **131397**;
- late sum **5891319** master cycles;
- average lateness **44.836 master cycles = 2.135 SPC cycles**;
- max lateness **168 master cycles = 8 SPC cycles**;
- **`dsp_multi_due_count = 0`**.

Compared with the multi-op corrected-timing baseline:
- BLOCK16: max **1029 = 49 SPC cycles**, **1420 >=672** events, cadence FAIL despite 60/60 throughput;
- one-op: max **168 = 8 SPC cycles**, **0 >=672** events, cadence PASS but throughput falls to **49.4/60**.

**ARCHITECTURE PROOF:** multi-instruction JIT block aggregation before scheduler return is the demonstrated cause of the invalid DSP-lateness tail. The scheduler can maintain bounded DSP cadence when return frequency is sufficiently high.

**REJECTED architecture:** `BLOCK_SIZE=1` is not a production solution; its throughput cost essentially gives back the corrected-timing ares gain.

Pinned ares source audit at `17813a3c...` shows the highest-cost finite single SPC700 instruction is DIV at **12 total cycles** (opcode fetch + 11 explicit read/idle cycles). WAIT/STOP are persistent states and Sodium64 already returns to the scheduler after their 3-cycle entry / 2-cycle ticks.

### Next design — guest-cycle-bounded multi-op JIT blocks
Target invariant: retain multi-op blocks but guarantee a generated block cannot consume a full DSP period before scheduler return.

DSP period = `DSP_SAMPLE=672` master cycles = **32 SPC cycles** at `apu_clock=21`.

A conservative compile-time block budget can be derived from the existing cycle mechanisms:
1. each source byte fetched by `jit_read8` = 1 guest cycle;
2. `jit_charge_cycles` = fixed extra guest cycles;
3. `jit_emit_runtime_cycles` = conditional runtime cycles, counted at their worst-case value for budgeting;
4. every generated call to `apu_read8` / `apu_write8` = 1 guest bus cycle.

No other audited APU generator file emits direct guest-`apu_ram` accesses; guest data cycles flow through those helpers. The direct LBU/SB/SH/LHU emissions in `apu_emitter.S` are emulator-state register spill/load machinery, not guest bus cycles.

Since one finite instruction is <=12 cycles, a multi-op compiler can continue only while the completed block budget is <=20 cycles. Adding one more worst-case instruction then yields a hard maximum of **32 guest cycles**, while the existing 16-byte source-span cap remains as an independent safety bound.

Next controlled implementation must add compile-time-only cycle accounting and this continuation rule, with no change to per-instruction guest debits or opcode semantics. It must be validated by cycle/address regression plus the same exact-window DSP-lateness run before any hardware test.


## Guest-cycle-bounded multi-op JIT candidate — running 2026-09-18

Diagnostic branch: **`phase2/apu-cycle-budget-interleave@a4b8f2d74f368568ef519ea76bb589d7fe98d265`**, based on matched-lateness authority `a8c56301...`.

Direct diff:
- `src/apu_emitter.S` +44/-8 — compiler-only cycle accounting plus block continuation bound;
- `.github/workflows/apu-matched-baseline.yml` +1 trigger line.

No opcode semantic implementation, per-instruction guest debit, DSP scheduler ordering, APU memory helper semantics or workload setting changed.

Design:
- preserve inherited independent `BLOCK_SIZE=16` source-span/tag safety bound;
- maintain compile-only `jit_block_cycles` worst-case guest-cycle count;
- +1 per source-byte fetch in `jit_read8`;
- +N for fixed cycles in `jit_charge_cycles`;
- +N for conditional runtime cycles in `jit_emit_runtime_cycles`, conservatively counting the taken/worst-case path;
- +1 for every generated `apu_read8`/`apu_write8` guest bus access inside `emit_jal`;
- after each completed opcode, continue compiling only if source span remains under 16 bytes **and** completed worst-case budget <=20 cycles.

Pinned reference bound: maximum finite single opcode = DIV at 12 cycles. Therefore any continued block can reach at most **20+12 = 32 SPC cycles**, one DSP period. Because `apu_execute` services DSP when `s3 <= a3` and enters a block only with positive headroom, a <=32-cycle block must return with lateness <672 master cycles.

Source audit found no generated direct guest-`apu_ram` data accesses outside `apu_read8`/`apu_write8`; direct load/store emission in `apu_emitter.S` is emulator-state spill/load machinery. WAIT/STOP remain separate persistent scheduler state and do not violate the finite-op bound.

Exact HEAD runs:
- **APU Matched Baseline `35355419586`** — running;
- **Build and Validate `35355419608`** — queued/running.

Acceptance:
1. normal/PROFILE build + Mupen smoke green;
2. exact-window `dsp_multi_due_count=0` and `dsp_late_max<672`;
3. materially better throughput than one-op 49.4/60;
4. then consume the same emitter change into cycle/address proof and require the full timing/semantic regression matrix green before clean consumption.

Falsifiers:
- any >=672 event;
- build/runtime regression;
- cycle proof regression;
- throughput near one-op indicating the temporal cap destroys the multi-op benefit.


## Cycle-budget implementation v1 — SUPERSEDED before acceptance 2026-09-18

Source-contract audit found a real compiler-helper clobber regression in first cycle-budget implementation `a4b8f2d7...`: its new bookkeeping used **`t2`** inside `jit_read8` / cycle helpers even though those helpers historically clobbered only their existing temporaries.

Concrete proof: `apu_bbc1` and `apu_bbs1` compute the tested-bit mask into `t2`, call `jit_read8`, then use `t2` to encode the generated ANDI. Therefore v1 can silently corrupt BBS/BBC compiled semantics. This is source-proven, not hypothetical.

State:
- `phase2/apu-cycle-budget-interleave@a4b8f2d7...` = **SUPERSEDED implementation** regardless of its eventual matched-run numbers;
- `phase2/apu-cycle-budget-proof@1f7aa124...` = **SUPERSEDED proof implementation** for the same reason;
- any v1 CI result may be retained only as diagnostic evidence about that exact flawed SHA, not as candidate correctness/performance authority.

No clean branch was touched.

## Guest-cycle-bounded multi-op JIT v2 — running 2026-09-18

Corrected diagnostic candidate:
**`phase2/apu-cycle-budget-interleave-v2@5b9f16c0127b9ec99e7bdc5d811a183e87065b86`**.
Core commit before trigger-only workflow line: `709def0969c97e66c195b490deb480324e6e9a3f`.

Corrected cycle-proof child:
**`phase2/apu-cycle-budget-proof-v2@91f8f13a9a4cdd8ccc98da7452935e387664a8c0`**, based on immutable proof authority `e7cc3cf...`.

The temporal-budget design is unchanged from v1. The only implementation correction is register discipline:
- `jit_read8` bookkeeping reuses only historical clobbers `v0/t0/t1`; **t2 is preserved**;
- `jit_charge_cycles` reuses only existing `t0/t1`;
- `jit_emit_runtime_cycles` reuses only existing `t0/t1/t5`;
- `emit_jal` remains within existing `t0/t1` clobbers.

Direct v2 candidate diff from matched-lateness base `a8c56301...`: only `src/apu_emitter.S` +42/-9 plus one workflow trigger line.
Direct v2 proof diff from `e7cc3cf...`: only `src/apu_emitter.S` +42/-9 plus one proof-workflow trigger line.

Acceptance remains unchanged:
1. exact Build/Validate + Mupen green;
2. matched Gothicvania: `multi_due=0`, max <672 and throughput materially above one-op 49.4/60;
3. full APU Cycle And Span Proof regression matrix green;
4. only then consume the emitter change into clean timing foundation.


## Cycle-budget implementation v1 — MATCHED RESULT VALID, IMPLEMENTATION SUPERSEDED 2026-09-18

Exact v1 diagnostic authority: **`phase2/apu-cycle-budget-interleave@a4b8f2d74f368568ef519ea76bb589d7fe98d265`**, based on matched-lateness diagnostic authority `a8c56301...`. **Do not consume this SHA:** its matched result is valid evidence for the cycle-budget architecture, but the implementation is superseded by the source-proven `t2` clobber regression documented above.

Direct production-semantic change from `a8c56301...` remains confined to `src/apu_emitter.S`:
- compile-only `jit_block_cycles` accounting;
- +1 per `jit_read8` source/operand fetch;
- fixed extra guest cycles through existing `jit_charge_cycles`;
- conditional cycles conservatively budgeted at the existing `jit_emit_runtime_cycles` value;
- +1 for generated `apu_read8` / `apu_write8` guest bus calls;
- multi-op continuation only while completed worst-case block budget <=20 cycles, preserving the independent 16-byte source-span cap.

CI:
- **Build and Validate `35355419608` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke all green.
- **APU Matched Baseline `35355419586` SUCCESS**.
- matched diagnostic artifact **`10551783478`**, digest `sha256:95c8a3a88ed7815e614440e1d366b2024e4043dfc7b18fdf60377611ad94950e`;
- exact PROFILE build artifact **`10551457203`**, digest `sha256:c16261aafd8ea11709d4e1cbcaceb9af5a46689330d5a8fc0458ae2603dc2ce6`.

All three fresh ares repeats were identical:
- measured frame vector **60,60,60,60,60 /60**;
- mean **60.00/60**, range **60..60**;
- samples **3584**;
- DSP due count **159539**;
- late sum **3350319 master cycles**;
- average lateness **21.0 master cycles = 1 SPC cycle**;
- maximum measured-window lateness **21 master cycles = 1 SPC cycle**;
- **`dsp_multi_due_count = 0`**.

Warmup still observed a bounded max of 483 master cycles (<672), with zero multi-due events. After the exact measurement-boundary reset, all five windows remained at one SPC cycle maximum lateness.

Comparison:
- original corrected multi-op BLOCK16: **60/60**, max **1029**, **1420 >=672** — cadence FAIL;
- one-op causal control: **49.4/60**, max **168**, **0 >=672** — cadence PASS, throughput FAIL;
- cycle-bounded multi-op: **60/60**, max **21**, **0 >=672** — cadence PASS + throughput target in valid ares lab.

**ARCHITECTURE PROOF (mechanism only):** the v1 matched result demonstrates that guest-cycle-bounded multi-op compilation can resolve the measured conflict between SPC700 JIT throughput and DSP scheduler cadence for Gothicvania in the valid ares lab. It does **not** validate the v1 implementation because that SHA violates a compiler-helper clobber contract. v2 must reproduce the result and pass cycle/semantic proof before clean consumption.

**What this does NOT prove:** commercial compatibility, real-N64 60 FPS, audio waveform correctness, or Gate B completion. ares remains a laboratory; exact opcode cycle/address regression and then real hardware authority are still required.

### Immediate next action (superseded by v2 work now running)
Validate the clobber-safe v2 emitter through both the matched cadence/throughput run and the existing cycle/address proof line. Do not consume the v1 emitter into any clean branch.

Acceptance:
- all existing 256-opcode cycle/address proof cases remain green;
- WAIT/STOP/NOP and branch taken/not-taken expectations remain green;
- normal/PROFILE build + emulator smoke remain green.

Only after that proof passes should the emitter change be consumed into the clean timing foundation and a fresh real-N64 M1 package be built from the resulting exact clean SHA.


## Cycle-budget v2 proof expectation repair — checkpoint 2026-09-18

Proof v2 advanced to **`phase2/apu-cycle-budget-proof-v2@151466bb39ab7a7739ec76e415e4deafb0a600e4`**.

Reason: the historical `long_nop_dbnzy` regression probe encoded the OLD architecture's desired cutoff: 16 NOP bytes / 32 guest cycles. Under the new temporal block contract the intentional cutoff is earlier:
- each NOP = 2 SPC cycles;
- after 10 NOPs budget =20 and one more finite instruction is permitted;
- after 11 NOPs budget =22, so the block terminates;
- expected PC advance =11 bytes;
- static/total debit =22 SPC cycles =462 master cycles.

Only proof expectations for this architecture-specific long-NOP cutoff changed:
- expected PC +16 -> +11;
- expected debit -672 -> -462;
- reference cycles 32 ->22;
- summary long-probe clock-units 32 ->22.

All instruction semantic/timing expectations, addressing cases, branch/runtime debits, halt scheduler checks, tag-region bound and historical family regressions remain unchanged.

Exact current proof runs:
- **APU Cycle And Span Proof `35356429346`** — queued;
- **Build and Validate `35356429215`** — queued.
Earlier proof-v2 run at `91f8f13a...` is superseded by this expectation-only correction.


## Guest-cycle-bounded multi-op JIT v2 — VALIDATED FOR CLEAN CONSUMPTION 2026-09-18

Corrected candidate authority: **`phase2/apu-cycle-budget-interleave-v2@5b9f16c0127b9ec99e7bdc5d811a183e87065b86`**.
Production emitter commit before trigger-only workflow change: **`709def0969c97e66c195b490deb480324e6e9a3f`**.

### L1/L2 build authority
**Build and Validate `35356204540` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen64Plus normal/profile smoke SUCCESS.

### Matched cadence + throughput authority
**APU Matched Baseline `35356204750` SUCCESS**, matched job `105636472480`.

All three fresh ares repeats produced the same five-window vector:
**61,59,60,61,60 /60**, mean **60.20/60**, range **59..61**, samples **3582**.

DSP scheduler evidence in each repeat:
- due count **159882**;
- late sum **16855692 master cycles**;
- average lateness **105.4258265 master cycles ~= 5.02 SPC cycles**;
- maximum lateness **546 master cycles = 26 SPC cycles**;
- **multi-due count = 0** (no event reached the 672-master / 32-SPC DSP period).

Warmup maximum was also bounded at 546 with zero multi-due events.

Artifacts:
- matched diagnostics **`10552485210`**, digest `sha256:f717d6488f0ef3ed04fd7a7c26d68ad7e29380d1533d8d467336dc4e0467c91b`;
- exact PROFILE build **`10551443618`**, digest `sha256:82122533a864a648aadbef12c660a565b63346c16bea1bbcc635dcd36071329e`.

**VALIDATED:** clobber-safe v2 retains the measured throughput benefit while keeping DSP scheduler lateness below one full sample period. This reproduces the architecture result without the v1 helper-clobber defect.

### Cycle/address/semantic proof authority
Proof branch: **`phase2/apu-cycle-budget-proof-v2@151466bb39ab7a7739ec76e415e4deafb0a600e4`**.

**APU Cycle And Span Proof `35356429346` SUCCESS**, dynamic proof job `105637636509`.
Companion **Build and Validate `35356429215` SUCCESS**.

Proof summary:
- `all_static_debits_match_source_prediction = true`;
- `all_header_spans_match_source_prediction = true`;
- `all_runtime_cycle_debits_match_expected = true`;
- `all_total_debits_match_reference = true`;
- `all_semantics_match_expected = true`;
- `all_halt_scheduler_ticks_match_expected = true`;
- `compiled_long_probe_is_bounded_to_one_tag_region = true`.

The architecture-specific long-NOP probe correctly compiled **11 NOP bytes / 22 SPC cycles / 462 master cycles**, not the old 16-NOP/32-cycle cutoff. BBS/BBC taken/not-taken, addressing families, branches, stack/call/return, word/bit operations, half-carry, DIV, decimal adjust, SLEEP and STOP remained in the unchanged semantic/timing matrix and passed.

Proof artifacts:
- diagnostics **`10552885741`**, digest `sha256:ca40f0c2e100b3b26b8c14b8c7f778e273bc77728f1511c4801203bc614114a2`;
- exact proof build **`10552426125`**, digest `sha256:4d9e5e4026fb5486036e7fe832273f916bcd10e004ada080155f546d4d325a1b`.

**ARCHITECTURE PROOF + COMPATIBILITY/TIMING REGRESSION:** v2 is now acceptable for clean consumption. This validates the audited SPC700 timing/address/semantic corpus and the Gothicvania matched cadence contract; it does not establish complete SPC700 correctness or real-N64 performance.

### Immediate next action
Create a clean child of **`phase2/apu-timing-foundation@9204ad2f...`** that consumes **only the exact v2 `src/apu_emitter.S` production change** from `709def09...`.
Do not consume PROFILE lateness counters, matched workflows, proof harness changes, or diagnostic files.

Then:
1. require clean Build and Validate + Mupen SUCCESS;
2. verify direct diff from `9204ad2f...` is only `src/apu_emitter.S`;
3. build a fresh real-N64 M1 Gothicvania package from that exact clean SHA;
4. only that fresh package may be presented for the next hardware milestone.


## Clean cycle-budget consumption — running 2026-09-18

Clean candidate: **`phase2/apu-cycle-budget-clean@d5ce93a03b2dbf5065fefa5276533e02f9658215`**.

Authority:
- parent is exact clean timing foundation **`9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`**;
- branch is ahead by exactly one commit;
- direct diff is exactly one production file: **`src/apu_emitter.S` +42/-9**;
- resulting emitter blob **`fc510743836c2a0a8afca771ca016cf2d02bf83a`** exactly matches the clobber-safe v2 emitter validated in matched and cycle-proof branches.

No PROFILE lateness counters, diagnostic workflows, proof scripts, or measurement-only source changes were consumed.

Exact clean CI:
- **Build and Validate `35357705471`** — queued/running.

Acceptance before hardware packaging:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen normal/profile smoke SUCCESS.

After clean CI passes, build a fresh M1 real-N64 package from this exact clean SHA. The previous hardware artifact from `9204ad2f...` remains BLOCKED/SUPERSEDED for this milestone because it predates the cycle-budget interleave fix.


## Clean cycle-budget candidate — VALIDATED 2026-09-18

Clean candidate authority: **`phase2/apu-cycle-budget-clean@d5ce93a03b2dbf5065fefa5276533e02f9658215`**.

Identity:
- exact parent: `phase2/apu-timing-foundation@9204ad2fae7f37d9950a0f3a88cc3ff4299e1bc1`;
- exactly one commit ahead;
- only changed production file: **`src/apu_emitter.S` +42/-9**;
- emitter blob **`fc510743836c2a0a8afca771ca016cf2d02bf83a`**, byte-identical to clobber-safe v2 production emitter `709def09...`.

No matched-lateness instrumentation, proof harness, diagnostic source, or diagnostic workflow was consumed.

**Build and Validate `35357705471` SUCCESS**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen64Plus normal runtime smoke SUCCESS;
- pinned Mupen64Plus PROFILE runtime/sample-decode smoke SUCCESS.

State: **VALIDATED clean M1 candidate / READY FOR REAL-N64 MILESTONE PACKAGE**.

This does not yet establish a real-N64 speedup. The next authority step is one fresh hardware package built from exact `d5ce93a0...`, using the already validated M0 SRAM capture method and the exact pinned Gothicvania workload.


## Real-N64 M1 cycle-budget package — READY FOR HARDWARE 2026-09-18

Measurement-package branch: **`phase2/apu-cycle-budget-hardware-m1@3d4555e5f4174770f1c98a8209fc6809ca57a447`**.
Runtime core authority: **`phase2/apu-cycle-budget-clean@d5ce93a03b2dbf5065fefa5276533e02f9658215`**.

Direct package-branch diff from runtime core is exactly one file:
`.github/workflows/apu-m1-hardware-package.yml`. No runtime source differs.

**APU M1 Real N64 Package `35358185620` SUCCESS**, package job `105642608821`.
Artifact:
- ID **`10552617325`**;
- name `sodium64-real-n64-m1-gothicvania`;
- artifact digest **`sha256:5e4ef08c647b2b9a3af905855258ca63809fa2767c3554bce1848b087c171100`**;
- expires 2026-10-02.

Package identity:
- `runtime_core_sha=d5ce93a03b2dbf5065fefa5276533e02f9658215`;
- mode `PROFILE=1 + HW_PROFILE=1`;
- warmup 2 complete 60-VI windows;
- measurement 5 complete 60-VI windows;
- frameskip 0;
- APU clock 21;
- audio 4;
- precision 8;
- pinned Gothicvania payload SHA256 `5519d51ff9c803c1653add5eca0585f37fe8bd96e2b1a758b1d5c7f3ee2ee519`;
- wrapped N64 ROM SHA256 **`d9c151c3246ecd553af247d565c52bad94ae33fe513b4f1a9f075f48fce1614b`**;
- underlying HW_PROFILE Sodium64 ROM SHA256 `8546b5fb7928b0d69d46dc9387bdaf926b2688fffc08579919a8f89f76d3df41`.

The workflow verified the embedded 512 KiB Gothicvania payload hash after wrapping and verified every package file against `SHA256SUMS.txt`.

### RESUME HERE — hardware authority required
Run **only** `sodium64-m1-gothicvania.z64` from artifact `10552617325` on the real N64/SummerCart64.

Procedure:
1. launch the ROM directly;
2. do not press the controller or open settings;
3. let automated Gothicvania gameplay run through 2 warmup + 5 measured 60-VI windows;
4. wait for the **solid red screen**, which is emitted only after SRAM capture DMA completes;
5. wait ~2 seconds, then use normal reset/return-to-cart flow so SRAM persists; do not power off first;
6. retrieve the SRAM/save for this ROM;
7. record whether gameplay, music and SFX looked/sounded sane before red.

Return the save file. Decode it with the package's `hw_profile_report.py` and exact ELF/map.

Hardware decision:
- compare the five real-N64 frame-budget windows against M0 **48,49,48,50,50 (mean 49.0/60)**;
- verify frameskip/APU/audio/precision metadata and sample density;
- compare R4300 profile distribution, especially APU/JIT/DSP and VI wait;
- use real hardware, not ares wall time, to decide whether the cycle-budget architecture materially advances M1.

Do not merge to master or update Road-to-1.0 convergence claims until this hardware result is interpreted.


## Real-N64 M1 cycle-budget milestone — MEASURED 60/60 x5 2026-09-18

Hardware authority capture received from exact package:
- runtime core **`phase2/apu-cycle-budget-clean@d5ce93a03b2dbf5065fefa5276533e02f9658215`**;
- package branch **`phase2/apu-cycle-budget-hardware-m1@3d4555e5f4174770f1c98a8209fc6809ca57a447`**;
- package artifact **`10552617325`**, artifact digest `sha256:5e4ef08c647b2b9a3af905855258ca63809fa2767c3554bce1848b087c171100`;
- wrapped ROM SHA256 **`d9c151c3246ecd553af247d565c52bad94ae33fe513b4f1a9f075f48fce1614b`**;
- returned SRAM/save decoded successfully by the exact package `hw_profile_report.py`.

Strict hardware capture validation:
- capture format: canonical big-endian;
- complete=1;
- warmup: 2 complete 60-VI windows;
- measurement: 5 complete 60-VI windows;
- sample count: **3580** at interval **65521**;
- frameskip: **0**;
- APU clock: **21** (full-rate project target);
- audio setting: **4** (active);
- precision: **8**;
- frame queue at capture: 1.

**REAL-N64 FRAME BUDGET:**
**60/60, 60/60, 60/60, 60/60, 60/60**.
Mean: **60.0/60**.
M0 authority baseline was **48,49,48,50,50**, mean **49.0/60**.

This is an absolute improvement of **+11.0 completed guest frames per 60-VI window on average**, about **+22.45%** relative completed-frame throughput versus M0, and eliminates the measured frame-budget deficit in this representative hardware workload.

Exact real-N64 R4300 sample profile (3580 valid samples):
- DSP/audio: **21.98%** (787);
- APU/SPC700 static: **20.36%** (729);
- APU JIT generated: **8.69%** (311);
- combined APU/JIT/DSP-audio: **51.03%**;
- S-CPU interpreter: **19.75%** (707);
- frame/VI wait: **11.51%** (412);
- PPU/events/frame prep: **8.63%** (309);
- DMA/HDMA: **7.01%** (251);
- RSP/VRAM semaphore wait: **2.01%** (72);
- input: **0.06%** (2).

Comparison to M0 real hardware:
- combined APU/audio: **61.83% -> 51.03%** (down 10.80 percentage points, ~17.5% relative share reduction);
- S-CPU: **22.12% -> 19.75%**;
- VI idle/headroom: **essentially 0% -> 11.51%**;
- frame budget: **49.0/60 -> 60.0/60**.

**MEASURED / ARCHITECTURE PROOF ON REAL HARDWARE:** the clobber-safe guest-cycle-bounded SPC700 multi-op JIT materially improves the representative real-N64 M1 workload while preserving frameskip=0, full-rate APU, active audio, precision=8, and the previously validated emulator-lab DSP scheduler invariant (max < one DSP period, multi-due=0).

User-provided video from the same run visually shows active Gothicvania gameplay and the final solid-red completion screen. Video is observational evidence only; SRAM is the performance/settings authority.

**What this proves:** this representative base workload now sustains the native 60/60 frame-budget target on real N64 under Road-valid settings, with measurable VI headroom and materially reduced APU/audio share.

**What this does NOT yet prove:** Gate B across the defined base-system corpus, complete audio waveform fidelity, broad commercial compatibility, or 1.0. One representative workload reaching 60/60 is a major M1 milestone, not a full base-system release claim.

### RESUME HERE
Interpret this as a major M1 convergence event. Before choosing the next optimization:
1. update Road/Roadmap only to the extent milestone/gate convergence has materially changed;
2. decide whether M1 exit condition is now satisfied or whether one additional representative hardware workload is required for milestone closure;
3. do **not** immediately optimize further against Gothicvania FPS because this workload now has **11.51% VI wait** on real hardware and is no longer throughput-bound;
4. re-profile/choose the next gate driver using a broader representative base workload/corpus rather than chasing more speed in this already-native workload;
5. keep the cycle-budget emitter architecture; v1 remains SUPERSEDED, v2 clean candidate is the valid implementation.


## Independent red-team audit after real-N64 60/60 — 2026-09-18

Independent Astra/Codex read-only audit reproduced the M0 and M1 SRAM decodes and profiles from the original artifacts and verified the recorded branch/commit identities, package provenance and checksums. The auditor did **not** modify the repository.

Additional authority:
- returned M1 SRAM SHA256: **`674e426257dff80ad1bcf3bbdd9837d3f68fe8f9d7a48f2fd21d2296d80f1582`**;
- audit independently reproduced M0 **48,49,48,50,50 /60** and M1 **60,60,60,60,60 /60**;
- both captures validate frameskip 0, APU clock 21, audio 4, precision 8 and complete capture state.

### Interpretation corrections

**SUPPORTED INTERPRETATION:** the measured real-N64 result establishes that the **combined timing-foundation + cycle-budget-v2 candidate** removes the Gothicvania frame-budget deficit for the measured hardware segment. Do not attribute the entire M0 49/60 -> M1 60/60 jump to the cycle-budget change alone.

Reason: the corrected timing foundation already reached the ares throughput ceiling while still violating DSP lateness. The strongest causal claim for cycle-budget v2 is that it preserved multi-op throughput while restoring the required scheduler return bound.

**REJECTED wording:** “cycle-budget alone produced +22.45% speedup.” The +22.45% figure is the relative increase in completed guest frames per 60-VI measurement window between two different full runtime states, not isolated causal attribution to one emitter patch.

**REJECTED wording:** “APU/audio costs 17.5% less.” The real-hardware profile shows APU/JIT/DSP **share** moving from 61.83% to 51.03%; statistical sample share is not an absolute cost measurement normalized to identical guest work.

**MEASURED:** M1 has 11.51% R4300 frame/VI wait in this capture. **SUPPORTED INTERPRETATION:** Gothicvania is no longer useful as an FPS-ranking workload for further optimization. **UNKNOWN:** that wait fraction is not a universal spare-N64 budget and does not directly measure unused RSP capacity.

### Cycle-budget contract audit

The source audit supports the current compile-time budget model:
- source/operand fetch through `jit_read8`: +1 guest cycle;
- fixed cycles through `jit_charge_cycles`: +N;
- conditional runtime cycles: budget worst-case/taken value;
- generated calls to guest `apu_read8` / `apu_write8`: +1 guest bus cycle;
- `jit_block_cycles` is compile-time accounting only and is not itself charged again at runtime.

Finite-op bound remains:
- completed-block continuation threshold = 20 SPC cycles;
- largest pinned finite single opcode = DIV at 12 SPC cycles;
- therefore a continued block can reach at most **32 SPC cycles = 672 master cycles** before scheduler return.

Important mathematical clarification: the **block duration may equal one DSP period**; the scheduler lateness remains strictly below one period if DSP is serviced whenever `s3 <= a3` before block entry and entry begins with positive headroom.

This contract is explicitly tied to the Road-valid **APU clock 21** configuration and must not be generalized blindly to other clock settings.

### Remaining bounded proof gap

Current dynamic APU proof contains **114 directed cases plus halted-state observations**. It validates audited families and regressions; it is **not** an exhaustive 256-opcode/state/composition proof.

The current largest deliberate block debit exercised by the proof is 22 SPC cycles (the long-NOP temporal-cutoff case). The exact **20 + DIV = 32-cycle boundary** has not yet been exercised dynamically.

**TODO / immediate proof batch:**
1. a 20-cycle NOP prefix followed by DIV;
2. a 20-cycle prefix built using real guest accesses followed by DIV;
3. taken/not-taken branch cases near the temporal cutoff;
4. a few tag/cache/reuse boundary cases, comparing first compile against cached execution.

Acceptance:
- compile-time budget is conservative relative to executed guest work;
- no produced block exceeds 32 SPC cycles;
- expected debit/state remain exact;
- cached execution matches initial compilation;
- no stale/self-modifying reuse is observed in the directed boundary cases.

This is a small extension of the existing proof harness, **not** a new profiling/tooling project.

### Accuracy risks preserved for later Gate C work

These are not demonstrated Gothicvania failures and were not introduced by v2, but remain architectural correctness boundaries:

- Some dummy reads are represented as cycle charge only rather than emitted observable bus reads; total cycles can therefore be correct while I/O side effects differ, especially around timer/DSP/port registers.
- Tag validation on block entry protects later reuse but does not by itself prove that a write performed during an executing block cannot invalidate not-yet-executed instructions within that same block.
- Future emitter helpers that bypass `apu_read8`/`apu_write8` or reintroduce direct guest-memory accesses could escape the cycle-budget accounting even if runtime debits remain correct. Any future APU-memory fast path must preserve or extend the budget contract deliberately.

### Milestone interpretation

**SUPPORTED INTERPRETATION:** M1's material performance objective is satisfied by the validated candidate: a measured APU/audio bottleneck was reduced enough for the representative hardware workload to reach native frame budget under Road-valid settings.

**ENGINEERING CLOSURE still required before declaring M1 closed/integrated:** complete the bounded edge proof above and integrate the clean candidate into `master` through normal validation.

A second hardware workload is **not** required retroactively to close M1. Broader workload coverage belongs to M2 / Gate B.

**Gate B remains OPEN.** The current SRAM does not prove sustained presentation cadence over a base corpus, AI underrun behavior, long-run A/V drift, PCM equivalence, or broad base-system compatibility.

### Direction after M1 closure

Do not resume Gothicvania FPS optimization or automatically return to `apu_read8`/`apu_write8` optimization.

After the bounded edge proof and integration:
- define a small base-system corpus with distinct CPU / PPU-HD-MA-Mode7 / audio characteristics;
- use emulator labs to filter correctness/progression;
- take the corpus to real N64 in one milestone batch;
- choose the next optimization or accuracy recovery from the **first demonstrated gate blocker**, not from subsystem sample share alone.

No evidence currently justifies cartridge assistance, a clean-sheet second emulator, or an immediate 65C816 dynarec.


## Cycle-budget boundary proof — running 2026-09-18

Diagnostic proof child:
**`phase2/apu-cycle-budget-edge-proof@4f197702ff81687d68a33842105c907b888a2be6`**, based on validated proof authority `151466bb...`.

Direct diff from proof authority:
- `.github/workflows/apu-cycle-proof.yml`: +1 branch-trigger line;
- `scripts/apu_cycle_proof.py`: directed proof additions only;
- **no emulator/runtime source changed**.

New bounded cases:
1. **`budget_20_nop_div_32`** — 10 NOPs (20 SPC cycles) + DIV (12), with a trailing sentinel NOP; expected compiled/executed block = exactly **32 cycles**, PC stops before sentinel.
2. **`budget_20_access_div_32`** — four real direct guest reads + four NOPs form a 20-cycle prefix, then DIV reaches exactly 32; validates that generated `apu_read8` costs participate in the temporal budget.
3. **`budget_branch_taken_22`** / **`budget_branch_not_taken_20`** — conditional path near cutoff, checking static debit plus runtime taken-cycle behavior.
4. Cached exact-32 block re-entry without mutation must reuse the existing block with identical debit/post-state and unchanged JIT pointer/lookup.
5. A covered-region tag increment before re-entry must force recompilation rather than execute the stale cached block.

Acceptance:
- all historical proof invariants remain green;
- every new `budget_*` case total <=32 SPC cycles;
- exact 20+DIV case reports 32 cycles and stops before trailing sentinel;
- access-built 20+DIV also totals 32 with correct state/debit;
- cached replay matches initial execution without recompile;
- covered tag mutation forces recompile.

Falsifiers:
- any produced edge block >32 cycles;
- missing access cost in the budget;
- wrong runtime branch debit/state;
- cached execution differs from initial execution;
- stale block survives an entry-tag mutation;
- any historical semantic/timing regression.

This proof does **not** attempt to close known Gate-C debts around observable dummy-read side effects or intra-block self-modifying code. Those remain explicitly separate accuracy work.

Exact triggered runs:
- **APU Cycle And Span Proof `35380159442`** @ `4f197702ff81...` — pending
- **Build and Validate `35380159566`** @ `4f197702ff81...` — pending
- **APU Cycle And Span Proof `35380154641`** @ `385caf3e0411...` — in_progress
- **Build and Validate `35380154737`** @ `385caf3e0411...` — completed/cancelled
- **Build and Validate `35380150454`** @ `151466bb39ab...` — in_progress


## Cycle-budget boundary proof attempt 1 — HARNESS FALSE NEGATIVE 2026-09-18

Exact attempt: **`phase2/apu-cycle-budget-edge-proof@4f197702ff81687d68a33842105c907b888a2be6`**.

- **Build and Validate `35380159566` SUCCESS** — runtime/build/Mupen remained green.
- **APU Cycle And Span Proof `35380159442` FAILED** only in the newly added cache-reuse assertion.
- diagnostic artifact **`10561814892`**, digest `sha256:0934deb69528d3da795b23834ad1e333756cbddee839bfec802f02dc209d80e4`.

The temporal-edge cases themselves **passed**:
- `budget_20_nop_div_32`: static/total debit **-672 master = 32 SPC cycles**, PC stopped at `0x020B` before the sentinel, DIV post-state matched.
- `budget_20_access_div_32`: static debit **-588** (28 static units) plus four real guest-read cycles produced exact total **-672 / 32 SPC cycles**, with correct DIV state.
- `budget_branch_taken_22`: exact 22-cycle total with expected +2 runtime taken debit.
- `budget_branch_not_taken_20`: exact 20-cycle total with identical compile-time worst-case shape and no taken debit applied.
- all historical cases reached the cache-reuse phase without a timing/semantic failure.

The tag-mutation half of the reuse experiment also worked:
- covered region tag increment changed the lookup/pointer on re-entry;
- stale block was rejected and recompilation occurred.

**HARNESS FALSE NEGATIVE:** the cached-reuse check was executed only after the rest of the full proof matrix. Every proof case uses the same fixed `TEST_PC=0x0200` and recompiles its own block there. Therefore the lookup and guest bytes no longer represented `budget_20_nop_div_32` when the reuse check ran. Evidence: the mutation byte observed at `0x0200` was **0xBE (DAS)** rather than the NOP expected from the 20+DIV seed. The observed cached debit/state therefore belonged to a later proof case and cannot test the intended block.

This failure is **REJECTED as runtime/cycle-budget evidence**.

Immediate repair: immediately before cache-reuse measurement, compile a fresh dedicated 20-NOP-cycle + DIV seed at the fixed test PC, then perform unchanged cached replay and tag-mutation checks before any other case can overwrite that lookup. No runtime source changes are permitted.


## Cycle-budget boundary proof — VALIDATED 2026-09-18

Final proof authority:
**`phase2/apu-cycle-budget-edge-proof@c72068140caa8d7c8b4c862c86de9ef59a9f9231`**.

CI:
- **APU Cycle And Span Proof `35382966438` SUCCESS**, dynamic job `105723612910`;
- **Build and Validate `35382966472` SUCCESS**: normal build, PROFILE build and pinned Mupen smoke green.
- proof artifact **`10562273321`**, digest `sha256:7db0e005a55a19ac20c311cf00cb0bd3f26d9c619b816178a4ce0c173734d9ef`;
- exact proof build **`10562117702`**, digest `sha256:52ceeab65be69f74b41697b6f39129b4bdf3d14c6d067a8270b4a09e5e39798c`.

Validated new edge evidence:
- `budget_20_nop_div_32`: **32 SPC cycles / 672 master cycles exact**, PC stops before trailing sentinel, DIV state correct.
- `budget_20_access_div_32`: four real guest reads contribute runtime bus cycles; total remains **32 SPC cycles exact** with correct state.
- `budget_branch_taken_22`: total **22**, including expected runtime taken debit.
- `budget_branch_not_taken_20`: total **20**, with conservative compile-time branch budget and correct untaken runtime behavior.
- dedicated `budget_reuse_seed_32`: cached replay executed the exact same 32-cycle block with unchanged lookup/JIT pointer and identical PC/A/Y/flags.
- covered tag mutation incremented the region tag and **forced recompilation**; stale entry was not reused.

Proof summary additionally remained true:
- all static debits match source prediction;
- all runtime debits match expected;
- all total debits match pinned reference;
- all semantics match expected;
- all halt scheduler ticks match expected;
- long-probe temporal cutoff remains bounded;
- all directed cycle-budget edge cases <=32;
- exact 20+DIV reaches 32;
- cached replay succeeds without recompile;
- covered entry-tag mutation forces recompile.

The earlier `4f197702...` proof failure is **HARNESS FALSE NEGATIVE / SUPERSEDED**, caused by testing cached replay after later cases had replaced the fixed TEST_PC lookup. No runtime change was needed.

**M1 bounded architecture contract is now validated to the intended edge.** This still does not prove intra-block self-modifying-code behavior or observable dummy-read I/O effects; those remain Gate-C accuracy debt, not blockers to this M1 performance integration.

### Integration discovery
Direct comparison shows `phase2/apu-cycle-budget-clean` is **not** a fast-forward child of current `master`:
- current master: `a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`;
- clean: `d5ce93a03b2dbf5065fefa5276533e02f9658215`;
- merge base: `ee86d3391f9ef7f407b9b3f683b145253ff1ef3f`;
- clean is 40 commits ahead of merge base while master contains 4 commits absent from clean.

**Do not merge the historical clean branch wholesale.** Next action: inspect the 4 master-only commits and reconstruct a fresh M1 integration branch from current master, porting the validated production state without losing current master changes or diagnostic-only branches.


## M1 master integration candidate — running 2026-09-18

Integration branch: **`phase2/m1-integration@671ed75c1f736ebb18bba7c40ec663b278f32865`**.
Parent authority: current **`master@a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`**.

### Runtime integration method
Historical `phase2/apu-cycle-budget-clean` diverges from master because master gained four documentation-only commits after their old merge base. To avoid importing rejected/noop experimental history, the M1 runtime was reconstructed **from current master** using an atomic Git tree whose 14 changed runtime/infrastructure files point to the exact final blob SHAs from clean `d5ce93a0...`.

First integration runtime commit:
**`bc64e8e6080aed53f8f85cff460ddbc930cbe4c1`**.

The master-only changes absent from historical clean were verified to be documentation only:
- `81e14f5f...` Road-to-1.0 M0/M1 docs;
- `69f893bc...` Roadmap APU-first route;
- `90fafc89...` Profiling M1 guidance;
- `a2270699...` docs synchronization.

No current-master emulator/runtime change was overwritten.

Exact clean blobs consumed include the validated emitter blob:
`src/apu_emitter.S = fc510743836c2a0a8afca771ca016cf2d02bf83a`
plus the final timing-foundation APU files and M0 hardware-profile infrastructure.

### Durable regression proof
The final edge-proof harness was preserved without importing proof-branch runtime diagnostics:
- `scripts/apu_cycle_proof.py`;
- `.github/workflows/apu-cycle-proof.yml`.

The durable workflow runs automatically on `master` only for relevant APU/JIT/proof paths (and on the integration branch for this graduation), plus manual dispatch. It does **not** import `src/apu_cycle_diag.S` or PROFILE-only diagnostic emitter changes.

Exact edge-proof scope now documented in Validation:
- **119 directed execution cases + 2 persistent SLEEP/STOP halt groups**;
- exact 20+DIV=32;
- access-built 32-cycle edge;
- conditional paths near cutoff;
- cached replay;
- entry-tag mutation/recompile;
- historical timing/address/semantic families.

### Canonical documentation convergence
On the integration branch:
- `ROAD_TO_1_0.md`: **M0 + M1 achieved; M2/Gate B active**;
- `ROADMAP.md`: Phase 2/M1 achieved; Phase 3 corpus discovery active; no automatic `apu_read8`/DSP/dynarec next step;
- `PROFILING.md`: matched guest-window and real-N64 SRAM authority, throughput vs event cadence vs presentation vs audio distinction, sample-share interpretation limits, Gothicvania demoted to regression workload;
- `VALIDATION.md`: exact 119-case proof scope and explicit non-coverage (dummy-read I/O effects, intra-block SMC, long-run A/V/PCM, broad compatibility).

The docs preserve the audit correction that the real-N64 49->60 movement belongs to the **combined timing-foundation + cycle-budget state**, not the final emitter patch alone, and that 61.83%->51.03% is a change in profile share rather than normalized absolute cost.

### Final integration gates now running
- final branch **Build and Validate `35384286620`** @ `671ed75c...` — pending/running;
- integrated runtime **APU Cycle And Span Proof `35384115986`** @ `5cf83f31...` — running. Later commits are documentation-only, so this proof exercises the exact integrated runtime/proof code.

Previous Build-and-Validate runs cancelled by subsequent sequential integration/doc commits are superseded and are not failure evidence.

### Decision map
If both gates pass:
1. open PR `phase2/m1-integration -> master`;
2. verify PR diff/status and merge without altering the candidate;
3. verify resulting master CI;
4. mark **M1 MERGED-CONSUMED / ACHIEVED** in continuity;
5. begin M2/Gate-B corpus definition as the next technical batch.

If either gate fails, do not merge; isolate whether failure belongs to runtime, durable proof packaging, documentation workflow behavior, or laboratory.


## Integrated durable proof attempt 1 — HARNESS FALSE NEGATIVE 2026-09-18

Integration runtime remained green under final **Build and Validate `35384286620`**:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen normal/profile smoke SUCCESS.

The first durable integrated proof run **`35384115986`** at integration runtime/proof SHA `5cf83f31b0fae672e347b6310530372bf4e974f3` failed after the newly added cycle-budget edge/reuse cases had already passed.

Observed failure:
`RuntimeError: target rejected memory read at 0x8000E600: ED2FFD`.

This is **HARNESS FALSE NEGATIVE / REJECTED as runtime evidence**.

Cause:
- GDB RSP memory reads return raw hexadecimal text;
- the guest bytes `ED 2F FD` legitimately return `ED2FFD`;
- the master-era `scripts/gdb_rsp_dump.py` treated **any** reply beginning with ASCII `E` as an RSP error;
- the validated proof branch had already corrected this parser to recognize an error only when the reply has the three-byte RSP error form (`len(reply) == 3 && startswith("E")`);
- that one-line harness fix was accidentally omitted when preserving the proof on the fresh master-based integration branch.

Evidence that the runtime/proof contract itself was healthy before the parser false positive:
- `budget_20_nop_div_32`: exact 32 SPC cycles, semantic/debit/span checks true;
- `budget_20_access_div_32`: exact 32 total cycles with real guest-read timing included;
- taken/not-taken cutoff branch checks true;
- fresh cached 32-cycle replay: same -672 debit, same PC/A/Y/flags, lookup/JIT pointer unchanged;
- covered tag mutation: stale block rejected and lookup/JIT pointer changed through recompilation.

The integration branch must consume the exact validated one-line RSP parser fix before re-running the durable proof. Also add `scripts/gdb_rsp_dump.py` to the proof workflow path filter because the proof imports `RSPClient` from that file.

No emulator/runtime source change is authorized by this finding.


## M1 integration durable-proof parser repair — running 2026-09-18

Integration branch advanced to **`phase2/m1-integration@d701f80f5339c727f231e4e9cc2b7222ec9c1561`**.

Changes since the previously Build/Validate-green `671ed75c...`:
- `scripts/gdb_rsp_dump.py`: consume the already-validated one-line RSP parser fix from the edge-proof line, recognizing only the three-byte `E??` RSP error form rather than misclassifying arbitrary E-prefixed memory hex data;
- `.github/workflows/apu-cycle-proof.yml`: add `scripts/gdb_rsp_dump.py` to the path trigger because the proof imports `RSPClient` from that file.

No emulator/runtime source changed. The 14 M1 runtime/infrastructure blobs consumed from clean remain unchanged from the real-N64 60/60 candidate.

Exact current runs:
- **APU Cycle And Span Proof `35385014498`** @ `d701f80f...` — running;
- **Build and Validate `35385014527`** @ `d701f80f...` — queued/running.

Question: does the durable proof reproduce the already-green edge-proof result once its exact validated RSP parser dependency is present?

Acceptance:
- all 119 directed cases + halt groups pass;
- exact 32-cycle/access/branch/cache/tag invariants remain true;
- final Build and Validate remains green.

Falsifier:
- any timing/semantic/cache/tag invariant fails after the parser repair, or final build/smoke regresses.

If accepted, this closes the final pre-PR integration gate. If not, do not merge; classify the failure before changing runtime.


## M1 integration pre-PR gates — VALIDATED 2026-09-18

Final integration branch authority:
**`phase2/m1-integration@d701f80f5339c727f231e4e9cc2b7222ec9c1561`**.

No emulator/runtime source changed after the validated M1 runtime integration commit; later changes preserve the durable proof, canonical docs and the one-line RSP harness parser dependency.

### Final Build and Validate
**Run `35385014527` SUCCESS** at exact HEAD `d701f80f...`:
- normal build SUCCESS;
- PROFILE build SUCCESS;
- pinned Mupen normal/profile smoke SUCCESS.

Artifacts:
- normal build **`10564130283`**, digest `sha256:4f87d77b053bf7be137ca5f657aa74d38a272af66b524134674950d4cd858ce4`;
- PROFILE build **`10563627262`**, digest `sha256:d3a36d51c4251f4fc4119a7da7b0a06b92f5cf43dfbf50f469251fda542a2524`;
- emulator smoke **`10563682276`**, digest `sha256:6d0bac540a4178f8bfa81d4a85752e32223b5cf9fcb868e2e26797dbbff3aea5`.

### Final durable SPC700 cycle-budget proof
**APU Cycle And Span Proof `35385014498` SUCCESS**, exact HEAD `d701f80f...`, dynamic job `105730158853`.

Artifacts:
- exact proof build **`10563771898`**, digest `sha256:93cb8ee27b798a15eeb0457d872f1cbf1ce94f01fe18cc86bf816294fd8fc05b`;
- proof diagnostics **`10563443390`**, digest `sha256:7973295305bc6f71cbb131dbc22228d696cd131e1dce6220600fcde063627096`.

All durable summary invariants are true:
- all cycle-budget edge cases <=32 SPC cycles;
- all static debits match prediction;
- all runtime debits match expected;
- all total debits match pinned reference;
- all semantics match expected;
- all header spans match expected;
- all SLEEP/STOP halt scheduler ticks match;
- long temporal-cutoff probe remains bounded;
- exact 20+DIV reaches 32;
- cached exact-32 replay reuses without recompilation and reproduces state/debit;
- covered tag mutation forces recompilation.

The prior integrated proof failure `35384115986` is **HARNESS FALSE NEGATIVE / SUPERSEDED** by the exact RSP parser dependency repair. It is not runtime failure evidence.

State: **VALIDATED / READY FOR PR TO MASTER**.

Next action: open `phase2/m1-integration -> master`, verify mergeability/diff/checks, merge without modifying the candidate, then validate the resulting master SHA before marking M1 MERGED-CONSUMED.


## PR #12 — M1 integration candidate OPEN / awaiting PR-only lab gate 2026-09-18

PR: **#12 `phase2/m1-integration -> master`**
Title: `M1: integrate validated SPC700 timing and cycle-budget core`.
Exact head: **`d701f80f5339c727f231e4e9cc2b7222ec9c1561`**.
Base at PR open: **`master@a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`**.

GitHub recalculated the initial transient `mergeable=false` to:
- `mergeable=true`;
- `rebaseable=true`;
- `mergeable_state=unstable`.

There is **no merge conflict**. The unstable state is due to an additional PR-only workflow currently running:
- **Ares Profile Validation `35385948762`** @ exact PR head `d701f80f...`.

Already-green exact-head pre-PR gates remain:
- Build and Validate `35385014527` SUCCESS;
- durable APU Cycle And Span Proof `35385014498` SUCCESS.

Decision:
- wait for the PR-only Ares validation;
- if green, merge PR #12 without modifying the candidate;
- if it fails, classify the failure as workload/lab/runtime before merge.


## PR #12 PR-only Ares gate — VALIDATED 2026-09-18

Exact PR head remains:
**`phase2/m1-integration@d701f80f5339c727f231e4e9cc2b7222ec9c1561`**.

**Ares Profile Validation `35385948762` SUCCESS** on the exact PR head.

Jobs:
- profile-build SUCCESS;
- ares-smoke SUCCESS;
- pinned N64-only ares build SUCCESS;
- deterministic workload generation SUCCESS;
- interpreter control + CPU-JIT workload matrix SUCCESS;
- frame-budget/profile report generation SUCCESS.

Road-valid runtime state was observed during the lab:
- `apu_clock=21`;
- audio `4`;
- precision `8`;
- valid statistical sample densities for the decision matrix.

Artifact:
- `sodium64-ares-profile-matrix` ID **`10564595266`**;
- digest **`sha256:f4bc1721be208f84046a37b3d5360c8c3673a76082964f1945e1ddaec5ba32a6`**.

Exact profile-build artifact:
- ID **`10563408739`**;
- digest `sha256:0dcdc3439594d540ce3745617affb84dcdca7f49d3392889722c7cf2bc9c2f7e`.

Interpretation: this is the additional PR-only emulator-lab regression gate. It does not supersede real-N64 hardware authority, but no lab regression was found that blocks integration.

PR #12 is currently:
- open;
- `mergeable=true`;
- no merge conflict;
- exact head unchanged from all green pre-merge gates.

**PRE-MERGE STATE: VALIDATED / READY TO MERGE.**

Next action: squash-merge PR #12 to keep the mainline history free of integration/harness intermediate commits while preserving the exact validated final tree, then validate the resulting master SHA before marking M1 MERGED-CONSUMED.


## PR #12 MERGED — post-merge validation running 2026-09-18

PR **#12** was squash-merged successfully.

New integrated authority:
**`master@ac1ce74740d974b70206fcb6ba842e492b5d7272`**.

Squash integrity check:
- PR head `d701f80f5339c727f231e4e9cc2b7222ec9c1561` tree: `28147decc7994542d352738c43f40fe1249bbb71`;
- merged master `ac1ce747...` tree: `28147decc7994542d352738c43f40fe1249bbb71`;
- **exact tree match = true**.

Therefore the squash merge changed commit history only; it did not alter the validated candidate tree.

Merge parent:
- previous master `a2270699e60cdf2b8b8303aaa5a1aa4a0e8dd89e`.

Post-merge exact-SHA workflows automatically triggered:
- **Build and Validate `35387454297`** @ `ac1ce747...` — running;
- **APU Cycle And Span Proof `35387454371`** @ `ac1ce747...` — running;
- **Ares Profile Validation `35387454367`** @ `ac1ce747...` — running.

Do **not** mark M1 MERGED-CONSUMED until these post-merge gates finish. Because the merged tree is byte-identical to the fully validated PR tree, any new failure must first be classified as workflow/lab nondeterminism versus genuine exact-tree regression rather than assumed to be a new code change.

Next action:
- wait for all three exact-master-SHA gates;
- if green, mark M1 **MERGED-CONSUMED / ACHIEVED** and move RESUME HERE to Gate-B corpus definition;
- if any fails, inspect exact failure before changing code.


## M1 MERGED-CONSUMED / ACHIEVED — 2026-09-18

Integrated authority:
**`master@ac1ce74740d974b70206fcb6ba842e492b5d7272`**.

PR #12 was squash-merged with an exact tree match to the fully validated PR head.

All exact-master-SHA post-merge gates are green:
- **Build and Validate `35387454297` SUCCESS**;
- **APU Cycle And Span Proof `35387454371` SUCCESS**;
- **Ares Profile Validation `35387454367` SUCCESS**.

Therefore the M1 runtime and its durable regression proof are now **MERGED-CONSUMED** in master. M1 is **ACHIEVED**. Gate B / M2 is the active milestone.

The authoritative M1 hardware result remains the real-N64 Gothicvania capture:
- 60,60,60,60,60 /60;
- frameskip 0;
- APU clock 21;
- audio 4;
- precision 8;
- 3,580 samples;
- 11.51% frame/VI wait.

Do not resume Gothicvania FPS optimization unless a later regression makes it gate-relevant again.

## Gate-B autonomy constraint — 2026-09-18

Iron clarified an architectural workflow requirement:

**The normal technical loop must remain autonomous through repository-accessible infrastructure. Do not make local commercial ROMs, Iron's powered-on PC, or Iron's continuous availability a dependency of routine diagnosis, iteration or gate selection.**

Consequences:

- The **primary Gate-B development corpus must be fully reproducible by the assistant/CI from legally redistributable/open sources or generated test workloads available from GitHub-accessible infrastructure.**
- Do **not** fill the corpus with near-duplicate workloads merely because they are convenient. Diversity of engine/toolchain and exercised SNES subsystems is required.
- Gothicvania remains one representative regression workload, not the template all new workloads must resemble.
- Open-source/source-available workloads may be patched for deterministic input/checkpoints when the patch is explicit, hashed and does not amputate required emulation work.
- Commercial ROMs may be used later as **supplemental representativeness / milestone validation** when Iron is available, but they must never become the main daily development loop.
- Commercial ROM bytes must not be committed or uploaded to GitHub/Actions/artifacts. A commercial test, if later used, is local-only and should be requested only when a sufficiently mature batch has accumulated and multiple autonomous lab checks already indicate it is worth testing.
- Real N64 remains final performance authority, but hardware sessions should aggregate multiple hardware-ready questions/workloads rather than serving as an iterative debugger.

This refines the red-team Batch-2 interpretation:
- Astra's requirement is a **small diverse base corpus**, not specifically a commercial corpus.
- First build a diverse autonomous corpus and use it to discover the next Gate-B blocker.
- Use commercial software later to test representativeness once autonomous evidence has converged enough to justify a milestone session.

### RESUME HERE — Gate B / M2

M1 is integrated and closed.

Immediate next technical batch:
1. define a **four-workload autonomous Gate-B corpus**: Gothicvania plus three non-redundant workloads chosen for materially different CPU/gameplay, PPU/HDMA/Mode-7, and audio behavior;
2. prefer different codebases/toolchains/engines where practical rather than three more PVSnesLib examples;
3. pin source commit/toolchain/input/checkpoint/ROM hash and expected observable behavior for every workload;
4. run them first in reproducible emulator labs and classify failures before changing runtime;
5. choose the next runtime intervention only from the first demonstrated corpus blocker;
6. reserve commercial-ROM and real-hardware validation for a later aggregated milestone after the autonomous corpus has converged.

Do not preselect APU, DSP, PPU, S-CPU dynarec or another architecture before the corpus evidence exists.


## Gate-B corpus selection refinement — 2026-09-18

Iron refined the desired diversity criterion for the three new autonomous workloads:

Choose workloads whose **architectural behavior** approximates three materially different commercial SNES families, using **SMW / DKC / Zelda: A Link to the Past** as reference archetypes. Similarity is about execution patterns and subsystem pressure, not visual style or IP imitation.

Target archetypes:
- **SMW-like:** scrolling platformer, dynamic/map updates, collision/object logic, sprites and per-frame gameplay loop;
- **DKC-like:** heavier audiovisual pressure, entity/animation work, DMA/HDMA/PPU activity and active audio/SPC700;
- **ALttP-like:** top-down area/map logic, scripting/state, object interaction, tilemap updates and transitions.

This remains inside Astra's Batch-2 direction: Gothicvania + three diverse workloads, emulator labs first, one aggregated real-N64 milestone later, next runtime work selected only from the first demonstrated blocker.

Initial research findings, not yet locked:
- `undisbeliever/space-rescue-squad@e08333a6...` is a strong DKC-like candidate: full platformer/game code, custom entity/collision/scrolling engine, HDMA, DMA-time budgeting, animated tilesets and Terrific Audio Driver. Code is zlib; game resources are source-available but restricted to this game, so use only as its own workload.
- `undisbeliever/castle_platformer@79e2eb4e...` is a possible SMW-like candidate: MIT, ca65, dynamic editable map, tile-specific movement/friction, interactive tiles, static platforms and dynamically loaded animated sprites. It may be too simple and shares author/lineage with Space Rescue Squad, so do not lock it without a diversity comparison.
- `Ramsis-SNES/furryrpg@35b4eb22...` is architecturally attractive for the ALttP/RPG role (area loader, scripting, sprite-to-BG collision, Mode-1 world map, Mode-7, SPC700/audio), but repository license metadata/file is absent despite the README describing it as open-source freeware. Treat licensing/reuse status as **OPEN QUESTION**; do not consume or redistribute it until that is resolved.
- `undisbeliever/unnamed-snes-engine` is MIT and top-down but currently a single-screen tech demo; useful fallback/probe, probably too narrow for the main representativeness slot.

Next action: continue candidate search with explicit preference for different authors/toolchains/engines where practical; validate buildability, licensing/distribution boundaries and reproducible deterministic execution before fixing the final three.


## Gate-B candidate quality reassessment — 2026-09-18

Iron challenged whether visually/gameplay-poor homebrew or game-jam projects are representative enough for the three principal Gate-B slots. This distinction matters.

**Selection rule clarified:** visual polish, commercial appeal and fun are not requirements for a performance/correctness workload. However, project scope, sustained gameplay complexity, engine diversity, subsystem activity and duration **are** relevant. A tiny demo may be technically correct yet still be too narrow to represent a commercial-style engine family.

Current reclassification:

- **Space Rescue Squad — STRONG CANDIDATE, still not locked.** Although created for the 2025 SNESDEV game jam and visually modest, repository evidence shows materially nontrivial architecture/content: ~15 authored rooms including boss/water/gravity scenarios; multiple enemy/projectile/entity behaviors; collision and scrolling engine; HDMA; explicit VBlank/DMA-time budgeting; animated tilesets; Terrific Audio Driver; five music themes and substantial BRR/sample content. Its game-jam origin alone does not disqualify it. It must still pass build reproducibility and sustained-workload profiling before occupying a principal slot.

- **Castle Platformer — DOWNGRADED to AUXILIARY / FALLBACK.** It has a legitimate MIT ca65 engine, dynamic map, entity physics, interactive tiles, animated sprites and five levels, but it is explicitly a simple platformer engine/demo, materially smaller, and shares author/technical lineage with Space Rescue Squad. It is useful as an open diagnostic/regression workload but currently does not justify one of the three principal diversity slots if a stronger independent SMW-like candidate exists.

- **Furry RPG — TECHNICALLY STRONG, ELIGIBILITY BLOCKED.** Architecture remains attractive for the ALttP/RPG role: area loader, event scripting, collision, world map, Mode 7, NMI/IRQ work and SPC700/SNESGSS audio. It is WIP and the repository contains no explicit LICENSE despite the README calling it open-source freeware. Do not consume it into the principal corpus until redistribution/automation rights are unambiguous.

Implication: do not confuse source availability with representativeness. The three main slots should survive an **audition** based on sustained real gameplay complexity, independent engine/toolchain lineage, observable subsystem activity and reproducible build/input/checkpoint behavior. Smaller demos remain useful as probes but should not crowd out stronger candidates.


## Gate-B Space Rescue Squad audition — source-build proof running 2026-09-18

First execution-based corpus audition has started on:
**`phase3/gate-b-srs-audition@25f71f2e3690385727fc5b45ff2c0810b5667460`**,
parented directly from integrated **`master@ac1ce74740d974b70206fcb6ba842e492b5d7272`**.

This branch changes **workflow only**. No Sodium64 runtime/emulator source is modified.

Question:
Can the strongest currently clean DKC-/heavy-platformer candidate, **Space Rescue Squad**, be reconstructed autonomously and reproducibly from its exact public source without Iron's PC, proprietary Aseprite regeneration, or redistribution of its ROM?

Pinned upstream:
- `undisbeliever/space-rescue-squad@e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865`;
- `bass-untech@9db6088a378061afc7b82f50997a5b9a1d951175`;
- `untech-editor@4c72dc69619c0c246aa7e6325b18b6fb3c219821`;
- `terrific-audio-driver@17823e5a55893e8442917abadb4e84feb216e5ad`.

Controlled build proof:
- builds the exact upstream CLI tools from pinned submodules;
- uses committed generated PNG inputs instead of requiring the proprietary Aseprite editor;
- builds the **unmodified release game** first;
- rejects any tracked-source mutation;
- records ROM size/hash and toolchain provenance;
- uploads **provenance/hash only, not the SRS ROM**.

Run:
- **Gate B SRS Audition `35393181107`** @ `25f71f2e...` — queued/running at checkpoint.

Acceptance:
- exact pinned source/submodules reproduce a non-empty release ROM;
- upstream tracked tree remains clean;
- build requires no local/private input;
- only non-ROM provenance leaves the job.

Falsifier / downgrade:
- required source/assets are unavailable or non-reproducible;
- build depends materially on proprietary/local-only tooling despite committed generated inputs;
- fixing the build would require maintaining a second toolchain/project disproportionate to Gate-B value.

If accepted, next controlled step is a **temporary explicit benchmark patch** (auto-start + deterministic input + survival only if needed while preserving collisions/hurt/audio), followed by a pinned ares N64 profile/frame-budget audition at Road-valid settings. Do not request hardware.


## SRS source-build attempt 1 — HARNESS/BUILD INVOCATION FALSE NEGATIVE 2026-09-18

Exact run:
- branch `phase3/gate-b-srs-audition@25f71f2e3690385727fc5b45ff2c0810b5667460`;
- **Gate B SRS Audition `35393181107` FAILED** in the final game-build step.

What passed:
- Ubuntu dependency install;
- exact SRS checkout and all pinned submodules;
- UnTech Editor CLI toolchain build;
- pinned Wiz build;
- Terrific Audio Driver `tad-compiler` build.

Failure:
`python3 ../tables/sine-table.py > gen/tables/sine-table.inc`
returned `Directory nonexistent`.

Cause:
The audition invoked `make ... bin/space-rescue-squad.sfc` directly. Upstream's normal `all` path depends on its `directories` target, which creates `gen/tables` and the other generated-output directories. Directly naming the ROM target bypassed that prerequisite.

Classification:
**HARNESS/BUILD INVOCATION FALSE NEGATIVE / REJECTED as candidate evidence.**
This does not show unavailable dependencies, proprietary-tool dependence or an upstream source defect.

Immediate repair:
run upstream `make -C game directories` before the explicit release-ROM target, then repeat unchanged. No upstream source, assets, Sodium64 runtime or benchmark behavior changes.


## SRS source-build proof — VALIDATED 2026-09-18

Exact candidate/build authority:
- audition branch `phase3/gate-b-srs-audition@0c5f3a3df4f2f790d8c09c5dd2b3f01c6d68e432`;
- **Gate B SRS Audition `35393460280` SUCCESS**;
- upstream SRS `e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865`;
- exact release ROM size **262,144 bytes**;
- exact unmodified release ROM SHA-256 **`d5bd7b17aa19a1b370efa38554b6ebfd77c4756e7184e9f2e848e8193bc9bed0`**.

Pinned-source toolchain successfully rebuilt:
- bass-untech `9db6088a378061afc7b82f50997a5b9a1d951175`;
- untech-editor `4c72dc69619c0c246aa7e6325b18b6fb3c219821`;
- terrific-audio-driver `17823e5a55893e8442917abadb4e84feb216e5ad` plus its pinned Wiz submodule.

No Aseprite binary was required: committed generated PNGs were used as intended build inputs. The tracked upstream tree remained unmodified after the release build.

Provenance-only artifact:
- ID **`10566587049`**;
- digest **`sha256:d1a63b07b6a434cc101da6585da01f25fd4b0a46613c18995008527fda1eab27`**.
- artifact contains hashes/provenance only; **the SRS ROM is not uploaded**.

Interpretation:
**Space Rescue Squad passes the autonomy/buildability gate.** Its game-jam origin does not create a toolchain or source-availability dependency on Iron.

This does not yet establish corpus membership, correctness under Sodium64, representativeness, or real-N64 performance.

Next controlled step:
create an explicit temporary benchmark patch that preserves normal audio/game-state/room/entity/collision/render logic, starts directly in the first gameplay level after normal initialization, and supplies deterministic Right+Run input. Run the resulting workload under the existing pinned ares N64 Sodium64 profile/frame-budget lab at frameskip 0, APU21, audio4, precision8. Do not request hardware.


## Gate-B SRS deterministic-profile attempt 1 — HARNESS FALSE NEGATIVE 2026-09-18

Repo/CI reconciliation found continuity lagging one technical step behind the actual audition branch.

Current audition authority before repair:
- **`phase3/gate-b-srs-audition@300a358e50f88df8a4f03e98dc5f7adb9dc5772b`**;
- branch remains workflow-only relative to **`master@ac1ce74740d974b70206fcb6ba842e492b5d7272`**;
- no Sodium64 emulator/runtime source is changed.

The previously documented source-build proof remains valid:
- **Gate B SRS Audition `35393460280` SUCCESS** @ `0c5f3a3d...`;
- exact unmodified upstream release ROM SHA-256 `d5bd7b17aa19a1b370efa38554b6ebfd77c4756e7184e9f2e848e8193bc9bed0`;
- build is autonomous from pinned public source/toolchain and requires no Iron-local input.

A later commit attempted the next controlled step: explicit deterministic first-level gameplay + Road-valid Sodium64 PROFILE/ares measurement.

Exact run:
- **Gate B SRS Audition `35393812922` FAILED** @ `300a358e...`;
- branch **Build and Validate `35393812773` SUCCESS** at the same SHA.

What the failed audition actually reached:
- source/toolchain checkout/build SUCCESS;
- unmodified SRS release build SUCCESS;
- provenance-only artifact upload SUCCESS;
- **benchmark-creation shell step FAILED before the Python patch executed**;
- all Sodium64 PROFILE, ares, wrapping and profiling steps were skipped.

Exact failure:
`unexpected EOF while looking for matching '\''`.

Cause:
the workflow's post-patch changed-file assertion was emitted with malformed shell quoting:
`test "$changed" = game/src/_main.asm\ngame/src/gameloop.inc'`.

Classification:
**HARNESS FALSE NEGATIVE / REJECTED as SRS or Sodium64 evidence.**
No benchmark ROM was produced and no emulator-profile result exists from this run.

Important non-conclusion:
This run says nothing yet about SRS boot/progression, Sodium64 compatibility, throughput, subsystem pressure, cadence, or corpus suitability.

Immediate controlled repair:
replace only the malformed changed-file shell comparison with a correctly quoted two-line expected value, keep the intended benchmark patch and all profiling settings unchanged, then rerun. Do not change emulator/runtime code and do not request hardware.


## Gate-B SRS deterministic-profile attempt 2 — WORKFLOW PARSE FALSE NEGATIVE 2026-09-18

Repair commit **`phase3/gate-b-srs-audition@07b0b3b152b6e903c3c01289e095d305720c0fda`** attempted to replace the malformed changed-file assertion.

GitHub Actions run:
- workflow/run **`35394545732`** — immediate FAILURE;
- **no jobs were created**;
- Build and Validate for the same branch commit was separately queued/running and is not relevant to this YAML parser failure.

Repo inspection shows the intended ANSI-C quoted expected string did not survive in the workflow file: the block contains only `expected=` before the next command. GitHub therefore rejected the workflow before executing the source-build or benchmark steps.

Classification:
**WORKFLOW PARSE/HARNESS FALSE NEGATIVE / REJECTED as candidate or runtime evidence.**

What this does NOT prove:
- nothing new about SRS build/runtime;
- nothing about benchmark patch validity;
- nothing about Sodium64 compatibility/performance.

Next repair:
avoid multiline shell-string quoting entirely. Materialize actual and expected changed-file lists into temporary files and compare with `cmp`. Keep every benchmark/runtime/profile setting otherwise unchanged.

## Gate-B SRS workflow reconstruction — RUNNING 2026-09-18

Root cause of the immediate parser failures after `300a358e...` was broader than the intended one-line quote repair:
the two attempted edits contaminated the workflow with an accidental **~325-line duplicated tail**.

Evidence:
- compare `300a358e... -> 63ba40f5...`: +325/-1 lines in the single workflow file;
- GitHub rejected the contaminated workflows before creating jobs;
- these runs are **WORKFLOW PARSE FALSE NEGATIVES**, not runtime evidence.

Clean reconstruction:
- rebuilt `.github/workflows/gate-b-srs-audition.yml` from the last GitHub-executed base **`300a358e50f88df8a4f03e98dc5f7adb9dc5772b`**;
- replaced only the malformed changed-file assertion with three simple checks:
  - exactly two changed paths;
  - one is `game/src/_main.asm`;
  - one is `game/src/gameloop.inc`.
- new audition head: **`phase3/gate-b-srs-audition@6e5d444017ca899bcf2b69be6cbf8dd94eee9507`**;
- compare vs `300a358e...`: **+3/-1 lines only**;
- workflow line count restored to 530 (previous contaminated head 852).

Current exact runs:
- **Gate B SRS Audition `35394713398`** @ `6e5d4440...` — running;
- Build and Validate `35394713401` @ same SHA — queued/running.

No Sodium64 runtime/emulator source changed.

Acceptance remains unchanged:
produce the deterministic first-level SRS benchmark from pinned public source, preserve normal emulation/gameplay/audio work, run Road-valid Sodium64 PROFILE under pinned ares, and obtain valid profile/frame-budget evidence.

Until `35394713398` reaches the profile stage, there is still **no SRS execution evidence** beyond the already-validated autonomous source build.

## Gate-B SRS deterministic benchmark — BUILD ACCEPTED / profiling running 2026-09-18

Exact audition head remains **`phase3/gate-b-srs-audition@6e5d444017ca899bcf2b69be6cbf8dd94eee9507`**.

Run **Gate B SRS Audition `35394713398`** has now passed:
- exact pinned SRS/toolchain checkout;
- full CLI toolchain build;
- unmodified release ROM rebuild;
- provenance-only upload;
- **explicit deterministic gameplay benchmark creation and rebuild**.

The benchmark patch therefore compiles successfully and reaches the next lab stage. It:
- keeps normal SRS audio initialization;
- initializes normal game state;
- selects the first authored gameplay room (`a1a_entrance`);
- preserves room/entity/collision/camera/metatile/animation/script/WaitFrame work;
- injects deterministic held Right+Run input in the normal game loop;
- does not disable enemies, collision, audio, PPU work, APU work, frameskip or precision.

Current run has advanced to Sodium64 PROFILE build; ares/profile/frame-budget steps are still pending/running.

Interpretation:
**BUILD/WORKLOAD CONSTRUCTION ACCEPTED.** This is not yet execution/compatibility/performance evidence. Do not classify SRS as a corpus member until the pinned ares lab actually boots/progresses and yields valid Road-state counters.

Benchmark ROM/patch hashes will be recorded from the completed run artifact/log once available.

## Gate-B SRS first execution profile — MEASURED / needs repeatability 2026-09-18

Exact authority:
- audition head **`phase3/gate-b-srs-audition@6e5d444017ca899bcf2b69be6cbf8dd94eee9507`**;
- **Gate B SRS Audition `35394713398` SUCCESS**;
- same-head **Build and Validate `35394713401` SUCCESS**;
- non-ROM diagnostic artifact **`10567217952`**, digest `sha256:7bd5e9045de0d2fb3b55902829947b3448d3fcecfe265f006e8a0d8daa4e7d1a`;
- source-build provenance artifact `10567178769`, digest `sha256:ea44a19cf04e20501ce04fcc395bb7e85fd026deadce797551ad95a19d2dba2b`.

Pinned workload:
- upstream `undisbeliever/space-rescue-squad@e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865`;
- unmodified release ROM: 262144 bytes, SHA-256 **`d5bd7b17aa19a1b370efa38554b6ebfd77c4756e7184e9f2e848e8193bc9bed0`**;
- deterministic benchmark ROM: 262144 bytes, SHA-256 **`7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`**;
- benchmark patch SHA-256 **`4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`**.

Benchmark patch scope is exactly two upstream files:
- `_main.asm`: after normal audio init, initialize normal game state, select authored room `a1a_entrance`, enter `Mode.GAME`;
- `gameloop.inc`: inject held Right+Run into the normal controller state before normal gameplay processing.

Preserved workload work:
audio init/song path, game state, room loading, entities, collisions, camera, metatiles, animations, scripts, PPU/DMA/HDMA paths and `WaitFrame`. Nothing is disabled for speed.

Road-valid observed runtime settings:
- frameskip `0`;
- APU clock `21`;
- audio `4`;
- precision `8`.

First pinned ares lab measurement (R4300 recompiler ON, RSP interpreter forced due known ares LAB LIMITATION):
- measured wall time 9 s to reach sample-density threshold;
- **1,282 valid statistical samples**;
- last complete internal VI window: **53/60**;
- virtual budget: **88.3% — below virtual target**;
- partial window at stop: 48/60, 48 guest frames;
- queue `1`.

Sample shares:
- frame/VI wait **28.24%**;
- APU/SPC700 static **28.08%**;
- S-CPU interpreter **15.99%**;
- PPU/events/frame prep **8.19%**;
- DSP/audio **6.63%**;
- APU JIT generated **6.24%**;
- DMA/HDMA **4.29%**;
- RSP/VRAM semaphore wait **2.18%**;
- SNES memory/I/O 0.08%; input 0.08%.

Interpretation:
**MEASURED in emulator lab, not real-N64 performance authority.** SRS successfully survives the full autonomous build/wrap/profile path and produces a materially different profile from Gothicvania. The single measured complete window is below 60/60, so SRS is a strong candidate for exposing a Gate-B issue.

However, do NOT yet call `53/60` a real-N64 deficit or choose an optimization from it. The simultaneously high 28.24% VI-wait share makes the first run insufficient to distinguish sustained compute deficit from bursty workload, measurement-window/startup effects, presentation/cadence behavior, or another lab/runtime interaction.

Next controlled experiment:
repeat the exact same SRS benchmark/profile multiple times at the same SHA/settings, preferably without changing runtime or workload, and compare complete-window frame budget plus subsystem distribution. If the sub-60 result is stable, add a progression/checkpoint observation before selecting a runtime intervention. No hardware request yet.

## Gate-B SRS repeatability experiment — RUNNING 2026-09-18

Exact experiment head:
**`phase3/gate-b-srs-audition@466be943a7a725c2833e9dba4dd8d56c2f0a01ff`**.

Diff from first successful SRS profile head `6e5d4440...`:
- one commit;
- **workflow only** (`.github/workflows/gate-b-srs-audition.yml`);
- no Sodium64 runtime/emulator source change;
- no upstream SRS source or benchmark logic change.

Workload identity is now gated before profiling:
- deterministic benchmark ROM must remain SHA-256 `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`;
- benchmark patch must remain SHA-256 `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`.

Controlled experiment:
- build the same pinned SRS benchmark once;
- build the same Sodium64 PROFILE runtime once;
- build the same pinned ares lab once;
- launch **three fresh ares processes** (`r1/r2/r3`) sequentially;
- each repeat uses the same Road-valid settings and the same warmup/settle/sample-density contract as the first measured run;
- each repeat requires >=800 samples and validates frameskip 0, APU21, audio4, precision8;
- aggregate all three profile JSONs and frame-budget state files into comparison tables.

Exact runs:
- **Gate B SRS Audition `35395725393`** @ `466be943...` — running;
- Build and Validate `35395725495` @ same SHA — running.

Question:
Is the first `53/60` complete-window result a repeatable property of this exact SRS lab segment, or a one-run/start-window artifact?

Acceptance for repeatability:
- all three fresh processes complete with valid Road-state counters;
- complete-window frame budgets cluster tightly enough to describe a stable lab signal;
- subsystem distributions remain broadly consistent rather than changing qualitatively between repeats.

Falsifier / interpretation:
- large frame-budget dispersion or materially different profile shapes means the current measurement window/lab procedure is unstable for SRS; do not optimize runtime from it;
- stable sub-60 windows support treating SRS as a real Gate-B lab blocker candidate, but still do **not** establish real-N64 performance deficit.

If stable, next experiment is progression/checkpoint anchoring or later-segment measurement before selecting any runtime intervention. No hardware request yet.

## Gate-B SRS repeatability result — NOT STABLE / measurement window rejected 2026-09-18

Exact authority:
- experiment head **`phase3/gate-b-srs-audition@466be943a7a725c2833e9dba4dd8d56c2f0a01ff`**;
- **Gate B SRS Audition `35395725393` SUCCESS**;
- **Build and Validate `35395725495` SUCCESS** at the same SHA;
- diagnostic artifact **`10568281259`**, digest `sha256:b5b79dbf4ad6d6de5edaca568df5e2300767159f9d4ab719dee0e6d477e1cb00`;
- source-build provenance artifact `10567223794`, digest `sha256:9cab4c5d581e252d0c2a5ec3889163f8db7964699d32e055ebdbee7e1b3e7adc`.

Workload identity checks passed before profiling:
- benchmark ROM SHA-256 `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e` — exact match;
- benchmark patch SHA-256 `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7` — exact match;
- no Sodium64 production/runtime source changed.

Three fresh pinned-ares processes at frameskip0/APU21/audio4/precision8:
- **r1:** 2,203 samples; last complete VI window **60/60**; measurement stopped after 12 s host wall time; VI wait 29.10%, APU static 24.10%, S-CPU 14.84%, DSP 9.71%, PPU 8.40%, APU JIT 5.95%, DMA 4.86%, Memory/I-O 1.77%, VRAM/RSP wait 1.18%.
- **r2:** 1,221 samples; last complete VI window **59/60**; stopped after 3 s host wall time; VI wait 41.11%, APU static 29.07%, DSP 12.04%, S-CPU 7.78%, PPU 4.75%, APU JIT 3.52%, DMA 1.56%.
- **r3:** 881 samples; last complete VI window **53/60**; stopped after 12 s host wall time; VI wait 33.60%, APU static 19.64%, S-CPU 17.25%, PPU 9.31%, APU JIT 6.81%, DMA 5.79%, DSP 4.09%, VRAM/RSP wait 3.41%.

The earlier first successful run at `6e5d4440...` also ended on **53/60**, but that does not rescue stability: the controlled three-repeat matrix spans **53..60/60** with qualitatively different subsystem mixes.

Interpretation:
**REJECTED:** treating the current single `fps_display` value as a stable SRS Gate-B performance result.

The experiment's explicit falsifier fired. The >=800-sample stopping rule reaches threshold at materially different host times and therefore captures the 'last complete 60-VI window' at different guest/workload phases. The profile distributions changing with the window supports phase/measurement-position sensitivity rather than one stable compute ceiling.

What this DOES show:
- SRS repeatedly boots/runs through the lab path at Road-valid settings;
- its workload has materially varying frame cost over time;
- the current measurement method is insufficiently phase-aligned for using one terminal window to select an optimization.

What this does NOT show:
- no defensible single SRS FPS number;
- no real-N64 deficit;
- no evidence yet that CPU, APU, DSP, PPU or DMA should be the next optimization target.

Immediate next experiment:
replace the terminal-window question with an **internal-VI-window history** measurement. Capture several consecutive completed 60-VI budgets from Sodium64 itself, independent of when the host reaches the statistical-sample threshold. Keep runtime settings and SRS workload unchanged. Prefer tiny PROFILE-only instrumentation (one history write per completed 60-VI window) plus host decoding over any production behavior change.

Acceptance:
a single run yields an ordered series of consecutive complete internal VI windows with enough context to distinguish startup/transitions from sustained gameplay. Repeat only after that series is defined.

No hardware request and no runtime optimization until this measurement ambiguity is resolved.


## Gate-B SRS internal 60-VI history experiment — RUNNING 2026-09-18

Exact diagnostic head:
**`phase3/gate-b-srs-audition@bd9f7a75518a21563cb62cbce2c5dfd177cc777b`**,
one commit ahead of the repeatability head `466be943...`.

Reason:
The controlled repeatability matrix rejected the terminal-window method: identical SRS workload/settings produced last-window values 60/60, 59/60 and 53/60 because the >=800-sample stop condition landed at different guest phases. No runtime optimization is justified from those terminal values.

Controlled change:
- `src/profile.S`: add a PROFILE-only 64-byte ordered VI-window history and count **outside the canonical S64P snapshot**, preserving the existing statistical snapshot/hardware format;
- `src/main.S`: under `#ifdef SODIUM64_PROFILE` only, append the just-completed `fps_display` value once at each existing exact 60-VI `update_fps` boundary;
- audition workflow: reset history count together with `fps_native/fps_emulate/fps_display`, then run a fixed **20 host seconds** and read the ordered history plus the normal statistical profile.

No production/release behavior is intentionally changed. The new VI-history write executes only in PROFILE builds and only once per emulated 60-VI window.

Alignment:
The harness already resets `fps_native=0`, `fps_emulate=0` and `fps_display` while the target is stopped immediately before measurement. It now resets `profile_vi_history_count` at the same point. Therefore the first recorded entry is the first full 60-VI diagnostic window after reset; subsequent entries are consecutive internal windows independent of when the host stops.

History capacity:
64 completed 60-VI windows. The current fixed 20-second host observation is expected to produce at least 8; the workflow rejects fewer than 8.

Workload identity remains pinned and unchanged:
- SRS upstream `e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865`;
- benchmark ROM SHA-256 `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`;
- benchmark patch SHA-256 `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`;
- frameskip0 / APU21 / audio4 / precision8;
- normal SRS entity/collision/camera/metatile/animation/script/audio work preserved.

Exact runs:
- **Gate B SRS Audition `35398205311`** @ `bd9f7a75...` — running;
- **Build and Validate `35398205355`** @ same SHA — running.

Question:
What ordered frame-budget pattern does this exact SRS segment produce across consecutive internally aligned 60-VI windows?

Acceptance:
- Build/Validate stays green;
- >=8 consecutive history entries are captured;
- settings remain Road-valid;
- sequence is coherent enough to distinguish startup/transition cost from sustained gameplay.

Falsifier:
- history instrumentation/build fails;
- fewer than 8 internal windows are captured;
- repeated internal sequence later proves unstable even when indexed by the same 60-VI position.

Decision:
Do not choose CPU/APU/DSP/PPU/DMA work from SRS until this phase-aligned sequence is understood. No hardware request.


## Gate-B SRS internal 60-VI history — MEASURED 60/60 sustained in ares lab 2026-09-18

Exact authority:
- diagnostic head **`phase3/gate-b-srs-audition@bd9f7a75518a21563cb62cbce2c5dfd177cc777b`**;
- **Gate B SRS Audition `35398205311` SUCCESS**;
- **Build and Validate `35398205355` SUCCESS** at the same SHA, including normal build, PROFILE build and pinned Mupen smoke;
- non-ROM audition artifact **`10570116759`**, digest **`sha256:4221fb4e6aa103d1987226fc83098a0fb8b10e4c38ed8d38bfb621fa6ee6ddb5`**;
- source-build provenance artifact **`10569901158`**, digest `sha256:afc441006b18a6ccc615f9d8744f281d5c0fe3d6eca1bf60ba22d859a77cda56`.

Workload identity remained exact:
- benchmark ROM SHA-256 `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`;
- benchmark patch SHA-256 `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`.

Road-valid observed settings:
- frameskip 0;
- APU clock 21;
- audio 4;
- precision 8.

The PROFILE-only history captured **15 consecutive internally aligned 60-VI windows**:
**`61,60,60,60,60,60,60,60,60,60,60,60,60,60,60`**.

Interpretation:
- the first 61/60 is a boundary/queue-settling transient after diagnostic counter reset and is not evidence of >native target cadence;
- the following **14 consecutive windows are exactly 60/60**;
- therefore the earlier terminal values 53/60 and 59/60 are **REJECTED as sustained-throughput evidence**. They were artifacts of stopping at different guest phases and reading only the current/last visible counter.
- This exact SRS segment does **not** currently demonstrate a sustained Gate-B throughput blocker in the pinned ares lab.

The fixed 20-s host observation produced 11,230 total statistical samples (4,096 ring-valid). The terminal statistical distribution was dominated by frame/VI wait (**53.32%**) with APU static 25.17%, DSP/audio 7.98%, S-CPU 5.05%, PPU 3.56%, DMA 0.63%, VRAM/RSP wait 0.02%. Treat this as a long aggregate activity profile, not normalized subsystem cost and not real-N64 headroom.

Important non-conclusions:
- ares 60/60 does not prove N64-real 60/60;
- this does not prove broad SRS correctness or that the deterministic input actually traverses all intended gameplay states;
- no hardware request is justified yet;
- no CPU/APU/DSP/PPU/DMA optimization is justified from this result.

Next controlled checks before SRS can become a fixed corpus member:
1. repeat the **internal history metric** in fresh ares processes to verify that the ordered sustained 60/60 pattern itself is reproducible;
2. add a guest-progression/checkpoint observation so a stable 60/60 cannot be produced by a workload that has become stuck in one low-activity gameplay state.

Only after those checks should SRS be locked as the DKC-like/autonomous corpus slot.


## Gate-B SRS internally aligned repeatability — RUNNING 2026-09-18

Exact head:
**`phase3/gate-b-srs-audition@2694c455ba92bace9e644652eb5034f8a88d6961`**.

Diff from first internal-history result `bd9f7a75...`:
- workflow only;
- no Sodium64 source/runtime/instrumentation change;
- no SRS source/benchmark change.

Controlled experiment:
- same pinned benchmark ROM and patch;
- same PROFILE VI-history instrumentation;
- same Road-valid frameskip0/APU21/audio4/precision8;
- same pinned ares lab;
- three fresh ares processes;
- fixed 20 host-second observation each;
- each process resets `fps_native`, `fps_emulate`, `fps_display` and history count together before measurement;
- compare histories by internal 60-VI index, not terminal host stop phase.

Question:
Does the sustained internal sequence itself reproduce across fresh processes?

Interpretation rule:
- exact common-prefix agreement is strongest;
- the first window is tracked separately because queue/reset settling may produce a one-frame transient;
- the sustained common prefix after window 1 is the primary repeatability signal;
- do not fail the workflow merely because a measured window is sub-60; preserve the data and interpret it.

Exact runs:
- **Gate B SRS Audition `35398977369`** @ `2694c455...` — running;
- Build and Validate `35398977413` @ same SHA — queued/running.

If sustained internally indexed windows reproduce at 60/60, the earlier 53/59 terminal-window readings remain rejected and SRS moves to progression/checkpoint validation rather than performance optimization.
If the internally indexed sequences diverge materially, keep SRS measurement methodology OPEN and do not select a blocker or request hardware.


## Gate-B SRS internally aligned repeatability — VALIDATED 2026-09-18

Exact authority:
- audition head **`phase3/gate-b-srs-audition@2694c455ba92bace9e644652eb5034f8a88d6961`**;
- **Gate B SRS Audition `35398977369` SUCCESS**;
- **Build and Validate `35398977413` SUCCESS** at the same SHA;
- non-ROM audition artifact **`10569538598`**, digest **`sha256:3e34de347e20401f0a3db796a8aa51aef0824373a5ad71b5d02c01c2f171f73d`**;
- source-build provenance artifact **`10569272694`**, digest `sha256:3c2c69a391919fc884a9caf0167030c5ec7c9dfe3b4f3157321f343b51e0c982`.

Three fresh pinned-ares processes used the exact same benchmark ROM/patch, Road-valid settings and PROFILE VI-history instrumentation.

Internally aligned histories:
- **r1 (14 windows):** `48,60,60,60,60,60,60,60,60,60,60,60,60,60`;
- **r2 (18):** `59,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60`;
- **r3 (19):** `59,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60,60`.

Across the 14-window common span:
- exact full prefix equality = false because the first diagnostic window varies `48/59/59`;
- **sustained common prefix after window 1 = exact match**;
- the common sustained sequence is **13 consecutive `60/60` windows in all three runs**.

Interpretation:
- the first post-reset window is a queue/reset-boundary transient and is not suitable as a sustained-throughput metric;
- after that transient, the internally indexed sustained frame-budget signal is **repeatably 60/60** for this exact SRS segment in the pinned ares lab;
- the older host-stop terminal readings `53/60` and `59/60` remain **REJECTED** as blocker evidence;
- no SRS throughput-driven CPU/APU/DSP/PPU/DMA optimization is justified from the current lab result.

The statistical sample mixes differ because each fixed host-duration run reaches a different amount of guest progress and the 4096-entry EPC ring represents the terminal portion, not a normalized same-guest interval. Example VI-wait shares were 45.0%, 65.0%, 64.0%. Do not interpret those differences as subsystem cost movement.

What remains OPEN before fixing SRS as a principal Gate-B corpus member:
**guest progression/checkpoint proof.** A stable 60/60 sequence is insufficient if deterministic Right+Run has become stuck in a low-activity state.

Immediate next experiment:
- resolve exact SRS guest symbols from the pinned build output rather than guessing WRAM offsets;
- observe at least room/state plus player/camera position through Sodium64's mapped guest WRAM across the same lab run;
- establish that meaningful game state changes during the sustained 60/60 sequence;
- keep SRS/Sodium64 production behavior unchanged and request no hardware.

If progression is demonstrated, SRS can be locked as the autonomous DKC-like/heavy-platformer slot and corpus selection proceeds to the remaining SMW-like and ALttP-like slots.


## Gate-B SRS guest-progression proof — RUNNING 2026-09-18

Exact current audition head:
**`phase3/gate-b-srs-audition@03496a4587a7bc76836f26791144bcab0c77573b`**.

Parent validated measurement head:
`2694c455ba92bace9e644652eb5034f8a88d6961`.

Change scope since the validated aligned-repeatability result:
**workflow only**. No Sodium64 source/runtime/instrumentation change and no benchmark-runtime logic change.

Purpose:
The sustained internally aligned SRS signal is reproducibly 60/60 after the first reset/queue transient, but that is insufficient to lock SRS into the corpus unless the deterministic Right+Run benchmark is proven to make meaningful guest progress instead of becoming stuck in a low-activity state.

Progress authority chosen from the game itself:
- starting room `a1a_entrance` has authored entrance x=56;
- its right-door script loads `a1b_stairway`;
- observe actual SRS `GameState.roomId`, player x/y, camera x/y and player health.

Address resolution:
- do **not** hardcode guessed WRAM offsets;
- after the exact benchmark ROM/patch is built and hashed, append **compile-time-only bass print directives** that expose the exact guest constants for those variables and room IDs;
- rebuild and require the ROM SHA-256 to remain exactly `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`, proving the symbol probe emits no guest bytes;
- resolve Sodium64's host `wram` symbol and map SRS 7E/7F addresses into that array for GDB observation.

Each of the three fresh aligned-history repeats now also captures end state:
- room ID;
- player x/y;
- camera x/y;
- player health.

Progress acceptance:
- every repeat must either leave `a1a_entrance` or move the player at least 64 px beyond the authored initial x;
- player health must remain >0 at the measured end;
- entering `a1b_stairway` is tracked explicitly as the strongest natural checkpoint.

The internally aligned frame-history comparison remains unchanged and still records data without assuming 60/60.

A first workflow commit `6d20faa2...` was statically found to be missing Python `import os` in the final comparator before its long run could be trusted. It is **SUPERSEDED as harness state** by `03496a45...`; no runtime hypothesis changed.

Current exact runs:
- **Gate B SRS Audition `35400382816`** @ `03496a45...` — queued/running;
- **Build and Validate `35400382836`** @ same SHA — queued/running.
Older `6d20faa2...` runs are superseded by concurrency/correction and must not be interpreted.

If accepted:
SRS has autonomous build + executable benchmark + repeatable sustained lab frame budget + meaningful guest progression. It can then be locked as the DKC-like/heavy-platformer Gate-B corpus slot, with real-N64 validation deferred to the later aggregated hardware milestone.

If falsified:
do not optimize Sodium64. Improve or reject the deterministic SRS route first, because a stuck/dead benchmark is not a representative workload.


## Gate-B SRS guest-progression attempt 1 — SYMBOL-PROBE HARNESS FALSE NEGATIVE 2026-09-18

Exact authority:
- audition head **`phase3/gate-b-srs-audition@03496a4587a7bc76836f26791144bcab0c77573b`**;
- **Gate B SRS Audition `35400382816` FAILED**;
- same-head **Build and Validate `35400382836` SUCCESS**;
- diagnostic artifact **`10571140040`**, digest `sha256:f5b30c73a825a77f44977b72ffb782a0b8e27864a91fc8e1a610cf83ca4de5ca`;
- source-build provenance artifact **`10570560258`**, digest `sha256:2719aeb4e3325aa6bff26860f3ab91dd18bf8252078b41796f0471c0c63890a3`.

What passed before failure:
- exact pinned SRS/toolchain checkout;
- full CLI toolchain build;
- unmodified release ROM rebuild;
- deterministic benchmark patch/rebuild;
- benchmark ROM SHA-256 remained **`7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`**;
- benchmark patch SHA-256 remained **`4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`**.

Failure occurred in the new compile-time-only symbol-resolution step, before Sodium64 PROFILE/ares execution:
`error: constant has unknown value: Project.GameState.Words.playerHealth`
at the injected `print_hex(6, Project.GameState.Words.playerHealth)`.

Therefore:
- no new progression measurement exists from this run;
- no new frame-budget/profile result exists from this run;
- this failure is **HARNESS FALSE NEGATIVE / REJECTED as SRS or Sodium64 runtime evidence**.

Interpretation:
Bass can assemble/use the generated game-state symbol in normal code, but the injected print site cannot resolve that constant value at that phase of assembly. Using more injected compile-time prints is fragile and risks coupling the benchmark to assembler ordering.

Next action:
resolve guest addresses from existing build/map/symbol outputs where possible, or use symbols/aliases that are already concretely allocated at the observation point. Prefer host-side parsing over further guest-code instrumentation. Keep benchmark ROM/patch and Sodium64 runtime unchanged. No hardware request.


## Gate-B SRS guest-progression proof v2 — RUNNING 2026-09-18

Exact audition head:
**`phase3/gate-b-srs-audition@99870f702751e9de08aac84c65dfb56d80d04586`**.

Parent:
`03496a4587a7bc76836f26791144bcab0c77573b`.

Controlled repair after the symbol-probe false negative:
- workflow only;
- no Sodium64 source/runtime change;
- no SRS benchmark/runtime logic change;
- deterministic benchmark ROM/patch identity remains required unchanged.

The failed observation dependency on `Project.GameState.Words.playerHealth` was removed. Health is not required to answer the current Gate-B question: whether the deterministic workload makes meaningful guest progress instead of remaining stuck in one low-activity state.

Progress evidence now uses:
- `GameState.roomId`;
- player x/y;
- camera x/y;
- authored room IDs `a1a_entrance` / `a1b_stairway`;
- authored initial player x.

Acceptance is unchanged in substance:
every fresh repeat must either leave `a1a_entrance` or move the player at least 64 px beyond the authored initial x. Entering `a1b_stairway` remains the strongest natural checkpoint.

The internally aligned VI-history measurement remains present and unchanged. No CPU/APU/DSP/PPU/DMA optimization is authorized from this experiment.

If progression is demonstrated alongside the already-validated sustained 60/60 aligned histories, SRS can be locked as the autonomous DKC-like/heavy-platformer corpus slot. If progression is not demonstrated, improve or reject the deterministic route before touching Sodium64.

No hardware request.


## Gate-B SRS guest-progression attempt 2 — CACHE-ALIAS OBSERVABILITY LIMITATION 2026-09-18

Exact authority:
- audition head **`phase3/gate-b-srs-audition@99870f702751e9de08aac84c65dfb56d80d04586`**;
- **Gate B SRS Audition `35405118537` FAILED** in the repeat-history stage;
- same-head **Build and Validate `35405118547` SUCCESS**, including normal/PROFILE builds and pinned Mupen smoke;
- audition artifact **`10571618879`**, digest `sha256:14a31c5c8d81e67cd719e66747025f493cfd882ef20b610355c9402ef98d3598`;
- source-build provenance artifact **`10571912960`**, digest `sha256:446ea03b9e64fcceff7035b8be6b0f672f5f403e7ca877795faa5f337dd2cacb`.

What this run DID establish:
- source/toolchain/release build SUCCESS;
- deterministic benchmark rebuild SUCCESS with unchanged benchmark ROM/patch hashes;
- guest symbol resolution SUCCESS:
  - `GameState.roomId = 0x7e2200`;
  - `Entity.Player.xPos.px = 0x7e0123`;
  - `Entity.Player.yPos.px = 0x7e0127`;
  - `Camera.xPos = 0x7e87b3`;
  - `Camera.yPos = 0x7e87b5`;
  - authored room IDs `a1a=0x01`, `a1b=0x02`;
  - map origin `LEFT=TOP=0x1000`;
- Sodium64 PROFILE and pinned ares lab setup SUCCESS;
- three benchmark executions began and internally aligned histories were captured;
- r3 contained only 7 complete internal windows and tripped the per-repeat diagnostic minimum of 8 before the final comparator.

The observed guest-coordinate values from this run are **REJECTED as authoritative progression evidence**.

Cause discovered by source audit:
- Sodium64 maps SNES WRAM `7E/7F` through R4300 TLB pages to the physical `wram` backing buffer;
- guest execution accesses those pages using the SNES-like R4300 virtual addresses (for example `0x007e0123`);
- the progression harness instead translated them to their KSEG0 backing alias (for example `0x80071123`) and asked ares GDB to read that alias;
- pinned ares `CPU::readDebug` correctly consults D-cache, but D-cache is **virtually indexed**: `line(vaddr) = lines[vaddr >> 4 & 0x1ff]`;
- therefore `0x007e0123` uses cache index `0x12`, while its KSEG0 alias `0x80071123` uses index `0x112`;
- a dirty guest WRAM line can consequently be present under the guest virtual alias while a GDB read through KSEG0 misses it and falls back to stale backing RDRAM.

This is a **LAB/OBSERVABILITY LIMITATION**, not evidence of an SRS gameplay or Sodium64 emulation failure.

Endian audit:
- Sodium64 `MEM_WRITE16` stores the SNES low byte at guest address and high byte at guest+1;
- `MEM_READ16` reconstructs that little-endian guest word;
- ares GDB 2-byte reads are returned as R4300 halfword values;
- the host-side little-endian reconstruction remains appropriate once the correct guest virtual alias is read.

Expected authored state provides an independent sanity bound:
- `a1a_entrance` entrance is x=56,y=164;
- engine adds map origin `0x1000`;
- initial player position should therefore be about x=4152,y=4260, with camera clamped near map origin.

Next controlled experiment:
- keep the exact benchmark ROM/patch and Sodium64 runtime unchanged;
- observe guest state by GDB **directly at the resolved virtual addresses `0x007e....`**, not via KSEG0 backing aliases;
- validate resulting positions against authored map bounds;
- decouple progression acceptance from an arbitrary >=8 history-count threshold (the aligned 60/60 repeatability was already established separately);
- require actual room transition or >=64 px player movement before locking SRS into the corpus.

No hardware request and no optimization is authorized from this finding.


## Gate-B SRS guest-progression proof v3 — RUNNING 2026-09-18

Exact audition head:
**`phase3/gate-b-srs-audition@09ffc26305781ba17624b3defa5932ac5db7e618`**.

This is a harness-only correction over the already-validated benchmark/runtime:
- guest-state reads now use the resolved SNES/R4300 virtual addresses directly (`0x007e....`) so pinned ares `readDebug` consults the same virtually-indexed D-cache line used by Sodium64 guest execution;
- the previous KSEG0 backing-buffer aliases are no longer used for SRS guest state;
- per-run internal-history minimum is reduced from 8 to 5 complete 60-VI windows because sustained aligned throughput repeatability was already validated separately; this run is a progression proof, not a throughput requalification;
- final comparator now rejects implausible guest state before considering progression:
  - room must be `a1a` or `a1b`;
  - player/camera x/y must lie in the engine's map-space range `0x1000 <= value < 0x8000`;
- progression still requires every repeat either to leave `a1a` or move player x at least 64 px beyond the authored initial x.

Benchmark identity remains required:
- ROM SHA-256 `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`;
- patch SHA-256 `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`.

No Sodium64 runtime/production code is changed by this progression repair. No hardware request.

Acceptance:
- guest observations satisfy authored/map plausibility;
- all repeats demonstrate progression;
- Road-valid settings remain frameskip0/APU21/audio4/precision8.

Falsifier:
- virtual-address reads still produce impossible state;
- deterministic route does not progress in all repeats;
- benchmark identity/settings change.

If accepted, SRS can be locked as the autonomous DKC-like/heavy-platformer corpus slot; its ares 60/60 evidence remains lab filtering only, not real-N64 performance authority.


## Gate-B SRS guest-progression attempt 3 — ARES UNALIGNED-HALF DEBUG LIMITATION 2026-09-18

Exact authority:
- audition head **`phase3/gate-b-srs-audition@09ffc26305781ba17624b3defa5932ac5db7e618`**;
- **Gate B SRS Audition `35406148298` FAILED** only in the final progression comparator;
- same-head **Build and Validate `35406148307` SUCCESS**;
- audition artifact **`10573085612`**, digest **`sha256:bb370553f1af0a70fa662b816afbadda509b8e428e104e45e08d4fba25759e2c`**;
- source-build provenance artifact **`10571984681`**, digest `sha256:91690474099710362dcb0e7f44b94e46737b8a76d40598117ed89a5d774b2ff8`.

What passed:
- exact pinned source/toolchain/release build;
- deterministic benchmark patch/rebuild with unchanged benchmark identity;
- symbol resolution;
- Sodium64 PROFILE build;
- pinned ares build;
- three benchmark executions;
- internally aligned history capture;
- Road-valid settings.

Observed room ID remained plausible (`a1a = 1`), but 16-bit coordinate observations were implausible, e.g. end-state tuples such as:
- player x 39518/39666/39533;
- player y 41728;
- camera x 6660;
- camera y 16.

These values are **REJECTED as guest-state evidence**.

### Root cause — LAB/OBSERVABILITY LIMITATION

Pinned ares GDB handles a two-byte memory request by calling `cpu.readDebug<Half>(address)`.

The resolved SRS 16-bit fields are at odd guest virtual addresses:
- player x `0x007e0123`;
- player y `0x007e0127`;
- camera x `0x007e87b3`;
- camera y `0x007e87b5`.

In pinned ares, `DataCache::Line::read<Half>` selects the halfword using `paddr >> 1`; the low address bit is therefore not represented as a byte offset for an unaligned two-byte debugger request. A GDB `mADDR,2` from these odd addresses does **not** reliably mean “read byte ADDR and byte ADDR+1”.

This explains why the 1-byte `room_id` observation is coherent while the 16-bit coordinate observations fail plausibility.

Classification:
**ARES DEBUGGER UNALIGNED-HALF LAB LIMITATION / REJECTED as SRS or Sodium64 runtime evidence.**

Immediate controlled repair:
- keep exact benchmark ROM/patch, Sodium64 runtime and guest virtual aliases unchanged;
- observe every SRS 16-bit field as **two independent 1-byte GDB reads** at `addr` and `addr+1`;
- reconstruct the SNES value host-side as `low | (high << 8)`, matching Sodium64 `MEM_WRITE16` / `MEM_READ16`;
- retain room/state plausibility and >=64-px/room-transition progression criteria;
- do not requalify throughput or request hardware.

If byte-wise guest observations become plausible and demonstrate progression in all repeats, SRS can be locked as the autonomous DKC-like/heavy-platformer Gate-B slot.


## Gate-B SRS guest-progression proof v4 — RUNNING 2026-09-18

Exact audition head:
**`phase3/gate-b-srs-audition@d00ce599563ee5a7be94356150bae73a018a4e52`**.

This is a harness-only observability repair over v3:
- no Sodium64 runtime/production change;
- no SRS benchmark/runtime logic change;
- benchmark identity and Road-valid settings remain required unchanged.

Root-cause-driven change:
- pinned ares GDB handles a 2-byte request with `readDebug<Half>`;
- all four observed SRS 16-bit fields are at odd guest virtual addresses;
- the halfword debug path indexes the D-cache by `paddr >> 1`, so an unaligned `mADDR,2` request does not reliably mean two consecutive guest bytes;
- each 16-bit field is now observed as **two separate one-byte reads** at `addr` and `addr+1`;
- host reconstruction uses the Sodium64/SNES layout: `value = low | (high << 8)`.

The coherent 1-byte room-id observation is unchanged.

Progress acceptance remains:
- room must be authored `a1a` or `a1b`;
- player/camera coordinates must lie in plausible map-space bounds;
- each repeat must either leave `a1a` or move player x >=64 px beyond the authored initial x;
- frameskip0 / APU21 / audio4 / precision8 remain mandatory.

Exact runs:
- **Gate B SRS Audition `35407369415`** @ `d00ce599...` — queued/running;
- **Build and Validate `35407369417`** @ same SHA — queued/running.

If accepted:
SRS has autonomous source build, deterministic benchmark, repeatable sustained aligned 60/60 lab throughput and meaningful guest progression. Lock it as the DKC-like/heavy-platformer Gate-B corpus slot and move corpus selection to the remaining SMW-like and ALttP-like slots.

If falsified:
do not optimize Sodium64. Classify the remaining observation/route problem first. No hardware request.


## Gate-B SRS guest-progression proof v4 — VALIDATED / CORPUS SLOT LOCKED 2026-09-18

Exact authority:
- audition branch **`phase3/gate-b-srs-audition@d00ce599563ee5a7be94356150bae73a018a4e52`**;
- **Gate B SRS Audition `35407369415` SUCCESS**;
- same-head **Build and Validate `35407369417` SUCCESS**, including normal/PROFILE builds and pinned Mupen smoke;
- main audition artifact **`10573367249`**, digest **`sha256:9b98631ce14cc0c90e55b91d6579b739f8bb79183ec2c817efad7c66db38f833`**;
- source-build provenance artifact **`10572508021`**, digest **`sha256:99a3d1742e9ed16bb17892c0c80059bd97c70c79120043f58c3825f0c6d7a66e`**.

Benchmark identity remained unchanged:
- upstream SRS `e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865`;
- unmodified release ROM SHA-256 `d5bd7b17aa19a1b370efa38554b6ebfd77c4756e7184e9f2e848e8193bc9bed0`;
- deterministic benchmark ROM SHA-256 **`7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`**;
- benchmark patch SHA-256 **`4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`**;
- patch still only enters the first authored gameplay level after normal initialization and supplies deterministic Right+Run input; audio, game state, room loading, entities, collisions, camera, metatile processing, animations, scripts and normal frame waiting remain active.

Road-valid settings observed in all repeats:
- frameskip `0`;
- APU clock `21`;
- audio `4`;
- precision `8`.

### Internally aligned 60-VI histories

Three fresh ares-lab repeats:

- r1: **`53,60,60,60,60,60,60,60 /60`** — 8 windows, mean 59.125;
- r2: **13 x `60/60`** — mean 60.0;
- r3: **`59,60,60,60,60,60,60,60,60,60,60,60 /60`** — 12 windows, mean 59.9167.

The first diagnostic window is not stable across launches. After discarding only that first transient window, the common seven-window prefix is **exactly `60/60 x7` in all three repeats**.

This is sustained emulator-lab throughput evidence, not real-N64 performance authority.

### Guest progression proof

The ares unaligned-half debugger limitation was avoided by reading each byte separately at the exact guest virtual WRAM addresses and reconstructing each SNES uint16 as `low | high << 8`.

All three repeats ended with the same plausible guest state:
- room ID **1 = authored `a1a_entrance`**;
- player x **4250**;
- player y **4259**;
- camera x **4122**;
- camera y **4096**.

Authored initial player x is **4152**. The deterministic route therefore advanced the player **+98 px** through normal gameplay in every repeat, exceeding the predeclared >=64-px progression criterion.

Comparator result:
- plausible guest state: **true, true, true**;
- progressed from a1a: **true, true, true**;
- entered a1b by measurement end: false, false, false.

The workload is therefore **not** a static/stuck low-activity state.

### Profile context — do not normalize as subsystem cost

Each repeat filled 4,096 statistical samples. Shares varied materially by repeat/measurement phase (for example VI wait 41.0%, 60.8%, 66.0%; APU static 26.9%, 25.2%, 23.6%). These shares are useful for locating activity but are **not** a stable normalized cross-run subsystem-cost claim for SRS.

### Decision

**Space Rescue Squad — LOCKED / GATE-B CORPUS SLOT / DKC-LIKE HEAVY PLATFORMER.**

Why it earns the slot:
- autonomous reproducible pinned source/toolchain build;
- materially nontrivial game/engine rather than a single-purpose microtest;
- independent engine/toolchain lineage from Gothicvania;
- entities, collision, camera, room/metatile processing, HDMA/DMA budgeting, animated tiles and active SPC700/audio;
- deterministic benchmark with meaningful guest progression;
- repeatable sustained Road-valid 60/60 laboratory cadence after the first launch transient.

What this does NOT establish:
- real-N64 60 FPS/performance;
- complete SRS playthrough/compatibility;
- broad Gate-B compatibility;
- audiovisual fidelity or long-run sync;
- that SRS exposes the next blocker.

Preserve **ARES DEBUGGER UNALIGNED-HALF LAB LIMITATION**: two-byte GDB reads from odd guest addresses are not trustworthy in the pinned lab; use byte-wise reads for such state observations.

No new hardware session is justified now.

### RESUME HERE — Gate-B corpus selection

Current corpus:
1. Gothicvania — existing representative regression workload;
2. **Space Rescue Squad — LOCKED DKC-like/heavy-platformer slot**;
3. SMW-like slot — OPEN;
4. ALttP-like slot — OPEN.

Next technical batch:
select and audition the remaining SMW-like and ALttP-like workloads using the same gate order: legal/autonomous source+asset provenance -> reproducible build -> deterministic meaningful gameplay route -> emulator-lab progression/correctness -> sustained aligned frame-budget characterization. Do not optimize Sodium64 until the four-workload corpus identifies a real blocker.

Do not merge the one-off SRS audition branch to master yet. It contains PROFILE-only VI-history instrumentation and candidate-specific workflow. Prefer consolidating corpus infrastructure after the remaining slots are selected rather than accumulating per-candidate diagnostic machinery in master.


## Gate-B Nova the Squirrel 2 audition — source-build proof running 2026-09-18

Repo/continuity reconciliation before this batch found no work newer than the previous SRS lock checkpoint:
- integrated **`master@ac1ce74740d974b70206fcb6ba842e492b5d7272`**;
- **`continuity@a8c3cfafdf015bb3e3f172705f2402554edbd664`** was newer than the last SRS CI completion and already recorded it;
- no open PRs;
- **Space Rescue Squad remains LOCKED** as the DKC-like/heavy-platformer Gate-B corpus slot;
- M1 remains MERGED-CONSUMED / ACHIEVED with real-N64 Gothicvania 60/60 x5.

The next required uncertainty is therefore corpus selection, not another Sodium64 optimization.

### SMW-like candidate selected for first audition

**Nova the Squirrel 2** is the first principal SMW-like audition candidate.

Pinned upstream:
- `NovaSquirrel/NovaTheSquirrel2@94385f1812f3b322f939f79a29502a1a3ee6d87f`.

Source evidence at that exact pin shows a materially broader engine/workload than the previously downgraded Castle Platformer fallback:
- large scrolling levels, including 256x32 / 32x256 layouts;
- independently moving second foreground layer;
- player/enemy/object logic, enemy health and attacks;
- hub world, overworld, dialogue/inventory/story machinery;
- many authored levels and generated map/tile resources;
- background effects, sprite/player graphics and per-frame PPU uploads;
- SPC700/audio driver and generated music/sample data;
- LZ4-compressed assets;
- separate Mode-7 level/actor path.

It also gives useful lineage diversity: different author/engine/toolchain from SRS and Gothicvania, with a ca65/ld65 + Python/LZ4 build.

Eligibility boundary:
- game/tool code is GPLv3 at the pinned source;
- upstream README explicitly says game assets are not licensed for reuse outside this game.
- This audition therefore uses the assets only as upstream inputs to build/profile this exact game and **does not upload or redistribute the ROM or assets**.

### Controlled source-build proof

Created from exact integrated master:
**`phase3/gate-b-nova2-audition@043950304a28aec583c5b1ba70ae12c99741e206`**.

This candidate changes only:
`.github/workflows/gate-b-nova2-audition.yml`.

No Sodium64 runtime/emulator source is changed.

Question:
Can exact pinned Nova 2 source/assets be rebuilt autonomously on Ubuntu with public dependencies only, without mutating tracked upstream content or launching an interactive emulator?

Build contract:
- install public `cc65`, `lz4`, Python/Pillow and normal host build tools;
- clone exact upstream pin;
- invoke explicit `nova-the-squirrel-2.sfc` target because upstream's default target launches an emulator;
- require a non-empty ROM;
- require no tracked-source/asset mutation after build;
- record exact ROM hash/size/tool versions;
- upload provenance/build log only, **never ROM bytes or upstream assets**.

Acceptance:
- clean autonomous source build from the exact pin;
- reproducible non-empty ROM identity recorded;
- upstream tracked tree remains unchanged;
- no private/local/proprietary dependency is required.

Falsifier / downgrade:
- missing/non-public build dependency;
- build cannot be reproduced from pinned repo state;
- build requires source/asset repair large enough to become a second project;
- asset/license boundary cannot be respected without redistributing restricted content.

If accepted, next controlled step is **not** immediate corpus lock: first design a temporary deterministic meaningful gameplay route that preserves normal game/PPU/audio/collision/entity work, then prove guest progression and sustained internally aligned frame-budget behavior in the pinned ares lab. Real N64 remains deferred until the four-workload corpus is assembled and one aggregated hardware session is justified.


## Nova2 source-build attempt 1 — BUILD-ENVIRONMENT FALSE NEGATIVE 2026-09-18

Exact failed authority:
- **Gate B Nova2 Audition `35410094420` FAILED** @ `043950304a28aec583c5b1ba70ae12c99741e206`;
- failure was in the upstream game-build step after checkout and dependency installation succeeded.

Observed build progress:
- exact upstream `94385f1812f3b322f939f79a29502a1a3ee6d87f` cloned successfully;
- ca65 compilation began normally;
- multiple Python graphics conversions completed;
- failure occurred in upstream `tools/encodepalettes.py` at `pal.pop(0)` while generating palette data.

Cause:
the runner installed Ubuntu Pillow 10.2.0. The 2023 upstream palette generator assumes the older padded `Image.getpalette()` behavior and indexes a fixed set of palette entries. This is a host-library compatibility mismatch, not evidence of a missing Nova2 asset, bad source tree or Sodium64 incompatibility.

Classification:
**BUILD-ENVIRONMENT / HARNESS FALSE NEGATIVE.**
Reject this run as candidate-quality evidence.

Controlled repair:
**`phase3/gate-b-nova2-audition@d1a3aacb0a724fb3ea8097f93b53c72aa56cc76b`** now reproduces an upstream-era Python stack with Python 3.11 + Pillow 9.4.0. No Nova2 source/assets and no Sodium64 runtime code are modified.

Question remains unchanged:
can the exact pinned game build autonomously from public source in a historically compatible environment?

Acceptance/falsifiers remain unchanged. If the next build proceeds past palette generation but exposes another environment dependency, classify it before changing candidate status.


## Nova2 source-build attempt 2 — Pillow pin still too new / superseded 2026-09-18

Exact failed authority:
- **Gate B Nova2 Audition `35410166557` FAILED** @ `d1a3aacb0a724fb3ea8097f93b53c72aa56cc76b`;
- Python 3.11 + Pillow 9.4.0 installed successfully;
- upstream build failed at the same `tools/encodepalettes.py -> pal.pop(0)` point.

This does **not** falsify the build-environment hypothesis. Pillow 9.2 changed `getpalette()` to account for actual palette size; therefore 9.4 still has the behavior incompatible with this older fixed-index generator.

Classification:
**SUPERSEDED HARNESS REPAIR / no candidate evidence.**

Controlled repair now running:
**`phase3/gate-b-nova2-audition@60ec5caca750af20e7a3c35baacaa03db3744186`**
uses Python 3.10 + Pillow 9.1.1, i.e. the pre-9.2 padded-palette behavior. No upstream or Sodium64 runtime files are modified.

Diagnostic expectation:
- if `encodepalettes.py` proceeds, the host-library diagnosis is confirmed;
- if it fails identically, stop version guessing and inspect exact PNG palette encoding / build-history assumptions before another change.


## Nova2 source-build attempt 3 — pre-9.2 Pillow explanation insufficient 2026-09-18

Exact failed authority:
- **Gate B Nova2 Audition `35410211745` FAILED** @ `60ec5caca750af20e7a3c35baacaa03db3744186`;
- Python 3.10 + Pillow 9.1.1 installed successfully;
- build again failed identically in `tools/encodepalettes.py` at fixed palette popping.

Discarded explanation:
**“Pillow >=9.2 alone caused the failure” is REJECTED as a sufficient cause.**
The host library may still be part of the historical build assumption, but version pinning alone does not reconstruct it.

No candidate-quality conclusion is allowed from these three failures: all occurred before ROM assembly and none involve Sodium64 runtime behavior.

Next controlled diagnostic:
**`phase3/gate-b-nova2-audition@af5602d91fff3658e083959b019138772c024f68`**
adds a harness-only readout of every source `palettes/*.png`:
- raw PNG PLTE entry count;
- Pillow-visible palette entry count;
- identification of regular palette files with fewer than the 16 entries assumed by `encodepalettes.py`.

The upstream tree remains unmodified. The build still runs afterward only to preserve the exact observed failure context.

Decision map:
- if one or more committed PNGs encode <16 PLTE entries, investigate the upstream author's palette-padding/build assumption and reproduce it narrowly rather than version-guessing;
- if all encode >=16, the failure is elsewhere in palette interpretation and must be isolated before another build repair.


## Nova2 palette assumption isolated — 2026-09-18

Exact diagnostic authority:
- **Gate B Nova2 Audition `35410283981` FAILED as expected after diagnostic** @ `af5602d91fff3658e083959b019138772c024f68`;
- the new palette-inspection step itself succeeded before the unchanged build failure.

Measured source encoding:
- `31` regular `palettes/*.png` files inspected;
- **21/31 encode fewer than 16 raw PNG PLTE entries**;
- examples: `BGForest=5`, `BGGlass=5`, `InventoryBG2=4`, `OWStone=7`, `SPNova=13`;
- Pillow 9.1.1 exposed exactly those raw entry counts, so `encodepalettes.py` exhausts the list after skipping entry zero and unconditionally reading 15 more colors.

This proves the failure is not missing source/assets. The committed source assets themselves intentionally contain compact palettes while the generator depends on a historical palette-padding behavior.

Build-history evidence:
- `tools/encodepalettes.py` originated **2019-05-03**;
- meaningful palette-system update **2020-02-22**;
- last source change was only the Python-3 shebang conversion on **2020-05-08**;
- affected palette assets also date mainly from 2019-2021.

Supported interpretation:
the correct compatibility target is therefore the **2019/2020 Pillow era**, not merely “pre-9.2”.

Next controlled repair:
**`phase3/gate-b-nova2-audition@3e691f0fea59ab289a054768f5f0879e8336a504`**
uses Python 3.8 + Pillow 7.1.2 (contemporary with the generator's last substantive era) and retains the raw-PLTE/Pillow-visible diagnostic.

Expected discriminator:
- if raw PLTE remains compact but Pillow-visible entries expand enough for the generator and build proceeds, historical palette semantics are confirmed;
- if Pillow 7.1.2 still exposes compact entries, do not keep version-hunting: reproduce the required padding explicitly in a harness compatibility layer and prove its generated palette semantics before accepting the workload.


## Nova2 source-build attempt 5 — historical palette semantics confirmed; next blocker isolated 2026-09-18

Exact authority:
- **Gate B Nova2 Audition `35410355265` FAILED** @ `3e691f0fea59ab289a054768f5f0879e8336a504`.

Important confirmed result:
Python 3.8 + Pillow 7.1.2 reproduced the historical palette behavior:
- raw PNG PLTE counts remained compact (same 4-16 entry source assets);
- Pillow-visible palette count became **256 for every inspected palette**;
- `tools/encodepalettes.py` therefore completed successfully.

This **confirms** the supported interpretation that the upstream generator relies on older Pillow palette padding. The earlier modern-Pillow failures are now understood and should not be revisited.

The build then advanced through extensive graphics/background/palette/level/Mode-7 generation and failed later while building the upstream BRR helper:
`gcc audio/brr/gssbrr.c -o audio/brr/gssbrr`
with undefined `sin`, `cos`, and `floor`.

Cause:
the upstream Linux Makefile rule omits `-lm` even though the exact helper source uses libm symbols.

Classification:
**SMALL UPSTREAM BUILD-SCRIPT COMPATIBILITY DEFECT**, not a missing/private dependency and not candidate runtime evidence.

Controlled repair:
**`phase3/gate-b-nova2-audition@156b928191c130f13a19868e634c519647d91d59`** prebuilds the exact upstream `audio/brr/gssbrr.c` with public host GCC + `-lm`, then invokes the unchanged ROM target. No upstream source/assets and no Sodium64 runtime files are edited.

Acceptance remains:
a clean ROM build from exact pinned upstream state, with all tracked upstream inputs unchanged and only provenance/logs uploaded.


## Nova2 autonomous source-build gate — PASSED 2026-09-18

Exact authority:
- branch **`phase3/gate-b-nova2-audition@156b928191c130f13a19868e634c519647d91d59`**;
- **Gate B Nova2 Audition `35410418476` SUCCESS**;
- provenance artifact **`10573526773`**, digest **`sha256:ab46bf2dcc239b0cfc0b3eebda8c2497eaf61ff5f177eac5b92da1046a8da5ff`**.

Pinned upstream:
- `NovaSquirrel/NovaTheSquirrel2@94385f1812f3b322f939f79a29502a1a3ee6d87f`.

Source-build identity:
- ROM size: **1048576 bytes**;
- ROM SHA-256: **`ecc61b2367a9261fe48131a61e5cf787b6409083827556109099a46a637d9b2f`**;
- Python 3.8.18;
- Pillow 7.1.2;
- ca65/ld65 from Ubuntu cc65 2.19 package;
- LZ4 1.9.4;
- exact upstream BRR helper source precompiled with host GCC + `-lm` because upstream Linux rule omits the required math library;
- no tracked upstream file mutated;
- artifact contains provenance/hash/build log only; no ROM or restricted upstream asset bytes are uploaded.

Interpretation:
**Nova the Squirrel 2 PASSES the legal/autonomous-source + reproducible-build gates for continued SMW-like audition.**
It is **not yet locked** into the corpus. Runtime correctness, deterministic meaningful gameplay progression and sustained aligned frame-budget characterization remain required.

Preserved build knowledge:
- modern Pillow is not valid for this pinned generator;
- Pillow 7.1.2 reproduces the historical 256-entry palette padding required by compact PNG PLTE assets;
- do not rediscover/re-litigate the earlier palette failures.

### RESUME HERE — Nova2 deterministic gameplay route

Next technical batch:
1. inspect pinned game startup/level-selection/player-input paths;
2. choose the smallest temporary benchmark patch or deterministic input route that enters a representative scrolling gameplay level;
3. preserve normal player physics, collision, actor updates, scrolling, PPU uploads and active audio;
4. record unmodified ROM identity separately from benchmark ROM identity;
5. boot/progress in pinned ares lab before attaching Sodium64 performance meaning.

Do **not** optimize Sodium64 from Nova2 yet.


## Independent autonomy, corpus and oracle audit — 2026-09-19

Scope: requested read-only project/direction audit. The only authorized repository mutation is this file on `continuity`. No Sodium64 runtime, workflows, other canonical docs, PRs, branch candidates, merges or experiment launches are changed by this audit. Dates here are UTC (the latest CI completed on September 19 UTC / September 18 Chile). Perfect target and N64-alone priority remain unchanged.

### 1. Evidence reconciliation and overall verdict

**SUPPORTED INTERPRETATION: direction is sound, but corpus admission currently overstates what the SRS route proves. Correctness/progression oracles are now more valuable than another optimization.**

Verified repository state:
- Integrated master: **`ac1ce74740d974b70206fcb6ba842e492b5d7272`**; PR **#12 MERGED-CONSUMED**. Exact-SHA master runs **35387454297** (Build and Validate), **35387454371** (APU Cycle And Span Proof), **35387454367** (Ares Profile Validation) all SUCCESS. Later cancelled runs with this SHA on newly created audition branches do not invalidate these completed master gates.
- No open PRs at audit time.
- Continuity before this audit: branch **`ae0c818c638d5dbd75bf9801bf758cd7c197aea2`**, file blob **`bcf47ceae9cb4182a658e48058406f53281618a0`**. Its final Nova2 checkpoint agrees with current branch/CI. Its opening M0/M1 snapshot is historical and dangerously stale if read alone; the new top RESUME HERE resolves that without deleting the history.
- SRS audition: **`phase3/gate-b-srs-audition@d00ce599563ee5a7be94356150bae73a018a4e52`**, audition **35407369415** SUCCESS and Build/Validate **35407369417** SUCCESS.
- Nova2 audition: **`phase3/gate-b-nova2-audition@156b928191c130f13a19868e634c519647d91d59`**, source-build **35410418476** SUCCESS and Build/Validate **35410418324** SUCCESS. No Nova2 gameplay result exists at this head.
- No in-progress experiment was found among the current candidate runs. Resume from completed evidence, not the earlier Pillow failures.
- All five canonical docs were read. Historical M1 hardware **60/60 x5**, full-rate APU, frameskip0 and 11.51% VI wait remain accepted previously audited hardware evidence; the original hardware SRAM was **not re-decoded in this audit**.

Independent new inspection:
- Read exact-SHA SRS workflow and its three-file diff from master (`.github/workflows/gate-b-srs-audition.yml`, PROFILE-only `src/main.S`, `src/profile.S`); read Nova2 workflow and exact job logs.
- Downloaded SRS artifact **10573367249**, recomputed ZIP SHA-256 **`9b98631ce14cc0c90e55b91d6579b739f8bb79183ec2c817efad7c66db38f833`**, inspected its provenance, benchmark patch, state/history JSON and reports. This matches Actions metadata. The ZIP contains no ROM, screenshot or PCM output. Raw profiler samples were not independently reclassified against an ELF in this audit.
- SRS source provenance artifact **10572508021** and Nova2 artifact **10573526773** were independently checked in metadata; Nova2 exact job **105808791825** confirms the recorded 1 MiB ROM hash, tool versions and successful unchanged-tree build. SRS exact job **105799802927** agrees with downloaded history/state evidence.
- No emulator/game was newly executed by this audit. New conclusions below are artifact/source interpretation, not new performance measurements.

### 2. Autonomy is compatible with the Road; commercial ROM upload is unnecessary

**DIRECTION / reaffirmed user constraint:** routine development must not require Iron's powered-on PC, locally supplied commercial ROMs or continuous manual feedback. Keep all commercial ROM bytes out of GitHub, Actions uploads and project artifacts. No private-ROM hosting workaround is proposed.

Separate three needs:
1. **Autonomous development corpus:** original homebrew games with reproducible source/assets and bounded deterministic routes, plus targeted original tests. Homebrew is real software; it need not be commercially released or visually polished to expose actual emulator bugs.
2. **Commercial representativeness:** eventual checks of the actual commercial workloads before making claims about their compatibility. Open games can expose missing behavior, but passing them does not prove SMW, DKC or ALttP pass. Keep this uncertainty explicit; commercial testing can remain an occasional supplemental/local milestone.
3. **Real-N64 authority:** required for final N64 performance/hardware claims, not every change. Prepare one build/procedure covering multiple questions when evidence warrants it. Absence of a hardware session leaves hardware claims pending; it must not halt all autonomous correctness work.

**REJECTED premise:** a game must have its original source available to test emulator correctness. The same ROM with the same power-on state and frame-indexed inputs can be executed in a reference SNES emulator and in Sodium64; compare selected observable state, graphics and audio. Source helps locate state and explain failures, but is not the required oracle.

**REJECTED inference:** no commercial ROM in CI means no meaningful progress is possible. Current M1 hardware evidence and autonomous game builds already refute that.

### 3. GATE DRIVER / MEASUREMENT PROOF: SRS route coverage is not yet established

**MEASURED, independently reproduced from the artifact:**
- unmodified SRS ROM **`d5bd7b17aa19a1b370efa38554b6ebfd77c4756e7184e9f2e848e8193bc9bed0`**;
- benchmark ROM **`7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`**;
- patch **`4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`**;
- window vectors: r1 **53,60,60,60,60,60,60,60**; r2 **13 x60**; r3 **59 followed by 11 x60**;
- final state in all three runs: room1, player **(4250,4259)**, camera **(4122,4096)**; initial authored x4152, thus +98px;
- no run ended in a1b; each has only one endpoint gameplay-state observation;
- Right+Run are held continuously. No jump/attack/door sequence is scripted.

The pinned authored `game/resources/rooms/a1a-entrance.utroom` starts at local (56,164), contains terrain steps and one initial cleaning-bot entity at (281,120), with the outgoing trigger near the far right. Final player local position is (154,163). This is compatible with an early obstacle/route stall, but collision causality has **not** been dynamically proven.

**REJECTED prior inference:** “therefore not a static/stuck low-activity state.” +98px from spawn proves some initial movement, not sustained movement/activity during the measured windows. The identical endpoint across 8/13/12 windows increases the concern but does not prove a freeze; a stationary player can coexist with active simulation/audio.

**Corrected status:** retain SRS as **SELECTED GAME / BUILD AND INITIAL PROGRESSION VALIDATED**. Reopen the benchmark route as **CANDIDATE — SUSTAINED REPRESENTATIVE ACTIVITY UNKNOWN**. The prior “LOCKED DKC-like/heavy-platformer” claim is **SUPERSEDED only as a claim of measured representative coverage**. Do not discard valid 60/60 observations or drop the game to make the corpus look better.

Small decisive experiment, before more optimization:
- Run the **same existing benchmark ROM** directly in a pinned SNES reference and through Sodium64.
- At fixed guest-frame checkpoints, record player/camera/room plus one or two meaningful activity signals (entity state, transition, relevant upload activity). Observe before, within and near the end of the measured interval, not only after it.
- If the reference also stops at the same obstacle: **WORKLOAD/INPUT ROUTE LIMITATION**; author a bounded input script including the required jumps/actions while retaining normal physics/collisions/audio. Keep the old workload identity and hash the new one separately.
- If only Sodium64 stalls or diverges: reduce to the earliest mismatch; distinguish reference/harness mapping from actual Sodium64 error before fixing runtime.
- If both show sustained representative activity despite stationary player x: record that activity and accept the route on the evidence actually observed.
- Falsifier for “heavy representative segment”: mostly idle simulation, absent expected entities/uploads, a short initial burst followed by a stall, or unexplained reference divergence. Source features existing somewhere in the game do not show they ran in this segment.

### 4. HYGIENE-BLOCKER: the SRS audition revived unsafe preparation/phase ambiguity

Exact workflow uses **1 host second warmup -> arbitrary debugger interrupt -> zero JIT lookup -> write APU clock21 and reset JIT pointer -> 1 host second settle -> reset counters -> 20 host seconds capture**. `scripts/gdb_rsp_dump.py` implements these stops with timed continue/interrupt; this call does not establish the previously proven safe guest configuration boundary. Integrated `src/apu.S` initializes `apu_clock` to **APU_CYCLE * 2**, so this is an actual rate transition, not necessarily an idempotent write.

**LAB LIMITATION / source-backed risk:** an arbitrary halt can occur in generated code; reusing the JIT buffer/resetting lookup and changing the clock there does not prove the current block/cycle state transitioned safely. No corruption is proven in the successful SRS run. Endpoint APU21 proves the endpoint setting, not clean full-rate startup and all history.

The internal 60-VI history is a useful improvement: later entries do span full internal VI windows. However, equal-length VI windows are not automatically the same game checkpoints. Reset is host-phase-selected; varying collected window counts and sample-ring coverage remain unsuitable for absolute cross-run subsystem-cost comparisons.

**TODO / bounded repair:** reuse the existing matched-window preparation contract already used in M1, or establish diagnostic Road-valid settings before first guest execution at a verified boundary. Do not introduce a new general profiler. Record exact start checkpoint, full warmup windows and a fixed guest-frame/VI horizon. Clear/arm history and profiling together at the intended boundary.

Do not explain the first 53/60 window as a proven “one-frame queue transient”: it is seven frames below60. A startup/phase transient is a hypothesis; its precise cause is unknown. Predetermine warmup exclusion and preserve all raw windows.

The comparator calculates `steady_common_prefix_equal` but does **not assert it**. Green CI here means the configured checks passed, not a persistent repeatability regression gate. During discovery, valid below-target results should remain evidence, not be suppressed by requiring60. If an accepted route later becomes a regression gate, make its actual progression/repeatability expectations explicit.

### 5. REQUIRED SUPPORT: a minimal autonomous reference lane

Do not build a second emulator. Use an existing pinned SNES implementation as a process/library dependency, with a small adapter to the existing harness. Candidate references include ares's **SNES** core or a Mesen-family SNES core; the current ares workflow builds **N64-only**, so a direct-SNES comparison is **TODO**, not already available. Prefer an independent core lineage for resolving disputed behavior; two N64 hosts running the same Sodium64 SNES core are not two independent SNES correctness oracles.

Minimum first deliverable is one SRS route comparison:
- exact upstream/patch/ROM hashes, reference version/settings and Sodium64 SHA;
- deterministic startup, RNG/SRAM state and input indexed by **guest frame**, not CI wall time;
- semantic RAM subset: room, player, camera and demonstrated activity;
- a few aligned image checkpoints and a bounded audio/synchronization check when capture is supported;
- machine-readable expected/observed values and earliest divergence.

Compare logical SNES state at the same phase, not whole N64 memory against SNES memory. Exclude uninitialized/scratch state only with documented reasons. Use SNES source pixels/palette-aware checks where available; N64 output scaling/filtering can invalidate naive whole-image hashes. Audio comparisons need sample-rate/latency alignment and declared tolerances; audio4 alone is not proof of non-silent correct PCM. Reference disagreement remains a question to resolve, not permission to choose the convenient output.

Separate correctness capture from performance capture where debugger stops/tracing would perturb measurement. Use a second reference or hardware only to investigate a concrete discrepancy, not as an endless mandatory matrix for every commit.

### 6. Corpus selection and coverage: preserve diversity without searching forever

| Workload | Audited status | Next useful evidence |
| --- | --- | --- |
| Gothicvania | M1 hardware regression authority | Preserve its achieved result and use as regression control |
| Space Rescue Squad | Source build and initial movement validated; measured-route coverage reopened | Reference-checked sustained activity and safe preparation |
| Nova the Squirrel 2 | Autonomous build passed; runtime audition pending | Clean repeat build identity, then a reference-checked scrolling gameplay route |
| ALttP-like/top-down slot | OPEN | Bounded search for eligible independent game with actual area/state/transition work |

**Nova2 nuance:** run35410418476 proves one successful autonomous build, not independent bit-for-bit repeatability across clean environments. Preserve Python3.8.18/Pillow7.1.2 and exact BRR source prebuild with `-lm`; do not revisit the resolved palette/version guesses. Verify the ROM hash **`ecc61b2367a9261fe48131a61e5cf787b6409083827556109099a46a637d9b2f`** in the next clean audition build. Record the relevant moving tool versions; a pinned source plus unpinned apt/latest tooling is not a fully frozen toolchain.

**Eligibility terminology:** SRS code is zlib and Nova2 code GPLv3, but their assets have game-specific reuse restrictions in upstream LICENSE/README. Describe them as **open code / source-available game assets**, not unrestricted fully open assets. Preserve current build-this-game-in-runner/no-ROM-or-asset-upload boundary; no extraction into a new workload/game. Before broadening redistribution, review the exact asset terms. A public repository or a successful compile alone does not resolve every reuse right.

**Furry RPG:** keep previously recorded eligibility blocker; do not call it admitted because its README says freeware. Castle Platformer / unnamed-snes-engine remain auxiliary/fallbacks, not newly promoted full commercial-family proxies. This audit found no verified superior licensed top-down game to substitute; do not invent one.

Selection should record **observed per-segment coverage**: CPU/game-state work, sprite/entity density, scrolling/tile uploads, DMA/HDMA/windows/color math/Mode7 where actually used, cartridge mapping, audio-driver lineage and duration. “SMW-like/DKC-like/ALttP-like” remains shorthand for desired behaviors, not equivalent stress or compatibility proof. Three platformer engines can still leave important gaps.

Bound the remaining candidate search to one focused batch with an explicit shortlist and rejection reasons. If no adequate fourth game is found, report the coverage gap, use a smaller eligible demo/targeted test for that missing behavior and continue diagnosing demonstrated blockers in the admitted games. Do not quietly declare the fourth representative slot filled, weaken Gate B or write a new large game to satisfy a count. A concrete correctness failure need not wait for an arbitrary fourth title to be fixed.

Targeted auxiliary sources verified during this audit:
- [gilyon/snes-tests](https://github.com/gilyon/snes-tests): 65C816/SPC700 test ROMs, generated expected register/memory results; repository declares MIT. Audit exact selected test/license/pin before adoption.
- [undisbeliever/snes-test-roms](https://github.com/undisbeliever/snes-test-roms): zlib LICENSE and source examples/tests for HDMA, VMAIN remapping, Mode7 tilemaps, windows, joypad and timing behavior. Choose only the small test answering a real gap.
These are **COMPATIBILITY/CAUSAL PROBES**, not substitutes for sustained game performance. Do not import an entire test ecosystem merely because it exists.

### 7. Decompilations/recompilations: useful research, limited oracle authority

Iron's proposal is worth using in a bounded, question-led way. Verified research references:

- [snesrev/smw](https://github.com/snesrev/smw/tree/eae20c65c58930c8b62c76188d259579ad4130f1), inspected `README.md` and `src/smw_cpu_infra.c` (blob `ab6e0ea7edd1903a3765b502bbe051d185c76712`). Provides named game state, replay/state-comparison ideas and identifiable PPU/audio paths.
- [snesrev/zelda3](https://github.com/snesrev/zelda3/tree/fbbb3f967a51fafe642e6140d0753979e73b4090), README blob `14c8366fccbdf7fd4d0f0d13361d169e4fe75874`. Documents optional original-machine-code comparison, per-frame RAM checks and replayable input histories.
- [elliotttate/DKC1Recomp](https://github.com/elliotttate/DKC1Recomp/tree/3eb9a10c49cb210df2bd63addafe2a78cf9f4e22), README blob `1a3175b9d59f875d635bd2390810818c62eceb39`. This is a **static recompilation** project, not interchangeable with a matching disassembly. Its documentation identifies structural metadata, deterministic input/headless validation and disassembly provenance.

All three require the original ROM or extracted game data for the complete runtime path. They therefore do **not** provide a ROM-free autonomous substitute for the commercial game.

**New concrete oracle caution:** SMW's `SmwCpuInitialize` patches out a wait-for-HBlank routine; `PatchBugs_SMW1` fixes game behavior; `SmwFixSnapshotForCompare` copies selected memory regions before comparison; `SmwRunOneFrameOfGame_Emulated` manually controls NMI/frame sequencing. Thus even a successful native-vs-emulated comparison there is not unmodified-SNES bus/timing proof. Do not transplant its exemptions or timing shortcuts into Sodium64.

Useful research output should be: **specific routine/state -> hardware behavior it depends on -> existing open workload/test covering it -> remaining gap**. For example, study tile-streaming queues, object state machines, audio upload protocols or indirect dispatch to improve test coverage. Implement original minimal probes when necessary; retain provenance/licensing if adapting actual code.

Do not build a port of DKC/SMW/Zelda, integrate their native renderer, copy extracted assets, or revive the SNES64/AOT second-project path. Native desktop FPS/code size is not Sodium64/N64 cost evidence.

### 8. RESUME HERE — next technical batches after this audit

**Current milestone: M0/M1 ACHIEVED; M2 / Gate B OPEN.** No runtime architecture is preselected.

1. **MEASUREMENT PROOF:** repair/reuse safe Road-valid startup in the audition harness and compare the existing SRS benchmark in direct SNES reference vs Sodium64 at a few fixed guest checkpoints. This resolves “normal route obstacle / observability issue / Sodium64 divergence” before re-locking its measured segment.
2. **Continuity checkpoint:** preserve reference identity, ROM/input/checkpoint hashes, raw vectors and outcome. If the route is inadequate, record why and introduce a separately hashed input-only route revision; do not overwrite old evidence.
3. **COMPATIBILITY PROOF:** resume Nova2 from its successful source-build head, not the old failures. Reconfirm build hash and audition a bounded meaningful route using the same reference method. No claim that its Mode7/audio/complex engine features are exercised until observed.
4. **Corpus completion:** bounded independent top-down search with explicit eligibility/coverage decision; document any gap. Consolidate only reusable corpus infrastructure after concrete routes justify it; keep one-off diagnostic branches out of master.
5. **Gate-driven intervention:** investigate the first demonstrated correctness/performance blocker, preserve failing cases and regression-check achieved workloads. Reserve N64 hardware for a prepared multi-question milestone. No commercial ROM upload, no always-on user PC requirement, no immediate dynarec/RSP/renderer rewrite.

This audit changes interpretation and next-action priority; it does not claim a new emulator fix, a new hardware result or Gate-B closure.


## Gate-B SRS safe matched-route capture — RUNNING 2026-09-19 UTC

Audit direction has been reconciled against the live repo before this batch:
- `master@ac1ce74740d974b70206fcb6ba842e492b5d7272` remains integrated truth;
- no open PR;
- Nova2 source build is already resolved at `phase3/gate-b-nova2-audition@156b928191c130f13a19868e634c519647d91d59`, run `35410418476` SUCCESS;
- SRS representative-route status remains **REOPENED** despite successful old audition `35407369415`;
- old SRS +98px end observation is insufficient to establish sustained representative gameplay.

### Controlled measurement repair

Current SRS diagnostic head:
**`phase3/gate-b-srs-audition@075068af92da1802aa3a2677c3d44f393215cc44`**.

Changes in this batch are harness-only:
- new `scripts/gdb_matched_srs.py`;
- SRS audition workflow now uses the already-validated M1 configuration boundary:
  **first `cpu_execute` before any guest execution**;
- Road-valid settings are written and verified there: frameskip0/APU21/audio4/precision8;
- JIT lookup/pointer reset occurs before guest CPU/APU execution, eliminating the old host-timed in-flight-JIT ambiguity;
- two complete 60-VI windows are predetermined warmup;
- profiler state is reset only at the exact following `update_fps` boundary;
- five complete 60-VI windows are then measured;
- SRS room/player/camera state is sampled byte-wise at **every** warmup/measured boundary, avoiding the pinned ares unaligned-half debugger limitation;
- discovery does **not** assert 60/60 or route progression. Below-target throughput or a stable stall must remain evidence rather than be hidden by CI acceptance logic.

No Sodium64 production/runtime optimization is introduced. Existing PROFILE-only SRS diagnostic instrumentation remains branch-local.

Exact runs now started for this head:
- **Gate B SRS Audition `35416459569`** — in progress at checkpoint;
- **Build and Validate `35416459565`** — queued/pending at checkpoint.

An intermediate script-only commit `97e81e1f...` launched Build and Validate `35416434504`; it is superseded for interpretation by the complete workflow head above.

### Question / readings

Primary question:
Does the existing deterministic Right+Run SRS benchmark continue changing meaningful guest state over fixed guest-time windows once startup is prepared safely?

Useful readings:
1. **Repeated sustained progression:** route remains viable; proceed to direct-SNES reference comparison at the same guest checkpoints.
2. **Deterministic stable stall:** route is inadequate or encounters a real gameplay divergence. Compare direct SNES before changing input; if direct SNES stalls identically, revise route only. If reference progresses and Sodium64 stalls, preserve first divergence as a compatibility blocker.
3. **Non-repeatable guest vectors:** measurement/observability remains suspect; do not interpret performance or route behavior.
4. **Build/harness failure:** classify separately; no candidate/runtime conclusion.

Next action after this run:
checkpoint exact window/state vectors first, then build the minimal direct-SNES reference lane. Do not resume Nova2 or optimize Sodium64 until this SRS ambiguity is separated.


## Gate-B SRS direct-SNES reference lane — RUNNING 2026-09-19 UTC

Second controlled batch started on a separate branch so it cannot cancel or mutate the in-progress Sodium64 SRS measurement:

**`phase3/gate-b-srs-reference@58aa11a71ef2960c16e6e033561fad3cbf28eb65`**,
parented from the complete safe-matched SRS diagnostic head `075068af92da1802aa3a2677c3d44f393215cc44`.

Exact run:
- **Gate B SRS Direct SNES Reference `35416567103`** — in progress at checkpoint;
- same-head **Build and Validate `35416567070`** — pending at checkpoint.

This branch adds only:
`.github/workflows/gate-b-srs-reference.yml`.
No Sodium64 production/runtime code is changed by the reference lane.

### Question

Does the exact existing SRS benchmark (same upstream pin, same benchmark patch hash and same ROM hash) progress/stall in the same way when executed directly by the pinned ares Super Famicom core?

Identity is fixed:
- SRS upstream `e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865`;
- benchmark ROM SHA-256 `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`;
- benchmark patch SHA-256 `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`;
- ares pin `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`;
- deterministic entropy enabled.

### Minimal reference adapter

Pinned ares does not expose the N64-style GDB guest-memory interface for the SFC core, so the workflow applies a **read-only reference-core observer** rather than creating another emulator:
- builds only the existing pinned ares SFC core;
- resolves SRS symbols at compile time without changing ROM bytes;
- reads direct ares SFC `cpu.wram` after each rendered SNES frame;
- records `frameCounter`, room, player x/y and camera x/y;
- captures 600 reference frames and exits;
- uploads machine-readable trace/provenance only, never the SRS ROM or assets.

`frameCounter` is especially important because upstream defines it as a 32-bit low-WRAM counter updated by `WaitFrame`. It provides a guest-owned alignment key for later Sodium64-vs-reference comparison rather than relying on host time or frontend frame number.

This lane is **correctness/route evidence only**. Direct-ares wall-clock speed is not Sodium64/N64 performance evidence.

### Predeclared readings

1. **Reference also reaches the same stable endpoint:** the Right+Run route itself is inadequate; revise only the deterministic input route, preserving old hashes/evidence.
2. **Reference continues while Sodium64 safe-matched state stalls/diverges:** preserve earliest matching `frameCounter` divergence as a Gate-B compatibility blocker before any performance optimization.
3. **Both progress similarly:** SRS route remains viable and can be characterized further with aligned checkpoints/image/audio evidence.
4. **Reference harness/build failure:** classify adapter/build issue only; no Sodium64/SRS conclusion.

Important follow-up:
the current safe Sodium64 SRS run `35416459569` captures semantic state at exact 60-VI boundaries but does **not yet capture SRS `frameCounter`**. Do not modify its branch while that run is active. After checkpointing its result, add `frameCounter` to a follow-up safe capture only if the direct reference shows that exact cross-core alignment is needed.


## SRS route source geometry clarification — 2026-09-19 UTC

Pinned upstream source gives a concrete scale for the old +98px observation:
- `game/resources/rooms/a1a-entrance.utroom` is a 48x14 authored room;
- `start` entrance local x = **56**;
- `right_door` entrance local x = **728**;
- right-room transition trigger is at tile x=46;
- old deterministic end state player x=4250 with map-left=4096 corresponds to local x=**154**, exactly +98px from the authored start.

Therefore the old endpoint reached only an early portion of the first room and was **far from the authored right-door transition**. This strengthens the audit conclusion that +98px cannot establish sustained representative route coverage.

It still does **not** prove why progression stopped. Competing explanations remain:
- normal room geometry/enemy interaction requiring additional input (e.g. jump/attack);
- benchmark-input limitation;
- Sodium64 correctness divergence;
- less likely remaining observation issue.

The direct-SNES reference lane `35416567103` is the controlled discriminator; do not infer the cause from map geometry alone.


## SRS direct-reference attempt 1 — PATCH-TEXT HASH HARNESS FALSE NEGATIVE 2026-09-19 UTC

Exact failed authority:
- **Gate B SRS Direct SNES Reference `35416567103` FAILED** @ `58aa11a71ef2960c16e6e033561fad3cbf28eb65`;
- failure occurred in step `Rebuild exact SRS benchmark from public source` before any direct-SNES reference execution.

What passed before failure:
- exact pinned SRS/submodule checkout;
- exact public toolchain rebuild;
- upstream release build;
- deterministic benchmark ROM rebuilt successfully;
- benchmark ROM SHA-256 check **PASSED** for `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`.

Failure:
the reconstructed `srs-benchmark.patch` text did not match historical patch SHA
`4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`.

Cause:
the reference workflow reproduced the same benchmark instructions/ROM bytes but omitted explanatory comments present in the historical benchmark patch. Therefore **ROM identity matched while patch-text identity did not**.

Classification:
**HARNESS FALSE NEGATIVE / NO SRS OR SODIUM64 EVIDENCE.**

Controlled repair:
**`phase3/gate-b-srs-reference@dd9eec47c98d4f27a66c1905b5ede62257899499`**
restores the exact historical benchmark comments as well as instructions so both patch SHA and ROM SHA are required to match before direct-reference execution.

No Sodium64 runtime code, benchmark behavior, upstream game source semantics or reference adapter semantics are changed by this repair.


## Gate-B SRS safe matched-route result — VALID MEASUREMENT / REPRESENTATIVE ROUTE NOT YET VALID 2026-09-19 UTC

Exact authority:
- **`phase3/gate-b-srs-audition@075068af92da1802aa3a2677c3d44f393215cc44`**;
- **Gate B SRS Audition `35416459569` SUCCESS**;
- same-head **Build and Validate `35416459565` SUCCESS**;
- diagnostics artifact **`10575723616`**, digest **`sha256:aa118560ab2d59b54e36717452ffcf65e58f835845d06ab504e01e491ff60539`**;
- source-build artifact **`10576445994`**, digest **`sha256:513a591bd4b4c0198a420603701eac6e4e33b7b368416e32bb74d0b310e60438`**.

Measurement contract:
- Road-valid settings configured and verified at the **first `cpu_execute` before any guest execution**;
- frameskip0 / APU21 / audio4 / precision8;
- JIT lookup/pointer reset before guest work;
- 2 complete 60-VI warmup windows;
- profiler-only reset at exact `update_fps` boundary;
- 5 complete 60-VI measured windows;
- byte-wise SRS guest state at every boundary;
- three fresh ares processes.

### MEASURED

All three repeats are **bit-for-bit identical in the observed semantic vectors**.

Each repeat measured frame vector:
**`[60, 60, 60, 60, 60] /60`**.

Seven observed guest-state boundaries (2 warmup + 5 measured), identical in r1/r2/r3:
1. room1 player **(4160,4259)** camera **(4096,4096)**
2. room1 player **(4250,4259)** camera **(4122,4096)**
3. room1 player **(4199,4259)** camera **(4096,4096)**
4. room1 player **(4250,4259)** camera **(4122,4096)**
5. room1 player **(4250,4259)** camera **(4122,4096)**
6. room1 player **(4250,4259)** camera **(4122,4096)**
7. room1 player **(4250,4259)** camera **(4122,4096)**

Derived:
- player-x span across observed boundaries: **90 px**;
- distinct boundary states: **3**;
- room transition: **none**;
- final identical-state suffix: **4 complete 60-VI windows**;
- final state exactly matches the prior endpoint `room1 / player(4250,4259) / camera(4122,4096)`.

Statistical profile is also exactly repeatable at this fixed route phase:
- **3584 samples** each;
- S-CPU8.7%, APU JIT4.0%, APU static28.1%, DSP12.8%, PPU5.2%, DMA1.3%, VI wait39.8% (other buckets negligible).

### Interpretation

**VALID MEASUREMENT:** the previous host-timed APU/JIT preparation concern has been removed for this result.

**MEASURED:** the existing Right+Run benchmark reaches 60/60 throughput in this pinned ares/N64 laboratory at Road-valid settings.

**MEASURED:** the existing Right+Run route then enters a deterministic stable guest-state stall. It is therefore **not validated as a sustained representative DKC-like route**.

Do not interpret the 60/60 vector as broad SRS performance: after the early movement, several measured windows are the same stalled gameplay state.

The cause of the stall remains **UNKNOWN**. This result alone does not distinguish:
- normal authored geometry/input requirement;
- deterministic benchmark-route deficiency;
- Sodium64 gameplay/correctness divergence.

The direct-SNES reference experiment is now the gate-driving discriminator. Do not change SRS input or optimize Sodium64 before reading it.

If direct SNES stalls at the same early location/state under the identical benchmark, classify the route as inadequate and design a richer deterministic input sequence.
If direct SNES progresses materially beyond it, add `frameCounter` to a follow-up safe Sodium64 capture and locate the earliest guest-aligned divergence.


## SRS stall source correlation — SUPPORTED STATIC ROUTE CAUSE 2026-09-19 UTC

After the safe matched stall was measured, pinned SRS source was inspected specifically at the observed endpoint.

Authored room facts:
- `a1a-entrance.utroom` start local x = 56;
- measured stall global x=4250 with map-left 4096 -> local x = **154**;
- base64 room row data decodes to metatile **167** beginning at column x=10 in the relevant lower collision row -> world/local pixel boundary **160**.

Pinned station tileset:
- `game/resources/metatiles/station.utmt` declares:
  **`<tile t="167" collision="solid"/>`**.

Pinned real player metasprite:
- `game/resources/metasprites/player.utsi` has grid origin x=16 and tile hitbox
  `x=10 width=12`, i.e. horizontal extent **-6..+6 relative to the player origin**.

At measured player x=154 local:
**154 + 6 = 160**, exactly the leading edge of the authored solid metatile.

Vertical state also remains at the authored start-ground height, consistent with the character pushing horizontally into the raised solid geometry rather than traversing it.

Classification:
**SUPPORTED STATIC — the deterministic Right+Run route is expected to collide with authored solid geometry at exactly the measured stall coordinate.**

This very strongly supports **benchmark input deficiency / normal game collision** rather than a Sodium64-specific stall, but retain the already-running direct-SNES lane as independent dynamic confirmation before closing the route cause.

If direct SNES confirms the same stop, mark the old Right+Run route REJECTED as representative coverage and replace it with a deterministic route including the required jump/action sequence. Preserve the old benchmark hash as a useful collision/regression probe rather than deleting its evidence.


## Gate B SRS direct-SNES reference — capture harness checkpoint 2026-09-19

Exact candidate remains **`phase3/gate-b-srs-reference@dd9eec47c98d4f27a66c1905b5ede62257899499`**. Direct-reference run **`35416725629`** is still `in_progress` in step **Capture direct-SNES semantic trace**. Earlier steps are green: exact public SRS rebuild, semantic symbol resolution, and pinned ares Super Famicom build all completed successfully. No evidence artifact exists yet.

Workflow audit:
- benchmark ROM identity is still exact: `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`;
- historical benchmark patch identity is exact: `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`;
- tracer exits only after **600 rendered SFC frames**;
- capture command has no command-local timeout/canary; only the job-level `timeout-minutes: 60` bounds it;
- artifact upload is pending, so there is currently **NO dynamic direct-SNES SRS state evidence** from this run.

Classification: **LAB LIMITATION / HARNESS OPEN QUESTION**, not Sodium64 or SRS correctness evidence. Do not infer a guest stall from an ares process that has not produced/returned the trace.

Next controlled batch: bound the direct-SFC capture itself and add enough startup/frame observability to distinguish (A) emulator never reaches the first rendered frame, (B) frames are produced but too slowly, or (C) the 600-frame termination path is wrong. Keep SRS ROM/input bytes and semantic addresses unchanged.


## SRS direct-reference harness repair attempt 1 — workflow-definition false negative 2026-09-19

Harness-only commit **`phase3/gate-b-srs-reference@ba5436747fd3f50a78af5790b1978442750d42af`** attempted to add PPU-load observability, a 300-second command-local bound, trace-count diagnostics, and `if: always()` evidence upload. It did **not** alter SRS source patch bytes, benchmark ROM identity, input sequence, semantic addresses, or Sodium64 runtime code.

GitHub run **`35418466127`** completed immediately as FAILURE with **zero jobs created**. Therefore this is a **HARNESS / workflow-definition false negative** and contains no ares/SRS/Sodium64 execution evidence. The older direct-reference run `35416725629` remained in progress because the invalid replacement workflow never instantiated a job capable of exercising concurrency cancellation.

Decision: diagnose and correct workflow syntax only. Do not change the direct-reference experiment or benchmark while repairing this definition.


## SRS direct-reference workflow validity restored — checkpoint 2026-09-19

Second harness-definition attempt **`60c07376e7d8134f4048ae287e5f14ccd6038870`** was also rejected before job creation (run **`35418518058`** FAILURE). Like `ba543674...`, it is **REJECTED as execution evidence**; no direct-SFC guest code ran.

Rather than continue patching an invalid definition, the workflow file was restored byte-for-byte to the last GitHub-accepted blob from `dd9eec47...`:
- branch commit **`phase3/gate-b-srs-reference@17e0be6f17ccf2f47860f5b689ff34118afca5fc`**;
- restored workflow blob **`67642e8430f0fda7d33bc641b1d3bec2266f07f2`**, exactly the known-valid `dd9eec47...` workflow content;
- new direct-reference run **`35418552346`** was created as **Gate B SRS Direct SNES Reference** and is pending at checkpoint;
- Build and Validate run **`35418552244`** is also pending.

This proves the workflow-definition failure was introduced only by the attempted observability edit. The SRS benchmark experiment itself remains unchanged. Next batch: add a **single minimal harness variable** to the known-valid workflow, keeping the YAML structure simple, so capture duration is bounded without simultaneously changing tracer/source observability.


## SRS direct-reference bounded capture experiment launched — checkpoint 2026-09-19

Exact harness-only HEAD: **`phase3/gate-b-srs-reference@4a753b6e866e41fc603d24ff21ef5d152bac1429`**.

Controlled change from the restored known-valid workflow:
- no tracer/source changes;
- no SRS benchmark/input/ROM changes;
- wrap only the direct ares execution in GNU `timeout --signal=TERM --kill-after=10s 300s`;
- pipe ares stdout/stderr through `tee` so partial `SODIUM64_SRS_REF` frame records survive in the GitHub job log if the command is bounded.

Runs:
- **Gate B SRS Direct SNES Reference `35418579758`** — pending at checkpoint;
- **Build and Validate `35418579750`** — pending at checkpoint.

Question: does pinned direct-SFC ares reach rendered frames under the exact benchmark?
Possible readings:
- 600 trace rows + clean exit => reference capture valid; parse semantic route immediately;
- some trace rows before 300-second bound => direct core progresses but unexpectedly slowly in this CI lab; partial rows are diagnostic, not a complete reference authority;
- zero trace rows before bound => startup/load/frame scheduling path is blocked before the PPU frame tracer; diagnose direct-ares invocation rather than SRS/Sodium64;
- workflow/build failure before capture => harness issue only.

Do not optimize Sodium64 or redesign the SRS route until this reference-lane ambiguity is resolved.


## SRS direct-reference tracer bypass root cause — static source proof 2026-09-19

Pinned ares source **`17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`** explains the apparent endless capture without invoking any SRS/Sodium64 defect:

- `desktop-ui/settings/settings.hpp`: **`settings.video.pixelAccuracy = false` by default**.
- `desktop-ui/emulator/super-famicom.cpp`: loading Super Famicom calls `ares::SuperFamicom::option("Pixel Accuracy", settings.video.pixelAccuracy)`.
- `ares/sfc/ppu/ppu.cpp`: `PPUBase::setAccurate(false)` selects **`ppuPerformanceImpl`**; true selects `ppuImpl`.
- the current direct-reference tracer is injected only into **`ares/sfc/ppu/main.cpp`**, which is compiled into `ppuImpl`, not the default `ppuPerformanceImpl`.

Therefore the default direct-SFC run can execute the game indefinitely while never incrementing `sodium64TraceFrame` or reaching the tracer's `std::exit(0)` at 600 frames. This is a **SUPPORTED STATIC ROOT CAUSE / LAB HARNESS DEFECT** for the hanging reference run. It does **not** demonstrate a guest stall.

Decision: make the reference mode explicit by launching pinned ares with **`Video/PixelAccuracy=true`**, matching the instrumented accurate PPU and strengthening reference fidelity. Keep SRS ROM/input/source bytes unchanged. The bounded `4a753b6e...` run is diagnostic-only and may be superseded/cancelled by this repair; no need to wait out 300 seconds solely to rediscover a statically proven tracer bypass.


## SRS direct-SNES accurate-PPU reference launched — checkpoint 2026-09-19

Exact candidate: **`phase3/gate-b-srs-reference@c5f4c0310cc2334d3f4784517a24e27addfc9e96`**.

Single controlled change from bounded harness `4a753b6e...`: add CLI setting **`Video/PixelAccuracy=true`** so pinned ares selects the already instrumented `ppuImpl` rather than the default `ppuPerformanceImpl`. The 300-second command bound and `tee` diagnostics remain. SRS source patch, deterministic Right+Run input, benchmark ROM bytes/hash, semantic symbol addresses, and tracer logic are unchanged.

Runs:
- **Gate B SRS Direct SNES Reference `35418629393`** — pending at checkpoint;
- **Build and Validate `35418629406`** — pending at checkpoint.

The superseded known-valid and bounded runs were cancelled through branch concurrency; this is intentional. Current question: with the instrumented accurate PPU selected, does the direct SFC core emit the expected 600 semantic frame records and exit cleanly? If yes, compare route progression against Sodium64; if no, use the now-visible partial log to isolate the remaining harness issue before touching guest input.


## SRS direct/reference alignment contract — source-backed checkpoint 2026-09-19

Pinned SRS source **`undisbeliever/space-rescue-squad@e08333a6cbdf5ac5f9e8deb052fe6a9fd9a54865`** defines `frameCounter` in `engine/vblank/_common.inc` as a 32-bit low-RAM counter “updated on every WaitFrame call” and explicitly states that lag frames are included while NMI is enabled. `WaitFrame__far` adds `NmiHandler.counter` into `frameCounter`; upstream unit tests exercise the same lag-frame behavior.

Measurement consequence: direct-SNES vs Sodium64 state should be aligned primarily by **game-owned `frameCounter`**, not host elapsed time or ares host-frame index. The direct tracer samples every rendered SFC frame, so repeated semantic rows for one `frameCounter` are possible around game-loop boundaries; comparison should collapse/group rows by guest counter and locate the earliest same-`frameCounter` divergence in room/player/camera state.

This source-backed alignment contract is compatible with Astra's warning about host-timed checkpoints and will be used once `35418629393` produces the direct trace. No benchmark behavior was changed by this batch.


## SRS direct-reference branch isolation check — checkpoint 2026-09-19

Direct compare **`075068af92da1802aa3a2677c3d44f393215cc44 -> c5f4c0310cc2334d3f4784517a24e27addfc9e96`** is isolated to exactly **one added file**: `.github/workflows/gate-b-srs-reference.yml` (373 lines). No Sodium64 runtime source, validated matched-profile script, or existing workflow is modified on the reference branch.

Interpretation: the direct-reference lane is infrastructure-only relative to the safe SRS Sodium64 authority. Any direct-SFC trace result cannot be attributed to a Sodium64 code modification introduced by this branch.


## SRS accurate-PPU reference pre-capture gates green — checkpoint 2026-09-19

Exact candidate remains **`phase3/gate-b-srs-reference@c5f4c0310cc2334d3f4784517a24e27addfc9e96`**.

Current authorities:
- **Build and Validate `35418629406` SUCCESS** for the exact candidate.
- Direct-reference run **`35418629393`** is still in progress.
- In that run, dependency setup, **exact SRS benchmark rebuild**, and **semantic guest-symbol resolution** are all SUCCESS.
- Step **Build pinned direct-SNES ares with read-only frame tracer** is in progress; capture has not started yet.

Therefore exact ROM/patch reconstruction and symbol observability have survived the PixelAccuracy repair unchanged. No direct-SNES dynamic route evidence exists yet; wait for the instrumented ares build/capture before judging the old Right+Run route.


## Conditional SRS replacement-route input semantics — source preparation 2026-09-19

No replacement benchmark has been launched. This is source preparation only, conditional on the direct reference confirming the old Right+Run wall.

Pinned SRS input/movement source establishes:
- `JOY_H_RUN_BUTTON = JOYH.y`; `JOY_H_JUMP_BUTTON = JOYH.b`.
- `InputBuffer.Process` loads the 5-frame jump buffer only from **`Controller.Joy1.pressed + 1` B**, so merely holding B in `current` does not initiate a jump.
- player movement reads B from **`Controller.Joy1.current + 1`** to select the lower “holding jump” gravity while the button remains held.
- a valid buffered jump while coyote/standing state is available calls `SetJumpYVelocity__a8i16` and then the normal tile-collision path; no collision bypass is required.
- `game/resources/movement-table.csv` gives both PlayerWalk and PlayerRun **JumpVelocity = 2.75 px/frame**.

If the direct reference confirms the authored wall, a next route can therefore differ only in deterministic controller input: introduce a real B press/hold sequence while retaining Right+Run and all ordinary game/collision logic. Test that input first on direct SFC and require sustained semantic progression before accepting it as representative.


## SRS controller-edge semantics for future route — source-backed checkpoint 2026-09-19

Pinned upstream `engine/vblank/controller.inc` defines normal joypad update as:
`pressed = (~previous current) & current`.
Therefore a representative deterministic jump should model an actual B edge:
- set B in `pressed` only on the first frame the button becomes held;
- keep B in `current` for the desired hold interval so player code selects holding-jump gravity;
- clear B from `pressed` on subsequent held frames.

The benchmark injection point in `game/src/gameloop.inc` is immediately before `InputBuffer.Process()`; player processing occurs later in the same loop and `WaitFrame__far` closes the frame. A guest-`frameCounter`-conditioned B pulse can therefore emulate normal controller semantics without changing player/collision state directly.

This remains conditional design evidence only. Do not alter the Right+Run benchmark until the active direct-SNES reference closes the old-route question.


## SRS x-regression authored-enemy hypothesis — source-backed but not yet dynamic 2026-09-19

The safe Sodium64 boundary sequence contains a non-monotonic player-x sample: local x≈154 at the wall, then ≈103, then back to 154. A source-backed authored explanation exists and should be checked against the direct trace:

- `a1a_entrance` spawns `cleaning_bot_slow` at local x=281, y=120, parameter=0.
- project metadata defines `WalkAndTurn` parameter **0 = left**.
- `cleaning_bot_slow` is in the `enemies` list, has knockback enabled, and speed `0x010000` = 1 px/frame.

Thus an enemy moving left toward the trapped player could plausibly account for the later knockback/reset-like x regression. Classification: **HYPOTHESIS / supported static mechanism**, not proven cause; room vertical geometry/entity trajectory still matters. Use the active direct-SNES frame trace to test whether the same regression occurs at comparable guest `frameCounter`. If it does, it strengthens authored-route equivalence; if not, investigate the earliest semantic divergence.


## Gate B SRS direct-SNES dynamic reference closes old-route ambiguity — 2026-09-19

Authority:
- candidate **`phase3/gate-b-srs-reference@c5f4c0310cc2334d3f4784517a24e27addfc9e96`**
- direct-reference run **`35418629393`**, job **`105832026639`**
- same-head **Build and Validate `35418629406` SUCCESS**
- pinned SRS benchmark ROM SHA256 `7d307bfec23d566cb33d265590269e9e67196104c6c2db2ad274f1efbc8b132e`
- pinned benchmark patch SHA256 `4c472a0986dfe4f7678c3234e57aeae611c77df44e7a38341b0756ee160024e7`
- pinned ares `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`
- direct SFC explicitly uses `Video/PixelAccuracy=true`, selecting the instrumented accurate PPU.

**MEASURED direct-SNES guest evidence:** the capture emitted all **600/600** tracer rows. The process then segfaulted during teardown, so GitHub marks the step/run FAILURE and artifact upload was skipped; however the complete 600-row semantic trace is present in the completed job log. Treat the exit-139 as a **HARNESS TEARDOWN DEFECT**, not guest execution failure.

Meaningful direct-reference route:
- authored gameplay becomes plausible after startup; `frameCounter` then advances normally through the trace to **game_frame=594**;
- first exact wall state `room=1 player=(4250,4259) camera=(4122,4096)` occurs at **game_frame=94**;
- exact wall intervals observed: **94–127**, **218–370**, and **377–594**;
- after the first wall interval the player moves left beginning at game_frame 128, then returns right and reaches the wall again;
- final row host_frame=600/game_frame=594 is the same exact wall state;
- no room transition occurs.

This dynamically confirms that the old deterministic Right+Run benchmark stalls against authored gameplay geometry on a direct SNES reference too. It is **not a Sodium64-specific gameplay stall**.

Cross-check against the seven safe Sodium64 60-VI boundary states from `35416459569`:
- sampling the direct trace at guest frames **37,97,157,217,277,337,397** reproduces **6/7 states exactly**;
- the only miss is guest frame 217: player is already exact at (4250,4259), but camera_x is 4120 rather than Sodium's 4122; the direct reference enters the exact wall state on the following guest frame 218.
- Because the existing Sodium capture does not yet record SRS `frameCounter`, do not overstate this as perfect same-frame equivalence; it is nevertheless strong dynamic route equivalence on top of the prior map/collision source proof.

Decision:
- classify old **Right+Run SRS route as REJECTED for representativeness**: it spends most of the measured horizon blocked by normal authored geometry.
- retain it as a useful deterministic **collision/enemy/regression probe**; its old 60/60 throughput is valid only for this limited route.
- do **not** optimize Sodium64 from this route.
- next representative SRS route must differ only by realistic controller input (B edge/hold semantics already documented), be validated on direct SFC first, and demonstrate sustained progression beyond local x=154, preferably reaching the authored `a1b_stairway` room transition.

Harness follow-up: repair termination so a complete 600-row trace exits green and uploads evidence. The guest trace itself is complete; do not rerun merely to answer the old-route semantic question.


## SRS direct-reference teardown repair launched — checkpoint 2026-09-19

Exact candidate: **`phase3/gate-b-srs-reference@dd05ba502a6c4c6b7c4de2da1384207d23ea5a2d`**.

Controlled harness-only change from the dynamically informative `c5f4c031...` run:
- tracer still emits the same row and flushes stderr after every frame;
- at host frame 600 replace **`std::exit(0)` with `std::_Exit(0)`**;
- purpose: skip ares global/static destructor teardown that produced SIGSEGV 139 after the complete 600-row trace.
- no SRS source/input/ROM/symbol changes; no Sodium64 runtime changes; PixelAccuracy=true remains explicit.

Runs:
- **Gate B SRS Direct SNES Reference `35419188132`** — in progress at checkpoint;
- **Build and Validate `35419188123`** — in progress at checkpoint.

Question: does the already-complete 600-row direct trace now terminate with process status 0 and permit the existing non-ROM artifact upload/semantic assertions to finish?

Expected readings:
- SUCCESS + artifact => harness teardown fixed; use artifact as durable authority, with semantics expected identical to `35418629393`;
- failure after 600 rows => guest evidence remains valid, teardown mechanism still needs a harness-only repair;
- any semantic trace difference before frame 600 would be unexpected and must be investigated rather than ignored.

The old Right+Run representativeness decision is already closed by `35418629393`; this rerun is for evidence hygiene only.


## Gate B SRS direct-reference harness closure — 2026-09-19 UTC

**Classification:** MEASUREMENT PROOF / LAB LIMITATION closure.

- Candidate: `phase3/gate-b-srs-reference@dd05ba502a6c4c6b7c4de2da1384207d23ea5a2d`.
- Direct-SNES reference run `35419188132` / job `105833513437`: **SUCCESS**.
- Same-head Build and Validate `35419188123`: **SUCCESS**; normal build, PROFILE build and emulator-smoke all green.
- Trace contract remained unchanged: pinned SRS source/benchmark ROM and patch, pinned ares accurate SFC core, read-only WRAM observation, 600 rendered-host-frame horizon.
- Dynamic result: exactly **600** parsed rows, **590** plausible-gameplay rows; last plausible row `host_frame=600 game_frame=594 room=1 player_x=4250 player_y=4259 camera_x=4122 camera_y=4096`. This matches the prior complete red run's semantic endpoint.
- Artifact `gate-b-srs-direct-snes-reference`: ID **`10577226179`**, 14,822 bytes, digest **`sha256:9e08567f7995096fe69cb1bfe2357c1514be8c5622f1df569ef5a6278f7ac715`**.
- The one-line `std::_Exit(0)` termination avoids the prior post-trace ares destructor crash. **SUPPORTED INTERPRETATION:** the earlier exit-139 was teardown-only. It never weakened the old Right+Run route conclusion.
- **Decision:** evidence hygiene is closed. Do not spend more Gate B time on this harness cleanup unless a future reference trace exposes a new defect.
- **Immediate next action:** create and validate a representative SRS controller route on direct SFC first. Change controller input only; preserve game state/collision logic. Require progression beyond local x=154 and prefer authored transition from `a1a_entrance` to `a1b_stairway` before using the route to measure Sodium64.


## Gate B SRS representative route v1 launch — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / workload selection; experiment RUNNING.

- New temporary branch from validated direct-reference head: `phase3/gate-b-srs-representative@c0652c7007ccb9886ff014af74f0c057b51ff18f`.
- Controlled variable: deterministic controller input only. Right+Run remain held. B is asserted in `pressed` only on the edge where `frameCounter & 0x3f == 0x08`, and B remains in `current` for the 16-frame interval `0x08..0x17`; this repeats every 64 guest frame-counter ticks.
- Game entry, authored player state, gravity, entity processing, tile collision and room scripts remain untouched from the prior source-built benchmark route.
- Direct-SFC discovery run: **`35420037005`**. Same-head Build/Validate: **`35420037006`**.
- This discovery workflow computes and records the exact modified benchmark patch/ROM SHA-256 after source build; hashes are not pre-asserted because this is the first build of a deliberately new route. If accepted, pin the observed identities for subsequent matched runs.
- Acceptance target: sustained progression beyond old wall state `room=1 player_x=4250` (local center x=154), preferably authored room transition to `a1b_stairway` within the 600-frame trace.
- Falsifier: route remains trapped at/behind the same obstacle or produces only an artificial non-progressing cycle. In that case keep the direct-reference harness, reject v1 route, and adjust only controller timing.
- **Do NOT interpret throughput or optimize Sodium64 from this run.** It is direct-SFC workload qualification only.


## Gate B SRS representative route v1 build checkpoint — 2026-09-19 UTC

- Candidate remains `phase3/gate-b-srs-representative@c0652c7007ccb9886ff014af74f0c057b51ff18f`.
- Same-head Build and Validate **`35420037006` SUCCESS**.
- The direct-SFC route run **`35420037005`** has already completed source rebuild and semantic-symbol resolution successfully and is building the pinned accurate ares SFC core.
- **What this proves:** the route-v1 branch is build/smoke viable and the modified public-source SRS benchmark compiles with the intended input semantics.
- **What this does not prove:** route representativeness/progression; no direct gameplay trace has completed yet.
- Next action remains unchanged: inspect the 600-frame direct trace before changing any input timing or touching Sodium64 measurement.


## Gate B SRS representative route v1 result — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / workload selection. Route v1 = **PARTIAL, REJECTED as final representative workload**.

Authority:
- Branch/HEAD: `phase3/gate-b-srs-representative@c0652c7007ccb9886ff014af74f0c057b51ff18f`.
- Direct-SFC run `35420037005` / job `105835852863`: **SUCCESS**.
- Same-head Build and Validate `35420037006`: **SUCCESS**.
- Route patch SHA-256: `6f01fb57b557b4426af7fc3290b3677e2a1c1d3b3effeb5006374655187e2a3b`.
- Route ROM SHA-256: `597caa5ef963bea4fed7991b8d1634e8d4c23ead5aabcfd3105926c892ebaa49`.
- Artifact `gate-b-srs-representative-direct-snes-reference`: ID `10577706765`, 20,378 bytes, digest `sha256:3bd49aa60e2bfdff8407e641664694030455e8f289e4b22f20e204a7644069d4`.

Dynamic reading from the raw 600-row trace:
- Startup garbage occupies the initial rows. A conservative filter (`game_frame <= 1000`, small room id, expected WRAM coordinate range) yields **587** gameplay rows beginning `host=14 game=6 room=1 x=4096 y=4096`.
- First passage beyond old blocked coordinate x=4250 occurs at **game frame 95**: x=4253, y=4214, camera x=4125.
- Progress continues through x>4300 gf117, x>4350 gf190, x>4400 gf217, x>4450 gf329, x>4500 gf355, and x>4550 gf377.
- Maximum/final x is **4554**. From about gf378 onward x remains 4554 while y continues normal jump/fall cycles; final row gf594 is room1 x4554 y4233 camera4426.
- **SUPPORTED INTERPRETATION:** normal jump input conclusively gets past the old authored x4250 obstacle and exercises much more of the room. This rejects any remaining notion that x4250 is an emulator/path hard stop.
- **REJECTED:** v1 as the final Gate-B representative route. It spends roughly the final 216 guest frames blocked at the next obstacle and does not trigger `a1b_stairway`.
- Static map correlation: x4554 corresponds to local center x458; the player's +6 right edge reaches local x464 / tile column29, where the authored room has a tall solid barrier. The trace approaches it from elevated platforms then descends before contact, so jump phase/timing is the next controlled input variable.
- **LAB HARNESS DEFECT (summary only):** the workflow's printed `plausible-gameplay` filter used only player-x range and therefore counted startup garbage (including room110/max x5742). The raw trace and its 600-row parser are unaffected. Correct the summary filter before using its max/room diagnostics again.
- Next experiment: v2 changes only jump timing around the approach to tile column29; keep Right+Run, true B edge/hold semantics, all game/collision state untouched, and validate direct SFC before any Sodium64 measurement.


## Gate B SRS representative route v2 launch — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / workload selection; experiment RUNNING.

- Branch/HEAD: `phase3/gate-b-srs-representative@982f7b1058b09077a47ad069efa03751ffadfc9e`.
- Direct-SFC run: **`35420515333`**. Same-head Build/Validate: **`35420515316`**.
- Controlled guest-input variable vs v1: periodic jump phase only. v1 pressed B when `frameCounter & 0x3f == 0x08`; v2 uses `== 0x20`. Both hold B for 16 guest ticks and keep Right+Run held.
- Rationale from v1 trace: v1 leaves an elevated platform around gf328, reaches its apex too early, then descends into the tall barrier at local tile column29. A later phase tests whether the normal authored jump can use the lower/elevated geometry more effectively without any state manipulation.
- Read-only harness repair in same workflow revision: summary `meaningful` rows now also require sane `game_frame` and room id, preventing startup garbage from polluting max-x/visited-room diagnostics. Raw trace format is unchanged.
- Possible readings:
  - progresses materially beyond x4554 / reaches another room => v2 candidate representative route; pin its computed patch/ROM hashes and consider matched Sodium64.
  - stalls at/before x4554 => reject v2 as final route; inspect exact approach and change controller timing only.
  - build/harness failure => no gameplay conclusion; repair harness.


## Gate B SRS representative route v2 stop-point checkpoint — 2026-09-19 UTC

- Exact candidate remains `phase3/gate-b-srs-representative@982f7b1058b09077a47ad069efa03751ffadfc9e`.
- Same-head Build and Validate **`35420515316` SUCCESS**.
- Direct-SFC run **`35420515333`** is **IN PROGRESS**. Completed successfully: checkout/dependencies, modified SRS source rebuild, and semantic guest-state symbol resolution. Current step at block stop: **Build pinned direct-SNES ares with read-only frame tracer**.
- Experiment question and readings are unchanged: does jump phase `0x20` progress beyond v1 max x4554 / preferably transition out of room1? If yes, pin computed patch/ROM identities and inspect sustained progression before Sodium64; if no, reject v2 and alter controller timing only.
- No Sodium64 runtime/performance conclusion exists from v2 yet.
- **RESUME FIRST ACTION:** inspect run `35420515333` and artifact/log if complete; also retain Build authority `35420515316 SUCCESS`. Do not rebuild/relaunch v2 unless the existing run itself fails for a harness reason.


## Gate B SRS representative route v2 result — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / workload selection. Route v2 = **REJECTED as final representative workload**.

- Authority: `phase3/gate-b-srs-representative@982f7b1058b09077a47ad069efa03751ffadfc9e`.
- Direct-SFC `35420515333` / job `105837192373`: **SUCCESS**. Build/Validate `35420515316`: **SUCCESS**.
- Patch SHA-256 `175ed8495cfdf8a53a0b3906269b4096b1c2f43b428a37618414eed63ba64b5c`; ROM SHA-256 `d534bbc62286304edfe6871621f3ee569acb51d811a36486fecf6cd8c293eee2`.
- Artifact `10576927974`, digest `sha256:b2fb8708d6fdf2ebcc51803b3fda6a312c3e58dc5487ed237513e688a559ea61`.
- Dynamic result: 600 raw rows / 587 correctly filtered gameplay rows. Max/final x **4554**; visited rooms **[1]**. First x4554 is around guest frame 402.
- v1 max x4554 around gf378; v2 max x4554 around gf402. **SUPPORTED INTERPRETATION:** moving the entire 64-frame jump phase +24 changes trajectory/timing but not the limiting obstacle.
- **REJECTED hypothesis:** a whole-pattern phase shift alone is sufficient to traverse the column29 barrier.
- Immediate next action: decode/correlate the exact authored barrier and use the v1/v2 trajectories to design a targeted normal-controller sequence. Do not launch another blind phase sweep and do not measure Sodium64 yet.


## Gate B SRS authored-geometry correlation before route v3 — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / source-backed route design.

- Decoded pinned `a1a-entrance.utroom` exactly as its 48x14 metatile map; no ROM/runtime modification.
- At the v1/v2 limiting coordinate, player center global x4554 => local center x458; the +6 tile-hitbox edge touches local x464, exactly **metatile column29**.
- Column29 contains solid station metatiles continuously at rows **5,6,7,8,9,10** (tiles 168/184 alternating). This is a tall authored wall, not a single ground obstacle.
- The route approaches from the upper structure: columns20–21 have solid tiles beginning at row5; columns22–24 provide a lower landing structure beginning at row7; columns25–28 form the horizontal gap before column29.
- v2 dynamic trace shows the periodic B edge at guest frame352 occurs at `x=4449 y=4160`, immediately after leaving the upper platform edge, then apexes near y4140 and reaches the wall at gf402 already far below its top. v1 is the same local trajectory shifted earlier.
- **SUPPORTED INTERPRETATION:** whole-pattern phase shifts synchronize back to essentially the same upper-platform launch state. The missing route action is not “jump a little earlier/later” from that upper ledge; it is to **skip that jump, land on the authored lower platform, then jump from its right edge**, shortening the required horizontal gap.
- Route-v3 controlled input hypothesis: preserve all earlier v2 periodic jumps; suppress only the gf352 B pulse/hold, allow the player to drop onto columns22–24, then inject one normal B edge/hold around the expected lower-platform traversal before resuming normal periodic pulses. No player position, momentum, collision or room state will be written.
- Falsifier: the player misses the lower platform or the targeted lower-platform jump still cannot exceed x4554. If so, inspect the resulting direct trace and adjust only the targeted controller timing.


## Gate B SRS representative route v3 launch — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / workload selection; experiment RUNNING.

- Branch/HEAD: `phase3/gate-b-srs-representative@d3a101e4f0166bcdd3d0af68641cdfa3d0c074de`.
- Direct-SFC run: **`35421458128`**. Same-head Build/Validate: **`35421458147`**.
- Controlled input change from v2:
  - preserve Right+Run and the same periodic phase-0x20, 16-frame B pulses;
  - suppress only absolute guest `frameCounter 0x0160..0x016f` (the gf352 jump/hold that launches from the upper platform);
  - add one normal B edge at `frameCounter=0x0176` (gf374) and hold through `0x0185` (16 frames), targeting the authored lower platform;
  - after that, periodic pulses resume normally.
- No player position, momentum, collision, entity, camera, room or script state is written. Only `Controller.Joy1.current/pressed` are synthesized with normal edge semantics before `InputBuffer.Process()`.
- Hypothesis: skipping the upper-ledge jump lets the player land on lower columns22–24; the gf374 edge then launches from that shorter-gap platform and should exceed v1/v2 max x4554.
- Falsifier: direct trace misses the lower platform, reaches x4554 or less, or otherwise enters another long non-progressing cycle.
- Possible success: sustained x>4554 and preferably eventual authored room transition. If successful, inspect trace before declaring the route representative and pin exact patch/ROM identities.
- **Do not measure Sodium64 yet.**


## Gate B SRS representative route v3 build checkpoint — 2026-09-19 UTC

- Candidate remains `phase3/gate-b-srs-representative@d3a101e4f0166bcdd3d0af68641cdfa3d0c074de`.
- Same-head Build and Validate **`35421458147` SUCCESS**.
- Direct-SFC route run **`35421458128`** remains in progress in the source-build/reference lane.
- **What this proves:** no normal/PROFILE/emulator-smoke regression from the route-v3 branch revision.
- **What it does not prove:** the modified SRS source patch has not yet completed its direct-SFC dynamic trace; no route acceptance or Sodium64 performance conclusion exists.


## Gate B SRS representative route v3 result — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / workload selection. Route v3 = **REJECTED as final workload, hypothesis refined**.

Authority:
- `phase3/gate-b-srs-representative@d3a101e4f0166bcdd3d0af68641cdfa3d0c074de`.
- Direct-SFC `35421458128` / job `105839822295`: **SUCCESS**.
- Build/Validate `35421458147`: **SUCCESS**.
- Route patch SHA-256: `e6cbc9478c79e21084fa748c1761068db23bb841fafbc39c25fd878cc584bc63`.
- Route ROM SHA-256: `354100d8f6dc14465cd8d06ba6bc9ba558c8d28c188a4387182569a37b6568a8`.
- Artifact `10576984161`, digest `sha256:4940fe564e9acbbbd85e81b480facf14517acc08835455e9b5f5374038ed1120`.

Dynamic result:
- 600 raw rows / 587 gameplay rows; room1 only; max/final x **4554**.
- Suppressing the gf352 upper-platform jump works as intended. The player descends normally: gf352 `x4449 y4163`; gf374 `x4491 y4187`; gf377 reaches `x4497 y4195`.
- **MEASURED landing evidence:** y remains exactly **4195** from gf377 through gf384 while x advances across the lower platform/edge. This is the expected standing center height for the authored row7 platform.
- The targeted B edge at gf374 does **not** produce a jump. Source-backed interpretation: `InputBuffer.jump` is a 5-frame shift buffer; the edge is consumed/aged while still airborne, and the landing occurs during movement after the frame's jump test. By the next standing frame the buffer has expired.
- **SUPPORTED INTERPRETATION:** the route-design geometry was correct; v3 reaches the intended lower platform. The failure is targeted-input timing, not inability to reach that platform.
- **Next controlled experiment v4:** keep every v3 input decision identical except move the one targeted B edge/hold start from gf374 (`0x0176`) to **gf378 (`0x017a`)**, when the trace shows the player is already standing on the lower platform. Preserve 16-frame hold, Right+Run, suppression of gf352 pulse, and all periodic pulses.
- Falsifier: gf378 jump is visibly executed but still cannot cross x4554, or no jump occurs despite standing evidence.


## Gate B SRS representative route v4 launch — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / workload selection; experiment RUNNING.

- Branch/HEAD: `phase3/gate-b-srs-representative@7932bc0cf44722990815685ed0f1d1e4e1951d92`.
- Direct-SFC run: **`35422018484`**. Same-head Build/Validate: **`35422018496`**.
- v3->v4 direct compare: one commit, one file `.github/workflows/gate-b-srs-reference.yml`, +7/-7; Sodium64 runtime untouched.
- Controlled gameplay change: keep the gf352 suppression and every other input identical to v3; move only the targeted lower-platform B edge/hold from gf374..389 to **gf378..393** (`0x017a..0x0189`).
- Evidence basis: v3 trace shows the player first reaches standing lower-platform height y4195 at gf377 and remains there through gf384. The gf374 edge expired before the next-frame standing/coyote test. gf378 is the first trace-backed safe standing frame for an immediate normal jump.
- Hypothesis: the gf378 edge triggers a genuine jump from the lower platform, shortening the gap to the column29 wall enough to exceed x4554.
- Falsifier: no upward jump after gf378, or an executed jump still stalls at/before x4554.
- If v4 crosses, inspect sustained progression/room transition and only then promote the route to matched Sodium64 measurement.


## Block stop checkpoint — route v4 in flight — 2026-09-19 UTC

- Current exact candidate: `phase3/gate-b-srs-representative@7932bc0cf44722990815685ed0f1d1e4e1951d92`.
- Build/Validate `35422018496`: **SUCCESS**.
- Direct-SFC `35422018484` / job `105841333068`: **IN PROGRESS** at block-stop checkpoint. SRS benchmark rebuild and semantic-symbol resolution are already SUCCESS; current long step is pinned accurate ares compilation.
- Question: does moving only the targeted normal B edge to gf378 cause a real lower-platform jump and exceed x4554?
- Possible readings:
  - jump + x>4554: inspect full 600-row route; if progression is sustained, pin route identities and prepare exact matched Sodium64 measurement with frameCounter observability.
  - jump but x<=4554: route mechanics still insufficient; inspect trajectory/geometry before changing input.
  - no jump: timing model still off; use trace to identify first standing/coyote frame and adjust input only.
  - harness/build failure: no gameplay conclusion.
- Read-only downstream preparation completed in this block: the existing safe Sodium64 harness can reuse this source route; add game-owned 32-bit `frameCounter` to compile-time symbol probes and read its four WRAM bytes through guest virtual addresses in `gdb_matched_srs.py` for exact same-frame differential alignment. Do not implement this until v4/direct route is qualified.


## Gate B SRS representative route v4 result — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / workload selection. Route v4 = **wall traversal VALIDATED; final route still PARTIAL**.

Authority:
- Branch/HEAD: `phase3/gate-b-srs-representative@7932bc0cf44722990815685ed0f1d1e4e1951d92`.
- Direct-SFC `35422018484` / job `105841333068`: **SUCCESS**.
- Same-head Build/Validate `35422018496`: **SUCCESS**.
- Route patch SHA-256: `e47e1fa2bc5aaeba290a5a9fea367b9abdc35146f708b15b4afdd15800f71250`.
- Route ROM SHA-256: `b5a5e7cba7a8560264e39cab10727974dc5330f0500400ff2b2d3fa53c1e8391`.
- Artifact `10576884824`, 22,640 bytes, digest `sha256:6d52b4853c04cd9cf33165ff9231cf2be93dd81e301895bfa56135d52418c0ef`.

Dynamic result:
- 600 raw / 587 gameplay rows.
- gf377: lower-platform standing state `x4497 y4195`.
- gf378 targeted B edge is accepted: state immediately moves upward to `x4500 y4192`, then continues rising through subsequent frames.
- Former limiting wall x4554 is exceeded at **gf403: x4556 y4150**.
- Progress remains sustained through the next structures; max x **4810** first appears around gf572 and remains the final x at gf594. Camera reaches x4608.
- Visited room ids remain **[1]**; no `a1b_stairway` transition within this 600-host-frame horizon.
- **SUPPORTED INTERPRETATION:** v4 validates the source-backed route design. The previous x4554 limit was purely input/level traversal, not Sodium64 or direct-SFC inability.
- **Next action before Sodium64:** inspect gf480..594 against authored door geometry. Decide whether x4810 is another input-induced stall near the right-door opening or merely horizon-limited progression. Prefer one more targeted input correction if it can produce the authored room transition without state manipulation.


## Gate B SRS door-approach correlation before route v5 — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / source-backed route design.

- v4 trace shows stable lower-platform/ground traversal around gf529..543: y=4195 while x advances 4728->4749.
- The periodic phase-0x20 pulse fires again at **gf544**. The trace immediately moves upward: gf544 `x4751 y4193`, then rises to y4151 while advancing toward the right edge.
- At gf572 the player reaches max x4810 and remains there through gf594 while descending only from y4151 to y4184.
- Coordinate correlation: global x4810 => local center x714; +6 right hitbox edge = local x720, exactly authored **column45**.
- Authored map: column45 is solid across rows2..7. Column46 (local x736) contains the right-door opening at rows8..10; room script trigger is `x=46 y=8 width=1 height=3` and loads `a1b_stairway`.
- At the v4 collision, local center y55 (global4151) places the player hitbox in the solid upper-door region, not the opening. The route is therefore input-induced: gf544 makes the player jump into the upper door frame.
- **Route-v5 hypothesis:** preserve v4 exactly, but suppress only the periodic B pulse/hold at absolute `frameCounter 0x0220..0x022f` (gf544..559). Let gravity carry the player toward the row8..10 doorway while Right+Run remains held. No game state manipulation.
- Success criterion: x progresses beyond 4810 and ideally room id changes from a1a to a1b within the existing 600-frame trace.
- Falsifier: player still blocks at x4810 or falls into another authored obstruction without transition; inspect resulting trace before any further input change.


## Gate B SRS representative route v5 launch — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / workload selection; experiment RUNNING.

- Branch/HEAD: `phase3/gate-b-srs-representative@2255a6f1aca6c2f81e64c035d94f2a3b0f9a2ecd`.
- Direct-SFC run: **`35424126162`**. Same-head Build/Validate: **`35424126115`**.
- v4->v5 compare: one commit, one file `.github/workflows/gate-b-srs-reference.yml`; Sodium64 runtime untouched.
- Controlled gameplay change: preserve the entire validated v4 route, including gf352 suppression and targeted gf378 lower-platform jump. Suppress only absolute `frameCounter 0x0220..0x022f` (gf544..559), the periodic jump that made v4 strike the solid upper right-door frame.
- Source-backed target: authored right-door trigger is tile column46, rows8..10, and loads `a1b_stairway`. v4 reached local x714 / column45 while too high; v5 lets gravity lower the player toward the opening with Right+Run held.
- Success criterion: x>4810 and preferably room id transition 1->a1b within the 600-frame direct trace.
- Falsifier: still blocked at x4810 or another authored obstacle without transition.
- Do not measure Sodium64 until this direct-SFC route qualification is resolved.


## Gate B SRS route v5 build checkpoint — 2026-09-19 UTC

- Candidate remains `phase3/gate-b-srs-representative@2255a6f1aca6c2f81e64c035d94f2a3b0f9a2ecd`.
- Same-head Build and Validate **`35424126115` SUCCESS**.
- Direct-SFC `35424126162` remains in progress in source-build/reference lane.
- Branch audit: direct compare from safe Sodium64 authority `075068af92da1802aa3a2677c3d44f393215cc44` to current v5 is +13 commits but **only one added file** overall: `.github/workflows/gate-b-srs-reference.yml`. Sodium64 runtime, safe audition workflow and `gdb_matched_srs.py` remain tree-identical to the validated safe authority.
- Consequence: if v5 qualifies, a matched Sodium64 candidate can branch from v5 without inheriting runtime changes; only the existing safe audition workflow/script need route+frameCounter observability edits.
- Exact known SRS symbols for future same-frame matching: `frameCounter=7e1249`, room id `7e2200`, player x/y `7e0123/7e0127`, camera x/y `7e87b3/7e87b5`; `a1a=01`, `a1b=02`, map left/top `0x1000/0x1000`.


## Matched-Sodium measurement design note pending v5 qualification — 2026-09-19 UTC

**Classification:** MEASUREMENT PROOF / planned contract refinement; not yet launched.

- Existing safe SRS harness uses 2 warmup + 5 measured exact 60-VI windows. On the new representative route this would end around the second-wall area and under-sample the late door traversal.
- Do **not** simply increase measured windows: PROFILE ring capacity is 4096 EPC samples, and the prior 5-window SRS capture already produced ~3584 samples. A longer measured interval would wrap the ring and make the retained sample distribution represent only the tail despite a larger monotonic sample count.
- Preferred matched-route contract if v5 qualifies: **5 warmup + 5 measured** exact 60-VI windows. All gameplay from boot still executes normally at Road-valid settings; only the statistical ring reset is delayed to the fifth exact boundary. Five measured windows remain comparable in sample density/capacity while targeting the late representative segment (second-wall traversal through door/transition).
- Add 32-bit game-owned `frameCounter` to every boundary state so direct-SFC and Sodium64 states are aligned by guest frame rather than assumed boundary offset.
- This is a planned measurement-contract change, not runtime optimization. Implement only after direct-SFC v5 route qualification.


## Gate B SRS representative route v5 result — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / workload selection. Route v5 = **progress improved; 600-frame horizon inconclusive for transition**.

Authority:
- Branch/HEAD: `phase3/gate-b-srs-representative@2255a6f1aca6c2f81e64c035d94f2a3b0f9a2ecd`.
- Direct-SFC `35424126162` / job `105847016934`: **SUCCESS**.
- Same-head Build/Validate `35424126115`: **SUCCESS**.
- Route patch SHA-256: `b21d55df2d5fb949646c9a2124d5c062fa5e7f312264dabb2f354fdc67a27935`.
- Route ROM SHA-256: `2455da2b775a04b0e07775b39327d98b1de6a26f2da50bb1a8080e6e2ffffc46`.
- Artifact `10578936699`, digest `sha256:bf790779bedc3d4755850c8f5d6634bd13d88ca2abf1341774620e3aeaa956ff`.

Dynamic result:
- v5 correctly suppresses the gf544 jump. Instead of rising, y descends from 4196 at gf544 through the door approach and reaches ground y4259 at gf583.
- x reaches 4810 at gf572, then **continues progressing** after ground contact: x4811 gf583..586, x4812 gf587..589, x4813 gf590..591, x4814 gf592..593, x4815 gf594.
- Room remains 1 through the final observed frame. This is materially different from v4's hard x4810 upper-frame collision: v5 has no identical-x suffix once grounded.
- Source trigger begins at local x736; player center x4815 => local719. The trace ends while still moving toward the trigger rather than proving a permanent block.
- **SUPPORTED INTERPRETATION:** 600 host frames are now an observation-horizon limitation for the room-transition question. Do not change route input yet.
- **Next controlled experiment:** keep exact v5 ROM/input and extend only the direct-SFC tracer horizon from 600 to 720 frames. This separates simple late transition from a possible later periodic-jump interference (next phase-0x20 pulse occurs at gf608).


## Gate B SRS v5 extended-horizon launch — 2026-09-19 UTC

**Classification:** MEASUREMENT PROOF / workload qualification; experiment RUNNING.

- Exact v5 input/ROM is unchanged. Harness-only candidate HEAD: `phase3/gate-b-srs-representative@d4c7d6ba1ca7a9a6233973560bfd2c7268fad661`.
- Direct-SFC extended run: **`35424563879`**. Same-head Build/Validate: **`35424563888`**.
- Controlled variable from v5 run `35424126162`: tracer observation horizon only, **600 -> 720 host frames**. Route source patch/input logic are untouched.
- Expected route identities must remain exactly v5 patch `b21d55df2d5fb949646c9a2124d5c062fa5e7f312264dabb2f354fdc67a27935` and ROM `2455da2b775a04b0e07775b39327d98b1de6a26f2da50bb1a8080e6e2ffffc46`; any mismatch is a harness/provenance failure.
- Question: with more observation only, does continuing rightward motion from gf594 eventually enter authored room id 02? Also observe whether the next periodic B pulse at gf608 interferes before transition.
- Readings:
  - room1->room2 with unchanged route hashes => v5 is qualified as a representative direct-SFC route; proceed to matched Sodium64.
  - renewed hard stall caused by gf608 jump => route input still needs one targeted correction.
  - continued forward motion but no transition by 714 => inspect exact geometry/trigger; horizon may still be insufficient but do not infer failure without a stall.


## SRS v5 extended-horizon isolation check — 2026-09-19 UTC

- Direct compare `2255a6f1... -> d4c7d6ba...`: exactly one commit, one file (`.github/workflows/gate-b-srs-reference.yml`), **+5/-5**.
- All five replacements are observation-contract `600 -> 720` changes: tracer exit threshold, trace row-count assertion, parsed-row length assertion, host-frame sequence upper bound and provenance text.
- No route generation/input source, benchmark patch, ROM source, Sodium64 runtime or semantic field changes.
- Therefore any dynamic divergence after the first 600 rows is attributable to continued execution of the same v5 route, subject to exact route hash equality check.


## Gate B SRS v4 door-approach interpretation — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / read-only route qualification.

- Re-read direct v4 trace `35422018484`: first x>4554 at gf403 (`x4556 y4150`); sustained progression continues to x4810 at gf572; final gf594 remains x4810 but y has fallen from 4151 to 4184.
- Map-left is 4096. x4810 => local center x714; player right tile-hitbox edge +6 => local x720, exactly the start of column45.
- Authored geometry: column45 is solid only rows2–7; rows8–10 are open. Column46 contains the `right_door` trigger over rows8–10 and its metatiles there are non-colliding; ground is lower. Therefore x4810 while high is expected collision with the upper door frame, not evidence of a new impassable route wall.
- **HYPOTHESIS:** v4 will enter the opening and trigger `a1b_stairway` if observed beyond the current 600-host-frame cutoff, with no controller change.
- Next experiment changes **tracer horizon only** from 600 to 900. Exact route source patch/ROM must stay `e47e1fa2...` / `b5a5e7cb...`; gameplay input remains byte-identical.
- Falsifier: after enough descent/landing time the player remains in room1 and cannot pass x4810; then inspect post-600 state before any input modification.


## Gate B SRS route v5 direct-SNES qualification — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF / representative-workload qualification = **VALIDATED**.

- Route branch lineage:
  - v4: `7932bc0c...`, authentic lower-platform jump, crossed x4554 but periodic gf544 jump approached the door too high.
  - v5 input commit: `2255a6f1aca6c2f81e64c035d94f2a3b0f9a2ecd`; suppress only absolute `frameCounter 0x0220..0x022f` B hold. Direct run `35424126162` SUCCESS, Build/Validate `35424126115` SUCCESS.
  - v5 read-only horizon head: `d4c7d6ba1ca7a9a6233973560bfd2c7268fad661`; only trace horizon 600->720. Direct run `35424563879` SUCCESS, Build/Validate `35424563888` SUCCESS.
- Exact gameplay route remains unchanged across the 600/720 v5 runs:
  - patch SHA-256 `b21d55df2d5fb949646c9a2124d5c062fa5e7f312264dabb2f354fdc67a27935`;
  - ROM SHA-256 `2455da2b775a04b0e07775b39327d98b1de6a26f2da50bb1a8080e6e2ffffc46`;
  - route id `door-transition-v5-suppress-gf544`.
- 720-frame dynamic authority: 720 raw rows / 707 gameplay rows. Room sequence **[1,2]**.
- Door approach: gf594 room1 x4815 y4259; gf614 x4832 y4241; **host621/gf616 room changes to 2** with the same transition-edge state; room2 load then replaces player/camera state and gameplay continues.
- Artifact: `10578072520`, 25,522 bytes, digest `sha256:98375a8b9b1ed8df9b3899ec246e531f51360d0776b0783dc8d8040c42b284cf`.
- **SUPPORTED INTERPRETATION:** v5 is a deterministic, authored, normal-input gameplay route that traverses multiple obstacle/platform/collision segments and executes an actual scripted room transition. It is materially representative compared with the rejected Right+Run wall probe.
- **Decision:** stop route tuning. Do not create v6 unless matched Sodium64 exposes a semantic divergence attributable to input/route rather than emulator behavior.
- Next gate question: on exact v5 ROM/input, does Sodium64 preserve the route semantics and what full-rate 60-VI frame budget/profile does it deliver under the already-validated safe configuration contract?


## Gate B SRS v5 matched Sodium64 launch — 2026-09-19 UTC

**Classification:** GATE DRIVER / COMPATIBILITY + MEASUREMENT PROOF; experiment RUNNING.

- Safe matched branch created from validated old-route authority `075068af92da1802aa3a2677c3d44f393215cc44`: current HEAD **`phase3/gate-b-srs-v5-matched@4ece04a4430b99f7ea00d26967cfa601812e8d15`**.
- Direct compare from `075068af...`: only `.github/workflows/gate-b-srs-audition.yml` and `scripts/gdb_matched_srs.py` change. No Sodium64 emulator/runtime core file changed in this v5 port.
- Exact route guardrails in workflow:
  - qualified direct-SNES route id `door-transition-v5-suppress-gf544`;
  - patch SHA-256 must equal `b21d55df2d5fb949646c9a2124d5c062fa5e7f312264dabb2f354fdc67a27935`;
  - built SRS ROM SHA-256 must equal `2455da2b775a04b0e07775b39327d98b1de6a26f2da50bb1a8080e6e2ffffc46`.
- Matched settings/measurement contract is intentionally preserved: configure at first `cpu_execute` before guest work, frameskip0/APU21/audio4/precision8, 2 warmup boundaries + **5 measured exact 60-VI windows**, three repeats. Profile snapshot is frozen immediately after measured window5.
- New read-only semantic observability:
  - 32-bit game-owned `frameCounter` compile-time address probe;
  - four separate guest-virtual WRAM byte reads, avoiding unaligned/alias-cache ambiguity;
  - four additional **post-profile state-only 60-VI boundaries** after snapshot so route semantics can reach the direct reference room transition without changing the 5-window performance budget.
- Summary stall/activity comparisons explicitly exclude `frameCounter` from spatial-state equality so advancing time alone cannot hide a spatial stall.
- Exact CI:
  - Gate B SRS v5 Matched **`35425597914`** — in progress at checkpoint;
  - same-head Build and Validate **`35425597920`** — pending at checkpoint.
- Experimental questions:
  1. Does the rebuilt benchmark reproduce the exact qualified v5 ROM/patch identities?
  2. Across three repeats, does Sodium64 preserve deterministic guest-state/frameCounter progression and reach room2 in the post-validation horizon?
  3. What are the five measured completed-frame vectors and profile distribution under the unchanged Road-valid settings?
- Readings:
  - exact route hash + deterministic semantics + room2 transition => route equivalence supported; interpret 5-window throughput/profile.
  - exact route hash but semantic divergence => compatibility/timing bug to localize before performance optimization.
  - source/hash/harness failure => no Sodium64 conclusion; repair harness only.
  - frame budget below 60/60 on this qualified route => profile becomes the next optimization evidence.


## Gate B SRS v5 matched — identity/build checkpoint — 2026-09-19 UTC

- Exact candidate remains `phase3/gate-b-srs-v5-matched@4ece04a4430b99f7ea00d26967cfa601812e8d15`.
- Build and Validate **`35425597920` SUCCESS**: normal build, PROFILE build and pinned Mupen emulator-smoke all green.
- Gate B SRS v5 Matched **`35425597914`** has completed successfully through:
  - exact pinned SRS/submodule checkout;
  - upstream CLI toolchain build;
  - unmodified release build/provenance;
  - deterministic v5 benchmark creation;
  - semantic symbol resolution with ROM-byte preservation.
- Because the benchmark-creation step contains hard assertions for patch `b21d55df...` and ROM `2455da2b...`, its SUCCESS establishes that the Sodium64 matched run is using the **same qualified v5 route bytes** as direct-SNES authority.
- The symbol-probe rebuild also passed its before/after ROM identity assertion, so adding `frameCounter` observability did not mutate guest bytes.
- Current step: build Sodium64 PROFILE runtime inside the matched workflow, before pinned ares N64 lab build and three safe repeats.
- No throughput/compatibility interpretation yet; exact-route identity is proven, measurement still pending.


## Gate B SRS v5 matched Sodium64 closure — 2026-09-19 UTC

**Classification:** COMPATIBILITY PROOF + MEASUREMENT PROOF = **VALIDATED in host laboratory**. This closes the current SRS Gate-B question; it does not replace real-N64 authority.

### Exact authorities

- Integrated runtime base: `master@ac1ce74740d974b70206fcb6ba842e492b5d7272`.
- Matched harness candidate: `phase3/gate-b-srs-v5-matched@4ece04a4430b99f7ea00d26967cfa601812e8d15`.
- Safe-lane base: `075068af92da1802aa3a2677c3d44f393215cc44`; direct compare to matched HEAD changes only the SRS workflow + GDB observer, not emulator core runtime.
- Build and Validate `35425597920`: **SUCCESS** (normal, PROFILE, pinned Mupen smoke).
- Gate B SRS v5 Matched `35425597914` / job `105850864586`: **SUCCESS**.
- Matched artifact `10579185638`, 33,026 bytes, digest `sha256:7e2a046ba6de1f147cd169d62203571966641b90bbf07947c9722e664ffbc6b6`.
- Source-build-proof artifact `10578974288`, digest `sha256:9d6ab8d3f3b1ff1bacac24efb862a5bb329bb5267eec4432b1502f3d721c7e43`.
- Qualified guest route is byte-identity guarded:
  - patch `b21d55df2d5fb949646c9a2124d5c062fa5e7f312264dabb2f354fdc67a27935`;
  - ROM `2455da2b775a04b0e07775b39327d98b1de6a26f2da50bb1a8080e6e2ffffc46`.
  Benchmark build + compile-time symbol-probe rebuild both passed identity assertions.

### Measurement contract and repeatability

Settings are applied at first `cpu_execute` before guest CPU/APU execution:
- `apu_clock=21`;
- frameskip `0`;
- audio `4`;
- precision `8`;
- JIT lookup/pointer reset.

Each of three repeats:
- 2 warmup exact 60-VI boundaries;
- 5 measured exact 60-VI boundaries;
- profile snapshot frozen immediately after measured boundary5;
- 4 additional state-only 60-VI post-validation boundaries after the snapshot.

All three repeats are byte-for-byte repeatable in the observed boundary state and profile distribution.

**Measured frame vector, all three repeats:** `[60,60,60,60,60]`.
- mean = **60.0/60**;
- min=max=60;
- profile samples = **3584** each repeat.
The final post-validation room-transition window reports 59 completed frames, but it occurs **after the profile snapshot** and therefore does not alter the fixed five-window throughput measurement.

### Observed Sodium64 guest sequence

All three repeats:
1. gf39 room1 player(4160,4241) camera(4096,4096)
2. gf99 room1 player(4250,4251) camera(4122,4096)
3. gf159 room1 player(4299,4243) camera(4171,4096)
4. gf219 room1 player(4394,4211) camera(4266,4096)
5. gf279 room1 player(4410,4195) camera(4282,4096)
6. gf339 room1 player(4432,4163) camera(4304,4096)
7. gf399 room1 player(4545,4153) camera(4417,4096)
8. gf459 room1 player(4680,4211) camera(4552,4096)
9. gf519 room1 player(4715,4173) camera(4587,4096)
10. gf579 room1 player(4810,4244) camera(4608,4096)
11. gf520 room2 player(4136,4467) camera(4096,4355)

Summary assertions:
- state sequence identical across repeats: **true**;
- measured frame vector identical across repeats: **true**;
- x-span across observed boundary sequence: **674 px**;
- 11 distinct spatial boundary states;
- room transition observed: **true**;
- identical spatial suffix = 1 boundary.

The generated summary text still says “across seven observed boundaries”; that wording is stale after extending the observer to 11 boundaries. **POLISH-OPTIONAL only**; the computed span/state data are correct and no rerun is justified for wording.

### Differential direct-SNES check with game-owned frameCounter

Direct authority is `d4c7d6ba...` / run `35424563879` / job `105848170976`.

At identical `(room_id, frameCounter)`:
- **4/11** boundaries are exact for player+camera state.
- Remaining seven differ only by 1–3 px total on individual axes; no room/path/camera-scale divergence occurs.
- Examples: gf219, gf279, gf339 are exact in room1; room2 gf520 is **byte-exact** `player(4136,4467) camera(4096,4355)`.

Allowing only the adjacent direct guest tick (±1):
- **10/11** Sodium spatial states appear exactly in the direct trace.
- The first boundary is the only non-exact adjacent-tick match and differs by just 1 px.
- Most non-same-counter exact matches correspond to the direct state at `frameCounter - 1`.

**SUPPORTED INTERPRETATION:** Sodium64 deterministically executes the same authored v5 route, including the lower-platform jump, door approach, script trigger and room2 load. The tiny pre-transition discrepancy pattern is consistent with the two observers sampling on different intra-frame sides of SRS's `frameCounter` update. This evidence does **not** prove intraframe byte-perfect CPU/PPU equivalence; do not manufacture such a claim.

### Profile — identical in all three repeats

3584 samples:
- S-CPU interpreter: **8.1%**
- Memory/I-O: **0.1%**
- APU JIT generated: **4.5%**
- APU/SPC700 static: **30.5%**
- DSP/audio: **14.3%**
- PPU/events/frame prep: **5.1%**
- DMA/HDMA: **1.5%**
- VRAM/RSP semaphore wait: **0.1%**
- RSP wait: **0.0%**
- frame/VI wait: **35.7%**
- profiler: **0.0%**
- other: **0.1%**

Representative v5 therefore uses more of the lab frame budget than the rejected wall probe (old VI wait ~39.8%, APU static28.1%, DSP12.8%, DMA1.3%) while still delivering five complete 60/60 measured windows.

**LIMIT:** this is ares N64 laboratory evidence, not a real-N64 performance result. Wall-clock/runtime speed in ares does not establish hardware FPS.

### Decision

- **SRS current Gate-B host-lab question: VALIDATED / CLOSED.**
- Do not optimize APU/PPU/etc. merely because they are large profile categories here: the qualified workload is not failing and has ~35.7% lab VI wait.
- Retain old Right+Run SRS as a collision/regression probe only.
- Retain v5 as the representative SRS compatibility/throughput workload.
- **Immediate Gate-B action:** move to Nova2 gameplay audition using its already-resolved source-build authority `phase3/gate-b-nova2-audition@156b928191c130f13a19868e634c519647d91d59` / run `35410418476 SUCCESS`. Do not redo Pillow/source-build work. The next optimization target should be selected only if Nova2 or another representative workload exposes a real throughput or semantic failure.

## Gate-C audit 2026-09-20 — batch A1: canonical state and first source findings

**Scope / authorization:** only this file on branch `continuity` may change. This checkpoint is partial by design so an interrupted audit leaves useful evidence. No emulator/core/runtime/master/workflow edits, technical PRs, commercial-ROM downloads or lab experiments.

### Canonical state and evidence boundaries
- **VALIDATED (repository inspection):** master `9441818dd8457a27bbd617a0f32c6d484550661f`; initial continuity `1914269d0279e50787c6a49536fd9d10c08976dd`. Read this file and master ROAD_TO_1_0, ROADMAP, PROFILING, VALIDATION. Both roadmap authorities close M2/Gate B and activate M3/Gate C. Comparison from `ac1ce74740d974b70206fcb6ba842e492b5d7272` to audited master changes only ROADMAP and ROAD_TO_1_0. No open PRs at inspection.
- Exact-head public CI: [Build and Validate 35483428361](https://github.com/ironangelo/sodium64/actions/runs/35483428361), [Ares Profile Validation 35483428330](https://github.com/ironangelo/sodium64/actions/runs/35483428330), both success. This is not proof of PPU correctness.
- **MEASURED (inherited hardware evidence, not remeasured/redecoded in this audit):** the prior canonical checkpoint records Gothicvania, SRS and Nova2 each 60/60 ×5 with frameskip 0, APU21, audio enabled, precision8. Preserve exact workload identities and captures above. No reason to repeat Gate B merely because Gate C begins. The milestone covers those workloads, not all titles/effects or full audio/PPU fidelity.
- **Documentation discrepancy:** PROFILING still contains an older post-M1/next-Gate-B framing. ROAD_TO_1_0, ROADMAP and the newest hardware checkpoint supersede that milestone framing. Older “hardware pending” bullets lower in RESUME HERE are historical, superseded by the achieved checkpoint above; they do not reopen M2.
- **LAB LIMITATION:** no commercial SMW/ALttP asset or deterministic reproduction is available here. All new findings so far are static inspection.

### Code findings at the exact audited master
Permalinks below pin the audited source; line ranges are locator hints.
1. **SUPPORTED INTERPRETATION — incomplete window boolean semantics:** [src/rsp_main.S, calc_windows, L1503–1542](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/rsp_main.S#L1503-L1542) explicitly TODOs window 2 and combine logic. Only nibble values 2/3 select window1 normal/inverted; every other value falls through win_none. WH2/WH3 and WBGLOG/WOBJLOG are not consumed by this routine. This proves unsupported states, not that SMW iris uses those unsupported states.
2. **SUPPORTED INTERPRETATION — layer masks lose main/sub independence:** BG path [rsp_main.S L620–642](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/rsp_main.S#L620-L642) ORs TMW and TSW before testing a BG. Hardware masks must be selected separately for the main/sub candidate. A TODO acknowledges the combination shortcut.
3. **SUPPORTED INTERPRETATION — OBJ windows omitted:** `draw_obj`, rsp_main.S L1204–1209 explicitly TODOs object windows and only checks the screen layer-enable bit before rendering sprites.
4. **SUPPORTED INTERPRETATION — color math is a backdrop approximation, not a full compositor:** `not_blank/fill_main/fill_win/fill_notwin`, rsp_main.S L382–416 uses CGADSUB bit5 and CGWSEL bits4–5 to choose fills. The source says “Fill backdrop based on math window settings so SMW transitions work” and TODOs proper color math. L469–478 flattens TM/TS into ordered passes with shared layers on top; this cannot generally represent two independently selected source pixels and SNES add/subtract/half. Need reference comparison before proposing a specific correction.
5. **SUPPORTED INTERPRETATION — scanline state can be coalesced:** `ppu_event/run_line`, ppu.S L193–246 uses dirty state plus cooldown before `make_section`; precision8 selects an adaptive cooldown, not an unconditional snapshot on each HDMA change. `make_section/section_init` L353–407 copies 64-byte PPU sections. Whether this contributes to the observed iris is **HYPOTHESIS**, not measured timing error.
6. **SUPPORTED INTERPRETATION — source ownership matters:** R4300 executes CPU/DMA/PPU event handling and packs state; RSP decodes/caches tiles and emits RDP commands; RDP rasterizes/composes into a single target framebuffer. Do not describe RSP as the sole pixel compositor or assume R4300 currently performs full SNES color math.
7. Further risks to verify: frame-end palette/VRAM snapshot, bounded OAM snapshots, window endpoint conventions, priority shortcuts. Preserve these as separate candidates instead of forcing one shared cause.

### Next audit batch
Trace reference window/color arithmetic semantics and public SMW transition routines; classify which missing features SMW actually requests. Investigate ALttP source separately. First future experiment must isolate one major uncertainty with original diagnostic assets and stable register state before adding HDMA; **do not implement or run it during this audit**.

## Gate-C audit 2026-09-20 — batch A2: code path, semantics, SMW and ALttP

**Read with batch A1. Status: static source audit complete for the targeted path; repair/performance/lab design follows in A3.** No new runtime measurement. **SUPPORTED INTERPRETATION** means an implementation fact or semantic inference supported by cited source, not confirmation of Iron's observed game defect. **HYPOTHESIS** connects a gap to that defect; **UNKNOWN** needs a trace. **MEASURED** is reserved for actual execution/captures. All Sodium64 locators below refer to master `9441818dd8457a27bbd617a0f32c6d484550661f`.

### A. Complete relevant path and ownership

| Stage | Exact source / symbols | State and consequence |
| --- | --- | --- |
| S-CPU store dispatch | [memory.S L658–708](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/memory.S#L658-L708), `tlbs_exception/tlbs_io/tlbs_ret`; `write_iomap` L120 onward | TLB I/O miss identifies SNES address, selects write handler and adjusts cycles. The $2123–$2133 entries dispatch the PPU registers discussed below. |
| DMA/HDMA register writes | [dma.S L87–225](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/dma.S#L87-L225), `reload_hdma/trigger_hdma/hcpu_io`, `transfer_modes/unit_lengths` | Reloads channel state, walks direct/indirect tables and writes via the same `write_iomap` handler. Channel mode determines B-bus address sequence. HDMA is present; claiming it is absent is wrong. |
| PPU register model | [ppu.S L141–172](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/ppu.S#L141-L172), L1431–1607 register handlers | `write_w12sel/write_w34sel/write_wobjsel/write_wh0..3/write_wbglog/write_wobjlog/write_tm/write_ts/write_tmw/write_tsw/write_cgwsel/write_cgadsub` store changed state and mark dirty. `write_coldata` merges selected RGB channels into `coldata`, then `update_fill`. WH0–3, both boolean-logic registers, TM/TS/TMW/TSW and math controls DO exist in the model. |
| Event application | [cpu.S `cpu_execute` around L441](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/cpu.S#L441), [ppu.S L193–255](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/ppu.S#L193-L255) | CPU cycle expiration enters `ppu_event`; current line increments; `run_line` snapshots dirty state only when cooldown permits, then calls HDMA, then advances the event budget by 341×4. Exact write-to-visible-dot timing is not represented by the 64-byte section format. Snapshot-before-HDMA is a fact; a one-line error is not proved without the line convention and a reference trace. |
| R4300 section encoding | [ppu.S L310–465](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/ppu.S#L310-L465), `make_section/section_init/update_frame/update_fill` | Previous section gets a split-line endpoint; a 64-byte block starting at `bghofs` is copied. Up to 16 OAM snapshots/frame. `MAIN_COLOR` is brightness-converted CGRAM0; `SUB_COLOR` is brightness-converted fixed COLDATA, NOT the winning subscreen pixel. Those names must not mislead a repair. |
| Frame-end resources / handoff | [ppu.S L468–625](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/ppu.S#L468-L625), `rsp_frame/update_dpal/dirty_loop/vram_loop/rsp_wait/menu_return/frame_wait` | Final CGRAM palette (255 nonzero entries) is converted with current brightness into a 0x800-byte TLUT queue. Dirty VRAM table copied; 64KiB VRAM cache written back. R4300 waits SP halt, updates UI, publishes queue pointers/section end/framebuffer to DMEM, uses VRAM semaphore, and unhalts RSP. Double state queues and triple framebuffers permit overlap; no new ownership protocol may be assumed safe without checking these fences. |
| Shared ABI / storage | [defines.h L113–209](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/defines.h#L113-L209) | Each section queue 0x5000, OAM queue 0x2200, palette queue 0x800, dirty queue 0x400; VRAM_BUFFER 0x10000. DMEM `BGHOFS..SPLIT_LINE` mirrors section state; frame pointers follow. WBGLOG/WOBJLOG/WH2/WH3 survive transport but are ignored downstream: **consumer omission**, not missing transfer. Raw fixed/backdrop RGB and per-section brightness/palette epochs do not survive in adequate form for general exact math. |
| RSP ingestion | [rsp_main.S L171–255](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/rsp_main.S#L171-L255), `draw_frame/next_section` | Copies current full VRAM into VRAM_BUFFER in chunks, clears semaphore, merges dirty bits, points RDP at framebuffer/palette; DMAs each section and optional OAM snapshot. Builds priority-specific object lists. |
| Windows / screen and layer selection | [rsp_main.S L352–497](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/rsp_main.S#L352-L497), L620–673, L872–875, L1204–1209, L1503–1542 | Backdrop fill approximation; TM/TS flattened passes; LAYER_CHART priority draw order; BG scissor spans via `calc_windows`; no OBJ or Mode7 window path. Only normal/inverted window1 is implemented. |
| Tile pixels / RDP | [rsp_main.S L783–869](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/rsp_main.S#L783-L869), `shared_decode4/16/256` L1450–1499; `rdp_send` L1628 | RSP vector instructions decode planar tile indices, preserve zero-index transparency and add palette offsets; cached textures feed RDP texture rectangles (Mode7 uses a separate path). `RDP_INIT/RDP_FRAME/RDP_FILL/RDP_WINDOW/RDP_TILE` are command templates. RDP rasterizes and overwrites the selected framebuffer. No independent main/sub per-pixel winners, math-eligible source IDs or exact RGB5 math pass are constructed. |
| Visible output | [main.S L240–325](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/src/main.S#L240-L325), `vi_interrupt/check_frame/set_buffer` | VI interrupt consumes ready-frame count and rotates VI_ORIGIN through three framebuffers. RSP wait/VI wait are synchronization costs, not interchangeable “free CPU time”. |

**Delay-slot caution:** `fill_main` branches at rsp_main.S L400 with the `MAIN_COLOR` load at L404 in its delay slot. The intervening label does not make that load missing. A superficial control-flow reading would invent a bug here.

### B. Reference semantics, distinct from this implementation

Reference source pinned to [ares window.cpp](https://github.com/ares-emulator/ares/blob/17813a3ccda21ab9bd45f09bfc2f91196dbf50ff/ares/sfc/ppu/window.cpp#L5-L46), [ares io.cpp](https://github.com/ares-emulator/ares/blob/17813a3ccda21ab9bd45f09bfc2f91196dbf50ff/ares/sfc/ppu/io.cpp#L478-L623), [ares dac.cpp](https://github.com/ares-emulator/ares/blob/17813a3ccda21ab9bd45f09bfc2f91196dbf50ff/ares/sfc/ppu/dac.cpp#L43-L173). This independent implementation is a semantic reference, not a claim that its output replaces real SNES authority.

- For each BG, OBJ and COLOR target, W1/W2 membership is inclusive L≤x≤R, independently inverted and enabled. With both enabled, the target's two-bit logic selects OR/AND/XOR/XNOR; with one enabled use that one; with neither, mask is false. L>R is empty before inversion. TMW and TSW independently suppress that target's main/sub candidate; they are not ORed together.
- COLOR has its own WOBJSEL high nibble and WOBJLOG bits2–3. Its combined mask drives two independent CGWSEL policies: main clipping to black (bits6–7) and math prevention (bits4–5). For each policy values 0/1/2/3 mean never / outside / inside / always **disable** the corresponding operation/color. Disabling main color does not mean disabling all final math output: clipped black may still receive the second operand.
- Choose nontransparent priority winners independently on main and sub. The main winner's identity selects CGADSUB bits0–5 (BG1..BG4, OBJ, backdrop). OBJ palettes0–3 are excluded from math; palettes4–7 can participate. A backdrop is not an ordinary transparent tile.
- CGWSEL bit1 selects subscreen versus fixed operand; if subscreen has no opaque winner, fixed color is the fallback. CGADSUB bit7 selects add/subtract; bit6 requests half subject to clipping/transparent-sub exceptions. Explicit fixed mode can halve; transparent-sub fallback disables half. CGRAM0 is main backdrop; COLDATA is separately updated fixed RGB.
- RGB components use 5-bit saturation/rounding rules. Addition with half is not “saturate at31 then divide”: compute the appropriate half sum; subtraction clamps negative components and then halves when allowed. Apply display brightness after color math. Correctness needs source eligibility, sub transparency, raw color and clip/math policy, not just two displayed RGB values.
- Independent documentation cross-check: [fullsnes PPU Window / Color-Math](https://problemkaputt.de/fullsnes.htm#snesppuwindow) describes inclusive endpoints, independent screen masks and math controls. Its compact WxxSEL text appears internally inconsistent in the displayed 2-bit value labels (“0..1 disabled” alongside “1 inside”); use the explicit enable/invert bitfields and ares decoder, not that typo. No public reference consulted proves Sodium64's exact event timing.

### C. Candidate causes, explanations and falsifiers

| ID / classification | Evidence at audited master | Can explain / cannot establish | Discriminating falsifier or test |
| --- | --- | --- | --- |
| H-OBJ — **SUPPORTED INTERPRETATION** omission; game causality **HYPOTHESIS** | `draw_obj` L1204 explicitly omits OBJ windows. OBJ mask register transported but unused for sprites. | Sprites bleeding outside an iris, or disappearing differently from BG. Does not by itself explain backdrop tint, an entire BG silhouette, or ALttP half-bright rain. | Static original diagnostic: same window on BG and OBJ, stable state, HDMA/math off. If both clip correctly at raw framebuffer level, recheck the audited path/build. For actual SMW, TMW/TSW OBJ bit clear at the failing pixel or no OBJ winner falsifies H-OBJ for that pixel. |
| H-COMP — **SUPPORTED INTERPRETATION** major semantic gap; game causality **HYPOTHESIS** | `not_blank` L382–416 consumes only backdrop math bit5 and CGWSEL bits4–5; `next_layer` L469–497 flattens TM/TS. No consumers implement CGADSUB bits0–4/6/7 or CGWSEL bits1/6/7 in renderer. | Wrong fixed/backdrop addition, rain transparency, half/add/sub, main clipping, shared-layer behavior. It cannot determine which of these a particular unknown SMW capture needs; several SMW backgrounds can accidentally match the fill approximation. | Hold all geometry/state constant, change only half/add/sub or second operand with known RGB5 expected values. A matching result on the exact build with identical winners would refute the claimed missing operation on that tested path. On game trace, if math is disabled and no clipping applies to mismatch pixel, reject this cause there. |
| H-SAMPLE — **SUPPORTED INTERPRETATION** coalescing; visible effect **HYPOTHESIS** | ppu.S `section_vals` L183; `run_line` L222–245; menu.S L34/L74. precision8 = MEDIUM entry (shift2, minimum16, increment1); after first dirty snapshot the initial cooldown is 16>>2=4 lines and grows adaptively, not “8-pixel precision”. | Stair-step/held iris widths and lost per-line register changes. Does not explain a stationary-mask sprite leak or arithmetic mismatch with constant registers. | Log HDMA writes, current PPU WH, each queued section and RSP-loaded WH with explicit visible-line mapping. If every differing reference line has its correct WH at consumer, this cause is falsified for that frame. Repeated section WH across changed source lines supports it. Do not silently switch performance controls to MAX. |
| H-W2 — **SUPPORTED INTERPRETATION** omission; **REJECTED as necessary explanation for inspected SMW iris routines** | `calc_windows` L1503 only recognizes nibble2/3; both-window nibbles fall through; WBGLOG/WOBJLOG unused. | Real two-window effects/boolean tests fail. Public SMW routines below use only W1, so this omission alone does not identify their bug. | Capture active WxxSEL nibbles; no W2 enable means H-W2 is irrelevant for that frame. Future synthetic OR/AND/XOR/XNOR truth table can qualify generic support separately. |
| H-MASK — **SUPPORTED INTERPRETATION** wrong screen independence | BG L622–627 ORs TMW/TSW; shared TM/TS layers removed from first pass. | Main-only/sub-only mask differences and composition involving a layer on both screens. Cannot explain a mask error if TS=0 and the relevant TMW is correctly applied. | Asymmetric screen-mask diagnostic, then actual trace. If the winning layer's masks and coverage are identical between screens, reject mask merging as cause for that pixel. |
| H-EDGE — **HYPOTHESIS**, statically supported endpoint risk | `calc_windows` stores L and R as alternating endpoints; scissor L658–668 uses +12/+13 and increments nonzero segment left; backdrop L418–429 similar. | Likely off-by-one at left boundary / zero-width single-pixel window under conversion to RDP coordinates. Does not explain a large missing transition. | Exact pixel probes for [0,0], [L,L], [0,255], [255,255], L>R, both polarities after removing the N64 x=12 presentation offset. If inclusive coverage matches, reject. No raster experiment run here. |
| H-EPOCH — **SUPPORTED INTERPRETATION** state-history loss; game relevance **UNKNOWN** | ppu.S `write_cgdata` L1418–1425 only backdrop triggers fill dirty; `update_dpal` frame-end brightness/CGRAM; single VRAM copy; max16 OAM copies. | Raster palette/brightness effects, legal midframe memory changes, >16 OAM epochs. Does not prove either reported scene exercises these cases; SNES access restrictions still apply. | Record legal writes and versions. Constant CGRAM/VRAM/brightness/OAM over the mismatch excludes the relevant epoch-loss hypothesis. |
| H-PRIO — **SUPPORTED INTERPRETATION** acknowledged approximation; game relevance **UNKNOWN** | `LAYER_CHART`; L480–483 admits OBJ priority effects inaccurate. | Wrong overlap/trees/sprite occlusion even with math disabled; separate from mask arithmetic. | Compare reference winner identity and priority at a bad pixel before math. Matching winners falsify ordering as cause there; differing winners with constant colors redirects away from arithmetic. |
| H-PHASE — **HYPOTHESIS**, not proved by call order alone | snapshot before HDMA, split-line minus1, pre_vblank early NMI flag L265; H timer writes unsupported in memory.S. | Possible line/IRQ phase error, especially status-bar boundary. Does not imply HDMA is entirely broken. | A two-value alternating-line diagnostic with timestamped source→handler→section→RSP chain determines phase. Same phase with lost intermediate samples is H-SAMPLE, not H-PHASE. |

Additional known Gate-C gaps, **DEFERRED from first iris experiment:** Mode7 window TODO L872–875; LAYER_CHART comments on offset-per-tile/hires/EXTBG; MOSAIC write_unk; SETINI handler TODO beyond overscan. These broaden compatibility risk but are not evidence that normal mode1 iris/rain uses them.

### D. Public SMW evidence without a ROM

Pinned [snesrev/smw src/smw_00.c](https://github.com/snesrev/smw/blob/eae20c65c58930c8b62c76188d259579ad4130f1/src/smw_00.c), [variables.h](https://github.com/snesrev/smw/blob/eae20c65c58930c8b62c76188d259579ad4130f1/src/variables.h), [common_rtl.c L866](https://github.com/snesrev/smw/blob/eae20c65c58930c8b62c76188d259579ad4130f1/src/common_rtl.c#L866-L874). This is public reverse-engineered source inspection only; no commercial bytes/assets acquired or reproduced.

- `SetupHDMAWindowingEffects` L949 (original-location annotation $009250) calls RtlHdmaSetup(channel7, mode0x41, B-bus0x26, table0x00927c, indirect bank0). Mode1 indirect transfers two successive bytes to $2126/$2127 = WH0/WH1; mirror HDMA enable0x80 selects channel7. `misc_hdmawindow_effect_table` is WRAM+$04A0, with two boundary bytes per row. `Setup...ClearWindowTable` fills [255,0] empty windows.
- `UpdateHDMAWindowBuffer_KeyholeEntry` L3846 ($00CA88) builds variable left/right bounds for rows around a center, clips them to 0..255 and uses [255,0] for empty rows. `Update...IrisInOnPlayerEntry` L3836 ($00CA6D) centers on player's on-screen position; radius/scaling byte at WRAM+$1433 changes by -4 through `PlayerState00_00CA44` L3822. This supports **scanline HDMA window geometry**, not a hardcoded renderer circle.
- **Player iris variant:** L3825–3828 sets W12SEL=0x33 (BG1/2 W1 inverted), W34SEL=0x03 (BG3 W1 inverted), WOBJSEL=0x33 (OBJ and COLOR W1 inverted), CGWSEL=0x22 (sub operand selected; math disabled where combined COLOR mask is true, here outside circle; no main-black clip). It does not set a universal TM/TS/TMW/TSW/CGADSUB tuple in that routine: those depend on prior scene setup and IRQ. **Capture rather than invent them.**
- **Title circle variant:** `GameMode04_PrepareTitleScreen` L1596 sets W12SEL=0x33, W34SEL=0, WOBJSEL=0x23 (OBJ inverted, COLOR non-inverted), CGWSEL=0x12 (math allowed inside non-inverted COLOR mask); `GameMode06_CircleEffect` L1074/$00941B updates geometry centered at (128,112). BG3/title layer is configured differently from player iris. Do not conflate these variants or assume all pixels outside every circle must be black.
- `SmwVectorNMI` L378 copies WxxSEL/CGWSEL mirrors and writes CGADSUB, initially clearing its BG3 math bit on the relevant branch. `SmwVectorIRQ` path restores scene settings near L529. `UpdatePaletteFromIndexedTable_00AE47` L2861 writes selected COLDATA channels from the background-color mirror. `UpdateEntirePalette` L944 sets CGRAM0=0. This explains why a background-fill workaround can sometimes imitate a fixed-color backdrop effect while still failing for OBJ/math/scanline details.
- Observable expectation is derived from the **actual active register tuple**: normal scene inside inclusive bounds, suppression of window-enabled BG/OBJ outside inverted layer windows, math permitted/denied by the COLOR window, remaining layers and backdrop according to TM/TS/CGADSUB. For player iris with all outside layers masked and CGRAM0 black, outside becomes black; a deliberately unmasked title layer may remain visible. Expect boundary variation per active scanline rather than large repeated horizontal bands.
- **Reference limitation:** [smw_rtl.c L67–90](https://github.com/snesrev/smw/blob/eae20c65c58930c8b62c76188d259579ad4130f1/src/smw_rtl.c#L67-L90) manually runs PPU lines and simplified HDMA/IRQ. [smw_cpu_infra.c](https://github.com/snesrev/smw/blob/eae20c65c58930c8b62c76188d259579ad4130f1/src/smw_cpu_infra.c#L192-L205) patches out WaitForHBlank_Entry2 and has bug/snapshot normalization machinery. The native port is a source of register intent, **not a cycle-accurate hardware oracle**. Its README requires original resources for gameplay, so it is not an asset-free ROM substitute.

### E. ALttP relationship: still indeterminate at symptom level

Pinned [snesrev/zelda3 overworld.c](https://github.com/snesrev/zelda3/blob/fbbb3f967a51fafe642e6140d0753979e73b4090/src/overworld.c#L1115-L1174) and [nmi.c WritePpuRegisters](https://github.com/snesrev/zelda3/blob/fbbb3f967a51fafe642e6140d0753979e73b4090/src/nmi.c#L67-L79):
- Overlay setup chooses forest/rain variants (rain index0x9f; forest0x9d/0x9e) and sets CGWSEL=0x82, TM=0x16 (BG2,BG3,OBJ), TS=1 (BG1 overlay); for these variants CGADSUB=0x72 (BG2/OBJ/backdrop enabled, additive half). CGWSEL bit1 selects subscreen; bit7 is a main-color-window policy, whose visible effect still depends on WOBJSEL/WOBJLOG. Do not infer active clipping without those values.
- [OverworldOverlay_HandleRain L729–747](https://github.com/snesrev/zelda3/blob/fbbb3f967a51fafe642e6140d0753979e73b4090/src/overworld.c#L729-L747) switches CGADSUB between0x32 and0x72 at particular frame-counter values and scrolls BG1. The changed bit is half, precisely a bit not implemented by Sodium64's composition path.
- **SUPPORTED INTERPRETATION:** ALttP rain/forest overlay intent requires independent main/sub winners and math. H-COMP is a strong candidate for that family. An opaque flattened BG1 overlay cannot generally reproduce the requested half-add.
- **Conclusion: still indeterminate whether Iron's SMW and ALttP observations share the same cause.** They share deficient window/screen/compositor architecture. SMW could be predominantly H-OBJ/H-SAMPLE while rain is H-COMP; a tree occlusion could be H-PRIO or asset/state epoch loss. No game capture identifies which pixel failed or the source winners.
- Distinguishing future evidence: freeze geometry and registers. If SMW's mask is correct but its RGB5 result disagrees under math, and ALttP has the same correct-winners/wrong-arithmetic signature, support common H-COMP. If SMW has sprite leakage/held WH while ALttP has correct geometry and incorrect half-add, establish separate proximate causes within the same subsystem.

### F. Rejected explanations / preserved constraints

- **REJECTED:** “M2 still pending” based on older continuity/PROFILING prose; newest hardware checkpoint and roadmaps supersede it.
- **REJECTED:** “No HDMA” / “PPU never stores window logic”; handlers, DMA route and section fields exist.
- **REJECTED for inspected SMW variants:** missing W2/XOR alone, or missing CGWSEL main-black clip alone. Those routines use W1 and CGWSEL high bits6–7=0. Both omissions remain real generic compatibility issues.
- **REJECTED:** no MAIN_COLOR load in fill_main (MIPS delay slot).
- **REJECTED as correctness solutions:** screen-order menu tweak, higher precision setting alone, game CRC/ID special case, hardcoded iris, underclock/frameskip, or restoring wrong math after a performance regression.
- **UNKNOWN:** whether historical images were title circle, player exit iris, keyhole or overworld variant; exact ROM revision and the precise failure signature. No audit should silently choose one as the observed case.

## Gate-C audit 2026-09-20 — batch A3 / FINAL: decision, experiment, repairs, performance and private lab

**Executive technical summary.** M2/Gate B is achieved for the defined real-N64 corpus; M3/Gate C is active. The targeted renderer has demonstrable SNES-semantic omissions, not merely an unexplained cosmetic mismatch. Most actionable first is **H-OBJ: no OBJ window application**, because public SMW iris code requests inverted W1 for OBJ and the current renderer explicitly skips that feature. **H-SAMPLE** independently threatens scanline geometry at the required precision8. **H-COMP** is broader and especially well supported for ALttP rain/forest, whose public source requests subscreen half-add. It is premature to call one of these the confirmed historical SMW cause or to redesign the entire compositor before a small discriminator. No speedup, full-core rewrite, game hack or commercial ROM is needed to establish the first correctness failure.

**Final report index:** A1 = canonical state/CI/authority limits; A2 A–B = complete code path/reference semantics; A2 C = candidate evidence and falsifiers; A2 D–E = SMW/ALttP; A2 F = rejections; A3 below = experiment, generic repair, cost model, regression policy and private-ROM threat model. Together these are the final audit, not a plan to write an audit later.

### 1. Recommended first technical batch — one uncertainty, no ROM needed

**TODO, not executed:** determine whether a stable W1 OBJ mask reaches the consumer intact yet fails to suppress sprites, independently of HDMA, color math and game assets.

Use a small **original deterministic SNES diagnostic**, following existing source-generated workload conventions in [scripts/make_profile_workloads.py](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/scripts/make_profile_workloads.py). The current six workloads are not a PPU window correctness suite. This next batch would add a test workload/capture recipe on a future authorized technical branch, **not implement the repair**.

- Mode1, brightness15, fixed original BG1 pattern; three original opaque OBJ markers at interior probe x values such as16,96,224 (away from edges), plus an unambiguous frame/phase marker. Stable palette/VRAM/OAM after initialization, no sprite overflow, HDMAEN=0, no H/V IRQ changes during display. CGRAM0 black.
- WH0=64, WH1=191, W12SEL=0x03 and WOBJSEL=0x03 (W1 inverted for BG1 and OBJ); W34SEL=0, logic registers0, TM=0x11, TS=0, TSW=0, CGWSEL=0, CGADSUB=0, fixed color0. Only W1 is enabled; W2 bounds irrelevant.
- Two deterministic Vblank-separated phases differ in **one bit**: control TMW=0x01 versus treatment TMW=0x11. Thus BG1 masking stays on; only OBJ main-window enable changes. Keep both phases long enough for a steady rendered frame, identified by guest state rather than host wall time.
- Expected: BG1 visible only within [64,191] in both phases. In control all three OBJ markers remain visible. In treatment only the inside marker remains; x16 and224 become backdrop black (unless another deliberately documented source occupies them). Inclusive endpoint checks are recorded separately; a one-pixel edge failure must not be mistaken for the large OBJ omission.
- Run the same diagnostic directly in a pinned SNES reference and wrapped through Sodium64 in the **valid N64 lab** (R4300 JIT on, RSP interpreter). Compare cropped raw framebuffer pixels before VI filtering/scaling. Use read-only debugger observations of PPU TM/TMW/WOBJSEL/WH, queued 64-byte section and RSP section at the corresponding frame to confirm request transport; no emulator-core tracing patch should be required for this first question.
- **Support H-OBJ:** input/section/RSP state agrees, BG control clips, but outside OBJ markers survive TMW bit4 in Sodium64 and disappear in reference.
- **Principal falsifier:** treatment clips outside OBJ correctly on the exact audited build with that same verified state; then the alleged exercised path/build identity is wrong or some other mechanism performs the clipping. If state differs before the consumer, the experiment has identified a transport/lab issue instead and has not tested H-OBJ cleanly.
- **Stop condition / artifact:** one control+treatment reference comparison, register/section manifest, exact runtime/diagnostic/tool SHAs, raw synthetic frame hashes and the three probe results. No parallel repair of HDMA/math/W2. After this result choose the generic OBJ-mask repair or follow the first divergent stage. This test establishes an independently sufficient semantic defect; **attribution to Iron's precise SMW observation remains blocked on that scene's trace**.

Why first: it exercises a feature the public SMW iris actually selects, has an exact expected result with original assets, and avoids the strongest confounders. It gives a reviewable autonomous checkpoint before any commercial-asset setup.

### 2. Minimum SMW experiment when Iron's asset is available

**BLOCKED only for commercial-game attribution; not blocking diagnostic work.** No experiment run or infrastructure created in this audit.

1. Identify ROM region/revision and exact SHA256, with a documented header-normalization rule and separate raw/normalized hashes if applicable. Record emulator/runtime/ELF/map, reference version, settings and input script. Do not assume the public port's annotated addresses match every revision.
2. First reproduce the **specific observed variant** (title circle versus player exit iris/keyhole/overworld). Use a deterministic input route and private starting state or replay; locate the first frame with a nontrivial partial circle, then capture previous/current/next frames. For title use the public GameMode06/radius mirror as a locator; for player iris use the radius decrement/public $00CA44 annotation, validated against that revision. Absolute frame numbers are **UNKNOWN** until a route exists.
3. Capture a bounded **PPU write trace**, not an indiscriminate CPU/ROM dump: frame, visible y, dot/cycle when available, write origin (CPU/HDMA and channel), register address/value. Relevant registers: $2100 INIDISP; $2101 OBSEL and $2105 BGMODE; BG scroll/tilebase if source identity differs; $2121/$2122 palette writes; all $2123–$2133 window/screen/math controls; $420C HDMAEN; channel7 $4370–$437A (DMAP, BBAD, table/bank, indirect address/bank, current table pointer and line counter), plus other active channels. Retain the decoded fixed RGB value, CGRAM0, palette epochs, OAM identity and TM/TS/TMW/TSW.
4. Compare for each visible line: expected WH0/WH1 from the actual HDMA stream → Sodium64 register value → section split/state → RSP-loaded section → RDP scissor/fill where needed. Explicitly normalize SNES y convention, section end-minus1, framebuffer x offset12 and vertical FB_OFFSET. Examine circle top/bottom, rapidly changing edge rows and status-bar/IRQ boundary; sample L-1,L,L+1,R-1,R,R+1 and an outside OBJ when in range.
5. Raw reference/Sodium64 pixels must be captured with matched game state, not merely matched host timestamps. Determine main/sub **winner identity, raw RGB5, OBJ palette class, sub transparency, color mask, clip/math eligibility and half state** at first differing pixel. Obtain reference winner metadata privately if reference instrumentation is needed later; it is not already provided by Sodium64's flat RDP output.
6. Interpretation:
   - correct HDMA writes but held WH across several different rows in section/RSP ⇒ H-SAMPLE;
   - constant one-row displacement with all states present ⇒ investigate H-PHASE;
   - correct window geometry/BG cutout but outside OBJ surviving active mask ⇒ H-OBJ;
   - wrong independent main/sub winners only when TMW≠TSW ⇒ H-MASK;
   - correct winners/mask yet incorrect RGB under add/sub/half/fixed fallback ⇒ H-COMP;
   - errors only at inclusive endpoints ⇒ H-EDGE;
   - reference winner wrong before math despite correct masks ⇒ H-PRIO;
   - source color/tile version diverges across raster updates ⇒ H-EPOCH.
7. Falsify each cause with the negative conditions in A2's candidate table. Do not infer cause from an aesthetically improved screenshot. For ALttP, capture a rainy overlay and the same frame-counter half toggle; compare source winners before math, and separately an opaque tree overlap. That is sufficient to distinguish shared arithmetic failure from separate window/priority problems.

Expected hardware observable is the SNES register semantics in A2, including exceptions. The circle is encoded by scanline intervals; a native port's “looks right” screenshot is secondary evidence. Final real-SNES checks are desirable for disputed edge/timing behavior; no claim of hardware pixel truth is made from public C alone.

### 3. Generic repair proposal — smallest justified semantic change first

**PROPOSED, NOT IMPLEMENTED.**

**First candidate if the diagnostic supports H-OBJ:** apply the existing SNES WOBJSEL window selection to OBJ candidates on the relevant screen when TMW/TSW bit4 enables it. Implement generic visible-span clipping in `draw_obj/draw_objtile` around rsp_main.S L1204 onward, sharing a corrected interval evaluator with BG as appropriate. Preserve OAM priority, sprite flips and source texture coordinates while clipping; restore RDP scissor at each appropriate boundary. Never draw masked sprite fragments or leave the last sprite's scissor active for subsequent layers.

- For the isolated main-only W1 case, required WH0/WH1, WOBJSEL, TMW already arrive in the existing 64-byte section; **no new R4300↔RSP field is required**. A generalized screen-aware solution must also retain which screen is being evaluated; the current flattened shared-layer shortcut cannot be declared fully fixed by adding one scissor.
- Extend the same evaluator to both windows and WOBJLOG/WBGLOG only under an explicit follow-up correctness contract. These fields already travel; the generic boolean logic is small, but changing RSP WIN_BOUNDS encoding/local storage and all its consumers requires consistent treatment. Mode7's missing windows is another consumer, not a reason for a game exception.
- Benefits: any software masking OBJ through SNES windows, including spotlights/dialog transitions; no title detection. Risks: OAM overlap priority, clipped flipped sprites, scissor restoration, edge cases L=R/L>R, higher section/span counts and RSP code size. Passing this does not certify math or scanline fidelity.

**H-SAMPLE repair candidate:** preserve every semantically distinct visible-line window/mask/math state at precision8; share/deduplicate equal consecutive state, but do not discard differing lines to satisfy cooldown. Separate cheap line-window state from expensive tile/OAM rebuilds if profiling justifies it. Minimum conceptual version emits correct line sections; optimized version carries an indexed line/span-state table while reusing stable tile resources. This likely changes producer/consumer control and possibly ABI for the optimized variant. Keep exact effective-line timing; do not simply move HDMA before snapshot by guesswork. No dot-accurate promise: subscanline writes need a separately scoped timestamp/event representation if tests demonstrate them.

**H-COMP repair candidate:** replace flattened screen passes/backdrop substitution with independently selected main/sub source winners and actual SNES color policy/arithmetic. A minimum correctness model (host reference or slow experimental renderer, not an assumed production winner) computes candidates, masks, winners, clip, math eligibility, second operand and RGB5 output in that order. Keep raw RGB5 fixed/backdrop/palette values, brightness at its correct epoch, main layer ID/OBJ eligibility and sub transparent flag. These data are necessary even if final architecture remains tile-based.
- General math needs changed intermediate representation/interface or a side buffer; today's MAIN_COLOR/SUB_COLOR are already brightness-transformed fill colors and cannot recover all raw arithmetic inputs. Update section size/offsets/queues/DMEM/linker assumptions together or version an auxiliary descriptor; never silently repurpose fields.
- Benefits: ALttP rain/forest overlays, additive/subtractive lighting, fixed-color fades, many other games naturally. Risks: exact rounding/saturation, transparent-sub half exception, clipped-main interactions, OBJ palette rules, direct color, hires/pseudo-hires and priority metadata. Base-resolution mode1 can be an explicit first milestone; unsupported modes stay documented.
- A generic hardware-semantic dispatch (math inactive, fixed operand, full two-source math) is acceptable **only with proven equivalence per branch**. CRC/game ID/scene detection, native-game C substituted for SNES execution, hardcoded circle and menu screen-swap as final solution are **REJECTED**.

### 4. Performance-preserving design: compare equivalent semantics

No performance numbers were measured for a proposed correction. Gate B's current cadence relied partly on cheaper approximations; the new cost must be paid and optimized honestly.

| Operation | Minimum correct granularity | Candidate optimization / limit |
| --- | --- | --- |
| Static mode/priority tables, arithmetic tables | initialization / mode change | Precompute small immutable lookup tables; verify rounding/flags against independent truth cases. |
| Register decode, window policies, fixed RGB | state change | Decode once and cache descriptor keyed by all relevant registers; source register storage is not a substitute for consumer semantics. |
| WH geometry with HDMA | each effective scanline/change | Reuse identical adjacent line descriptors; exact run-length grouping only. Never average/suppress differing boundaries. |
| Window boolean combinations | per state/scanline span | Sort W1/W2 boundary events, evaluate truth table per interval. Boolean state is constant inside intervals, so no per-pixel window branching is necessary. |
| Tile decode and priority candidate generation | dirty tile / tile row / span | Reuse indexed tile caches across color/window changes; do not invalidate bitplane decode merely because window edges move. |
| BG/OBJ visibility | tile/span clipped against mask | Reject fully masked tiles, split crossing fragments, avoid per-pixel membership tests. OBJ ordering still needs correct candidate selection. |
| Main/sub winner and eligibility | ultimately pixel-dependent where sources overlap | Span classification can select a kernel; individual transparent texture pixels and competing priorities still vary inside the span. A window-span mask alone cannot replace winner metadata. |
| Add/sub/half | pixel for independently varying source colors | Constant fixed-color cases can use exact transformed palettes/tables per eligible class and epoch; general two-source math needs both inputs per pixel. |
| Brightness/CGRAM/VRAM/OAM versions | whenever hardware-visible version changes | Palette epochs/deltas and indexed raw colors; frame-only storage is safe only when invariance is established. Respect SNES memory-access timing. |
| RSP DMA / RDP submission / final output | bounded batches of rows/spans/tiles | Batch descriptors and transfers; avoid CPU readback and CPU↔RSP handshake per pixel. Preserve completion and cache ownership fences. |

**Option A — correct minimum.** For window-only repair, use exact visible spans/scissors on existing RSP/RDP tile paths, with correct screen mask and line state. For full math qualification, use an explicit simple scanline two-winner representation and scalar RGB5 combination as the correctness baseline. It is deliberately not promised to sustain60; it establishes semantics against which alternatives are checked. Avoid committing to a full framebuffer software compositor before its costs and integration are measured.

**Option B — equivalent optimized representation.**
- Convert inclusive [L,R] to half-open [L,R+1) with **9-bit endpoints allowing256**. Empty L>R is handled before inversion. Two windows produce at most four internal boundary events; with0 and256 there are at most five constant-membership spans for a stable horizontal state. All six target masks share those geometric cuts; each span carries compact main/sub layer-disable masks plus color clip/math policy. Inversions/combinations do not create additional geometric edges. Midline writes and other non-window state changes can add segments and must not be forced into this bound.
- Cache the descriptor on R4300 per relevant change, or compute on RSP if measurement shows transport costs dominate. Compare both under identical output; existing RSP already computes W1 bounds, so moving all work to R4300 is not self-evidently better. Share descriptors across rows, not an unbounded lookup indexed by every register combination.
- For explicit fixed-color math, a 256-entry transformed palette per needed operation/brightness/eligibility class can amortize arithmetic; do not apply it to OBJ palettes0–3, a different winning layer or transparent-sub half exception. Changing fixed color every line can defeat this optimization. Preserve raw source colors and transform after semantic decisions.
- For general main/sub math, evaluate row buffers/vector RGB5 kernels versus RDP multi-pass candidates. RSP vector ALU could help parallel arithmetic, but loading both colors/metadata and spilling DMEM may dominate. RDP blending must be proven to match SNES per-channel integer rules and half exceptions; generic alpha blending is **not** an established substitute. A lossless no-math fast path is useful only when no subscreen display/clip/hires condition invalidates it.
- Do not move game timing, global event queues, large sparse lookup tables or per-write synchronization to RSP just because it is a coprocessor. Keep ownership simple: R4300 schedules/captures, RSP consumes bounded batches, RDP rasterizes supported exact paths. Changing that split requires evidence.

**Static sizes, not performance predictions:**
- Current 64-byte section ×224 lines =14,336 bytes (239=15,296), below one0x5000/20,480-byte queue before extra records. This suggests line-granular state can fit in storage; it says nothing about tile restarts, DMA latency, RSP/RDP commands or render time. Queue bounds and end/sentinel records must still be counted.
- Two RGB16 winner buffers for one256-pixel row require1,024 bytes before metadata; full256×224 two-screen RGB16 storage requires229,376 bytes before metadata/output. These are representation arithmetic only. RSP DMEM is4KiB and heavily occupied by existing tables/OAM/commands; “one row fits” cannot justify placing it there without a map/alias/lifetime audit. RSP IMEM size and linker map also constrain code growth.
- Current whole-VRAM copy is64KiB/frame and TLUT queue2KiB/frame; additional per-line palettes, intermediate-screen reads/writes or synchronization may be costlier than a small span descriptor.
- Compare R4300 PPU/state-building, RSP busy/wait, RDP completion pressure, DMA bytes/count, command count, section count, cache misses/invalidations and VI wait using identical workloads and correct image checks. Profiler sample percentages are not independent budgets or guaranteed headroom. Gothicvania's recorded11.51% VI wait is less margin than SRS/Nova2, but no simple subtraction predicts a repair's FPS.
- **Risks of optimization:** stale keys omitting brightness/TSW/logic; 8-bit256 overflow; off-by-one inclusivity; equality grouping across different resource epochs; tile-atomic clipping on partial windows; lost per-pixel winner eligibility; per-game fast-path assumptions; recomputation/DMA explosion on HDMA; branch pressure from many tiny spans; uncached/cached alias mistakes; overwriting buffers still in RSP/RDP use. Source inspection alone does not establish RDP completion safety for new multi-pass/readback usage.

### 5. Correctness + Gate-B regression plan after implementation

**TODO, not executed. Sequential decision gates, not a giant parallel work list.**

1. Land/qualify the original discriminator first. Then implement the smallest proven generic semantic correction on a separately authorized branch. Keep before/after exact binaries and matching ELF/maps.
2. Add independent deterministic truth cases for the touched contract: W1/W2 normal/inverted/disabled, OR/AND/XOR/XNOR, inclusive and empty/full edges, BG/OBJ and independent TMW/TSW. For a math change additionally test clip versus math prevention, each main source, OBJ palette eligibility, fixed versus opaque/transparent sub, add/sub/half including overflow/underflow/odd components, backdrop and brightness. Expected values come from a small independent model plus reference execution, not a copy of the optimized implementation.
3. Then add alternating-line/HDMA geometry and targeted resource-epoch tests. Reference-test both synthetic ROM directly on SNES emulation and its Sodium64-wrapped form; compare aligned pre-VI raw output/defined pixel probes. Avoid screenshots normalized in ways that hide errors.
4. Public source-based candidates already found: [undisbeliever/snes-test-roms window-mask-logic.asm](https://github.com/undisbeliever/snes-test-roms/blob/ac6ef8006809c0ff5dabc8ff137a4623967697fe/src/effects/window-mask-logic.asm) and [window-shapes-single.asm](https://github.com/undisbeliever/snes-test-roms/blob/ac6ef8006809c0ff5dabc8ff137a4623967697fe/src/effects/window-shapes-single.asm), both explicit Zlib source notices, commit `ac6ef8006809c0ff5dabc8ff137a4623967697fe`. Tree also contains HDMA textbox wipe, indirect patterns, CGRAM and timing tests. **Inspected, not built/run/qualified here.** Preserve notices, inspect dependencies/assets and pin toolchain before treating any as CI corpus; interactive demos need deterministic input/expected-output adaptation.
5. When private ROMs exist, run the exact SMW iris and relevant ALttP route with the bounded protocol above; establish new golden evidence only after reference agreement. Keep graphical regressions and operation-specific synthetic checks, not just “booted”.
6. Run existing build/smoke/APU regression gates and the **validated N64 ares configuration: R4300 recompiler ON, RSP recompiler OFF/interpreter ON**. PROFILING and current ares-profile workflow document the RSP-JIT lab pathology. Host wall-clock speed and virtual N64 throughput are not real-N64 FPS. Existing green CI is not a window/math oracle.
7. Reuse **Gothicvania, Space Rescue Squad and Nova the Squirrel2** exact versioned controls, same initialization/route/sample boundaries, frameskip0, APU21, audio enabled (encoded4), precision8, matching layer setting and original2-warmup/5-measured contract. Record runtime/workload/wrapped SHA, settings, decoder version and captures. A broader/new workload may supplement but not silently replace a control.
8. Screen out correctness/performance regressions autonomously in the lab. After enough validated changes, one real-N64 milestone bundle validates all three controls and new relevant PPU workload, with raw32KiB SRAM authorities and matching artifacts. No request for Iron to test every tiny change. Existing60/60×5 is the target; visual completeness and audio timing must also remain valid.
9. If correct rendering lowers cadence: **correctness → measure regression → profile correct implementation → optimize preserving semantics → recover cadence**. Keep the correct candidate and evidence; do not merge a performance regression as Gate-C complete, but do not revert to a knowingly incorrect shortcut as the final “solution”. Fast paths must pass equivalence tests. Do not use frameskip, APU underclock, disabled audio or changing precision as recovery.

### 6. Commercial-ROM laboratory: concrete recommendation and threat model

**PROPOSED architecture only. No asset, repository, token, key, secret, workflow, runner or infrastructure was created.**

**Recommendation:** keep all ordinary public CI asset-free. Put the commercial test **control plane in a separate private laboratory repository**, with its own pinned trusted workflow. It consumes an explicitly admitted Sodium64 source SHA, not arbitrary public PR code. For minimum initial GitHub-only setup, a private asset repository is workable with a narrowly scoped short-lived GitHub App contents-read token. Prefer fetching one pinned file via API into a private temporary directory over cloning its entire history. If choosing storage afresh for longer-term use, a private encrypted object with versioning/retention controls and OIDC-based single-object read avoids Git history and long-lived cross-repo asset credentials. The private workflow remains the controller in either design.

**Trust boundary:** the emulator/test program runs with the decrypted asset and can read it. Read-only credentials, encryption and a private repo do **not** stop malicious code already executing in that job from exfiltrating it through network, logs or output. Therefore only audited/pinned source, harness, build dependencies and actions enter the asset-bearing execution environment. No arbitrary SHA from a public issue/PR dispatch. Pinning gives identity, not trust by itself. If testing untrusted code is ever required, use stronger offline isolation and trusted output mediation; do not pass it cloud/asset secrets.

| Threat / actor | Design control | Residual limit |
| --- | --- | --- |
| Public fork/PR author | No private secrets in public repo; public PR checks use only original/open fixtures. Private lab admits reviewed exact SHAs; no pull_request_target checkout of attacker code, untrusted workflow_run artifact chain or unchecked reusable workflow input. | A malicious change accepted into trusted source can still read the ROM. Admission/code review is part of the boundary. |
| Compromised action/dependency | Actions and toolchains pinned to reviewed immutable digests/SHAs; build in an asset-free phase, isolate asset-bearing execution; no downloaded mutable scripts after asset mount. | Dependency/host compromise cannot be solved by a token scope alone. |
| Accidental logs/artifacts/cache | Private temp mount; controlled stdout/stderr; no shell xtrace, memory dumps or raw exception uploads; strict output allowlist and no caches in asset-bearing job. | Automatic secret masking does not recognize ROM bytes or all transformed credentials. |
| Stolen asset credential | Short-lived read-only token for exactly one asset repo, or OIDC single-object role bound to private workflow identity/environment/ref/audience. No public-write grant. | The permitted asset can be read during credential lifetime; revoke/rotate after exposure. |
| Runner persistence or cross-job leakage | Fresh ephemeral isolated runner/VM, no public-job reuse, bounded permissions, teardown of temporary volume. | Provider/admin access remains trusted; a persistent self-hosted host needs its own isolation/cleanup guarantees. |
| Output disguised as evidence | Trusted schema validator permits fixed-size counts/hashes/approved register fields only, rejects arbitrary strings/binaries/paths; no arbitrary attachments. Separate clean publication phase has no ROM credential. | A fully malicious test can encode information into arbitrary results; schema checks complement trusted source, not replace it. |
| Cancellation/crash | Cleanup trap plus guaranteed execution-environment destruction; publication only after normal verified cleanup/sanitization. | A shell “always” step alone cannot guarantee deletion after hard termination; unlink is not proof of physical media erasure. |

**Credential choices.**
- `GITHUB_TOKEN` should have minimum job permissions, typically contents:read for the private controller and none where unnecessary. It is scoped to the workflow repository and cannot simply read a different private asset repository. No public sodium64 write token is needed for test execution. [GitHub token scope](https://docs.github.com/en/actions/concepts/security/github_token).
- A GitHub App installation token restricted to asset repo contents:read is preferred for cross-repo automation; installation tokens expire after about one hour and can be revoked. App private key is itself sensitive: keep it in the private control plane, never pass it to the emulator; constrain minting/install scope. [GitHub App installation authentication](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation).
- A read-only deploy key is simpler and limited to one repo, but lacks automatic expiration and grants repository contents/history, not one ROM path. Do not enable write access; rotate and remove after suspected exposure. [Deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys).
- A fine-grained PAT limited to one asset repo, Contents:read and short expiration is an acceptable fallback, not a broad classic repo token or a token with workflow/admin rights. It remains tied to an account and its policy/lifecycle. [Personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).
- For object storage, use OIDC to avoid a long-lived cloud key: exact private repo/workflow identity, protected ref/environment and audience, one object's read/decrypt rights; no list/write/delete. Verify the actual current claims format before configuring trust rather than copying a legacy subject example. [OIDC](https://docs.github.com/en/actions/concepts/security/openid-connect).
- Extra client-side encryption can reduce exposure from an accidental repo visibility change, history/backups or asset-storage reader lacking the key. It does not protect plaintext from the executing test or log/artifact bugs after decryption. Keep key separate from encrypted blob; do not place a large base64 ROM in Actions secrets and call that secure storage.

**Required lifecycle, fail closed.**
1. Private controller selects reviewed exact emulator/test/toolchain SHA and ROM manifest; build executable without ROM. Fetch no raw commercial content in public jobs.
2. Asset-bearing phase receives minimal retrieval credential only for acquisition, removes/revokes it when practical, verifies exact source SHA256 before execution, then verifies normalized SHA if header removal is needed. Wrong asset fails before running. Hash is integrity/identity, **not evidence of legal rights**.
3. Run reference and Sodium64 in a constrained environment with no public publication credential, no general outbound network where enforceable, no crash/core/savestate upload. Redirect verbose/raw diagnostic output to temporary private storage; logging is deliberately bounded. Disable credential persistence in checkout and never embed tokens in command URLs or output.
4. Collect only necessary derived evidence into a **separate clean staging directory** using explicit names/schema/size limits. Exclude ROM, headerless copies, extracted resources, private snapshots, WRAM/VRAM/CGRAM/OAM dumps and raw debugger memory blocks. Commercial screenshots/audio/trace bytes may still contain protected expressive material: keep private and narrowly retain only what is necessary; derived does not automatically mean publishable.
5. Stop processes, delete source/normalized asset, wrappers, temporary reference assets, saves/dumps and credentials before any output upload; unmount/destroy the ephemeral asset volume. Normal publishing is contingent on cleanup and allowlist validation. Failed/cancelled jobs do not publish “all diagnostics”; destruction remains the fallback for incomplete cleanup.
6. Persist approved evidence privately with short retention and provenance; a separate **asset-free trusted publisher** can expose small reviewed summaries/hashes/test counts if desired. It should reconstruct a fixed schema, not forward arbitrary private job attachments/logs. No such public publishing is currently necessary or authorized in this audit.
7. At provisioning time, test the containment policy using an **original canary asset**, including failed/cancelled runs, wrappers/caches/log paths and allowlist rejection. Do not test leak-prevention by uploading commercial material.

**Repository-specific leak finding — SUPPORTED INTERPRETATION.** [rom-converter.py L18–32](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/rom-converter.py#L18-L32) copies the input guest ROM into the N64 .z64 at offset0x104000. A wrapped .z64 is therefore **commercial-bearing** even though its extension is not .sfc/.smc. The current [open-homebrew-profile.yml final upload](https://github.com/ironangelo/sodium64/blob/9441818dd8457a27bbd617a0f32c6d484550661f/.github/workflows/open-homebrew-profile.yml#L375-L385) publishes `workload/` and `profiles/` on always(). Its earlier step puts the source homebrew asset in workload/source. That is appropriate to audit separately under those assets' terms, but **must not be reused unchanged with a commercial ROM**. Ares profile uploads profiles/ broadly; raw memory dumps need schema review. Extension denylists and deleting only smw.sfc are insufficient. This is an architecture warning, not a current leak: **no commercial ROM was found/acquired here and no workflow was changed**.

**GitHub-hosted versus self-hosted.** A fresh private GitHub-hosted job is the simplest default for repeatable remote work; GitHub/provider is inside the trust model. A self-hosted runner on Iron's daily PC conflicts with the availability goal and adds persistent-machine exposure. A dedicated always-on isolated private runner can enable stricter network policy or hardware capture, but needs ephemeral single-job VM/volume, no public runner attachment and no unrelated credentials. A private local offline appliance minimizes cloud plaintext exposure but still needs an always-on host for autonomy. Do not promise that CI can establish real N64 cadence without hardware access.

**Official security references and their scope:** GitHub documents imperfect log redaction, immutable action pinning and persistent self-hosted risks in [Secure use](https://docs.github.com/en/actions/reference/security/secure-use). [Secrets usage](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets) describes default withholding from fork/Dependabot runs; this is not a safe substitute for avoiding privileged execution of untrusted code. [Dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) warns that PR/fork access can expose base-branch caches. The containment design above is this audit's recommendation, not a claim that GitHub automatically enforces it.

**Security, privacy, copyright are separate.** Security controls restrict who/code can access the bytes. Privacy requires private repo/storage, restricted collaborators, short retention and a trusted hosting provider. Copyright/licensing depends on asset provenance, jurisdiction, applicable permissions and what copying/hosting/extraction is authorized; personal possession and private visibility alone do not resolve it. No jurisdiction-specific legality determination is made here. GitHub also maintains a [DMCA takedown process](https://docs.github.com/en/site-policy/content-removal-policies/dmca-takedown-policy); it is not a license to host a game. If remote storage rights are unresolved, retain commercial asset locally/private offline and keep autonomous CI on original/open diagnostics. Inspecting public reverse-engineered source to identify register intent does not require copying game resources into this project.

### 7. Final disposition / next-window handoff

- **VALIDATED:** exact audited master `9441818dd8457a27bbd617a0f32c6d484550661f`, M3/Gate C active; A1/A2 source evidence and committed checkpoints read back successfully. Inherited hardware corpus60/60×5 remains authority; no new performance measurement.
- **SUPPORTED INTERPRETATION:** explicit OBJ/Mode7 windows missing; W2/boolean combination absent; BG masks OR main/sub; incomplete color arithmetic and flattened screen winners; precision8 coalesces line states; raw/palette/epoch limitations.
- **HYPOTHESIS:** H-OBJ is first narrow SMW-relevant target; H-SAMPLE is independent; H-COMP strongly fits public ALttP overlay intent. Actual scene causality/common cause remains **UNKNOWN**.
- **REJECTED:** W2 as necessary cause of inspected W1-only SMW iris; high CGWSEL main-clip omission as sole explanation for its0x12/0x22 variants; “HDMA absent”; delay-slot false positive; game hacks or setting changes as final fix.
- **TODO immediate:** original two-phase TMW-bit4 diagnostic described in §1; one question, then checkpoint/decision. Do not start the full compositor rewrite or commercial lab build in parallel.
- **BLOCKED:** attribution to Iron's exact SMW/ALttP scenes until legal private assets/route evidence are available. **Not blocked:** original deterministic masks/math tests, source audit, repair design and open-homebrew regression automation.
- **DEFERRED:** commercial infrastructure provisioning, actual ROM use, core changes, experiments, performance requalification and real-hardware milestone until separately authorized work. No new code is marked IMPLEMENTED.
- **Project direction:** public asset-free diagnostics + private optional game qualification + occasional batched real-hardware gates is compatible with Iron's autonomy goal. Commercial ROMs are not required in public GitHub; a native port's source is useful evidence, not a substitute for independently validating SNES hardware semantics.

## Gate-C focused audit 2026-09-21 — checkpoint 0: verified baseline

Scope: read-only runtime/code/workflows/PRs; only this continuity file is writable. Audit requested in five sequential batches (PR13, PR14, H-COMP architecture, exact math, direction). No implementation or experiment execution.

- **VALIDATED repository identity:** master `5b7134930a0ca859f6aa24e54102de116948e3ed`; starting continuity `723bced2bc6ca6ce72532946280bdc2e87e91883`. Read RESUME HERE and master ROAD_TO_1_0, ROADMAP, PROFILING, VALIDATION. M0/M1/M2 achieved, M3/Gate C active. Latest continuity agrees with repository identity; old pending entries are historical.
- PR14 **MERGED-CONSUMED**, exact candidate `8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec`, merge is current master; integrated ppu.S blob `1085f2a253e1522268c6ebb430086fd318ddfa6e` matches candidate. PR13 **OPEN / UNMERGED** at `phase4/gate-c-rsp-overlay-clean@84ecafad7cc3505d82f134b2672d9ed1146fedc0`.
- **VALIDATED CI metadata:** master Ares run35543805220 is success at attempt2; #13 exact-head Build35530189781 success. Overlay whole-frame35530604792, same-frame35533933132 and H-OBJ35530449506 jobs are success. WH mixed35541332012 and H-COMP BG35549088629 jobs are success. Green status alone does not independently establish the attached semantic claims; source/log review follows.
- **SUPPORTED INTERPRETATION — integration evidence boundary:** PR13's frozen source still derives from pre-PR14 master9441818..., and includes the H-OBJ repair in addition to overlay infrastructure. Source-disjoint does not mean the combined urgent-WH producer plus overlay consumer was dynamically qualified. Its previous virtual and future hardware evidence must name the exact integrated candidate; don't silently transfer timing claims to a future composition.
- No reopening of M2 or PR14 on generic precaution. No current reason to change runtime for the successful identical-source Ares rerun. Audit batch1 is next.

## Gate-C focused audit 2026-09-21 — batch1 checkpoint A: same-frame evidence narrowed

**Relevant finding persisted before further audit.** Reviewed actual log of [run35533933132 / semantic job106139474289](https://github.com/ironangelo/sodium64/actions/runs/35533933132), not only green status.

- **MEASURED in existing emulator log:** two guest IRQs both identify frame30; treatment capture is at guest frame37, phase0x33, final BGMODE1, final slot word0x91670E64 and an advanced framebuffer pointer.
- **SUPPORTED INTERPRETATION:** this proves guest transitions were requested and later renderer/publication progress with the regular slot restored. The logged assertions do **not** check a rendered Mode7 band or the framebuffer belonging to frame30. Capturing seven frames later cannot establish correct same-frame intermediate pixels or exclude a dropped/coalesced transition section.
- **SUPERSEDED narrow wording:** “same-frame switching validated” should mean exercised guest same-frame transitions plus post-transition recovery, not pixel-correct mixed-mode rendering. This does not invalidate the separate whole-frame regular→Mode7→regular slot observation.
- **TODO cheap discriminator before hardware:** capture the exact published mixed-mode frame, verify its section-mode sequence and distinct expected regular/Mode7/regular bands (original assets), then confirm following-frame recovery. A diagnostic that skips the middle band must fail even if the final slot is regular. No new run is executed in this audit.
- **No confirmed PR13 runtime defect yet.** Continue static loader/ABI audit; hardware DMA/bus/cadence authority remains open.

## Gate-C focused audit 2026-09-21 — batch1 COMPLETE: PR13 overlays

Audited [PR13](https://github.com/ironangelo/sodium64/pull/13), frozen head `84ecafad7cc3505d82f134b2672d9ed1146fedc0`, branch `phase4/gate-c-rsp-overlay-clean`, OPEN/UNMERGED. Four commits469beba→88103b7→ace6064→84ecafa; only defines.h, main.S, rsp_main.S, new rsp_mode7.S differ from its old base. It is an overlay + H-OBJ integration, not color math.

### Loader and ABI findings
- **SUPPORTED INTERPRETATION — fixed-slot design is coherent for current entries.** [rsp_main.S L1399–1413](https://github.com/ironangelo/sodium64/blob/84ecafad7cc3505d82f134b2672d9ed1146fedc0/src/rsp_main.S#L1399-L1413) uses a resident suffix loader, IMEM destination0x13A8 and length register0x3E7 (=1000 bytes). Claimed compiled slot [0x3A8,0x790) is aligned to8 and wholly inside4KiB. Fault stub branches out before the loader writes the slot; `dma_read/dma_wait` are also resident. It waits COP0_DMA_BUSY clear before reentering the loaded entry. No demonstrated self-overwrite of executing loader or return-to-old-slot instruction was found.
- Regular→Mode7 needs live t1 (BG enabled) and section bounds; DMA wait clobbers t0, not t1. Mode7→regular [rsp_mode7.S L504–512](https://github.com/ironangelo/sodium64/blob/84ecafad7cc3505d82f134b2672d9ed1146fedc0/src/rsp_mode7.S#L504-L512) saves the regular layer code t0 in v0 in the branch delay slot; resident loader restores t0 in its return branch delay slot. a0/a1/a2/ra are scratch at these dispatch entries, t3 layer index and vector state survive. The loader is a tail transition, **not a general nested function-call overlay ABI**.
- **VALIDATED source comparison:** regular/Mode7 prefix through draw_bg is text-identical, and resident suffix beginning draw_obj has identical non-comment instructions. Both .data sources have identical symbolic text. This alone does NOT prove assembled data bytes match: TILE_JUMPS/CACHE_RETS refer to variant-local labels. Only main's DMEM image is initially installed; its regular decode/cache entry addresses are safe because regular code is restored before those paths use them. OBJ cache return and shared routines are resident. Future math overlay must not use regular-only jump targets while another payload is resident.
- [main.S initialization](https://github.com/ironangelo/sodium64/blob/84ecafad7cc3505d82f134b2672d9ed1146fedc0/src/main.S#L160-L170) publishes immutable embedded slot sources after initial IMEM/DMEM upload. OVERLAY_MAIN_SRC0xE90/OVERLAY_MODE7_SRC0xE94 occupy declared DMEM gap below VEC_DATA0xF70. All audited SP DMA helpers synchronously wait; no new overlapping SP DMA producer was found. This reasoning depends on retaining that single blocking-owner contract.
- **HYPOTHESIS maintenance risk, not current defect:** fixed loader offsets/lengths are hardcoded; .align3 aligns but does not assert fixed slot length or common-symbol equality. Two near-duplicate source files can drift. Existing compiled evidence reports equal0xD00 active text,768B free, all variant differences inside slot, vs master0xFD8/40B free. This audit inspected source/logs, not freshly reassembled/disassembled artifact ZIPs. Preserve existing compiled-size evidence as inherited, not a new measurement.
- Cheap pre-hardware guard: compare compiled prefix/suffix bytes and every externally reached/common label; assert entry offsets, slot endpoint, resident loader outside slot, source alignment/extent, data-layout compatibility and4KiB ceilings. Check **reachable DMEM pointer targets**, not just first slot word or identical symbolic .data. Add such assertions in a future authorized proof/build batch; none added here.

### Existing dynamic evidence and limits
- Exact-head Build35530189781 succeeds. Whole-frame [35530604792](https://github.com/ironangelo/sodium64/actions/runs/35530604792) log observed slot words0x91670E64→0x1000024E→0x91670E64 with matching mode1→7→1 and continuing publication. Good evidence for demand load/restoration.
- Same-frame35533933132 is narrower, as checkpoint1A records: IRQs at frame30, readback frame37. **TODO** exact mixed-frame section+pixel-band capture; final restored word alone cannot reject a skipped middle render. No real-N64 DMA/bus timing/cadence proof.
- **SUPPORTED INTERPRETATION:** resident OBJ repair now clips W1 spans and restores section scissor (rsp_main.S L921–979, L1147–1159). It deliberately retains TMW|TSW and the existing W1 helper; W2/boolean logic and independent main/sub masks remain H-COMP dependencies. The stale “TODO implement windows for objects” comment at L886 is superseded by the implementation below it, not evidence that the repair is absent.
- Source-disjoint PR14 integration still needs an exact combined candidate check: more urgent sections can increase renderer dispatch/switch traffic without a textual conflict. Do not alter frozen PR13 in this audit.

### Decision
**Reasonable architecture for controlled Gate-C proof work; not yet a production base with proven hardware budget.** No concrete fatal loader/register-preservation defect found. Do not merge to obtain space. A math overlay is possible but needs explicit resident return point, register/vector/DMEM lifetime and code-size contract; the existing two-renderer fault stubs are not an automatic third-payload protocol. Cross-overlay calls from instructions being evicted would invalidate the current safety argument.

**Next audit batch:** PR14 urgency semantics and evidence scope. Future recommended #13 experiment: compiled-layout/entry guard plus exact transition-frame band readback; hardware later tests the exact combined runtime under regular/Mode7/urgent-WH activity, not a nominally similar ancestor.

## Gate-C focused audit 2026-09-21 — batch2 COMPLETE: PR14 integrated WH urgency

[PR14](https://github.com/ironangelo/sodium64/pull/14) is **MERGED-CONSUMED** at master `5b7134930a0ca859f6aa24e54102de116948e3ed`. Exact candidate/head `8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec`; ppu.S blob1085f2a... matches. One runtime file, +12/-4; no overlay or math change.

- **SUPPORTED INTERPRETATION — localized and conceptually appropriate for the demonstrated line-state contract:** [ppu.S L419–424](https://github.com/ironangelo/sodium64/blob/5b7134930a0ca859f6aa24e54102de116948e3ed/src/ppu.S#L419-L424) writes sect_status=0x0100; only WH0–WH3 changed-value branches L1469–1505 call it. Value comparison occurs before the delay-slot store, so same-value byte writes do not renew urgency. Repeated changed writes in one line coalesce into one pending section containing final state, not multiple immediate render calls. A later generic update_frame stores the dirty upper byte and does not restore a countdown, so it cannot cancel pending urgency.
- **SUPPORTED INTERPRETATION — adaptive state is coupled, despite unchanged generic code.** `run_line` L228–240 increments the global cooldown for **every** emitted section, including urgent ones. A burst of WH changes therefore increases the cooldown inherited by a later non-WH change in that frame. “Generic adaptive code unchanged” is true; “all non-WH effective timing unchanged” is not established and should not be assumed. Example: after N urgent snapshots the cooldown accumulator is16+N (before applicable frame reset); MEDIUM shifts the previous accumulator by2 to arm the next ordinary countdown. This is a concrete falsifiable interaction, not a demonstrated game regression.
- **TODO cheap targeted control:** burst of changed WH0 for a bounded set of lines, then keep WH stable and change one generic section register (e.g. BG scroll or CGADSUB). Record intended line, dirty/countdown/cooldown, actual section and effective row; compare with identical no-burst baseline. Include repeated identical WH writes as negative control. Keep this test scoped; do not reopen/undo #14 without a materially wrong observable.
- **Unnecessary work boundary:** changes to inactive W1/W2 or a value changed and restored within one line can still create a section; WH2/3 currently lack full renderer support. That is conservative state preservation, not a false hardware model. Do not “optimize” by checking only current enable bits: a window may become enabled before the next line. Any no-op suppression needs effective-state equivalence.
- **Resource bound:** writes cannot make more than one scheduled snapshot per run_line, so the four WH handlers do not imply four sections per line. Initial/final records must be counted; current0x5000 queue provides320×64-byte records, enough for the supported224/239-line single-snapshot schedule. OAM copy budget remains16; this PR does not make arbitrary raster OAM changes correct. No new queue overflow was found on this contract.
- **VALIDATED existing virtual evidence:** reviewed actual mixed job106159437587/run35541332012 output: completed queue has224 records,224 unique WH0 values exactly0..223 at precision8; separate budget capture reports fps_display60 with partial15/60 VI and15 guest frames. This supports retention and a completed virtual window, not60×5 hardware authority or a pixel-perfect reference iris.
- **Evidence scope:** WH0 is dynamically enumerated; analogous changed-value handlers cover WH1–3 by source inspection, not four independent224-state trials. Unique-state retention alone does not prove the hardware-correct visible-row phase, subscanline timing or complete window output. The snapshot-before-HDMA ordering is inherited and not altered by #14; don't label it wrong solely from order.
- **Important H-COMP implication:** WH urgency is NOT urgency for CGWSEL/CGADSUB/TM/TS/TMW/TSW/brightness/palette epochs. Those controls can be accidentally captured more promptly when WH also changes. A future strip compositor must not infer its color-state correctness from the224/224 WH test or globally treat every register as equivalent without evidence.

**Decision:** keep #14 closed for its stated changed-WH line-retention repair. No supported reason here to revert/reopen it. Preserve its narrow correctness claim and pending real-N64 cadence qualification. The burst→generic-state control and a visible-row alignment check are small, concrete follow-ups, not blockers to source-only H-COMP design.

Next audit batch: H-COMP strip/metadata representation and exact RDP constraints.


## Gate-C focused audit 2026-09-21 — batch 3A: metadata representation and memory contract

Audit baseline remains master `5b7134930a0ca859f6aa24e54102de116948e3ed`; code/runtime read-only. This is an immediate checkpoint, not a completed dynamic proof.

- **SUPPORTED INTERPRETATION — primitive-Z is a candidate encoded channel, not a literal layer-ID surface.** At ares `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`, `ares/n64/vulkan/parallel-rdp/parallel-rdp/shaders/memory_interfacing.h:558–568` compresses Z before write; `store_vram_depth:260–269` writes `(compressed_depth << 2) | (compressed_dz >> 2)`, with other DZ bits in hidden RDRAM. `rdp_renderer.cpp:3508` masks PrimDepth to 15 bits and shifts it. A future implementation must choose a small collision-free codebook through the complete encoding, fix/mask DZ, and decode visible bits. Never depend on reading hidden bits. Source support for transparent rejection does NOT prove the metadata values have the assumed representation. **REJECTED:** treating the raw 16-bit Z readback as the PrimDepth/layer number without encoding proof.
- **SUPPORTED INTERPRETATION — depth pitch follows color-image width.** The same ares source `init_tile:286–301` indexes both surfaces using `fb_width*y+x`. Sodium64 master `src/rsp_main.S:rdp_frame` uses SetColorImage word `0x3F10011700000000`: width-minus-one 0x117, i.e. 280 pixels, not 256. With this command path, eight rows of each 16-bit scratch surface require 4,480 bytes (two = 8,960), before other storage. A separately programmed 256-wide target is possible but requires explicit target/coordinate/scissor changes; depth associated with the 280-wide main target still has that pitch. **Architectural risk:** global screen Y into an eight-row Z allocation overruns it unless the depth base/coordinates are adjusted for every strip, including the existing framebuffer offsets. Alignment and guard regions must be part of the proof.
- **OPEN QUESTION — subscreen validity is separate from RGB.** `memory_interfacing.h:550–556` writes framebuffer alpha from coverage. An RGBA16 framebuffer's low bit cannot simply be assumed to preserve texture opacity. Opaque black must remain distinguishable from a transparent hole; non-black color-keying is incorrect. An explicit sub-valid tag or a proven coverage-to-validity rule is required.
- **Architectural risk — a new RDP-to-RSP/CPU dependency needs a real completion contract.** Existing `rdp_send` waits on command-busy; this is not by itself proof that all pixel writes have reached RDRAM for a subsequent SP DMA/readback. RSP completion also does not establish RDP completion. Future composition requires an ordered DP completion fence and the appropriate cache ownership transitions. This is a requirement for the proposed new pipeline, not evidence of an existing rendering race.
- **Direction adjustment / TODO:** before implementing exact math, run a tiny exact-command-path metadata/readback proof: explicit clears; two distinct main tags; opaque black; transparent holes; overlapping draws; two consecutive reused strips; first/last strip addresses and canaries; decoded Z words plus pixels; DP fence ordering. Include the texture-rectangle path first, then Mode7 triangle coverage separately before claiming Mode7 support. No experiment was implemented or executed in this audit.
- **LAB LIMITATION:** ares source describes a reference implementation and helps derive falsifiers; neither its Vulkan coherency nor a virtual result establishes real-N64 DMA, bus, cache, or cadence behavior. Encoding and command ordering must be checked against the actual output and later hardware.

Primary source inspected: [ares pinned memory_interfacing.h](https://github.com/ares-emulator/ares/blob/17813a3ccda21ab9bd45f09bfc2f91196dbf50ff/ares/n64/vulkan/parallel-rdp/parallel-rdp/shaders/memory_interfacing.h). Batch 3 remains in progress; batches 0–2 completed.


## Gate-C focused audit 2026-09-21 — batch 3B: operand-loss path and brightness prerequisite

- **SUPPORTED INTERPRETATION / invalidation risk for future work:** exact arithmetic over today's rendered colors is not sufficient. Master `src/ppu.S:update_fill/set_fill:427–455` and `update_dpal:509–532` multiply the original CGRAM/fixed colors by brightness before packing N64 RGB5551. The section payload includes converted MAIN_COLOR/SUB_COLOR, not original colors plus a brightness epoch. By contrast ares's pinned SNES `ppu-performance/dac.cpp:render/pixel/blend` attaches brightness after the color-math result. Rounding/clamping and brightness do not generally commute. **REJECTED:** advertising bit-exact general color math while only combining pre-dimmed surfaces. Full-brightness-only arithmetic is a useful explicitly scoped proof, not the final contract.
- **TODO — smallest generic contract:** preserve raw RGB5 operands (palette, fixed color, CGRAM0) and the applicable brightness/blank state until composition; apply brightness afterward using an explicitly validated conversion. Audit palette changes separately: the present palette queue is produced per frame by `update_dpal`, while section state is copied by `section_init`; strips do not automatically restore missing palette epochs. Do not silently broaden this into a full raster-palette rewrite in the first batch.
- **VALIDATED behavior + SUPPORTED INTERPRETATION of mechanism:** H-COMP BG run 35549088629/job 106180372990 has distinct raw/add/half CGADSUB states with identical captured framebuffer hashes `c2d096fc30454282840b9fc2669e8ff10c185b1656a0ab6c154f8da77fcefb6b` and center pixel 16385. Its same-BG-on-both-screens setup demonstrates ignored arithmetic in that fixture; by itself it is not a proof that independently colored operands were retained or lost. The static path below establishes the architectural operand-loss mechanism.
- **Code path at audited master:** register state → `src/ppu.S:section_init:391–401` copies SECTION_SIZE from `bghofs` (payload defined at 141–172) → RDRAM SECTION_QUEUE → `src/rsp_main.S:next_section:224–234` DMA to BGHOFS and section bounds → backdrop fill at 382–457 chooses/swaps MAIN_COLOR/SUB_COLOR using a window shortcut rather than arithmetic → `469–478` merges TM/TS, removes shared layers from the lower pass → `next_layer:480–497` draws both passes into the same framebuffer with a hand-ordered LAYER_CHART. A main pixel overwrites the lower pixel; there is no surviving independent sub operand at a later math stage. Screen-order UI swapping is a workaround, not a composition model.
- **SUPPORTED INTERPRETATION — separating targets also requires separating masks:** `draw_bg:620–642` combines TMW|TSW, so merely drawing the existing command stream twice is still wrong when main/sub window enables differ. `calc_windows:1503–1542` only implements W1; W2/combination logic is omitted. The existing backdrop shortcut is not the SNES color-window policy. These limitations must remain visible in scope and tests; PR #14 preserves WH state but does not supply these semantics.
- **Architectural risk — metadata records the renderer's winner, not automatically the SNES winner.** `next_layer:482–483` explicitly documents approximate priority and an OBJ case it cannot represent. With Z compare disabled, primitive-Z stamps the last accepted draw. It cannot repair the draw order or OBJ tie-breaking. Preserve main winner source/eligibility and sub presence, while retaining a separate priority correctness obligation; do not claim a new Z channel proves BG/OBJ ordering.

Next: complete the bounded strip alternatives/ownership contract; no runtime changes or experiment execution. Source reference: [pinned SNES DAC](https://github.com/ares-emulator/ares/blob/17813a3ccda21ab9bd45f09bfc2f91196dbf50ff/ares/sfc/ppu-performance/dac.cpp).


## Gate-C focused audit 2026-09-21 — batch 3 COMPLETE: bounded strip architecture

**Conclusion: SUPPORTED INTERPRETATION, conditional direction.** Retain the existing RSP tile/OBJ/Mode7 rasterization and RDP drawing, render independent screen winners, then add a bounded composition stage. Small strips solve the demonstrated RDRAM capacity problem; primitive-Z remains **HYPOTHESIS** until exact-command dynamic proof. Neither a second software renderer nor a general render-graph framework is justified.

### Minimal data and ordering contract

1. R4300 preserves applicable raw palette/fixed/backdrop colors, brightness, CGWSEL/CGADSUB, TM/TS and independent TMW/TSW plus window state; color changes and section boundaries are explicit epochs.
2. For each section/strip intersection, draw the sub winner to scratch with TS/TSW; initialize empty sub to fixed color in ordinary low-resolution mode, but retain an explicit “no real sub winner” classification. Draw main to the existing output region with TM/TMW, initializing backdrop to CGRAM0 with its own source class. Both operands must survive until composition. Do not reuse a strip across a state boundary without per-row state or splitting.
3. Main metadata can be the actual source class (BG1–4, OBJ eligible/ineligible, backdrop), or simply precomputed math eligibility when CGADSUB is constant over that epoch. OBJ palettes 0–3 never enable math; palettes 4–7 follow CGADSUB bit4, as pinned ares `object.cpp:127–129` / `io.cpp:601–607` show. Do not tag every OBJ identically. Main clipping to black does not turn its source into backdrop.
4. Color-window clipping and math permission are independent of layer-window masking. Evaluate W1/W2 inversion/OR/AND/XOR/XNOR and inside/outside policies at state changes/row spans. Pixel source eligibility/sub-validity still varies with texture transparency inside those spans. A fixed number of SNES window edges does not imply a constant winner throughout each span.
5. At a real completion boundary, consume raw main, raw sub, main eligibility and sub-validity; select fixed versus sub, suppress half under the oracle conditions, do exact RGB5 math, then brightness and N64 packing. Preserve forced blank and no-math behavior. Hires/pseudo-hires and direct-color need explicit scope/qualification; the ordinary low-resolution fallback rules cannot silently stand in for them.

### Primitive-Z contract and falsifiers

- Current `rdp_init` OtherModes is `0x2F0088FF00040001`: the depth compare/update and primitive-source controls needed for stamping are not already enabled. The candidate would deliberately use primitive depth, Z-update, compare disabled, and preserve the existing alpha rejection. This is a proposed state change, not implemented behavior.
- Pinned ares `shading.h:320–358` rejects failing alpha before a pixel reaches depth write; `depth_test.h` permits a pass without Z comparison; `memory_interfacing.h` conditionally writes Z after coverage/depth processing. This supports feasibility, not dynamic validation of Sodium64's TLUT/combiner/texture rectangle commands. Non-Z triangle commands used by Mode7 must be tested separately.
- `z_encode.h:z_compress` explicitly loses precision. Reserve distinct encoded values for clear/backdrop and every required tag, with fixed DZ and a decoder over visible bits. A transparent foreground must leave the previous tag unchanged; an opaque non-math foreground must overwrite an eligible background tag. A zero/black RGB value is not transparency.
- Z has the color target's width. Specify absolute color/depth addresses and resulting first/last byte of every draw, including x+12, framebuffer underflow offset, overscan/FB_OFFSET and short final strip. Avoid creating an out-of-range depth base by an unexamined global-Y bias. Ares's `index ^ 1` is its host word-swizzle convention, not a command to byte-swap native N64 memory. Capture native bytes and decoded big-endian 16-bit words; validate SP load order and RGB5551↔SNES BGR555 packing explicitly.
- Scratch clears are semantic operations: reset sub-validity and main backdrop tags before every reuse, disable unintended depth/alpha effects for clear, restore drawing modes afterward. Reused strip B must not inherit strip A's visible tags. Test overlapping draws and edges to catch coverage/RMW hazards.

### Ownership, synchronization, and memory

RDP command consumption, RDP pixel completion, SP DMA completion, and CPU cache visibility are separate events. Existing blocking SP DMA helpers establish only SP-transfer completion. Keep command storage alive until consumed; do not overwrite DMEM RDP command buffers with a composition chunk prematurely. RDRAM scratch is not extra RSP DMEM: the latter is only 4 KiB and already houses tile tables, VRAM dirty state, OAM, section state, commands and constants. Use a small proven dead DMEM range or spill/restore it with a declared ABI; an 8-row RGB16 strip alone exceeds DMEM.

A DP completion protocol must use a fresh completion generation/acknowledgement and avoid waiting for an interrupt whose owner cannot run. Account for any existing DP handler before introducing chunk submissions. The SDK documents FullSync as the end-of-frame/display-list completion signal; **do not mechanically insert that macro into the middle of the existing frame loop and assume the surrounding interrupt/VI contract is safe**. An explicit chunk boundary or equivalent proven drained-pipeline handshake is needed. PipeSync is for RDP state ordering, not a CPU cache invalidation. If CPU touches scratch, define cached versus uncached aliases, writeback before RDP/SP reads, invalidation after RDP/SP writes, and avoid stale dirty cache lines later overwriting DMA output. RSP-only composition avoids CPU cache reads but not DP/SP ordering.

Primary manuals: [DP completion signal](https://ultra64.ca/files/documentation/online-manuals/man/n64man/gdp/gDPFullSync.html), [RDP synchronization](https://ultra64.ca/files/documentation/online-manuals/man/pro-man/pro12/12-02.html), [RDP formats](https://ultra64.ca/files/documentation/online-manuals/man/pro-man/pro15/15-05.html). These corroborate completion/state-order distinctions, eight-byte image alignment, coverage storage and compressed Z. Primitive depth itself does not require a PipeSync for each update; batch broader state changes rather than adding a fence per primitive.

| Candidate | Evidence / derived incremental storage for 8 rows at pitch 280 | Unknown / cheapest falsifier |
|---|---|---|
| **Correctness-first candidate:** sub RGB16 + separate main and sub tag surfaces, each 16-bit | 3 × 4,480 = **13,440 B**, plus small state/guards; preserves independent facts without assuming framebuffer alpha survives. Reuse current drawing, select the relevant depth target for each screen pass. | All three surfaces still depend on proven tag writes and correct clear/order. Run tiny opaque/transparent overlap + reused-strip proof. Commands include target/mode changes, clears, depth stamps and completion; no FPS estimate. |
| **Optimized candidate:** sub RGB16 + one reused Z strip | **8,960 B**, plus small state/guards. Render sub, finish DP, convert sub tag to an explicit presence bit in the scratch pixel's otherwise unused RGB5551 low bit; reuse Z for main eligibility, then compose. Once RDP has finished and the kernel owns scratch, that bit is software metadata, not assumed RDP alpha. | Extra read/modify/write and fence may outweigh saved 4,480 B. Before modifying the bit, capture whether the simple clear/opaque draw path already gives a reliable presence bit; if proven, omit conversion only within that contract. Fail on opaque black/hole or subsequent RDP sampling that treats the metadata as ordinary alpha. |
| **Fallback if Z proof fails:** dedicated color metadata draw pass using the existing geometry/texture-alpha rejection | One 16-bit tag target per simultaneously needed fact; small strips remain capacity-plausible. Explicit RGB codes avoid Z compression. | Repeating geometry costs commands, texture work and synchronization; combiner must output constant code while preserving texture alpha. No new CPU tile renderer. Falsifier is differing mask coverage/pixel ownership between color and tag passes. |
| **CPU composition as initial semantic carrier** | Same operand/tag storage; no new RSP kernel required. CPU uses already rendered pixels, not software BG/OBJ rasterization. | Bus/cache stalls and lost overlap can be expensive. Small bounded output proof first, then profile exact implementation before choosing it for production. |
| **Full-frame sub + compact 8-bit metadata** | Earlier capacity audit derived 172,032 B at 256×224, leaving ~57.7 KiB before additional code/data; not the rejected two-RGB16 design. | More persistent memory and encoding work; an RDP Z target is 16-bit and cannot be counted as an 8-bit mask without conversion. Keep as fallback, not another parallel project. |

Two extra full RGB16 active surfaces remain **REJECTED as capacity-unsafe**: the recorded integrated-artifact gap is 229,760 B and those two alone need 229,376 B. Triple presentation buffers are not free scratch.

### Performance boundaries, without invented timing

- Per state change/section: decode policy and eligibility, cache window spans and codebook constants; split only at actual relevant epochs.
- Per strip: select/clear scratch, retain correct texture-coordinate phase, synchronize producer→consumer, DMA contiguous chunks; protect final short strip and section intersections.
- Per tile/span: reuse decode caches and existing rasterization; stamp a constant main eligibility/source code per appropriate draw. An additional SetPrimDepth is one 64-bit command when its tag changes; no proof yet of how often this is needed on representative scenes.
- Per pixel: read independent winners, select operand/half policy and exact arithmetic. This unavoidable pixel-dependent work need not recompute windows, decode tiles, or perform general layer traversal.
- For a simple composition pass reading three 16-bit inputs and writing one 16-bit output, active 256×224 traffic is **458,752 B/frame** before RDP writes, clears, padding, sub-valid conversion or spills. This is a byte-count model, not measured bandwidth or FPS.
- More strips reduce scratch but increase command/fence/overlay overhead. A tall section can be divided, but a strip cannot merge differing state epochs accidentally; with PR #14's 224 sections, per-section setup may dominate. Compare fixed small heights only after semantic proof, using the same output oracle.
- Lossless no-math fast paths are worth keeping only when clip, separate screen visibility, brightness and hires conditions establish equivalence. Do not reintroduce TM/TS flattening merely because CGADSUB happens to be zero.

**Next batch:** audit exact math/oracle and kernel placement. No architecture is selected as production-fast by these storage estimates.


## Gate-C focused audit 2026-09-21 — batch 4A: oracle scope and RDP rejection boundary

Immediate checkpoint before choosing a kernel location.

- **SUPPORTED INTERPRETATION — oracle cross-check:** directly inspected both pinned ares `ares/sfc/ppu-performance/dac.cpp` and accurate `ares/sfc/ppu/dac.cpp`. The packed ADD/SUB/HALF formulas agree. Accurate `DAC::above` explicitly selects fixed color and disables half when blendMode requests sub but sub is transparent; color-window main clipping suppresses half. This strengthens the ordinary low-resolution contract, but two implementations in one project are not independent hardware evidence. Accurate DAC also documents unconfirmed hardware initialization of the first hires pixel; do not extend this proof to every hires boundary.
- **Important narrowing / SUPERSEDED overbroad interpretation:** the earlier 32×32 expanded-8-bit HALF sanity check rejects that algebraic surrogate; it is not exhaustive proof that every possible RDP path is incapable of exact HALF. At the same pinned ares revision, texture decoding `texture.h:77–78` expands RGB5 by bit replication, whereas framebuffer memory input `memory_interfacing.h:decode_memory_color` supplies RGBA5551 components with low three bits zero. The blender also quantizes weights and uses its own normalization/rounding (`blender.h`). An experiment that expands BOTH inputs as textures does not describe texture-plus-framebuffer blending. **REJECTED remains:** unproven generic 50% blending as a finished solution, and special Blender ADD as a general saturated ADD. **UNKNOWN remains:** whether a particular explicitly encoded RDP command sequence can exactly implement a useful restricted operation.
- **Concrete falsifier:** specify texture or memory origin of each operand, muxes, cycle type, alpha/coverage modes, dither, signed intermediate/clamp and final RGB5 packing; compare all channel pairs and adversarial packed colors. If any one expected result differs, reject that sequence only. Do not launch a broad search for clever RDP algebra before the operand/tag proof.
- **LAB LIMITATION — “bit exact” must name its domain.** Exact RGB5 math can be checked before brightness/host display conversion. Pinned `ares/sfc/ppu/color.cpp` uses a separate luma/output mapping (including an analog-inspired dim-level behavior and optional display transform). Screenshot RGB after that mapping is not a neutral arithmetic oracle. Compare raw SNES RGB5 plus brightness first; validate Sodium64's final RGB5551 conversion separately with declared settings.

Sources: [accurate DAC](https://github.com/ares-emulator/ares/blob/17813a3ccda21ab9bd45f09bfc2f91196dbf50ff/ares/sfc/ppu/dac.cpp), [RDP texture decode](https://github.com/ares-emulator/ares/blob/17813a3ccda21ab9bd45f09bfc2f91196dbf50ff/ares/n64/vulkan/parallel-rdp/parallel-rdp/shaders/texture.h), [RDP memory input](https://github.com/ares-emulator/ares/blob/17813a3ccda21ab9bd45f09bfc2f91196dbf50ff/ares/n64/vulkan/parallel-rdp/parallel-rdp/shaders/memory_interfacing.h). No new arithmetic experiment was run.


## Gate-C focused audit 2026-09-21 — batch 4 COMPLETE: exact math and kernel placement

### Oracle and operation order

**SUPPORTED INTERPRETATION:** the pinned accurate/performance SNES DAC implementations agree on these ordinary low-resolution per-channel operations, for raw five-bit channels `a,b in [0,31]`:

| Operation | Required channel result | Trap |
|---|---|---|
| ADD | min(31, a+b) | RDP special Blender ADD lacks the required general saturation. |
| SUB | max(0, a-b) | Signed wrap is not clamp-to-zero. |
| HALF-ADD | floor((a+b)/2) | Do not clamp the sum to 31 before halving; 31+31 must yield 31, not 15. |
| HALF-SUB | floor(max(0,a-b)/2) | Clamp negative differences before unsigned packing; mask channel boundaries before packed shifts. |

The oracle's packed constants isolate channel carry/borrow; a scalar/vector implementation must preserve that property. Simply adding packed RGB5551 words permits inter-channel carries and includes coverage/alpha in the arithmetic. It is possible to remove the low metadata bit and retain N64's reversed channel order internally because the same operation applies independently to every channel; a per-pixel R/B swap is not intrinsically required. This is an optimization candidate, with conversion tests required at input/output boundaries.

Policy precedes arithmetic: apply main color-window black clipping; stop math if color-window math permission is false or CGADSUB disables the actual main winner; choose fixed color directly when CGWSEL requests fixed; otherwise select real sub winner or fixed fallback. Half is enabled only when requested and main is not clipped, and is additionally suppressed for a transparent/backdrop sub fallback when sub mode was requested. Direct fixed-color mode can still halve. Main backdrop uses CGRAM0 and CGADSUB bit5; a real opaque-black sub is not the transparent fallback. OBJ math depends on palette class as recorded in batch 3. Apply brightness afterward. Preserve forced blank.

**Proof proposal, not executed:** 1,024 pairs for each of four single-channel operations; asymmetric mixed-channel colors that expose cross-channel carry/borrow, R/B reversal and alpha-bit leakage; endpoint/equal/underflow/saturation cases; then a separate policy matrix for source enable, main clip, math window, fixed/sub, sub-validity, half and blank. An exhaustive channel table establishes channel arithmetic, not complete SNES pixel policy or all packed RGB pairs. Compare compiled kernel output with raw RGB5 oracle and policy state, not a display-transformed screenshot.

### Placement alternatives and bounded discriminators

| Location | Concrete constraints / supporting evidence | Minimum next discriminator after operand proof |
|---|---|---|
| **R4300 scalar post-pass** | Can express the oracle with ordinary integer operations; no dependence on PR #13 or spare RSP IMEM. Reuses RDP-rendered pixels and does not duplicate tile/OBJ rendering. Costs CPU time, memory ownership transitions and possibly frame overlap. | Bounded exact strip output under fixed inputs, then existing profiler on the correct path. If correct but slow, retain its oracle and move only the hot arithmetic/transfer stage. |
| **RSP scalar or vector kernel** | Parallel lanes and contiguous SP DMA are useful possibilities. Packed scalar formulas require safe intermediate widths; vector VADD/VSUB saturation/carry is not automatically RGB5 saturation. Unpacking channels into lanes or explicit masks/carry logic needs instruction, register and DMEM accounting. Rendering constants/live vectors and DMA helpers form an ABI, not free scratch. | Compile the complete callable kernel including loads, packing, policy, DMA, entry/exit and spills; inspect text/DMEM map; compare actual output with the oracle. Instruction count for arithmetic alone is not total footprint or throughput. |
| **RDP-only exact sequence** | Existing draw pipeline avoids an extra processor readback only if it can express arithmetic AND source/policy selection exactly. Texture and framebuffer inputs, signed combiner clamp, blender normalization, coverage and dithering differ. Blender ADD/naive HALF failures do not prove every combiner sequence impossible. | One fully specified sequence for one operation, tested against all channel pairs through actual commands. Stop that candidate on a mismatch; do not expand into a general shader-search project. |
| **RDP winners + RSP/CPU exact math** | Cleanest current division of responsibility: keep rasterization/cache/priority machinery, move only resolved operands and compact policy to math. Small strips bound RDRAM; transfer/sync cost remains real. | First metadata/ownership proof, then exact output, then matched profiling. Choice between CPU and RSP is deferred to compiled size and measured cost. |

**IMEM decision:** master monolithic text is 4,056 B, only 40 B / ten 32-bit instruction words unallocated. There is no compiled complete new kernel proving it fits. Conversely, an impossibility theorem cannot be inferred from “40 B free”: a small operation, existing helper reuse or controlled refactor can change the bound. Treat a general drop-in kernel as **UNPROVEN**, not “certainly fits” or “PR #13 mathematically required.”

PR #13's 3,328 B resident+active image leaves 768 B; the overlay slot itself is 1,000 B. Those are different budgets. A complete math kernel might fit appended resident space, or might be a third slot payload, but neither fit is measured. A third payload must enter from resident code at a completed draw boundary, keep its loader/continuation outside the overwritten range, preserve the renderer state needed to resume, and restore the regular/Mode7 slot before dispatching an entry that needs it. The current two fault stubs alone do not define an arbitrary nested-call math-overlay ABI.

**Derived conditional cost:** if a math overlay replaces the entire 1,000 B slot and each eight-row strip requires loading math then restoring a renderer, 224 lines / 8 = 28 strips imply 56,000 B/frame of slot-load traffic, before extra section/mode transitions. This is not measured performance, and may not apply to a resident kernel, retained math phase, different chunking or partial slot design. With many one-line state sections, naive switching may be much worse. Do not consume overlays as an automatic speed win.

A separate CPU-dispatched microcode task would also avoid a merge dependency on #13, but full code/state reload and task ownership could be more intrusive; not the recommended first proof. CPU arithmetic can establish exact output without that detour. **Conclusion on dependency:** reuse #13 if a measured complete kernel footprint and ownership design justify it; do not merge it merely to make room for an unmeasured kernel.

### Cheap representation optimizations, not architecture commitments

- Policy/window spans per state epoch can select no-math/add/sub/half routines once; per-pixel tags still choose eligibility and transparent fallback.
- A channel lookup for one operation costs 32×32 = 1,024 bytes at one byte/result; all four cost 4,096 bytes, the entire RSP DMEM before any existing state. Per-channel CPU tables are a possible control, not a free vector gather. Avoid a full RGB-pair table.
- Brightness mapping can be cached per active level rather than recomputed with a general multiply at every pixel, but preserve the chosen output quantization and raster epoch. Raw RGB5 math proof remains separate from display conversion.
- Reuse decoded textures and independent-screen draw traversal. Do not optimize away source identity, sub-validity, window permission or unclamped HALF-ADD intermediates.
- Measure DMA bytes/waits, DP drain time, CPU stalls, overlay faults and section/strip counts on the correct implementation. A faster standalone math loop can lose overall through extra synchronization.

**Status:** batches 0–4 complete; all kernel location/size/performance results above are source constraints or proposed experiments, not implementations or newly measured runs. Next: Gate-C direction and final bounded experiment order.


## Gate-C focused audit 2026-09-21 — batch 5 COMPLETE / final checkpoint

### Canonical state rechecked at close

- **M3 / Gate C ACTIVE**; M0/M1/M2 achieved. Audited and re-read remote master: **`5b7134930a0ca859f6aa24e54102de116948e3ed`**.
- **PR #13 OPEN / UNMERGED**, `phase4/gate-c-rsp-overlay-clean@84ecafad7cc3505d82f134b2672d9ed1146fedc0`; API base remains `9441818dd8457a27bbd617a0f32c6d484550661f`. Source package includes the H-OBJ repair as well as overlays. A future combined #13 + integrated #14 build needs its own identity and evidence; this audit did not create it.
- **PR #14 MERGED-CONSUMED**; technical head `8be82f5fb3a02f6390d5dfbaf3d94addc8f4e1ec`, merge is current master. Changed-WH urgency is integrated.
- Master Build/Validate **35543805198 success, attempt1**, master Ares **35543805220 success, attempt2**, both exact master SHA; rechecked at close. Attempt2 success does not erase the recorded attempt1 lab collapse. No new run was dispatched.
- Road/roadmap agree on achieved Gate B and active Gate C. **Documentation lag:** the end of `PROFILING.md` still says the next target is corpus discovery/ranking; ROAD_TO_1_0/ROADMAP and recorded three-workload hardware closure supersede that old next-step prose. It is not authority to resume automatic CPU/APU optimization. Runtime/docs outside this file were left unchanged.

### Executive technical decision

**H-COMP is a real Gate-C driver.** The BG diagnostic and renderer source establish a generic missing color-composition feature, without requiring commercial assets. It does not establish that every historical SMW/ALttP symptom has this cause, nor does fixing H-COMP close Gate C. Continue toward independent main/sub winners and exact color policy using the current tile/RDP architecture.

Change the next-step emphasis from “write an exact vector kernel” to **“prove the smallest operand/tag/ownership contract through the actual RDP path.”** Arithmetic is independently specifiable; the more fragile assumption is that the proposed metadata survives alpha/coverage/encoding/stride and can be safely consumed. Keep CPU as an admissible bounded semantic carrier until actual RSP footprint and measured cost justify moving the kernel. Do not start a general compositor framework, new software rasterizer, broad RDP algebra search or extra commercial-ROM infrastructure for this proof.

### Conclusions on the two PRs and H-COMP

- **PR #13:** fixed-slot demand loading is reasonable for further isolated Gate-C work. Source review found no demonstrated executing-code overwrite or missing SP-DMA completion in its current tail-dispatch ABI. Existing compiled layout evidence and whole-frame virtual behavior support feasibility. **Qualification still missing:** actual mixed-frame pixel bands (the current same-frame test captures frame37 after IRQs in frame30), a combined candidate with #14, and real-N64 DMA/bus/cadence. Do not declare it hardware-qualified or merge it just to unlock hypothetical kernel space. A third math overlay requires a new explicit entry/exit/DMEM contract.
- **PR #14:** keep closed for its narrow demonstrated WH change-retention repair. The localized changed-value path is conceptually appropriate for that defect. A concrete residual coupling is that urgent sections advance the shared adaptive cooldown, potentially delaying a later unrelated generic register change; measure that with the specific burst→generic control if future color-state work depends on it. Also distinguish retained state count from visible-line alignment. Neither uncertainty is evidence that the fix should be reverted.
- **H-COMP strip proposal:** retain as a bounded candidate, with **raw operands + separate screen masks + main eligibility + sub-validity + post-math brightness + explicit ownership**. Primitive-Z is an encoded candidate channel, not a validated one; framebuffer alpha is not automatically opacity; last-draw tagging is not a priority fix. Small scratch remains feasible despite the correction from 256 to the existing 280-pixel pitch. Exact kernel placement/performance remains **UNKNOWN**.

### Three most important risks

1. **Silent metadata corruption or unsafe scratch reuse:** compressed Z code collisions/DZ contamination, coverage mistaken for transparency, wrong 280-wide/global-Y addressing, or SP/CPU reads before RDP writes finish. Any one can make a mathematically perfect kernel wrong or corrupt memory.
2. **Incomplete semantic inputs:** pre-applied brightness, flattened/OR-combined masks, missing palette/color epochs, ineligible OBJ classes and approximate priority. A good ADD test at full brightness can hide all of these. Record explicit scope instead of generalizing a synthetic pass.
3. **Integration cost and false performance confidence:** fine WH sections can amplify clears, fences, repeated draw work and overlay faults; virtual 60/60 and a 768-byte IMEM margin do not prove real-N64 cadence or complete-kernel fit. The actual #13+#14 composition has not been qualified as one candidate.

### Three next experiments, in dependency order (not parallel workstreams)

**E1 — immediate, highest information gain: exact RDP tag/sub-validity/readback proof.**

Question: can the existing draw-command path produce trustworthy winner/presence tags in bounded scratch, ready for a consumer after an explicit completion handshake?

Use the existing diagnostic/capture infrastructure and a tiny original tile pattern; no commercial ROM or Iron-at-PC dependency. Keep SNES math out of this test. Freeze command words, codebook/DZ, OtherModes, combiner, TLUT, target width, physical addresses, scissor and completion protocol. Compare a control with depth stamping disabled against the one controlled stamping change. Include:
- two visibly different overlapping source tags, an eligible background covered by a noneligible foreground;
- transparent foreground holes versus opaque black, plus clear/backdrop sentinel;
- two strips reusing the same allocation with deliberately different occupancy, first/last active X, different global Y and a short final strip;
- exact native RGB/Z bytes, decoded tags, guard bytes and DP/SP completion order; capture the producing frame, not a later recovered frame.

**Pass:** every opaque accepted fragment writes the expected encoded tag; holes retain the underlying tag; clear/no-sub remains distinct; tags decode without collisions; reuse leaves no stale values or guard changes; readback occurs after proven completion. **Falsifier:** any wrong tag, ambiguous presence bit, stale pixel or out-of-bounds write with otherwise known-good geometry. If only the alpha-presence shortcut fails, use explicit sub-validity; if primitive-Z fails under the required command path, test the bounded color-metadata fallback rather than forcing Z into production. A Mode7 triangle subcase is required before extending the claim to Mode7, not before learning the initial rectangle result.

**Stop condition:** one small pass/fail evidence package with command/build identity. Do not build the full compositor to answer this question.

**E2 — only after a viable operand contract: exact math + complete footprint.**

Feed known raw main/sub/tag strips through the smallest CPU or RSP candidate and compare with the raw RGB5/policy oracle from batch4. Include saturation, odd HALF sums, negative SUB, fixed versus empty sub, opaque black, OBJ palette eligibility, color-window clip/disable, and brightness-after-math. Inspect the complete callable footprint including DMA/policy/spills; decide CPU, resident RSP or overlay from that evidence. **Falsifier:** any policy/arithmetic mismatch or an undeclared IMEM/DMEM overlap. A mismatch is a semantic failure, not something to hide with scene-specific output. No need for real N64 to reject a bad formula or overflowing binary layout.

**E3 — only after exact output: integrated strip/section/mode regression and cadence milestone.**

Freeze an integration candidate based on current master plus only required qualified components. Compare against baseline on an original mixed workload with WH changes, independent screen masks, two color-state epochs, overlapping BG/OBJ, and a captured actual regular→Mode7→regular transition frame. Include section/strip boundary and reuse checks. Use the specific WH-burst then generic-state control to distinguish cooldown delay from a compositor error. Measure commands, DMA/fence/overlay counts and existing profiler categories; then run the exact versioned Gothicvania/SRS/Nova2 controls. After lower-level output and virtual progression gates pass, request one prepared real-N64 milestone for low-level behavior and native cadence, rather than a manual test after each small batch.

**Performance contract remains:** frameskip0, APU21, audio enabled (4), precision8; exact runtime/workload/wrapped-ROM hashes and matching ELF/map; two warmup and five complete 60-VI windows for the established hardware capture protocol. Preserve audio/progression checks and the corrected graphics oracle alongside 60/60×5. If a correct path is slower: **correctness → measure regression → profile the correct path → optimize without changing semantics → recover cadence**. Do not revert to flattened operands, underclock audio, skip frames or weaken fixtures.

### What needs hardware; what does not

- **Can proceed autonomously now:** source/ABI guards, assembled size/layout, exact integer/policy tests, deterministic original diagnostics, register/section trace analysis, frame-aligned pixel evidence and emulator readback experiments. These reduce uncertainty without commercial assets.
- **Needs real N64 authority later:** overlay DMA execution/bus/cache assumptions that emulators may mask, actual DP/SP handoff behavior, representative cadence and audio stability at the milestone. Ares/Mupen are useful lower-level filters, not substitutes for that authority.
- **LAB LIMITATION:** pinned ares RSP-interpreter mode remains the established valid custom-microcode laboratory; do not treat its problematic RSP-JIT route as an emulator-core regression. Vulkan RDP source inspection is not proof of the exact backend dynamically exercised by every existing CI job. Cross-backend agreement is helpful but still not hardware.
- **UNKNOWN:** actual historical SMW/ALttP failure-to-cause mapping; complete Mode7/hires/direct-color/palette-raster fidelity; production kernel size and hardware cost. No ROM acquisition or commercial-game reproduction occurred here.

### Preserved rejected explanations / bounded decisions

**REJECTED:** two new full RGB16 surfaces as capacity-safe; generic special Blender ADD as exact saturated SNES ADD; naive expanded-8-bit average as general HALF; raw Z word equals layer ID; nonblack means valid sub pixel; CI success implies visual correctness; post-transition capture proves mixed-frame bands; retained WH count proves all raster registers or exact pixel phase; 60/60 virtual means real-N64 performance.

**Not rejected:** strips; primitive-Z with an encoded/proven contract; all possible RDP exact sequences; CPU post-composition as a bounded control; fixed-slot overlays as an architecture. Their limits and falsifiers are recorded above rather than converted into unsupported impossibility claims.

### Completion and persistence record

**Completed:** initial canonical reconciliation plus requested batches **1, 2, 3, 4, 5**. Findings were persisted between batches and immediately at material discoveries. Earlier checkpoints this audit: `30f76f99`, `d40e170c`, `2696781c`, `88a35f40`, `52fa949c`, `86111add`, `08b048c1`, `715e91fc`, `0ee34035`.

**Not performed / TODO, not an unfinished audit batch:** runtime implementation, new experiments/builds/benchmarks, new hardware captures, final kernel assembly sizing, fresh binary artifact extraction, commercial ROM experiments. Existing logs/API/source were inspected; prior compiled/hardware evidence retains its original authority and is not relabeled as newly measured.

**Last material finding:** the HALF surrogate rejection is narrower than all RDP paths because texture and framebuffer operands are represented differently; the exact low-resolution SNES formulas are independently cross-checked within pinned ares.

**Next exact action:** E1, a single bounded original diagnostic for encoded primitive-Z tags, sub-validity and fenced scratch reuse through Sodium64's actual rectangle command path. Do not start the kernel or merge #13 before this discriminator resolves the current architecture assumption. This sequencing does not prevent already-authorized read-only analysis or a separately prepared hardware qualification of #13.

Only `continuity:docs/CONTINUITY.md` was written. No core/runtime/workflow/technical branch modifications, PR creation/merge, destructive experiment or ROM handling.
