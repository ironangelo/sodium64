/* SPDX-License-Identifier: GPL-3.0-or-later
 * One exclusive private volatile slot, supplied by board code. Transport,
 * stacks and host clocks are not owners. No external state import. */
#include "scene_slot.h"
static scene_slot_work *active;
static scene_slot_block active_block;
static void put(unsigned char *p,uint32_t v) {
    for(unsigned i=0;i<4;i++)p[i]=(unsigned char)(v>>(24-8*i));
}
static int read(uint32_t offset,unsigned bytes,unsigned char *output) {
    if(!active||offset>active->bytes||bytes>active->bytes-offset)return 0;
    while(bytes) {
        uint32_t base=offset&~511u;unsigned skip=offset&511u,n=512-skip;
        if(n>bytes)n=bytes;
        if(!active_block(base,active->block,0))return 0;
        /* Validator passes piece, never the IO block itself. */
        for(unsigned i=0;i<n;i++)output[i]=active->block[skip+i];
        output+=n;offset+=n;bytes-=n;
    }
    return 1;
}
static int write_piece(scene_slot_work *w,scene_slot_block block,
                       uint32_t *at,const unsigned char *source,unsigned bytes) {
    while(bytes) {
        unsigned skip=*at&511u,n=512-skip;if(n>bytes)n=bytes;
        for(unsigned i=0;i<n;i++)w->block[skip+i]=source[i];
        *at+=n;source+=n;bytes-=n;
        if(!(*at&511u)&&!block(*at-512,w->block,1))return 0;
    }
    return 1;
}
int scene_slot_store(scene_slot_work *w,scene_slot_block block,
    scene_slot_owner_io io,const scene_state_binding *binding,
    const scene_state_owner *owners,unsigned count,scene_state_progress progress) {
    if(!w||!block||!io)return 0;
    w->bytes=0;w->stage=1;
    if(!scene_state_header(w->piece,binding,owners,count,progress,0))return 0;
    uint32_t length=64+12*count,payload=0,at=0,crc=0xffffffffu;
    for(unsigned i=0;i<count;i++)length+=owners[i].bytes;
    /* Header invalid until complete payload write and body checksum. */
    for(unsigned i=0;i<64;i++)w->piece[i]=0;
    if(!write_piece(w,block,&at,w->piece,64))return 0;
    for(unsigned i=0;i<count;i++) {
        put(w->piece,owners[i].id);put(w->piece+4,owners[i].bytes);put(w->piece+8,payload);
        crc=scene_state_crc32_update(crc,w->piece,12);payload+=owners[i].bytes;
        if(!write_piece(w,block,&at,w->piece,12))return 0;
    }
    w->stage=2;
    for(unsigned i=0;i<count;i++)for(uint32_t done=0;done<owners[i].bytes;) {
        unsigned n=owners[i].bytes-done;if(n>512)n=512;
        if(!io(i,done,n,w->piece,0))return 0;
        crc=scene_state_crc32_update(crc,w->piece,n);
        if(!write_piece(w,block,&at,w->piece,n))return 0;
        done+=n;
    }
    if(at!=length)return 0;
    if(at&511u) {
        for(unsigned i=at&511u;i<512;i++)w->block[i]=0;
        if(!block(at&~511u,w->block,1))return 0;
    }
    w->stage=3;
    if(!scene_state_header(w->piece,binding,owners,count,progress,~crc)||!block(0,w->block,0))return 0;
    for(unsigned i=0;i<64;i++)w->block[i]=w->piece[i];
    if(!block(0,w->block,1))return 0;
    w->bytes=length;active=w;active_block=block;
    scene_state_progress accepted;
    if(scene_state_validate(read,w->piece,length,binding,owners,count,&accepted)!=1) {w->bytes=0;return 0;}
    w->stage=4;return 1;
}
int scene_slot_load(scene_slot_work *w,scene_slot_block block,
    scene_slot_owner_io io,const scene_state_binding *binding,
    const scene_state_owner *owners,unsigned count,scene_state_progress *progress) {
    if(!w||!block||!io||!progress)return 0;
    w->stage=11;active=w;active_block=block;scene_state_progress accepted;
    if(scene_state_validate(read,w->piece,w->bytes,binding,owners,count,&accepted)!=1)return 0;
    uint32_t at=64+12*count;w->stage=12;
    for(unsigned i=0;i<count;i++)for(uint32_t done=0;done<owners[i].bytes;) {
        unsigned n=owners[i].bytes-done;if(n>512)n=512;
        if(!read(at,n,w->piece)||!io(i,done,n,w->piece,1))return 2;
        /* Compare the actual destination against the immutable slot again;
         * a staging-buffer hash cannot demonstrate a successful RAM write. */
        if(!io(i,done,n,w->piece,0))return 2;
        for(unsigned j=0;j<n;j++) {
            uint32_t offset=at+j;
            if((!j||!(offset&511u))&&!block(offset&~511u,w->block,0))return 2;
            if(w->piece[j]!=w->block[offset&511u])return 2;
        }
        done+=n;at+=n;
    }
    *progress=accepted;w->stage=13;return 1;
}
