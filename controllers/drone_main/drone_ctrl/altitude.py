"""Altitude loops: Method A (PD) and Method B (PID + feedforward + tilt compensation).

Module: altitude.py
Owner: M2
Inputs:  altitude reference z_ref (m), measured z (m), vertical speed vz (m/s),
         optional reference speed vz_ref (m/s), roll and pitch (rad), dt (s).
Outputs: vertical_input (rad/s) added to the hover speed T_h in the mixer.
Tests:   tests/test_altitude.py

Method A: v = Kp*(z_ref - z) - Kd*vz            (no integral, no feedforward)
Method B: w = T_h + PID(z_ref - z, d/dt = vz_ref - vz) + T_h * az_ref / (2 g)
          v = w / sqrt(cos(phi)*cos(theta)) - T_h
Thrust grows with the square of rotor speed, so dividing the speed by
sqrt(cos phi cos theta) keeps the vertical thrust component constant while tilted.
"""

import math

from .pid import PIDController

G = 9.81


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(v, hi))


class BaselineAltitude:
    """Method A: proportional-derivative altitude control around hover speed."""

    def __init__(self, kp: float, kd: float, max_input: float) -> None:
        self.kp = kp
        self.kd = kd
        self.max_input = max_input

    def compute(self, z_ref: float, z: float, vz: float) -> float:
        v = self.kp * (z_ref - z) - self.kd * vz
        return _clamp(v, -self.max_input, self.max_input)


class ImprovedAltitude:
    """Method B: PID with anti-windup, filtered derivative, feedforward, tilt compensation."""

    def __init__(self, kp: float, ki: float, kd: float, integral_limit: float,
                 derivative_alpha: float, max_input: float, hover_speed: float,
                 min_tilt_cos: float = 0.7) -> None:
        self.hover_speed = hover_speed
        self.max_input = max_input
        self.min_tilt_cos = min_tilt_cos
        self.pid = PIDController(kp=kp, ki=ki, kd=kd, output_limit=max_input,
                                 integral_limit=integral_limit,
                                 derivative_alpha=derivative_alpha)

    def reset(self) -> None:
        self.pid.reset()

    def compute(self, z_ref: float, z: float, vz: float, dt: float, vz_ref: float = 0.0,
                roll: float = 0.0, pitch: float = 0.0, az_ref: float = 0.0) -> float:
        u = self.pid.compute(z_ref - z, dt, error_dot=vz_ref - vz)
        # Acceleration feedforward: T ~ w^2, so dT/T = 2 dw/w and a = g dT/T
        # gives dw = w_h * a_ref / (2 g).
        u += self.hover_speed * az_ref / (2.0 * G)
        tilt_cos = max(math.cos(roll) * math.cos(pitch), self.min_tilt_cos)
        speed = (self.hover_speed + u) / math.sqrt(tilt_cos)
        return _clamp(speed - self.hover_speed, -self.max_input, self.max_input)
