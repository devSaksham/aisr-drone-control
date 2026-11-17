"""Webots controller entry point for the Mavic 2 Pro.

Module: drone_main.py
Owner: M4
Inputs:  scenario from current_scenario.json (see drone_ctrl/config.py).
Outputs: motor commands every step; telemetry CSV + config snapshot at the end.

Loop: read sensors -> estimate state -> controller.step() -> set motor speeds -> log.
The run ends at `sim_duration_s` (the wind supervisor then quits Webots).
"""

import os
import sys

WEBOTS_HOME = os.environ.get("WEBOTS_HOME", "C:/Program Files/Webots")
_lib = os.path.join(WEBOTS_HOME, "lib", "controller", "python")
if os.path.isdir(_lib) and _lib not in sys.path:
    sys.path.append(_lib)
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from controller import Robot  # noqa: E402
from drone_ctrl.baseline import BaselineController  # noqa: E402
from drone_ctrl.config import (BaselineGains, ImprovedGains, PhysicalParams,  # noqa: E402
                               apply_overrides, load_scenario, snapshot)
from drone_ctrl.improved import ImprovedController  # noqa: E402
from drone_ctrl.logger import TelemetryLogger  # noqa: E402
from drone_ctrl.sensors import DroneSensors  # noqa: E402

MOTOR_NAMES = ["front left propeller", "front right propeller",
               "rear left propeller", "rear right propeller"]


def build_controller(scenario, params):
    """Create the controller selected by scenario.method, with any gain overrides."""
    if scenario.method.lower() == "baseline":
        gains = apply_overrides(BaselineGains(), scenario.gains.get("baseline", {}))
        return BaselineController(scenario.waypoints, gains, params,
                                  scenario.target_precision_m, scenario.switch_times), gains
    gains = apply_overrides(ImprovedGains(), scenario.gains.get("improved", {}))
    return ImprovedController(scenario.waypoints, gains, params,
                              scenario.target_precision_m, scenario.switch_times), gains


def main() -> None:
    robot = Robot()
    step_ms = int(robot.getBasicTimeStep())
    dt = step_ms / 1000.0
    scenario = load_scenario(REPO_ROOT)
    params = PhysicalParams()
    controller, gains = build_controller(scenario, params)
    sensors = DroneSensors(robot, step_ms, scenario.gps_noise_std, scenario.imu_noise_std,
                           scenario.seed)
    out_dir = os.path.join(REPO_ROOT, scenario.output_dir)
    logger = TelemetryLogger(out_dir)

    motors = [robot.getDevice(name) for name in MOTOR_NAMES]
    for m in motors:
        m.setPosition(float("inf"))
        m.setVelocity(1.0)

    try:
        while robot.step(step_ms) != -1:
            t = robot.getTime()
            state = sensors.read()
            if state is None:
                continue
            out = controller.step(state, t, dt)
            for m, w in zip(motors, out.motors):
                m.setVelocity(w)
            logger.log(t, state, sensors.gps.getValues(), out)
            # Progress shown on screen by the supervisor (Robot.customData field).
            n_wp = len(scenario.waypoints)
            robot.setCustomData("done" if out.finished else f"{out.wp_index + 1}/{n_wp}")
            if t >= scenario.sim_duration_s:
                break
    finally:
        path = logger.flush(snapshot(scenario, gains, params))
        print(f"[drone_main] {scenario.scenario_id}/{scenario.method}: "
              f"{len(logger.rows)} rows -> {path}")


if __name__ == "__main__":
    main()
