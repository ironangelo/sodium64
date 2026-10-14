# R58 - closed-input mixed-epoch BRR batch

Status: IMPLEMENTED semantic boundary, RSP primitive and native discriminator;
complete-core RSP backend/native cost acceptance remain pending.
R57's thin Gaussian PIO/DMA cost remains rejected. This experiment tests a
larger useful-work boundary before constructing another vector kernel.

Each original V4 still captures the exact BRR header, two encoded bytes and
two decoded-history samples at its original clock. Source address/offset,
loop/end/pitch state and buffer cursor advance at their original phases.
Only the pure four-sample decode and duplicated-buffer writes are queued.
At phase21, voice0's prior-period V4 can join voices1..7's current-period V4;
up to32 decoded samples share one closed-input batch. The first next Gaussian
use is voice0 V3c30, nine DSP clocks later. Actual wall-clock admission,
renderer sharing and transport/preparation remain open.

Every public run return materializes remaining jobs, including one-clock
slices. State export/import flushes derived work before touching logical
state. Soft reset materializes history it retains; load/hard reset discards
the derived queue before replacing all voice state. The168-byte captured-job/
mask/peak storage is outside unchanged `state_t m` and serialized logical
bytes. Peak width is diagnostic only. This CPU surrogate is not a claimed
speedup; the scalar equations remain exactly the pinned full-core equations.

`DSP_FULL_BRR_BATCH` defaults0 and requires FULL_DSP_PROBE1. It is qualified
separately with DSP_FULL_GAUSS_BATCH0. Both the core and probe translation units
receive the same class-layout flag; the existing32768-byte snapshot lease
remains ample, with no new static audio surface or capacity reduction.

Local differential PASS:12288 directed V4 cases across all16 ranges/four
filters/eight voices/three positions/odd signed-history edges/RAM wrap;
12288 directed V3c cases;9216 entry-phase/chunk cases;8192 arbitrary slices;
52231 full logical-state/RAM/PCM comparisons;1024 dense one-clock DSP register
writes and RAM mutations. Peak admitted batch is eight voices. KON/KOFF/PMON,
noise, envelope, BRR, echo, internal/external output buffers, reset and state
copy/import are exercised. Seven real mutations reject, including captured
input/history/duplicate writes, missing public-return flush and soft-reset
history loss. All65536 APURAM bytes/128 DSP registers/PCM extents are compared.

The unchanged full-core transaction matches all three original2048-frame
checksums/nonzero counts,6144 total frames, fullRAM backup/readback/restore,
backup/restore corruption and input rejection, including snapshot ownership.
Actual N64 core/probe objects build. Flag0's18 executable core sections are
byte-exact R49 signal1; flag1 changes only the intended phase/state helpers.
This is not native timing, complete DSP/DAC output or gameplay acceptance.

Next: implement one eight-lane/four-sample RSP BRR primitive using the captured
inputs and original recurrence. Keep per-term arithmetic floors, int16 clamp
then signed16 double/wrap, all invalid ranges and odd histories exact. Reuse
the existing directed RSP model and full context/DMA owners, not another
emulator. Require a meaningful arithmetic/extent/fault gate before a short
physical transfer+kernel discriminator. Only material native value warrants
full-core integration or broader CI. The existing R57 source/tail/cursor
recovery proof and all earlier evidence remain preserved.

Full SPC/DSP/DAC audio, renderer contention, sustained native60/50, complete
required corpus and master integration remain open. R44 stays experimental,
R45 off, and no candidate is merged by this semantic batch.

## Linked RSP arithmetic primitive implemented; native transport pending

`rsp_dsp_brr.S` is444 bytes/111 instructions for32 decoded samples. Its96-byte
input contains eight encoded words, two signed-history vectors, range weight/
scale and filter IDs. It handles all invalid ranges and odd histories exactly;
per-term floors remain independent, full48-bit ACC survives intermediate
partial sums, final signed16 saturation precedes the original double/wrap.
Twelve resident constant vectors occupy060..11F; only120..15F is output.
It uses no DMA/RCP/reciprocal instructions. This is not cycle/performance proof.

Actual linked binary PASS:21952 directed groups over all16 ranges/four filters/
signed-history edges, all65536 encoded words, and65536 random groups:153024
groups/612096 decoded samples. Entry vectors/ACC/flags are randomized; allDMEM
outside64 output bytes is unchanged. Six real instruction mutations reject.
The existing full-context model still passes637 roundtrips/65536 MID values/
nine mutations after the necessary VMUDH/VEQ/VMRG semantic additions. These
match the pinned primary ares RSP SISD source; native acceptance remains open.

Next use the existing exclusive full-RSP context/current-DMA-cursor transaction
for a short native scalar/PIO/DMA discriminator. Count packet preparation from
the captured encoded/header/history inputs, cache writeback/setup/wait/output
together. Compare the same original scalar recurrence, not precomputed samples.
Record installation/whole-context cleanup separately, preserve live controls
and restorecoordinate8 via menu/install/readback. No broadCI until value.

## Native discriminator ready - preparation included

The opt-in BRR probe uses the existing full-context/canonical scene guards,
PIO0/DMA1 selector and current-cursor repair. Its96-byte input DMA writes back
six private aligned lines;64-byte outputs are compared to the original scalar
recurrence in cached original-job form. Packet formatting from encoded word,
header and two histories is charged to transport: timing includes preparation,
writeback/setup/kernel/wait/output. Synthetic source generation is outside
both paths. Installation/full-context cleanup are recorded separately.

The production C transaction with actual BRR/capture/restore binaries passes
253 meaningful fault/extent/current-pending/source/cursor/byte controls.
RPC264+1000 passes the explicit32-sample/96-byte/64-byte/preparation receipt.
The native artifact's remaining16 RSP banks are byte-exact R57, new kernel
hash exact arithmetic proof, all43 owners/full24576 events/194 slots and
boot/actual DMA/static arena pass. No event/ROM capacity or arena relaxed.

Physical plan: three alternating64-packet PIO/DMA pairs, each2048 original
decoded samples, atALttP600..605. Require exact checksum/currentDMA readbacks/
700-byte context/8192-byte SP/image67200/pausedPCM8192/head/register/boundary
controls, step660 and finalcoordinate8/menu/install/readback. Retain a backend
only with at least40% median cost saving versus this image's original scalar
formula and observed maximum fitting the nominalnine-DSP-clock8.7890625us
first-use budget. This is an engineering discriminator, not complete DSP or
renderer-sharing acceptance. Reject failed value before broadCI or tuning.
