#include "full_dsp_window_memory.h"
#ifdef SODIUM64_DSP_FULL_WINDOW
#include "full_dsp_window.h"
#include <new>
#include <string.h>

struct window_owner_state {
    SPC_DSP reference, candidate;
    SPC_DSP_Window window;
    short pcm0[64], pcm1[64];
    unsigned char serialized0[SPC_DSP::state_size], serialized1[SPC_DSP::state_size];
};
typedef char state_fits_owner[(sizeof(window_owner_state)<=DSP_WINDOW_STATE_BYTES)?1:-1];
typedef char owner_above_base[(DSP_WINDOW_OWNER_BEGIN>=0x400000u)?1:-1];
typedef char owner_below_boot[(DSP_WINDOW_OWNER_END<=0x7f0000u)?1:-1];

#ifdef SODIUM64_DSP_WINDOW_MEMORY_HOST
extern unsigned char* window_memory_host_cached(uint32_t);
extern volatile unsigned char* window_memory_host_uncached(uint32_t);
extern void window_memory_host_cache_release(uint32_t,uint32_t);
#endif
static unsigned char* cached(uint32_t physical) {
#ifdef SODIUM64_DSP_WINDOW_MEMORY_HOST
    return window_memory_host_cached(physical);
#else
    return (unsigned char*)(uintptr_t)(0x80000000u|physical);
#endif
}
static volatile unsigned char* uncached(uint32_t physical) {
#ifdef SODIUM64_DSP_WINDOW_MEMORY_HOST
    return window_memory_host_uncached(physical);
#else
    return (volatile unsigned char*)(uintptr_t)(0xa0000000u|physical);
#endif
}
static void cache_release(full_dsp_window_memory_plan const& plan) {
#ifdef SODIUM64_DSP_WINDOW_MEMORY_HOST
    window_memory_host_cache_release(plan.owner_begin,plan.owner_end);
#else
    for(uint32_t at=plan.owner_begin;at<plan.owner_end;at+=16) {
        void* p=cached(at);
        __asm__ volatile("cache 0x15,0(%0)"::"r"(p):"memory");
    }
    __asm__ volatile("sync":::"memory");
#endif
}
static void copy(unsigned char** out,void* state,size_t n) {
    memcpy(*out,state,n);*out+=n;
}
static void echo(void* context,unsigned,unsigned char const*) {
    ++((full_dsp_window_memory_result*)context)->echo_writes;
}
static bool compare(window_owner_state& state,unsigned char* ref_ram,unsigned char* cpu,unsigned char* shadow,
                    full_dsp_window_memory_result& result) {
    state.window.flush();
    unsigned char* a=state.serialized0;unsigned char* b=state.serialized1;
    state.reference.copy_state(&a,copy);state.window.copy_state(&b,copy);
    if(a-state.serialized0!=b-state.serialized1||
       memcmp(state.serialized0,state.serialized1,a-state.serialized0)||
       memcmp(ref_ram,cpu,DSP_WINDOW_RAM_BYTES)||memcmp(ref_ram,shadow,DSP_WINDOW_RAM_BYTES)||
       memcmp(state.pcm0,state.pcm1,sizeof(state.pcm0)))return false;
    ++result.state_checks;return true;
}

uint32_t full_dsp_window_memory_probe(uint32_t bytes,full_dsp_window_memory_result* output) {
    if(!output)return 0;
    *output=full_dsp_window_memory_result();
    full_dsp_window_memory_plan plan;
    if(!full_dsp_window_memory_select(bytes,&plan))return 0;
    // This API is a paused, temporary probe, never the live guest state. Its
    // caller must deny capture and any active lease before entry. Nothing in
    // the base4MiB, SP memory, DMA registers or guest audio buffer is written.
    output->stage=1;output->owner_bytes=plan.owner_end-plan.owner_begin;
    cache_release(plan);
    for(uint32_t at=plan.owner_begin;at<plan.owner_end;at++)*uncached(at)=0xa5;
    unsigned char *ref_ram=cached(plan.reference_begin),*cpu=cached(plan.producer_begin),*shadow=cached(plan.shadow_begin);
    for(unsigned i=0;i<DSP_WINDOW_RAM_BYTES;i++)ref_ram[i]=cpu[i]=(unsigned char)(i*37+(i>>8)*13+11);
    // Clear/construct all state in its explicit upper-memory lease.
    memset(cached(plan.state_begin),0,DSP_WINDOW_STATE_BYTES);
    window_owner_state* state=::new((void*)cached(plan.state_begin))window_owner_state();
    state->reference.init(ref_ram);state->window.init(state->candidate,cpu,shadow,echo,output);
    unsigned char regs[128]={0};regs[SPC_DSP::r_dir]=0x20;regs[SPC_DSP::r_esa]=0xff;
    regs[SPC_DSP::r_edl]=1;regs[SPC_DSP::r_flg]=0;regs[SPC_DSP::r_pmon]=0xfe;
    state->reference.load(regs);state->window.load(regs);
    output->stage=2;
    bool ok=true;
    for(unsigned period=0;period<16&&ok;period++) {
        memset(state->pcm0,0xcc,sizeof(state->pcm0));memset(state->pcm1,0xcc,sizeof(state->pcm1));
        state->reference.set_output(state->pcm0,64);state->window.set_output(state->pcm1,64);
        for(unsigned phase=0;phase<32&&ok;phase++) {
            state->reference.run(1);state->window.advance(1);++output->clocks;
            unsigned addr=0x4000+period*32+phase,value=period*19+phase*7;
            ref_ram[addr]=(unsigned char)value;state->window.write_ram(addr,value);
            // Journal writes after the latch, echo reads on either channel and
            // register publications all occur inside these real core windows.
            if(phase==28){state->reference.write(0x2d,period);state->window.write_reg(0x2d,period);}
            if(phase==29||phase==30) {
                unsigned echo_addr=0xff00+period*4+(phase==30?2:0);
                int expected=ref_ram[echo_addr];
                if(state->window.read_ram(echo_addr)!=expected)ok=false;
                ++output->producer_reads;
            }
            if(phase==3||phase==31) {
                int expected=state->reference.read(9);
                if(state->window.read_reg(9)!=expected)ok=false;
                ++output->producer_reads;
                if(!compare(*state,ref_ram,cpu,shadow,*output))ok=false;
            }
        }
        if(!compare(*state,ref_ram,cpu,shadow,*output))ok=false;
    }
    state->window.flush();state->~window_owner_state();
    output->stage=3;cache_release(plan);
    const uint32_t guards[]={plan.owner_begin,plan.shadow_begin+DSP_WINDOW_RAM_BYTES,
        plan.reference_begin+DSP_WINDOW_RAM_BYTES,plan.producer_begin+DSP_WINDOW_RAM_BYTES,
        plan.state_begin+DSP_WINDOW_STATE_BYTES};
    for(unsigned i=0;i<5;i++)for(unsigned j=0;j<DSP_WINDOW_GUARD_BYTES;j++)
        if(*uncached(guards[i]+j)!=0xa5)ok=false;
    // Verify cached payloads reached their uncached physical aliases. At probe
    // exit the RAM views are equal; compare all64KiB through uncached reads.
    for(unsigned i=0;i<DSP_WINDOW_RAM_BYTES;i++)
        if(*uncached(plan.reference_begin+i)!=*uncached(plan.shadow_begin+i)||
           *uncached(plan.reference_begin+i)!=*uncached(plan.producer_begin+i))ok=false;
    output->stage=ok?4:3;
    return ok?1:2;
}
#endif
