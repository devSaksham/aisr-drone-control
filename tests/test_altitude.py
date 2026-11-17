"""Tests for altitude.py (owner: M2)."""
from drone_ctrl.altitude import BaselineAltitude, ImprovedAltitude


def test_baseline_pushes_up_when_below_target():
    assert BaselineAltitude(4.0, 3.0, 10.0).compute(2.0, 1.0, 0.0) > 0


def test_baseline_damps_upward_speed():
    assert BaselineAltitude(4.0, 3.0, 10.0).compute(1.0, 1.0, 0.5) < 0


def test_improved_integral_removes_offset_over_time():
    alt = ImprovedAltitude(4.0, 2.0, 0.0, 10.0, 0.0, 15.0, 68.5)
    first = alt.compute(1.0, 0.9, 0.0, 0.01)
    for _ in range(300):
        later = alt.compute(1.0, 0.9, 0.0, 0.01)
    assert later > first


def test_tilt_compensation_adds_thrust():
    alt = ImprovedAltitude(4.0, 0.0, 0.0, 10.0, 0.0, 15.0, 68.5)
    assert alt.compute(1.0, 1.0, 0.0, 0.01, roll=0.2) > alt.compute(1.0, 1.0, 0.0, 0.01)


def test_acceleration_feedforward_sign():
    alt = ImprovedAltitude(0.0, 0.0, 0.0, 10.0, 0.0, 15.0, 68.5)
    assert alt.compute(1, 1, 0, 0.01, az_ref=1.0) > 0 > alt.compute(1, 1, 0, 0.01, az_ref=-1.0)
