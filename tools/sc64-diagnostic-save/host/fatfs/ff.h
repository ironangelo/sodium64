/* Host qualification shim; never included in the N64 menu build. */
#ifndef TEST_FF_H
#define TEST_FF_H
#include <stdio.h>
typedef struct { FILE *file; int writing; } FIL;
typedef unsigned int UINT;
typedef int FRESULT;
enum { FR_OK, FR_NO_FILE, FR_EXIST, FR_DISK_ERR, FR_DENIED };
enum { FA_READ=1, FA_WRITE=2, FA_CREATE_NEW=4 };
FRESULT f_open(FIL *, const char *, unsigned);
FRESULT f_read(FIL *, void *, UINT, UINT *);
FRESULT f_write(FIL *, const void *, UINT, UINT *);
FRESULT f_sync(FIL *);
FRESULT f_close(FIL *);
#endif
