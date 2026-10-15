# R63 - deferred state on opcode-tag escape

Status: IMPLEMENTED and locally qualified; native performance still unmeasured.
`SPC_BUS_CLOCK=1 SPC_CODE_GUARD=2` selects the lazy path. The default remains
the eager guard (`SPC_CODE_GUARD=1`); the full experiment remains default-off.
Mode0 remains an intentionally incorrect cost control, not a candidate.

The eager guard's previous native pair increased the mean completed interval
by0.966007ms (5.297351%) on the matched intro route. This bounded follow-up keeps
ordinary guest-register and NZ deferral on matching source tags. On mismatch,
compiler dirty/load/NZ metadata selects the architectural bytes to commit.
Queued NZ comes from runtime A2; the rest of PSW comes from live S1 only when
flags have been loaded, otherwise from the architectural byte. Fixed bus debt
is still flushed exactly once before the guard. Re-entry uses the ordinary
APU/JIT path. No second interpreter, writable owner or host-SP borrowing.

The linked JIT proof passes28 cases in both modes, with full early/final guest
state and tagged replay. Real writes cover source-opcode changes, dirty A/X/Y/
SP, trailing idle, queued NZ with unloaded flags, and queued NZ with live carry.
Seven explicitly synthetic source-tag publications cover SF-only CLRC/SETP/
CLRV, a clean NOP and POP A/X/Y without NZ. They are not real DSP echo tests.
Each mode rejects three linked mutants omitting debt, NZ or SP commitment.
The within-instruction DBNZ displacement remains exact. The lazy native ELF
also passes192 implied/arithmetic/flags controls against the frozen baseline
and six modified-immediate producers plus132 steady controls against eager.
Seven default-off assembly units remain allocated-section exact to R61.

Fresh native pair: `build_usb_spc_eager_r63_lazy_v1/s64-spc-eager-r63.elf` and
`build_usb_spc_lazy_r63_v1/s64-spc-lazy-native-r63.elf`, mode1 versus2. Both keep
the existing coordinate8 renderer, trace/sampler, bus clock and KOFF fix;
SECTION_OBSERVER0, no audio observers or complete DSP backend. The pair differs
in exactly one compiler JAL word; other allocated sections, section extents,
1636 shared symbol addresses and all12 RSP banks match. Both total854756 bytes.
Linked boot30 cases,43 arena owners and194 ROM slots pass. Allocated endD15C8
leaves2616 bytes below unchanged arenaD2000. See PREFLIGHT.json and the directed,
implied, immediate and default-off companion reports.

Native discriminator: normal install/readback/launch for eager then lazy;
pause at guest/render600, private image, resume and quiet20s capture. Compare
only shared complete absolute guest boundaries and check the same start image.
The planned host-FPS exclusion is192 pixels at [20,23,44,31]; preserve the full
comparison too. Restore coordinate8/menu/install/readback in every outcome.
All raw/game-derived material remains private. One paired intro route cannot
establish complete image/audio fidelity, presentation FPS or corpus acceptance.

Useful result: recover at least half the prior observed overhead, approximately
0.483ms in the matched mean interval, with the start-image control passing.
If this bounded attempt misses that gate, stop guard tuning and advance the
broader fetch/epoch/dataflow and complete resident RSP DSP discriminator.
Absolute DSP epoch, pre-access catch-up, full fetch/echo coherence, live full
DSP/DAC and sustained native60/50 remain OPEN. Master and prior candidates stay
preserved; no integration, broad CI or performance acceptance in this checkpoint.
