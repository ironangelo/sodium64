# S3 state envelope integrity layer

IMPLEMENTED host/unit layer only. `scene_state_format.c/.h` are not linked into
gameplay or the frozen S2 artifact. No complete serializer, slot, import or
machine restore exists yet. S2 context reconstruction is REJECTED by Mode7;
this decoder cannot make incomplete state restorable.

Private S64S/version1 envelope uses explicit big-endian fields,64-byte header,
up to32 logical owners and a4MiB total bound. ROM/code/layout/configuration
CRC bindings must match. Guest/render progress must agree; reserved words
must be zero. Current-build whitelist fixes each unique ID/size/ordered payload
offset; file addresses are never accepted. Header and complete descriptor/
payload CRC32 are checked before publishing decoded progress. Read errors are
distinct from invalid/incompatible data. There is no RAM commit operation.

Corrected tests execute production C against an independent Python struct/
zlib oracle:1209 cases, all payload-byte corruptions, header changes, changed
bindings, recomputed-checksum descriptor mutations, duplicate/oversize/empty
owners, truncated/extra bytes and every read-error position. Output progress
remains untouched after every rejection. Native O64 compilation passes.
The initial fixture mishandled bytearray in a ctypes callback and could produce
false-positive rejection tests; that receipt is INVALID_HARNESS and retained
privately. Corrected callbacks convert bytes and fail on any callback exception.
[Format evidence](evidence/scene-state-s3-format.json).

Next close live CPU/RSP/guest-memory/mapper/JIT/input/host-clock ownership,
then implement a private same-build slot with complete prevalidation and
transactional restore/readback. Full replay and next1/60/600 remain gates;
cross-build reuse and persistent transfer follow only after a real restore
works. Full native cadence, complete audio, corpus and master remain open.
