"""Tests for logger.py (owner: M1)."""
import csv
import json
from types import SimpleNamespace

from drone_ctrl.logger import COLUMNS, TelemetryLogger
from drone_ctrl.sensors import DroneState


def test_writes_csv_and_snapshot(tmp_path):
    log = TelemetryLogger(str(tmp_path))
    out = SimpleNamespace(ref_pos=[0, 0, 1, 0], waypoint=[0, 0, 1, 0], wp_index=0,
                          finished=False, roll_ref=0.0, pitch_ref=0.0,
                          motors=[68.5, -68.5, -68.5, 68.5])
    log.log(0.008, DroneState(z=1.0), [0, 0, 1], out)
    log.flush({"a": 1})
    with open(tmp_path / "telemetry.csv") as f:
        rows = list(csv.reader(f))
    assert rows[0] == COLUMNS and len(rows) == 2 and len(rows[1]) == len(COLUMNS)
    assert float(rows[1][COLUMNS.index("m_fr")]) == 68.5  # magnitudes are logged
    with open(tmp_path / "config_snapshot.json") as f:
        assert json.load(f) == {"a": 1}
