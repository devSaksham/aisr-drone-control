"""Offline tests for baseline.py and improved.py (owner: M4).

A fake state is stepped through each controller without Webots to check the wiring:
outputs, take-off behaviour and reference continuity.
"""
from drone_ctrl.baseline import BaselineController
from drone_ctrl.config import BaselineGains, ImprovedGains, PhysicalParams
from drone_ctrl.improved import ImprovedController
from drone_ctrl.sensors import DroneState

WPS = [[0, 0, 1.5, 0], [1, 0, 1.5, 0]]


def test_baseline_on_ground_commands_climb_without_tilt():
    out = BaselineController(WPS, BaselineGains(), PhysicalParams(), 0.2).step(
        DroneState(z=0.1), 0.0, 0.008)
    assert out.roll_ref == 0 and out.pitch_ref == 0
    assert all(abs(m) > 68.5 for m in out.motors)


def test_baseline_airborne_tilts_toward_waypoint():
    out = BaselineController([[1, 0, 1.5, 0]], BaselineGains(), PhysicalParams(), 0.2).step(
        DroneState(z=1.5), 0.0, 0.008)
    assert out.pitch_ref > 0


def test_improved_spools_up_before_planning():
    c = ImprovedController(WPS, ImprovedGains(), PhysicalParams(), 0.2)
    out = c.step(DroneState(z=0.07), 0.0, 0.008)
    assert c._planned_index == -1 and abs(out.motors[0]) > 68.5


def test_improved_reference_starts_at_drone():
    c = ImprovedController(WPS, ImprovedGains(), PhysicalParams(), 0.2)
    out = c.step(DroneState(z=0.5, vz=0.8), 3.0, 0.008)
    assert abs(out.ref_pos[2] - 0.5) < 0.02
