"""Run the pinned R45 CPU, overlay and RDP packet fixtures on the clean port."""
import argparse
from pathlib import Path
import subprocess
import sys


from replay_clean_renderer_ports import clean_macros


RETAINED = 'fa77692e9f8d5c04d38da19ed3d866db7108f4c7'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('--elf', type=Path, required=True)
    parser.add_argument('--retained', type=Path, required=True)
    parser.add_argument('--renderer', type=Path, required=True)
    parser.add_argument('--bypass', action='store_true', help='also check the early Sub and non-indexed mode bypass')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    head = subprocess.check_output(['git', '-C', str(args.retained), 'rev-parse', 'HEAD'], text=True).strip()
    assert head == RETAINED, 'retained proof checkout must match the recorded revision'
    changes = subprocess.check_output(['git', '-C', str(args.retained), 'status', '--porcelain', '--untracked-files=no'])
    assert not changes
    retained = args.retained / 'scripts'
    sys.path.insert(0, str(retained.resolve()))
    import test_gate_c_cgram_rsp_consumer_clean_contract as contract

    contract.parse_macros = lambda _root: clean_macros(args.renderer, contract.MacroEval)
    macro = contract.parse_macros(None).name

    script = retained / 'test_backdrop_rows.py'
    source = script.read_text()
    # Layout uses aligned pointers and the clean CGRAM owner. The removed
    # compose limit is poisoned in its historical test case and must be ignored.
    replacements = {
        "build/'sodium64-backdrop45.elf'": f'Path({str(args.elf)!r})',
        '0xa00d4e08': hex(macro('HCOMP_CGRAM_EVENT_QUEUE1') + 8),
        '0xa00d4e00': hex(macro('HCOMP_CGRAM_EVENT_QUEUE1')),
        '0xd4400': hex(macro('HCOMP_CGRAM_SIDEBAND_QUEUE1') & 0x1fffffff),
        "s['rsp_hcomp_text_start']|3|initial": "s['rsp_hcomp_text_start']|initial",
        "s['rsp_hcomp_backdrop_text_start']|3": "s['rsp_hcomp_backdrop_text_start']",
        '0x80190001': '0x80190000',
        '0x801a0003': '0x801a0000',
        '0xa0180003': '0xa0180000',
        ' and not limit and ': ' and ',
    }
    if args.bypass:
        replacements.update({
            '*, cgws, screen=1, blank=False': '*, cgws, screen=1, mode=8, blank=False',
            "d[addr('BG_MODE')] = 7": "d[addr('BG_MODE')] = mode",
            'bypass = bool(cgws & 0xf3)':
                "if fault in ('missing_sub_bypass', 'missing_mode_bypass'):\n"
                "        offset = 20 if fault == 'missing_sub_bypass' else 32\n"
                "        instruction = struct.unpack_from('>I', vm.code, vm.pc + offset)[0]\n"
                "        assert instruction >> 26 == (4 if fault == 'missing_sub_bypass' else 5)\n"
                "        put(vm.code, vm.pc + offset, 0)\n"
                "    bypass = bool(cgws & 0xf3 or not screen or mode & 6)",
            "'excluded CGWSEL loaded a helper/descriptor'": "'excluded policy loaded a helper/descriptor'",
            'regs[19] == 7<<4': 'regs[19] == mode<<4',
            'dispatch_case(args.build,cgws=cgws,screen=screen,blank=blank,delay=delay,parity=parity)\n'
            '                        dispatches += 1':
                'for mode in range(16):\n'
                '                            dispatch_case(args.build,cgws=cgws,screen=screen,mode=mode,blank=blank,delay=delay,parity=parity)\n'
                '                            dispatches += 1',
            '    result.update(rsp_cases=':
                "    for fault, screen, mode in (('missing_sub_bypass',0,8),('missing_mode_bypass',1,7)):\n"
                '        try: dispatch_case(args.build,cgws=0,screen=screen,mode=mode,fault=fault)\n'
                '        except AssertionError as e:\n'
                "            assert str(e) == 'excluded policy loaded a helper/descriptor'\n"
                '            rejected.append(fault)\n'
                "        else: raise AssertionError('escaped bypass negative: '+fault)\n"
                '    result.update(rsp_cases=',
        })
    for old, new in replacements.items():
        assert old in source, old
        source = source.replace(old, new)
    sys.argv = [str(script), str(args.build)]
    if args.output:
        sys.argv.extend(('--output', str(args.output)))
    exec(compile(source, str(script), 'exec'), {'__name__': '__main__', '__file__': str(script)})


if __name__ == '__main__':
    main()
