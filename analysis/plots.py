"""Report figures generated from the experiment telemetry.

Module: plots.py
Owner: M5
Inputs:  results/<scenario>/<method>/seed_<n>/telemetry.csv, results/summary.csv,
         results/probe/probe.csv.
Outputs: results/figures/*.png (300 dpi, used by the report and the slides).

Run:  python analysis/plots.py
Colours: Method A = blue (#2a78d6, dashed), Method B = orange (#eb6834, solid).
The pair was checked with the dataviz palette validator (CVD-safe); the dash pattern
is a second encoding so the figures also read in grayscale print.
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)
FIG_DIR = os.path.join(REPO, "results", "figures")

STYLE = {
    "baseline": {"color": "#2a78d6", "ls": "--", "label": "Method A (baseline)"},
    "improved": {"color": "#eb6834", "ls": "-", "label": "Method B (improved)"},
}
INK, MUTED, GRID = "#1f1f1e", "#6b6b66", "#e4e3df"
plt.rcParams.update({
    "font.family": "serif", "font.size": 10, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "lines.linewidth": 1.6,
    "legend.frameon": False, "savefig.dpi": 300, "savefig.bbox": "tight",
})


def tele(scenario: str, method: str, seed: int = 0, tag: str = "") -> pd.DataFrame:
    name = f"seed_{seed}" + (f"_{tag}" if tag else "")
    return pd.read_csv(os.path.join(REPO, "results", scenario, method, name, "telemetry.csv"))


def tilt_deg(d: pd.DataFrame) -> np.ndarray:
    return np.degrees(np.arccos(np.clip(np.cos(d.roll) * np.cos(d.pitch), -1, 1)))


def save(fig, name: str) -> None:
    os.makedirs(FIG_DIR, exist_ok=True)
    fig.savefig(os.path.join(FIG_DIR, name))
    plt.close(fig)
    print(f"  {name}")


def waypoints_of(d_run_dir: str):
    import json
    with open(os.path.join(d_run_dir, "config_snapshot.json"), encoding="utf-8") as f:
        return np.array(json.load(f)["scenario"]["waypoints"])


def fig_step_response() -> None:
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    for m in STYLE:
        d = tele("E1", m)
        ax.plot(d.time, d.true_z, color=STYLE[m]["color"], ls=STYLE[m]["ls"], label=STYLE[m]["label"])
    d = tele("E1", "baseline")
    ax.step(d.time, d.wp_z, where="post", color=MUTED, lw=1.0, ls=":", label="Commanded altitude")
    ax.set(xlabel="Time (s)", ylabel="Altitude z (m)", ylim=(0, 2.4))
    ax.legend(loc="lower right")
    save(fig, "fig_e1_step_response.png")


def fig_xy(scenario: str, name: str, title_note: str = "") -> None:
    fig, ax = plt.subplots(figsize=(4.8, 4.6))
    wps = waypoints_of(os.path.join(REPO, "results", scenario, "baseline", "seed_0"))
    ax.plot(wps[:, 0], wps[:, 1], color=MUTED, lw=1.0, ls=":", zorder=1)
    for m in STYLE:
        d = tele(scenario, m)
        ax.plot(d.true_x, d.true_y, color=STYLE[m]["color"], ls=STYLE[m]["ls"], label=STYLE[m]["label"])
    ax.scatter(wps[:, 0], wps[:, 1], s=40, color=INK, zorder=3, label="Waypoints")
    labels = {}
    for i, (x, y) in enumerate(wps[:, :2], 1):  # merge labels of coincident waypoints
        labels.setdefault((round(x, 2), round(y, 2)), []).append(str(i))
    for (x, y), ids in labels.items():
        ax.annotate("WP" + "/".join(ids), (x, y), textcoords="offset points", xytext=(6, 6),
                    color=INK, fontsize=8)
    if title_note:
        ax.annotate(title_note, xy=(0.02, 0.02), xycoords="axes fraction", color=MUTED, fontsize=8)
    ax.set(xlabel="x (m)", ylabel="y (m)", aspect="equal")
    ax.legend(loc="upper left", bbox_to_anchor=(0, 1.18), ncol=2, fontsize=8)
    save(fig, name)


def fig_3d() -> None:
    fig = plt.figure(figsize=(5.6, 4.6))
    ax = fig.add_subplot(projection="3d")
    wps = waypoints_of(os.path.join(REPO, "results", "E3", "baseline", "seed_0"))
    for m in STYLE:
        d = tele("E3", m)
        ax.plot(d.true_x, d.true_y, d.true_z, color=STYLE[m]["color"], ls=STYLE[m]["ls"], label=STYLE[m]["label"])
    ax.scatter(wps[:, 0], wps[:, 1], wps[:, 2], s=30, color=INK, label="Waypoints")
    ax.set(xlabel="x (m)", ylabel="y (m)", zlabel="z (m)")
    ax.legend(loc="upper left", fontsize=8)
    save(fig, "fig_e3_3d_path.png")


def fig_wind() -> None:
    from analysis.metrics import cross_track
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    for m in STYLE:
        d = tele("E4", m)
        wps = waypoints_of(os.path.join(REPO, "results", "E4", m, "seed_0"))
        d = d[d.time >= 5.0]  # after take-off; on the ground the distance is meaningless
        err = cross_track(d[["true_x", "true_y", "true_z"]].values, wps)
        ax.plot(d.time, err, color=STYLE[m]["color"], ls=STYLE[m]["ls"], label=STYLE[m]["label"])
    ax.axvspan(8.0, d.time.max(), color=GRID, alpha=0.5, lw=0)
    ax.annotate("wind on from t = 8 s (0.3 N + 0.15 N gusts)", xy=(8.3, 1.02),
                xycoords=("data", "axes fraction"), color=MUTED, fontsize=8)
    ax.set(xlabel="Time (s)", ylabel="Distance from path (m)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=8)
    save(fig, "fig_e4_wind_error.png")


def fig_tilt() -> None:
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    for m in STYLE:
        d = tele("E2", m)
        ax.plot(d.time, tilt_deg(d), color=STYLE[m]["color"], ls=STYLE[m]["ls"], label=STYLE[m]["label"], lw=1.2)
    ax.set(xlabel="Time (s)", ylabel="Tilt (deg)", xlim=(3, 30))  # airborne from about 3 s
    ax.legend(loc="upper right")
    save(fig, "fig_e2_tilt.png")


def fig_noise(summary: pd.DataFrame) -> None:
    s = summary[summary.scenario == "E5"]
    if s.empty:
        return
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    ok = {m: s[(s.method == m) & s.success.astype(bool)] for m in STYLE}
    bp = ax.boxplot([ok[m].path_rmse_m.values for m in STYLE], widths=0.45, patch_artist=True,
                    showfliers=False, medianprops={"color": INK})
    for patch, m in zip(bp["boxes"], STYLE):
        patch.set(facecolor=STYLE[m]["color"], alpha=0.3, edgecolor=STYLE[m]["color"])
    for i, m in enumerate(STYLE, 1):
        sm = ok[m]
        ax.scatter(np.full(len(sm), i) + np.linspace(-0.1, 0.1, len(sm)), sm.path_rmse_m,
                   s=16, color=STYLE[m]["color"], zorder=3)
        allm = s[s.method == m]
        crashed = allm[allm.crashed.astype(bool)].seed.astype(int).tolist()
        note = f"success {len(sm)}/{len(allm)}"
        if crashed:
            note += "\ncrashed: seed " + ", ".join(map(str, sorted(crashed)))
        ax.annotate(note, (i, 1.0), xycoords=("data", "axes fraction"), ha="center", va="top",
                    color=INK, fontsize=8)
    ax.set_xticks([1, 2], [STYLE[m]["label"] for m in STYLE])
    ax.set_ylabel("Path RMSE, successful runs (m)")
    ax.margins(y=0.35)
    save(fig, "fig_e5_noise_box.png")


def fig_sweep(summary: pd.DataFrame) -> None:
    s = summary[summary.scenario == "E6"].copy()
    if s.empty:
        return
    s["kp"] = s.tag.str.split("=").str[1].astype(float)
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    failed = []
    for m in STYLE:
        sm = s[s.method == m].sort_values("kp")
        ok = sm[sm.success.astype(bool)]
        ax.plot(ok.kp, ok.path_rmse_m, color=STYLE[m]["color"], ls=STYLE[m]["ls"], marker="o",
                ms=5, label=STYLE[m]["label"])
        failed += [(m, k) for k in sm[~sm.success.astype(bool)].kp]
    ax.margins(y=0.3)
    top = ax.get_ylim()[1]
    for m, k in failed:  # crashed runs have no meaningful RMSE: mark them along the top edge
        ax.scatter([k], [top], marker="x", s=60, color=STYLE[m]["color"], clip_on=False, zorder=4)
        ax.annotate("crashed", (k, top), textcoords="offset points", xytext=(0, -14),
                    ha="center", color=STYLE[m]["color"], fontsize=8)
    ax.axvline(50, color=MUTED, lw=0.8, ls=":")
    ax.annotate("Webots sample", xy=(49.3, 0.5), xycoords=("data", "axes fraction"), ha="right",
                rotation=90, va="center", color=MUTED, fontsize=8)
    ax.set(xlabel=r"Roll proportional gain $K_{p,\phi}$", ylabel="E2 path RMSE (m)")
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2)
    save(fig, "fig_e6_roll_gain_sweep.png")


def fig_probe() -> None:
    path = os.path.join(REPO, "results", "probe", "probe.csv")
    if not os.path.exists(path):
        return
    d = pd.read_csv(path)
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.6), sharex=False)
    for ax, (col, inj, t0, label) in zip(axes, [("roll", "d_roll", 8, "roll"), ("pitch", "d_pitch", 13, "pitch")]):
        w = d[(d.t > t0 - 1) & (d.t < t0 + 3)]
        ax.plot(w.t, w[col], color=INK, label=f"measured {label} (rad)")
        ax.plot(w.t, w[inj] * 0.02, color=MUTED, ls=":", label=f"{label} input offset (x0.02)")
        ax.set(xlabel="Time (s)", title=f"+1 offset on {label} input")
        ax.legend(fontsize=7, loc="lower left")
    save(fig, "fig_probe_signs.png")


def main() -> None:
    summary = pd.read_csv(os.path.join(REPO, "results", "summary.csv"))
    steps = [("E1", fig_step_response), ("E2", lambda: fig_xy("E2", "fig_e2_xy_path.png")),
             ("E2", fig_tilt), ("E3", fig_3d),
             ("E4", lambda: fig_xy("E4", "fig_e4_xy_path.png", "wind along +y from t = 8 s")),
             ("E4", fig_wind), ("E5", lambda: fig_noise(summary)), ("E6", lambda: fig_sweep(summary)),
             ("", fig_probe)]
    for scenario, fn in steps:
        if scenario and not os.path.isdir(os.path.join(REPO, "results", scenario)):
            print(f"  skip {scenario} (no results yet)")
            continue
        fn()


if __name__ == "__main__":
    main()
