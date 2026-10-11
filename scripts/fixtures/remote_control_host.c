/* Original synthetic model of the production command parser. No ROM data,
 * serial port, N64, card, firmware update, or physical acceptance involved. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "../../src/remote_control.h"
#include "../../tools/sc64-diagnostic-save/recorder_runtime_abi.h"
uint32_t continuous_save_error_stage,continuous_save_error_code;
uint32_t continuous_save_sc64_status,continuous_save_data0,continuous_save_pi_status;
uint32_t continuous_save_last_command,continuous_save_sd_status,continuous_save_sink_ready;
uint32_t native_diag_phase,native_diag_usb_only,native_diag_snapshot_ready,native_diag_snapshot_sequence;
int32_t native_diag_capture_result;
unsigned char native_diag_snapshot[32768];
volatile uint16_t joyxlh[4];
#ifdef SODIUM64_AUDIO_OBSERVER
unsigned char dsp_buffer[8192],dsp_regs[128],enabled;
uint16_t dsp_pointer;
volatile uint32_t dsp_audio_blocks,dsp_audio_idle,dsp_audio_full;
volatile uint32_t dsp_audio_gap_max,dsp_audio_last_count;
const uint32_t dsp_audio_dac_rate=1526;
#ifdef SODIUM64_DSP_KOFF_RELEASE
volatile uint32_t dsp_release_steps,dsp_release_last;
#endif
uint32_t remote_host_audio_register(unsigned offset){if(offset!=4&&offset!=12)abort();return 0x40000000u+offset;}
#endif
#ifdef SODIUM64_BRR_OBSERVER
volatile uint32_t dsp_brr_next,dsp_brr_count;
unsigned char dsp_brr_records[512];
#endif
static uint32_t clock_value;
static unsigned cases, packets, types[3], sizes[3], menu_calls;
static int fail_send;
static int frame_ready=1;
static int expect_paused_ack;
static unsigned paused_ack_checks;
static char response[2048];
uint32_t remote_host_count(void){return clock_value;}
int remote_host_menu(void){menu_calls++;return 0;}
int remote_host_frame_ready(void){return frame_ready;}
int remote_host_send(unsigned type,const void *data,unsigned bytes){
    if(type==1&&expect_paused_ack){if(!remote_paused)abort();paused_ack_checks++;}
    if(fail_send)return 0;
    if(packets<3){types[packets]=type;sizes[packets]=bytes;}packets++;
    if(type==1){if(bytes>=sizeof(response))abort();memcpy(response,data,bytes);response[bytes]=0;}
    if(type==3){const unsigned char expected[16]={0,0,0,4,0,0,0,2,0,0,1,24,0,0,0,240};
        if(bytes!=16||memcmp(data,expected,16))abort();}
    if(type==2&&bytes==32768&&data!=native_diag_snapshot)abort();
#ifdef SODIUM64_AUDIO_OBSERVER
    if(type==2&&bytes==8192&&data!=dsp_buffer)abort();
#endif
#ifdef SODIUM64_BRR_OBSERVER
    if(type==2&&bytes==512&&data!=dsp_brr_records)abort();
#endif
    return 1;
}
static void check(int ok){cases++;if(!ok){fprintf(stderr,"FAIL case %u response=%s\n",cases,response);exit(1);}}
static void run(const char *line){packets=0;response[0]=0;remote_process_request((const unsigned char *)line,strlen(line)+1,0xa00d0000);}
static void expect(const char *line,const char *part){run(line);check(strstr(response,part)!=NULL);}
/* Exercise the actual frame/idle hooks as the suspended assembly bridge does. */
static void advance(unsigned renders){
    for(unsigned i=0;i<renders;i++) {
        if(remote_paused)remote_control_idle(0xa00d0000);
        else remote_control_frame(0xa00d0000);
    }
}
static void pause_at(uint32_t target){
    char request[64];snprintf(request,sizeof(request),"s64 12345678 pause-at %u",(unsigned)target);
    expect(request," OK pause_at_render_frame_id=");
    check(remote_pause_pending&&remote_pause_target==target);
}
int main(void){
    remote_control_init();
    expect("s64 1234ABcd hello","S64 1234ABcd OK mode=emu protocol=1");
    check(strstr(response,"fps_claim=none")!=NULL);
    expect("s64 12345678 not_a_command","S64 12345678 ERR unknown_verb");
    expect("s64 1234567Z status","S64 00000000 ERR invalid_request");
    expect("s64 12345678 status unexpected","S64 12345678 ERR argument_count");
    const unsigned char embedded[]="s64 12345678 status\0x";
    remote_process_request(embedded,sizeof(embedded),0);check(strstr(response,"S64 12345678 ERR embedded_nul")!=NULL);
    unsigned char oversized[257];memset(oversized,'x',sizeof(oversized));memcpy(oversized,"s64 12345678 ",13);
    remote_process_request(oversized,sizeof(oversized),0);check(strstr(response,"S64 12345678 ERR packet_length")!=NULL);
    expect("s64 12345678 buttons 8000 3","OK buttons=32768 duration_guest_frames=3");
    check(remote_buttons==0x8000&&remote_button_frames==3&&joyxlh[0]==0x8000);
    expect("s64 12345678 buttons 8001 3","ERR invalid_buttons");
    expect("s64 12345678 buttons 8000 0","ERR invalid_buttons");
    expect("s64 12345678 buttons 8000 4294967295","ERR invalid_buttons");
    check(remote_button_frames==3);
    expect("s64 12345678 release","OK released=1");check(!remote_buttons&&!remote_button_frames&&!joyxlh[0]);
    native_diag_phase=1;
    expect("s64 12345678 pause","ERR capture_busy");
    expect("s64 12345678 frame","ERR capture_busy");
    expect("s64 12345678 sav","ERR capture_busy");
    expect("s64 12345678 menu","ERR capture_busy");check(!menu_calls);
    native_diag_phase=4;continuous_save_error_stage=3;continuous_save_error_code=6;
    continuous_save_sc64_status=0x40000000;continuous_save_data0=0x123;
    expect("s64 12345678 capture sd","ERR sd_unready");
    expect("s64 12345678 capture usb","OK capture_ready=1 sink=usb");
    check(native_diag_usb_only==1&&remote_arm_pending==1);
    check(continuous_save_error_stage==3&&continuous_save_data0==0x123);
    remote_arm_pending=0;fail_send=1;run("s64 12345678 capture usb");check(!remote_arm_pending);fail_send=0;
    native_diag_phase=0;continuous_save_sink_ready=1;
    expect("s64 12345678 capture sd","OK capture_ready=1 sink=sd");check(!native_diag_usb_only&&remote_arm_pending);
    remote_arm_pending=0;
    expect("s64 12345678 pause","OK paused=1 boundary=rsp_retired");check(remote_paused);
    expect("s64 12345678 capture usb","ERR paused");
    remote_guest_frames=70;remote_render_frames=35;remote_vi_count=99;remote_presentations=29;
    clock_value=0xfffffff0u;run("s64 12345678 profile");
    check(strstr(response,"guest_frame_id=70 render_frame_id=35 boot_tv_type=1 vi=99 new_presentations=29")!=NULL);
    clock_value=20;run("s64 12345678 status");check(strstr(response,"count_wraps_observed=1")!=NULL);
    remote_control_idle(0);check(remote_guest_frames==70&&remote_render_frames==35);
    frame_ready=0;expect("s64 12345678 frame","ERR frame_dp_busy");
    check(packets==1&&types[0]==1);frame_ready=1;
    expect("s64 12345678 frame","OK exported=frame width=280 height=240");
    check(packets==3&&types[0]==3&&sizes[0]==16&&types[1]==4&&sizes[1]==134400&&types[2]==1);
    expect("s64 12345678 sav","ERR capture_not_sealed");
    native_diag_snapshot_ready=1;native_diag_snapshot_sequence=42;
    for(unsigned i=0;i<sizeof(native_diag_snapshot);i++)native_diag_snapshot[i]=(unsigned char)(i*31);
    unsigned char old[32768];memcpy(old,native_diag_snapshot,sizeof(old));
    expect("s64 12345678 sav","OK exported=sav bytes=32768 immutable=1 sealed_id=42");
    check(packets==2&&types[0]==2&&sizes[0]==32768&&!memcmp(old,native_diag_snapshot,sizeof(old)));
    expect("s64 12345678 resume","OK paused=0");check(!remote_paused);
    expect("s64 12345678 step 1","ERR not_paused");
    expect("s64 12345678 step 0","ERR invalid_step");
    expect("s64 12345678 step 36001","ERR invalid_step");
    expect("s64 12345678 step 4294967295","ERR invalid_step");
    expect("s64 12345678 step -1","ERR invalid_step");
    expect("s64 12345678 step 1 extra","ERR invalid_step");
    expect("s64 12345678 pause-at 4294967296","ERR invalid_frame_id");
    expect("s64 12345678 pause-at -1","ERR invalid_frame_id");
    expect("s64 12345678 pause-at 36 extra","ERR invalid_frame_id");
    expect("s64 12345678 pause-at 35","ERR stale_frame_id");
    expect("s64 12345678 pause-at 34","ERR stale_frame_id");
    expect("s64 12345678 pause-at 36036","ERR frame_target_range");
    check(!remote_paused&&!remote_pause_pending&&remote_render_frames==35&&remote_guest_frames==70);
    pause_at(36035); /* The maximum accepted forward distance is inclusive. */
    expect("s64 12345678 resume","OK paused=0");check(!remote_pause_pending);
    pause_at(38);
    expect("s64 12345678 step 1","ERR not_paused");check(remote_pause_pending&&remote_pause_target==38);
    expect("s64 12345678 buttons 8000 4","OK buttons=32768 duration_guest_frames=4");
    advance(2);check(remote_render_frames==37&&!remote_paused&&remote_pause_pending);
    advance(1);check(remote_render_frames==38&&remote_paused&&!remote_pause_pending);
    advance(8);check(remote_render_frames==38&&remote_guest_frames==70&&remote_button_frames==4&&joyxlh[0]==0x8000);
    run("s64 12345678 status");check(strstr(response,"pause_pending=0 pause_at_render_frame_id=38 frame_control_max=36000")!=NULL);
    expect("s64 12345678 resume","OK paused=0");
    advance(2);check(remote_render_frames==40&&!remote_paused&&!remote_pause_pending);
    expect("s64 12345678 pause","OK paused=1");
    expect("s64 12345678 buttons 8000 3","OK buttons=32768 duration_guest_frames=3");
    expect_paused_ack=1;fail_send=1;run("s64 12345678 step 1");
    check(remote_paused&&!remote_pause_pending&&remote_render_frames==40&&paused_ack_checks==1);
    fail_send=0;
    expect("s64 12345678 step 1","OK step_renders=1 pause_at_render_frame_id=41 accepted_render_frame_id=40 pause_pending=1");
    expect_paused_ack=0;
    check(!remote_paused&&remote_pause_pending&&paused_ack_checks==2&&remote_button_frames==3&&joyxlh[0]==0x8000);
    advance(4);check(remote_render_frames==41&&remote_paused&&!remote_pause_pending&&remote_guest_frames==70);
    expect_paused_ack=1;
    expect("s64 12345678 step 3","OK step_renders=3 pause_at_render_frame_id=44 accepted_render_frame_id=41");
    expect_paused_ack=0;
    advance(2);check(remote_render_frames==43&&!remote_paused&&remote_pause_pending);
    advance(10);check(remote_render_frames==44&&remote_paused&&!remote_pause_pending);
    packets=0;response[0]=0;
    const unsigned char unavailable[]="s64 12345678 step 1";
    remote_process_request(unavailable,sizeof(unavailable),0);
    check(strstr(response,"ERR frame_unavailable")!=NULL&&remote_paused&&!remote_pause_pending);
    expect("s64 12345678 pause-at 47","ERR paused");check(remote_paused&&!remote_pause_pending);
    expect("s64 12345678 step 2","OK step_renders=2");
    expect("s64 12345678 pause","OK paused=1");check(!remote_pause_pending);
    expect("s64 12345678 step 2","OK step_renders=2");
    expect("s64 12345678 resume","OK paused=0");check(!remote_pause_pending);
    advance(3);check(remote_render_frames==47&&!remote_paused);
    pause_at(49);pause_at(51); /* Replacing a target cancels the older expiry. */
    fail_send=1;run("s64 12345678 pause-at 48");fail_send=0;
    check(remote_pause_pending&&remote_pause_target==51);
    expect("s64 12345678 release","OK released=1");check(remote_pause_pending);
    advance(3);check(remote_render_frames==50&&!remote_paused);
    advance(4);check(remote_render_frames==51&&remote_paused&&!remote_pause_pending);
    for(unsigned phase=1;phase<=3;phase++) {
        native_diag_phase=phase;
        expect("s64 12345678 step 1","ERR capture_busy");
        expect("s64 12345678 pause-at 52","ERR capture_busy");
        check(remote_paused&&!remote_pause_pending&&remote_render_frames==51);
    }
    native_diag_phase=0;remote_arm_pending=1;
    expect("s64 12345678 step 1","ERR capture_busy");
    expect("s64 12345678 pause-at 52","ERR capture_busy");
    expect("s64 12345678 pause","ERR capture_busy");
    remote_arm_pending=0;expect("s64 12345678 resume","OK paused=0");
    for(unsigned phase=1;phase<=3;phase++) {
        pause_at(remote_render_frames+1);native_diag_phase=phase;
        advance(1);check(!remote_paused&&!remote_pause_pending);
        native_diag_phase=0;
    }
    pause_at(remote_render_frames+2);
    fail_send=1;run("s64 12345678 capture sd");fail_send=0;
    check(remote_pause_pending&&!remote_arm_pending);
    expect("s64 12345678 capture sd","OK capture_ready=1 sink=sd");
    check(!remote_pause_pending&&remote_arm_pending);
    remote_arm_pending=0;advance(3);check(!remote_paused&&!remote_pause_pending);
    pause_at(remote_render_frames+1);remote_arm_pending=1;
    advance(1);check(!remote_paused&&!remote_pause_pending);remote_arm_pending=0;
    /* Only the fixture seeds counters, to test actual hook arithmetic at wrap. */
    remote_render_frames=UINT32_MAX-2;
    pause_at(0);advance(2);check(remote_render_frames==UINT32_MAX&&!remote_paused);
    advance(1);check(remote_render_frames==0&&remote_paused&&!remote_pause_pending);
    advance(10);check(remote_render_frames==0&&remote_guest_frames==70);
    expect("s64 12345678 resume","OK paused=0");
    expect("s64 12345678 pause-at 4294967295","ERR stale_frame_id");
    expect("s64 12345678 pause","OK paused=1");
    expect_paused_ack=1;
    expect("s64 12345678 step 2","OK step_renders=2 pause_at_render_frame_id=2 accepted_render_frame_id=0");
    expect_paused_ack=0;
    advance(5);check(remote_render_frames==2&&remote_paused&&!remote_pause_pending);
    expect("s64 12345678 step 36000","OK step_renders=36000 pause_at_render_frame_id=36002");
    advance(36005);check(remote_render_frames==36002&&remote_paused&&!remote_pause_pending);
    expect("s64 12345678 resume","OK paused=0");check(!remote_pause_pending);
    remote_render_frames=UINT32_MAX-1;
    expect("s64 12345678 pause","OK paused=1");
    expect_paused_ack=1;
    expect("s64 12345678 step 2","OK step_renders=2 pause_at_render_frame_id=0 accepted_render_frame_id=4294967294");
    expect_paused_ack=0;
    advance(5);check(remote_render_frames==0&&remote_paused&&!remote_pause_pending);
    expect("s64 12345678 resume","OK paused=0");
    pause_at(4);
    expect("s64 12345678 menu","OK transition_ready=menu outcome=pending");check(menu_calls==1);
    check(!remote_pause_pending);
#ifdef SODIUM64_AUDIO_OBSERVER
    remote_render_frames=10;remote_paused=0;remote_arm_pending=0;native_diag_phase=0;
    expect("s64 12345678 audio","ERR not_paused");check(packets==1);
    remote_paused=1;native_diag_phase=1;
    expect("s64 12345678 audio","ERR capture_busy");check(packets==1);
    native_diag_phase=0;dsp_pointer=3;
    expect("s64 12345678 audio","ERR audio_pointer");check(packets==1);
    dsp_pointer=8192;expect("s64 12345678 audio","ERR audio_pointer");
    dsp_pointer=4096;enabled=0x7f;dsp_audio_blocks=42;dsp_audio_idle=7;dsp_audio_full=2;
    dsp_audio_gap_max=123;dsp_audio_last_count=456;
#ifdef SODIUM64_DSP_KOFF_RELEASE
    dsp_release_steps=7;dsp_release_last=0x01018010;
#endif
    for(unsigned i=0;i<8192;i++)dsp_buffer[i]=(unsigned char)(i*17);
    for(unsigned i=0;i<128;i++)dsp_regs[i]=(unsigned char)i;
    unsigned char saved_audio[8192];memcpy(saved_audio,dsp_buffer,8192);
    expect("s64 12345678 audio extra","ERR argument_count");
    expect("s64 12345678 audio","OK exported=audio bytes=8192 pcm=s16be_stereo ring=1");
    check(packets==2&&sizes[0]==8192&&types[0]==2&&types[1]==1);
    check(strstr(response,"ring_head_bytes=4096 enabled=127 blocks=42 idle_before_submit=7 full_before_submit=2")!=NULL);
    check(strstr(response,"dspregs=00010203040506070809")!=NULL);
    check(strstr(response,"ai_programmed_dac_rate=1526 ai_init_clock_hz=48681812")!=NULL);
    check(!memcmp(saved_audio,dsp_buffer,8192)&&dsp_audio_blocks==42);
#ifdef SODIUM64_DSP_KOFF_RELEASE
    check(dsp_release_steps==7&&dsp_release_last==0x01018010);
#endif
    fail_send=1;run("s64 12345678 audio");check(packets==0);fail_send=0;
    expect("s64 12345678 audio-reset","OK audio_reset=1");
    check(packets==1&&!dsp_audio_blocks&&!dsp_audio_idle&&!dsp_audio_full&&!dsp_audio_gap_max&&!dsp_audio_last_count);
#ifdef SODIUM64_DSP_KOFF_RELEASE
    check(!dsp_release_steps&&!dsp_release_last);
#endif
    check(dsp_pointer==4096&&enabled==0x7f&&!memcmp(saved_audio,dsp_buffer,8192));
    remote_paused=0;
#endif
#ifdef SODIUM64_BRR_OBSERVER
    remote_render_frames=10;remote_paused=0;remote_arm_pending=0;native_diag_phase=0;
    expect("s64 12345678 audio-brr","ERR not_paused");check(packets==1);
    remote_paused=1;native_diag_phase=1;
    expect("s64 12345678 audio-brr","ERR capture_busy");check(packets==1);
    native_diag_phase=0;remote_arm_pending=1;
    expect("s64 12345678 audio-brr","ERR capture_busy");remote_arm_pending=0;
    remote_render_frames=0;expect("s64 12345678 audio-brr","ERR frame_unavailable");
    remote_render_frames=10;
    dsp_brr_next=32;expect("s64 12345678 audio-brr","ERR brr_index");
    dsp_brr_next=31;dsp_brr_count=12345;
    for(unsigned i=0;i<512;i++)dsp_brr_records[i]=(unsigned char)(i*19);
    unsigned char saved_brr[512];memcpy(saved_brr,dsp_brr_records,512);
    expect("s64 12345678 audio-brr extra","ERR argument_count");
    expect("s64 12345678 audio-brr","OK exported=audio-brr bytes=512 stride=16 slots=32 endian=be");
    check(packets==2&&types[0]==2&&sizes[0]==512);
    check(strstr(response,"next=31 completed_mod32=12345 valid_records=32")!=NULL);
    check(dsp_brr_next==31&&dsp_brr_count==12345&&!memcmp(saved_brr,dsp_brr_records,512));
    dsp_brr_next=0;dsp_brr_count=0;
    expect("s64 12345678 audio-brr","valid_records=0");
    dsp_brr_count=1;expect("s64 12345678 audio-brr","valid_records=1");
    fail_send=1;run("s64 12345678 audio-brr");check(packets==0);fail_send=0;
    remote_paused=0;
#endif
    /* Random text and adversarial bounds exercise the same production parser.
     * Each case must remain within buffers and may never boot or arm. */
    remote_arm_pending=0;unsigned before=menu_calls;
    uint32_t rng=1;
    for(unsigned k=0;k<1000;k++){
        unsigned char fuzz[256];unsigned n=k%256;
        for(unsigned i=0;i<n;i++){rng=rng*1664525u+1013904223u;fuzz[i]=(unsigned char)(rng>>24);}
        remote_process_request(fuzz,n,0);
    }
    check(menu_calls==before&&!remote_arm_pending);
    printf("REMOTE_CONTROL PASS cases=%u fuzz=1000 production_parser=1 hardware_mocked=1\n",cases);
    return 0;
}
