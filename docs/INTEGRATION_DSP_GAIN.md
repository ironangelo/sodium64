# Clean-master integration: preserve GAIN stereo accumulators

The scheduled GAIN handler used t4 for the voice offset while dsp_sample kept
the running right channel in t4. Due envelopes could therefore discard earlier
voices. This applies to master's cached mixer as well as the optional dry mixer
where R33 first isolated it. Use existing t1/t2 handler scratch, including direct
GAIN's envelope/timer stores; instruction count and envelope/rate behavior stay
the same. No dry-mix flag, observer, transport or experimental renderer is added.

Historical native handler evidence: experiment/sub-alpha-r44,
docs/DSP_GAIN_2026-10-11.md and docs/evidence/dsp-gain-2026-10-11.json. The actual
N64 handler had 16/16 accumulator failures before and 0/16 after, with touched
fields restored and the paused image/PCM/boundary preserved. This is invariant
evidence for the handler, not new-master whole-waveform acceptance.

The clean-master linked proof covers all eight voices and 256 GAIN bytes with
independent 64-bit stereo sentinels, exact direct stores/custom rate and register,
HI/LO/CP0 preservation. Another 2,048 full legacy-scheduler samples check both
channels against independent expected envelopes and cached-volume arithmetic.
An emitted SLL mutation restores the clobber and must reject. Normal and PROFILE
builds execute the gate in CI; existing emulator regression gates still apply.

This repairs audio correctness. Gaussian interpolation, echo, latching/clock
accuracy and complete DSP/DAC fidelity remain open. No game-speed claim follows.
Rollback: revert this PR; there are no state or serialization changes.
