# Architectural RSP context prototype

IMPLEMENTED assembly/local proof only. `SCENE_RSP_CONTEXT=1` requires
SCENE_STATE1 and assembles two324-byte programs. There is no C entry point yet;
linker discards the unreachable blobs, so whole CPU text/data remain exactS1.
No native context transaction or full machine restore has run.

Temporary DMEM layout captures32 scalar32-bit registers,32 vector128-bit
registers, eight48-bit ACC lanes and VCO/VCC/VCE masks:700 bytes. Capture stores
original vectors before reading ACC with VSAR; it restores its temporary v0
and t0 before BREAK. It leaves all architectural register/flag/ACC state
unchanged. Original SP memory and halted pipeline are separate CPU owners.

Restore derives a negative high helper from saved HI/MID, constructs ACC via
VMUDN and three VMADH operations modulo48, then loads all original vectors,
flags and scalar registers before BREAK. Helpers are derived, not authoritative
state. Instruction semantics were checked against
[pinned ares RSP source](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/n64/rsp/interpreter-vpu.cpp).
No third-party source or game data is copied into this prototype.

Actual linked programs:381 complete roundtrips (random plus cross-product
signed edges), all65536 MID values through linked arithmetic, nine mutation
rejections. Capture preserves every register/flag/ACC and writes only its700
bytes; restore changes no DMEM. All13 current renderer banks contain no RSP
reciprocal/reciprocal-square-root opcode. Adding one opens DIVIN/DIVOUT/DIVDP
ownership and invalidates this coverage. Hardware timing and CPU SP/PI/USB
transaction are not modeled here.
[Local context proof](evidence/scene-state-rsp-context-local.json).

Next wire a bounded native roundtrip: canonical natural retirement; back up/
read back full SP memory and halted pipeline; capture live context to exclusive
private scratch; deliberately overwrite register state; restore exact context;
recapture/read back all700 bytes; restore original SP memory/normalize the
pending resident jump; compare next1/60/600 image/PCM. Prevalidate before any
mutation and retain menu-only recovery after incomplete commit. Keep recorder,
transport, ordinary saves/SD and code pointers protected. Full CPU/guest memory,
JIT/mapper/input/host-clock owners and complete state slot remain separate gates.

## Bounded native transaction implemented

SCENE_RSP_CONTEXT1 now links the two programs and production transaction.
`state-rsp-roundtrip` requires healthy canonical pause/no recorder. Full8KiB
SP memory is backed up/read back/rechecked before the first mutation. Early
capture sentinels and matched HALT t0=2 check pipeline admission. Capture700
bytes, read back, restore deliberately zero register state and recapture all
zeros, then restore original registers and recapture700 bytes exact. Finally
validate/restore/read back original SP memory, checksum and status/restart3C.
All transfers use exclusive volatile TX scratch; no SD/guest ROM/save or
DP/AI access. Incomplete recovery locks gameplay to status/state-check/menu.
Success stays paused without guest/render progress; no full machine restore.

Production parser254/fuzz1000; C plus actual RSP transaction175 cases including
92 transfer-error positions,74 read corruptions and five waits; linked O64
bridge16; full43-owner/capacity bounds pass. Original26 renderer extents exactS1;
staticD3D38<D4000. Arena and capacities were not loosened. Existing continuous
102 bridge/recorder checks passed before the final early-store sentinel addition;
the final O64 boundary proof is fresh. No broad CI.
[Native preflight](evidence/scene-state-rsp-context-preflight.json).

Next native title600 roundtrip, then normal601/660/1200 image/PCM/head/regs/
enabled against the same frozen control. If successful, run Mode7 race4500
roundtrip and4501/4560/5100 using the existing exact reference. Each finally
restores coordinate8/menu/install/readback. Private register bytes stay local.

## First physical context transaction failed; stage trace next

Runtime74c66f2 title600 ordinary image/PCM match, canonical pause succeeds,
but the full context transaction returns restore_failed. Stage was not exposed;
do not infer which register or helper failed. No next-frame comparison or broad
CI. Worker32249 terminal; coordinate8/menu/readback PASS.
[Native failure](evidence/scene-state-rsp-context-native-failure.json).

The diagnostic now retains stage and first mismatching word index in error/
status receipts. Stages:1 admission,2 SP backup,3 capture execution,4 early
store sentinels,5 context slot backup,7 zero restore,8 zero capture,9 zero check,
10 original context memory,12 original register restore,13 recapture,14 context
comparison,15 SP backup validation,16 SP memory restore/readback/checksum,
17 final pipeline/status,18 success. Raw register values stay private; no new
game work. Parser254/fuzz1000 and production transaction175 still pass. Repeat
the same title gate to localize the discrepancy before changing reconstruction.

## Native early-store failure and shared pending entry hypothesis

Stage diagnosticcdc601d reports stage4/mismatchword8:the early t0=2 sentinel
fails after capture. Word0's zero store did run. Worker76955 terminal/menu/
coordinate8/readback PASS. Thus the failure precedes context slot backup or
ACC restoration. No raw register values or game payload are published.

Hypothesis:the stopped renderer's target3C survives CPU PC0 write, skipping
early stores after the first instruction. The model with this pending entry
reproduces the original unprefixed artifact's exact stage4/word8 rejection.
This is a hardware-derived hypothesis, not a general claim about PC writes.
Both programs now reserve60 NOP bytes so ordinary entry0 and pending target3C
reach the same body without a control transfer in the inherited delay slot.
Local637 roundtrips cover both entries, all65536 MID values and nine faults;
production transaction176 includes the original-artifact failure reproduction.
StaticD3DA8<D4000. [Entry evidence](evidence/scene-state-rsp-pending-entry.json).

Native repeat is required before accepting this fix. The programs remain
experimental; complete machine state and full native cadence/fidelity are open.
