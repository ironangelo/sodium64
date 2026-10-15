/* Host qualification shim; never included in the N64 menu build. */
#ifndef TEST_FF_H
#define TEST_FF_H
#include <stdio.h>
typedef struct { FILE *file; int writing; } FIL;
typedef struct { void *handle; char path[1024]; } DIR;
typedef struct { unsigned char fattrib; char fname[256]; } FILINFO;
typedef unsigned int UINT;
typedef int FRESULT;
enum { FR_OK, FR_NO_FILE, FR_EXIST, FR_DISK_ERR, FR_DENIED };
enum { FA_READ=1, FA_WRITE=2, FA_CREATE_NEW=4 };
enum { AM_DIR=0x10 };
FRESULT f_open(FIL *, const char *, unsigned);
FRESULT f_read(FIL *, void *, UINT, UINT *);
FRESULT f_write(FIL *, const void *, UINT, UINT *);
FRESULT f_sync(FIL *);
FRESULT f_close(FIL *);
FRESULT f_opendir(DIR *, const char *);
FRESULT f_readdir(DIR *, FILINFO *);
FRESULT f_closedir(DIR *);
#endif
