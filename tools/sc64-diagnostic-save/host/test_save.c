#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fatfs/ff.h>
#include "diagnostic_save.h"
#include "diagnostic_pool.h"
#ifndef O_BINARY
#define O_BINARY 0
#endif

static int fail_mode;
static char ordinary[1024];
static unsigned normal_write_attempts;
FRESULT f_open(FIL *f, const char *path, unsigned flags) {
    f->writing = flags & FA_WRITE;
    if (f->writing && !strcmp(path, ordinary)) normal_write_attempts++;
    if ((fail_mode == 1 && !f->writing) || (fail_mode == 2 && f->writing)) return FR_DENIED;
    int fd = open(path, (f->writing ? O_WRONLY | O_CREAT | O_EXCL : O_RDONLY) | O_BINARY, 0600);
    if (fd < 0) return errno == EEXIST ? FR_EXIST : errno == ENOENT ? FR_NO_FILE : FR_DISK_ERR;
    f->file = fdopen(fd, f->writing ? "wb" : "rb");
    assert(f->file);
    return FR_OK;
}
FRESULT f_read(FIL *f, void *p, UINT n, UINT *count) {
    if (fail_mode == 3) return FR_DISK_ERR;
    *count=fread(p, 1, n, f->file);
    return ferror(f->file) ? FR_DISK_ERR : FR_OK;
}
FRESULT f_write(FIL *f, const void *p, UINT n, UINT *count) {
    *count=fwrite(p, 1, fail_mode == 4 ? n/2 : n, f->file);
    return ferror(f->file) ? FR_DISK_ERR : FR_OK;
}
FRESULT f_sync(FIL *f) { return fflush(f->file) || fail_mode == 5 ? FR_DISK_ERR : FR_OK; }
FRESULT f_close(FIL *f) { return fclose(f->file) || (fail_mode == 6 && f->writing) ? FR_DISK_ERR : FR_OK; }
static void create(const char *p, unsigned size) {
    FILE *f=fopen(p,"wb");assert(f);
    for(unsigned i=0;i<size;i++) fputc((i*43+7)&255,f);
    assert(!fclose(f));
}
static void check(const char *p, int guest_present) {
    FILE *f=fopen(p,"rb");assert(f);
    for(unsigned i=0;i<32768;i++) assert(fgetc(f)==(i>=8192 ? 0 : guest_present ? (int)((i*43+7)&255) : 255));
    assert(fgetc(f)==EOF);fclose(f);
}
static unsigned pool_mode, pool_maps, pool_publishes, pool_cases;
static unsigned char published[S64C_MAX_BYTES];
static size_t published_bytes;
static uint32_t be32(const unsigned char *p) {
    return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];
}
static bool pool_info(void *unused, unsigned char info[S64C_SD_INFO_BYTES]) {
    (void)unused;
    memset(info,pool_mode==7?0:pool_mode==16?255:0x46,S64C_SD_INFO_BYTES);
    return pool_mode==17;
}
static bool pool_sectors(void *unused, const char *path, uint32_t sectors[S64C_SECTORS],
                         uint32_t *first, uint32_t *end) {
    (void)unused;
    check(path,1); /* The callback sees only closed, exact-size reservations. */
    unsigned id=(unsigned)strtoul(path+strlen(path)-10,NULL,10);
    assert(id);
    *first=100;*end=1000000;
    for(unsigned i=0;i<S64C_SECTORS;i++) sectors[i]=100+id*200+2*((i*5)%64);
    if(pool_mode==8) sectors[0]=0;
    if(pool_mode==9) sectors[63]=sectors[0];
    if(pool_mode==10 && pool_maps) sectors[0]=300;
    if(pool_mode==11) sectors[63]=*end;
    if(pool_mode==12 && pool_maps) ++*first;
    if(pool_mode==14) sectors[63]=0;
    ++pool_maps;
    return pool_mode==15;
}
static bool pool_publish(void *unused, const unsigned char *data, size_t bytes) {
    (void)unused;
    ++pool_publishes;
    assert(bytes<=sizeof published);
    memcpy(published,data,bytes);published_bytes=bytes;
    return pool_mode==13;
}
static void pool_setup(unsigned mode) { pool_mode=mode;pool_maps=pool_publishes=0;published_bytes=0; }
static void check_descriptor(unsigned count,unsigned first_id) {
    assert(published_bytes==S64C_HEADER_BYTES+count*S64C_SLOT_BYTES);
    assert(be32(published+S64C_OFF_MAGIC)==S64C_MAGIC);
    assert(be32(published+S64C_OFF_VERSION)==1);
    assert(be32(published+S64C_OFF_BYTES)==published_bytes);
    assert(be32(published+S64C_OFF_COUNT)==count);
    assert(be32(published+S64C_OFF_SECTORS)==64);
    assert(be32(published+S64C_OFF_SAVE_BYTES)==32768);
    assert(be32(published+S64C_OFF_ROM_OFFSET)==0x104000);
    assert(be32(published+S64C_OFF_DATA_FIRST)==100);
    assert(be32(published+S64C_OFF_DATA_END)==1000000);
    uint32_t sum=0;
    for(size_t i=0;i<published_bytes;i+=4) sum+=be32(published+i);
    assert(!sum);
    for(unsigned slot=0;slot<count;slot++) {
        const unsigned char *entry=published+S64C_HEADER_BYTES+slot*S64C_SLOT_BYTES;
        assert(be32(entry)==first_id+slot && !be32(entry+4));
        for(unsigned i=0;i<64;i++) assert(be32(entry+8+i*4)==100+(first_id+slot)*200+2*((i*5)%64));
    }
}
static void test_pools(void) {
    diagnostic_pool_backend_t backend={NULL,pool_info,pool_sectors,pool_publish};
    char *path=NULL;
    pool_setup(0);
    assert(!diagnostic_pool_prepare(ordinary,"pool",3,0x104000,114688,&backend,&path));
    assert(!strcmp(path,"Progress-diag-pool-000001.sav"));free(path);
    assert(pool_maps==3 && pool_publishes==1);check_descriptor(3,1);++pool_cases;
    /* Fill an earlier completed capture with unmistakable bytes; the second
     * session must leave it untouched and choose all fresh IDs. */
    create("Progress-diag-pool-000002.sav",32768);
    pool_setup(0);
    assert(!diagnostic_pool_prepare(ordinary,"pool",3,0x104000,114688,&backend,&path));free(path);
    assert(pool_maps==3 && pool_publishes==1);check_descriptor(3,4);
    FILE *old=fopen("Progress-diag-pool-000002.sav","rb");assert(old);
    for(unsigned i=0;i<32768;i++) assert(fgetc(old)==(int)((i*43+7)&255));
    assert(fgetc(old)==EOF);assert(!fclose(old));++pool_cases;
    pool_setup(0);
    assert(!diagnostic_pool_prepare(ordinary,"maxpool",16,0x104000,0x102000,&backend,&path));free(path);
    assert(pool_maps==16 && pool_publishes==1);check_descriptor(16,1);++pool_cases;
    for(unsigned mode=7;mode<=17;mode++) {
        pool_setup(mode);char tag[24];snprintf(tag,sizeof tag,"poolfault%02u",mode);
        assert(diagnostic_pool_prepare(ordinary,tag,3,0x104000,114688,&backend,&path)&&!path);
        assert(pool_publishes==(mode==13?1u:0u));++pool_cases;
    }
    const struct {unsigned count;uint32_t offset;uint64_t size;} invalid[]={
        {0,0x104000,114688},{17,0x104000,114688},{16,0x100000,114688},
        {16,0x104000,0},{16,0x104000,0x102001},{16,0x104000,UINT64_MAX}};
    for(unsigned i=0;i<sizeof invalid/sizeof invalid[0];i++) {
        pool_setup(0);
        assert(diagnostic_pool_prepare(ordinary,"badpool",invalid[i].count,invalid[i].offset,
            invalid[i].size,&backend,&path)&&!path);
        assert(!pool_maps&&!pool_publishes);++pool_cases;
    }
    for(int mode=1;mode<=6;mode++) {
        fail_mode=mode;pool_setup(0);char tag[24];snprintf(tag,sizeof tag,"poolio%02d",mode);
        assert(diagnostic_pool_prepare(ordinary,tag,3,0x104000,114688,&backend,&path)&&!path);
        assert(!pool_maps&&!pool_publishes);++pool_cases;
    }
    fail_mode=0;
    assert(!normal_write_attempts);
    printf("SC64_CONTINUOUS_POOL PASS %u cases: fragmented/disjoint sectors, two sessions, old saves preserved, 16-slot bounds, card/map/publication/I/O failure rejection\n",pool_cases);
}
int main(int argc, char **argv) {
    assert(argc==2);assert(!chdir(argv[1]));
    snprintf(ordinary,sizeof ordinary,"Progress.sav");create(ordinary,32768);
    char *p;assert(!diagnostic_save_reserve(ordinary,"v4abc",&p));
    assert(!strcmp(p,"Progress-diag-v4abc-000001.sav"));check(p,1);free(p);
    assert(!diagnostic_save_reserve(ordinary,"v4abc",&p));
    assert(!strcmp(p,"Progress-diag-v4abc-000002.sav"));check(p,1);free(p);
    FILE *f=fopen(ordinary,"rb");assert(f);
    for(unsigned i=0;i<32768;i++) assert(fgetc(f)==(int)((i*43+7)&255));
    fclose(f);
    assert(!diagnostic_save_reserve("NewGame.sav","v4abc",&p));check(p,0);free(p);
    create("Short.sav",100);assert(diagnostic_save_reserve("Short.sav","v4abc",&p)&&!p);
    for(int mode=1;mode<=6;mode++) { fail_mode=mode;assert(diagnostic_save_reserve(ordinary,"fault",&p)&&!p); }
    fail_mode=0;assert(!diagnostic_save_reserve(ordinary,"fault",&p));
    assert(!strcmp(p,"Progress-diag-fault-000004.sav"));check(p,1);free(p);
    for(const char **t=(const char *[]){"", "../escape", "tab\t", "abcdefghijklmnopqrstuvwxyz",NULL};*t;t++)
        assert(diagnostic_save_reserve(ordinary,*t,&p)&&!p);
    assert(diagnostic_save_reserve("bad.rom","v4",&p)&&!p);
    assert(diagnostic_save_reserve("missing/directory.sav","v4",&p)&&!p);
    assert(normal_write_attempts==0);
    test_pools();
    puts("SC64_DIAGNOSTIC_SAVE PASS repeated single-ROM launches, existing captures/progress preserved, exclusive writes, I/O failure rejection");
}
