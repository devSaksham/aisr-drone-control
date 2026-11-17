"""Tests for analysis/metrics.py (owner: M5)."""
import numpy as np
import pandas as pd

from analysis.metrics import crash_info, cross_track, step_metrics


def test_first_order_step_has_no_overshoot():
    t = np.linspace(0, 10, 1001)
    m = step_metrics(t, 1 - np.exp(-t), 0.0, 1.0)
    assert m["overshoot_pct"] == 0
    assert abs(m["rise_time_s"] - np.log(9)) < 0.02  # 10-90 % of 1-exp(-t) is ln 9
    assert m["ss_error_m"] < 0.01


def test_overshoot_measured():
    t = np.linspace(0, 10, 1001)
    y = 1 - np.exp(-0.5 * t) * np.cos(2 * t)
    assert step_metrics(t, y, 0.0, 1.0)["overshoot_pct"] > 10


def test_downward_step():
    t = np.linspace(0, 10, 1001)
    m = step_metrics(t, 1 + np.exp(-t), 2.0, 1.0)
    assert m["overshoot_pct"] == 0 and m["ss_error_m"] < 0.01


def test_cross_track_distance():
    p = np.array([[1.0, 0.5, 1.0], [3.0, 0.0, 1.0]])
    assert np.allclose(cross_track(p, [[0, 0, 1], [2, 0, 1]]), [0.5, 1.0])


def test_crash_detection():
    df = pd.DataFrame({"time": [0, 1, 2], "roll": [0, 0, 2.0], "pitch": [0, 0, 0],
                       "true_z": [0.1, 1.0, 0.1]})
    info = crash_info(df)
    assert info["crashed"] and info["crash_time_s"] == 2
