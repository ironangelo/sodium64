/* SPDX-License-Identifier: GPL-3.0-or-later
 * Original complete-DSP architectural fixtures. No emulator runtime linkage.
 * The separately compiled reference is unchanged snes_spc (retained LGPL).
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <vector>
#include "blargg_common.h"
#define private public
#define SPC_DSP Reference_DSP
#define SPC_State_Copier Reference_State_Copier
#include "SPC_DSP.h"
#undef SPC_DSP
#undef SPC_State_Copier
#undef SPC_DSP_H
#define SPC_DSP Trace_DSP
#define SPC_State_Copier Trace_State_Copier
#include "SPC_DSP.h"
#undef SPC_DSP
#undef SPC_State_Copier
#undef private

enum Kind { PHASE, DSP_READ8, DSP_READ16, DSP_WRITE16, FETCH,
            RAM_READ8, RAM_WRITE8, REG_READ, REG_WRITE, PCM, KON_OBSERVE };
struct Event { uint32_t clock,kind,address,value; };
static std::vector<Event> events;
static Reference_DSP reference;
static Trace_DSP traced;
static unsigned char ram0[65536],ram1[65536];
// Keep a spare tail: the reference switches to its overflow buffer when full.
static short pcm0[4096+16],pcm1[4096+16];
static unsigned at_clock,collect,full_checks,max_active_mask,total_clocks;
static unsigned phases[32],work[6][8],echo_writes,echo_wraps;
static bool replaying;
static size_t replay_cursor;

static void require_fixture(bool condition,const char* reason) {
    if(!condition) { fprintf(stderr,"FAIL %s clock=%u\n",reason,at_clock); exit(1); }
}
static void emit(unsigned kind,unsigned address,unsigned value) {
    if(collect) {
        Event e={at_clock,kind,address,value};
        if(replaying) {
            require_fixture(replay_cursor<events.size(),"trace ended during DSP operation");
            Event const& expected=events[replay_cursor++];
            require_fixture(e.clock==expected.clock&&e.kind==expected.kind&&
                            e.address==expected.address&&e.value==expected.value,
                            "replayed chronological bus operation");
        } else events.push_back(e);
    }
}
extern "C" bool arch_recording() { return collect!=0; }
extern "C" unsigned char arch_read8(unsigned char* base,unsigned address) {
    require_fixture(address<65536,"DSP byte address range");
    unsigned value=base[address];emit(DSP_READ8,address,value);return (unsigned char)value;
}
extern "C" unsigned arch_read16(unsigned char* base,unsigned char const* address) {
    uintptr_t offset=(uintptr_t)address-(uintptr_t)base;
    require_fixture(offset<65535,"DSP word address range");
    unsigned value=address[0]|address[1]<<8;emit(DSP_READ16,(unsigned)offset,value);return value;
}
extern "C" void arch_write16(unsigned char* base,unsigned char* address,int value) {
    uintptr_t offset=(uintptr_t)address-(uintptr_t)base;
    require_fixture(offset<65535,"DSP echo word range");
    address[0]=(unsigned char)value;address[1]=(unsigned char)(value>>8);
    emit(DSP_WRITE16,(unsigned)offset,(unsigned)value&65535u);
    if(collect)echo_writes++;
}
extern "C" void arch_phase(unsigned phase) {
    require_fixture(phase<32,"DSP phase range");
    if(collect) { phases[phase]++;emit(PHASE,phase,0); }
}
extern "C" void arch_work(unsigned kind,unsigned voice) {
    require_fixture(kind<6&&voice<8,"DSP work owner");
    if(collect)work[kind][voice]++;
}

template<class Core>
static typename Core::sample_t* pointer_offset(Core& dsp,short* pointer,short* output) {
    uintptr_t p=(uintptr_t)pointer,begin=(uintptr_t)output,extra=(uintptr_t)dsp.m.extra;
    if(p>=begin&&p<=begin+sizeof(pcm0))
        return (typename Core::sample_t*)(p-begin+0x1000);
    require_fixture(p>=extra&&p<=extra+sizeof(dsp.m.extra),"PCM pointer owner");
    return (typename Core::sample_t*)(p-extra+0x10000);
}
template<class Core>
static void normalized(Core& dsp,unsigned char* output,short* pcm) {
    typename Core::state_t state=dsp.m;
    state.ram=0;
    state.echo_hist_pos=(int(*)[2])(uintptr_t)(dsp.m.echo_hist_pos-dsp.m.echo_hist+1);
    state.out=pointer_offset(dsp,dsp.m.out,pcm);
    state.out_begin=pointer_offset(dsp,dsp.m.out_begin,pcm);
    state.out_end=pointer_offset(dsp,dsp.m.out_end,pcm);
    for(unsigned v=0;v<8;v++)
        state.voices[v].regs=(typename Core::uint8_t*)(uintptr_t)(dsp.m.voices[v].regs-dsp.m.regs+1);
    memcpy(output,&state,sizeof(state));
}
static void compare_all() {
    require_fixture(sizeof(reference.m)==sizeof(traced.m),"complete state ABI");
    unsigned char a[sizeof(reference.m)],b[sizeof(traced.m)];
    normalized(reference,a,pcm0);normalized(traced,b,pcm1);
    require_fixture(!memcmp(a,b,sizeof(a)),"complete normalized DSP state");
    require_fixture(!memcmp(ram0,ram1,sizeof(ram0)),"all64KiB APURAM");
    require_fixture(!memcmp(pcm0,pcm1,sizeof(pcm0)),"complete PCM buffer");
    full_checks++;
    unsigned active=0;
    for(unsigned v=0;v<8;v++)if(reference.m.voices[v].env>0)active|=1u<<v;
    max_active_mask|=active;
}
static void write_reg(unsigned address,unsigned value) {
    emit(REG_WRITE,address,value&255);
    reference.write(address,value);traced.write(address,value);
}
static void write_ram(unsigned address,unsigned value) {
    require_fixture(address<65536,"producer RAM address");
    emit(RAM_WRITE8,address,value&255);
    ram0[address]=ram1[address]=(unsigned char)value;
}
static void read_ram(unsigned address,unsigned kind) {
    require_fixture(ram0[address]==ram1[address],"producer RAM read");
    emit(kind,address,ram0[address]);
}
static void read_reg(unsigned address) {
    int value=reference.read(address);
    require_fixture(value==traced.read(address),"producer DSP register read");
    emit(REG_READ,address,(unsigned)value);
}
static void observe_kon() {
    bool value=reference.check_kon();
    require_fixture(value==traced.check_kon(),"producer KON observation");
    emit(KON_OBSERVE,0,(unsigned)value);
}
static void initialize(unsigned scenario) {
    memset(&reference,0,sizeof(reference));memset(&traced,0,sizeof(traced));
    memset(ram0,0,sizeof(ram0));
    for(unsigned i=0x200;i<0x1000;i++)ram0[i]=(unsigned char)(i*13+0x37);
    for(unsigned voice=0;voice<8;voice++) {
        unsigned start=0x3000+voice*0x100,entry=0x2000+voice*4;
        ram0[entry]=ram0[entry+2]=(unsigned char)start;
        ram0[entry+1]=ram0[entry+3]=(unsigned char)(start>>8);
        for(unsigned block=0;block<16;block++) {
            unsigned address=start+block*9;
            unsigned range=scenario==3?block:8+(voice&3);
            ram0[address]=(unsigned char)((range<<4)|((voice&3)<<2)|(block==15?3:0));
            for(unsigned byte=1;byte<9;byte++)ram0[address+byte]=(unsigned char)(voice*29+block*43+byte*71+0x17);
        }
    }
    for(unsigned n=0xe000;n<0xe800;n++)ram0[n]=(unsigned char)(n*37+11);
    memcpy(ram1,ram0,sizeof(ram0));
    unsigned char regs[128]={0};
    for(unsigned voice=0;voice<8;voice++) {
        unsigned p=scenario==0?0x1000:0x3fff,b=voice*16;
        regs[b]=97-voice*7;regs[b+1]=(unsigned char)(-89+(int)voice*9);
        regs[b+2]=(unsigned char)p;regs[b+3]=(unsigned char)(p>>8);
        regs[b+4]=(unsigned char)voice;regs[b+7]=(unsigned char)(0x70-voice*3);
        regs[b+15]=(unsigned char)((int)voice*9-23);
    }
    regs[0x0c]=101;regs[0x1c]=93;regs[0x5d]=0x20;regs[0x6d]=0xe0;regs[0x7d]=1;
    regs[0x6c]=scenario>=2?31:0x20;
    if(scenario>=2) { regs[0x4d]=255;regs[0x2c]=91;regs[0x3c]=77;
        regs[0x0d]=(unsigned char)-69;regs[0x2d]=254;regs[0x3d]=16; }
    reference.init(ram0);traced.init(ram1);
    reference.load(regs);traced.load(regs);
    write_reg(0x4c,scenario==0?1:255);
    memset(pcm0,0xcc,sizeof(pcm0));memset(pcm1,0xcc,sizeof(pcm1));
    reference.set_output(pcm0,128);traced.set_output(pcm1,128);
    for(unsigned i=0;i<64*32;i++){reference.run(1);traced.run(1);}
    observe_kon(); // API observation is not part of the serialized core state.
    reference.set_output(pcm0,sizeof(pcm0)/sizeof(pcm0[0]));
    traced.set_output(pcm1,sizeof(pcm1)/sizeof(pcm1[0]));
    memset(pcm0,0xcc,sizeof(pcm0));memset(pcm1,0xcc,sizeof(pcm1));
}
static void nominal_producer(unsigned scenario) {
    unsigned phase=at_clock&31,frame=at_clock>>5;
    if(at_clock==total_clocks-1) {observe_kon();return;}
    unsigned release_mask=scenario==0?1:2;
    if(phase==0&&(frame==64||frame==160)){write_reg(0x5c,release_mask);return;}
    if(phase==0&&(frame==68||frame==164)){write_reg(0x5c,0);return;}
    if(phase==8&&(frame==68||frame==164)){write_reg(0x4c,release_mask);return;}
    if(frame==16&&phase<24&&!(phase&3)) {
        unsigned addresses[6]={0x15,0x16,0x27,0x37,0x67,0x77};
        unsigned values[6]={0x8f,0xe8,0x9c,0xbc,0xdc,0xfc};
        write_reg(addresses[phase/4],values[phase/4]);return;
    }
    if(scenario>=2) {
        if(phase==28&&!(frame&63)){write_reg(0x2d,(frame&64)?0xfe:0x7e);return;}
        if(phase==24&&!(frame&127)){write_reg(0x3d,(frame&128)?0x10:0x20);return;}
        if(phase==28&&(frame==128||frame==384)){write_reg(0x6d,frame==128?0xe8:0xe0);return;}
        if((at_clock&511)==30){read_ram((unsigned)reference.m.t_echo_ptr,FETCH);return;}
        if((at_clock&511)==31){read_ram((unsigned)reference.m.t_echo_ptr+1,RAM_READ8);return;}
    }
    if(!(at_clock&63)) {
        unsigned voice=(at_clock>>6)&7;
        write_ram(0x3001+voice*0x100+((at_clock>>9)%16)*9,at_clock*7+voice);return;
    }
    if((at_clock&127)==8||(at_clock&127)==16) {
        unsigned voice=(at_clock>>7)&7,address=0x3000+voice*0x100+((frame&64)?9:0);
        bool high=(at_clock&127)==16;
        write_ram(0x2002+voice*4+(high?1:0),high?address>>8:address&255);return;
    }
    unsigned polling_mask=scenario==0?2047:511;
    if((at_clock&polling_mask)==33){read_reg(((frame&7)<<4)+8);return;}
    if((at_clock&polling_mask)==41){read_reg(((frame&7)<<4)+9);return;}
    if(!(at_clock&1))read_ram(0x200+(at_clock%0xdfe),FETCH);
}
static void producer(unsigned scenario) {
    nominal_producer(scenario);
    if(scenario==3) {
        unsigned phase=at_clock&31,frame=at_clock>>5;
        if(phase==9)read_reg(((frame&7)<<4)+8);
        if(phase==30)read_reg(((frame&7)<<4)+9);
        if(phase==28&&!(frame&31))
            for(unsigned n=0;n<65;n++)write_ram(0x1800+n,frame+n); // bounded FIFO pressure.
        if(phase==28&&frame==8) {
            write_reg(0x2d,0xaa);write_reg(0x2d,0xfe);read_reg(0x2d);
        }
    }
}
static unsigned char* copy_end;
static void save_bytes(unsigned char** p,void* state,size_t n) {
    require_fixture(*p<=copy_end&&n<=(size_t)(copy_end-*p),"state export bounds");
    memcpy(*p,state,n);*p+=n;
}
static void load_bytes(unsigned char** p,void* state,size_t n) {
    require_fixture(*p<=copy_end&&n<=(size_t)(copy_end-*p),"state import bounds");
    memcpy(state,*p,n);*p+=n;
}
template<class Core>static std::vector<unsigned char> state_bytes(Core& core) {
    unsigned char data[Core::state_size]={0},*end=data;
    copy_end=data+sizeof(data);core.copy_state(&end,save_bytes);
    require_fixture(end<=data+sizeof(data),"serialized state capacity");
    return std::vector<unsigned char>(data,end);
}
static void put32(FILE* f,uint32_t value) {
    unsigned char b[4]={(unsigned char)(value>>24),(unsigned char)(value>>16),
                        (unsigned char)(value>>8),(unsigned char)value};
    require_fixture(fwrite(b,1,4,f)==4,"write fixture word");
}
static void put_blob(FILE* f,const unsigned char* data,size_t n) {
    require_fixture(fwrite(data,1,n,f)==n,"write fixture block");
}
static unsigned align16(unsigned n) { return (n+15u)&~15u; }
static void pad_to(FILE* f,unsigned offset) {
    long position=ftell(f);
    require_fixture(position>=0&&(unsigned long)position<=offset,"section padding order");
    for(unsigned n=(unsigned)position;n<offset;n++)require_fixture(fputc(0,f)!=EOF,"section padding write");
}
static uint32_t get32(std::vector<unsigned char> const& data,size_t offset) {
    require_fixture(offset<=data.size()&&data.size()-offset>=4,"trace word bounds");
    return (uint32_t)data[offset]<<24|(uint32_t)data[offset+1]<<16|
           (uint32_t)data[offset+2]<<8|data[offset+3];
}
template<class Core>static void import_state(Core& core,std::vector<unsigned char>& data,
                                            unsigned offset,unsigned count) {
    require_fixture(offset<=data.size()&&count<=data.size()-offset,"initial state extent");
    unsigned char* cursor=&data[offset];copy_end=cursor+count;
    core.copy_state(&cursor,load_bytes);
    require_fixture(cursor==copy_end,"complete initial state import");
}
template<class Core>static void admitted_state(Core const& core) {
    // Upstream's unmasked directory corner is outside this fixture domain.
    // Check before its read, including after producer-written DIR/SRCN changes.
    require_fixture(core.m.phase>=0&&core.m.phase<32&&core.m.t_dir_addr>=0&&
                    core.m.t_dir_addr<=65532&&!(core.m.t_dir_addr&3),"admitted directory address");
    require_fixture(core.m.t_echo_ptr>=0&&core.m.t_echo_ptr<=65532&&
                    !(core.m.t_echo_ptr&3)&&!(core.m.echo_offset&3),"admitted echo address");
    for(unsigned i=0;i<8;i++) {
        typename Core::voice_t const& v=core.m.voices[i];
        require_fixture(v.buf_pos>=0&&v.buf_pos<=8&&!(v.buf_pos&3)&&
                        v.interp_pos>=0&&v.interp_pos<=0x7fff&&
                        v.kon_delay>=0&&v.kon_delay<=5&&
                        v.env_mode>=Core::env_release&&v.env_mode<=Core::env_sustain,
                        "admitted voice state");
    }
}
static int replay(char const* path) {
    FILE* file=fopen(path,"rb");require_fixture(file!=0,"open replay fixture");
    require_fixture(!fseek(file,0,SEEK_END),"seek fixture end");
    long length=ftell(file);require_fixture(length>=128&&length<=32*1024*1024,"replay file bounds");
    rewind(file);std::vector<unsigned char> data((size_t)length);
    require_fixture(fread(&data[0],1,data.size(),file)==data.size(),"read replay fixture");
    fclose(file);unsigned h[32];for(unsigned i=0;i<32;i++)h[i]=get32(data,i*4);
    require_fixture(h[0]==0x53363444&&h[1]==0x41524331&&h[2]==1&&h[3]==128,"replay format");
    require_fixture(h[5]>=32&&h[5]<=2048&&h[6]==h[5]*32&&h[14]==16&&
                    h[23]==data.size(),"replay dimensions");
    require_fixture(h[8]<=data.size()&&65536<=data.size()-h[8],"initial RAM extent");
    require_fixture(h[12]<=data.size()&&h[13]<=(data.size()-h[12])/16,"event extent");
    require_fixture(h[17]<=data.size()&&65536<=data.size()-h[17],"final RAM extent");
    require_fixture(h[19]<=data.size()&&h[5]*4<=data.size()-h[19],"PCM extent");
    memset(&reference,0,sizeof(reference));memset(&traced,0,sizeof(traced));
    memcpy(ram0,&data[h[8]],65536);memcpy(ram1,ram0,65536);
    reference.init(ram0);traced.init(ram1);
    import_state(reference,data,h[10],h[11]);import_state(traced,data,h[10],h[11]);
    admitted_state(reference);admitted_state(traced);
    require_fixture(reference.m.phase==(int)h[21],"initial state phase matches header");
    reference.set_output(pcm0,sizeof(pcm0)/sizeof(pcm0[0]));
    traced.set_output(pcm1,sizeof(pcm1)/sizeof(pcm1[0]));
    memset(pcm0,0xcc,sizeof(pcm0));memset(pcm1,0xcc,sizeof(pcm1));
    for(unsigned i=0;i<h[13];i++) {
        size_t p=h[12]+(size_t)i*16;
        Event e={get32(data,p),get32(data,p+4),get32(data,p+8),get32(data,p+12)};
        require_fixture(e.clock<h[6],"event clock extent");events.push_back(e);
    }
    compare_all();replaying=true;collect=1;unsigned clocks=0;
    while(replay_cursor<events.size()) {
        Event e=events[replay_cursor];at_clock=e.clock;
        require_fixture(at_clock==clocks,"producer/DSP clock order");
        switch(e.kind) {
        case FETCH:case RAM_READ8:
            require_fixture(e.address<65536,"replayed producer read range");
            read_ram(e.address,e.kind);break;
        case RAM_WRITE8:
            require_fixture(e.value<256,"replayed producer write byte");
            write_ram(e.address,e.value);break;
        case REG_READ:
            require_fixture(e.address<128,"replayed register read range");
            read_reg(e.address);break;
        case REG_WRITE:
            require_fixture(e.address<128&&e.value<256,"replayed register write range");
            write_reg(e.address,e.value);break;
        case KON_OBSERVE:observe_kon();break;
        case PHASE: {
            admitted_state(reference);admitted_state(traced);
            unsigned before=(unsigned)reference.sample_count();
            reference.run(1);traced.run(1);compare_all();clocks++;
            unsigned after=(unsigned)reference.sample_count();
            if(after!=before)emit(PCM,before/2,((uint32_t)(uint16_t)pcm0[before]<<16)|(uint16_t)pcm0[before+1]);
            break;
        }
        default:require_fixture(false,"orphaned DSP bus operation");
        }
    }
    collect=0;require_fixture(clocks==h[6],"complete replay clock count");
    std::vector<unsigned char> final0=state_bytes(reference),final1=state_bytes(traced);
    require_fixture(h[15]<=data.size()&&h[16]<=data.size()-h[15],"final state extent");
    require_fixture(final0==final1&&final0.size()==h[16]&&
                    !memcmp(&final0[0],&data[h[15]],final0.size()),"complete replayed final state");
    require_fixture(!memcmp(ram0,&data[h[17]],65536),"complete replayed final RAM");
    require_fixture((unsigned)reference.sample_count()==h[5]*2,"complete replayed PCM count");
    for(unsigned i=0;i<h[5];i++)require_fixture(get32(data,h[19]+i*4)==
        (((uint32_t)(uint16_t)pcm0[i*2]<<16)|(uint16_t)pcm0[i*2+1]),"replayed PCM frame");
    printf("replayed_clocks=%u replayed_events=%u replayed_frames=%u\n",clocks,(unsigned)events.size(),h[5]);
    return 0;
}
int main(int argc,char** argv) {
    if(argc==3&&!strcmp(argv[1],"replay"))return replay(argv[2]);
    require_fixture(argc==4,"scenario, frames and output path required");
    unsigned scenario=(unsigned)atoi(argv[1]),frames=(unsigned)atoi(argv[2]);
    require_fixture(scenario<4&&frames>=32&&frames<=2048,"fixture range");
    total_clocks=frames*32;
    initialize(scenario);
    std::vector<unsigned char> initial0=state_bytes(reference),initial1=state_bytes(traced);
    require_fixture(initial0==initial1,"initial serialized state");
    unsigned char initial_ram[65536];memcpy(initial_ram,ram0,sizeof(initial_ram));
    compare_all();collect=1;
    for(at_clock=0;at_clock<frames*32;at_clock++) {
        producer(scenario);
        unsigned before=(unsigned)reference.sample_count();
        unsigned echo_before=(unsigned)reference.m.echo_offset;
        reference.run(1);traced.run(1);compare_all();
        if((at_clock&31)==29&&(unsigned)reference.m.echo_offset<echo_before)echo_wraps++;
        unsigned after=(unsigned)reference.sample_count();
        if(after!=before) {
            require_fixture(after==before+2,"one complete stereo frame");
            emit(PCM,before/2,((uint32_t)(uint16_t)pcm0[before]<<16)|(uint16_t)pcm0[before+1]);
        }
    }
    collect=0;
    std::vector<unsigned char> final0=state_bytes(reference),final1=state_bytes(traced);
    require_fixture(final0==final1,"final serialized state");compare_all();
    require_fixture((unsigned)reference.sample_count()==frames*2,"complete PCM count");
    uint32_t h[32]={0x53363444,0x41524331,1,128,scenario,frames,frames*32,32000,128,65536};
    h[10]=h[8]+h[9];h[11]=(uint32_t)initial0.size();
    h[12]=align16(h[10]+h[11]);h[13]=(uint32_t)events.size();h[14]=16;
    h[15]=h[12]+h[13]*16;h[16]=(uint32_t)final0.size();
    h[17]=align16(h[15]+h[16]);h[18]=65536;h[19]=h[17]+h[18];h[20]=frames*4;
    h[21]=0;h[22]=64;h[23]=h[19]+h[20];h[24]=scenario==0?1:255;
    uint32_t phase_mask=0;for(unsigned i=0;i<32;i++)if(phases[i])phase_mask|=1u<<i;
    h[25]=phase_mask;h[26]=0x01020304;
    FILE* output=fopen(argv[3],"wb");require_fixture(output!=0,"open output");
    for(unsigned i=0;i<32;i++)put32(output,h[i]);
    put_blob(output,initial_ram,sizeof(initial_ram));put_blob(output,&initial0[0],initial0.size());
    pad_to(output,h[12]);
    for(size_t i=0;i<events.size();i++) {
        Event const& e=events[i];put32(output,e.clock);put32(output,e.kind);
        put32(output,e.address);put32(output,e.value);
    }
    put_blob(output,&final0[0],final0.size());pad_to(output,h[17]);
    put_blob(output,ram0,sizeof(ram0));
    for(unsigned i=0;i<frames;i++)put32(output,((uint32_t)(uint16_t)pcm0[i*2]<<16)|(uint16_t)pcm0[i*2+1]);
    require_fixture(fclose(output)==0,"close fixture");
    unsigned nonzero=0,pmon=0,noise=0;for(unsigned i=0;i<frames*2;i++)nonzero+=pcm0[i]!=0;
    for(unsigned i=0;i<8;i++){pmon+=work[3][i];noise+=work[4][i];}
    printf("scenario=%u clocks=%u full_state_checks=%u pcm_frames=%u nonzero_pcm=%u "
           "events=%u phase_mask=%u max_active_mask=%u pmon=%u noise=%u echo_writes=%u echo_wraps=%u",
           scenario,frames*32,full_checks,frames,nonzero,(unsigned)events.size(),phase_mask,
           max_active_mask,pmon,noise,echo_writes,echo_wraps);
    for(unsigned i=0;i<8;i++)printf(" brr%u=%u gaussian%u=%u envelope%u=%u",i,work[0][i],i,work[1][i],i,work[2][i]);
    printf("\n");return 0;
}
