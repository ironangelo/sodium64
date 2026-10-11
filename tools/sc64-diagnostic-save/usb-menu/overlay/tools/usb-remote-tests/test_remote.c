/* Synthetic files only. Executes the real menu USB parser and emulator loader
 * with mocked hardware/pool publication; this is never physical evidence. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libdragon.h>
#include <usb.h>
#include <fatfs/ff.h>
#include "menu/usb_comm.h"
#include "menu/cart_load.h"
#include "menu/usb_remote_protocol.h"
#include "menu/diagnostic_pool.h"

static unsigned char packet[S64_REMOTE_MENU_MAX + 512];
static size_t packet_bytes, packet_position;
static char replies[8192], loaded_game[512], pool_save[512];
static uint32_t loaded_offset, loaded_file_offset, pool_offset;
static uint64_t pool_emulator_bytes;
static unsigned calls, saves, pools, boots, invalidates, checks;
static int fail_load, fail_pool, fail_ack;
static int fail_backup, fail_commit, fail_rollback;
static unsigned fat_renames;
static menu_t menu;
static boot_params_t parameters;

int remote_test_rename(const char *source, const char *destination) {
    if ((fail_backup && strstr(destination, ".previous.")) ||
        (fail_commit && strstr(source, ".tmp.")) ||
        (fail_rollback && strstr(source, ".previous."))) return -1;
    return rename(source, destination);
}

FRESULT f_rename(const TCHAR *source, const TCHAR *destination) {
    assert(!strstr(source, ":/") && !strstr(destination, ":/"));
    fat_renames++;
    return remote_test_rename(source, destination) ? FR_DISK_ERR : FR_OK;
}

unsigned long usb_poll(void) {
    return packet_position < packet_bytes ? (DATATYPE_TEXT << 24) | (packet_bytes - packet_position) : 0;
}
void usb_read(void *buffer, int size) {
    assert(size >= 0 && (size_t)size <= packet_bytes - packet_position);
    memcpy(buffer, packet + packet_position, size);
    packet_position += size;
}
void usb_purge(void) { packet_position = packet_bytes; }
char usb_write(int type, const void *data, int size) {
    assert(type == DATATYPE_TEXT && packet_position == packet_bytes);
    assert(strlen(replies) + size < sizeof replies);
    strncat(replies, data, size);
    return fail_ack ? 0 : 1;
}
bool is_memory_expanded(void) { return true; }
uint32_t io_read(uint32_t address) { (void)address; return 0; }
void rspq_wait(void) {}
void sound_deinit(void) {}
bool flashcart_has_feature(flashcart_features_t feature) { (void)feature; return true; }
rom_save_type_t rom_info_get_save_type(rom_info_t *info) { (void)info; assert(false); return SAVE_TYPE_NONE; }
flashcart_err_t flashcart_load_64dd_ipl(char *path, flashcart_progress_callback_t progress) {
    (void)path; (void)progress; assert(false); return FLASHCART_ERR_LOAD;
}
flashcart_err_t flashcart_load_64dd_disk(char *path, flashcart_disk_parameters_t *parameters) {
    (void)path; (void)parameters; assert(false); return FLASHCART_ERR_LOAD;
}
flashcart_err_t flashcart_load_64dd_disks(char *path, flashcart_disk_parameters_t *parameters, char **swap, int count) {
    (void)path; (void)parameters; (void)swap; (void)count; assert(false); return FLASHCART_ERR_LOAD;
}
flashcart_err_t flashcart_load_rom(char *path, bool swap, flashcart_progress_callback_t progress) {
    assert(strstr(path, "/menu/emulators/sodium64-remote.z64") && !swap && !progress);
    calls++;
    return fail_load ? FLASHCART_ERR_LOAD : FLASHCART_OK;
}
flashcart_err_t flashcart_load_file(char *path, uint32_t offset, uint32_t file_offset) {
    strcpy(loaded_game, path); loaded_offset = offset; loaded_file_offset = file_offset;
    return FLASHCART_OK;
}
flashcart_err_t flashcart_load_save(char *path, flashcart_save_type_t type) {
    assert(!path && type == FLASHCART_SAVE_TYPE_SRAM_256KBIT); saves++;
    return FLASHCART_OK;
}
flashcart_err_t flashcart_set_next_boot_mode(flashcart_reboot_mode_t mode) {
    assert(mode == FLASHCART_REBOOT_MODE_MENU); boots++;
    return FLASHCART_OK;
}
void diagnostic_pool_menu_invalidate(void) { invalidates++; }
const diagnostic_pool_report_t *diagnostic_pool_report(void) {
    static const diagnostic_pool_report_t report = { .stage = "host_mock" };
    return &report;
}
bool diagnostic_pool_menu_prepare(const char *save, const char *tag, unsigned slots,
                                 uint32_t offset, uint64_t emulator_bytes, char **reserved) {
    assert(!strcmp(tag, "usb-loop") && slots == 16);
    pools++; strcpy(pool_save, save); pool_offset = offset; pool_emulator_bytes = emulator_bytes;
    *reserved = fail_pool ? NULL : strdup(save);
    return fail_pool;
}
bool diagnostic_pool_menu_load_initial(const char *path) { assert(path); return false; }
bool diagnostic_save_reserve(const char *a, const char *b, char **c) {
    (void)a; (void)b; (void)c; assert(false); return true;
}
int dir_findfirst(const char *path, dir_t *entry) {
    (void)path; strcpy(entry->d_name, "Private Game.sfc"); entry->d_type = DT_REG; entry->d_size = 4096; return 0;
}
int dir_findnext(const char *path, dir_t *entry) { (void)path; (void)entry; return -1; }

static void request(const char *text) {
    packet_bytes = strlen(text) + 1; memcpy(packet, text, packet_bytes);
    packet_position = 0; replies[0] = 0; usb_comm_poll(&menu);
    assert(packet_position == packet_bytes);
}
static void expect(const char *text) { assert(strstr(replies, text)); checks++; }
static void write_file(const char *relative, const void *data, size_t bytes) {
    char path[512]; snprintf(path, sizeof path, "%s%s", menu.storage_prefix, relative);
    FILE *file = fopen(path, "wb"); assert(file); assert(fwrite(data, 1, bytes, file) == bytes); assert(!fclose(file));
}
static bool exists(const char *relative) {
    char path[512]; snprintf(path, sizeof path, "%s%s", menu.storage_prefix, relative);
    FILE *file = fopen(path, "rb"); if (!file) return false; fclose(file); return true;
}
static void install_path(const char *id, const char *target, uint32_t crc, const unsigned char *program, size_t bytes) {
    int header = snprintf((char *)packet, sizeof packet,
        "s64 %s install %s %08x @%u@", id, target, crc, (unsigned)bytes);
    memcpy(packet + header, program, bytes); packet[header + bytes] = 0;
    packet_bytes = header + bytes + 1; packet_position = 0; replies[0] = 0; usb_comm_poll(&menu);
}
static void install(const char *id, uint32_t crc, const unsigned char *program, size_t bytes) {
    install_path(id, "/menu/emulators/sodium64-remote.z64", crc, program, bytes);
}
static void ini(unsigned offset) {
    char text[512];
    snprintf(text, sizeof text, "[snes]\nrom=sodium64-remote.z64\nrom_offset=0x%x\nsave_type=3\n"
        "diagnostic_saves=1\ndiagnostic_continuous=1\ndiagnostic_slots=16\ndiagnostic_tag=usb-loop\n", offset);
    write_file("/menu/emulators.ini", text, strlen(text));
}

int main(int argc, char **argv) {
    assert(argc == 2); menu.storage_prefix = argv[1]; menu.boot_params = &parameters; menu.mode = MENU_MODE_BROWSER;
    uint32_t value;
    assert(s64_remote_hex32("dEaDbeef", &value) && value == 0xdeadbeef);
    assert(!s64_remote_hex32("12", NULL) && !s64_remote_hex32("0000000g", NULL));
    assert(s64_remote_size("1056768", S64_REMOTE_PROGRAM_MAX, &value));
    assert(!s64_remote_size("1056769", S64_REMOTE_PROGRAM_MAX, &value));
    assert(!s64_remote_size("-1", S64_REMOTE_PROGRAM_MAX, &value));
    assert(s64_remote_path("/SNES/Private Game.sfc", false));
    assert(!s64_remote_path("/SNES/../secret.sfc", false) && !s64_remote_path("/SNES//file", false));
    assert(!s64_remote_path("sd:/SNES/a.sfc", false) && !s64_remote_path("/SNES/a\n.sfc", false));
    assert(!s64_remote_install_path("/menu/sc64menu.z64") && !s64_remote_install_path("/menu/emulators/a.sav"));
    assert(!s64_remote_install_path("/menu/emulators/../a.z64"));
    assert(s64_remote_install_path("/sc64menu.n64") && !s64_remote_install_path("/sc64menu.n64.other"));
    assert((s64_remote_crc32(0xffffffffu, "123456789", 9) ^ 0xffffffffu) == 0xcbf43926u); checks += 12;
    request("s64 abcdef12 hello"); expect("S64 abcdef12 OK mode=menu protocol=1");
    request("s64 ABCDEF12 status"); expect("S64 ABCDEF12 OK");
    request("s64 invalid0 hello"); expect("S64 00000000 ERR ID");
    request("s64 00000001 hello extra"); expect("ERR ARGUMENT");
    request("s64 00000002 list /SNES"); expect("ITEM file 4096 /SNES/Private Game.sfc"); expect("OK count=1");
    request("s64 00000003 listdir /missing"); expect("ERR DIRECTORY");
    request("s64 00000004 launch /SNES/../Private Game.sfc"); expect("ERR PATH");
    request("s64 00000005 install /SNES/game.sfc 00000000 @1@x"); expect("ERR PATH");
    request("s64 00000006 install /menu/emulators/test.z64 zzzzzzzz @1@x"); expect("ERR CRC_ARGUMENT");
    request("s64 00000007 install /menu/emulators/test.z64 00000000 @99999999@x"); expect("ERR SIZE");
    request("s64 00000008 launch /SNES/Private Game.sfc");
    packet_bytes--; packet_position = 0; replies[0] = 0; usb_comm_poll(&menu); expect("ERR ARGUMENT");
    unsigned char program[4096] = {0x80,0x37,0x12,0x40};
    unsigned char game[4608] = {1,2,3};
    uint32_t crc = s64_remote_crc32(0xffffffffu, program, sizeof program) ^ 0xffffffffu;
    write_file("/menu/emulators/sodium64-remote.z64", program, sizeof program);
    write_file("/SNES/Private Game.sfc", game, sizeof game);
    install("00000010", crc ^ 1, program, sizeof program); expect("ERR CRC");
    assert(!exists("/menu/emulators/sodium64-remote.z64.tmp.00000010"));
    install("00000011", crc, program, sizeof program); expect("OK installed=1 verified=1 bytes=4096");
    assert(fat_renames == 2); checks++;
    assert(exists("/menu/emulators/sodium64-remote.z64.previous.00000011"));
    install("00000012", crc, program, sizeof program); expect("OK installed=1 verified=1");
    assert(exists("/menu/emulators/sodium64-remote.z64.previous.00000011"));
    assert(exists("/menu/emulators/sodium64-remote.z64.previous.00000012"));
    install("00000012", crc, program, sizeof program); expect("ERR COLLISION");
    program[0] = 0;
    install("00000019", s64_remote_crc32(0xffffffffu, program, sizeof program) ^ 0xffffffffu,
            program, sizeof program); expect("ERR PROGRAM");
    assert(exists("/menu/emulators/sodium64-remote.z64")); program[0] = 0x80;
    fail_backup = 1;
    install("00000020", crc, program, sizeof program); expect("ERR BACKUP");
    assert(exists("/menu/emulators/sodium64-remote.z64") && !exists("/menu/emulators/sodium64-remote.z64.tmp.00000020"));
    fail_backup = 0; fail_commit = 1;
    install("00000021", crc, program, sizeof program); expect("ERR COMMIT rollback_failed=0 temporary_retained=1");
    assert(exists("/menu/emulators/sodium64-remote.z64") && exists("/menu/emulators/sodium64-remote.z64.tmp.00000021"));
    fail_rollback = 1;
    install("00000022", crc, program, sizeof program); expect("ERR COMMIT rollback_failed=1 temporary_retained=1");
    assert(!exists("/menu/emulators/sodium64-remote.z64") && exists("/menu/emulators/sodium64-remote.z64.previous.00000022"));
    fail_commit = fail_rollback = 0;
    char previous[512], destination[512];
    snprintf(previous, sizeof previous, "%s/menu/emulators/sodium64-remote.z64.previous.00000022", menu.storage_prefix);
    snprintf(destination, sizeof destination, "%s/menu/emulators/sodium64-remote.z64", menu.storage_prefix);
    assert(!rename(previous, destination));
    /* A menu exceeds the emulator bank limit and is still committed only after
     * closed-file readback. Bad CRC and failed rename preserve the old menu. */
    size_t menu_bytes = S64_REMOTE_PROGRAM_MAX + 4096;
    unsigned char *new_menu = calloc(1, menu_bytes); assert(new_menu);
    memcpy(new_menu, program, sizeof program);
    uint32_t menu_crc = s64_remote_crc32(0xffffffffu, new_menu, menu_bytes) ^ 0xffffffffu;
    write_file(S64_REMOTE_MENU, program, sizeof program);
    install_path("00000023", S64_REMOTE_MENU, menu_crc ^ 1, new_menu, menu_bytes); expect("ERR CRC");
    assert(exists(S64_REMOTE_MENU) && !exists("/sc64menu.n64.tmp.00000023"));
    install_path("00000024", S64_REMOTE_MENU, menu_crc, new_menu, menu_bytes); expect("OK installed=1 verified=1");
    assert(exists("/sc64menu.n64.previous.00000024"));
    fail_commit = 1;
    install_path("00000025", S64_REMOTE_MENU, menu_crc, new_menu, menu_bytes); expect("ERR COMMIT rollback_failed=0");
    assert(exists(S64_REMOTE_MENU)); fail_commit = 0; free(new_menu);
    request("s64 00000026 install /sc64menu.n64 00000000 @4194305@x"); expect("ERR SIZE");
    ini(0x200000);
    request("s64 00000013 launch /SNES/Private Game.sfc"); expect("ERR INI"); assert(!calls);
    ini(0x104000); menu.browser.entry = NULL; menu.browser.directory = NULL;
    request("s64 00000014 launch /SNES/Private Game.sfc"); expect("OK ready=launch");
    assert(menu.mode == MENU_MODE_BOOT && menu.next_mode == MENU_MODE_BOOT);
    assert(parameters.device_type == BOOT_DEVICE_TYPE_ROM && parameters.detect_cic_seed && !parameters.clear_rdram);
    assert(strstr(loaded_game, "/SNES/Private Game.sfc") && loaded_offset == 0x104000 && loaded_file_offset == 0x200);
    assert(strstr(pool_save, "/SNES/Private Game.sav") && pool_offset == 0x104000 && pool_emulator_bytes == sizeof program);
    assert(calls == 1 && pools == 1 && saves == 1 && boots == 1 && invalidates == 1); checks += 5;
    menu.mode = menu.next_mode = MENU_MODE_BROWSER; fail_load = 1;
    request("s64 00000015 launch /SNES/Private Game.sfc"); expect("ERR LOAD loader=");
    assert(menu.mode == MENU_MODE_NONE && menu.next_mode == MENU_MODE_NONE); checks++;
    fail_load = 0; fail_pool = 1;
    request("s64 00000016 launch /SNES/Private Game.sfc"); expect("ERR LOAD loader=");
    expect("pool_stage=host_mock pool_slot=0 pool_sector=0 pool_value=0 pool_limit=0");
    assert(menu.mode == MENU_MODE_NONE && menu.next_mode == MENU_MODE_NONE); checks++;
    fail_pool = 0; fail_ack = 1;
    request("s64 00000017 launch /SNES/Private Game.sfc"); expect("OK ready=launch");
    assert(menu.mode == MENU_MODE_NONE && menu.next_mode == MENU_MODE_NONE); checks++;
    fail_ack = 0; request("s64 00000018 status"); expect("recovery=1");
    printf("USB menu host: %u checks passed; mocked hardware, synthetic inputs only\n", checks);
    return 0;
}
