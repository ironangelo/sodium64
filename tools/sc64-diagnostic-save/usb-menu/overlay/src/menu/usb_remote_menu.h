/* Included once by usb_comm.c; legacy commands retain their original behavior. */
#ifndef USB_REMOTE_MENU_H
#define USB_REMOTE_MENU_H

#ifndef S64_REMOTE_BUILD
#define S64_REMOTE_BUILD "paired-A14-usb-loop-fatfs16"
#endif

typedef struct {
    uint32_t remaining;
    char id[9];
} remote_request_t;

static bool remote_recovery;

static int remote_char(remote_request_t *request) {
    unsigned char c;
    if (!request->remaining) return -1;
    usb_read(&c, 1);
    request->remaining--;
    return c;
}

static bool remote_string(remote_request_t *request, char *buffer, size_t capacity,
                          char delimiter, int *terminator) {
    for (size_t i = 0; i < capacity; i++) {
        int c = remote_char(request);
        if (c < 0) return false;
        if (c == 0 || c == delimiter) {
            buffer[i] = 0;
            if (terminator) *terminator = c;
            return true;
        }
        buffer[i] = (char)c;
    }
    buffer[capacity - 1] = 0;
    return false;
}

/* Purge before replying: libdragon refuses USB TX with unread RX bytes. */
static bool remote_reply(remote_request_t *request, const char *kind, const char *format, ...) {
    char response[512];
    int prefix = snprintf(response, sizeof response, "S64 %s %s ", request->id, kind);
    va_list args;
    va_start(args, format);
    int bytes = vsnprintf(response + prefix, sizeof response - prefix - 2, format, args);
    va_end(args);
    if (bytes < 0 || (size_t)bytes >= sizeof response - prefix - 2) return false;
    response[prefix + bytes] = '\n';
    response[prefix + bytes + 1] = 0;
    usb_purge();
    request->remaining = 0;
    return usb_write(DATATYPE_TEXT, response, prefix + bytes + 1) == 1;
}

static bool remote_exists(const char *path) {
    struct stat st;
    return stat(path, &st) == 0;
}

static FRESULT remote_rename(const char *source, const char *destination) {
    return f_rename(strip_fs_prefix((char *)source), strip_fs_prefix((char *)destination));
}

static bool remote_program_file(const char *path, uint32_t *bytes) {
    int64_t length = file_get_size((char *)path);
    if (length < 4096 || length > S64_REMOTE_PROGRAM_MAX) return false;
    FILE *file = fopen(path, "rb");
    if (!file) return false;
    unsigned char header[4];
    bool valid = fread(header, 1, 4, file) == 4 &&
        header[0] == 0x80 && header[1] == 0x37 && header[2] == 0x12 && header[3] == 0x40;
    if (fclose(file)) valid = false;
    if (valid && bytes) *bytes = (uint32_t)length;
    return valid;
}

static void remote_list(menu_t *menu, remote_request_t *request, const char *directory) {
    if (!menu->storage_prefix || !s64_remote_path(directory, true)) {
        remote_reply(request, "ERR", "PATH");
        return;
    }
    path_t *path = path_init(menu->storage_prefix, (char *)directory);
    /* FatFs stat rejects the root itself; directory iteration handles it. */
    if (strcmp(directory, "/") && !directory_exists(path_get(path))) {
        path_free(path);
        remote_reply(request, "ERR", "DIRECTORY");
        return;
    }
    unsigned count = 0;
    dir_t entry;
    int state = dir_findfirst(path_get(path), &entry);
    while (state == 0) {
        if (strcmp(entry.d_name, ".") && strcmp(entry.d_name, "..")) {
            char listed[S64_REMOTE_PATH_MAX + 1];
            int n = snprintf(listed, sizeof listed, "%s%s%s", directory,
                             !strcmp(directory, "/") ? "" : "/", entry.d_name);
            if (n < 0 || n >= (int)sizeof listed ||
                !s64_remote_path(listed, entry.d_type == DT_DIR)) {
                path_free(path);
                remote_reply(request, "ERR", "ENTRY_PATH count=%u", count);
                return;
            }
            if (count == S64_REMOTE_LIST_MAX) {
                path_free(path);
                remote_reply(request, "ERR", "LIST_LIMIT count=%u", count);
                return;
            }
            if (!remote_reply(request, "ITEM", "%s %lld %s",
                    entry.d_type == DT_DIR ? "dir" : "file", (long long)entry.d_size, listed)) {
                path_free(path);
                return;
            }
            count++;
        }
        state = dir_findnext(path_get(path), &entry);
    }
    path_free(path);
    if (state < -1) remote_reply(request, "ERR", "DIRECTORY_READ count=%u", count);
    else remote_reply(request, "OK", "count=%u", count);
}

/* Validate the dedicated bank INI before SDRAM is replaced. The existing
 * loader alone owns game-header stripping, save paths and A14 pool creation. */
static bool remote_launch_config(menu_t *menu) {
    path_t *cfg_path = path_init(menu->storage_prefix, "/menu/emulators.ini");
    ini_t *cfg = ini_load(path_get(cfg_path));
    path_free(cfg_path);
    if (!cfg) return false;
    const char *program = ini_get_string(cfg, "snes", "rom", "");
    const char *offset = ini_get_string(cfg, "snes", "rom_offset", "");
    char *end;
    unsigned long parsed = strtoul(offset, &end, 0);
    bool valid = !strcmp(program, S64_REMOTE_PROGRAM) && end != offset && !*end &&
        parsed == S64_REMOTE_ROM_OFFSET &&
        ini_get_int(cfg, "snes", "save_type", -1) == FLASHCART_SAVE_TYPE_SRAM_256KBIT &&
        ini_get_int(cfg, "snes", "diagnostic_saves", 0) == 1 &&
        ini_get_int(cfg, "snes", "diagnostic_continuous", 0) == 1;
    ini_free(cfg);
    return valid;
}

static void remote_launch(menu_t *menu, remote_request_t *request, const char *game) {
    static const char *extensions[] = { "sfc", "smc", NULL };
    if (!s64_remote_path(game, false) || !file_has_extensions((char *)game, extensions)) {
        remote_reply(request, "ERR", "PATH");
        return;
    }
    if (!menu->storage_prefix ||
        (menu->mode != MENU_MODE_BROWSER && menu->mode != MENU_MODE_NONE && menu->mode != MENU_MODE_ERROR) ||
        menu->mode == MENU_MODE_BOOT || menu->next_mode == MENU_MODE_BOOT ||
        menu->load_pending.rom_file || menu->load_pending.disk_file ||
        menu->load_pending.emulator_file || menu->load_pending.extract_file) {
        remote_reply(request, "ERR", "BUSY");
        return;
    }
    if (!is_memory_expanded() || !flashcart_has_feature(FLASHCART_FEATURE_SAVE_WRITEBACK) ||
        !flashcart_has_feature(FLASHCART_FEATURE_ROM_REBOOT_FAST)) {
        remote_reply(request, "ERR", "HARDWARE");
        return;
    }
    if (!remote_launch_config(menu)) {
        remote_reply(request, "ERR", "INI");
        return;
    }
    path_t *rom_path = path_init(menu->storage_prefix, (char *)game);
    path_t *program = path_init(menu->storage_prefix, S64_REMOTE_DIRECTORY S64_REMOTE_PROGRAM);
    int64_t game_bytes = file_get_size(path_get(rom_path));
    bool files_valid = game_bytes >= 1024 && game_bytes <= 0x800200 &&
        file_exists(path_get(rom_path)) && remote_program_file(path_get(program), NULL);
    path_free(program);
    if (!files_valid) {
        path_free(rom_path);
        remote_reply(request, "ERR", "FILE");
        return;
    }
    /* Assets/DFS and audio live in the cart image about to be replaced. After
     * a load attempt keep a black USB recovery mode instead of reading them. */
    sound_deinit();
    rspq_wait();
    remote_recovery = true;
    menu->mode = menu->next_mode = MENU_MODE_NONE;
    cart_load_err_t result = cart_load_emulator_path(menu, CART_LOAD_EMU_TYPE_SNES, rom_path, NULL);
    path_free(rom_path);
    if (result != CART_LOAD_OK) {
        const diagnostic_pool_report_t *report = diagnostic_pool_report();
        remote_reply(request, "ERR", "LOAD loader=%u flashcart=%u recovery=1 pool_stage=%s pool_slot=%u pool_sector=%u pool_value=%u pool_limit=%u",
                     (unsigned)result, (unsigned)menu->flashcart_err, report->stage,
                     report->slot, report->sector, report->value, report->limit);
        return;
    }
    /* This ACK confirms loader readiness. Only a subsequent emulator hello
     * from the host confirms startup; never transition if TX failed. */
    if (!remote_reply(request, "OK", "ready=launch mode=menu rom_offset=00104000")) return;
    command_reboot(menu);
    menu->mode = MENU_MODE_BOOT;
}

static void remote_install(menu_t *menu, remote_request_t *request) {
    char target[S64_REMOTE_PATH_MAX + 1], checksum[9], length[11];
    int terminator;
    uint32_t expected, size;
    if (!remote_string(request, target, sizeof target, ' ', &terminator) || terminator != ' ' ||
        !s64_remote_install_path(target)) {
        remote_reply(request, "ERR", "PATH");
        return;
    }
    uint32_t maximum = !strcmp(target, S64_REMOTE_MENU) ? S64_REMOTE_MENU_MAX : S64_REMOTE_PROGRAM_MAX;
    if (!remote_string(request, checksum, sizeof checksum, ' ', &terminator) || terminator != ' ' ||
        !s64_remote_hex32(checksum, &expected)) {
        remote_reply(request, "ERR", "CRC_ARGUMENT");
        return;
    }
    if (remote_char(request) != '@' ||
        !remote_string(request, length, sizeof length, '@', &terminator) || terminator != '@' ||
        !s64_remote_size(length, maximum, &size) || size < 4096 ||
        request->remaining != size + 1) {
        remote_reply(request, "ERR", "SIZE");
        return;
    }
    if (!menu->storage_prefix || menu->mode == MENU_MODE_BOOT || menu->next_mode == MENU_MODE_BOOT) {
        remote_reply(request, "ERR", "BUSY");
        return;
    }
    path_t *destination = path_init(menu->storage_prefix, target);
    char temporary[384], previous[384];
    snprintf(temporary, sizeof temporary, "%s.tmp.%s", path_get(destination), request->id);
    snprintf(previous, sizeof previous, "%s.previous.%s", path_get(destination), request->id);
    if (strlen(path_get(destination)) + 19 >= sizeof previous ||
        remote_exists(temporary) || remote_exists(previous)) {
        path_free(destination);
        remote_reply(request, "ERR", "COLLISION");
        return;
    }
    FILE *file = fopen(temporary, "wb");
    if (!file) {
        path_free(destination);
        remote_reply(request, "ERR", "CREATE");
        return;
    }
    unsigned char buffer[8192];
    uint32_t crc = 0xffffffffu, remaining = size;
    bool failed = false, magic = false;
    while (remaining) {
        uint32_t block = remaining < sizeof buffer ? remaining : sizeof buffer;
        usb_read(buffer, block);
        request->remaining -= block;
        if (remaining == size) magic = buffer[0] == 0x80 && buffer[1] == 0x37 &&
            buffer[2] == 0x12 && buffer[3] == 0x40;
        crc = s64_remote_crc32(crc, buffer, block);
        if (fwrite(buffer, 1, block, file) != block) { failed = true; break; }
        remaining -= block;
    }
    if (fclose(file)) failed = true;
    crc ^= 0xffffffffu;
    if (failed || remaining || remote_char(request) != 0 || request->remaining || !magic || crc != expected) {
        remove(temporary);
        path_free(destination);
        remote_reply(request, "ERR", failed ? "WRITE" : (!magic ? "PROGRAM" : "CRC"));
        return;
    }
    /* Reopen the closed FAT file and verify its exact persisted length/body. */
    file = fopen(temporary, "rb");
    uint32_t verified = 0, verify_crc = 0xffffffffu;
    failed = !file;
    if (file) {
        size_t bytes;
        while ((bytes = fread(buffer, 1, sizeof buffer, file)) != 0) {
            if (bytes > size - verified) { failed = true; break; }
            verified += bytes;
            verify_crc = s64_remote_crc32(verify_crc, buffer, bytes);
        }
        if (ferror(file)) failed = true;
        if (fclose(file)) failed = true;
    }
    if (failed || verified != size || (verify_crc ^ 0xffffffffu) != expected) {
        remove(temporary);
        path_free(destination);
        remote_reply(request, "ERR", "READBACK");
        return;
    }
    bool had_previous = remote_exists(path_get(destination));
    if (had_previous && !file_exists(path_get(destination))) {
        remove(temporary);
        path_free(destination);
        remote_reply(request, "ERR", "FILE");
        return;
    }
    if (had_previous && remote_rename(path_get(destination), previous) != FR_OK) {
        remove(temporary);
        path_free(destination);
        remote_reply(request, "ERR", "BACKUP");
        return;
    }
    if (remote_rename(temporary, path_get(destination)) != FR_OK) {
        bool rollback_failed = had_previous && remote_rename(previous, path_get(destination)) != FR_OK;
        path_free(destination);
        remote_reply(request, "ERR", "COMMIT rollback_failed=%u temporary_retained=1", rollback_failed);
        return;
    }
    path_free(destination);
    remote_reply(request, "OK", "installed=1 verified=1 bytes=%u crc32=%08x previous=%u",
                 (unsigned)size, (unsigned)expected, had_previous);
}

static void command_remote(menu_t *menu) {
    remote_request_t request = { .remaining = USBHEADER_GETSIZE(usb_poll()), .id = "00000000" };
    char id[9], verb[16], argument[S64_REMOTE_PATH_MAX + 1];
    int terminator;
    if (!remote_string(&request, id, sizeof id, ' ', &terminator) || terminator != ' ' ||
        !s64_remote_hex32(id, NULL)) {
        remote_reply(&request, "ERR", "ID");
        return;
    }
    memcpy(request.id, id, sizeof id);
    if (!remote_string(&request, verb, sizeof verb, ' ', &terminator)) {
        remote_reply(&request, "ERR", "COMMAND");
        return;
    }
    if (!strcmp(verb, "install")) {
        if (terminator != ' ') remote_reply(&request, "ERR", "ARGUMENT");
        else remote_install(menu, &request);
        return;
    }
    if (!strcmp(verb, "hello") || !strcmp(verb, "status")) {
        if (terminator != 0 || request.remaining) remote_reply(&request, "ERR", "ARGUMENT");
        else remote_reply(&request, "OK", "mode=menu protocol=1 build=%s capabilities=hello,status,list,listdir,launch,install recovery=%u program_max=%u menu_max=%u",
                          S64_REMOTE_BUILD, remote_recovery, S64_REMOTE_PROGRAM_MAX, S64_REMOTE_MENU_MAX);
        return;
    }
    if (terminator != ' ' || !remote_string(&request, argument, sizeof argument, 0, NULL) || request.remaining) {
        remote_reply(&request, "ERR", "ARGUMENT");
        return;
    }
    if (!strcmp(verb, "list") || !strcmp(verb, "listdir")) remote_list(menu, &request, argument);
    else if (!strcmp(verb, "launch")) remote_launch(menu, &request, argument);
    else remote_reply(&request, "ERR", "COMMAND");
}

#endif
