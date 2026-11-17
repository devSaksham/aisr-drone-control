"""Roll/pitch inner attitude loop (shared by Method A and Method B).

Module: attitude.py
Owner: M2
Inputs:  roll/pitch references (rad), measured roll/pitch (rad), gyro rates p, q (rad/s).
Outputs: roll_input, pitch_input (motor-speed differentials, rad/s) for the mixer.
Tests:   tests/test_attitude.py

Sign convention verified in Webots (docs/frames.md): a positive roll input drives roll
negative, a positive pitch input drives pitch negative. The stabilising PD law is
therefore
    roll_input  = Kp_r * (phi   - phi_ref)   + Kd_r * p
    pitch_input = Kp_p * (theta - theta_ref) + Kd_p * q
which is the Webots sample law with a setpoint added. The angle error is clamped to
+/- 1 rad like the sample, so a large error cannot saturate every motor at once.
"""

from typing import Tuple


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(v, hi))


class AttitudeController:
    """PD attitude stabiliser on IMU angle with gyro-rate damping."""

    def __init__(self, kp_roll: float = 50.0, kd_roll: float = 1.0,
                 kp_pitch: float = 30.0, kd_pitch: float = 1.0,
                 max_input: float = 40.0) -> None:
        self.kp_roll = kp_roll
        self.kd_roll = kd_roll
        self.kp_pitch = kp_pitch
        self.kd_pitch = kd_pitch
        self.max_input = max_input

    def compute(self, roll_ref: float, roll: float, p: float,
                pitch_ref: float, pitch: float, q: float) -> Tuple[float, float]:
        """Return (roll_input, pitch_input)."""
        roll_err = _clamp(roll - roll_ref, -1.0, 1.0)
        pitch_err = _clamp(pitch - pitch_ref, -1.0, 1.0)
        roll_input = self.kp_roll * roll_err + self.kd_roll * p
        pitch_input = self.kp_pitch * pitch_err + self.kd_pitch * q
        m = self.max_input
        return _clamp(roll_input, -m, m), _clamp(pitch_input, -m, m)
