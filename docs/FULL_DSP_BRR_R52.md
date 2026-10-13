# R52 - Complete clocked DSP four-sample BRR dataflow

REJECTED; material native performance gate failed. Isolated from R49 6d6e4eb, default
DSP_FULL_BRR_GROUP0, FULL_DSP_PROBE1 required. DSP_SIGNAL_ELIDE1 in both
variants; no R50 counter, R51 sampler or gameplay mixer replacement.

The existing V4 group selects its filter once and keeps the two recurrence
histories in registers. Original cached header/first byte and one live RAM byte
stay at the same phase. Keep every sample, full-scale/half-scale history,
ranges13..15, integer floors, clamp/signed16 doubling, both mirrored stores,
buffer/address/pitch/END/loop and left-mix updates. No whole-block batching.

Both native variants use FULL_DSP_SNAPSHOT_CORE1: placement construction in
otherwise unpublished 32768B snapshot storage, destruction before RAM restore.
RPC denies sealed snapshots and every nonzero capture phase before backup.
No sampler, IRQ-mask change, arena relocation or capacity reduction. Initial
static-instance link overflow was never installed; both measured variants use
the same scratch-storage scheme. Default scratch0 retains the original storage.

Local pinned comparison passes82944 actual V4 cases, independently checked
BRR arithmetic:8 voices/16 ranges/4 filters/3 positions/9 signed-history pairs/
6 input patterns, cached-vs-live RAM and address wrap. Also12288 V3c cases,
8192 arbitrary clock slices/11550 stereo frames/103424 full-state comparisons,
all65536 RAM bytes/128 registers/PCM/internal outputs. Five negative mutations
reject. Original transaction6144 frames/checksums/nonzero counts,128 backup/
readbacks/128 restores,16 backup faults/corruption/two restore faults/five
invalid inputs pass; snapshot tail stays untouched. Parser219 cases/1000 fuzz,
including sealed snapshot and phases6/7/UINT32_MAX denials, pass.

Flag0 all18 core executable sections match physical R49 signal1 exactly.
Group1 changes decode_brr/V4/run; compiler outlines decode_brr. All13 RSP banks
match. Nine/ten linked functions and36 product writers pass existing straight-
line HI/LO spacing checks; this is not a full control-flow or silicon proof.
Both boot12/TV5, six CPU words/two banks/four actual D6400 DMA sites/three
negative mutations pass. Static endsD4A88/D5A88 remain belowD6000; full24576
events/194 ROM slots/43 simultaneous owners. Layout differs and is part of
the measured implementation; R51 instrumented times are not a baseline.
[Numeric preflight](evidence/full-dsp-brr-r52-preflight.json).

Native discriminator: frozen same-source group0 then1, original three2048-frame
complete-DSP workloads three repeats each at paused ALttP600. Core-only Count
excludes setup/USB/checksums, with no synthetic AI submission. Require every
host PCM checksum/nonzero count and64KiB RAM backup/readback/restore, full live
image/PCM/head/regs/enabled/boundary unchanged, gueststep660. Finally restore
coordinate8 through menu/install/readback. Root alone owns COM3; poll a live
worker rather than restarting after observation timeout.

Predeclared: >=8% median saving in both active-eight-voice cases warrants
broader fidelity qualification; below3% in both rejects material performance.
Any mismatch or >2% regression blocks acceptance. Intermediate results remain
isolated/unqualified, without open-ended tuning. Each2048-frame standalone
budget is64ms before guest CPU/APU/rendering; passing does not establish native
game60, DAC/SNES sound fidelity or corpus compatibility. R44/R45/master and
the state prototype stay preserved; full objective and integration remain open.


## Native cost outcome

Worker89966 terminal exit0, runtime9f00e9bf3861a0dddd65e752245fa5f23fad7c88. Three repeats per flag;
all18 checksums/nonzero results and36864 original synthetic frames match host.
Every trial64KiB RAM backup/readback/restore. Both live67200pixels/8192PCM/
heads/regs/enabled/boundary unchanged; gueststep600->660 succeeds. Recovery
coordinate8/menu/install/readback verified. No synthetic waveform sent to AI.

| Original workload | Baseline ms | Candidate ms | Time saving | Fraction of64ms |
| --- | ---: | ---: | ---: | ---: |
| One voice | 56.128064 | 61.476181 | -9.528419% | 96.057% |
| Eight high-pitch voices | 92.424981 | 107.983595 | -16.833775% | 168.724% |
| Eight with echo/FIR/PMON/noise | 95.529451 | 138.018496 | -44.477431% | 215.654% |

REJECTED; material native performance gate failed. No BRR micro-tuning or broad CI for this failed material gate. Preserve code/proofs isolated; inspect the remaining full-core scheduling cost for a larger generic reduction.
The64ms standalone core budgets still exclude guest CPU/APU/rendering. This
does not establish native game60, DAC/SNES sound fidelity or general corpus
compatibility. [Numeric receipt](evidence/full-dsp-brr-r52-native.json).
