# Quadrotor Drone Altitude and Waypoint Control in Webots

**Course:** CSAI4014 Algorithms for Intelligent Systems and Robotics, B.Tech CSE (AI & ML), Sem VII
**Batch:** B1-B2 | **Group:** G13 | **Project:** P10
**Platform:** Webots R2025a, DJI Mavic 2 Pro model, Python 3.10+ controller

> Status: work in progress. Sections marked *TODO* are filled in as each module is
> built and verified in simulation. No result in this repository is written by hand;
> every number comes from `results/summary.csv`, produced by real Webots runs.

## What this project does
A simulated DJI Mavic 2 Pro takes off, holds a commanded altitude and flies through a
list of 3D waypoints, also under wind and sensor noise. Two cascaded controllers are
compared on the same scenarios:

- **Method A (baseline):** P/PD loops in the style of the Webots sample controller, step waypoint commands.
- **Method B (improved):** PID with anti-windup and filtered derivative, minimum-jerk
  trajectory, velocity feedback in the position loop, hover-thrust feedforward.

## Quick start
```bash
git clone https://github.com/devSaksham/aisr-drone-control.git
cd aisr-drone-control
pip install -r requirements.txt
make test          # or: run.bat test
```

Webots R2025a must be installed (default path `C:\Program Files\Webots`).

| Command | What it does |
|---|---|
| `make test` | Unit tests (pytest) |
| `make experiments` | Headless Webots runs for all scenarios |
| `make figures` | Figures and tables from `results/` |
| `make report` | Build `report/report.pdf` |
| `make slides` | Build the slide deck |

## Team modules
| Slot | Module | Files |
|---|---|---|
| M1 | State estimation and infrastructure | `drone_ctrl/config.py`, `sensors.py`, `logger.py`, `worlds/` |
| M2 | Altitude and attitude control | `drone_ctrl/pid.py`, `altitude.py`, `attitude.py`, `mixer.py` |
| M3 | Navigation and trajectory | `drone_ctrl/position.py`, `yaw.py`, `waypoints.py`, `trajectory.py` |
| M4 | Integration and disturbance | `drone_main.py`, `drone_ctrl/baseline.py`, `improved.py`, `wind_supervisor/` |
| M5 | Experiments and analysis | `experiments/`, `analysis/`, `slides/` |

Member names are added once assigned. *TODO*
