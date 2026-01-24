"""
Tests for physics calculations.
"""

import math

import pytest

from rocket_sim.physics import Physics


class TestGravityAtAltitude:
    """Tests for gravity_at_altitude function."""

    def test_surface_gravity(self) -> None:
        """Test gravity at Earth's surface."""
        g = Physics.gravity_at_altitude(0)
        # Should be approximately 9.81 m/s^2
        assert 9.7 < g < 9.9

    def test_gravity_decreases_with_altitude(self) -> None:
        """Test that gravity decreases with altitude."""
        g_surface = Physics.gravity_at_altitude(0)
        g_100km = Physics.gravity_at_altitude(100_000)
        g_400km = Physics.gravity_at_altitude(400_000)

        assert g_surface > g_100km > g_400km

    def test_iss_orbit_gravity(self) -> None:
        """Test gravity at ISS orbit altitude (~400km)."""
        g = Physics.gravity_at_altitude(400_000)
        # Should be approximately 8.7 m/s^2
        assert 8.6 < g < 8.8

    def test_negative_altitude_raises_error(self) -> None:
        """Test that negative altitude raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Physics.gravity_at_altitude(-100)

    def test_custom_body(self) -> None:
        """Test gravity calculation with custom celestial body."""
        g_earth = Physics.gravity_at_altitude(0, Physics.EARTH)
        g_moon = Physics.gravity_at_altitude(0, Physics.MOON)

        # Moon surface gravity is about 1/6 of Earth's
        assert g_moon < g_earth
        assert 1.5 < g_moon < 1.7


class TestEscapeVelocity:
    """Tests for escape_velocity function."""

    def test_surface_escape_velocity(self) -> None:
        """Test escape velocity at Earth's surface."""
        v = Physics.escape_velocity(0)
        # Should be approximately 11.2 km/s
        assert 11_000 < v < 11_300

    def test_escape_velocity_decreases_with_altitude(self) -> None:
        """Test that escape velocity decreases with altitude."""
        v_surface = Physics.escape_velocity(0)
        v_400km = Physics.escape_velocity(400_000)

        assert v_surface > v_400km

    def test_negative_altitude_raises_error(self) -> None:
        """Test that negative altitude raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Physics.escape_velocity(-100)


class TestOrbitalVelocity:
    """Tests for orbital_velocity function."""

    def test_iss_orbital_velocity(self) -> None:
        """Test orbital velocity at ISS altitude."""
        v = Physics.orbital_velocity(400_000)
        # ISS orbital velocity is approximately 7.66 km/s
        assert 7_600 < v < 7_700

    def test_orbital_velocity_relationship(self) -> None:
        """Test that escape velocity = sqrt(2) * orbital velocity."""
        altitude = 400_000
        v_orbital = Physics.orbital_velocity(altitude)
        v_escape = Physics.escape_velocity(altitude)

        ratio = v_escape / v_orbital
        assert abs(ratio - math.sqrt(2)) < 0.01


class TestAtmosphericDensity:
    """Tests for atmospheric_density function."""

    def test_sea_level_density(self) -> None:
        """Test atmospheric density at sea level."""
        rho = Physics.atmospheric_density(0)
        assert abs(rho - 1.225) < 0.01

    def test_density_decreases_exponentially(self) -> None:
        """Test that density decreases with altitude."""
        rho_0 = Physics.atmospheric_density(0)
        rho_10km = Physics.atmospheric_density(10_000)
        rho_30km = Physics.atmospheric_density(30_000)

        assert rho_0 > rho_10km > rho_30km

    def test_above_karman_line(self) -> None:
        """Test that density is zero above Karman line."""
        rho = Physics.atmospheric_density(110_000)
        assert rho == 0.0

    def test_negative_altitude_raises_error(self) -> None:
        """Test that negative altitude raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Physics.atmospheric_density(-100)


class TestCelestialBody:
    """Tests for CelestialBody dataclass."""

    def test_surface_gravity(self) -> None:
        """Test surface gravity calculation."""
        g = Physics.EARTH.surface_gravity
        assert 9.7 < g < 9.9

    def test_moon_properties(self) -> None:
        """Test Moon celestial body properties."""
        assert Physics.MOON.name == "Moon"
        assert Physics.MOON.mass > 0
        assert Physics.MOON.radius > 0
