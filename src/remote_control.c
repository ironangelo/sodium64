/* SPDX-License-Identifier: GPL-3.0-or-later
 * Retired-frame bench extraction from d7a071a2 remote_control.c.
 * No recorder, SD writer, scene serializer, DSP backend or renderer experiment.
 * SC64 register/PI/USB and IPL3 return operations retain the qualified bridge.
 */
#include "remote_control.h"
#ifdef REMOTE_CONTROL_HOST
volatile uint32_t remote_guest_frames,remote_render_frames,remote_vi_count,remote_presentations;
volatile uint32_t remote_buttons,remote_button_frames,remote_paused;
volatile uint32_t remote_pause_pending,remote_pause_target;
#endif
uint32_t remote_boot_tv_type=1,remote_boot_ram_bytes;
extern volatile uint16_t joyxlh[4];
extern unsigned char apu_clock,audio_set,precision_set,skipped_set,underclk_set;
extern unsigned char dsp_buffer[8192],dsp_regs[128],enabled;
extern uint16_t dsp_pointer;
#ifdef REMOTE_CONTROL_HOST
static uint32_t poll_calls,poll_total,poll_max,transport_error,menu_error,count_last,count_wraps;
static int present;
static unsigned reply_length;
#else
/* Cold boot clears this admitted lease before any frame/VI hook can run. */
#define BENCH_WORD(n) (((uint32_t *)0x80441c60u)[n])
#define poll_calls BENCH_WORD(0)
#define poll_total BENCH_WORD(1)
#define poll_max BENCH_WORD(2)
#define transport_error BENCH_WORD(3)
#define menu_error BENCH_WORD(4)
#define count_last BENCH_WORD(5)
#define count_wraps BENCH_WORD(6)
#define present BENCH_WORD(7)
#define reply_length BENCH_WORD(8)
#define rx_discard_until BENCH_WORD(9)
#define raw_identifier BENCH_WORD(10)
#define last_command BENCH_WORD(11)
#define last_sc_status BENCH_WORD(12)
#define last_data0 BENCH_WORD(13)
#endif
enum { USB_CART=0x13800000,RX_CART=0x1ffe0000,FRAME_BYTES=280*240*2,
       CMD_TIMEOUT=REMOTE_COUNT_HZ/10,DMA_TIMEOUT=REMOTE_COUNT_HZ/5,USB_TIMEOUT=REMOTE_COUNT_HZ*2 };
#ifdef REMOTE_CONTROL_HOST
static char reply[1536];
extern uint32_t remote_host_count(void);
extern int remote_host_send(unsigned,const void *,unsigned);
extern int remote_host_menu(void);
extern int remote_host_frame_ready(void);
static uint32_t count(void) {return remote_host_count();}
static int send_packet(unsigned t,const void *p,unsigned n) {return remote_host_send(t,p,n);}
static int reboot_menu(void) {return remote_host_menu();}
#else
/* The exact8MiB boot guard in the assembly bridge precedes every access.
 * This explicit8KiB upper lease is disjoint from all base4MiB owners and
 * R61's separate400000..4340a0 /438000..440000 owners. Nothing is loaded or
 * cleared there by IPL3. Low/high32-byte guards belong to this lease.
 */
#define request_buffer ((unsigned char *)0x80441220u)
#define transfer_buffer ((unsigned char *)0x80441420u)
#define reply ((char *)0x80441620u)
static volatile uint32_t *const sc=(volatile uint32_t *)0xbfff0000;
static void transport_failure(unsigned e) {if(!transport_error)transport_error=e;}
static unsigned char *uncached(void *p) {return (unsigned char *)((uintptr_t)p|0xa0000000u);}
static int owner_guards_valid(void) {
    volatile uint32_t *lo=(volatile uint32_t *)0xa0440000u;
    volatile uint32_t *hi=(volatile uint32_t *)0xa0441fe0u;
    for(unsigned i=0;i<8;i++)if(lo[i]!=0x55363447u||hi[i]!=0x55363447u)return 0;
    return 1;
}
static uint32_t count(void) {
    uint32_t n; __asm__ volatile("mfc0 %0,$9":"=r"(n)); return n;
}

static int sc_io(unsigned index,uint32_t *value,int write) {
    uint32_t saved,status,start=count();
    __asm__ volatile("mfc0 %0,$12":"=r"(saved));
    status=saved&~1u;
    __asm__ volatile("mtc0 %0,$12\n nop\n nop"::"r"(status):"memory");
    volatile uint32_t *pi_status=(volatile uint32_t *)0xa4600010;
    while(*pi_status&3) {
        if((uint32_t)(count()-start)>=CMD_TIMEOUT) {
            __asm__ volatile("mtc0 %0,$12\n nop\n nop"::"r"(saved):"memory");
            transport_failure(7);return 0;
        }
    }
    __asm__ volatile("sync":::"memory");
    if(write)sc[index]=*value;else *value=sc[index];
    __asm__ volatile("sync":::"memory");
    __asm__ volatile("mtc0 %0,$12\n nop\n nop"::"r"(saved):"memory");
    return 1;
}

static int sc_read(unsigned index,uint32_t *value) {return sc_io(index,value,0);}

static int sc_write(unsigned index,uint32_t value) {return sc_io(index,&value,1);}

static int command(unsigned id,uint32_t a,uint32_t b,uint32_t result[2]) {
    if (transport_error) return 0;
    last_command=id;
    uint32_t start=count();
    if(!sc_read(0,&last_sc_status))return 0;
    while(last_sc_status&0x80000000u) {
        if((uint32_t)(count()-start)>=CMD_TIMEOUT) {
            (void)sc_read(1,&last_data0);transport_failure(1);return 0;
        }
        if(!sc_read(0,&last_sc_status))return 0;
    }
    if(!sc_write(1,a)||!sc_write(2,b)||!sc_write(0,id))return 0;
    start=count();
    if(!sc_read(0,&last_sc_status))return 0;
    while(last_sc_status&0x80000000u) {
        if((uint32_t)(count()-start)>=CMD_TIMEOUT) {
            (void)sc_read(1,&last_data0);transport_failure(2);return 0;
        }
        if(!sc_read(0,&last_sc_status))return 0;
    }
    if(!sc_read(1,&last_data0))return 0;
    if(result) { result[0]=last_data0;if(!sc_read(2,&result[1]))return 0; }
    if(last_sc_status&0x40000000u) { transport_failure(3);return 0; }
    return 1;
}

static int wait_io(uint32_t address,uint32_t mask,uint32_t wanted,uint32_t ticks) {
    volatile uint32_t *p=(volatile uint32_t *)(uintptr_t)address;
    uint32_t start=count();
    while((*p&mask)!=wanted) {
        if((uint32_t)(count()-start)>=ticks) return 0;
    }
    return 1;
}

static int pi_transfer(void *ram,uint32_t cart,unsigned bytes,int to_cart) {
    volatile uint32_t *pi=(volatile uint32_t *)0xa4600000;
    if(!bytes || !wait_io(0xa4600010,3,0,DMA_TIMEOUT)) {transport_failure(4);return 0;}
    __asm__ volatile("sync":::"memory");
    pi[0]=(uint32_t)(uintptr_t)ram&0x1fffffffu;pi[1]=cart;
    pi[to_cart?2:3]=bytes-1;
    if(!wait_io(0xa4600010,3,0,DMA_TIMEOUT) || (pi[4]&4)) {transport_failure(5);return 0;}
    __asm__ volatile("sync":::"memory");
    return 1;
}

static int wait_usb(unsigned id) {
    uint32_t r[2],start=count();
    do {
        if(!command(id,0,0,r)) return 0;
        if(!(r[0]&0x80000000u)) return 1;
    } while((uint32_t)(count()-start)<USB_TIMEOUT);
    transport_failure(6); return 0;
}

static int send_packet(unsigned type,const void *data,unsigned bytes) {
    uint32_t r[2];
    if(!present || bytes>FRAME_BYTES || !wait_usb('U')) return 0;
    if(!command('C',1,1,r)) return 0;
    uint32_t previous=r[1];
    const unsigned char *src=data;
    unsigned done=0;
    while(done<bytes) {
        unsigned n=bytes-done; if(n>512)n=512;
        unsigned char *dst=uncached(transfer_buffer);
        for(unsigned i=0;i<n;i++)dst[i]=src[done+i];
        if(n&1)dst[n]=0;
        if(!pi_transfer(dst,USB_CART+done,(n+1)&~1u,1))return 0;
        done+=n;
    }
    if(!command('C',1,previous,0))return 0;
    return command('M',USB_CART,(type<<24)|bytes,0)&&wait_usb('U');
}

extern unsigned char remote_reboot_start[],remote_reboot_end[];
extern void remote_reboot_jump(uint32_t);
static int reboot_menu(void) {
    volatile uint32_t *sp=(volatile uint32_t *)0xa4040000;
    volatile uint32_t *dp=(volatile uint32_t *)0xa4100000;
    volatile uint32_t *vi=(volatile uint32_t *)0xa4400000;
    volatile uint32_t *ai=(volatile uint32_t *)0xa4500000;
    volatile uint32_t *pi=(volatile uint32_t *)0xa4600000;
    uint32_t r[2],tv=remote_boot_tv_type;
    uint32_t status;
    __asm__ volatile("mfc0 %0,$12":"=r"(status));
    status &= ~1u;
    __asm__ volatile("mtc0 %0,$12\n nop\n nop"::"r"(status):"memory");
    if(tv>2)tv=1;
    if(!wait_io(0xa4040010,1,1,DMA_TIMEOUT)||!wait_io(0xa4040018,1,0,DMA_TIMEOUT)) {menu_error=1;return 0;}
    if(!wait_io(0xa410000c,0x170,0,DMA_TIMEOUT)) {menu_error=2;return 0;}
    if(!wait_io(0xa4800018,3,0,DMA_TIMEOUT)) {menu_error=3;return 0;}
    if(!wait_io(0xa4600010,3,0,DMA_TIMEOUT)) {menu_error=4;return 0;}
    if(!wait_io(0xa450000c,0xc0000000u,0,REMOTE_COUNT_HZ)) {menu_error=5;return 0;}
    ai[2]=0;
    ai[0]=0;ai[1]=0;ai[3]=0;
    sp[4]=0x00aaaaae;sp[7]=0;*(volatile uint32_t *)0xa4080000=0;
    dp[3]=0x15; /* clear XBUS, freeze and flush only after natural idle */
    /* The SC64 bootloader waits again for scanline zero after loading the
     * menu. VI_CURRENT writes only acknowledge IRQs. Keep sync timings alive
     * across that second boot, otherwise a nonzero counter can stop forever. */
    if(!wait_io(0xa4400010,0xfffffffeu,0,DMA_TIMEOUT)) {menu_error=8;return 0;}
    vi[0]=0;vi[1]=0;vi[2]=0;vi[3]=0x3ff;vi[4]=0;
    pi[4]=3;*(volatile uint32_t *)0xa4800018=0;
    /* Disable old save writeback by reselecting its existing save type. */
    if(!command('c',6,0,r)||!command('C',6,r[1],0)||
       !command('i',0,0,0)||!command('C',5,0,0)) {menu_error=6;return 0;}
    unsigned n=(unsigned)(remote_reboot_end-remote_reboot_start);
    volatile uint32_t *imem=(volatile uint32_t *)0xa4001000;
    const uint32_t *blob=(const uint32_t *)remote_reboot_start;
    for(unsigned i=0;i<n/4;i++)imem[i]=blob[i];
    __asm__ volatile("sync":::"memory");
    if(!command('C',0,1,0)) {menu_error=7;return 0;}
    pi[5]=255;pi[6]=255;pi[7]=15;pi[8]=3;
    uint32_t config=*(volatile uint32_t *)0xb0000000;
    pi[5]=config&255;pi[6]=(config>>8)&255;
    pi[7]=(config>>16)&15;pi[8]=(config>>20)&3;
    volatile uint32_t *dmem=(volatile uint32_t *)0xa4000000;
    volatile uint32_t *cart=(volatile uint32_t *)0xb0000000;
    for(unsigned i=16;i<1024;i++)dmem[i]=cart[i];
    /* Writeback/invalidate all D lines and invalidate I lines before CPU IPL3.
     * New boot runs independently from replaced SDRAM and old JIT pages. */
    for(uint32_t p=0x80000000;p<0x80002000;p+=16)
        __asm__ volatile("cache 1,0(%0)"::"r"(p):"memory");
    for(uint32_t p=0x80000000;p<0x80004000;p+=32)
        __asm__ volatile("cache 0,0(%0)"::"r"(p):"memory");
    __asm__ volatile("sync":::"memory");
    remote_reboot_jump(tv);
    return 0;
}
static unsigned receive(void) {
    uint32_t r[2];
    if(!command('u',0,0,r) || (r[0]&0x80000000u) || !r[1])return 0;
    unsigned bytes=r[1]&0xffffffu, n=bytes;
    if(rx_discard_until && (int32_t)(count()-rx_discard_until)<0)return 0;
    rx_discard_until=0;
    if(n>REMOTE_REQUEST_MAX)n=REMOTE_REQUEST_MAX;
    if(!command('m',RX_CART,n,0)||!wait_usb('u')||
       !pi_transfer(uncached(request_buffer),RX_CART,(n+1)&~1u,0))return 0;
    if(bytes>n)rx_discard_until=count()+REMOTE_COUNT_HZ*2;
    /* Binary traffic is never interpreted or installed. */
    if((r[0]&255)!=1)return 0;
    return bytes>n?REMOTE_REQUEST_MAX+1:n;
}

#endif
static int eq(const char *a,const char *b) {
    while(*a&&*a==*b){a++;b++;}return *a==*b;
}

static void append(const char *p) {
    while(*p&&reply_length<1536u-2)reply[reply_length++]=*p++;
}

static void number(uint32_t n) {
    char digits[10];unsigned k=0;
    do{digits[k++]=(char)('0'+n%10);n/=10;}while(n);
    while(k&&reply_length<1536u-2)reply[reply_length++]=digits[--k];
}

static void field(const char *name,uint32_t value) {append(name);number(value);}

static void prefix(const char *id,int ok) {
    reply_length=0;append("S64 ");append(id);append(ok?" OK":" ERR ");
}

static int finish(void) {append("\n");return send_packet(1,reply,reply_length);}

static void error(const char *id,const char *code) {prefix(id,0);append(code);(void)finish();}

static int hex(const char *p,unsigned digits,uint32_t *value) {
    uint32_t n=0;
    for(unsigned i=0;i<digits;i++) {
        unsigned c=(unsigned char)p[i],v;
        if(!c)return 0;
        if(c>='0'&&c<='9')v=c-'0';
        else if(c>='a'&&c<='f')v=c-'a'+10;
        else if(c>='A'&&c<='F')v=c-'A'+10;
        else return 0;
        n=(n<<4)|v;
    }
    if(p[digits])return 0;
    *value=n;return 1;
}

static int decimal(const char *p,uint32_t *value,uint32_t limit) {
    uint32_t n=0;if(!*p)return 0;
    for(;*p;p++) {
        unsigned v=(unsigned char)*p-'0';
        if(v>9 || n>limit/10 || (n==limit/10 && v>limit%10))return 0;
        n=n*10+v;
    }
    *value=n;return 1;
}

static void cancel_pause_target(void) {
    remote_pause_pending=0;remote_pause_target=0;
}

static void status(const char *id) {
    uint32_t now=count();if(now<count_last)count_wraps++;count_last=now;
    prefix(id,1);append(" mode=emu protocol=1 build=master-usb-bench capabilities=pause,pause-at,step,resume,buttons,release,frame,audio,menu");
    field(" count32=",now);field(" count_hz=",REMOTE_COUNT_HZ);field(" count_wraps_observed=",count_wraps);
    field(" guest_frame_id=",remote_guest_frames);field(" render_frame_id=",remote_render_frames);
    field(" vi=",remote_vi_count);field(" new_presentations=",remote_presentations);field(" paused=",remote_paused);
    field(" apu_clock=",apu_clock);field(" skipped_set=",skipped_set);field(" audio_set=",audio_set);field(" precision_set=",precision_set);
    field(" input_buttons=",remote_buttons);field(" input_remaining=",remote_button_frames);
    field(" pause_pending=",remote_pause_pending);field(" pause_at_render_frame_id=",remote_pause_target);
    field(" usb_poll_calls=",poll_calls);field(" usb_poll_count_total_mod32=",poll_total);field(" usb_poll_count_max=",poll_max);
    field(" transport_error=",transport_error);field(" menu_error=",menu_error);field(" boot_ram_bytes=",remote_boot_ram_bytes);
    append(" metric_provenance=cp0_count,guest_boundary,rsp_retired,vi_irq,vi_origin_publish fps_claim=none");(void)finish();
}
void remote_process_request(const unsigned char *request,size_t bytes,uint32_t retired_framebuffer) {
    char line[REMOTE_REQUEST_MAX],*tokens[6];unsigned nt=0;
    char request_id[9];const char *id="00000000";uint32_t unused;
    /* Recover only a validated fixed-width ID before rejecting a packet, so
     * malformed arguments still receive their caller's matching ERR. */
    if(bytes>=13&&request[0]=='s'&&request[1]=='6'&&request[2]=='4'&&request[3]==' '&&request[12]==' ') {
        for(unsigned i=0;i<8;i++)request_id[i]=(char)request[4+i];
        request_id[8]=0;
        if(hex(request_id,8,&unused))id=request_id;
    }
    if(!bytes||bytes>REMOTE_REQUEST_MAX){error(id,"packet_length");return;}
    unsigned len=0;
    for(size_t i=0;i<bytes;i++) {
        unsigned c=request[i];
        if(!c) {
            for(size_t j=i+1;j<bytes;j++)if(request[j]){error(id,"embedded_nul");return;}
            break;
        }
        if(c=='\n'||c=='\r') {
            for(size_t j=i+1;j<bytes;j++)if(request[j]&&request[j]!='\n'&&request[j]!='\r') {
                error(id,"trailing_data");return;
            }
            break;
        }
        if(c<32||c>126||len>=sizeof(line)-1){error(id,"invalid_text");return;}
        line[len++]=(char)c;
    }
    line[len]=0;
    char *p=line;
    while(*p) {
        while(*p==' ')p++;
        if(!*p)break;
        if(nt==6){error(id,"argument_count");return;}
        tokens[nt++]=p;
        while(*p&&*p!=' ')p++;
        if(*p)*p++=0;
    }
    if(nt<3||!eq(tokens[0],"s64")||!hex(tokens[1],8,&unused)) {error(id,"invalid_request");return;}
    id=tokens[1];const char *verb=tokens[2];

    if(eq(verb,"hello")||eq(verb,"status")) {
        if(nt!=3){error(id,"argument_count");return;}status(id);return;
    }
    if(menu_error&&!eq(verb,"menu")) {error(id,"transition_failed_requires_reset");return;}
    if(eq(verb,"pause-at")||eq(verb,"step")) {
        int step=eq(verb,"step");uint32_t value,target;
        if(nt!=4||!decimal(tokens[3],&value,step?REMOTE_FRAME_CONTROL_MAX:UINT32_MAX)||
           (step&&!value)) {error(id,step?"invalid_step":"invalid_frame_id");return;}
        if(menu_error){error(id,"transition_failed_requires_reset");return;}
        if(step) {
            if(!remote_paused){error(id,"not_paused");return;}
            if(!retired_framebuffer){error(id,"frame_unavailable");return;}
            target=remote_render_frames+value;
        } else {
            if(remote_paused){error(id,"paused");return;}
            target=value;
            uint32_t delta=target-remote_render_frames;
            if(!delta||delta>=0x80000000u){error(id,"stale_frame_id");return;}
            if(delta>REMOTE_FRAME_CONTROL_MAX){error(id,"frame_target_range");return;}
        }
        prefix(id,1);
        if(step)field(" step_renders=",value);
        field(" pause_at_render_frame_id=",target);
        field(" accepted_render_frame_id=",remote_render_frames);
        append(" pause_pending=1");
        /* The bridge cannot leave its retired pause until this ACK succeeds.
         * Keep buttons and their guest-frame duration under the existing hook. */
        if(finish()) {
            remote_pause_target=target;remote_pause_pending=1;
            if(step) {
                remote_paused=0;
            }
        }
        return;
    }
    if(eq(verb,"buttons")) {
        uint32_t mask,frames;
        if(nt!=5||!hex(tokens[3],4,&mask)||!decimal(tokens[4],&frames,36000u)||!frames||(mask&15)) {
            error(id,"invalid_buttons");return;
        }
        remote_buttons=mask;remote_button_frames=frames;
        joyxlh[0]=(uint16_t)mask;
        prefix(id,1);field(" buttons=",mask);field(" duration_guest_frames=",frames);
        field(" accepted_guest_frame_id=",remote_guest_frames);(void)finish();return;
    }
    if(eq(verb,"release")) {
        if(nt!=3){error(id,"argument_count");return;}
        remote_buttons=0;remote_button_frames=0;
        joyxlh[0]=0;
        prefix(id,1);append(" released=1");(void)finish();return;
    }

    if(nt!=3){error(id,"argument_count");return;}
    if(eq(verb,"resume")) {
        cancel_pause_target();remote_paused=0;prefix(id,1);append(" paused=0");
        field(" retired_frame_id=",remote_render_frames);(void)finish();return;
    }
    if(eq(verb,"pause")) {
        cancel_pause_target();remote_paused=1;remote_buttons=remote_button_frames=0;joyxlh[0]=0;
        prefix(id,1);append(" paused=1 boundary=rsp_retired");field(" retired_frame_id=",remote_render_frames);(void)finish();return;
    }
    if(eq(verb,"frame")) {
        if(!remote_paused){error(id,"not_paused");return;}
        if(!retired_framebuffer){error(id,"frame_unavailable");return;}
#ifdef REMOTE_CONTROL_HOST
        int ready=remote_host_frame_ready();
#else
        int ready=wait_io(0xa410000c,0x170,0,DMA_TIMEOUT);
#endif
        if(!ready){error(id,"frame_dp_busy");return;}
        unsigned char header[16]={0,0,0,4,0,0,0,2,0,0,1,24,0,0,0,240};
        if(!send_packet(3,header,16)||!send_packet(4,(const void *)(uintptr_t)retired_framebuffer,FRAME_BYTES)) {error(id,"usb_export_failed");return;}
        prefix(id,1);append(" exported=frame width=280 height=240 pixel_bytes=2 boundary=rsp_retired");
        field(" render_frame_id=",remote_render_frames);(void)finish();return;
    }
    if(eq(verb,"audio")) {
        if(!remote_paused){error(id,"not_paused");return;}
        if(!retired_framebuffer||!remote_render_frames){error(id,"frame_unavailable");return;}
        if(dsp_pointer>=8192||(dsp_pointer&3)){error(id,"audio_pointer");return;}
#ifdef REMOTE_CONTROL_HOST
        const void *pcm=dsp_buffer;
#else
        const void *pcm=uncached(dsp_buffer);
#endif
        if(!send_packet(2,pcm,8192)){error(id,"usb_export_failed");return;}
        prefix(id,1);append(" exported=audio bytes=8192 pcm=s16be_stereo ring=1");
        field(" ring_head_bytes=",dsp_pointer);field(" enabled=",enabled);field(" render_frame_id=",remote_render_frames);
        append(" dspregs=");static const char digits[]="0123456789abcdef";
        for(unsigned i=0;i<128;i++){char b[3]={digits[dsp_regs[i]>>4],digits[dsp_regs[i]&15],0};append(b);}
        append(" provenance=paused_dsp_ring_not_dac no_audio_fidelity_claim=1");(void)finish();return;
    }
    if(!eq(verb,"menu")){error(id,"unknown_verb");return;}
    cancel_pause_target();remote_buttons=remote_button_frames=0;remote_paused=1;joyxlh[0]=0;
    prefix(id,1);append(" transition_ready=menu outcome=pending");if(finish()&&!reboot_menu())remote_paused=1;
}

void remote_control_init(void) {
    count_last=count();cancel_pause_target();
    /* Same full-rate diagnostic selection as existing HW_PROFILE, before JIT. */
    apu_clock=21;underclk_set=0;skipped_set=0;audio_set=4;precision_set=8;
#ifdef REMOTE_CONTROL_HOST
    present=1;
#else
    if(!sc_write(4,0)||!sc_write(4,0x5f554e4c)||!sc_write(4,0x4f434b5f)||!sc_read(3,&raw_identifier))return;
    present=raw_identifier==0x53437632;
#endif
}
void remote_control_frame(uint32_t framebuffer) {
#ifndef REMOTE_CONTROL_HOST
    if(!owner_guards_valid()){transport_failure(9);remote_paused=1;return;}
#endif
    remote_render_frames++;
    if(remote_pause_pending&&remote_render_frames==remote_pause_target){remote_pause_pending=0;remote_paused=1;}
    if(!present||transport_error)return;
    uint32_t start=count();
#ifndef REMOTE_CONTROL_HOST
    unsigned n=receive();if(n)remote_process_request(uncached(request_buffer),n,framebuffer);
#else
    (void)framebuffer;
#endif
    uint32_t delta=count()-start;poll_calls++;poll_total+=delta;if(delta>poll_max)poll_max=delta;
}
void remote_control_idle(uint32_t framebuffer) {
    uint32_t start=count();
#ifndef REMOTE_CONTROL_HOST
    if(!owner_guards_valid()){transport_failure(9);return;}
    if(present&&!transport_error){unsigned n=receive();if(n)remote_process_request(uncached(request_buffer),n,framebuffer);}
    while((uint32_t)(count()-start)<REMOTE_COUNT_HZ/120){}
#else
    (void)framebuffer;
#endif
    uint32_t delta=count()-start;poll_calls++;poll_total+=delta;if(delta>poll_max)poll_max=delta;
}
