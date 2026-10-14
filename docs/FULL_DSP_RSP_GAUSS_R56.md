# R56 - eight-lane Gaussian primitive and physical transport discriminator

Status: IMPLEMENTED; native RSP performance and integration remain pending.
R55's CPU batching cost remains rejected. This isolated branch retains its
semantic boundary but moves it from DSP phase0 to phase22. Voice0 targets the
current sample's V3c30; voices1..7 target the next sample's V3c1..19. The local
full-core differential gate passes all partial starts, register/RAM writes,
KON/PMON/noise, reset, state export/import and PCM comparisons. This supplies
eight DSP clocks before first use instead of phase0's one; scheduling and
renderer sharing on hardware are still unproven.

The actual assembled RSP program is80 bytes/20 instructions. Four VMUDM
operations use signed samples and unsigned Gaussian coefficients shifted5:
their MID16 results implement each original product's floor division by2048.
VADDC retains the original first-three signed16 wrap; clearing VCO before
VADD supplies the final saturation, followed by the original even mask.
Inputs occupy DMEM000..07F, masks080..08F, outputs090..09F. The program has
no DMA/RCP/reciprocal instructions and changes vectors/ACC/VCO only.

The linked binary passes614656 directed lanes spanning all256 fractions and
seven signed edge samples in all four taps, plus65536 randomized lanes.
Four instruction mutations fail. All4096 DMEM bytes outside the16-byte result
remain unchanged; entry vectors/ACC/flags are randomized. These are arithmetic
and ownership results, not RSP cycles or native-game performance.

`DSP_RSP_GAUSS_PROBE=1` is default0 and requires the existing paused canonical
scene-state/full-RSP-context/trace/audio guards. It extends the existing
`state-rsp-roundtrip` diagnostic, replacing its zero-context exercise with
64 synthetic eight-lane packets. The complete original700-byte architectural
context and8192-byte SP memory follow the existing backup/readback/restore
gates. Result mismatch and bounded task-wait failure still restore the owner;
inability to HALT or restore restricts the emulator to menu recovery.

Each packet prepares cached private stack inputs outside timing, times the independent scalar
formula, then times128-byte PIO upload/start/wait/16-byte output readback.
Kernel/mask installation is measured separately. Four pinned coefficient
sets and deterministic samples make all512 outputs independently checkable.
The host transaction executes actual capture/primitive/restore binaries;
238 cases cover92 transfer failures,74 read corruptions, all67 wait positions
and a result mutation. All64 primitive timeouts safely stop and restore.
The unchanged default zero-context transaction also passes. The context model
passes637 roundtrips/65536 MID values/nine mutations; RPC254+1000 fuzz pass.

Native artifact: `sodium64-rsp-gauss-r56-context-v7`, FULL_DSP_PROBE0,
DSP_FULL_GAUSS_BATCH0, SCENE_STATE1, SCENE_RSP_CONTEXT1, SCENE_SLOT0,
SCENE_RSP_REBIND0, SIGNAL_PROFILE1, DSP_RSP_GAUSS_PROBE1. Its diagnostic C
uses-Os; no arena/event capacity was moved or reduced. Static endD1E28 is
belowD4000; all43 owners,24576 events,194 slots, boot and actual DMA bounds
pass. All13 renderer banks equal the previous non-slot context artifact;
both context banks equal the qualified delayed-entry pair. SLOT uses a
different arena and is not the renderer binary baseline for this artifact.
Earlier v5 O2 link overlap was rejected locally; no failed artifact installed.

Physical question: does an eight-wide primitive including this PIO handshake
beat the scalar formula and fit the first-use window? Three64-packet trials
are planned at paused ALttP600/601/602. Require512 exact outputs/checksum each,
full context/SP readback, unchanged67200 pixels/8192 PCM bytes/head/registers,
guest boundaries, step660 and final coordinate8/menu/install/readback.
Raw game captures/inputs remain private. A failed PIO deadline rejects this
transport, not every possible DMA or resident RSP design. No inference from
20 instructions, no broad CI or promotion before material native evidence.

Full DSP/SPC timing, DAC output, simultaneous rendering, game fidelity,
sustained native60/50, required corpus and master integration remain open.
R44 is experimental and R45 remains off. Master and all prior evidence stay
preserved. Numeric original-fixture/preflight evidence is in the companion
`FULL_DSP_RSP_GAUSS_R56_PREFLIGHT.json`.
