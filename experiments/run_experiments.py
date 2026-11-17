"""Headless batch runner for the experiment scenarios.

Module: run_experiments.py
Owner: M5
Inputs:  experiments/scenarios/*.yaml, Webots executable (WEBOTS_EXE or default path).
Outputs: results/<scenario>/<method>/seed_<n>/telemetry.csv (+ config_snapshot.json),
         results/summary.csv with one row of metrics per run.

Examples:
    python experiments/run_experiments.py                 # every scenario, both methods
    python experiments/run_experiments.py --only E2       # one scenario
    python experiments/run_experiments.py --only E1 --methods baseline --no-summary
Each run writes current_scenario.json, which the drone controller and the wind
supervisor read, then launches
    webots --mode=fast --batch --no-rendering --minimize <world>
"""

import argparse
import copy
import glob
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)
WEBOTS_EXE = os.environ.get(
    "WEBOTS_EXE", r"C:\Program Files\Webots\msys64\mingw64\bin\webots.exe")
METHODS = ("baseline", "improved")


def load_scenarios(only: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    out = []
    for path in sorted(glob.glob(os.path.join(REPO, "experiments", "scenarios", "*.yaml"))):
        with open(path, "r", encoding="utf-8") as f:
            sc = yaml.safe_load(f)
        if only and sc["scenario_id"] not in only:
            continue
        out.append(sc)
    return out


def run_dir(scenario_id: str, method: str, seed: int, tag: str = "") -> str:
    name = f"seed_{seed}" + (f"_{tag}" if tag else "")
    return os.path.join("results", scenario_id, method, name)


def run_single(scenario: Dict[str, Any], method: str, seed: int, out_rel: str,
               timeout_s: float = 300.0) -> Dict[str, Any]:
    """Run one Webots simulation and return its run description."""
    run = copy.deepcopy(scenario)
    run.update({"method": method, "seed": seed, "output_dir": out_rel.replace("\\", "/")})
    run.pop("seeds", None)
    with open(os.path.join(REPO, "current_scenario.json"), "w", encoding="utf-8") as f:
        json.dump(run, f, indent=2)
    tele = os.path.join(REPO, out_rel, "telemetry.csv")
    if os.path.exists(tele):
        os.remove(tele)
    cmd = [WEBOTS_EXE, "--mode=fast", "--batch", "--no-rendering", "--minimize",
           os.path.join(REPO, scenario["world"])]
    t0 = time.time()
    try:
        subprocess.run(cmd, cwd=REPO, timeout=timeout_s, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        print(f"    timeout after {timeout_s:.0f}s")
    ok = os.path.exists(tele)
    print(f"  {run['scenario_id']:>4} {method:<9} seed {seed:<4} "
          f"{'ok ' if ok else 'NO TELEMETRY'} ({time.time() - t0:.0f}s wall)")
    return run


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", nargs="*", help="scenario ids, e.g. E1 E2")
    ap.add_argument("--methods", nargs="*", default=list(METHODS))
    ap.add_argument("--no-summary", action="store_true")
    args = ap.parse_args()

    for sc in load_scenarios(args.only):
        if sc.get("dev") and not args.only:
            continue  # development scenarios only run when named explicitly
        for variant, tag in sweep_variants(sc):
            for seed in variant.get("seeds", [0]):
                for method in args.methods:
                    run_single(variant, method, seed, run_dir(sc["scenario_id"], method, seed, tag))
    if not args.no_summary:
        write_summary()


def sweep_variants(sc: Dict[str, Any]):
    """Yield (scenario, tag) pairs: one per sweep value, or the scenario itself."""
    sweep = sc.get("sweep")
    if not sweep:
        yield sc, ""
        return
    for value in sweep["values"]:
        variant = copy.deepcopy(sc)
        variant.pop("sweep")
        override = {sweep["param"]: value}
        variant["gains"] = {"baseline": dict(override), "improved": dict(override)}
        variant["tag"] = f"{sweep['param']}={value}"
        yield variant, f"{sweep['param']}{value}"


def write_summary() -> None:
    """Rebuild results/summary.csv from every run directory under results/E*/."""
    from analysis.metrics import summarise_runs
    dirs = sorted(os.path.dirname(p) for p in
                  glob.glob(os.path.join(REPO, "results", "E*", "*", "*", "telemetry.csv")))
    summarise_runs(dirs, os.path.join(REPO, "results", "summary.csv"))


if __name__ == "__main__":
    main()
