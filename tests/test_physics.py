"""Tests for gravitational helpers and built-in celestial bodies."""

from __future__ import annotations

import math

import pytest

from rocket_sim.physics import Atmosphere, CelestialBody, Physics


class TestGravity:
    def test_surface_gravity_earth(self) -> None:
        g = Physics.gravity_at_altitude(0)
        # GM/R^2 with our constants comes out to ~9.82
        assert 9.7 < g < 9.9

    def test_gravity_decreases_with_altitude(self) -> None:
        g0 = Physics.gravity_at_altitude(0)
        g1 = Physics.gravity_at_altitude(400_000)  # ~ISS
        assert g1 < g0
        assert 8.5 < g1 < 8.8

    def test_gravity_negative_altitude_raises(self) -> None:
        with pytest.raises(ValueError):
            Physics.gravity_at_altitude(-1)

    def test_gravity_on_moon(self) -> None:
        g = Physics.gravity_at_altitude(0, Physics.MOON)
        assert 1.5 < g < 1.7

    def test_gravity_on_mars(self) -> None:
        g = Physics.gravity_at_altitude(0, Physics.MARS)
        assert 3.6 < g < 3.8


class TestEscapeAndOrbital:
    def test_escape_velocity_earth_surface(self) -> None:
        v = Physics.escape_velocity(0)
        assert 11_180 < v < 11_200  # ~11.186 km/s

    def test_orbital_velocity_iss(self) -> None:
        v = Physics.orbital_velocity(400_000)
        assert 7_650 < v < 7_700  # ~7672 m/s

    def test_escape_is_sqrt2_times_orbital(self) -> None:
        for h in (0, 100_000, 400_000):
            v_esc = Physics.escape_velocity(h)
            v_orb = Physics.orbital_velocity(h)
            assert math.isclose(v_esc, math.sqrt(2) * v_orb, rel_tol=1e-6)


class TestCelestialBody:
    def test_surface_gravity_property(self) -> None:
        assert math.isclose(Physics.EARTH.surface_gravity, Physics.gravity_at_altitude(0))

    def test_negative_mass_raises(self) -> None:
        with pytest.raises(ValueError):
            CelestialBody(name="Bad", mass=-1, radius=1)

    def test_negative_radius_raises(self) -> None:
        with pytest.raises(ValueError):
            CelestialBody(name="Bad", mass=1, radius=-1)

    def test_all_builtin_bodies_present(self) -> None:
        assert Physics.EARTH.atmosphere is not None
        assert Physics.MOON.atmosphere is None  # vacuum
        assert Physics.MARS.atmosphere is not None
        assert Physics.VENUS.atmosphere is not None
        assert Physics.TITAN.atmosphere is not None


class TestAtmosphere:
    def test_earth_surface_density(self) -> None:
        atm = Atmosphere.earth()
        assert math.isclose(atm.density_at(0), 1.225, rel_tol=1e-3)

    def test_density_falls_off_at_scale_height(self) -> None:
        atm = Atmosphere.earth()
        assert math.isclose(
            atm.density_at(atm.scale_height), atm.surface_density / math.e, rel_tol=1e-6
        )

    def test_negative_altitude_returns_surface(self) -> None:
        atm = Atmosphere.earth()
        # Defensive: density_at should not blow up on a tiny negative number
        assert atm.density_at(-0.01) == atm.surface_density

    def test_mars_thinner_than_earth(self) -> None:
        assert Atmosphere.mars().surface_density < Atmosphere.earth().surface_density / 50

    def test_venus_thicker_than_earth(self) -> None:
        assert Atmosphere.venus().surface_density > Atmosphere.earth().surface_density * 50

    def test_titan_thicker_than_earth(self) -> None:
        assert Atmosphere.titan().surface_density > Atmosphere.earth().surface_density

    def test_invalid_atmosphere_raises(self) -> None:
        with pytest.raises(ValueError):
            Atmosphere(surface_density=-1, scale_height=1)
        with pytest.raises(ValueError):
            Atmosphere(surface_density=1, scale_height=0)
