#ifndef SODIUM64_FULL_DSP_WINDOW_H
#define SODIUM64_FULL_DSP_WINDOW_H

#ifdef SODIUM64_DSP_FULL_WINDOW
#include "../third_party/snes_spc/SPC_DSP.h"

// Semantic boundary for a future resident backend. No native SPC bridge yet.
// All producer bus accesses must use this interface. Caller owns two disjoint
// 64KiB RAM buffers and the core; they must outlive this controller.
class SPC_DSP_Window {
public:
    enum { event_capacity = 64 };
    typedef void (*echo_publish_t)(void*, unsigned, unsigned char const*);

    SPC_DSP_Window() : core(0), pending(0), count(0) {}
    void init(SPC_DSP&, unsigned char* cpu_ram, unsigned char* shadow_ram,
              echo_publish_t = 0, void* context = 0);
    void advance(unsigned clocks);
    void flush();
    int read_ram(unsigned addr); // includes instruction fetches
    void write_ram(unsigned addr, unsigned data);
    int read_reg(unsigned addr);
    void write_reg(unsigned addr, unsigned data);
    void set_output(SPC_DSP::sample_t*, int size);
    int sample_count(); // catch up before consuming PCM
    void reset();
    void soft_reset();
    void load(unsigned char const regs[SPC_DSP::register_count]);
    void copy_state(unsigned char**, SPC_DSP::copy_func_t);
    bool check_kon();
    unsigned pending_clocks() const { return pending; }
    unsigned pending_events() const { return count; }

private:
    SPC_DSP_Window(SPC_DSP_Window const&);
    SPC_DSP_Window& operator=(SPC_DSP_Window const&);
    struct event_t {
        unsigned short addr;
        unsigned char clock, data, reg;
    } events[event_capacity];
    SPC_DSP* core;
    unsigned char *cpu, *shadow;
    unsigned pending, count;
    echo_publish_t publish;
    void* publish_context;
    bool echo_hazard(unsigned addr) const;
    void queue(unsigned addr, unsigned data, bool reg);
    void apply(event_t const&);
    static void publish_echo(void*, unsigned, unsigned char const*);
};
#endif
#endif
