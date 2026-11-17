"""Tests for yaw.py (owner: M3)."""
import math

from drone_ctrl.yaw import YawController, wrap_to_pi


def test_wrap():
    assert abs(wrap_to_pi(3 * math.pi / 2) + math.pi / 2) < 1e-12


def test_turns_short_way():
    # From +170 deg to -170 deg is +20 deg, not -340 deg.
    u = YawController(1.0, max_input=10).compute(math.radians(-170), math.radians(170))
    assert u > 0 and abs(u - math.radians(20)) < 1e-9


def test_rate_damping_and_clamp():
    assert YawController(1.0, kd=1.0, max_input=0.5).compute(0, 0, 1.0) == -0.5
