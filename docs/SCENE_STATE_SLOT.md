# Private scene slot prototype

IMPLEMENTED, native machine continuation pending. SCENE_SLOT1 requires the
canonical scene hook, full RSP context, trace recorder and audio observer.
Default0. It exposes state-save, state-load and state-fingerprint only through
the private bench. One volatile slot is restricted to the same build and boot;
no file importer, persistence, cross-build reuse or public game UI is provided.

The slot has29 whitelisted owners, payload3887195 bytes, envelope3887607 bytes.
It retains21 explicit static spans559691 bytes; the disjoint renderer/JIT/ROM
cache arena D6000..400000; O64 guest continuation272 bytes and original Status;
32 indexed TLB entries plus their current CP0 fields532 bytes; remote guest
input/progress; full SP memory8192 bytes and architectural RSP context700 bytes.
Transport, C stack, diagnostic recorder/observer state and immutable tables
remain separate. The slot starts at offset40000 of the exclusive volatile USB
TX workspace, beyond framebuffer packets and transient SP context scratch.

Complete guest-ROM and immutable N64 cart-prefix CRCs are bound once in this
boot. Layout includes fixed owner IDs, sizes and addresses; configuration binds
TV type, layers, precision, skipped frames, audio, APU clock, counter/underclock
settings, ROM type and SRAM requirement. Initial admission supports ordinary
ROM types0..2 and at most8KiB guest SRAM. EXL/ERL, FPU/64-bit address modes,
nonzero Wired and frameskip are rejected. Other chip/CPU modes remain gates.

Presentation drains with VI enabled, then interrupts are masked for copying.
SI is fenced, D-cache written back, and complete header/descriptors/body CRC
validate before load changes any saved owner. Every destination is read back.
SP registers are restored and recaptured; SP memory and signals are verified;
TLB entries/current fields are restored and read back. Restored JIT receives
full D/I cache maintenance. Host measurement clocks and recorder readiness
restart; Count and live transport remain current. Any partial machine commit
latches menu-only recovery. The usual verified menu/emulator restoration is
mandatory for native workers.

The private fingerprint covers live saved owners, excluding presentation
clocks and copies of remote control metadata. Input/progress ACKs are compared
separately. Full O64/RSP fingerprints include architectural scratch state;
differences require interpretation, not automatic omission. Private CRC values,
state bytes, ROMs, PCM and game images must remain local.

The slot-only C services use Os so static allocation stays belowD6000 without
reducing24576 event capacity or194 ROM-cache slots. All43 concurrent arena
owners and boot clears are checked. With SCENE_SLOT0 CPU text/data/allocated
extents remain byte-exact the physically measured full-RSP baseline.

Local gates:269 separate RSP store/load cases using actual microcode, including
changed registers/memory/signals;1908 production envelope/commit cases with
odd extents, full byte-corruption sweep and IO faults;64 linked TLB/cache cases;
16 O64 canonical boundary cases;234 parser cases and1000 malformed packets.
These mock hardware timing. They do not establish native machine restoration.

First native discriminant: ALttP title600, save; advance601/660/1200 as control;
load600 after1200; repeat next1/60/600 and compare normal images, implemented
PCM/heads/registers, input ACKs and live owner fingerprints. Stop on mismatch,
preserve evidence and restore coordinate8. Then use Mode7 and active gameplay.
Persistent RDP/TMEM assumptions still need these native continuation gates.
No performance/full audio/fidelity/corpus/integration claim follows from a slot.

First native runtime999db32 worker50104 is terminal: normal ALttP600 image
67200 pixels and implemented PCM8192 bytes/head/registers matched the frozen
control. Fingerprint rejected at ROM binding stage104 before any SP operation.
No machine save/load was attempted. Coordinate8/menu/readback restored. Keep
this failure distinct from local passes; inspect exact mapper metadata next.
