# Host USB session lifecycle

The bench client closes sc64deployer stdin to request EOF, then waits for the
debug loop to exit. sc64deployer2.20.2 ignores blank input lines; a blank line
does not request shutdown. The previous client waited three seconds after that
ignored line and could force-kill an otherwise cooperative process.

The primary implementation is sc64deployer2.20.2, `sw/deployer/src/debug.rs`
(`Handler::process_user_input`) and `sw/deployer/src/main.rs` (debug-loop EOF).
EOF closes the host process; the client does not send another console packet or
automatically return an emulator to the menu. Callers still own explicit menu
return and verified habitual restoration. Unresponsive processes retain the
bounded timeout/kill/reap fallback.

Two real-pipe regressions model that deployed input contract: a cooperative
worker exits0 on EOF after exactly one requested command; an uncooperative
worker still gets reaped after the bounded wait. Both reject the old client.
All19 host transport tests pass on Windows. No USB device is involved in those
tests. Emulator sources, flags, linker owners and production payload are unchanged.

The native profiler's terminal red screen still requires recovery; this host
fix does not add an autonomous terminal reboot. The previously qualified
pause/capture/resume/menu bridge remains the normal autonomous route. Restore
that route before further broad physical validation, keeping diagnostics out
of the normal release.

Windows USB removal near the last profiler worker's close is retained as an
observation, not proof of causality. This lifecycle correction does not by
itself qualify a fix for `No SC64 devices found`, native startup or fidelity.
