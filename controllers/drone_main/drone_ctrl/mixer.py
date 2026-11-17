"""Motor mixer and saturation for the Mavic 2 Pro X-configuration.

Module: mixer.py
Owner: M2
Inputs:  vertical_input, roll_input, pitch_input, yaw_input (rad/s differentials).
Outputs: signed propeller speeds [FL, FR, RL, RR] (rad/s) for Motor.setVelocity().
Tests:   tests/test_mixer.py

Mixing matrix and spin signs are those of the Webots sample controller
(verified in docs/frames.md):
    FL = T + v - yaw + pitch - roll      (+ spin)
    FR = T + v + yaw + pitch + roll      (- spin)
    RL = T + v + yaw - pitch - roll      (- spin)
    RR = T + v - yaw - pitch + roll      (+ spin)
Each magnitude is clamped to [min_speed, max_speed] before the sign is applied.
"""

from typing import List

SPIN_SIGNS = (1.0, -1.0, -1.0, 1.0)


class MotorMixer:
    """Maps body commands to the four propeller speeds."""

    def __init__(self, hover_speed: float = 68.5, max_speed: float = 576.0,
                 min_speed: float = 0.0) -> None:
        self.hover_speed = hover_speed
        self.max_speed = max_speed
        self.min_speed = min_speed

    def magnitudes(self, vertical: float, roll: float, pitch: float, yaw: float) -> List[float]:
        """Unsigned, clamped rotor speeds in the order FL, FR, RL, RR."""
        base = self.hover_speed + vertical
        raw = [base - yaw + pitch - roll,
               base + yaw + pitch + roll,
               base + yaw - pitch - roll,
               base - yaw - pitch + roll]
        return [max(self.min_speed, min(w, self.max_speed)) for w in raw]

    def mix(self, vertical: float, roll: float, pitch: float, yaw: float) -> List[float]:
        """Signed rotor speeds ready for Motor.setVelocity()."""
        mags = self.magnitudes(vertical, roll, pitch, yaw)
        return [s * w for s, w in zip(SPIN_SIGNS, mags)]
