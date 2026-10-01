#!/usr/bin/env python3
"""Decode S64C per-VI trace and preserved S64V; physical hue needs phase video."""
import argparse
import json
import struct
from pathlib import Path
from decode_stage2_probe import HEAD_NAMES, OFFSET, SIZE, band_info, qualify_workload, write_png

MAGIC = 0x53363443
FB = [0xF2300, 0x113000, 0x133D00]
COLORS = [0x7BC1, 0x07C1, 0xF801, 0x003F, 0xFFFF, 0x0001]

def normalize(blob):
    if len(blob) != 32768:
        raise ValueError('expected complete 32768-byte color save')
    if blob[:4] == b'S64C':
        return blob, 'canonical big-endian'
    if blob[:4] == b'C46S':
        return b''.join(blob[i:i+4][::-1] for i in range(0,len(blob),4)), '32-bit word-swapped'
    raise ValueError('missing S64C: use the decoder matching this ROM')

def decode(blob):
    b, fmt = normalize(blob)
    h = struct.unpack_from('>64I', b)
    if h[:6] != (MAGIC,1,32768,1,320,48) or h[9:12] != (256,OFFSET,SIZE):
        raise ValueError('unsupported/incomplete S64C geometry')
    attempted, stored, dropped = h[6:9]
    if not 1 <= stored <= 320 or attempted != stored + dropped:
        raise ValueError('invalid trace counts')
    if h[41] != 3 or h[40] != 7 or h[12:14] != (0x202,0x3202):
        raise ValueError('frozen comparisons missing/invalid')
    if h[18] not in FB or h[18] != h[19]:
        raise ValueError('frozen phase origins differ')
    for start,end in ((h[14],h[15]),(h[16],h[17])):
        if not 93750000 <= ((end-start)&0xFFFFFFFF) <= 100000000:
            raise ValueError('frozen hold too short')
    refs = [list(struct.unpack_from('>6H',b,o)) for o in (80,92)]
    if h[37] != 0x15040800:
        raise ValueError('Road settings changed')
    raw=b[OFFSET:OFFSET+SIZE]
    ph=dict(zip(HEAD_NAMES,struct.unpack_from('>32I',raw)))
    if (ph['magic'],ph['version'],ph['size'],ph['complete'],ph['valid']) != (0x53363456,1,SIZE,1,7):
        raise ValueError('missing/incomplete/undrained S64V')
    if not ph['sp_status']&1 or ph['dp_status']&0x170 or ph['dp_current']!=ph['dp_end']:
        raise ValueError('pending final SP/DP work')
    if ph['sp_dma_busy'] or ph['sp_dma_full'] or ph['vi_width']!=280:
        raise ValueError('invalid final DMA/VI width')
    if [ph['fb1'],ph['fb2'],ph['fb3']]!=FB or ph['vi_origin']!=h[18]:
        raise ValueError('final probe source differs from held source')
    if ph['dsp_pointer']>=8192 or ph['dsp_pointer']%4:
        raise ValueError('invalid PCM pointer')
    pixels=list(struct.unpack_from('>4096H',raw,0x80))
    rows=[list(struct.unpack_from('>256H',raw,0x2080+i*512)) for i in range(3)]
    if rows[FB.index(ph['vi_origin'])]!=pixels[:256]:
        raise ValueError('independent selected buffer copy disagrees')
    pcm=raw[0x2D10:0x3D10]
    records=[]
    for i in range(stored):
        r=struct.unpack_from('>12I',b,256+48*i)
        seq,ticks,origin,producer,bounds,sp,dp,current,end,upper,lower,audio=r
        if seq != i+1:
            raise ValueError('nonconsecutive VI records')
        if i and not 0 < ((ticks-records[-1]['ticks'])&0xFFFFFFFF) < 10000000:
            raise ValueError('nonmonotonic or implausibly sparse VI clock')
        left,right=bounds>>24,(bounds>>16)&255
        from make_gate_c_stage1 import window
        phases=[n for n in range(256) if window(n)==(left,right)]
        valid_owner=origin in FB and producer>0 and not bounds&65535 and len(phases)==1
        records.append(dict(vi=seq,ticks=ticks,origin=origin,producer=producer,
            window=[left,right],phases=phases,owner_valid=valid_owner,
            sp_status=sp,dp_status=dp,dp_current=current,dp_end=end,
            outside_color=upper>>16,inside_color=upper&65535,
            lower_red=lower>>16,reference_yellow=lower&65535,
            dsp_pointer=audio>>16,enabled=(audio>>8)&255,ready_depth=audio&255,
            memory_colors_match=valid_owner and upper==0x7BC10001 and lower==0xF8017BC1))
    budgets=list(h[32:37])
    result=dict(format=fmt,header=dict(attempted=attempted,stored=stored,dropped=dropped,
        control_a=h[12],control_b=h[13],origin=h[18],
        phase_a_ticks=[h[14],h[15]],phase_b_ticks=[h[16],h[17]],
        reference_colors=refs,hook_body_max_ticks=h[28],hook_body_total_ticks=h[29],
        producer_count=h[30],unknown_owner_events=h[42],invalid_origin_events=h[43]),
        frame_budgets=budgets,band=band_info(pixels),probe_header=ph,
        trace_complete=dropped==0 and attempted==stored,
        memory_colors_match=all(r['memory_colors_match'] for r in records),
        references_match=refs==[COLORS,COLORS],records=records,
        limitations=['Sparse samples cannot rule out every transient lower stripe',
            'Per-VI trace starts after warmup and ends with five measured VI windows',
            'Hook timing excludes register save/restore and producer swatch overhead',
            'Physical display hue requires video of live/frozen A/frozen B',
            'Instrumented diagnostic cadence is not baseline performance'])
    return result,b,raw,pixels,pcm

def qualify(result,raw,mixed):
    if not result['trace_complete']:
        raise ValueError('trace dropped VI records')
    if not result['memory_colors_match'] or not result['references_match']:
        raise ValueError('lab selected colors/ownership differ')
    if not 295 <= result['header']['stored'] <= 305:
        raise ValueError('missing measured VI events')
    if result['frame_budgets'] != [60]*5 or not result['band']['reference_matches']:
        raise ValueError('lab cadence/final band differs')
    producers=[r['producer'] for r in result['records']]
    if any(b-a not in (0,1) for a,b in zip(producers,producers[1:])) or len(set(producers))<290:
        raise ValueError('displayed producer trace skips/stalls')
    if {p for r in result['records'] for p in r['phases']} != set(range(256)):
        raise ValueError('missing displayed guest phases')
    for r in result['records']:
        if r['dsp_pointer']>=8192 or r['dsp_pointer']%4 or r['ready_depth']>2:
            raise ValueError('per-VI queue/PCM pointer invalid')
        if r['enabled'] != (255 if mixed else 0):
            raise ValueError('per-VI voice activity differs')
    legacy={'header':result['probe_header'],'band':result['band'],'frame_budgets':result['frame_budgets']}
    return qualify_workload(legacy,raw,mixed)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('save',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    result,b,raw,pixels,pcm=decode(args.save.read_bytes())
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.output/'native-probe.bin').write_bytes(raw)
    write_png(args.output/'native-pixels.png',pixels)
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
if __name__=='__main__': main()
