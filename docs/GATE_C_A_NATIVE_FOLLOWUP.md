Independent A follow-up, 2026-10-02

Native A (3b2536d) failed at 326 completed frames, exactly as the earlier
diagnostic capture did. The valid save and exact resident/Main IMEM confirm
the tested runtime. LoadSync is present. The LoadSync-only repair is therefore
insufficient; no native fix or 60 FPS claim is established.

CPU waits for RSP; RSP is in rdp_fetch_wait; RDP remains at CA8 with END CD0,
status 161, no SP DMA in flight. Captured band is y=125, rows=1, Main/general
HCOMP. CURRENT marks the fetch blockage, not necessarily its initiating
primitive. A command-history trace would be required to distinguish an earlier
pipeline error from the command at CURRENT.

Independent libdragon validator e356bf3f56f7afbf7e5246329562f145965cfdfc reports
64-byte alignment errors for compact Z and derived Sub color bases at this Y.
The selected reconstructed state has no validator CRASH diagnostic. This is
state reconstruction, not a replay of the real immutable command history.
Some Nintendo manual editions state 64-bit rather than 64-byte alignment;
do not equate this validator error with proven native deadlock causality.

This A2 candidate only aligns compact image bases and moves all associated
pixel readers to the matching per-band origins. Global draw/scissor coordinates,
Main framebuffer, color math, source fencing, settings and guest are unchanged.
It derives directly from A, excludes FAST1/B and retains all fixed overlay
entries. Original compiled regressions cover every admitted Y, short bands,
both queue indices, presence copy and arithmetic input addresses.

Native low cadence is separately established: about 24-25 completed FPS during
seconds 3-7, CPU RSP wait 75.8-87.8%, SP running 99.7-100%, DP command busy
12.5-15.3%. These samples identify a rendering-side wait; they do not quantify
which RSP subroutine is most expensive. General HCOMP traverses both screens,
copies presence and performs software color math even in virtual 8-row bands.

B remains paused. Alignment correction remains a candidate until a fresh real
console capture passes the previous stopping point. If failure is unchanged,
instrument immutable submission history and narrowly localize attribute/target
transitions, rather than treating CURRENT as the offending instruction.

Keep all commercial ROMs, wrappers, saves, footage and extracted contexts
private. Public CI receives only emulator source and original generated tests.
Do not move master or create a PR/merge for this candidate.

Compiled qualification: immutable runtime 93cf51ba5da0305b0d8308b7950bef1404a1fa1a, run37073139943 SUCCESS (normal/profile/native/original Mupen LLE smoke; master release skipped). Native artifact11256196473. Address regression PASS3784 original instruction-executed cases; command/source lifetime PASS408. Expanded compact allocation reserves the preceding 64-byte line; the complete-image observer moves its lower 64-byte guard outside that allocation without relaxing pixel comparisons. Native freeze/FPS acceptance remains pending.
