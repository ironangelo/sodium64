/* SPDX-License-Identifier: GPL-3.0-or-later
 * Original fragmented SD/card model for the actual production C sink.
 */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include "../../tools/sc64-diagnostic-save/continuous_save_abi.h"
extern int continuous_save_init(void);
extern int continuous_save_capture(const unsigned char *, unsigned);
extern uint32_t continuous_save_last_id;
static uint32_t meta[S64C_MAX_BYTES/4];
static unsigned char disk[1024][512], source[32768], snapshots[3][32768], info[32];
static unsigned calls, writes, fail_at, corrupt_at, cases;
static int begin_fail, info_mismatch;
static void put(unsigned char *b, unsigned off, uint32_t v) {
    for (unsigned i=0;i<4;i++) b[off+i]=(unsigned char)(v>>(24-i*8));
}
static uint32_t word(const unsigned char *b) {
    return (uint32_t)b[0]<<24 | (uint32_t)b[1]<<16 | (uint32_t)b[2]<<8 | b[3];
}
uint32_t cs_meta_word(unsigned off) {
    assert(off%4==0 && off<sizeof(meta)); return meta[off/4];
}
static int operation(void) { return ++calls!=fail_at; }
int cs_begin(void) { return !begin_fail; }
int cs_info(unsigned char b[32]) {
    if (!operation()) return 0;
    memcpy(b,info,32); if (info_mismatch) b[19]^=1; return 1;
}
int cs_read(uint32_t lba, unsigned char b[512]) {
    assert(lba>=1000 && lba<2024);
    if (!operation()) return 0;
    memcpy(b,disk[lba-1000],512);
    if (calls==corrupt_at) b[37]^=1;
    return 1;
}
int cs_write(uint32_t lba, const unsigned char b[512]) {
    assert(lba>=1000 && lba<2024);
    if (!operation()) return 0;
    memcpy(disk[lba-1000],b,512); writes++; return 1;
}
static void checksum_meta(void) {
    meta[S64C_OFF_CHECKSUM/4]=0;
    uint32_t sum=0;
    for (unsigned i=0;i<meta[2]/4;i++) sum+=meta[i];
    meta[S64C_OFF_CHECKSUM/4]=0-sum;
}
static unsigned lba_index(unsigned slot,unsigned sector) {
    return meta[(72+slot*264+8+sector*4)/4]-1000;
}
static void source_new(unsigned ordinal) {
    for (unsigned i=0;i<sizeof(source);i++) source[i]=(unsigned char)(i*43+ordinal*17);
    memset(source+8192,0,512);
    put(source,8192,0x53363444);put(source,8196,5);put(source,8200,1);
    put(source,8204,2);put(source,8208,32768);
    uint32_t sum=0;
    for (unsigned i=0;i<sizeof(source);i+=4)
        if (i<8192 || i>=8704) sum+=word(source+i);
    put(source,8192+240,sum);
}
static void setup(unsigned n) {
    memset(meta,0,sizeof(meta)); memset(disk,0,sizeof(disk));
    meta[0]=S64C_MAGIC;meta[1]=1;meta[2]=72+n*264;meta[3]=n;
    meta[4]=64;meta[5]=32768;meta[6]=0x104000;meta[16]=1000;meta[17]=2024;
    for (unsigned i=0;i<32;i++) info[i]=(unsigned char)(i*13+9);
    for (unsigned i=0;i<8;i++) meta[8+i]=word(info+i*4);
    for (unsigned i=0;i<n;i++) {
        unsigned off=(72+i*264)/4;meta[off]=101+i;
        for (unsigned j=0;j<64;j++) {
            /* Fragmented, globally disjoint permutation of 1024 sectors. */
            meta[off+2+j]=1000+((i*64+j)*17%1024);
            if (j<16) memset(disk[lba_index(i,j)],0x55,512);
        }
    }
    checksum_meta(); source_new(1);
    calls=writes=fail_at=corrupt_at=0;begin_fail=info_mismatch=0;
}
static void check_slot(unsigned i,const unsigned char *expected) {
    for (unsigned j=0;j<64;j++) assert(!memcmp(disk[lba_index(i,j)],expected+j*512,512));
}
static void check_previous(void) {
    check_slot(0,snapshots[0]); check_slot(1,snapshots[1]);
}
int main(void) {
    setup(3); assert(continuous_save_init()==1);
    for (unsigned i=0;i<3;i++) {
        source_new(i+1);memcpy(snapshots[i],source,32768);
        assert(continuous_save_capture(source,32768)==1);
        assert(continuous_save_last_id==101+i);
        for (unsigned j=0;j<=i;j++) check_slot(j,snapshots[j]);
        cases++;
    }
    unsigned before=writes;
    assert(continuous_save_capture(source,32768)==-1 && writes==before);cases++;
    /* Soft restart loses cursor: prior data must still be skipped, never reset. */
    assert(continuous_save_init()==1);
    assert(continuous_save_capture(source,32768)==-1 && writes==before);
    for (unsigned i=0;i<3;i++) check_slot(i,snapshots[i]);
    cases++;
    /* Obtain the exact number of operations in a third successful commit. */
    setup(3);assert(continuous_save_init()==1);
    for (unsigned i=0;i<2;i++) {
        source_new(i+1);memcpy(snapshots[i],source,32768);
        assert(continuous_save_capture(source,32768)==1);
    }
    calls=0;source_new(3);assert(continuous_save_capture(source,32768)==1);
    unsigned operation_count=calls;
    for (unsigned fail=1;fail<=operation_count;fail++) {
        setup(3);assert(continuous_save_init()==1);
        for (unsigned i=0;i<2;i++) {
            source_new(i+1);memcpy(snapshots[i],source,32768);
            assert(continuous_save_capture(source,32768)==1);
        }
        source_new(3);calls=0;fail_at=fail;
        assert(continuous_save_capture(source,32768)==0);
        check_previous();before=writes;
        fail_at=0;
        assert(continuous_save_capture(source,32768)==0 && writes==before);
        check_previous();cases++;
    }
    /* Corrupt readbacks at every body/header verification boundary. */
    for (unsigned corrupt=51;corrupt<=operation_count;corrupt+=2) {
        setup(1);assert(continuous_save_init()==1);calls=0;corrupt_at=corrupt;
        assert(continuous_save_capture(source,32768)==0);cases++;
    }
    /* Malformed maps/checksum/card change fail before any sector writes. */
    const unsigned offsets[]={1,2,3,4,5,6,16,17,18,19,20,21};
    for (unsigned i=0;i<sizeof(offsets)/sizeof(*offsets);i++) {
        setup(3);meta[offsets[i]]=offsets[i]==19?1:0;checksum_meta();
        assert(continuous_save_init()==-1 && !writes);cases++;
    }
    setup(3);meta[7]^=1;assert(continuous_save_init()==-1 && !writes);cases++;
    setup(3);meta[(72+264+8)/4]=meta[(72+8)/4];checksum_meta();
    assert(continuous_save_init()==-1 && !writes);cases++;
    setup(3);info_mismatch=1;assert(continuous_save_init()==-1 && !writes);cases++;
    setup(3);begin_fail=1;assert(continuous_save_init()==-1 && !writes);cases++;
    setup(3);meta[0]=0;assert(continuous_save_init()==0 && !writes);cases++;
    setup(3);assert(continuous_save_init()==1);info_mismatch=1;
    assert(continuous_save_capture(source,32768)==0 && !writes);cases++;
    setup(3);assert(continuous_save_init()==1);source[100]^=1;
    assert(continuous_save_capture(source,32768)==0 && !writes);cases++;
    setup(16);assert(continuous_save_init()==1);
    printf("CONTINUOUS_SAVE_SINK PASS cases=%u operations=%u fragmented_maps=1 no_overwrite=1 explicit_readback=1 failure_lock=1\n",cases,operation_count);
}
