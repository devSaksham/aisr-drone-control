"""Method B: trajectory-tracking controller with PID anti-windup and feedforward.

Module: improved.py
Owner: M4
Inputs:  DroneState (estimated), simulation time t, dt.
Outputs: ControlOutput with signed motor speeds and the references used (for logging).
Tests:   tests/test_improved.py

Differences from Method A (everything else, including the attitude loop and mixer,
is identical so the comparison isolates these changes):
1. Each waypoint change starts a minimum-jerk reference segment instead of a step.
   The next waypoint is only accepted once the current segment has finished.
2. Altitude: PID with conditional anti-windup, filtered derivative, reference-velocity
   feedforward and thrust tilt compensation.
3. Position: position-P -> velocity-PI cascade with velocity and acceleration
   feedforward from the trajectory (integral removes drift and steady wind).
4. Yaw: PD instead of P.
"""

from typing import Optional, Sequence

from .altitude import ImprovedAltitude
from .attitude import AttitudeController
from .baseline import ControlOutput
from .config import ImprovedGains, PhysicalParams
from .mixer import MotorMixer
from .position import ImprovedPosition
from .sensors import DroneState
from .trajectory import MinJerkTrajectory
from .waypoints import WaypointManager
from .yaw import YawController


class ImprovedController:
    """Method B assembly."""

    def __init__(self, waypoints: Sequence[Sequence[float]], gains: ImprovedGains,
                 params: PhysicalParams, tolerance_m: float,
                 switch_times: Optional[Sequence[float]] = None) -> None:
        self.g = gains
        self.params = params
        self.timed = bool(switch_times)
        self.wps = WaypointManager(waypoints, tolerance_m, gains.wp_hold_s, switch_times)
        self.traj = MinJerkTrajectory(gains.traj_max_vel, gains.traj_max_acc,
                                      gains.traj_min_time)
        self.alt = ImprovedAltitude(gains.alt_kp, gains.alt_ki, gains.alt_kd,
                                    gains.alt_int_limit, gains.alt_d_alpha, gains.alt_max,
                                    params.hover_speed)
        self.pos = ImprovedPosition(gains.pos_kp, gains.vel_kp, gains.vel_ki,
                                    gains.vel_int_limit, gains.max_speed, gains.max_tilt)
        self.att = AttitudeController(gains.roll_kp, gains.roll_kd, gains.pitch_kp,
                                      gains.pitch_kd, gains.att_max)
        self.yaw = YawController(gains.yaw_kp, gains.yaw_kd, gains.yaw_max)
        self.mixer = MotorMixer(params.hover_speed, params.max_motor_speed)
        self._planned_index = -1

    def step(self, s: DroneState, t: float, dt: float) -> ControlOutput:
        airborne = s.z > self.params.takeoff_alt
        if self._planned_index < 0:
            if not airborne:
                # Take-off phase: the rotors need ~2.5 s to lift the drone. Running the
                # trajectory clock during that time would let the reference run ahead
                # and wind up the altitude loop, so spool up with a fixed boost and
                # start the first segment once the drone has left the ground.
                self.wps.update((s.x, s.y, s.z), t, dt, allow_advance=False)
                motors = self.mixer.mix(self.g.takeoff_boost, *self.att.compute(
                    0.0, s.roll, s.p, 0.0, s.pitch, s.q), 0.0)
                return ControlOutput(motors, [s.x, s.y, s.z, s.yaw], list(self.wps.target),
                                     self.wps.index, False)
            self.traj.plan([s.x, s.y, s.z, s.yaw], self.wps.target,
                           start_vel=[s.vx, s.vy, s.vz])
            self._planned_index = self.wps.index

        wp, finished = self.wps.update((s.x, s.y, s.z), t, dt,
                                       allow_advance=self.traj.done or self.timed)
        if self.wps.index != self._planned_index:
            # Continue the reference from the previous waypoint, so it never jumps.
            self.traj.plan(self.wps.waypoints[self._planned_index], wp)
            self._planned_index = self.wps.index

        ref, vel, acc = self.traj.step(dt)
        vertical = self.alt.compute(ref[2], s.z, s.vz, dt, vz_ref=vel[2],
                                    roll=s.roll, pitch=s.pitch, az_ref=acc[2])
        if airborne:
            roll_ref, pitch_ref = self.pos.compute(ref[:2], (s.x, s.y), (s.vx, s.vy), s.yaw,
                                                   dt, vel_ff=vel[:2], acc_ff=acc[:2])
            yaw_in = self.yaw.compute(ref[3], s.yaw, s.r)
        else:
            self.pos.reset()
            roll_ref = pitch_ref = yaw_in = 0.0
        roll_in, pitch_in = self.att.compute(roll_ref, s.roll, s.p, pitch_ref, s.pitch, s.q)
        motors = self.mixer.mix(vertical, roll_in, pitch_in, yaw_in)
        return ControlOutput(motors, [float(v) for v in ref], list(wp), self.wps.index,
                             finished, roll_ref, pitch_ref)
