/* Original synthetic hardware/transport model for the production transaction. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../src/scene_rsp_probe.h"
static uint32_t sp[2048],gold[2048],cart[2048],scratch[128];
static uint32_t status,pc,program[]={0x12345678,0x87654321};
static unsigned calls,writes,cases,fail_call,corrupt_call,word_fault,wait_fault,pc_fault;
static uint32_t read_word(uint32_t address) {
    if(address==0xa4040010)return status;
    if(address==0xa4080000)return pc;
    if(address<0xa4000000||address>=0xa4002000||(address&3))abort();
    return sp[(address-0xa4000000)/4];
}
static void write_word(uint32_t address,uint32_t value) {
    writes++;
    if(address==0xa4040010) {
        if(value==5)status&=~3u;
        else if(value==6)status=(status|1)&~2u;
        else abort();
        return;
    }
    if(address==0xa4080000){pc=pc_fault&&value==0x3c0?value+4:value;return;}
    if(address<0xa4000000||address>=0xa4002000||(address&3))abort();
    if(word_fault&&calls>48&&address==0xa4000020)value^=1;
    sp[(address-0xa4000000)/4]=value;
}
static int transfer(uint32_t *buffer,uint32_t offset,int write) {
    if(buffer!=scratch||offset>8192-512||(offset&511))abort();
    calls++;
    if(calls==fail_call)return 0;
    if(write)memcpy(cart+offset/4,buffer,512);
    else memcpy(buffer,cart+offset/4,512);
    if(calls==corrupt_call)buffer[31]^=1;
    return 1;
}
static int wait_halt(void) {
    if(wait_fault)return 0;
    if(pc||sp[0]>4||sp[1024]!=program[0]||sp[1025]!=program[1])abort();
    status|=3;return 1;
}
static void reset(void) {
    for(unsigned i=0;i<2048;i++)sp[i]=i*971u+123u;
    sp[1024+0x3c0/4]=0x0900040f;
    memcpy(gold,sp,sizeof(sp));memset(cart,0,sizeof(cart));
    status=0x101;pc=0x3c0;calls=writes=0;
    fail_call=corrupt_call=word_fault=wait_fault=pc_fault=0;
}
static unsigned run(unsigned queue) {
    return scene_rsp_probe_execute(scratch,program,2,queue,read_word,write_word,transfer,wait_halt);
}
static void check(int ok) {cases++;if(!ok){fprintf(stderr,"scene transaction failure case=%u calls=%u writes=%u\n",cases,calls,writes);exit(1);}}
int main(void) {
    for(unsigned q=0;q<=4;q+=4) {
        reset();check(run(q)==1&&calls==64&&pc==0x3c0&&status==0x101&&!memcmp(sp,gold,sizeof(sp)));
    }
    for(unsigned f=1;f<=64;f++) {
        reset();fail_call=f;unsigned result=run(0);
        check(result==(f<=48?0u:2u));
        if(f<=48)check(!writes&&!memcmp(sp,gold,sizeof(sp)));
    }
    for(unsigned c=2;c<=64;c+=2) {
        reset();corrupt_call=c;unsigned result=run(4);
        check(result==(c<=48?0u:2u));
        if(c<=48)check(!writes&&!memcmp(sp,gold,sizeof(sp)));
    }
    reset();wait_fault=1;check(run(0)==2);
    reset();word_fault=1;check(run(0)==2);
    reset();pc_fault=1;check(run(0)==2);
    for(unsigned bad=2;bad<7;bad++) {
        reset();if(bad==4)continue;
        check(run(bad)==0&&!calls&&!writes);
    }
    for(unsigned bit=1;bit<=0x40;bit<<=1) {
        if(bit==4||bit==8||bit==16)continue;
        reset();status^=bit;check(run(0)==0&&!calls&&!writes);
    }
    reset();sp[1024+pc/4]^=1;check(run(0)==0&&!calls&&!writes);
    reset();pc=4096;check(run(0)==0&&!calls&&!writes);
    reset();pc=0x3c1;check(run(0)==0&&!calls&&!writes);
    reset();check(scene_rsp_probe_execute(scratch,program,1025,0,read_word,write_word,transfer,wait_halt)==0&&!writes);
    printf("SCENE_RSP_TRANSACTION PASS cases=%u backup_blocks=16 fault_transfer_positions=64\n",cases);
}
