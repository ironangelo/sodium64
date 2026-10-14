/* Original bus-order counterexamples, not an optimized DSP implementation. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define private public
#include "../../third_party/snes_spc/SPC_DSP.h"
#undef private

static SPC_DSP core[2];
static unsigned char ram[2][65536];
static short pcm[2][128];
static void check(bool condition){if(!condition)abort();}
static void initialize() {
    unsigned char regs[128];memset(regs,0,sizeof(regs));regs[SPC_DSP::r_flg]=0x20;
    memset(ram,0,sizeof(ram));memset(pcm,0,sizeof(pcm));
    for(unsigned i=0;i<2;i++) {
        core[i].init(ram[i]);core[i].load(regs);core[i].set_output(pcm[i],128);
        check(core[i].m.phase==0);
    }
}
int main() {
    initialize();
    core[0].run(28);core[0].write(SPC_DSP::r_pmon,0xfe);core[0].run(4);
    core[1].write(SPC_DSP::r_pmon,0xfe);core[1].run(32);
    check(core[0].m.phase==core[1].m.phase&&core[0].m.t_pmon==0&&core[1].m.t_pmon==0xfe);
    puts("LATE_REGISTER phase27_latch=0 late_phase28_write=254 deferred_latch=254 REJECTED");

    initialize();
    for(unsigned i=0;i<2;i++) {
        core[i].m.voices[1].brr_addr=0x4000;core[i].m.voices[1].brr_offset=1;
        ram[i][0x4000]=4;ram[i][0x4001]=0x12;
    }
    core[0].run(2);ram[0][0x4001]=0xe9;core[0].run(1);
    ram[1][0x4001]=0xe9;core[1].run(3);
    check(core[0].m.phase==core[1].m.phase&&core[0].m.t_brr_byte==0x12&&core[1].m.t_brr_byte==0xe9);
    puts("FUTURE_RAM phase1_read=18 phase2_write=233 deferred_read=233 REJECTED");

    initialize();
    for(unsigned i=0;i<2;i++) {
        core[i].write(SPC_DSP::r_flg,0);core[i].m.phase=29;
        core[i].m.t_echo_ptr=0xfffc;core[i].m.t_echo_enabled=0;
        core[i].m.t_echo_out[0]=0x1234;core[i].m.t_echo_out[1]=-2;
    }
    core[0].run(1);
    unsigned actual=ram[0][0xfffc]|(ram[0][0xfffd]<<8);
    unsigned deferred=ram[1][0xfffc]|(ram[1][0xfffd]<<8);
    check(actual==0x1234&&deferred==0);core[1].run(1);
    check(!memcmp(ram[0],ram[1],65536));
    puts("ECHO_READ phase29_write=4660 phase30_CPU_read=4660 deferred_CPU_read=0 REJECTED");

    initialize();
    for(unsigned i=0;i<2;i++){core[i].m.phase=3;core[i].m.outx_buf=0x56;}
    core[0].run(1);
    actual=core[0].read(SPC_DSP::v_outx);deferred=core[1].read(SPC_DSP::v_outx);
    check(actual==0x56&&deferred==0);core[1].run(1);
    check(core[0].read(SPC_DSP::v_outx)==core[1].read(SPC_DSP::v_outx));
    puts("OUTX_READ phase3_publish=86 phase4_CPU_read=86 deferred_CPU_read=0 REJECTED");
    puts("FULL_DSP_WINDOW PASS original_counterexamples=4 unqualified_deferred_window_rejected=1");
}
