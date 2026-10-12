/* Paused-only physical RDP experiment. Default builds omit it entirely.
 * Borrow the retired winner/TLUT scratch and permanently forbid guest resume
 * until menu reboot, because this probe replaces TMEM and painter state.
 * No ROM/game-derived data or SD writes occur in this probe.
 */
#if defined(SODIUM64_RDP_MATH_PROBE) && !defined(REMOTE_CONTROL_HOST)
#include <rdpq_macros.h>
_Static_assert(HCOMP_TLUT_BASE==0xa0384000u,"probe must borrow the audited retired scratch");
_Static_assert(0xa0385200u<=HCOMP_TLUT_OBJ+0x800u,"probe command lists must remain in scratch");
_Static_assert(29*8<=256,"probe command list exceeds one staging slot");
_Static_assert(0xa0385800u+48*280*2<=HCOMP_WINNER_ARENA+HCOMP_SURFACE_BYTES,
    "probe depth rows must remain in the retired winner surface");
static unsigned rdp_probe_dirty;

static int rdp_probe_submit(volatile uint64_t *commands,unsigned words) {
    volatile uint32_t *dp=(volatile uint32_t *)0xa4100000u;
    if(!wait_io(0xa410000cu,0x770,0,DMA_TIMEOUT))return 0;
    dp[3]=1; /* RDRAM command source, no SP/DMEM DMA. */
    __asm__ volatile("sync":::"memory");
    dp[0]=(uint32_t)(uintptr_t)commands&0x1fffffffu;
    dp[1]=((uint32_t)(uintptr_t)commands+words*8)&0x1fffffffu;
    uint32_t start=count();
    while((dp[3]&0x770)||dp[2]!=dp[1])
        if((uint32_t)(count()-start)>DMA_TIMEOUT)return 0;
    return 1;
}

#ifndef SODIUM64_RDP_FIXED_ONLY_PROBE
static uint32_t rdp_probe_rgb(unsigned x,unsigned y,unsigned source) {
    unsigned r=source?y:x,g=source?31-y:31-x,b=source?y:x;
    return (r<<27)|(g<<19)|(b<<11)|255;
}
#endif

/* Fixed RGB operand, matching Setup's RGBA5551 -> ENV (component << 3).
 * Test every fixed value, and separately report the nonwrapping <=16 range.
 * This is a synthetic hardware proof, never a game-identity admission rule.
 */
static int rdp_probe_fixed(const char *id,uint32_t fbp) {
    volatile uint16_t *pixels=(volatile uint16_t *)(uintptr_t)(fbp|0xa0000000u);
    const uint64_t combiners[4]={
        RDPQ_COMBINER2((0,0,0,TEX0),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((0,0,0,ENV),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((TEX0,0,PRIM_ALPHA,ENV),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((TEX0,ENV,PRIM_ALPHA,0),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE))};
    unsigned all[4]={0},safe[4]={0},first[4]={0},submissions=0;
    rdp_probe_dirty=1;
    for(unsigned a=0;a<32;a++)
        ((volatile uint16_t *)0xa0384000u)[a]=(a<<11)|((31-a)<<6)|(a<<1)|1;
    for(unsigned b=0;b<32;b++)for(unsigned mode=0;mode<4;mode++) {
        volatile uint64_t *cmd=(volatile uint64_t *)(uintptr_t)
            (0xa0385000u+(submissions++&1)*256);
        unsigned n=0,x=12+mode*36,y=16+b;
        cmd[n++]=0x2700000000000000ull;
        cmd[n++]=0x2f00000000000200ull|SOM_CYCLE_2|SOM_TF0_RGB|
            SOM_TF1_RGB|SOM_RGBDITHER_NONE|SOM_ALPHADITHER_NONE;
        cmd[n++]=0x3f10011700000000ull|fbp;
        cmd[n++]=0x2d000000004603c0ull;
        cmd[n++]=0x3a000000ffffffffull;
        unsigned value=b<<3;
        cmd[n++]=0x3b000000000000ffull|((uint64_t)value<<24)|((uint64_t)value<<16)|((uint64_t)value<<8);
        cmd[n++]=0xfc00000000000000ull|(combiners[mode]&0x00ffffffffffffffull);
        cmd[n++]=0x2800000000000000ull;
        cmd[n++]=0x3d10001f00384000ull;
        cmd[n++]=0x3510100007080200ull;
        cmd[n++]=0x2600000000000000ull;
        cmd[n++]=0x340000000707c000ull;
        cmd[n++]=0x2700000000000000ull;
        cmd[n++]=0x3510100000080200ull;
        cmd[n++]=0x320000000007c000ull;
        cmd[n++]=0xe400000000000000ull|((uint64_t)((x+32)*4)<<44)|
            ((uint64_t)((y+1)*4)<<32)|((x*4)<<12)|(y*4);
        cmd[n++]=0x0000000004000400ull;
        cmd[n++]=0x2900000000000000ull;
        if(!rdp_probe_submit(cmd,n)){error(id,"rdp_probe_dp_timeout_requires_menu");return 0;}
        for(unsigned a=0;a<32;a++) {
            unsigned r=a,g=31-a;
            if(mode==1){r=b;g=b;}
            if(mode==2){r+=b;g+=b;if(r>31)r=31;if(g>31)g=31;}
            if(mode==3){r=r>b?r-b:0;g=g>b?g-b:0;}
            unsigned expected=(r<<11)|(g<<6)|(r<<1);
            unsigned actual=pixels[y*280+x+a]&0xfffeu;
            if(actual!=expected){if(!all[mode])first[mode]=(b<<24)|(a<<16)|actual;all[mode]++;if(b<=16)safe[mode]++;}
        }
    }
    prefix(id,1);append(" rdp_probe=1 native=1 resume_requires_menu=1 fixed_env=1 full_arithmetic=1 depth_gating=0 pairs_per_mode=1024 safe_fixed_max=16 safe_pairs_per_mode=544");
    field(" copy_differences=",all[0]);field(" env_copy_differences=",all[1]);
    field(" add_full_differences=",all[2]);field(" sub_full_differences=",all[3]);
    field(" safe_add_differences=",safe[2]);field(" safe_sub_differences=",safe[3]);
    field(" first_add_full=",first[2]);field(" first_sub_full=",first[3]);(void)finish();return 1;
}

/* Original numeric pixels only: can coverage carry one semantic bit without
 * changing RGB or transparency? Never resume guest rendering after this test.
 * RGBA16 and CI8/TLUT are tested against both preexisting low-bit values. */
static int rdp_probe_coverage(const char *id,uint32_t fbp) {
    volatile uint16_t *pixels=(volatile uint16_t *)(uintptr_t)(fbp|0xa0000000u);
    volatile uint16_t *texture=(volatile uint16_t *)0xa0384000u;
    volatile uint8_t *indices=(volatile uint8_t *)0xa0384040u;
    volatile uint16_t *palette=(volatile uint16_t *)0xa0384080u;
    const uint64_t combine=RDPQ_COMBINER1((0,0,0,TEX0),(TEX0,0,PRIM,0));
    unsigned rgb[4]={0},tags[4]={0},transparent[4]={0},first[4]={0},first_rgb[4]={0},submissions=0;
    rdp_probe_dirty=1;
    for(unsigned x=0;x<32;x++) {
        unsigned value=x>1?((x<<11)|((31-x)<<6)|(((x*7)&31)<<1)|1):(x==1);
        texture[x]=palette[x]=value;indices[x]=(uint8_t)x;
    }
    for(unsigned dest=0;dest<4;dest++)for(unsigned ci=0;ci<2;ci++)
    for(unsigned old=0;old<2;old++)for(unsigned permitted=0;permitted<2;permitted++) {
        unsigned x=12,y=16+submissions,alpha=permitted?255:63,n=0;
        unsigned sentinel=0x7be0u|old;
        for(unsigned a=0;a<32;a++)pixels[y*280+x+a]=(uint16_t)sentinel;
        volatile uint64_t *cmd=(volatile uint64_t *)(uintptr_t)
            (0xa0385000u+(submissions++&1)*256);
        cmd[n++]=0x2700000000000000ull;
        cmd[n++]=0x2f00000000001001ull|SOM_TF0_RGB|SOM_TF1_RGB|SOM_RGBDITHER_NONE|
            SOM_ALPHADITHER_NONE|((uint64_t)dest<<8)|(ci?SOM_TLUT_RGBA16:0);
        cmd[n++]=0x3f10011700000000ull|fbp;
        cmd[n++]=0x2d000000004603c0ull;
        cmd[n++]=0x3900000000000001ull; /* Threshold1 discards only zero alpha. */
        cmd[n++]=0x3a000000ffffff00ull|alpha;
        cmd[n++]=0x3c00000000000000ull|(combine&0x00ffffffffffffffull);
        cmd[n++]=0x2800000000000000ull;
        if(ci) {
            cmd[n++]=0x3d10001f00384080ull;
            cmd[n++]=0x3510010007000000ull;
            cmd[n++]=0x2600000000000000ull;
            cmd[n++]=0x300000000707c000ull; /* Load32 TLUT entries. */
            cmd[n++]=0x2700000000000000ull;
        }
        cmd[n++]=ci?0x3d48001f00384040ull:0x3d10001f00384000ull;
        cmd[n++]=ci?0x3548080007000050ull:0x3510100007000050ull;
        cmd[n++]=0x2600000000000000ull;
        cmd[n++]=0x340000000707c000ull;
        cmd[n++]=0x2700000000000000ull;
        cmd[n++]=ci?0x3548080000000050ull:0x3510100000000050ull;
        cmd[n++]=0x320000000007c000ull;
        cmd[n++]=0x2400000000000000ull|((uint64_t)((x+32)*4)<<44)|
            ((uint64_t)((y+1)*4)<<32)|((x*4)<<12)|(y*4);
        cmd[n++]=0x0000000004000400ull;
        cmd[n++]=0x2900000000000000ull;
        if(n>29||!rdp_probe_submit(cmd,n)){error(id,"coverage_probe_timeout_requires_menu");return 0;}
        for(unsigned a=0;a<32;a++) {
            unsigned actual=pixels[y*280+x+a];
            if(!a) {if(actual!=sentinel)transparent[dest]++;continue;}
            if((actual&0xfffeu)!=(texture[a]&0xfffeu)) {
                if(!rgb[dest])first_rgb[dest]=(a<<16)|actual;
                rgb[dest]++;
            }
            if((actual&1u)!=permitted) {if(!tags[dest])first[dest]=(ci<<24)|(old<<20)|(permitted<<16)|actual;tags[dest]++;}
        }
    }
    prefix(id,1);append(" rdp_probe=1 native=1 resume_requires_menu=1 coverage_tags=1 formats=2 pixel_cases=1024 z_disabled=1 antialias_disabled=1 memory_read_disabled=1");
    for(unsigned dest=0;dest<4;dest++) {
        append(dest==0?" clamp":dest==1?" wrap":dest==2?" zap":" save");
        field("_rgb_differences=",rgb[dest]);
        append(dest==0?" clamp":dest==1?" wrap":dest==2?" zap":" save");
        field("_tag_differences=",tags[dest]);
        append(dest==0?" clamp":dest==1?" wrap":dest==2?" zap":" save");
        field("_transparent_differences=",transparent[dest]);
        append(dest==0?" clamp":dest==1?" wrap":dest==2?" zap":" save");
        field("_first_tag=",first[dest]);
        append(dest==0?" clamp":dest==1?" wrap":dest==2?" zap":" save");
        field("_first_rgb=",first_rgb[dest]);
    }
    (void)finish();return 1;
}

static void rdp_probe(const char *id,unsigned normalized,uint32_t framebuffer) {
    if(!remote_paused||remote_pause_pending||busy_capture()||remote_arm_pending) {
        error(id,"rdp_probe_requires_idle_pause");return;
    }
    uint32_t fbp=framebuffer&0x1fffffffu;
    uint32_t sp=*(volatile uint32_t *)0xa4040010u;
    if((fbp!=(FRAMEBUFFER1&0x1fffffffu)&&
        fbp!=(FRAMEBUFFER2&0x1fffffffu)&&
        fbp!=(FRAMEBUFFER3&0x1fffffffu))||
       !(sp&1)||(sp&14)||
       *(volatile uint32_t *)0xa4040014u||
       *(volatile uint32_t *)0xa4040018u) {
        error(id,"rdp_probe_ownership");return;
    }
    if(!wait_io(0xa410000cu,0x770,0,DMA_TIMEOUT)) {
        error(id,"rdp_probe_dp_busy");return;
    }
    if(normalized==7){(void)rdp_probe_fixed(id,fbp);return;}
    if(normalized==8){(void)rdp_probe_coverage(id,fbp);return;}
#ifdef SODIUM64_RDP_FIXED_ONLY_PROBE
    error(id,"rdp_probe_requires_fixed_mode7");
#else
    volatile uint16_t *pixels=(volatile uint16_t *)(uintptr_t)(fbp|0xa0000000u);
    const uint64_t combiners[5][4]={{
        RDPQ_COMBINER2((0,0,0,TEX0),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((0,0,0,TEX1),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((TEX0,TEX1,PRIM_ALPHA,TEX1),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((TEX0,TEX1,PRIM_ALPHA,0),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE))},{
        RDPQ_COMBINER2((0,0,0,TEX0),(0,0,0,ONE),(COMBINED,0,ENV_ALPHA,0),(0,0,0,ONE)),
        RDPQ_COMBINER2((0,0,0,TEX1),(0,0,0,ONE),(COMBINED,0,ENV_ALPHA,0),(0,0,0,ONE)),
        RDPQ_COMBINER2((TEX0,TEX1,PRIM_ALPHA,TEX1),(0,0,0,ONE),(COMBINED,0,ENV_ALPHA,0),(0,0,0,ONE)),
        RDPQ_COMBINER2((TEX0,TEX1,PRIM_ALPHA,0),(0,0,0,ONE),(COMBINED,0,ENV_ALPHA,0),(0,0,0,ONE))},{
        RDPQ_COMBINER2((0,0,0,TEX0),(0,0,0,TEX1),(COMBINED,0,ENV_ALPHA,0),(0,0,0,COMBINED)),
        RDPQ_COMBINER2((0,0,0,TEX1),(0,0,0,TEX1),(COMBINED,0,ENV_ALPHA,0),(0,0,0,COMBINED)),
        RDPQ_COMBINER2((TEX0,TEX1,PRIM_ALPHA,TEX1),(0,0,0,TEX1),(COMBINED,0,ENV_ALPHA,0),(0,0,0,COMBINED)),
        RDPQ_COMBINER2((TEX0,TEX1,PRIM_ALPHA,0),(0,0,0,TEX1),(COMBINED,0,ENV_ALPHA,0),(0,0,0,COMBINED))},{
        RDPQ_COMBINER2((0,0,0,TEX0),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((0,0,0,TEX1),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((TEX0,0,PRIM_ALPHA,TEX1),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((TEX0,TEX1,PRIM_ALPHA,0),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE))},{
        RDPQ_COMBINER2((0,0,0,TEX0),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((0,0,0,TEX1),(0,0,0,ONE),(0,0,0,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((TEX0,TEX1,PRIM_ALPHA,TEX1),(0,0,0,ONE),(COMBINED,0,ENV_ALPHA,COMBINED),(0,0,0,ONE)),
        RDPQ_COMBINER2((TEX0,TEX1,PRIM_ALPHA,0),(0,0,0,ONE),(COMBINED,0,ENV_ALPHA,COMBINED),(0,0,0,ONE))}};
    unsigned depth_gate=normalized==4||normalized==5;
    unsigned differences[4]={0},first[4]={0},submissions=0;
    rdp_probe_dirty=1;
    for(unsigned half=0;half<2;half++) {
        for(unsigned source=0;source<2;source++) {
            uintptr_t base=0xa0384000u+source*0x800u;
            for(unsigned y=0;y<16;y++)for(unsigned x=0;x<32;x++) {
                uint32_t rgb=rdp_probe_rgb(x,y+half*16,source);
                unsigned index=y*32+x;
                if(normalized==1)((volatile uint32_t *)base)[index]=rgb;
                else ((volatile uint16_t *)base)[index]=
                    ((rgb>>16)&0xf800)|((rgb>>13)&0x7c0)|((rgb>>10)&0x3e)|
                    (normalized==3&&source==1?(x+y+half*16)&1:1);
            }
        }
        for(unsigned mode=0;mode<4;mode++) {
            /* Alternate list addresses: CURRENT==END must not accidentally
             * match the previously retired submission before a new fetch. */
            unsigned n=0,x=12+mode*36,y=16+half*16;
            if(normalized>=3) {
                /* Masked pixels must retain an independently populated Main
                 * value. Alpha compare avoids any framebuffer blending. */
                for(unsigned yy=0;yy<16;yy++)for(unsigned xx=0;xx<32;xx++)
                    pixels[(y+yy)*280+x+xx]=(xx<<11)|((31-xx)<<6)|(xx<<1)|1;
            }
            if(depth_gate)for(unsigned block=0;block<2;block++) {
                volatile uint64_t *zc=(volatile uint64_t *)(uintptr_t)
                    (0xa0385000u+(submissions++&1)*256);
                unsigned zn=0;
                zc[zn++]=0x2700000000000000ull;
                zc[zn++]=0x2f30000000000000ull; /* Fill cycle initializes hidden Z bits too. */
                zc[zn++]=0x3f10011700385800ull;
                zc[zn++]=0x2d000000004603c0ull;
                for(unsigned row=0;row<8;row++) {
                    unsigned yy=y+block*8+row;
                    zc[zn++]=0x2700000000000000ull;
                    zc[zn++]=0x3700000000000000ull|((yy&1)?0x0c000400u:0x04000c00u);
                    zc[zn++]=0x3600000000000000ull|((uint64_t)((x+31)*4)<<44)|
                        ((uint64_t)(yy*4)<<32)|((x*4)<<12)|(yy*4);
                }
                zc[zn++]=0x2900000000000000ull;
                if(!rdp_probe_submit(zc,zn)){error(id,"rdp_probe_dp_timeout_requires_menu");return;}
            }
            volatile uint64_t *cmd=(volatile uint64_t *)(uintptr_t)
                (0xa0385000u+(submissions++&1)*256);
            cmd[n++]=0x2700000000000000ull;
            /* Point sampling still needs RGB fetching in both cycles;
             * clearing TF0/TF1 selects the RDP's YUV conversion path. */
            cmd[n++]=0x2f00000000000200ull|SOM_CYCLE_2|SOM_TF0_RGB|
                SOM_TF1_RGB|SOM_RGBDITHER_NONE|SOM_ALPHADITHER_NONE|
                (normalized==3)|(depth_gate?0x14:0);
            cmd[n++]=0x3f10011700000000ull|fbp;
            cmd[n++]=0x2d000000004603c0ull; /* 280x240 exclusive scissor. */
            cmd[n++]=normalized==5?0x3a000000ffffffffull:0x3a000000ffffff80ull;
            cmd[n++]=normalized==6?0x3b000000ffffffffull:0x3b000000fffffffbull;
            cmd[n++]=0x3900000000000001ull; /* Alpha compare threshold 1. */
            cmd[n++]=0xfc00000000000000ull|
                (combiners[normalized==6?4:normalized==5?3:normalized==3?2:normalized>=2?1:0][mode]&0x00ffffffffffffffull);
            if(depth_gate) {
                cmd[n++]=0x3e00000000385800ull;
                cmd[n++]=0x2e00000010000000ull;
            }
            for(unsigned source=0;source<2;source++) {
                unsigned format=normalized==1?3:2,tmem=source*128;
                uint64_t tile=0x3500000000000000ull|((uint64_t)format<<51)|((uint64_t)8<<41)|((uint64_t)tmem<<32);
                cmd[n++]=0x2800000000000000ull;
                cmd[n++]=0x3d00001f00000000ull|((uint64_t)format<<51)|(0x00384000u+source*0x800u);
                cmd[n++]=tile|0x07080200u;
                cmd[n++]=0x2600000000000000ull;
                cmd[n++]=0x340000000707c03cull;
                cmd[n++]=0x2700000000000000ull;
                cmd[n++]=tile|((uint64_t)source<<24)|0x00080200u;
                cmd[n++]=0x320000000007c03cull|((uint64_t)source<<24);
            }
            cmd[n++]=0xe400000000000000ull|((uint64_t)((x+32)*4)<<44)|((uint64_t)((y+16)*4)<<32)|((x*4)<<12)|(y*4);
            cmd[n++]=0x0000000004000400ull;
            cmd[n++]=0x2900000000000000ull;
            if(!rdp_probe_submit(cmd,n)){error(id,"rdp_probe_dp_timeout_requires_menu");return;}
            for(unsigned yy=0;yy<16;yy++)for(unsigned xx=0;xx<32;xx++) {
                unsigned a=xx,b=yy+half*16,value;
                value=mode==0?a:mode==1?b:mode==2?(a+b)/2:a>b?(a-b)/2:0;
                unsigned green=mode==0?31-a:mode==1?31-b:mode==2?(62-a-b)/2:b>a?(b-a)/2:0;
                if(normalized>=5) {
                    if(mode==2){value=a+b;if(value>31)value=31;green=62-a-b;if(green>31)green=31;}
                    if(mode==3){value=a>b?a-b:0;green=b>a?b-a:0;}
                }
                if((normalized==3||depth_gate)&&!((a+b)&1)){value=a;green=31-a;}
                unsigned expected=(value<<11)|(green<<6)|(value<<1);
                unsigned actual=pixels[(y+yy)*280+x+xx]&0xfffeu;
                if(actual!=expected) {
                    if(!differences[mode])first[mode]=(b<<24)|(a<<16)|actual;
                    differences[mode]++;
                }
            }
        }
    }
    prefix(id,1);append(" rdp_probe=1 native=1 resume_requires_menu=1");
    field(" normalized_rgba32=",normalized==1);field(" rgba16_rescale251=",normalized>=2&&normalized<=4);
    field(" alpha_gating=",normalized==3);
    field(" depth_gating=",depth_gate);
    field(" full_arithmetic=",normalized>=5);
    field(" half_then_double=",normalized==6);
    field(" pairs_per_mode=",1024);
    field(" tex0_differences=",differences[0]);field(" tex1_differences=",differences[1]);
    field(normalized>=5?" add_full_differences=":" add_half_differences=",differences[2]);
    field(normalized>=5?" sub_full_differences=":" sub_half_differences=",differences[3]);
    field(" first_add_half=",first[2]);field(" first_sub_half=",first[3]);(void)finish();
#endif
}
#endif
