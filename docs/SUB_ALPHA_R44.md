# R44 - Sub presence in coverage, work in progress

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
