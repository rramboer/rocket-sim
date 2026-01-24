"""
Tests for rocket presets.
"""

import pytest

from rocket_sim.models import RocketConfig
from rocket_sim.presets import PRESETS, get_preset, get_preset_info, list_presets


class TestPresets:
    """Tests for preset rocket configurations."""

    def test_presets_not_empty(self) -> None:
        """Test that presets dictionary is not empty."""
        assert len(PRESETS) > 0

    def test_all_presets_are_rocket_configs(self) -> None:
        """Test that all presets are RocketConfig instances."""
        for name, config in PRESETS.items():
            assert isinstance(config, RocketConfig), f"{name} is not a RocketConfig"

    def test_all_presets_have_valid_parameters(self) -> None:
        """Test that all presets have valid parameters."""
        for name, config in PRESETS.items():
            assert config.mass > 0, f"{name} has invalid mass"
            assert config.thrust > 0, f"{name} has invalid thrust"
            assert config.burn_time > 0, f"{name} has invalid burn_time"

    def test_all_presets_have_positive_twr(self) -> None:
        """Test that all presets have positive thrust-to-weight ratio."""
        for name, config in PRESETS.items():
            twr = config.thrust_to_weight_ratio
            assert twr > 0, f"{name} has invalid TWR: {twr}"

    def test_famous_rockets_exist(self) -> None:
        """Test that famous rockets are in presets."""
        famous_rockets = ["Saturn V", "Falcon 9", "Space Shuttle"]
        for rocket in famous_rockets:
            assert rocket in PRESETS, f"Missing preset: {rocket}"


class TestGetPreset:
    """Tests for get_preset function."""

    def test_get_existing_preset(self) -> None:
        """Test getting an existing preset."""
        config = get_preset("Falcon 9")
        assert config.name == "Falcon 9"
        assert config.mass > 0

    def test_get_preset_case_insensitive(self) -> None:
        """Test case-insensitive preset lookup."""
        config1 = get_preset("FALCON 9")
        config2 = get_preset("falcon 9")
        config3 = get_preset("Falcon 9")

        assert config1.mass == config2.mass == config3.mass

    def test_get_nonexistent_preset_raises_error(self) -> None:
        """Test that getting nonexistent preset raises KeyError."""
        with pytest.raises(KeyError, match="Unknown preset"):
            get_preset("Nonexistent Rocket")


class TestListPresets:
    """Tests for list_presets function."""

    def test_list_presets_returns_list(self) -> None:
        """Test that list_presets returns a list."""
        names = list_presets()
        assert isinstance(names, list)

    def test_list_presets_matches_dict_keys(self) -> None:
        """Test that list_presets matches PRESETS keys."""
        names = list_presets()
        assert set(names) == set(PRESETS.keys())


class TestGetPresetInfo:
    """Tests for get_preset_info function."""

    def test_get_preset_info(self) -> None:
        """Test getting formatted preset info."""
        info = get_preset_info("Falcon 9")
        assert "Falcon 9" in info
        assert "Mass:" in info
        assert "Thrust:" in info
        assert "Burn Time:" in info
