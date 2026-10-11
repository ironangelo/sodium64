#ifndef USB_REMOTE_TEST_USB_H
#define USB_REMOTE_TEST_USB_H
#define DATATYPE_TEXT 1
#define USBHEADER_GETTYPE(h) (((h) >> 24) & 0xff)
#define USBHEADER_GETSIZE(h) ((h) & 0xffffff)
unsigned long usb_poll(void);
void usb_read(void *buffer, int size);
void usb_purge(void);
char usb_write(int type, const void *data, int size);
#endif
