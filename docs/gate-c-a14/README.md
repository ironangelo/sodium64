# A14: combined renderer and continuous private captures

This isolated candidate includes A13, packed RGB555 math and direct Sub
presence. The earlier combined control `328b65a` passed the full 94 normal and
12 armed trace image suites; qualification must be repeated for this new
continuous-capture source. Native timing and physical SummerCart64 persistence
remain unmeasured. No commercial ROM, save or derived framebuffer is included.

## One installation, repeated captures

The paired menu and empty trace emulator use `diagnostic_continuous=1` and
`diagnostic_slots=16` in the existing SNES emulator section. The menu reserves
16 unique 32 KiB files before each game launch. Start arms approximately 20 s;
the recorder seals its measurements in the timer IRQ, then returns to the
game. At the next naturally completed renderer frame it writes and verifies a
fresh reserved file, displays OK for two Count-domain seconds and can rearm.
The synchronous SD work can cause a pause outside the measurement window.
Start during an active capture is ignored. The same emulator handles every
game; changing the INI between scenes is unnecessary.

The pool uses exclusive file creation, closed/synchronized allocations,
fragmented-sector maps, SD CSD/CID, filesystem data bounds and a checksummed
S64C descriptor at cartridge offsets `0x102000..0x104000`. The emulator checks
the descriptor, card identity and global sector uniqueness. It writes only
those preallocated data sectors. Automatic single-file save writeback is
disabled. A nonzero diagnostic reservation is skipped on a soft restart.
Slots never wrap, including partially failed writes. Unused reservations have
no valid S64D header and are not extra measured scenes.

Each body sector has an explicit SD completion and byte-for-byte readback.
The header is first written with complete=0 and committed with complete=1
only after the body verifies. OK requires the final header readback as well.
Exhaustion and transport failure have visible states and block new captures;
gameplay can continue. Failure retains the sealed diagnostic 24 KiB, while
the private guest 8 KiB remains mutable; there is no retry or complete immutable
snapshot recovery protocol. A real renderer stall remains terminal and can
export a unique diagnostic file if SD transport succeeds.

The ordinary game save is read-only input. Gameplay changes occur in private
guest SRAM and in captured files; this diagnostic mode does not update the
ordinary save. Guests requiring more than 8 KiB SRAM are refused before SRAM
modification. The old menu/recorder terminal path remains available when the
continuous descriptor is absent. An invalid descriptor fails closed.

## Context and measurement

S64D version5 retains v4 geometry and append-only payload, plus CON5 context at
header+0x1E0: recorder cutoff Count, later natural-boundary/guest SRAM Count,
session capture sequence and context kind. A later sealed-window stall has its
own fault Count/wait-site/Status. The decoder never treats the cutoff IRQ and
later guest snapshot as the same instant. SD work, verification and OK display
are excluded from the retained measurement window.

Cadence is completed emulator boundaries, not presented FPS. CPU and RSP
overlap; sampled occupancy and waits are not additive engine runtimes. v4's
live DMEM bank/stage/PPU candidates still lack hardware access qualification.
Continuous capture does not repair or strengthen those attribution claims.

## Qualification boundaries

The linked CPU test executes the real recorder and assembly C bridge with a
mocked C sink. It covers 36 captures across 12 sessions, ordinary GPR64/HI/LO/
Status/EXL preservation, queue-index sp=0/4, Count wrap, IRQ/frame races, no
forced normal HALT/FREEZE, sealed-window later faults, failure lockout, invalid
handoff and legacy behavior. The actual production C algorithm is separately
host-compiled against a fragmented SD model, with failures at every successful
commit operation and corrupted readbacks. The real menu allocation helper is
host-compiled against an exclusive-open FAT shim with I/O failures. Linux uses
ASan/UBSan. Runtime sections must remain disjoint from the renderer arena.

The complete normal and armed image suite and legacy original-guest recorders
remain required for the new exact commit. These emulator/host tests do not
establish physical SD persistence, write latency, audio resumption or an FPS
gain. Those are hardware acceptance checks for the paired package.

## Work removed and future USB

Packed math reduces the core issued instructions per eight active pixels from
67/73 to 22/26 for add/sub; these are instruction counts, not measured cycles.
Direct Sub presence removes the WINNER-to-PRESENCE read/write snapshot:
250,880 DMA bytes per full general 224-row Sub section. Sub drawing and its
SyncFull fence remain; an explicit SetZImage selects Main's independent owner.
Net hardware gain remains dependent on the complete CPU/APU/RSP/RDP pipeline.

USB iteration would additionally require an explicit application control plane,
acknowledged safe reboot/upload, frame-indexed input replay, capture receipt
and visual/audio export. This candidate does not implement that future bench.
Its continuous files go directly to SD; ordinary USB save-memory download is
not a receiver for this new SD sink. No serial port or firmware was changed.
