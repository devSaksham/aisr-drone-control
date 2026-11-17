"""Sensor access, noise injection and state estimation.

Module: sensors.py
Owner: M1
Inputs:  Webots GPS, inertial unit and gyro devices; noise standard deviations; seed.
Outputs: DroneState (position, velocity, attitude, body rates) every control step.
Tests:   tests/test_sensors.py

The GPS gives position only. Velocity is estimated with a constant-velocity Kalman
filter per axis (state [p, v]):
    predict:  x = F x,  P = F P F^T + Q,     F = [[1, dt], [0, 1]]
    update:   K = P H^T (H P H^T + R)^-1,    H = [1, 0],  R = sigma_gps^2
Q comes from white acceleration noise with spectral density q (m^2/s^3).
Plain finite differences of a GPS with 5 cm noise at dt = 8 ms would give velocity
noise of several m/s; the filter reduces this and also smooths the position.
"""

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

MIN_GPS_STD = 0.002  # m, floor so the filter stays well-conditioned without noise


@dataclass
class DroneState:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    p: float = 0.0
    q: float = 0.0
    r: float = 0.0


class ConstantVelocityKF:
    """Three independent 1D constant-velocity Kalman filters (x, y, z)."""

    def __init__(self, dt: float, meas_std: float, accel_psd: float = 4.0) -> None:
        self.F = np.array([[1.0, dt], [0.0, 1.0]])
        self.Q = accel_psd * np.array([[dt**3 / 3, dt**2 / 2], [dt**2 / 2, dt]])
        self.R = max(meas_std, MIN_GPS_STD) ** 2
        self.x = np.zeros((3, 2))
        self.P = np.array([np.eye(2) for _ in range(3)])
        self.initialised = False

    def update(self, z: np.ndarray) -> np.ndarray:
        """Feed one 3D position measurement; returns [[p, v], ...] for x, y, z."""
        if not self.initialised:
            self.x[:, 0] = z
            self.initialised = True
            return self.x.copy()
        for i in range(3):
            x = self.F @ self.x[i]
            P = self.F @ self.P[i] @ self.F.T + self.Q
            s = P[0, 0] + self.R
            k = P[:, 0] / s
            x = x + k * (z[i] - x[0])
            P = P - np.outer(k, P[0, :])
            self.x[i], self.P[i] = x, P
        return self.x.copy()


class DroneSensors:
    """Reads the Mavic's sensors and returns an estimated DroneState."""

    def __init__(self, robot: Any, time_step_ms: int, gps_noise_std: float = 0.0,
                 imu_noise_std: float = 0.0, seed: int = 0) -> None:
        self.dt = time_step_ms / 1000.0
        self.gps_noise_std = gps_noise_std
        self.imu_noise_std = imu_noise_std
        self.rng = np.random.default_rng(seed)
        self.kf = ConstantVelocityKF(self.dt, gps_noise_std)
        self.gps = self.imu = self.gyro = None
        if robot is not None:
            self.gps = robot.getDevice("gps")
            self.imu = robot.getDevice("inertial unit")
            self.gyro = robot.getDevice("gyro")
            for dev in (self.gps, self.imu, self.gyro):
                dev.enable(time_step_ms)

    def estimate(self, gps_xyz, rpy, rates) -> DroneState:
        """Add the configured noise to raw readings and run the estimator."""
        pos = np.asarray(gps_xyz, dtype=float).copy()
        att = np.asarray(rpy, dtype=float).copy()
        gyr = np.asarray(rates, dtype=float).copy()
        if self.gps_noise_std > 0:
            pos += self.rng.normal(0.0, self.gps_noise_std, 3)
        if self.imu_noise_std > 0:
            att += self.rng.normal(0.0, self.imu_noise_std, 3)
            gyr += self.rng.normal(0.0, self.imu_noise_std, 3)
        est = self.kf.update(pos)
        return DroneState(x=est[0, 0], y=est[1, 0], z=est[2, 0],
                          vx=est[0, 1], vy=est[1, 1], vz=est[2, 1],
                          roll=att[0], pitch=att[1], yaw=att[2],
                          p=gyr[0], q=gyr[1], r=gyr[2])

    def read(self) -> Optional[DroneState]:
        """Poll the Webots devices; returns None until the GPS has a valid fix."""
        xyz = self.gps.getValues()
        if any(v != v for v in xyz):  # NaN before the first sample
            return None
        return self.estimate(xyz, self.imu.getRollPitchYaw(), self.gyro.getValues())
