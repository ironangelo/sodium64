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
