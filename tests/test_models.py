"""
Tests for rocket and engine models.
"""

import pytest

from rocket_sim.models import Engine, Rocket, RocketConfig


class TestEngine:
    """Tests for Engine class."""

    def test_engine_creation(self) -> None:
        """Test basic engine creation."""
        engine = Engine(thrust=10000, burn_time=100)
        assert engine.thrust == 10000
        assert engine.burn_time == 100

    def test_engine_is_burning(self) -> None:
        """Test is_burning method."""
        engine = Engine(thrust=10000, burn_time=10)

        assert engine.is_burning(0)
        assert engine.is_burning(5)
        assert engine.is_burning(9.9)
        assert not engine.is_burning(10)
        assert not engine.is_burning(15)

    def test_engine_get_thrust(self) -> None:
        """Test get_thrust method."""
        engine = Engine(thrust=10000, burn_time=10)

        assert engine.get_thrust(0) == 10000
        assert engine.get_thrust(5) == 10000
        assert engine.get_thrust(10) == 0
        assert engine.get_thrust(15) == 0

    def test_total_impulse(self) -> None:
        """Test total impulse calculation."""
        engine = Engine(thrust=10000, burn_time=100)
        assert engine.total_impulse == 1_000_000

    def test_negative_thrust_raises_error(self) -> None:
        """Test that negative thrust raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Engine(thrust=-100, burn_time=10)

    def test_negative_burn_time_raises_error(self) -> None:
        """Test that negative burn time raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Engine(thrust=1000, burn_time=-10)


class TestRocket:
    """Tests for Rocket class."""

    def test_rocket_creation(self, simple_engine: Engine) -> None:
        """Test basic rocket creation."""
        rocket = Rocket(mass=1000, engine=simple_engine)
        assert rocket.mass == 1000
        assert rocket.altitude == 0
        assert rocket.velocity == 0
        assert rocket.time == 0

    def test_rocket_update(self, simple_rocket: Rocket) -> None:
        """Test rocket position update."""
        initial_altitude = simple_rocket.altitude

        altitude, velocity = simple_rocket.update(0.1)

        assert altitude >= initial_altitude
        assert simple_rocket.time == 0.1

    def test_rocket_ascends_with_thrust(self) -> None:
        """Test that rocket ascends when thrust > weight."""
        engine = Engine(thrust=20000, burn_time=100)  # High thrust
        rocket = Rocket(mass=1000, engine=engine)

        for _ in range(100):
            rocket.update(0.1)

        assert rocket.altitude > 0
        assert rocket.velocity > 0

    def test_rocket_reset(self, simple_rocket: Rocket) -> None:
        """Test rocket reset functionality."""
        # Advance the rocket
        for _ in range(10):
            simple_rocket.update(0.1)

        assert simple_rocket.time > 0

        simple_rocket.reset()

        assert simple_rocket.altitude == 0
        assert simple_rocket.velocity == 0
        assert simple_rocket.time == 0

    def test_ground_collision(self) -> None:
        """Test that rocket stops at ground level."""
        engine = Engine(thrust=0, burn_time=0)  # No thrust
        rocket = Rocket(mass=1000, engine=engine)
        rocket.altitude = 100
        rocket.velocity = -1000  # Falling fast

        # Update should clamp to ground
        altitude, velocity = rocket.update(1.0)

        assert altitude == 0
        assert velocity == 0

    def test_kinetic_energy(self, simple_rocket: Rocket) -> None:
        """Test kinetic energy calculation."""
        simple_rocket.velocity = 100
        ke = simple_rocket.kinetic_energy
        assert ke == 0.5 * simple_rocket.mass * 100**2

    def test_is_ascending(self, simple_rocket: Rocket) -> None:
        """Test is_ascending property."""
        simple_rocket.velocity = 100
        assert simple_rocket.is_ascending

        simple_rocket.velocity = -100
        assert not simple_rocket.is_ascending

    def test_from_config(self, simple_config: RocketConfig) -> None:
        """Test creating rocket from config."""
        rocket = Rocket.from_config(simple_config)
        assert rocket.mass == simple_config.mass
        assert rocket.engine.thrust == simple_config.thrust
        assert rocket.engine.burn_time == simple_config.burn_time


class TestRocketConfig:
    """Tests for RocketConfig class."""

    def test_config_creation(self) -> None:
        """Test basic config creation."""
        config = RocketConfig(
            mass=1000,
            thrust=10000,
            burn_time=100,
            name="Test",
        )
        assert config.mass == 1000
        assert config.thrust == 10000
        assert config.burn_time == 100
        assert config.name == "Test"

    def test_thrust_to_weight_ratio(self) -> None:
        """Test thrust-to-weight ratio calculation."""
        config = RocketConfig(mass=1000, thrust=9810, burn_time=100)
        # TWR should be approximately 1.0 (thrust ~= weight)
        assert 0.95 < config.thrust_to_weight_ratio < 1.05

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        config = RocketConfig(
            mass=1000,
            thrust=10000,
            burn_time=100,
            name="Test",
        )
        d = config.to_dict()

        assert d["mass"] == 1000
        assert d["thrust"] == 10000
        assert d["burn_time"] == 100
        assert d["name"] == "Test"

    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        d = {"mass": 1000, "thrust": 10000, "burn_time": 100, "name": "Test"}
        config = RocketConfig.from_dict(d)

        assert config.mass == 1000
        assert config.thrust == 10000
        assert config.burn_time == 100
        assert config.name == "Test"

    def test_invalid_mass_raises_error(self) -> None:
        """Test that invalid mass raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            RocketConfig(mass=0, thrust=1000, burn_time=10)

        with pytest.raises(ValueError, match="must be positive"):
            RocketConfig(mass=-100, thrust=1000, burn_time=10)

    def test_negative_thrust_raises_error(self) -> None:
        """Test that negative thrust raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            RocketConfig(mass=1000, thrust=-100, burn_time=10)
