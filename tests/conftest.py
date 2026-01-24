"""
Pytest configuration and fixtures for rocket-sim tests.
"""

import pytest

from rocket_sim.config import SimulationConfig
from rocket_sim.models import Engine, Rocket, RocketConfig


@pytest.fixture
def simple_engine() -> Engine:
    """Create a simple test engine."""
    return Engine(thrust=10000, burn_time=10)


@pytest.fixture
def simple_rocket(simple_engine: Engine) -> Rocket:
    """Create a simple test rocket."""
    return Rocket(mass=1000, engine=simple_engine)


@pytest.fixture
def falcon9_config() -> RocketConfig:
    """Create Falcon 9 configuration."""
    return RocketConfig(
        mass=549054,
        thrust=7607000,
        burn_time=162,
        name="Falcon 9",
    )


@pytest.fixture
def simple_config() -> RocketConfig:
    """Create a simple rocket configuration for testing."""
    return RocketConfig(
        mass=1000,
        thrust=20000,
        burn_time=30,
        name="Test Rocket",
    )


@pytest.fixture
def sim_config() -> SimulationConfig:
    """Create default simulation configuration."""
    return SimulationConfig(dt=0.1, max_time=1000)


@pytest.fixture
def fast_sim_config() -> SimulationConfig:
    """Create fast simulation configuration for quicker tests."""
    return SimulationConfig(dt=1.0, max_time=500)
