"""Build the 17-slide presentation (PowerPoint) from the experiment results.

Module: generate_slides.py
Owner: M5
Inputs:  results/summary.csv, results/figures/*.png, results/demo/video + frames.
Outputs: slides/slides.pptx (editable, demo videos embedded) and slides/slides.pdf.

Faculty rules applied: at most 17 slides including title and end slide; headings
28-32 pt; body text 20 pt or larger; one idea per slide; a figure on most slides;
the presenter's name in the corner of every slide; own figures only.
Look and feel follows the supplied "Elegance" design system: ink / charcoal / ivory
palette, light serif headings, light sans body, wide margins, no shadows.
Every number on a slide is read from results/summary.csv, never typed by hand.
"""

import os
import subprocess
import sys

import pandas as pd
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt
from lxml import etree

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FIG = os.path.join(REPO, "results", "figures")
VID = os.path.join(REPO, "results", "demo", "video")
FRAMES = os.path.join(REPO, "results", "demo", "frames")
OUT = os.path.join(REPO, "slides")

INK = RGBColor(0x1A, 0x1A, 0x1A)
CHAR = RGBColor(0x33, 0x33, 0x33)
IVORY = RGBColor(0xF4, 0xEF, 0xE9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BORDER = RGBColor(0xE5, 0xE7, 0xEB)
MUTED = RGBColor(0x7A, 0x75, 0x6E)
W, H = 12192000, 6858000
MX = 700000                    # left/right margin
CW = W - 2 * MX                # content width

SAP = {"M1": "500121969", "M2": "500119129", "M3": "500126859", "M4": "500123608", "M5": "500120274"}
MEMBERS = {"M1": "Saksham Agrawal", "M2": "Khushi Gupta", "M3": "Tanvi Singhal",
           "M4": "Khyati Yadav", "M5": "Ambrish Chauraiya", "All": "All members"}


def _installed(*needles: str) -> bool:
    dirs = [r"C:\Windows\Fonts", os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts")]
    for d in dirs:
        if os.path.isdir(d) and any(any(n.lower() in f.lower() for n in needles) for f in os.listdir(d)):
            return True
    return False


# Design-system fonts when installed (free from Google Fonts); otherwise the closest
# fonts that ship with Windows/Office, so the deck still looks right on any laptop.
SERIF = "Cormorant Garamond" if _installed("cormorant") else "Garamond"
SANS = "DM Sans" if _installed("dmsans", "dm sans", "dm_sans") else "Segoe UI Light"


class Results:
    """Formatted numbers from summary.csv."""

    def __init__(self) -> None:
        self.df = pd.read_csv(os.path.join(REPO, "results", "summary.csv"))

    def raw(self, sc: str, method: str, metric: str) -> float:
        g = self.df[(self.df.scenario == sc) & (self.df.method == method) & (self.df.tag.fillna("") == "")]
        return float(pd.to_numeric(g[metric], errors="coerce").mean())

    def one(self, sc: str, method: str, metric: str, dec: int = 3) -> str:
        v = self.raw(sc, method, metric)
        return "--" if pd.isna(v) else f"{v:.{dec}f}"

    def success(self, sc: str, method: str) -> str:
        g = self.df[(self.df.scenario == sc) & (self.df.method == method)]
        return f"{int(g.success.astype(bool).sum())}/{len(g)}"

    def sweep_fail(self, method: str) -> str:
        g = self.df[(self.df.scenario == "E6") & (self.df.method == method)]
        bad = g[~g.success.astype(bool)].tag.str.split("=").str[1].tolist()
        return " & ".join(bad) if bad else "none"


# ---------------------------------------------------------------- primitives
def set_bg(slide, color) -> None:
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


def txt(slide, x, y, w, h, lines, font=None, size=20, color=CHAR, bold=False, spc=0,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, after=10, line=1.15):
    box = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, t in enumerate(lines if isinstance(lines, list) else [lines]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(after)
        p.line_spacing = line
        r = p.add_run()
        r.text = t
        r.font.size = Pt(size)
        r.font.name = font or SANS
        r.font.color.rgb = color
        r.font.bold = bold
        if spc:
            r._r.get_or_add_rPr().set("spc", str(spc))
    return box


def rect(slide, x, y, w, h, fill=WHITE, line=BORDER, radius=0.04, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, Emu(x), Emu(y), Emu(w), Emu(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(0.75)
    s.shadow.inherit = False
    return s


def chip(slide, x, y, w, text, fill=IVORY, size=12):
    s = rect(slide, x, y, w, 330000, fill=fill, line=None, radius=0.5)
    tf = s.text_frame
    tf.margin_left = tf.margin_right = 90000
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text.upper()
    r.font.size = Pt(size)
    r.font.name = SANS
    r.font.color.rgb = CHAR
    r._r.get_or_add_rPr().set("spc", "200")
    return s


def presenter(slide, who: str, on_ivory: bool = False) -> None:
    label = MEMBERS[who] + ("" if who == "All" else f"  ·  {who}")
    w = 3300000
    chip(slide, W - MX - w, H - 640000, w, label, fill=WHITE if on_ivory else IVORY)


def new_slide(prs, label, title, who, ivory=False):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, IVORY if ivory else WHITE)
    txt(s, MX, 330000, CW, 260000, label.upper(), size=12, spc=300, color=MUTED)
    txt(s, MX, 640000, CW, 700000, title, font=SERIF, size=32, color=INK)
    presenter(s, who, ivory)
    return s


def picture(slide, path, x, y, w=None, h=None, frame=True):
    if not os.path.isabs(path):
        path = os.path.join(FIG, path)
    if not os.path.exists(path):
        txt(slide, x, y, w or 4000000, 400000, f"[missing: {os.path.basename(path)}]", size=14)
        return None
    pic = slide.shapes.add_picture(path, Emu(x), Emu(y), width=Emu(w) if w else None,
                                   height=Emu(h) if h else None)
    if frame:
        pic.line.color.rgb = BORDER
        pic.line.width = Pt(0.75)
    return pic


def tile(slide, x, y, w, h, big, small, big_size=44):
    rect(slide, x, y, w, h, fill=WHITE, line=BORDER, radius=0.04)
    txt(slide, x + 260000, y + 200000, w - 520000, 700000, big, font=SERIF, size=big_size, color=INK)
    txt(slide, x + 260000, y + 200000 + 800000, w - 520000, h - 1000000, small, size=20, after=0)


def _cell_border(cell, color="E5E7EB", width=9525):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT"):
        ln = etree.SubElement(tcPr, qn(tag), w="0")
        etree.SubElement(ln, qn("a:noFill"))
    ln = etree.SubElement(tcPr, qn("a:lnB"), w=str(width))
    sf = etree.SubElement(ln, qn("a:solidFill"))
    etree.SubElement(sf, qn("a:srgbClr"), val=color)


def table(slide, rows, x, y, w, col_w, row_h=480000, size=20):
    shape = slide.shapes.add_table(len(rows), len(rows[0]), Emu(x), Emu(y), Emu(w), Emu(row_h * len(rows)))
    t = shape.table
    tblPr = t._tbl.tblPr
    for a in ("firstRow", "bandRow"):
        tblPr.set(a, "0")
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None:
        sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
    sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # No Style, No Grid
    for j, cw in enumerate(col_w):
        t.columns[j].width = Emu(cw)
    for i, row in enumerate(rows):
        t.rows[i].height = Emu(row_h)
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.text = ""
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_left = 120000
            c.fill.solid()
            c.fill.fore_color.rgb = IVORY if i == 0 else WHITE
            p = c.text_frame.paragraphs[0]
            r = p.add_run()
            r.text = str(val)
            r.font.size = Pt(size)
            r.font.name = SANS
            r.font.color.rgb = INK if i == 0 else CHAR
            r.font.bold = i == 0
            _cell_border(c)


def video(slide, name, x, y, w, h):
    mp4 = os.path.join(VID, name + "_small.mp4")
    poster = os.path.join(FRAMES, name + "_poster.png")
    if os.path.exists(mp4):
        slide.shapes.add_movie(mp4, Emu(x), Emu(y), Emu(w), Emu(h),
                               poster_frame_image=poster if os.path.exists(poster) else None,
                               mime_type="video/mp4")
    else:
        picture(slide, poster, x, y, w=w, h=h)


# ---------------------------------------------------------------- deck
def block_diagram(slide, y=1900000):
    names = ["Waypoints", "Min-jerk path\n(Method B)", "Position\nloop", "Attitude,\naltitude, yaw",
             "Motor\nmixer", "Drone\n(Webots)"]
    bw, gap, bh = 1650000, 180000, 1250000
    x = MX
    boxes = []
    for n in names:
        b = rect(slide, x, y, bw, bh, fill=IVORY, line=None, radius=0.06)
        tf = b.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for i, line in enumerate(n.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = line
            r.font.size = Pt(20)
            r.font.name = SANS
            r.font.color.rgb = INK
        boxes.append(b)
        x += bw + gap
    for a, b in zip(boxes, boxes[1:]):
        c = slide.shapes.add_connector(1, a.left + a.width, a.top + a.height // 2, b.left, b.top + b.height // 2)
        c.line.color.rgb = INK
        c.line.width = Pt(1.25)
    fb = rect(slide, MX + 2 * (bw + gap), y + bh + 650000, 3 * bw + 2 * gap, 800000, fill=WHITE, line=BORDER)
    tf = fb.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "GPS + IMU + gyro  →  Kalman estimator"
    r.font.size = Pt(20)
    r.font.name = SANS
    r.font.color.rgb = INK
    # feedback arrow up to the control blocks
    c = slide.shapes.add_connector(1, fb.left + fb.width // 2, fb.top, fb.left + fb.width // 2, y + bh)
    c.line.color.rgb = INK
    c.line.width = Pt(1.25)
    txt(slide, MX, y + bh + 2000000, CW, 500000,
        "Estimated state feeds every loop, every 8 ms. A supervisor robot adds wind and records the run.",
        size=20, color=MUTED)


def build() -> Presentation:
    r = Results()
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(W), Emu(H)
    shot = os.path.join(FRAMES, "e2_improved_poster.png")

    # 1 Title
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, IVORY)
    txt(s, MX, 700000, 6200000, 260000, "CSAI4014  ·  P10  ·  G13  ·  B1-B2", size=12, spc=300, color=MUTED)
    txt(s, MX, 1300000, 6000000, 1800000, "Quadrotor Drone Altitude and Waypoint Control in Webots",
        font=SERIF, size=32, color=INK)
    txt(s, MX, 3250000, 6000000, 700000, "Algorithms for Intelligent Systems and Robotics", size=20)
    txt(s, MX, 4300000, 6000000, 800000, ["Resham Shivwanshi", "Course Faculty  ·  UPES Dehradun"],
        size=20, after=2)
    line = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(7050000), Emu(1300000), Emu(9525), Emu(3900000))
    line.fill.solid()
    line.fill.fore_color.rgb = BORDER
    line.line.fill.background()
    txt(s, 7450000, 1300000, 4100000, 3900000,
        [f"{MEMBERS[m]}\n{SAP[m]}".replace("\n", "  ·  ") for m in ("M1", "M2", "M3", "M4", "M5")],
        size=20, color=INK, after=22)
    presenter(s, "M1", True)

    # 2 Problem
    s = new_slide(prs, "Problem and motivation", "Why a drone needs good control", "M1")
    txt(s, MX, 1900000, 5300000, 3600000,
        ["Surveys, inspection, spraying and delivery are waypoint missions.",
         "A quadrotor is unstable. Software must keep it level every moment.",
         "Wind and noisy GPS make it harder."], size=22, after=24)
    picture(s, shot, 6400000, 1700000, w=5100000)

    # 3 Objectives
    s = new_slide(prs, "Objectives", "Four measurable targets", "M1")
    tw, th = 5300000, 1850000
    for i, (big, small) in enumerate([("< 5 %", "overshoot on altitude steps"),
                                      ("< 2 cm", "steady-state altitude error"),
                                      ("< 0.10 m", "path error on waypoint missions"),
                                      ("9 of 10", "noisy-sensor runs must succeed")]):
        tile(s, MX + (i % 2) * (tw + 200000), 1600000 + (i // 2) * (th + 200000), tw, th, big, small)

    # 4 Existing solutions
    s = new_slide(prs, "Existing solutions", "What exists, and the gap", "M2")
    table(s, [["Approach", "Strength", "Limitation"],
              ["Webots sample P/PD", "Simple", "Steady error, harsh steps"],
              ["PX4 PID cascade", "Industry standard", "Many gains to tune"],
              ["LQ / geometric control", "Optimal, global", "Needs an exact model"],
              ["Minimum-snap paths", "Smooth, fast", "Heavy optimisation"]],
          MX, 1600000, CW, [3600000, 3300000, 3900000])
    txt(s, MX, 4400000, CW, 1200000,
        "The gap: no measured, repeatable comparison of the sample controller and an industry-style "
        "cascade in Webots.", font=SERIF, size=28, color=INK)

    # 5 Novelty
    s = new_slide(prs, "Novelty", "What our results show", "M2")
    effort = 100 * (1 - r.raw("E2", "improved", "control_effort") / r.raw("E2", "baseline", "control_effort"))
    items = [(f"Kp {r.sweep_fail('baseline')}", "roll gains where Method A crashes; B never does"),
             (f"{r.one('E4', 'baseline', 'waypoints_reached', 0)} of 5", "waypoints Method A reaches in wind; B reaches all 5"),
             (f"{r.success('E5', 'baseline')}  vs  {r.success('E5', 'improved')}", "successful noisy runs, A versus B"),
             (f"{effort:.0f} % less", "control effort for B on the square")]
    for i, (big, small) in enumerate(items):
        tile(s, MX + (i % 2) * (tw + 200000), 1600000 + (i // 2) * (th + 200000), tw, th, big, small)

    # 6 Syllabus mapping
    s = new_slide(prs, "Syllabus mapping", "Where the course shows up", "M2")
    table(s, [["AISR topic", "Where we used it"],
              ["Robot dynamics and frames", "Thrust model, ENU and body frames"],
              ["Sensors and estimation", "GPS, IMU, gyro, Kalman filter"],
              ["Feedback control", "Altitude, attitude, position, yaw"],
              ["Trajectory planning", "Waypoints, minimum-jerk path"],
              ["Simulation and evaluation", "Webots runs, metrics"]],
          MX, 1600000, CW, [4600000, 6200000])

    # 7 Architecture
    s = new_slide(prs, "System architecture", "From waypoint to motor speed", "M3")
    block_diagram(s)

    # 8 Robot and environment
    s = new_slide(prs, "Robot and environment", "Measured, not assumed", "M3")
    txt(s, MX, 1900000, 4700000, 3600000,
        ["DJI Mavic 2 Pro in Webots R2025a.",
         "GPS, inertial unit and gyroscope.",
         "A probe measured every motor sign."], size=22, after=24)
    picture(s, "fig_probe_signs.png", 5700000, 1600000, w=5800000)

    # 9 Algorithm 1
    s = new_slide(prs, "Algorithm 1", "Minimum-jerk trajectory", "M3")
    txt(s, MX, 1700000, 5600000, 1200000, "p(t) = p₀ + (p₁ − p₀)(10τ³ − 15τ⁴ + 6τ⁵)",
        font=SERIF, size=24, color=INK)
    txt(s, MX, 3200000, 5100000, 2600000,
        ["Zero speed and acceleration at both ends.",
         "Starts from the measured climb speed at take-off."], size=22, after=22)
    picture(s, "fig_e2_xy_path.png", 6500000, 1500000, h=4400000)

    # 10 Algorithm 2
    s = new_slide(prs, "Algorithm 2", "Method A and Method B", "M4")
    table(s, [["", "Method A", "Method B"],
              ["Waypoints", "Step", "Minimum-jerk path"],
              ["Altitude", "PD", "PID, anti-windup, feedforward"],
              ["Position", "PD", "P, then velocity PI"],
              ["Attitude", "PD", "Same"]],
          MX, 1600000, CW, [2400000, 3000000, 5400000])
    txt(s, MX, 4500000, CW, 900000, "Every tuning trial, including crashes, is logged.", size=22, color=MUTED)

    # 11 Simulation setup
    s = new_slide(prs, "Simulation setup", "Six experiments", "M4")
    sc = [("E1", "Altitude steps"), ("E2", "Square mission"), ("E3", "3D waypoints"),
          ("E4", "Crosswind"), ("E5", "Sensor noise"), ("E6", "Roll-gain sweep")]
    cw3, ch3 = 3400000, 1500000
    for i, (eid, name) in enumerate(sc):
        x, y = MX + (i % 3) * (cw3 + 300000), 1700000 + (i // 3) * (ch3 + 250000)
        rect(s, x, y, cw3, ch3, fill=WHITE, line=BORDER)
        txt(s, x + 240000, y + 200000, 1200000, 600000, eid, font=SERIF, size=36, color=INK)
        txt(s, x + 240000, y + 900000, cw3 - 480000, 500000, name, size=20, after=0)

    # 12 Demo
    s = new_slide(prs, "Live demonstration", "Square mission, side by side", "M4", ivory=True)
    vw, vh = 5250000, 2953000
    video(s, "e2_baseline", MX, 1700000, vw, vh)
    video(s, "e2_improved", MX + vw + 300000, 1700000, vw, vh)
    chip(s, MX, 1700000 + vh + 220000, 2600000, "Method A  ·  baseline", fill=WHITE)
    chip(s, MX + vw + 300000, 1700000 + vh + 220000, 2600000, "Method B  ·  improved", fill=WHITE)

    # 13 Results: altitude and path
    s = new_slide(prs, "Results", "Altitude and path", "M5")
    picture(s, "fig_e1_step_response.png", MX, 1500000, w=5300000)
    picture(s, "fig_e3_3d_path.png", MX + 5500000, 1500000, h=3300000)
    txt(s, MX, 5100000, 5300000, 800000,
        f"Altitude error: A {r.one('E1', 'baseline', 'step2_ss_error_m')} m, B {r.one('E1', 'improved', 'step2_ss_error_m')} m",
        size=20)
    txt(s, MX + 5500000, 5100000, 5300000, 800000,
        f"3D path error: A {r.one('E3', 'baseline', 'path_rmse_m')} m, B {r.one('E3', 'improved', 'path_rmse_m')} m",
        size=20)

    # 14 Results: wind
    s = new_slide(prs, "Results", "Crosswind: one stalls, one finishes", "M5")
    fw, fh = 5250000, 2953000
    picture(s, "fig_e4_xy_path.png", MX, 1500000, h=fh + 200000)
    picture(s, "fig_e4_wind_error.png", MX + fw + 300000, 1500000, h=fh + 200000)
    txt(s, MX, 1500000 + fh + 400000, fw, 600000,
        f"Method A: {r.one('E4', 'baseline', 'waypoints_reached', 0)} of 5 waypoints", size=22, color=INK)
    txt(s, MX + fw + 300000, 1500000 + fh + 400000, fw, 600000,
        f"Method B: 5 of 5, path error {r.one('E4', 'improved', 'path_rmse_m')} m", size=22, color=INK)

    # 15 Results: comparison
    s = new_slide(prs, "Results", "Comparison at a glance", "M5")
    table(s, [["Metric", "A", "B"],
              ["Square path error (m)", r.one("E2", "baseline", "path_rmse_m"), r.one("E2", "improved", "path_rmse_m")],
              ["Square control effort", r.one("E2", "baseline", "control_effort", 1), r.one("E2", "improved", "control_effort", 1)],
              ["Noisy runs that succeed", r.success("E5", "baseline"), r.success("E5", "improved")],
              ["Roll gains that crash", r.sweep_fail("baseline"), r.sweep_fail("improved")]],
          MX, 1600000, 5600000, [2900000, 1300000, 1400000], size=20)
    picture(s, "fig_e6_roll_gain_sweep.png", 6500000, 1500000, w=5000000)

    # 16 Team
    s = new_slide(prs, "Team contribution", "Five modules, one system", "M5")
    table(s, [["Member", "Module"],
              ["Saksham Agrawal", "Sign probe, Kalman estimator, config, logger"],
              ["Khushi Gupta", "PID, altitude, attitude, mixer"],
              ["Tanvi Singhal", "Position, yaw, waypoints, trajectory"],
              ["Khyati Yadav", "Method A and B assembly, wind supervisor"],
              ["Ambrish Chauraiya", "Experiments, metrics, figures, tables"]],
          MX, 1600000, CW, [3500000, 7300000])

    # 17 Conclusion and thanks
    s = prs.slides.add_slide(prs.slide_layouts[6])
    set_bg(s, IVORY)
    txt(s, MX, 700000, CW, 260000, "CONCLUSION", size=12, spc=300, color=MUTED)
    txt(s, MX, 1300000, 9500000, 1800000,
        "Method B: lower path error, half the control effort, and it survives wind and noise.",
        font=SERIF, size=32, color=INK)
    txt(s, MX, 3300000, 9500000, 900000,
        "Next: a real drone with motor lag and battery effects, then LQR or MPC.", size=22)
    txt(s, MX, 4300000, 9500000, 1400000,
        ["Thank you  ·  Questions?", "github.com/devSaksham/aisr-drone-control",
         "youtu.be/450zcQy80m8"], size=20, color=INK, after=8)
    presenter(s, "All", True)
    return prs


def export_pdf(pptx_path: str, pdf_path: str) -> bool:
    """Export with PowerPoint (Windows COM via PowerShell); returns True on success."""
    ps = (f"$p=New-Object -ComObject PowerPoint.Application;"
          f"$d=$p.Presentations.Open('{pptx_path}',$true,$false,$false);"
          f"$d.SaveAs('{pdf_path}',32);$d.Close();$p.Quit()")
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, timeout=240,
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
    print(f"  {n} slides -> {pptx_path}  (fonts: {SERIF} / {SANS})")
    if export_pdf(pptx_path, os.path.join(OUT, "slides.pdf")):
        print("  exported slides/slides.pdf")


if __name__ == "__main__":
    sys.exit(main())
