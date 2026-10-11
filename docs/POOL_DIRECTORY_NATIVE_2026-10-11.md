# R28 - Native directory-scan menu and repeated SD captures (2026-10-11)

The new menu installs while the N64 is on, with length/CRC/readback verified.
The existing SD menu is renamed to a unique .previous.requestID and its file
listing is checked before rebooting. This retains the original SD object;
its full contents were not downloaded to the host. An initial host preflight
had incorrectly assumed an older asset-reference binary was the latest menu.
Its hash check rejected that assumption before any write. The transaction's
retained original SD file is the actual rollback copy.

The existing homebrew fixture launches, then coordinate8 returns by USB to
boot the new SD menu without physical Reset. COM3 hello confirms menu/recovery0.
The same ALttP launch now receives its menu receipt in31.922 seconds, versus
the preceding203.703/209.703-second launches. This is one new timing sample
at the current accumulated directory size, not a universal cold-boot or FPS
speedup. It is an approximately84.3-84.8 percent latency reduction.

The acknowledged600/1380/1980 replay preserves67200 retired RGB pixels with
zero differences. Two USB-triggered SD captures run20 seconds each in the
same game session. Each returns recorder_result1, phase0, sealed_ready1 and
a distinct sealed_id1/2, then pauses and exports a full32768-byte snapshot.
Both v5 files parse with valid signature/layout and payload checksum, full
trace and zero overflow. The emulator's successful SD commit includes its
sector readback gate. This qualifies that route; no direct PC SD access while
powered on is used. File contents were not independently downloaded through
a menu filesystem command, and physical Start/visible OK acceptance is not
inferred from this USB trigger.

The first native save completed before a host-analysis error. The script
misread parse's return shape: it returns(result dictionary,normalized bytes),
with the header inside result['header']. Tuple/key repair attempts failed
before touching the console again. The first snapshot was decoded from its
existing private file; the same acknowledged pause was verified and the
second capture resumed from it. No duplicate first capture/ROM launch/Reset
was used. The reusable helper is repaired. The format has a payload checksum,
not a separate header checksum; the initial overly broad field is corrected.

Gameplay resumes after both captures; the final USB return to the new menu
succeeds. Installed menu1736704B SHA256
1e5fd76febfe2405fbea0f855dad63514960502631af1a1cd081d1f907c2c6f5.
Coordinate8 remains the selected emulator, with verified earlier readback;
firmware2.20.2 is unchanged. The prior menu stays on SD under its unique name.

[Curated evidence](evidence/pool-directory-native-2026-10-11.json) contains
counts, code identity and timing only. All commercial saves/images, their
contents/hashes, parsed register/PC/frame data and transport logs stay private.
This change accelerates iteration and preserves repeated capture function;
it does not establish full audio, final video or constant60 for the game matrix.
The full active goal and ALttP priority remain. Master stays unchanged/PR21 draft.
