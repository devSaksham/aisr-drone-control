# Architecture

The report's Figure 1 (Section 6) is the reference block diagram. In short:

```
waypoints -> [min-jerk trajectory, Method B only] -> position loop -> roll/pitch refs
          -> attitude PD + altitude (PD | PID+FF) + yaw (P | PD) -> mixer -> 4 rotors -> Webots
GPS / inertial unit / gyro -> Kalman velocity estimator -> state fed back to every loop (every 8 ms)
wind_supervisor (separate robot): wind force, crash watchdog, demo markers/labels, run end
```

| Loop | Method A | Method B | File (owner) |
|---|---|---|---|
| Reference | step to next waypoint | quintic minimum-jerk segment, starts from measured velocity | `trajectory.py`, `waypoints.py` (M3) |
| Altitude | PD around hover speed | PID + anti-windup + velocity/acceleration feedforward + tilt compensation | `altitude.py`, `pid.py` (M2) |
| Position | PD -> tilt | P -> velocity PI (anti-windup) + feedforward -> tilt | `position.py` (M3) |
| Attitude | PD, Kp 25 / Kd 4 roll, 30 / 2.5 pitch | same | `attitude.py` (M2) |
| Yaw | P | PD | `yaw.py` (M3) |
| Mixer | Webots sample sign pattern | same | `mixer.py` (M2) |
| Estimator | constant-velocity Kalman filter, q = 0.1 | same | `sensors.py` (M1) |

Signs and frames: `docs/frames.md`. Gains: `controllers/drone_main/drone_ctrl/config.py`.
