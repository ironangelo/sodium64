# Native freeze and cadence recorder

## Scope

The ordinary runtime2b4e0de also failed on Iron's N64. The37.657856-second recording identifies that filename and MEDIUM/skip0/audioON/APU-underclockOFF/BACK. Readable samples include14 early,24/25 during Nintendo Presents,54 at title fade and21 retained on the unchanging title. No iris/demo follows. Point readings and stale drawn counters are not an average or a measured matched delta. The actual blocked CPU/RSP/DP state is still unknown. Native failure overrides the earlier host progression qualification.

Use a separately named private wrapper built with `make NATIVE_DIAG=1` to capture the same unchanged game on the actual N64. It has its own timer and SRAM format and must not be combined with PROFILE/HW_PROFILE/COLOR_DIAG. Master and the ordinary stage3 renderer are unchanged. All four RSP images remain byte-identical to2b4; only CPU instrumentation changes.

## User flow

The diagnostic fixes BACK/MEDIUM8/skip0/audioON/APU-clock21/counterON before guest execution. The settings menu is disabled in this capture build, preventing deliberate menu pauses from triggering the watchdog. Use the unique diagnostic filename and its own32KiB SRAM save; do not reuse the filename or save slot of a gameplay ROM. Guest SRAM must be <=8KiB (the private supplied LoROM wrapper is verified2KiB). This build is not a general-purpose replacement for arbitrary guests with larger SRAM.

Boot it and wait without pressing buttons. When no completed frame is observed for approximately2 nominal Count-domain seconds after a frame has been submitted, or at the20-second capture limit, finalization deliberately stops the renderer and displays **CAPTURE SAVED** plus **FRAME STALL** or **TIME LIMIT**. This terminal screen is intentional. **SAVE FAILED** means PI completion/error checks failed and the save must not be accepted.

After CAPTURE SAVED, use the flashcart's normal reset/return-to-menu flow so its pending SRAM can be persisted to SD; do not power off first. Retrieve the32KiB save associated with the exact diagnostic filename (.sav/.sra/.ram extension and SD directory depend on the flashcart/menu). Send the save privately and a recording/photo of the terminal screen. If it never reaches a diagnostic screen, record that outcome and the wait duration; a CPU/interrupt/PI bus failure can prevent this transport from running.

## Evidence captured

A CP0 Compare interrupt samples CPU EPC roughly357times/nominal second. Its fast path touches only k0/k1. The20Hz slow path explicitly preserves at,t0..t9,ra and never touches HI/LO or the other live GPRs. The monotonic frame-completion/submission/section and VI counters let the host distinguish ongoing work from a stale FPS overlay. No RSP semaphore read is made: that would change ownership.

CPU samples retain the latest2048EPCs (approximately5.7seconds at the nominal cadence); a64-record20Hz ring retains approximately3.2seconds of RSP/DP status, START/END/CURRENT, DMA, band/screen and progress. Per-second records retain the complete capture's completion cadence, CPU RSP/frame waits/JIT/other buckets and sampled SP/DP occupancy. ISR body time and maximum latency are measured, so diagnostic FPS are explicitly distinguished from the ordinary build's throughput. Additional CPU hook/exception entry costs are not included in that ISR-body fraction.

At trigger, record CPU EPC/Cause/Status, live GPRs (reserved k0/k1 are not original), guest CPU PC raw,sound/VI/PI context and pre-stop SP/DP status/pointers. Request RSP HALT, wait with a bound, and read SP_PC only after HALT acknowledgement. Then freeze DP and copy resident DMEM/IMEM, marking whether SP DMA settled. Post-HALT PC is deliberately intrusive evidence: never report it as an earlier untouched active PC. Interpret it against the captured resident IMEM, including overlays, rather than assuming the Main bank is installed.

Terminal diagnostics never resume the renderer, clear a failing command queue, reuse an owned surface or silently turn a timeout into gameplay. RSP-HALT/SP-DMA/PI waits are bounded. Header is committed last after body transfers; the decoder rejects incomplete, inconsistent, corrupted or wrong saves.

The CPU RSP/VI waits also poll an independent Count deadline. This is necessary when they execute inside an outer TLB exception with EXL=1, which prevents Compare/VI interrupts from running. On this path the header records the direct wait-site PC separately from EPC and preserves the pre-stop Status: EPC/Cause can belong to the outer guest memory-access exception. A sparse timer sample history in that state is expected, not proof of low sampling-time CPU occupancy. The captured direct wait exceeded a two-second threshold; this alone does not prove that it would be infinite.

DP pipeline/TMEM bits can remain latched; occupancy percentages of these status bits are not exact independent active-time counters. CPU statistical occupancy also does not give precise per-function timing. The Count-domain rates assume the nominal46.875MHz clock; raw VI/Count progress remains available. Any save collected from a software emulator proves capture mechanics only, never N64 performance or the root cause of Iron's freeze.

Each20Hz telemetry record also has four raw24-bit DP clock/command/pipe/TMEM cycle counters. Reads never clear them. The host retains modulo24-bit deltas and flags gaps >=0.25s as ambiguous for multiple wraps; it does not infer exact independent frame costs from a latched status bit. Primary definitions: [RSP COP0, counters and CPU register view](https://hcs64.com/files/RSPCOP0.pdf).

## Save format S64D v1

All fields are canonical big-endian. The decoder accepts complete saves with bytes reversed per32-bit word or16-bit halfword.

| SRAM offsets | Contents |
| --- | --- |
|0000–1FFF|Preserved guest SRAM region|
|2000–21FF|Versioned S64D header, pre/post-stop registers, final partial occupancy window|
|2200–41FF|2048 CPU EPC ring entries|
|4200–51FF|64 telemetry records of64bytes|
|5200–61FF|Captured resident DMEM|
|6200–71FF|Captured resident IMEM|
|7200–76FF|Up to20 measurement records of64bytes|
|7800–7BFF|64 sidecar records of four24-bit DP cycle counters|
|7C00–7D0F|Interrupted CPU64-bit GPRs plus HI/LO; k0/k1 excluded from original-GPR validity|
|7E00–7FFF|CGRAM snapshot|

The header's sum32 covers the full body excluding2000–21FF. Complete=1 is written to cart only in the final header transfer. Format constants and field definitions are in `scripts/native_diag_report.py`.

```sh
python3 scripts/native_diag_report.py PRIVATE_CAPTURE.sav \
  --elf MATCHING_CPU.elf --map MATCHING_CPU.map \
  --json-output PRIVATE_REPORT.json --extract-private PRIVATE_DUMPS
```

The decoder can read the CPU ELF without an installed MIPS toolchain. Keep the exact ELF/map and empty template hashes with the private wrapper manifest. ELF/map and empty templates contain emulator source only and may be public; **game wrappers, saves, dumps, footage and derived captures must remain private and outside GitHub/Actions/public artifacts/hosting**.

## Diagnosis decision

- CPU RSP-wait samples plus a stopped resident RSP instruction identify the wait family. Compare pre-stop DP CURRENT/END and pending/busy bits with that instruction; use captured IMEM/DMEM to establish the installed bank and command bytes.
- Completed frames continue slowly: inspect per-second CPU/RSP occupancy, retained EPC symbols, section counts and hardware telemetry. Optimize the observed dominant path, then repeat an ordinary matched-settings native measurement.
- No terminal diagnostic: this recorder did not establish the blocked state. Do not invent a PC or treat a stale save/counter as current evidence; escalate to a different capture transport/watchdog context if needed.

A generic SMW decompilation is optional reference for later guest-behavior questions. It cannot reveal which wait is stuck in this emulator on Iron's hardware. Capturing the actual failing wrapper first gives a concrete instruction/register basis for subsequent changes.
