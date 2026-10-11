/* SPDX-License-Identifier: GPL-3.0-or-later
 * Continuous diagnostic SD sink. The menu owns FAT and reserves closed files;
 * this code writes only their validated, disjoint data-sector lists. Never FAT.
 * No commercial content is linked. A successful PI DMA is not an SD receipt.
 */
#include <stdint.h>
#include <stddef.h>
#include "../tools/sc64-diagnostic-save/continuous_save_abi.h"
#include "../tools/sc64-diagnostic-save/recorder_runtime_abi.h"

uint32_t continuous_save_error_stage, continuous_save_error_code;
uint32_t continuous_save_sc64_status, continuous_save_data0;
uint32_t continuous_save_pi_status, continuous_save_last_command;
uint32_t continuous_save_sd_status, continuous_save_sink_ready;
static unsigned error_stage;
static int cs_fail(unsigned code) {
    /* Retain the first physical failure across USB-only captures and retries. */
    if (!continuous_save_error_code) {
        continuous_save_error_stage=error_stage;
        continuous_save_error_code=code;
    }
    return 0;
}

enum { META_CART = 0x10102000, META_BYTES = 8192, HEADER_BYTES = 72,
       SLOT_BYTES = 264, MAX_SLOTS = 16, SECTORS = 64, SAVE_BYTES = 32768,
       BRAM = 0x1ffe0000, MAGIC = 0x53363443 };
_Static_assert(META_CART==S64C_CART_ADDRESS && HEADER_BYTES==S64C_HEADER_BYTES &&
               SLOT_BYTES==S64C_SLOT_BYTES && MAX_SLOTS==S64C_MAX_SLOTS &&
               SECTORS==S64C_SECTORS && SAVE_BYTES==S64C_SAVE_BYTES &&
               MAGIC==S64C_MAGIC, "paired menu ABI mismatch");

#ifdef CONTINUOUS_SAVE_HOST
/* The host test compiles THIS algorithm and supplies the hardware boundary. */
extern uint32_t cs_meta_word(unsigned offset);
extern int cs_begin(void);
extern int cs_info(unsigned char info[32]);
extern int cs_read(uint32_t lba, unsigned char data[512]);
extern int cs_write(uint32_t lba, const unsigned char data[512]);
#else
#ifdef CONTINUOUS_SAVE_TRANSPORT_HOST
extern uint32_t cs_transport_count(void);
extern uint32_t cs_transport_reg_read(unsigned index);
extern void cs_transport_reg_write(unsigned index, uint32_t value);
extern uint32_t cs_transport_pi_read(unsigned index);
extern void cs_transport_pi_write(unsigned index, uint32_t value);
extern uint32_t cs_transport_meta_word(unsigned offset);
#define cs_count cs_transport_count
#define reg_read cs_transport_reg_read
#define reg_write cs_transport_reg_write
#define pi_read cs_transport_pi_read
#define pi_write cs_transport_pi_write
#define meta_read cs_transport_meta_word
#define cs_sync() ((void)0)
#else
static uint32_t cs_count(void) {
    uint32_t n; __asm__ volatile ("mfc0 %0,$9" : "=r"(n)); return n;
}
static volatile uint32_t *const regs = (volatile uint32_t *)0xbfff0000;
static volatile uint32_t *const pi = (volatile uint32_t *)0xa4600000;
static uint32_t reg_read(unsigned i) { return regs[i]; }
static void reg_write(unsigned i,uint32_t v) { regs[i]=v; }
static uint32_t pi_read(unsigned i) { return pi[i]; }
static void pi_write(unsigned i,uint32_t v) { pi[i]=v; }
#define cs_sync() __asm__ volatile ("sync" ::: "memory")
static uint32_t meta_read(unsigned offset) {
    return *(volatile uint32_t *)(uintptr_t)(0xb0102000u + offset);
}
#endif
/* PI cart PIO writes are asynchronous. Every subsequent cart access must wait
 * for both DMA and IO idle, including KEY words and descriptor reads. Callers
 * already exclude guest PI DMA (startup or native diagnostic finalization).
 * Retain a sticky PI error; never reset an engine of unknown ownership. */
static int cs_pi_idle(void) {
    if (continuous_save_error_code) return 0;
    uint32_t start=cs_count();
    while ((continuous_save_pi_status=pi_read(4))&3)
        if ((uint32_t)(cs_count()-start)>=46875000u)
            return cs_fail(S64_SAVE_ERROR_PI_TIMEOUT);
    return !(continuous_save_pi_status&4) || cs_fail(S64_SAVE_ERROR_PI);
}
static int cs_reg_read(unsigned index,uint32_t *value) {
    if (!cs_pi_idle()) return 0;
    *value=reg_read(index);
    return 1;
}
static int cs_reg_write(unsigned index,uint32_t value) {
    if (!cs_pi_idle()) return 0;
    reg_write(index,value);
    cs_sync();
    return 1;
}
static uint32_t cs_meta_word(unsigned offset) {
    if (!cs_pi_idle()) return 0;
    return meta_read(offset);
}
/* Both the command engine and PI transfers have finite Count-domain waits.
 * On any timeout the session is disabled: do not send a new command into an
 * engine whose previous ownership is unknown. No SRAM auto-writeback is used.
 */
static int cs_command(unsigned command, uint32_t a, uint32_t b) {
    if (continuous_save_error_code) return 0;
    uint32_t start = cs_count();
    continuous_save_last_command=command;
    for (;;) {
        if (!cs_reg_read(0,&continuous_save_sc64_status)) return 0;
        if (!(continuous_save_sc64_status&0x80000000u)) break;
        if ((uint32_t)(cs_count()-start) >= 46875000u*4) {
            return cs_fail(S64_SAVE_ERROR_COMMAND_TIMEOUT);
        }
    }
    if (!cs_reg_write(1,a) || !cs_reg_write(2,b) || !cs_reg_write(0,command)) return 0;
    start=cs_count();
    for (;;) {
        if (!cs_reg_read(0,&continuous_save_sc64_status)) return 0;
        if (!(continuous_save_sc64_status&0x80000000u)) break;
        if ((uint32_t)(cs_count()-start) >= 46875000u*4) {
            return cs_fail(S64_SAVE_ERROR_COMMAND_TIMEOUT);
        }
    }
    if (!cs_reg_read(1,&continuous_save_data0)) return 0;
    return !(continuous_save_sc64_status & 0x40000000u) || cs_fail(S64_SAVE_ERROR_SC64);
}
static int cs_pi(void *ram, uint32_t cart, unsigned n, int to_cart) {
    if (!cs_pi_idle()) return 0;
    cs_sync();
    pi_write(0,(uint32_t)(uintptr_t)ram&0x1fffffffu); pi_write(1,cart);
    pi_write(to_cart?2:3,n-1);
    if (!cs_pi_idle()) return 0;
    cs_sync();
    return 1;
}
static int cs_begin(void) {
    error_stage=S64_SAVE_STAGE_UNLOCK;
    if (!cs_reg_write(4,0) || !cs_reg_write(4,0x5f554e4c) ||
        !cs_reg_write(4,0x4f434b5f) || !cs_reg_read(3,&continuous_save_data0)) return 0;
    if (continuous_save_data0!=0x53437632) return cs_fail(S64_SAVE_ERROR_IDENTIFIER);
    /* The paired menu never enables save writeback. SD INIT acquires N64 lock;
     * byte swapping is explicitly off for raw byte-identical save files. */
    error_stage=S64_SAVE_STAGE_SD_INIT;
    if (!cs_command('i',0,1)) return 0;
    error_stage=S64_SAVE_STAGE_SD_SWAP;
    if (!cs_command('i',0,5)) return 0;
    error_stage=S64_SAVE_STAGE_SD_STATUS;
    if (!cs_command('i',0,2)) return 0;
    if (!cs_reg_read(2,&continuous_save_sd_status)) return 0;
    if ((continuous_save_sd_status&0x13)!=3) return cs_fail(S64_SAVE_ERROR_SD_STATUS);
    return 1;
}
static unsigned char sector_buffer[512] __attribute__((aligned(16)));
static unsigned char *cs_buffer(void) {
#ifdef CONTINUOUS_SAVE_TRANSPORT_HOST
    return sector_buffer;
#else
    return (unsigned char *)((uintptr_t)sector_buffer|0xa0000000u);
#endif
}
static int cs_info(unsigned char info[32]) {
    return cs_command('i',BRAM,3) && cs_pi(info,BRAM,32,0);
}
static int cs_read(uint32_t lba, unsigned char data[512]) {
    return cs_command('I',lba,0) && cs_command('s',BRAM,1) && cs_pi(data,BRAM,512,0);
}
static int cs_write(uint32_t lba, const unsigned char data[512]) {
    return cs_pi((void *)data,BRAM,512,1) && cs_command('I',lba,0) && cs_command('S',BRAM,1);
}
#endif

#ifdef CONTINUOUS_SAVE_HOST
static unsigned char sector_buffer[512];
static unsigned char *cs_buffer(void) { return sector_buffer; }
#endif
static unsigned slots, cursor;
/* Public ID is used only for the UI and remains zero until verified success. */
uint32_t continuous_save_last_id;

static uint32_t slot_word(unsigned slot, unsigned offset) {
    return cs_meta_word(HEADER_BYTES+slot*SLOT_BYTES+offset);
}
static int metadata_valid(void) {
    error_stage=S64_SAVE_STAGE_DESCRIPTOR;
    unsigned n=cs_meta_word(12), bytes=cs_meta_word(8);
    if (cs_meta_word(0)!=MAGIC || cs_meta_word(4)!=1 || !n || n>MAX_SLOTS ||
        bytes!=HEADER_BYTES+n*SLOT_BYTES || bytes>META_BYTES ||
        cs_meta_word(16)!=SECTORS || cs_meta_word(20)!=SAVE_BYTES ||
        cs_meta_word(24)!=0x104000) return cs_fail(S64_SAVE_ERROR_DESCRIPTOR_FORMAT);
    uint32_t sum=0,first=cs_meta_word(64),end=cs_meta_word(68);
    if (!first || end<=first) return cs_fail(S64_SAVE_ERROR_DESCRIPTOR_MAP);
    for (unsigned i=0;i<bytes;i+=4) sum+=cs_meta_word(i);
    if (sum) return cs_fail(S64_SAVE_ERROR_DESCRIPTOR_CHECKSUM);
    for (unsigned i=0;i<n;i++) {
        uint32_t id=slot_word(i,0);
        if (!id || id>999999 || slot_word(i,4)) return cs_fail(S64_SAVE_ERROR_DESCRIPTOR_MAP);
        for (unsigned j=0;j<i;j++) if (id==slot_word(j,0)) return cs_fail(S64_SAVE_ERROR_DESCRIPTOR_MAP);
        for (unsigned j=0;j<SECTORS;j++) {
            uint32_t lba=slot_word(i,8+j*4);
            if (lba<first || lba>=end) return cs_fail(S64_SAVE_ERROR_DESCRIPTOR_MAP);
            /* Global uniqueness, including each fragmented file's own map. */
            for (unsigned k=0;k<=i;k++) {
                unsigned limit=k==i?j:SECTORS;
                for (unsigned l=0;l<limit;l++)
                    if (lba==slot_word(k,8+l*4)) return cs_fail(S64_SAVE_ERROR_DESCRIPTOR_MAP);
            }
        }
    }
    return !continuous_save_error_code;
}
static int card_matches(void) {
    error_stage=S64_SAVE_STAGE_CARD_INFO;
    unsigned char *b=cs_buffer();
    if (!cs_info(b)) return cs_fail(S64_SAVE_ERROR_TRANSPORT);
    for (unsigned i=0;i<32;i++) {
        uint32_t word=cs_meta_word(32+(i&~3u));
        if (b[i]!=(unsigned char)(word>>(24-(i&3)*8))) return cs_fail(S64_SAVE_ERROR_CARD_MISMATCH);
    }
    return !continuous_save_error_code;
}
int continuous_save_init(void) {
    continuous_save_sink_ready=0; slots=cursor=0; continuous_save_last_id=0;
    continuous_save_error_stage=continuous_save_error_code=0;
    continuous_save_sc64_status=continuous_save_data0=continuous_save_pi_status=0;
    continuous_save_last_command=continuous_save_sd_status=0;
    error_stage=S64_SAVE_STAGE_DESCRIPTOR;
    uint32_t magic=cs_meta_word(0);
    if (continuous_save_error_code) return -1;
    if (magic!=MAGIC) { cs_fail(S64_SAVE_ERROR_DESCRIPTOR_MISSING); return 0; }
    if (!metadata_valid()) return -1;
    error_stage=S64_SAVE_STAGE_SD_INIT;
    if (!cs_begin()) { cs_fail(S64_SAVE_ERROR_TRANSPORT); return -1; }
    if (!card_matches()) return -1;
    slots=cs_meta_word(12);
    if (continuous_save_error_code) return -1;
    continuous_save_sink_ready=1; return 1;
}
static int equal(const unsigned char *a, const unsigned char *b, unsigned n) {
    for (unsigned i=0;i<n;i++) if (a[i]!=b[i]) return 0;
    return 1;
}
static uint32_t source_word(const unsigned char *p) {
    return (uint32_t)p[0]<<24 | (uint32_t)p[1]<<16 | (uint32_t)p[2]<<8 | p[3];
}
static int source_valid(const unsigned char *source) {
    const unsigned char *h=source+8192;
    if (source_word(h)!=0x53363444 || source_word(h+4)!=5 ||
        source_word(h+8)!=1 || source_word(h+16)!=SAVE_BYTES) return 0;
    uint32_t sum=0;
    for (unsigned i=0;i<SAVE_BYTES;i+=4)
        if (i<8192 || i>=8704) sum+=source_word(source+i);
    return sum==source_word(h+240);
}
static int write_verified(uint32_t lba, const unsigned char *data) {
    unsigned char *b=cs_buffer();
    /* data may be this same buffer (incomplete header). Retain its expected
     * bytes in the cart BRAM? Readback replaces it, so header path instead uses
     * a source view plus a completeness override in the caller below. */
    if (!cs_write(lba,data) || !cs_read(lba,b)) return cs_fail(S64_SAVE_ERROR_TRANSPORT);
    return equal(data,b,512) || cs_fail(S64_SAVE_ERROR_READBACK);
}
int continuous_save_capture(const unsigned char *source, unsigned bytes) {
    if (!continuous_save_sink_ready) { cs_fail(S64_SAVE_ERROR_UNAVAILABLE); return 0; }
    error_stage=S64_SAVE_STAGE_SOURCE;
    if (bytes!=SAVE_BYTES || !source || !source_valid(source)) {
        cs_fail(S64_SAVE_ERROR_SOURCE); goto fail;
    }
    if (!metadata_valid() || !card_matches()) goto fail;
    unsigned char *b=cs_buffer();
    unsigned chosen;
    for (;;) {
        error_stage=S64_SAVE_STAGE_SLOT_SCAN;
        if (cursor>=slots) {
            continuous_save_sink_ready=0;
            cs_fail(S64_SAVE_ERROR_EXHAUSTED); return -1;
        }
        chosen=cursor++; /* Never recycle a slot, including partial failures. */
        int fresh=1;
        for (unsigned j=16;j<SECTORS;j++) {
            if (!cs_read(slot_word(chosen,8+j*4),b)) { cs_fail(S64_SAVE_ERROR_TRANSPORT); goto fail; }
            for (unsigned k=0;k<512;k++) if (b[k]) fresh=0;
        }
        if (fresh) break;
        /* A reset may lose the cursor. Nonzero reservation is already used;
         * skip it without ANY write, even if its prior capture is incomplete. */
    }
    uint32_t head_lba=slot_word(chosen,8+16*4);
    error_stage=S64_SAVE_STAGE_HEADER_BEGIN;
    for (unsigned k=0;k<512;k++) b[k]=source[8192+k];
    for (unsigned k=8;k<12;k++) b[k]=0;
    if (!cs_write(head_lba,b) || !cs_read(head_lba,b)) { cs_fail(S64_SAVE_ERROR_TRANSPORT); goto fail; }
    for (unsigned k=0;k<512;k++) {
        unsigned char want=(k>=8 && k<12)?0:source[8192+k];
        if (b[k]!=want) { cs_fail(S64_SAVE_ERROR_READBACK); goto fail; }
    }
    for (unsigned j=0;j<SECTORS;j++) {
        error_stage=S64_SAVE_STAGE_BODY;
        if (j==16) continue;
        if (!write_verified(slot_word(chosen,8+j*4),source+j*512)) goto fail;
    }
    /* Commit complete=1 only after every body sector has its own readback. */
    error_stage=S64_SAVE_STAGE_HEADER_COMMIT;
    if (!write_verified(head_lba,source+8192)) goto fail;
    continuous_save_last_id=slot_word(chosen,0);
    return 1;
fail:
    continuous_save_sink_ready=0; return 0; /* Frozen recorder retained; no new SD arm. */
}
