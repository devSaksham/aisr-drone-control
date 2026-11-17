"""Live demo launcher: open Webots with rendering for one scenario and method.

Module: demo.py
Owner: M4
Inputs:  scenario id (E1, E2, ...), method (baseline | improved).
Outputs: a normal, visible Webots window flying the chosen mission in real time;
         telemetry is still written to results/demo/<scenario>_<method>/.

Examples (used for the live demonstration in the video):
    python experiments/demo.py E2 improved
    python experiments/demo.py E2 baseline
    python experiments/demo.py E4 improved      # with wind
"""

import argparse
import copy
import json
import os
import subprocess
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

from experiments.run_experiments import WEBOTS_EXE, load_scenarios  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Open a visible Webots demo run")
    ap.add_argument("scenario", help="scenario id, e.g. E2")
    ap.add_argument("method", choices=["baseline", "improved"])
    ap.add_argument("--fast", action="store_true", help="run faster than real time")
    a = ap.parse_args()

    sc = copy.deepcopy(load_scenarios([a.scenario])[0])
    sc.pop("seeds", None)
    sc.update({"method": a.method, "seed": 0, "screenshots": True,
               "output_dir": f"results/demo/{a.scenario}_{a.method}"})
    with open(os.path.join(REPO, "current_scenario.json"), "w", encoding="utf-8") as f:
        json.dump(sc, f, indent=2)
    mode = "--mode=fast" if a.fast else "--mode=realtime"
    print(f"Opening Webots: {sc['name']} with Method {'A' if a.method == 'baseline' else 'B'}")
    subprocess.Popen([WEBOTS_EXE, mode, os.path.join(REPO, sc["world"])], cwd=REPO)


if __name__ == "__main__":
    main()
