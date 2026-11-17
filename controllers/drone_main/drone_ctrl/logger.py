"""Telemetry logging.

Module: logger.py
Owner: M1
Inputs:  per-step time, estimated state, true GPS position, controller output.
Outputs: <output_dir>/telemetry.csv and <output_dir>/config_snapshot.json.
Tests:   tests/test_logger.py

Rows are buffered in memory and written once at the end of the run so that file I/O
does not slow the 8 ms control loop.
"""

import csv
import json
import os
from typing import Any, Dict, List, Sequence

COLUMNS = [
    "time", "x", "y", "z", "vx", "vy", "vz", "roll", "pitch", "yaw", "p", "q", "r",
    "true_x", "true_y", "true_z",
    "ref_x", "ref_y", "ref_z", "ref_yaw", "wp_x", "wp_y", "wp_z", "wp_index", "finished",
    "roll_ref", "pitch_ref", "m_fl", "m_fr", "m_rl", "m_rr",
]


class TelemetryLogger:
    """Collects telemetry rows and writes them as CSV."""

    def __init__(self, output_dir: str, filename: str = "telemetry.csv") -> None:
        self.output_dir = output_dir
        self.path = os.path.join(output_dir, filename)
        self.rows: List[List[float]] = []

    def log(self, t: float, state: Any, true_xyz: Sequence[float], out: Any) -> None:
        self.rows.append([
            t, state.x, state.y, state.z, state.vx, state.vy, state.vz,
            state.roll, state.pitch, state.yaw, state.p, state.q, state.r,
            true_xyz[0], true_xyz[1], true_xyz[2],
            *out.ref_pos[:4], *out.waypoint[:3], out.wp_index, int(out.finished),
            out.roll_ref, out.pitch_ref, *[abs(m) for m in out.motors],
        ])

    def flush(self, snapshot: Dict[str, Any]) -> str:
        os.makedirs(self.output_dir, exist_ok=True)
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)
            writer.writerows(self.rows)
        with open(os.path.join(self.output_dir, "config_snapshot.json"), "w",
                  encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)
        return self.path
