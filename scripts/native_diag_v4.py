#!/usr/bin/env python3
"""Private S64D v4 decoder. Exact cadence/waits and classified observations.

The CPU can prepare N+1 while the RSP renders N. A completed-boundary interval
contains the earlier VI wait and the later RSP wait; neither is an exact RSP
render duration. Sampling and waits overlap. Do not sum occupancy percentages
or infer a named game scene / arithmetic operation from these records.
"""
from __future__ import annotations
import struct

CPU_MODULES=('s_cpu','apu_static_or_jit','dsp','dma','ppu','rsp_wait','vi_wait','other')
STAGES=('rsp_dma_wait','rsp_command_fetch_wait','rsp_texture_retire_wait')
RSP_STAGES=('halted','unknown_or_bank_transition','dma_wait','rdp_wait','composition_phase_or_mode7_window','general_math','direct_composition','source_draw_or_resident_control')
RSP_BANKS={0:'unknown',1:'main',2:'mode7_draw',3:'hcomp_phase',4:'hcomp_fast',5:'hcomp_math',6:'mode7_window',7:'hcomp_setup'}

def parse_v4(blob,h,order,second_fields):
    head=0x2000;hz=h['count_hz']
    stride,overflow,event_bytes,second_bytes=struct.unpack_from('>4I',blob,head+0x128)
    marker,nframes,capacity,frame_bytes,baseline,hook_ticks,hook_max=struct.unpack_from('>7I',blob,head+0x138)
    period,guest_exp,baseline_ordinal=struct.unpack_from('>3I',blob,head+0x188)
    if (h['sample_capacity'],h['event_capacity'],stride,event_bytes,second_bytes,marker,capacity,frame_bytes,period)!=(256,160,32,40,64,0x46524d34,1280,12,5859375):
        raise ValueError('unexpected v4 measurement geometry')
    bookend_ticks,bank_protocol=struct.unpack_from('>2I',blob,head+0x1d8)
    if (bookend_ticks,bank_protocol)!=(46875,0x42414e34):raise ValueError('v4 RSP bank protocol invalid')
    if overflow&~31 or h['event_count']>160 or h['seconds_count']>20 or nframes>1280:
        raise ValueError('v4 count/overflow invalid')
    if guest_exp>3:raise ValueError('v4 overlaps guest SRAM')
    retained=min((h['sample_count']+31)//32,256)
    if h['pc_next_byte']!=retained*4:raise ValueError('v4 CPU count/cursor disagree')
    if h['sample_count']>8192 and not overflow&2:raise ValueError('v4 CPU overflow was not marked')
    body=blob[:head]+blob[head+512:]
    if sum(struct.unpack(f'>{len(body)//4}I',body))&0xffffffff!=h['body_sum32']:
        raise ValueError('save payload checksum mismatch; reject truncated/stale capture')
    if baseline>h['elapsed_ticks'] or baseline_ordinal>h['frames_completed']:
        raise ValueError('v4 frame baseline invalid')
    if baseline_ordinal and baseline_ordinal!=1:raise ValueError('v4 manual-arm baseline ordinal invalid')
    if not overflow&8 and nframes!=max(0,h['frames_completed']-baseline_ordinal):
        raise ValueError('v4 completed-frame totals disagree')
    if nframes and not baseline_ordinal:raise ValueError('v4 completed-frame baseline missing')
    h.update(byte_order=order,elapsed_seconds_count_domain=h['elapsed_ticks']/hz,
        observer_fraction=h['observer_ticks']/max(1,h['elapsed_ticks']),
        observer_frame_hook_ticks=hook_ticks,observer_frame_hook_max_ticks=hook_max,
        observer_frame_hook_fraction=hook_ticks/max(1,h['elapsed_ticks']),
        observer_measured_fraction=(h['observer_ticks']+hook_ticks)/max(1,h['elapsed_ticks']),
        observer_measurement_is_complete=False,
        cpu_epc_instruction=h['cpu_epc']+(4 if h['cpu_cause']&0x80000000 else 0),
        capture_via='direct wait watchdog' if h['direct_wait_pc'] else 'timer watchdog',
        retained_cpu_stride=stride,retained_cpu_samples=retained,
        retained_cpu_sampling_hz_nominal=hz/h['sample_interval']/stride,
        occupancy_sampling_hz=hz/h['sample_interval'],observation_hz_nominal=hz/period,
        trace_overflow_flags=overflow,terminal_memory_snapshots=False,
        sp_pc_meaningful_after_halt=False,guest_cpu_pc_raw=None,
        trace_covers_whole_interval=not bool(overflow),frame_records=nframes,
        frame_capacity=capacity,frame_baseline_elapsed_ticks=baseline,
        frame_baseline_ordinal=baseline_ordinal,initial_partial_boundary_excluded=True,
        guest_sram_header_exp=guest_exp,cpu_other_includes_vram_wait=True)
    pcs=list(struct.unpack_from(f'>{retained}I',blob,0x2200))
    frames=[];previous=baseline
    for i in range(nframes):
        tick,rsp,vi=struct.unpack_from('>3I',blob,0x2600+i*12)
        dt=tick-previous
        if dt<=0 or tick>h['elapsed_ticks']:raise ValueError('v4 non-monotonic frame cadence')
        if rsp+vi>dt:raise ValueError('v4 waits exceed completed-boundary interval')
        frames.append(dict(sequence=i+1,completed_boundary_ordinal=i+1+baseline_ordinal,
            elapsed_ticks=tick,interval_start_ticks=previous,interval_ticks=dt,
            interval_ms=dt*1000/hz,cpu_rsp_wait_ticks=rsp,cpu_vi_wait_ticks=vi,
            cpu_rsp_wait_ms=rsp*1000/hz,cpu_vi_wait_ms=vi*1000/hz,
            remainder_ticks=dt-rsp-vi,
            remainder_meaning='unclassified CPU/preparation/UI/interrupt elapsed time; not exact active CPU time',
            completed_cadence_is_presentation_fps=False,
            interval_over_60hz_nominal_budget=dt>hz/60))
        previous=tick
    events=[];irq=0;previous=dict(elapsed_ticks=0,frames_completed=0,sections_created=0)
    for i in range(h['event_count']):
        offset=0x6200+i*40
        tick,sections,fc,pc,sp,flags,dp=struct.unpack_from('>2I2H2BH',blob,offset)
        controls=struct.unpack_from('>6BH',blob,offset+16)
        modules=dict(zip(CPU_MODULES,struct.unpack_from('>8B',blob,offset+24)))
        rsp_stages=dict(zip(RSP_STAGES,struct.unpack_from('>8B',blob,offset+32)))
        if not overflow&16 and sum(rsp_stages.values())!=sum(modules.values()):raise ValueError('v4 RSP/CPU observation totals disagree')
        bank=pc>>12;pc&=0xfff
        if bank not in RSP_BANKS or sp&1 and (pc or bank):raise ValueError('v4 RSP snapshot invalid')
        irq+=sum(modules.values())
        if tick<=previous['elapsed_ticks'] or fc<previous['frames_completed'] or sections<previous['sections_created'] or tick>h['elapsed_ticks']:
            raise ValueError('v4 non-monotonic observation')
        row=dict(sequence=i+1,elapsed_ticks=tick,frames_completed=fc,sections_created=sections,
            irq_sample_count=irq,sp_pc_live=pc,sp_status=sp,dp_status=dp,
            sp_pc_observational=True,sp_pc_overlay_identity_known=False,
            sp_pc_overlay_identity_candidate=bank!=0,
            rsp_bank_id=bank,rsp_bank=RSP_BANKS[bank],rsp_stage_samples=rsp_stages,
            rsp_stage_counts_are_sampled=True,rsp_bank_bookend_max_ticks=bookend_ticks,
            cpu_module_samples=modules,module_counts_saturated=bool(overflow&16),
            sp_status_signals_4_to_7_omitted=True,
            ppu_live_sample=dict(bg_mode=flags&15,policy=(flags>>4)&3,screen=(flags>>6)&1,
                stat_flags_force_blank=bool(flags&128),other_stat_flags_omitted=True,
                cgwsel=controls[0],cgadsub=controls[1],ts=controls[2],tm=controls[3],
                tsw=controls[4],tmw=controls[5],band_rows=controls[6],atomic=False,
                hardware_access_validated=False),
            interval_seconds=(tick-previous['elapsed_ticks'])/hz,
            completed_frames_in_interval=fc-previous['frames_completed'],
            sections_in_interval=sections-previous['sections_created'],
            short_interval_fps_authority=False)
        events.append(row);previous=row
    seconds=[];previous=dict(elapsed_ticks=0,frames_completed=0,sections_created=0)
    for i in range(h['seconds_count']):
        offset=0x7b00+i*64
        tick,fc,sections=struct.unpack_from('>3I',blob,offset)
        counts=struct.unpack_from('>9H',blob,offset+12);seq=struct.unpack_from('>H',blob,offset+30)[0]
        modules=dict(zip(CPU_MODULES,struct.unpack_from('>8H',blob,offset+32)))
        vram,*stages=struct.unpack_from('>4H',blob,offset+48)
        observer,hook=struct.unpack_from('>2I',blob,offset+56)
        if seq!=i+1 or tick<=previous['elapsed_ticks'] or fc<previous['frames_completed'] or sections<previous['sections_created'] or tick>h['elapsed_ticks']:
            raise ValueError('v4 non-monotonic second')
        if sum(counts[1:5])!=counts[0] or sum(modules.values())!=counts[0] or any(c>counts[0] for c in counts[5:]) or sum(stages)>counts[5]:
            raise ValueError('v4 occupancy/module buckets disagree')
        if modules['rsp_wait']!=counts[1] or modules['vi_wait']!=counts[2] or modules['apu_static_or_jit']<counts[3] or vram>modules['ppu']:
            raise ValueError('v4 CPU classifications disagree')
        row=dict(zip(second_fields[5:14],counts));dt=tick-previous['elapsed_ticks']
        row.update(sequence=seq,elapsed_ticks=tick,frames_completed=fc,sections_created=sections,
            duration_seconds_count_domain=dt/hz,completed_frames_in_interval=fc-previous['frames_completed'],
            completed_fps_count_domain=(fc-previous['frames_completed'])*hz/dt,
            cpu_module_samples=modules,cpu_vram_wait_subset=vram,
            rsp_resident_wait_samples=dict(zip(STAGES,stages)),
            observer_ticks=observer,observer_frame_hook_ticks=hook)
        seconds.append(row);previous=row
    partial=struct.unpack_from('>9I',blob,head+0x100)
    pm=dict(zip(CPU_MODULES,struct.unpack_from('>8I',blob,head+0x158)))
    pe=dict(zip(CPU_MODULES,struct.unpack_from('>8I',blob,head+0x198)))
    vram,*stages=struct.unpack_from('>4I',blob,head+0x178)
    if sum(partial[1:5])!=partial[0] or sum(pm.values())!=partial[0] or any(x>partial[0] for x in partial[5:]) or sum(stages)>partial[5]:
        raise ValueError('v4 partial CPU occupancy/module buckets disagree')
    if pm['rsp_wait']!=partial[1] or pm['vi_wait']!=partial[2] or pm['apu_static_or_jit']<partial[3] or vram>pm['ppu']:
        raise ValueError('v4 partial CPU classifications disagree')
    if sum(x['samples'] for x in seconds)+partial[0]!=h['sample_count']:
        raise ValueError('v4 whole-interval IRQ totals disagree')
    pr=dict(zip(RSP_STAGES,struct.unpack_from('>8I',blob,head+0x1b8)))
    if not overflow&16 and sum(pr.values())!=sum(pe.values()):raise ValueError('v4 partial RSP/CPU observation totals disagree')
    h['partial_observation_rsp_stage_samples']=pr
    h['rsp_stage_samples_total']={name:sum(e['rsp_stage_samples'][name] for e in events)+pr[name] for name in RSP_STAGES}
    if not overflow&16 and irq+sum(pe.values())!=h['sample_count']:
        raise ValueError('v4 observation IRQ totals disagree')
    h['partial_window']=dict(zip(second_fields[5:14],partial))
    h['partial_window'].update(cpu_module_samples=pm,cpu_vram_wait_subset=vram,
        rsp_resident_wait_samples=dict(zip(STAGES,stages)))
    h['partial_observation_cpu_module_samples']=pe
    h['cpu_vram_wait_subset_total']=sum(x['cpu_vram_wait_subset'] for x in seconds)+vram
    timeline=[];j=0
    for i,pc in enumerate(pcs):
        ordinal=i*stride+1
        while j<len(events) and events[j]['irq_sample_count']<ordinal:j+=1
        timeline.append(dict(pc=pc,irq_sequence=ordinal,
            elapsed_ticks_lower=events[j-1]['elapsed_ticks'] if j else 0,
            elapsed_ticks_upper=events[j]['elapsed_ticks'] if j<len(events) else h['elapsed_ticks'],
            bounds_valid=not bool(overflow&16)))
    # Completed cadence differs from actual presentation. Rank intervals as
    # candidates, never report 1/delta as an authoritative on-screen FPS.
    worst=sorted(frames,key=lambda x:x['interval_ticks'],reverse=True)[:12]
    for frame in frames:
        indices=[e['sequence'] for e in events if e['elapsed_ticks']>frame['interval_start_ticks'] and e['elapsed_ticks']-e['interval_seconds']*hz<frame['elapsed_ticks']]
        frame['overlapping_observation_sequences']=indices
    h['frame_analysis']=dict(worst_boundary_intervals=worst,
        all_full_boundaries_retained=not bool(overflow&8),
        completed_cadence_is_presentation_fps=False,
        shader_operation_counts_available=False,
        rsp_overlay_stage_attribution_available=False,
        rsp_overlay_pc_validated_by_epoch=False,
        rsp_overlay_stage_candidates_retained=True,
        rsp_bank_bookend_protocol_present=True,
        live_dmem_access_hardware_validated=False,
        arithmetic_operands_or_exact_operation_counts_available=False,
        root_cause_is_not_automatically_confirmed=True)
    return dict(header=h,frames=frames,events=events,seconds=seconds,cpu_samples=pcs,cpu_timeline=timeline),blob

def render_v4(result):
    h=result['header'];hz=h['count_hz']
    lines=[f"Full completed boundaries: {len(result['frames'])}/1280; first partial boundary excluded; overflow={h['trace_overflow_flags']}",
        f"8 Hz workload observations: {len(result['events'])}/160; every IRQ enters CPU and RSP stage counts.",
        f"Measured observer bodies (ISR + frame helper): {h['observer_measured_fraction']*100:.3f}%; incomplete perturbation budget.",
        'CPU/RSP overlap; sampled module counts and exact waits must not be added.',
        'Worst completed-boundary intervals: end seconds | elapsed ms | CPU RSP wait ms | CPU VI wait ms | remainder ms']
    for f in h['frame_analysis']['worst_boundary_intervals']:
        lines.append(f"  {f['elapsed_ticks']/hz:7.3f} | {f['interval_ms']:7.3f} | {f['cpu_rsp_wait_ms']:7.3f} | {f['cpu_vi_wait_ms']:7.3f} | {f['remainder_ticks']*1000/hz:7.3f}")
    lines.append('Remainder includes preparation/UI/interrupts; it is not measured active CPU time.')
    totals={name:sum(s['cpu_module_samples'][name] for s in result['seconds'])+h['partial_window']['cpu_module_samples'][name] for name in CPU_MODULES}
    lines.append('All-IRQ CPU modules: '+', '.join(f'{k}={v}' for k,v in totals.items()))
    lines.append('All-IRQ RSP stage candidates (not hardware-validated): '+', '.join(f'{k}={v}' for k,v in h['rsp_stage_samples_total'].items()))
    lines.append('v4 reads live DMEM for bank/PPU candidates, including sub-word reads. Epoch bookends do not validate that hardware access. Do not use bank/stage/PPU candidates as exact causal evidence; use CPU samples, completed-boundary timing and explicit RSP/VI waits.')
    return lines
