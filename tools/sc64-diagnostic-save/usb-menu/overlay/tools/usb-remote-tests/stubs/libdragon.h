#ifndef USB_REMOTE_TEST_LIBDRAGON_H
#define USB_REMOTE_TEST_LIBDRAGON_H
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <dir.h>
#define debugf(...) ((void)0)
static inline void *scratch_malloc(size_t bytes) { return malloc(bytes); }
static inline void scratch_free(void *pointer) { free(pointer); }
bool is_memory_expanded(void);
uint32_t io_read(uint32_t address);
void rspq_wait(void);
#endif
