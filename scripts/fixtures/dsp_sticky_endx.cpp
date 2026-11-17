#include "full_dsp_window.h"

#include <cassert>
#include <cstdio>
#include <cstring>

namespace {

enum { endx = 0x7c, kon = 0x4c, flg = 0x6c };
unsigned char cpu_ram[65536], shadow_ram[65536], oracle_ram[65536];

struct Test {
    SPC_DSP core, oracle;
    SPC_DSP_Window window;
    SPC_DSP::sample_t output[64], expected[64];

    explicit Test(unsigned value) {
        unsigned char regs[128] = {};
        regs[endx] = value;
        regs[flg] = 0xe0;
        window.init(core, cpu_ram, shadow_ram);
        oracle.init(oracle_ram);
        window.load(regs);
        oracle.load(regs);
        window.set_output(output, 64);
        oracle.set_output(expected, 64);
    }

    void advance(unsigned clocks) {
        window.advance(clocks);
        oracle.run(clocks);
    }

    void write(unsigned addr, unsigned value) {
        window.write_reg(addr, value);
        oracle.write(addr, value);
    }

    void check(unsigned value, unsigned remaining) {
        assert(unsigned(oracle.read(endx)) == value);
        assert(window.read_reg(endx) == oracle.read(endx));
        assert(window.pending_clocks() == remaining);
        window.flush();
        for (unsigned addr = 0; addr < 128; ++addr)
            assert(core.read(addr) == oracle.read(addr));
        assert(core.sample_count() == oracle.sample_count());
        assert(!std::memcmp(output, expected, core.sample_count() * sizeof *output));
        assert(!std::memcmp(cpu_ram, oracle_ram, sizeof cpu_ram));
        assert(!std::memcmp(shadow_ram, oracle_ram, sizeof shadow_ram));
    }
};

} // namespace

int main() {
    for (unsigned phase = 0; phase < 32; ++phase) {
        Test saturated(0xff);
        saturated.advance(32 + phase);
        saturated.window.flush();
        saturated.advance(32);
        saturated.check(0xff, 32);

        Test unsaturated(0xfe);
        unsaturated.advance(32 + phase);
        unsaturated.window.flush();
        unsaturated.advance(32);
        unsaturated.check(0xfe, 0);

        Test clear(0xff);
        clear.advance(32 + phase);
        clear.window.flush();
        clear.advance(1);
        clear.write(endx, 0xff); // Every write clears both the register and its latch.
        clear.advance(31);
        clear.check(0, 0);

        Test queued_kon(0xff);
        queued_kon.advance(32 + phase);
        queued_kon.window.flush();
        queued_kon.advance(1);
        queued_kon.write(kon, 1);
        queued_kon.advance(127);
        queued_kon.check(0xfe, 0);
    }

    Test latched_kon(0xff);
    latched_kon.advance(32);
    latched_kon.window.flush();
    latched_kon.write(kon, 2);
    latched_kon.advance(31); // KON has latched, but voice 1 has not started yet.
    latched_kon.window.flush();
    assert(latched_kon.core.read(endx) == 0xff);
    latched_kon.write(kon, 0); // Clear the producer latch only.
    latched_kon.advance(7);
    latched_kon.check(0xfd, 0);

    Test immediate_kon(0xff);
    immediate_kon.advance(32);
    immediate_kon.window.flush();
    immediate_kon.write(kon, 1);
    immediate_kon.advance(64);
    immediate_kon.check(0xfe, 0);

    std::puts("DSP_STICKY_ENDX PASS cases=130 phases=32");
}
