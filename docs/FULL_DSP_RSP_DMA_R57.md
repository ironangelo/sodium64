# R57 - one128-byte DMA input packet versus PIO

Status: IMPLEMENTED; physical DMA performance/ownership pending.
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

Local C/actual-RSP transaction passes243 cases: all92 transfer faults,
74 read corruptions,67 task-wait positions, DMA BUSY timeout, corrupt input,
idle-length mismatch and address-restore fault. Same-image PIO control passes.
Parser263+1000 fuzz includes both selectors, malformed/out-of-range modes
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
