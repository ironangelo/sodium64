# KOFF release integration

The R22 extraction remains a draft. Its USB build now links locally with the
isolated bench layout from PR35. The production correction has no dependency
on the faithful compositor, observers or another DSP backend.

The current master KOFF handler immediately disables selected voices. The
extracted R22 correction from `1b12398077ad804874af42fcdc6be34be2793794` latches
release and schedules the next generated sample. Each release sample subtracts
eight from its envelope, clamps at zero and updates the existing cached volumes.
The voice remains enabled until its envelope reaches zero. ADSR1 writes cannot
leave release; existing KON restarts attack/GAIN. No runtime flag, extra DSP
state, diagnostic counter or production menu option is added.

The release arithmetic follows the integrated primary reference in
`tools/dsp-architecture/vendor/snes_spc/SPC_DSP.cpp`, `SPC_DSP::run_envelope`.
This does not close KON delay, every-other-sample register latching, complete
envelope/mixer accuracy, echo/Gaussian or DAC qualification.

Local normal, PROFILE and HW_PROFILE builds pass the linked production proof:
256 KOFF masks;16384 voice/envelope cases;2064 actual sample-scheduler calls;
32 protected ADSR1 writes;32 repeated/cleared KOFF/GAIN/ADSR2 writes;16 complete
KON reset/rate-scheduler calls;10 APU-port callers;128 invalid register addresses.
Three emitted faults are rejected: wrong decrement, wrong timer wrap and bypassed
ADSR release guard. The actual old-master handler demonstrates immediate voice
disable. Existing GAIN handler/stereo4096, BRR57344 and APU65536 contracts pass
on the new normal build. These are software scopes, not fresh native acceptance.

The original R22 native release endpoints remain historical evidence only. That
run included12 observer instructions per release step; it does not measure this
clean production port's cost. Changed note-tail PCM is expected and needs an
appropriate release reference, rather than equality to the truncated old output.

The original standalone USB build exceeded the strict CGRAM boundary by
4,080 bytes after a 4 KiB alignment jump. A local C bridge build with -Oz
saved zero bytes. The separate bench prerequisite keeps zero-initialized
SRAM, WRAM and the empty TLB pages in aligned BSS in REMOTE builds. KOFF now
ends at 0x800be008, 504 bytes below the unchanged 0x800be200 owner. Its
linked KOFF test also runs in USB CI.

The local R47 and KOFF combination fits at the same boundary and passes
the KOFF, BRR and scheduled stereo proofs. That build provides a software
control for the combined audio changes. Exact-head CI and native note-tail,
PCM and cadence evidence remain required before promotion.
