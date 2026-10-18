# Production and laboratory builds

The downloadable rolling release is `sodium64.zip`. It contains exactly
`sodium64.z64` and `rom-converter.py`, produced by the normal build. The emulator
has no USB debugging menu, remote reset, image/audio capture commands or runtime
profiler. Those features are omitted at compilation, including their buffers
and interrupt/frame hooks; they are not hidden options consuming release space.

The source repository also retains reproducible development tools. Laboratory
builds are selected explicitly with `REMOTE=1`, `PROFILE=1` or `HW_PROFILE=1`.
The USB build uses its separate `build_usb_bench` directory and
`sodium64-usb-bench.z64` output. When switching other build flags locally, use a
fresh `BUILD_DIR` to avoid reusing objects from another configuration. Keep
laboratory executables outside release packaging.

The modified SummerCart menu belongs to the external laboratory setup. It is
not shipped in this project and is not required by the production emulator.

CI checks the unstripped normal ELF for diagnostic symbols and allocated
diagnostic leases, and checks the ROM's appended symbol text. Before publishing,
it repeats that admission check and creates a ZIP from the exact two normal
payloads. It validates the resulting ZIP before replacing the previous release.
Actual profiling builds must be rejected by the same checker; additional-file
and changed-payload cases exercise the package boundary. These checks enforce
the known diagnostic contracts and package contents, not gameplay fidelity.

The build pipeline can retain separate CI artifacts with ELF files, logs and
profiling builds for maintainers. Those artifacts are distinct from the public
Latest download. Keeping diagnostics in source does not link them into the
release ROM or reserve their memory there.
