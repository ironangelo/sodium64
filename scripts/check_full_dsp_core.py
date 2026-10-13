#!/usr/bin/env python3
"""Check linked complete-core functions, VR4300 HI/LO spacing and output ABI."""
import argparse,hashlib,json,struct
from pathlib import Path
from test_native_diag_arm import load_elf

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('elf',type=Path)
    p.add_argument('--json-output',type=Path)
    a=p.parse_args();memory,s=load_elf(a.elf)
    functions=[]
    data=a.elf.read_bytes();endian='>' if data[5]==2 else '<'
    hfmt,sfmt=('16sHHIIIIIHHHHHH','IIIIIIIIII') if data[4]==1 else ('16sHHIQQQIHHHHHH','IIQQQQIIQQ')
    h=struct.unpack_from(endian+hfmt,data)
    sections=[struct.unpack_from(endian+sfmt,data,h[6]+i*h[11]) for i in range(h[12])]
    for sec in sections:
        if sec[1]!=2:continue
        strings=sections[sec[6]];names_blob=data[strings[4]:strings[4]+strings[5]]
        for offset in range(sec[4],sec[4]+sec[5],sec[9]):
            if data[4]==1:name,start,length,info,_,_=struct.unpack_from(endian+'IIIBBH',data,offset)
            else:name,info,_,_,start,length=struct.unpack_from(endian+'IBBHQQ',data,offset)
            label=names_blob[name:].split(b'\0',1)[0].decode()
            if info&15==2 and ('SPC_DSP' in label or 'full_dsp_probe' in label or 'colored_owner' in label):
                functions.append((start,length,label))
    names={name for _,_,name in functions}
    assert {'full_dsp_probe_execute','full_dsp_probe_execute_mode'} & names
    assert {'_ZN7SPC_DSP3runEi','_ZN7SPC_DSP9voice_V3cEPNS_7voice_tE',
            '_ZN7SPC_DSP8voice_V4EPNS_7voice_tE','_ZN7SPC_DSP4initEPv',
            '_ZN7SPC_DSP10set_outputEPsi','_ZN7SPC_DSP4loadEPKh'}<=names
    def word(pc):return sum(memory[(pc+i)&0x1fffffff]<<(24-8*i) for i in range(4))
    writers=0
    for start,length,name in functions:
        for pc in range(start,start+length,4):
            w=word(pc)
            if w>>26==0 and w&63 in (24,25,26,27,28,29,30,31):
                writers+=1
                for prior in (pc-4,pc-8):
                    if prior>=start:
                        q=word(prior)
                        assert not (q>>26==0 and q&63 in (16,18)),(name,hex(pc),'MFHI/LO hazard')
    assert writers>10
    assert 'dsp_mix_records' not in s and 'dsp_brr_records' not in s
    proof=dict(passed=True,linked_reference_functions=len(functions),
               straight_line_product_writer_sites=writers,spacing_checked=True,
               ELF_sha256=hashlib.sha256(a.elf.read_bytes()).hexdigest(),
               complete_waveform_timing_or_gameplay_claim=False,commercial_data=False)
    if a.json_output:a.json_output.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
