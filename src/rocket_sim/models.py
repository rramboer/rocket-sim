"""
Rocket and Engine models for the simulation.

This module defines the core data structures representing rockets and
their propulsion systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rocket_sim.physics import Physics

if TYPE_CHECKING:
    from rocket_sim.physics import CelestialBody


@dataclass
class RocketConfig:
    """
    Configuration parameters for a rocket.

    This is a simple data container for rocket specifications that can be
    used to create Rocket instances.

    Attributes:
        mass: Total mass of the rocket in kilograms.
        thrust: Engine thrust force in Newtons.
        burn_time: Engine burn duration in seconds.
        name: Optional name/label for the rocket.
    """

    mass: float
    thrust: float
    burn_time: float
    name: str = "Custom Rocket"

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.mass <= 0:
            raise ValueError(f"Mass must be positive: {self.mass}")
        if self.thrust < 0:
            raise ValueError(f"Thrust cannot be negative: {self.thrust}")
        if self.burn_time < 0:
            raise ValueError(f"Burn time cannot be negative: {self.burn_time}")

    @property
    def thrust_to_weight_ratio(self) -> float:
        """Calculate thrust-to-weight ratio at sea level."""
        weight = self.mass * Physics.EARTH.surface_gravity
        return self.thrust / weight if weight > 0 else 0.0

    def to_dict(self) -> dict[str, float | str]:
        """Convert configuration to dictionary."""
        return {
            "mass": self.mass,
            "thrust": self.thrust,
            "burn_time": self.burn_time,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float | str]) -> RocketConfig:
        """Create configuration from dictionary."""
        return cls(
            mass=float(data["mass"]),
            thrust=float(data["thrust"]),
            burn_time=float(data["burn_time"]),
            name=str(data.get("name", "Custom Rocket")),
        )


@dataclass
class Engine:
    """
    Represents a rocket engine with constant thrust during its burn time.

    Attributes:
        thrust: Thrust force in Newtons.
        burn_time: Duration of thrust in seconds.
    """

    thrust: float  # Newtons
    burn_time: float  # seconds

    def __post_init__(self) -> None:
        """Validate engine parameters."""
        if self.thrust < 0:
            raise ValueError(f"Thrust cannot be negative: {self.thrust}")
        if self.burn_time < 0:
            raise ValueError(f"Burn time cannot be negative: {self.burn_time}")

    @property
    def total_impulse(self) -> float:
        """Calculate total impulse (thrust * time) in Newton-seconds."""
        return self.thrust * self.burn_time

    def is_burning(self, elapsed_time: float) -> bool:
        """Check if engine is burning at given time. Returns True for elapsed_time in [0, burn_time)."""
        return 0 <= elapsed_time < self.burn_time

    def get_thrust(self, elapsed_time: float) -> float:
        """
        Get thrust at a given time.

        Args:
            elapsed_time: Time since engine ignition in seconds.

        Returns:
            Thrust in Newtons (0 if burn completed).
        """
        return self.thrust if self.is_burning(elapsed_time) else 0.0


@dataclass
class Rocket:
    """
    Represents a rocket with physical state and propulsion.

    Note: Mass is held constant throughout the simulation; propellant
    burn is not modelled. This is the "constant-mass approximation."

    Attributes:
        mass: Rocket mass in kilograms (treated as constant).
        engine: Engine instance providing propulsion.
        body: Celestial body for gravity calculations. Defaults to Earth.
        altitude: Current altitude in meters.
        velocity: Current velocity in m/s (positive = upward).
        time: Elapsed time since launch in seconds.
    """

    mass: float
    engine: Engine
    body: CelestialBody | None = None
    altitude: float = field(default=0.0, init=False)
    velocity: float = field(default=0.0, init=False)
    time: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        """Validate rocket parameters."""
        if self.mass <= 0:
            raise ValueError(f"Mass must be positive: {self.mass}")

    @classmethod
    def from_config(
        cls,
        config: RocketConfig,
        body: CelestialBody | None = None,
    ) -> Rocket:
        """
        Create a Rocket instance from a RocketConfig.

        Args:
            config: Configuration parameters for the rocket.
            body: Celestial body for gravity. Defaults to Earth.

        Returns:
            A new Rocket instance.
        """
        engine = Engine(thrust=config.thrust, burn_time=config.burn_time)
        return cls(mass=config.mass, engine=engine, body=body)

    @property
    def _body(self) -> CelestialBody:
        """Resolve body to Earth if unset (kept private to avoid changing the dataclass field type)."""
        return self.body if self.body is not None else Physics.EARTH

    def reset(self) -> None:
        """Reset rocket to initial launch state."""
        self.altitude = 0.0
        self.velocity = 0.0
        self.time = 0.0

    def update(self, dt: float) -> tuple[float, float]:
        """
        Update rocket state for a time step.

        Computes acceleration from thrust and gravity, then updates
        velocity and position using symplectic Euler (Euler-Cromer)
        integration, which conserves energy better than the plain
        Euler method for orbital trajectories.

        Mass is held constant — no propellant burn is modelled.

        Args:
            dt: Time step in seconds.

        Returns:
            Tuple of (altitude, velocity) after the update.
        """
        gravity = Physics.gravity_at_altitude(self.altitude, self._body)

        thrust = self.engine.get_thrust(self.time)
        if thrust > 0:  # noqa: SIM108
            # Kept as if/else for readability; thrust and coast acceleration are physically distinct.
            # During burn: a = (T - mg) / m = T/m - g
            acceleration = thrust / self.mass - gravity
        else:
            # Coasting: only gravity
            acceleration = -gravity

        # Symplectic Euler: update velocity first, then position with new velocity
        self.velocity += acceleration * dt
        self.altitude += self.velocity * dt
        self.time += dt

        # Ground collision detection
        if self.altitude < 0:
            self.altitude = 0.0
            self.velocity = 0.0

        return self.altitude, self.velocity

    @property
    def kinetic_energy(self) -> float:
        """Calculate current kinetic energy in Joules."""
        return 0.5 * self.mass * self.velocity**2

    @property
    def potential_energy(self) -> float:
        """
        Calculate gravitational potential energy relative to the surface.

        Uses the exact integral of GMm/r² (variable gravity), expressed
        equivalently as PE = m·g₀·h · R/(R + h), where g₀ and R are the
        body's surface gravity and radius.
        """
        if self.altitude <= 0:
            return 0.0
        body = self._body
        g0 = body.surface_gravity
        r = body.radius
        return self.mass * g0 * self.altitude * (r / (r + self.altitude))

    @property
    def total_energy(self) -> float:
        """Calculate total mechanical energy in Joules."""
        return self.kinetic_energy + self.potential_energy

    @property
    def is_ascending(self) -> bool:
        """Check if rocket is moving upward."""
        return self.velocity > 0

    @property
    def is_on_ground(self) -> bool:
        """Check if rocket is on the ground."""
        return self.altitude <= 0 and self.velocity <= 0
