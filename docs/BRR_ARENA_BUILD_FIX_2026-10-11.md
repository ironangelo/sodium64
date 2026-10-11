# R25 - Actual CPU/RSP arena disagreement (2026-10-11)

## Reproduced fault and concrete binary cause

The exact combined R22 archive again loses USB after pause600 and step780,
this time leaving20 seconds without any USB queries. Status and return-to-menu
both time out. Firmware information still responds. A physical menu recovery
is required. This rejects frequent polling as the sole explanation.

Inspection of the actual linked binaries finds a build-order defect introduced
in R22. Make appends BRR_OBSERVER to N64_RSPASFLAGS, then assigns the base RSP
flags with '=' and discards it. CPU preprocessing selects0xD4000, but the Math
and fixed-window RSP banks retain backup0xA00D2400, not0xA00D4400.
Their actual1024-byte DMA writes reach0xD2400..0xD2800. Combined static memory
ends at0xD25C8, and request_buffer is at0xD2490: the DMA overlaps USB state.
This is a demonstrated binary overlap; the precise frozen instruction and
successful physical correction remain unobserved at this checkpoint.

R24's no-KOFF binary has the same incorrect RSP pointer. Its static memory
ends0xD15C8, below that old backup, explaining why that run can pass without
establishing the advertised unified CPU/RSP layout. Its unchanged RGB/PCM and
native decoder comparisons remain valid. Its earlier41-owner result checked
source-selected owners, not the missed compiled RSP writer. That qualification
is corrected explicitly rather than reusing a green source-only check.

## Fix and regression

Initialize N64_RSPASFLAGS before adding BRR_OBSERVER. A fresh separate build
now contains0xA00D4400 in all four backup/readback call sites. Only four loaded
bytes differ from the failed archive: the immediate byte24 changes to44 at
those sites. All CPU instructions and other allocated bytes, including sample
mixing, BRR and release, are identical.

check_brr_observer_arena.py reads six actual CPU queue words, validates their
source-selected owners, compares both RSP banks with their embedded CPU images,
and decodes all four actual DMA parameter constructions and lengths. Each
1024-byte owner must agree with the CPU and avoid every allocated ELF section.
It rejects the exact failed archive before installation. Three negative
mutations are rejected: CPU queue disagreement, stale RSP backup and embedded
bank disagreement. The optional audio CI job now runs this regression.

Fresh runtime/41-owner checks pass: end0xD25C8, arena0xD4000, gap0x1A38.
Release16384 cases/two mutations, actual sample/APU callers, delayed RDP/DMA
288/24/24/72 cases and1792 compiled windows/two mutations pass. The corrected
archive is147456 bytes, SHA256
18db14833af29d0c664ff43abe94cbd01b7f9cf828bda9c999ff84863357941a;
ELF78095cbe990ca747e75a08ff9107cd5f061d3d608359facadc22664fbefb4999.

[Curated proof](evidence/brr-arena-build-fix-2026-10-11.json) separates the exact
old binary failure from the corrected compiled guard. Native installation and
RGB/PCM/chunk comparison await responsive menu recovery. Last installed empty
template remains the failed combined archive
b28f6a602a1ee9632478c04c73196658fb9d497cba467369e3add3f3774cd6c1.
No restored-console, complete audio or60fps acceptance is claimed. Master
remains unchanged and PR21 draft. Raw commercial outputs/transport logs stay
private. The active goal is unchanged.
