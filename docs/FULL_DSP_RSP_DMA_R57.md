# R57 - one128-byte DMA input packet versus PIO

Status: MEASURED exact physical cursor/context restoration; thin Gaussian DMA performance REJECTED.
R56 proved the80-byte Gaussian kernel on1536 native lanes, but its PIO transport
averaged9.037667us per eight-wide packet and peaked12.266667us. It missed the
nominal7.8125us first-use engineering budget and saved only1.814297% against
the cached packed scalar formula. Do not tune that PIO implementation further.

R57 keeps all16 RSP banks exactly equal to R56, including both full-context
programs and the native-proved primitive. `DSP_RSP_GAUSS_DMA=1`, default0,
requires the existing Gaussian/context/state/trace/audio guards. The same
image's `state-rsp-roundtrip 0` selects PIO; `state-rsp-roundtrip 1` selects
one128-byte DRAM->DMEM transfer for each packet. Other values reject before
mutation. No-argument requests retain PIO. Existing numeric `gauss_PIO_*`
fields hold the selected transport cost; `gauss_transport_DMA` identifies it.

DMA source is the sixteen-byte-aligned private cached bridge stack packet.
Only128 input bytes are written back: eight hit-writeback-D operations using
the same cache operation as current renderer/profile owners, then SYNC.
Guard cached KSEG0, alignment and the complete8MiB physical RDRAM extent.
SP_MEM_ADDR0/SP_DRAM_ADDR/source/SP_RD_LEN127 form one input DMA, bounded to
DMEM000..07F. Wait for DMA BUSY/FULL to clear before starting the unchanged
kernel. The timed interval includes cache writeback/SYNC/setup/DMA wait,
kernel start/wait and the16-byte PIO result readback. Kernel/mask installation
and input preparation remain separate, as in R56.

An input-DMA timeout returns unsafe without overwriting the context/memory
owner and requires menu recovery. Otherwise restore both original SP DMA
addresses and require both idle length readbacks unchanged without rewriting
their registers (which would launch more DMA). Then use the existing exact
700-byte context/8192-byte SP restoration/readback gates. Primitive result
mismatch or task timeout still follows that complete safe restoration.

Local C/actual-RSP transaction passes253 cases: all92 transfer faults,
74 read corruptions,67 task-wait positions, DMA BUSY timeout, corrupt input,
idle-length mismatch and address-restore fault. Same-image PIO control passes.
Parser264+1000 fuzz includes both selectors, malformed/out-of-range modes
and strict recovery-only dispatch. Unchanged R56 primitive/context arithmetic
gates are reused, including the exact linked kernel and1536 physical lanes.
Boot/actual renderer DMA/full24576 events/194 slots/43 owners/arena pass.
No capacity reduction, arena shift, guest work or private game data uploaded.

Native discriminator: three paired64-packet PIO/DMA trials in one image,
same original512 outputs/checksum per trial, nominal8-DSP-clock7.8125us budget.
Retain DMA cost value only if its median packet latency falls at least40%
versus this image's PIO and its observed maximum fits the nominal budget.
Require full context/SP/DMA readbacks, all67200 live pixels/8192 paused PCM
bytes/head/register/enabled/guest-boundary controls, step660 and verified
coordinate8/menu/install/readback recovery. No broad CI before value.

This remains a transport/primitive test under an exclusive paused owner.
CPU input preparation, renderer contention/residency, task installation/context
switching, partial DSP-call/write ordering, complete DSP/DAC audio and sustained
native60/50/corpus/integration are open. No packet timing is a game FPS claim.
Master/R44/R45/state prototype and earlier rejected/preserved evidence remain
unchanged. Companion preflight JSON contains source-only/numeric fixture proof.

## First physical run - DMA ownership gate failed before cost acceptance

Exec10433 ended exit1; coordinate8/menu/install/readback restoration passed.
PIO mode0 at600 passed all512 primitive results, fullcontext/SP readback and
live image/PCM controls. Its totals were scalar28686/PIO22294 Count ticks,
PIO maximum513 ticks. These are one trial, not a complete paired result.
DMA mode1 at601 returned `scene_context_restore_failed stage=6
mismatch_word=4294967295`. The current error does not distinguish a DMA/task
stop failure from the new DMA-address/idle-length restoration guard. No DMA
cost or primitive acceptance can be claimed from this response.
Preserve the strict guard and add only failure readbacks to distinguish the
case, reusing all unchanged semantic/ownership gates. No broad CI or promotion.

## Diagnostic v2 - keep the failed gate and expose exact numeric cause

The next artifact reports failure kind, expected/observed readback and the
DMA register index. Kind1 is bounded DMA BUSY/FULL timeout,2 is failed task
HALT,3 is restored-address/idle-length mismatch,4 is invalid CPU DMA source.
It also reports how many primitive lanes completed before the failure.
All safety/ownership/latency gates remain unchanged. The added source-invalid
case and precise diagnostic assertions pass; all16 RSP binaries remain exact.
Use the unique v2 artifact/frozen worker/plan; do not restart terminal10433.

## Physical v2 - DMA arithmetic exact; current/pending cursor distinction

Exec21219 finished exit1; coordinate8/menu/install/readback recovery passed.
PIO0 passed512 arithmetic lanes/fullcontext/SP/images/PCM. DMA1 also completed
all512 original arithmetic lanes, but its exact owner gate failed for register0:
SP_MEM_ADDR expected6032 (0x1790), observed128 (0x80), mismatch80000000,
failurekind3. Cost acceptance and DMA context restoration remain OPEN.

The primary [ares RSP I/O](https://raw.githubusercontent.com/ares-emulator/ares/master/ares/n64/rsp/io.cpp)
reads DMA current addresses and writes pending addresses. Its
[DMA implementation](https://raw.githubusercontent.com/ares-emulator/ares/master/ares/n64/rsp/dma.cpp)
copies pending to current only when starting a transfer, and advances the current
cursor through the transfer. This explains the observed physical end cursor;
the former synthetic direct-write/readback fixture modeled that register
incorrectly. This is semantic evidence, not N64 performance from ares.

Next correct the existing transaction model to separate current/pending DMA,
and reproduce the actual6032->128 rejection before changing the implementation.
Preserve exact readback and memory guarantees. Evaluate a bounded8-byte
no-change read DMA ending at the original SP/DRAM cursors, only after checking
alignment, whole RDRAM/SP bounds, canonical idle counters, and exact equality
of source/tail bytes captured before the first mutation. It must preserve
both idle length readbacks and all8KiB, with no writes to RDRAM. Any mismatch
or timeout still locks to menu recovery. Audit future DMA helpers' complete
address/length rebinding; hidden pending descriptors must not be assumed equal.
This is an implementation hypothesis, not a completed repair or permission
to waive the failed gate. Retry only after the meaningful fault controls pass.
See the companion CURSOR.json for original-fixture/hardware-register numbers.

## 2026-10-14 - cursor restoration implemented, native v3 gate next

The corrected current/pending transaction model first reproduced exactly
the native v2 failure (expected6032, observed128,512 exact arithmetic lanes).
The implementation now admits only aligned in-range source/SP cursors, idle
count/lengthFF8 and equal shared length readbacks. Before its first SP mutation
it verifies the original eight-byte SP tail equals the last DMA's RDRAM tail.
It rechecks the source before one eight-byte read DMA ending at both original
cursors. This restores current readbacks without writing RDRAM or changing
SP contents; DMEM/IMEM wrap and the captured skip field are retained.

The byte comparison, all four DMA readbacks,700-byte context and entire8192-byte
SP restore/readback remain required. A changed source, changed byte, failed
counter/address readback or DMA timeout requires menu recovery. Cleanup is
outside per-packet timing. It neither waives the physical rejection nor claims
that unreadable pending descriptors equal their old values. All four actual
resident DMA length sites in the unchanged main/Mode7 binaries completely
rebind both addresses before issuing length; the CPU uploader does likewise.

The253-case C/actual-RSP gate passes current/pending semantics, all prior faults,
pre/post source mismatch, invalid bounds, cursor DMA BUSY/byte faults, exact
current-register readback, DMEM/IMEM wrap, skip preservation and no RDRAM writes.
All16 RSP binaries are unchanged; the old kernel/context proofs and exact
264+1000 RPC result are reused. Boot/43 owners/full capacities/arena/DMA pass.
Use fresh native v3 artifact/plan/worker, same paired physical gates. Native
cursor restoration and DMA cost remain pending until that run completes.

## 2026-10-14 - physical v3 complete; DMA cost hypothesis rejected

Exec81581 ended exit0, allcontrols and coordinate8/menu/install/readback passed.
All3072 original arithmetic lane results matched in six alternating PIO/DMA
trials. All four DMA current readbacks,700-byte RSP context/8192-byte SP memory
and each67200 image pixels/8192 paused PCM bytes/head/register/enabled/guest
boundary survived. The guarded eight-byte cleanup restores the observed
current cursors without changing SP contents or writing RDRAM. Step660 passed.

PIO totals21934/21934/21950 ticks; DMA22729/22824/22725. Median per packet:
PIO7.311333us, DMA7.576333us,
DMA time saving-3.624510% (slower). Observed maxima:
PIO10.986667us, DMA13.482667us.
Both fail the nominal7.8125us observed-max budget; DMA also fails40% saving.
These timings include transport/cache writeback/start/wait/output only.
Cached scalar reference, input preparation, installation, whole-context and
cursor cleanup remain explicitly separate; no complete-core speed claim.

Do not tune this thin Gaussian transport or run broadCI for it. The next
material question must carry more useful DSP work per transfer while preserving
all register/RAM/partial-clock/BRR/echo semantics. Before building a wider BRR
kernel, inspect its actual producer/consumer clocks and prove a closed-input
batch boundary against the full pinned core. Mixed epochs may capture voice0's
prior V4 and other voices' current V4, but that is only a hypothesis. State
exports and every short run return must still expose the exact original state.
R49 and every prior result remain preserved; fullDSP/DAC/renderer sharing/
native60/50/corpus/integration are open. See the companion NATIVE.json.
