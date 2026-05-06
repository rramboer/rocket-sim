"""Tests for Rocket, Parachute, Streamer."""

from __future__ import annotations

import math

import pytest

from rocket_sim.models import Parachute, Rocket, Streamer
from rocket_sim.motors import Motor


class TestParachute:
    def test_area(self) -> None:
        p = Parachute(diameter_m=1.0)
        assert math.isclose(p.cross_sectional_area, math.pi / 4)

    def test_negative_diameter_raises(self) -> None:
        with pytest.raises(ValueError):
            Parachute(diameter_m=-0.1)

    def test_zero_cd_raises(self) -> None:
        with pytest.raises(ValueError):
            Parachute(diameter_m=0.3, drag_coefficient=0)


class TestStreamer:
    def test_area(self) -> None:
        s = Streamer(length_m=0.5, width_m=0.05)
        assert math.isclose(s.cross_sectional_area, 0.025)

    def test_negative_dimension_raises(self) -> None:
        with pytest.raises(ValueError):
            Streamer(length_m=-0.5, width_m=0.05)


class TestRocket:
    def test_launch_mass(self, constant_thrust_motor: Motor) -> None:
        rocket = Rocket(
            name="Test",
            dry_mass_kg=0.030,
            motor=constant_thrust_motor,
            diameter_m=0.025,
            drag_coefficient=0.5,
            recovery=Parachute(diameter_m=0.3),
        )
        assert math.isclose(rocket.launch_mass_kg, 0.030 + 0.020)

    def test_mass_decreases_during_burn(self, constant_thrust_motor: Motor) -> None:
        rocket = Rocket(
            name="Test",
            dry_mass_kg=0.030,
            motor=constant_thrust_motor,
            diameter_m=0.025,
            drag_coefficient=0.5,
            recovery=None,
        )
        # Constant thrust over 1 s: 50 % of propellant burned at t=0.5 s
        m_at_half = rocket.mass_at(0.5)
        assert math.isclose(m_at_half, 0.030 + 0.020 - 0.005, rel_tol=1e-6)

    def test_negative_mass_raises(self, constant_thrust_motor: Motor) -> None:
        with pytest.raises(ValueError):
            Rocket(
                name="X",
                dry_mass_kg=-1,
                motor=constant_thrust_motor,
                diameter_m=0.02,
                drag_coefficient=0.5,
                recovery=None,
            )

    def test_zero_diameter_raises(self, constant_thrust_motor: Motor) -> None:
        with pytest.raises(ValueError):
            Rocket(
                name="X",
                dry_mass_kg=0.05,
                motor=constant_thrust_motor,
                diameter_m=0,
                drag_coefficient=0.5,
                recovery=None,
            )

    def test_cross_sectional_area(self, constant_thrust_motor: Motor) -> None:
        rocket = Rocket(
            name="Test",
            dry_mass_kg=0.030,
            motor=constant_thrust_motor,
            diameter_m=0.04,
            drag_coefficient=0.5,
            recovery=None,
        )
        assert math.isclose(rocket.cross_sectional_area, math.pi * 0.02**2)
