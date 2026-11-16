#!/usr/bin/env python3
"""Execute the linked reset and require complete invalidation with exact bounds."""
import argparse
from linked_cpu_regression import CPU, load_elf


def check(memory, symbols):
    cpu = CPU(memory.copy())
    start, end = symbols['jit_lookup'], symbols['jit_pointer']
    assert start % 8 == end % 8 == 0 and end-start == 0x40000
    lo, hi = start & 0x1fffffff, end & 0x1fffffff
    # Every pointer, including stale or never-replayed entries, starts nonzero.
    # Both sentinels include adjacent live metadata, not just unused padding.
    cpu.memory.update((lo-32+i, 0xa5) for i in range(hi-lo+64))
    cpu.pattern()
    before = cpu.regs.copy()
    cp, product = cpu.cp.copy(), (cpu.hi, cpu.lo)
    cpu.execute(symbols['reset_buffer'], stop=symbols['compile_block'])
    assert cpu.blob(start, hi-lo) == bytes(hi-lo), 'lookup entry survived reset'
    assert cpu.blob(start-32, 32) == bytes([0xa5])*32, 'leading owner overwritten'
    assert cpu.blob(end+4, 28) == bytes([0xa5])*28, 'trailing owner overwritten'
    assert cpu.read(end) == 0xa01c0000, 'JIT pointer was not reset'
    assert all(cpu.regs[i] == before[i] for i in range(32) if i not in (1, 8, 9, 31))
    # Restarted compilation installs its own link before calling the emitter.
    assert cpu.regs[31] & 0xffffffff == symbols['reset_buffer']+8
    assert (cpu.hi, cpu.lo) == product and cpu.cp == cp and not cpu.cp_writes
    coverage = set()
    for address, width, value in cpu.memory_writes:
        assert value == 0 or address == hi, 'nonzero lookup publication during reset'
        assert lo <= address and address+width <= hi+4, 'write escaped lookup/pointer owner'
        if address < hi:
            assert not coverage.intersection(range(address, address+width)), 'duplicate clear'
            coverage.update(range(address, address+width))
    assert len(coverage) == 0x40000, 'incomplete lookup invalidation'
    return cpu.steps


def check_clock_change(memory, symbols):
    """Run cached NOP blocks, operate the linked settings menu, then dispatch again."""
    pcs = (0x0200, 0x8200, 0xfe00)
    start = symbols['jit_lookup']
    pointer = symbols['jit_pointer']
    clock = symbols['apu_clock']
    options = ('counter_set', 'layer_set', 'precision_set', 'skipped_set', 'audio_set')

    def dispatch(cpu, pc, clock_value):
        cpu.write(symbols['apu_count'], pc, 2)
        cpu.pattern()
        cpu.regs[19], cpu.regs[7] = 4096, 0
        cpu.execute(symbols['apu_execute'], stop=symbols['cpu_execute'], max_steps=15000)
        cycles = 2*(cpu.read(symbols['apu_count'], 2)-pc)
        assert cycles > 0
        assert 4096-cpu.regs[19] == cycles*clock_value, 'cached debit uses the wrong clock'

    def close(cpu, selected):
        start_button, down, left, right = 0x10, 4, 2, 1
        current = cpu.read(clock, 1)
        old_options = [cpu.read(symbols[name], 1) for name in options]
        joybus = symbols['joybus_cmd'] & 0x1fffffff

        def update(button_samples):
            samples = iter(button_samples)
            input_pc = symbols['get_pressed']

            def sample(c):
                # Supply the Joybus result, then execute the actual edge detector.
                buttons = next(samples, None)
                assert buttons is not None, 'menu requested unexpected input'
                c.memory[joybus+4] = buttons
                c.before_instruction[input_pc] = sample

            cpu.pattern()
            cpu.regs[4] = cpu.read(symbols['framebuffer'])
            cpu.before_instruction[input_pc] = sample
            cpu.execute(symbols['update_menu'], stop=symbols['menu_return'])
            del cpu.before_instruction[input_pc]
            assert next(samples, None) is None, 'menu returned before consuming the input'

        cpu.memory[joybus+2] = 0  # Controller connected.
        cpu.memory[symbols['frame_count'] & 0x1fffffff] = 0
        if 'remote_frame_bridge' in symbols:
            cpu.hooks[symbols['remote_frame_bridge']] = lambda _cpu: None
        update([0])  # Release Start from the preceding game frame.
        cpu.memory_writes.clear()
        buttons = [start_button]
        if selected != current:
            # Five separate D-pad edges select the sixth option, APU underclock.
            buttons.extend([0, down] * 5)
            buttons.extend((0, right if selected == 42 else left))
        buttons.extend((0, start_button))
        update(buttons)
        assert cpu.read(symbols['underclk_set'], 1) == (4 if selected == 42 else 0), 'menu did not select the requested APU clock'
        assert cpu.read(clock, 1) == selected, 'menu did not apply the requested APU clock'
        assert [cpu.read(symbols[name], 1) for name in options] == old_options

    for old, new in ((42,21),(21,42)):
        cpu = CPU(memory.copy())
        cpu.write(clock, old, 1)
        cpu.write(symbols['underclk_set'], 4 if old == 42 else 0, 1)
        for pc in pcs:
            dispatch(cpu, pc, old)
        compiled = cpu.read(pointer)
        assert compiled > 0xa01c0000
        entries = [cpu.read(start+4*pc) for pc in pcs]
        assert all(0x801c0000 <= value < 0x80200000 for value in entries)
        close(cpu, old)
        lookup, limit = start & 0x1fffffff, pointer & 0x1fffffff
        assert not any(lookup <= address <= limit or address == (clock & 0x1fffffff)
                       for address, _, _ in cpu.memory_writes), 'unchanged menu close wrote APU cache state'
        assert cpu.read(pointer) == compiled
        assert [cpu.read(start+4*pc) for pc in pcs] == entries
        dispatch(cpu, pcs[0], old)
        assert cpu.read(pointer) == compiled, 'unchanged menu close evicted cached code'
        tags = cpu.blob(symbols['jit_tags'], 4096)
        close(cpu, new)
        assert cpu.blob(start, 0x40000) == bytes(0x40000), 'old-clock lookup survived menu close'
        assert cpu.read(pointer) == 0xa01c0000
        assert cpu.blob(symbols['jit_tags'], 4096) == tags
        for pc in pcs:
            dispatch(cpu, pc, new)
        assert all(cpu.read(start+4*pc) for pc in pcs)
        compiled = cpu.read(pointer)
        dispatch(cpu, pcs[1], new)
        assert cpu.read(pointer) == compiled
    return len(pcs)*2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf')
    args = parser.parse_args()
    memory, symbols = load_elf(args.elf)
    steps = check(memory, symbols)
    clock_rebuilds = check_clock_change(memory, symbols)
    # Real emitted-code faults: omit a store, omit the delay-slot store, or
    # stop one batch early. All must fail independently of the positive run.
    begin, end = symbols['reset_loop'], symbols['compile_block']
    words = [(pc, int.from_bytes(bytes(memory.get((pc+i) & 0x1fffffff, 0) for i in range(4)), 'big'))
             for pc in range(begin, begin+80, 4)]
    stores = [(pc, word) for pc, word in words if word >> 26 == 63]
    assert len(stores) == 8, 'expected eight linked SD stores'
    mutants = [(stores[0][0], 0), (stores[-1][0], 0)]
    for pc, word in words:
        if word >> 26 in (8, 9) and (word >> 16 & 31) == 8 and (word & 65535) == 64:
            mutants.append((pc, (word & ~65535) | 128))
    assert len(mutants) == 3
    for pc, replacement in mutants:
        bad = memory.copy()
        for i, byte in enumerate(replacement.to_bytes(4, 'big')):
            bad[(pc+i) & 0x1fffffff] = byte
        try:
            check(bad, symbols)
        except AssertionError:
            continue
        raise AssertionError('reset fault accepted')
    cpu = CPU(memory.copy())
    call = [pc for pc in range(symbols['menu_close'],symbols['menu_close']+64,4)
            if cpu.read(pc) >> 26 == 3 and
            (((pc+4)&0xf0000000) | ((cpu.read(pc)&0x3ffffff)<<2)) == symbols['apu_invalidate_jit']]
    assert len(call) == 1
    cpu.write(call[0], 0)
    try:
        check_clock_change(cpu.memory, symbols)
    except AssertionError as error:
        assert str(error) == 'old-clock lookup survived menu close'
    else:
        raise AssertionError('missing clock invalidation fault accepted')
    cpu = CPU(memory.copy())
    setting_store = symbols['menu_close']-4
    assert cpu.read(setting_store) == 0xa1090000, 'expected the right-button setting store'
    cpu.write(setting_store, 0)
    try:
        check_clock_change(cpu.memory, symbols)
    except AssertionError as error:
        assert str(error) == 'menu did not select the requested APU clock'
    else:
        raise AssertionError('missing menu setting update fault accepted')
    print(f'APU_LOOKUP_RESET PASS entries=65536 bytes=262144 faults=5 instructions={steps} '
          f'clock_rebuilds={clock_rebuilds} menu_transitions=4; no N64 timing claim')


if __name__ == '__main__':
    main()
