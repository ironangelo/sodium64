# Stage3 iris candidate

Stage3 fixes and qualification on `phase4/gate-c-stage3-iris`. This is a candidate for native N64 review; stage3 and Gate C remain open until the native image, audio/cadence and freeze observations are accepted. Master is unchanged.

## Native failure and follow-up repair

Iron reports substantial slowdown and a complete pre-iris freeze with the latest delivered candidate, including loss of menu response. The offered recording was unavailable to the upload system, so this is a user-reported failure: no exact FPS, frame timing, candidate/settings readback or frozen hardware state was independently extracted. The f24be2b host evidence below remains scoped to those controls and does not override failed native acceptance.

The CPU updates the menu only after `rsp_wait` observes RSP HALT. A persistent graphics wait can therefore prevent menu access; the report is consistent with that mechanism but does not identify the actual RSP PC.

The sender previously treated cleared DMA/pending-pointer bits as proof that the complete DMEM list had been read. It did not compare DPC_CURRENT with the submitted END. An asynchronous model with a DMA-idle gap made that compiled sender return after 15 instructions with zero bytes captured. This is protocol counterexample evidence, not captured real-N64 timing. The follow-up waits for both pending pointer latches to clear and CURRENT to reach END; repeated-END tests retain a stale previous CURRENT while the new START is pending. The preceding synchronous sender already retired its list, so the new sender does not additionally wait for the previous primitive's command-busy bit before every submission. SyncFull callers retain their explicit completion waits.

Generic DMA writes no longer retire the entire RDP when copying VRAM, cache statistics, Sub-presence strips or arithmetic outputs. The corresponding phases already own their destination dependencies. Decoded texture writes (TEXTURE == 0) retain the source fence, and historical raw-palette replay enters that same fence explicitly. Main and Mode7 keep identical resident helpers, the fixed suffix and the non-control delay slot at1F5C.

The expanded compiled protocol model passes288 command cases (continuous reads, transient DMA gaps and repeated-END pending START),24 texture cases,24 explicit palette cases and72 independent-DMA cases. These are ownership/serialization checks, not native FPS or freeze acceptance. The repaired ordinary build and complete-image/private progression qualification must be recorded before another candidate is delivered.

Primary command-FIFO description: [RSP Coprocessor0, Controlling the RDP](https://hcs64.com/files/RSPCOP0.pdf). Do not equate a transient DMA-idle sample with CURRENT == END.

## Runtime repairs

- Reset the BG span index after the shared window helper, which clobbers it through its final transition at 256. Preserve the renderer's fixed 242-instruction slot.
- Use exact inclusive scissor endpoints, including a singleton at255.
- Keep submitted DMEM command bytes owned until DPC DMA/end/start validity clears. Preserve the public 1F5C sender and the non-control delay slot used by dma_wait's return.
- Retire outstanding RDRAM texture readers with an immutable SyncFull before a DMA write can replace their source. Command fetch completion alone does not retire LoadBlock's texture source. The sender and DMA wrappers share resident helpers in retired prefix space without moving renderer/overlay entrypoints.
- Vectorize arithmetic over eight pixels, with separate five-bit channel saturation and HALF rules. Compute the selected window masks once per band; retain Main winner eligibility, low-OBJ suppression and absent-Sub/fixed-color behavior. Restore the decoder's empty v20 accumulator on return.
- Copy the Sub presence strip in up to 1024-byte transfers through TILE_TABLE after the Sub fence. Main BG and OBJ reload that cache before use; VRAM_TABLE at 0x440 remains untouched. For a 224-line frame of 8-line bands this copy drops from 3920 DMA submissions to 280; this is a transfer-count result, not an N64 FPS measurement.

The texture repair was motivated by an original Mode1 grid whose Sub palette changes between tile rows. The earlier ordinary build failed that complete-image oracle. A diagnostic resident-code patch with the retirement helper then passed 57,344 pixels and six arena guards. Only the final immutable CI build's unpatched qualification is acceptance evidence for the candidate.

## Accepted build evidence

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
