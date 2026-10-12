# R41 - Ares dependency failure and reproducible SDL fix

LAB LIMITATION: Ares38300934335/profile build passed, ares-smoke114983870325
failed while compiling SDL, before any Sodium64 execution. The pinned ares
helper cloned mutable SDL main; KMSDRM used a pointer operator on a struct
member at SDL_kmsdrmopengles.c:480. Build38300923921 and CGRAM38300930969 passed
the actual d10b79f Sodium64 source, including GCC16 adaptive/arena gates.

SDL upstream fixed this exact member access in
[d399b610](https://github.com/libsdl-org/SDL/commit/d399b610ecc68632ae44c0e4874715ca549693aa).
IMPLEMENTED: assert and patch the pinned ares helper's single clone line to
check out that exact SDL revision. Ares17813a3, R4300 JIT/RSP interpreter,
profiling workloads, assertions and runtime matrix remain unchanged. No
driver or runtime check disabled; no emulator performance substituted for N64.
SDL source revision now survives the session and future upstream changes.

This branch changes workflow/docs only relative to d10b79f. Retry the Ares
workflow alone on the fixed revision; retain successful Build/CGRAM evidence
at d10b79f rather than rerunning unrelated suites. Do not label the failed
original run as PASS. The full native60/audio/corpus goal remains open.
