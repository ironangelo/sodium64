/* SPDX-License-Identifier: GPL-3.0-or-later
 * Original synthetic workload around the unmodified LGPL S-DSP reference.
 * No AI/guest timing, render, SD, or legacy DSP state is changed here.
 */
#include "full_dsp_probe.h"
#include "../third_party/snes_spc/SPC_DSP.h"
#include <string.h>

#ifdef SODIUM64_FULL_DSP_PC_PROFILE
#include <new>
extern "C" unsigned char native_diag_snapshot[32768];
typedef char profile_core_fits_snapshot[(sizeof(SPC_DSP)<=32768)?1:-1];
static SPC_DSP *profile_reference_dsp;
#define reference_dsp (*profile_reference_dsp)
#else
static SPC_DSP reference_dsp;
#endif

static void workload(unsigned char *ram, unsigned scenario) {
    memset(ram,0,65536);
    for(unsigned voice=0;voice<8;voice++) {
        unsigned start=0x2100+voice*0x100;
        unsigned entry=0x2000+voice*4;
        ram[entry]=ram[entry+2]=(unsigned char)start;
        ram[entry+1]=ram[entry+3]=(unsigned char)(start>>8);
        for(unsigned block=0;block<16;block++) {
            unsigned addr=start+block*9;
            ram[addr]=(unsigned char)(((8+(voice&3))<<4)|((voice&3)<<2)|(block==15?3:0));
            for(unsigned byte=1;byte<9;byte++)
                ram[addr+byte]=(unsigned char)(voice*29+block*43+byte*71+0x17);
        }
    }
    for(unsigned offset=0;offset<0x800;offset++)
        ram[0xe000+offset]=(unsigned char)(offset*37+11);
    unsigned char regs[128]={0};
    for(unsigned voice=0;voice<8;voice++) {
        unsigned base=voice*16;
        unsigned pitch=scenario==0?0x1000:0x3fff;
        regs[base]=97-voice*7;
        regs[base+1]=(unsigned char)(-89+voice*9);
        regs[base+2]=(unsigned char)pitch;
        regs[base+3]=(unsigned char)(pitch>>8);
        regs[base+4]=(unsigned char)voice;
        regs[base+7]=(unsigned char)(0x70-voice*3); // direct gain
        regs[base+0xf]=(unsigned char)((int)voice*9-23); // signed FIR
    }
    regs[SPC_DSP::r_mvoll]=101;regs[SPC_DSP::r_mvolr]=93;
    regs[SPC_DSP::r_dir]=0x20;regs[SPC_DSP::r_esa]=0xe0;regs[SPC_DSP::r_edl]=1;
    if(scenario==2) {
        regs[SPC_DSP::r_eon]=0xff;
        regs[SPC_DSP::r_evoll]=91;regs[SPC_DSP::r_evolr]=77;
        regs[SPC_DSP::r_efb]=(unsigned char)-69;
        regs[SPC_DSP::r_pmon]=0xfe;
        regs[SPC_DSP::r_non]=0x10;
        regs[SPC_DSP::r_flg]=31; // echo writes and noise
    } else regs[SPC_DSP::r_flg]=0x20; // no echo RAM writes
    reference_dsp.init(ram);
    reference_dsp.load(regs);
    reference_dsp.write(SPC_DSP::r_kon,scenario?0xff:1);
}

#ifdef SODIUM64_FULL_DSP_PC_PROFILE
static bool run(unsigned char *ram,unsigned scenario,full_dsp_probe_clock clock,
                unsigned char *scratch,full_dsp_probe_transfer transfer,
#else
static void run(unsigned char *ram,unsigned scenario,full_dsp_probe_clock clock,
#endif
                full_dsp_probe_result *result) {
    workload(ram,scenario);
    *result=full_dsp_probe_result();
    result->checksum=2166136261u;
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
    // The PI buffer is idle between backup and restore. Clear it so unused
    // PC slots cannot retain guest RAM bytes from the previous backup block.
    for(unsigned i=0;i<512;i++)scratch[i]=0;
    if(!full_dsp_profile_begin((uint32_t *)scratch))return false;
#endif
    //32 stereo frames per block. Re-arm the output to avoid upstream's small
    // overflow buffer. Clock reads exclude setup/checksumming and USB copies.
    short output[64];
    for(unsigned block=0;block<FULL_DSP_PROBE_FRAMES/32;block++) {
        reference_dsp.set_output(output,64);
        uint32_t before=clock();
        reference_dsp.run(32*32);
        uint32_t elapsed=clock()-before;
        result->ticks+=elapsed;
        if(elapsed>result->max_block_ticks)result->max_block_ticks=elapsed;
        for(unsigned sample=0;sample<64;sample++) {
            uint16_t value=(uint16_t)output[sample];
            result->nonzero_samples+=value!=0;
            result->checksum=(result->checksum^(value>>8))*16777619u;
            result->checksum=(result->checksum^(value&255))*16777619u;
        }
        result->frames+=32;
    }
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
    result->pc_samples=full_dsp_profile_end(&result->pc_next);
    return transfer(scratch,FULL_DSP_PC_CART_OFFSET+scenario*512,1)!=0;
#endif
}

uint32_t full_dsp_probe_execute(unsigned char *ram,unsigned char *scratch,
    full_dsp_probe_transfer transfer,full_dsp_probe_clock clock,
    full_dsp_probe_result result[FULL_DSP_PROBE_CASES]) {
    if(!ram||!scratch||!transfer||!clock||!result)return 0;
    // Back up and read back every block before touching guest RAM. Scratch
    // must be uncached for the native PI DMA implementation.
    for(unsigned offset=0;offset<65536;offset+=512) {
        for(unsigned byte=0;byte<512;byte++)scratch[byte]=ram[offset+byte];
        if(!transfer(scratch,offset,1)||!transfer(scratch,offset,0))return 0;
        for(unsigned byte=0;byte<512;byte++)if(scratch[byte]!=ram[offset+byte])return 0;
    }
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
    // The remote admission gate leases this existing unsealed snapshot storage.
    // No live capture or published immutable snapshot may coexist with the lease.
    profile_reference_dsp=::new ((void *)native_diag_snapshot) SPC_DSP();
    bool profile_ok=true;
    for(unsigned scenario=0;scenario<FULL_DSP_PROBE_CASES;scenario++) {
        if(!run(ram,scenario,clock,scratch,transfer,&result[scenario])) {profile_ok=false;break;}
    }
    profile_reference_dsp->~SPC_DSP();profile_reference_dsp=0;
#else
    for(unsigned scenario=0;scenario<FULL_DSP_PROBE_CASES;scenario++)
        run(ram,scenario,clock,&result[scenario]);
#endif
    for(unsigned offset=0;offset<65536;offset+=512) {
        if(!transfer(scratch,offset,0))return 2;
        volatile unsigned char *restored=ram+offset;
        for(unsigned byte=0;byte<512;byte++)restored[byte]=scratch[byte];
        for(unsigned byte=0;byte<512;byte++)if(restored[byte]!=scratch[byte])return 2;
    }
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
    return profile_ok?1:3;
#else
    return 1;
#endif
}
