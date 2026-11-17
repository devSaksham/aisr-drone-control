"""Heading (yaw) controller with angle wrapping.

Module: yaw.py
Owner: M3
Inputs:  yaw reference psi_ref (rad), measured yaw psi (rad), yaw rate r (rad/s).
Outputs: yaw_input (rad/s differential) for the mixer.
Tests:   tests/test_yaw.py

Verified in Webots: a positive yaw input gives a positive (CCW) yaw rate, so
    yaw_input = Kp * wrap(psi_ref - psi) - Kd * r
wrap() maps the error into [-pi, pi) so the drone always turns the short way round.
Method A uses kd = 0 (pure P), Method B uses PD.
"""

import math


def wrap_to_pi(angle: float) -> float:
    """Wrap an angle in radians to [-pi, pi)."""
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


class YawController:
    """P/PD yaw controller."""

    def __init__(self, kp: float, kd: float = 0.0, max_input: float = 2.0) -> None:
        self.kp = kp
        self.kd = kd
        self.max_input = max_input

    def compute(self, yaw_ref: float, yaw: float, yaw_rate: float = 0.0) -> float:
        u = self.kp * wrap_to_pi(yaw_ref - yaw) - self.kd * yaw_rate
        return max(-self.max_input, min(u, self.max_input))
