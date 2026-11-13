"""Compare one synthetic workload at identical VI windows from cold boot."""
import argparse
import json
from pathlib import Path

from apu_cycle_proof import continue_to_breakpoint, read_u8
from gdb_rsp_dump import ARES_N64_GUEST_SIGNALS, connect_with_retry
from linked_cpu_regression import load_elf


WARMUP_WINDOWS = 5
MEASURED_WINDOWS = 12
SETTINGS = {"apu_clock": 21, "audio_set": 4, "skipped_set": 0, "precision_set": 8}


def measure(client, symbols):
    capabilities = client.request("qSupported:multiprocess+;swbreak+")
    assert b"swbreak+" in capabilities and b"QPassSignals+" in capabilities, capabilities
    assert client.request("?").startswith((b"S", b"T"))
    assert client.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}") == b"OK"

    windows = []
    for index in range(WARMUP_WINDOWS + MEASURED_WINDOWS):
        continue_to_breakpoint(client, symbols["update_fps"], f"60-VI boundary {index + 1}")
        assert read_u8(client, symbols["fps_native"]) == 59
        counts = {name: read_u8(client, symbols[name]) for name in SETTINGS}
        assert counts == SETTINGS, counts
        frames = read_u8(client, symbols["fps_emulate"])
        assert frames <= 65, frames
        windows.append(frames)
        # Advance beyond the same breakpoint before looking for the next VI window.
        continue_to_breakpoint(client, symbols["check_frame"], "completed VI update")
        assert read_u8(client, symbols["fps_display"]) == frames
        assert read_u8(client, symbols["fps_native"]) == 0
        assert read_u8(client, symbols["fps_emulate"]) == 0

    assert client.request("D") == b"OK"
    return {"settings": SETTINGS, "warmup_windows": windows[:WARMUP_WINDOWS],
            "measured_windows": windows[WARMUP_WINDOWS:]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--elf", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _, symbols = load_elf(args.elf)
    client = connect_with_retry("127.0.0.1", args.port, 45, 45)
    try:
        data = measure(client, symbols)
    finally:
        client.close()
    args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
