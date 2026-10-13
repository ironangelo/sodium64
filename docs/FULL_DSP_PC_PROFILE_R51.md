# R51 - Scoped complete-DSP PC sampling

IMPLEMENTED; native profile pending. FULL_DSP_PC_PROFILE1 defaults0 and requires
FULL_DSP_PROBE1. R49 signal1 is retained; R50 counter optimization is excluded.
This reuses PROFILE's Count/Compare/EPC ring algorithm during the existing three
original synthetic complete-core workloads. No separate emulator or general
profiler framework is added. No synthetic PCM is submitted to AI.

Every65521 Count ticks the owned IRQ records EPC using only k0/k1, increments
the sample count and schedules Compare. A128-word ring borrows the existing
512-byte PI transfer scratch only between RAM backup and restore, when no DMA
uses it. It is cleared first so unused slots cannot contain private guest RAM.
After each case its512 bytes go to the exclusive volatile cart USB scratch at
65536+case*512, disjoint from the64KiB RAM backup. No SD or firmware write occurs.

The original profiler's16KiB ring and timer cannot coexist with NATIVE_DIAG;
its fast sampling algorithm is reused with this scoped storage and dispatcher.
Begin rejects an active Compare owner/EXL/ERL/unaligned or null ring. It saves
Status and Compare, enables only the sampler interrupt during the paused scope,
then End restores both values without writing Count. A previously masked IP7
can be acknowledged by restoring Compare; this is not exact Cause restoration
or an O64 save-state claim. The ordinary recorder state and emulated deadlines
are not touched by the sampler. Existing frame-bridge context restoration stays.

The first instrumentation link exceeded the static arena because of page
alignment. No failed artifact was installed and no arena/capacity was reduced.
The diagnostic core object now leases the existing32768-byte immutable-snapshot
storage only when capture phase0 and snapshot_ready0. RPC rejects busy/sealed/
published snapshots before RAM mutation. Placement construction/destruction
defines the object's lifetime; the rest of that snapshot allocation is untouched.
After release a future capture can reuse its full original capacity. The ring
and exported PC data live elsewhere. Native static endD5AD8<D6000, gap528;
full24576 events/194 ROM slots/43 owners remain. The measurement artifact uses
SIGNAL_PROFILE0; this does not alter the clocked core's18 executable sections,
all byte-exact to the physical R49 signal1 object. Default0 keeps all871404
allocated bytes of the physical R49 artifact exactly.

Local sampler gates:8 begin/end,7 denied without effects,32 actual IRQ/ring
wrap/counter-wrap cases, dispatcher state preservation, GPR64/HI/LO/write owners
and Count/Compare/Status rules. Production parser221 cases+1000 fuzz includes
snapshot lease and export bounds, stale-frame, capture/paused/arity and failed
profile invalidation. The original6144-frame transaction matches all three
PCM checksums/nonzero counts, full64KiB RAM backup/readback/restore,16 backup
faults/corrupt backup/two restore faults/five invalid inputs. Profile admission
and profile-cart write faults restore RAM and return3 without a gameplay lock.
Unleased snapshot tail bytes stay exact. Boot12/TV5,9 core functions/36 HI/LO
sites, CPU6 words/two banks/four actual D6400 DMA sites/three faults pass.

The paused audio-full-dsp-probe command performs these owned scopes. Only a
successful complete RAM/configuration restore publishes audio-full-dsp-profile:
three512-byte big-endian rings, sample totals/cursors, fixed interval, exact
paused frame and synthetic provenance. Its export reuses the existing1536-byte
reply storage before writing its textual metadata. Transport/capture/paused/
origin-frame failures deny the read; there is no arbitrary address selector.

Native plan: one frozen artifact, six original probe repetitions at frame600,
then unchanged image/PCM/head/register/enabled/RAM and step660 controls, finally
coordinate8/menu/install/readback. All checksums must match the host. Aggregate
PCs by exact ELF function extents; report total/retained/outside and ring wrap,
not just a convenient tail. This answers which active-core function warrants
a larger change. Instrumented timings, masked VI service, alternate diagnostic
layout and statistical uncertainty are explicit: they do not replace R49's
uninstrumented cost measurements or prove exclusive instruction cost, gameplay
cadence, SNES/DAC fidelity, the corpus or master integration.
