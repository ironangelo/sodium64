# A3 direct backdrop qualification

The general compositor repeats each real raster section in compact bands of up
to eight rows. A3 adds an exact specialization for black Main backdrop,
CGADSUB=0x20 and CGWSEL=0x02/0x12, with ordinary nonblank rendering. It renders
fixed color plus Sub into final Main, fills the prevented COLOR-window spans
with black, restores full section scissor/texture combiner, then draws opaque
Main layers. This removes compact Z/presence copies, software arithmetic and
artificial eight-row subdivision for that family. Main-only no-op sections also
retain their complete real bounds. Actual raster/palette epochs remain intact.

Other states retain A2's general compositor and aligned compact bases. Both
resident renderer banks and the arithmetic bank are byte-identical to A2.
Source retirement and complete DMEM command ownership barriers are retained.
The fast bank uses the same fixed 1000-byte 13A8..1790 slot and an audited source
pointer at DMEM F28, between immutable texture fence and proof command table.

Runtime commit: `0c82a77b1598b9d1f365f7644446c0f1055e6469`.
Qualified build commit: `4077278ce930c1eb7952b793e56f25e5dcbcd973`.
[Build/normal/native/profile/original smoke](https://github.com/ironangelo/sodium64/actions/runs/37077222372): PASS.
[Whole-frame original raster guests](https://github.com/ironangelo/sodium64/actions/runs/37077167184): PASS at `771577d`, with identical five RSP banks to the native deliverable.

`pixel-results.json` records 36 original cases and 2,064,384 checked viewport
pixels, zero mismatches, six intact compact guards per accepted frame, natural
fenced boundaries, no framebuffer seeding and no guest-state debugger writes.
Cases include the existing add/sub/half, BG/OBJ, blank/short, RGB mixed-channel,
layer windows and ordinary SRAM controls, plus nine direct backdrop/partial/
XOR/inverted/empty/singleton/absent Sub/short/raster-window guests. Downloaded
frame binaries were independently reclassified against the pixel oracle.

`test_hcomp_direct_backdrop.py` executes the compiled admission and black-span
routine, including the actual resident window helper, against independent
256-pixel truth. It also checks whole/general-section bounds. Results:
65,540 admission cases, 8,704 mask cases and 3,495 geometry cases.
Existing compiled alignment/consumer suite: 3,784 cases. RDP command/source
lifetime suite: 408 cases. Native runtime ends at BDF10; boot-clear arena starts
at C2000, leaving a disjoint gap of 0x40F0 bytes.

Run the compiled execution check from the repository root:

```sh
python3 docs/gate-c-a3/test_hcomp_direct_backdrop.py \
  build/src/rsp_main.elf build/src/rsp_hcomp.elf build/src/rsp_hcomp_fast.elf
```

This qualification establishes these original pixel semantics and boundaries,
not real-N64 throughput or all-game compatibility. Native A3 FPS, intro and
separate gameplay results remain pending. Prior A2 native footage/save passed
the formerly failing iris/reset point and showed sustained low FPS before and
after the iris, with dominant CPU RSP wait. The performance goal remains 60 FPS.
No commercial ROM, wrapper, save, video, extracted game memory or pixel asset is
included in repository or Actions; all automated guests are original fixtures.
Master is unchanged; no PR or merge is part of this qualification.
