# Faithful compositor extraction on integrated master

Status: CANDIDATE. This port is not enabled by default, not merged, and has no
new native acceptance or timing claim. `FAITHFUL_RENDERER=1` selects the coherent
R17 renderer derived from the A11/A13 compositor. This is the visual path used
for the dark ALttP house and rain/layer scenes; R44/R45 are later optimizations
and are outside this extraction.

The source is pinned to `238170abf956da705806f979f9cc256fbc565ac0`, with the selected R17 feature combination
documented in that tree's `docs/USB_HARDWARE_LOOP.md`. Diagnostic branches and
unselected renderer experiments are removed. APU, CPU, DSP, profiler and USB
implementations remain the integrated master versions. The existing decoder
return ownership repair is retained in both resident banks.

The temporary legacy/faithful switch supports a controlled comparison while
qualifying this port. It is not a second user-facing rendering mode. Promotion
still requires the integration gates below; a successful default build alone
does not execute the new renderer.

Current local evidence:

- Normal, PROFILE, USB and independent HW_PROFILE-warmup25 variants compile with the new
  renderer. All resident banks stay at 4 KiB; each slot remains 1000 bytes.
- All twelve RSP banks, including data and extents, are byte-exact against a
  fresh compile of the frozen selected source plus the two explicit decoder
  return NOPs. `scripts/check_faithful_reference.py` regenerates this proof.
- The decoder passes all 9984 linked scalar ownership cases and four emitted
  mutations. This does not model vector arithmetic or pixels.
- Disabled normal build is identical at all 767064 loaded bytes/addresses to
  measured integrated master. APU/CPU-interpreter/DSP sources remain unchanged.
- Emitted boot/ISR/snapshot tests pass 67 cases and check all 24 embedded RSP
  sections after actual clearing. The legacy 27-case proof still passes.
  Lower owner plans and diagnostic upper leases are disjoint; three owner
  corruptions are rejected. The USB bridge retains its 46 cases/four mutants.
- Actual CPU source publication passes four register patterns in each of four
  builds: all twelve writes, uncached fallback descriptors and preserved
  register/HI/LO/CP0 owners. Four emitted faults per build are rejected. This
  does not model RSP consumption or DMA/cache timing.
- APU lookup reset, scheduled GAIN and all 57344 BRR cases pass in the extended
  build. These are structural/arithmetic contracts, not waveform acceptance.

The original R17 plan uses 194 ROM-cache pages, reserving the remaining lower
RDRAM for composition surfaces. ROM bytes still page from cart; this does not
truncate ROM support. The cursor and readonly EntryLo0 construction pass 776
cases/four actual instruction mutants per variant. PI/TLB replacement and
representative native cache cost remain separate gates.

The first USB/HW links correctly rejected growth beyond the legacy BE200
CGRAM bound. The new renderer actually moves Q1 to D2000, as in its selected
native configuration; its linker now checks that explicit owner in every
variant. Q2 and composition surfaces remain in the original proven 4 MiB plan.
No bound was suppressed, and the existing profiler/USB upper leases are kept.

Gates before promotion:

1. Execute CPU boot clears, every emitted source binding and all simultaneous
   memory owners against the new layout, including rejection mutants.
2. Run full compiled producer/consumer, palette/window/math and delayed-DMA
   contracts against this exact port, preserving existing runtime proofs.
3. Add explicit CI coverage for the enabled renderer and check its exact SHA.
   The dedicated port workflow exercises all four configurations; Ares also
   compiles the enabled compositor rather than testing the legacy default.
4. On real N64, compare aligned house/rain/SMW/DKC/Mode7 controls to the faithful
   reference for images and integrated core for guest/APU/PCM behavior. Include
   full-rate cadence, quiet windows, return and verified habitual restoration.
5. Resolve any differences before default promotion. Keep R44/R45 and the
   complete resident-DSP cost test as distinct subsequent gates.

No commercial inputs, captures, states, audio or game-derived hashes belong in
this branch. The emitted-parity manifest contains only original program bytes.

For a fresh checkout, the optional reference-byte proof needs the immutable
source object (`git fetch --depth=1 origin 238170abf956da705806f979f9cc256fbc565ac0`).
The emulator build itself has no historical Git or modified-menu dependency.

[Scoped local proof receipt](evidence/faithful-compositor-local.json).
