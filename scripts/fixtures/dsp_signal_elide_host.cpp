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
#define SPC_DSP Optimized_DSP
#define SPC_State_Copier Optimized_State_Copier
#include "../../third_party/snes_spc/SPC_DSP.h"
#undef SPC_DSP
#undef SPC_State_Copier
#undef private

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
}
