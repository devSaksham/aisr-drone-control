"""Minimum-jerk (quintic) trajectory between two waypoints.

Module: trajectory.py
Owner: M3
Inputs:  start pose [x, y, z, yaw] (+ optional start velocity), end pose, speed and
         acceleration limits, dt.
Outputs: reference position, velocity and acceleration at the current time.
Tests:   tests/test_trajectory.py

Each axis follows a quintic p(t) = c0 + c1 t + ... + c5 t^5 on [0, T] whose six
coefficients satisfy the boundary conditions p(0)=p0, p'(0)=v0, p''(0)=0, p(T)=p1,
p'(T)=0, p''(T)=0. A quintic with these conditions is the minimum-jerk path (it
minimises the integral of squared jerk). From rest (v0 = 0) it reduces to
    p(t) = p0 + (p1 - p0) * (10 tau^3 - 15 tau^4 + 6 tau^5),   tau = t / T,
whose peak speed is 1.875*D/T and peak acceleration 5.774*D/T^2 for a distance D;
T is the smallest duration meeting both limits (and a minimum duration).
Starting from the measured velocity (v0 != 0) is used at take-off, so the reference
does not order an already-climbing drone to stop abruptly.
The yaw change is wrapped so the drone turns the short way round.
"""

import math
from typing import Optional, Sequence, Tuple

import numpy as np

PEAK_VEL_FACTOR = 1.875
PEAK_ACC_FACTOR = 10.0 / math.sqrt(3.0)  # 5.774


def _wrap(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def min_jerk_profile(tau: float) -> Tuple[float, float, float]:
    """Rest-to-rest profile: s(tau), ds/dtau, d2s/dtau2 for tau clamped to [0, 1]."""
    t = min(1.0, max(0.0, tau))
    s = 10 * t**3 - 15 * t**4 + 6 * t**5
    ds = 30 * t**2 - 60 * t**3 + 30 * t**4
    dds = 60 * t - 180 * t**2 + 120 * t**3
    return s, ds, dds


def quintic_coefficients(p0: np.ndarray, v0: np.ndarray, p1: np.ndarray,
                         T: float) -> np.ndarray:
    """Coefficients c0..c5 (6 x n) for start (p0, v0, a0=0) and end (p1, 0, 0)."""
    d = p1 - p0
    c3 = (20 * d - 12 * v0 * T) / (2 * T**3)
    c4 = (-30 * d + 16 * v0 * T) / (2 * T**4)
    c5 = (12 * d - 6 * v0 * T) / (2 * T**5)
    zeros = np.zeros_like(p0)
    return np.array([p0, v0, zeros, c3, c4, c5])


class MinJerkTrajectory:
    """One active minimum-jerk segment at a time."""

    def __init__(self, max_vel: float, max_acc: float, min_duration: float = 1.0) -> None:
        self.max_vel = max_vel
        self.max_acc = max_acc
        self.min_duration = min_duration
        self.coef = np.zeros((6, 4))
        self.end = np.zeros(4)
        self.duration = min_duration
        self.elapsed = 0.0

    def plan(self, start: Sequence[float], end: Sequence[float],
             start_vel: Optional[Sequence[float]] = None) -> float:
        """Start a new segment; returns its duration (s)."""
        p0 = np.array(start[:4], dtype=float)
        p1 = np.array(end[:4], dtype=float)
        p1[3] = p0[3] + _wrap(p1[3] - p0[3])
        v0 = np.zeros(4)
        if start_vel is not None:
            v0[:len(start_vel)] = start_vel
        dist = float(np.linalg.norm(p1[:3] - p0[:3]))
        t_vel = PEAK_VEL_FACTOR * dist / self.max_vel
        t_acc = math.sqrt(PEAK_ACC_FACTOR * dist / self.max_acc)
        self.duration = max(t_vel, t_acc, self.min_duration)
        self.coef = quintic_coefficients(p0, v0, p1, self.duration)
        self.end = p1
        self.elapsed = 0.0
        return self.duration

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration

    def sample(self, t: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Evaluate the segment at time t (clamped to [0, T])."""
        if t >= self.duration:
            pos = self.end.copy()
            pos[3] = _wrap(pos[3])
            return pos, np.zeros(4), np.zeros(4)
        t = max(0.0, t)
        c = self.coef
        pos = c[0] + c[1] * t + c[2] * t**2 + c[3] * t**3 + c[4] * t**4 + c[5] * t**5
        vel = c[1] + 2 * c[2] * t + 3 * c[3] * t**2 + 4 * c[4] * t**3 + 5 * c[5] * t**4
        acc = 2 * c[2] + 6 * c[3] * t + 12 * c[4] * t**2 + 20 * c[5] * t**3
        pos[3] = _wrap(pos[3])
        return pos, vel, acc

    def step(self, dt: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Advance by dt and return (position, velocity, acceleration) as [x, y, z, yaw]."""
        self.elapsed += dt
        return self.sample(self.elapsed)
