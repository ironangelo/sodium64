/* Exercise the production register/timeout/DMA driver without physical MMIO. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define CONTINUOUS_SAVE_TRANSPORT_HOST 1
#include "../../src/continuous_save.c"
static uint32_t reg_values[7], pi_values[5], now, fault, count_step;
static unsigned launched, dma_register, key_count, cases, pio_busy, pio_accesses, meta_accesses;
static uint32_t keys[3];
uint32_t cs_transport_count(void) { now+=count_step; return now; }
static void cart_access(void) {
    assert(!pio_busy); /* A second cart access while IO_BUSY would be unsafe. */
    pio_accesses++;
}
uint32_t cs_transport_meta_word(unsigned off) {
    cart_access(); meta_accesses++;
    return fault==10?0x53363443u+off:0;
}
uint32_t cs_transport_reg_read(unsigned i) {
    cart_access();
    if (!i && (fault==1 || (fault==2 && launched))) return 0x80000000;
    return reg_values[i];
}
void cs_transport_reg_write(unsigned i,uint32_t v) {
    cart_access();
    reg_values[i]=v;
    if (i==4 && key_count<3) keys[key_count++]=v;
    if (!i) {
        launched=1;
        reg_values[0]=fault==3?0x40000000:0;
        if (fault==3) reg_values[1]=0x1234001e;
        if (v=='i' && reg_values[2]==2) reg_values[2]=fault==9?0x13:3;
    }
    if (fault==10) pio_busy=2;
    if ((fault==11 && i==4) || (fault==12 && i==1)) pio_busy=1;
}
uint32_t cs_transport_pi_read(unsigned i) {
    if (i==4 && (fault==4 || (fault==5 && dma_register))) return 3;
    if (i==4 && (fault==6 || (fault==7 && dma_register))) return 4;
    if (i==4 && pio_busy) {
        if (fault==10) pio_busy--;
        return 2;
    }
    return pi_values[i];
}
void cs_transport_pi_write(unsigned i,uint32_t v) {
    assert(i!=4); /* Production must not clear/reset PI to conceal a failure. */
    pi_values[i]=v;
    if (i==2 || i==3) dma_register=i;
}
static void reset(unsigned injection) {
    memset(reg_values,0,sizeof(reg_values)); memset(pi_values,0,sizeof(pi_values));
    reg_values[3]=0x53437632; now=fault=launched=dma_register=key_count=0;
    pio_busy=pio_accesses=meta_accesses=0; count_step=46875000;
    continuous_save_error_stage=continuous_save_error_code=0;
    continuous_save_sc64_status=continuous_save_data0=continuous_save_pi_status=0;
    continuous_save_sd_status=continuous_save_last_command=0;
    error_stage=S64_SAVE_STAGE_BODY; fault=injection;
}
int main(void) {
    reset(0); assert(cs_begin());
    assert(key_count==3 && keys[0]==0 && keys[1]==0x5f554e4c && keys[2]==0x4f434b5f);
    assert(continuous_save_sd_status==3 && !continuous_save_error_code); cases++;
    reset(0); reg_values[3]=0; assert(!cs_begin());
    assert(continuous_save_error_stage==S64_SAVE_STAGE_UNLOCK && continuous_save_error_code==S64_SAVE_ERROR_IDENTIFIER); cases++;
    for(unsigned f=1;f<=3;f++) {
        reset(f); assert(!cs_command('S',BRAM,1));
        assert(continuous_save_error_stage==S64_SAVE_STAGE_BODY && continuous_save_last_command=='S');
        assert(continuous_save_error_code==(f==3?S64_SAVE_ERROR_SC64:S64_SAVE_ERROR_COMMAND_TIMEOUT));
        if(f==3) assert(continuous_save_sc64_status==0x40000000 && continuous_save_data0==0x1234001e);
        else assert(continuous_save_sc64_status==0x80000000);
        cases++;
    }
    unsigned char ram[512];
    for(unsigned f=4;f<=7;f++) {
        reset(f); assert(!cs_pi(ram,BRAM,512,0));
        assert(continuous_save_error_code==(f<6?S64_SAVE_ERROR_PI_TIMEOUT:S64_SAVE_ERROR_PI));
        assert(continuous_save_pi_status==(f<6?3u:4u)); cases++;
    }
    for(int direction=0;direction<2;direction++) {
        reset(0); assert(cs_pi(ram,BRAM,512,direction));
        assert(dma_register==(direction?2u:3u) && pi_values[dma_register]==511 && pi_values[1]==BRAM); cases++;
    }
    reset(9); assert(!cs_begin());
    assert(continuous_save_error_stage==S64_SAVE_STAGE_SD_STATUS && continuous_save_error_code==S64_SAVE_ERROR_SD_STATUS && continuous_save_sd_status==0x13); cases++;
    reset(3); assert(!cs_begin());
    assert(continuous_save_error_stage==S64_SAVE_STAGE_SD_INIT && continuous_save_error_code==S64_SAVE_ERROR_SC64); cases++;
    reset(10); count_step=468750; assert(cs_begin());
    assert(key_count==3 && pio_accesses==23 && !pio_busy && !continuous_save_error_code); cases++;
    reset(10); count_step=468750; assert(cs_command('S',BRAM,1));
    assert(pio_accesses==6 && reg_values[1]==BRAM && reg_values[2]==1 && launched); cases++;
    reset(10); count_step=468750; pio_busy=2;
    assert(cs_meta_word(12)==0x5336344fu && cs_meta_word(0)==MAGIC);
    assert(meta_accesses==2 && pio_accesses==2 && !continuous_save_error_code); cases++;
    for (unsigned f=4;f<=6;f+=2) {
        reset(f); assert(!cs_begin());
        assert(!key_count && !pio_accesses && continuous_save_error_stage==S64_SAVE_STAGE_UNLOCK);
        assert(continuous_save_error_code==(f==4?S64_SAVE_ERROR_PI_TIMEOUT:S64_SAVE_ERROR_PI)); cases++;
    }
    reset(11); assert(!cs_begin());
    assert(key_count==1 && pio_accesses==1 && continuous_save_pi_status==2);
    assert(continuous_save_error_stage==S64_SAVE_STAGE_UNLOCK && continuous_save_error_code==S64_SAVE_ERROR_PI_TIMEOUT); cases++;
    reset(12); assert(!cs_command('S',BRAM,1));
    assert(!launched && pio_accesses==2 && continuous_save_pi_status==2);
    assert(continuous_save_error_stage==S64_SAVE_STAGE_BODY && continuous_save_error_code==S64_SAVE_ERROR_PI_TIMEOUT); cases++;
    for (unsigned f=4;f<=6;f+=2) {
        reset(f); assert(continuous_save_init()==-1);
        assert(!meta_accesses && !pio_accesses && !continuous_save_sink_ready);
        assert(continuous_save_error_stage==S64_SAVE_STAGE_DESCRIPTOR);
        assert(continuous_save_error_code==(f==4?S64_SAVE_ERROR_PI_TIMEOUT:S64_SAVE_ERROR_PI)); cases++;
    }
    reset(3); assert(!cs_command('S',BRAM,1));
    unsigned accesses=pio_accesses;
    fault=0; error_stage=S64_SAVE_STAGE_UNLOCK;
    assert(!cs_begin() && !cs_command('i',0,1) && !cs_meta_word(0));
    assert(pio_accesses==accesses && continuous_save_error_stage==S64_SAVE_STAGE_BODY && continuous_save_error_code==S64_SAVE_ERROR_SC64); cases++;
    printf("CONTINUOUS_SAVE_TRANSPORT PASS cases=%u production_driver=1 physical_mmio=0\n",cases);
}
