#!/usr/bin/env python3
"""Apply the small opt-in integration to an exact, pinned upstream checkout."""
from pathlib import Path
import argparse,shutil,subprocess
PIN='e28c26e1aeae3c18851fc24118080e23e5a86a9f'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('checkout',type=Path);a=p.parse_args()
repo=a.checkout.resolve();root=Path(__file__).resolve().parent
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==PIN,'upstream pin mismatch'
file=repo/'src/menu/cart_load.c';s=file.read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,('upstream context changed',old)
    s=s.replace(old,new)
replace('#include "path.h"','#include "path.h"\n#include "diagnostic_save.h"\n#include "diagnostic_pool.h"')
replace('    uint32_t emulated_file_offset = 0;', '    uint32_t emulated_file_offset = 0;\n    bool diagnostic_saves = false;\n    bool diagnostic_continuous = false;\n    int diagnostic_slots = 16;\n    uint64_t diagnostic_emulator_bytes = 0;\n    char diagnostic_tag[26] = "v4";')
replace('            ini_free(cfg);', '''            diagnostic_saves = ini_get_int(cfg, emu_section, "diagnostic_saves", 0) == 1;
            diagnostic_continuous = ini_get_int(cfg, emu_section, "diagnostic_continuous", 0) == 1;
            diagnostic_slots = ini_get_int(cfg, emu_section, "diagnostic_slots", 16);
            const char *tag = ini_get_string(cfg, emu_section, "diagnostic_tag", "v4");
            strncpy(diagnostic_tag, tag, sizeof(diagnostic_tag) - 1);
            diagnostic_tag[sizeof(diagnostic_tag) - 1] = 0;
            ini_free(cfg);''')
# Apply only inside the emulator loader; preserve every ordinary N64 save path.
pos=s.index('cart_load_err_t cart_load_emulator (')
left=s[:pos];s=s[pos:]
replace('    if (!file_exists(path_get(path))) {', '''    if (diagnostic_continuous && !diagnostic_saves) {
        path_free(path);
        return CART_LOAD_ERR_FUNCTION_NOT_SUPPORTED;
    }
    if (diagnostic_saves && (emu_type != CART_LOAD_EMU_TYPE_SNES ||
        save_type != FLASHCART_SAVE_TYPE_SRAM_256KBIT ||
        !flashcart_has_feature(FLASHCART_FEATURE_SAVE_WRITEBACK) ||
        !flashcart_has_feature(FLASHCART_FEATURE_ROM_REBOOT_FAST))) {
        path_free(path);
        return CART_LOAD_ERR_FUNCTION_NOT_SUPPORTED;
    }
    if (!file_exists(path_get(path))) {''')
replace('    menu->flashcart_err = flashcart_load_rom(path_get(path), false, progress);', '''    diagnostic_emulator_bytes = file_get_size(path_get(path));
    if (emu_type == CART_LOAD_EMU_TYPE_SNES) diagnostic_pool_menu_invalidate();
    menu->flashcart_err = flashcart_load_rom(path_get(path), false, progress);''')
replace('    menu->flashcart_err = flashcart_load_save(path_get(path), save_type);', '''    if (diagnostic_saves) {
        char *reserved = NULL;
        bool reserve_failed = diagnostic_continuous
            ? diagnostic_pool_menu_prepare(path_get(path), diagnostic_tag, diagnostic_slots,
                emulated_rom_offset, diagnostic_emulator_bytes, &reserved)
            : diagnostic_save_reserve(path_get(path), diagnostic_tag, &reserved);
        if (reserve_failed) {
            path_free(path);
            return CART_LOAD_ERR_SAVE_LOAD_FAIL;
        }
        path_free(path);
        path = path_create(reserved);
        free(reserved);
        // Reset always returns to the menu; completed capture slots never wrap.
        menu->flashcart_err = flashcart_set_next_boot_mode(FLASHCART_REBOOT_MODE_MENU);
        if (menu->flashcart_err != FLASHCART_OK) {
            path_free(path);
            return CART_LOAD_ERR_BOOT_MODE_FAIL;
        }
    }
    if (diagnostic_continuous) {
        // A path here would enable automatic writeback to one mutable file.
        // Select SRAM without writeback, then load the first reservation only.
        menu->flashcart_err = flashcart_load_save(NULL, save_type);
        if (menu->flashcart_err == FLASHCART_OK && diagnostic_pool_menu_load_initial(path_get(path))) {
            menu->flashcart_err = FLASHCART_ERR_LOAD;
        }
    } else {
        menu->flashcart_err = flashcart_load_save(path_get(path), save_type);
    }''')
file.write_text(left+s)
for name in ('diagnostic_save.c','diagnostic_save.h','diagnostic_pool.c','diagnostic_pool.h',
             'diagnostic_pool_menu.c','continuous_save_abi.h'):shutil.copyfile(root/name,repo/'src/menu'/name)
file=repo/'Makefile';s=file.read_text();assert s.count('\tmenu/cart_load.c \\\n')==1
file.write_text(s.replace('\tmenu/cart_load.c \\\n','\tmenu/cart_load.c \\\n\tmenu/diagnostic_save.c \\\n\tmenu/diagnostic_pool.c \\\n\tmenu/diagnostic_pool_menu.c \\\n'))
print('SC64_DIAGNOSTIC_INTEGRATION_APPLIED',PIN)
