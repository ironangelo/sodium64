/* Synthetic clocked-core differential; no game data. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../third_party/snes_spc/blargg_common.h"
#define private public
#define SPC_DSP Reference_DSP
#define SPC_State_Copier Reference_State_Copier
#include "../../third_party/snes_spc/SPC_DSP.h"
#undef SPC_DSP
#undef SPC_State_Copier
#undef SPC_DSP_H
#ifdef SODIUM64_TEST_GAUSS_BATCH
#define SODIUM64_DSP_FULL_GAUSS_BATCH 1
#endif
#ifdef SODIUM64_TEST_BRR_BATCH
#define SODIUM64_DSP_FULL_BRR_BATCH 1
#endif
#define SPC_DSP Optimized_DSP
#define SPC_State_Copier Optimized_State_Copier
#include "../../third_party/snes_spc/SPC_DSP.h"
#undef SPC_DSP
#undef SPC_State_Copier
#undef private
#undef SODIUM64_DSP_FULL_GAUSS_BATCH
#undef SODIUM64_DSP_FULL_BRR_BATCH

static Reference_DSP ref;
static Optimized_DSP opt;
static unsigned char ram0[65536],ram1[65536];
static short pcm0[32],pcm1[32];
static unsigned checks,directed,slices,frames;
static uint32_t rng=0x49d5a7;
static uint32_t random_word(){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
static void check(bool ok,const char *what){if(!ok){fprintf(stderr,"mismatch %s check=%u\n",what,checks);abort();}}

template<class Core>
static short *sample_pointer(Core &core,short *p,short *output){
    if(!p)return 0;
    uintptr_t value=(uintptr_t)p,external=(uintptr_t)output,extra=(uintptr_t)core.m.extra;
    if(value>=external&&value<=external+sizeof(pcm0))return (short*)(value-external+0x1000);
    check(value>=extra&&value<=extra+sizeof(core.m.extra),"output owner");
    return (short*)(value-extra+0x2000);
}
template<class Core>
static void state(Core &core,unsigned char *bytes,short *output){
    typename Core::state_t m=core.m;
    // Normalize host addresses only; every scalar, array and padding byte stays.
    m.ram=0;
    m.echo_hist_pos=(int(*)[2])(uintptr_t)(core.m.echo_hist_pos-core.m.echo_hist+1);
    m.out=sample_pointer(core,m.out,output);
    m.out_begin=sample_pointer(core,m.out_begin,output);
    m.out_end=sample_pointer(core,m.out_end,output);
    for(unsigned i=0;i<8;i++)m.voices[i].regs=(typename Core::uint8_t*)(uintptr_t)(core.m.voices[i].regs-core.m.regs+1);
    memcpy(bytes,&m,sizeof(m));
}
static void compare(){
    check(sizeof(ref.m)==sizeof(opt.m),"state size");
    unsigned char a[sizeof(ref.m)],b[sizeof(opt.m)];
    state(ref,a,pcm0);state(opt,b,pcm1);
    check(!memcmp(a,b,sizeof(a)),"all core state");
    check(!memcmp(ram0,ram1,sizeof(ram0)),"all APURAM");
    check(!memcmp(pcm0,pcm1,sizeof(pcm0)),"PCM extent");checks++;
}
static void initialize(unsigned voices){
    memset(&ref,0,sizeof(ref));memset(&opt,0,sizeof(opt));
    memset(ram0,0,sizeof(ram0));
    for(unsigned v=0;v<8;v++){
        unsigned addr=0x3000+v*0x100,dir=0x2000+v*4;
        ram0[dir]=ram0[dir+2]=(unsigned char)addr;
        ram0[dir+1]=ram0[dir+3]=(unsigned char)(addr>>8);
        for(unsigned block=0;block<16;block++){
            ram0[addr+block*9]=(unsigned char)((block<<4)|((block&3)<<2)|(block==15?3:0));
            for(unsigned n=1;n<=8;n++)ram0[addr+block*9+n]=(unsigned char)random_word();
        }
    }
    for(unsigned n=0xe000;n<0xe800;n++)ram0[n]=(unsigned char)random_word();
    memcpy(ram1,ram0,sizeof(ram0));
    ref.init(ram0);opt.init(ram1);
    unsigned char regs[128]={0};
    for(unsigned v=0;v<8;v++){
        unsigned p=0x1000+v*0x600;
        regs[v*16]=97-v*7;regs[v*16+1]=(unsigned char)(-89+(int)v*9);
        regs[v*16+2]=(unsigned char)p;regs[v*16+3]=(unsigned char)(p>>8);
        regs[v*16+4]=(unsigned char)v;regs[v*16+7]=v&1?0x70:0;
        regs[v*16+15]=(unsigned char)((int)v*9-23);
    }
    regs[0x0c]=101;regs[0x1c]=93;regs[0x2c]=91;regs[0x3c]=77;
    regs[0x5d]=0x20;regs[0x6d]=0xe0;regs[0x7d]=1;
    regs[0x0d]=(unsigned char)-69;regs[0x2d]=0xfe;regs[0x4d]=0xff;regs[0x6c]=31;
    ref.load(regs);opt.load(regs);ref.write(0x4c,voices);opt.write(0x4c,voices);
    memset(pcm0,0xcc,sizeof(pcm0));memset(pcm1,0xcc,sizeof(pcm1));
    ref.set_output(pcm0,32);opt.set_output(pcm1,32);
}
#if defined(SODIUM64_TEST_GAUSS_BATCH) || defined(SODIUM64_TEST_BRR_BATCH)
static unsigned chunk_cases,chunk_frames;
static void save_state(unsigned char **out,void *state,size_t bytes){memcpy(*out,state,bytes);*out+=bytes;}
static void load_state(unsigned char **in,void *state,size_t bytes){memcpy(state,*in,bytes);*in+=bytes;}
#ifdef SODIUM64_TEST_GAUSS_BATCH
static void batch_lifetime(){
    initialize(255);ref.run(257);opt.run(257);compare();
    check(opt.gaussian_valid!=0,"Gauss batch admitted");
    ref.soft_reset();opt.soft_reset();compare();
    check(!opt.gaussian_valid,"Gauss reset invalidation");
    initialize(255);ref.run(257);opt.run(257);compare();
    unsigned char a[8192],b[8192],*p=a,*q=b;
    ref.copy_state(&p,save_state);opt.copy_state(&q,save_state);
    check(p-a==q-b&&!memcmp(a,b,p-a),"serialized logical state");
    check(!opt.gaussian_valid,"Gauss copy invalidation");compare();
    ref.run(32);opt.run(32);compare();
    p=a;q=b;ref.copy_state(&p,load_state);opt.copy_state(&q,load_state);
    check(!opt.gaussian_valid,"Gauss import invalidation");compare();
    ref.run(1);opt.run(1);compare();
}
#endif
#ifdef SODIUM64_TEST_BRR_BATCH
static void brr_directed(){
    const int histories[8][2]={{-32768,32767},{32767,-32768},{-32767,1},{-1,-1},
        {1,1},{0,0},{12345,-12345},{32766,-32767}};
    unsigned cases=0;
    for(unsigned voice=0;voice<8;voice++)for(unsigned shift=0;shift<16;shift++)
    for(unsigned filter=0;filter<4;filter++)for(unsigned position=0;position<3;position++)
    for(unsigned history=0;history<8;history++){
        initialize(255);
        Reference_DSP::voice_t &a=ref.m.voices[voice];Optimized_DSP::voice_t &b=opt.m.voices[voice];
        a.buf_pos=b.buf_pos=(int)(position*4);a.interp_pos=b.interp_pos=0x4000;
        a.brr_addr=b.brr_addr=0xfff8;a.brr_offset=b.brr_offset=7;
        for(unsigned i=0;i<24;i++)a.buf[i]=b.buf[i]=(int16_t)random_word();
        a.buf[a.buf_pos+11]=b.buf[b.buf_pos+11]=histories[history][0];
        a.buf[a.buf_pos+10]=b.buf[b.buf_pos+10]=histories[history][1];
        ref.m.t_brr_byte=opt.m.t_brr_byte=0x87;ram0[0]=ram1[0]=0xf0;
        ref.m.t_brr_header=opt.m.t_brr_header=(int)((shift<<4)|(filter<<2)|3);
        ref.m.t_brr_next_addr=opt.m.t_brr_next_addr=0x3000;
        ref.m.t_pitch=opt.m.t_pitch=0x3fff;ref.m.t_output=opt.m.t_output=0;
        ref.voice_V4(&a);opt.voice_V4(&b);opt.flush_brr_batch();compare();cases++;
    }
    printf("BRR_BATCH_DIRECTED PASS cases=%u all_ranges_filters_voices_positions_odd_histories_RAM_wrap=exact\n",cases);
}
static void brr_lifetime(){
    initialize(255);
    for(unsigned i=0;i<8;i++){
        ref.write(i*16+2,255);opt.write(i*16+2,255);
        ref.write(i*16+3,63);opt.write(i*16+3,63);
    }
    ref.run(4096);opt.run(4096);compare();
    check(opt.brr_batch_peak==8,"BRR closed input width");
    check(!opt.brr_pending,"BRR public return materialization");
    ref.m.t_brr_byte=opt.m.t_brr_byte=0x87;ref.m.t_brr_header=opt.m.t_brr_header=0x98;
    ref.m.voices[0].interp_pos=opt.m.voices[0].interp_pos=0x4000;
    ref.m.t_pitch=opt.m.t_pitch=0;ref.m.t_output=opt.m.t_output=0;
    ref.voice_V4(&ref.m.voices[0]);opt.voice_V4(&opt.m.voices[0]);
    check(opt.brr_pending==1,"BRR private input captured");
    ref.soft_reset();opt.soft_reset();compare();
    check(!opt.brr_pending,"BRR soft reset materialization");
    ref.m.voices[2].interp_pos=opt.m.voices[2].interp_pos=0x4000;
    ref.voice_V4(&ref.m.voices[2]);opt.voice_V4(&opt.m.voices[2]);
    unsigned char a[8192],b[8192],*p=a,*q=b;
    ref.copy_state(&p,save_state);opt.copy_state(&q,save_state);
    check(p-a==q-b&&!memcmp(a,b,p-a),"serialized BRR state");compare();
    check(!opt.brr_pending,"BRR export materialization");
    ref.run(32);opt.run(32);compare();
    p=a;q=b;ref.copy_state(&p,load_state);opt.copy_state(&q,load_state);compare();
    check(!opt.brr_pending,"BRR import clear");
    ref.run(1);opt.run(1);compare();
    printf("BRR_BATCH_BOUNDARY PASS width=%u public_return_export_soft_reset_import=exact\n",opt.brr_batch_peak);
}
#endif
static void per_clock_events(){
    const unsigned regs[]={0x4c,0x5c,0x6c,0x2d,0x3d,0x4d,0x0c,0x1c,0x0d,0x2c,0x3c,0x5d,0x6d,0x7d};
    initialize(255);ref.run(256);opt.run(256);compare();
    for(unsigned step=0;step<1024;step++){
        unsigned addr=regs[step%14],value=random_word()&255;
        ref.write(addr,value);opt.write(addr,value);
        unsigned byte=random_word()&65535;ram0[byte]=ram1[byte]=(unsigned char)random_word();
        memset(pcm0,0xcc,sizeof(pcm0));memset(pcm1,0xcc,sizeof(pcm1));
        ref.set_output(pcm0,32);opt.set_output(pcm1,32);
        ref.run(1);opt.run(1);compare();
        for(unsigned reg=0;reg<128;reg++)check(ref.read(reg)==opt.read(reg),"per-clock DSP registers");
    }
    printf("GAUSS_BATCH_EVENTS PASS clocks=1024 writes=1024 RAM_mutations=1024\n");
}
static void chunks_directed(){
    const unsigned masks[]={0,1,0x55,0xff};
    const unsigned longer[]={95,96,97,127,128,129,255,256};
    uint32_t saved_rng=rng;
    for(unsigned mask=0;mask<4;mask++)for(unsigned phase=0;phase<32;phase++)
    for(unsigned n=0;n<72;n++){
        initialize(masks[mask]);
        ref.run(256+phase);opt.run(256+phase);compare();
        check(ref.m.phase==(int)phase&&opt.m.phase==(int)phase,"directed entry phase");
        // Mutations occur between calls, just as clock-bounded SPC writes do.
        unsigned addr=random_word()&127,value=random_word()&255;
        ref.write(addr,value);opt.write(addr,value);
        unsigned byte=random_word()&65535;
        ram0[byte]=ram1[byte]=(unsigned char)random_word();
        memset(pcm0,0xcc,sizeof(pcm0));memset(pcm1,0xcc,sizeof(pcm1));
        ref.set_output(pcm0,32);opt.set_output(pcm1,32);
        unsigned clocks=n<64?n+1:longer[n-64];
        ref.run(clocks);opt.run(clocks);compare();
        for(unsigned reg=0;reg<128;reg++)check(ref.read(reg)==opt.read(reg),"directed DSP registers");
        chunk_frames+=(unsigned)ref.sample_count()/2;chunk_cases++;
    }
    rng=saved_rng;
}
#endif
int main(){
    initialize(255);
    for(unsigned voice=0;voice<8;voice++)for(unsigned e=0;e<3;e++)
    for(unsigned non=0;non<2;non++)for(unsigned fraction=0;fraction<256;fraction++){
        unsigned envs[]={0,1,2047};
        for(unsigned v=0;v<8;v++)for(unsigned n=0;n<24;n++)
            ref.m.voices[v].buf[n]=opt.m.voices[v].buf[n]=(int16_t)random_word();
        Reference_DSP::voice_t &a=ref.m.voices[voice];Optimized_DSP::voice_t &b=opt.m.voices[voice];
        a.env=b.env=envs[e];a.hidden_env=b.hidden_env=(int)(fraction*8);
        a.env_mode=Reference_DSP::env_sustain;b.env_mode=Optimized_DSP::env_sustain;
        a.kon_delay=b.kon_delay=fraction%6;
        a.buf_pos=b.buf_pos=fraction%12;
        a.interp_pos=b.interp_pos=(int)((fraction<<4)|((fraction&3)<<12));
        ref.m.t_non=opt.m.t_non=non?255:0;
        ref.m.noise=opt.m.noise=(int)(random_word()&0x7fff);
        ref.m.t_pmon=opt.m.t_pmon=fraction&1?0xfe:0;
        ref.m.t_pitch=opt.m.t_pitch=0x2000;
        ref.m.t_output=opt.m.t_output=(int16_t)random_word();
        ref.m.t_brr_header=opt.m.t_brr_header=fraction&3;
        ref.m.t_adsr0=opt.m.t_adsr0=fraction&1?0x80:0;
        ref.m.regs[0x6c]=opt.m.regs[0x6c]=fraction&8?0x80:0;
        ref.voice_V3c(&a);opt.voice_V3c(&b);compare();directed++;
    }
#if defined(SODIUM64_TEST_GAUSS_BATCH) || defined(SODIUM64_TEST_BRR_BATCH)
    chunks_directed();
#ifdef SODIUM64_TEST_GAUSS_BATCH
    batch_lifetime();
#endif
#ifdef SODIUM64_TEST_BRR_BATCH
    brr_directed();
    brr_lifetime();
#endif
    per_clock_events();
#endif
    const unsigned masks[]={0,1,0x55,0xff};
    for(unsigned scenario=0;scenario<4;scenario++){
        initialize(masks[scenario]);
        for(unsigned step=0;step<2048;step++){
            unsigned clocks=step<32?1:1+random_word()%96;
            if(step%7==0){
                unsigned addr=random_word()&127,value=random_word()&255;
                ref.write(addr,value);opt.write(addr,value);
            }
            if(step%13==0){unsigned addr=random_word()&65535;ram0[addr]=ram1[addr]=(unsigned char)random_word();}
            if(step==1024){ref.soft_reset();opt.soft_reset();}
            memset(pcm0,0xcc,sizeof(pcm0));memset(pcm1,0xcc,sizeof(pcm1));
            // Periodically exercise the core's own extra output buffer as well.
            bool extra=step%19==0;
            ref.set_output(extra?0:pcm0,extra?0:32);opt.set_output(extra?0:pcm1,extra?0:32);
            ref.run(clocks);opt.run(clocks);compare();
            for(unsigned addr=0;addr<128;addr++)check(ref.read(addr)==opt.read(addr),"DSP registers");
            if(!extra)frames+=(unsigned)ref.sample_count()/2;
            slices++;
        }
    }
    printf("DSP_SIGNAL_ELIDE PASS directed=%u slices=%u frames=%u state_checks=%u\n",directed,slices,frames,checks);
#if defined(SODIUM64_TEST_GAUSS_BATCH) || defined(SODIUM64_TEST_BRR_BATCH)
    printf("GAUSS_BATCH_PHASE PASS cases=%u frames=%u\n",chunk_cases,chunk_frames);
#endif
}
