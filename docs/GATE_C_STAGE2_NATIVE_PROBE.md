# Stage 2 native pixel and PCM probe

Purpose: distinguish the unresolved real-N64 green/yellow band from computed
pixels versus presentation, and inspect generated PCM plus AI state. The
candidate includes the confirmed HW_PROFILE arena-collision repair. It does
not claim the green band, blue flashes or audible-output issue fixed.

Run `sodium64-stage2-visual.z64` and `sodium64-stage2-mixed.z64` separately on
the same NTSC N64/cart/TV used for the original tests. No menu settings are
needed: frameskip 0, APU 21, audio 4, precision 8 are forced. Both run two
warmup windows and five measured 60-VI windows, then save and turn solid red.
Wait for solid red before leaving. Use the cart's ordinary SRAM flush/menu
procedure and retain a separate raw 32768-byte save per ROM. Keep the old
Stage 1 saves/videos as separate evidence. A phone video/audio of the run
provides presentation context; the new saves carry the native snapshot.

Expected reference: thin yellow/black band with moving/resizing black window;
visual is silent, mixed produces synthetic sustained tones, not music/SFX.
Blue flashes are not a programmed animation. The red completion screen is
intentional. Correct reference appearance remains a hardware question.

S64H and S64P are unchanged at 0 and 0x100. S64V v1 occupies SRAM
0x4200..0x7F0F (size 0x3D10). It is captured only after all measured windows,
using existing local SRAM storage with uncached writes. No new renderer
surface, per-frame instrumentation, color arithmetic or audio-runtime change.
Current SP/RDP work drains naturally, bounded by 9,375,000 Count ticks;
timeout invalidates the snapshot without hiding the original profiler capture.

The 128-byte header names validity, SP/DP/VI registers, PCM next-write offset,
enabled voices, AI context, interrupted EPC, guest and queue counters, and
fixed-buffer addresses. Payload relative to S64V:

| Offset | Bytes | Content |
| --- | ---: | --- |
| 0x0080 | 8192 | VI-selected columns12..267, physical rows8..23 |
| 0x2080 | 1536 | First band row from each of the three framebuffers |
| 0x2680 | 512 | First Main winner row |
| 0x2880 | 512 | First preserved TS winner row |
| 0x2A80 | 512 | First raw Sub row |
| 0x2C80 | 16 | Existing consumed-section record |
| 0x2C90 | 128 | DSP registers |
| 0x2D10 | 4096 | Previous1024 chronological stereo PCM sample frames |

Decode with `python3 scripts/decode_stage2_probe.py SAVE --output DIRECTORY`.
The decoder checks capture integrity independently of yellow-reference
fidelity, preserves green pixels as useful diagnostic data, and writes JSON,
PNG and a nominal32000Hz WAV. Latest renderer tags may refer to a newer frame
than the VI-selected buffer. AI readbacks are diagnostic context, not audible
output authority. A single final snapshot cannot prove intermittent-flash
cadence, per-frame presentation or all-game correctness/performance.

Before delivery, qualification must show unchanged normal runtime text and
RSP binaries, disjoint normal/HW_PROFILE allocation, branch-delay checks, and
continuous pinned-ares execution through actual PI cart writes. Independently
read cart SRAM and compare with transfer-source bytes and the surviving
graphics/DSP sources, then decode both workloads. Native Stage 2 remains open
until returned hardware evidence resolves the fidelity questions.

First-hand qualification: run36716662088 at47398d7016d98058c9841b319ee90e28953319f5
completed both continuous runs through PI SRAM writes. Both captures have
valid7, naturally halted SP/drained DP, yellow/black band and60/60x5.
Cart/source/context/PCM byte equality passed before an incorrect final mixed
oracle required unequal channels. This is REJECTED: the original driver uses
left=right=16 for every voice, and its established motion checker requires
equal channels. Corrected host replay pins the exact executed ROMs and ELF,
verifies original eight voice settings, equal channels, nonzero bipolar
varied PCM, and corruption negatives. No runtime or guest repair was needed.
This replay is not a new emulator/hardware measurement.

LAB LIMITATION: initial pinned-ares AI address/DAC/bitrate raw readbacks
duplicate AI_LENGTH. Treat those raw fields as diagnostic observations, not
configuration proof or meaningful sample-rate values. Readable AI status,
length, stored PCM and the known initialization remain separate evidence.
