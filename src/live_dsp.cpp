/* Complete scalar backend on the original live SPC workload. */
#include "live_dsp.h"
#include "full_dsp_window.h"

#include <new>
#include <stddef.h>

extern "C" {
    extern unsigned char apu_ram[], dsp_addr;
    extern uint32_t jit_tags[], dsp_buffer[];
    extern uint16_t dsp_pointer;
#if SODIUM64_DSP_EFFECTS_MODE
    extern unsigned remote_boot_ram_bytes;
#endif
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

#if SODIUM64_DSP_EFFECTS_MODE
enum { effects_magic = 0x44535045u, effects_header = 2, effects_row = 4 };
const unsigned effects_capacity = LIVE_DSP_EFFECTS_PACKED_MAX / 4;
unsigned effects_pos = effects_header;
uint32_t effects_key(unsigned op, unsigned address, unsigned value) {
    if (op == LIVE_DSP_PCM) return op << 24;
    if (op == LIVE_DSP_REG_READ || op == LIVE_DSP_REG_WRITE) address = dsp_addr;
    if (op != LIVE_DSP_RAM_WRITE && op != LIVE_DSP_REG_WRITE) value = 0;
    return (op << 24) | ((value & 255) << 16) | address;
}
#endif

#if SODIUM64_DSP_EFFECTS_MODE == 1
volatile uint32_t* const effects = reinterpret_cast<volatile uint32_t*>(LIVE_DSP_EFFECTS_BASE);
void log_effect(uint32_t word) {
    if (stats->effects_error) return;
    if (effects_pos == effects_capacity) { stats->effects_error = 1; return; }
    effects[effects_pos++] = word;
}
#elif SODIUM64_DSP_EFFECTS_MODE == 2
enum { cached_effects = 0x80600000u };
const uint32_t* const effects = reinterpret_cast<const uint32_t*>(cached_effects);
unsigned effects_end;
bool wait_pi() {
    volatile uint32_t* status = reinterpret_cast<volatile uint32_t*>(0xa4600010u);
    uint32_t start, now;
    __asm__ volatile("mfc0 %0,$9" : "=r"(start));
    while (*status & 3) {
        __asm__ volatile("mfc0 %0,$9" : "=r"(now));
        if (now - start > 9375000u) return false;
    }
    return !(*status & 4);
}
bool dma_effects(unsigned cart, unsigned destination, unsigned length) {
    volatile uint32_t* const pi = reinterpret_cast<volatile uint32_t*>(0xa4600000u);
    pi[0] = destination & 0x1fffffffu;
    pi[1] = cart;
    pi[3] = length - 1;
    return wait_pi();
}
bool load_effects() {
    const volatile uint32_t* const rom = reinterpret_cast<const volatile uint32_t*>(0xa0000000u | LIVE_DSP_EFFECTS_ROM);
    if (remote_boot_ram_bytes != 0x800000u || !wait_pi() || rom[0] != effects_magic)
        return false;
    unsigned bytes = rom[1];
    if (bytes < effects_header * 4 || bytes > LIVE_DSP_EFFECTS_PACKED_MAX || (bytes & 3))
        return false;
    for (unsigned i = 0; i < bytes; i += 16)
        __asm__ volatile("cache 0x11, 0(%0)" :: "r"(cached_effects + i) : "memory");
    unsigned first = bytes < LIVE_DSP_EFFECTS_FIRST ? bytes : LIVE_DSP_EFFECTS_FIRST;
    if (!dma_effects(LIVE_DSP_EFFECTS_ROM, cached_effects, first)) return false;
    if (bytes > first && !dma_effects(LIVE_DSP_EFFECTS_TAIL, cached_effects + first, bytes-first)) return false;
    if (effects[0] != effects_magic || effects[1] != bytes) return false;
    effects_end = bytes / 4;
    return true;
}
#endif

void publish_echo(void*, unsigned address, const unsigned char* bytes) {
    ++stats->echo_words;
    ++jit_tags[address >> 6]; // The even aligned word stays within this page.
    if (address == 0x47fe && bytes[1] == 0) ++stats->echo_opcode_changes;
#if SODIUM64_DSP_EFFECTS_MODE == 1
    log_effect((address << 16) | (unsigned(bytes[0]) << 8) | bytes[1]);
#endif
}

void initialize() {
    ::new (state) live_state();
    *stats = live_dsp_stats();
#if SODIUM64_DSP_EFFECTS_MODE == 2
    if (!load_effects()) stats->effects_error = 1;
#else
    state->window.init(state->core, apu_ram, reinterpret_cast<unsigned char*>(LIVE_DSP_SHADOW), publish_echo);
    state->window.set_output(state->samples, audio_words);
#if SODIUM64_DSP_EFFECTS_MODE == 1
    if (remote_boot_ram_bytes != 0x800000u) stats->effects_error = 1;
#endif
#endif
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

void account_pcm_call() {
    ++stats->sample_calls;
    if (!(reinterpret_cast<volatile uint32_t*>(0xa4040010)[0] & 1u)) ++stats->renderer_busy;
}

void emit_pcm(uint32_t word) {
    volatile uint32_t* const ring = reinterpret_cast<volatile uint32_t*>(
        reinterpret_cast<uintptr_t>(dsp_buffer) | 0xa0000000u);
    volatile uint32_t* const ai = reinterpret_cast<volatile uint32_t*>(0xa4500000u);
    unsigned at = dsp_pointer;
    ring[at / 4] = word;
    dsp_pointer = (at + 4) & 0x1fff;
    if ((at & 0xfff) == 0xffc) {
        __asm__ volatile("sync" ::: "memory");
        ai[0] = (reinterpret_cast<uintptr_t>(dsp_buffer) + (at & 0x1000)) & 0x00ffffff;
        ai[1] = 0x1000;
    }
    ++stats->pcm;
}

void queue_pcm() {
    account_pcm_call();
    int count = state->window.sample_count();
    if (count < 0 || count >= audio_words || (count & 1)) {
        ++stats->output_errors;
        state->window.set_output(state->samples, audio_words);
        return;
    }

    for (int i = 0; i < count; i += 2) {
        uint32_t word = (unsigned(static_cast<uint16_t>(state->samples[i + 1])) << 16) |
                        static_cast<uint16_t>(state->samples[i]);
#if SODIUM64_DSP_EFFECTS_MODE == 1
        log_effect(word);
#endif
        emit_pcm(word);
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
#if SODIUM64_DSP_EFFECTS_MODE != 2
    state->window.advance(clocks);
#endif
    return true;
}

#ifdef SODIUM64_DSP_LIVE_INPUT_QUEUE
void drain_ram_input() {
    unsigned size = live_dsp_input.size;
    for (unsigned i = 0; i < size; ++i) {
        input_event const& event = live_dsp_input.events[i];
        if (!advance_to(event.epoch)) continue;
#if SODIUM64_DSP_EFFECTS_MODE == 2
        reinterpret_cast<unsigned char*>(LIVE_DSP_SHADOW)[event.address] = event.value;
#else
        state->window.write_ram(event.address, event.value);
#endif
    }
    stats->queued_ram_writes += size;
    live_dsp_input.size = 0;
}
#endif

#if SODIUM64_DSP_EFFECTS_MODE == 2
unsigned replay_effects(unsigned op, unsigned address, unsigned value, uint32_t epoch) {
    if (stats->effects_error) return 0;
    if (effects_end - effects_pos < effects_row) {
        stats->effects_error = 2;
        return 0;
    }
    const uint32_t* const row = effects + effects_pos;
    unsigned output = (row[2] >> 8) & 255;
    unsigned samples = row[2] & 255;
    unsigned words = row[3] >> 8;
    if (row[0] != epoch || row[1] != effects_key(op, address, value) ||
        (row[3] & 0x7f) != live_dsp_input.size || words + samples > effects_end - effects_pos - effects_row ||
        (samples && (op != LIVE_DSP_PCM || samples >= audio_words / 2))) {
        stats->effects_error = 3;
        return 0;
    }
    effects_pos += effects_row;
    drain_ram_input();
    if (!advance_to(epoch)) return 0;
    for (unsigned i = 0; i < words; ++i) {
        uint32_t word = effects[effects_pos++];
        unsigned at = word >> 16;
        if (at & 1) { stats->effects_error = 4; return 0; }
        unsigned char data[2] = {static_cast<unsigned char>(word >> 8), static_cast<unsigned char>(word)};
        unsigned char* shadow = reinterpret_cast<unsigned char*>(LIVE_DSP_SHADOW);
        shadow[at] = apu_ram[at] = data[0];
        shadow[at+1] = apu_ram[at+1] = data[1];
        publish_echo(0, at, data);
    }
    switch (op) {
    case LIVE_DSP_RAM_WRITE:
        reinterpret_cast<unsigned char*>(LIVE_DSP_SHADOW)[address] = apu_ram[address] = value;
        break;
    case LIVE_DSP_RAM_READ:
    case LIVE_DSP_FETCH:
        if (apu_ram[address] != output) stats->effects_error = 5;
        break;
    case LIVE_DSP_REG_WRITE:
        if (dsp_addr < 128) ++stats->writes;
        break;
    case LIVE_DSP_REG_READ:
        ++stats->outputs;
        break;
    case LIVE_DSP_PCM:
        account_pcm_call();
        for (unsigned i = 0; i < samples; ++i) emit_pcm(effects[effects_pos++]);
        break;
    }
#ifdef SODIUM64_DSP_RSP_SWAP
    if (row[3] & 0x80) required(op == LIVE_DSP_REG_READ, epoch);
#endif
    live_dsp_input.exclusive_limit = row[2] >> 16;
    ++stats->effects_rows;
    return output;
}
#endif

} // namespace

#if SODIUM64_DSP_EFFECTS_MODE == 1
extern "C" unsigned live_dsp_effects_size() {
    if (!initialized || stats->effects_error) return 0;
    effects[0] = effects_magic;
    effects[1] = effects_pos * 4;
    return effects[1];
}
#endif

extern "C" unsigned live_dsp_access(unsigned op, unsigned address, unsigned value, uint32_t epoch) {
#ifdef SODIUM64_DSP_RSP_YIELD
    if (op == LIVE_DSP_RENDER_YIELD) {
        live_rsp_yield_service(1);
        return 0;
    }
    if (op == LIVE_DSP_REG_READ || op == LIVE_DSP_PCM) live_rsp_yield_service(0);
#endif
    if (!initialized) initialize();
#if SODIUM64_DSP_EFFECTS_MODE == 2
    return replay_effects(op, address, value, epoch);
#else
#if SODIUM64_DSP_EFFECTS_MODE == 1
    unsigned start = effects_pos;
    unsigned queued = live_dsp_input.size;
    unsigned echo_before = stats->echo_words, pcm_before = stats->pcm;
    unsigned required_before = stats->required_reg + stats->required_echo;
    log_effect(epoch);
    log_effect(effects_key(op, address, value));
    log_effect(0);
    log_effect(0);
#endif
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
#if SODIUM64_DSP_EFFECTS_MODE == 1
    if (!stats->effects_error) {
        bool demanded = stats->required_reg + stats->required_echo != required_before;
        effects[start+2] = (live_dsp_input.exclusive_limit << 16) | ((result & 255) << 8) | (stats->pcm - pcm_before);
        effects[start+3] = ((stats->echo_words - echo_before) << 8) | (demanded ? 0x80 : 0) | queued;
        ++stats->effects_rows;
    }
#endif
    return result;
#endif
}
