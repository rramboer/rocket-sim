"""
Physics calculations for rocket simulation.

This module provides physics-related calculations including gravitational
acceleration, escape velocity, and other orbital mechanics computations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class CelestialBody:
    """Represents a celestial body with gravitational properties."""

    name: str
    mass: float  # kg
    radius: float  # meters

    @property
    def surface_gravity(self) -> float:
        """Calculate surface gravity in m/s^2."""
        return Physics.G * self.mass / (self.radius**2)


class Physics:
    """
    Physics calculations for rocket trajectories.

    This class provides static methods for computing gravitational effects,
    escape velocities, and other physics-related values needed for accurate
    rocket trajectory simulation.

    Constants:
        G: Universal gravitational constant (m^3/kg/s^2)
        EARTH: Earth's physical properties
    """

    G: ClassVar[float] = 6.67430e-11  # Gravitational constant (m^3/kg/s^2)

    # Pre-defined celestial bodies
    EARTH: ClassVar[CelestialBody] = CelestialBody(
        name="Earth",
        mass=5.972e24,  # kg
        radius=6.371e6,  # meters
    )

    MOON: ClassVar[CelestialBody] = CelestialBody(
        name="Moon",
        mass=7.342e22,  # kg
        radius=1.737e6,  # meters
    )

    MARS: ClassVar[CelestialBody] = CelestialBody(
        name="Mars",
        mass=6.417e23,  # kg
        radius=3.390e6,  # meters
    )

    @staticmethod
    def gravity_at_altitude(
        altitude: float,
        body: CelestialBody | None = None,
    ) -> float:
        """
        Calculate gravitational acceleration at a given altitude.

        Uses Newton's law of universal gravitation with the inverse-square law
        to compute gravity at any altitude above the surface.

        Args:
            altitude: Height above surface in meters. Must be >= 0.
            body: Celestial body to use. Defaults to Earth.

        Returns:
            Gravitational acceleration in m/s^2.

        Raises:
            ValueError: If altitude is negative.

        Examples:
            >>> Physics.gravity_at_altitude(0)  # Surface gravity
            9.819...
            >>> Physics.gravity_at_altitude(400_000)  # ISS orbit ~400km
            8.676...
        """
        if altitude < 0:
            raise ValueError(f"Altitude cannot be negative: {altitude}")

        if body is None:
            body = Physics.EARTH

        distance_from_center = body.radius + altitude
        return Physics.G * body.mass / (distance_from_center**2)

    @staticmethod
    def escape_velocity(
        altitude: float,
        body: CelestialBody | None = None,
    ) -> float:
        """
        Calculate escape velocity at a given altitude.

        Escape velocity is the minimum speed needed for an object to escape
        from the gravitational influence of a celestial body without further
        propulsion.

        Args:
            altitude: Height above surface in meters. Must be >= 0.
            body: Celestial body to use. Defaults to Earth.

        Returns:
            Escape velocity in m/s.

        Raises:
            ValueError: If altitude is negative.

        Examples:
            >>> Physics.escape_velocity(0)  # From Earth's surface
            11185.7...
            >>> Physics.escape_velocity(400_000)  # From ISS orbit
            10926.5...
        """
        if altitude < 0:
            raise ValueError(f"Altitude cannot be negative: {altitude}")

        if body is None:
            body = Physics.EARTH

        distance_from_center = body.radius + altitude
        return math.sqrt(2 * Physics.G * body.mass / distance_from_center)

    @staticmethod
    def orbital_velocity(
        altitude: float,
        body: CelestialBody | None = None,
    ) -> float:
        """
        Calculate circular orbital velocity at a given altitude.

        This is the velocity needed to maintain a stable circular orbit
        at the specified altitude.

        Args:
            altitude: Height above surface in meters. Must be >= 0.
            body: Celestial body to use. Defaults to Earth.

        Returns:
            Orbital velocity in m/s.

        Examples:
            >>> Physics.orbital_velocity(400_000)  # ISS orbital velocity
            7672.4...
        """
        if altitude < 0:
            raise ValueError(f"Altitude cannot be negative: {altitude}")

        if body is None:
            body = Physics.EARTH

        distance_from_center = body.radius + altitude
        return math.sqrt(Physics.G * body.mass / distance_from_center)

    @staticmethod
    def atmospheric_density(altitude: float) -> float:
        """
        Estimate atmospheric density using exponential atmosphere model.

        This is a simplified model that assumes exponential decay of
        atmospheric density with altitude. Accurate for altitudes up to
        about 100 km.

        Args:
            altitude: Height above surface in meters. Must be >= 0.

        Returns:
            Atmospheric density in kg/m^3.

        Note:
            Returns 0 for altitudes above 100 km (Karman line).
        """
        if altitude < 0:
            raise ValueError(f"Altitude cannot be negative: {altitude}")

        # Above Karman line, negligible atmosphere
        if altitude > 100_000:
            return 0.0

        # Sea level density and scale height
        rho_0 = 1.225  # kg/m^3 at sea level
        scale_height = 8500  # meters

        return rho_0 * math.exp(-altitude / scale_height)

    @staticmethod
    def drag_force(
        velocity: float,
        altitude: float,
        drag_coefficient: float,
        cross_sectional_area: float,
    ) -> float:
        """
        Calculate aerodynamic drag force.

        Uses the standard drag equation: F_d = 0.5 * rho * v^2 * C_d * A

        Args:
            velocity: Speed in m/s.
            altitude: Height above surface in meters.
            drag_coefficient: Dimensionless drag coefficient (typically 0.2-0.5 for rockets).
            cross_sectional_area: Reference area in m^2.

        Returns:
            Drag force in Newtons (always positive, opposing motion).
        """
        rho = Physics.atmospheric_density(altitude)
        return 0.5 * rho * velocity**2 * drag_coefficient * cross_sectional_area
