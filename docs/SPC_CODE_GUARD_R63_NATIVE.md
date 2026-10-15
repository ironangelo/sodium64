# R63 - native opcode-guard cost discriminator

Status: IMPLEMENTED paired artifacts/preflight; physical cost measurement pending.
This is a bounded cost experiment, not a full-DSP or Road-to-1.0 acceptance.

SPC_CODE_GUARD defaults1 within the default-off SPC_BUS_CLOCK experiment.
SPC_CODE_GUARD=0 suppresses only the next-opcode guard call and remains an
incorrect source-changing-code control. Four compiler NOPs retain the same
layout. The paired ELF files differ in exactly two CPU text words; all other
allocated sections,1623 shared symbol addresses and all12 linked RSP banks are
exact. Both variants retain runtime immediate/DBNZ fetching and KOFF repair.

Use fresh build_usb_spc_guard_on_r63_v2 / build_usb_spc_guard_off_r63_v2,
PROJ_NAME=s64-spc-gon / s64-spc-goff. Both use NATIVE_DIAG=1,
NATIVE_DIAG_TRACE=1 REMOTE=1 SIGNAL_PROFILE=1 WIDE_MATH=1 ELIGIBILITY_TAGS=1
MASK_SCAN=1 TLUT_SHADER=1 FULL_ROW_MATH=1 RDP_HALF_MATH=1 FIXED_WINDOW_MATH=1
RDP_FIXED_MATH=1 SECTION_OBSERVER=0 TMEM_ATLAS=1 TMEM_ATLAS_BITS=3
TMEM_COORD_ATLAS=1 SPC_BUS_CLOCK=1 DSP_KOFF_RELEASE=1; only SPC_CODE_GUARD differs.
Audio/BRR/mix observers and live full-DSP probes are off. Preserve full layers,
precision20, frameskip0, APU21 and audio4 in physical records.

The first SECTION_OBSERVER=1 attempt failed the existing static-arena assertion
by1480 bytes and was never used on COM3. Disabling that optional observation
code preserves rendering choices and fits the unchanged arena: allocated end
0xD15C8, limit0xD2000, gap2616 bytes. Runtime/event gates pass43 owners and194
ROM slots; the actual linked boot gate passes30 cases. Both native artifacts
pass six live-immediate producer and132 normal controls; the opcode case is
exact only with the guard, as intended. See the curated PREFLIGHT.json.

Planned physical test: normal paired menu/install/readback, identical private
ALttP boot route, retired image at guest/render600, then a quiet20-second USB
capture per variant. Compare only shared absolute completed-boundary IDs after
the initial partial interval, validate checksums/settings/no overflow, and keep
all ROMs/raw captures/images/derived hashes local. Completed-boundary cadence
is not presentation FPS. An intro route is only a first cost discriminator.
Always restore coordinate8/menu with verified install/readback. No game-data
artifact, merge, candidate promotion or fidelity/performance claim is implied.

Private plan/worker/run family: private/usb-bench/2026-10-13/
spc-code-guard-r63-native-plan.json, native_spc_code_guard_r63.py and
spc-code-guard-r63-native-v1/. The worker must pin this source, both ROM files,
the bench script and recovery artifact before taking COM3. No worker is armed
by this document; verify its actual process/exec handle before resuming a run.
