"""Tests for SimulationConfig validators and JSON round-tripping."""

from __future__ import annotations

import json

import pytest

from rocket_sim.config import SimulationConfig


class TestConfig:
    def test_defaults(self) -> None:
        c = SimulationConfig()
        assert c.dt > 0
        assert c.max_time > 0
        assert c.deploy_mode == "motor-delay"
        assert c.launch_altitude_m == 0

    def test_to_from_dict_roundtrip(self) -> None:
        c = SimulationConfig(dt=0.02, max_time=120, launch_altitude_m=1500, deploy_mode="apogee")
        d = c.to_dict()
        c2 = SimulationConfig.from_dict(d)
        assert c == c2

    def test_save_and_load(self, tmp_path) -> None:
        c = SimulationConfig(dt=0.02, max_time=120, launch_altitude_m=1500)
        p = tmp_path / "cfg.json"
        c.save(p)
        loaded = SimulationConfig.load(p)
        assert loaded == c

    def test_save_writes_json(self, tmp_path) -> None:
        c = SimulationConfig()
        p = tmp_path / "cfg.json"
        c.save(p)
        # Parses as JSON.
        json.loads(p.read_text())

    def test_unknown_deploy_mode_in_dict_raises(self) -> None:
        with pytest.raises(ValueError):
            SimulationConfig.from_dict({"deploy_mode": "wat"})
