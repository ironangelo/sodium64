# R41 - Consistent AUDIO-only diagnostic storage

IMPLEMENTED/local integrity passed, physical regression pending. GCC16.2 CI
failed the matched corrected AUDIO1/BRR0/MIX0 reference at the D2000 link bound,
while native GCC14.2 fit D15C8. This is a diagnostic/compiler storage mismatch,
not a measured speed improvement. Normal profile and existing extended layouts
remain unchanged. AUDIO-only trace now uses the already audited D4000 arena.

Make propagates AUDIO_OBSERVER to both CPU/RSP assemblers and selects the D4000
link assertion. Macro/preprocessor/full-owner guards accept explicit audio
selection at the end of their existing API. Compiled guard reads the actual six
CPU queue words, two embedded banks and all four1024-byte backup/restore DMA
sites, then rejects CPU disagreement/stale RSP backup/embedded-bank mismatch.
No bound is removed; event cap24576 and194 ROM cache slots are preserved.

Local corrected/adaptive builds: endsD15C8/D1688 below D4000;41 owner extents
disjoint. Fourteen arena tests,576 decoder cases,448 span cases/four negative
guards,30 island cases/three faults, branch delays,1792 window cases/two faults,
command/source lifetime and boot12/TV5 pass. Initial host PATH lacked gcc in two
preprocessor fixtures; corrected environment passes14/14, failed log retained
privately. New full CI job keeps ordinary spans and additionally compiles the
adaptive candidate with the matching reference and explicit arena/embedded-DMA
gates. No full CI/native acceptance yet.

Next: immutable candidate short story1852 physical images/PCM/checksum/cadence
against prior corrected control and R40, menu restoration; then exact-source
Build/CGRAM/Ares workflows. Never substitute green CI for native performance
or paused PCM for complete synchronized audio. Prior D2000 artifacts/results
remain archived. No merge, game policy, new surfaces or ROM capacity reduction.
Commercial data/captures/replays/hashes stay local.
