"""Live demo launcher: open Webots with rendering for a mission and a method.

Module: demo.py
Owner: M4
Inputs:  a scenario id (E1, E2, ...) OR your own target points, and the method.
Outputs: a visible Webots window flying the mission; telemetry is still written to
         results/demo/<name>_<method>/ and the metrics are printed at the end.

Examples:
    python experiments/demo.py E2 improved
    python experiments/demo.py E4 baseline                 # square mission in wind
    python experiments/demo.py --points "0,0,1.5  2,1,2  -1,2,1  0,0,1" improved
    python experiments/demo.py --points "0,0,2,0  3,0,2,1.57" baseline --wind 0.3

Each point is x,y,z (metres, world frame) with an optional 4th value: the heading
(yaw, radians; 0 = facing +x, 1.57 = facing +y). The drone takes off from (0, 0) and
flies to the points in order. Keep points within about 10 m of the start; the
altitude should stay between 0.5 m and 5 m.
"""

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from experiments.run_experiments import WEBOTS_EXE, load_scenarios  # noqa: E402

MIN_ALT, MAX_ALT = 0.5, 5.0


def parse_points(text: str):
    """'x,y,z[,yaw] x,y,z ...' -> [[x, y, z, yaw], ...] with basic sanity checks."""
    points = []
    for token in text.split():
        values = [float(v) for v in token.split(",")]
        if len(values) not in (3, 4):
            raise ValueError(f"point '{token}' needs 3 or 4 numbers: x,y,z[,yaw]")
        if not MIN_ALT <= values[2] <= MAX_ALT:
            raise ValueError(f"altitude {values[2]} m outside {MIN_ALT}-{MAX_ALT} m")
        points.append(values if len(values) == 4 else values + [0.0])
    if not points:
        raise ValueError("no points given")
    return points


def custom_scenario(points, wind: float):
    n = len(points)
    return {"scenario_id": "CUSTOM", "name": f"Your mission ({n} points)",
            "world": "worlds/wind.wbt" if wind else "worlds/square.wbt",
            "sim_duration_s": 20.0 + 12.0 * n, "target_precision_m": 0.2,
            "waypoints": points, "wind_force": [0.0, wind, 0.0], "wind_start_s": 8.0}


def main() -> None:
    ap = argparse.ArgumentParser(description="Open a visible Webots demo run")
    ap.add_argument("args", nargs="+", help="[SCENARIO] METHOD, e.g. 'E2 improved'")
    ap.add_argument("--points", help='your own targets, e.g. "0,0,1.5 2,1,2 0,0,1"')
    ap.add_argument("--wind", type=float, default=0.0, help="crosswind in N (with --points)")
    ap.add_argument("--fast", action="store_true", help="run faster than real time")
    a = ap.parse_args()

    method = a.args[-1]
    if method not in ("baseline", "improved"):
        ap.error("the last argument must be 'baseline' or 'improved'")
    if a.points:
        sc = custom_scenario(parse_points(a.points), a.wind)
    else:
        if len(a.args) != 2:
            ap.error("give a scenario id (e.g. E2) or --points")
        sc = copy.deepcopy(load_scenarios([a.args[0]])[0])
        sc.pop("seeds", None)
        sc.pop("sweep", None)
    out_rel = f"results/demo/{sc['scenario_id']}_{method}"
    sc.update({"method": method, "seed": 0, "screenshots": True, "output_dir": out_rel})
    with open(os.path.join(REPO, "current_scenario.json"), "w", encoding="utf-8") as f:
        json.dump(sc, f, indent=2)

    label = "A (baseline)" if method == "baseline" else "B (improved)"
    print(f"Opening Webots: {sc['name']} with Method {label}")
    for i, p in enumerate(sc["waypoints"], 1):
        print(f"  point {i}: x={p[0]:+.2f} y={p[1]:+.2f} z={p[2]:.2f} yaw={p[3]:+.2f}")
    tele = os.path.join(REPO, out_rel, "telemetry.csv")
    if os.path.exists(tele):
        os.remove(tele)
    # Open a throwaway copy of the world: if someone presses Save in the Webots GUI,
    # only the copy is overwritten and the experiment worlds stay clean.
    src = os.path.join(REPO, sc["world"])
    world = os.path.join(os.path.dirname(src), "_demo_" + os.path.basename(src))
    shutil.copyfile(src, world)
    mode = "--mode=fast" if a.fast else "--mode=realtime"
    proc = subprocess.Popen([WEBOTS_EXE, mode, world], cwd=REPO)

    # When the run ends the controller writes its telemetry; print the result then.
    while not os.path.exists(tele) and proc.poll() is None:
        time.sleep(1.0)
    if os.path.exists(tele):
        time.sleep(1.0)
        from analysis.metrics import load_run
        m = load_run(os.path.join(REPO, out_rel)) or {}
        print(f"Result: success={m.get('success')}  waypoints reached="
              f"{m.get('waypoints_reached')}/{len(sc['waypoints'])}  "
              f"path RMSE={m.get('path_rmse_m', float('nan')):.3f} m  "
              f"mission time={m.get('mission_time_s', float('nan')):.1f} s")


if __name__ == "__main__":
    main()
