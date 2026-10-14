/* SPDX-License-Identifier: GPL-3.0-or-later
 * Pause-only full RSP context roundtrip in exclusive volatile TX scratch.
 * Guest/SD/SAV/DP/AI state is untouched; no persistent machine slot here. */
#include "scene_rsp_context.h"
#define SP_MEM 0xa4000000u
#define SP_PC 0xa4080000u
#define SP_STATUS 0xa4040010u
#define CONTEXT_SLOT 8192u
#define CONTEXT_WORDS (SCENE_RSP_CONTEXT_BYTES/4)
volatile uint32_t scene_rsp_context_stage;
volatile uint32_t scene_rsp_context_mismatch_word;

#ifdef SODIUM64_DSP_RSP_GAUSS_PROBE
extern const uint32_t rsp_dsp_gauss_text_start[],rsp_dsp_gauss_text_end[];
volatile uint32_t scene_rsp_gauss_metrics[8];
#ifdef SODIUM64_DSP_RSP_GAUSS_DMA
volatile uint32_t scene_rsp_gauss_dma;
volatile uint32_t scene_rsp_gauss_dma_diag[3];
static uint32_t dma_source(uint32_t *packet) {
#ifdef SODIUM64_RSP_GAUSS_HOST
    extern uint32_t scene_rsp_gauss_host_dma_source(uint32_t *);
    return scene_rsp_gauss_host_dma_source(packet);
#else
    uintptr_t address=(uintptr_t)packet;
    if((address&15)||((uint32_t)address&0xe0000000u)!=0x80000000u||
       (address&0x1fffffffu)>0x7fff80u)return 0;
    /* Same hit-writeback operation as the existing renderer/profile owners.
     * Exactly eight private aligned lines, no adjacent stack data. */
    for(unsigned i=0;i<128;i+=16)
        __asm__ volatile("cache 0x19,0(%0)"::"r"((unsigned char *)packet+i):"memory");
    __asm__ volatile("sync":::"memory");
    return (uint32_t)address&0x1fffffffu;
#endif
}
#endif
static uint32_t ticks(void) {
#ifdef SODIUM64_RSP_GAUSS_HOST
    extern uint32_t scene_rsp_gauss_host_ticks(void);
    return scene_rsp_gauss_host_ticks();
#else
    uint32_t value;__asm__ volatile("mfc0 %0,$9":"=r"(value)::"memory");return value;
#endif
}
#ifdef SODIUM64_DSP_RSP_GAUSS_DMA
static uint32_t dma_tail_address(uint32_t cursor) {
    return (cursor&0x1000u)|((cursor-8)&0xfffu);
}
static int dma_cursor_restore(const uint32_t original[4],const uint32_t tail[2],
                              scene_rsp_read read,scene_rsp_write write) {
    uint32_t target=dma_tail_address(original[0]),source=original[1]-8;
    /* Address writes only change pending DMA. Replay exactly eight identical
     * source bytes to advance current back to both captured end cursors.
     * RDRAM is read-only. All renderer DMA sites rebind addresses and length. */
    for(unsigned i=0;i<2;i++)if(read(0xa0000000u+source+4*i)!=tail[i])return 0;
    if(read(0xa4040018u)||read(0xa4040014u))return 0;
    write(0xa4040000u,target);write(0xa4040004u,source);
    write(0xa4040008u,7|(original[2]&0xfff00000u));
    uint32_t start=ticks();
    while(read(0xa4040018u)||read(0xa4040014u))
        if((uint32_t)(ticks()-start)>=46875000u/5u)return 0;
    for(unsigned i=0;i<2;i++)if(read(SP_MEM+target+4*i)!=tail[i])return 0;
    /* Rebind the pending addresses too. They cannot be read independently;
     * resumed renderer helpers always overwrite both before their length. */
    write(0xa4040000u,original[0]);write(0xa4040004u,original[1]);
    return 1;
}
#endif
static int gauss_probe(scene_rsp_read read,
                       scene_rsp_write write,scene_rsp_wait wait) {
    /* Cached private CPU stack, not the uncached PI transfer-buffer alias:
     * otherwise scalar timing would unfairly include uncached sample loads. */
    uint32_t scratch[44] __attribute__((aligned(16)));
    static const uint16_t coef[4][4]={
        {370,1305,374,0},{168,1210,659,11},
        {56,965,969,58},{0,374,1305,370}};
    for(unsigned i=0;i<8;i++)scene_rsp_gauss_metrics[i]=0;
    scene_rsp_gauss_metrics[2]=0xffffffffu;
    if(rsp_dsp_gauss_text_end-rsp_dsp_gauss_text_start!=20)return 0;
    uint32_t start=ticks();
    for(unsigned i=0;i<20;i++)write(SP_MEM+4096+4*i,rsp_dsp_gauss_text_start[i]);
    for(unsigned i=0;i<4;i++)write(SP_MEM+128+4*i,0xfffefffeu);
    scene_rsp_gauss_metrics[7]=ticks()-start;
    for(unsigned i=0;i<20;i++)if(read(SP_MEM+4096+4*i)!=rsp_dsp_gauss_text_start[i])return 0;
    uint32_t checksum=2166136261u;
    for(unsigned n=0;n<64;n++) {
        /* Preparation is outside both timings. Four pinned fractions per
         * packet, all lanes independent, signed samples spanning full16. */
        for(unsigned lane=0;lane<8;lane++)for(unsigned tap=0;tap<4;tap++) {
            uint32_t sample=(n*15583+lane*29519+tap*32749+0x8000)&65535;
            uint32_t coefficient=(uint32_t)coef[(n+lane)&3][tap]<<5;
            unsigned i=tap*8+lane/2;
            if(!(lane&1)){scratch[i]=sample<<16;scratch[i+4]=coefficient<<16;}
            else {scratch[i]|=sample;scratch[i+4]|=coefficient;}
        }
        start=ticks();
        for(unsigned lane=0;lane<8;lane++) {
            int sum=0;unsigned shift=(lane&1)?0:16;
            for(unsigned tap=0;tap<4;tap++) {
                unsigned i=tap*8+lane/2;
                int sample=(int16_t)(scratch[i]>>shift);
                unsigned coefficient=((scratch[i+4]>>shift)&65535)>>5;
                sum+=(sample*(int)coefficient)>>11;
                if(tap==2)sum=(int16_t)sum;
            }
            if(sum>32767)sum=32767;
            if(sum< -32768)sum= -32768;
            uint32_t expected=(uint32_t)sum&65534;
            if(!(lane&1))scratch[36+lane/2]=expected<<16;
            else scratch[36+lane/2]|=expected;
        }
        scene_rsp_gauss_metrics[3]+=ticks()-start;
        for(unsigned i=0;i<4;i++)write(SP_MEM+144+4*i,~scratch[36+i]);
        start=ticks();
#ifdef SODIUM64_DSP_RSP_GAUSS_DMA
        if(scene_rsp_gauss_dma) {
            uint32_t physical=dma_source(scratch);
            if(!physical) {
                scene_rsp_gauss_dma_diag[0]=4;
                scene_rsp_gauss_dma_diag[1]=0x80000000u;
                scene_rsp_gauss_dma_diag[2]=(uint32_t)(uintptr_t)scratch;return 0;
            }
            write(0xa4040000u,0);write(0xa4040004u,physical);
            write(0xa4040008u,127); /* one128-byte DRAM->DMEM input, no IMEM */
            while(read(0xa4040018u)||read(0xa4040014u))
                if((uint32_t)(ticks()-start)>=46875000u/5u) {
                    scene_rsp_gauss_dma_diag[0]=1;
                    scene_rsp_gauss_dma_diag[2]=(read(0xa4040018u)<<16)|read(0xa4040014u);
                    return -1;
                }
        } else
#endif
        for(unsigned i=0;i<32;i++)write(SP_MEM+4*i,scratch[i]);
        write(SP_PC,0);write(SP_STATUS,5);
        if(!wait()||(read(SP_STATUS)&0x63)!=3) {
            /* This fixed kernel has no DMA/RCP instructions. Stop it before
             * reloading the original owner; a failed HALT requires menu. */
            write(SP_STATUS,2);
            if(read(SP_STATUS)&1)return 0;
#ifdef SODIUM64_DSP_RSP_GAUSS_DMA
            scene_rsp_gauss_dma_diag[0]=2;scene_rsp_gauss_dma_diag[1]=1;
            scene_rsp_gauss_dma_diag[2]=read(SP_STATUS);
#endif
            return -1;
        }
        for(unsigned i=0;i<4;i++)scratch[40+i]=read(SP_MEM+144+4*i);
        uint32_t elapsed=ticks()-start;
        scene_rsp_gauss_metrics[4]+=elapsed;
        if(elapsed>scene_rsp_gauss_metrics[5])scene_rsp_gauss_metrics[5]=elapsed;
        for(unsigned i=0;i<4;i++) {
            if(scratch[40+i]!=scratch[36+i]) {
                scene_rsp_gauss_metrics[2]=n*8+i*2;return 0;
            }
            checksum=(checksum^scratch[40+i])*16777619u;
        }
        scene_rsp_gauss_metrics[1]+=8;
    }
    scene_rsp_gauss_metrics[6]=checksum;scene_rsp_gauss_metrics[0]=1;return 1;
}
#endif

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
    scene_rsp_context_stage=1;
    scene_rsp_context_mismatch_word=0xffffffffu;
#ifdef SODIUM64_DSP_RSP_GAUSS_DMA
    for(unsigned i=0;i<3;i++)scene_rsp_gauss_dma_diag[i]=0;
#endif
    if(!scratch||!capture||!capture_words||capture_words>1024||!restore||
       !restore_words||restore_words>1024||!read||!write||!transfer||!wait)return 0;
    uint32_t status=read(SP_STATUS),pc=read(SP_PC);
    if((status&0x63)!=1||(pc!=0x3c4&&pc!=0x3c8)||
       read(SP_MEM+0x13bc)!=0x24080002||
       read(SP_MEM+0x13c0)!=0x40882000||read(SP_MEM+0x13c4)!=0x0900040f||
       read(SP_MEM+0x13c8)!=0||read(0xa4040018)||read(0xa4040014))return 0;
#ifdef SODIUM64_DSP_RSP_GAUSS_DMA
    uint32_t dma_original[4]={0,0,0,0},dma_tail[2]={0,0};
    if(scene_rsp_gauss_dma) {
        for(unsigned i=0;i<4;i++)dma_original[i]=read(0xa4040000u+4*i);
        /* Idle current count/length, same shared descriptor in both readbacks,
         * aligned source and complete8-byte RDRAM/SP tail bounds. No mutation. */
        if(dma_original[0]>0x1fffu||(dma_original[0]&7)||
           dma_original[1]<8||dma_original[1]>0x800000u||(dma_original[1]&7)||
           (dma_original[2]&0xfffffu)!=0xff8u||dma_original[2]!=dma_original[3])return 0;
        for(unsigned i=0;i<2;i++) {
            dma_tail[i]=read(SP_MEM+dma_tail_address(dma_original[0])+4*i);
            if(dma_tail[i]!=read(0xa0000000u+dma_original[1]-8+4*i))return 0;
        }
    }
#endif
    uint32_t original=2166136261u;
    scene_rsp_context_stage=2;
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
    scene_rsp_context_stage=3;
    if(!run(capture,capture_words,write,read,wait))return 2;
    scene_rsp_context_stage=4;
    if(read(SP_MEM)!=0){scene_rsp_context_mismatch_word=0;return 2;}
    if(read(SP_MEM+32)!=2){scene_rsp_context_mismatch_word=8;return 2;}
    uint32_t context=2166136261u;
    scene_rsp_context_stage=5;
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
#ifdef SODIUM64_DSP_RSP_GAUSS_PROBE
    /* The primitive deliberately changes vectors/ACC/flags. The original
     * architectural context and all8KiB still follow the same restore gate. */
    scene_rsp_context_stage=6;
    if(gauss_probe(read,write,wait)<0)return 2;
#ifdef SODIUM64_DSP_RSP_GAUSS_DMA
    if(scene_rsp_gauss_dma) {
        if(!dma_cursor_restore(dma_original,dma_tail,read,write)) {
            scene_rsp_gauss_dma_diag[0]=5;return 2;
        }
        for(unsigned i=0;i<4;i++) {
            uint32_t observed=read(0xa4040000u+4*i);
            if(observed!=dma_original[i]) {
                scene_rsp_context_mismatch_word=0x80000000u|i;
                scene_rsp_gauss_dma_diag[0]=3;scene_rsp_gauss_dma_diag[1]=dma_original[i];
                scene_rsp_gauss_dma_diag[2]=observed;return 2;
            }
        }
    }
#endif
#else
    /* Force a different register context, then capture and check every field
     * is zero. This is an actual restore test, not an unchanged-state copy. */
    for(unsigned i=0;i<CONTEXT_WORDS;i++)write(SP_MEM+4*i,0);
    scene_rsp_context_stage=6;
    prepare(read,write);
    scene_rsp_context_stage=7;
    if(!run(restore,restore_words,write,read,wait))return 2;
    scene_rsp_context_stage=8;
    if(!run(capture,capture_words,write,read,wait))return 2;
    scene_rsp_context_stage=9;
    for(unsigned i=0;i<CONTEXT_WORDS;i++)if(read(SP_MEM+4*i)){scene_rsp_context_mismatch_word=i;return 2;}
#endif
    if(!verify(scratch,CONTEXT_SLOT,CONTEXT_WORDS,context,transfer))return 2;
    scene_rsp_context_stage=10;
    for(unsigned start=0;start<CONTEXT_WORDS;start+=128) {
        if(!transfer(scratch,CONTEXT_SLOT+4*start,0))return 2;
        unsigned n=CONTEXT_WORDS-start;if(n>128)n=128;
        for(unsigned i=0;i<n;i++)write(SP_MEM+4*(start+i),scratch[i]);
        for(unsigned i=0;i<n;i++)if(read(SP_MEM+4*(start+i))!=scratch[i]){scene_rsp_context_mismatch_word=start+i;return 2;}
    }
    scene_rsp_context_stage=11;
    prepare(read,write);
    scene_rsp_context_stage=12;
    if(!run(restore,restore_words,write,read,wait))return 2;
    scene_rsp_context_stage=13;
    if(!run(capture,capture_words,write,read,wait))return 2;
    scene_rsp_context_stage=14;
    for(unsigned start=0;start<CONTEXT_WORDS;start+=128) {
        if(!transfer(scratch,CONTEXT_SLOT+4*start,0))return 2;
        unsigned n=CONTEXT_WORDS-start;if(n>128)n=128;
        for(unsigned i=0;i<n;i++)if(read(SP_MEM+4*(start+i))!=scratch[i]){scene_rsp_context_mismatch_word=start+i;return 2;}
    }
    scene_rsp_context_stage=15;
    if(!verify(scratch,0,2048,original,transfer))return 2;
    scene_rsp_context_stage=16;
    uint32_t restored=2166136261u;
    for(unsigned start=0;start<2048;start+=128) {
        if(!transfer(scratch,4*start,0))return 2;
        for(unsigned i=0;i<128;i++) {
            restored=hash(restored,scratch[i]);write(SP_MEM+4*(start+i),scratch[i]);
        }
        for(unsigned i=0;i<128;i++)if(read(SP_MEM+4*(start+i))!=scratch[i])return 2;
    }
    if(restored!=original)return 2;
    scene_rsp_context_stage=17;
    write(SP_PC,0x3c);write(SP_STATUS,6);
    if(read(SP_PC)!=0x3c||read(SP_STATUS)!=status)return 2;
    scene_rsp_context_stage=18;return 1;
}

#ifdef SODIUM64_SCENE_SLOT
static int canonical(scene_rsp_read read) {
    uint32_t pc=read(SP_PC);
    return (read(SP_STATUS)&0x63)==1&&(pc==0x3c4||pc==0x3c8||pc==0x3c)&&
        read(SP_MEM+0x13bc)==0x24080002&&read(SP_MEM+0x13c0)==0x40882000&&
        read(SP_MEM+0x13c4)==0x0900040f&&!read(SP_MEM+0x13c8)&&
        !read(0xa4040018)&&!read(0xa4040014);
}
static int memory_load(uint32_t *scratch,uint32_t offset,uint32_t expected,
                       scene_rsp_read read,scene_rsp_write write,
                       scene_rsp_transfer transfer) {
    uint32_t value=2166136261u;
    for(unsigned start=0;start<2048;start+=128) {
        if(!transfer(scratch,offset+4*start,0))return 0;
        for(unsigned i=0;i<128;i++) {
            value=hash(value,scratch[i]);write(SP_MEM+4*(start+i),scratch[i]);
        }
        for(unsigned i=0;i<128;i++)if(read(SP_MEM+4*(start+i))!=scratch[i])return 0;
    }
    return value==expected;
}
static int stop_restore(uint32_t status,scene_rsp_read read,scene_rsp_write write) {
    /* HALT, clear BREAK/interrupt/single-step/int-on-break; restore all eight
     * renderer signal bits explicitly, rather than retaining current signals. */
    uint32_t command=2|4|8|0x20|0x80;
    for(unsigned i=0;i<8;i++)command|=(status&(0x80u<<i)?0x400u:0x200u)<<(2*i);
    write(SP_PC,0x3c);write(SP_STATUS,command);
    return read(SP_PC)==0x3c&&read(SP_STATUS)==status;
}
uint32_t scene_rsp_context_store(uint32_t scratch[128],uint32_t offset,
    scene_rsp_saved *saved,const uint32_t *capture,unsigned capture_words,
    scene_rsp_read read,scene_rsp_write write,scene_rsp_transfer transfer,
    scene_rsp_wait wait) {
    scene_rsp_context_stage=21;scene_rsp_context_mismatch_word=0xffffffffu;
    if(!scratch||!saved||!capture||!capture_words||capture_words>1024||
       !read||!write||!transfer||!wait||(offset&511)||offset>0x7fdc00u||!canonical(read))return 0;
    scene_rsp_saved accepted={2166136261u,2166136261u,read(SP_STATUS)};
    scene_rsp_context_stage=22;
    for(unsigned start=0;start<2048;start+=128) {
        for(unsigned i=0;i<128;i++) {
            scratch[i]=read(SP_MEM+4*(start+i));accepted.memory_hash=hash(accepted.memory_hash,scratch[i]);
        }
        if(!transfer(scratch,offset+4*start,1)||!transfer(scratch,offset+4*start,0))return 0;
        for(unsigned i=0;i<128;i++)if(scratch[i]!=read(SP_MEM+4*(start+i)))return 0;
    }
    if(!verify(scratch,offset,2048,accepted.memory_hash,transfer))return 0;
    write(SP_MEM,0xffffffffu);write(SP_MEM+32,0xffffffffu);
    scene_rsp_context_stage=23;
    if(!run(capture,capture_words,write,read,wait))return 2;
    if(read(SP_MEM)||read(SP_MEM+32)!=2)return 2;
    scene_rsp_context_stage=24;
    for(unsigned start=0;start<CONTEXT_WORDS;start+=128) {
        unsigned n=CONTEXT_WORDS-start;if(n>128)n=128;
        for(unsigned i=0;i<128;i++) {
            scratch[i]=i<n?read(SP_MEM+4*(start+i)):0;
            if(i<n)accepted.context_hash=hash(accepted.context_hash,scratch[i]);
        }
        if(!transfer(scratch,offset+8192+4*start,1)||!transfer(scratch,offset+8192+4*start,0))return 2;
        for(unsigned i=0;i<n;i++)if(scratch[i]!=read(SP_MEM+4*(start+i)))return 2;
    }
    if(!verify(scratch,offset+8192,CONTEXT_WORDS,accepted.context_hash,transfer))return 2;
    scene_rsp_context_stage=25;
    if(!verify(scratch,offset,2048,accepted.memory_hash,transfer)||
       !memory_load(scratch,offset,accepted.memory_hash,read,write,transfer)||
       !stop_restore(accepted.status,read,write))return 2;
    *saved=accepted;scene_rsp_context_stage=26;return 1;
}
uint32_t scene_rsp_context_load(uint32_t scratch[128],uint32_t offset,
    const scene_rsp_saved *saved,const uint32_t *capture,unsigned capture_words,
    const uint32_t *restore,unsigned restore_words,
    scene_rsp_read read,scene_rsp_write write,scene_rsp_transfer transfer,
    scene_rsp_wait wait) {
    scene_rsp_context_stage=31;scene_rsp_context_mismatch_word=0xffffffffu;
    if(!scratch||!saved||!capture||!capture_words||capture_words>1024||!restore||
       !restore_words||restore_words>1024||!read||!write||!transfer||!wait||
       (offset&511)||offset>0x7fdc00u||(saved->status&0x63)!=1||!canonical(read))return 0;
    /* No SP writes before both full retained owners validate. */
    if(!verify(scratch,offset,2048,saved->memory_hash,transfer)||
       !verify(scratch,offset+8192,CONTEXT_WORDS,saved->context_hash,transfer))return 0;
    scene_rsp_context_stage=32;
    for(unsigned start=0;start<CONTEXT_WORDS;start+=128) {
        if(!transfer(scratch,offset+8192+4*start,0))return 2;
        unsigned n=CONTEXT_WORDS-start;if(n>128)n=128;
        for(unsigned i=0;i<n;i++)write(SP_MEM+4*(start+i),scratch[i]);
        for(unsigned i=0;i<n;i++)if(read(SP_MEM+4*(start+i))!=scratch[i])return 2;
    }
    prepare(read,write);scene_rsp_context_stage=33;
    if(!run(restore,restore_words,write,read,wait)||!run(capture,capture_words,write,read,wait))return 2;
    scene_rsp_context_stage=34;
    for(unsigned start=0;start<CONTEXT_WORDS;start+=128) {
        if(!transfer(scratch,offset+8192+4*start,0))return 2;
        unsigned n=CONTEXT_WORDS-start;if(n>128)n=128;
        for(unsigned i=0;i<n;i++)if(read(SP_MEM+4*(start+i))!=scratch[i]) {
            scene_rsp_context_mismatch_word=start+i;return 2;
        }
    }
    scene_rsp_context_stage=35;
    if(!verify(scratch,offset,2048,saved->memory_hash,transfer)||
       !memory_load(scratch,offset,saved->memory_hash,read,write,transfer)||
       !stop_restore(saved->status,read,write))return 2;
    scene_rsp_context_stage=36;return 1;
}
#endif
