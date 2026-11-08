# KOFF release integration

Status: BLOCKED on the standalone USB layout gate. This clean extraction starts
at master `bac1a4df51bd706e778730b488a50be8c5fc6f47`; it does not include PR21,
the faithful compositor, observers or another DSP backend.

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

The standalone USB build fails its unchanged strict linker assertion:
`__bss_end=0x800bf1f0 > first CGRAM owner0x800be200`, an overrun of4080 bytes.
The256-byte text growth pushes the pre-data boundary across a4KiB alignment.
An isolated `-Oz` compile of the laboratory C bridge saves zero bytes; that
negative control is retained and does not change the build flags. Do not relax
the CGRAM owner assertion or remove release correctness to force a green build.

The selected faithful compositor has its own explicit larger lower-memory plan,
but PR32 is still blocked on native qualification. This extraction must wait
for a qualified layout/default promotion, or a separately proven laboratory
layout repair. All required CI, applicable native note-tail/cadence controls and
combined baseline checks must pass before this draft is integrated. No speed
gain, whole-audio fidelity or current native acceptance is claimed.
