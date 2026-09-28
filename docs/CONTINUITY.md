# Sodium64 fork continuity

Canonical live handoff for `ironangelo/sodium64`.

> **Continuity compaction / recovery (2026-09-28):** the live handoff again grew past the GitHub Contents API comfort boundary (~1.8 MB), which caused normal `fetch_file` reads to return an empty body. The complete pre-compaction Gate-C operational log is permanently preserved at continuity commit **`f175f2151d4adc0a9d0067e1714c649bc9088c66`**. Older pre-overflow history remains preserved at **`686f5a1da210f8fcd1b9cd6e74d5663f4d359c30`**, and the Sep-23–25 E4d block is also in `docs/CONTINUITY_ARCHIVE_E4D_2026-09-23_25.md`. This live file is intentionally compacted to current state, durable evidence, rejected explanations, risks and immediate next action. **Archived means preserved, not discarded.**

## RESUME HERE — current audited state (2026-09-28 UTC)


### CHECKPOINT — clean CGWSEL second-operand source selection VALIDATED (2026-09-28 UTC)

- **ARCHITECTURE PROOF / VALIDATED / STAGE CLOSED:** exact branch head `phase4/gate-c-hcomp-cgwsel-source-clean@762250a95c6d2ef4bda1b2f4d82e255c43889c83`.
- Semantic runtime change is `6786bf55c08d5ec689b234bc2759d4b3f37ba457`; later commits are host-only guest/oracle/workflow work and the exact ROM-hash pin. Runtime hashes: ROM **`f4d3c58ea6ae05ef89f8b78b66be3b4c1e8b8efdb4bcae52069f58161a49741a`**, ELF **`cf43093a37a979ee9c01b0a92402b772a82b2ae5fcb544035fe0c9b3c88a08aa`**.
- Dedicated **Gate C H-COMP CGWSEL Source Clean `36377395203 SUCCESS`**; artifact **`10951817024`**, digest **`sha256:483759afdb3fc719807c72c55c62095956dc580b57f6c6ba3b5114862a23c96e`**. Classifier: **`HCOMP_CGWSEL_SOURCE_SELECTION_VALIDATED`**, `passed=true`.
- Same-head generic **Build and Validate `36377395162 SUCCESS`**: normal build, PROFILE build, branch-delay audit and pinned Mupen/LLE smoke all green.
- Frozen controls held exactly across both captures: Main BG1 red `0x001F`, live Sub BG2 green `0x03E0`, provenance `0x0C00 -> mask1`, `CGADSUB=0x01`, compact ownership, TM-end Z cut and one-fresh-frame fence. `main_sub_provenance_identical_across_source_states=true`; provenance guards intact.
- **Fixed case:** `CGWSEL=0x00`, fixed blue `0x7C00`, selected addend `0x7C00`, exact E1f half-add result **`0x3C0F`**.
- **Subscreen case:** `CGWSEL=0x02`, selected addend live Sub `0x03E0`, exact E1f half-add result **`0x01EF`**.
- Appended source mailbox is consistent with the intended selector while the original first 16 B remains byte-compatible: fixed/source state `[fixed=7C00, selected=7C00, cgwsel=0000, source=0000]`; Sub state `[fixed=7C00, selected=03E0, cgwsel=0002, source=0001]`.
- ABI remained frozen: regular/Mode7 RSP text **0x1000**, H-COMP **0x790**, `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788`, resident IMEM growth zero.
- **Still NOT PROVEN:** add/sub/half mode selection, absent-Sub HALF suppression, mid-frame fixed-color history, brightness ordering below full brightness, color windows/clip/prevent, BG3/BG4/OBJ/backdrop provenance, production-safe real-N64 RDP->RSP fence, throughput and real-N64 cadence/performance.
- The earlier `36377226182 FAILURE` remains classified **REJECTED AS SEMANTIC EVIDENCE / TOOLING-PIN ONLY**: it stopped at the deliberately stale ROM pin before captures. The corrected exact-head run above is authority.

### ACTIVE — clean CGADSUB add/sub/half mode discriminator (2026-09-28 UTC)

- **GATE DRIVER:** with Main winner, CGADSUB eligibility, CGWSEL source selection, Main/Sub operands and provenance now fixed, validate the operation bits of real `CGADSUB` independently: add vs subtract and half vs full.
- Start from exact validated parent **`762250a9...`**. Do not import the old cumulative E2g/E3/E4 compositor as a solution; historical arithmetic proof code may be read only as evidence/reference and individual pieces must re-earn entry.
- First audit the exact current carrier and canonical SNES `CGADSUB` bit layout from repo evidence/reference. Freeze `CGWSEL=0x02` (live Sub), BG1 winner/eligibility, operand colors, row mapping, provenance, section geometry, ABI and fence.
- Use the smallest matrix that distinguishes **ADD full / ADD half / SUB full / SUB half** while holding every other semantic variable constant. Precommit exact RGB555 expected results and require queue carrier + selected operand + provenance + result agreement.
- Explicitly separate normal half behavior from the later special case where HALF is suppressed when the second operand is fixed color / no subscreen contribution; do not combine those questions in the first mode matrix.
- Falsifiers: requested CGADSUB bits do not survive to the section, Main/Sub/provenance changes between cases, gate changes unexpectedly, any exact arithmetic result mismatches, ABI moves, guards regress, or generic build/smoke regresses.
- **Immediate action:** audit current `CGADSUB` transport and the existing clean/historical arithmetic helpers, then create the child branch and the smallest controlled four-state mode matrix.

- **IMPLEMENTED candidate:** fresh child `phase4/gate-c-hcomp-cgadsub-modes-clean` from exact validated parent `762250a95c6d2ef4bda1b2f4d82e255c43889c83`. Runtime commit **`dee7fdb10731cb059a985ea45e8642587c6a8143`** changes only `src/rsp_hcomp.S`; current host/workflow head is **`cd9a32b47dc5bd1541183262d6fd66c18f4d114c`**.
- Controlled four-state matrix is precommitted with `CGWSEL=0x02`, Main red `0x001F`, live Sub green `0x03E0`, BG1 winner/provenance and eligibility fixed. Raw `CGADSUB` states/results: **ADD full `0x01 -> 0x03FF`**, **ADD half `0x41 -> 0x01EF`**, **SUB full `0x81 -> 0x001F`**, **SUB half `0xC1 -> 0x000F`**.
- Runtime now decodes bit7 (add/subtract) and bit6 (full/half) only after the already-validated winner gate and CGWSEL source selector. Packed saturating add/sub formulas are per-channel; the previously validated E1f expression remains the half-add path. No CPU/PPU transport, provenance, renderer ownership, source selector or mailbox layout changed.
- Net H-COMP growth is mechanically absorbed from unused fixed-slot padding: `.byte 0:0xE8 -> 0x5C`; intended public ABI remains `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788`, H-COMP total `0x790`, resident IMEM growth zero. Build/ELF is authority and has not yet validated this prediction.
- Deterministic guest generator, strict four-state ares oracle and executable contract are present on the child. Dedicated workflow `Gate C H-COMP CGADSUB Modes Clean` is installed on head `cd9a32b4...`.
- **Deliberate first-run pin protocol:** the new dedicated workflow intentionally retains the validated parent ROM SHA `f4d3c58e...`. The first build must therefore stop at that stale pin *after* source/binary contract + branch-delay checks if the candidate builds cleanly. That failure is expected tooling/pin evidence only; capture must not run until the exact new ROM hash is measured and the workflow-only pin is replaced.
- **STATUS: IMPLEMENTED / CI DISPATCHED, semantic result UNKNOWN.** Do not interpret generic build success or the deliberate pin failure as arithmetic correctness. Next action is to inspect the exact-head run, verify ABI/build, pin the measured ROM hash host-only, then require the four first-hand captures to pass.
- **EXPECTED PIN FAILURE / MEASUREMENT PROOF:** dedicated run **`36419660606 FAILURE`** on head `cd9a32b4...` stopped exactly at the deliberately stale parent ROM SHA after every preceding gate passed. Artifact **`10968607683`**, digest **`sha256:0f46e9c7c612a8c00dab47343d5177aac9c8b5bcbc8b08aa7b87cf26e916f756`**. No semantic captures ran.
- Exact new candidate hashes measured by that run: ROM **`53df19d9d0b9f0996d1bb7aca15f744ab28e67525362656ef01f726eaa9e576c`**, ELF **`fa9e863fd4a7927e3591f86ad54154b1e8d156c3f6dc147cbca87bcea6ea8483`**.
- **ABI prediction VALIDATED:** executable contract `HCOMP_CGADSUB_MODES_EXEC_CLEAN_CONTRACT_VALIDATED`; regular/Mode7 RSP text `0x1000`, H-COMP `0x790`; `hcomp_screen_switch=0x1760`, `draw_mode7_entry=0x1788`, resident IMEM growth zero; all three branch-delay audits pass.
- **RECLASSIFIED:** run `36419660606` is **TOOLING/PIN FAILURE ONLY**, not arithmetic evidence. Immediate action is host-only: replace exactly the stale ROM pin with `53df19d9...`; do not change runtime, guests, oracle, capture or ares pin.
- Host-only exact-pin commit **`73d9d08037151457e53c6150c8ebeeb5a176f4ac`** changes only the workflow ROM SHA to `53df19d9...`; semantic runtime remains `dee7fdb1...`.
- Exact-head reruns dispatched: dedicated **`36419920887`** and generic **Build and Validate `36419921205`**. **STATUS: ABI VALIDATED / SEMANTIC CI RUNNING.**


### Phase / authority

- **Phase:** M3 / **Gate C — base-system fidelity and compatibility**.
- **Integrated truth:** `master@7cc8facfe8643fb85888f301f79995575830521d`, merge of PR #18 (“preserve CGRAM epochs through RSP replay”).
- **Open PRs:** none at this checkpoint.
- **Current candidate:** `phase4/gate-c-hcomp-cgwsel-source-clean@762250a95c6d2ef4bda1b2f4d82e255c43889c83`.
- **Semantic runtime commit:** `6786bf55c08d5ec689b234bc2759d4b3f37ba457`; later commits are host/oracle/pin only.
- **Exact runtime hashes:** ROM `f4d3c58ea6ae05ef89f8b78b66be3b4c1e8b8efdb4bcae52069f58161a49741a`; ELF `cf43093a37a979ee9c01b0a92402b772a82b2ae5fcb544035fe0c9b3c88a08aa`.
- **Classification:** **ARCHITECTURE PROOF / VALIDATED / STAGE CLOSED** for clean CGWSEL second-operand selection on the live Main/Sub/provenance path.
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

**Next controlled rung: real CGADSUB add/sub/half operation selection on the clean live path.**

1. Start from `phase4/gate-c-hcomp-cgwsel-source-clean@762250a9...`.
2. Audit exact current CGADSUB transport and canonical bit semantics before editing.
3. Freeze validated winner provenance, BG1 eligibility, CGWSEL=`0x02` live-Sub source, Main/Sub operands, compact ownership, TM-end Z cut, row mapping, fixed ABI and one-frame fence.
4. Build a four-state discriminator for ADD full / ADD half / SUB full / SUB half with all other variables constant.
5. Precommit exact RGB555 results; require carrier + selected operand + provenance + result agreement.
6. Keep HALF suppression for fixed-color/no-Sub as a separate later discriminator.
7. Only after the mode matrix is green, proceed to the next missing compositor semantic (likely the HALF special case or remaining provenance/window interaction), chosen from evidence.

**Immediate action:** inspect current CGADSUB carrier plus clean/historical arithmetic helpers, then create the minimal child experiment without importing old cumulative compositor state.

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
