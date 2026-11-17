"""Horizontal position loops: world-frame error -> roll/pitch references.

Module: position.py
Owner: M3
Inputs:  position reference (x, y), optional reference velocity/acceleration,
         estimated position and velocity (world frame), yaw psi (rad), dt (s).
Outputs: (roll_ref, pitch_ref) in rad for the attitude loop.
Tests:   tests/test_position.py

Both methods compute a desired horizontal acceleration a = (a_x, a_y) in the world
frame, rotate it into the body frame with the yaw angle and convert it to tilt using
the small-angle model verified in docs/frames.md:
    a_xb =  cos(psi)*a_x + sin(psi)*a_y        pitch_ref = +a_xb / g
    a_yb = -sin(psi)*a_x + cos(psi)*a_y        roll_ref  = -a_yb / g

Method A (PD):        a = Kp*(p_ref - p) - Kd*v
Method B (cascade):   v_cmd = v_ff + Kp_pos*(p_ref - p)          (|v_cmd| <= v_max)
                      a     = a_ff + PI(v_cmd - v) with anti-windup
The integral term in Method B removes constant biases such as the thrust-centre drift
and a steady wind force.
"""

import math
from typing import Sequence, Tuple

from .pid import PIDController

G = 9.81


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(v, hi))


def accel_to_tilt(ax: float, ay: float, yaw: float, max_tilt: float) -> Tuple[float, float]:
    """Convert a world-frame acceleration demand to (roll_ref, pitch_ref)."""
    c, s = math.cos(yaw), math.sin(yaw)
    ax_b = c * ax + s * ay
    ay_b = -s * ax + c * ay
    pitch_ref = _clamp(ax_b / G, -max_tilt, max_tilt)
    roll_ref = _clamp(-ay_b / G, -max_tilt, max_tilt)
    return roll_ref, pitch_ref


class BaselinePosition:
    """Method A: PD on position error with velocity damping."""

    def __init__(self, kp: float, kd: float, max_tilt: float) -> None:
        self.kp = kp
        self.kd = kd
        self.max_tilt = max_tilt

    def compute(self, ref_xy: Sequence[float], pos_xy: Sequence[float],
                vel_xy: Sequence[float], yaw: float) -> Tuple[float, float]:
        ax = self.kp * (ref_xy[0] - pos_xy[0]) - self.kd * vel_xy[0]
        ay = self.kp * (ref_xy[1] - pos_xy[1]) - self.kd * vel_xy[1]
        return accel_to_tilt(ax, ay, yaw, self.max_tilt)


class ImprovedPosition:
    """Method B: position P -> velocity PI cascade with feedforward."""

    def __init__(self, kp_pos: float, kp_vel: float, ki_vel: float, integral_limit: float,
                 max_speed: float, max_tilt: float) -> None:
        self.kp_pos = kp_pos
        self.max_speed = max_speed
        self.max_tilt = max_tilt
        max_acc = G * math.tan(max_tilt)
        self.vel_pid = [PIDController(kp=kp_vel, ki=ki_vel, output_limit=max_acc,
                                      integral_limit=integral_limit) for _ in range(2)]

    def reset(self) -> None:
        for pid in self.vel_pid:
            pid.reset()

    def compute(self, ref_xy: Sequence[float], pos_xy: Sequence[float],
                vel_xy: Sequence[float], yaw: float, dt: float,
                vel_ff: Sequence[float] = (0.0, 0.0),
                acc_ff: Sequence[float] = (0.0, 0.0)) -> Tuple[float, float]:
        v_cmd = [vel_ff[i] + self.kp_pos * (ref_xy[i] - pos_xy[i]) for i in range(2)]
        speed = math.hypot(v_cmd[0], v_cmd[1])
        if speed > self.max_speed:
            v_cmd = [v * self.max_speed / speed for v in v_cmd]
        acc = [acc_ff[i] + self.vel_pid[i].compute(v_cmd[i] - vel_xy[i], dt) for i in range(2)]
        return accel_to_tilt(acc[0], acc[1], yaw, self.max_tilt)
