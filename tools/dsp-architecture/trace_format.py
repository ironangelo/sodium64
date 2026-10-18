#!/usr/bin/env python3
"""Strict structural and chronological RAM validation for original DSP fixtures.

Complete DSP state/PCM replay is additionally performed by fixture.cpp. A valid
file alone establishes neither a complete RSP backend nor native performance.
"""
from collections import Counter
from pathlib import Path
import struct

PHASE, DSP_READ8, DSP_READ16, DSP_WRITE16, FETCH, RAM_READ8, RAM_WRITE8, REG_READ, REG_WRITE, PCM, KON_OBSERVE = range(11)
NAMES = ('phase','DSP_read8','DSP_read16','DSP_write16','synthetic_fetch',
         'producer_read8','producer_write8','register_read','register_write',
         'PCM_frame','KON_observation')


def align16(value):
    return (value+15)&~15


def decode_trace(data):
    def check(condition, message):
        if not condition:
            raise ValueError(message)
    check(128 <= len(data) <= 32*1024*1024, 'file size')
    h = struct.unpack_from('>32I',data)
    check(data[:8] == b'S64DARC1' and h[2:4] == (1,128),'format/version')
    check(h[4] < 4 and 32 <= h[5] <= 2048 and h[6] == h[5]*32 and h[7] == 32000,'scenario/clocks')
    check(h[8:10] == (128,65536) and h[10] == 65664,'initial RAM')
    check(0 < h[11] <= 640 and h[12] == align16(h[10]+h[11]),'initial state')
    check(h[13] > 0 and h[14] == 16 and h[15] == h[12]+h[13]*16,'event extent')
    check(0 < h[16] <= 640 and h[17] == align16(h[15]+h[16]),'final state')
    check(h[18] == 65536 and h[19] == h[17]+65536 and h[20] == h[5]*4,'final RAM/PCM')
    check(h[21:24] == (0,64,len(data)) and h[23] == h[19]+h[20],'complete file extent')
    check(h[24] == (1 if h[4] == 0 else 255) and h[25] == 0xffffffff,'voice/phase contract')
    check(h[26] == 0x01020304 and not any(h[27:]),'byte order/reserved words')
    check(not any(data[h[10]+h[11]:h[12]]) and not any(data[h[15]+h[16]:h[17]]),'nonzero padding')
    ram = bytearray(data[h[8]:h[8]+65536])
    check(len(ram) == 65536,'truncated initial RAM')
    events = memoryview(data)[h[12]:h[15]]
    phases = Counter()
    kinds = Counter()
    producer_bus = Counter()
    last_clock, phase_seen, samples, echo_fetches = -1, False, 0, 0
    for clock,kind,address,value in struct.iter_unpack('>4I',events):
        check(last_clock <= clock < h[6], 'event time order')
        if clock != last_clock:
            check(last_clock == -1 or phase_seen, 'clock without DSP phase')
            check(clock == last_clock+1, 'missing DSP clock')
            phase_seen = False
        check(kind < len(NAMES),'unknown event kind')
        if kind == PHASE:
            check(not phase_seen and address == clock%32 and value == 0,'phase event')
            phase_seen = True
            phases[address] += 1
        elif kind in (DSP_READ8,DSP_READ16,DSP_WRITE16,PCM):
            check(phase_seen,'DSP access before its phase')
        else:
            check(not phase_seen,'producer access after current DSP phase')
        if kind in (DSP_READ8,FETCH,RAM_READ8,RAM_WRITE8):
            check(address < 65536 and value < 256,'byte access range')
            if kind == RAM_WRITE8:
                ram[address] = value
            else:
                check(ram[address] == value,'chronological RAM byte mismatch')
                if kind == FETCH and 0xe000 <= address < 0xf000:
                    echo_fetches += 1
        elif kind in (DSP_READ16,DSP_WRITE16):
            check(address <= 65534 and address%2 == 0 and value < 65536,'word access range')
            if kind == DSP_WRITE16:
                ram[address:address+2] = value.to_bytes(2,'little')
            else:
                check(int.from_bytes(ram[address:address+2],'little') == value,
                      'chronological RAM word mismatch')
        elif kind in (REG_READ,REG_WRITE):
            check(address < 128 and value < 256,'register access range')
        elif kind == PCM:
            check(address == samples and clock%32 == 27,'PCM publication order')
            check(struct.unpack_from('>I',data,h[19]+samples*4)[0] == value,'PCM payload mismatch')
            samples += 1
        elif kind == KON_OBSERVE:
            check(address == 0 and value in (0,1),'KON observation')
        kinds[NAMES[kind]] += 1
        if kind in (FETCH,RAM_READ8,RAM_WRITE8,REG_READ,REG_WRITE):
            producer_bus[clock] += 1
        last_clock = clock
    check(last_clock == h[6]-1 and phase_seen,'unfinished final clock')
    check(len(phases) == 32 and all(phases[p] == h[5] for p in range(32)),'complete32-phase execution')
    check(samples == h[5],'complete stereo output')
    check(ram == data[h[17]:h[17]+65536],'complete chronological final RAM')
    peak_bus = max(producer_bus.values(),default=0)
    check(h[4] == 3 or peak_bus <= 1,'nominal producer exceeded one bus access per clock')
    return {'scenario':h[4],'clocks':h[6],'frames':h[5],'events':h[13],
            'initial_state_bytes':h[11],'final_state_bytes':h[16],
            'all32_phases':True,'chronological_RAM_exact':True,
            'echo_region_synthetic_fetches':echo_fetches,
            'max_producer_bus_operations_per_clock':peak_bus,
            'producer_case':'stress' if h[4] == 3 else 'synthetic nominal',
            'event_counts':dict(kinds),'bytes':len(data)}


def read_trace(path):
    return decode_trace(Path(path).read_bytes())
