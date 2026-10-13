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
#ifdef SODIUM64_TEST_FULL_BRR_GROUP
static unsigned brr_cases;
static int floor_div(int n,int d){return n>=0?n/d:-((-n+d-1)/d);}
static void brr_oracle(unsigned packed,unsigned shift,unsigned filter,int p1,int p2,int out[4]){
    for(unsigned i=0;i<4;i++){
        int n=(int)((packed>>(12-i*4))&15);if(n>=8)n-=16;
        int s=shift<=12?floor_div(n*(1<<shift),2):(n<0?-2048:0);
        int half2=floor_div(p2,2);
        if(filter==1)s+=floor_div(p1,2)+floor_div(-p1,32);
        if(filter==2)s+=p1-half2+floor_div(half2,16)+floor_div(-3*p1,64);
        if(filter==3)s+=p1-half2+floor_div(-13*p1,128)+floor_div(3*half2,16);
        if(s<-32768)s=-32768;if(s>32767)s=32767;
        int stored=(s*2)&65535;if(stored>=32768)stored-=65536;
        out[i]=stored;p2=p1;p1=stored;
    }
}
static void brr_directed(){
    initialize(255);
    static const unsigned packed_values[]={0x0000,0x7777,0x8888,0xffff,0x17a8,0xf2b3};
    static const int history[][2]={{0,0},{2,-2},{-2,2},{32766,-32768},{-32768,32766},
                                  {1,-1},{-1,1},{32767,-32767},{-32767,32767}};
    uint32_t saved_rng=rng;
    for(unsigned voice=0;voice<8;voice++)for(unsigned shift=0;shift<16;shift++)
    for(unsigned filter=0;filter<4;filter++)for(unsigned pos=0;pos<12;pos+=4)
    for(unsigned h=0;h<9;h++)for(unsigned input=0;input<6;input++){
        Reference_DSP::voice_t &a=ref.m.voices[voice];Optimized_DSP::voice_t &b=opt.m.voices[voice];
        for(unsigned i=0;i<12;i++){
            int sample=(int16_t)random_word();
            a.buf[i]=a.buf[i+12]=b.buf[i]=b.buf[i+12]=sample;
        }
        unsigned prior1=(pos+11)%12,prior2=(pos+10)%12;
        a.buf[prior1]=a.buf[prior1+12]=b.buf[prior1]=b.buf[prior1+12]=history[h][0];
        a.buf[prior2]=a.buf[prior2+12]=b.buf[prior2]=b.buf[prior2+12]=history[h][1];
        a.buf_pos=b.buf_pos=pos;a.interp_pos=b.interp_pos=0x4000|(random_word()&0x3fff);
        a.brr_addr=b.brr_addr=h&1?0xfffa:0x3000;
        a.brr_offset=b.brr_offset=1+2*(input&3);
        unsigned packed=packed_values[input],header=(shift<<4)|(filter<<2)|(input&3);
        ref.m.t_brr_header=opt.m.t_brr_header=(int)header;
        ref.m.t_brr_byte=opt.m.t_brr_byte=(int)(packed>>8);
        // Earlier V3b input is cached; current RAM bytes intentionally differ.
        ram0[a.brr_addr]=ram1[a.brr_addr]=(unsigned char)(header^255);
        ram0[(a.brr_addr+a.brr_offset)&65535]=ram1[(a.brr_addr+a.brr_offset)&65535]=(unsigned char)((packed>>8)^255);
        ram0[(a.brr_addr+a.brr_offset+1)&65535]=ram1[(a.brr_addr+a.brr_offset+1)&65535]=(unsigned char)packed;
        ref.m.t_brr_next_addr=opt.m.t_brr_next_addr=0x3a00;
        ref.m.t_pitch=opt.m.t_pitch=(int)(random_word()&0x7fff);
        ref.m.t_output=opt.m.t_output=(int16_t)random_word();
        ref.m.t_eon=opt.m.t_eon=255;
        ref.m.t_main_out[0]=opt.m.t_main_out[0]=(int16_t)random_word();
        ref.m.t_echo_out[0]=opt.m.t_echo_out[0]=(int16_t)random_word();
        int expected[4];brr_oracle(packed,shift,filter,history[h][0],history[h][1],expected);
        ref.voice_V4(&a);opt.voice_V4(&b);compare();
        for(unsigned i=0;i<4;i++)check(a.buf[pos+i]==expected[i]&&a.buf[pos+i+12]==expected[i],"independent BRR arithmetic");
        brr_cases++;
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
#ifdef SODIUM64_TEST_FULL_BRR_GROUP
    brr_directed();
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
#ifdef SODIUM64_TEST_FULL_BRR_GROUP
    printf("FULL_BRR_GROUP PASS cases=%u\n",brr_cases);
#endif
}
