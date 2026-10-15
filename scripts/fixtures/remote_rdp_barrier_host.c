/* Original sequenced hardware model: compile the production barrier verbatim. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
static uint32_t read_io(uint32_t),clock_count(void);
static void write_io(uint32_t,uint32_t),fence(void);
#define RDP_READ(a) read_io(a)
#define RDP_WRITE(a,v) write_io(a,v)
#define RDP_COUNT() clock_count()
#define RDP_FENCE() fence()
#include "remote_rdp_barrier.h"
static uint32_t status,irq,mask,halt,dma,now,initial_irq,initial_xbus;
static unsigned writes,submitted,current_reads,pipe_reads,irq_reads,fences,stall,command_busy;
static uint32_t words[2],start;
static unsigned cases;
#define CHECK(c) do{assert(c);cases++;}while(0)
static uint32_t clock_count(void){now+=5;return now;}
static uint32_t read_io(uint32_t a){
    switch(a){
    case 0xa4040010:return halt;
    case 0xa4040018:return dma;
    case 0xa430000c:return mask;
    case 0xa4300008:
        if(submitted&&current_reads>=3&&pipe_reads>=3&&stall!=3&&++irq_reads>=2)irq|=0x20;
        return irq;
    case 0xa410000c:
        if(!submitted&&command_busy){if(command_busy!=99)--command_busy;return status|0x740;}
        /* BUSY can briefly read clear before the new command starts. */
        if(submitted&&current_reads<3)return initial_xbus;
        if(submitted&&stall!=2&&++pipe_reads>=3)status&=~0x170u;
        return status;
    case 0xa4100008:
        if(submitted&&stall!=1&&++current_reads>=3)return 0x441ca8;
        return 0x1234;
    default:assert(0);return 0;
    }
}
static void write_io(uint32_t a,uint32_t v){
    writes++;
    switch(a){
    case 0xa0441ca0:assert(!submitted);words[0]=v;break;
    case 0xa0441ca4:assert(!submitted);words[1]=v;break;
    case 0xa410000c:
        if(submitted){assert(current_reads>=3&&pipe_reads>=3&&!(status&0x170));}
        assert(v==1||v==2);if(v==1)status&=~1u;else status|=1;break;
    case 0xa4100000:assert(fences&&!(status&1));start=v;break;
    case 0xa4100004:
        assert(start==0x441ca0&&v==0x441ca8&&words[0]==0x29000000&&!words[1]);
        assert(!command_busy&&!submitted);submitted=1;break;
    case 0xa4300000:
        assert(v==0x800&&!(initial_irq&0x20)&&(irq&0x20));irq&=~0x20u;break;
    default:assert(0);
    }
}
static void fence(void){fences++;}
static void reset(uint32_t xb,uint32_t pending){
    status=xb|0x30;irq=initial_irq=pending;initial_xbus=xb;
    mask=dma=now=0;halt=1;
    writes=submitted=current_reads=pipe_reads=irq_reads=fences=stall=command_busy=0;
    words[0]=words[1]=0xdeadbeef;start=0;
}
int main(void){
    for(unsigned xb=0;xb<2;xb++)for(unsigned pending=0;pending<2;pending++){
        reset(xb,pending?0x28:8);now=0xfffffff0u;command_busy=3;
        CHECK(remote_rdp_drain(80)==1);
        CHECK(submitted&&current_reads>=3&&pipe_reads>=3);
        CHECK((status&1)==xb&&!(status&0x170)&&irq==initial_irq&&fences==2);
    }
    reset(1,0);status=1;CHECK(remote_rdp_drain(80)==1);CHECK(!writes&&!submitted);
    reset(1,0);halt=0;CHECK(remote_rdp_drain(80)==0);CHECK(!writes);
    reset(1,0);dma=1;CHECK(remote_rdp_drain(80)==0);CHECK(!writes);
    reset(1,0);mask=0x20;CHECK(remote_rdp_drain(80)==0);CHECK(!writes);
    for(unsigned bit=2;bit<=4;bit*=2){
        reset(1,0);status|=bit;CHECK(remote_rdp_drain(80)==0);CHECK(!writes);
    }
    reset(1,0);command_busy=99;now=0xfffffff0u;
    CHECK(remote_rdp_drain(80)==0);CHECK(!writes&&!submitted&&now<100);
    for(unsigned failure=1;failure<=3;failure++){
        reset(1,0);stall=failure;now=0xfffffff0u;
        CHECK(remote_rdp_drain(80)==-1);CHECK(submitted&&!(status&1));
        CHECK(!(irq&0x20)&&now<200); /* bounded wrap-safe failure; no resume */
    }
    printf("RDP_BARRIER PASS cases=%u production_header=1 hardware_model=1\n",cases);
}
