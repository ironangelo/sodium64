#include "full_dsp_window.h"

#ifdef SODIUM64_DSP_FULL_WINDOW
#include <string.h>
#include <stdint.h>

#ifdef SODIUM64_DSP_LIVE_CORE
#include "live_dsp.h"
static inline uint32_t native_count() {
    uint32_t result;
    __asm__ volatile("mfc0 %0,$9" : "=r"(result) :: "memory");
    return result;
}

static inline void run_dsp(SPC_DSP& core, unsigned clocks) {
    uint32_t start = native_count();
    core.run(clocks);
    uint32_t elapsed = native_count() - start;
    live_dsp_stats* stats = reinterpret_cast<live_dsp_stats*>(LIVE_DSP_STATS);
    stats->core_ticks += elapsed;
    ++stats->core_runs;
}
#else
static inline void run_dsp(SPC_DSP& core, unsigned clocks) {
    core.run(clocks);
}
#endif

void SPC_DSP_Window::init(SPC_DSP& dsp, unsigned char* cpu_ram,
                         unsigned char* shadow_ram, echo_publish_t callback,
                         void* context) {
    uintptr_t a = (uintptr_t)cpu_ram, b = (uintptr_t)shadow_ram;
    assert(cpu_ram && shadow_ram && (a < b ? b - a : a - b) >= 65536);
    (void)a; (void)b;
    if (core) {
        flush();
        core->echo_publish = 0; core->echo_publish_context = 0;
    }
    core = &dsp; cpu = cpu_ram; shadow = shadow_ram;
    pending = count = 0; publish = callback; publish_context = context;
    memcpy(shadow, cpu, 65536);
    core->init(shadow);
    core->echo_publish = publish_echo;
    core->echo_publish_context = this;
}

bool SPC_DSP_Window::echo_hazard(unsigned addr) const {
    return pending && addr >= echo_first && addr < echo_end;
}

#ifdef SODIUM64_DSP_LIVE_INPUT_QUEUE
unsigned SPC_DSP_Window::echo_write_floor() const {
    // ESA/EDL writes are applied only after the producer has drained the
    // queue. Until then include the current and latched bases, the old
    // address used by phase 29/30, and either possible ring length.
    unsigned base = core->m.regs[SPC_DSP::r_esa] << 8;
    unsigned latched_base = core->m.t_esa << 8;
    unsigned ptr = core->m.t_echo_ptr;
    unsigned length = (core->m.regs[SPC_DSP::r_edl] & 15u) << 11;
    unsigned latched_length = core->m.echo_length;
    if (length < latched_length) length = latched_length;
    if (length < core->m.echo_offset + 4u) length = core->m.echo_offset + 4u;
    if (base + length > 65536 || latched_base + length > 65536 || (ptr & 3u))
        return 0;
    if (latched_base < base) base = latched_base;
    return ptr < base ? ptr : base;
}
#endif

void SPC_DSP_Window::start_echo_projection() {
    unsigned phase = core->m.phase;
    echo_first = 65536;
    echo_end = 0;
    echo_offset = core->m.echo_offset;
    echo_length = core->m.echo_length;
    echo_right_only = phase == 30;
    echo_clock = phase <= 29 ? 30 - phase : (echo_right_only ? 1 : 31);

    // Phase 22 captures the pointer, 28 gates the left write and 29
    // advances the offset and gates the right write.
    unsigned latched_address = (core->m.t_esa * 256u + echo_offset) & 65535u;
    echo_address = phase <= 22 || phase == 31 ? latched_address : core->m.t_echo_ptr;
    echo_writes_after_latch = !(core->m.regs[SPC_DSP::r_flg] & 0x20);
    bool latched_write = !(core->m.t_echo_enabled & 0x20);
    echo_can_write = echo_right_only ? latched_write :
        (echo_writes_after_latch || (phase == 29 && latched_write));
}

void SPC_DSP_Window::project_echo(unsigned clocks) {
    while (echo_clock <= clocks) {
        if (echo_can_write) {
            // Enclose both channel writes. The right channel may still be
            // one clock away. Extra addresses can cause an early catch-up.
            if (echo_address < echo_first) echo_first = echo_address;
            if (echo_address + 4 > echo_end) echo_end = echo_address + 4;
        }
        if (!echo_right_only) {
            if (!echo_offset) echo_length = (core->m.regs[SPC_DSP::r_edl] & 15u) << 11;
            echo_offset += 4;
            if (echo_offset >= echo_length) echo_offset = 0;
        }
        echo_address = ((core->m.regs[SPC_DSP::r_esa] << 8) + echo_offset) & 65535u;
        echo_clock += echo_right_only ? 31 : 32;
        echo_right_only = false;
        echo_can_write = echo_writes_after_latch;
    }
}

void SPC_DSP_Window::advance(unsigned clocks) {
    while (clocks) {
        if (!pending) start_echo_projection();
        unsigned step = clock_capacity - pending;
        if (step > clocks) step = clocks;
        pending += step; clocks -= step;
        if (pending == clock_capacity) flush();
        else project_echo(pending);
    }
}

void SPC_DSP_Window::apply(event_t const& event) {
    if (event.reg) core->write(event.addr, event.data);
    else shadow[event.addr] = event.data;
}

void SPC_DSP_Window::flush() {
    unsigned cursor = 0;
    for (unsigned i = 0; i < count; i++) {
        event_t const& event = events[i];
        assert(event.clock >= cursor && event.clock <= pending);
        if (event.clock > cursor) run_dsp(*core, event.clock - cursor);
        cursor = event.clock;
        apply(event); // same-clock events retain producer order
    }
    if (pending > cursor) run_dsp(*core, pending - cursor);
    pending = count = 0;
}

void SPC_DSP_Window::queue(unsigned addr, unsigned data, bool reg) {
    if (count == event_capacity) flush(); // do not discard the new event
    event_t event;
    event.addr = (unsigned short)addr;
    event.clock = (unsigned char)pending;
    event.data = (unsigned char)data;
    event.reg = (unsigned char)reg;
    if (!pending) apply(event);
    else events[count++] = event;
}

int SPC_DSP_Window::read_ram(unsigned addr) {
    assert(addr < 65536);
    if (echo_hazard(addr)) flush();
    return cpu[addr];
}

void SPC_DSP_Window::write_ram(unsigned addr, unsigned data) {
    assert(addr < 65536);
    if (echo_hazard(addr)) flush();
    // Overflow must catch up before this producer write becomes observable.
    if (count == event_capacity) flush();
    cpu[addr] = (unsigned char)data;
    queue(addr, data, false);
}

static bool output_may_publish(unsigned addr, unsigned phase, unsigned clocks) {
    // GEN_DSP_TIMING publishes V7/V8/V9 for voice n at 2/3/4 + 3*n.
    // phase is the next unexecuted clock. V7 publishes global ENDX.
    if (addr == SPC_DSP::r_endx) {
        unsigned next = phase <= 23 ? 2 + 3 * (phase / 3) : 32 + 2;
        return clocks > next - phase;
    }
    unsigned voice_reg = addr & 15;
    if (voice_reg != SPC_DSP::v_envx && voice_reg != SPC_DSP::v_outx)
        return false;
    unsigned next = 3 * (addr >> 4) + (voice_reg == SPC_DSP::v_envx ? 4 : 3);
    return clocks > ((next - phase) & 31);
}

int SPC_DSP_Window::read_reg(unsigned addr) {
    assert(addr < SPC_DSP::register_count);
    if (pending && output_may_publish(addr, core->m.phase, pending)) {
#ifdef SODIUM64_DSP_RSP_SWAP
        // Count ownership after the live bridge has serviced any pending yield.
        if (!(reinterpret_cast<volatile uint32_t*>(0xa4040010u)[0] & 1u))
            ++reinterpret_cast<live_dsp_stats*>(LIVE_DSP_STATS)->required_reg_busy;
#endif
        flush();
        return core->read(addr);
    }

    // Return the newest producer write, including an earlier write at the
    // same clock. A RAM write to the same numeric address is independent.
    for (unsigned i = count; i != 0; --i) {
        const event_t& event = events[i - 1];
        if (event.reg && event.addr == addr)
            return addr == SPC_DSP::r_endx ? 0 : event.data;
    }
    return core->read(addr);
}

void SPC_DSP_Window::write_reg(unsigned addr, unsigned data) {
    assert(addr < SPC_DSP::register_count);
    // These three registers are the inputs to the echo address/write
    // projection. Keep them constant while any clocks are pending.
    if (addr == SPC_DSP::r_esa || addr == SPC_DSP::r_edl || addr == SPC_DSP::r_flg) flush();
    queue(addr, data, true);
}

void SPC_DSP_Window::publish_echo(void* context, unsigned addr,
                                unsigned char const* bytes) {
    SPC_DSP_Window* self = (SPC_DSP_Window*)context;
    assert(addr < 65535);
    self->cpu[addr] = bytes[0]; self->cpu[addr + 1] = bytes[1];
    // Only real, enabled DSP writes publish. A future native callback must
    // make CPU caches and SPC JIT code tags observe these two bytes.
    if (self->publish) self->publish(self->publish_context, addr, bytes);
}

void SPC_DSP_Window::set_output(SPC_DSP::sample_t* out, int size) {
    flush(); core->set_output(out, size);
}
int SPC_DSP_Window::sample_count() { flush(); return core->sample_count(); }
void SPC_DSP_Window::reset() { flush(); core->reset(); }
void SPC_DSP_Window::soft_reset() { flush(); core->soft_reset(); }
void SPC_DSP_Window::load(unsigned char const regs[SPC_DSP::register_count]) {
    flush(); core->load(regs);
}
void SPC_DSP_Window::copy_state(unsigned char** io, SPC_DSP::copy_func_t copy) {
    flush(); core->copy_state(io, copy);
}
bool SPC_DSP_Window::check_kon() { flush(); return core->check_kon(); }
#endif
