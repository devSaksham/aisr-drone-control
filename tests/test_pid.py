"""Tests for pid.py (owner: M2)."""
from drone_ctrl.pid import PIDController


def test_proportional_only():
    assert PIDController(kp=2.0).compute(1.5, 0.01) == 3.0


def test_integral_accumulates():
    pid = PIDController(kp=0.0, ki=1.0)
    for _ in range(100):
        u = pid.compute(1.0, 0.01)
    assert abs(u - 1.0) < 1e-9


def test_output_is_clamped():
    assert PIDController(kp=10.0, output_limit=2.0).compute(5.0, 0.01) == 2.0


def test_anti_windup_freezes_integrator_when_saturated():
    with_aw = PIDController(kp=1.0, ki=5.0, output_limit=1.0)
    without = PIDController(kp=1.0, ki=5.0, output_limit=1.0, anti_windup=False)
    for _ in range(500):
        with_aw.compute(2.0, 0.01)
        without.compute(2.0, 0.01)
    assert with_aw.integral < 0.1 < without.integral


def test_derivative_filter_smooths_spikes():
    raw = PIDController(kp=0.0, kd=1.0, derivative_alpha=0.0)
    filt = PIDController(kp=0.0, kd=1.0, derivative_alpha=0.9)
    assert abs(filt.compute(0.0, 0.01, error_dot=10.0)) < abs(raw.compute(0.0, 0.01, error_dot=10.0))
