#!/usr/bin/env python3
"""R44 linked selector, Setup handoff and retired command/alpha ownership.

Numeric fixtures only. R42 supplies physical rectangle feasibility; this does
not rasterize Mode7 edges or claim native game fidelity/performance.
"""
import argparse
import json
import struct
from pathlib import Path

from check_rsp_branch_delay_slots import read_text
from test_gate_c_cgram_rsp_consumer_clean_contract import parse_macros
from test_hcomp_eligibility_tags import DepthVM
from test_hcomp_packed_math import seeds
from test_hcomp_sub_presence import section
from test_rsp_math_dma import MathVM, ROOT, put, symbols

STOP = 0x794


class PacketVM(DepthVM):
    def cop0_write(self, register, value):
        if register == 9:
            assert self.pending_fetch is None
            assert 0 <= self.rdp_start < value <= 4096 and value % 8 == 0
            self.pending_fetch = dict(start=self.rdp_start, end=value, remaining=self.delay)
            self.current = value if self.stale_current else self.rdp_start
        else:
            super().cop0_write(register, value)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('build', type=Path)
    ap.add_argument('--baseline', type=Path, help='also execute the retained fixed-color regression cases')
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    addr = parse_macros(ROOT).name
    images = {name: read_text(args.build / ('src/rsp_' + name + '.elf'))[1]
              for name in ('main', 'hcomp', 'hcomp_fast', 'hcomp_setup')}
    syms = {name: symbols(args.build / ('src/rsp_' + name + '.elf')) for name in images}
    initial = section(args.build / 'src/rsp_main.elf', '.data')
    descriptor, packet = addr('HCOMP_SUB_ALPHA_DESC'), addr('HCOMP_PROOF_RDP_CMDS')
    assert syms['hcomp_fast']['hcomp_sub_alpha_select'] == 0x768
    assert syms['hcomp_setup']['hcomp_setup_copy'] == addr('RSP_CONTEXT_SWITCH_ENTRY') - 0x1000
    assert syms['main']['hcomp_sub_alpha_mode_send'] == addr('RSP_SUB_ALPHA_MODE_SEND') - 0x1000
    assert all(len(images[n]) == (4096 if n == 'main' else 1000) for n in images)
    selector_cases = setup_cases = command_cases = transition_cases = 0
    def slot(name):
        code = bytearray(images['main'])
        code[0x3a8:0x790] = images[name]
        return code
    for mode in range(16):
        d = bytearray(initial)
        d[addr('BG_MODE')] = mode
        regs = [0xa5000000+i for i in range(32)]
        regs[0], regs[31] = 0, STOP
        before = bytes(d)
        vm = MathVM(slot('hcomp_fast'), d, bytearray(), regs, seeds(), 7,
                    set(range(descriptor, descriptor+2)))
        vm.pc = syms['hcomp_fast']['hcomp_sub_alpha_select']
        vm.execute(STOP)
        expected = 0x25 if mode & 7 == 7 else 0x1001
        assert int.from_bytes(d[descriptor:descriptor+2], 'big') == expected
        assert all(d[i] == before[i] for i in range(4096) if not descriptor <= i < descriptor+2)
        selector_cases += 1
        for ts in (0, 1, 2, 16, 31):
            state = bytearray(d)
            state[addr('HCOMP_EFFECTIVE_TS')] = ts
            struct.pack_into('>I', state, addr('HCOMP_BAND_Y'), 8)
            regs = [0xa5000000+i for i in range(32)]
            regs[0], regs[3], regs[28], regs[29] = 0, 0xff, 0, 0
            regs[30] = 0xcafeffff
            vm = MathVM(slot('hcomp_setup'), state, bytearray(), regs, seeds(), 7, set())
            vm.pc = syms['hcomp_setup']['hcomp_vector_constants']
            vm.execute(0xf7c)
            assert regs[30] == (0x10 if ts and mode & 7 != 7 else 0), 'Setup alpha state'
            assert regs[25] == 0x13b0, 'Setup must return to Math entry'
            setup_cases += 1
        for screen in (0, 1):
            for delay in (2, 9, 31):
                for kind in ('compact', 'raw', 'main-transition'):
                    state = bytearray(d)
                    state[addr('HCOMP_SCREEN')] = screen
                    state[addr('CGADSUB')] = 0x20
                    starts = {'compact': (packet, packet+32),
                              'raw': (addr('RDP_FRAME'), addr('RDP_FRAME')+8),
                              'main-transition': (packet+8, packet+24)}
                    start, end = starts[kind]
                    regs = [0]*32
                    regs[4], regs[5], regs[31] = start, end, STOP
                    owners = set(range(packet+14, packet+16))
                    owners.update(range(addr('SCRN_DATA'), addr('SCRN_DATA')+8))
                    vm = PacketVM(images['main'], state, regs, owners, delay, True)
                    vm.pc = syms['main']['hcomp_sub_alpha_mode_send']
                    vm.execute(STOP)
                    assert vm.pending_fetch is None and len(vm.captures) == 1
                    assert regs[6] == (255 if screen else 63), 'fill alpha handoff'
                    if kind != 'raw':
                        words = struct.unpack('>' + str(len(vm.captures[0])//8) + 'Q', vm.captures[0])
                        other = next(w for w in words if w >> 56 == 0x2f)
                        assert other & 0xffff == (0x25 if screen else expected)
                    else:
                        assert vm.captures[0][:4] == initial[start:start+4], 'raw command class changed'
                    # Execute the actual backdrop tag helper after the sender.
                    # It may use t0/a1/SCRN but must keep the fill alpha alive.
                    regs[4], regs[5], regs[31] = packet+24, packet+32, STOP
                    vm.pc = syms['main']['hcomp_eligibility_depth_send']
                    vm.execute(STOP)
                    assert regs[6] == (255 if screen else 63)
                    assert vm.pending_fetch is None
                    command_cases += 1
        for delay in (2, 9, 31):
            state = bytearray(d)
            state[addr('HCOMP_SCREEN')] = 0
            put(state, packet+20, 0x23400)
            put(state, addr('FRAMEBUFFER'), 0xf2300)
            before = bytes(state)
            regs = [0]*32
            owners = set(range(packet+14, packet+16)) | set(range(packet+20, packet+24))
            owners.add(addr('HCOMP_SCREEN'))
            owners.update(range(addr('RDP_FRAME')+4, addr('RDP_FRAME')+8))
            vm = PacketVM(slot('hcomp'), state, regs, owners, delay, True)
            vm.pc = syms['hcomp']['hcomp_copy_ts_done']
            vm.execute(syms['hcomp']['hcomp_fill_target'])
            assert state[addr('HCOMP_SCREEN')] == 1
            assert struct.unpack_from('>I', state, packet+20)[0] == (
                0x23400 - (addr('HCOMP_PRESENCE_ORIGIN')-addr('HCOMP_WINNER_ORIGIN'))) & 0xffffffff
            assert vm.captures[0][:8] == bytes.fromhex('2f0088ff00040025'), 'Main Z mode not restored'
            assert vm.pending_fetch is None
            assert all(state[i] == before[i] for i in range(4096) if i not in owners)
            transition_cases += 1
    report = dict(passed=True, selector_cases=selector_cases, setup_handoff_cases=setup_cases,
                  retired_command_alpha_cases=command_cases, main_transition_cases=transition_cases,
                  raw_packet_class_preserved=True, mode7_mode_selector_retains_z=True,
                  hardware_mocked=True, rasterization_proved=False, native_performance_proved=False)
    if args.baseline:
        import test_rsp_fixed_window as fixed
        import test_rsp_rdp_fixed as rdp_fixed
        for name in ('rsp_hcomp_fixed_window', 'rsp_hcomp_rdp_fixed', 'rsp_hcomp_tlut'):
            assert read_text(args.build/'src'/f'{name}.elf')[1] == read_text(args.baseline/'src'/f'{name}.elf')[1], name
        cpu = args.build/'sodium64-subalpha44.elf'
        report['rdp_fixed_cpu_binding'] = rdp_fixed.binding(cpu)
        for module, label, fault, message in (
                (fixed, 'fixed_window', 'restoration', 'restoration failed before overlay'),
                (rdp_fixed, 'rdp_fixed', True, 'GPU source not retired before Phase')):
            options = dict(arena=0xA00D4000) if module is fixed else {}
            results = [module.run(args.build, case, i, **options) for i, case in enumerate(module.regression_cases())]
            try:
                module.run(args.build, dict(rows=3, mask='spans'), 0, fault=fault, **options)
            except AssertionError as error:
                assert message in str(error), str(error)
            else:
                raise AssertionError('accepted unsafe '+label+' restoration')
            report[label] = dict(cases=len(results), pixels=sum(r.get('pixels', 0) for r in results),
                                 negative_guards=1, implementation_byte_exact=True)
    if args.output:
        args.output.write_text(json.dumps(report, indent=2)+'\n')
    print('SUB_ALPHA_LINKED', json.dumps(report))


if __name__ == '__main__':
    main()
