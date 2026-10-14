#include "full_dsp_window.h"

#ifdef SODIUM64_DSP_FULL_WINDOW
#include <string.h>
#include <stdint.h>

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
    if (!pending || core->m.phase == 31) return false;
    unsigned base = core->m.phase <= 22 ?
        (core->m.t_esa * 256u + core->m.echo_offset) & 65535u :
        (unsigned)core->m.t_echo_ptr;
    // Conservative for both channels, including RAM writes and code fetches.
    // A window ends before another phase22 can select a different address.
    return ((addr - base) & 65535u) < 4;
}

void SPC_DSP_Window::advance(unsigned clocks) {
    while (clocks) {
        unsigned step = 32u - core->m.phase - pending;
        if (step > clocks) step = clocks;
        pending += step; clocks -= step;
        if ((unsigned)core->m.phase + pending == 32) flush();
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
        if (event.clock > cursor) core->run(event.clock - cursor);
        cursor = event.clock;
        apply(event); // same-clock events retain producer order
    }
    if (pending > cursor) core->run(pending - cursor);
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

int SPC_DSP_Window::read_reg(unsigned addr) {
    assert(addr < SPC_DSP::register_count);
    flush();
    return core->read(addr);
}

void SPC_DSP_Window::write_reg(unsigned addr, unsigned data) {
    assert(addr < SPC_DSP::register_count);
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
