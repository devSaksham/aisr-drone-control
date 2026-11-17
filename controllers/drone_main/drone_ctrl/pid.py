"""Discrete PID controller with anti-windup and a filtered derivative.

Module: pid.py
Owner: M2
Inputs:  error e = reference - measurement, time step dt (s),
         optional derivative of the error (e.g. from a velocity sensor).
Outputs: control effort u (clamped to +/- output_limit if given).
Tests:   tests/test_pid.py

Control law (parallel form):
    u = Kp*e + Ki*integral(e dt) + Kd*d_f
where d_f is the derivative passed through a first-order low-pass filter
    d_f[k] = alpha*d_f[k-1] + (1 - alpha)*d_raw[k].

Anti-windup (conditional integration / clamping): the integrator is frozen while the
output is saturated and the error would push it further into saturation, and the
integral state itself is bounded by +/- integral_limit.
"""

from typing import Optional


class PIDController:
    """Scalar PID controller used by the altitude and position loops."""

    def __init__(self, kp: float, ki: float = 0.0, kd: float = 0.0,
                 output_limit: Optional[float] = None,
                 integral_limit: Optional[float] = None,
                 derivative_alpha: float = 0.0,
                 anti_windup: bool = True) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = output_limit
        self.integral_limit = integral_limit
        self.derivative_alpha = derivative_alpha
        self.anti_windup = anti_windup
        self.reset()

    def reset(self) -> None:
        """Clear integrator and derivative history."""
        self.integral = 0.0
        self.prev_error: Optional[float] = None
        self.d_filtered = 0.0
        self.saturated = False

    def _clamp(self, value: float, limit: Optional[float]) -> float:
        if limit is None:
            return value
        return max(-limit, min(value, limit))

    def compute(self, error: float, dt: float, error_dot: Optional[float] = None) -> float:
        """Return the control effort for one time step."""
        if dt <= 0.0:
            return 0.0

        # Derivative: use the supplied error rate if available (no derivative kick),
        # otherwise a finite difference of the error.
        if error_dot is not None:
            d_raw = error_dot
        elif self.prev_error is not None:
            d_raw = (error - self.prev_error) / dt
        else:
            d_raw = 0.0
        a = self.derivative_alpha
        self.d_filtered = a * self.d_filtered + (1.0 - a) * d_raw
        self.prev_error = error

        # Tentative integral update.
        candidate = self.integral + error * dt
        candidate = self._clamp(candidate, self.integral_limit)
        u_unsat = self.kp * error + self.ki * candidate + self.kd * self.d_filtered
        u = self._clamp(u_unsat, self.output_limit)
        self.saturated = u != u_unsat

        # Conditional integration: keep the old integral if saturated and the error
        # has the same sign as the saturated output (it would wind up further).
        if self.anti_windup and self.saturated and error * u_unsat > 0.0:
            u = self._clamp(self.kp * error + self.ki * self.integral + self.kd * self.d_filtered,
                            self.output_limit)
        else:
            self.integral = candidate
        return u
