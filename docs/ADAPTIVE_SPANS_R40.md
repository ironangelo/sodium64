# R40 - Semantic resident-code island, 2026-10-12

IMPLEMENTED/local preflight; native pending. R39 demonstrates decoder overlay
traffic causes story regression. Keep the byte-identical original decoder on
no-visible-Sub bands; retain R38 span/worker code on visible-Sub bands. This
uses the existing effective-Sub semantic predicate, no game identity.

`ADAPTIVE_SPANS=1` requires BG_SPANS1. A184-byte aligned island AD0..B88
includes unchanged adjacent delay words. The original compiled image is
byte-identical to the corrected control. CPU binds its aligned source in one
unreachable Mode7 padding word; low bit records which image is resident.
The Phase bank checks this semantic mode. Only a change loads Setup, updates
the matching three decoder jump words, reads the island outside executing
IMEM, then restores Phase. The original pointers and worker pointers differ
by52C, checked against actual symbols. No heap/new surfaces/ROM capacity change.
No-Sub span calls take a small resident gate and keep old tile2 rectangles.

Local30 mode/mask/queued-DMA cases prove paired code/jump tables, preserved
boundary words/CPU binding, no RDRAM writes or executing-island overwrite.
Existing576 decoder/448 span/two initializer/four mutation proofs pass;
branch-delay/boot12/TV5/arena gates pass, staticD1688 < D2000. All geometry
assertions remain: moving the second comparison into the first branch delay
recovers one instruction without changing either failure condition. The
original branch target is linked as an external symbol, avoiding an assembler
absolute-branch overflow. No unsafe artifact was loaded on hardware.

Next: native story1852 first, then rain12944 if story recovers, pixels/PCM and
quiet checksum captures against exact prior controls. Reject a failed repair
before full CI. The independent GCC16 AUDIO1/BRR0/MIX0 D2000 static-memory
failure stays open; no bound weakening or memory-layout change in this A/B.
Master/retained branches and earlier experiments remain preserved. All game
data, captures, replay/transport and hashes remain private.
