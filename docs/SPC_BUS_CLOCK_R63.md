# R63 - native SPC bus-clock prefix

Status: IMPLEMENTED initial directed native-JIT timing correction, default-off.
This is not a complete256-opcode bus bridge, live full DSP, native speed result
or integrable candidate. R61's native upper-memory/window proof is preserved.

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

Final ordered v1 artifact: build_spc_bus_clock_r63_v1/s64-spc-clock-r63-v1.elf,
text54608/data718296/BSS0. The earlier build_spc_bus_clock_r63 artifact is an
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
