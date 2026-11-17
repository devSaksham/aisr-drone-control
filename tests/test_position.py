"""Tests for position.py (owner: M3). Signs follow docs/frames.md."""
import math

from drone_ctrl.position import BaselinePosition, ImprovedPosition, accel_to_tilt


def test_forward_needs_positive_pitch():
    roll, pitch = accel_to_tilt(1.0, 0.0, 0.0, 0.3)
    assert pitch > 0 and abs(roll) < 1e-12


def test_left_needs_negative_roll():
    roll, _ = accel_to_tilt(0.0, 1.0, 0.0, 0.3)
    assert roll < 0


def test_yaw_rotation():
    # Facing +y (yaw 90 deg), a world +y demand is "forward": positive pitch.
    roll, pitch = accel_to_tilt(0.0, 1.0, math.pi / 2, 0.3)
    assert pitch > 0 and abs(roll) < 1e-9


def test_tilt_is_limited():
    roll, pitch = accel_to_tilt(100.0, -100.0, 0.0, 0.15)
    assert pitch == 0.15 and roll == 0.15


def test_baseline_moves_toward_target():
    _, pitch = BaselinePosition(1.0, 1.0, 0.2).compute((1, 0), (0, 0), (0, 0), 0.0)
    assert pitch > 0


def test_improved_integral_builds_against_steady_error():
    pos = ImprovedPosition(1.0, 2.0, 1.0, 5.0, 1.5, 0.3)
    first = pos.compute((0.1, 0), (0, 0), (0, 0), 0.0, 0.01)[1]
    for _ in range(200):
        later = pos.compute((0.1, 0), (0, 0), (0, 0), 0.0, 0.01)[1]
    assert later > first
