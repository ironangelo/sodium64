# Private scene slot prototype

MEASURED ALttP title advanced-machine continuation passes; Mode7 pending.
SCENE_SLOT1 requires the
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

Metadata runtimefaa4b7b physically reported an invalid2048-byte size and type3
for the ordinary control. Direct cart LBU was the new source of these fields.
Extract size/type from the mapper's existing aligned header word instead;
retain both mapper address/cycle behavior and the original SRAM word path.
Explicit ROM exponent bounds prevent masked shifts accepting malformed sizes.
The metadata-only worker completed and restored coordinate8/menu/readback.
Full restore remains pending for this repair.

Runtime25a748a native worker88793 terminal/restored: the aligned header repair
admits the control and saves3887607 bytes at600. After progressing1200, load600
passes destination/SP/TLB readback and all live owner fingerprints. Next601
also matches all fingerprints/image/PCM. Next660 image/PCM/head/registers and
all owners except the combined dynamic arena match; owner22 CRC differs.
Stopped before restored1200. Six normal images403200 pixels and six implemented
PCM rings49152 bytes match the frozen control, but complete continuation gate
is not passed. Locate the dynamic difference; do not silently drop it from the
gate. Private64KiB region fingerprints subdivide that existing owner only.

Runtime96e4a9b worker28199 repeats the same continuation result; only regions1,
2 and6 differ. They overlap Q1 events/raw shadows/consumed-section guard and
framebuffer1, plus framebuffer3. JIT/ROM cache and later composition surfaces
are unchanged by these region checks. The source of the exact bytes is still
unknown. Worker terminal, coordinate8/menu/readback restored. The pause-only
state-region ordinal0..50 exports a whitelisted64KiB slice (last40960 bytes)
privately for diagnosis; it accepts no arbitrary address or state import.
SCENE_SLOT rejects BACKDROP_ROWS1 until its additional Main row cursor and
candidate owners are included and separately qualified. The current29-owner
slot is explicitly BACKDROP_ROWS0; this limit does not change renderer defaults.

Runtimee9f6a81 worker96383 terminal/restored: all96 changed dynamic bytes are
48 black/white pixels in framebuffer1/3 rows23..30 x28..43, exactly the FPS
glyphs. Canonical660 image67200 RGB pixels matches. No event/palette/JIT data
differs in the exported regions. native_diag_init explicitly enables this
host-clock counter; its value and stale glyphs differ with bench dwell time.
This identifies the dynamic delta as instrumentation, not an unexplained guest
change. A raw O64 context CRC also differs in this run; classify its fields.

SCENE_SLOT only disables FPS glyph drawing at init; observer counters remain
active and default diagnostic/gameplay behavior is unchanged. New controls and
restored images compare all67200 pixels. Comparisons against old frozen images
exclude only their FPS glyph box rows23..30 x20..43 (up to3 decimal digits);
this exclusion must not be applied to current-control fidelity comparisons.
state-cpu-context exports only the canonical272-byte O64 owner privately for
field-level diagnosis. No arbitrary memory or state import is exposed.

Runtime35e1d3a worker9963 terminal PASS/restored: save600, advance1200, load600
then next1/60/600. All27 raw guest/renderer/context owner fingerprints and51
dynamic region fingerprints match at restored601/660/1200, with all272 O64
bytes unchanged (no field normalization was necessary). Full destination/SP/
TLB readback and loaded600 fingerprints pass. Current-control/restored images
match all201600 pixels across three checkpoints. Seven PCM rings57344 bytes
and heads/registers/enabled match the frozen control. Old-image comparison is
469056 pixels outside only the documented FPS glyph box. Coordinate8/menu/
install/readback restored; no live COM3. This is the first complete native
machine advance/restore control, restricted to the title route and build/boot.
Mode7 and active gameplay remain necessary; no cadence/full DSP/DAC/SNES
oracle/corpus/integration acceptance follows. The prior raw deltas were host
FPS rendering noise; retain their evidence, not a broad checksum exemption.

Mode7 runtime35e1d3a worker41679 terminal/restored: exact route4500 and control
4501/4560/5100 image/PCM pass. Load5100->4500 full readback/fingerprints pass;
restored4501 full image/PCM and every dynamic/guest owner pass. Only O64 CRC
differs; private272-byte comparison identifies exactly EPC at256..259, with
all GPR64/HI/LO and other bytes equal. Original canonical Status401 has EXL/ERL
clear: EPC records a completed host VI interrupt and is not used by the live
guest return. It varies with host interrupt timing. Stop before next60/600,
preserve the failure and restore baseline; this is not a guest-state mismatch.

The fingerprint now normalizes only inactive EPC's4 bytes when EXL/ERL are
clear. Full272-byte serialization and destination readback remain unchanged;
active exception states remain rejected. Every other O64 byte, all RSP/SP/TLB,
guest input and the entire dynamic arena remain compared. No GPR, HI/LO or
memory mask is added. Repeat the Mode7 continuation under this exact scope.
