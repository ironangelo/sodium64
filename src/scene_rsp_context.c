/* SPDX-License-Identifier: GPL-3.0-or-later
 * Pause-only full RSP context roundtrip in exclusive volatile TX scratch.
 * Guest/SD/SAV/DP/AI state is untouched; no persistent machine slot here. */
#include "scene_rsp_context.h"
#define SP_MEM 0xa4000000u
#define SP_PC 0xa4080000u
#define SP_STATUS 0xa4040010u
#define CONTEXT_SLOT 8192u
#define CONTEXT_WORDS (SCENE_RSP_CONTEXT_BYTES/4)

static uint32_t hash(uint32_t value,uint32_t word) {
    for(unsigned shift=24;;shift-=8) {
        value=(value^((word>>shift)&255))*16777619u;
        if(!shift)return value;
    }
}
static int run(const uint32_t *program,unsigned words,scene_rsp_write write,
               scene_rsp_read read,scene_rsp_wait wait) {
    for(unsigned i=0;i<words;i++)write(SP_MEM+4096+4*i,program[i]);
    write(SP_PC,0);write(SP_STATUS,5);
    return wait()&&(read(SP_STATUS)&0x63)==3;
}
static int verify(uint32_t *scratch,uint32_t cart,unsigned words,uint32_t expected,
                  scene_rsp_transfer transfer) {
    uint32_t value=2166136261u;
    for(unsigned start=0;start<words;start+=128) {
        if(!transfer(scratch,cart+4*start,0))return 0;
        unsigned n=words-start;if(n>128)n=128;
        for(unsigned i=0;i<n;i++)value=hash(value,scratch[i]);
    }
    return value==expected;
}
static void prepare(scene_rsp_read read,scene_rsp_write write) {
    for(unsigned i=0;i<4;i++) {
        uint32_t h=read(SP_MEM+SCENE_RSP_ACC_HI+4*i);
        uint32_t m=read(SP_MEM+SCENE_RSP_ACC_MID+4*i),n=0;
        for(unsigned shift=0;shift<=16;shift+=16) {
            uint32_t hi=(h>>shift)&65535,mid=(m>>shift)&65535;
            n|=((0u-hi-(mid>>15))&65535)<<shift;
        }
        write(SP_MEM+SCENE_RSP_NEG_HI+4*i,n);
        write(SP_MEM+SCENE_RSP_ONE+4*i,0x00010001);
        write(SP_MEM+SCENE_RSP_NEG_HALF+4*i,0x80008000);
    }
}
uint32_t scene_rsp_context_roundtrip(uint32_t scratch[128],
    const uint32_t *capture,unsigned capture_words,
    const uint32_t *restore,unsigned restore_words,
    scene_rsp_read read,scene_rsp_write write,scene_rsp_transfer transfer,
    scene_rsp_wait wait) {
    if(!scratch||!capture||!capture_words||capture_words>1024||!restore||
       !restore_words||restore_words>1024||!read||!write||!transfer||!wait)return 0;
    uint32_t status=read(SP_STATUS),pc=read(SP_PC);
    if((status&0x63)!=1||(pc!=0x3c4&&pc!=0x3c8)||
       read(SP_MEM+0x13bc)!=0x24080002||
       read(SP_MEM+0x13c0)!=0x40882000||read(SP_MEM+0x13c4)!=0x0900040f||
       read(SP_MEM+0x13c8)!=0||read(0xa4040018)||read(0xa4040014))return 0;
    uint32_t original=2166136261u;
    for(unsigned start=0;start<2048;start+=128) {
        for(unsigned i=0;i<128;i++) {
            scratch[i]=read(SP_MEM+4*(start+i));original=hash(original,scratch[i]);
        }
        if(!transfer(scratch,4*start,1)||!transfer(scratch,4*start,0))return 0;
        for(unsigned i=0;i<128;i++)if(scratch[i]!=read(SP_MEM+4*(start+i)))return 0;
    }
    if(!verify(scratch,0,2048,original,transfer))return 0;
    /* First mutation is after a fully checked SP backup. Capture leaves all
     * registers/flags/ACC intact, and the following slot readback proves it. */
    /* Sentinels independently prove the early stores ran after clearing the
     * stopped pipeline. The matched HALT prologue guarantees original t0=2. */
    write(SP_MEM,0xffffffffu);write(SP_MEM+32,0xffffffffu);
    if(!run(capture,capture_words,write,read,wait))return 2;
    if(read(SP_MEM)!=0||read(SP_MEM+32)!=2)return 2;
    uint32_t context=2166136261u;
    for(unsigned start=0;start<CONTEXT_WORDS;start+=128) {
        unsigned n=CONTEXT_WORDS-start;if(n>128)n=128;
        for(unsigned i=0;i<128;i++) {
            scratch[i]=i<n?read(SP_MEM+4*(start+i)):0;
            if(i<n)context=hash(context,scratch[i]);
        }
        if(!transfer(scratch,CONTEXT_SLOT+4*start,1)||!transfer(scratch,CONTEXT_SLOT+4*start,0))return 2;
        for(unsigned i=0;i<n;i++)if(scratch[i]!=read(SP_MEM+4*(start+i)))return 2;
    }
    if(!verify(scratch,CONTEXT_SLOT,CONTEXT_WORDS,context,transfer))return 2;
    /* Force a different register context, then capture and check every field
     * is zero. This is an actual restore test, not an unchanged-state copy. */
    for(unsigned i=0;i<CONTEXT_WORDS;i++)write(SP_MEM+4*i,0);
    prepare(read,write);
    if(!run(restore,restore_words,write,read,wait)||!run(capture,capture_words,write,read,wait))return 2;
    for(unsigned i=0;i<CONTEXT_WORDS;i++)if(read(SP_MEM+4*i))return 2;
    if(!verify(scratch,CONTEXT_SLOT,CONTEXT_WORDS,context,transfer))return 2;
    for(unsigned start=0;start<CONTEXT_WORDS;start+=128) {
        if(!transfer(scratch,CONTEXT_SLOT+4*start,0))return 2;
        unsigned n=CONTEXT_WORDS-start;if(n>128)n=128;
        for(unsigned i=0;i<n;i++)write(SP_MEM+4*(start+i),scratch[i]);
        for(unsigned i=0;i<n;i++)if(read(SP_MEM+4*(start+i))!=scratch[i])return 2;
    }
    prepare(read,write);
    if(!run(restore,restore_words,write,read,wait)||!run(capture,capture_words,write,read,wait))return 2;
    for(unsigned start=0;start<CONTEXT_WORDS;start+=128) {
        if(!transfer(scratch,CONTEXT_SLOT+4*start,0))return 2;
        unsigned n=CONTEXT_WORDS-start;if(n>128)n=128;
        for(unsigned i=0;i<n;i++)if(read(SP_MEM+4*(start+i))!=scratch[i])return 2;
    }
    if(!verify(scratch,0,2048,original,transfer))return 2;
    uint32_t restored=2166136261u;
    for(unsigned start=0;start<2048;start+=128) {
        if(!transfer(scratch,4*start,0))return 2;
        for(unsigned i=0;i<128;i++) {
            restored=hash(restored,scratch[i]);write(SP_MEM+4*(start+i),scratch[i]);
        }
        for(unsigned i=0;i<128;i++)if(read(SP_MEM+4*(start+i))!=scratch[i])return 2;
    }
    if(restored!=original)return 2;
    write(SP_PC,0x3c);write(SP_STATUS,6);
    return read(SP_PC)==0x3c&&read(SP_STATUS)==status?1u:2u;
}
