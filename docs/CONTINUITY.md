# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

> **Continuity compaction / recovery (2026-09-28):** the live handoff again grew past the GitHub Contents API comfort boundary (~1.8 MB), which caused normal `fetch_file` reads to return an empty body. The complete pre-compaction Gate-C operational log is permanently preserved at continuity commit **`f175f2151d4adc0a9d0067e1714c649bc9088c66`**. Older pre-overflow history remains preserved at **`686f5a1da210f8fcd1b9cd6e74d5663f4d359c30`**, and the Sep-23–25 E4d block is also in `docs/CONTINUITY_ARCHIVE_E4D_2026-09-23_25.md`. This live file is intentionally compacted to current state, durable evidence, rejected explanations, risks and immediate next action. **Archived means preserved, not discarded.**

## RESUME HERE — current audited state (2026-09-28 UTC)


### ACTIVE — clean CGWSEL second-operand source discriminator (2026-09-28 UTC)

- Fresh child **`phase4/gate-c-hcomp-cgwsel-source-clean`** was created exactly from validated provenance authority **`ef1c37839fad4eca1339c92f4ee92f9a3463f301`**. Frozen controls: BG1 winner provenance `0x0C00 -> mask1`, CGADSUB BG1 eligibility, compact Sub/Main ownership, E1f half-add operation, TM-end Z cut, row mapping, fixed overlay ABI and the one-fresh-frame pinned-ares fence.
- **GATE DRIVER / question:** with winner, eligibility and arithmetic fixed, does real **CGWSEL bit1** select the H-COMP second operand correctly between semantic Sub and fixed color?
- **Canonical register audit:** current CPU transports raw `CGWSEL` in every 0x40-B section and `write_cgwsel` is raster-sensitive. SNES CGWSEL bit1 selects color-math second operand: **0=fixed color, 1=subscreen**; window bits remain zero in this rung. Current `COLDATA` is retained losslessly in PR#18 typed section markers, while the legacy section `SUB_COLOR` also carries COLDATA after master-brightness conversion. For this deliberately **full-brightness, constant-COLDATA** discriminator, canonicalizing `SUB_COLOR` back to RGB555 is exact; this avoids mixing a new raw-marker transport change into the source-selection experiment.
- **Controlled workload:** keep Main winner BG1 opaque red RGB555 **`0x001F`**, live Sub BG2 opaque green **`0x03E0`**, `CGADSUB=0x01` (BG1 math eligible), TMW/TSW=0, full brightness and the existing 8-line Sub lifetime. Set constant fixed color COLDATA to opaque blue RGB555 **`0x7C00`**. Only CGWSEL differs between the two authority guests: `0x00` => fixed; `0x02` => Sub.
- **Exact E1f results precommitted:** fixed-blue case must select addend `0x7C00` and produce packed half-add **`0x3C0F`**; Sub-green case must select addend `0x03E0` and produce **`0x01EF`**. Both cases must remain gate=1 with identical Main/Sub pixels and provenance.
- **Runtime hook:** frame-end H-COMP will keep the existing live Sub in its established field, canonicalize this section's `SUB_COLOR` as fixed RGB555, use only `CGWSEL&0x02` to choose the E1f addend, and append fixed/selected/CGWSEL/source evidence after the existing 16-B mailbox so prior provenance fields remain byte-compatible. No renderer ownership, provenance, CGADSUB or arithmetic mode change is allowed.
- **Guest implementation plan:** preserve startup/NMI addresses and existing rendering/HDMA geometry. Replace only the 5-B initial CGWSEL setup with same-size `JSR $81F0; NOP; NOP`; place an 11-B proof subroutine in already-unused pre-NMI NOP padding at `$81F0` that writes the requested CGWSEL value and COLDATA blue `$9F` to `$2132`, then RTS. The two guests therefore differ semantically only in the CGWSEL immediate (plus checksum); both execute the same nonzero fixed-color write.
- **Falsifiers:** either queue does not carry requested CGWSEL with stable fixed color; Main/Sub/provenance/guards regress; gate differs from1; fixed case does not select `0x7C00`/result `0x3C0F`; Sub case does not select `0x03E0`/result `0x01EF`; fixed ABI moves; or generic build/smoke regresses.
- **Non-claims:** this rung does not prove mid-frame changing COLDATA, brightness ordering below full brightness, absent-Sub fallback/HALF suppression, color windows/clip/prevent, add/sub/half mode selection, BG3/BG4/OBJ/backdrop provenance, throughput or real-N64 RDP->RSP fencing.
- **IMPLEMENTED runtime candidate `6786bf55c08d5ec689b234bc2759d4b3f37ba457`:** only `src/rsp_hcomp.S` changes runtime. It canonicalizes section `SUB_COLOR` to fixed RGB555, chooses `t7 = fixed` for `CGWSEL bit1=0` or `t7 = live Sub` for bit1=1, and feeds the unchanged E1f expression. Existing first 16 B of the provenance mailbox remain structurally identical; appended words publish fixed RGB555, selected addend, raw CGWSEL and normalized source flag. Mailbox DMA expands 16 -> 24 B.
- The source-selection path adds exactly **19 instructions / 76 B** before the fixed switch region; H-COMP padding is reduced mechanically **`0x134 -> 0xE8`**. Predicted public ABI and total H-COMP size remain unchanged; exact ELF/build is authority.
- Deterministic guest generator added on host-only head **`d0d0e50a000266d8b59afdb20cb3d88731cc438e`**. It preserves all existing instruction addresses by replacing the original 5-B CGWSEL setup with same-size `JSR $81F0; NOP; NOP`, placing an 11-B subroutine in verified unused NOP padding before frozen NMI `$8200`. Both guests write nonzero fixed blue via `COLDATA=$9F`; only their CGWSEL immediate differs (`0x00` vs `0x02`, plus checksum).
- Generic **Build and Validate `36376954032`** dispatched on exact host/runtime head `d0d0e50a...`. Dedicated semantic authority is not yet implemented.
- **STATUS: IMPLEMENTED / BUILD RUNNING.** Reject on any fixed ABI movement or compile/smoke regression before creating the semantic ares matrix.


### Phase / authority

- **Phase:** M3 / **Gate C — base-system fidelity and compatibility**.
- **Integrated truth:** `master@7cc8facfe8643fb85888f301f79995575830521d`, merge of PR #18 (“preserve CGRAM epochs through RSP replay”).
- **Open PRs:** none at this checkpoint.
- **Current candidate:** `phase4/gate-c-hcomp-main-provenance-clean@ef1c37839fad4eca1339c92f4ee92f9a3463f301`.
- **Semantic runtime commit:** `7adf58be206709d03733d365602ab558caf072d4`; `ef1c...` is a host/workflow-only ROM-hash pin on top.
- **Exact runtime hashes:** ROM `5cad678264d87f52c402eedb7e1ab8b26af01a979570299dbf947599607dad33`; ELF `092bf2ee7e67d153d260f19eeb99ce2f9f975689fb9b9716ce1742556087f65f`.
- **Classification:** **ARCHITECTURE PROOF / VALIDATED / STAGE CLOSED** for clean regular-BG Main winner provenance driving real BG1/BG2 CGADSUB eligibility on live rendered operands.
- This candidate is **not merged** and is not yet production compositor authority.

### Final clean BG1/BG2 winner-provenance result — VALIDATED

- Same-head generic **Build and Validate `36373014434 SUCCESS`**: normal build, PROFILE build and pinned Mupen/LLE smoke all green.
- Dedicated **Gate C H-COMP Main Provenance Clean `36373014424 SUCCESS`** on exact head `ef1c3783...`.
- Final evidence artifact **`10949629224`**, digest **`sha256:3c8b5e660706cfccccbaebb5c8ea13689be112cd6c4fadd5271fd8aa015a5f50`**.
- Classifier: **`HCOMP_MAIN_BG12_PROVENANCE_GATING_VALIDATED`**, `passed=true`, `color_operands_stable_within_winner_pairs=true`, `provenance_stable_within_winner_pairs=true`.
- Exact executable contract remains:
  - `draw_bg=0xA40013A8`
  - `hcomp_screen_switch=0xA4001760`
  - `draw_mode7_entry=0xA4001788`
  - regular/Mode7 RSP text **0x1000 / 4096 B** each
  - H-COMP text **0x790 / 1936 B**
  - `resident_imem_growth=0`
  - provenance scratch `0xA00E2000..0xA00E317F`
  - sample `0xA00E2018`
  - Set-Z underflow base `0x000DFD00`
  - provenance lifetime **section0 TM only**
  - disable boundary **TM end before next section**.

#### Four-state first-hand matrix

| Case | Main winner / color | Sub color | Provenance | CGADSUB | Gate | Result |
|---|---|---|---|---|---|---|
| BG1×CG1 | BG1 red, RGB555 `0x001F` | green `0x03E0` | `0x0C00 -> mask 0x01` | `0x01` | ON | exact E1f half-add `0x01EF` |
| BG1×CG2 | BG1 red `0x001F` | green `0x03E0` | `0x0C00 -> mask 0x01` | `0x02` | OFF | raw Main `0x001F` |
| BG2×CG1 | BG2 green `0x03E0` | red `0x001F` | `0x1400 -> mask 0x02` | `0x01` | OFF | raw Main `0x03E0` |
| BG2×CG2 | BG2 green `0x03E0` | red `0x001F` | `0x1400 -> mask 0x02` | `0x02` | ON | exact E1f half-add `0x01EF` |

- Exact mailboxes:
  - BG1×CG1: `001F,03E0,01EF,0001,0C00,0001,0001,0000`
  - BG1×CG2: `001F,03E0,001F,0000,0C00,0001,0002,0000`
  - BG2×CG1: `03E0,001F,03E0,0000,1400,0002,0001,0000`
  - BG2×CG2: `03E0,001F,01EF,0001,1400,0002,0002,0000`
- In every state the compact provenance surface is exact: **2,048 active winner-tag words + 192 sentinel border words**, and **both prefix and suffix guards are intact**.
- BG1 states: semantic Main exact **2,048 red `0xF801` + 2,432 sentinel**; Sub exact **2,048 green `0x07C1` + 192 sentinel**.
- BG2 states: semantic Main exact **2,048 green `0x07C1` + 2,432 sentinel**; Sub exact **2,048 red `0xF801` + 192 sentinel**.
- Exactly one physical Main framebuffer is rendered in each independent capture; the other two are untouched. Physical slot identity may rotate between emulator processes and is not semantic identity.
- Both section queues independently carry the requested `TM/TS/CGADSUB/split` matrix.
- Every capture uses one fresh renderer-frame reentry with `guest_frame_delta=1`, **RSP HALT**, **DPC_CURRENT=DPC_END=0x000C58**, and `bufferBusy=false`. Pinned-ares `PIPE_BUSY=true` remains diagnostic only.

### What this proves

- **VALIDATED:** the clean regular-BG renderer can emit first-hand winner identity into a bounded per-pixel provenance carrier.
- **VALIDATED:** BG1 maps to stored winner tag `0x0C00` and native CGADSUB mask `0x01`; BG2 maps to `0x1400` / `0x02`.
- **VALIDATED:** H-COMP can consume that winner identity and gate the already-validated arithmetic path using the correct real CGADSUB bit, not a guest-hardcoded winner.
- **VALIDATED:** the compact provenance lifetime can be bounded to section0 TM and cut before any later-section RDP work.
- **VALIDATED:** the repair does not grow resident IMEM or move the frozen renderer/H-COMP public ABI.

### What this does NOT prove

- Overlapping BG priority arbitration beyond the controlled single-Main-BG workloads.
- BG3/BG4/OBJ/backdrop provenance.
- OBJ palette-group color-math exception.
- `CGWSEL` second-operand selection (Sub vs fixed color), clip/prevent/color-window semantics.
- General add/sub/half mode selection from `CGADSUB` bits; only the already-authoritative E1f half-add operation is exercised here.
- Full-band/full-frame compositor throughput.
- Production-safe real-N64 RDP→RSP ownership/fencing; the proof-time framebuffer/provenance DMA reads are architecture evidence under pinned ares.
- Real-N64 cadence/performance. Emulators remain laboratories, not final authority.

### RESUME NEXT — GATE DRIVER

**Next controlled rung: CGWSEL second-operand source selection on the clean live path.**

1. Start from `phase4/gate-c-hcomp-main-provenance-clean@ef1c3783...`; do not import old cumulative E2g/E3/E4 compositor source.
2. First audit the exact current `CGWSEL` carrier/register semantics in repo + canonical SNES behavior. Do not assume bit layout from memory.
3. Freeze the newly validated controls: winner provenance, BG1/BG2 CGADSUB eligibility, compact Sub/Main ownership, TM-end Z cut, row mapping, fixed ABI and one-frame fence.
4. Build the smallest discriminator where Main winner, CGADSUB eligibility and arithmetic operation stay fixed, while only the **second operand source** changes between semantic Sub and fixed color according to CGWSEL.
5. Precommit exact RGB555 operands/results and require carrier + live pixels + provenance + mailbox agreement.
6. Only after CGWSEL source selection is green, add a separate controlled rung for **add vs subtract vs half** mode semantics. Do not combine those variables.
7. BG3/BG4/OBJ/backdrop provenance, windows/clip/prevent and throughput remain later rungs.

**Immediate action:** inspect current CGWSEL/fixed-color transport and identify the smallest source-selection hook that reuses the validated live Main/provenance path without changing renderer ownership.

**STATUS: VALIDATED / STAGE CLOSED.**

---

## Durable Gate-C chain retained in the live handoff

### 1. PR #18 CGRAM epoch transport/replay — MERGED

- `master@7cc8facf...` includes PR #18.
- Typed CGRAM events survive CPU capture → section queues → RSP replay/raw shadow.
- This is integrated truth and remains the representation source for later H-COMP work.

### 2. Clean first-hand Main/Sub color ownership — VALIDATED

- Final host-only head `phase4/gate-c-hcomp-main-sub-pixels-clean@4ec7fe3dbf2c0249221730dae0b2c7b06cf9fabe`.
- Dedicated `36356687503 SUCCESS`, artifact `10944247264`, digest `sha256:e3adf4e0eeb13f18054ca9615915fa76f48329039715e30df2a03de41737a544`.
- Compact Sub `0xA00E4000`: exact green active strip.
- Main: exact red active strip in **published physical rows8..15**, with rows0..7 untouched.
- **REJECTED:** old row0-only Main oracle; its failure was a host false negative, not a target-switch defect.

### 3. Clean live BG1 CGADSUB gating — VALIDATED

- Final host-only head `phase4/gate-c-hcomp-cgadsub-gating-clean@69c64fa09d22d71bb653701b0300da6f9ac1eb12`.
- Dedicated `36358604516 SUCCESS`, artifact `10944812755`, digest `sha256:fb5fdb747468ddc584d005851843e0b8f0818e4342166348e1e697c610113f1f`.
- Same rendered Main/Sub pair: CGADSUB BG1 disabled → raw Main; enabled → exact E1f `0x01EF`.
- **REJECTED:** requiring the same physical triple-buffer slot across independent emulator processes.

### 4. Clean BG1/BG2 winner provenance + CGADSUB eligibility — VALIDATED

- Current stage described above.
- First semantic attempt proved tags/gates but wrote Z beyond its owned arena.
- Final TM-end lifetime repair closes those bounds without weakening the oracle.

---

## Rejected explanations / durable negative knowledge

- **REJECTED:** build green implies semantic correctness.
- **REJECTED:** host/emulator full speed implies N64 full speed.
- **REJECTED:** pinned-ares `PIPE_BUSY` must clear for a completed submitted list. In the pinned ares model it remains sticky without Sync Full; completion authority for this lab is RSP HALT + `bufferBusy=false` + `DPC_CURRENT==DPC_END`.
- **REJECTED:** GDB R4300 single-step at the prelaunch fence. It can cross the `jr` delay slot and clear SP HALT. The validated laboratory fence uses the two-breakpoint no-single-step protocol.
- **REJECTED:** semantic Main lives in published framebuffer rows0..7. Validated mapping is rows8..15 for this workload.
- **REJECTED:** physical FB1/FB2/FB3 slot identity is stable across independent ares processes.
- **REJECTED:** a compact Z arena is safe merely because intended color pixels occupy only the compact strip. Z-update lifetime is global RDP state and must be explicitly bounded.
- **REJECTED:** disabling Z in the *next* TS→TM switch is sufficient. Section backdrop work occurs before that switch; the cut must happen at **TM end before next_section work**.
- **REJECTED:** weakening guards or allocating a large full-frame provenance surface to hide the spill. The compact E1c-style ownership model won after correcting lifetime.
- **REJECTED:** importing the old cumulative E2g/E3/E4 compositor as the clean solution. Historical branches are concept/evidence references only unless a specific piece independently earns reintroduction.

---

## Laboratory / validation boundaries

- Pinned ares: `17813a3ccda21ab9bd45f09bfc2f91196dbf50ff`, N64-only, RSP recompiler forced off for the established proof lab.
- Mupen/LLE smoke is a generic hygiene check, not semantic color-math authority.
- Real N64 remains final authority for cache/TLB, RSP/RDP synchronization, DMA/bus behavior, VI/AI cadence and performance.
- Current proofs are synthetic architecture/measurement proofs. They are not broad software-compatibility claims.
- Do not upload commercial ROMs to the repo. Continue using deterministic/open diagnostic guests until a representative software rung is needed.

## Fixed engineering constraints carried forward

- Preserve frozen renderer/H-COMP overlay addresses unless a deliberate architecture change is separately justified and measured.
- Preserve the validated semantic screen order: low byte TS, high byte TM; shared-screen behavior must not be silently reintroduced from old workarounds.
- Preserve compact Sub ownership and current Main published row mapping as controls while testing color-math semantics.
- Prefer one semantic variable per experiment: `baseline → hypothesis → controlled change → measurement → interpretation → decision`.
- Keep proof-only provenance/fences classified as architecture evidence until a production-safe design wins on real hardware constraints.
- Every candidate must retain normal build + PROFILE build + branch-delay checks; pinned Mupen smoke is generic hygiene, pinned ares dedicated artifacts are experiment authority for these current synthetic discriminators.

## Road-to-1.0 direction

The target is unchanged: N64 real, correct native cadence, one SNES frame per corresponding native frame, frameskip 0, full-rate SPC700/APU and correct audio, high CPU/PPU/DMA/HDMA/timing fidelity, broad compatibility, no per-game manual modes, DSP-1 family, SuperFX/SuperFX2, SA-1, and final hardware validation.

Current Gate-C work is moving that road because it is replacing the inherited renderer's Main/Sub/color-math approximation with measured, bounded semantics. Do not let the proof harness become a second project; each next batch must close a compositor/fidelity uncertainty needed by the Road.
