# Standalone S-DSP reference

The six source/header files are copied without changes from
`blarggs-audio-libraries/snes_spc` commit
`ec8ee2bbe30451614c1d02a83f7af1c97d497d45`, `snes_spc/`.
They identify themselves as snes_spc 0.9.0, copyright 2007 Shay Green,
LGPL-2.1-or-later. The upstream license is retained as `COPYING.LESSER`.

Author's description: https://slack.net/~ant/libs/audio.html
Pinned source: https://github.com/blarggs-audio-libraries/snes_spc/tree/ec8ee2bbe30451614c1d02a83f7af1c97d497d45/snes_spc

Only the optional `FULL_DSP_PROBE=1` diagnostic links this reference. It does
not replace the normal DSP or generate/substitute gameplay audio. The wrapper
uses original synthetic RAM/register patterns to measure the complete core
on the N64 before deciding how to implement the missing DSP behavior.

Build with the real big-endian target and O64 ABI. `-fno-builtin` is used;
`-ffreestanding` hides the SDK C++ allocator declarations needed to parse the
old upstream headers. No dynamic allocation is used by the probe.
