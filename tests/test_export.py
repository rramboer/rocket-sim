"""Tests for SimulationResult.to_csv / to_json export helpers."""

from __future__ import annotations

import csv
import json

from rocket_sim.models import Rocket
from rocket_sim.simulation import simulate_rocket


class TestCsvExport:
    def test_writes_expected_columns(self, alpha_iii: Rocket, tmp_path) -> None:
        result = simulate_rocket(alpha_iii)
        path = tmp_path / "flight.csv"
        result.to_csv(path)
        with open(path) as f:
            reader = csv.reader(f)
            header = next(reader)
        assert header == [
            "time_s",
            "altitude_m",
            "velocity_ms",
            "acceleration_ms2",
            "mass_kg",
            "thrust_n",
            "drag_n",
            "phase",
        ]

    def test_row_count_matches_states(self, alpha_iii: Rocket, tmp_path) -> None:
        result = simulate_rocket(alpha_iii)
        path = tmp_path / "flight.csv"
        result.to_csv(path)
        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        # header + N states
        assert len(rows) == 1 + len(result.states)

    def test_first_row_starts_at_t_zero(self, alpha_iii: Rocket, tmp_path) -> None:
        result = simulate_rocket(alpha_iii)
        path = tmp_path / "flight.csv"
        result.to_csv(path)
        with open(path) as f:
            reader = csv.DictReader(f)
            first = next(reader)
        assert float(first["time_s"]) == 0.0
        assert first["phase"] == "boost"


class TestJsonExport:
    def test_to_dict_has_expected_keys(self, alpha_iii: Rocket) -> None:
        result = simulate_rocket(alpha_iii)
        d = result.to_dict()
        assert "rocket_name" in d
        assert "summary" in d
        assert "states" in d
        # Summary contains apogee.
        assert "apogee_m" in d["summary"]
        # States is non-empty list of dicts with the right keys.
        assert isinstance(d["states"], list)
        assert d["states"][0]["phase"] == "boost"

    def test_writes_valid_json(self, alpha_iii: Rocket, tmp_path) -> None:
        result = simulate_rocket(alpha_iii)
        path = tmp_path / "flight.json"
        result.to_json(path)
        # Parses without error.
        loaded = json.loads(path.read_text())
        assert loaded["rocket_name"] == result.rocket_name
        assert loaded["summary"]["apogee_m"] == result.apogee_m
        assert len(loaded["states"]) == len(result.states)

    def test_states_match_summary_apogee(self, alpha_iii: Rocket, tmp_path) -> None:
        result = simulate_rocket(alpha_iii)
        path = tmp_path / "flight.json"
        result.to_json(path)
        loaded = json.loads(path.read_text())
        max_alt = max(s["altitude_m"] for s in loaded["states"])
        # apogee_m is reported relative to launch site; with default
        # launch_altitude_m=0 they should match.
        assert max_alt == loaded["summary"]["apogee_m"]
