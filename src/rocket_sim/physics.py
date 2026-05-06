"""
Physics primitives for rocket trajectory simulation.

This module provides:

- `Atmosphere`: an exponential-atmosphere model used to compute air density
  at altitude.
- `CelestialBody`: gravitational and atmospheric properties of a planet
  or moon. Includes pre-defined bodies (Earth, Moon, Mars, Venus, Titan).
- `Physics`: a static-method namespace for gravitational helpers
  (`gravity_at_altitude`, `escape_velocity`, `orbital_velocity`).

Drag and mass-loss are integrated directly into the simulation loop
(see `rocket_sim.simulation`); they are not exposed here as standalone
helpers.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Atmosphere:
    """
    Exponential-atmosphere model.

    Density decays as `rho(h) = surface_density * exp(-h / scale_height)`.
    Set `atmosphere=None` on a `CelestialBody` to model a vacuum (no drag).

    Attributes:
        surface_density: Density at the surface in kg/m^3.
        scale_height: Scale height in meters.
    """

    surface_density: float  # kg/m^3
    scale_height: float  # meters

    def __post_init__(self) -> None:
        if self.surface_density < 0:
            raise ValueError(f"surface_density must be >= 0: {self.surface_density}")
        if self.scale_height <= 0:
            raise ValueError(f"scale_height must be > 0: {self.scale_height}")

    def density_at(self, altitude: float) -> float:
        """
        Return atmospheric density at the given altitude (meters above surface).

        Returns 0 for negative altitudes (defensive — should not happen in normal sim use).
        """
        if altitude < 0:
            return self.surface_density
        return self.surface_density * math.exp(-altitude / self.scale_height)

    @classmethod
    def earth(cls) -> Atmosphere:
        """Earth: 1.225 kg/m^3 surface, 8500 m scale height."""
        return cls(surface_density=1.225, scale_height=8500.0)

    @classmethod
    def mars(cls) -> Atmosphere:
        """Mars: ~0.020 kg/m^3 surface, ~11100 m scale height."""
        return cls(surface_density=0.020, scale_height=11100.0)

    @classmethod
    def venus(cls) -> Atmosphere:
        """Venus: ~65 kg/m^3 surface (very thick), ~15900 m scale height."""
        return cls(surface_density=65.0, scale_height=15900.0)

    @classmethod
    def titan(cls) -> Atmosphere:
        """Titan (Saturn's moon): ~5.4 kg/m^3 surface, ~21000 m scale height."""
        return cls(surface_density=5.4, scale_height=21000.0)


@dataclass(frozen=True)
class CelestialBody:
    """
    Represents a celestial body with gravitational and atmospheric properties.

    Attributes:
        name: Display name (e.g. "Earth").
        mass: Body mass in kilograms.
        radius: Body radius in meters.
        atmosphere: Atmosphere model, or None for a vacuum (no drag).
    """

    name: str
    mass: float  # kg
    radius: float  # meters
    atmosphere: Atmosphere | None = None

    def __post_init__(self) -> None:
        if self.mass <= 0:
            raise ValueError(f"Body mass must be > 0: {self.mass}")
        if self.radius <= 0:
            raise ValueError(f"Body radius must be > 0: {self.radius}")

    @property
    def surface_gravity(self) -> float:
        """Surface gravitational acceleration in m/s^2."""
        return Physics.G * self.mass / (self.radius**2)


class Physics:
    """
    Static gravitational helpers and pre-defined celestial bodies.

    Constants:
        G: Universal gravitational constant (m^3/kg/s^2).
        EARTH, MOON, MARS, VENUS, TITAN: pre-defined `CelestialBody` instances.
    """

    G: ClassVar[float] = 6.67430e-11

    EARTH: ClassVar[CelestialBody] = CelestialBody(
        name="Earth",
        mass=5.972e24,
        radius=6.371e6,
        atmosphere=Atmosphere.earth(),
    )

    MOON: ClassVar[CelestialBody] = CelestialBody(
        name="Moon",
        mass=7.342e22,
        radius=1.737e6,
        atmosphere=None,  # vacuum
    )

    MARS: ClassVar[CelestialBody] = CelestialBody(
        name="Mars",
        mass=6.417e23,
        radius=3.390e6,
        atmosphere=Atmosphere.mars(),
    )

    VENUS: ClassVar[CelestialBody] = CelestialBody(
        name="Venus",
        mass=4.867e24,
        radius=6.0518e6,
        atmosphere=Atmosphere.venus(),
    )

    TITAN: ClassVar[CelestialBody] = CelestialBody(
        name="Titan",
        mass=1.3452e23,
        radius=2.5747e6,
        atmosphere=Atmosphere.titan(),
    )

    @staticmethod
    def gravity_at_altitude(
        altitude: float,
        body: CelestialBody | None = None,
    ) -> float:
        """
        Gravitational acceleration at the given altitude above the surface (m/s^2).

        Uses the inverse-square law. For altitudes below the surface, raises ValueError.

        Args:
            altitude: Height above the surface in meters. Must be >= 0.
            body: Celestial body. Defaults to Earth.

        Examples:
            >>> Physics.gravity_at_altitude(
            ...     0
            ... )  # Earth surface (~9.82, slightly above conventional 9.80665)
            9.819...
            >>> Physics.gravity_at_altitude(400_000)  # ~ISS altitude
            8.694...
        """
        if altitude < 0:
            raise ValueError(f"Altitude cannot be negative: {altitude}")
        if body is None:
            body = Physics.EARTH
        r = body.radius + altitude
        return Physics.G * body.mass / (r * r)

    @staticmethod
    def escape_velocity(
        altitude: float,
        body: CelestialBody | None = None,
    ) -> float:
        """
        Escape velocity at the given altitude (m/s).

        Standalone utility; not used by the trajectory simulator (hobby
        rockets do not approach escape speeds), but useful for educational
        comparisons.

        Args:
            altitude: Height above the surface in meters. Must be >= 0.
            body: Celestial body. Defaults to Earth.

        Examples:
            >>> Physics.escape_velocity(0)
            11185.9...
        """
        if altitude < 0:
            raise ValueError(f"Altitude cannot be negative: {altitude}")
        if body is None:
            body = Physics.EARTH
        r = body.radius + altitude
        return math.sqrt(2 * Physics.G * body.mass / r)

    @staticmethod
    def orbital_velocity(
        altitude: float,
        body: CelestialBody | None = None,
    ) -> float:
        """
        Circular-orbit velocity at the given altitude (m/s).

        Standalone utility; not used by the trajectory simulator.

        Examples:
            >>> Physics.orbital_velocity(400_000)
            7672.4...
        """
        if altitude < 0:
            raise ValueError(f"Altitude cannot be negative: {altitude}")
        if body is None:
            body = Physics.EARTH
        r = body.radius + altitude
        return math.sqrt(Physics.G * body.mass / r)
