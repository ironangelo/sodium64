# Scene save-state feasibility - 2026-10-12

HYPOTHESIS/design only; no serializer or restore feature is implemented or
qualified by this document. User proposed states to shorten native iteration
and welcomed extra controls when they answer the active goal efficiently.

## Measured reason to investigate

The R44 native rain run took about259 seconds between its frame600 image and
rain12944 image. Initial menu-mediated launch took45.95 seconds; four image
exports themselves total0.56 seconds. Replay, not export complexity, dominates
setup. A state before the discriminating scene could remove most repeated
history, while keeping all emulated work during measured windows intact.
These times are private transport receipts; no private payload/path/hash is
published. The existing deterministic replay remains the control.

## Current implementation and reusable foundation

`remote_control.c` treats `snapshot` as a completed framebuffer export, not a
machine state. There is no corresponding machine-state restore command.
`remote_control.S` already parks at the frame bridge and preserves normal
GPR64, HI/LO and EPC in a272-byte saved context, on a separate4096-byte stack.
The bridge can originate inside the PPU's outer TLB exception and temporarily
allows VI while paused. RSP retirement is established before image export;
final DP writes need the additional explicit export fence. These are useful
foundations, not proof that a full state is immediately restorable.

Mutable state includes128KiB WRAM,32KiB SRAM working memory,64KiB guest VRAM,
CGRAM/OAM/I/O and DMA/HDMA, S-CPU registers/mode/event state,64KiB APU RAM plus
SPC registers/timers/ports/halt/cycle budget, and complete implemented DSP
voice/envelope/BRR/noise/mixer history. Controller latches and mapper/chip
state also matter. APU JIT tags/code, renderer texture/dirty/palette caches,
double section queues, RSP scalar/vector state and source pointers need
explicit ownership/reconstruction rules. Host Count/Compare, VI/AI/DP and USB
transport state cannot simply be copied back as arbitrary N64 RAM.

The [Snes9x snapshot format](https://github.com/snes9xgit/snes9x/blob/master/docs/snapshots.txt)
independently documents CPU/registers/PPU/DMA/memories/sound/controllers/timing
and separate enhancement-chip blocks. It is a useful coverage checklist,
not a format Sodium64 can import unchanged.

## Decision and first acceptance gate

Worth a bounded diagnostic prototype after preserving R44 qualification;
keep it isolated from the measured renderer. No new UI or profiler is needed
for the first question: can a quiescent state reproduce the same subsequent
guest frames, PCM/DSP state and event progression as uninterrupted replay?

First map all mutable/derived/immutable owners and the paused continuation.
Choose either a fully proved saved continuation or a clean instruction/event
boundary; do not assume the frame callback is an instruction boundary. Prove
SP/DP/DMA/AI retirement and cache coherence. Export a versioned, bounded,
checksummed private state, validating ROM identity/settings/layout before any
restore mutation. Initially require proved layout compatibility. Cross-build
renderer experiments must rebind current immutable code/DMEM descriptors and
reconstruct caches/JIT; copying old host addresses into a new build is invalid.
This cross-build question is essential to the expected A/B time savings.

Compare uninterrupted replay versus restore at1/60/600 subsequent frames:
images, complete implemented CPU/SPC/DSP/memory state, PCM and event counts.
Then repeat actual native capture after identical warmup, with fresh recorder
and host-clock baselines, frameskip0/APU21/audio4 and unchanged measured work.
Reject wrong ROM/layout/version, truncation/checksum errors and active capture
without partial mutation; reject unsafe resumptions and verify menu recovery
on transaction failure. Preserve firmware, ordinary saves and configuration.

Only after these gates may states replace repeated setup replay. Full replay
stays available to detect drift. State files/ROM/SAV/images/PCM remain private.
An incomplete state or matching screenshot alone cannot qualify timing/audio.

## Performance direction stays open

R44 rain40.540954 completions/s means24.667ms per completed boundary, with
4.880ms explicit CPU/RSP wait. Under the simplifying assumption that all other
cost stays constant, removing that entire wait still leaves roughly19.787ms
(about50.5 completions/s). This is a planning bound, not an additive profile
or a native prediction: overlap, bus effects and changed scheduling can alter
both terms. Reaching60 requires continued material CPU/APU/PPU/DMA and renderer
work with sound/visual fidelity preserved. Save states support those decisions;
they do not satisfy the active60Hz/50Hz/audio/corpus acceptance conditions.

## Source owner pass after the R45 material checkpoint

The current bridge is called from `menu.S:update_menu` after natural RSP HALT.
In `ppu.S:draw_frame`, this precedes the handed frame's DMEM descriptors,
event cursor, VRAM semaphore publication and next renderer submit. Therefore
the ordinary paused framebuffer boundary still owns a queued, not-yet-submitted
frame's historical sections, CGRAM events and OAM copies. Current final PPU
registers alone cannot reconstruct that history. Either preserve those complete
owners with explicit format semantics, or prove a canonical drain/continuation
boundary before making them derived state. No new drain is implemented here.

`cpu.S:cpu_init/cpu_execute` identifies s7 as the guest PC, s4 as guest status,
s5/s3/a3 as PPU/APU/DSP relative cycle budgets and s8 as direct-page offset.
The accumulator/X/Y/stack/data-bank fields are in CPU data. s6 is an immutable
host opcode-table pointer, not guest state; the saved gp/return/EPC and PPU
continuation must also be classified. This reinforces the explicit ownership
requirement rather than accepting a whole MIPS context as a portable state.

`apu.S` separates RAM and registers/PC/ports/timer deadlines/control/halt from
the JIT lookup/tag/code owners in `apu_emitter.S`. `dsp.S` separates registers,
noise/timer/ring position, voice counters/envelopes/BRR addresses/history from
host handler pointers and cached pitch/volume fields. Restore needs current
bindings and derived cache reconstruction with complete implemented synthesis
history retained. Configuration such as sample setting4 must be bound to the
state; existing paused PCM agreement still does not qualify complete DSP/audio.

Decision remains positive for a bounded prototype after the active renderer
regression gates. The first question is exact next1/60/600 guest progress,
memory/image/PCM equivalence and safe failure, followed by cross-build ownership
and comparable warmup. A same-build screenshot shortcut would not replace the
required A/B replay. Full replay remains the control; no serializer/restore,
new product UI or copied private state is qualified by this owner pass.
