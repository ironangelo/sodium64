/* Original synthetic parser/control fixture. No device or guest data. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../../src/remote_control.h"
volatile uint16_t joyxlh[4];
unsigned char apu_clock=42,audio_set,precision_set,skipped_set,underclk_set=4;
unsigned char dsp_buffer[8192],dsp_regs[128],enabled;
uint16_t dsp_pointer;
static unsigned now,fail_send,frame_ready=1,menus,raw_packets,frame_packets,cases;
static char response[1600];
#define CHECK(c) do{assert(c);cases++;}while(0)
uint32_t remote_host_count(void){now+=97;return now;}
int remote_host_send(unsigned t,const void *p,unsigned n){
    if(fail_send)return 0;
    if(t==1){assert(n<sizeof response);memcpy(response,p,n);response[n]=0;}
    else if(t==2){assert(n==8192&&p==dsp_buffer);raw_packets++;}
    else if(t==3){const unsigned char *b=p;assert(n==16&&b[3]==4&&b[11]==24&&b[15]==240);}
    else if(t==4){assert(n==280*240*2);frame_packets++;}
    else assert(0);
    return 1;
}
int remote_host_menu(void){menus++;return 0;}
int remote_host_frame_ready(void){return frame_ready;}
static void request(const char *s){response[0]=0;remote_process_request((const unsigned char *)s,strlen(s)+1,0xa0100000u);}
static void ok(const char *s){request(s);CHECK(strstr(response,"S64 1234abcd OK "));}
static void bad(const char *s){request(s);CHECK(strstr(response," ERR "));}
int main(void){
    remote_boot_ram_bytes=8388608;remote_control_init();
    CHECK(apu_clock==21&&underclk_set==0&&audio_set==4&&precision_set==8&&skipped_set==0);
    ok("s64 1234abcd hello");CHECK(strstr(response,"build=master-usb-bench"));
    CHECK(strstr(response,"fps_claim=none")&&!strstr(response,"state-save"));
    bad("s64 1234abcd capture");bad("s64 1234abcd frame");bad("s64 1234abcd audio");
    bad("s64 1234abcd buttons 0001 4");bad("s64 1234abcd buttons 0010 0");
    bad("s64 1234abcd buttons 0010 36001");bad("s64 1234abcd buttons gg10 4");
    ok("s64 1234abcd buttons 8010 7");CHECK(remote_buttons==0x8010&&remote_button_frames==7&&joyxlh[0]==0x8010);
    ok("s64 1234abcd release");CHECK(!remote_buttons&&!remote_button_frames&&!joyxlh[0]);
    ok("s64 1234abcd pause");CHECK(remote_paused);
    remote_render_frames=100;
    frame_ready=0;bad("s64 1234abcd frame");CHECK(!frame_packets);
    frame_ready=1;ok("s64 1234abcd frame");CHECK(frame_packets==1);
    dsp_pointer=8192;bad("s64 1234abcd audio");dsp_pointer=1;bad("s64 1234abcd audio");
    dsp_pointer=8188;enabled=255;for(unsigned i=0;i<128;i++)dsp_regs[i]=(unsigned char)i;
    ok("s64 1234abcd audio");CHECK(raw_packets==1&&strstr(response,"ring_head_bytes=8188"));
    CHECK(strstr(response,"dspregs=0001020304")&&strstr(response,"not_dac"));
    bad("s64 1234abcd step 0");bad("s64 1234abcd step 36001");
    fail_send=1;request("s64 1234abcd step 2");CHECK(remote_paused&&!remote_pause_pending);
    fail_send=0;ok("s64 1234abcd step 2");CHECK(!remote_paused&&remote_pause_pending&&remote_pause_target==102);
    remote_control_frame(0xa0100000);CHECK(!remote_paused&&remote_render_frames==101);
    remote_control_frame(0xa0100000);CHECK(remote_paused&&remote_render_frames==102&&!remote_pause_pending);
    unsigned guest=remote_guest_frames,render=remote_render_frames;
    for(unsigned i=0;i<100;i++)remote_control_idle(0xa0100000);
    CHECK(remote_guest_frames==guest&&remote_render_frames==render);
    bad("s64 1234abcd pause-at 104");ok("s64 1234abcd resume");
    bad("s64 1234abcd pause-at 102");bad("s64 1234abcd pause-at 101");
    bad("s64 1234abcd pause-at 36103");bad("s64 1234abcd pause-at 4294967296");
    remote_render_frames=0xfffffffeu;ok("s64 1234abcd pause-at 0");
    remote_control_frame(0xa0100000);CHECK(!remote_paused&&remote_render_frames==0xffffffffu);
    remote_control_frame(0xa0100000);CHECK(remote_paused&&!remote_render_frames&&!remote_pause_pending);
    bad("s64 1234abcd menu unexpected");CHECK(!menus);
    fail_send=1;request("s64 1234abcd menu");CHECK(!menus&&remote_paused);
    fail_send=0;ok("s64 1234abcd menu");CHECK(menus==1&&remote_paused);
    bad("s64 1234abcd status extra");bad("s64 1234abcd release extra");
    unsigned char embedded[]={ 's','6','4',' ','1','2','3','4','a','b','c','d',' ',0,'x' };
    remote_process_request(embedded,sizeof embedded,0xa0100000);CHECK(strstr(response,"1234abcd ERR embedded_nul"));
    unsigned char oversized[257]={0};remote_process_request(oversized,sizeof oversized,0);CHECK(strstr(response,"ERR packet_length"));
    /* Invalid packets cannot escape parser bounds or alter frame/input state. */
    uint32_t seed=0x12345678;
    for(unsigned trial=0;trial<32000;trial++){
        unsigned char fuzz[280];unsigned n=trial%280;
        for(unsigned j=0;j<n;j++){seed=seed*1664525u+1013904223u;fuzz[j]=(unsigned char)(seed>>24);}
        if(n>=3)fuzz[0]='!';
        uint32_t g=remote_guest_frames,r=remote_render_frames,b=remote_buttons,p=remote_paused;
        remote_process_request(fuzz,n,0xa0100000);
        assert(g==remote_guest_frames&&r==remote_render_frames&&b==remote_buttons&&p==remote_paused);
    }
    printf("REMOTE_CONTROL PASS cases=%u fuzz=32000 transport_mocked=1\n",cases);
}
