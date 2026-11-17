"""Tests for config.py (owner: M1)."""
import json

import pytest
from drone_ctrl.config import (BaselineGains, ImprovedGains, PhysicalParams, apply_overrides,
                               load_scenario, parse_scenario, snapshot)


def test_parse_ignores_unknown_keys():
    cfg = parse_scenario({"scenario_id": "E2", "seed": 3, "world": "x.wbt"})
    assert cfg.scenario_id == "E2" and cfg.seed == 3


def test_overrides_change_only_named_gains():
    g = apply_overrides(BaselineGains(), {"pos_kp": 0.7})
    assert g.pos_kp == 0.7 and g.alt_kp == BaselineGains().alt_kp


def test_unknown_override_is_rejected():
    with pytest.raises(KeyError):
        apply_overrides(ImprovedGains(), {"not_a_gain": 1.0})


def test_load_scenario_from_file(tmp_path, monkeypatch):
    monkeypatch.delenv("DRONE_SCENARIO_JSON", raising=False)
    (tmp_path / "current_scenario.json").write_text(json.dumps({"method": "baseline"}))
    assert load_scenario(str(tmp_path)).method == "baseline"


def test_snapshot_contains_everything():
    snap = snapshot(parse_scenario({}), ImprovedGains(), PhysicalParams())
    assert set(snap) == {"scenario", "gains", "params"}
