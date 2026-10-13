/* Original synthetic workload/backup transaction, no commercial data. */
#include "../../src/full_dsp_probe.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef SODIUM64_FULL_DSP_SNAPSHOT_CORE
#include "../../third_party/snes_spc/SPC_DSP.h"
extern "C" { unsigned char native_diag_snapshot[32768] __attribute__((aligned(16))); }
#endif

static unsigned char ram[65536],original[65536],cart[65536],scratch[512];
static unsigned transfers,fail_at,corrupt_at;
static uint32_t ticks;
static void check(bool ok){if(!ok)abort();}
static int transfer(unsigned char *block,uint32_t offset,int write) {
    check(offset<65536&&!(offset&511));
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
#ifdef SODIUM64_FULL_DSP_SNAPSHOT_CORE
    memset(native_diag_snapshot,0x5a,sizeof(native_diag_snapshot));
#endif
}
int main() {
    full_dsp_probe_result result[FULL_DSP_PROBE_CASES];
    initialize();
    check(full_dsp_probe_execute(ram,scratch,transfer,clock_read,result)==1);
    check(transfers==384&&!memcmp(original,ram,65536)&&!memcmp(cart,original,65536));
#ifdef SODIUM64_FULL_DSP_SNAPSHOT_CORE
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
    unsigned restore_faults=0;
    for(unsigned position=257;position<=384;position+=127) {
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
