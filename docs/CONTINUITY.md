# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

> **Continuity compaction / recovery (2026-09-21):** the live file crossed the GitHub contents-size boundary and a later checkpoint accidentally replaced it with an empty file. The last complete pre-overflow operational log is permanently preserved in Git at continuity commit **`686f5a1da210f8fcd1b9cd6e74d5663f4d359c30`** (and earlier history). This live document is intentionally compacted to current state + durable decisions so future checkpoints remain well below the API limit. Historical detail not repeated here is **archived, not discarded**.

## RESUME HERE — current audited state (2026-09-21 UTC)

### Phase / gate
- **M3 / Gate C — base-system fidelity and compatibility.**
- Road destination unchanged: real N64, correct native cadence, frameskip 0, full-rate APU/audio, broad fidelity/compatibility, no per-game modes; SuperFX/SuperFX2 and SA-1 remain required later.
- Current Gate-C driver is **H-COMP / SNES color-math compositor fidelity**, not another performance rewrite.

### Integrated truth
- **master:** `5b7134930a0ca859f6aa24e54102de116948e3ed` — `Gate C: preserve per-line window edges at medium precision`.
- This integrates the validated WH0–WH3 urgent-section repair. Do not confuse validation branches below with integrated production state.
- **PR #13 remains OPEN / CANDIDATE** at `84ecafad7cc3505d82f134b2672d9ed1146fedc0`: fixed-slot RSP renderer overlays + validated H-OBJ repair. It is not merged. Emulator evidence supports correctness/capacity; real N64 remains authority for overlay DMA/bus/cadence before integration.

### H-COMP root finding
- **VALIDATED omission:** integrated renderer does not implement general SNES main/sub color arithmetic. Earlier deterministic diagnostics established both ADD/SUB omission and general main/sub operand loss.
- **SUPPORTED architectural requirement:** exact production H-COMP must preserve/reconstruct **raw, unattenuated RGB555 operands** until after color math. Current `update_fill` / palette path applies master brightness before values reach the RSP, so those brightness-scaled values cannot be authoritative color-math operands.
- Pinned SNES reference semantics establish per-channel RGB5 arithmetic with clipping. Brightness is conceptually later than the main/sub arithmetic.
- A production design must still solve operand preservation, selection/gating, half rules, windows, throughput, and integration. The scalar proof kernels below are semantic discriminators, **not production compositor architecture**.

### ACTIVE / RESUME HERE — E2c shared-membership baseline guest implemented
- **E2a remains CLOSED / VALIDATED** on `phase4/gate-c-h-comp-e2a-color-strip-reuse@67c18c9ab4baf7531db8384eef8df59e9641ab86`; semantic run `35657048671 SUCCESS`, artifact `10665172832`, digest `sha256:043f5f76ec87fed5603e6289e7d3617fde147227139f4618de8b3b7c13133471`. Preserve it as frozen evidence.
- E2b validation branch is now **`phase4/gate-c-h-comp-e2b-real-target-switch@115b32aab183fe18bc4d4011277816c2f8f1c888`**.
- Runtime candidate remains exactly parent **`af1ad807b3a2890e8f60501e2bffc2e834f4d65a`**: first real TS traversal begins on compact RGB16 Color Image `0x000E2E80`; at the existing `srl s7,s7,8` boundary and only for `k0==0`, Color Image is restored to `FRAMEBUFFER(sp)-8*560` before the TM traversal. E2a synthetic fill/copy machinery is removed; end-of-frame Sync Full + DP-idle fence and status/framebuffer marker remain.
- Deterministic carrier commit **`0f41914ee000181210192926d87ff22fa2397f85`**: BG1 opaque red / `TM=01` main-only, BG2 opaque green / `TS=02` sub-only, no shared layers/color math/active windows; direct WH0 HDMA writes 0 for the first 8 visible transfers then 1 thereafter to request an urgent real section boundary.
- Host-only measurement commit **`bbb945bc5d94ac68749bbedda5c18f62457cf613`** captures both section queues and decodes `WH0@0x2E`, `TS@0x39`, `TM@0x3A`, `SPLIT_LINE@0x3F`. Precommitted carrier oracle is record 0 = `WH0=0, TS=2, TM=1, split=8`; record 1 = `WH0=1, TS=2, TM=1, split=224` in at least one stable queue.
- Workflow-retarget commit **`41196ea6a8bbd549d4a7369e0d96eb7d2e5cde68`** dispatched the E2b carrier semantic workflow.
- **Harness repair `ecd7a2ec4d57afae8c94de15c75f8e85f02182fe`:** the first carrier workflow still ANDed its result with the retired E2a synthetic pixel classifier. That criterion is invalid because `af1ad...` intentionally removed the E2a synthetic runtime. The current classifier is therefore **section-only**; pixel buffers are still captured but are explicitly non-authoritative until geometry passes.
- Superseded/cancelled runs from earlier branch heads are not evidence. Exact-head **Build and Validate `35658901019 SUCCESS`** on `ecd7a2ec...`: normal build, PROFILE build and pinned Mupen/LLE smoke all green, including statistical-profile decode. This closes compile/layout/generic-boot risk for the current head; it does not validate E2b semantics. Exact-head **E2b Carrier Section Proof `35658901047 FAILURE`** on `ecd7a2ec...`; artifact **`10667090796`**, digest **`sha256:79d4899c2756aff3f7813e9e9950ed742c921925b3bd95253411f206b914f907`**. The failure is a carrier-geometry failure, not target-switch evidence.
- Exact-head normal build artifact **`10665834472`**, digest **`sha256:0dc75b6c02608c02538488e9566cfb69880f00a45df643cb6dbb664daf0cab3f`**, inspected directly: RSP `.text=0xCB0=3,248 B`, DMEM `.data=0x1000`, leaving **848 B IMEM free**. E2a was `0xFB8=4,024 B` / 72 B free, so retiring its synthetic proof body recovered 776 B. This is capacity/layout evidence only, not throughput.
- **Independent off-by-one control:** validated H-SAMPLE artifact from run `35539983428` / artifact `10614436889` records `WH0=0 -> end_line 1`, `WH0=1 -> end_line 2`, … `WH0=7 -> end_line 8`, and finishes `WH0=223 -> end_line 224`. Therefore the E2b table's eight initial zero transfers followed by value 1 supports the precommitted `split_line=8` expectation without adapting to E2b output. **Scope limit:** that capture has `frame_counter=2` (completed first fully configured frame), so it controls line-to-section off-by-one but does **not** test E2b's warmed cross-frame WH0 persistence hypothesis; E2b deliberately warms to counter >=5.
- **MEASURED / CAUSE CONFIRMED — cross-frame WH0 persistence breaks the initial carrier:** artifact `10667090796` shows the same first three records in **both** section queues: record 0 `WH0=1, TS=2, TM=1, split_line=0`; record 1 `WH0=0, TS=2, TM=1, split_line=8`; record 2 `WH0=1, TS=2, TM=1, split_line=224`. Capture is fresh/quiescent: baseline/warmup counter `6`, guest counter `7` (`delta=1`), `SP_STATUS=1`, `DP_STATUS=129` busy mask clear. This exactly confirms the pre-run static explanation: the previous frame leaves WH0=1, the warmed next frame snapshots it, line-0 HDMA writes 0 and creates the extra zero-length section, then the intended line-8 transition follows. **Initial carrier is REJECTED/SUPERSEDED; RSP target-switch runtime remains UNJUDGED and must not be changed from this result.**
- **IMPLEMENTED guest-only carrier repair `71737e68a833c118dfbc3c675874036f687ab702`:** NMI now writes `WH0=0` during VBlank immediately after acknowledging NMI. No RSP/runtime, TM/TS, HDMA table, capture classifier, target address or oracle change. Because `vblank_end` resets `sect_status` before `section_init`, this VBlank write is intended only to restore the starting PPU state and eliminate the measured warmed-frame `WH0=1 -> split=0` artifact.
- Exact-head **Build and Validate `35663719717 SUCCESS`** on `71737e68...`; build/profile/pinned smoke are green after the one-line guest-only repair. **E2b Carrier Section Proof `35663719699 SUCCESS`**, artifact **`10668144178`**, digest **`sha256:18e486758212d5292a0a16d345f632482dc8ac9232f10ab0c0d36e702adf8ecf`**.
- **CARRIER GEOMETRY VALIDATED / MEASURED:** artifact `10668144178` classifies `E2B_CARRIER_SECTION_VALIDATED / passed=true`; **both queue1 and queue2** have record 0 `WH0=0, TS=2, TM=1, split_line=8` and record 1 `WH0=1, TS=2, TM=1, split_line=224`. Capture is fresh/quiescent: warmup/baseline counter `6`, guest counter `7` (`delta=1`), `SP_STATUS=1`, `DP_STATUS=129` with busy mask clear. The prior `split=0` explanation is therefore fully closed: VBlank/NMI WH0 reset fixed only the carrier, exactly as intended.
- **IMPLEMENTED controlled compact-base fix `608185426f572d81385d35bc6fa5520659b9baa2`:** only `src/rsp_main.S` changed at runtime, replacing compact Color Image base `0x000E2E80` with **`0x000E1D00`** and correcting the adjacent comment from global y=8 to y=16. Diff vs `71737e68...` is confined to that one code constant + comment; guest, section geometry, pass-boundary main restore, RDP fence behavior and harness are byte-identical.
- Exact-head **Build and Validate `35664655335 SUCCESS`** on `60818542...`; corrected-base runtime builds and the generic validation path is green. **E2b Carrier Section Proof `35664655322 SUCCESS`**, artifact **`10669710146`**, digest **`sha256:d0a4d2c40ac673e6ea0ea77ba7eea707c423bfe4a2ca117694c6f6d52f2bfbcc`**.
- **MEASURED SAME-SHA E2B TARGET SEPARATION PASS on `60818542...`:** artifact `10669710146` keeps carrier geometry green in both queues (`WH0=0, TS=2, TM=1, split=8`; then `WH0=1, TS=2, TM=1, split=224`) and the fenced capture is fresh/quiescent: warmup/baseline `8`, guest `9`, `delta=1`, `SP_STATUS=1`, `DP_STATUS=129` busy mask clear.
- **Compact operand exact:** `color_final_b.bin` = **2,048/2,048 active words `0x07C1` green** plus **192/192 border words `0x55AA` sentinel**; prefix guard = **64×`0xC3`**, suffix guard = **64×`0x3C`**. No compact overrun is observed after the base correction.
- **Main operand exact:** published framebuffer rows **8..15** contain **2,048/2,048 active words `0xF801` red**; their 192 border words remain zero. Rows 0..7 remain zero, independently confirming the corrected row mapping. Thus the existing real `next_layer` traversal separates no-shared TS/BG2 into compact RGB16 and TM/BG1 into the main framebuffer in the same real 8-line section.
- **Interpretation:** E2b's architecture question is dynamically answered **yes in pinned ares**. The previously flagged mid-pass Set Color Image fence gap did **not** prevent correct separation in this virtual-lab path; retain it only as a real-hardware/ownership risk, not as an explanation for E2b. This still says nothing about shared layers, >8-line slicing, compositor arithmetic, throughput or real-N64 cadence.
- **Validation bookkeeping:** the current workflow's built-in `result.json` still asserts only the carrier geometry; the pixel/guard pass above comes from direct inspection of the exact workflow artifact. Before marking E2b fully CLOSED, encode this already-measured oracle into the host capture classifier/workflow with **no runtime/guest change**, rerun exact-head semantic CI, and require the same counts.
- **IMPLEMENTED host-only final classifier `115b32aab183fe18bc4d4011277816c2f8f1c888`:** only `scripts/gate_c_h_comp_e1_z_tag_capture_n64.py` changed vs measured-pass parent `60818542...`; runtime, guest and workflow are byte-identical. New authority `classify_e2b_target_separation()` combines the already-frozen carrier oracle with **positional** compact RGB16 checks (x=12..267 green `0x07C1`, border sentinel `0x55AA`), both compact guards intact, and main framebuffer rows 8..15 active x=12..267 red `0xF801` with zero green. It does not add shared-layer, border-main, throughput or hardware claims.
- Exact-head **Build and Validate `35666240346 SUCCESS`** on `115b32aa...`; host-only classifier formalization does not disturb build/runtime. **E2b semantic `35666240359`** remains in progress. If semantic is green with classification `E2B_REAL_TARGET_SEPARATION_VALIDATED`, mark E2b CLOSED / VALIDATED; if red, treat it first as classifier/oracle formalization failure because the parent artifact already measured the same bytes green.
- **E2b CLOSED / VALIDATED** on exact head **`115b32aab183fe18bc4d4011277816c2f8f1c888`**. Final semantic run **`35666240359 SUCCESS`**, artifact **`10668929268`**, digest **`sha256:5a4186cbbd5898eb62f22eda24930f950fc960ae674bce5b78f514036c2415c0`**. `result.json` reports **`E2B_REAL_TARGET_SEPARATION_VALIDATED / passed=true`**.
- Final CI authority reproduces every frozen oracle on the same capture: both section queues record `WH0=0, TS=2, TM=1, split=8` then `WH0=1, TS=2, TM=1, split=224`; compact active = **2,048× `0x07C1`**, compact border = **192× `0x55AA`**, both guards true; main rows 8..15 active = **2,048× `0xF801`**, green count 0, mismatches empty. Fresh/quiescent capture: baseline 9 -> guest 10 (`delta=1`), `SP_STATUS=1`, `DP_STATUS=129`.
- **E2b conclusion:** the existing real dual traversal can separate a no-shared TS operand into bounded compact RGB16 and TM into the normal framebuffer for a true 8-row section in pinned ares. The proof-only target-switch runtime is validated as architecture evidence, not production integration. No claim is made about shared layers, long-section banding, compositor arithmetic, throughput or real N64 ownership/cadence.
- **The previous “do not interpret pixels yet” gate is now satisfied** by carrier validation plus the same-SHA corrected-base artifact above.
- **SUPERSEDED pixel-row assumption:** the earlier oracle said compact/main physical rows 0..7 because it assumed the first real section begins at global y=8. Repo evidence disproves that assumption for this carrier: `SETINI=0` makes `fb_border=8`, and `rsp_frame` stores `FB_OFFSET=fb_border+8=16`; therefore the first real 8-line section draws at global y=16..23. With production main target `FRAMEBUFFER(sp)-8*560`, that section lands in published framebuffer **rows 8..15**, not 0..7. Do not use the old row-0 oracle.
- **SUPPORTED ADDRESS BUG / next controlled E2b delta after carrier gate:** current compact target base is `0x000E2E80 = 0xE4000 - 8*560`, copied from E2a's synthetic global-y=8 band. The real carrier's first section is global y=16..23, so this base maps y=16 to **`0xE5180`**, exactly the configured compact suffix-guard address, and leaves intended scratch `0xE4000..0xE517F` untouched. To map real y=16..23 onto compact rows 0..7, the candidate base must instead be **`0xE4000 - 16*560 = 0x000E1D00`**. This is corroborated by **validated E2a Band B**, which used exactly `0x000E1D00` for global y=16..23 and produced the expected compact green output. The E2b run artifact should still independently expose sentinel scratch / guard overwrite; do not patch until the repaired carrier section discriminator on `71737e68...` closes green so geometry and target-address variables remain separated.
- **Precommitted artifact signature for the current wrong compact base (before inspecting repaired-carrier output):** if geometry passes while base remains `0xE2E80`, captured intended scratch `0xE4000..0xE517F` should remain entirely RGB16 sentinel `0x55AA` (2,240 words). The 64-byte suffix guard at `0xE5180` is the start of the accidentally targeted physical row: x=0..11 = first 24 bytes should remain `0x3C`; x=12..31 = final 40 bytes should be overwritten by active rendering (ultimately BG2 green if the TS pass itself works). Main evidence, if target restoration works, belongs in framebuffer rows 8..15. This prediction was recorded before the repaired-carrier semantic artifact completed.
- **MEASURED ADDRESS FAILURE — artifact `10668144178` matches the precommitted wrong-base signature exactly:** intended compact scratch `0xE4000..0xE517F` is **2,240/2,240 words `0x55AA` untouched**; prefix guard is intact (`64×0xC3`); suffix guard at `0xE5180` is exactly **24 bytes `0x3C` + 20 RGB16 green pixels `0x07C1`** (40 bytes), proving active rendering begins there; proof archive at `0xE6000` contains **348 green words + 1,892 `0xCCCC`**, consistent with the same misplaced 8-row band crossing into that region. This converts the compact-base issue from supported static analysis to **MEASURED**.
- **MEASURED main-side traversal/switch success on the same frame:** published framebuffer rows 0..7 remain zero, while rows **8..15** contain exactly **2,048 active words `0xF801` red** and 192 zero border words. Therefore the TM/BG1 traversal and compact->main Color Image switch did take effect correctly in pinned ares for this path. The current observed failure is not “TM failed” and not “switch never happened”; it is specifically the compact TS target base. The earlier mid-pass fence concern remains a real hardware/ownership risk, but it is **not the cause of this virtual-lab pixel result**.
- **Oracle draw-order audit remains valid after correcting row mapping:** current RSP binds compact Color Image before `next_section`, so the first section backdrop and TS/BG2 share the compact target; opaque BG2 green should finish over black backdrop. The pass-boundary switch occurs before TM/BG1, so main active pixels should finish red. Once the compact base is corrected, the intended compact oracle remains 2,048× green + 192 sentinel border with guards intact; the corresponding production main band is framebuffer rows **8..15**, active x=12..267 = 2,048× red and zero green. Main border/background stays outside the discriminator.
- **Framebuffer readback ownership audited:** at `next_frame`, after Sync Full and explicit DP-idle wait, the RSP stores `FRAMEBUFFER(sp)` into the proof marker and only then halts/rotates `sp`. Therefore `proof_framebuffer_pointer` names the framebuffer that just completed rendering, not the next triple-buffer slot. After correcting the real 224-line row mapping, the E2b first-section main band is bytes **`framebuffer[0x1180:0x2300]`** (physical rows 8..15; 8×280×2 bytes), not `framebuffer[:0x1180]`. No RSP-side archive/copy helper is needed.
- **OPEN QUESTION / next pixel-stage risk:** validated E2a changed/reused Color Image only after a `Sync Full` + explicit DP-idle ownership fence. Current E2b switches compact -> main at the real TS/TM pass boundary by emitting Set Color Image directly, without an equivalent preceding fence. `rdp_send` itself waits only DP command-buffer busy (`0x40`), not pipe/TMEM busy and does not insert a sync, so it does not close this ownership gap implicitly. This is not evidence of failure and must not be changed before pixel measurement; if carrier geometry is green but compact/main pixels do not separate, test this ownership/synchronization difference first as a controlled RSP delta.
- **Static discard for later pixel diagnosis:** current proof `rdp_init` sets **primitive depth + Z update with no Z compare** (`0x2F0088FF00040025`). Therefore BG2's metadata-Z write during the compact TS pass cannot reject the later BG1 TM draw through depth comparison. If pixel separation later fails, do not pursue “first pass Z blocked second pass” as the explanation.
- **Narrow pass meaning:** existing real `next_layer` dual traversal can separate no-shared TS/TM operands across compact/full Color Image targets for a true 8-row section. Shared layers are a later discriminator; >8-row band slicing, compositor arithmetic, raw-brightness plumbing, windows/gating, throughput, PR #13 overlay integration and real-N64 cadence remain out of scope.
- Status: **E2B CLOSED / VALIDATED**.
- Immediate next action: begin **E2c baseline only** from validated E2b head `115b32aa...`: create a child proof branch, change only the guest to `TM=0x01 / TS=0x01` (BG1 red shared), keep E2b RSP runtime byte-identical, and measure the precommitted historical-suppression baseline (compact active black `0x0001`, main active red `0xF801`). Do not remove shared suppression until that baseline is measured.

### E2c shared-membership discriminator — ACTIVE
- **Question:** after validated two-target separation, can a layer enabled on both SNES screens be preserved in both raw operands instead of being suppressed from the first traversal by the historical single-framebuffer workaround?
- **E2c branch created from exact validated E2b head:** `phase4/gate-c-h-comp-e2c-shared-membership` from `115b32aab183fe18bc4d4011277816c2f8f1c888`.
- **IMPLEMENTED guest-only baseline commit `69e8f5fdd9da0c7be44d66f61cfa446e3468cfcf`:** only `scripts/make_gate_c_h_comp_e1_z_tag.py` differs from E2b. The sole rendering-semantic delta is `TS 0x02 -> 0x01`, so BG1 red is shared on TM+TS; comments/title were updated accordingly. `src/rsp_main.S` and the validated E2b target-switch runtime are byte-identical. Exact-head **Build and Validate `35666996028`** dispatched; semantic intentionally not dispatched yet because the inherited E2b host classifier expects `TS=2`/green compact.

- Reuse E2b's exact 8-line WH0 carrier, compact target, target-switch runtime, capture boundary and red BG1 tile. Change the child guest only to **BG1 shared on both screens: `TM=0x01`, `TS=0x01`**; no BG2 dependency, no color math/windows.
- **Baseline first / guest-only:** with current mask code unchanged, `shared=1` and `sub s7,s7,t1` removes BG1 from the first traversal. Precommitted baseline oracle: carrier remains 8/224; compact active x=12..267 = **2,048× backdrop black RGBA5551 `0x0001`** with 192× `0x55AA` border and guards intact; main rows 8..15 active x=12..267 = **2,048× red `0xF801`**.
- Only after that baseline measures the historical suppression, make a **one-instruction membership delta** in the child runtime: stop subtracting the shared mask from first-pass `s7` (the existing `and t1,t0,s7` may remain as dead proof-local work; do not combine this experiment with target/fence/band/compositor changes).
- Precommitted repaired oracle: same carrier/guards/main red, but compact active changes **only** from 2,048× black `0x0001` to **2,048× red `0xF801`**. That directly proves the same BG1 contributes to both independent operands.
- This remains **ARCHITECTURE PROOF / HYPOTHESIS** until both E2c baseline + one-variable repair are measured. It does not yet prove production performance, shared OBJ behavior, priorities, color math or band reuse.
- **Immediate E2c action:** after the guest-only generic build is green, change only the host classifier/workflow for the precommitted baseline: section records must become `TS=1/TM=1` at 8/224; compact active must be 2,048× black `0x0001` + 192× sentinel with guards intact; main active remains 2,048× red. Keep `src/rsp_main.S` frozen. Only after that baseline is measured may shared suppression be removed.

### Pre-kernel architecture proofs — CLOSED
- **E1a VALIDATED:** primitive-Z can carry deterministic alpha/presence metadata through the tested RDP path in pinned ares. Validated head `aef1643c0be3b6dd758bdd226ddef97e554ffec9`.
- **E1b VALIDATED:** two-BG winner-layer metadata can be encoded/read correctly. Validated head `8ec1362dd62f117e53b37eaf6523c7bdf00b75bf`.
- **E1c VALIDATED:** one compact Z16 strip can be rebased to different global y bands and physically reused within one frame when explicit DP fences separate ownership. Validated head `994a1fd502f97424e7a5a8dc32e985490b0d39c7`; semantic run `35631286707 SUCCESS`, artifact `10655445324`, digest `sha256:a56b40a3eb5d82106880a4267b17e05018a4a63ff1547faeb41bb5ed389f5038`.
- Combined meaning: the metadata/compact-strip preconditions needed for a possible bounded compositor are viable in the pinned virtual lab. This does **not** prove production throughput or real-N64 bus behavior.

### E1d CLOSED / VALIDATED — raw RGB555 saturating addition
- Exact validated head: **`763218735489aa68e2c87115d9183a404c96a11c`**.
- Semantic run **`35635441459 SUCCESS`**, job `106451604758`.
- Evidence artifact **`10656800647`**, digest `sha256:688f5940ee77f60b8823edca4d91b0ac1b63aa023b069bac6063be43dbfe6a16`.
- Classifier: **`E1D_RGB555_SAT_ADD_VALIDATED / passed=true`**.
- **16/16** actual raw RGB555 outputs equal the precommitted oracle; `mismatches=[]`.
- Prefix `0xA5`, suffix `0x5A`, and 96-byte reserve `0xD7` guards all intact.
- Fresh/quiescent capture: guest counter `10 -> 11` (`delta=1`), `SP_STATUS=1`, `DP_STATUS=129` with busy mask clear, marker `0xE1F00D01`, capture boundary `0x8000AAF8`.
- Exact-head Build/Validate `35635441750 SUCCESS`; scalar proof RSP `.text=0xFB0=4,016 B`, only **80 B IMEM free**.
- **Meaning:** independent-channel RGB555 addition with clamp-to-31 is dynamically proven in pinned ares under the fenced DMA/readback contract.
- **Not proven:** subtraction (handled by E1e below), half rules, CGADSUB/CGWSEL gating, production operand plumbing, vector throughput, real-N64 cost/cadence.
- **Discarded/important harness lesson:** first semantic run `35634232284` was red because proof block `0xA00C6000..60FF` lay inside the normal full-frame E1 Z16 surface `0xA00C0000..0xA00E0CFF`; RDP overwrote operands/guards with `0x0400` depth tags. Relocating only the proof block to `0xA00E2000..20FF` changed the result to exact pass. That red run is **SUPERSEDED / HARNESS ADDRESS-COLLISION**, not arithmetic evidence.

### E1e CLOSED / VALIDATED — raw RGB555 subtraction with floor at zero
- Validation branch: `phase4/gate-c-h-comp-e1e-color-sub-kernel`.
- Exact validated head: **`3c4972f4e58ab89b8e8a2628ca322d353c069049`**.
- Parent implementation head `d268187eda440d3880593ef5d49dde365124a3ff`; final head changes only semantic-workflow isolation/retargeting.
- Exact semantic run **`35637100140 SUCCESS`**, job **`106457077883`**.
- Evidence artifact **`10657246010`**, digest **`sha256:d1b4d2f18e801bec2df189e25e13881d925a8fd204edd31ea3eb74b87be73681`**.
- Artifact classifier: **`E1E_RGB555_SUB_FLOOR0_VALIDATED / passed=true`**.
- Exact A/B operands are unchanged from E1d; expected and actual output words are:
  `0000, 001E, 03C0, 7800, 0000, 0001, 0020, 0400, 001F, 03E0, 2108, 0842, 7C1F, 03FF, 2C0B, 0013`.
- **16/16 exact**, `mismatches=[]`.
- Guards: prefix=true, suffix=true, reserve=true.
- Fresh/quiescent capture: baseline `10`, guest `11`, `counter_delta=1`, `SP_STATUS=1`, `DP_STATUS=129`, capture-ready `0x8000AAF8`.
- Exact-head generic **Build and Validate `35637100360 SUCCESS`**.
- Implementation-head exact build artifact `10656946144`, digest `sha256:9ec60baeb1a8b874c53f09c71503cd2bfd62e24fa27d1dd50d0f006162d51963`; RSP `.text=0xFA4=4,004 B`, **92 B IMEM free**, DMEM `0x1000`.
- **Meaning:** independent-channel RGB555 `max(A-B,0)` semantics are dynamically proven in the same pinned lab and same memory/fence contract as E1d.
- **Not proven:** half-color semantics, CGADSUB selection/gating, window/color-window interaction, fixed-color special cases, production raw operand plumbing, vector throughput, or real-N64 performance.

### E1g CLOSED / VALIDATED — raw RGB555 half-sub arithmetic proven dynamically
- Exact validated head **`8bdec1f3cf580e23bd662dda47ffb5c9201bcbca`**.
- Exact semantic run **`35640776537 SUCCESS`**, job **`106469271771`**.
- Evidence artifact **`10658152381`**, digest **`sha256:da061dc1d46a3cec962043f5a3171f73b7bf5e9ac829cf6cd05fac6aeff839f3`**, inspected directly.
- Classifier: **`E1G_RGB555_HALF_SUB_VALIDATED / passed=true`**; **16/16 exact**, `mismatches=[]`.
- Exact output vector: `0000,000F,01E0,3C00,0000,0000,0000,0000,000F,01E0,1084,0421,3C0F,01EF,1405,0009`.
- Guards independently inspected: prefix 32×`A5`, suffix 32×`5A`, reserve 96×`D7`.
- Fresh/quiescent capture: baseline `8` -> guest `9` (`counter_delta=1`), `SP_STATUS=1`, `DP_STATUS=129` with busy mask clear, capture boundary `0x8000AAF8`.
- Exact-head generic **Build and Validate `35640776778 SUCCESS`**, including Mupen/LLE smoke.
- RSP map in semantic artifact: `.text=0xF6C=3,948 B`, **148 B IMEM free**; DMEM `.data=0x1000`.
- **Meaning:** packed half-sub semantics `floor(max(A-B,0)/2)` per RGB5 channel are proven under the same fenced RSP DMA/readback contract as E1d/E1e/E1f.
- **Does NOT prove:** second-operand selection, half suppression, CGADSUB/CGWSEL/window gating, production raw operand plumbing, per-section brightness transport, throughput, or real-N64 cadence.
- With E1d/E1e/E1f/E1g closed, the basic raw RGB555 arithmetic family is no longer the next uncertainty. Freeze these proof branches; do not merge scalar proof kernels into master.

### E1g batch 4 — complete exact-head half-sub discriminator DISPATCHED
- Final E1g head **`8bdec1f3cf580e23bd662dda47ffb5c9201bcbca`** adds only workflow isolation/retargeting on top of implementation `233279dc...`; runtime and host oracle are byte-unchanged.
- Exact semantic run **`35640776537`** — **Gate C H-COMP E1g RGB555 Half-Sub Proof** — is QUEUED at checkpoint.
- Exact-head generic Build/Validate **`35640776778`** is also QUEUED; implementation-head `35640340728` is already fully SUCCESS including Mupen/LLE.
- Semantic pass authority is artifact-only: `E1G_RGB555_HALF_SUB_VALIDATED / passed=true`, all 16 expected outputs exact, no mismatches, prefix/suffix/reserve guards intact, one fresh guest frame, RSP HALT and DP-idle at the established capture boundary.
- No gating/window or brightness-ABI implementation while these exact-head runs are active. **Resume first with `35640776537` and inspect its artifact before closing E1g or starting the next discriminator.**

### E1g batch 3 — exact generic validation + IMEM check PASSED
- Exact implementation head `233279dcd1574dfba7f1e5439a655f9315f71f41`, **Build and Validate `35640340728 SUCCESS`** across normal build, PROFILE build and pinned Mupen/LLE smoke; update-release skipped as expected.
- Exact normal artifact **`10658450370`**, digest `sha256:a7a121a29e32f8f5e2ea79221723ace56d0bb3ff65384c620df4ff72bc0f7664`, inspected directly.
- RSP `.text = 0xF6C = 3,948 B`, leaving **148 B of 4,096-byte IMEM free**; DMEM `.data = 0x1000` exactly.
- Code-size comparison: E1g packed half-sub is **56 B smaller than E1e** floor-zero per-channel subtraction (`0xFA4=4,004 B`), but 32 B larger than E1f packed half-add (`0xF4C=3,916 B`). This is compactness evidence only, not throughput evidence.
- Generic compile/boot/smoke risk is closed for this implementation. Next controlled delta is workflow-only: isolate/retarget the inherited E1e semantic workflow to E1g, leaving runtime/oracle byte-unchanged, then dispatch pinned-ares evidence.

### E1g batch 2 — packed half-sub runtime + host oracle IMPLEMENTED; semantic workflow intentionally dormant
- Exact implementation head **`233279dcd1574dfba7f1e5439a655f9315f71f41`** on `phase4/gate-c-h-comp-e1g-half-sub-kernel`.
- Runtime preserves E1e's exact proof memory/DMA/fence contract and replaces only the per-channel subtraction body with the precommitted pinned-ares packed half-sub sequence: `diff=x-y+0x8420`; derive `borrow`; clamp packed channels; `&0x7BDE >> 1`.
- Host keeps the same 16 A/B vectors and guards, changing only the expected oracle to `0000,000F,01E0,3C00,0000,0000,0000,0000,000F,01E0,1084,0421,3C0F,01EF,1405,0009` and classifier identity **`E1G_RGB555_HALF_SUB_VALIDATED`**.
- No CGADSUB/CGWSEL/window gating is modeled here; E1g is arithmetic only.
- Inherited semantic workflow remains filtered/named for E1e, so this implementation cannot accidentally generate E1g semantic authority.
- **IMPLEMENTED, not validated.** Next: exact-head Build/Validate + artifact IMEM check; only then isolate/retarget the semantic workflow.

### E1g batch 1 — child branch created from exact validated E1e subtraction boundary
- New validation-only branch **`phase4/gate-c-h-comp-e1g-half-sub-kernel`** created exactly from E1e validated head `3c4972f4e58ab89b8e8a2628ca322d353c069049`.
- Rationale: half-sub is cleanly isolated against the already validated floor-at-zero subtraction path. Same 16 A/B operands, `0xA00E2000..20FF` proof memory, DMA staging, guards and capture boundary are inherited unchanged.
- E1e and E1f remain frozen validated evidence. Next controlled change is exactly the precommitted packed half-sub arithmetic + E1g expected oracle/classifier; no gating/window work in this branch.

### E1g implementation precommit — exact packed MIPS sequence frozen, still NO branch/code
- If E1f validates, E1g should branch from validated E1e subtraction head `3c4972f4...`, preserving the same proof memory/DMA/fences/oracle harness and changing only subtraction arithmetic + expected outputs.
- Proposed scalar RSP sequence mirrors pinned ares literally for each `x=A, y=B`: `diff=x-y+0x8420`; `borrow=(diff-((x^y)&0x8420))&0x8420`; `base=(diff-borrow)&(borrow-(borrow>>5))`; `out=(base&0x7BDE)>>1`.
- MIPS implementation can use ordinary 32-bit register arithmetic because the reference itself is `u32`; all masks/constants fit immediate operations. No branches or per-channel extraction are required.
- Expected consequence to test, not assume: E1g should be materially smaller than E1e's 4,004-B scalar per-channel kernel. Code size is secondary evidence only; exact 16-word semantics remain the primary discriminator.
- This precommit exists to prevent adapting the implementation after seeing results. **Do not instantiate it until E1f closes.**

### E1g prep — half-sub packed reference equivalence checked while E1f runs; NO E1g code
- Pinned ares half-sub formula remains the authority: compute packed saturated subtraction via `diff=x-y+0x8420`, derive per-channel borrow mask, clamp, then `&0x7BDE >> 1`.
- Independent host derivation rechecked the precommitted 16-word E1g oracle exactly: `0000,000F,01E0,3C00,0000,0000,0000,0000,000F,01E0,1084,0421,3C0F,01EF,1405,0009`.
- As a static/control check, the pinned packed half-add and half-sub identities were compared against explicit per-channel definitions over **117,649 structured RGB555 color pairs** built from channel values `{0,1,2,15,16,30,31}`; zero mismatches for either formula. This deliberately covers zero, odd/even rounding, midpoints, near-max and max values on all three channels plus cross-channel carry/borrow combinations.
- This is host-side algebra/control evidence, not an N64 semantic run. **Do not create or implement E1g until E1f's exact semantic run closes.**

### E1f CLOSED / VALIDATED — raw RGB555 half-add arithmetic proven dynamically
- Exact validated head **`07c5f27b2d6e881c43d0844214376c59a2248036`**.
- Exact semantic **`35639124824 SUCCESS`**, job **`106463842354`**.
- Evidence artifact **`10657453837`**, digest **`sha256:b9932fbdd5e9e2a2d5254a9c028552a64f52d0a02ca413f8bac8012f0b523f0d`**.
- Artifact inspected directly: **`E1F_RGB555_HALF_ADD_VALIDATED / passed=true`**, all **16/16** actual words equal the precommitted oracle, `mismatches=[]`.
- Exact outputs: `0000,0010,0200,4000,7FFF,000F,01E0,3C00,000F,01E0,318C,0C63,3DEF,3DEF,3DEF,2AAA`.
- Raw guards independently inspected: prefix is 32×`A5`, suffix 32×`5A`, reserve 96×`D7`; classifier reports all three true.
- Fresh/quiescent boundary: warmup counter 6, baseline 7 -> guest 8 (`counter_delta=1`), `SP_STATUS=1`, `DP_STATUS=129` with busy mask clear, capture-ready `0x8000AAF8`.
- Exact-head generic **Build and Validate `35639124728 SUCCESS`**. Implementation artifact `10657132935` measured RSP `.text=0xF4C=3,916 B`, **180 B free**.
- **Meaning:** the pinned-ares packed identity `(A+B-((A^B)&0x0421))>>1` exactly reproduces independent-channel RGB555 floor-average under the established fenced RSP DMA contract, including cross-channel carry traps.
- **Does NOT prove:** half-sub (E1g), CGADSUB/CGWSEL half gating/suppression, raw production operand plumbing, per-section brightness solution, vector throughput, or real-N64 cost/cadence.
- Freeze E1f as evidence. Next controlled semantic delta may now instantiate the already-precommitted E1g packed half-sub proof from validated E1e.

### E1f batch 6 — complete exact-head generic validation GREEN while semantic lab builds
- Final E1f head `07c5f27b2d6e881c43d0844214376c59a2248036`, **Build and Validate `35639124728 SUCCESS`** across normal build, PROFILE build and pinned Mupen/LLE smoke; update-release skipped as expected.
- Because the final E1f commit is workflow-only, the already measured implementation artifact/code size remains authoritative: RSP `.text=0xF4C=3,916 B`, 180 B free.
- Exact semantic `35639124824` has passed deterministic guest generation, exact runtime build/wrap/symbol discovery and pinned-ares dependency setup; pinned ares itself is currently building.
- E1f semantics remain **OPEN** until evidence artifact inspection. No runtime edit while this run is active.

### E1f batch 5 — complete exact-head half-add discriminator DISPATCHED
- Final E1f head **`07c5f27b2d6e881c43d0844214376c59a2248036`** adds only workflow isolation/retargeting on top of implementation `5a5e3907...`; runtime and host oracle are byte-unchanged.
- Exact semantic run **`35639124824`** — **Gate C H-COMP E1f RGB555 Half-Add Proof** — is IN_PROGRESS.
- Exact-head generic Build/Validate **`35639124728`** is also IN_PROGRESS; implementation-head `35638793678` is already fully SUCCESS including Mupen/LLE.
- Semantic pass authority remains artifact-only: `E1F_RGB555_HALF_ADD_VALIDATED / passed=true`, all 16 expected words exact, no mismatches, all guards intact, one fresh guest frame, RSP HALT and DP-idle at the established boundary.
- No E1g half-sub or gating implementation while these exact-head runs are active. Resume by inspecting `35639124824` and its artifact first.

### E1f batch 4 — exact compile/IMEM check PASSED; packed half-add materially smaller
- Exact implementation head `5a5e390700aab8835e9b6229965c7bccc24081ba`; normal and PROFILE build jobs in `35638793678` are green.
- Exact normal artifact **`10657132935`**, digest `sha256:e73ece0618e99ba11c29eff3e3578ec9fb56f544383e366669e5223c791b5c54`, inspected directly.
- RSP `.text = 0xF4C = 3,916 B`, leaving **180 B IMEM free**; DMEM remains exactly `0x1000`.
- This is **100 B smaller than E1d saturating-add** (`0xFB0`) and 88 B smaller than E1e subtraction (`0xFA4`), because the exact packed half-add identity avoids per-channel extract/clamp sequences.
- Interpretation: source-derived packed arithmetic is not only semantically well-defined but substantially more compact in this proof. This is code-size evidence, **not throughput or production-placement evidence**.
- Generic Mupen/LLE smoke for `35638793678` is still running at checkpoint. Do not retarget semantic workflow until the full generic run is green.

### E1f batch 3 — static single-variable/oracle audit CLEAN while build runs
- Compare E1d validated head `76321873...` -> E1f implementation `5a5e3907...` is exactly one commit touching only `src/rsp_main.S` and the host classifier: runtime +11/-46 lines, host +11/-11. No workflow, guest, address, guard or fence change.
- Exact runtime source implements the pinned ares identity literally: `t2=(A^B)&0x0421; t3=A+B-t2; t3>>=1`.
- Oracle was independently recomputed per channel and agrees with the packed reference expression for all 16 vectors.
- Existing operands include cross-channel carry traps: e.g. `001F+0020 -> half 000F` and `03E0+0400 -> half 01E0`; naïve packed `(A+B)>>1` cannot pass these accidentally.
- 15-bit operands keep the 32-bit MIPS `add/sub` sequence far from signed overflow. Static audit found no endian/DMA-order change relative to validated E1d.
- Build/Validate `35638793678` is active; do not retarget semantic workflow until exact artifact/map confirms fit.

### E1f batch 2 — packed half-add runtime + host oracle IMPLEMENTED; semantic workflow still dormant
- Exact implementation head **`5a5e390700aab8835e9b6229965c7bccc24081ba`** on `phase4/gate-c-h-comp-e1f-half-add-kernel`.
- Runtime keeps the validated E1d DMA/staging/memory/fence contract and replaces only the scalar arithmetic loop with pinned-reference packed half-add: `xor -> &0x0421 -> add -> subtract carry-isolation mask -> >>1`.
- Host keeps the exact same 16 A/B operands and guards, changing only the expected vector to the precommitted E1f oracle and classifier identity **`E1F_RGB555_HALF_ADD_VALIDATED`**.
- No half-enable/window/CGADSUB gating is modeled here; this is arithmetic only.
- Inherited semantic workflow remains filtered to E1d, so E1f cannot accidentally produce semantic authority yet.
- **IMPLEMENTED, not validated.** Next: inspect exact-head normal/PROFILE build and IMEM size before retargeting the semantic workflow.

### E1f batch 1 — child branch created from exact validated E1d add boundary
- New validation-only branch **`phase4/gate-c-h-comp-e1f-half-add-kernel`** created exactly from E1d validated head `763218735489aa68e2c87115d9183a404c96a11c`.
- Rationale: E1f half-add is most cleanly isolated against the validated add path, not against E1e subtraction. Same 16 A/B operands, proof block `0xA00E2000..20FF`, DMA staging, guards and capture boundary are inherited unchanged.
- Implementation strategy precommitted before code: mirror the pinned ares packed half-add identity `(x+y-((x^y)&0x0421))>>1` for each raw RGB555 word. This is semantic proof plus code-size evidence only; it is not a production throughput claim.
- E1d remains frozen; E1e remains independently frozen/validated.

### E1f prep — half-color semantics source-grounded, no code yet
- Pinned SNES reference: `ares-emulator/ares@17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`, both `ares/sfc/ppu-performance/dac.cpp` and accurate `ares/sfc/ppu/dac.cpp`.
- **Half-add arithmetic:** reference uses `(x + y - ((x ^ y) & 0x0421)) >> 1`; this is exactly independent per-channel `floor((A+B)/2)` for RGB555, with cross-channel carry suppression. No saturate-to-31 step is needed because averaging two 5-bit channels is already <=31.
- **Half-sub arithmetic:** reference first performs per-channel floor-at-zero subtraction, then masks `0x7BDE` before shifting; equivalently each channel is `floor(max(A-B,0)/2)`.
- **Half gating:** when fixed color is the second operand (`blendMode=0`), half applies when the half bit is set and the above/color-window permits math. When subscreen is selected (`blendMode=1`), half is suppressed if the below operand is transparent/backdrop (`Source::COL`); accurate implementation falls back to fixed color and forces `colorHalve=false` in that case. Window/color-enable gating is therefore a separate semantic layer from the arithmetic itself.
- **Decision:** split the next work into at least two discriminators: **E1f = half-add arithmetic only** and **E1g = half-sub arithmetic only**. Do not mix operand-selection/window suppression into those kernels. A later E1h-style discriminator should cover CGADSUB/blendMode/window half-enable gating.
- Reusing E1d/E1e's 16 A/B operands, exact E1f half-add oracle is: `0000,0010,0200,4000,7FFF,000F,01E0,3C00,000F,01E0,318C,0C63,3DEF,3DEF,3DEF,2AAA`.
- Precomputed E1g half-sub oracle for later use: `0000,000F,01E0,3C00,0000,0000,0000,0000,000F,01E0,1084,0421,3C0F,01EF,1405,0009`.
- **Status:** source-derived / oracle precommitted; no E1f branch or runtime change yet.

### Section ABI capacity check — 0x40 bytes are fully occupied
- Exact `defines.h` offset walk confirms the section layout consumes all **64/64 bytes**: `BGHOFS` starts at section +0; after scroll/Mode7/window/color/layer state, `BG_MODE` is +61, `STAT_FLAGS` +62, and `SPLIT_LINE` +63. `MASK_SEL` begins immediately after the section.
- Therefore there is **no existing spare byte** for per-section brightness. A production solution must either prove a safe bit/field repack, replace/reinterpret existing stored state, widen/restructure section records and measure its cost, or derive brightness by another exact mechanism.
- Do not widen `SECTION_SIZE` speculatively: queue sizing, DMA volume, section count/cooldown and RSP DMEM layout make that a performance-sensitive architectural change that needs its own evidence.

### Production H-COMP integration risk — master brightness is not explicit in the 0x40-byte section ABI
- Source audit found `write_inidisp` stores master brightness in the global `brightness` byte and calls `update_fill`; the 0x40-byte section snapshot copied from `bghofs` contains brightness-scaled `sub_color/main_color` but **no explicit brightness field**.
- `rsp_frame:update_dpal` also loads the current global `brightness` once while converting CGRAM into the frame palette queue. Thus exact “raw color math first, master brightness last” cannot simply replace the existing section colors with raw RGB555 and assume brightness is recoverable for every historical section.
- **OPEN QUESTION / potential Gate-C fidelity debt:** whether mid-frame INIDISP brightness changes are currently represented correctly for normal layer palette colors is not established by this audit. Existing fixed/backdrop colors can encode brightness in their already-scaled values, but the palette queue appears frame-level. Do not label this a bug until a focused raster-brightness test proves it.
- **Integration implication:** any production raw-operand design must explicitly account for per-section master brightness (new/repacked section state or another proven mechanism) rather than losing raster-sensitive brightness history. This is a design constraint, not a reason to widen the ABI yet.

### Post-arithmetic gating audit — existing section ABI already carries the needed control registers
- Master source audit while E1f runs: each 0x40-byte frame section already snapshots `WOBJSEL`, `CGWSEL`, `CGADSUB`, `TS/TM/TSW/TMW` and window edges alongside colors/layer state. Therefore later color-math gating does **not** need a second CPU→RSP control pipeline merely to transport these registers.
- Current RSP backdrop path already consumes `CGADSUB & 0x20` (backdrop math enable), `CGWSEL` and `WOBJSEL` to choose/swap fill colors across color-window segments, but explicitly says `TODO: implement color math properly`; it substitutes/switches already brightness-scaled `MAIN_COLOR/SUB_COLOR` rather than performing SNES arithmetic.
- **SUPPORTED direction:** a later gating discriminator can reuse the existing section/window ABI and established `calc_windows` segmentation. The unresolved production problem is primarily exact raw operand preservation/identity + compositor execution, not transport of CGADSUB/CGWSEL themselves.
- **Do not infer integration readiness:** existing fill-window behavior covers backdrop approximation only and does not establish per-layer main/sub operand availability or exact half suppression semantics.

### E1h prep — isolate half suppression / second-operand selection after E1g; NO branch/code
- Pinned accurate ares defines the key post-arithmetic gating in `PPU::DAC::above()`: if the winning main layer is not color-math-enabled or the below color-window mask disables math, return the main color unchanged; otherwise choose the second operand from fixed color (`CGWSEL blendMode=0`) or subscreen (`blendMode=1`). If subscreen is selected but its winner is transparent/backdrop, ares falls back to fixed color **and forces half off**. Otherwise `CGADSUB bit6` enables half only when the above color-window output allows main color.
- Keep this separate from color-window truth-table testing. Proposed **E1h** semantic discriminator: add mode only, color math otherwise enabled, above/below window allows color, one fixed main color `X=0x4210`, subscreen `S=0x0842`, fixed color `F=0x2108`; vary only `blendMode`, `belowTransparent`, and `halfRequested`.
- Precommitted six-row oracle:
  1. fixed, half=0 -> full add `X+F = 0x6318`;
  2. fixed, half=1 -> half-add `(X+F)/2 = 0x318C`;
  3. subscreen present, half=0 -> full add `X+S = 0x4A52`;
  4. subscreen present, half=1 -> half-add `(X+S)/2 = 0x2529`;
  5. subscreen transparent, half=0 -> fixed fallback full add `X+F = 0x6318`;
  6. subscreen transparent, half=1 -> **same fixed fallback full add `0x6318`**, proving half suppression rather than merely operand fallback.
- This matrix deliberately makes fixed/subscreen and full/half results distinct, so a wrong selector or failure to suppress half cannot pass accidentally.
- A later **E1i** should isolate CGWSEL color-window above/below masks + WOBJSEL/WHx logic using the already established section/window ABI. Do not combine E1h and E1i.
- **Blocked on E1g closure:** do not create E1h branch or code until exact E1g semantic artifact is validated.

### Post-E1g production architecture audit — operand/state transport is now the gate driver
- **Arithmetic is closed:** E1d/E1e/E1f/E1g prove exact raw RGB555 add/sub/half-add/half-sub in the pinned RSP lab. The next uncertainty is no longer arithmetic; it is how to feed a production compositor exact main/sub operands and raster-sensitive state without duplicating the renderer or exploding memory/bus cost.
- The existing 64-byte section record is fully occupied as fields, but **`STAT_FLAGS` only consumes bits 7 (`force blank`) and 6 (`OAM dirty`) in current source**. Bits 0..5 are unused by both CPU and RSP paths. Therefore the original 4-bit INIDISP master-brightness value can fit in bits 0..3 **without changing `SECTION_SIZE`**. The current internal multiplier `0,2..16` can be reconstructed from that raw nibble later.
- Existing section fields `SUB_COLOR` and `MAIN_COLOR` are 16-bit values currently filled by `update_fill` with brightness-scaled N64-packed COLDATA and CGRAM[0]. **SUPPORTED design option:** repurpose those same slots to preserve raw RGB555 fixed color (COLDATA) and raw RGB555 backdrop (CGRAM[0]); this would also avoid section growth. Not implemented/proven yet.
- Conservative queue-capacity check: each `SECTION_QUEUE` reserves `0x5000` bytes. Even an upper-bound 242 records × 64 B consumes only `0x3C80`, leaving at least **`0x1380` bytes**. A sideband fallback is physically possible if repacking later proves insufficient, but it is not needed yet and should not be introduced speculatively.
- Current `rsp_frame:update_dpal` converts all 256 CGRAM entries once per rendered frame using the **current global brightness**, then writes the brightness-scaled N64 palette queue. This frame-global palette conversion is incompatible with a general “raw operands first, master brightness last” compositor unless changed.
- **OPEN QUESTION / pre-existing Gate-C debt:** writes to CGRAM entry 0 call `update_fill` and can affect sections, but nonzero mid-frame CGRAM writes do not call `update_frame`; the palette queue is rebuilt later from final/current CGRAM. A focused raster-palette test is required before labeling observable behavior wrong. Do not attribute this possible debt to H-COMP.
- Current renderer does not truly compose main/sub screens. `MASK_SEL` (fed by the menu's **SUB LAYER ORDER: BACK/FRONT**) chooses whether the same renderer traverses TS then TM or TM then TS into one framebuffer. This is the historical no-blending workaround and cannot remain semantically necessary for the 1.0 no-manual-mode target.
- Crucially, the RSP already has a **natural pass boundary** after finishing the first screen mask: `srl s7,s7,8` then the second layer traversal starts. This supports a production hypothesis that reuses the same renderer, switching RDP color target between main and sub passes rather than building a second renderer.
- **SUPPORTED architecture hypothesis:** render one screen raw into the normal full framebuffer; render the other screen raw into a compact reusable color strip; keep/reuse winner metadata from the E1a–E1c path; run exact compositor arithmetic over the band; then apply section brightness. This aligns with E1c strip ownership and avoids the previously rejected full-frame extra-surface design.
- Current color-window control transport is already present per section (`CGWSEL/CGADSUB/WOBJSEL/WHx`), but `calc_windows` explicitly supports only Window 1 and has `TODO: support window 2 and combine logic`. The four CGWSEL color-mask modes themselves map coherently onto the existing `FILL_JUMPS` approximation; Window-2/combine fidelity is a separate debt.
- Mode 7 windows are also explicitly TODO and BG windows currently combine TMW/TSW approximately. These remain Gate-C debts but are not yet the smallest architecture discriminator for H-COMP.

### Forward architecture finding — E2a rebasing matches the renderer's existing framebuffer coordinate convention
- The normal RSP renderer already starts each frame by programming `RDP_FRAME.address = FRAMEBUFFER - 280*16` bytes. At RGB16 stride 560 B/row this is an **8-row negative base offset**, so global RDP y=8 maps to the physical framebuffer base.
- E2a uses the identical transform for its first compact band: `scratch - 8*560`; later bands generalize it as **`scratch_base - band_start*560`**.
- Therefore a future real-traversal target switch can preserve the renderer's global tile/scissor coordinates and change only the Color Image base for the compact operand; no separate tile-coordinate rewrite is implied by E2a.
- This is source/layout evidence only. E2b still has to prove that the real BG/OBJ traversal behaves correctly when the target changes.
- Classification: **SUPPORTED SOURCE FINDING**.

### Forward architecture finding — compact production target needs a section→band subloop, not section-sized scratch
- E2a proves/asks about an **8-row** reusable physical strip, but the real renderer's screen-pass boundary occurs inside each raster **section**, whose `SPLIT_LINE` may be much farther than 8 rows. Merely switching Color Image at `srl s7,s7,8` would therefore overrun an 8-row scratch for long sections.
- Source audit shows the vertical section bounds are concentrated in `k0/k1`: backdrop/scissor bounds, BG initial row + `blt s1,k1` termination, and OBJ section-intersection clipping. This is favorable for a bounded subloop rather than renderer duplication.
- **SUPPORTED production direction:** retain the true section end separately, then iterate **section → fixed-height bands**; for each band set `k0=band_start`, `k1=min(section_end, band_start+strip_rows)`, render the required screen operands into their targets, compose/consume the compact operand, then advance until the section end. Section state itself is loaded once and reused across its bands.
- This still needs a controlled dynamic proof. It does **not** establish performance, cache correctness across repeated band traversals, OBJ behavior at band boundaries, or real-N64 bus cost.
- Refined E2 sequence if E2a passes: E2b should first prove the real target switch on a deliberately **8-row/no-shared** carrier section (one variable); a later band-reuse proof then exercises a section longer than the strip before production integration.
- Classification: **SUPPORTED SOURCE FINDING / ARCHITECTURE REQUIREMENT**, not implemented.

### Forward architecture finding — two screen traversals already exist; target separation is not a wholesale duplicate-render cost
- Current renderer packs two screen masks into `s7` (low/high byte) and, when both are nonzero, already walks `next_layer` once for the first screen then `srl s7,s7,8` and walks it again for the second screen.
- Therefore the supported two-target H-COMP direction does **not** require inventing a second renderer or doubling all exclusive-layer traversal versus Sodium64's existing TM/TS workaround. The existing dual traversal is the machinery to reuse.
- Incremental production costs relative to the current path are instead: Color/Z target state switches/fences, compact operand bandwidth/readback/composition, fixed-band handling, and **re-rendering layers shared by TM+TS** that current code deliberately suppresses from the first pass.
- This materially strengthens the target-switch architecture hypothesis, but is **not performance proof**. Real-N64 profiling remains required because extra target traffic/compositor work and shared-layer duplication may still exceed the frame budget.
- Classification: **SUPPORTED SOURCE FINDING / ARCHITECTURE PROOF SUPPORT**.

### Forward architecture finding — real two-target traversal must stop suppressing shared layers
- Source audit at the existing screen-pass boundary found a production-relevant constraint for the discriminator **after** E2a.
- Current section setup builds the two traversal masks as follows: load one of TS/TM according to `MASK_SEL`; load the other; compute `shared = first & second`; then **subtract shared layers from the first pass** before packing the other mask into the high byte. The later `srl s7,s7,8` boundary therefore draws shared layers only once, on the second traversal.
- That behavior is intentional for the historical **single-framebuffer / no-blending workaround**, where drawing shared layers twice would be redundant or harmful. It is **not valid for true independent main/sub operands**: a layer enabled on both SNES screens must contribute to both raw target images.
- Therefore production eventually needs both (1) Color Image target switching at the natural traversal boundary and (2) shared-layer membership preserved in **both** screen masks. However, experimental discipline says **do not change/test both at once**.
- The existing deterministic carrier already has two visually distinct real renderer inputs (BG1 black/checker, BG2 opaque green) and writes TM/TS directly. A minimal child guest can set **BG1 main-only (`TM=0x01`) and BG2 sub-only (`TS=0x02`)**, making `shared=0` so the historical subtraction is inert.
- Refined sequence if E2a passes:
  1. **E2b target-switch only:** use that no-shared carrier and the real `next_layer` traversal; change only Color Image ownership at the existing `srl s7,s7,8` boundary and prove distinct main/sub outputs.
  2. **E2c shared-membership only:** after E2b closes target switching, introduce a controlled shared-layer case and remove/replace the historical shared suppression, proving the layer contributes to both operands.
- This finding does not alter E2a's synthetic Color Image rebasing question and requires no runtime change while semantic run `35657048671` is active.
- Classification: **SUPPORTED SOURCE FINDING / NEXT-ARCHITECTURE CONSTRAINT**, not implemented.

### E2a batch 11 — semantic workflow retargeted as workflow-only delta
- E2a branch advanced to **`67c18c9ab4baf7531db8384eef8df59e9641ab86`** with one workflow-only commit: `proof: dispatch E2a color strip semantic validation`.
- Runtime/source/classifier are unchanged from generic-green `0f588c69...`. Only `.github/workflows/gate-c-h-comp-e1-z-tag.yml` metadata changed:
  - workflow name -> **Gate C H-COMP E2a Color Strip-Reuse Proof**
  - push branch filter -> **`phase4/gate-c-h-comp-e2a-color-strip-reuse`**
  - concurrency group -> E2a
  - evidence artifact name -> E2a
- The deterministic carrier guest, pinned ares commit/lab mode, exact-ELF capture boundary, E1c Z control, E2a color classifier and all proof addresses/oracles remain byte-identical to the generic-green candidate.
- **Expected dispatch:** this push should start both standard Build/Validate and E2a semantic workflow. Semantic result is the first authority for compact Color Image strip rebasing/reuse.
- **Decision rule:** pass only if E1c Z control remains valid, color archive A and reused final B match their complete 280x8 contracts with sentinels/guards, B contains zero stale A words, and the real main snapshot is written identically before/after. Any failure must be classified by sub-contract; do not collapse it into “Color Image impossible.”
- Classification: semantic dispatch delta **IMPLEMENTED / WORKFLOW-ONLY**; result **PENDING**.

### Focused RSP return-delay audit after E2a root cause — two latent adjacency hazards, no current repair
- A bounded audit of `jr ra` in current `rsp_main.S` found that almost all returns either have an explicit useful delay-slot instruction or explicit `nop`.
- Two additional returns rely on the **next function's first physical instruction** as an implicit delay slot:
  - `clear_cache: jr ra` executes `shared_mirror: srl t2,t6,11`;
  - `mode7_out: jr ra` executes `mode7_read: andi t0,t2,0x7F00`.
- Current callers treat those temporaries as scratch / overwrite them before authoritative use, and there is no observed regression attributable to either path. **Do not “fix” them speculatively in the active E2a experiment.**
- Operational lesson from the validated E2a bug: future edits must not insert a new first instruction after either return without first making the delay slot explicit. Treat adjacency there as a **HYGIENE RISK**, not as intentional API.
- No other hidden `jr ra` adjacency of the same form was found in this file.
- Classification: **SOURCE AUDIT / HYGIENE RISK**, current behavior unchanged.

### E2a batch 10 — delay-slot repair dynamically CONFIRMED; generic validation GREEN
- Exact repaired head **`0f588c698cd46cc01d618d2eb98e6c3e209f5225`**, **Build and Validate `35656638964 SUCCESS`** across normal build, PROFILE build and pinned Mupen/LLE smoke.
- Smoke artifact **`10665935859`**, digest `sha256:d7a59eb0cd9fbc3adadb73fb76b01d48521d7d98902a2798aa40184ec4ec1818`.
- Direct smoke inspection: normal run reaches **`PC 0x80009138`** after the 2 s run instead of remaining at the failing first-task state; profile run also reaches `0x80009138`.
- Statistical snapshot is valid again: 32-bit word-swapped S64P v1, interval 65521, **4769 total / 4096 valid samples**, last EPC `0x8000AB04`; decoder succeeds. The prior all-`AA55AA55` snapshot is therefore a consequence of the control-flow hang, not evidence of a profiler/scratch overlap.
- This is a clean cause/fix confirmation: failing `0bb47e8a...` → repaired `0f588c69...` differs by exactly one `nop`, and the previously red generic smoke becomes fully green.
- **REJECTED explanations:** direct E2a scratch/profile range collision; profiler decoder defect; compact Color Image rebasing as cause of the generic hang. The actual blocker was the exposed `jr ra` delay slot in `dma_wait`.
- E2a compact-color semantics are still **UNKNOWN**: generic validation proves only compile/boot/runtime health. The inherited semantic workflow remains branch-filtered to E1c and has not tested E2a yet.
- **Next controlled batch:** retarget only the existing pinned-ares semantic workflow metadata/branch/evidence naming from E1c to E2a while preserving its guest, capture boundary and exact E2a classifier; dispatch by push and interpret the resulting exact-head semantic artifact.
- Classification: delay-slot defect **VALIDATED / FIXED**; repaired E2a runtime **GENERIC GREEN**; architecture proof **OPEN**.

### E2a batch 9 — repaired exact build fits; dynamic smoke still running
- Exact repaired head **`0f588c698cd46cc01d618d2eb98e6c3e209f5225`** auto-dispatched **Build and Validate `35656638964`**.
- Build job **SUCCESS**; PROFILE build job **SUCCESS**. Exact normal artifact **`10665131259`**, digest `sha256:28b8ee6765662c21321332d1e46a9dcc01e7d500ff34a99dbce6d3799948818e`; profile artifact **`10665041424`**, digest `sha256:43dc651c607c0a6528afbc1e5447a2739fe351192579ab8e49f34315fb7bf0af`.
- Direct artifact inspection measures **RSP `.text = 0xFB8 = 4,024 B`**, exactly +4 B versus failing E2a `0xFB4`; `.data = 0x1000`. This leaves **72 B IMEM free**. Final base ROM remains **98,304 B**.
- Therefore the controlled `dma_wait` delay-slot repair has no compile/link/IMEM-capacity blocker. This does **not** yet prove the first-task hang is dynamically repaired.
- At checkpoint, `emulator-smoke` job `106522338904` is still running. **Next authority:** normal smoke PC/progress plus valid PROFILE snapshot/decoder on this exact SHA. Semantic E2a remains gated behind that result.
- Classification: repair **IMPLEMENTED / BUILD-VALIDATED**; runtime recovery **PENDING**; architecture **OPEN**.

### E2a batch 8 — one-instruction delay-slot repair IMPLEMENTED
- E2a proof branch advanced to **`phase4/gate-c-h-comp-e2a-color-strip-reuse@0f588c698cd46cc01d618d2eb98e6c3e209f5225`**.
- Controlled delta from failing `0bb47e8a...`: exactly one explicit **`nop`** inserted after `dma_wait: jr ra`, making the DMA return delay slot intentional and preventing `e2a_fill_strip: move s3, ra` from executing on nested DMA returns.
- No proof addresses, loop counts, scratch layout, RDP command words, sentinel values, capture/classifier code or workflow files changed.
- Expected RSP text delta is +4 B from failing E2a `0xFB4=4020`, i.e. **`0xFB8=4024` / 72 B free** if link layout is otherwise unchanged; exact artifact remains authority.
- **Next:** inspect exact-head Build/Validate. Required recovery signs are normal smoke PC leaving the initial boot address / sustained runtime progress plus a valid PROFILE snapshot. Only then dispatch/interpret E2a semantic evidence.
- Classification: repair **IMPLEMENTED / CANDIDATE**, validation pending.

### E2a batch 7 — root cause found: new helper occupies `dma_wait` return delay slot
- Exact source comparison E1c `994a1fd5...` → E2a `0bb47e8a...` identifies a deterministic RSP control-flow bug. `dma_wait` ends with **`jr ra` and no explicit delay-slot instruction** under `.set noreorder`.
- In validated E1c, the next physical instruction was `e1c_make_pattern: li t1, TEXTURE`; therefore every DMA return executed that incidental clobber in the `jr ra` delay slot, but it did not redirect control and E1c remained semantically valid.
- E2a inserted `e2a_fill_strip` immediately after `dma_wait`; its first instruction is **`move s3, ra`**. That instruction is therefore executed in the return delay slot of every `dma_read/dma_write`.
- Inside `e2a_fill_strip`, `s3` is intended to preserve the helper caller's return address. The nested `jal dma_write` changes `ra`; then `dma_wait -> jr ra` executes `move s3, ra` in its delay slot and overwrites the saved outer return with the inner DMA continuation. The helper's final `jr s3` consequently jumps back inside itself instead of returning to `next_frame`. `e2a_copy_strip` is exposed to the same mechanism.
- This mechanism directly explains the first-task hang and is independent of compact Color Image semantics, scratch addresses, RDP rebasing, profiler layout or Mupen timing. It also explains why chasing the `AA55` raw snapshot as a memory writer was misleading.
- **Controlled repair precommitted:** add exactly one explicit `nop` as the `dma_wait` `jr ra` delay slot on the E2a proof branch. Do not change addresses, loop counts, RDP commands, sentinels, oracle, workflow or compositor semantics. Expected code cost: +4 B, keeping E2a within 4 KiB IMEM.
- **Falsifier:** if exact repaired head still fails generic smoke/frame progress, the delay-slot defect was real but not sufficient; inspect the next earliest runtime boundary rather than broadening the compositor.
- Classification: delay-slot cause **SUPPORTED/STATICALLY DETERMINISTIC**; repair **TODO**; E2a architecture still **OPEN** pending exact-head generic + semantic evidence.

### E2a batch 6 — key correction: E2a generic failure is PRE-SODIUM64 BOOT, not runtime DMA corruption
- Direct inspection of the uploaded Mupen logs changes the interpretation materially. In E2a normal smoke, after the 3-second run/pause the debugger reports **`PC: A4000040`** — the same IPL3/boot address printed at emulator start. Sodium64 never reached its `0x8000....` runtime.
- Control E1g normal smoke at the same 3-second boundary reports **`PC: 8000AAE4`** and the profile control reaches `0x80009138`; it therefore leaves IPL3 and executes Sodium64 normally.
- Consequently E2a's all-`AA55AA55` raw profiler snapshot **cannot be used as evidence of an E2a runtime SP-DMA overwrite**: the E2a RSP proof code is uploaded by Sodium64 only after main runtime startup, which never occurred in this failing smoke.
- **SUPERSEDED interpretation from batch 5:** “deterministic early-runtime corruption / proof-helper DMA writer” is rejected as the primary explanation. The raw facts from batch 5 remain useful (all-`AA55` snapshot, no declared scratch/profile overlap), but the failure boundary is now earlier: **pre-runtime N64 boot / ROM-image acceptance or startup**.
- This also explains why both the static profiler header and its entire sample region can remain an uninitialized/test-pattern-looking image: `profile_init` and normal runtime sampling were never reached.
- E2a's normal-build job succeeding therefore proves compile/link/packaging only. Its Mupen process completing proves the harness ran, but **boot correctness is FAIL** for exact head `0bb47e8a...`.
- **Next controlled discriminator:** compare E1c/E1g bootable ROM image/layout/header/entry/load boundaries against E2a, especially the RSP embedded-image size/layout and any ROM/bootstrap size invariant crossed by E2a. Do not edit runtime proof semantics until the pre-runtime boot cause is identified.
- Classification: **MEASURED / PRE-RUNTIME BOOT FAILURE**. Compact Color Image architecture remains **UNKNOWN**, not falsified. No semantic workflow dispatch.

### E2a batch 5 — generic red narrowed to deterministic early-runtime corruption; exact writer still OPEN
- Smoke artifact **`10660612301`** from implementation head `0bb47e8a0d226eb12946f26be613aceee26b5036` was downloaded and inspected directly. The complete profiler snapshot at `0x800B76E0`, size `0x4020` (16,416 B), is **one repeated 32-bit word `0xAA55AA55` across all 4,104 words**; this is not merely a bad magic field.
- Control artifact **`10658447258`** from validated E1g generic run `35640776778` uses the **same profile address and size** and contains a valid S64P snapshot (`4769` total samples, `4096` valid). The generic profiling harness/address itself therefore works on the immediately preceding proof family.
- Exact E2a PROFILE link map places `profile_magic..profile_sample_buffer_end` at **`0x800B76E0..0x800BB6FF`**; the embedded RSP blob starts immediately afterward at `0x800BB700`. E2a proof scratch/archives are at physical `0x000C0000+` and `0x000E4000+`; `FRAMEBUFFER1` is `0x000F2300`. **There is no direct declared-range overlap with the profiler snapshot.**
- The bad Mupen log advances only through the first early RSP activity and then stops producing the repeated progress visible in the E1g control. Therefore the earlier “normal headless Mupen execution SUCCESS” is only process/smoke completion here; it is **not proof that E2a makes normal frame progress**.
- `0x55AA55AA` is also E2a's proof scratch sentinel, but the all-`AA55` raw RDRAM image is **not yet sufficient to attribute the writer**: it could be an erroneous RSP DMA/control path, or an underlying/never-written-back RDRAM pattern exposed because execution stalls before profiler state becomes externally visible. Do not promote either explanation without a discriminator.
- **SUPPORTED localization:** the failure occurs before E2a semantic authority and before any compact-color result can be interpreted. It is **not evidence against Color Image strip rebasing itself**.
- **Next controlled discriminator:** audit the new proof-only fill/copy helpers and cross-frame register/control contract against validated E1c, then make the smallest helper-only change that restores a known-safe DMA loop without changing addresses, RDP commands, oracle, color semantics or workflow. Generic Build/Validate must become healthy before semantic dispatch.
- Classification: E2a architecture **OPEN**; generic smoke **FAIL / deterministic early-runtime corruption**; exact cause **OPEN QUESTION**; no semantic workflow dispatch.

### E2a batch 4 — generic Mupen profile decode red; cause OPEN
- Implementation-head Build and Validate **`35647142587 FAILURE`**, but the failure is narrowly localized: normal build SUCCESS, PROFILE build SUCCESS, normal headless Mupen/LLE execution SUCCESS, profiling Mupen run + memory dump SUCCESS; only **Decode statistical profile** failed.
- Failing emulator-smoke job: **`106490744106`**. Smoke artifact **`10660612301`**, digest `sha256:457100f3227307bdec9fa9c4c6afd32766a98a99f1a20593e7d084bdf28bf4e3`.
- Exact decoder error: **`bad profiler magic 0xAA55AA55; expected 0x53363450`** (or canonical 32-bit word-swapped form). Profile snapshot region reported by workflow: `PROFILE_ADDR=0x800B76E0`, size `0x4020`.
- The observed word is the N64/Mupen-visible byte/word ordering of the proof sentinel `0x55AA55AA`, so this is not being dismissed as random profiler noise.
- **OPEN QUESTION:** determine whether E2a/E1c RDP rebasing actually overwrote the profiler snapshot region, or whether the profiling workload never initialized its header and happened to expose sentinel-filled RDRAM. Generic CI red is not yet evidence against compact Color Image rebasing itself.
- **Do not dispatch E2a semantic workflow** until this is separated. Next controlled diagnosis: compare successful E1g generic profiler address/header, inspect the E2a smoke snapshot byte distribution, and map any `AA55/55AA` run against E2a/E1c RDP target geometry.
- Classification at this checkpoint: compile/IMEM **MEASURED/PASS**; normal emulator boot **PASS**; profiler decoder **FAIL / OPEN QUESTION**; E2a color-strip semantics **NOT YET VALIDATED**.

### E2a batch 3 — PROFILE compile/IMEM gate PASSED, only 76 B headroom
- Build/Validate run **`35647142587`** for implementation head `0bb47e8a...` is active.
- PROFILE build job is SUCCESS; exact artifact **`10660414623`**, digest `sha256:1ab2c88dc272ad2dd19c8ca91cd50426db40c980ac49e94459552e4c46e87393`, inspected directly.
- RSP `.text = 0xFB4 = 4,020 B`, leaving only **76 B IMEM free**; ROM/ELF build completed successfully.
- Delta versus validated E1c (`0xED0=3,792 B`) is +228 B despite adding color strip + framebuffer-integrity evidence, because proof loops were factored into shared helpers.
- **Interpretation:** E2a fits as an architecture/measurement proof, but the resident proof body is already at the same “near-full IMEM” warning level as E1d-g. This strongly reinforces that production composition cannot simply accumulate scalar/proof logic in the resident renderer; later overlay/placement must be earned separately.
- Do not dispatch semantic yet. Wait for normal build + pinned Mupen/LLE smoke from `35647142587`; then retarget workflow only.

### E2a batch 2 — compact RGB16 strip runtime/classifier IMPLEMENTED; workflow still dormant
- Exact implementation head **`0bb47e8a0d226eb12946f26be613aceee26b5036`** on `phase4/gate-c-h-comp-e2a-color-strip-reuse`.
- Runtime extends validated E1c without touching production/master: dedicated `0xA00E4000` 280×8 RGB16 scratch, color guards, band-A color archive, and real-framebuffer before/after snapshots.
- Band A rebases global y=8..15 to the color scratch and uses opaque black (`0x0001` expected); band B rebases y=16..23 onto the same physical scratch and uses opaque green (`0x07C1` expected). Existing E1c Z metadata rebasing remains active as the control.
- Normal framebuffer Color Image state is restored and DP-fenced before the after-snapshot. The classifier requires main-before == main-after and initializes those snapshots to different sentinels so a missing copy cannot pass by equality.
- Proof-only repeated 4,480-byte fill/copy loops were factored into shared helpers to stay within 4 KiB IMEM; no throughput claim can be drawn from these diagnostic DMA copies.
- Host classifier now requires **both** inherited E1c Z contract and new E2a color contract. Semantic workflow remains E1c-filtered, so E2a cannot accidentally become VALIDATED before exact build/IMEM inspection.
- **IMPLEMENTED, not validated.** Next: inspect the automatically dispatched exact-head Build/Validate; if IMEM fits and smoke is green, retarget the semantic workflow only.

### E2a batch 1 — proof branch created from exact validated E1c boundary
- New validation-only branch **`phase4/gate-c-h-comp-e2a-color-strip-reuse`** created exactly from `994a1fd502f97424e7a5a8dc32e985490b0d39c7`.
- This intentionally inherits the already validated E1c compact-Z strip, guest, fences and capture boundary. No production/master code changed.
- Next controlled delta is the precommitted color-strip scratch/archive + main-before/main-after integrity evidence. E1c Z behavior must remain byte-for-byte semantically equivalent.

### E2a precommit — compact Color Image strip reuse, exact controlled proof frozen before code
- **Purpose / GATE DRIVER:** extend validated E1c from compact Z metadata to the missing **RGB16 second-screen operand surface**. This is an architecture proof, not production integration or performance evidence.
- Planned proof branch: `phase4/gate-c-h-comp-e2a-color-strip-reuse`, based exactly on validated E1c head `994a1fd502f97424e7a5a8dc32e985490b0d39c7`. E1c's Z rebasing/fences remain the control; the only new semantic variable is compact **Color Image** target rebasing/reuse.
- Dedicated proof memory in the verified free gap below `FRAMEBUFFER1=0xA00F2300`:
  - color scratch: **`0xA00E4000..0xA00E517F`** = 280×8×2 = `0x1180` B;
  - prefix guard: `0xA00E3FC0..0xA00E3FFF` = 64 B, `0xC3`;
  - suffix guard: `0xA00E5180..0xA00E51BF` = 64 B, `0x3C`;
  - archived band A: **`0xA00E6000..0xA00E717F`**;
  - main-frame before snapshot: **`0xA00E8000..0xA00E917F`**;
  - main-frame after snapshot: **`0xA00EA000..0xA00EB17F`**.
  These regions are disjoint from E1 status `0xA00E1000`, E1d-g proof block `0xA00E2000..20FF`, E1c Z scratch/archive, and the first real Sodium64 framebuffer.
- Scratch initialization remains `0x55AA` per RGB16 word. Active x range is the established `12..267` (256 pixels), with 12-pixel borders untouched on each side.
- **Band A:** global y=8..15 maps to physical color-strip rows 0..7 via Color Image base `0x000E4000 - 8*560 = 0x000E2E80`; draw opaque black, expected RGB16 **`0x0001`** on 2,048 active pixels and `0x55AA` on 192 border pixels; DP-fence, then archive.
- **Band B:** global y=16..23 reuses the same physical strip via Color Image base `0x000E4000 - 16*560 = 0x000E1D00`; draw opaque green, expected RGB16 **`0x07C1`** on 2,048 active pixels and `0x55AA` on 192 borders; **zero stale `0x0001` active pixels** after reuse.
- Before changing Color Image ownership, archive the first 8 rows of the actual `FRAMEBUFFER(sp)`; after the second band, restore the normal Color Image address, fence, archive the same 4,480 B again. **Main-before must equal main-after byte-for-byte.**
- Keep E1c's validated compact-Z path active in the same proof so the new color strip and existing metadata strip are shown to coexist under the same ownership fences. Do not change Z semantics/oracle.
- **Pass authority:** color A/B exact histograms + per-pixel checks; color guards intact; no stale A color in B; main framebuffer snapshot byte-identical; inherited E1c Z contract still exact; one fresh guest frame; RSP HALT; DP busy mask clear.
- **Not in E2a:** production palette/raw conversion, TS/TM renderer pass switch, brightness application, CGADSUB arithmetic, E1h gating, Window 2, PR #13 overlays, throughput/cadence claims. Those remain later discriminators.
- **Falsifier:** wrong/rebased rows, guard corruption, stale A color, main framebuffer mutation, or inability to restore/fence Color Image deterministically. Any such result blocks the compact-color-strip hypothesis before production work.

### Immediate next uncertainty
- **NEXT GATE DRIVER: prove or falsify compact second-screen color-target rebasing with the existing renderer/RDP contract.**
- Do not spend the next batch merely proving E1h's six-row boolean selector unless the production architecture needs it; its oracle is already source-grounded and can become a regression proof later.
- The next architecture proof should change one thing: demonstrate that a second render pass can target a compact RGB16 strip representing a chosen global y-band, while the normal/full target remains intact and explicit DP fences make ownership/readback deterministic.
- Prefer reusing E1c's already validated strip rebasing/fence machinery. No production palette rewrite, no brightness application, no CGADSUB arithmetic, no Window-2 work, no PR #13 overlay integration in this first two-target proof.
- **Expected pass evidence:** deterministic main/full target pattern remains intact outside its intended writes; compact color strip contains exactly the second-pass expected pixels for at least two distinct global y-bands using the same physical strip; guards remain intact; stale-band data is absent after reuse; SP/DP quiescent at capture.
- **Falsifier:** if RDP Color Image/scissor/tile coordinate semantics cannot rebase the second pass onto a compact strip without invasive duplicate rendering logic or unacceptable target/stride constraints, abandon this compact-color-strip architecture before production integration.
- E1h (fixed vs subscreen selection + transparent-sub half suppression) and later color-window truth-table proofs remain **DEFERRED semantic regressions**, not discarded.

### H-COMP capacity / integration constraint
- Scalar E1d/E1e nearly fill current resident 4 KiB RSP IMEM; this is useful semantic evidence and a warning against a resident scalar production compositor.
- PR #13 demonstrates a fixed-slot overlay architecture with reported active RSP text `0xD00=3,328 B` and **768 B headroom**, but remains candidate pending real-N64 hardware validation.
- Keep two questions separate:
  1. **semantic proof:** can the required SNES operation be represented exactly?
  2. **production architecture/performance:** where/how should that operation live under N64 IMEM/bus/cadence constraints?
- Do not use PR #13 to “make E1 proofs fit” unless a later production integration decision earns it.

## Key Gate-C findings retained after compaction
- WH0–WH3 urgent-section repair is integrated on master; this preserves per-line window-edge changes at Road-valid MEDIUM precision.
- Earlier focused audit found PR #13 loader/tail-entry ABI coherent in source and no fatal source defect; real SP DMA/bus behavior remains L4 authority.
- H-COMP full-frame extra-surface design was rejected as an immediate production direction because memory/bandwidth/capacity make bounded strips more plausible; this is an architecture hypothesis, not a final performance proof.
- Primitive-Z metadata is viable in pinned ares, but Z/readback use requires explicit DP-completion ownership fencing.
- The robust E1a guest had to avoid the inherited repeated-tile fast-path artifact; the repeated-tile truncation is a **LAB/PROOF-GUEST issue**, not evidence that primitive-Z metadata is invalid.
- E1b's first red result was a **HARNESS BREAKPOINT bug**; corrected post-wait boundary `rsp_wait+0x14` is the established capture authority.
- E1d's first red result was a **HARNESS ADDRESS-COLLISION** with full-frame Z; proof scratch now lives at `0xA00E2000..20FF`.
- Ares/Mupen remain laboratories. None of E1a–E1e is real-N64 performance authority.

## M0–M2 durable milestone summary
- **M0 achieved:** real-N64 representative baseline mean **49.0/60**, essentially no VI idle; APU/audio dominated (~61.8%), disproving an assumed “65C816 first” optimization direction.
- **M1 achieved:** guest-cycle-bounded multi-op SPC700 JIT architecture validated; inherited timing/semantic debt repaired across the directed suite; real N64 Gothicvania reached **60/60 ×5** at Road-valid settings with ~11.5% VI wait.
- **M2 / Gate B achieved:** versioned base-system corpus converged on Gothicvania, Space Rescue Squad and Nova the Squirrel 2; all completed **60/60 ×5** on real N64 at their authoritative stages. Gate C therefore proceeds from a base-core performance architecture already capable of native cadence on that corpus.
- Detailed M0/M1/M2 experiment history, rejected hypotheses and exact artifacts remain in pre-compaction continuity history and canonical ROADMAP/PROFILING/VALIDATION docs.

## Current exact repo state
- `master@5b7134930a0ca859f6aa24e54102de116948e3ed` — integrated truth.
- `phase4/gate-c-h-comp-e1e-color-sub-kernel@3c4972f4e58ab89b8e8a2628ca322d353c069049` — **VALIDATED proof branch**, not integrated.
- PR #13 `phase4/gate-c-rsp-overlay-clean@84ecafad7cc3505d82f134b2672d9ed1146fedc0` — **OPEN / CANDIDATE**, not integrated.
- No long semantic experiment is currently required before starting the half-rule source audit.

## Operating protocol
Authority: **current Iron instruction > repo/artifact evidence > canonical docs > continuity > chats/memory/inference**. `master` is integrated truth; phase branches are candidates/proofs only.

Cadence: **technical batch → continuity checkpoint → technical batch → continuity checkpoint**. Checkpoint every material result, changed hypothesis, falsification, risk, lab limitation, meaningful CI/artifact result, branch/HEAD transition or next-action change **before advancing**.

Experimental discipline: **baseline → hypothesis → controlled change → measurement → interpretation → decision**. One important variable at a time. Record exact SHA/run/artifact/settings/environment and state what a result proves and does not prove.

Validation authority:
- host/direct tests for isolated semantics;
- N64 build gate for compile/layout;
- Mupen/ares for automated virtual-lab execution;
- real N64 for hardware-specific timing, bus/DMA/RSP/RDP behavior and final performance/cadence.

Do not build a second emulator around Sodium64. Do not let proof tooling become the project. Ask: **does this move a Road-to-1.0 gate?**

Historical full continuity before compaction: **`continuity@686f5a1da210f8fcd1b9cd6e74d5663f4d359c30:docs/CONTINUITY.md`**.
