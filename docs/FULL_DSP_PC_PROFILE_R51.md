# R51 - Scoped complete-DSP PC sampling

MEASURED; scoped native profile complete. FULL_DSP_PC_PROFILE1 defaults0 and requires
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


## Native profile complete

Worker3060 terminal exit0, runtimea7f852601ee71fdeee91e30b767495e62a8af628. All18 scenario checksum/nonzero
results/36864 original synthetic stereo frames match host. Every trial backs
up/readbacks/restores64KiB APURAM; full67200 live pixels/8192 live PCM bytes,
heads/registers/enabled/boundary stay unchanged. Actual step600->660 and final
coordinate8/menu/install/readback pass. No synthetic PCM goes to AI.

Six repeats retain all246/402/432 samples for one voice/active8/allfeatures,
1080 total, no ring wrap or unclassified address. The wrapper is separately
named in the full receipt. Active8 has V4=143/402
(35.572%), V3c=111/402
(27.612%), run84/402. Allfeatures has
V4=154/432 (35.648%),
V3c=108/432 (25.000%), run104/432.
[Complete numeric receipt](evidence/full-dsp-pc-profile-r51-native.json).

V4 includes BRR decoding, position advancement and left-channel output; this
does not assign its entire share to BRR. V3c includes interpolation/PMON/KON/
envelope work. The observed largest active residency justifies investigating
a larger V4/BRR dataflow reduction rather than more counter guard variants.
Next bounded question: dispatch each four-sample BRR chunk once by filter and
keep its full-scale history recurrence in registers, preserving the original
one cached/one live input byte phase, invalid ranges, clamp/sign16 doubling,
two mirrored writes and buffer positions. Compare all filters/ranges/history/
wrap/voices and actual clocked state against the pinned core before native.

These are statistical counts in this instrumented layout, not exclusive costs
or exact R49 residency. The core object and temporary storage addresses differ;
host IRQ masks and sampling also perturb timings. Instrumented allfeatures
time is about100.61ms versus R49's uninstrumented95.50ms, so it must not be
used as the next performance baseline. R49 remains the uninstrumented authority.
Full DSP/gameplay integration, native60, DAC/SNES fidelity and corpus remain open.
