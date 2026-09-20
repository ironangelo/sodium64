# Validation strategy

Sodium64 should not depend on frequent manual testing on a real Nintendo 64. Validation is layered so most failures are caught before hardware is involved.

## Levels

### L0 — source and deterministic host checks

Use host-side tests for logic that can be isolated from Nintendo 64 hardware: instruction semantics, flags, addressing, memory mapping, cycle accounting, block translation, cache invalidation, and coprocessor behavior. These tests should eventually compare optimized paths against a trusted reference model.

### L1 — N64 build gate

Every pull request must compile `sodium64.z64` with the project toolchain. CI preserves the ROM, ELF, linker maps, build log, and build metrics as an artifact so code-size and layout changes can be inspected.

### L2 — automated N64 execution

Add emulator-based smoke tests only where they answer questions that host tests cannot: boot behavior, R4300/RSP interaction, DMA, TLB/cache behavior, VI timing, and rendering integration. Prefer deterministic traces, screenshots, and counters over visual inspection alone.

### L3 — milestone emulator validation

Use a small representative ROM corpus to validate compatibility, image/audio behavior, and performance after substantial architectural changes. Do not ask for a new manual test after every small commit.

### L4 — real Nintendo 64 hardware gate

Real hardware is the authority for hardware-specific behavior and final performance. Hardware testing should happen at milestones, with one build designed to answer several concrete questions at once.

## SPC700 translated-code regression scope

The integrated SPC700 cycle/address proof is a **directed regression suite**, not an exhaustive formal proof of the processor.

Current validated edge artifact contains **119 directed execution cases plus two persistent SLEEP/STOP halt groups**. It checks, where applicable:

- compile-time/static cycle debit;
- generated runtime conditional/access debit;
- total `s3` debit against the pinned SPC700 reference;
- source/tag span metadata;
- register, flag, stack, memory and PC postconditions;
- branch taken/not-taken timing;
- SLEEP/STOP entry and repeated scheduler ticks;
- the guest-cycle block contract at the exact **20 + DIV = 32 SPC-cycle** edge;
- an equivalent 32-cycle edge containing real guest reads;
- cached replay without unnecessary recompilation;
- recompilation after a covered entry-tag mutation.

Passing this suite means the audited timing/semantic families and cycle-budget boundaries still match their expected behavior. It does **not** establish:

- exhaustive coverage of all 256 opcodes across all input states/compositions;
- correctness of every observable dummy bus read or I/O side effect;
- safety of every possible intra-block self-modifying-code pattern;
- long-run audio synchronization or PCM equivalence;
- broad game compatibility.

Known accuracy boundaries remain explicit work for Gate C rather than being hidden behind a green timing suite.

The workflow is retained as executable regression infrastructure and should run on `master` when relevant APU/JIT sources or the proof itself change. Do not expand it into a general-purpose second emulator; add cases when they protect a demonstrated architectural contract or a real regression.

## Merge policy

A change can merge without real-hardware validation when its relevant lower-level gates are strong enough and it is cleanly reversible. Changes that materially alter low-level R4300/RSP/RDP/VI behavior may remain unmerged until an emulator or hardware milestone validates them.

`master` should remain the best-known stable state. Experimental architectures belong on branches and may be closed without merge if measurements do not justify them.

## Performance definition

The long-term target is one emulated SNES frame per native display frame with full-speed audio and high fidelity. The following do **not** count as performance improvements toward that target:

- frame skipping;
- deliberate APU underclocking;
- reducing emulated timing work by knowingly breaking compatibility;
- visual omissions that merely hide rendering cost.

Approximation can still be explored when it is demonstrably indistinguishable for software, but fidelity regressions must be explicit and measured.

## Hardware-test cadence

Prefer milestone tests after several validated PRs rather than repeated build-feedback loops. A hardware test request should state:

1. which build/commit to run;
2. which ROMs or test ROMs to use;
3. what observable result is expected;
4. what metrics or screenshots are useful;
5. what technical decision the result will unlock.

For SRAM-capture milestones, preserve the exact runtime SHA, wrapped-ROM hash, workload hash, settings, warmup/measured-window contract, sample count, matching ELF/map and returned save hash. A video or subjective smoothness report is useful observational context but does not replace the captured hardware counters.
