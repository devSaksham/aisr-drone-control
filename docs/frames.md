# Coordinate Frames and Sign Conventions (verified in Webots)

Owner: M1. Everything below was measured in Webots R2025a, not assumed. To reproduce it:

```bash
webots --mode=fast --batch --no-rendering --minimize worlds/probe.wbt
python experiments/analyse_probe.py
```

The probe (`controllers/sign_probe/sign_probe.py`) hovers with the exact stabilising law of
the Webots sample `mavic2pro_patrol.py` and then adds one open-loop offset at a time to the
roll, pitch and yaw inputs.

## 1. World frame
| Item | Value | How verified |
|---|---|---|
| Convention | ENU: x East, y North, z Up | GPS z rises from 0.07 m to about 2 m during take-off |
| Gravity | along -z | drone falls when thrust is reduced |
| `basicTimeStep` | 8 ms (dt = 0.008 s) | world file; the sample controller requires 8 ms |
| Air damping | `defaultDamping` linear 0.5, angular 0.5 | required by the sample controller (comment at the end of `mavic2pro_patrol.py`); kept in all our worlds so we use the same physics as the reference |
| Start pose | (0, 0, 0.1) m, yaw 0 rad | our worlds; the Webots sample world starts at yaw = pi |

## 2. Sensors
| Device | Returns | Notes |
|---|---|---|
| `gps` | (x, y, z) in the world frame | z is altitude |
| `inertial unit` | (roll phi, pitch theta, yaw psi), rad | yaw is CCW-positive, in (-pi, pi] |
| `gyro` | (p, q, r), rad/s, body axes | Correlation of the gyro with the numerical derivative of roll/pitch/yaw is +0.99 / +1.00 / +1.00 |

## 3. Measured responses (probe run, yaw approx. 0, so body axes = world axes)
| Test | Attitude response | Motion (background drift removed) |
|---|---|---|
| roll input offset +1 | roll goes **negative** (peak -0.025 rad) | +0.205 m in **+y** |
| pitch input offset +1 | pitch goes **negative** (peak -0.043 rad) | -0.328 m in **-x** |
| yaw input offset +0.3 | yaw rate **positive** (+0.092 rad/s) | yaw +0.25 rad (CCW) |

What follows from this:
- **Roll:** a positive roll input produces a negative roll (left side down). A negative roll accelerates the drone toward body +y (left). So **a_y,body ~ -g * phi**.
- **Pitch:** a positive pitch input produces a negative pitch (nose up). A negative pitch accelerates the drone toward body -x. So **a_x,body ~ +g * theta**, and a positive pitch (nose down) flies forward.
- **Yaw:** a positive yaw input produces a positive (CCW) yaw rate.

## 4. Control laws that follow
Attitude loop (the sample's law, with a setpoint added). It stabilises because a positive input reduces the angle:

```
roll_input  = Kp_roll  * (phi   - phi_ref)   + Kd_roll  * p
pitch_input = Kp_pitch * (theta - theta_ref) + Kd_pitch * q
yaw_input   = Kp_yaw * wrap(psi_ref - psi)   - Kd_yaw * r
```

The first (pre-overhaul) controller used `Kp*(phi_ref - phi) - Kd*p`, which is this law with the
sign flipped. The result was positive feedback, and the drone flipped over.

Position loop: the world-frame error is rotated into the body frame with yaw psi:

```
e_xb =  cos(psi) * e_x + sin(psi) * e_y
e_yb = -sin(psi) * e_x + cos(psi) * e_y
theta_ref = +a_xb_cmd / g      (forward needs nose down, positive pitch)
phi_ref   = -a_yb_cmd / g      (left needs negative roll)
```

## 5. Motors and mixing (from the sample controller and the Mavic2Pro PROTO)
| Motor device | Spin sign sent | PROTO thrust constant |
|---|---|---|
| `front left propeller` | + | +0.00026 |
| `front right propeller` | - | -0.00026 |
| `rear left propeller` | - | -0.00026 |
| `rear right propeller` | + | +0.00026 |

```
FL = T + v - yaw + pitch - roll      FR = T + v + yaw + pitch + roll
RL = T + v + yaw - pitch - roll      RR = T + v - yaw - pitch + roll
```

- T = 68.5 rad/s is the empirical hover speed from the sample.
- PROTO `maxVelocity` = 576 rad/s.
- Each speed is computed as a magnitude, then sent with the sign shown above.

## 6. Observations that matter for the controllers
1. **Hover drift.** With the sample's P-only attitude law and no position control, the drone
   drifts about +0.063 m/s in x and -0.018 m/s in y. The PROTO places the front propellers at
   x = +0.055 m and the rear ones at x = -0.177 m, so the thrust is not centred, and a
   proportional-only loop leaves a constant tilt bias. An integral term in the position
   loop can remove this.
2. **Altitude offset in the sample.** The sample commands `3 * (z_ref - z + 0.6)^3`. With
   T = 68.5 already close to hover thrust, it settles about 0.5 m *above* the reference
   (1.5 m target, about 2.0 m reached in the probe).
3. **Take-off.** The drone rests nose-up at about -0.07 rad pitch on the ground and
   leaves the ground about 2.5-3 s after the motors start.
