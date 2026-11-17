#include "full_dsp_window.h"

#include <cassert>
#include <cstdio>
#include <cstring>
#include <vector>

static void echo_word(void* context, unsigned addr, unsigned char const* bytes) {
    std::vector<unsigned>& words = *static_cast<std::vector<unsigned>*>(context);
    words.push_back((addr << 16) | (bytes[0] << 8) | bytes[1]);
}

static void save_bytes(unsigned char** out, void* state, size_t size) {
    std::memcpy(*out, state, size);
    *out += size;
}

static void compare_state(SPC_DSP_Window& window, SPC_DSP& immediate) {
    unsigned char actual[SPC_DSP::state_size], expected[SPC_DSP::state_size];
    unsigned char* a = actual;
    unsigned char* e = expected;
    window.copy_state(&a, save_bytes);
    immediate.copy_state(&e, save_bytes);
    assert(a - actual == e - expected && !std::memcmp(actual, expected, a - actual));
}

int main() {
    const unsigned lengths[] = {1, 2, 31, 32, 33, 255, 256};
    static unsigned char cpu[65536], shadow[65536], oracle_cpu[65536], oracle[65536];
    const unsigned timed_phases = (1u << 0) | (1u << 2) | (1u << 3) | (1u << 4) |
        (1u << 21) | (1u << 22) | (1u << 23) | (1u << 25) | (1u << 29) | (1u << 30);
    unsigned cases = 0, events = 0, queued_endpoints = 0, wraps = 0, echo_words = 0;
    bool nonzero_pcm = false;
    for (unsigned start = 0; start < 32; ++start) {
        for (unsigned i = 0; i < sizeof lengths / sizeof *lengths; ++i) {
            unsigned clocks = lengths[i];
            SPC_DSP core, immediate;
            SPC_DSP_Window window, oracle_bridge;
            std::vector<unsigned> echoes, oracle_echoes;
            std::memset(cpu, 0, sizeof cpu);
            cpu[0x1201] = cpu[0x1203] = 0x13; // BRR start and loop directory.
            cpu[0x1300] = 0x83; // End and loop.
            std::memset(cpu + 0x1301, 0x71, 8);
            std::memcpy(oracle_cpu, cpu, sizeof cpu);
            window.init(core, cpu, shadow, echo_word, &echoes);
            // Use the second bridge only to connect the echo callback.
            oracle_bridge.init(immediate, oracle_cpu, oracle, echo_word, &oracle_echoes);
            unsigned char regs[128] = {};
            regs[0] = regs[1] = regs[7] = regs[0x0c] = regs[0x1c] = regs[0x7f] = 0x7f;
            regs[3] = 0x10;
            regs[0x4c] = regs[0x4d] = 1;
            regs[0x5d] = 0x12;
            regs[0x6d] = 0x40;
            window.load(regs);
            immediate.load(regs);
            window.advance(32*10 + start);
            immediate.run(32*10 + start);
            short pcm[64] = {}, oracle_pcm[64] = {};
            window.set_output(pcm, 64);
            immediate.set_output(oracle_pcm, 64);
            assert(echoes == oracle_echoes);
            echoes.clear();
            oracle_echoes.clear();

            unsigned cursor = 0;
            for (unsigned clock = 0; clock <= clocks; ++clock) {
                unsigned phase = (start + clock) & 31;
                if (clock != 0 && clock != 1 && clock != clocks-1 && clock != clocks &&
                    !(clock < 32 && (timed_phases & (1u << phase)))) continue;
                if (clock != cursor) {
                    window.advance(clock - cursor);
                    immediate.run(clock - cursor);
                    cursor = clock;
                }
                unsigned addr = 0x1301 + (phase & 7);
                unsigned reg = phase == 2 ? 0x7c : phase == 3 ? 8 : phase == 4 ? 9 : 0x0d;
                if (clock == clocks)
                    assert(window.pending_clocks() == (clocks == 256 ? 0 : clocks));
                unsigned data = (clock + start + 37) & 0xff;
                window.write_ram(addr, data ^ 0xff);
                window.write_reg(reg, data ^ 0xff);
                window.write_ram(addr, data);
                window.write_reg(reg, data);
                oracle[addr] = oracle_cpu[addr] = data ^ 0xff;
                immediate.write(reg, data ^ 0xff);
                oracle[addr] = oracle_cpu[addr] = data;
                immediate.write(reg, data);
                if (clock == 0 || clock == 256) assert(window.pending_events() == 0);
                else if (clock == clocks) ++queued_endpoints;
                if (start == 31 && clock == 1) ++wraps;
                events += 4;
            }

            // Compare the endpoint before any more clocks consume the last writes.
            compare_state(window, immediate);
            assert(!std::memcmp(shadow, oracle, sizeof shadow));
            window.advance(64);
            immediate.run(64);
            compare_state(window, immediate);
            assert(!std::memcmp(cpu, oracle_cpu, sizeof cpu));
            assert(!std::memcmp(shadow, oracle, sizeof shadow));
            assert(echoes == oracle_echoes);
            unsigned samples = window.sample_count();
            assert(samples == unsigned(immediate.sample_count()));
            assert(!std::memcmp(pcm, oracle_pcm, samples * sizeof *pcm));
            for (unsigned j = 0; j < samples; ++j) nonzero_pcm |= pcm[j] != 0;
            echo_words += echoes.size();
            ++cases;
        }
    }
    assert(nonzero_pcm && echo_words && queued_endpoints == 192 && wraps == 7);
    std::printf("DSP_WINDOW_EVENTS PASS cases=%u events=%u queued_endpoints=%u "
                "phase_wraps=%u echo_words=%u\n", cases, events, queued_endpoints, wraps, echo_words);
}
