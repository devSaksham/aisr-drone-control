"""Parameters and scenario loading.

Module: config.py
Owner: M1
Inputs:  `current_scenario.json` in the repo root (written by experiments/run_experiments.py)
         or the DRONE_SCENARIO_JSON environment variable.
Outputs: PhysicalParams, BaselineGains, ImprovedGains, ScenarioConfig dataclasses.
Tests:   tests/test_config.py

All tunable numbers live here; no other module hard-codes a gain. Gains can be
overridden per run through the scenario's `gains` dictionary (used by the tuning
and sensitivity scripts), e.g. {"baseline": {"pos_kp": 0.8}}.
"""

import json
import os
from dataclasses import asdict, dataclass, field, fields
from typing import Any, Dict, List


@dataclass
class PhysicalParams:
    """Mavic 2 Pro values from the Webots PROTO and sample controller (docs/frames.md)."""
    hover_speed: float = 68.5      # rad/s, empirical hover rotor speed (sample)
    max_motor_speed: float = 576.0  # rad/s, PROTO maxVelocity
    takeoff_alt: float = 0.3       # m, horizontal loops engage above this height


@dataclass
class BaselineGains:
    """Method A: P/PD loops, step waypoints, no integral, no feedforward."""
    alt_kp: float = 12.0
    alt_kd: float = 8.0
    alt_max: float = 10.0
    roll_kp: float = 25.0
    roll_kd: float = 4.0
    pitch_kp: float = 30.0
    pitch_kd: float = 2.5
    att_max: float = 40.0
    pos_kp: float = 1.0
    pos_kd: float = 1.2
    max_tilt: float = 0.15
    yaw_kp: float = 0.5
    yaw_max: float = 1.0
    wp_hold_s: float = 0.5


@dataclass
class ImprovedGains:
    """Method B: PID + anti-windup, min-jerk trajectory, velocity cascade, feedforward."""
    alt_kp: float = 16.0
    alt_ki: float = 4.0
    alt_kd: float = 10.0
    alt_int_limit: float = 5.0
    alt_d_alpha: float = 0.5
    alt_max: float = 15.0
    roll_kp: float = 25.0
    roll_kd: float = 4.0
    pitch_kp: float = 30.0
    pitch_kd: float = 2.5
    att_max: float = 40.0
    pos_kp: float = 1.2
    vel_kp: float = 2.0
    vel_ki: float = 0.5
    vel_int_limit: float = 2.0
    max_speed: float = 1.5
    max_tilt: float = 0.15
    traj_max_vel: float = 1.2
    traj_max_acc: float = 1.0
    traj_min_time: float = 1.0
    yaw_kp: float = 0.8
    yaw_kd: float = 0.3
    yaw_max: float = 1.0
    wp_hold_s: float = 0.5
    takeoff_boost: float = 6.0  # rad/s above hover while spooling up on the ground


@dataclass
class ScenarioConfig:
    """One simulation run."""
    scenario_id: str = "DEMO"
    name: str = "Interactive demo"
    method: str = "improved"           # "baseline" or "improved"
    seed: int = 0
    sim_duration_s: float = 30.0
    output_dir: str = "results/demo"
    waypoints: List[List[float]] = field(default_factory=lambda: [[0.0, 0.0, 1.5, 0.0]])
    target_precision_m: float = 0.2
    switch_times: List[float] = field(default_factory=list)  # timed waypoints (E1)
    gps_noise_std: float = 0.0          # m
    imu_noise_std: float = 0.0          # rad (angles) and rad/s (gyro)
    wind_force: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])  # N, world frame
    wind_start_s: float = 0.0
    wind_end_s: float = 1e9
    gust_amplitude: float = 0.0         # N, sinusoidal gust added on the wind direction
    gust_period_s: float = 4.0
    gains: Dict[str, Dict[str, float]] = field(default_factory=dict)
    tag: str = ""                       # label of a sweep variant, e.g. "roll_kp=25"


def apply_overrides(gains: Any, overrides: Dict[str, float]) -> Any:
    """Return `gains` with any matching fields replaced from `overrides`."""
    names = {f.name for f in fields(gains)}
    for key, value in (overrides or {}).items():
        if key not in names:
            raise KeyError(f"unknown gain '{key}' for {type(gains).__name__}")
        setattr(gains, key, float(value))
    return gains


def parse_scenario(data: Dict[str, Any]) -> ScenarioConfig:
    cfg = ScenarioConfig()
    known = {f.name for f in fields(cfg)}
    for key, value in data.items():
        if key in known:
            setattr(cfg, key, value)
    return cfg


def load_scenario(repo_root: str = ".") -> ScenarioConfig:
    """Read the run description; falls back to the interactive demo defaults."""
    env_json = os.environ.get("DRONE_SCENARIO_JSON")
    if env_json:
        return parse_scenario(json.loads(env_json))
    path = os.path.join(repo_root, "current_scenario.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return parse_scenario(json.load(f))
    return ScenarioConfig()


def snapshot(scenario: ScenarioConfig, gains: Any, params: PhysicalParams) -> Dict[str, Any]:
    """Everything needed to reproduce a run, saved next to its telemetry."""
    return {"scenario": asdict(scenario), "gains": asdict(gains), "params": asdict(params)}
