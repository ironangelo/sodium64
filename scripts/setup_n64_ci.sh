#!/usr/bin/env bash
# Reproducible assembly-build SDK, independent of the unavailable GHCR image.
set -euo pipefail

sdk_work="${RUNNER_TEMP:?}/sodium64-sdk"
mkdir -p "$sdk_work"
package="$sdk_work/toolchain.deb"
curl --fail --location --retry 3 \
  https://github.com/DragonMinded/libdragon/releases/download/toolchain-continuous-prerelease/gcc-toolchain-mips64-amd64.deb \
  --output "$package"
printf '%s  %s\n' fac8e6572493a66468b7d45df41b042f90b1a630ec96aa218bd5fb1f320a0a4d "$package" | sha256sum --check
dpkg-deb --extract "$package" "$sdk_work/package"
compiler=$(find "$sdk_work/package" -type f -name mips64-elf-gcc)
test -n "$compiler" && test "$(printf '%s\n' "$compiler" | wc -l)" -eq 1
export N64_INST="$(dirname "$(dirname "$compiler")")"
export PATH="$N64_INST/bin:$PATH"

sdk_source="$sdk_work/libdragon"
git init "$sdk_source"
git -C "$sdk_source" remote add origin https://github.com/DragonMinded/libdragon.git
git -C "$sdk_source" fetch --depth=1 origin e356bf3f56f7afbf7e5246329562f145965cfdfc
git -C "$sdk_source" checkout --detach FETCH_HEAD
test "$(git -C "$sdk_source" rev-parse HEAD)" = e356bf3f56f7afbf7e5246329562f145965cfdfc

# Sodium64 links its own assembly runtime; only the ROM tools, RSP definitions
# and linker scripts are needed. Do not build a different runtime library.
make -C "$sdk_source" install-mk
mkdir -p "$N64_INST/mips64-elf/lib" "$N64_INST/mips64-elf/include"
cp "$sdk_source/n64.ld" "$sdk_source/rsp.ld" "$N64_INST/mips64-elf/lib/"
cp "$sdk_source/include/rsp.inc" "$N64_INST/mips64-elf/include/"
make -C "$sdk_source/tools" -j2 n64tool-install n64sym-install n64elfcompress-install ed64romconfig-install
printf 'N64_INST=%s\n' "$N64_INST" >> "$GITHUB_ENV"
printf '%s\n' "$N64_INST/bin" >> "$GITHUB_PATH"
mips64-elf-gcc --version
