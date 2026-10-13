# R54 - Complete-DSP data-cache placement discriminator

IMPLEMENTED; native outcome pending. Isolated from R49 6d6e4eb, default
DSP_FULL_CACHE_PROBE0 requires snapshot-core1/full-probe1. R49 signal1 remains;
no R50 counter, R51 sampler, R52 BRR grouping or R53 sample chunks. No gameplay
replacement. Original scalar arithmetic, phases, RAM reads, workloads and
2048-frame case sizes stay intact; only physical storage/pointer selection moves.

R52's baseline compiler already carried both BRR histories in registers.
Its grouped rewrite did not remove those claimed loads. The R52 linked Gaussian
table starts80018070, snapshot core800cbdb0; these ranges share D-cache indices.
R54's table80018850 also aliases parts of the synthetic BRR/echo RAM at8001a400.
These are static overlaps, not measured misses or proof of why R52 regressed.
The NEC manual describes8KiB direct-mapped data cache,16-byte lines,indexVA12:4:
[NEC VR4300 manual, chapter11](https://hack64.net/docs/VR43XX.pdf#page=278).

One frozen image has independent mode bits1/2/4 for core/PCM/Gaussian. Colored
indices1000/1c00/1800 respectively; three disjoint physical spans in the existing
unpublished32768B snapshot. Core1564B, PCM128B, immutable LUT1024B. Worst placement
fits23679B; class<=2048 assertion keeps the colored core disjoint from LUT/PCM.
Every nonzero capture phase or sealed snapshot denies before RAM backup. The
lookup pointer resets to the original table before RAM restore, including its
failure paths. No heap, new sampler, IRQ mask, MMU, cache flush or arena change.
Each LUT copy preserves all512 coefficients. Default0 keeps18 core executable
sections exact physicalR49; flag1 changes only V3c's table pointer load, adds
lease/current helpers, and keeps run plus all arithmetic/timing code exact.

Local: all8 modes produce24 matching case outputs/49152 synthetic stereo frames,
complete64KiB RAM backup/readback/restore, disjoint leases/all other snapshot
bytes unchanged, original LUT pointer restored. Original16 backup faults,
corrupt backup/two restore faults/five nil inputs plus invalid modes8/UINT32_MAX
reject. Differential12288 V3c/8192 arbitrary slices/11601 stereo frames/20480
full-state checks, all65536 RAM/128regs/PCM/internal output extents pass, with
lookup leases switched between calls. Env1/noise/copy/reset mutations reject.
Production parser241 cases+1000 fuzz passes fixed mode dispatch/lease admission
and failure lock. Initial fixture pointer-vs-int warning was repaired; no failed
artifact installed. Linked checks include the actual mode entry/free wrapper
helpers; guards recognize it as FULL_DSP_PROBE and retain all D6000 addresses.
Boot12/TV5/HI-LO/CPU6 queue words/two banks/fourD6400 DMAs/three faults pass;
13 RSP banks exact, full24576events/194slots/43owners, endsD4A88/D5A88<D6000.
[Numeric preflight](evidence/full-dsp-cache-r54-preflight.json).

Native question: can cache partitioning materially reduce full-core cost,
instead of treating driver layout effects as DSP arithmetic cost? One image,
ALttPpaused600, modes0/1/2/4/7 round-robin three times, three original workloads
each. Record actual cache indices/relative owned offsets and host PCM checksum/
nonzero match; all15 trials64KiB RAM restore. Full live image/PCM/head/regs/
enabled/boundary unchanged, step660, finallycoordinate8/menu/install/readback.
Core-only timing excludes initialization/USB/checksums; real output integration
must include its own costs. Root aloneCOM3, poll the same running worker.

Predeclared: >=8% savings both active cases within this image is material.
Also require best active medians below physical R49 historical92.392/95.496ms
by at least8% before calling it a retained cost improvement; repairing a poor
new baseline is only diagnostic evidence. Below3%both rejects material benefit.
Any mismatch blocks. Keep each standalone64ms budget explicit before guest CPU/
APU/rendering. No broadCI or another placement sweep unless the result changes
the architecture decision. These addresses are diagnostic; no universal fixed
layout, game60, DAC/SNES/corpus fidelity or integration acceptance is claimed.
