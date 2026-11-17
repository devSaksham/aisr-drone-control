"""Analyse the sign-convention probe run.

Module: analyse_probe.py
Owner: M1
Input: results/probe/probe.csv written by controllers/sign_probe/sign_probe.py
Output: printed table of measured responses (used in docs/frames.md)

Run:  webots --mode=fast --batch --no-rendering --minimize worlds/probe.wbt
      python experiments/analyse_probe.py
"""

import os
import sys

import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_CSV = os.path.join(REPO, "results", "probe", "probe.csv")

# Same windows as PHASES in sign_probe.py: (label, start, end)
WINDOWS = [("roll offset +1", 8.0, 9.0), ("pitch offset +1", 13.0, 14.0),
           ("yaw offset +0.3", 18.0, 19.0)]
SETTLE_S = 1.5   # extra time after the offset to let the motion show up
DRIFT_WINDOW = (5.5, 8.0)  # undisturbed hover used to estimate background drift


def nearest(d: pd.DataFrame, t: float) -> pd.Series:
    return d.iloc[(d.t - t).abs().argmin()]


def analyse(csv_path: str = DEFAULT_CSV) -> pd.DataFrame:
    d = pd.read_csv(csv_path)
    a, b = DRIFT_WINDOW
    s, e = nearest(d, a), nearest(d, b)
    drift_vx, drift_vy = (e.x - s.x) / (b - a), (e.y - s.y) / (b - a)
    rows = []
    for label, t0, t1 in WINDOWS:
        win = d[(d.t >= t0) & (d.t < t1)]
        s, e = nearest(d, t0), nearest(d, t1 + SETTLE_S)
        span = (t1 + SETTLE_S) - t0
        rows.append({
            "test": label,
            "peak_roll_rad": win.roll.iloc[win.roll.abs().argmax()],
            "peak_pitch_rad": win.pitch.iloc[win.pitch.abs().argmax()],
            "mean_yaw_rate": win.wz.mean(),
            "dx_minus_drift_m": (e.x - s.x) - drift_vx * span,
            "dy_minus_drift_m": (e.y - s.y) - drift_vy * span,
            "dyaw_rad": e.yaw - s.yaw,
        })
    out = pd.DataFrame(rows)
    print(f"background hover drift: vx={drift_vx:+.3f} m/s, vy={drift_vy:+.3f} m/s")
    print(out.round(3).to_string(index=False))
    return out


if __name__ == "__main__":
    analyse(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV)
