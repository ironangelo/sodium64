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
