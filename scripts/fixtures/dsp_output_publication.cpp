#include "full_dsp_window.h"

#include <cassert>
#include <cstdio>

int main() {
    // Next publication per register, independently listed from GEN_DSP_TIMING.
    const unsigned outx_phases[] = {3, 6, 9, 12, 15, 18, 21, 24};
    const unsigned envx_phases[] = {4, 7, 10, 13, 16, 19, 22, 25};
    const unsigned endx_phases[] = {2, 5, 8, 11, 14, 17, 20, 23};
    static unsigned char cpu_ram[65536], shadow_ram[65536], oracle_ram[65536];
    unsigned cases = 0;
    for (unsigned phase = 0; phase < 32; ++phase) {
        for (unsigned reg = 0; reg < 17; ++reg) {
            const bool endx = reg == 16;
            unsigned voice = reg / 2;
            bool outx = reg & 1;
            unsigned addr = endx ? 0x7c : voice * 16 + (outx ? 9 : 8);
            unsigned next = 31;
            if (endx) {
                for (unsigned i = 0; i < 8; ++i) {
                    unsigned distance = (endx_phases[i] - phase) & 31;
                    if (distance < next) next = distance;
                }
            } else {
                next = ((outx ? outx_phases : envx_phases)[voice] - phase) & 31;
            }
            for (unsigned clocks = 0; clocks <= 40; ++clocks) {
                for (unsigned with_write = 0; with_write < 2; ++with_write) {
                    SPC_DSP core, oracle;
                    SPC_DSP_Window window;
                    cpu_ram[addr] = oracle_ram[addr] = 0;
                    window.init(core, cpu_ram, shadow_ram);
                    oracle.init(oracle_ram);
                    unsigned char regs[128] = {};
                    regs[0x6c] = 0xe0; // Disable echo writes for this register-only test.
                    regs[addr] = 0xa5;
                    window.load(regs);
                    oracle.load(regs);
                    window.advance(phase);
                    window.flush();
                    if (phase) oracle.run(phase);
                    unsigned before = clocks / 2;
                    unsigned after = clocks - before;
                    window.advance(before);
                    if (before) oracle.run(before);
                    if (with_write) {
                        window.write_reg(addr, 0x3d);
                        oracle.write(addr, 0x3d);
                        window.write_ram(addr, 0xc2);
                        oracle_ram[addr] = 0xc2;
                    }
                    window.advance(after);
                    if (after) oracle.run(after);
                    assert(window.read_reg(addr) == oracle.read(addr));
                    assert(window.pending_clocks() == (clocks > next ? 0 : clocks));
                    window.flush();
                    for (unsigned i = 0; i < 128; ++i) assert(core.read(i) == oracle.read(i));
                    assert(cpu_ram[addr] == oracle_ram[addr]);
                    assert(shadow_ram[addr] == oracle_ram[addr]);
                    ++cases;
                }
            }
        }
    }
    std::printf("Exact register reads and publication boundaries in %u cases\n", cases);
}
