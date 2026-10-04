# Diagnostic saves for SummerCart64

Opt-in integration built from N64FlashcartMenu commit
`e28c26e1aeae3c18851fc24118080e23e5a86a9f`. Upstream remains GPL-3.0-or-later:
https://github.com/Polprzewodnikowy/N64FlashcartMenu/blob/e28c26e1aeae3c18851fc24118080e23e5a86a9f/LICENSE.md

The emulator writes raw cartridge SRAM. The menu selects its SD writeback target
before boot. This integration creates a new target on every launch of the same
ROM: `<ROM-stem>-diag-<diagnostic_tag>-000001.sav`, then 000002, etc. No ROM aliases
or duplicated guest files are used. Captures and guest state remain private.

An existing ordinary `.sav` is opened read-only and its first 8 KiB imported.
The remainder of the new 32 KiB capture file is cleared. Missing ordinary saves
start with erased guest SRAM. Short/unreadable existing saves and allocation or
flush failures reject the launch. Every output uses FATFS `FA_CREATE_NEW`;
existing captures are never truncated. IDs are found from existing filenames,
without an RTC or mutable index. Failed/uncaptured reservations can leave files:
only a completed, checksum-valid S64D capture is diagnostic evidence.

The legacy single-capture mode uses the **paired empty v4 diagnostic emulator** and SNES games
whose SRAM header requires at most 8 KiB. The emulator refuses larger SRAM before
altering it. With diagnostics disabled, the upstream ordinary save path remains
unchanged. Diagnostics require SD writeback and menu reboot support. This build
sets the next reboot to the menu for each diagnostic launch.

Merge these keys into `sd:/menu/emulators.ini` (do not overwrite other sections):

```ini
[snes]
rom=sodium64-diagnostic.z64
save_type=3
rom_offset=0x104000
diagnostic_saves=1
diagnostic_tag=v4
```

Install the paired emulator at `sd:/menu/emulators/sodium64-diagnostic.z64` and
this menu at the SD root as `sc64menu.n64`, retaining your previous menu. Load the
same personal ROM normally, navigate to the scene, press N64 Start once, and wait
20 seconds for `CAPTURE SAVED`. Reset to the menu and load that same file again
for the next scene. The new capture goes beside the ordinary save or in its
`saves` subfolder, matching the menu's existing setting. Gameplay during a
capture belongs only to that capture's private SRAM; the ordinary save is not
updated. To resume normal use, select the normal emulator and disable
`diagnostic_saves`.

Host qualification: `python3 tools/sc64-diagnostic-save/test_save.py` compiles the
actual helper with ASan/UBSan against an exclusive-open filesystem shim and
injects read/write/sync/close failures. The separate workflow builds the pinned
menu and supplies its exact patch/source. Real SD/flashcart writeback and reboot
behavior still require hardware qualification; host tests do not establish it.

## Repeated captures in the same running game

The new continuous mode requires the **paired continuous diagnostic emulator
and menu**. It keeps the ordinary SRAM input read-only and reserves a bounded
pool of fresh capture files before launch. Add these opt-in keys to the same
`[snes]` section, retaining the emulator filename/build tag supplied with the
paired package:

```ini
diagnostic_continuous=1
diagnostic_slots=16
```

The default pool is 16 files (512 KiB SD). Every file is exclusively created,
fully allocated, synchronized and closed before the menu obtains its 64 sector
addresses. Reserved files that have not been used contain no S64D capture;
they are not extra measured scenes. A new launch chooses new IDs and does not
reuse previous reservations or captures. Allocation, read, flush, card identity,
sector overlap, bounds or descriptor verification failures reject launch.

The menu writes the versioned S64C descriptor into cartridge offsets
`0x102000..0x104000`, beyond conventional IPL3 checksum data and before the SNES
image. It rejects emulator images larger than `0x102000` or a different SNES
offset. The descriptor contains the raw CSD/CID, filesystem data bounds, IDs and
all fragmented file sectors, with a big-endian additive checksum. The first
reservation supplies the private initial SRAM; this mode does **not** configure
automatic writeback to a single mutable file. Loading another SNES emulator
through this menu invalidates the old descriptor first.

The paired recorder uses a new slot for each capture, writes SD sectors
explicitly, publishes the complete header last and reads the file back before
confirming success. It never wraps at the end of the pool. The gameplay pause
for committing/verifying a file is outside the measured 20-second window.
Rearming the old A13 terminal recorder alone would overwrite one file; it cannot
provide this flow. Setting `diagnostic_continuous=0` selects the original
single-reservation menu path.

`python3 tools/sc64-diagnostic-save/test_save.py --json-output pool-proof.json`
executes the real pool/reservation C helper with failure-injecting callbacks.
It checks two sessions, previous file/progress preservation, fragmented sector
maps, cross-file disjointness, the full 16-slot ABI and rejection of allocation,
card, mapping and publication failures. Linux CI uses ASan/UBSan; native Windows
GCC executes the same assertions without those unavailable sanitizers. These
proofs and compilation do not establish physical SD persistence, pause length
or correct gameplay/audio resumption; those require the paired hardware trial.
