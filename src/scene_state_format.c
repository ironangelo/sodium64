/* SPDX-License-Identifier: GPL-3.0-or-later
 * Fixed owner IDs/sizes come from the current build, never from file addresses.
 * This integrity layer is not linked into gameplay until slot owners are closed. */
#include "scene_state_format.h"

static uint32_t crc(uint32_t value,const unsigned char *data,unsigned bytes) {
    for(unsigned i=0;i<bytes;i++) {
        value^=data[i];
        for(unsigned bit=0;bit<8;bit++)value=(value>>1)^(0xedb88320u&((uint32_t)0-(value&1)));
    }
    return value;
}
uint32_t scene_state_crc32(const unsigned char *data,unsigned bytes) {
    return ~crc(0xffffffffu,data,bytes);
}
static uint32_t word(const unsigned char *p) {
    return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];
}
static void put(unsigned char *p,uint32_t value) {
    for(unsigned i=0;i<4;i++)p[i]=(unsigned char)(value>>(24-8*i));
}
static int extent(const scene_state_owner *owners,unsigned count,uint32_t *payload) {
    if(!owners||!count||count>SCENE_STATE_OWNER_LIMIT)return 0;
    uint32_t sum=0,overhead=64+12*count;
    for(unsigned i=0;i<count;i++) {
        if(!owners[i].id||!owners[i].bytes||owners[i].bytes>SCENE_STATE_MAX_BYTES-overhead-sum)return 0;
        for(unsigned j=0;j<i;j++)if(owners[i].id==owners[j].id)return 0;
        sum+=owners[i].bytes;
    }
    *payload=sum;return 1;
}
int scene_state_header(unsigned char output[64],const scene_state_binding *binding,
    const scene_state_owner *owners,unsigned count,scene_state_progress progress,
    uint32_t body_crc) {
    uint32_t payload;
    if(!output||!binding||progress.guest!=progress.render||!extent(owners,count,&payload))return 0;
    uint32_t values[16]={SCENE_STATE_MAGIC,SCENE_STATE_VERSION,64,count,payload,
        binding->rom_crc,binding->code_crc,binding->layout_crc,binding->config_crc,
        progress.guest,progress.render,body_crc,0,0,0,0};
    for(unsigned i=0;i<16;i++)put(output+4*i,values[i]);
    put(output+48,scene_state_crc32(output,64));return 1;
}
int scene_state_validate(scene_state_read read,unsigned char scratch[512],
    uint32_t available,const scene_state_binding *binding,
    const scene_state_owner *owners,unsigned count,scene_state_progress *progress) {
    uint32_t payload;
    if(!read||!scratch||!binding||!progress||!extent(owners,count,&payload)||
       available!=64+12*count+payload)return 0;
    if(!read(0,64,scratch))return -1;
    if(word(scratch)!=SCENE_STATE_MAGIC||word(scratch+4)!=SCENE_STATE_VERSION||
       word(scratch+8)!=64||word(scratch+12)!=count||word(scratch+16)!=payload||
       word(scratch+20)!=binding->rom_crc||word(scratch+24)!=binding->code_crc||
       word(scratch+28)!=binding->layout_crc||word(scratch+32)!=binding->config_crc||
       word(scratch+36)!=word(scratch+40)||word(scratch+52)||word(scratch+56)||word(scratch+60))return 0;
    scene_state_progress accepted={word(scratch+36),word(scratch+40)};
    uint32_t expected=word(scratch+44),header_crc=word(scratch+48);
    put(scratch+48,0);
    if(scene_state_crc32(scratch,64)!=header_crc)return 0;
    uint32_t value=0xffffffffu,offset=0;
    for(unsigned i=0;i<count;i++) {
        if(!read(64+12*i,12,scratch))return -1;
        if(word(scratch)!=owners[i].id||word(scratch+4)!=owners[i].bytes||word(scratch+8)!=offset)return 0;
        value=crc(value,scratch,12);offset+=owners[i].bytes;
    }
    uint32_t start=64+12*count;
    for(unsigned done=0;done<payload;) {
        unsigned bytes=payload-done;if(bytes>512)bytes=512;
        if(!read(start+done,bytes,scratch))return -1;
        value=crc(value,scratch,bytes);done+=bytes;
    }
    if(~value!=expected)return 0;
    *progress=accepted;return 1;
}
