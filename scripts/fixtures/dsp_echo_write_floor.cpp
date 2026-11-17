#include "full_dsp_window.h"

#include <cassert>
#include <cstdio>
#include <cstring>

struct Echo {
    unsigned floor, words, below_page, bounded_words;
};

static void echo_word(void* context, unsigned address, unsigned char const*) {
    Echo& echo = *static_cast<Echo*>(context);
    assert(address >= echo.floor && address + 1 < 65536 && !(address & 1));
    ++echo.words;
    if (address < 256) ++echo.below_page;
    if (echo.floor) ++echo.bounded_words;
}

static void advance(SPC_DSP_Window& window, SPC_DSP& immediate, unsigned clocks) {
    window.advance(clocks);
    if (clocks) immediate.run(clocks);
}

static void write_reg(SPC_DSP_Window& window, SPC_DSP& immediate,
                      unsigned addr, unsigned data) {
    window.write_reg(addr, data);
    immediate.write(addr, data);
}

int main() {
    enum { FLG = 0x6c, ESA = 0x6d, EDL = 0x7d };
    struct Scenario {
        unsigned old_esa, old_edl, new_esa, new_edl, old_floor, new_floor;
        bool wraps;
    };
    const Scenario scenarios[] = {
        {0x40, 1, 0x60, 2, 0x4000, 0x4000, false},
        {0x60, 1, 0x40, 0, 0x6000, 0x4000, false},
        {0xf7, 1, 0xf8, 1, 0xf700, 0xf700, false}, // New ring ends exactly at 64 KiB.
        {0xf8, 1, 0xf9, 0, 0xf800, 0, true},     // Old EDL remains latched across wrap.
        {0xff, 0, 0xff, 1, 0xff00, 0, true},     // New EDL causes wrap.
        {0xff, 1, 0x40, 0, 0, 0, false},         // Old latched ESA could still wrap.
    };
    static unsigned char cpu[65536], shadow[65536], oracle[65536];
    unsigned cases = 0, words = 0, bounded = 0, wrapped = 0, deferred = 0, right = 0;
    for (unsigned i = 0; i < sizeof scenarios / sizeof *scenarios; ++i) {
        Scenario const& s = scenarios[i];
        for (unsigned phase = 0; phase < 32; ++phase) {
            Echo echo = {};
            SPC_DSP core, immediate;
            SPC_DSP_Window window;
            for (unsigned addr = 0; addr < 65536; ++addr)
                cpu[addr] = oracle[addr] = (addr ^ (addr >> 8) ^ 0x5a) & 0xff;
            window.init(core, cpu, shadow, echo_word, &echo);
            immediate.init(oracle);
            unsigned char regs[128] = {};
            regs[ESA] = s.old_esa;
            regs[EDL] = s.old_edl;
            window.load(regs);
            immediate.load(regs);
            advance(window, immediate, 32*5 + phase);
            window.flush();
            echo.floor = window.echo_write_floor();
            assert(echo.floor == s.old_floor);

            // The register writes drain old clocks using the previous bound.
            advance(window, immediate, 32);
            write_reg(window, immediate, ESA, s.new_esa);
            write_reg(window, immediate, EDL, s.new_edl);
            echo.floor = window.echo_write_floor();
            assert(echo.floor == s.new_floor);
            unsigned low_before = echo.below_page;
            if (i == 0) {
                // Phase 29 has latched the higher ESA, while phase 30 still
                // writes the old lower pointer. Recompute the bound there.
                unsigned to_right = (30 + 32 - phase) & 31;
                advance(window, immediate, to_right ? to_right : 32);
                window.flush();
                echo.floor = window.echo_write_floor();
                assert(echo.floor >= 0x4000 && echo.floor < 0x6000);
                unsigned before = echo.words;
                advance(window, immediate, 1);
                window.flush();
                assert(echo.words == before + 1);
                ++right;
            }

            if (echo.floor) {
                const unsigned addr = echo.floor - 1;
                unsigned before = shadow[addr];
                advance(window, immediate, 7);
                window.write_ram(addr, before ^ 0xa5);
                window.write_ram(addr, before ^ 0x5a);
                oracle[addr] = before ^ 0x5a;
                assert(window.pending_clocks() == 7 && window.pending_events() == 2);
                assert(window.read_ram(addr) == oracle[addr] && shadow[addr] == before);
                deferred += 2;
            }
            advance(window, immediate, 32*640);
            window.flush();
            if (s.wraps) {
                assert(echo.below_page > low_before);
                ++wrapped;
            }
            assert(!std::memcmp(cpu, oracle, sizeof cpu));
            assert(!std::memcmp(shadow, oracle, sizeof shadow));

            window.soft_reset();
            immediate.soft_reset();
            write_reg(window, immediate, FLG, 0);
            echo.floor = window.echo_write_floor();
            advance(window, immediate, 32*3);
            window.flush();
            assert(!std::memcmp(cpu, oracle, sizeof cpu));
            assert(!std::memcmp(shadow, oracle, sizeof shadow));
            ++cases;
            words += echo.words;
            bounded += echo.bounded_words;
        }
    }
    std::printf("DSP_ECHO_WRITE_FLOOR PASS cases=%u echo_words=%u bounded_words=%u "
                "wrapped=%u stale_right=%u deferred_writes=%u\n",
                cases, words, bounded, wrapped, right, deferred);
}
