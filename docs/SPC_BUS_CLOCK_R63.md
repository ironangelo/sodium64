# R63 - native SPC bus-clock prefix

Status: IMPLEMENTED directed native-JIT timing/address correction, default-off.
This is not a complete256-opcode bus bridge, live full DSP, native speed result
or integrable candidate. R61's native upper-memory/window proof is preserved.

## 16-bit PC and pointer wrap correction

WRAP_AUDIT records10 open cases in the initial13 on the frozen branch ELF.
BRA/BNE at$FFFE retain the old PC instead of reaching$0000; negative relative
targets can corrupt the emitted ORI instead of encoding the16-bit PC. The
compiler fetch cursor crosses$FFFF into non-SPC data, allowing NOP to decode
unrelated bytes and changing registers/stack. An operand crossing the boundary
can therefore read the wrong byte. CALL's return bytes were already right,
but its final source-tag offset was$1000, outside the valid$0000..$0FFC range.
JMP[$FFFB+X] reads its second pointer byte from$10000 rather than$0000.

The enabled compile fetch now wraps after every byte; a completed instruction
that wraps the source PC ends its block, retaining the independent source-span
bound. Conditional and unconditional relative targets are masked before JIT
encoding. The indirect jump wraps its second pointer-byte address before its
real read. Default-off paths are unchanged. The original snippet loader now
also wraps its source bytes, so operand-crossing tests exercise the real case.

WRAP_CURRENT passes45 directed cases: all flag-branch conditions at the upper
boundary and negative targets, BBC/BBS/CBNE/DBNZ negative targets, NOP/MOV source
wrap, CALL/PCALL return/operand edges, indirect pointer wrap, and read/write
effective-address wraps through X/Y and indirect-Y. It checks all bus addresses/
end clocks, totals, PC/register/flag/memory results, exact first/last source-tag
offsets and cached replay. Three actual linked/emitted mutations (omit fetch
wrap, omit wrap block boundary, omit second pointer-byte wrap) are rejected.

Clock32/address25/word23/control288/branch-bit172/implied192/KOFF30 still pass
on build_spc_bus_clock_r63_wrap/s64-spc-wrap.elf, bus clock1/KOFF1, linked
text+data774120 bytes/BSS0. Six default-off ASM units still match allocated
sections of R61 source61505bc6 byte for byte. Previous artifacts preserved.
No COM3/native speed, full fidelity, broad CI or integration claim.

Next implement the instruction-fetch/pre-access/absolute DSP epoch contract;
wrap correctness does not solve compile-time reads of future echo-modified
code or I/O fetches. Full resident RSP DSP still needs an early native full-work
cost discriminator. All full DSP/DAC/native60/50/corpus/integration gates OPEN.

## Branch, bit and implied-access correction

BRANCH_BIT_AUDIT records14 open cases in172 on the frozen control ELF:
DBNZ dp charges its displacement fetch before the write (write5 instead of4);
DBNZ Y has no dummy PC read; (X)/(X)+/(X),(Y) omit their dummy PC reads;
(X) stores omit the destination dummy read; (X)+ loads place their quirk idle
before instead of after the load; all three memory-CMP forms place their
trailing idle before the final read. The other158 directed cases match.

The enabled path now performs those accesses and positions the fetch/idles
according to the pinned primary sequences. BRANCH_BIT_CURRENT passes all172
cases, checking bus type/address/end clock, total cycles, PC, register/flag/
memory outcomes and cached replay. Coverage includes all conditional branch
flags, all8 BBC/BBS bits and both paths, CBNE direct/indexed, DBNZ wrap/zero,
absolute bit operations, SET1/CLR1, TSET1/TCLR1 and the8 indirect/CMP cases.
It is directed coverage at the stated operands, not all inputs or compositions.

IMPLIED_AUDIT has0/192 exact bus traces:30 implied opcodes charged a PC read
without emitting it; SLEEP/STOP performed their entry read one cycle late.
JIT_PC_READ emits a real read plus the required remaining idle cycles while
retaining the old two-instruction charge-only expansion when default-off.
Enabled SLEEP/STOP place their idle after the entry read. IMPLIED_CURRENT now
passes192 variants (32 opcodes, three incoming PSWs, with/without a queued-NZ
prefix). All register/PSW/PC/halt outcomes and totals match the frozen control
ELF, and cached replay is exact. The frozen outcomes are regression controls,
not an independent exhaustive arithmetic-semantics oracle.

Clock32/address25/word23/control288/KOFF30 and the existing linked/emitted
mutations still pass after these changes. Six default-off ASM units remain
allocated-section byte-exact source61505bc6. New artifact
build_spc_bus_clock_r63_branch/s64-spc-branch.elf, bus clock1/KOFF1, linked
text+data773992 bytes/BSS0. Prior control/KOFF binaries are preserved. These
are host executions of the real native JIT, not N64 throughput measurements.

Next establish the remaining16-bit address/PC edges and instruction-fetch
contract before the live absolute DSP epoch/pre-access/echo/cache/tag bridge.
Required real reads are now emitted for these audited families; opcode and
operand fetches still occur through the compile-time path, which is not
equivalent to handling DSP echo changes to future instructions. No live full
DSP, native60/50/fidelity/corpus/CI/integration claim; full resident RSP DSP
still needs its early native full-work cost discriminator.

## Stack and control bus correction

The initial actual-JIT CONTROL_AUDIT has17 open cases: PUSH/POP lack a real
dummy PC read; CALL/PCALL place their idle cycles incorrectly; TCALL/BRK read
the vector before pushing the return state. Multi-byte stack accesses also
cross the page boundary: CALL at SP$00 writes$00FF instead of$01FF, while
RET/RETI pull from$0200 instead of$0100, producing the wrong return PC.
The original numeric audit is preserved with its exact ELF hash.

With SPC_BUS_CLOCK enabled, jit_dummy_pc emits a real bus read without advancing
the compile PC; push/pull idles follow the primary sequence. CALL/PCALL move
the post-push idles after the writes; TCALL/BRK push before fetching the vector.
Stack addressing wraps within page one. BRK pushes the old PSW and changes I/B
after the vector reads. RET also now loads the full apu_read8 compiler target:
the old relocatable LI retained only its low16 bits, so the JAL worked but the
bus classifier missed that first read. All changes remain default-off.

CONTROL_CURRENT checks36 directed cases across clocks1/21/42/255 and two JIT
buffer positions:288 variants, including96 actual resets. They cover all16
TCALL vectors, single push/pull forms, CALL/PCALL/RET/RETI/BRK, and multi-byte
push/pull wraps. Bus addresses/order/end clocks, aggregate totals, PC, A/X/Y/SP/
PSW, written bytes and boundary canaries match, with exact cached replay.
Two emitted-code mutations (wrong dummy PC; missing stack-page restoration)
are rejected. This is directed coverage, not all-opcode/all-state acceptance.

The32 clock,25 address,23 word and30 KOFF cases still pass on the control ELF;
the existing clock/word mutations still fail as required. Default-off allocated
sections of six ASM units, now including apu_control, remain byte-exact R61
source61505bc6. Artifact build_spc_bus_clock_r63_control/s64-spc-control.elf,
SPC_BUS_CLOCK=1/DSP_KOFF_RELEASE=1; total linked text+data773928 bytes, BSS0.
The prior two-word KOFF delta proof stays pinned to its own preserved binaries.
No COM3 use or native fidelity/DAC/FPS/CI/integration claim for this batch.

Next audit branch/bit paths and the remaining dummy-PC instructions using the
same real JIT. Absolute DSP epoch, pre-access catch-up and future-code echo/
cache/tag integration still precede a live full-DSP bridge; full resident RSP
DSP still needs an early native full-work cost discriminator.

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
