"""Performance metrics computed from telemetry CSVs.

Module: metrics.py
Owner: M5
Inputs:  results/<scenario>/<method>/seed_<n>/telemetry.csv and config_snapshot.json.
Outputs: dict of metrics per run; results/summary.csv for many runs.
Tests:   tests/test_metrics.py

All position metrics use the TRUE position (`true_x/y/z`, the GPS reading before any
injected noise), so a noisy estimate cannot make a run look better than it was.

Definitions
- crashed:        tilt above 60 deg, or true z < 0.15 m after having flown above 0.5 m.
- success:        not crashed and every waypoint reached (mission finished).
- step metrics:   per altitude step (timed waypoints): rise time 10-90 %, overshoot in %
                  of the step size, settling time into a +/-2 % band (min 2 cm) that is
                  never left again, steady-state error = mean |e| over the last 2 s.
- path RMSE:      RMS 3D distance from the true position to the straight-line polyline
                  through the waypoints, from first waypoint reached until finish.
- mission time:   time at which the last waypoint was reached.
- max tilt:       max of acos(cos(roll) cos(pitch)) once airborne, in degrees.
- control effort: mean over time of sum_i (w_i - w_hover)^2, in (rad/s)^2.
"""

import json
import math
import os
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

HOVER_SPEED = 68.5
CRASH_TILT_DEG = 60.0
SETTLE_BAND = 0.02
MIN_BAND_M = 0.02
SS_WINDOW_S = 2.0


def tilt_deg(df: pd.DataFrame) -> np.ndarray:
    c = np.clip(np.cos(df.roll.values) * np.cos(df.pitch.values), -1.0, 1.0)
    return np.degrees(np.arccos(c))


def crash_info(df: pd.DataFrame) -> Dict[str, Any]:
    tilt = tilt_deg(df)
    flown = np.maximum.accumulate(df.true_z.values) > 0.5
    low = flown & (df.true_z.values < 0.15)
    bad = (tilt > CRASH_TILT_DEG) | low
    idx = int(np.argmax(bad)) if bad.any() else None
    return {"crashed": bool(bad.any()),
            "crash_time_s": float(df.time.values[idx]) if idx is not None else math.nan}


def step_metrics(t: np.ndarray, y: np.ndarray, y0: float, y1: float) -> Dict[str, float]:
    """Classic step-response metrics for one segment that starts at t[0]."""
    step = y1 - y0
    out = {"rise_time_s": math.nan, "overshoot_pct": math.nan,
           "settling_time_s": math.nan, "ss_error_m": math.nan}
    if len(t) < 2 or abs(step) < 1e-6:
        return out
    frac = (y - y0) / step
    t10 = t[np.argmax(frac >= 0.1)] if (frac >= 0.1).any() else math.nan
    t90 = t[np.argmax(frac >= 0.9)] if (frac >= 0.9).any() else math.nan
    out["rise_time_s"] = float(t90 - t10)
    out["overshoot_pct"] = float(max(0.0, (frac.max() - 1.0) * 100.0))
    band = max(SETTLE_BAND * abs(step), MIN_BAND_M)
    outside = np.abs(y - y1) > band
    if not outside[-1]:
        last_out = np.where(outside)[0]
        k = last_out[-1] + 1 if len(last_out) else 0
        out["settling_time_s"] = float(t[k] - t[0])
    tail = t >= t[-1] - SS_WINDOW_S
    out["ss_error_m"] = float(np.mean(np.abs(y[tail] - y1)))
    return out


def point_to_segment(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Distance from each row of p (N x 3) to segment a-b."""
    ab = b - a
    denom = float(ab @ ab)
    if denom < 1e-12:
        return np.linalg.norm(p - a, axis=1)
    s = np.clip((p - a) @ ab / denom, 0.0, 1.0)
    return np.linalg.norm(p - (a + np.outer(s, ab)), axis=1)


def cross_track(p: np.ndarray, waypoints: Sequence[Sequence[float]]) -> np.ndarray:
    wp = np.asarray([w[:3] for w in waypoints], dtype=float)
    if len(wp) == 1:
        return np.linalg.norm(p - wp[0], axis=1)
    d = np.stack([point_to_segment(p, wp[i], wp[i + 1]) for i in range(len(wp) - 1)])
    return d.min(axis=0)


def reach_times(df: pd.DataFrame) -> List[float]:
    """Times at which wp_index advanced, plus the finish time if reached."""
    idx = df.wp_index.values
    times = [float(df.time.values[i]) for i in range(1, len(idx)) if idx[i] > idx[i - 1]]
    if df.finished.values.any():
        times.append(float(df.time.values[np.argmax(df.finished.values > 0)]))
    return times


def evaluate(df: pd.DataFrame, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compute every metric for one run."""
    sc = cfg["scenario"]
    m: Dict[str, Any] = {"scenario": sc["scenario_id"], "method": sc["method"],
                         "seed": sc["seed"], "duration_s": float(df.time.values[-1])}
    m.update(crash_info(df))
    airborne = np.maximum.accumulate(df.true_z.values) > 0.3
    m["max_tilt_deg"] = float(tilt_deg(df)[airborne].max()) if airborne.any() else 0.0
    motors = df[["m_fl", "m_fr", "m_rl", "m_rr"]].values
    m["control_effort"] = float(np.mean(np.sum((motors - HOVER_SPEED) ** 2, axis=1)))
    pos = df[["true_x", "true_y", "true_z"]].values
    wps = sc["waypoints"]

    if sc.get("switch_times"):  # timed altitude steps (E1)
        switch = list(sc["switch_times"]) + [m["duration_s"] + 1e-9]
        prev = 0.1  # resting height on the ground
        for i, wp in enumerate(wps):
            seg = (df.time.values >= switch[i]) & (df.time.values < switch[i + 1])
            sm = step_metrics(df.time.values[seg], df.true_z.values[seg], prev, wp[2])
            for k, v in sm.items():
                m[f"step{i + 1}_{k}"] = v
            prev = wp[2]
        m["success"] = not m["crashed"]
        return m

    times = reach_times(df)
    m["waypoints_reached"] = len(times)
    m["mission_time_s"] = times[-1] if len(times) == len(wps) else math.nan
    m["success"] = (not m["crashed"]) and len(times) == len(wps)
    start = times[0] if times else 0.0
    end = m["mission_time_s"] if m["success"] else m["duration_s"]
    window = (df.time.values >= start) & (df.time.values <= end)
    ct = cross_track(pos[window], wps) if window.any() else np.array([math.nan])
    m["path_rmse_m"] = float(np.sqrt(np.mean(ct ** 2)))
    m["path_max_err_m"] = float(np.max(ct))
    return m


def load_run(run_dir: str) -> Optional[Dict[str, Any]]:
    tele = os.path.join(run_dir, "telemetry.csv")
    snap = os.path.join(run_dir, "config_snapshot.json")
    if not (os.path.exists(tele) and os.path.exists(snap)):
        return None
    with open(snap, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return evaluate(pd.read_csv(tele), cfg)


def summarise_runs(run_dirs: Sequence[str], out_csv: str, repo: str = ".") -> pd.DataFrame:
    rows = []
    for d in run_dirs:
        r = load_run(d if os.path.isabs(d) else os.path.join(repo, d))
        if r is None:
            print(f"  missing telemetry: {d}")
            continue
        r["run_dir"] = d.replace("\\", "/")
        rows.append(r)
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"  summary of {len(df)} runs -> {out_csv}")
    return df
