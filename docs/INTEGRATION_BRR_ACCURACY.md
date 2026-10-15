# Clean-master integration: BRR integer decoding

The inherited decoder disagrees with the primary S-DSP arithmetic in 5,660 of
7,168 original synthetic blocks. Extract R20 (bbe46447) as a permanent correction:
use arithmetic floors for negative filter terms, handle invalid ranges13..15,
clamp the intermediate to signed16 and preserve signed15 half-sample storage.
Pitch conversion, envelopes, clocks, DSP mixing and every RSP bank stay separate.
No inaccurate alternate execution mode or diagnostic hook is added.

Normal and PROFILE N64 builds pass locally. The reused linked oracle executes
57,344 voice cases, all ranges/filters/eight voices, directed extreme histories
and deterministic random inputs. Four actual instruction mutations fail. All
sample/address writes stay within the selected voice, with unrelated registers,
HI/LO and CP0 preserved. A clean-master ELF reproduces exactly the5,660 failing
blocks. CI executes the positive/mutation gates on both build configurations;
the optional old-ELF counterexample was executed locally and is not a CI asset.

Primary arithmetic authority is Snes9x1.63 SPC_DSP::decode_brr. R20's independent
adapter and later native BRR observer evidence are preserved on the continuity
branch in DSP_BRR_ACCURACY_2026-10-11.md and its curated evidence. Their native
scene/ring observations establish the bounded decoder correction, not this
clean-head whole-waveform or DAC qualification. Changed PCM is expected; the old
incorrect PCM is not a fidelity oracle. The native cost of this correction must
remain explicit in the measured combined baseline rather than being called a
speed optimization. Interpolation/echo/full-DSP/latching accuracy remain open.

Rollback is a direct revert; there are no new owners, settings or state formats.
