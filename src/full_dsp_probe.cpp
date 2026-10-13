/* SPDX-License-Identifier: GPL-3.0-or-later
 * Original synthetic workload around the unmodified LGPL S-DSP reference.
 * No AI/guest timing, render, SD, or legacy DSP state is changed here.
 */
#include "full_dsp_probe.h"
#include "../third_party/snes_spc/SPC_DSP.h"
#include <string.h>

#ifdef SODIUM64_FULL_DSP_SNAPSHOT_CORE
#include <new>
extern "C" unsigned char native_diag_snapshot[32768];
typedef char scratch_core_fits_snapshot[(sizeof(SPC_DSP)<=32768)?1:-1];
static SPC_DSP *scratch_reference_dsp;
#define reference_dsp (*scratch_reference_dsp)
#ifdef SODIUM64_DSP_FULL_CACHE_PROBE
typedef char colored_lease_fits[(8191+8192+0x1c00+128<=32768&&sizeof(SPC_DSP)<=0x800)?1:-1];
static unsigned char *colored_owner(unsigned color) {
    uintptr_t base=(uintptr_t)native_diag_snapshot;
    // The extra8KiB keeps both colored spans beyond the ordinary core lease.
    uintptr_t boundary=(base+8191)&~(uintptr_t)8191;
    return (unsigned char *)(boundary+8192+color);
}
#endif
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

static void run(unsigned char *ram,unsigned scenario,full_dsp_probe_clock clock,
                full_dsp_probe_result *result,unsigned mode,const short *gaussian) {
    workload(ram,scenario);
    *result=full_dsp_probe_result();
    result->checksum=2166136261u;
    //32 stereo frames per block. Re-arm the output to avoid upstream's small
    // overflow buffer. Clock reads exclude setup/checksumming and USB copies.
#ifdef SODIUM64_DSP_FULL_CACHE_PROBE
    short ordinary_output[64];
    short *output=mode&2?(short *)colored_owner(0x1c00):ordinary_output;
    result->core_cache_index=(uintptr_t)&reference_dsp&8191;
    result->output_cache_index=(uintptr_t)output&8191;
    result->core_scratch_offset=(unsigned char *)&reference_dsp-native_diag_snapshot;
    result->output_scratch_offset=mode&2?(unsigned char *)output-native_diag_snapshot:0xffffffffu;
    result->gauss_cache_index=(uintptr_t)gaussian&8191;
    result->gauss_scratch_offset=mode&4?(const unsigned char *)gaussian-native_diag_snapshot:0xffffffffu;
#else
    (void)mode;(void)gaussian;short output[64];
#endif
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
}

static uint32_t execute(unsigned char *ram,unsigned char *scratch,
    full_dsp_probe_transfer transfer,full_dsp_probe_clock clock,
    full_dsp_probe_result result[FULL_DSP_PROBE_CASES],unsigned mode) {
    if(!ram||!scratch||!transfer||!clock||!result||mode>7)return 0;
    // Back up and read back every block before touching guest RAM. Scratch
    // must be uncached for the native PI DMA implementation.
    for(unsigned offset=0;offset<65536;offset+=512) {
        for(unsigned byte=0;byte<512;byte++)scratch[byte]=ram[offset+byte];
        if(!transfer(scratch,offset,1)||!transfer(scratch,offset,0))return 0;
        for(unsigned byte=0;byte<512;byte++)if(scratch[byte]!=ram[offset+byte])return 0;
    }
#ifdef SODIUM64_FULL_DSP_SNAPSHOT_CORE
    // Both A/B variants lease only unpublished, unsealed snapshot storage.
    // The remote admission gate denies capture/snapshot owners before backup.
    void *owner=native_diag_snapshot;
#ifdef SODIUM64_DSP_FULL_CACHE_PROBE
    if(mode&1)owner=colored_owner(0x1000);
#endif
    scratch_reference_dsp=::new (owner) SPC_DSP();
#endif
    const short *gaussian=0;
#ifdef SODIUM64_DSP_FULL_CACHE_PROBE
    gaussian=full_dsp_probe_gauss_lease(mode&4?(short *)colored_owner(0x1800):0);
#endif
    for(unsigned scenario=0;scenario<FULL_DSP_PROBE_CASES;scenario++)
        run(ram,scenario,clock,&result[scenario],mode,gaussian);
#ifdef SODIUM64_DSP_FULL_CACHE_PROBE
    full_dsp_probe_gauss_lease(0);
#endif
#ifdef SODIUM64_FULL_DSP_SNAPSHOT_CORE
    scratch_reference_dsp->~SPC_DSP();scratch_reference_dsp=0;
#endif
    for(unsigned offset=0;offset<65536;offset+=512) {
        if(!transfer(scratch,offset,0))return 2;
        volatile unsigned char *restored=ram+offset;
        for(unsigned byte=0;byte<512;byte++)restored[byte]=scratch[byte];
        for(unsigned byte=0;byte<512;byte++)if(restored[byte]!=scratch[byte])return 2;
    }
    return 1;
}

uint32_t full_dsp_probe_execute(unsigned char *ram,unsigned char *scratch,
    full_dsp_probe_transfer transfer,full_dsp_probe_clock clock,
    full_dsp_probe_result result[FULL_DSP_PROBE_CASES]) {
    return execute(ram,scratch,transfer,clock,result,0);
}
#ifdef SODIUM64_DSP_FULL_CACHE_PROBE
uint32_t full_dsp_probe_execute_mode(unsigned char *ram,unsigned char *scratch,
    full_dsp_probe_transfer transfer,full_dsp_probe_clock clock,
    full_dsp_probe_result result[FULL_DSP_PROBE_CASES],uint32_t mode) {
    return execute(ram,scratch,transfer,clock,result,mode);
}
#endif
