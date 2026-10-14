#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../src/full_dsp_window_memory.h"
static unsigned char memory[DSP_WINDOW_OWNER_END-DSP_WINDOW_OWNER_BEGIN] __attribute__((aligned(32)));
static unsigned pointer_calls,releases;static bool corrupt_guard;
static void check(bool ok){if(!ok){fprintf(stderr,"FAIL upper-memory owner\n");exit(1);}}
unsigned char* window_memory_host_cached(uint32_t physical) {
    check(physical>=DSP_WINDOW_OWNER_BEGIN&&physical<DSP_WINDOW_OWNER_END);++pointer_calls;
    return memory+physical-DSP_WINDOW_OWNER_BEGIN;
}
volatile unsigned char* window_memory_host_uncached(uint32_t physical) {
    return window_memory_host_cached(physical);
}
void window_memory_host_cache_release(uint32_t begin,uint32_t end) {
    check(begin==DSP_WINDOW_OWNER_BEGIN&&end==DSP_WINDOW_OWNER_END);++releases;
    if(corrupt_guard&&releases==2)memory[0]^=1;
}
int main(){
    unsigned rejected=0;
    const uint32_t sizes[]={0,1,4194303,4194304,4194305,8388607,8388609,0xffffffffu};
    for(unsigned i=0;i<sizeof(sizes)/sizeof(sizes[0]);i++) {
        full_dsp_window_memory_plan plan;memset(&plan,0xff,sizeof(plan));
        check(!full_dsp_window_memory_select(sizes[i],&plan));
        full_dsp_window_memory_plan zero;memset(&zero,0,sizeof(zero));check(!memcmp(&plan,&zero,sizeof(plan)));
        full_dsp_window_memory_result result;memset(&result,0xff,sizeof(result));
        check(full_dsp_window_memory_probe(sizes[i],&result)==0);
        full_dsp_window_memory_result empty;memset(&empty,0,sizeof(empty));check(!memcmp(&result,&empty,sizeof(result)));
        check(pointer_calls==0&&releases==0);++rejected;
    }
    check(!full_dsp_window_memory_select(8388608u,0));
    check(!full_dsp_window_memory_probe(8388608u,0));
    full_dsp_window_memory_result result;
    check(full_dsp_window_memory_probe(8388608u,&result)==1);
    check(result.stage==4&&result.clocks==512&&result.state_checks==48&&result.producer_reads==64&&result.echo_writes==32);
    check(result.owner_bytes==sizeof(memory)&&releases==2);
    pointer_calls=releases=0;corrupt_guard=true;
    check(full_dsp_window_memory_probe(8388608u,&result)==2&&result.stage==3&&releases==2);
    printf("WINDOW_MEMORY PASS rejected_sizes=%u rejected_before_pointer=1 state_checks=48 clocks=512 producer_reads=64 echo_writes=32 guard_fault_rejected=1 owner_bytes=%u\n",rejected,(unsigned)sizeof(memory));
}
