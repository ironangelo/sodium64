# Stage3 iris candidate

Stage3 fixes and qualification on `phase4/gate-c-stage3-iris`. This is a candidate for native N64 review; stage3 and Gate C remain open until the native image, audio/cadence and freeze observations are accepted. Master is unchanged.

## Native failure and follow-up repair

Iron reports substantial slowdown and a complete pre-iris freeze with the latest delivered candidate, including loss of menu response. The re-uploaded55.608422-second recording confirms the selected f24be2b filename and BACK/MEDIUM/skip0/audioON/APU-underclockOFF settings. The initiallyOFF counter becomes visible afterward: readable samples show23 during Nintendo Presents,24 at16s,51 during title fade and21 from18s onward. The logo, wood/copyright appear, but no iris/demo stage appears through the end. These samples are not an average or a matched performance delta, and the21 left drawn on the frozen image does not mean continued21FPS execution. Menu nonresponse is additionally reported; the actual stopped native CPU/RSP/DP state remains unknown. The f24be2b host evidence below remains scoped to those controls and does not override failed native acceptance.

The CPU updates the menu only after `rsp_wait` observes RSP HALT. A persistent graphics wait can therefore prevent menu access; the report is consistent with that mechanism but does not identify the actual RSP PC.

The sender previously treated cleared DMA/pending-pointer bits as proof that the complete DMEM list had been read. It did not compare DPC_CURRENT with the submitted END. An asynchronous model with a DMA-idle gap made that compiled sender return after 15 instructions with zero bytes captured. This is protocol counterexample evidence, not captured real-N64 timing. The follow-up waits for both pending pointer latches to clear and CURRENT to reach END; repeated-END tests retain a stale previous CURRENT while the new START is pending. The preceding synchronous sender already retired its list, so the new sender does not additionally wait for the previous primitive's command-busy bit before every submission. SyncFull callers retain their explicit completion waits.

Generic DMA writes no longer retire the entire RDP when copying VRAM, cache statistics, Sub-presence strips or arithmetic outputs. The corresponding phases already own their destination dependencies. Decoded texture writes (TEXTURE == 0) retain the source fence, and historical raw-palette replay enters that same fence explicitly. Main and Mode7 keep identical resident helpers, the fixed suffix and the non-control delay slot at1F5C.

The prefix must also retain an inert instruction at2CC: the preceding CGRAM pair branch executes it as a delay slot. An undelivered draft0e9779f replaced that slot with DP_START and failed ordinary local boot;2b4e0de restores NOP and preserves the source-fence entry2FC by sharing the filter delay slot with its status read. This was a follow-up patch regression caught before delivery, separately from the native f24 failure. The compiled model now asserts that semantic delay-slot contract.

The expanded compiled protocol model passes288 command cases (continuous reads, transient DMA gaps and repeated-END pending START),24 texture cases,24 explicit palette cases and72 independent-DMA cases. These are ownership/serialization checks, not native FPS or freeze acceptance. The corrected ordinary runtime2b4e0de14306331a241c3f94ce00ff1244e8b3cb passed generic normal/profile/original-smoke run37043629848. Normal artifact11243756182 is an empty98,304-byte template, SHA25693d5db67ea38d752826052b31fed8e57e1e6655352bd43671a35ced7b24dde08. All four embedded RSP text images exactly match the locally checked4096/1000-byte binaries; delay slots, fixed ABI, 4MiB arena and absence of diagnostic/profile symbols pass. The final unpatched ordinary build passes all27 complete-image controls (1,548,288 pixels and six compact guards each), including row-palette cases. Read-only private game observation completed30 samples with all last15 frames distinct: title foreground is retained, iris reveals the stage and the demo progresses. A new private candidate is ready for native review; these checks do not establish native FPS/audio or freeze resolution.

Primary command-FIFO description: [RSP Coprocessor0, Controlling the RDP](https://hcs64.com/files/RSPCOP0.pdf). Do not equate a transient DMA-idle sample with CURRENT == END.

## Runtime repairs

- Reset the BG span index after the shared window helper, which clobbers it through its final transition at 256. Preserve the renderer's fixed 242-instruction slot.
- Use exact inclusive scissor endpoints, including a singleton at255.
- Keep submitted DMEM command bytes owned until pending START/END adoption and CURRENT==END. Preserve the public1F5C sender, the non-control delay slot used by dma_wait's return, and the inert CGRAM-branch delay slot at2CC. The original f24 DMA-bit-only wait is superseded by the follow-up above.
- Retire outstanding RDRAM texture readers with an immutable SyncFull before a DMA write can replace their source. Command fetch completion alone does not retire LoadBlock's texture source. The sender and DMA wrappers share resident helpers in retired prefix space without moving renderer/overlay entrypoints.
- Vectorize arithmetic over eight pixels, with separate five-bit channel saturation and HALF rules. Compute the selected window masks once per band; retain Main winner eligibility, low-OBJ suppression and absent-Sub/fixed-color behavior. Restore the decoder's empty v20 accumulator on return.
- Copy the Sub presence strip in up to 1024-byte transfers through TILE_TABLE after the Sub fence. Main BG and OBJ reload that cache before use; VRAM_TABLE at 0x440 remains untouched. For a 224-line frame of 8-line bands this copy drops from 3920 DMA submissions to 280; this is a transfer-count result, not an N64 FPS measurement.

The texture repair was motivated by an original Mode1 grid whose Sub palette changes between tile rows. The earlier ordinary build failed that complete-image oracle. A diagnostic resident-code patch with the retirement helper then passed 57,344 pixels and six arena guards. Only the final immutable CI build's unpatched qualification is acceptance evidence for the candidate.

## Prior local build evidence (native rejected)

Runtime commit: `f24be2b0de7469533ca948841cb5d15b6eebf14b`. Generic normal/profile build and original smoke run:36964998162, successful. The empty ordinary template is 98,304 bytes, SHA256 `38dc8252a6606181b4c7858a62cf0fed4cea43028f3302204c3fe34a5f0e0176`.

- 27 complete-image cases pass 1,548,288 pixels with six compact-arena guards each. The final unpatched row-palette cases pass too.
- 512 diagnostic arithmetic cases pass 1,048,576 pixels over 8 rows.
- Compiled delayed retirement models pass 96 command cases and 24 texture cases.
- All four local compiled RSP text images exactly match the final CPU ELF's embedded images. Their 4096/1000-byte sizes, fixed ABI, branch delay slots and 4 MiB arena constraints pass; the ordinary ELF has no diagnostic/profiling symbols.
- Private ordinary-game observation shows the foreground title and wood/copyright frame retained while the iris reveals the stage; the demo advances. Commercial images and metadata stay private. This is not native FPS/audio authority.

## Qualification boundaries

Complete-image fixtures exercise Main/Sub arithmetic, BG1..4 winner tags, layer/color windows, XOR, x255, short and force-blank sections, both OBJ math groups, SRAM import/save, and mixed RGB channel grids. Column palettes isolate arithmetic; row palettes also stress texture-cache source lifetime. They are generated original inputs and contain no commercial game assets.

The diagnostic arithmetic harness seeds original colors/tags, installs an inert CPU loop after a natural fence, and runs the compiled bank. Its pixels establish kernel semantics only. It is explicitly distinct from ordinary full-frame fixtures, which do not seed framebuffers or mutate guest state, and from private ordinary-game review.

A delayed-fetch model executes the compiled resident instructions against 96 command-retirement cases and 24 texture-reader cases. It checks ownership and ABI preservation; it does not establish native crash causality or cadence.

All commercial ROMs, wrappers, game dumps, captures and footage stay private and out of GitHub, Actions, public artifacts and hosting. Public CI produces an empty ordinary emulator template plus original synthetic controls only.

## Native review

Use the new ordinary candidate with Frame Precision MEDIUM (8), Frames Skipped 0, APU Underclock OFF and Audio ON. Turn the FPS counter ON when recording. Preserve the same settings on any comparison build.

Observe the logo and wood/copyright frame in front while the iris reveals the stage, then allow the title demo to advance. Record image order, any freeze, FPS behavior and audio continuity. Host elapsed time and synthetic pixels do not replace this check. Additional texture retirement can add waits while textures change; its cadence must be measured on the console.

The inherited hue/brightness, per-section palette replay, Mode0 native banks and Mode7 fidelity work outside the admitted SMW stage3 scope still require their own evidence.
