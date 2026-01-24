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
    Represents a rocket engine.

    Models a simple rocket engine with constant thrust output during
    its burn time.

    Attributes:
        thrust: Thrust force in Newtons.
        burn_time: Duration of thrust in seconds.
        specific_impulse: Engine efficiency in seconds (optional).
    """

    thrust: float  # Newtons
    burn_time: float  # seconds
    specific_impulse: float = 300.0  # seconds (typical for chemical rockets)

    def __post_init__(self) -> None:
        """Validate engine parameters."""
        if self.thrust < 0:
            raise ValueError(f"Thrust cannot be negative: {self.thrust}")
        if self.burn_time < 0:
            raise ValueError(f"Burn time cannot be negative: {self.burn_time}")
        if self.specific_impulse <= 0:
            raise ValueError(f"Specific impulse must be positive: {self.specific_impulse}")

    @property
    def total_impulse(self) -> float:
        """Calculate total impulse (thrust * time) in Newton-seconds."""
        return self.thrust * self.burn_time

    def is_burning(self, elapsed_time: float) -> bool:
        """Check if engine is still burning at given time."""
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

    This class models the rocket's physical properties and tracks its
    state (position, velocity) during simulation.

    Attributes:
        mass: Rocket mass in kilograms.
        engine: Engine instance providing propulsion.
        altitude: Current altitude in meters.
        velocity: Current velocity in m/s (positive = upward).
        time: Elapsed time since launch in seconds.
    """

    mass: float
    engine: Engine
    altitude: float = field(default=0.0, init=False)
    velocity: float = field(default=0.0, init=False)
    time: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        """Validate rocket parameters."""
        if self.mass <= 0:
            raise ValueError(f"Mass must be positive: {self.mass}")

    @classmethod
    def from_config(cls, config: RocketConfig) -> Rocket:
        """
        Create a Rocket instance from a RocketConfig.

        Args:
            config: Configuration parameters for the rocket.

        Returns:
            A new Rocket instance.
        """
        engine = Engine(thrust=config.thrust, burn_time=config.burn_time)
        return cls(mass=config.mass, engine=engine)

    def reset(self) -> None:
        """Reset rocket to initial launch state."""
        self.altitude = 0.0
        self.velocity = 0.0
        self.time = 0.0

    def update(
        self,
        dt: float,
        body: CelestialBody | None = None,
    ) -> tuple[float, float]:
        """
        Update rocket state for a time step.

        Computes acceleration from thrust and gravity, then updates
        velocity and position using simple Euler integration.

        Args:
            dt: Time step in seconds.
            body: Celestial body for gravity calculation. Defaults to Earth.

        Returns:
            Tuple of (altitude, velocity) after the update.
        """
        # Get current gravity
        gravity = Physics.gravity_at_altitude(self.altitude, body)

        # Calculate acceleration
        thrust = self.engine.get_thrust(self.time)
        if thrust > 0:  # noqa: SIM108
            # During burn: a = (T - mg) / m = T/m - g
            acceleration = thrust / self.mass - gravity
        else:
            # Coasting: only gravity
            acceleration = -gravity

        # Euler integration
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
        Calculate gravitational potential energy relative to surface.

        Uses the exact formula accounting for varying gravity with altitude.
        """
        g0 = Physics.EARTH.surface_gravity
        r = Physics.EARTH.radius
        # PE = mgh * (r / (r + h)) for varying gravity
        if self.altitude == 0:
            return 0.0
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
        return self.altitude == 0 and self.velocity == 0
