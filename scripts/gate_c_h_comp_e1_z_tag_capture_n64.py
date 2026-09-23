#!/usr/bin/env python3
"""Capture/classify Gate-C E4b corrected same-band ownership proof."""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gdb_rsp_dump import (  # noqa: E402
    ARES_N64_GUEST_SIGNALS,
    RSPClient,
    connect_with_retry,
    validate_stop,
)

FB_WIDTH = 280
FB_HEIGHT = 240
FB_BYTES = FB_WIDTH * FB_HEIGHT * 2

Z_COMMAND_ADDR = 0xA00BEE80
Z_BASE = 0xA00C0000
Z_SIZE = FB_BYTES
Z_PREFIX_SIZE = Z_BASE - Z_COMMAND_ADDR
Z_SUFFIX_SIZE = 64
STATUS_ADDR = 0xA00E1000
STATUS_MARKER = 0xE1F00D01
STATUS_SIZE = 8
SP_STATUS_ADDR = 0xA4040010
DP_STATUS_ADDR = 0xA410000C

SECTION_QUEUE1_ADDR = 0xA016C600
SECTION_QUEUE2_ADDR = 0xA0171600
SECTION_RECORD_SIZE = 0x40
SECTION_RECORD_COUNT = 16
SECTION_CAPTURE_SIZE = SECTION_RECORD_SIZE * SECTION_RECORD_COUNT
SECTION_BGNBA_OFFSET = 0x10
SECTION_BG1SC_OFFSET = 0x2A
SECTION_WH0_OFFSET = 0x2E
SECTION_TS_OFFSET = 0x39
SECTION_TM_OFFSET = 0x3A
SECTION_BG_MODE_OFFSET = 0x3D
SECTION_STAT_FLAGS_OFFSET = 0x3E
SECTION_SPLIT_LINE_OFFSET = 0x3F

PREFIX_BYTE = 0xC3
SENTINEL_WORD = 0x55AA
SUFFIX_BYTE = 0x3C
BACKDROP_TAG_WORD = 0x0400
BG1_TAG_WORD = 0x0C00
BG2_TAG_WORD = 0x1400
BOOL_FALSE_TAG_WORD = 0x0400
BOOL_TRUE_TAG_WORD = 0x0C00
BG1_BLACK_RGBA5551 = 0x0001
BG2_GREEN_RGBA5551 = 0x07C1
E2B_MAIN_RED_RGBA5551 = 0xF801
E2B_MAIN_ROW0 = 8
E2B_MAIN_ROW1 = 16
E2D_MAIN_ROW1 = 24
E2D_SUFFIX_INTACT_BYTES = 24
E2F_BACKDROP_BLUE_RGBA5551 = 0x003F
E3A_ADD_YELLOW_RGBA5551 = 0xFFC1
E3B_DIM_BLUE_RGBA5551 = 0x001F
E3B_DIM_RED_RGBA5551 = 0x7801
E4B_DIM_YELLOW_RGBA5551 = 0x7BC1
E3B_PREBRIGHT_RED_RGBA5551 = 0xF001
E2F_MAIN_SENTINEL_WORD = 0x294B
E2F_FRAMEBUFFER_ADDRS = (0xA00F2300, 0xA0113000, 0xA0133D00)
E2F_MAIN_BAND_OFFSET = E2B_MAIN_ROW0 * FB_WIDTH * 2
E2F_MAIN_BAND_BYTES = (E2D_MAIN_ROW1 - E2B_MAIN_ROW0) * FB_WIDTH * 2
E4B_MAIN_PREFIX_BYTES = E2B_MAIN_ROW0 * FB_WIDTH * 2

E1C_Z_SCRATCH_ADDR = 0xA00C0000
E1C_Z_SCRATCH_SIZE = 0x1180
E1C_ARCHIVE_A_ADDR = 0xA00C2000
E1C_PREFIX_GUARD_ADDR = 0xA00BFFC0
E1C_SUFFIX_GUARD_ADDR = 0xA00C1180
E1C_GUARD_SIZE = 64
E2G_SECOND_Z_ADDR = E1C_ARCHIVE_A_ADDR
E2G_SECOND_Z_PREFIX_ADDR = 0xA00C1FC0
E2G_SECOND_Z_SUFFIX_ADDR = 0xA00C3180
E2G_SECOND_Z_PREFIX_BYTE = 0xD6
E2G_SECOND_Z_SUFFIX_BYTE = 0x6D
E1C_ROWS = 8
E1C_ACTIVE_X0 = 12
E1C_ACTIVE_X1 = 268

E2A_COLOR_SCRATCH_ADDR = 0xA00E4000
E2A_COLOR_SCRATCH_SIZE = 0x1180
E2A_COLOR_ARCHIVE_A_ADDR = 0xA00E6000
E2A_COLOR_PREFIX_GUARD_ADDR = 0xA00E3FC0
E2A_COLOR_SUFFIX_GUARD_ADDR = 0xA00E5180
E2A_MAIN_BEFORE_ADDR = 0xA00E8000
E2A_MAIN_AFTER_ADDR = 0xA00EA000
E2A_COLOR_A_WORD = BG1_BLACK_RGBA5551
E2A_COLOR_B_WORD = BG2_GREEN_RGBA5551
E2A_MAIN_BEFORE_INIT = 0xA6
E2A_MAIN_AFTER_INIT = 0x5B
E2A_ARCHIVE_INIT = 0xCC


def parse_int(text: str) -> int:
    return int(text, 0)


def read_u(client: RSPClient, address: int, size: int) -> int:
    return int.from_bytes(client.read_memory(address, size, size), "big")


def write_pattern(client: RSPClient, address: int, data: bytes, chunk: int = 0x400) -> None:
    for offset in range(0, len(data), chunk):
        client.write_memory(address + offset, data[offset:offset + chunk])


def initialize_proof_memory(client: RSPClient) -> None:
    write_pattern(client, Z_COMMAND_ADDR, bytes([PREFIX_BYTE]) * Z_PREFIX_SIZE)
    write_pattern(client, Z_BASE, SENTINEL_WORD.to_bytes(2, "big") * (Z_SIZE // 2))
    write_pattern(client, Z_BASE + Z_SIZE, bytes([SUFFIX_BYTE]) * Z_SUFFIX_SIZE)
    client.write_memory(STATUS_ADDR, bytes(STATUS_SIZE))

    assert client.read_memory(Z_COMMAND_ADDR, Z_PREFIX_SIZE, 0x400) == bytes([PREFIX_BYTE]) * Z_PREFIX_SIZE
    assert client.read_memory(Z_BASE, Z_SIZE, 0x400) == SENTINEL_WORD.to_bytes(2, "big") * (Z_SIZE // 2)
    assert client.read_memory(Z_BASE + Z_SIZE, Z_SUFFIX_SIZE, 0x100) == bytes([SUFFIX_BYTE]) * Z_SUFFIX_SIZE
    assert client.read_memory(STATUS_ADDR, STATUS_SIZE, STATUS_SIZE) == bytes(STATUS_SIZE)

    # E2g baseline: reserve the old E1c archive region as a deterministic
    # second screen-specific Z candidate. Current runtime must leave it untouched.
    second_z_prefix = bytes([E2G_SECOND_Z_PREFIX_BYTE]) * E1C_GUARD_SIZE
    second_z_data = SENTINEL_WORD.to_bytes(2, "big") * (E1C_Z_SCRATCH_SIZE // 2)
    second_z_suffix = bytes([E2G_SECOND_Z_SUFFIX_BYTE]) * E1C_GUARD_SIZE
    write_pattern(client, E2G_SECOND_Z_PREFIX_ADDR, second_z_prefix)
    write_pattern(client, E2G_SECOND_Z_ADDR, second_z_data)
    write_pattern(client, E2G_SECOND_Z_SUFFIX_ADDR, second_z_suffix)
    assert client.read_memory(E2G_SECOND_Z_PREFIX_ADDR, E1C_GUARD_SIZE, 0x100) == second_z_prefix
    assert client.read_memory(E2G_SECOND_Z_ADDR, E1C_Z_SCRATCH_SIZE, 0x400) == second_z_data
    assert client.read_memory(E2G_SECOND_Z_SUFFIX_ADDR, E1C_GUARD_SIZE, 0x100) == second_z_suffix

    color_prefix = bytes([PREFIX_BYTE]) * E1C_GUARD_SIZE
    color_scratch = SENTINEL_WORD.to_bytes(2, "big") * (E2A_COLOR_SCRATCH_SIZE // 2)
    color_suffix = bytes([SUFFIX_BYTE]) * E1C_GUARD_SIZE
    color_archive = bytes([E2A_ARCHIVE_INIT]) * E2A_COLOR_SCRATCH_SIZE
    main_before = bytes([E2A_MAIN_BEFORE_INIT]) * E2A_COLOR_SCRATCH_SIZE
    main_after = bytes([E2A_MAIN_AFTER_INIT]) * E2A_COLOR_SCRATCH_SIZE
    write_pattern(client, E2A_COLOR_PREFIX_GUARD_ADDR, color_prefix)
    write_pattern(client, E2A_COLOR_SCRATCH_ADDR, color_scratch)
    write_pattern(client, E2A_COLOR_SUFFIX_GUARD_ADDR, color_suffix)
    write_pattern(client, E2A_COLOR_ARCHIVE_A_ADDR, color_archive)
    write_pattern(client, E2A_MAIN_BEFORE_ADDR, main_before)
    write_pattern(client, E2A_MAIN_AFTER_ADDR, main_after)

    assert client.read_memory(E2A_COLOR_PREFIX_GUARD_ADDR, E1C_GUARD_SIZE, 0x100) == color_prefix
    assert client.read_memory(E2A_COLOR_SCRATCH_ADDR, E2A_COLOR_SCRATCH_SIZE, 0x400) == color_scratch
    assert client.read_memory(E2A_COLOR_SUFFIX_GUARD_ADDR, E1C_GUARD_SIZE, 0x100) == color_suffix
    assert client.read_memory(E2A_COLOR_ARCHIVE_A_ADDR, E2A_COLOR_SCRATCH_SIZE, 0x400) == color_archive
    assert client.read_memory(E2A_MAIN_BEFORE_ADDR, E2A_COLOR_SCRATCH_SIZE, 0x400) == main_before
    assert client.read_memory(E2A_MAIN_AFTER_ADDR, E2A_COLOR_SCRATCH_SIZE, 0x400) == main_after

    # E2f: make absence of a second-screen backdrop deterministic. Seed only
    # the first-section physical rows in every framebuffer between quiescent
    # frames; the one captured RSP frame must overwrite only what it renders.
    main_seed = E2F_MAIN_SENTINEL_WORD.to_bytes(2, "big") * (E2F_MAIN_BAND_BYTES // 2)
    prefix_seed = E2F_MAIN_SENTINEL_WORD.to_bytes(2, "big") * (E4B_MAIN_PREFIX_BYTES // 2)
    for framebuffer_addr in E2F_FRAMEBUFFER_ADDRS:
        # E4b clean epoch: the same-band compositor now touches physical rows
        # 0..7 during warmup, so reset them too before the one captured frame.
        write_pattern(client, framebuffer_addr, prefix_seed)
        assert client.read_memory(
            framebuffer_addr, E4B_MAIN_PREFIX_BYTES, 0x400
        ) == prefix_seed

        band_addr = framebuffer_addr + E2F_MAIN_BAND_OFFSET
        write_pattern(client, band_addr, main_seed)
        assert client.read_memory(band_addr, E2F_MAIN_BAND_BYTES, 0x400) == main_seed


def wait_for_proof(
    client: RSPClient,
    *,
    guest_counter_address: int,
    poll_seconds: float,
    attempts: int,
    minimum_counter: int | None = None,
    baseline_counter: int | None = None,
) -> dict[str, int]:
    for attempt in range(1, attempts + 1):
        validate_stop(
            client.continue_then_interrupt(poll_seconds),
            f"E1c proof poll #{attempt}",
        )
        counter = read_u(client, guest_counter_address, 1)
        marker = read_u(client, STATUS_ADDR, 4)
        delta = None if baseline_counter is None else ((counter - baseline_counter) & 0xFF)
        print(
            f"poll {attempt}: guest_counter=0x{counter:02X} "
            f"delta={delta} status=0x{marker:08X}"
        )
        counter_ok = True
        if minimum_counter is not None:
            counter_ok = counter >= minimum_counter
        if baseline_counter is not None:
            counter_ok = delta is not None and delta >= 1
        if counter_ok and marker == STATUS_MARKER:
            return {
                "attempt": attempt,
                "guest_counter": counter,
                "status": marker,
                "counter_delta": 0 if delta is None else delta,
            }
    raise RuntimeError("E1c proof marker/fresh guest frame was not observed")


def set_breakpoint(client: RSPClient, address: int, enabled: bool) -> None:
    command = "Z0" if enabled else "z0"
    reply = client.request(f"{command},{address:x},4")
    if reply != b"OK":
        action = "insert" if enabled else "remove"
        raise RuntimeError(
            f"target rejected software breakpoint {action} at 0x{address:08X}: "
            f"{reply.decode('ascii', errors='replace')}"
        )


def read_quiescent_state(client: RSPClient) -> dict[str, int]:
    marker = read_u(client, STATUS_ADDR, 4)
    framebuffer_pointer = read_u(client, STATUS_ADDR + 4, 4)
    sp_status = read_u(client, SP_STATUS_ADDR, 4)
    dp_status = read_u(client, DP_STATUS_ADDR, 4)
    return {
        "status": marker,
        "proof_framebuffer_pointer": framebuffer_pointer,
        "sp_status": sp_status,
        "dp_status": dp_status,
    }


def validate_quiescent_state(state: dict[str, int], *, require_marker: bool) -> None:
    if (state["sp_status"] & 0x1) == 0:
        raise RuntimeError(
            f"capture breakpoint reached without RSP HALT: SP_STATUS=0x{state['sp_status']:08X}"
        )
    if state["dp_status"] & 0x70:
        raise RuntimeError(
            f"capture breakpoint reached with DP busy: DP_STATUS=0x{state['dp_status']:08X}"
        )
    if require_marker and state["status"] != STATUS_MARKER:
        raise RuntimeError(
            f"capture breakpoint reached without fresh proof marker: 0x{state['status']:08X}"
        )
    if require_marker and not (
        0x80000000 <= state["proof_framebuffer_pointer"] <= 0xBFFFFFFF
    ):
        raise RuntimeError(
            "proof marker contains invalid framebuffer pointer "
            f"0x{state['proof_framebuffer_pointer']:08X}"
        )


def decode_section_queue(data: bytes) -> list[dict[str, int]]:
    if len(data) != SECTION_CAPTURE_SIZE:
        raise ValueError(f"unexpected section capture size: {len(data)}")
    records: list[dict[str, int]] = []
    for index in range(SECTION_RECORD_COUNT):
        base = index * SECTION_RECORD_SIZE
        record = data[base:base + SECTION_RECORD_SIZE]
        records.append({
            "index": index,
            "bgnba": int.from_bytes(
                record[SECTION_BGNBA_OFFSET:SECTION_BGNBA_OFFSET + 2], "big"
            ),
            "bg1sc": record[SECTION_BG1SC_OFFSET],
            "wh0": record[SECTION_WH0_OFFSET],
            "ts": record[SECTION_TS_OFFSET],
            "tm": record[SECTION_TM_OFFSET],
            "bg_mode": record[SECTION_BG_MODE_OFFSET],
            "stat_flags": record[SECTION_STAT_FLAGS_OFFSET],
            "split_line": record[SECTION_SPLIT_LINE_OFFSET],
        })
    return records


def classify_e2d_carrier_sections(
    queue1: bytes,
    queue2: bytes,
) -> dict[str, object]:
    decoded = {
        "queue1": decode_section_queue(queue1),
        "queue2": decode_section_queue(queue2),
    }

    expected = [
        {"index": 0, "wh0": 0x00, "ts": 0x01, "tm": 0x01, "split_line": 16},
        {"index": 1, "wh0": 0x01, "ts": 0x01, "tm": 0x01, "split_line": 224},
    ]

    matches: list[str] = []
    observations: dict[str, object] = {}
    for name, records in decoded.items():
        first_two = records[:2]
        ok = True
        checks: list[dict[str, object]] = []
        for exp, actual in zip(expected, first_two):
            fields = {
                key: actual[key] == value
                for key, value in exp.items()
            }
            checks.append({
                "expected": exp,
                "actual": actual,
                "field_matches": fields,
                "passed": all(fields.values()),
            })
            ok = ok and all(fields.values())
        observations[name] = {
            "passed": ok,
            "checks": checks,
            "first_four_records": records[:4],
        }
        if ok:
            matches.append(name)

    passed = bool(matches)
    return {
        "classification": (
            "E2D_BAND_CARRIER_VALIDATED"
            if passed
            else "E2D_BAND_CARRIER_FAILED"
        ),
        "passed": passed,
        "matching_queues": matches,
        "expected_records": expected,
        "queues": observations,
    }


def classify_e2f_carrier_sections(
    queue1: bytes,
    queue2: bytes,
) -> dict[str, object]:
    decoded = {
        "queue1": decode_section_queue(queue1),
        "queue2": decode_section_queue(queue2),
    }
    expected = [
        {"index": 0, "wh0": 0x00, "ts": 0x02, "tm": 0x01, "split_line": 16},
        {"index": 1, "wh0": 0x01, "ts": 0x02, "tm": 0x01, "split_line": 224},
    ]
    matches: list[str] = []
    observations: dict[str, object] = {}
    for name, records in decoded.items():
        checks: list[dict[str, object]] = []
        ok = True
        for exp, actual in zip(expected, records[:2]):
            fields = {key: actual[key] == value for key, value in exp.items()}
            checks.append({
                "expected": exp,
                "actual": actual,
                "field_matches": fields,
                "passed": all(fields.values()),
            })
            ok = ok and all(fields.values())
        observations[name] = {
            "passed": ok,
            "checks": checks,
            "first_four_records": records[:4],
        }
        if ok:
            matches.append(name)
    passed = bool(matches)
    return {
        "classification": (
            "E2F_BACKDROP_CARRIER_VALIDATED"
            if passed
            else "E2F_BACKDROP_CARRIER_FAILED"
        ),
        "passed": passed,
        "matching_queues": matches,
        "expected_records": expected,
        "queues": observations,
    }


def classify_e3b_raw_before_brightness(
    queue1: bytes,
    queue2: bytes,
    color_final: bytes,
    color_prefix_guard: bytes,
    color_suffix_guard: bytes,
    framebuffer: bytes,
    sub_z: bytes,
    sub_z_prefix: bytes,
    sub_z_suffix: bytes,
    main_z: bytes,
    main_z_prefix: bytes,
    main_z_suffix: bytes,
) -> dict[str, object]:
    carrier = classify_e2f_carrier_sections(queue1, queue2)
    decoded_carriers = {
        "queue1": decode_section_queue(queue1),
        "queue2": decode_section_queue(queue2),
    }
    brightness_queues: list[str] = []
    for name in carrier["matching_queues"]:
        records = decoded_carriers[name][:2]
        if (
            len(records) == 2
            and records[0]["stat_flags"] == 0x48
            and records[1]["stat_flags"] == 0x08
        ):
            brightness_queues.append(name)
    brightness_passed = bool(brightness_queues)

    def words(data: bytes) -> list[int]:
        return [
            int.from_bytes(data[i:i + 2], "big")
            for i in range(0, len(data), 2)
        ]

    compact_words = words(color_final)
    framebuffer_words = words(framebuffer)
    sub_z_words = words(sub_z)
    main_z_words = words(main_z)

    expected_state = (E1C_ACTIVE_X1 - E1C_ACTIVE_X0) * E1C_ROWS // 4
    expected_composed = (E1C_ACTIVE_X1 - E1C_ACTIVE_X0) // 4
    compact_wrong: list[dict[str, int]] = []
    main_wrong: list[dict[str, int]] = []
    sub_z_wrong: list[dict[str, int]] = []
    main_z_wrong: list[dict[str, int]] = []
    pair_counts = collections.Counter()
    state_counts = collections.Counter()

    for y in range(E1C_ROWS):
        main_y = E2B_MAIN_ROW1 + y
        for x in range(E1C_ACTIVE_X0, E1C_ACTIVE_X1):
            state = ((x - E1C_ACTIVE_X0) // 8) & 3
            expected_sub_color = (
                E2B_MAIN_RED_RGBA5551 if state in (2, 3)
                else E2F_BACKDROP_BLUE_RGBA5551
            )
            if main_y == E2B_MAIN_ROW1:
                expected_main_color = (
                    E3B_DIM_RED_RGBA5551 if state in (1, 3)
                    else E3B_DIM_BLUE_RGBA5551
                )
            else:
                expected_main_color = (
                    E2B_MAIN_RED_RGBA5551 if state in (1, 3)
                    else E2F_BACKDROP_BLUE_RGBA5551
                )
            expected_sub_tag = BOOL_TRUE_TAG_WORD if state in (2, 3) else BOOL_FALSE_TAG_WORD
            expected_main_tag = BOOL_TRUE_TAG_WORD if state in (1, 3) else BOOL_FALSE_TAG_WORD

            actual_sub_color = compact_words[y * FB_WIDTH + x]
            actual_main_color = framebuffer_words[main_y * FB_WIDTH + x]
            actual_sub_tag = sub_z_words[y * FB_WIDTH + x]
            actual_main_tag = main_z_words[y * FB_WIDTH + x]

            if actual_sub_color != expected_sub_color and len(compact_wrong) < 64:
                compact_wrong.append({
                    "x": x, "y": y, "state": state,
                    "actual": actual_sub_color, "expected": expected_sub_color,
                })
            if actual_main_color != expected_main_color and len(main_wrong) < 64:
                main_wrong.append({
                    "x": x, "y": main_y, "state": state,
                    "actual": actual_main_color, "expected": expected_main_color,
                })
            if actual_sub_tag != expected_sub_tag and len(sub_z_wrong) < 64:
                sub_z_wrong.append({
                    "x": x, "y": y, "state": state,
                    "actual": actual_sub_tag, "expected": expected_sub_tag,
                })
            if actual_main_tag != expected_main_tag and len(main_z_wrong) < 64:
                main_z_wrong.append({
                    "x": x, "y": y, "state": state,
                    "actual": actual_main_tag, "expected": expected_main_tag,
                })

            state_counts[state] += 1
            pair_counts[(actual_main_tag, actual_sub_tag)] += 1

    # Rows 8..15 are raw Main controls; the compositor owns row 16 only.
    for main_y in range(E2B_MAIN_ROW0, E2B_MAIN_ROW1):
        for x in range(E1C_ACTIVE_X0, E1C_ACTIVE_X1):
            state = ((x - E1C_ACTIVE_X0) // 8) & 3
            expected_main_color = (
                E2B_MAIN_RED_RGBA5551 if state in (1, 3)
                else E2F_BACKDROP_BLUE_RGBA5551
            )
            actual_main_color = framebuffer_words[main_y * FB_WIDTH + x]
            if actual_main_color != expected_main_color and len(main_wrong) < 64:
                main_wrong.append({
                    "x": x, "y": main_y, "state": state,
                    "actual": actual_main_color, "expected": expected_main_color,
                })

    compact_hist = collections.Counter(
        compact_words[y * FB_WIDTH + x]
        for y in range(E1C_ROWS)
        for x in range(E1C_ACTIVE_X0, E1C_ACTIVE_X1)
    )
    main_hist = collections.Counter(
        framebuffer_words[y * FB_WIDTH + x]
        for y in range(E2B_MAIN_ROW0, E2D_MAIN_ROW1)
        for x in range(E1C_ACTIVE_X0, E1C_ACTIVE_X1)
    )
    sub_hist = collections.Counter(
        sub_z_words[y * FB_WIDTH + x]
        for y in range(E1C_ROWS)
        for x in range(E1C_ACTIVE_X0, E1C_ACTIVE_X1)
    )
    main_z_hist = collections.Counter(
        main_z_words[y * FB_WIDTH + x]
        for y in range(E1C_ROWS)
        for x in range(E1C_ACTIVE_X0, E1C_ACTIVE_X1)
    )
    compact_border = collections.Counter(
        compact_words[y * FB_WIDTH + x]
        for y in range(E1C_ROWS)
        for x in range(FB_WIDTH)
        if not (E1C_ACTIVE_X0 <= x < E1C_ACTIVE_X1)
    )
    sub_border = collections.Counter(
        sub_z_words[y * FB_WIDTH + x]
        for y in range(E1C_ROWS)
        for x in range(FB_WIDTH)
        if not (E1C_ACTIVE_X0 <= x < E1C_ACTIVE_X1)
    )
    main_z_border = collections.Counter(
        main_z_words[y * FB_WIDTH + x]
        for y in range(E1C_ROWS)
        for x in range(FB_WIDTH)
        if not (E1C_ACTIVE_X0 <= x < E1C_ACTIVE_X1)
    )

    color_guards_ok = (
        color_prefix_guard == bytes([PREFIX_BYTE]) * E1C_GUARD_SIZE
        and color_suffix_guard == bytes([SUFFIX_BYTE]) * E1C_GUARD_SIZE
    )
    sub_guards_ok = (
        sub_z_prefix == bytes([PREFIX_BYTE]) * E1C_GUARD_SIZE
        and sub_z_suffix == SENTINEL_WORD.to_bytes(2, "big") * (E1C_GUARD_SIZE // 2)
    )
    main_guards_ok = (
        main_z_prefix == bytes([E2G_SECOND_Z_PREFIX_BYTE]) * E1C_GUARD_SIZE
        and main_z_suffix == bytes([E2G_SECOND_Z_SUFFIX_BYTE]) * E1C_GUARD_SIZE
    )

    colors_passed = (
        not compact_wrong
        and not main_wrong
        and compact_hist[E2B_MAIN_RED_RGBA5551] == expected_state * 2
        and compact_hist[E2F_BACKDROP_BLUE_RGBA5551] == expected_state * 2
        and main_hist[E2B_MAIN_RED_RGBA5551] == expected_state * 4 - expected_composed * 2
        and main_hist[E2F_BACKDROP_BLUE_RGBA5551] == expected_state * 4 - expected_composed * 2
        and main_hist[E3B_DIM_RED_RGBA5551] == expected_composed * 2
        and main_hist[E3B_DIM_BLUE_RGBA5551] == expected_composed * 2
        and main_hist[E3B_PREBRIGHT_RED_RGBA5551] == 0
        and compact_border[SENTINEL_WORD] == (FB_WIDTH - 256) * E1C_ROWS
        and color_guards_ok
    )
    expected_pairs = collections.Counter({
        (BOOL_FALSE_TAG_WORD, BOOL_FALSE_TAG_WORD): expected_state,
        (BOOL_TRUE_TAG_WORD, BOOL_FALSE_TAG_WORD): expected_state,
        (BOOL_FALSE_TAG_WORD, BOOL_TRUE_TAG_WORD): expected_state,
        (BOOL_TRUE_TAG_WORD, BOOL_TRUE_TAG_WORD): expected_state,
    })
    metadata_passed = (
        not sub_z_wrong
        and not main_z_wrong
        and sub_hist[BOOL_FALSE_TAG_WORD] == expected_state * 2
        and sub_hist[BOOL_TRUE_TAG_WORD] == expected_state * 2
        and main_z_hist[BOOL_FALSE_TAG_WORD] == expected_state * 2
        and main_z_hist[BOOL_TRUE_TAG_WORD] == expected_state * 2
        and sub_border[SENTINEL_WORD] == (FB_WIDTH - 256) * E1C_ROWS
        and main_z_border[SENTINEL_WORD] == (FB_WIDTH - 256) * E1C_ROWS
        and sub_guards_ok
        and main_guards_ok
        and state_counts == collections.Counter({
            0: expected_state, 1: expected_state,
            2: expected_state, 3: expected_state,
        })
        and pair_counts == expected_pairs
    )
    passed = bool(
        carrier["passed"]
        and brightness_passed
        and colors_passed
        and metadata_passed
    )

    return {
        "classification": (
            "E3B_RAW_BEFORE_BRIGHTNESS_VALIDATED"
            if passed else "E3B_RAW_BEFORE_BRIGHTNESS_FAILED"
        ),
        "passed": passed,
        "carrier": carrier,
        "brightness": {
            "passed": brightness_passed,
            "matching_queues": brightness_queues,
            "expected_stat_flags": ["0x48", "0x08"],
        },
        "colors": {
            "passed": colors_passed,
            "compact_full_red": compact_hist[E2B_MAIN_RED_RGBA5551],
            "compact_full_blue": compact_hist[E2F_BACKDROP_BLUE_RGBA5551],
            "main_full_red": main_hist[E2B_MAIN_RED_RGBA5551],
            "main_full_blue": main_hist[E2F_BACKDROP_BLUE_RGBA5551],
            "main_dim_red": main_hist[E3B_DIM_RED_RGBA5551],
            "main_dim_blue": main_hist[E3B_DIM_BLUE_RGBA5551],
            "main_prebright_red30": main_hist[E3B_PREBRIGHT_RED_RGBA5551],
            "compact_mismatches": compact_wrong,
            "main_mismatches": main_wrong,
        },
        "sub_z": {
            "false_words": sub_hist[BOOL_FALSE_TAG_WORD],
            "true_words": sub_hist[BOOL_TRUE_TAG_WORD],
            "border_sentinel_words": sub_border[SENTINEL_WORD],
            "guards_ok": sub_guards_ok,
            "mismatches": sub_z_wrong,
        },
        "main_z": {
            "false_words": main_z_hist[BOOL_FALSE_TAG_WORD],
            "true_words": main_z_hist[BOOL_TRUE_TAG_WORD],
            "border_sentinel_words": main_z_border[SENTINEL_WORD],
            "guards_ok": main_guards_ok,
            "mismatches": main_z_wrong,
        },
        "pairwise": {
            "state_counts": dict(state_counts),
            "pairs": {
                f"{main:04x}/{sub:04x}": count
                for (main, sub), count in sorted(pair_counts.items())
            },
            "expected_each": expected_state,
        },
        "constants": {
            "boolean_false_tag": hex(BOOL_FALSE_TAG_WORD),
            "boolean_true_tag": hex(BOOL_TRUE_TAG_WORD),
            "full_blue_rgba5551": hex(E2F_BACKDROP_BLUE_RGBA5551),
            "full_red_rgba5551": hex(E2B_MAIN_RED_RGBA5551),
            "dim_blue_rgba5551": hex(E3B_DIM_BLUE_RGBA5551),
            "dim_red_rgba5551": hex(E3B_DIM_RED_RGBA5551),
            "prebright_red30_rgba5551": hex(E3B_PREBRIGHT_RED_RGBA5551),
            "sub_z_address": hex(E1C_Z_SCRATCH_ADDR),
            "main_z_address": hex(E2G_SECOND_Z_ADDR),
        },
    }


def classify_e4a_dma2d_band_stream(
    queue1: bytes,
    queue2: bytes,
    color_final: bytes,
    color_prefix_guard: bytes,
    color_suffix_guard: bytes,
    framebuffer: bytes,
    sub_z: bytes,
    sub_z_prefix: bytes,
    sub_z_suffix: bytes,
    main_z: bytes,
    main_z_prefix: bytes,
    main_z_suffix: bytes,
    main_before: bytes,
    main_after: bytes,
) -> dict[str, object]:
    base = classify_e3b_raw_before_brightness(
        queue1,
        queue2,
        color_final,
        color_prefix_guard,
        color_suffix_guard,
        framebuffer,
        sub_z,
        sub_z_prefix,
        sub_z_suffix,
        main_z,
        main_z_prefix,
        main_z_suffix,
    )

    dim_row = E3B_DIM_BLUE_RGBA5551.to_bytes(2, "big") * 8
    full_row = E2F_BACKDROP_BLUE_RGBA5551.to_bytes(2, "big") * 8
    expected_gather = dim_row + full_row * 7
    expected_before = (
        expected_gather
        + bytes([E2A_MAIN_BEFORE_INIT]) * (len(main_before) - len(expected_gather))
    )
    expected_after = bytearray([E2A_MAIN_AFTER_INIT]) * len(main_after)
    expected_segments: list[dict[str, int]] = []
    for row in range(8):
        start = row * FB_WIDTH * 2 + E1C_ACTIVE_X0 * 2
        end = start + 16
        expected_after[start:end] = expected_gather[row * 16:(row + 1) * 16]
        expected_segments.append({
            "row": row,
            "start": start,
            "end_exclusive": end,
        })

    before_passed = main_before == expected_before
    after_passed = main_after == bytes(expected_after)
    before_changed = sum(
        actual != E2A_MAIN_BEFORE_INIT for actual in main_before
    )
    after_changed = sum(
        actual != E2A_MAIN_AFTER_INIT for actual in main_after
    )
    dma2d_passed = bool(
        before_passed
        and after_passed
        and before_changed == 128
        and after_changed == 128
    )
    passed = bool(base["passed"] and dma2d_passed)

    base["classification"] = (
        "E4A_DMA2D_GATHER_SCATTER_VALIDATED"
        if passed else "E4A_DMA2D_GATHER_SCATTER_FAILED"
    )
    base["passed"] = passed
    base["dma2d"] = {
        "passed": dma2d_passed,
        "len_register": hex(0x2200700F),
        "gather": {
            "passed": before_passed,
            "changed_bytes": before_changed,
            "expected_changed_bytes": 128,
            "expected_words": {
                "dim_blue": 8,
                "full_blue": 56,
            },
            "tail_init_byte": hex(E2A_MAIN_BEFORE_INIT),
        },
        "scatter": {
            "passed": after_passed,
            "changed_bytes": after_changed,
            "expected_changed_bytes": 128,
            "segments": expected_segments,
            "init_byte": hex(E2A_MAIN_AFTER_INIT),
            "stride_bytes": FB_WIDTH * 2,
        },
    }
    return base


def classify_e4b_same_band_row_correct(
    queue1: bytes,
    queue2: bytes,
    color_final: bytes,
    color_prefix_guard: bytes,
    color_suffix_guard: bytes,
    framebuffer: bytes,
    sub_z: bytes,
    sub_z_prefix: bytes,
    sub_z_suffix: bytes,
    main_z: bytes,
    main_z_prefix: bytes,
    main_z_suffix: bytes,
) -> dict[str, object]:
    """Executable authority for the precommitted row-correct E4b oracle."""
    carrier = classify_e2f_carrier_sections(queue1, queue2)
    decoded = {
        "queue1": decode_section_queue(queue1),
        "queue2": decode_section_queue(queue2),
    }
    brightness_queues: list[str] = []
    for name in carrier["matching_queues"]:
        records = decoded[name][:2]
        if (
            len(records) == 2
            and records[0]["stat_flags"] == 0x48
            and records[1]["stat_flags"] == 0x08
        ):
            brightness_queues.append(name)
    brightness_passed = bool(brightness_queues)

    def words(data: bytes) -> list[int]:
        return [
            int.from_bytes(data[i:i + 2], "big")
            for i in range(0, len(data), 2)
        ]

    fb_words = words(framebuffer)
    compact_words = words(color_final)
    sub_words = words(sub_z)
    main_words = words(main_z)

    top_border_wrong: list[dict[str, int]] = []
    for y in range(0, E2B_MAIN_ROW0):
        for x in range(FB_WIDTH):
            actual = fb_words[y * FB_WIDTH + x]
            if actual != E2F_MAIN_SENTINEL_WORD and len(top_border_wrong) < 64:
                top_border_wrong.append({
                    "x": x, "y": y,
                    "actual": actual, "expected": E2F_MAIN_SENTINEL_WORD,
                })

    tile_wrong: list[dict[str, int]] = []
    tile_rows: list[dict[str, object]] = []
    for y in range(E2B_MAIN_ROW0, E2D_MAIN_ROW1):
        if y <= 14:
            expected = E4B_DIM_YELLOW_RGBA5551
        elif y <= 22:
            expected = E3B_DIM_RED_RGBA5551
        else:
            expected = E3B_DIM_BLUE_RGBA5551
        row_values = []
        for x in range(E1C_ACTIVE_X0, E1C_ACTIVE_X0 + 8):
            actual = fb_words[y * FB_WIDTH + x]
            row_values.append(actual)
            if actual != expected and len(tile_wrong) < 64:
                tile_wrong.append({
                    "x": x, "y": y,
                    "actual": actual, "expected": expected,
                })
        tile_rows.append({
            "row": y,
            "expected": hex(expected),
            "matching_words": sum(value == expected for value in row_values),
            "expected_words": 8,
        })

    compact_wrong: list[dict[str, int]] = []
    sub_wrong: list[dict[str, int]] = []
    pair_counts = collections.Counter()
    compact_hist = collections.Counter()
    sub_hist = collections.Counter()
    main_hist = collections.Counter()
    for y in range(E1C_ROWS):
        for x in range(E1C_ACTIVE_X0, E1C_ACTIVE_X1):
            state = ((x - E1C_ACTIVE_X0) // 8) & 3
            expected_compact = (
                BG2_GREEN_RGBA5551 if state in (2, 3)
                else E2F_BACKDROP_BLUE_RGBA5551
            )
            expected_sub = (
                BOOL_TRUE_TAG_WORD if state in (2, 3)
                else BOOL_FALSE_TAG_WORD
            )
            actual_compact = compact_words[y * FB_WIDTH + x]
            actual_sub = sub_words[y * FB_WIDTH + x]
            actual_main = main_words[y * FB_WIDTH + x]
            compact_hist[actual_compact] += 1
            sub_hist[actual_sub] += 1
            main_hist[actual_main] += 1
            pair_counts[(actual_main, actual_sub)] += 1
            if actual_compact != expected_compact and len(compact_wrong) < 64:
                compact_wrong.append({
                    "x": x, "y": y, "state": state,
                    "actual": actual_compact, "expected": expected_compact,
                })
            if actual_sub != expected_sub and len(sub_wrong) < 64:
                sub_wrong.append({
                    "x": x, "y": y, "state": state,
                    "actual": actual_sub, "expected": expected_sub,
                })

    # The vertically asymmetric guest deliberately crosses a tile row on the
    # eighth scanline.  This 8x8 Main-Z signature was frozen before inspecting
    # the row-correct semantic artifact.
    main_tile_wrong: list[dict[str, int]] = []
    for y in range(E1C_ROWS):
        expected = BOOL_TRUE_TAG_WORD if y < 7 else BOOL_FALSE_TAG_WORD
        for x in range(E1C_ACTIVE_X0, E1C_ACTIVE_X0 + 8):
            actual = main_words[y * FB_WIDTH + x]
            if actual != expected and len(main_tile_wrong) < 64:
                main_tile_wrong.append({
                    "x": x, "y": y,
                    "actual": actual, "expected": expected,
                })

    compact_border = collections.Counter(
        compact_words[y * FB_WIDTH + x]
        for y in range(E1C_ROWS)
        for x in range(FB_WIDTH)
        if not (E1C_ACTIVE_X0 <= x < E1C_ACTIVE_X1)
    )
    sub_border = collections.Counter(
        sub_words[y * FB_WIDTH + x]
        for y in range(E1C_ROWS)
        for x in range(FB_WIDTH)
        if not (E1C_ACTIVE_X0 <= x < E1C_ACTIVE_X1)
    )
    main_border = collections.Counter(
        main_words[y * FB_WIDTH + x]
        for y in range(E1C_ROWS)
        for x in range(FB_WIDTH)
        if not (E1C_ACTIVE_X0 <= x < E1C_ACTIVE_X1)
    )
    color_guards_ok = (
        color_prefix_guard == bytes([PREFIX_BYTE]) * E1C_GUARD_SIZE
        and color_suffix_guard == bytes([SUFFIX_BYTE]) * E1C_GUARD_SIZE
    )
    sub_guards_ok = (
        sub_z_prefix == bytes([PREFIX_BYTE]) * E1C_GUARD_SIZE
        and sub_z_suffix
        == SENTINEL_WORD.to_bytes(2, "big") * (E1C_GUARD_SIZE // 2)
    )
    main_guards_ok = (
        main_z_prefix == bytes([E2G_SECOND_Z_PREFIX_BYTE]) * E1C_GUARD_SIZE
        and main_z_suffix == bytes([E2G_SECOND_Z_SUFFIX_BYTE]) * E1C_GUARD_SIZE
    )

    expected_pairs = collections.Counter({
        (BOOL_FALSE_TAG_WORD, BOOL_FALSE_TAG_WORD): 512,
        (BOOL_TRUE_TAG_WORD, BOOL_FALSE_TAG_WORD): 512,
        (BOOL_FALSE_TAG_WORD, BOOL_TRUE_TAG_WORD): 512,
        (BOOL_TRUE_TAG_WORD, BOOL_TRUE_TAG_WORD): 512,
    })
    controls_passed = bool(
        not compact_wrong
        and not sub_wrong
        and not main_tile_wrong
        and compact_hist[E2F_BACKDROP_BLUE_RGBA5551] == 1024
        and compact_hist[BG2_GREEN_RGBA5551] == 1024
        and sum(compact_hist.values()) == 2048
        and sub_hist[BOOL_FALSE_TAG_WORD] == 1024
        and sub_hist[BOOL_TRUE_TAG_WORD] == 1024
        and sum(sub_hist.values()) == 2048
        and main_hist[BOOL_FALSE_TAG_WORD] == 1024
        and main_hist[BOOL_TRUE_TAG_WORD] == 1024
        and sum(main_hist.values()) == 2048
        and pair_counts == expected_pairs
        and compact_border[SENTINEL_WORD] == 192
        and sub_border[SENTINEL_WORD] == 192
        and main_border[SENTINEL_WORD] == 192
        and color_guards_ok
        and sub_guards_ok
        and main_guards_ok
    )
    same_band_passed = bool(not top_border_wrong and not tile_wrong)
    passed = bool(
        carrier["passed"]
        and brightness_passed
        and same_band_passed
        and controls_passed
    )

    return {
        "classification": (
            "E4B_SAME_BAND_ROW_CORRECT_VALIDATED"
            if passed else "E4B_SAME_BAND_ROW_CORRECT_FAILED"
        ),
        "passed": passed,
        "carrier": carrier,
        "brightness": {
            "passed": brightness_passed,
            "matching_queues": brightness_queues,
            "expected_stat_flags": ["0x48", "0x08"],
        },
        "same_band": {
            "passed": same_band_passed,
            "top_border_mismatches": top_border_wrong,
            "tile_mismatches": tile_wrong,
            "tile_rows": tile_rows,
            "top_border_expected_word": hex(E2F_MAIN_SENTINEL_WORD),
            "tile_x_range": [E1C_ACTIVE_X0, E1C_ACTIVE_X0 + 8],
        },
        "controls": {
            "passed": controls_passed,
            "compact_blue_words": compact_hist[E2F_BACKDROP_BLUE_RGBA5551],
            "compact_green_words": compact_hist[BG2_GREEN_RGBA5551],
            "sub_false_words": sub_hist[BOOL_FALSE_TAG_WORD],
            "sub_true_words": sub_hist[BOOL_TRUE_TAG_WORD],
            "main_false_words": main_hist[BOOL_FALSE_TAG_WORD],
            "main_true_words": main_hist[BOOL_TRUE_TAG_WORD],
            "pairwise": {
                f"{main:04x}/{sub:04x}": count
                for (main, sub), count in sorted(pair_counts.items())
            },
            "compact_border_sentinel_words": compact_border[SENTINEL_WORD],
            "sub_border_sentinel_words": sub_border[SENTINEL_WORD],
            "main_border_sentinel_words": main_border[SENTINEL_WORD],
            "color_guards_ok": color_guards_ok,
            "sub_guards_ok": sub_guards_ok,
            "main_guards_ok": main_guards_ok,
            "compact_mismatches": compact_wrong,
            "sub_mismatches": sub_wrong,
            "main_tile_mismatches": main_tile_wrong,
        },
        "constants": {
            "dim_yellow_rgba5551": hex(E4B_DIM_YELLOW_RGBA5551),
            "dim_red_rgba5551": hex(E3B_DIM_RED_RGBA5551),
            "dim_blue_rgba5551": hex(E3B_DIM_BLUE_RGBA5551),
            "raw_blue_rgba5551": hex(E2F_BACKDROP_BLUE_RGBA5551),
            "raw_green_rgba5551": hex(BG2_GREEN_RGBA5551),
            "false_tag": hex(BOOL_FALSE_TAG_WORD),
            "true_tag": hex(BOOL_TRUE_TAG_WORD),
        },
    }


def classify_e2e_z_band_alignment(
    queue1: bytes,
    queue2: bytes,
    color_final: bytes,
    color_prefix_guard: bytes,
    color_suffix_guard: bytes,
    framebuffer: bytes,
    z_final: bytes,
    z_prefix_guard: bytes,
    z_suffix_guard: bytes,
) -> dict[str, object]:
    carrier = classify_e2d_carrier_sections(queue1, queue2)

    def words(data: bytes) -> list[int]:
        return [
            int.from_bytes(data[i:i + 2], "big")
            for i in range(0, len(data), 2)
        ]

    compact_words = words(color_final)
    compact_wrong: list[dict[str, int]] = []
    for index, actual in enumerate(compact_words):
        y, x = divmod(index, FB_WIDTH)
        active = E1C_ACTIVE_X0 <= x < E1C_ACTIVE_X1
        expected = E2B_MAIN_RED_RGBA5551 if active else SENTINEL_WORD
        if actual != expected and len(compact_wrong) < 64:
            compact_wrong.append({
                "x": x,
                "y": y,
                "actual": actual,
                "expected": expected,
            })

    expected_compact_active = (
        E1C_ACTIVE_X1 - E1C_ACTIVE_X0
    ) * E1C_ROWS
    expected_border = (
        FB_WIDTH - (E1C_ACTIVE_X1 - E1C_ACTIVE_X0)
    ) * E1C_ROWS
    expected_main_active = (
        E1C_ACTIVE_X1 - E1C_ACTIVE_X0
    ) * (E2D_MAIN_ROW1 - E2B_MAIN_ROW0)
    compact_hist = collections.Counter(compact_words)
    prefix_ok = color_prefix_guard == bytes([PREFIX_BYTE]) * E1C_GUARD_SIZE
    suffix_ok = color_suffix_guard == bytes([SUFFIX_BYTE]) * E1C_GUARD_SIZE

    framebuffer_words = words(framebuffer)
    main_wrong: list[dict[str, int]] = []
    main_active_words: list[int] = []
    for y in range(E2B_MAIN_ROW0, E2D_MAIN_ROW1):
        row = framebuffer_words[y * FB_WIDTH:(y + 1) * FB_WIDTH]
        for x in range(E1C_ACTIVE_X0, E1C_ACTIVE_X1):
            actual = row[x]
            main_active_words.append(actual)
            if actual != E2B_MAIN_RED_RGBA5551 and len(main_wrong) < 64:
                main_wrong.append({
                    "x": x,
                    "y": y,
                    "actual": actual,
                    "expected": E2B_MAIN_RED_RGBA5551,
                })
    main_hist = collections.Counter(main_active_words)

    compact_passed = (
        len(compact_words) == FB_WIDTH * E1C_ROWS
        and not compact_wrong
        and compact_hist[E2B_MAIN_RED_RGBA5551] == expected_compact_active
        and compact_hist[SENTINEL_WORD] == expected_border
        and prefix_ok
        and suffix_ok
    )
    main_passed = (
        len(main_active_words) == expected_main_active
        and not main_wrong
        and main_hist[E2B_MAIN_RED_RGBA5551] == expected_main_active
        and main_hist[BG2_GREEN_RGBA5551] == 0
    )
    z_words = words(z_final)
    z_wrong: list[dict[str, int]] = []
    for index, actual in enumerate(z_words):
        y, x = divmod(index, FB_WIDTH)
        active = E1C_ACTIVE_X0 <= x < E1C_ACTIVE_X1
        expected = BG1_TAG_WORD if active else SENTINEL_WORD
        if actual != expected and len(z_wrong) < 64:
            z_wrong.append({
                "x": x,
                "y": y,
                "actual": actual,
                "expected": expected,
            })
    z_hist = collections.Counter(z_words)
    z_prefix_ok = z_prefix_guard == bytes([PREFIX_BYTE]) * E1C_GUARD_SIZE
    z_suffix_ok = z_suffix_guard == (
        SENTINEL_WORD.to_bytes(2, "big") * (E1C_GUARD_SIZE // 2)
    )
    z_passed = (
        len(z_words) == FB_WIDTH * E1C_ROWS
        and not z_wrong
        and z_hist[BG1_TAG_WORD] == expected_compact_active
        and z_hist[SENTINEL_WORD] == expected_border
        and z_prefix_ok
        and z_suffix_ok
    )

    pixels_passed = compact_passed and main_passed
    passed = bool(carrier["passed"] and pixels_passed and z_passed)

    return {
        "classification": (
            "E2E_REAL_Z_BAND_ALIGNMENT_VALIDATED"
            if passed
            else "E2E_REAL_Z_BAND_ALIGNMENT_FAILED"
        ),
        "passed": passed,
        "carrier": carrier,
        "z_contract": {
            "passed": z_passed,
            "active_bg1_tag_words": z_hist[BG1_TAG_WORD],
            "sentinel_border_words": z_hist[SENTINEL_WORD],
            "prefix_guard_ok": z_prefix_ok,
            "suffix_guard_ok": z_suffix_ok,
            "mismatches": z_wrong,
            "constants": {
                "scratch_address": hex(E1C_Z_SCRATCH_ADDR),
                "scratch_size": E1C_Z_SCRATCH_SIZE,
                "active_tag": hex(BG1_TAG_WORD),
                "sentinel_word": hex(SENTINEL_WORD),
                "expected_active_words": expected_compact_active,
                "expected_border_words": expected_border,
            },
        },
        "pixel_contract": {
            "passed": pixels_passed,
            "constants": {
                "width": FB_WIDTH,
                "compact_rows": E1C_ROWS,
                "compact_address": hex(E2A_COLOR_SCRATCH_ADDR),
                "compact_size": E2A_COLOR_SCRATCH_SIZE,
                "compact_active_x0": E1C_ACTIVE_X0,
                "compact_active_x1_exclusive": E1C_ACTIVE_X1,
                "compact_color": hex(E2B_MAIN_RED_RGBA5551),
                "compact_border": hex(SENTINEL_WORD),
                "main_row0": E2B_MAIN_ROW0,
                "main_row1_exclusive": E2D_MAIN_ROW1,
                "main_color": hex(E2B_MAIN_RED_RGBA5551),
                "expected_compact_active_words": expected_compact_active,
                "expected_main_active_words": expected_main_active,
                "expected_border_words": expected_border,
            },
            "compact": {
                "passed": compact_passed,
                "active_red_words": compact_hist[E2B_MAIN_RED_RGBA5551],
                "sentinel_border_words": compact_hist[SENTINEL_WORD],
                "prefix_guard_ok": prefix_ok,
                "suffix_guard_ok": suffix_ok,
                "mismatches": compact_wrong,
            },
            "main": {
                "passed": main_passed,
                "active_red_words": main_hist[E2B_MAIN_RED_RGBA5551],
                "active_green_words": main_hist[BG2_GREEN_RGBA5551],
                "active_words": len(main_active_words),
                "mismatches": main_wrong,
            },
        },
    }


def classify_z(
    archive_a: bytes,
    final_b: bytes,
    prefix_guard: bytes,
    suffix_guard: bytes,
) -> dict[str, object]:
    assert len(archive_a) == E1C_Z_SCRATCH_SIZE
    assert len(final_b) == E1C_Z_SCRATCH_SIZE
    assert len(prefix_guard) == E1C_GUARD_SIZE
    assert len(suffix_guard) == E1C_GUARD_SIZE

    def words(data: bytes) -> list[int]:
        return [
            int.from_bytes(data[i:i + 2], "big")
            for i in range(0, len(data), 2)
        ]

    a_words = words(archive_a)
    b_words = words(final_b)
    a_hist = collections.Counter(a_words)
    b_hist = collections.Counter(b_words)

    a_wrong: list[dict[str, int]] = []
    b_wrong: list[dict[str, int]] = []
    for index, (za, zb) in enumerate(zip(a_words, b_words)):
        y, x = divmod(index, FB_WIDTH)
        active = E1C_ACTIVE_X0 <= x < E1C_ACTIVE_X1
        expected_a = BG1_TAG_WORD if active else SENTINEL_WORD
        expected_b = BG2_TAG_WORD if active else SENTINEL_WORD
        if za != expected_a and len(a_wrong) < 64:
            a_wrong.append({"x": x, "y": y, "actual": za, "expected": expected_a})
        if zb != expected_b and len(b_wrong) < 64:
            b_wrong.append({"x": x, "y": y, "actual": zb, "expected": expected_b})

    prefix_ok = prefix_guard == bytes([PREFIX_BYTE]) * E1C_GUARD_SIZE
    suffix_ok = suffix_guard == bytes([SUFFIX_BYTE]) * E1C_GUARD_SIZE
    expected_active = (E1C_ACTIVE_X1 - E1C_ACTIVE_X0) * E1C_ROWS
    expected_border = (FB_WIDTH - (E1C_ACTIVE_X1 - E1C_ACTIVE_X0)) * E1C_ROWS

    passed = (
        prefix_ok
        and suffix_ok
        and not a_wrong
        and not b_wrong
        and a_hist[BG1_TAG_WORD] == expected_active
        and a_hist[SENTINEL_WORD] == expected_border
        and b_hist[BG2_TAG_WORD] == expected_active
        and b_hist[SENTINEL_WORD] == expected_border
        and b_hist[BG1_TAG_WORD] == 0
        and len(a_words) == FB_WIDTH * E1C_ROWS
        and len(b_words) == FB_WIDTH * E1C_ROWS
    )

    return {
        "classification": (
            "E1C_STRIP_REUSE_CONTRACT_VALIDATED"
            if passed
            else "E1C_STRIP_REUSE_CONTRACT_FAILED"
        ),
        "passed": passed,
        "constants": {
            "width": FB_WIDTH,
            "rows": E1C_ROWS,
            "scratch_address": hex(E1C_Z_SCRATCH_ADDR),
            "scratch_size": E1C_Z_SCRATCH_SIZE,
            "archive_a_address": hex(E1C_ARCHIVE_A_ADDR),
            "prefix_guard_address": hex(E1C_PREFIX_GUARD_ADDR),
            "suffix_guard_address": hex(E1C_SUFFIX_GUARD_ADDR),
            "guard_size": E1C_GUARD_SIZE,
            "active_x0": E1C_ACTIVE_X0,
            "active_x1_exclusive": E1C_ACTIVE_X1,
            "sentinel_word": hex(SENTINEL_WORD),
            "band_a_tag_word": hex(BG1_TAG_WORD),
            "band_b_tag_word": hex(BG2_TAG_WORD),
            "expected_active_words": expected_active,
            "expected_border_words": expected_border,
        },
        "counts": {
            "archive_a_tag_words": a_hist[BG1_TAG_WORD],
            "archive_a_sentinel_words": a_hist[SENTINEL_WORD],
            "final_b_tag_words": b_hist[BG2_TAG_WORD],
            "final_b_sentinel_words": b_hist[SENTINEL_WORD],
            "final_b_stale_a_words": b_hist[BG1_TAG_WORD],
            "words_per_compact_strip": len(a_words),
        },
        "guards": {
            "prefix_ok": prefix_ok,
            "suffix_ok": suffix_ok,
        },
        "archive_a_histogram_top": [
            {"word": hex(word), "count": count}
            for word, count in a_hist.most_common(8)
        ],
        "final_b_histogram_top": [
            {"word": hex(word), "count": count}
            for word, count in b_hist.most_common(8)
        ],
        "mismatches": {
            "archive_a_wrong": a_wrong,
            "final_b_wrong": b_wrong,
        },
    }


def classify_e2a(
    z_archive_a: bytes,
    z_final_b: bytes,
    z_prefix_guard: bytes,
    z_suffix_guard: bytes,
    color_archive_a: bytes,
    color_final_b: bytes,
    color_prefix_guard: bytes,
    color_suffix_guard: bytes,
    main_before: bytes,
    main_after: bytes,
) -> dict[str, object]:
    z = classify_z(z_archive_a, z_final_b, z_prefix_guard, z_suffix_guard)

    def words(data: bytes) -> list[int]:
        return [
            int.from_bytes(data[i:i + 2], "big")
            for i in range(0, len(data), 2)
        ]

    a_words = words(color_archive_a)
    b_words = words(color_final_b)
    a_hist = collections.Counter(a_words)
    b_hist = collections.Counter(b_words)
    a_wrong: list[dict[str, int]] = []
    b_wrong: list[dict[str, int]] = []
    for index, (ca, cb) in enumerate(zip(a_words, b_words)):
        y, x = divmod(index, FB_WIDTH)
        active = E1C_ACTIVE_X0 <= x < E1C_ACTIVE_X1
        expected_a = E2A_COLOR_A_WORD if active else SENTINEL_WORD
        expected_b = E2A_COLOR_B_WORD if active else SENTINEL_WORD
        if ca != expected_a and len(a_wrong) < 64:
            a_wrong.append({"x": x, "y": y, "actual": ca, "expected": expected_a})
        if cb != expected_b and len(b_wrong) < 64:
            b_wrong.append({"x": x, "y": y, "actual": cb, "expected": expected_b})

    expected_active = (E1C_ACTIVE_X1 - E1C_ACTIVE_X0) * E1C_ROWS
    expected_border = (FB_WIDTH - (E1C_ACTIVE_X1 - E1C_ACTIVE_X0)) * E1C_ROWS
    prefix_ok = color_prefix_guard == bytes([PREFIX_BYTE]) * E1C_GUARD_SIZE
    suffix_ok = color_suffix_guard == bytes([SUFFIX_BYTE]) * E1C_GUARD_SIZE
    main_equal = main_before == main_after
    main_before_written = main_before != bytes([E2A_MAIN_BEFORE_INIT]) * len(main_before)
    main_after_written = main_after != bytes([E2A_MAIN_AFTER_INIT]) * len(main_after)

    color_passed = (
        prefix_ok
        and suffix_ok
        and not a_wrong
        and not b_wrong
        and a_hist[E2A_COLOR_A_WORD] == expected_active
        and a_hist[SENTINEL_WORD] == expected_border
        and b_hist[E2A_COLOR_B_WORD] == expected_active
        and b_hist[SENTINEL_WORD] == expected_border
        and b_hist[E2A_COLOR_A_WORD] == 0
        and len(a_words) == FB_WIDTH * E1C_ROWS
        and len(b_words) == FB_WIDTH * E1C_ROWS
        and main_equal
        and main_before_written
        and main_after_written
    )
    passed = bool(z["passed"] and color_passed)

    return {
        "classification": (
            "E2A_COLOR_STRIP_REUSE_VALIDATED"
            if passed
            else "E2A_COLOR_STRIP_REUSE_FAILED"
        ),
        "passed": passed,
        "z_control": z,
        "color_contract": {
            "passed": color_passed,
            "constants": {
                "scratch_address": hex(E2A_COLOR_SCRATCH_ADDR),
                "scratch_size": E2A_COLOR_SCRATCH_SIZE,
                "archive_a_address": hex(E2A_COLOR_ARCHIVE_A_ADDR),
                "prefix_guard_address": hex(E2A_COLOR_PREFIX_GUARD_ADDR),
                "suffix_guard_address": hex(E2A_COLOR_SUFFIX_GUARD_ADDR),
                "main_before_address": hex(E2A_MAIN_BEFORE_ADDR),
                "main_after_address": hex(E2A_MAIN_AFTER_ADDR),
                "band_a_color": hex(E2A_COLOR_A_WORD),
                "band_b_color": hex(E2A_COLOR_B_WORD),
                "sentinel_word": hex(SENTINEL_WORD),
                "expected_active_words": expected_active,
                "expected_border_words": expected_border,
            },
            "counts": {
                "archive_a_color_words": a_hist[E2A_COLOR_A_WORD],
                "archive_a_sentinel_words": a_hist[SENTINEL_WORD],
                "final_b_color_words": b_hist[E2A_COLOR_B_WORD],
                "final_b_sentinel_words": b_hist[SENTINEL_WORD],
                "final_b_stale_a_words": b_hist[E2A_COLOR_A_WORD],
                "words_per_compact_strip": len(a_words),
            },
            "guards": {
                "prefix_ok": prefix_ok,
                "suffix_ok": suffix_ok,
            },
            "main_frame": {
                "before_after_equal": main_equal,
                "before_snapshot_written": main_before_written,
                "after_snapshot_written": main_after_written,
            },
            "mismatches": {
                "archive_a_wrong": a_wrong,
                "final_b_wrong": b_wrong,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9149)
    parser.add_argument("--connect-timeout", type=float, default=30.0)
    parser.add_argument("--response-timeout", type=float, default=30.0)
    parser.add_argument("--guest-counter-address", required=True, type=parse_int)
    parser.add_argument("--framebuffer-address", required=True, type=parse_int)
    parser.add_argument("--capture-ready-address", required=True, type=parse_int)
    parser.add_argument("--poll-seconds", type=float, default=0.20)
    parser.add_argument("--attempts", type=int, default=80)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    client = connect_with_retry(
        args.host, args.port, args.connect_timeout, args.response_timeout
    )
    try:
        supported = client.request("qSupported:multiprocess+;swbreak+;hwbreak+")
        print(f"GDB server capabilities: {supported.decode('ascii', errors='replace')}")
        initial = client.request("?")
        print(f"Initial target state: {initial.decode('ascii', errors='replace')}")
        if b"QPassSignals+" not in supported:
            raise RuntimeError("GDB server does not advertise QPassSignals")
        if client.request(f"QPassSignals:{ARES_N64_GUEST_SIGNALS}") != b"OK":
            raise RuntimeError("target rejected QPassSignals")

        # Warm the guest/runtime before touching the evidence scratch. The initial
        # GDB stop can occur while startup ownership is still unstable; E1a only needs
        # guest progress plus the post-DP-fence marker to establish a stable epoch.
        warmup = wait_for_proof(
            client,
            guest_counter_address=args.guest_counter_address,
            poll_seconds=args.poll_seconds,
            attempts=args.attempts,
            minimum_counter=5,
        )

        # Stop at the CPU's post-rsp_wait point. Sodium64 reaches this PC only
        # after observing SP_STATUS.HALT, so both producer and DP can be checked
        # at a deterministic between-frame boundary rather than a timed host poll.
        set_breakpoint(client, args.capture_ready_address, True)
        validate_stop(client.request("c"), "E2b clean-epoch breakpoint")
        anchor = read_quiescent_state(client)
        validate_quiescent_state(anchor, require_marker=True)

        # Create the clean epoch only now, between frames with the RSP halted.
        initialize_proof_memory(client)
        baseline_counter = read_u(client, args.guest_counter_address, 1)

        # Step over the breakpoint once, reinstall it behind the PC, and let one
        # complete subsequent RSP frame reach the same quiescent boundary.
        set_breakpoint(client, args.capture_ready_address, False)
        validate_stop(client.request("s"), "E2b breakpoint step-over")
        set_breakpoint(client, args.capture_ready_address, True)
        validate_stop(client.request("c"), "E2b fenced capture breakpoint")

        quiescent = read_quiescent_state(client)
        validate_quiescent_state(quiescent, require_marker=True)
        counter = read_u(client, args.guest_counter_address, 1)
        delta = (counter - baseline_counter) & 0xFF
        if delta < 1:
            raise RuntimeError(
                "capture breakpoint did not include a fresh guest frame: "
                f"baseline=0x{baseline_counter:02X} current=0x{counter:02X}"
            )

        state = {
            "attempt": 1,
            "guest_counter": counter,
            "status": quiescent["status"],
            "counter_delta": delta,
            "warmup_counter": warmup["guest_counter"],
            "baseline_counter": baseline_counter,
            "sp_status": quiescent["sp_status"],
            "dp_status": quiescent["dp_status"],
        }

        fb_pointer = quiescent["proof_framebuffer_pointer"]
        display_fb_pointer = read_u(client, args.framebuffer_address, 4)
        framebuffer = client.read_memory(fb_pointer, FB_BYTES, 0x400)
        second_z = client.read_memory(
            E2G_SECOND_Z_ADDR, E1C_Z_SCRATCH_SIZE, 0x400
        )
        second_z_prefix = client.read_memory(
            E2G_SECOND_Z_PREFIX_ADDR, E1C_GUARD_SIZE, E1C_GUARD_SIZE
        )
        second_z_suffix = client.read_memory(
            E2G_SECOND_Z_SUFFIX_ADDR, E1C_GUARD_SIZE, E1C_GUARD_SIZE
        )
        final_b = client.read_memory(
            E1C_Z_SCRATCH_ADDR, E1C_Z_SCRATCH_SIZE, 0x400
        )
        prefix_guard = client.read_memory(
            E1C_PREFIX_GUARD_ADDR, E1C_GUARD_SIZE, E1C_GUARD_SIZE
        )
        suffix_guard = client.read_memory(
            E1C_SUFFIX_GUARD_ADDR, E1C_GUARD_SIZE, E1C_GUARD_SIZE
        )
        color_archive_a = client.read_memory(
            E2A_COLOR_ARCHIVE_A_ADDR, E2A_COLOR_SCRATCH_SIZE, 0x400
        )
        color_final_b = client.read_memory(
            E2A_COLOR_SCRATCH_ADDR, E2A_COLOR_SCRATCH_SIZE, 0x400
        )
        color_prefix_guard = client.read_memory(
            E2A_COLOR_PREFIX_GUARD_ADDR, E1C_GUARD_SIZE, E1C_GUARD_SIZE
        )
        color_suffix_guard = client.read_memory(
            E2A_COLOR_SUFFIX_GUARD_ADDR, E1C_GUARD_SIZE, E1C_GUARD_SIZE
        )
        main_before = client.read_memory(
            E2A_MAIN_BEFORE_ADDR, E2A_COLOR_SCRATCH_SIZE, 0x400
        )
        main_after = client.read_memory(
            E2A_MAIN_AFTER_ADDR, E2A_COLOR_SCRATCH_SIZE, 0x400
        )
        section_queue1 = client.read_memory(
            SECTION_QUEUE1_ADDR, SECTION_CAPTURE_SIZE, 0x400
        )
        section_queue2 = client.read_memory(
            SECTION_QUEUE2_ADDR, SECTION_CAPTURE_SIZE, 0x400
        )

        (out / "framebuffer.rgba5551").write_bytes(framebuffer)
        (out / "z_second_candidate.bin").write_bytes(second_z)
        (out / "z_second_prefix_guard.bin").write_bytes(second_z_prefix)
        (out / "z_second_suffix_guard.bin").write_bytes(second_z_suffix)
        (out / "z_final_b.bin").write_bytes(final_b)
        (out / "z_prefix_guard.bin").write_bytes(prefix_guard)
        (out / "z_suffix_guard.bin").write_bytes(suffix_guard)
        (out / "color_archive_a.bin").write_bytes(color_archive_a)
        (out / "color_final_b.bin").write_bytes(color_final_b)
        (out / "color_prefix_guard.bin").write_bytes(color_prefix_guard)
        (out / "color_suffix_guard.bin").write_bytes(color_suffix_guard)
        (out / "main_before.bin").write_bytes(main_before)
        (out / "main_after.bin").write_bytes(main_after)
        (out / "section_queue1.bin").write_bytes(section_queue1)
        (out / "section_queue2.bin").write_bytes(section_queue2)

        # E4b authority encodes the already-precommitted corrected-row
        # same-band oracle. Runtime, guest, targets and capture timing are frozen.
        result = classify_e4b_same_band_row_correct(
            section_queue1,
            section_queue2,
            color_final_b,
            color_prefix_guard,
            color_suffix_guard,
            framebuffer,
            final_b,
            prefix_guard,
            suffix_guard,
            second_z,
            second_z_prefix,
            second_z_suffix,
        )
        result["capture_state"] = {
            **state,
            "framebuffer_pointer": hex(fb_pointer),
            "display_framebuffer_pointer": hex(display_fb_pointer),
            "capture_ready_address": hex(args.capture_ready_address),
        }
        (out / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        if not result["passed"]:
            raise RuntimeError("E4b row-correct same-band classifier failed; see result.json")

        try:
            client.request("D")
        except Exception:
            pass
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
