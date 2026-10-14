# R62 - whole-emulator N64 resource inventory

Status: source audit and safe boot-memory reporting MEASURED; physical N64
reports8MiB and Expansion Pak available. No expanded-memory allocation or speed claim.
The user's resource question applies to CPU, graphics, audio, memory and all
remaining Road-to-1.0 work, not only DSP.

| Resource | Current evidence | Useful next question |
| --- | --- | --- |
| R4300 CPU | S-CPU interpreter, SPC700 JIT, PPU events, scheduling; caches and64-bit loads/stores used | Can event ordering, code/data locality and packing remove material work? |
| RSP | Resident renderer, decoding and composition; vector arithmetic used; DSP kernels experimental | Can larger resident workloads and CPU/RSP overlap beat the measured transfer/synchronization cost without displacing needed graphics? |
| RDP | Texture/rectangle/fill/composition commands and synchronization used | Can more exact composition reuse hardware work, preserving SNES pixel/color/timing behavior? |
| DMA/cache/bus | SP/PI/AI transfers and explicit cache maintenance used | Can larger useful transfers, less copying and fewer ownership switches reduce both CPU stalls and bus contention? |
| VI/AI | Display presentation and PCM delivery configured | Native cadence, full-rate source generation and faithful DAC audio still require separate acceptance |
| Expansion Pak | Current fixed renderer/event/ROM-cache arena ends at physical4MiB; no upper4MiB allocation/detection policy found | Use verified extra RAM for persistent state/shadow RAM, ROM/JIT/tile caches or buffers, then measure representative workloads |
| CPU FPU | No FP arithmetic in the emulation assembly; CU1 disabled in ordinary startup status | Consider only a concrete operation with exact integer-equivalence and native benefit; not a general-purpose spare core |

The Expansion Pak supplies4MiB of additional memory, bringing an ordinary N64
to8MiB. It adds storage capacity; it does not replace or increase the CPU/RSP/
RDP execution engines. Extra RAM could avoid refetches/redecoding or permit a
better dataflow layout, but those are hypotheses until measured. Sources:
[Nintendo's Expansion Pak description](https://www.nintendo.com/es-es/Hardware/La-historia-de-Nintendo/Nintendo-64/Accesorios/Accesorios-627128.html),
[libdragon memory interface](https://github.com/DragonMinded/libdragon/blob/e356bf3f56f7afbf7e5246329562f145965cfdfc/include/n64sys.h).

Source anchors: `src/defines.h` fixes `ROM_CACHE_SLOTS=194`, composition and
event owners below4MiB, and Q2 ends at`0xA0400000`. The4/8MiB constants in
`memory.S` are SNES bank-decoding boundaries, not evidence of expanded N64 RAM.
`main.S`, `rsp_main.S` and `dsp.S` show CPU/cache, renderer/RDP and VI/AI/DMA
use. R59/R60 measured a real transfer-cost problem; moving work to RSP alone
does not earn a speedup. R60's current standalone BRR backend remains rejected.

## Safe detection

Modern paired IPL3 reports detected RDRAM bytes in DMEM0..3 and TV type in
byte9. R62 preserves the RAM word immediately after the existing TV capture
and before renderer/RSP initialization. Only exact4MiB/8MiB values are accepted;
anything else reports unknown0. `status` now reports `rdram_bytes` and
`expansion_available`. It does not probe absent memory, change the map, allocate
upper RAM or infer physical presence from an8MiB pointer bound.

Primary boot contract:
[libdragon IPL3](https://github.com/DragonMinded/libdragon/blob/e356bf3f56f7afbf7e5246329562f145965cfdfc/boot/ipl3.c).
Linked boot proof covers18 RAM/TV combinations and all previous TV/reboot
cases,30 total; legacy low-RAM metadata deliberately disagrees. Parser267
cases plus1000 fuzz inputs passes. All17 RSP banks remain exactR60; the owner,
arena, boot, DMA-rebinding/cache checks pass. See the companion PREFLIGHT.json.
No broad CI is needed for this isolated diagnostic checkpoint.

Next physical action: normal menu/install/readback, launch existing private
ALttP, read the detected size, then restore coordinate8/menu/install/readback.
No DSP task or throughput claim. Record the live handle and poll it once issued.

If8MiB is confirmed, first reserve only a small explicit upper-RAM owner for
the R61 shadow/event dataflow when that protocol is proved, preserving base
buffers/caches. Independently evaluate wider ROM/JIT/tile caching or render
buffers when representative misses/stalls justify it; do not assume that more
RAM doubles FPS. Any allocation needs bounds, overlap, cache/DMA, boot and
same-build save-state ownership gates. Preserve operation on base4MiB through
an explicit fallback rather than accessing unverified extra memory.

R61's four bus-order counterexamples remain closed evidence; its safe window
controller, exact JIT timestamps and full resident DSP are still unimplemented.
Continue that semantic implementation after this bounded resource check. All
other fidelity/native60/50/corpus/integration gates remain open; master and
all prior candidates preserved. Commercial inputs and derived data stay local.

## Physical result

Exec48145 completed exit0. Actual paired IPL3 reports8388608 bytes; status
expansion_available=1. Normal menu/install/readback and final coordinate8/menu/
install/readback pass. No application read/write probe of upper RAM, no DSP task
or performance/fidelity claim. The active fixed emulator arena still ends at
4MiB. The remaining4MiB is a confirmed architectural resource, not an already
implemented optimization or an unqualified memory-health test.

After the R61 dataflow protocol is proved, prefer an explicit small upper-RAM
shadow/event owner to reclaiming or shrinking an existing base-memory cache.
Preserve all base owners and guard upper allocations by the captured size.
Broader ROM/JIT/tile/render memory uses need their own measured discriminator
when miss/copy/stall evidence supports them. Keep the whole-emulator resource
audit in scope, including graphics and chips beyond audio.
