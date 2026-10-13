# R44 - Sub presence in coverage, work in progress

## 2026-10-12 - fixed-space repair and local qualification

IMPLEMENTED, not MEASURED/VALIDATED. Fast selector now occupies its owned
1768..1783 tail; admission ends within1740. Setup publishes the shared s8
alpha class in its owned1768..1783 tail; fixed context entry15B0 is unchanged.
Math canonicalization uses its176C..1787 tail; full-row512-byte batches remain
enabled and all1000-byte slot/.org limits pass. Main/Mode7 remain4096 bytes.
SUB_ALPHA=0 recompilation preserves all13 RSP text/data banks byte-exact to R43.

Linked numeric proofs:16 selectors,80 actual Setup handoffs,288 retired command/
alpha cases,48 Main Z transitions;12 Math cases70912 pixels plus3 Mode7 Z
fallback controls;36 RDP HALF cases248832 pixels including opaque black/absent
Sub;19 fixed-window and28 fixed-RDP cases retain byte-exact implementations.
Delayed DMA and VRAM/OAM restoration pass; re-enabled presence DMA and actual
OAM-target overwrite mutations are rejected. The old presence-pointer mutation
became inert after retiring that DMA, so the guard now mutates the live Sub DMA.
Fixture bindings use the complete HALF/fixed-RDP/fixed-window/Math chain and
actual relocated D4400 backup, not obsolete partial-chain/D2400 assumptions.

576 decoder/448 span/two initializers/four guards,30 adaptive/source cases/four
unsafe faults,boot12/TV5,41 arena owners,branch delays and actual CPU/RSP backup
sites pass. Runtime endD1A88 < D4000. Existing raw/direct composition never
invokes presence Math; compact admission refreshes the descriptor before use.
Main mode restores0025 after the Sub fence; Mode7 keeps its original Z input.
Numeric command/row tests are not Mode7 edge rasterization or native fidelity.

Next: freeze this exact artifact/plan and run the established physical ALttP
rain12944 route with four frames and8192 paused PCM versus preserved control/
R43, then quiet20-second checksum/settings/wait measurement and finally menu/
coordinate8 restoration/readback. No broad CI before native value. R43 and
master stay preserved. Full60/audio/corpus goal remains open; private data local.

## Historical prototype checkpoint

HYPOTHESIS: remove Sub Z writes and one packed-Math presence input DMA by
deriving presence from Sub RGB5551 coverage. Main winner Z stays unchanged.
R42 physically proved1024 original rectangle cases with production palette;
R43 rain still36.804 versus32.289 control. This targets real renderer/bus work.

WIP implementation, NOT SAFE ARTIFACT/NOT MEASURED: SUB_ALPHA1 requires
ADAPTIVE_NOSPAN1, defaults0. Distinct mode descriptors in unreachable Mode2/
Mode3/Mode4 padding after first layer terminators; Mode7 keeps original Sub Z
path. Resident28-byte mode/alpha wrapper replaces unused no-Sub span gate;
Sub/Main fills use63/255, alpha compare threshold1 preserves zero discard.
Main transition restores Z mode/image after the existing fence. General Math
skips presence DMA and canonicalizes Sub low bit to0400/0C00 tags. RDP HALF
reads Sub colors and canonicalizes the same tags; fixed paths admitting no
real Sub keep their old winner semantics. Register/source ownership and raw
fill alpha still need complete emitted-code proofs before any hardware load.

Local compile failed rsp_hcomp_fast.S .org backwards: the six-instruction mode
selection exceeded its fixed space. Other arithmetic banks have not yet been
checked for capacity. Do not weaken .org/arena guards, deliver or install this
build. No R44 artifact has been loaded. Next reorganize mode selection into
owned code space, compile, then prove complete general/HALF/fixed/raw/Mode7
semantics and delayed DMA before short N64 A/B. Avoid unrelated full CI.

R43 source/runtime and all earlier measured artifacts remain preserved on
separate branches. N64 is responsive menu with coordinate8 restored/readback,
no live COM3 worker. Root owns COM3 exclusively. Firmware/saves/config and
master unchanged. Commercial inputs/captures/hashes private. Full goal open.
