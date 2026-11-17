"""Waypoint manager: sequential switching with arrival tolerance and hold time.

Module: waypoints.py
Owner: M3
Inputs:  waypoint list [[x, y, z, yaw], ...], current position, sim time t, dt.
Outputs: active waypoint, index, finished flag, and the time each waypoint was reached.
Tests:   tests/test_waypoints.py

A waypoint counts as reached when the 3D distance stays below `tolerance_m` for
`hold_time_s` seconds. The manager then advances to the next waypoint; after the last
one it reports the mission as finished. In timed mode (`switch_times`) the waypoints
change at fixed times instead, which gives both methods identical step commands.
"""

import math
from typing import List, Optional, Sequence, Tuple


class WaypointManager:
    """Sequential waypoint state machine."""

    def __init__(self, waypoints: Sequence[Sequence[float]], tolerance_m: float = 0.25,
                 hold_time_s: float = 0.5,
                 switch_times: Optional[Sequence[float]] = None) -> None:
        self.waypoints: List[List[float]] = []
        for wp in waypoints or [[0.0, 0.0, 1.0, 0.0]]:
            w = [float(v) for v in wp]
            if len(w) == 3:
                w.append(0.0)
            self.waypoints.append(w)
        self.tolerance_m = tolerance_m
        self.hold_time_s = hold_time_s
        self.index = 0
        self.finished = False
        self._hold = 0.0
        self.reach_times: List[Optional[float]] = [None] * len(self.waypoints)
        # Timed mode (used for step-response tests): waypoint i becomes active at
        # switch_times[i] regardless of where the drone is.
        self.switch_times = list(switch_times) if switch_times else None

    @property
    def target(self) -> List[float]:
        return self.waypoints[self.index]

    def distance(self, pos: Sequence[float]) -> float:
        t = self.target
        return math.sqrt(sum((t[i] - pos[i]) ** 2 for i in range(3)))

    def update(self, pos: Sequence[float], t: float, dt: float,
               allow_advance: bool = True) -> Tuple[List[float], bool]:
        """Advance the state machine; returns (active_waypoint, finished)."""
        if self.switch_times is not None:
            while self.index + 1 < len(self.waypoints) and t >= self.switch_times[self.index + 1]:
                self.index += 1
            return self.target, False
        if self.finished:
            return self.target, True
        if self.distance(pos) <= self.tolerance_m:
            self._hold += dt
            if self._hold >= self.hold_time_s and allow_advance:
                self.reach_times[self.index] = t
                self._hold = 0.0
                if self.index + 1 < len(self.waypoints):
                    self.index += 1
                else:
                    self.finished = True
        else:
            self._hold = 0.0
        return self.target, self.finished
