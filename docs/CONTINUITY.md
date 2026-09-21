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

### Immediate next uncertainty
- **NEXT: half-color semantics, source-grounded before code.**
- Do **not** implement “just shift the final RGB555 result right one” from intuition. Derive exact SNES half behavior from pinned/reference implementation first, including:
  - add vs subtract;
  - per-channel rounding/truncation order;
  - whether half applies before/after clipping;
  - backdrop/fixed-color/subscreen cases;
  - the CGADSUB half-enable suppression rules (notably when sub-screen/fixed-color selection changes the second operand);
  - interaction with color-window gating.
- Only after an exact oracle is written should a child proof branch be created. Keep half separate from CGWSEL/window selection if possible so one semantic variable changes at a time.
- E1d and E1e are frozen evidence; do not mutate their validated branches.
- Do **not** merge scalar proof code into master simply because semantics pass.

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
