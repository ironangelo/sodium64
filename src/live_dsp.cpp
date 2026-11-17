/* Complete scalar backend on the original live SPC workload. */
#include "live_dsp.h"
#include "full_dsp_window.h"

#include <new>
#include <stddef.h>

extern "C" {
    extern unsigned char apu_ram[], dsp_addr;
    extern uint32_t jit_tags[], dsp_buffer[];
    extern uint16_t dsp_pointer;
#ifdef SODIUM64_DSP_RSP_YIELD
    void live_rsp_yield_service(unsigned from_wait);
#endif
}

namespace {

enum {
    guest_cycle = LIVE_DSP_GUEST_CYCLE,
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

#ifdef SODIUM64_DSP_LIVE_INPUT_QUEUE
struct input_event {
    uint32_t epoch;
    uint16_t address;
    uint8_t value;
};
struct input_queue {
    uint32_t size, exclusive_limit;
    input_event events[LIVE_DSP_INPUT_CAPACITY];
};
typedef char input_layout_matches_assembly[
    sizeof(input_event) == (1u << LIVE_DSP_INPUT_EVENT_SHIFT) &&
    offsetof(input_event, address) == 4 && offsetof(input_event, value) == 6 &&
    offsetof(input_queue, size) == LIVE_DSP_INPUT_SIZE &&
    offsetof(input_queue, exclusive_limit) == LIVE_DSP_INPUT_EXCLUSIVE_LIMIT &&
    offsetof(input_queue, events) == LIVE_DSP_INPUT_EVENTS &&
    sizeof(input_queue) == LIVE_DSP_INPUT_BYTES ? 1 : -1];
extern "C" input_queue live_dsp_input;
#endif

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

bool advance_to(uint32_t epoch) {
    uint32_t delta = epoch - state->last_epoch;
    if (delta > max_access_gap || delta % guest_cycle) {
        ++stats->clock_errors;
        return false;
    }
    unsigned clocks = delta / guest_cycle;
    state->last_epoch = epoch;
    stats->cycles += clocks;
    state->window.advance(clocks);
    return true;
}

#ifdef SODIUM64_DSP_LIVE_INPUT_QUEUE
void drain_ram_input() {
    unsigned size = live_dsp_input.size;
    for (unsigned i = 0; i < size; ++i) {
        input_event const& event = live_dsp_input.events[i];
        if (advance_to(event.epoch)) state->window.write_ram(event.address, event.value);
    }
    stats->queued_ram_writes += size;
    live_dsp_input.size = 0;
}
#endif

} // namespace

extern "C" unsigned live_dsp_access(unsigned op, unsigned address, unsigned value, uint32_t epoch) {
#ifdef SODIUM64_DSP_RSP_YIELD
    if (op == LIVE_DSP_RENDER_YIELD) {
        live_rsp_yield_service(1);
        return 0;
    }
    if (op == LIVE_DSP_REG_READ || op == LIVE_DSP_PCM) live_rsp_yield_service(0);
#endif
    if (!initialized) initialize();
#ifdef SODIUM64_DSP_LIVE_INPUT_QUEUE
    drain_ram_input();
#endif
    if (!advance_to(epoch)) return 0;
    unsigned result = 0;
    switch (op) {
    case LIVE_DSP_RAM_WRITE:
        state->window.write_ram(address, value);
        break;
    case LIVE_DSP_RAM_READ:
    case LIVE_DSP_FETCH:
        result = read_dsp_bus(false, address, epoch);
        break;
    case LIVE_DSP_REG_WRITE:
        if (dsp_addr < 128) {
            state->window.write_reg(dsp_addr, value);
            ++stats->writes;
        }
        break;
    case LIVE_DSP_REG_READ:
        ++stats->outputs;
        result = read_dsp_bus(true, dsp_addr & 0x7f, epoch);
        break;
    case LIVE_DSP_PCM:
        queue_pcm();
        break;
    }
#ifdef SODIUM64_DSP_LIVE_INPUT_QUEUE
    live_dsp_input.exclusive_limit = state->window.echo_write_floor();
#endif
    return result;
}
