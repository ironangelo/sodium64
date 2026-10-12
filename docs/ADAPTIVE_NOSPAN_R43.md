# R43 - No-Sub overlay without per-tile span dispatch

IMPLEMENTED/local preflight, native pending. R40 recovered decoder residency
but story remains0.50percent slower than corrected control. Its no-Sub tiles
still call the span gate. Make an immutable1000-byte Main overlay variant
with that single call word changed to NOP, selected only on existing semantic
mode transitions. Sub retains unchanged coalescing and decoder-worker island.
No game identity, new hot-loop condition, guest omission or texture change.

ADAPTIVE_NOSPAN1 requires ADAPTIVE_SPANS1, defaults0. CPU copies the existing
Main slot once into an exclusive16-byte-aligned1008-byte buffer;1000 live bytes
plus8 cache padding. Cached stores,63 hit-writeback/invalidate D-cache lines,
SYNC, then pointer publication; no unflushed cached/uncached alias mixture.
Two immutable pointers use Mode6's unreachable padding after its first null
layer. Setup saves two table-construction instructions by using exact decoder
spacing, spending them on source selection without growing its fixed slot.
No-Sub source stays selected through subsequent Main reloads.

Local576 decoder/448 span/two initializer/four guard cases pass.30 semantic
mode/mask/delayed-DMA cases additionally execute Main reload, exact single-word
overlay patch, CPU copy/cache operands/order, original184-byte decoder and
boundary ownership; four unsafe variants rejected. Cache alias behavior itself
is not modelled; exact writeback range/order and early hardware are required.
Boot12/TV5/branch delays/41 owners/actual six CPU words/two embedded banks/four
backup DMA sites pass. D1A88 < D4000;194 ROM slots retained.

Preflight caught call PC1638 instead of actual163C; corrected before any N64
load. Isolated CPU fixture initially lacked already-loaded DMEM; seeded the
compiled initial DMEM, preserving the Mode6 terminator. No failed artifact
was loaded. All R40/R41/R42 artifacts preserved. Next: native story1852 first
with three images/PCM/quiet checksum versus corrected56.149815 and R40 55.868406;
if regression recovered, rain12944 confirms prior14.298672percent benefit.
No full CI repetition until this physical question is answered.

R41 d10b79f Build38300923921/CGRAM38300930969 passed. Original Ares38300934335
failed upstream SDL compilation. Workflow-only794b553 pinned the exact SDL
fix; Ares38304110691 SUCCESS, unchanged Sodium64 code. Do not relabel original
failure or claim R43 inherits qualification of its changed runtime.
Master/retained untouched; all private game data and hashes stay local.
