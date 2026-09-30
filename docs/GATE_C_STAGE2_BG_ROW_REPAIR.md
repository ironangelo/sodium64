# Stage 2 regular-BG row repair

The delivered renderer reused t3 as a character/cache address, then read BGXSC
through it on the next tile row. A window byte could become a tilemap selector,
skip opaque Main tiles by priority, and expose the blue backdrop. The accepted
visual phase161 framebuffer contains exactly such a40-row hole at rows31..70.

Recover t3=s2>>1 at every draw_row. Reuse the recovered t3 for SHIFT_TABLE
before any tile/window helper clobbers it, replacing the previous second shift
into t2. Instruction count is unchanged. The compiled repair must preserve the
4096-byte image and fixed overlay entries; CPU text, other RSP images and DMEM
data must match the executed native-probe parent. Guest ROMs remain byte equal.

Qualification covers all216x256 active lower pixels, all256 window phases in
both original workloads, original static and motion controls, ownership guards,
and independent uninterrupted PI-save/profiler runs. Per-frame semantic reads
are not cadence measurements. Blue holes fail even if the upper band passes.

The new native files are sodium64-stage2-rowfix-visual.z64 and
sodium64-stage2-rowfix-mixed.z64. Run each separately on the same console/cart/TV,
wait for the solid red completion screen, flush SRAM normally and keep separate
32768-byte saves. Settings and stimulus match the prior tests: FS0, APU21,
audio4, precision8; visual silent, mixed eight sustained synthetic tones.

Native blue disappearance and upper hue are observations still needed. No
VI, RDP sender, color math, audio or event allocation repair is bundled here.
Upper green and general event arena overlap remain separate open work; Stage2
is not closed by a laboratory pass. The existing native snapshot samples only
the upper band and adjacent8rows, so it cannot itself certify lower-frame
presentation. A short view of the run can establish whether flashes persist.
