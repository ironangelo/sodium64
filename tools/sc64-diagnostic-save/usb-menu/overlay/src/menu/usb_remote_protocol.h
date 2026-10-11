/* Private USB bench protocol primitives; no hardware or filesystem access. */
#ifndef USB_REMOTE_PROTOCOL_H
#define USB_REMOTE_PROTOCOL_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#define S64_REMOTE_PATH_MAX 255u
#define S64_REMOTE_PROGRAM_MAX 0x102000u
#define S64_REMOTE_MENU_MAX 0x400000u
#define S64_REMOTE_MENU "/sc64menu.n64"
#define S64_REMOTE_ROM_OFFSET 0x104000u
#define S64_REMOTE_PROGRAM "sodium64-remote.z64"
#define S64_REMOTE_DIRECTORY "/menu/emulators/"
#define S64_REMOTE_LIST_MAX 256u

static inline bool s64_remote_hex32(const char *text, uint32_t *value) {
    uint32_t result = 0;
    if (strlen(text) != 8) return false;
    for (unsigned i = 0; i < 8; i++) {
        unsigned char c = (unsigned char)text[i];
        unsigned n;
        if (c >= '0' && c <= '9') n = c - '0';
        else if (c >= 'a' && c <= 'f') n = c - 'a' + 10;
        else if (c >= 'A' && c <= 'F') n = c - 'A' + 10;
        else return false;
        result = (result << 4) | n;
    }
    if (value) *value = result;
    return true;
}

static inline bool s64_remote_size(const char *text, uint32_t maximum, uint32_t *value) {
    uint32_t result = 0;
    if (!*text) return false;
    for (const unsigned char *p = (const unsigned char *)text; *p; p++) {
        if (*p < '0' || *p > '9' || result > maximum / 10u ||
            (result == maximum / 10u && (unsigned)(*p - '0') > maximum % 10u)) return false;
        result = result * 10u + *p - '0';
    }
    if (!result) return false;
    *value = result;
    return true;
}

/* Paths are card-root absolute, without a host/device prefix or dot components.
 * Internal spaces are retained for private game paths; control bytes cannot
 * create additional response lines. FAT aliases/ambiguous names are rejected. */
static inline bool s64_remote_path(const char *path, bool directory) {
    size_t length = strlen(path);
    if (!length || length > S64_REMOTE_PATH_MAX || path[0] != '/') return false;
    if (length == 1) return directory;
    const char *component = path + 1;
    for (const char *p = component;; p++) {
        unsigned char c = (unsigned char)*p;
        if (c && (c < 32 || c == 127 || c == ':' || c == '\\' || c == '@' ||
                  c == '*' || c == '?' || c == '"' || c == '<' || c == '>' || c == '|')) return false;
        if (c == '/' || c == 0) {
            size_t n = (size_t)(p - component);
            if (!n || (n == 1 && component[0] == '.') ||
                (n == 2 && component[0] == '.' && component[1] == '.') ||
                component[0] == ' ' || p[-1] == ' ' || p[-1] == '.') return false;
            if (!c) break;
            component = p + 1;
        }
    }
    return true;
}

static inline bool s64_remote_install_path(const char *path) {
    if (!strcmp(path, S64_REMOTE_MENU)) return true;
    if (!s64_remote_path(path, false) ||
        strncmp(path, S64_REMOTE_DIRECTORY, sizeof(S64_REMOTE_DIRECTORY) - 1)) return false;
    const char *name = path + sizeof(S64_REMOTE_DIRECTORY) - 1;
    size_t n = strlen(name);
    if (n < 5 || n > 64 || strcmp(name + n - 4, ".z64")) return false;
    for (size_t i = 0; i < n - 4; i++) {
        char c = name[i];
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '-' || c == '_')) return false;
    }
    return true;
}

static inline uint32_t s64_remote_crc32(uint32_t crc, const void *data, size_t bytes) {
    const unsigned char *p = data;
    while (bytes--) {
        crc ^= *p++;
        for (unsigned bit = 0; bit < 8; bit++)
            crc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
    }
    return crc;
}

#endif
