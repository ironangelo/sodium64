/* Original numeric bus traces; unchanged immediate production core is oracle. */
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
#define SODIUM64_DSP_FULL_WINDOW 1
#include "../../src/full_dsp_window.h"
#undef private

static Reference_DSP ref;
static SPC_DSP opt;
static SPC_DSP_Window window;
static unsigned char ram0[65536],cpu[65536],shadow[65536],regs[128];
static short pcm0[512],pcm1[512];
static unsigned checks,reads,clocks,echo_writes,overflow_cases,directed;
static uint32_t rng=0x61a49c32;
static uint32_t random_word(){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;}
static void check(bool ok,const char* what){if(!ok){fprintf(stderr,"FAIL %s checks=%u phase=%d pending=%u\n",what,checks,opt.m.phase,window.pending_clocks());exit(1);}}
struct echo_record { unsigned addr, value; };
static echo_record expected[1024],observed[1024];
static unsigned expected_count,observed_count,tags0[1024],tags1[1024];
static void compare();
static void publish(void*,unsigned addr,unsigned char const* bytes){
    check(observed_count<1024,"echo log bound");
    observed[observed_count].addr=addr;observed[observed_count++].value=bytes[0]|bytes[1]<<8;
    tags1[addr>>6]++;echo_writes++;
}
static void tick(unsigned n){
    for(unsigned i=0;i<n;i++){
        int phase=ref.m.phase;unsigned addr=ref.m.t_echo_ptr+(phase==30?2:0);
        bool write=(phase==29||phase==30)&&!(ref.m.t_echo_enabled&0x20);
        ref.run(1);
        if(write){
            check(expected_count<1024,"reference echo log bound");
            expected[expected_count].addr=addr;
            expected[expected_count++].value=ram0[addr]|ram0[addr+1]<<8;
            tags0[addr>>6]++;
        }
        window.advance(1);
        if(!window.pending_clocks())compare();
    }
    clocks+=n;
}
template<class Core>
static short* sample_pointer(Core& dsp,short* p,short* output){
    uintptr_t value=(uintptr_t)p,external=(uintptr_t)output,extra=(uintptr_t)dsp.m.extra;
    if(value>=external&&value<=external+sizeof(pcm0))return(short*)(value-external+0x1000);
    check(value>=extra&&value<=extra+sizeof(dsp.m.extra),"PCM pointer owner");
    return(short*)(value-extra+0x2000);
}
template<class Core>
static void state(Core& dsp,unsigned char* bytes,short* output){
    typename Core::state_t m=dsp.m;
    m.ram=0;m.echo_hist_pos=(int(*)[2])(uintptr_t)(dsp.m.echo_hist_pos-dsp.m.echo_hist+1);
    m.out=sample_pointer(dsp,m.out,output);m.out_begin=sample_pointer(dsp,m.out_begin,output);
    m.out_end=sample_pointer(dsp,m.out_end,output);
    for(unsigned i=0;i<8;i++)m.voices[i].regs=(typename Core::uint8_t*)(uintptr_t)(dsp.m.voices[i].regs-dsp.m.regs+1);
    memcpy(bytes,&m,sizeof(m));
}
static void compare(){
    check(window.pending_clocks()==0&&window.pending_events()==0,"flush drains queue");
    check(sizeof(ref.m)==sizeof(opt.m),"logical state ABI");
    unsigned char a[sizeof(ref.m)],b[sizeof(opt.m)];state(ref,a,pcm0);state(opt,b,pcm1);
    check(!memcmp(a,b,sizeof(a)),"complete normalized DSP state");
    check(!memcmp(ram0,cpu,sizeof(cpu)),"complete CPU RAM");
    check(!memcmp(ram0,shadow,sizeof(shadow)),"complete DSP shadow RAM");
    check(!memcmp(pcm0,pcm1,sizeof(pcm0)),"complete PCM extent");
    check(expected_count==observed_count&&!memcmp(expected,observed,expected_count*sizeof(expected[0])),"enabled echo publication order/address/value");
    check(!memcmp(tags0,tags1,sizeof(tags0)),"exact echo JIT-tag callback count");
    checks++;
}
static void flush(){window.flush();compare();}
static void initialize(unsigned active=255){
    window.flush();
    memset(&ref,0,sizeof(ref));memset(&opt,0,sizeof(opt));
    memset(ram0,0,sizeof(ram0));memset(regs,0,sizeof(regs));
    memset(tags0,0,sizeof(tags0));memset(tags1,0,sizeof(tags1));
    expected_count=observed_count=0;
    for(unsigned v=0;v<8;v++){
        unsigned addr=0x3000+v*0x100,dir=0x2000+v*4;
        ram0[dir]=ram0[dir+2]=(unsigned char)addr;
        ram0[dir+1]=ram0[dir+3]=(unsigned char)(addr>>8);
        for(unsigned block=0;block<16;block++){
            ram0[addr+block*9]=(unsigned char)((block<<4)|((block&3)<<2)|(block==15?3:0));
            for(unsigned n=1;n<=8;n++)ram0[addr+block*9+n]=(unsigned char)random_word();
        }
        unsigned pitch=0x1000+v*0x600;
        regs[v*16]=97-v*7;regs[v*16+1]=(unsigned char)(-89+(int)v*9);
        regs[v*16+2]=(unsigned char)pitch;regs[v*16+3]=(unsigned char)(pitch>>8);
        regs[v*16+4]=(unsigned char)v;regs[v*16+7]=0x70;
        regs[v*16+15]=(unsigned char)((int)v*9-23);
    }
    for(unsigned n=0xe000;n<0xe800;n++)ram0[n]=(unsigned char)random_word();
    regs[0x0c]=101;regs[0x1c]=93;regs[0x2c]=91;regs[0x3c]=77;
    regs[0x5d]=0x20;regs[0x6d]=0xe0;regs[0x7d]=1;
    regs[0x0d]=(unsigned char)-69;regs[0x2d]=0xfe;regs[0x4d]=0xff;regs[0x6c]=31;
    memcpy(cpu,ram0,sizeof(cpu));
    ref.init(ram0);window.init(opt,cpu,shadow,publish,0);
    ref.load(regs);window.load(regs);ref.write(0x4c,active);window.write_reg(0x4c,active);
    memset(pcm0,0xcc,sizeof(pcm0));memset(pcm1,0xcc,sizeof(pcm1));
    ref.set_output(pcm0,512);window.set_output(pcm1,512);compare();
}
static void reg_write(unsigned addr,unsigned value){ref.write(addr,value);window.write_reg(addr,value);if(!window.pending_clocks())compare();}
static void ram_write(unsigned addr,unsigned value){ram0[addr]=(unsigned char)value;window.write_ram(addr,value);if(!window.pending_clocks())compare();}
static void reg_read(unsigned addr){check(ref.read(addr)==window.read_reg(addr),"producer DSP register read");reads++;compare();}
static void ram_read(unsigned addr){check(ram0[addr]==window.read_ram(addr),"producer RAM read / instruction fetch");reads++;if(!window.pending_clocks())compare();}
static void save(unsigned char** out,void* state,size_t n){memcpy(*out,state,n);*out+=n;}
static void load(unsigned char** in,void* state,size_t n){memcpy(state,*in,n);*in+=n;}

static void original_hazards(){
    initialize(0);tick(28);reg_write(0x2d,0xfe);tick(4);flush();
    check(opt.m.t_pmon==0xfe,"PMON later latch from initial0xfe");
    initialize(0);ref.write(0x2d,0);window.write_reg(0x2d,0);
    tick(28);reg_write(0x2d,0xfe);tick(4);flush();check(opt.m.t_pmon==0,"late PMON not read early");
    initialize(0);
    ref.m.voices[1].brr_addr=opt.m.voices[1].brr_addr=0x4000;
    ref.m.voices[1].brr_offset=opt.m.voices[1].brr_offset=1;
    ram_write(0x4000,4);ram_write(0x4001,0x12);
    tick(2);ram_write(0x4001,0xe9);tick(1);flush();check(opt.m.t_brr_byte==0x12,"future BRR byte hidden");
    initialize(0);ref.m.phase=opt.m.phase=29;reg_write(0x6c,0);
    ref.m.t_echo_ptr=opt.m.t_echo_ptr=0xfffc;ref.m.t_echo_enabled=opt.m.t_echo_enabled=0;
    ref.m.t_echo_out[0]=opt.m.t_echo_out[0]=0x1234;
    tick(1);ram_read(0xfffc);ram_read(0xfffd);flush();
    initialize(0);ref.m.phase=opt.m.phase=3;ref.m.outx_buf=opt.m.outx_buf=0x56;
    tick(1);reg_read(9);check(opt.read(9)==0x56,"OUTX publication");directed+=4;
}
static void all_phases_regs(){
    for(unsigned phase=0;phase<32;phase++)for(unsigned addr=0;addr<128;addr++){
        initialize();tick(128+phase);flush();
        tick(1);unsigned value=(addr*19+phase*7)&255;
        if(addr==0x5d)value=0x20; // existing core assumes a non-wrapping directory extent
        reg_write(addr,value);reg_write(addr,value^((addr==0x5d)?0:0x55));
        tick(1+(phase%7));reg_read(addr);tick(37);flush();directed++;
    }
}
static void echo_admission(){
    const unsigned esa[]={0,0x80,0xff},offset[]={0,4,0x7fc,0x7800};
    for(unsigned phase=0;phase<32;phase++)for(unsigned s=0;s<3;s++)
    for(unsigned o=0;o<4;o++)for(unsigned mode=0;mode<4;mode++){
        initialize(0);ref.m.phase=opt.m.phase=phase;
        ref.m.t_esa=opt.m.t_esa=esa[s];ref.m.echo_offset=opt.m.echo_offset=offset[o];
        ref.m.echo_length=opt.m.echo_length=0x800;
        unsigned base=(esa[s]*256+offset[o])&65535;
        ref.m.t_echo_ptr=opt.m.t_echo_ptr=base;
        ref.m.t_echo_enabled=opt.m.t_echo_enabled=mode&1?0x20:0;
        reg_write(0x6c,mode&2?0x20:0);reg_write(0x6d,esa[(s+1)%3]);reg_write(0x7d,o);
        ref.m.t_echo_out[0]=opt.m.t_echo_out[0]=0x1234;
        ref.m.t_echo_out[1]=opt.m.t_echo_out[1]=-2;
        tick(1);
        ram_read((base+4)&65535); // safe neighboring byte must not require blanket catch-up
        for(unsigned byte=0;byte<4;byte++)ram_read((base+byte)&65535);
        ram_write((base+1)&65535,0xa5);tick(64);flush();directed++;
    }
    // Distinct captured pointer after phase22, even after ESA/EDL/offset change.
    initialize(0);ref.m.phase=opt.m.phase=29;
    ref.m.t_echo_ptr=opt.m.t_echo_ptr=0xfffc;
    ref.m.t_esa=opt.m.t_esa=0x20;ref.m.echo_offset=opt.m.echo_offset=0x100;
    ref.m.t_echo_enabled=opt.m.t_echo_enabled=0;ref.m.t_echo_out[0]=opt.m.t_echo_out[0]=0x5678;
    tick(1);ram_read(0xfffc);ram_write(0xfffd,0xa5);tick(2);flush();directed++;
}
static void fifo_and_lifecycle(){
    for(unsigned phase=0;phase<31;phase++){
        initialize();ref.m.phase=opt.m.phase=phase;tick(1);
        for(unsigned n=0;n<SPC_DSP_Window::event_capacity+5;n++){
            if(n&1)reg_write(0x2d,n);else ram_write(0x6000+n,n);
        }
        flush();overflow_cases++;
    }
    for(unsigned phase=0;phase<32;phase++){
        initialize();tick(128+phase);ram_write(0x6000,0x77);reg_write(0x4c,0xa5);
        unsigned char a[8192],b[8192],*p=a,*q=b;
        ref.copy_state(&p,save);window.copy_state(&q,save);
        check(p-a==q-b&&!memcmp(a,b,p-a),"state export flush");compare();
        tick(19);ram_write(0x6000,0x88);p=a;q=b;
        ref.copy_state(&p,load);window.copy_state(&q,load);compare();
        tick(17);ram_write(0x6001,0x99);
        ref.soft_reset();window.soft_reset();compare();
        tick(29);ref.load(regs);window.load(regs);compare();
        tick(27);check(ref.sample_count()==window.sample_count(),"PCM consumption flush");compare();
        tick(30);ref.set_output(pcm0,512);window.set_output(pcm1,512);compare();
        tick(14);check(ref.check_kon()==window.check_kon(),"KON observation flush");compare();
        tick(15);ref.reset();window.reset();compare();directed++;
    }
}
static void random_bus(){
    for(unsigned scenario=0;scenario<32;scenario++){
        initialize((scenario&3)?255:0);
        for(unsigned n=0;n<768;n++){
            unsigned op=random_word()%9,addr=random_word()&65535,value=random_word()&255;
            if(op<3){tick(random_word()%17);if(!window.pending_clocks())compare();}
            else if(op==3)ram_write(addr,value);
            else if(op==4){addr&=127;if(addr==0x5d)value&=0xfc;reg_write(addr,value);}
            else if(op==5)ram_read(addr);
            else if(op==6)reg_read(addr&127);
            else if(op==7){unsigned base=(ref.m.t_esa*256+ref.m.echo_offset)&65535;ram_read(base);}
            else flush();
        }
        flush();
    }
}
int main(){
    // First use needs no flush of an unbound controller.
    window.pending=window.count=0;
    original_hazards();all_phases_regs();echo_admission();fifo_and_lifecycle();random_bus();
    printf("FULL_DSP_WINDOW_CONTROLLER PASS state_checks=%u producer_reads=%u clocks=%u directed=%u FIFO_overflow=%u echo_word_publications=%u original_hazards=4\n",checks,reads,clocks,directed,overflow_cases,echo_writes);
}
