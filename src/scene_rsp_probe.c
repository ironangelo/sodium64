/* SPDX-License-Identifier: GPL-3.0-or-later
 * Exclusive volatile cart TX scratch, never SD/ROM/SAV. This is a hypothesis
 * probe for renderer context reconstruction, not a machine-state restore. */
#include "scene_rsp_probe.h"

static uint32_t hash(uint32_t value,uint32_t word) {
    for(unsigned shift=24;;shift-=8) {
        value=(value^((word>>shift)&255))*16777619u;
        if(!shift)return value;
    }
}

uint32_t scene_rsp_probe_execute(uint32_t scratch[128],
    const uint32_t *program,unsigned words,unsigned queue,
    scene_rsp_read read,scene_rsp_write write,
    scene_rsp_transfer transfer,scene_rsp_wait wait) {
    if(!scratch||!program||!words||words>1024||(queue!=0&&queue!=4)||
       !read||!write||!transfer||!wait)return 0;
    const uint32_t status=read(0xa4040010),pc=read(0xa4080000);
    /* Canonical H-COMP HALT precedes its jump to the ordinary resident
     * draw-frame entry. Refuse another stop/IRQ/single-step or branch delay. */
    if((status&0x63)!=1||pc>0xffc||(pc&3)||
       read(0xa4001000+pc)!=0x0900040fu)return 0;
    uint32_t original=2166136261u;
    for(unsigned offset=0;offset<8192;offset+=512) {
        for(unsigned i=0;i<128;i++) {
            scratch[i]=read(0xa4000000+offset+4*i);
            original=hash(original,scratch[i]);
        }
        if(!transfer(scratch,offset,1)||!transfer(scratch,offset,0))return 0;
        for(unsigned i=0;i<128;i++)
            if(scratch[i]!=read(0xa4000000+offset+4*i))return 0;
    }
    /* Validate the complete backup again before the first hardware mutation. */
    uint32_t verified=2166136261u;
    for(unsigned offset=0;offset<8192;offset+=512) {
        if(!transfer(scratch,offset,0))return 0;
        for(unsigned i=0;i<128;i++)verified=hash(verified,scratch[i]);
    }
    if(verified!=original)return 0;
    write(0xa4000000,queue);
    for(unsigned i=0;i<words;i++)write(0xa4001000+4*i,program[i]);
    write(0xa4080000,0);
    write(0xa4040010,5); /* clear HALT/BROKE, leave all other signal bits */
    if(!wait())return 2;
    if((read(0xa4040010)&0x63)!=3)return 2; /* BREAK without IRQ or single-step */
    uint32_t restored=2166136261u;
    for(unsigned offset=0;offset<8192;offset+=512) {
        if(!transfer(scratch,offset,0))return 2;
        for(unsigned i=0;i<128;i++)restored=hash(restored,scratch[i]);
        for(unsigned i=0;i<128;i++)write(0xa4000000+offset+4*i,scratch[i]);
        for(unsigned i=0;i<128;i++)
            if(read(0xa4000000+offset+4*i)!=scratch[i])return 2;
    }
    if(restored!=original)return 2;
    write(0xa4080000,pc);
    write(0xa4040010,6); /* keep HALT, clear probe BROKE */
    if(read(0xa4080000)!=pc||read(0xa4040010)!=status)return 2;
    return 1;
}
