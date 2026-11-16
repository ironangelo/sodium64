/* Complete scalar backend on the original live SPC workload. */
#include "live_dsp.h"
#include "full_dsp_window.h"

#include <new>

extern "C" {
    extern unsigned char apu_ram[], dsp_addr;
    extern uint32_t jit_tags[], dsp_buffer[];
    extern uint16_t dsp_pointer;
}

namespace {

enum {
    guest_cycle = 21,
    audio_words = 32,
    // Allow one full PCM period plus the existing bounded SPC block runout.
    max_access_gap = (SODIUM64_DSP_PCM_PERIOD + 1) * 32 * guest_cycle
};
struct live_state {
    SPC_DSP core;
    SPC_DSP_Window window;
    uint32_t last_epoch;
    short samples[audio_words];
};
typedef char state_is_bounded[sizeof(live_state) <= LIVE_DSP_STATS - LIVE_DSP_STATE ? 1 : -1];

live_state* const state = reinterpret_cast<live_state*>(LIVE_DSP_STATE);
live_dsp_stats* const stats = reinterpret_cast<live_dsp_stats*>(LIVE_DSP_STATS);
bool initialized;

void publish_echo(void*, unsigned address, const unsigned char* bytes) {
    ++stats->echo_words;
    ++jit_tags[address >> 6]; // The even aligned word stays within this page.
    if (address == 0x47fe && bytes[1] == 0) ++stats->echo_opcode_changes;
}

void initialize() {
    ::new (state) live_state();
    *stats = live_dsp_stats();
    state->window.init(state->core, apu_ram, reinterpret_cast<unsigned char*>(LIVE_DSP_SHADOW), publish_echo);
    state->window.set_output(state->samples, audio_words);
    initialized = true;
}

#ifdef SODIUM64_DSP_RSP_SWAP
void required(bool reg, uint32_t epoch) {
    uint32_t gap = epoch - stats->last_required_epoch;
    if ((stats->required_reg || stats->required_echo) && gap && gap <= 3 * guest_cycle)
        ++stats->required_le3;
    stats->last_required_epoch = epoch;
    if (reg) ++stats->required_reg;
    else ++stats->required_echo;
}
#endif

unsigned read_dsp_bus(bool reg, unsigned address, uint32_t epoch) {
#ifdef SODIUM64_DSP_RSP_SWAP
    uint32_t before = stats->core_runs;
#else
    (void)epoch;
#endif
    unsigned value = reg ? state->window.read_reg(address) : state->window.read_ram(address);
#ifdef SODIUM64_DSP_RSP_SWAP
    if (before != stats->core_runs) required(reg, epoch);
#endif
    return value;
}

void queue_pcm() {
    ++stats->sample_calls;
    if (!(reinterpret_cast<volatile uint32_t*>(0xa4040010)[0] & 1u)) ++stats->renderer_busy;
    int count = state->window.sample_count();
    if (count < 0 || count >= audio_words || (count & 1)) {
        ++stats->output_errors;
        state->window.set_output(state->samples, audio_words);
        return;
    }

    volatile uint32_t* const ring = reinterpret_cast<volatile uint32_t*>(
        reinterpret_cast<uintptr_t>(dsp_buffer) | 0xa0000000u);
    volatile uint32_t* const ai = reinterpret_cast<volatile uint32_t*>(0xa4500000u);
    for (int i = 0; i < count; i += 2) {
        unsigned at = dsp_pointer;
        ring[at / 4] = (unsigned(static_cast<uint16_t>(state->samples[i + 1])) << 16) |
                       static_cast<uint16_t>(state->samples[i]);
        dsp_pointer = (at + 4) & 0x1fff;
        if ((at & 0xfff) == 0xffc) {
            __asm__ volatile("sync" ::: "memory");
            ai[0] = (reinterpret_cast<uintptr_t>(dsp_buffer) + (at & 0x1000)) & 0x00ffffff;
            ai[1] = 0x1000;
        }
        ++stats->pcm;
    }
    state->window.set_output(state->samples, audio_words);
}

} // namespace

extern "C" unsigned live_dsp_access(unsigned op, unsigned address, unsigned value, uint32_t epoch) {
    if (!initialized) initialize();
    uint32_t delta = epoch - state->last_epoch;
    if (delta > max_access_gap || delta % guest_cycle) {
        ++stats->clock_errors;
        // Keep a bad clock from turning a single access into an unbounded run.
        return 0;
    }
    unsigned clocks = delta / guest_cycle;
    state->last_epoch = epoch;
    stats->cycles += clocks;
    state->window.advance(clocks);
    switch (op) {
    case LIVE_DSP_RAM_WRITE:
        state->window.write_ram(address, value);
        break;
    case LIVE_DSP_RAM_READ:
    case LIVE_DSP_FETCH:
        return read_dsp_bus(false, address, epoch);
    case LIVE_DSP_REG_WRITE:
        if (dsp_addr < 128) {
            state->window.write_reg(dsp_addr, value);
            ++stats->writes;
        }
        break;
    case LIVE_DSP_REG_READ:
        ++stats->outputs;
        return read_dsp_bus(true, dsp_addr & 0x7f, epoch);
    case LIVE_DSP_PCM:
        queue_pcm();
        break;
    }
    return 0;
}
