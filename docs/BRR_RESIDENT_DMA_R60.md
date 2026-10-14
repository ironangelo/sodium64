# R60 - raw BRR jobs and resident DMA return

Status: IMPLEMENTED, locally qualified; physical cost pending. Default-off
diagnostic under the existing canonical pause and full-context guards.

R59 measured preparation at approximately36% of packet cost. Even free
formatting leaves13.999/14.355 us versus14.539/14.538 us scalar, failing the
40% saving and8.7890625 us engineering gates. A formatting-only repair is
rejected. R60 changes the transfer protocol and representation together.

The CPU retains the original eight16-byte encoded/header/history jobs. The
RSP reads128 bytes by DMA, constructs its vector inputs locally, executes the
unchanged110-instruction R58 arithmetic body and returns64 output bytes by
DMA. The CPU posts one mailbox and starts the task; cached output reads replace
the old16 uncached output reads. Range weights come from a resident16-entry
table. All257 program instructions fit in1028 bytes of private IMEM.

The only writable DMA destination is the64-byte output inside a static,
16-byte-aligned224-byte object:128 input bytes,64 output bytes and32 guard
bytes. Static lifetime preserves ownership when a DMA timeout requires the
menu. The CPU validates the complete192-byte input/output range before the
first task, writes back128 input bytes, writes back and invalidates the output
sentinels before DMA, and invalidates64 output bytes after completion. All
cache maintenance, mailbox/task setup, both DMAs, adapter/arithmetic, waiting
and output reads are included in the accepted packet total. Synthetic job
generation, independent scalar reference, diagnostic guard checks, installation
and the enclosing full-context transaction remain separate, as in R58/R59.
The CPU-formatting counter is zero because formatting now runs inside the
timed RSP task; no work is subtracted from the total.

Local proof:1472 linked-kernel packets/47104 original samples, all16 ranges,
four filters, signed odd/extreme histories, raw32-bit upper-word bits and
randomized entry registers/vectors/ACC/flags. The110 arithmetic instructions
are byte-exact to R58; its612096-sample arithmetic proof is retained. Six real
mutations reject wrong histories/range tables, missing DMA waits, wrong input
extent and wrong output address. Production C plus actual linked RSP runs254
transaction cases, including input/output stalls, guard corruption, all64
task-wait faults, exact700-byte context/8192-byte SP/current-DMA restoration,
source/cursor faults and safe menu-required exits. Parser264+1000 passes,
including rejection of the PIO request before mutation. The unchanged context
program/model passes637 roundtrips, all65536 accumulator MID values and nine
mutations. Cache/bus timing is mocked locally, not accepted from these tests.

The scalar/control-flow additions follow the pinned primary
[ares RSP IPU source](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/n64/rsp/interpreter-ipu.cpp),
[SCC source](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/n64/rsp/interpreter-scc.cpp)
and the existing pinned current/pending DMA model. See the companion
`BRR_RESIDENT_DMA_R60_PREFLIGHT.json` for linked owners, boot and DMA checks.

Next: three native trials at canonical ALttP600..602, each64 packets/2048
original-fixture samples versus the same captured-job scalar work. Require
independent checksum, unchanged700-byte context/8192-byte SP/current-DMA,
67200 pixels/8192 paused PCM/head/register/enabled/guest boundaries; step660
and restore coordinate8/menu/install/readback. Useful cost requires at least
40% median saving and observed maximum within8.7890625 us. Only then consider
live closed-input integration and broader validation; no broad CI beforehand.

This is a primitive/protocol discriminator. Complete DSP/DAC, phase scheduling,
renderer residency/sharing, full guest emulation, native60/50, corpus fidelity
and master integration remain open. All earlier candidates are preserved.
ROMs, states, captures, PCM, raw native reports and game-derived hashes stay
private; only emulator source and original numeric-fixture summaries are public.
