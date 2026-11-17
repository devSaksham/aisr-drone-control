"""Sign-convention probe for the Webots Mavic 2 Pro.

Module: sign_probe.py
Owner: M1
Purpose: Verify, in simulation, the coordinate frames and control-input signs that the
         real controllers rely on, instead of assuming them.

Method: hover with the exact stabilising law of the Webots sample controller
(``mavic2pro_patrol.py``), then inject one open-loop offset at a time into the roll,
pitch and yaw inputs and log how the drone responds. The CSV written to
``results/probe/probe.csv`` is analysed by ``experiments/analyse_probe.py``.
"""

import csv
import os
import sys

webots_home = os.environ.get("WEBOTS_HOME", "C:/Program Files/Webots")
python_lib = os.path.join(webots_home, "lib", "controller", "python")
if os.path.exists(python_lib) and python_lib not in sys.path:
    sys.path.append(python_lib)

from controller import Supervisor  # noqa: E402

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(REPO_ROOT, "results", "probe")

# Constants copied from the Webots sample controller.
K_VERTICAL_THRUST = 68.5
K_VERTICAL_OFFSET = 0.6
K_VERTICAL_P = 3.0
K_ROLL_P = 50.0
K_PITCH_P = 30.0
TARGET_ALT = 1.5

# (start_s, end_s, roll_offset, pitch_offset, yaw_offset)
PHASES = [
    (8.0, 9.0, 1.0, 0.0, 0.0),
    (13.0, 14.0, 0.0, 1.0, 0.0),
    (18.0, 19.0, 0.0, 0.0, 0.3),
]
END_S = 25.0


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(v, hi))


def offsets(t: float):
    for start, end, r, p, y in PHASES:
        if start <= t < end:
            return r, p, y
    return 0.0, 0.0, 0.0


def main() -> None:
    robot = Supervisor()  # probe world only: lets the probe end the run itself
    ts = int(robot.getBasicTimeStep())
    imu = robot.getDevice("inertial unit")
    gps = robot.getDevice("gps")
    gyro = robot.getDevice("gyro")
    for dev in (imu, gps, gyro):
        dev.enable(ts)
    names = ["front left propeller", "front right propeller",
             "rear left propeller", "rear right propeller"]
    motors = [robot.getDevice(n) for n in names]
    for m in motors:
        m.setPosition(float("inf"))
        m.setVelocity(1.0)

    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    while robot.step(ts) != -1:
        t = robot.getTime()
        roll, pitch, yaw = imu.getRollPitchYaw()
        x, y, z = gps.getValues()
        wx, wy, wz = gyro.getValues()
        d_roll, d_pitch, d_yaw = offsets(t)

        roll_in = K_ROLL_P * clamp(roll, -1, 1) + wx + d_roll
        pitch_in = K_PITCH_P * clamp(pitch, -1, 1) + wy + d_pitch
        yaw_in = d_yaw
        vert = K_VERTICAL_P * clamp(TARGET_ALT - z + K_VERTICAL_OFFSET, -1, 1) ** 3

        fl = K_VERTICAL_THRUST + vert - yaw_in + pitch_in - roll_in
        fr = K_VERTICAL_THRUST + vert + yaw_in + pitch_in + roll_in
        rl = K_VERTICAL_THRUST + vert + yaw_in - pitch_in - roll_in
        rr = K_VERTICAL_THRUST + vert - yaw_in - pitch_in + roll_in
        for m, v in zip(motors, (fl, -fr, -rl, rr)):
            m.setVelocity(v)

        rows.append([t, x, y, z, roll, pitch, yaw, wx, wy, wz, d_roll, d_pitch, d_yaw])
        if t >= END_S:
            break

    with open(os.path.join(OUT_DIR, "probe.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t", "x", "y", "z", "roll", "pitch", "yaw", "wx", "wy", "wz",
                    "d_roll", "d_pitch", "d_yaw"])
        w.writerows(rows)
    print(f"[sign_probe] wrote {len(rows)} rows")
    robot.simulationQuit(0)


if __name__ == "__main__":
    main()
