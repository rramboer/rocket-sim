"""Tests for kit-preset registry and lookup."""

from __future__ import annotations

import pytest

from rocket_sim.models import Parachute, Rocket, Streamer
from rocket_sim.presets import get_kit, get_kit_info, list_kits


class TestKitPresets:
    def test_all_kits_present(self) -> None:
        names = list_kits()
        assert "alpha-iii" in names
        assert "big-bertha" in names
        assert "mosquito" in names
        assert "v-2" in names

    def test_get_kit_returns_rocket(self) -> None:
        rocket = get_kit("alpha-iii")
        assert isinstance(rocket, Rocket)
        assert rocket.name == "Estes Alpha III"
        assert rocket.dry_mass_kg > 0
        assert rocket.diameter_m > 0
        assert rocket.motor is not None

    def test_get_kit_case_insensitive(self) -> None:
        rocket = get_kit("ALPHA-III")
        assert rocket.name == "Estes Alpha III"

    def test_get_kit_returns_independent_copies(self) -> None:
        a = get_kit("alpha-iii")
        b = get_kit("alpha-iii")
        # Should be equal in content but distinct instances.
        assert a == b
        assert a is not b

    def test_unknown_kit_raises(self) -> None:
        with pytest.raises(KeyError):
            get_kit("nonexistent-rocket")

    def test_alpha_iii_uses_parachute(self) -> None:
        rocket = get_kit("alpha-iii")
        assert isinstance(rocket.recovery, Parachute)

    def test_mosquito_uses_streamer(self) -> None:
        rocket = get_kit("mosquito")
        assert isinstance(rocket.recovery, Streamer)

    def test_get_kit_info_contains_motor(self) -> None:
        info = get_kit_info("alpha-iii")
        assert "Estes Alpha III" in info
        assert "C6-5" in info
