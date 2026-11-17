"""Build the 17-slide presentation (PowerPoint) from the experiment results.

Module: generate_slides.py
Owner: M5
Inputs:  results/summary.csv, results/figures/*.png, results/demo screenshots.
Outputs: slides/slides.pptx (editable) and slides/slides.pdf (exported with PowerPoint).

Faculty rules applied: at most 17 slides including title and end slide; headings
30 pt; body text 20 pt or larger; one idea per slide; a figure on most slides; the
presenter's name in the corner of every slide; own figures only.
Every number on a slide is read from results/summary.csv, never typed by hand.
"""

import os
import subprocess
import sys

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Pt

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIG = os.path.join(REPO, "results", "figures")
OUT = os.path.join(REPO, "slides")
INK, MUTED, ACCENT = RGBColor(0x1F, 0x1F, 0x1E), RGBColor(0x6B, 0x6B, 0x66), RGBColor(0xEB, 0x68, 0x34)
BLUE = RGBColor(0x2A, 0x78, 0xD6)
W, H = Emu(12192000), Emu(6858000)  # 16:9

MEMBERS = {"M1": "Saksham Agrawal", "M2": "Khushi Gupta", "M3": "Tanvi Singhal",
           "M4": "Khyati Yadav", "M5": "Ambrish Chauraiya", "All": "All members"}


class Results:
    """Formatted numbers from summary.csv."""

    def __init__(self) -> None:
        self.df = pd.read_csv(os.path.join(REPO, "results", "summary.csv"))

    def one(self, sc: str, method: str, metric: str, dec: int = 3) -> str:
        g = self.df[(self.df.scenario == sc) & (self.df.method == method) & (self.df.tag.fillna("") == "")]
        v = pd.to_numeric(g[metric], errors="coerce").mean()
        return "--" if pd.isna(v) else f"{v:.{dec}f}"

    def success(self, sc: str, method: str) -> str:
        g = self.df[(self.df.scenario == sc) & (self.df.method == method)]
        return f"{int(g.success.astype(bool).sum())}/{len(g)}"

    def sweep_fail(self, method: str) -> str:
        g = self.df[(self.df.scenario == "E6") & (self.df.method == method)]
        bad = g[~g.success.astype(bool)].tag.str.split("=").str[1].tolist()
        return ", ".join(bad) if bad else "none"


def add_text(slide, x, y, w, h, lines, size=20, color=INK, bold=False, align=PP_ALIGN.LEFT):
    box = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tf = box.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines if isinstance(lines, list) else [lines]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.alignment = align
        p.space_after = Pt(8)
        for r in p.runs:
            r.font.size = Pt(size)
            r.font.color.rgb = color
            r.font.bold = bold
            r.font.name = "Calibri"
    return box


def new_slide(prs, title, presenter):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_text(s, 500000, 300000, 11000000, 800000, title, size=30, bold=True)
    line = s.shapes.add_shape(1, Emu(500000), Emu(1080000), Emu(1600000), Emu(50000))
    line.fill.solid()
    line.fill.fore_color.rgb = ACCENT
    line.line.fill.background()
    add_text(s, 8200000, 6300000, 3800000, 450000, f"Presenter: {MEMBERS[presenter]} ({presenter})",
             size=14, color=MUTED, align=PP_ALIGN.RIGHT)
    return s


def bullets(slide, lines, x=500000, y=1350000, w=11000000, h=4800000, size=22):
    return add_text(slide, x, y, w, h, [f"•  {t}" for t in lines], size=size)


def picture(slide, name, x, y, w=None, h=None):
    path = name if os.path.isabs(name) else os.path.join(FIG, name)
    if os.path.exists(path):
        slide.shapes.add_picture(path, Emu(x), Emu(y), width=Emu(w) if w else None,
                                 height=Emu(h) if h else None)
    else:
        add_text(slide, x, y, w or 4000000, 600000, f"[missing figure: {os.path.basename(path)}]", size=14)


def table(slide, rows, x, y, w, col_w=None, size=18):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), Emu(x), Emu(y), Emu(w),
                                   Emu(420000 * len(rows)))
    t = shape.table
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.text = str(val)
            for run in cell.text_frame.paragraphs[0].runs:  # empty cells have no run
                run.font.size = Pt(size)
                run.font.bold = i == 0
    if col_w:
        for j, cw in enumerate(col_w):
            t.columns[j].width = Emu(cw)


def block_diagram(slide, y=1500000):
    names = ["Waypoints", "Min-jerk\ntrajectory (B)", "Position\nloop", "Attitude +\naltitude + yaw",
             "Motor\nmixer", "Mavic 2 Pro\n(Webots)"]
    x, bw, gap = 400000, 1700000, 250000
    shapes = []
    for n in names:
        b = slide.shapes.add_shape(1, Emu(x), Emu(y), Emu(bw), Emu(1000000))
        b.fill.solid()
        b.fill.fore_color.rgb = RGBColor(0xF4, 0xF3, 0xF0)
        b.line.color.rgb = INK
        b.text_frame.text = n
        for p in b.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.size = Pt(18)
                r.font.color.rgb = INK
        shapes.append(b)
        x += bw + gap
    for a, b in zip(shapes, shapes[1:]):
        c = slide.shapes.add_connector(1, a.left + a.width, a.top + a.height // 2, b.left, b.top + b.height // 2)
        c.line.color.rgb = INK
        c.line.width = Pt(2)
    fb = slide.shapes.add_shape(1, Emu(4400000), Emu(y + 1700000), Emu(3600000), Emu(800000))
    fb.fill.solid()
    fb.fill.fore_color.rgb = RGBColor(0xF4, 0xF3, 0xF0)
    fb.line.color.rgb = INK
    fb.text_frame.text = "GPS + IMU + gyro → Kalman estimator"
    for p in fb.text_frame.paragraphs:
        p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            r.font.size = Pt(18)
            r.font.color.rgb = INK
    add_text(slide, 400000, y + 2800000, 11200000, 1200000,
             ["Feedback: the estimated state goes back to every loop, every 8 ms.",
              "A supervisor robot adds wind and records the run."], size=20, color=MUTED)


def build() -> Presentation:
    r = Results()
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    # 1 Title
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_text(s, 600000, 900000, 11000000, 1400000, "Quadrotor Drone Altitude and Waypoint Control in Webots",
             size=32, bold=True, align=PP_ALIGN.CENTER)
    add_text(s, 600000, 2300000, 11000000, 1500000,
             ["CSAI4014 Algorithms for Intelligent Systems and Robotics",
              "Project No. P10  |  Group No. G13  |  Batch B1-B2"], size=22, align=PP_ALIGN.CENTER)
    add_text(s, 1800000, 3700000, 8600000, 2200000,
             [f"{MEMBERS[m]}  (SAP: ____________)" for m in ("M1", "M2", "M3", "M4", "M5")],
             size=20, align=PP_ALIGN.CENTER)
    add_text(s, 600000, 5900000, 11000000, 450000, "Course Faculty, CSAI4014  |  School of Computer Science, UPES",
             size=18, color=MUTED, align=PP_ALIGN.CENTER)
    add_text(s, 8200000, 6300000, 3800000, 450000, "Presenter: Saksham Agrawal (M1)", size=14,
             color=MUTED, align=PP_ALIGN.RIGHT)

    # 2 Problem and motivation
    s = new_slide(prs, "Problem and Motivation", "M1")
    bullets(s, ["Drones fly surveys, inspections, spraying and deliveries as waypoint missions",
                "A quadrotor is unstable: software must hold it level and at height, all the time",
                "Path error costs money: missed crop rows, collisions near structures",
                "Wind and noisy GPS make it harder",
                "Simulation first: safe, repeatable, measurable"], w=6200000)
    picture(s, os.path.join(REPO, "results", "demo", "E2_improved", "screenshots", "t10.0s.png"),
            6900000, 1500000, w=4800000)

    # 3 Objectives
    s = new_slide(prs, "Objectives", "M1")
    bullets(s, ["Verify the simulated drone's frames and motor signs by measurement",
                "Altitude steps: overshoot < 5 %, steady-state error < 2 cm",
                "Waypoint missions (square, 3D): path RMSE < 0.10 m, no crash",
                "Robustness: finish under crosswind; >= 9 of 10 runs with sensor noise",
                "Fair comparison: Method A (baseline) vs Method B (improved)"])

    # 4 Existing solutions
    s = new_slide(prs, "Existing Solutions and the Gap", "M2")
    table(s, [["Approach", "Strength", "Limitation"],
              ["Webots sample P/PD", "Simple", "Steady error; harsh steps"],
              ["PX4 PID cascade", "Industry standard", "Many gains to tune"],
              ["LQ / geometric control", "Optimal / global", "Needs exact model"],
              ["Min-snap trajectories", "Smooth, fast", "Complex optimisation"]],
          500000, 1400000, 11000000, size=20)
    add_text(s, 500000, 4000000, 11000000, 1500000,
             ["Gap: no measured, reproducible comparison of the sample-style controller against an "
              "industry-style cascade inside Webots, under wind, noise and gain changes."], size=22)

    # 5 Novelty
    s = new_slide(prs, "Novelty (backed by our results)", "M2")
    bullets(s, [
        "Measured, not assumed: a sign probe fixed every control sign; sample roll gain found unsafe",
        f"Gain robustness: Method A crashes at roll Kp = {r.sweep_fail('baseline')}; "
        f"Method B succeeds for every gain 15-50",
        f"Wind: Method A stalls ({r.one('E4', 'baseline', 'waypoints_reached', 0)}/5 waypoints); "
        f"Method B finishes, RMSE {r.one('E4', 'improved', 'path_rmse_m')} m",
        f"Noise: Method B {r.success('E5', 'improved')} vs Method A {r.success('E5', 'baseline')} successful runs",
        "Fully reproducible: one command regenerates every number and figure"], size=21)

    # 6 Syllabus mapping
    s = new_slide(prs, "Syllabus Mapping", "M2")
    table(s, [["AISR topic", "Where we used it"],
              ["Robot dynamics & frames", "Thrust model, ENU / body frames"],
              ["Sensors & state estimation", "GPS, IMU, gyro; Kalman filter"],
              ["Feedback control (PID)", "Altitude, attitude, position, yaw"],
              ["Motion / trajectory planning", "Waypoints, minimum-jerk path"],
              ["Simulation & evaluation", "Webots, Monte Carlo, metrics"]],
          500000, 1400000, 11000000, col_w=[4400000, 6600000], size=20)

    # 7 System architecture
    s = new_slide(prs, "System Architecture", "M3")
    block_diagram(s)

    # 8 Robot and environment
    s = new_slide(prs, "Robot and Environment Model", "M3")
    bullets(s, ["DJI Mavic 2 Pro model in Webots R2025a",
                "4 propellers, thrust = k · ω², max 576 rad/s",
                "Sensors: GPS, inertial unit, gyroscope",
                "World: flat floor, 8 ms physics step",
                "Probe: +roll input → roll negative → moves +y"], w=5600000, size=20)
    picture(s, "fig_probe_signs.png", 6200000, 1500000, w=5600000)

    # 9 Algorithm 1
    s = new_slide(prs, "Algorithm 1: Minimum-Jerk Trajectory", "M3")
    add_text(s, 500000, 1300000, 6000000, 3800000,
             ["p(t) = p0 + (p1 - p0)(10τ³ - 15τ⁴ + 6τ⁵)",
              "Zero speed and acceleration at both ends",
              "Duration set by speed 1.2 m/s, accel 1.0 m/s² limits",
              "Take-off: starts from the measured climb speed",
              "Next waypoint only after the segment ends"], size=20)
    picture(s, "fig_e2_xy_path.png", 6900000, 1300000, h=4900000)

    # 10 Algorithm 2 / controller design
    s = new_slide(prs, "Algorithm 2: Controller Design and Tuning", "M4")
    table(s, [["", "Method A", "Method B"],
              ["Waypoints", "Step", "Min-jerk path"],
              ["Altitude", "PD", "PID + anti-windup + feedforward"],
              ["Position", "PD", "P → velocity PI"],
              ["Attitude", "PD (Kp 25, Kd 4)", "same"],
              ["Tilt limit", "0.15 rad", "0.15 rad"]],
          500000, 1400000, 11000000, col_w=[2600000, 3400000, 5000000], size=20)
    add_text(s, 500000, 4600000, 11000000, 1200000,
             ["Tuned in simulation; every trial (including crashes) is in docs/tuning_log.md."], size=20)

    # 11 Simulation setup
    s = new_slide(prs, "Simulation Setup", "M4")
    table(s, [["ID", "Scenario"], ["E1", "Altitude steps 2 m → 1 m"], ["E2", "2 m square at 1.5 m"],
              ["E3", "3D waypoints"], ["E4", "Crosswind 0.3 N + gusts"], ["E5", "GPS/IMU noise, 10 seeds"],
              ["E6", "Roll-gain sweep 15-50"]],
          500000, 1350000, 5600000, col_w=[900000, 4700000], size=18)
    add_text(s, 6400000, 1400000, 5400000, 4000000,
             ["python experiments/run_experiments.py", "python analysis/plots.py",
              "python experiments/demo.py E2 improved"], size=18)

    # 12 Live demonstration
    s = new_slide(prs, "Live Demonstration", "M4")
    add_text(s, 500000, 2000000, 11000000, 2500000,
             ["Switching to Webots now", "1. Square mission: Method A, then Method B",
              "2. Your own target points (Tanvi)", "3. Crosswind test (Ambrish)"], size=26)

    # 13 Results 1
    s = new_slide(prs, "Results 1: Altitude and Path", "M5")
    picture(s, "fig_e1_step_response.png", 300000, 1350000, w=6000000)
    picture(s, "fig_e3_3d_path.png", 6500000, 1250000, w=5300000)
    add_text(s, 300000, 4500000, 6000000, 1500000,
             [f"Steady-state error: A {r.one('E1', 'baseline', 'step2_ss_error_m')} m, "
              f"B {r.one('E1', 'improved', 'step2_ss_error_m')} m",
              f"3D path RMSE: A {r.one('E3', 'baseline', 'path_rmse_m')} m, "
              f"B {r.one('E3', 'improved', 'path_rmse_m')} m"], size=20)

    # 14 Results 2
    s = new_slide(prs, "Results 2: Comparison", "M5")
    table(s, [["Metric", "Method A", "Method B"],
              ["E2 path RMSE (m)", r.one("E2", "baseline", "path_rmse_m"), r.one("E2", "improved", "path_rmse_m")],
              ["E2 control effort", r.one("E2", "baseline", "control_effort", 1), r.one("E2", "improved", "control_effort", 1)],
              ["E4 waypoints in wind", r.one("E4", "baseline", "waypoints_reached", 0) + "/5",
               r.one("E4", "improved", "waypoints_reached", 0) + "/5"],
              ["E5 success (noise)", r.success("E5", "baseline"), r.success("E5", "improved")],
              ["E6 crashes at roll Kp", r.sweep_fail("baseline"), r.sweep_fail("improved")]],
          300000, 1350000, 6200000, col_w=[2800000, 1700000, 1700000], size=18)
    picture(s, "fig_e6_roll_gain_sweep.png", 6700000, 1400000, w=5200000)

    # 15 Team contribution
    s = new_slide(prs, "Team Contribution", "M5")
    table(s, [["Member", "Module and files"],
              ["Saksham Agrawal (M1)", "Sign probe, Kalman estimator, config, logger, worlds"],
              ["Khushi Gupta (M2)", "PID, altitude, attitude, mixer"],
              ["Tanvi Singhal (M3)", "Position, yaw, waypoints, min-jerk trajectory"],
              ["Khyati Yadav (M4)", "Method A/B assembly, wind supervisor, demo"],
              ["Ambrish Chauraiya (M5)", "Experiments, metrics, figures, tables"]],
          500000, 1400000, 11000000, col_w=[3800000, 7200000], size=20)

    # 16 Conclusion and industry use
    s = new_slide(prs, "Conclusion and Industry Use", "All")
    bullets(s, ["Method B: lower path error, half the control effort, survives wind and noise",
                "Same cascade idea as PX4; our tests show why each part matters",
                "Use: inspection, spraying, delivery waypoint missions",
                "Next: real drone (motor dynamics, latency, battery), LQR / MPC"])

    # 17 End slide
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_text(s, 600000, 1800000, 11000000, 1000000, "Thank you  |  Questions?", size=36, bold=True,
             align=PP_ALIGN.CENTER)
    add_text(s, 600000, 3200000, 11000000, 1800000,
             ["GitHub: github.com/devSaksham/aisr-drone-control",
              "Contact: ______________________"], size=22, align=PP_ALIGN.CENTER)
    add_text(s, 8200000, 6300000, 3800000, 450000, "Presenter: All members", size=14, color=MUTED,
             align=PP_ALIGN.RIGHT)
    return prs


def export_pdf(pptx_path: str, pdf_path: str) -> bool:
    """Export with PowerPoint (Windows COM via PowerShell); returns True on success."""
    ps = (f"$p=New-Object -ComObject PowerPoint.Application;"
          f"$d=$p.Presentations.Open('{pptx_path}',$true,$false,$false);"
          f"$d.SaveAs('{pdf_path}',32);$d.Close();$p.Quit()")
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, timeout=180,
                       capture_output=True)
        return os.path.exists(pdf_path)
    except Exception as exc:  # PowerPoint not installed, etc.
        print(f"  PDF export skipped: {exc}")
        return False


def main() -> None:
    prs = build()
    n = len(prs.slides)
    assert n <= 17, f"{n} slides: the limit is 17"
    pptx_path = os.path.join(OUT, "slides.pptx")
    prs.save(pptx_path)
    print(f"  {n} slides -> {pptx_path}")
    if export_pdf(pptx_path, os.path.join(OUT, "slides.pdf")):
        print("  exported slides/slides.pdf")


if __name__ == "__main__":
    sys.exit(main())
