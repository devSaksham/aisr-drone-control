"""Tests for trajectory.py (owner: M3)."""
import math

import numpy as np
from drone_ctrl.trajectory import MinJerkTrajectory, min_jerk_profile


def test_profile_boundary_conditions():
    assert min_jerk_profile(0.0) == (0.0, 0.0, 0.0)
    s, ds, dds = min_jerk_profile(1.0)
    assert abs(s - 1) < 1e-12 and abs(ds) < 1e-12 and abs(dds) < 1e-12


def test_limits_respected():
    tr = MinJerkTrajectory(max_vel=1.0, max_acc=0.5)
    T = tr.plan([0, 0, 0, 0], [2, 0, 0, 0])
    ts = np.linspace(0, T, 500)
    assert max(tr.sample(t)[1][0] for t in ts) <= 1.0 + 1e-6
    assert max(abs(tr.sample(t)[2][0]) for t in ts) <= 0.5 + 1e-6


def test_matches_closed_form_from_rest():
    tr = MinJerkTrajectory(1.0, 1.0)
    T = tr.plan([0, 0, 0, 0], [1, 0, 0, 0])
    assert abs(tr.sample(T / 2)[0][0] - min_jerk_profile(0.5)[0]) < 1e-9


def test_start_velocity_is_honoured():
    tr = MinJerkTrajectory(1.0, 1.0)
    tr.plan([0, 0, 0.3, 0], [0, 0, 2, 0], start_vel=[0, 0, 0.8])
    assert abs(tr.sample(0.0)[1][2] - 0.8) < 1e-9
    assert np.allclose(tr.sample(tr.duration)[0][:3], [0, 0, 2])


def test_yaw_wraps_short_way():
    tr = MinJerkTrajectory(1.0, 1.0)
    tr.plan([0, 0, 1, math.radians(170)], [1, 0, 1, math.radians(-170)])
    assert abs(abs(tr.sample(tr.duration / 2)[0][3]) - math.pi) < 0.01
