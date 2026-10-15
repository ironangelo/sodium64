/* SPDX-License-Identifier: GPL-3.0-or-later
 * Diagnostic-only drain at the natural RSP HALT boundary. The renderer emits
 * no SyncFull, so HALT and command-DMA completion do not retire its pixels.
 * Both RSP banks set START and END for every submission, never read CURRENT.
 * The 8-byte command is in the admitted, uncached USB lease, not renderer DMEM.
 * READ/WRITE/COUNT/FENCE are MMIO on target and a sequenced device model in CI.
 */
#ifndef REMOTE_RDP_BARRIER_H
#define REMOTE_RDP_BARRIER_H
static int wait_io(uint32_t address,uint32_t mask,uint32_t wanted,uint32_t ticks) {
    uint32_t start=RDP_COUNT();
    while((RDP_READ(address)&mask)!=wanted) {
        if((uint32_t)(RDP_COUNT()-start)>=ticks)return 0;
    }
    return 1;
}

/* 0: rejected before submission; -1: submitted but not retired, fail closed.
 * In the latter case the caller forbids resuming the guest. Never change XBUS
 * back while a timed-out command could still be fetching from RDRAM.
 */
static int remote_rdp_drain(uint32_t ticks) {
    uint32_t state=RDP_READ(0xa410000c),pending=RDP_READ(0xa4300008)&0x20;
    if(!(RDP_READ(0xa4040010)&1)||(RDP_READ(0xa4040018)&1)||
       (state&6)||(RDP_READ(0xa430000c)&0x20))return 0;
    if(!wait_io(0xa410000c,0x740,0,ticks))return 0;
    if(!(RDP_READ(0xa410000c)&0x170))return 1;
    RDP_WRITE(0xa0441ca0,0x29000000);RDP_WRITE(0xa0441ca4,0);
    RDP_FENCE();
    RDP_WRITE(0xa410000c,1); /* clear XBUS: fetch only our SyncFull from RDRAM */
    RDP_WRITE(0xa4100000,0x00441ca0);RDP_WRITE(0xa4100004,0x00441ca8);
    if(!wait_io(0xa4100008,0x00ffffff,0x00441ca8,ticks)||
       !wait_io(0xa410000c,0x770,0,ticks)||
       (!pending&&!wait_io(0xa4300008,0x20,0x20,ticks)))return -1;
    RDP_WRITE(0xa410000c,(state&1)?2:1);
    if(!pending)RDP_WRITE(0xa4300000,0x800); /* preserve any previous DP IRQ */
    RDP_FENCE();
    return 1;
}
#endif
