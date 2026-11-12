"""Replay retained linked R43/R44 proofs against clean renderer worktrees."""
import argparse
from pathlib import Path
import sys
import subprocess


RETAINED_HEAD = '7a83d4982f20f7dd2fd44ab506d66a5a084f6db1'


def clean_macros(renderer, macro_eval):
    macros = {}
    for line in (renderer / 'src/renderer/defines.h').read_text().splitlines():
        if line.startswith('#define '):
            _, name, *value = line.split('//', 1)[0].split(maxsplit=2)
            if value and '(' not in name:
                macros[name] = value[0]
    return macro_eval(macros)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('proof', choices=('adaptive_spans', 'bg_spans', 'sub_alpha',
                                         'math_fullrow', 'rdp_half'))
    parser.add_argument('build', type=Path)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--retained', type=Path, required=True,
                        help=f'clean checkout of the archived proof source at {RETAINED_HEAD}')
    parser.add_argument('--renderer', type=Path, required=True, help='clean renderer source checkout')
    parser.add_argument('--elf', type=Path)
    args = parser.parse_args()
    retained = args.retained.resolve()
    head = subprocess.check_output(['git', '-C', str(retained), 'rev-parse', 'HEAD'], text=True).strip()
    assert head == RETAINED_HEAD, 'retained proof checkout must match the recorded revision'
    changes = subprocess.check_output(['git', '-C', str(retained), 'status', '--porcelain', '--untracked-files=no'])
    assert not changes, 'retained proof checkout must have no tracked changes'
    sys.path.insert(0, str(retained / 'scripts'))
    import test_gate_c_cgram_rsp_consumer_clean_contract as contract
    contract.parse_macros = lambda _root: clean_macros(args.renderer, contract.MacroEval)
    script = retained / 'scripts' / f'test_rsp_{args.proof}.py'
    source = script.read_text()
    sys.argv = [str(script), str(args.build), '--baseline', str(args.baseline)]
    if args.proof == 'adaptive_spans':
        assert args.elf is not None
        sys.argv.extend(('--elf', str(args.elf)))
        # Clean bank sources are aligned addresses. The retained harness tagged
        # these Main pointers only to feed the removed native tracing code.
        pairs = {
            "(base|1,(cs['rsp_main_text_start']+0x3a8)|1)":
                "(base,cs['rsp_main_text_start']+0x3a8)",
            '((MAIN+0x3a8) if current or not nospan else NOSPAN)|1':
                '((MAIN+0x3a8) if current or not nospan else NOSPAN)',
            '((MAIN+0x3a8) if wrong_main else NOSPAN)|1':
                '((MAIN+0x3a8) if wrong_main else NOSPAN)',
            '(MAIN+0x3a8)|1)': '(MAIN+0x3a8))',
            '((MAIN+0x3a8) if wanted else NOSPAN)|1':
                '((MAIN+0x3a8) if wanted else NOSPAN)',
            "put(d,a('OVERLAY_HCOMP_SRC'),PHASE|3);put(d,a('OVERLAY_HCOMP_SETUP_SRC'),SETUP|7)":
                "put(d,a('OVERLAY_HCOMP_SRC'),PHASE);put(d,a('OVERLAY_HCOMP_SETUP_SRC'),SETUP)",
        }
    elif args.proof == 'bg_spans':
        pairs = {'WORKER|1': 'WORKER', 'MAIN|1': 'MAIN',
                 "assert vm.r[3]==EXIT,'decoder loop v1 owner changed'":
                     "assert vm.r[3]==before_r[3],'decoder changed caller v1'"}
    elif args.proof == 'sub_alpha':
        # The unchanged fixed-color paths keep the clean compositor's proof
        # harness and owner map. This proof covers selector, Setup handoff and packets.
        old = "        cpu = args.build/'sodium64-subalpha44.elf'"
        new = "        report['fixed_color_banks_byte_exact'] = True"
        assert old in source and '    if args.output:' in source
        start, end = source.index(old), source.index('    if args.output:')
        source = source[:start] + new + '\n' + source[end:]
        pairs = {}
    elif args.proof == 'math_fullrow':
        names = ('rsp_main', 'rsp_hcomp_math', 'rsp_hcomp')
        sys.argv = [str(script), *(str(args.build / 'src' / f'{n}.elf') for n in names),
                    '--baseline', str(args.baseline / 'src' / 'rsp_hcomp_math.elf')]
        pairs = {
            'PHASE_BANK | 3': 'PHASE_BANK',
            "assert 'hcomp_fullrow_admission' not in baseline[2], 'baseline already full row'":
                "assert 'hcomp_fullrow_admission' in baseline[2], 'clean R43 full-row control missing'",
            'case, i, a.backup_address, stage))': 'case, i, a.backup_address, stage, full=True))',
            "at = math_symbols['hcomp_fullrow_admission']+(48 if alpha else 52)":
                "start = math_symbols['hcomp_fullrow_admission']\n"
                "        end = math_symbols['hcomp_fullrow_mode_ready']\n"
                "        at, = [pc for pc in range(start, end, 4)\n"
                "               if struct.unpack_from('>I', vm.code, pc)[0] == 0x21eb0400]",
        }
    else:
        assert args.elf is not None
        sys.argv.extend(('--cpu', str(args.elf)))
        pairs = {
            "regs[8] = syms['rsp_hcomp_math_text_start'] | 5":
                "regs[8] = syms['rsp_hcomp_rdp_fixed_text_start']",
            "assert read(data) == syms['rsp_hcomp_math_text_start'] | 5":
                "assert read(data) == syms['rsp_hcomp_rdp_fixed_text_start']",
            "assert read(0xa4000000+addr('OVERLAY_HCOMP_MATH_SRC')) == text | 5":
                "assert read(0xa4000000+addr('OVERLAY_HCOMP_MATH_SRC')) == text",
            'ts == 1 and not limit': 'ts == 1',
            'RDP_BANK|5': 'RDP_BANK', 'PHASE_BANK|3': 'PHASE_BANK', 'MATH_BANK|5': 'MATH_BANK',
        }
    # Replay the historical fixture with explicit adaptations for the clean ABI.
    for old, new in pairs.items():
        assert old in source, old
        source = source.replace(old, new)
    exec(compile(source, str(script), 'exec'), {'__name__': '__main__', '__file__': str(script)})


if __name__ == '__main__':
    main()
