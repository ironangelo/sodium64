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
