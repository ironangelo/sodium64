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

static int fail_mode;
static char ordinary[1024];
static unsigned normal_write_attempts;
FRESULT f_open(FIL *f, const char *path, unsigned flags) {
    f->writing = flags & FA_WRITE;
    if (f->writing && !strcmp(path, ordinary)) normal_write_attempts++;
    if ((fail_mode == 1 && !f->writing) || (fail_mode == 2 && f->writing)) return FR_DENIED;
    int fd = open(path, f->writing ? O_WRONLY | O_CREAT | O_EXCL : O_RDONLY, 0600);
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
    puts("SC64_DIAGNOSTIC_SAVE PASS repeated single-ROM launches, existing captures/progress preserved, exclusive writes, I/O failure rejection");
}
