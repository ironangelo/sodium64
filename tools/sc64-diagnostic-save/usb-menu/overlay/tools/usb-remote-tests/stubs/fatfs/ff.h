#ifndef USB_REMOTE_TEST_FATFS_H
#define USB_REMOTE_TEST_FATFS_H
typedef char TCHAR;
typedef enum { FR_OK = 0, FR_DISK_ERR = 1 } FRESULT;
FRESULT f_rename(const TCHAR *source, const TCHAR *destination);
#endif
