# Quadrotor Drone Altitude and Waypoint Control in Webots

**Course:** CSAI4014 Algorithms for Intelligent Systems and Robotics, B.Tech CSE (AI & ML), Sem VII
**Batch:** B1-B2 | **Group:** G13 | **Project:** P10
**Platform:** Webots R2025a, DJI Mavic 2 Pro model, Python 3.10+ controller

A simulated DJI Mavic 2 Pro takes off, holds a commanded altitude and flies through a
list of 3D waypoints, also under crosswind and sensor noise. Two cascaded controllers
are compared on identical scenarios:

- **Method A (baseline):** P/PD loops in the style of the Webots sample controller, step waypoint commands.
- **Method B (improved):** minimum-jerk trajectory, PID with anti-windup and a filtered
  derivative, position-to-velocity cascade with integral action, velocity and
  acceleration feedforward, thrust tilt compensation.

Both use the same attitude loop, mixer and Kalman velocity estimator. Every sign
convention was **measured** in Webots first (see `docs/frames.md`).

## Results (42 Webots runs)
Generated from `results/summary.csv`; see `results/summary_table.md` and the report.

| Experiment | Method A | Method B |
|---|---|---|
| E1 altitude steady-state error | 0.054 m | 0.003 m |
| E2 square: path RMSE / control effort | 0.063 m / 27.1 | 0.049 m / 12.1 |
| E3 3D mission: path RMSE | 0.275 m | 0.046 m |
| E4 crosswind: waypoints reached | 3 of 5 (stalls) | 5 of 5 |
| E5 sensor noise: successful runs | 8 / 10 | 10 / 10 |
| E6 roll-gain sweep 15-50: crashes at | 40, 50 | none |

## Quick start
```bash
git clone https://github.com/devSaksham/aisr-drone-control.git
cd aisr-drone-control
pip install -r requirements.txt
make test                      # or: run.bat test
```
Webots R2025a must be installed (default `C:\Program Files\Webots`; override with the
`WEBOTS_EXE` environment variable). LaTeX (MiKTeX/TeX Live) is needed for the report and
PowerPoint for exporting the slides to PDF.

| Command | What it does |
|---|---|
| `make test` | 56 unit tests |
| `make experiments` | all six scenarios, both methods, headless (about 20 min) |
| `make figures` | figures, tables, report numbers and the video script |
| `make report` | `report/report.pdf` (needs `report/upes_logo.png` from the faculty Overleaf zip) |
| `make slides` | `slides/slides.pptx` + `slides/slides.pdf` |
| `make demo` | live, rendered Webots run |

## Give the drone your own target points
```bash
python experiments/demo.py --points "0,0,1.5  2,1,2  -1,2,1  0,0,1" improved
python experiments/demo.py --points "0,0,2,0  3,0,2,1.57" baseline --wind 0.3
```
Each point is `x,y,z` in metres (world frame: x east, y north, z up), with an optional
4th value for the heading in radians. Altitude must be 0.5-5 m. The drone takes off from
(0, 0) and visits the points in order; the result is printed when the run ends.
The demo opens a copy of the world, so pressing *Save* in Webots cannot change the
experiment worlds (and the experiment runner refuses to run on a world that contains
saved simulation state).

## Team modules
| Slot | Member | Module | Files |
|---|---|---|---|
| M1 | Saksham Agrawal ([@devSaksham](https://github.com/devSaksham)) | State estimation and infrastructure | `drone_ctrl/config.py`, `sensors.py`, `logger.py`, `worlds/`, `controllers/sign_probe/` |
| M2 | Khushi Gupta ([@khushigupttaa04](https://github.com/khushigupttaa04)) | Altitude and attitude control | `drone_ctrl/pid.py`, `altitude.py`, `attitude.py`, `mixer.py` |
| M3 | Tanvi Singhal ([@deee5](https://github.com/deee5)) | Navigation and trajectory | `drone_ctrl/position.py`, `yaw.py`, `waypoints.py`, `trajectory.py` |
| M4 | Khyati Yadav ([@khyatiyadav06](https://github.com/khyatiyadav06)) | Integration and disturbance | `drone_main.py`, `drone_ctrl/baseline.py`, `improved.py`, `wind_supervisor/`, `experiments/demo.py` |
| M5 | Ambrish Chauraiya ([@ambrishchaurasia](https://github.com/ambrishchaurasia)) | Experiments and analysis | `experiments/`, `analysis/`, `slides/` |

## Repository map
```
controllers/drone_main/      controller entry point + drone_ctrl package (M1-M4)
controllers/wind_supervisor/ wind, crash watchdog, demo labels (M4)
controllers/sign_probe/      sign-convention probe (M1)
worlds/                      hover, square, wind, probe worlds
experiments/                 scenarios (YAML), batch runner, tuning harness, demo
analysis/                    metrics, figures, tables/report numbers
tests/                       unit tests, one file per module
report/                      LaTeX report on the faculty template (sections/ = one file per section)
slides/                      slide generator (PowerPoint)
docs/                        frames, references, tuning log, video script, viva Q&A, templates
results/                     summary.csv, figures (raw telemetry is regenerated, not committed)
```

## Integrity
No number in the report, slides or video script is typed by hand: all are generated
from `results/summary.csv`. Every tuning trial, including crashes, is in
`docs/tuning_log.md`. Faculty material (instructions, sample report, template zip and
logo) is kept local and is not part of this repository.
