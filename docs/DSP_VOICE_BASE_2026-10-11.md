# R31 - DSP voice field addressing (2026-10-11)

DSP_VOICE_BASE defaults0 and requires DSP_DRY_MIX1. During sampling, t8 points
at the existing16-byte voice structure instead of being an index repeatedly
added to absolute fields. a0 is already DSP scratch; it supplies the common
base after noise and is restored after each envelope call. Envelope handlers
retain their original index ABI. BRR addresses/registers/pitch/counters and
full-precision mix semantics are unchanged; no new memory is allocated.

The linked proof checks all nine signed16 field offsets, all256 enabled masks,
actual rate/envelope handlers, noise, all64 BRR range/filter pairs, end/loop
flags and both AI halves.2048 paired actual scheduler calls preserve PCM,
active registers/modes/envelopes/counters, sample buffers, observers and672
guest cycles per sample. Three base/index/restore mutations fail. The test VM
now executes ordinary signed/unsigned32-bit division for real timer handlers;
it rejects exceptional operands and does not model stalls or hardware timing.
The matrix executes2215794 ->2095550 scalar instructions, not a native gain.

Existing dry16384 voice/32768 output/128 scheduler/4096 dispatcher cases and
seven mutations pass; its maximum sample count641 ->545. Pitch131072 writes,
524288 loads,65536 uncached references and actual APU cases pass; a cached
load changes3 ->1 instructions. All57344 BRR voice cases/four mutations pass.
Their direct entry setup supports the pointer ABI without weakening memory or
register ownership checks. CI builds an otherwise-identical index reference
and executes the paired regression on the actual combined observer ELF.

With the new flag0, all855212 allocated coordinate8 bytes remain identical.
Reboot12/framebuffer5 and all41 owners pass, endD15C8 belowD2000. The native
production candidate disables both sample observers and retains existing AI/
release counters. Three-scene physical comparison is running: title/room
against R30 and rain against R29 dry (R30 rain was not retested). No native
performance result or full audio/video qualification is inferred at preflight.

Initial assembler syntax could not resolve a forward field difference; explicit
low16 relocation fixes it, with linked fit/address checks. Early host setup
incorrectly assumed21 guest cycles and v1 preservation; the actual sampling
contract is672 and BRR owns v1. A wrong reference pathname failed before load;
the existing original audio ELF was then used. Pitch result metadata retaining
the old3 was corrected to the actual asserted1. An edit with a partial line
was rejected before modification. None of these were physical USB failures.

Exact preceding1c23f23 Build38185802390 passes all six required jobs and
CGRAM38185805755 succeeds; Ares38185805806 remains pending at this record.
Master is unchanged, PR21 draft. Full60/visual/audio game matrix is open.
Commercial inputs/outputs/hashes and transport remain private; public proof
contains original synthetic counters and code identities only.

## R31 completed physical comparison

Four268800 RGB pixels and three24576-byte PCM rings remain identical at the
same acknowledged checkpoints. Native release/head/register/enabled checks and
all full/checksummed/no-overflow/settings-matched traces pass. One quiet window
per scene: title first30050.035870 ->51.863320 (+3.652 percent); room55.306802
->57.666181 (+4.265 percent); rain32.220722 ->32.284901 (+0.199 percent).
Rain uses R29 dry as reference; the later R30 trial omitted rain. These are
retired-boundary cadence, not TV FPS. Rain's tiny delta is not an established
speed gain. Native audio fractions92.92/96.03/53.58 percent of nominal AI
include endpoint overhead. No constant60/full DSP/output qualification follows.

Room sampled DSP occupancy39.71 percent/mean RSP wait0.001707ms versus rain
DSP19.45 percent/RSP-wait36.65 percent/mean11.255151ms. Sampling does not
provide exclusive function timing, but DSP addressing alone does not remove
the observed rain wait. Title first300 is separate from the whole20s mixture.

Empty candidate SHA25682b3999f383669cc0a156a723d1e247ad441db40e6829aa4d1945bed6a26a92e;
ELFe490994538ec8e4e7a89156e1867c283d4768e6a2d3ead7d03cbb679c0bc1280.
USB returns and coordinate8 restoration/readback/menu status pass without Reset.
The scanner menu remains installed; firmware is unchanged. Source36883ee CI
is pending independently; prior1c23f23 Build/CGRAM pass, Ares pending.

Primary NEC manual U10504EJ7V0UM00 pages76/479 says integer multiply stalls
the whole pipeline and requires two intervening instructions after MFHI/MFLO
before a new multiply. Therefore moving unrelated arithmetic into a multiply
interval is not a justified stall-hiding optimization. The current dry master
sequence MFLO/SRA/MULT has only one intervening instruction: newly identified
unsupported scheduling, despite arithmetic/native checkpoint matches. Next,
move existing left signed16 casts before the right multiplication, add an
actual linked hazard gate and retest. This is an unresolved hardware contract,
not an observed cause of the user's audio symptoms. It does not affect the
restored dry-disabled coordinate8 build.
[NEC primary manual](https://datasheets.chipdb.org/NEC/Vr-Series/Vr43xx/U10504EJ7V0UMJ1.pdf).
