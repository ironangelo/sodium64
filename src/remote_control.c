/* SPDX-License-Identifier: GPL-3.0-or-later
 * Opt-in SC64 bench, not a ROM uploader. Commands run at the natural retired
 * RSP frame boundary; no renderer, guest timing, or arithmetic policy changes.
 * Registers and command arguments follow sw/controller + libdragon/src/usb.c.
 */
#include "remote_control.h"
#include "../tools/sc64-diagnostic-save/recorder_runtime_abi.h"
#if SODIUM64_REMOTE_SECTION_OBSERVER || defined(SODIUM64_RDP_MATH_PROBE)
/* Use the exact arena/DMEM ABI selected by this build's diagnostic flags. */
#include "defines.h"
_Static_assert(SECTION_SIZE==64,"section observer requires the queued 64-byte ABI");
#ifndef REMOTE_CONTROL_HOST
extern volatile uint8_t queue_id;
#endif
#endif

volatile uint32_t remote_guest_frames, remote_render_frames;
volatile uint32_t remote_vi_count, remote_presentations;
volatile uint32_t remote_buttons, remote_button_frames;
volatile uint32_t remote_paused, remote_arm_pending;
volatile uint32_t remote_pause_pending, remote_pause_target;
/* Filled by main.S before Sodium replaces the IPL3 boot-info in SP DMEM. */
volatile uint32_t remote_boot_tv_type=1;
extern volatile uint16_t joyxlh[4];
static uint32_t poll_calls, poll_total, poll_max, transport_error;
static uint32_t menu_error;
static uint32_t count_last, count_wraps;
#ifndef REMOTE_CONTROL_HOST
static uint32_t rx_discard_until;
static uint32_t raw_identifier, last_command, last_sc_status, last_data0;
#endif
static int present;
#ifndef REMOTE_CONTROL_HOST
static unsigned char request_buffer[REMOTE_REQUEST_MAX] __attribute__((aligned(16)));
static unsigned char transfer_buffer[512] __attribute__((aligned(16)));
#endif
static char reply[1536];
static unsigned reply_length;
enum { USB_CART = 0x13800000, RX_CART = 0x1ffe0000, FRAME_BYTES = 280*240*2,
       CMD_TIMEOUT = REMOTE_COUNT_HZ/10, DMA_TIMEOUT = REMOTE_COUNT_HZ/5,
       USB_TIMEOUT = REMOTE_COUNT_HZ*2,
       MAILBOX_CART = 0x08007f80, MAILBOX_TIMEOUT = REMOTE_COUNT_HZ/200 };

#ifdef REMOTE_CONTROL_HOST
extern uint32_t remote_host_count(void);
extern int remote_host_send(unsigned type,const void *data,unsigned bytes);
extern int remote_host_menu(void);
extern int remote_host_frame_ready(void);
static uint32_t count(void) { return remote_host_count(); }
static int send_packet(unsigned type,const void *data,unsigned bytes) {
    return remote_host_send(type,data,bytes);
}
static int reboot_menu(void) { return remote_host_menu(); }
#else
static volatile uint32_t *const sc = (volatile uint32_t *)0xbfff0000;
static uint32_t count(void) {
    uint32_t n; __asm__ volatile("mfc0 %0,$9":"=r"(n)); return n;
}
static unsigned char *uncached(void *p) {
    return (unsigned char *)((uintptr_t)p|0xa0000000u);
}
/* One-shot diagnostic mailbox, physical 08007f80 / host 03fe7f80, 64 bytes.
 * This tail is outside the guest's first 8 KiB SRAM and remains mapped even
 * when SC64 registers/data BRAM are locked. Never write during capture.
 * Big-endian u32: S64R, version, phase (1 init / 2 first frame / 3 failure),
 * present, error, raw identifier, render frames, poll calls, last command,
 * SC status, DATA0, PI status, Count, zero, zero, additive checksum.
 * Checksum is committed before the signature; interrupted writes stay invalid.
 * No mailbox traffic runs while recording, sealing or committing a capture. */
static void mailbox_publish(unsigned phase) {
    if(native_diag_phase>=1 && native_diag_phase<=3)return;
    uint32_t start=count();
    volatile uint32_t *pi_status=(volatile uint32_t *)0xa4600010;
    volatile uint32_t *mailbox=(volatile uint32_t *)(uintptr_t)(MAILBOX_CART|0xa0000000u);
    uint32_t words[16]={0x53363452u,1,phase,(uint32_t)present,transport_error,
        raw_identifier,remote_render_frames,poll_calls,last_command,last_sc_status,
        last_data0,*pi_status,count(),0,0,0};
    uint32_t sum=0;
    for(unsigned i=0;i<15;i++)sum+=words[i];
    words[15]=0u-sum;
    /* Invalidate first, then commit magic last. Every PIO word shares one
     * total 5 ms budget; this path neither retries nor changes transport state. */
    for(unsigned i=0;i<17;i++) {
        while(*pi_status&3) {
            if((uint32_t)(count()-start)>=MAILBOX_TIMEOUT)return;
        }
        if((uint32_t)(count()-start)>=MAILBOX_TIMEOUT)return;
        if(!i)mailbox[0]=0;
        else if(i==16)mailbox[0]=words[0];
        else mailbox[i]=words[i];
        __asm__ volatile("sync":::"memory");
    }
    while(*pi_status&3) {
        if((uint32_t)(count()-start)>=MAILBOX_TIMEOUT)return;
    }
}
static void transport_failure(unsigned error) {
    if(transport_error)return;
    transport_error=error;
    mailbox_publish(3);
}
/* PI PIO writes are asynchronous. Serialize every SC64 register access,
 * including the unlock keys, as libdragon's io_read/io_write do. Keep IRQs
 * masked between checking PI idle and issuing PIO so DMA cannot interleave. */
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
/* A timed-out engine is never reused: ownership of its prior operation is
 * unknown. No unbounded SC64, PI, SP, DP, SI, AI or USB wait is permitted. */
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
extern void remote_reboot_jump(uint32_t tv);
/* Port of menu src/boot/boot.c and reboot.S. All C executes from RDRAM;
 * the final reboot receiver resides in SP IMEM before cart remapping. The
 * bootloader switch changes mapping only; it does NOT reset the CPU. */
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
    while(*p&&reply_length<sizeof(reply)-2)reply[reply_length++]=*p++;
}
static void number(uint32_t n) {
    char digits[10];unsigned k=0;
    do{digits[k++]=(char)('0'+n%10);n/=10;}while(n);
    while(k&&reply_length<sizeof(reply)-2)reply[reply_length++]=digits[--k];
}
static void field(const char *name,uint32_t value) {append(name);number(value);}
static void signed_field(const char *name,int32_t value) {
    append(name);
    if(value<0){append("-");number(0u-(uint32_t)value);}else number((uint32_t)value);
}
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
static int busy_capture(void) {
    return native_diag_phase==1||native_diag_phase==2||native_diag_phase==3;
}
static void cancel_pause_target(void) {
    remote_pause_pending=0;remote_pause_target=0;
}
#if SODIUM64_REMOTE_SECTION_OBSERVER
static int section_read(uint32_t address,unsigned bytes,uint32_t *value) {
#ifdef REMOTE_CONTROL_HOST
    return remote_host_section_read(address,bytes,value);
#else
    if(bytes==4)*value=*(volatile uint32_t *)(uintptr_t)address;
    else if(bytes==2)*value=*(volatile uint16_t *)(uintptr_t)address;
    else if(bytes==1)*value=*(volatile uint8_t *)(uintptr_t)address;
    else return 0;
    return 1;
#endif
}
static void section_hex_byte(unsigned value) {
    static const char digits[]="0123456789abcdef";
    char text[3]={digits[(value>>4)&15],digits[value&15],0};append(text);
}
static void sections(const char *id,uint32_t cursor,uint32_t retired_framebuffer) {
    uint32_t slot,sp_status,dma_busy,dma_full,dp_status,end,frame_end,framebuffer;
    uint32_t base,fixed,count_sections,previous=0,returned;
    if(!present||transport_error||menu_error){error(id,"sections_transport_unready");return;}
    if(busy_capture()||remote_arm_pending){error(id,"capture_busy");return;}
    if(!remote_paused){error(id,"not_paused");return;}
    if(!retired_framebuffer||!remote_render_frames){error(id,"frame_unavailable");return;}
#ifdef REMOTE_CONTROL_HOST
    slot=remote_host_section_queue_id();
#else
    slot=queue_id;
#endif
    if(slot!=0&&slot!=4){error(id,"sections_owner");return;}
    /* Only aligned words are read from DMEM, after HALT and settled SP DMA.
     * queue_id was advanced to the retired t6 slot before rsp_wait. CPU's
     * live PPU registers/producer pointers describe the following frame. */
    if(!section_read(0xa4040010u,4,&sp_status)||
       !section_read(0xa4040018u,4,&dma_busy)||
       !section_read(0xa4040014u,4,&dma_full)||
       !section_read(0xa410000cu,4,&dp_status)) {error(id,"sections_read_failed");return;}
    if(!(sp_status&1)||(sp_status&14)||dma_busy||dma_full){error(id,"sections_rsp_busy");return;}
    if(dp_status&0x170){error(id,"sections_dp_busy");return;}
    if(!section_read(DMEM(SECTION_PTR)+slot,4,&end)||
       !section_read(DMEM(FRAME_END)+slot,4,&frame_end)||
       !section_read(DMEM(FRAMEBUFFER)+slot,4,&framebuffer)) {error(id,"sections_read_failed");return;}
    base=slot?SECTION_QUEUE2:SECTION_QUEUE1;
    fixed=slot?HCOMP_ROW_FIXED_QUEUE2:HCOMP_ROW_FIXED_QUEUE1;
    if(end<=base||end>base+0x5000u||(end-base)%SECTION_SIZE){error(id,"sections_owner");return;}
    if(framebuffer!=retired_framebuffer){error(id,"sections_framebuffer");return;}
    if(!frame_end||frame_end>240){error(id,"sections_geometry");return;}
    count_sections=(end-base)/SECTION_SIZE;
    if(cursor>count_sections){error(id,"sections_cursor");return;}
    /* Verify all historical bounds before returning a page, so the final
     * consumed section certifies the exact frame end rather than stale RAM. */
    for(uint32_t i=0;i<count_sections;i++) {
        uint32_t bound;
        if(!section_read(base+i*SECTION_SIZE+63,1,&bound)){error(id,"sections_read_failed");return;}
        if(bound<previous||bound>frame_end){error(id,"sections_geometry");return;}
        previous=bound;
    }
    if(previous!=frame_end){error(id,"sections_geometry");return;}
    returned=count_sections-cursor;if(returned>6)returned=6;
    prefix(id,1);append(" sections=1");
    field(" render_frame_id=",remote_render_frames);
    field(" guest_boundary_id=",remote_guest_frames);
    field(" slot=",slot);field(" framebuffer=",framebuffer);
    field(" queue_base=",base);field(" queue_end=",end);
    field(" frame_end=",frame_end);field(" section_count=",count_sections);
    field(" cursor=",cursor);field(" returned=",returned);field(" next_cursor=",cursor+returned);
    append(" provenance=halted_retired_queue_rdram section_encoding=be64_hex fixed_summary=y0,y1_exclusive,first,min,max,constant");
    previous=0;
    if(cursor&&!section_read(base+(cursor-1)*SECTION_SIZE+63,1,&previous)){error(id,"sections_read_failed");return;}
    for(uint32_t i=cursor;i<cursor+returned;i++) {
        unsigned char bytes[64];uint32_t bound,first=0,minimum=0,maximum=0;
        for(unsigned j=0;j<sizeof(bytes);j++) {
            uint32_t value;
            if(!section_read(base+i*SECTION_SIZE+j,1,&value)){error(id,"sections_read_failed");return;}
            bytes[j]=(unsigned char)value;
        }
        bound=bytes[63];
        for(uint32_t y=previous;y<bound;y++) {
            uint32_t value;
            if(!section_read(fixed+y*2,2,&value)){error(id,"sections_read_failed");return;}
            if(y==previous)first=minimum=maximum=value;
            else {if(value<minimum)minimum=value;if(value>maximum)maximum=value;}
        }
        append(" s");number(i);append("=");
        for(unsigned j=0;j<sizeof(bytes);j++)section_hex_byte(bytes[j]);
        append(" f");number(i);append("=");number(previous);append(",");number(bound);
        append(",");number(first);append(",");number(minimum);append(",");number(maximum);
        append(",");number(bound>previous&&minimum==maximum);
        previous=bound;
    }
    /* No truncation can masquerade as a complete page. This path has no
     * guest/queue writes, DMA, persistent snapshot, or running-frame hook. */
    if(reply_length>=sizeof(reply)-3){error(id,"sections_reply_size");return;}
    (void)finish();
}
#endif
#include "rdp_math_probe.h"
#ifdef SODIUM64_AUDIO_OBSERVER
#ifdef SODIUM64_DSP_KOFF_RELEASE
extern volatile uint32_t dsp_release_steps, dsp_release_last;
#endif
extern unsigned char dsp_buffer[8192], dsp_regs[128];
extern uint16_t dsp_pointer;
extern unsigned char enabled;
extern volatile uint32_t dsp_audio_blocks, dsp_audio_idle, dsp_audio_full;
extern volatile uint32_t dsp_audio_gap_max, dsp_audio_last_count;
extern const uint32_t dsp_audio_dac_rate;
#ifdef SODIUM64_MIX_OBSERVER
extern unsigned char dsp_mix_records[80];
extern volatile uint32_t dsp_mix_ready, dsp_mix_count, dsp_mix_ring_offset, dsp_mix_enabled;
#endif
#ifdef REMOTE_CONTROL_HOST
extern uint32_t remote_host_audio_register(unsigned offset);
#endif
static void audio_observation(const char *id,int reset,uint32_t framebuffer) {
    if(!present||transport_error||menu_error){error(id,"audio_transport_unready");return;}
    if(busy_capture()||remote_arm_pending){error(id,"capture_busy");return;}
    if(!remote_paused){error(id,"not_paused");return;}
    if(!framebuffer||!remote_render_frames){error(id,"frame_unavailable");return;}
    if(dsp_pointer>=8192||(dsp_pointer&3)){error(id,"audio_pointer");return;}
    uint32_t observed_at=count(); /* Before the potentially slow USB export. */
    if(reset) {
        dsp_audio_blocks=dsp_audio_idle=dsp_audio_full=0;
        dsp_audio_gap_max=dsp_audio_last_count=0;
#ifdef SODIUM64_DSP_KOFF_RELEASE
        dsp_release_steps=dsp_release_last=0;
#endif
#ifdef SODIUM64_MIX_OBSERVER
        dsp_mix_ready=dsp_mix_count=0;
#endif
    } else {
#ifdef REMOTE_CONTROL_HOST
        const void *pcm=dsp_buffer;
#else
        const void *pcm=uncached(dsp_buffer);
#endif
        if(!send_packet(2,pcm,8192)){error(id,"usb_export_failed");return;}
    }
    prefix(id,1);append(reset?" audio_reset=1":" exported=audio bytes=8192 pcm=s16be_stereo ring=1");
    field(" ring_head_bytes=",dsp_pointer);field(" enabled=",enabled);
    field(" blocks=",dsp_audio_blocks);field(" idle_before_submit=",dsp_audio_idle);
    field(" full_before_submit=",dsp_audio_full);field(" max_submit_gap_ticks=",dsp_audio_gap_max);
    field(" last_submit_count32=",dsp_audio_last_count);field(" count32=",observed_at);
    field(" render_frame_id=",remote_render_frames);
#ifdef SODIUM64_DSP_KOFF_RELEASE
    field(" release_steps=",dsp_release_steps);field(" release_last=",dsp_release_last);
#endif
    /* DAC rate/control/bitrate do not provide useful readback on hardware.
     * Export the linked initialization value, not a fictitious frequency from
     * a zero register read. Its equality to actual AI init is a compiled gate. */
    field(" ai_programmed_dac_rate=",dsp_audio_dac_rate);
    append(" ai_init_clock_hz=48681812 ai_programmed_control=1 ai_programmed_bit_rate=15");
    for(unsigned offset=4;offset<=12;offset+=8) {
#ifdef REMOTE_CONTROL_HOST
        uint32_t value=remote_host_audio_register(offset);
#else
        uint32_t value=*(volatile uint32_t *)(uintptr_t)(0xa4500000u+offset);
#endif
        append(" ai");number(offset);append("=");number(value);
    }
    append(" dspregs=");
    static const char digits[]="0123456789abcdef";
    for(unsigned i=0;i<128;i++) {
        char byte[3]={digits[dsp_regs[i]>>4],digits[dsp_regs[i]&15],0};append(byte);
    }
    append(" provenance=paused_dsp_ring_not_dac no_audio_fidelity_claim=1");
    (void)finish();
}
#endif
#ifdef SODIUM64_BRR_OBSERVER
extern volatile uint32_t dsp_brr_next, dsp_brr_count;
extern unsigned char dsp_brr_records[512];
static void brr_observation(const char *id,uint32_t framebuffer) {
    if(!present||transport_error||menu_error){error(id,"audio_transport_unready");return;}
    if(busy_capture()||remote_arm_pending){error(id,"capture_busy");return;}
    if(!remote_paused){error(id,"not_paused");return;}
    if(!framebuffer||!remote_render_frames){error(id,"frame_unavailable");return;}
    uint32_t next=dsp_brr_next,completed=dsp_brr_count;
    if(next>=32){error(id,"brr_index");return;}
    if(!send_packet(2,dsp_brr_records,512)){error(id,"usb_export_failed");return;}
    prefix(id,1);append(" exported=audio-brr bytes=512 stride=16 slots=32 endian=be");
    field(" next=",next);field(" completed_mod32=",completed);
    field(" valid_records=",completed<32?completed:32);
    field(" render_frame_id=",remote_render_frames);
    append(" provenance=native_brr_input_output_not_dac no_full_audio_fidelity_claim=1");
    (void)finish();
}
#endif
#ifdef SODIUM64_MIX_OBSERVER
static void mix_observation(const char *id,uint32_t framebuffer) {
    if(!present||transport_error||menu_error){error(id,"audio_transport_unready");return;}
    if(busy_capture()||remote_arm_pending){error(id,"capture_busy");return;}
    if(!remote_paused){error(id,"not_paused");return;}
    if(!framebuffer||!remote_render_frames){error(id,"frame_unavailable");return;}
    if(dsp_mix_ready!=1){error(id,"mix_not_ready");return;}
    uint32_t offset=dsp_mix_ring_offset,mask=dsp_mix_enabled;
    if((offset!=4092&&offset!=8188)||mask>255){error(id,"mix_state");return;}
    if(!send_packet(2,dsp_mix_records,80)){error(id,"usb_export_failed");return;}
    prefix(id,1);append(" exported=audio-mix bytes=80 voices=8 stride=8 endian=be");
    field(" completed_mod32=",dsp_mix_count);field(" ring_sample_offset_bytes=",offset);
    field(" render_frame_id=",remote_render_frames);
    append(" provenance=native_dry_mix_input_output_not_dac no_full_audio_fidelity_claim=1");
    (void)finish();
}
#endif
#ifdef SODIUM64_DSP_GAIN_PROBE
extern uint32_t remote_dsp_gain_probe(uint32_t voice,uint32_t gain,uint32_t result[2]);
static void gain_probe(const char *id,uint32_t framebuffer) {
    if(!present||transport_error||menu_error){error(id,"audio_transport_unready");return;}
    if(busy_capture()||remote_arm_pending){error(id,"capture_busy");return;}
    if(!remote_paused){error(id,"not_paused");return;}
    if(!framebuffer||!remote_render_frames){error(id,"frame_unavailable");return;}
    unsigned failures=0,cases=0;
    for(unsigned voice=0;voice<8;voice++)for(unsigned family=0;family<2;family++) {
        uint32_t result[2];
        if(!remote_dsp_gain_probe(voice,family?0xff:0x40,result)) {
            error(id,"gain_probe_restore_failed");return;
        }
        cases++;
        failures+=(result[0]!=0x1357||result[1]!=0x2468);
    }
    prefix(id,1);append(" gain_probe=1");field(" cases=",cases);
    field(" accumulator_failures=",failures);append(" restored=1");
    field(" render_frame_id=",remote_render_frames);
    append(" provenance=synthetic_handler_not_audio_waveform");(void)finish();
}
#endif
static void status(const char *id) {
    uint32_t now=count();if(now<count_last)count_wraps++;count_last=now;
    prefix(id,1);
    append(" mode=emu protocol=1 build=A14-usb-loop capabilities=pause,pause-at,step,resume,buttons,release,capture,frame,sav,profile,menu");
#ifdef SODIUM64_AUDIO_OBSERVER
    append(",audio,audio-reset");
#endif
#ifdef SODIUM64_BRR_OBSERVER
    append(",audio-brr");
#endif
#ifdef SODIUM64_MIX_OBSERVER
    append(",audio-mix");
#endif
#ifdef SODIUM64_DSP_GAIN_PROBE
    append(",audio-gain-probe");
#endif
#if SODIUM64_REMOTE_SECTION_OBSERVER
    append(",sections");
#endif
#if defined(SODIUM64_RDP_MATH_PROBE) && !defined(REMOTE_CONTROL_HOST)
    append(",rdp-probe");
    field(" rdp_probe_dirty=",rdp_probe_dirty);
#endif
    field(" paused=",remote_paused);field(" count32=",now);
    field(" count_wraps_observed=",count_wraps);field(" count_hz=",REMOTE_COUNT_HZ);
    field(" guest_frame_id=",remote_guest_frames);field(" render_frame_id=",remote_render_frames);
    field(" boot_tv_type=",remote_boot_tv_type);
    field(" vi=",remote_vi_count);field(" new_presentations=",remote_presentations);
    field(" recorder_phase=",native_diag_phase);
    signed_field(" recorder_result=",native_diag_capture_result);
    field(" recorder_error_stage=",continuous_save_error_stage);
    field(" recorder_error_code=",continuous_save_error_code);
    field(" recorder_sc64_status=",continuous_save_sc64_status);
    field(" recorder_data0=",continuous_save_data0);
    field(" recorder_pi_status=",continuous_save_pi_status);
    field(" recorder_last_command=",continuous_save_last_command);
    field(" recorder_sd_status=",continuous_save_sd_status);
    field(" recorder_sink_ready=",continuous_save_sink_ready);
    field(" sealed_ready=",native_diag_snapshot_ready);
    field(" sealed_id=",native_diag_snapshot_sequence);
    field(" input_buttons=",remote_buttons);field(" input_remaining=",remote_button_frames);
    field(" usb_poll_calls=",poll_calls);field(" usb_poll_count_total_mod32=",poll_total);
    field(" usb_poll_count_max=",poll_max);field(" transport_error=",transport_error);
    field(" menu_error=",menu_error);
    field(" pause_pending=",remote_pause_pending);
    field(" pause_at_render_frame_id=",remote_pause_target);
    field(" frame_control_max=",REMOTE_FRAME_CONTROL_MAX);
    append(" usb_poll_scope=C_handler_excludes_bridge");
    append(" metric_provenance=cp0_count,guest_boundary,rsp_retired,vi_irq,vi_origin_publish fps_claim=none");
    (void)finish();
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
#ifdef SODIUM64_DSP_GAIN_PROBE
    if(eq(verb,"audio-gain-probe")) {
        if(nt!=3){error(id,"argument_count");return;}
        gain_probe(id,retired_framebuffer);return;
    }
#endif
#ifdef SODIUM64_BRR_OBSERVER
    if(eq(verb,"audio-brr")) {
        if(nt!=3){error(id,"argument_count");return;}
        brr_observation(id,retired_framebuffer);return;
    }
#endif
#ifdef SODIUM64_AUDIO_OBSERVER
    if(eq(verb,"audio")||eq(verb,"audio-reset")) {
        if(nt!=3){error(id,"argument_count");return;}
        audio_observation(id,eq(verb,"audio-reset"),retired_framebuffer);return;
    }
#endif
#ifdef SODIUM64_MIX_OBSERVER
    if(eq(verb,"audio-mix")) {
        if(nt!=3){error(id,"argument_count");return;}
        mix_observation(id,retired_framebuffer);return;
    }
#endif
#if defined(SODIUM64_RDP_MATH_PROBE) && !defined(REMOTE_CONTROL_HOST)
    if(eq(verb,"rdp-probe")) {
        uint32_t normalized;
        if(nt!=4||!decimal(tokens[3],&normalized,7)){error(id,"rdp_probe_format");return;}
        rdp_probe(id,normalized,retired_framebuffer);return;
    }
    if(rdp_probe_dirty&&!eq(verb,"hello")&&!eq(verb,"status")&&!eq(verb,"profile")&&
       !eq(verb,"frame")&&!eq(verb,"snapshot")&&!eq(verb,"menu")) {
        error(id,"rdp_probe_requires_menu");return;
    }
#endif
#if SODIUM64_REMOTE_SECTION_OBSERVER
    if(eq(verb,"sections")) {
        uint32_t cursor;
        if(nt!=4||!decimal(tokens[3],&cursor,0x5000u/SECTION_SIZE)){error(id,"sections_cursor");return;}
        sections(id,cursor,retired_framebuffer);return;
    }
#endif
    if(eq(verb,"hello")||eq(verb,"status")||eq(verb,"profile")) {
        if(nt!=3){error(id,"argument_count");return;}status(id);return;
    }
    if(eq(verb,"pause-at")||eq(verb,"step")) {
        int step=eq(verb,"step");uint32_t value,target;
        if(nt!=4||!decimal(tokens[3],&value,step?REMOTE_FRAME_CONTROL_MAX:UINT32_MAX)||
           (step&&!value)) {error(id,step?"invalid_step":"invalid_frame_id");return;}
        if(busy_capture()||remote_arm_pending){error(id,"capture_busy");return;}
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
            if(step)remote_paused=0;
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
    if(eq(verb,"capture")) {
        int usb=nt==4&&eq(tokens[3],"usb");
        if(nt>4||(nt==4&&!usb&&!eq(tokens[3],"sd"))) {error(id,"capture_sink");return;}
        if(remote_paused){error(id,"paused");return;}
        if(busy_capture()||remote_arm_pending){error(id,"capture_busy");return;}
        if(!usb && (!continuous_save_sink_ready||native_diag_phase!=0)) {
            error(id,"sd_unready use_capture_usb");return;
        }
        native_diag_usb_only=usb;
        prefix(id,1);append(usb?" capture_ready=1 sink=usb":" capture_ready=1 sink=sd");
        append(" duration_seconds=20 outcome=pending");
        if(finish()){cancel_pause_target();remote_arm_pending=1;}
        return;
    }
    if(nt!=3){error(id,"argument_count");return;}
    if(eq(verb,"resume")) {
        if(menu_error){error(id,"transition_failed_requires_reset");return;}
        cancel_pause_target();
        remote_paused=0;prefix(id,1);append(" paused=0");
        field(" retired_frame_id=",remote_render_frames);(void)finish();return;
    }
    if(eq(verb,"pause")||eq(verb,"frame")||eq(verb,"snapshot")||eq(verb,"sav")||eq(verb,"export")||eq(verb,"menu")) {
        if(busy_capture()||remote_arm_pending){error(id,"capture_busy");return;}
    } else {error(id,"unknown_verb");return;}
    if(eq(verb,"pause")) {
        cancel_pause_target();
        remote_paused=1;remote_buttons=0;remote_button_frames=0;
        joyxlh[0]=0;
        prefix(id,1);append(" paused=1 boundary=rsp_retired");
        field(" retired_frame_id=",remote_render_frames);(void)finish();return;
    }
    if(eq(verb,"frame")||eq(verb,"snapshot")) {
        /* CPU owns this completed, unpublished framebuffer. Guest and RSP
         * stay at this boundary throughout Header + Screenshot transmission. */
        unsigned char header[16]={0,0,0,4,0,0,0,2,0,0,1,24,0,0,0,240};
        if(!retired_framebuffer){error(id,"frame_unavailable");return;}
#ifdef REMOTE_CONTROL_HOST
        int frame_ready=remote_host_frame_ready();
#else
        /* RSP HALT alone can precede the final RDP framebuffer writes. Only
         * an explicit image export waits for the DP; capture timing is intact. */
        int frame_ready=wait_io(0xa410000c,0x170,0,DMA_TIMEOUT);
#endif
        if(!frame_ready){error(id,"frame_dp_busy");return;}
        if(!send_packet(3,header,16)||!send_packet(4,(const void *)(uintptr_t)retired_framebuffer,FRAME_BYTES)) {
            error(id,"usb_export_failed");return;
        }
        prefix(id,1);append(" exported=frame width=280 height=240 pixel_bytes=2 boundary=rsp_retired");
        field(" render_frame_id=",remote_render_frames);(void)finish();return;
    }
    if(eq(verb,"sav")||eq(verb,"export")) {
        if(!native_diag_snapshot_ready){error(id,"capture_not_sealed");return;}
#ifdef REMOTE_CONTROL_HOST
        const void *snapshot=native_diag_snapshot;
#else
        const void *snapshot=uncached(native_diag_snapshot);
#endif
        if(!send_packet(2,snapshot,32768)){error(id,"usb_export_failed");return;}
        prefix(id,1);append(" exported=sav bytes=32768 immutable=1");
        field(" sealed_id=",native_diag_snapshot_sequence);(void)finish();return;
    }
    cancel_pause_target();
    remote_buttons=0;remote_button_frames=0;remote_paused=1;
    joyxlh[0]=0;
    prefix(id,1);append(" transition_ready=menu outcome=pending");
    if(finish()&&!reboot_menu())remote_paused=1;
}

void remote_control_init(void) {
    count_last=count();
    cancel_pause_target();
#ifdef REMOTE_CONTROL_HOST
    present=1;
#else
    if(!sc_write(4,0)||!sc_write(4,0x5f554e4c)||!sc_write(4,0x4f434b5f)||
       !sc_read(3,&raw_identifier))return;
    present=raw_identifier==0x53437632;
    mailbox_publish(1);
#endif
}
void remote_control_frame(uint32_t retired_framebuffer) {
    remote_render_frames++;
    /* Each hook retires exactly one render; idle polling never advances it.
     * A separate pending bit makes target zero valid across uint32 wrap. */
    if(remote_pause_pending) {
        if(busy_capture()||remote_arm_pending)cancel_pause_target();
        else if(remote_render_frames==remote_pause_target) {
            remote_pause_pending=0;remote_paused=1;
        }
    }
#ifndef REMOTE_CONTROL_HOST
    int first_frame=remote_render_frames==1;
#endif
    if(!present||transport_error) {
#ifndef REMOTE_CONTROL_HOST
        if(first_frame&&!transport_error)mailbox_publish(2);
#endif
        return;
    }
    uint32_t start=count();
#ifndef REMOTE_CONTROL_HOST
    unsigned n=receive();
    if(n)remote_process_request(uncached(request_buffer),n,retired_framebuffer);
#else
    (void)retired_framebuffer;
#endif
    uint32_t delta=count()-start;
    poll_calls++;poll_total+=delta;if(delta>poll_max)poll_max=delta;
#ifndef REMOTE_CONTROL_HOST
    if(first_frame&&!transport_error)mailbox_publish(2);
#endif
}
void remote_control_idle(uint32_t retired_framebuffer) {
    /* Called only while suspended at the same retired frame. No guest or
     * render counter advances; VI IRQs keep displaying completed buffers. */
    uint32_t start=count();
#ifndef REMOTE_CONTROL_HOST
    if(present&&!transport_error) {
        unsigned n=receive();
        if(n)remote_process_request(uncached(request_buffer),n,retired_framebuffer);
    }
    while((uint32_t)(count()-start)<REMOTE_COUNT_HZ/120) {}
#else
    (void)retired_framebuffer;
#endif
    uint32_t delta=count()-start;
    poll_calls++;poll_total+=delta;if(delta>poll_max)poll_max=delta;
}
