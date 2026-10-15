# Clean-master integration: APU lookup reset

This extracts the complete unrolled invalidation from f4e061c6, without its PPU
section changes or the later live-group cache in ca3f6f59. Every one of the
65,536 lookup pointers is still cleared, including stale entries. The JIT buffer
pointer reset, tag validation, source limits and guest-cycle budget are unchanged.
There are no new owners, execution modes or runtime diagnostics.

The linked test fills all 262,144 lookup bytes and adjacent live metadata with
nonzero sentinels, executes the emitted reset through the branch delay slot,
and requires exact one-time coverage, pointer reset and preservation of other
owners/registers/HI/LO/CP0. Three emitted-code mutations omit each of two stores
or skip alternate batches; all must reject. Normal and PROFILE builds run this
gate in CI. The existing APU cycle/span proof remains required for integration.

The clear uses 4,096 branches instead of 65,536. Linked instruction counts are
a structural cost result, not measured N64 cycles or a game FPS improvement.
Combined performance and image/audio acceptance belong to a separately measured
integration baseline. The later live-group optimization remains pending its own
publication/reset proof on clean master.

Rollback: revert this PR; it introduces no persistent state or format change.

The first repaired-SDK cycle-proof run38764141249 failed before any SPC case:
its historical Gothicvania build artifact had expired. The proof now boots the
repository's original deterministic gameplay-balanced ROM, then takes over APU
state exactly as before. All119 directed cases, halted groups, expected values,
cycle/tag/span/cache contracts and required assertions remain unchanged. This
does not substitute a synthetic workload for the historical Gothicvania native
performance gate; it removes an irrelevant expiring boot-asset dependency from
the directed processor proof. The generated fixture hash is retained in CI.
