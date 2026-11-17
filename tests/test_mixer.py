"""Tests for mixer.py (owner: M2). Signs follow the Webots sample controller."""
from drone_ctrl.mixer import MotorMixer


def test_hover_signs():
    assert MotorMixer(68.5).mix(0, 0, 0, 0) == [68.5, -68.5, -68.5, 68.5]


def test_roll_input_speeds_up_right_side():
    fl, fr, rl, rr = MotorMixer(68.5).magnitudes(0, 1.0, 0, 0)
    assert fr > fl and rr > rl


def test_pitch_input_speeds_up_front():
    fl, fr, rl, rr = MotorMixer(68.5).magnitudes(0, 0, 1.0, 0)
    assert fl > rl and fr > rr


def test_yaw_input_pattern():
    fl, fr, rl, rr = MotorMixer(68.5).magnitudes(0, 0, 0, 1.0)
    assert fr > fl and rl > rr


def test_saturation():
    assert max(MotorMixer(68.5, max_speed=100).magnitudes(100, 0, 0, 0)) == 100
    assert min(MotorMixer(68.5).magnitudes(-100, 0, 0, 0)) == 0
