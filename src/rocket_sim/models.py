"""
Rocket airframes and recovery systems.

Defines:

- `Recovery` types (`Parachute`, `Streamer`) representing the
  drag device deployed during descent. `None` is also accepted by
  `Rocket.recovery` and represents a ballistic descent ("lawn dart").
- `Rocket`: the airframe + motor + recovery combination, plus the
  celestial body it's launching from.

The simulation orchestrator (`rocket_sim.simulation.RocketSimulation`)
owns the live trajectory state — `Rocket` itself is a pure
configuration / dataclass.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rocket_sim.motors import Motor
    from rocket_sim.physics import CelestialBody


@dataclass(frozen=True)
class Parachute:
    """
    Round parachute used during descent.

    Attributes:
        diameter_m: Canopy diameter in meters.
        drag_coefficient: Effective Cd. 0.75 is a reasonable default
            for a flat-circular hobby chute.
    """

    diameter_m: float
    drag_coefficient: float = 0.75

    def __post_init__(self) -> None:
        if self.diameter_m <= 0:
            raise ValueError(f"Parachute diameter must be > 0: {self.diameter_m}")
        if self.drag_coefficient <= 0:
            raise ValueError(f"Parachute Cd must be > 0: {self.drag_coefficient}")

    @property
    def cross_sectional_area(self) -> float:
        """Effective area used in F_drag = ½ρv²·Cd·A (m²)."""
        return math.pi * (self.diameter_m / 2.0) ** 2


@dataclass(frozen=True)
class Streamer:
    """
    Streamer (a long flat ribbon used for small rockets that don't need
    a chute).

    Attributes:
        length_m: Streamer length in meters.
        width_m: Streamer width in meters.
        drag_coefficient: Effective Cd. 0.5 is a rough default for
            a fluttering streamer.
    """

    length_m: float
    width_m: float
    drag_coefficient: float = 0.5

    def __post_init__(self) -> None:
        if self.length_m <= 0 or self.width_m <= 0:
            raise ValueError("Streamer dimensions must be > 0")
        if self.drag_coefficient <= 0:
            raise ValueError(f"Streamer Cd must be > 0: {self.drag_coefficient}")

    @property
    def cross_sectional_area(self) -> float:
        """Reference area for the drag equation (m²)."""
        return self.length_m * self.width_m


# Public type alias for the "recovery" slot on `Rocket`.
Recovery = Parachute | Streamer | None


@dataclass(frozen=True)
class Rocket:
    """
    A model-rocket airframe configured with a motor and recovery system.

    The total mass at ignition is `dry_mass_kg + motor.total_mass_kg`,
    decreasing during burn as propellant is consumed.

    Attributes:
        name: Display name (e.g. "Estes Alpha III").
        dry_mass_kg: Empty mass of the airframe (no motor) in kg.
        motor: Motor instance providing thrust and propellant mass.
        diameter_m: Airframe diameter in meters (used for drag area).
        drag_coefficient: Body drag coefficient. 0.5–0.8 typical for
            model rockets.
        recovery: `Parachute`, `Streamer`, or `None` (ballistic).
        body: Celestial body to launch from. Defaults to Earth.
    """

    name: str
    dry_mass_kg: float
    motor: Motor
    diameter_m: float
    drag_coefficient: float
    recovery: Recovery
    body: CelestialBody | None = None

    def __post_init__(self) -> None:
        if self.dry_mass_kg <= 0:
            raise ValueError(f"dry_mass_kg must be > 0: {self.dry_mass_kg}")
        if self.diameter_m <= 0:
            raise ValueError(f"diameter_m must be > 0: {self.diameter_m}")
        if self.drag_coefficient <= 0:
            raise ValueError(f"drag_coefficient must be > 0: {self.drag_coefficient}")

    @property
    def cross_sectional_area(self) -> float:
        """Airframe cross-sectional area (m²)."""
        return math.pi * (self.diameter_m / 2.0) ** 2

    @property
    def launch_mass_kg(self) -> float:
        """Total mass at ignition: dry mass + loaded motor mass (kg)."""
        return self.dry_mass_kg + self.motor.total_mass_kg

    def mass_at(self, t: float) -> float:
        """Total mass at time t since ignition (kg). Decreases during motor burn."""
        return self.dry_mass_kg + self.motor.mass_at(t)
