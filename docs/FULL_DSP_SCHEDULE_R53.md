# R53 - Complete DSP whole-sample scheduling

IMPLEMENTED; native cost pending. Isolated from R49 6d6e4eb; default
DSP_FULL_SAMPLE_CHUNKS0 requires FULL_DSP_PROBE1. Signal1/snapshot-scratch1
in both native variants. No R50 counter, R51 sampler or R52 BRR grouping.

The original run dispatcher decrements/tests after every clock, including
complete32-clock samples. R53 keeps that dispatcher for prefix/tail calls and
expands the same GEN_DSP_TIMING sequence for complete groups without interior
stop checks. Every ordered voice/BRR/latch/envelope/noise/echo/FIR action stays;
the phase21 t_brr_next_addr dependency is unchanged. Publish the final phase
upfront as the original did. No guest write can be delayed past a caller's
clock boundary, and no state fields are added. This is a generic control/dataflow
question; sampler run residency included DSP work and is not dispatch-only cost.

Pinned differential:9216 chunk cases (all32 entry phases,1..64 plus95/96/97/
127/128/129/255/256 clocks, four voice masks, writes/RAM mutations between
calls),13052 directed stereo frames. Existing12288 V3c/8192 arbitrary slices/
11601 additional stereo frames,38912 full-state comparisons/65536RAM bytes/
all128regs/PCM/internal-output extents. Five mutations reject: env1,noise,
prefix phase,tail phase,returned phase. Transaction6144 frames/original three
checksums/nonzero/RAMbackup-readback-restore/faults/snapshot tail pass. RPC219+
1000fuzz/snapshot admission tests are reused with exact production+fixture
hashes; no parser source changes since R52.

Flag0 all18 core executable sections match physical R49 signal1, and its entire
ELF is exact393ab26095ad07dd19cac669a8df9e719658ab34f155061c648dc0036fea6267
from R52's native baseline. Only run/new run_partial sections differ in flag1.
All13 RSP banks match. Nine/ten linked functions,36/61 product writers pass
the existing straight-line HI/LO gate; no broad control-flow/silicon proof is
claimed. Boot12/TV5/CPU6 queue words/two banks/four actualD6400 DMA sites/three
faults pass. StaticD4A88/D5A88<D6000, full24576events/194ROMslots/43owners.
Both reuse the unpublished32768B snapshot lease, denying every capture phase
or sealed snapshot; no IRQ change, arena relocation or capacity reduction.
[Numeric preflight](evidence/full-dsp-schedule-r53-preflight.json).

Frozen native A/B: group0then1, same-source three original2048-frame workloads
three times each at ALttPpaused600. Fresh baseline controls current physical
conditions despite exact earlier ELF. Host checksums/nonzero/RAM restore and
full live image/PCM/head/regs/enabled/boundary must match; gueststep660; finally
coordinate8/menu/install/readback. Root aloneCOM3, poll same live worker.

Predeclared: >=8% median saving in both active-eight cases warrants broader
qualification; below3%both rejects material performance; mismatch or >2%
regression blocks acceptance. Intermediate results stay isolated without an
open-ended tuning chain. Each2048-frame budget is64ms before guest CPU/APU/
rendering; core-only timing is not game60/DAC/SNES/corpus fidelity acceptance.
R44/R45/master and the bounded state prototype remain preserved, objective open.
