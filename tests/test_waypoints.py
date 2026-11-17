"""Tests for waypoints.py (owner: M3)."""
from drone_ctrl.waypoints import WaypointManager


def test_advances_after_hold_time():
    wm = WaypointManager([[0, 0, 1], [1, 0, 1]], tolerance_m=0.1, hold_time_s=0.05)
    for k in range(10):
        wm.update((0, 0, 1), k * 0.01, 0.01)
    assert wm.index == 1 and wm.reach_times[0] is not None


def test_no_advance_outside_tolerance():
    wm = WaypointManager([[0, 0, 1], [1, 0, 1]], tolerance_m=0.1, hold_time_s=0.0)
    wm.update((0.5, 0, 1), 0.0, 0.01)
    assert wm.index == 0


def test_finishes_on_last_waypoint():
    wm = WaypointManager([[0, 0, 1]], tolerance_m=0.1, hold_time_s=0.0)
    assert wm.update((0, 0, 1), 0.0, 0.01)[1]


def test_allow_advance_gate():
    wm = WaypointManager([[0, 0, 1], [1, 0, 1]], tolerance_m=0.1, hold_time_s=0.0)
    wm.update((0, 0, 1), 0.0, 0.01, allow_advance=False)
    assert wm.index == 0


def test_timed_mode():
    wm = WaypointManager([[0, 0, 2], [0, 0, 1]], switch_times=[0.0, 15.0])
    assert wm.update((9, 9, 9), 14.9, 0.01)[0][2] == 2
    assert wm.update((9, 9, 9), 15.0, 0.01)[0][2] == 1
