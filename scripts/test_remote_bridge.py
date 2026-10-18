#!/usr/bin/env python3
"""Linked O64 owners/boot guard and disabled-image identity, not native timing."""
import argparse,json
from pathlib import Path
from linked_cpu_regression import CPU,load_elf,sx32

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('elf',type=Path)
    p.add_argument('--disabled-elf',type=Path);p.add_argument('--parent-elf',type=Path)
    p.add_argument('--json-output',type=Path);a=p.parse_args()
    memory,s=load_elf(a.elf)
    arena=s.get('renderer_cgram_owner_begin',0xbe200)
    assert arena in (0xbe200,0xd2000), 'unqualified renderer owner'
    assert max(memory)<arena and s['__bss_end']<=0x80000000+arena
    assert not any(0x400000<=address<0x800000 for address in memory)
    cases=0
    def cpu():
        c=CPU(memory.copy());c.regs=[sx32(i*0x10203+0x30405)^((i*0x112233)<<32) for i in range(32)]
        c.regs[0]=0;c.regs[31]=sx32(0xdead0000);return c
    for size in (0,4194304,8388607,8388609,0xffffffff,8388608):
        for tv in (0,1,2,255):
            c=cpu()
            c.memory.update((0x4000000+i,v)for i,v in enumerate(size.to_bytes(4,'big')))
            c.memory[0x4000009]=tv;c.memory_writes=[]
            accepted=size==8388608
            stop=s['remote_upper_initialized'] if accepted else s['remote_boot_ram_rejected']
            c.execute(s['main'],stop=stop)
            assert c.read(s['remote_boot_ram_bytes'])==(8388608 if accepted else 0)
            assert c.read(s['remote_boot_tv_type'])==(tv if tv<3 else 1)
            upper=[(at,n,v)for at,n,v in c.memory_writes if 0x400000<=at<0x800000]
            if accepted:
                assert len(c.cache_ops)==512
                assert all(0x440000<=at and at+n<=0x442000 for at,n,v in upper)
                for at in (0x80440000,0x80441fe0):
                    assert all(c.read(at+i*4)==0x55363447 for i in range(8))
                assert all(c.read(at)==0 for at in (s['remote_guest_frames'],s['remote_render_frames'],s['remote_buttons']))
            else:assert not upper and not c.cache_ops
            cases+=1
    callbacks=0
    # VI cannot steal PI from an idle/paused C bridge, even after resume has
    # cleared remote_paused while its acknowledgement is still transmitting.
    for active in (0,1):
        c=cpu();c.allow_rcp_writes=True;c.write(s['remote_bridge_active'],active)
        c.write(s['remote_paused'],0);c.write(s['sram_dirty'],1,1);c.memory_writes=[]
        c.execute(s['update_fps'],stop=s['check_frame'])
        pi=[(at,n,v) for at,n,v in c.memory_writes if 0x4600000<=at<0x4600020]
        assert c.read(s['sram_dirty'],1)==active
        assert (not pi) if active else (len(pi)==3 and pi[-1]==(0x4600008,4,32767))
        cases+=1
    preserved=[i for i in range(1,32) if i not in (26,27)]
    for entry in ('remote_init_bridge','remote_frame_bridge'):
        for size in (0,4194304,8388607,8388609,8388608):
            for paused in (False,True):
                c=cpu();original=c.regs.copy();status=0x10008403 if entry=='remote_frame_bridge' else 0x10008402
                c.cp[12]=status&~1;c.cp[14]=0x80012340
                c.write(s['remote_boot_ram_bytes'],size);c.write(s['remote_saved_status'],status)
                c.write(s['remote_paused'],0);c.memory_writes=[]
                before_hi,before_lo=c.hi,c.lo;seen=[]
                def clobber(c):
                    assert c.regs[29]&0xffffffff==0x804411e0
                    # A C callee returns with its ABI stack restored. The
                    # wrapper must still restore Sodium's different sp value.
                    for i in preserved:
                        if i!=29:c.regs[i]=(0x1122334455667788+i)&((1<<64)-1)
                    c.hi=5;c.lo=7;c.cp[12]=status&~1;c.cp[14]=0x800ffff0
                def start(c):
                    seen.append('start');clobber(c)
                    c.write(s['remote_paused'],int(paused))
                def idle(c):
                    assert c.cp[12]&7==1
                    seen.append('idle');clobber(c);c.write(s['remote_paused'],0)
                c.hooks[s['remote_control_init']]=start;c.hooks[s['remote_control_frame']]=start;c.hooks[s['remote_control_idle']]=idle
                c.execute(s[entry]);assert all(c.regs[i]==original[i] for i in preserved)
                assert c.hi==before_hi and c.lo==before_lo and c.cp[12]==status and c.cp[14]==0x80012340
                assert c.read(s['remote_bridge_active'])==0
                if size==8388608:
                    assert seen==(['start','idle'] if paused and entry=='remote_frame_bridge' else ['start']);callbacks+=len(seen)
                    assert all(at<0x400000 or 0x440020<=at and at+n<=0x441fe0 for at,n,v in c.memory_writes)
                else:
                    assert not seen and all(at<0x400000 for at,n,v in c.memory_writes)
                cases+=1
    # Faults alter the actual linked instructions, not a separate model.
    def word(at):return int.from_bytes(bytes(memory.get((at+i)&0x1fffffff,0) for i in range(4)),'big')
    faults=[]
    for at in range(s['remote_bridge_admitted'],s['remote_reboot_jump'],4):
        w=word(at)
        if w>>26==63 and w>>16&31==1 and w&65535==0:
            faults.append(('truncate_GPR64',at,(w&0x03ffffff)|(43<<26)))
        if w>>26==63 and w&65535==240:faults.append(('omit_HI',at,0))
        if w>>26==16 and w>>21&31==4 and w>>11&31==14:faults.append(('omit_EPC',at,0))
        if w>>26==16 and w>>21&31==4 and w>>16&31==27 and w>>11&31==12:
            faults.append(('omit_Status',at,0))
    assert len(faults)==4
    rejected=[]
    for name,at,replacement in faults:
        bad=memory.copy();bad.update(((at&0x1fffffff)+i,v) for i,v in enumerate(replacement.to_bytes(4,'big')))
        c=CPU(bad);c.regs=[sx32(0x1357+i)^((0x10203+i)<<32) for i in range(32)]
        c.regs[0]=0;c.regs[31]=sx32(0xdead0000);before=c.regs.copy();hi,lo=c.hi,c.lo
        c.cp[12]=0x8402;c.cp[14]=0x80012340;c.write(s['remote_boot_ram_bytes'],8388608)
        c.write(s['remote_saved_status'],0x8403);c.write(s['remote_paused'],0)
        def destructive(c):
            for i in preserved:
                if i!=29:c.regs[i]=0x123456789abcdef0+i
            c.hi=0;c.lo=0;c.cp[14]=0x800ffff0
        c.hooks[s['remote_control_frame']]=destructive
        c.execute(s['remote_frame_bridge'])
        intact=all(c.regs[i]==before[i] for i in preserved) and c.hi==hi and c.lo==lo and c.cp[12]==0x8403 and c.cp[14]==0x80012340
        assert not intact,('linked fault accepted',name);rejected.append(name)
    identity=False
    if a.disabled_elf or a.parent_elf:
        assert a.disabled_elf and a.parent_elf
        disabled,_=load_elf(a.disabled_elf);parent,_=load_elf(a.parent_elf)
        assert disabled==parent,'disabled bench changes parent loaded bytes'
        identity=True
    proof={'passed':True,'cases':cases,'callbacks':callbacks,'all_gpr64_hilo_epc_status_preserved':True,
           'unknown_and_base4MiB_rejected_before_upper_access':True,'upper_lease':[0x440000,0x442000],
           'no_loaded_upper_section':True,'static_end':hex(s['__bss_end']),
           'VI_defers_dirty_SRAM_during_entire_PI_bridge':True,
           'first_fixed_owner':hex(0x80000000+arena),'disabled_loaded_image_identical':identity,
           'emitted_faults_rejected':rejected,'physical_acceptance':False,'commercial_data':False}
    print(json.dumps(proof,indent=2))
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__':main()
