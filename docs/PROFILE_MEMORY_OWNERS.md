# Profiling must preserve the measured renderer

The existing16KiB profiling buffer was linked into the base arena before the
embedded RSP blobs. In the measured original-master HW ELF, static end800C02B0
exceeds the first CGRAM owner800BE200. Executing the actual boot clear destroys
1156 nonzero bytes of Mode7 code and395 nonzero bytes of its data before upload.
This is a diagnostic integrity defect. Earlier ordinary-renderer control counts
remain scoped observations; they never establish Mode7/DSP-1/full fidelity.

PROFILE/HW_PROFILE now use an explicitly initialized20KiB lease at physical
448000..44D000. It is disjoint from base4MiB, the R61 resident-DSP/snapshot
owners and USB bench440000..442000. No upper ELF/BSS payload is loaded. Main
checks exact IPL3-detected8MiB before upper writes or VI; unknown/base4MiB
diagnostic boots stop. Ordinary releases keep their original loaded bytes.
The link must stay below800BE200; no renderer/cache/CGRAM address is moved.

Boot retires cached lines, clears only this lease and initializes headers and
both32-byte guards. The ISR retains its k0/k1-only contract. Terminal hardware
capture verifies both guards; failure cannot publish a completed capture or
resume the guest. Initializing the hardware profiler invalidates a prior SRAM
magic outside the measured interval. SRAM capture is still the existing
terminal diagnostic, with the paired-menu isolated-save route on real hardware.

S64H version2 adds lease bounds and a verified-guard receipt in reserved words;
the decoder keeps historical version1 readable without inventing guard proof.
Default timing stays2 warmup plus5 measured60-VI windows. An explicit
HW_PROFILE_WARMUP=2..60 supports later original-boot scenes. The reader requires
the identical predeclared --expected-warmup; unannounced timing mismatches fail.
Presentation/DAC fidelity and arbitrary gameplay acceptance are separate gates.

Linked gates execute exact8MiB admission, owner initialization, the full base
clear, all four RSP-bank survival comparisons, ISR register/ring behavior,
successful terminal header/decoding and both failed guards. The original
linked HW ELF is retained as a real negative counterexample. Native capture
and exact-head CI are required before this diagnostic repair is integrated.
