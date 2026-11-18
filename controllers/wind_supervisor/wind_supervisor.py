"""Supervisor: wind disturbance, crash watchdog, screenshots and run termination.

Module: wind_supervisor.py
Owner: M4
Inputs:  scenario from current_scenario.json (wind_force, gust settings, duration).
Outputs: external force on the DRONE node every step; waypoint markers and an
         on-screen status line for demos; optional screenshots;
         simulationQuit() at the end of the run or after a crash.

Wind model (world frame, applied at the drone's centre of mass with addForce):
    F(t) = F_const * (1 + (A / |F_const|) * sin(2*pi*t / T_gust))   for t in [t_start, t_end]
i.e. a constant force plus a sinusoidal gust of amplitude A along the same direction.
The Mavic itself is not a supervisor; this separate robot owns the privileged calls.
"""

import json
import math
import os
import sys

WEBOTS_HOME = os.environ.get("WEBOTS_HOME", "C:/Program Files/Webots")
_lib = os.path.join(WEBOTS_HOME, "lib", "controller", "python")
if os.path.isdir(_lib) and _lib not in sys.path:
    sys.path.append(_lib)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

from controller import Supervisor  # noqa: E402

CRASH_COS_TILT = 0.5     # body z-axis below 60 deg from vertical counts as crashed
CRASH_HOLD_S = 1.0       # must stay crashed this long before the run is cut short
SCREENSHOT_TIMES = (3.0, 10.0)


def load_cfg() -> dict:
    env = os.environ.get("DRONE_SCENARIO_JSON")
    if env:
        return json.loads(env)
    path = os.path.join(REPO_ROOT, "current_scenario.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def wind_at(t: float, cfg: dict) -> list:
    force = [float(v) for v in cfg.get("wind_force", [0.0, 0.0, 0.0])]
    if not cfg.get("wind_start_s", 0.0) <= t <= cfg.get("wind_end_s", 1e9):
        return [0.0, 0.0, 0.0]
    mag = math.sqrt(sum(f * f for f in force))
    amp = float(cfg.get("gust_amplitude", 0.0))
    if mag > 0 and amp:
        scale = 1.0 + (amp / mag) * math.sin(2 * math.pi * t / cfg.get("gust_period_s", 4.0))
        force = [f * scale for f in force]
    return force


MARKER = ('Pose {{ translation {x} {y} {z} children [ Shape {{ appearance PBRAppearance {{ '
          'baseColor {c} roughness 1 metalness 0 transparency 0.3 }} geometry Sphere {{ '
          'radius 0.07 subdivision 2 }} }} ] }}')
LABEL_COLOR = 0xFFFFFF
METHOD_NAMES = {"baseline": "Method A (baseline P/PD, step waypoints)",
                "improved": "Method B (PID + min-jerk trajectory)"}


def draw_waypoints(sup: Supervisor, waypoints: list) -> None:
    """Add a small sphere at each waypoint (green = first, red = others) for the demo view."""
    children = sup.getRoot().getField("children")
    for i, wp in enumerate(waypoints):
        colour = "0.1 0.8 0.2" if i == 0 else "0.9 0.2 0.2"
        children.importMFNodeFromString(-1, MARKER.format(x=wp[0], y=wp[1], z=wp[2], c=colour))


def show_status(sup: Supervisor, cfg: dict, t: float, drone, force: list) -> None:
    """Three on-screen text lines: what is flying, where it is, which waypoint/wind."""
    name = METHOD_NAMES.get(cfg.get("method", ""), cfg.get("method", ""))
    sup.setLabel(0, f"{cfg.get('scenario_id', '')}: {cfg.get('name', '')}  |  {name}",
                 0.01, 0.01, 0.07, LABEL_COLOR, 0.0, "Arial")
    if drone is None:
        return
    x, y, z = drone.getPosition()
    progress = drone.getField("customData").getSFString() or "-"
    sup.setLabel(1, f"t = {t:5.1f} s   position x={x:+.2f}  y={y:+.2f}  z={z:.2f} m   "
                    f"waypoint {progress}", 0.01, 0.05, 0.07, LABEL_COLOR, 0.0, "Arial")
    wind = f"wind force = ({force[0]:+.1f}, {force[1]:+.1f}) N" if any(force) else "no wind"
    sup.setLabel(2, wind, 0.01, 0.09, 0.07, LABEL_COLOR, 0.0, "Arial")


def main() -> None:
    sup = Supervisor()
    step_ms = int(sup.getBasicTimeStep())
    cfg = load_cfg()
    duration = float(cfg.get("sim_duration_s", 30.0))
    drone = sup.getFromDef("DRONE")
    draw_waypoints(sup, cfg.get("waypoints", []))
    shot_dir = os.path.join(REPO_ROOT, cfg.get("output_dir", "results/demo"), "screenshots")
    shots = list(SCREENSHOT_TIMES) if cfg.get("screenshots") else []
    crashed_for = 0.0
    movie = cfg.get("record")
    if movie:
        sup.movieStartRecording(movie, 1280, 720, 0, 90, 1, False)

    while sup.step(step_ms) != -1:
        t = sup.getTime()
        force = wind_at(t, cfg)
        if drone is not None and any(force):
            drone.addForce(force, False)
        show_status(sup, cfg, t, drone, force)
        if drone is not None:
            body_z_up = drone.getOrientation()[8]  # R[2][2]: cos of tilt
            crashed_for = crashed_for + step_ms / 1000.0 if body_z_up < CRASH_COS_TILT else 0.0
        if shots and t >= shots[0]:
            os.makedirs(shot_dir, exist_ok=True)
            sup.exportImage(os.path.join(shot_dir, f"t{shots.pop(0):04.1f}s.png"), 90)
        if movie and (crashed_for >= CRASH_HOLD_S or t >= duration):
            sup.movieStopRecording()
            while not sup.movieIsReady():
                sup.step(0)
            movie = None
        if crashed_for >= CRASH_HOLD_S:
            print(f"[wind_supervisor] drone crashed at t={t:.2f}s, ending run")
            sup.simulationQuit(0)
            break
        if t >= duration + 0.1:
            sup.simulationQuit(0)
            break


if __name__ == "__main__":
    main()
