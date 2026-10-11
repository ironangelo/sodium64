# Paired USB menu source checkpoint

These overlays preserve the menu code used for the native hardware loop.
Upstream N64FlashcartMenu is pinned to
`e28c26e1aeae3c18851fc24118080e23e5a86a9f`; linked libdragon to
`55aac1355773169d87e45424b772faf0dfb9432a`.
Derived upstream menu files remain GPL-3.0; see COPYING.menu.
FatFs headers retain their upstream copyright and redistribution notices.

Apply to a clean, exact upstream checkout with initialized submodules:
```sh
python3 tools/sc64-diagnostic-save/apply_usb_loop.py /path/to/N64FlashcartMenu
```
This explicit snapshot application copies the current diagnostic helpers and
menu overlays. It does not use the older capture-only apply.py, flash firmware
or install anything on a cartridge. The application helper is packaging glue
added during the October11 synchronization; its syntax/static consistency was
checked, but a fresh full upstream rebuild through this helper is pending.

The overlay contains the actual Makefile, cart_load.c/h and USB handlers, matching
FatFs headers and host/asset/ABI guards. Original assets remain upstream; there
are no packaged ROMs, private game files or captured outputs in this directory.
Build all FatFs consumers freshly. Do not combine older libdragon.a with headers
from a newer N64_INST. The snapshot header copies use LF for version control;
byte-comparison ABI checks expect the library-source headers with matching EOL.

`usb-loop.mk` is a portable form of the local pinned linker invocation.
S64_LIBDRAGON_DIR and S64_TOOLS_DIR must refer to the pinned library/tool source
builds; S64_TOOLS_SUFFIX may be .exe on Windows. Example after compiling that SDK:
```sh
make -f usb-loop.mk -j4 BUILD_DIR=build_pinned_fatfs OUTPUT_DIR=output_remote \
  S64_LIBDRAGON_DIR=/path/to/libdragon-55aac \
  S64_TOOLS_DIR=/path/to/libdragon-55aac/tools \
  FLAGS=-DNDEBUG MENU_VERSION='"Sodium64 A14 USB loop"'
python3 tools/test_usb_remote.py
python3 tools/test_paired_menu_assets.py
python3 tools/check_paired_fatfs.py --build build_pinned_fatfs \
  --reference /path/to/libdragon-55aac
python3 tools/check_paired_menu_assets.py --help
```
Asset packaging must use matching converters/mkdfs/n64sym and original sound/
font assets. The installed menu had verified DFS SHA256
bc88c435ad71922015f625e960d983694881ce82a03064e56ea93401e0644d50.
This is an asset-container identity, not a commercial game dump.
The ledger explains the missing-cursorsound assertion and incompatible FIL ABI.

Menu commands mediate FAT writes while the N64 is on. Emulator commands never
grant direct PC filesystem ownership. Readback/CRC, retained previous files,
bounded paths/sizes and rollback are required. A receipt proves the transaction,
not final TV pixels. Power-cycle recovery is still needed for nonresponsive code.

Booting a game calls the existing emulator/INI/save/pool path with the selected
SNES ROM path. It does not run an empty sodium64 image as a game. Keep
emulators.ini injection offset0x104000, diagnostic_saves=1,
diagnostic_continuous=1, diagnostic_slots=16 and an identifying diagnostic_tag.
Preserve ordinary saves; the pool reserves exclusive diagnostic targets and
does not overwrite old files.

Installed menu on October10:1736704B,
SHA256803a716bb51ebef672c43a80671776fcae4a0330d5348aeeda8954666113a144.
This tracks the last verified binary; a fresh rebuild is not yet asserted
byte-identical or physically accepted. Firmware2.20.2 remains unchanged.
