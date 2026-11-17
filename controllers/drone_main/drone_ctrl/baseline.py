"""Method A: baseline cascaded P/PD controller with step waypoint commands.

Module: baseline.py
Owner: M4
Inputs:  DroneState (estimated), simulation time t, dt.
Outputs: ControlOutput with signed motor speeds and the references used (for logging).
Tests:   tests/test_baseline.py

Per step: waypoint manager -> altitude PD -> position PD -> attitude PD -> yaw P -> mixer.
The full next waypoint is commanded immediately (a step), as in the Webots sample
and most textbook examples. No integral action and no feedforward.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .altitude import BaselineAltitude
from .attitude import AttitudeController
from .config import BaselineGains, PhysicalParams
from .mixer import MotorMixer
from .position import BaselinePosition
from .sensors import DroneState
from .waypoints import WaypointManager
from .yaw import YawController


@dataclass
class ControlOutput:
    """What a controller produced in one step (motors plus references for logging)."""
    motors: List[float]
    ref_pos: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    waypoint: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    wp_index: int = 0
    finished: bool = False
    roll_ref: float = 0.0
    pitch_ref: float = 0.0


class BaselineController:
    """Method A assembly."""

    def __init__(self, waypoints: Sequence[Sequence[float]], gains: BaselineGains,
                 params: PhysicalParams, tolerance_m: float,
                 switch_times: Optional[Sequence[float]] = None) -> None:
        self.g = gains
        self.params = params
        self.wps = WaypointManager(waypoints, tolerance_m, gains.wp_hold_s, switch_times)
        self.alt = BaselineAltitude(gains.alt_kp, gains.alt_kd, gains.alt_max)
        self.pos = BaselinePosition(gains.pos_kp, gains.pos_kd, gains.max_tilt)
        self.att = AttitudeController(gains.roll_kp, gains.roll_kd, gains.pitch_kp,
                                      gains.pitch_kd, gains.att_max)
        self.yaw = YawController(gains.yaw_kp, 0.0, gains.yaw_max)
        self.mixer = MotorMixer(params.hover_speed, params.max_motor_speed)

    def step(self, s: DroneState, t: float, dt: float) -> ControlOutput:
        wp, finished = self.wps.update((s.x, s.y, s.z), t, dt)
        vertical = self.alt.compute(wp[2], s.z, s.vz)
        airborne = s.z > self.params.takeoff_alt
        if airborne:
            roll_ref, pitch_ref = self.pos.compute(wp[:2], (s.x, s.y), (s.vx, s.vy), s.yaw)
            yaw_in = self.yaw.compute(wp[3], s.yaw, s.r)
        else:
            roll_ref = pitch_ref = yaw_in = 0.0
        roll_in, pitch_in = self.att.compute(roll_ref, s.roll, s.p, pitch_ref, s.pitch, s.q)
        motors = self.mixer.mix(vertical, roll_in, pitch_in, yaw_in)
        return ControlOutput(motors, list(wp), list(wp), self.wps.index, finished,
                             roll_ref, pitch_ref)
