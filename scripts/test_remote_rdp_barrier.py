#!/usr/bin/env python3
"""Execute the actual diagnostic RDP barrier and reject broken ordering mutants."""
import argparse,json,os,re,subprocess,tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cc',default=os.environ.get('CC','gcc'))
    p.add_argument('--json-output',type=Path)
    p.add_argument('--rsp-elf',type=Path,nargs=2)
    a=p.parse_args();root=Path(__file__).resolve().parents[1]
    header=(root/'src/remote_rdp_barrier.h').read_text()
    mutants={
        'missing_sync_full':('0x29000000','0x27000000'),
        'missing_current_wait':('!wait_io(0xa4100008,0x00ffffff,0x00441ca8,ticks)','0'),
        'missing_pipe_wait':('!wait_io(0xa410000c,0x770,0,ticks)','0'),
        'missing_xbus_restore':('RDP_WRITE(0xa410000c,(state&1)?2:1);','RDP_WRITE(0xa410000c,1);'),
        'discard_previous_irq':('if(!pending)RDP_WRITE(0xa4300000,0x800);','RDP_WRITE(0xa4300000,0x800);'),
    }
    with tempfile.TemporaryDirectory(prefix='s64-rdp-barrier-') as directory:
        tmp=Path(directory);exe=tmp/('barrier.exe' if os.name=='nt' else 'barrier')
        for label,mutation in [('production',None),*mutants.items()]:
            source=header
            if mutation:
                old,new=mutation;assert source.count(old)==1;source=source.replace(old,new)
            (tmp/'remote_rdp_barrier.h').write_text(source)
            command=[a.cc,'-std=c11','-O1','-Wall','-Wextra','-Werror','-I'+str(tmp),
                     str(root/'scripts/fixtures/remote_rdp_barrier_host.c'),'-o',str(exe)]
            compiled=subprocess.run(command,capture_output=True,text=True)
            assert compiled.returncode==0,compiled.stdout+compiled.stderr
            result=subprocess.run([str(exe)],capture_output=True,text=True)
            if label=='production':
                assert result.returncode==0,result.stdout+result.stderr
                match=re.search(r'PASS cases=(\d+)',result.stdout);assert match
                cases=int(match[1]);print(result.stdout,end='')
            else:assert result.returncode!=0,'mutant escaped: '+label
    proof={'passed':True,'cases':cases,'rejected_mutants':list(mutants),
           'production_header':True,'hardware_model':True,'physical_acceptance':False}
    if a.rsp_elf:
        from linked_cpu_regression import load_elf
        for path in a.rsp_elf:
            memory,symbols=load_elf(path)
            def word(at):return int.from_bytes(bytes(memory[(at+i)&0x1fffffff] for i in range(4)),'big')
            expected=[0x40085800,0x31080040,0x1500fffd,0x40844000,0x40854800,0x03e00008,0]
            assert [word(symbols['rdp_send']+i*4) for i in range(7)]==expected
            for pc in range(0xa4001000,0xa4002000,4):
                instruction=word(pc)
                if instruction>>26==16 and (instruction>>21)&31==0:
                    assert (instruction>>11)&31 not in (8,9,10),'RSP depends on old DP pointer'
        proof['both_rsp_banks_restart_START_END_without_pointer_reads']=True
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print('RDP_BARRIER rejected_mutants='+str(len(mutants)))
if __name__=='__main__':main()
