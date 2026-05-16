"""Pytest fixtures for the rocket-sim test suite."""

from __future__ import annotations

import pytest

from rocket_sim.config import SimulationConfig
from rocket_sim.models import Parachute, Rocket
from rocket_sim.motors import Motor, get_motor
from rocket_sim.physics import Atmosphere, CelestialBody, Physics
from rocket_sim.presets import get_kit


@pytest.fixture
def constant_thrust_motor() -> Motor:
    """A simple motor with constant thrust over its burn — useful for analytic tests."""
    return Motor(
        designation="TEST-1",
        name="Test constant-thrust motor",
        diameter_m=0.018,
        length_m=0.07,
        propellant_mass_kg=0.010,
        total_mass_kg=0.020,
        thrust_curve=((0.0, 5.0), (1.0, 5.0), (1.0, 0.0)),
        delay_seconds=0.0,
        manufacturer="Test",
    )


@pytest.fixture
def c6_motor() -> Motor:
    return get_motor("C6-5")


@pytest.fixture
def alpha_iii() -> Rocket:
    return get_kit("alpha-iii")


@pytest.fixture
def vacuum_body() -> CelestialBody:
    """Earth-mass body with no atmosphere — useful for ballistic-test cases."""
    return CelestialBody(
        name="VacuumEarth",
        mass=Physics.EARTH.mass,
        radius=Physics.EARTH.radius,
        atmosphere=None,
    )


@pytest.fixture
def earth() -> CelestialBody:
    return Physics.EARTH


@pytest.fixture
def moon() -> CelestialBody:
    return Physics.MOON


@pytest.fixture
def mars() -> CelestialBody:
    return Physics.MARS


@pytest.fixture
def fast_sim_config() -> SimulationConfig:
    return SimulationConfig(dt=0.05, max_time=300.0)


@pytest.fixture
def parachute() -> Parachute:
    return Parachute(diameter_m=0.30)


@pytest.fixture
def earth_atmosphere() -> Atmosphere:
    return Atmosphere.earth()
