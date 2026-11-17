"""Tests for attitude.py (owner: M2). Signs follow docs/frames.md."""
from drone_ctrl.attitude import AttitudeController


def test_positive_roll_gives_positive_roll_input():
    # A positive roll input drives roll negative, so it is the restoring action.
    roll_in, _ = AttitudeController().compute(0.0, 0.1, 0.0, 0.0, 0.0, 0.0)
    assert roll_in > 0


def test_reference_shifts_equilibrium():
    roll_in, pitch_in = AttitudeController().compute(0.1, 0.1, 0.0, -0.05, -0.05, 0.0)
    assert roll_in == 0 and pitch_in == 0


def test_rate_damping_sign():
    _, pitch_in = AttitudeController().compute(0, 0, 0, 0, 0, 1.0)
    assert pitch_in > 0


def test_output_saturates():
    roll_in, _ = AttitudeController(kp_roll=100, max_input=5).compute(0, 1.0, 0, 0, 0, 0)
    assert roll_in == 5
