/* Synthetic ownership model for the production paused section observer.
 * Original numeric bytes only; no N64 timing, ROMs, USB, or SD access. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../src/remote_control.c"

uint32_t continuous_save_error_stage,continuous_save_error_code;
uint32_t continuous_save_sc64_status,continuous_save_data0,continuous_save_pi_status;
uint32_t continuous_save_last_command,continuous_save_sd_status,continuous_save_sink_ready;
uint32_t native_diag_phase,native_diag_usb_only,native_diag_snapshot_ready,native_diag_snapshot_sequence;
int32_t native_diag_capture_result;
unsigned char native_diag_snapshot[32768];
volatile uint16_t joyxlh[4];
static unsigned char queued[2][0x5000];
static uint16_t row_color[2][240];
#if SODIUM64_BACKDROP_ROWS
static uint16_t main_color_rows[2][240];
#endif
static uint32_t owner_end[2],owner_rows[2],owner_fb[2];
static uint32_t model_slot,model_sp,model_dma_busy,model_dma_full,model_dp;
static uint32_t fail_address;
static unsigned cases,reads,producer_reads,packets;
static char response[2048];

uint32_t remote_host_count(void){return 1234;}
int remote_host_menu(void){return 0;}
int remote_host_frame_ready(void){return 1;}
int remote_host_send(unsigned type,const void *data,unsigned bytes){
    if(type!=1||bytes>=sizeof(response))abort();
    memcpy(response,data,bytes);response[bytes]=0;packets++;return 1;
}
uint32_t remote_host_section_queue_id(void){return model_slot;}
int remote_host_section_read(uint32_t address,unsigned bytes,uint32_t *value){
    reads++;
    if(address==fail_address)return 0;
    if(address>=0xa4000000u&&address<0xa4001000u&&(bytes!=4||address%4))abort();
    if(address==0xa4040010u){*value=model_sp;return 1;}
    if(address==0xa4040018u){*value=model_dma_busy;return 1;}
    if(address==0xa4040014u){*value=model_dma_full;return 1;}
    if(address==0xa410000cu){*value=model_dp;return 1;}
    for(unsigned q=0;q<2;q++){
        unsigned slot=q*4;uint32_t base=q?SECTION_QUEUE2:SECTION_QUEUE1;
        uint32_t fixed=q?HCOMP_ROW_FIXED_QUEUE2:HCOMP_ROW_FIXED_QUEUE1;
        if(address==DMEM(SECTION_PTR)+slot){*value=owner_end[q];return 1;}
        if(address==DMEM(FRAME_END)+slot){*value=owner_rows[q];return 1;}
        if(address==DMEM(FRAMEBUFFER)+slot){*value=owner_fb[q];return 1;}
        if(address>=base&&address<base+sizeof(queued[q])){
            if(bytes!=1)abort();
            if(slot!=model_slot)producer_reads++;
            *value=queued[q][address-base];return 1;
        }
        if(address>=fixed&&address<fixed+sizeof(row_color[q])){
            if(bytes!=2||address%2)abort();
            if(slot!=model_slot)producer_reads++;
            *value=row_color[q][(address-fixed)/2];return 1;
        }
#if SODIUM64_BACKDROP_ROWS
        uint32_t main=q?HCOMP_ROW_MAIN_QUEUE2:HCOMP_ROW_MAIN_QUEUE1;
        if(address>=main&&address<main+sizeof(main_color_rows[q])){
            if(bytes!=2||address%2)abort();
            if(slot!=model_slot)producer_reads++;
            *value=main_color_rows[q][(address-main)/2];return 1;
        }
#endif
    }
    fprintf(stderr,"unexpected read %08x/%u\n",address,bytes);abort();
}
static void check(int ok){cases++;if(!ok){fprintf(stderr,"FAIL %u: %s\n",cases,response);exit(1);}}
static uint32_t memory_sum(void){
    uint32_t sum=0;
    for(unsigned q=0;q<2;q++){
        for(unsigned i=0;i<sizeof(queued[q]);i++)sum=sum*31+queued[q][i];
        for(unsigned i=0;i<240;i++)sum=sum*31+row_color[q][i];
#if SODIUM64_BACKDROP_ROWS
        for(unsigned i=0;i<240;i++)sum=sum*31+main_color_rows[q][i];
#endif
    }
    return sum;
}
static void run_frame(const char *line,uint32_t fb){
    uint32_t sum=memory_sum(),guest=remote_guest_frames,render=remote_render_frames;
    unsigned paused=remote_paused;packets=0;reads=0;producer_reads=0;response[0]=0;
    remote_process_request((const unsigned char*)line,strlen(line)+1,fb);
    check(packets==1&&memory_sum()==sum&&remote_guest_frames==guest&&remote_render_frames==render&&remote_paused==paused);
    check(!producer_reads);
}
static void expect(const char *line,const char *text){run_frame(line,0xa0113000);check(strstr(response,text)!=NULL);}
static void setup(unsigned count){
    model_slot=4;model_sp=1;model_dma_busy=model_dma_full=model_dp=0;fail_address=0;
    remote_paused=1;remote_guest_frames=901;remote_render_frames=900;
    native_diag_phase=remote_arm_pending=transport_error=menu_error=0;
    for(unsigned q=0;q<2;q++){
        uint32_t base=q?SECTION_QUEUE2:SECTION_QUEUE1;
        owner_end[q]=base+count*64;owner_rows[q]=224;owner_fb[q]=q?0xa0113000:0xa0133d00;
        memset(queued[q],q?0xb2:0xa1,sizeof(queued[q]));
        for(unsigned i=0;i<count;i++)queued[q][i*64+63]=(unsigned char)((i+1)*224/count);
        for(unsigned i=0;i<240;i++)row_color[q][i]=q?0x3456:0x1234;
#if SODIUM64_BACKDROP_ROWS
        for(unsigned i=0;i<240;i++)main_color_rows[q][i]=(uint16_t)((q+1)*0x1000+i);
#endif
    }
}
int main(void){
    remote_control_init();setup(3);
    queued[1][63]=20;queued[1][127]=100;queued[1][191]=224;
    for(unsigned i=30;i<40;i++)row_color[1][i]=(uint16_t)(0x1000+i);
    expect("s64 12345678 sections 0","OK sections=1 render_frame_id=900 guest_boundary_id=901 slot=4");
    check(strstr(response,"section_count=3 cursor=0 returned=3 next_cursor=3")!=NULL);
    check(strstr(response," f0=0,20,13398,13398,13398,1")!=NULL);
    check(strstr(response," f1=20,100,13398,4126,13398,0")!=NULL);
    check(strstr(response," f2=100,224,13398,13398,13398,1")!=NULL);
    check(strstr(response," s0=b2b2b2")!=NULL&&strlen(response)<1536);
    expect("s64 12345678 sections 3","returned=0 next_cursor=3");
    expect("s64 12345678 sections 4","ERR sections_cursor");
    expect("s64 12345678 sections -1","ERR sections_cursor");
    expect("s64 12345678 sections 321","ERR sections_cursor");
    expect("s64 12345678 sections","ERR sections_cursor");
    expect("s64 12345678 sections 0 extra","ERR sections_cursor");
    remote_paused=0;expect("s64 12345678 sections 0","ERR not_paused");check(!reads);remote_paused=1;
    for(unsigned phase=1;phase<=3;phase++){
        native_diag_phase=phase;expect("s64 12345678 sections 0","ERR capture_busy");check(!reads);
    }native_diag_phase=0;
    remote_arm_pending=1;expect("s64 12345678 sections 0","ERR capture_busy");check(!reads);remote_arm_pending=0;
    present=0;expect("s64 12345678 sections 0","ERR sections_transport_unready");check(!reads);present=1;
    transport_error=7;expect("s64 12345678 sections 0","ERR sections_transport_unready");check(!reads);transport_error=0;
    menu_error=1;expect("s64 12345678 sections 0","ERR sections_transport_unready");check(!reads);menu_error=0;
    run_frame("s64 12345678 sections 0",0);check(strstr(response,"ERR frame_unavailable")!=NULL&&!reads);
    remote_render_frames=0;expect("s64 12345678 sections 0","ERR frame_unavailable");check(!reads);remote_render_frames=900;
    model_slot=2;expect("s64 12345678 sections 0","ERR sections_owner");check(!reads);model_slot=4;
    model_sp=0;expect("s64 12345678 sections 0","ERR sections_rsp_busy");
    model_sp=3;expect("s64 12345678 sections 0","ERR sections_rsp_busy");
    model_sp=5;expect("s64 12345678 sections 0","ERR sections_rsp_busy");model_sp=1;
    model_dma_busy=1;expect("s64 12345678 sections 0","ERR sections_rsp_busy");model_dma_busy=0;
    model_dma_full=1;expect("s64 12345678 sections 0","ERR sections_rsp_busy");model_dma_full=0;
    model_dp=0x100;expect("s64 12345678 sections 0","ERR sections_dp_busy");model_dp=0;
    uint32_t end=owner_end[1];owner_end[1]=SECTION_QUEUE2;expect("s64 12345678 sections 0","ERR sections_owner");
    owner_end[1]=SECTION_QUEUE2-64;expect("s64 12345678 sections 0","ERR sections_owner");
    owner_end[1]=SECTION_QUEUE2+0x5001;expect("s64 12345678 sections 0","ERR sections_owner");
    owner_end[1]=end+1;expect("s64 12345678 sections 0","ERR sections_owner");owner_end[1]=end;
    owner_fb[1]^=64;expect("s64 12345678 sections 0","ERR sections_framebuffer");owner_fb[1]^=64;
    owner_rows[1]=0;expect("s64 12345678 sections 0","ERR sections_geometry");
    owner_rows[1]=241;expect("s64 12345678 sections 0","ERR sections_geometry");owner_rows[1]=224;
    queued[1][63]=101;expect("s64 12345678 sections 0","ERR sections_geometry");queued[1][63]=20;
    queued[1][191]=223;expect("s64 12345678 sections 0","ERR sections_geometry");queued[1][191]=224;
    fail_address=DMEM(SECTION_PTR)+4;expect("s64 12345678 sections 0","ERR sections_read_failed");
    fail_address=SECTION_QUEUE2+63;expect("s64 12345678 sections 0","ERR sections_read_failed");
    fail_address=HCOMP_ROW_FIXED_QUEUE2;expect("s64 12345678 sections 0","ERR sections_read_failed");
    setup(8);expect("s64 12345678 sections 0","section_count=8 cursor=0 returned=6 next_cursor=6");
    check(strstr(response," s5=")!=NULL&&strstr(response," s6=")==NULL&&strlen(response)<1536);
    expect("s64 12345678 sections 6","returned=2 next_cursor=8");check(strstr(response," f6=168,196,")!=NULL);
    setup(320);expect("s64 12345678 sections 314","section_count=320 cursor=314 returned=6 next_cursor=320");
    check(strstr(response," s319=")!=NULL&&strlen(response)<1536);
    setup(3);model_slot=0;owner_fb[0]=0xa0113000;
    expect("s64 12345678 sections 0","guest_boundary_id=901 slot=0");check(strstr(response," s0=a1a1a1")!=NULL);
    expect("s64 12345678 status","capabilities=pause,pause-at,step,resume,buttons,release,capture,frame,sav,profile,menu,sections");
#if SODIUM64_BACKDROP_ROWS
    setup(3);
    expect("s64 12345678 backdrop-rows 80","slot=4 cursor=80 returned=16 next_cursor=96 frame_end=224");
    check(strstr(response,"values=20502051205220532054")!=NULL);
    expect("s64 12345678 backdrop-rows 220","returned=4 next_cursor=224");
    expect("s64 12345678 backdrop-rows 224","ERR backdrop_rows_cursor");
    expect("s64 12345678 backdrop-rows 240","ERR backdrop_rows_cursor");
    expect("s64 12345678 backdrop-rows -1","ERR backdrop_rows_cursor");
    remote_paused=0;expect("s64 12345678 backdrop-rows 0","ERR not_paused");remote_paused=1;
    native_diag_phase=1;expect("s64 12345678 backdrop-rows 0","ERR capture_busy");native_diag_phase=0;
    model_sp=0;expect("s64 12345678 backdrop-rows 0","ERR sections_rsp_busy");model_sp=1;
    model_dp=0x100;expect("s64 12345678 backdrop-rows 0","ERR sections_dp_busy");model_dp=0;
    fail_address=HCOMP_ROW_MAIN_QUEUE2+160;
    expect("s64 12345678 backdrop-rows 80","ERR sections_read_failed");fail_address=0;
    model_slot=0;owner_fb[0]=0xa0113000;
    expect("s64 12345678 backdrop-rows 80","slot=0 cursor=80");check(strstr(response,"values=10501051")!=NULL);
#endif
    printf("PASS sections_cases=%u read_only=1 modeled_hardware=1\n",cases);return 0;
}
