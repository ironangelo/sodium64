/* Original synthetic workload/backup transaction, no commercial data. */
#include "../../src/full_dsp_probe.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
#include "../../third_party/snes_spc/SPC_DSP.h"
#endif

static unsigned char ram[65536],original[65536],cart[65536+1536],scratch[512] __attribute__((aligned(16)));
static unsigned transfers,fail_at,corrupt_at;
static uint32_t ticks;
static void check(bool ok);
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
extern "C" { unsigned char native_diag_snapshot[32768] __attribute__((aligned(16))); }
static unsigned profile_begin_calls,profile_end_calls,profile_reject;
static uint32_t *profile_ring;
extern "C" uint32_t full_dsp_profile_begin(uint32_t *ring) {
    profile_begin_calls++;profile_ring=ring;
    return profile_begin_calls!=profile_reject;
}
extern "C" uint32_t full_dsp_profile_end(uint32_t *next) {
    // Exercise scratch ownership/tail clearing without pretending host timing
    // is hardware sampling. The compiled IRQ has separate actual-word tests.
    profile_end_calls++;
    for(unsigned i=0;i<37;i++)profile_ring[i]=0x80015000+i*4;
    for(unsigned i=37;i<128;i++)check(profile_ring[i]==0);
    *next=37;return 37;
}
#endif
static void check(bool ok){if(!ok)abort();}
static int transfer(unsigned char *block,uint32_t offset,int write) {
    check(offset<65536&&!(offset&511)
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
          ||(write&&offset>=65536&&offset<65536+1536&&!(offset&511))
#endif
    );
    transfers++;
    if(transfers==fail_at)return 0;
    if(write)memcpy(cart+offset,block,512);
    else memcpy(block,cart+offset,512);
    if(transfers==corrupt_at)block[73]^=1;
    return 1;
}
static uint32_t clock_read(){ticks+=100;return ticks;}
static void initialize() {
    for(unsigned i=0;i<65536;i++)ram[i]=(unsigned char)(i*57+(i>>8)*3+19);
    memcpy(original,ram,65536);memset(cart,0xcc,65536);
    transfers=fail_at=corrupt_at=0;ticks=0;
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
    profile_begin_calls=profile_end_calls=profile_reject=0;
    memset(native_diag_snapshot,0x5a,sizeof(native_diag_snapshot));
#endif
}
int main() {
    full_dsp_probe_result result[FULL_DSP_PROBE_CASES];
    initialize();
    check(full_dsp_probe_execute(ram,scratch,transfer,clock_read,result)==1);
    check(transfers==384
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
          +3
#endif
          &&!memcmp(original,ram,65536)&&!memcmp(cart,original,65536));
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
    for(unsigned i=sizeof(SPC_DSP);i<sizeof(native_diag_snapshot);i++)check(native_diag_snapshot[i]==0x5a);
#endif
    for(unsigned i=0;i<FULL_DSP_PROBE_CASES;i++) {
        check(result[i].frames==2048&&result[i].ticks==6400&&result[i].max_block_ticks==100);
        check(result[i].nonzero_samples>1000);
        printf("case%u frames=%u checksum=%u nonzero=%u\n",i,result[i].frames,result[i].checksum,result[i].nonzero_samples);
    }
    unsigned backup_faults=0;
    for(unsigned position=1;position<=256;position+=17) {
        initialize();fail_at=position;
        check(full_dsp_probe_execute(ram,scratch,transfer,clock_read,result)==0);
        check(!memcmp(original,ram,65536)&&!ticks);backup_faults++;
    }
    initialize();corrupt_at=2;
    check(full_dsp_probe_execute(ram,scratch,transfer,clock_read,result)==0);
    check(!memcmp(original,ram,65536)&&!ticks);
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
    for(unsigned i=1;i<=3;i++){
        initialize();profile_reject=i;
        check(full_dsp_probe_execute(ram,scratch,transfer,clock_read,result)==3);
        check(!memcmp(original,ram,65536)&&profile_end_calls==i-1);
    }
    for(unsigned i=257;i<=259;i++){
        initialize();fail_at=i;
        check(full_dsp_probe_execute(ram,scratch,transfer,clock_read,result)==3);
        check(!memcmp(original,ram,65536));
    }
#endif
    unsigned restore_faults=0;
    for(unsigned position=257
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
        +3
#endif
        ;position<=384
#ifdef SODIUM64_FULL_DSP_PC_PROFILE
        +3
#endif
        ;position+=127) {
        initialize();fail_at=position;
        check(full_dsp_probe_execute(ram,scratch,transfer,clock_read,result)==2);
        check(memcmp(original,ram,65536));restore_faults++;
    }
    initialize();
    check(full_dsp_probe_execute(0,scratch,transfer,clock_read,result)==0&&!transfers);
    check(full_dsp_probe_execute(ram,0,transfer,clock_read,result)==0&&!transfers);
    check(full_dsp_probe_execute(ram,scratch,0,clock_read,result)==0&&!transfers);
    check(full_dsp_probe_execute(ram,scratch,transfer,0,result)==0&&!transfers);
    check(full_dsp_probe_execute(ram,scratch,transfer,clock_read,0)==0&&!transfers);
    printf("FULL_DSP_PROBE PASS frames=6144 backup_blocks=128 restore_blocks=128 backup_faults=%u restore_faults=%u corrupt_backup=1 invalid_inputs=5\n",backup_faults,restore_faults);
}
