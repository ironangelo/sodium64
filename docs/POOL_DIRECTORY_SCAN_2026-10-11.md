# R26 - One read-only filename scan per launch (2026-10-11)

Repeated native launches now take203.703 and209.703 seconds in the two latest
trials. The first pool reservation still starts at ID1 and attempts exclusive
creation at every old filename. A shared cursor already avoided repeating the
same search for all16 slots, but the first search grows with every launch.
This is observed latency plus a concrete algorithmic cost, not a timed claim
that reservation probing accounts for the entire delay.

The reservation helper now scans its parent directory once, reads only exact
stem/tag/six-digit .sav names and seeds one above the highest matching ID.
The pool shares that seed. Every actual file creation retains FA_CREATE_NEW,
so a new collision after scanning is skipped and preserved. ASCII case is
ignored; non-ASCII case differences retain the exclusive-open fallback. Files
with different stems/tags/extensions, malformed widths/digits and directories
cannot seed the cursor. Matching999999 and directory open/read/close failures
reject launch. Failure leaves the caller's cursor unchanged. No existing file
is modified or deleted; ordinary SRAM input remains read-only. No RTC/index
file, descriptor change, sector-map relaxation or game-state change is added.

The real C helper runs against a filesystem failure shim.26 previous pool
cases still pass.96 existing captures plus16 new slots now need one directory
scan and16 exclusive-create calls, compared with112 before the change.
Exact-name noise, mixed ASCII case, exhaustion, invalid arguments, all three
scan I/O failures, and a real creation race preserving the four-byte competing
file pass. The main GitHub host-validation job runs this same regression with
ASan/UBSan on Linux; local Windows GCC lacks those sanitizers, and no fresh CI
result is asserted here.

The paired pinned menu builds successfully with the existing FatFsR0.16/SDK.
All8 compiled filesystem consumers reference byte-identical library-source
headers; original DFS assets match the known working menu exactly. USB menu
52 synthetic host checks and16 asset regressions pass. Archive1736704 bytes,
SHA2561e5fd76febfe2405fbea0f855dad63514960502631af1a1cd081d1f907c2c6f5.
This is a new code candidate, not the last installed menu. Firmware is unchanged.

[Curated proof](evidence/pool-directory-scan-2026-10-11.json) excludes private
paths, ROMs, file contents and captures. Native installation, next-boot menu
response, capture persistence and actual launch-time comparison await manual
menu recovery from the R25 interruption. The corrected observer also awaits
that recovery. The active constant60/visual/audio/game-matrix goal remains open.
