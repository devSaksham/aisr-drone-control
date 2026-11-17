"""Tests for sensors.py (owner: M1)."""
import numpy as np
from drone_ctrl.sensors import ConstantVelocityKF, DroneSensors


def test_kf_tracks_constant_velocity():
    dt, v = 0.008, 0.5
    kf = ConstantVelocityKF(dt, meas_std=0.0)
    for k in range(500):
        est = kf.update(np.array([v * k * dt, 0.0, 1.0]))
    assert abs(est[0, 1] - v) < 0.01 and abs(est[2, 1]) < 0.01


def test_kf_reduces_velocity_noise():
    dt, sigma = 0.008, 0.05
    rng = np.random.default_rng(1)
    kf = ConstantVelocityKF(dt, meas_std=sigma)
    vel, fd, prev = [], [], None
    for _ in range(2000):
        z = np.array([0.0, 0.0, 1.0]) + rng.normal(0, sigma, 3)
        vel.append(kf.update(z)[0, 1])
        if prev is not None:
            fd.append((z[0] - prev) / dt)
        prev = z[0]
    assert np.std(vel[500:]) < 0.1 * np.std(fd)


def test_noise_is_reproducible_with_seed():
    a = DroneSensors(None, 8, gps_noise_std=0.05, seed=7).estimate([0, 0, 1], [0, 0, 0], [0, 0, 0])
    b = DroneSensors(None, 8, gps_noise_std=0.05, seed=7).estimate([0, 0, 1], [0, 0, 0], [0, 0, 0])
    assert a == b
