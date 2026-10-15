# R63 - native SPC bus-clock prefix

Status: IMPLEMENTED directed native-JIT timing/address correction, default-off.
This is not a complete256-opcode bus bridge, live full DSP, native speed result
or integrable candidate. R61's native upper-memory/window proof is preserved.

## KOFF release guest-register repair

The actual release-enabled binary proved a separate legacy I/O defect. With A
already live in the JIT, MOV $F3,#$01 targeting KOFF changed A from$11 to$01;
the following store wrote$01. `write_koff` used T7 for its mask, but T7 holds
the live SPC accumulator. This is an executed register-corruption case, not a
claim that a particular commercial audio symptom has been explained.

The release path now uses T4, an existing DSP write-handler scratch register.
Only two native instruction words change; data/size is identical. No cycle,
voice-release policy or new state is introduced. This repair is gated by the
existing DSP_KOFF_RELEASE option and works independently of SPC_BUS_CLOCK.

`test_spc_koff_abi.py` executes30 real-JIT/real-handler variants: three live A
values, five masks including zero/all/high-bit voices, immediate and X sources.
The baseline corrupts A in26 cases; fixed binaries have zero failures with bus
clock both on and off. All8 mode/deadline/envelope fields and enabled bits are
checked after every case; cycle totals and cached outcomes stay exact. Six
distinct linked DSP-write handlers also preserve A/X/Y in directed controls.
COUNTEREXAMPLES/CURRENT/CLOCK_OFF.json pin the actual ELF hashes. Default-off
allocated sections of all five changed ASM units remain exact source61505bc6.
No native gameplay/DAC/fidelity or performance acceptance is asserted yet.

## Word bus correction

The actual JIT exposed seven word-page failures: MOVW read/write, ADDW/SUBW/
CMPW and INCW/DECW used0x0200 after0x01FF instead of wrapping to0x0100.
INCW/DECW also read both bytes before either write. Required order is low read,
low write, high read, high write. WORD_AUDIT records the original address/order
failure; its initial SUBW expected-H bit omitted8. Current expectations use
the primary12-bit no-borrow rule (0x0611-0x1235 ->0xF3DC, PSW0xA8).

Enabled word templates now preserve the direct-page bit when advancing an
address. INCW/DECW retain a16-bit low adjustment across the low write and high
read, propagate carry/borrow and publish bytes in the required sequence.
The shared multi-instruction EMIT_DP_NEXT macro is emitted before a bus JAL,
never placed in its single-instruction delay slot. No guest cycles are omitted.

WORD_CURRENT passes23 actual-JIT cases: seven operations plus16 increment/
decrement boundary values. It checks exact bus order/addresses/clocks, data,
registers/NZH flags, an unchanged0x0200 canary and cold/cached outcomes. Two
emitted instruction mutations (omit page mask; omit low write) are rejected.
The preceding32 clock/buffer cases and25 data-address cases remain exact.
Default-off allocated sections of all four bus-template ASM units match R61 byte
for byte. Current artifact text54768/data718296/BSS0, no hardware/CI claim.

## Address-family correction

The first13-case data-bus audit found nine open cases despite correct aggregate
cycles. Absolute/indexed pure writes omitted destination dummy reads; indirect
pointers read high before low; indirect-indexed stores placed the index idle
before pointer reads; direct-to-direct MOV charged its target operand fetch
before the source read. ADDRESS_AUDIT.json preserves that initial failed stage.

The enabled path now emits those reads, orders both indirect pointer bytes low
then high with8-bit direct-page wrap, places read/store index idles in their
distinct primary-source positions, and fetches the second direct operand after
the source read. No required guest cycles are added or removed from totals.
The full data-bus trace observes every real apu_read8/write8 call, rather than
only F3 handlers.25 directed cases now match address/type/end clock and totals,
including X/Y/absolute forms, indirect reads/writes, direct-to-direct transfer,
RMW, word read/write and three DP1 pointer-wrap cases. Cached replay is exact.
This tests the selected words atF3/F4, not every word wrap or opcode state.

The32 initial clock/buffer cases, eight actual buffer resets and both linked
mutants still pass after these changes. Default-off allocated sections of both
ASM units remain exact source61505bc6. Current artifact text54704/data718296/
BSS0; ADDRESS_CURRENT.json pins its ELF hash. No hardware/CI or speed result.
Next cover the remaining word-page edges, branch/bit/stack paths and dummy PC
reads using the same trace. Epoch/fetch/echo/tag/live-full-DSP gates stay open.

The existing linked MIPS interpreter executes the real JIT compiler, its emitted
code and real DSP I/O handlers. Original numeric snippets expose a causal gap:

| Snippet | Required DSP bus end clocks | Prior mid-block S3 clocks |
| --- | --- | --- |
| MOV A,$F3 | read3 | read1 |
| NOP;NOP;MOV A,$F3 | read7 | read1 |
| MOV $F3,A | read3,write4 | write1; dummy read absent |
| MOV $F3,#imm | read4,write5 | read1,write2 |

All prior aggregate block totals were correct. The missing timestamp prefix
is compile S2's fixed fetch/idle debit, previously applied only at block return.
Do not pass mid-block S3 directly to the R61 controller without correcting it.
Primary bus sequence:
[pinned ARES SPC700 instructions](https://github.com/ares-emulator/ares/blob/9408cb43d4948fc3ea6e152a307a34348df3fe04/ares/component/processor/spc700/instructions.cpp).

`SPC_BUS_CLOCK=1` publishes accumulated fixed debt before each emitted guest
bus call, clearing compile debt after the inserted ADDI. It uses only the
emitter's existing T0/T1 clobbers and duplicates its ordinary store/cache/
bounds sequence, without borrowing Sodium's non-stack SP or a live register.
The direct-address pure-store dummy cycle now emits a real read rather than
only charging an idle. Total/worst-case block cycle accounting is preserved.

`test_spc_bus_clock.py` runs32 variants of these four snippets across clocks
1/21/42/255 and normal/near-end JIT pointers. All corrected access clocks,
aggregate totals and cached replay pass; eight buffer resets execute. Two
actual linked-instruction mutations (omit prefix; retain debited prefix) fail.
The same32 baseline variants reproduce the wrong mid-block timestamps.
Default-off allocated assembler sections of apu_emitter/apu_address match the
exact R61 source61505bc6 byte for byte. No expanded MIPS VM or new emulator is
introduced. See COUNTEREXAMPLES/DIRECTED/BUILD.json and the executable scripts.

Initial ordered v1 artifact: build_spc_bus_clock_r63_v1/s64-spc-clock-r63-v1.elf,
text54608/data718296/BSS0 before the address-family extension above. The earlier build_spc_bus_clock_r63 artifact is an
off/control build: its early Make flag placement was overwritten by the base
ASFLAGS assignment. Corrected Make placement and a separate v1 build ensure
the directed proof actually executes the enabled path. No physical run or CI.

Next extend the same real data-bus trace to absolute, indexed, indirect,
word/bit/RMW/branch/stack paths. The generic prefix cannot repair a template
whose internal fetch/read/idle order is wrong or whose dummy access is absent.
Repair those demonstrated mismatches before a native DSP bridge. Also preserve
conditional/aggregate/halt/tag behavior; echo-modified future instruction
fetches require more than next-block invalidation. Ordinary RAM currently
reads/writes before its helper's debit, so the later backend must catch up
before that actual access. S3 is relative scheduling debt, not by itself a new
absolute DSP epoch. Exact live DSP integration and its full resident RSP cost
discriminator remain open with native60/50/fidelity/corpus/master gates.

No commercial inputs or derived data are used by these proofs. Master and all
prior candidates remain unchanged; this branch is an isolated experiment.
