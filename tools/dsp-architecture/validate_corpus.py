"""Negative controls on actual complete-DSP fixtures and compiled replay."""
from pathlib import Path
import struct
from trace_format import decode_trace, DSP_READ16, DSP_WRITE16, REG_READ, REG_WRITE


def events(data):
    h=struct.unpack_from('>32I',data)
    return h,list(struct.iter_unpack('>4I',data[h[12]:h[15]]))


def word(data,offset,value):
    result=bytearray(data)
    struct.pack_into('>I',result,offset,value)
    return bytes(result)


def remove_event(data,index):
    h,_=events(data)
    start=h[12]+index*16
    result=bytearray(data[:start]+data[start+16:])
    h=list(h);h[13]-=1
    for field in (15,17,19,23):h[field]-=16
    struct.pack_into('>32I',result,0,*h)
    return bytes(result)


def validate_corpus(paths,replay,stage):
    rejected=[]
    for path in paths:
        data=Path(path).read_bytes();h,sequence=events(data)
        bad=[('truncated',data[:-1]),('unknown_version',word(data,8,99)),
             ('overlapping_events',word(data,12*4,h[12]-16)),
             ('opposite_byte_order',b''.join(data[i:i+4][::-1] for i in range(0,128,4))+data[128:]),
             ('unknown_event_kind',word(data,h[12]+4,0xffffffff)),
             ('final_RAM_changed',word(data,h[17],struct.unpack_from('>I',data,h[17])[0]^1)),
             ('PCM_tail_changed',word(data,h[19],struct.unpack_from('>I',data,h[19])[0]^1))]
        phase_index=next(i for i,e in enumerate(sequence) if e[1]==0 and e[0]==11)
        bad.append(('missing_DSP_phase',remove_event(data,phase_index)))
        for name,changed in bad:
            try:decode_trace(changed)
            except ValueError:rejected.append(str(path.name)+':'+name)
            else:raise AssertionError('malformed fixture escaped: '+name)
    normal=Path(paths[2]).read_bytes();h,sequence=events(normal)
    read=next(i for i,e in enumerate(sequence) if e[1]==REG_READ)
    changed_reg=word(normal,h[12]+read*16+12,sequence[read][3]^1)
    # A RAM-only validator cannot establish DSP register/publication semantics.
    decode_trace(changed_reg)
    stress=Path(paths[3]).read_bytes();sh,ss=events(stress)
    first=next(i for i,e in enumerate(ss[:-1]) if e[1:]==(REG_WRITE,0x2d,0xaa)
               and ss[i+1][0]==e[0] and ss[i+1][1:]==(REG_WRITE,0x2d,0xfe))
    p=sh[12]+first*16
    reordered=stress[:p]+stress[p+16:p+32]+stress[p:p+16]+stress[p+32:]
    decode_trace(reordered)
    write=next(i for i,e in enumerate(sequence) if e[1]==DSP_WRITE16)
    read16=next(i for i,e in enumerate(sequence) if e[1]==DSP_READ16)
    semantic=[('register_value_changed',changed_reg),('same_clock_register_order',reordered),
              ('enabled_echo_write_dropped',remove_event(normal,write)),
              ('DSP_word_read_changed',word(normal,h[12]+read16*16+12,sequence[read16][3]^1)),
              ('PCM_tail_changed',word(normal,h[19],struct.unpack_from('>I',normal,h[19])[0]^1))]
    core_rejected=[]
    for name,changed in semantic:
        path=Path(stage)/(name+'.s64darc');path.write_bytes(changed)
        result=replay(path)
        assert result.returncode!=0 and 'FAIL ' in result.stderr,(name,result.stdout,result.stderr)
        core_rejected.append(name)
        print('REPLAY REJECTED '+name+': '+result.stderr.strip())
    return {'malformed_fixtures_rejected':rejected,
            'complete_core_semantic_mutants_rejected':core_rejected,
            'RAM_only_reader_does_not_establish_DSP_register_semantics':True}
