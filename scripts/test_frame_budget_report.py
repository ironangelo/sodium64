#!/usr/bin/env python3
"""Host-side tests for frame-budget observation reporting."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import frame_budget_report  # noqa: E402


class FrameBudgetReportTests(unittest.TestCase):
    def make_state(self, **overrides: int) -> Path:
        observations = {
            "fps_display": 60,
            "fps_native": 17,
            "fps_emulate": 17,
            "frame_count": 1,
            "skipped_set": 0,
            "apu_clock": 21,
            "audio_set": 4,
            "precision_set": 8,
        }
        observations.update(overrides)
        handle = tempfile.NamedTemporaryFile(
            "w", suffix="-state.json", delete=False, encoding="utf-8"
        )
        json.dump(
            {"measured_wall_seconds": 3.0, "observations": observations},
            handle,
        )
        handle.close()
        path = Path(handle.name)
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        return path

    def test_valid_full_rate_state(self) -> None:
        row = frame_budget_report.load_budget_row(self.make_state(), 60)
        self.assertEqual(row.fps_display, 60)
        self.assertEqual(row.cadence_status, "at/above virtual target")
        self.assertEqual(row.full_interval_percent, 100.0)

    def test_below_target_is_evidence_not_invalid_measurement(self) -> None:
        row = frame_budget_report.load_budget_row(self.make_state(fps_display=37), 60)
        self.assertEqual(row.cadence_status, "below virtual target")
        self.assertAlmostEqual(row.full_interval_percent, 61.6666667)

    def test_frameskip_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "frameskip must be disabled"):
            frame_budget_report.load_budget_row(self.make_state(skipped_set=4), 60)

    def test_underclock_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "APU must run at full rate"):
            frame_budget_report.load_budget_row(self.make_state(apu_clock=42), 60)

    def test_audio_off_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "audio is disabled"):
            frame_budget_report.load_budget_row(self.make_state(audio_set=0), 60)

    def test_sentinel_requires_complete_vi_window(self) -> None:
        with self.assertRaisesRegex(ValueError, "no complete 60-VI budget window"):
            frame_budget_report.load_budget_row(self.make_state(fps_display=0xFF), 60)


if __name__ == "__main__":
    unittest.main(verbosity=2)
