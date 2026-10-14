# R59 - BRR packet preparation cost discriminator

Status: IMPLEMENTED diagnostic; physical cost pending. R58's current PIO/DMA
backend remains REJECTED. No full-core DSP, game cadence or integration claim.

R58 measured 32-sample packets at 21.924 us PIO and 22.281333 us DMA, versus
14.539667/14.548 us for the original scalar arithmetic. Its accepted total
includes job formatting, input transfer, kernel execution, waiting and output
readback. The aggregate does not identify which part dominates.

R59 adds one diagnostic accumulator for the existing preparation interval and
reports `brr_preparation_ticks`. It does not subtract preparation from the
accepted total, alter the kernel, change the captured inputs or replace the
scalar reference. The accumulation is outside both timed intervals; this is
a diagnostic workload, not an emulator performance candidate.

Local gates: production parser 264 cases plus 1000 fuzz inputs; production C
and linked RSP transaction 253 cases, including transfer, corruption, timeout,
cursor/source faults and exact full-context restoration. All 17 RSP banks are
unchanged from R58; the 612096-sample R58 arithmetic proof is reused by exact
kernel hash. The native arena, 43 owners, event capacity, boot, DMA bindings
and cache writeback checks pass. See `BRR_PACKET_COST_R59_PREFLIGHT.json`.

Physical question: how much of each 64-packet total is preparation? Run two
alternating PIO/DMA pairs at canonical ALttP frames 600..603, each with 2048
original decoded samples and the independent checksum. Require unchanged
700-byte context, 8192-byte SP memory, current DMA readbacks, 67200 pixels,
8192 paused PCM bytes, audio head/register/enabled fields and guest boundary;
then step to 660 and restore the coordinate8 menu artifact with readback.

If preparation dominates, compare a representation that retains captured raw
jobs and avoids CPU vector-plane construction. If it does not, do not continue
formatting micro-tweaks; reconsider transport and resident scheduling. Residual
total minus preparation is an attribution diagnostic, not an accepted speedup
or a proof of a universal RSP limit. Every later candidate must count all work.

Only emulator source and original numeric-fixture summaries are public. ROMs,
states, captures, PCM, raw reports and game-derived hashes remain private.
R49, R44/R45, all earlier candidates and master are preserved. Complete DSP/DAC,
renderer sharing, sustained native 60/50 Hz and the full corpus remain open.
