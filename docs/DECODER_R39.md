# R39 - Decoder relocation cost isolated, 2026-10-12

MEASURED: unchanged corrected flags, DECODE_BANK1/BG_SPANS0. Actual N64
story1852 quiet20s53.641175/s, explicit CPU/RSP wait3.858279ms versus fresh
control56.149815/s. R38 with coalescing53.985990/s. The decoder transfer cost
reproduces the regression; the span change slightly offsets it here. Three
native checkpoints201600 RGB pixels/8192 PCM bytes plus heads/registers/
enabled unchanged; checksums/settings valid, menu/coordinate8 restoration pass.
No universal timing/fidelity claim. Native decoded call equivalence576 passes.

Next R40: semantic visible-Sub admission with a small resident-code island.
Keep original decoder and its original jump table resident on no-Sub bands;
activate the span helper/worker island only with visible Sub. Copy184 aligned
IMEM bytes only when that semantic class changes, outside the executing bank;
include identical surrounding delay-slot words and preserve all entry PCs.
One immutable184-byte original code image plus a tagged source/mode pointer,
no per-game policy, no extra full emulator. Differential code/epoch/source
ownership proof required before an early story/rain A/B. Preserve R38/R39.
The independent GCC16 diagnostic-arena failure also stays open. No full CI
repeat until a promising repair; retained source/master remain untouched.
