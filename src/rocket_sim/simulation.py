"""
Core simulation engine for rocket trajectory calculations.

This module provides the main simulation class that orchestrates the
physics calculations and tracks simulation state.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rocket_sim.config import SimulationConfig
from rocket_sim.models import Rocket, RocketConfig
from rocket_sim.physics import Physics

if TYPE_CHECKING:
    from rocket_sim.physics import CelestialBody

logger = logging.getLogger(__name__)


@dataclass
class SimulationState:
    """
    Represents the state of the simulation at a point in time.

    Attributes:
        time: Elapsed time in seconds.
        altitude: Altitude in meters.
        velocity: Velocity in m/s.
        acceleration: Acceleration in m/s^2.
        is_burning: Whether the engine is firing.
    """

    time: float
    altitude: float
    velocity: float
    acceleration: float = 0.0
    is_burning: bool = False

    def to_tuple(self) -> tuple[float, float, float]:
        """Return (time, altitude, velocity) tuple."""
        return (self.time, self.altitude, self.velocity)


@dataclass
class SimulationResult:
    """
    Complete results from a rocket simulation.

    Attributes:
        rocket_name: Name of the simulated rocket.
        config: Configuration used for the rocket.
        states: List of simulation states over time.
        max_altitude: Maximum altitude reached in meters.
        max_velocity: Maximum velocity reached in m/s.
        flight_time: Total flight time in seconds.
        escaped: Whether the rocket achieved escape velocity.
        landing_time: Time of landing (if applicable).
    """

    rocket_name: str
    config: RocketConfig
    states: list[SimulationState] = field(default_factory=list)
    max_altitude: float = 0.0
    max_velocity: float = 0.0
    flight_time: float = 0.0
    escaped: bool = False
    landing_time: float | None = None

    @property
    def time_data(self) -> list[float]:
        """Extract time values from states."""
        return [s.time for s in self.states]

    @property
    def altitude_data(self) -> list[float]:
        """Extract altitude values from states."""
        return [s.altitude for s in self.states]

    @property
    def velocity_data(self) -> list[float]:
        """Extract velocity values from states."""
        return [s.velocity for s in self.states]

    @property
    def max_altitude_km(self) -> float:
        """Maximum altitude in kilometers."""
        return self.max_altitude / 1000

    def get_state_at_time(self, time: float) -> SimulationState | None:
        """
        Get simulation state closest to the specified time.

        Args:
            time: Time in seconds.

        Returns:
            SimulationState closest to the specified time, or None if no states.
        """
        if not self.states:
            return None

        return min(self.states, key=lambda s: abs(s.time - time))

    def summary(self) -> str:
        """Generate a summary string of the simulation results."""
        status = "Escaped" if self.escaped else "Landed"
        return (
            f"Simulation Results: {self.rocket_name}\n"
            f"  Status:          {status}\n"
            f"  Max Altitude:    {self.max_altitude_km:,.2f} km\n"
            f"  Max Velocity:    {self.max_velocity:,.2f} m/s\n"
            f"  Flight Time:     {self.flight_time:,.2f} s"
        )


class RocketSimulation:
    """
    Rocket launch simulation engine.

    This class runs physics simulations for rocket trajectories,
    tracking the rocket's altitude, velocity, and other parameters
    over time.

    Example:
        >>> from rocket_sim import RocketSimulation, get_preset
        >>> config = get_preset("Falcon 9")
        >>> sim = RocketSimulation(config)
        >>> result = sim.run()
        >>> print(f"Max altitude: {result.max_altitude_km:.2f} km")
    """

    def __init__(
        self,
        rocket_config: RocketConfig,
        sim_config: SimulationConfig | None = None,
        body: CelestialBody | None = None,
    ) -> None:
        """
        Initialize the simulation.

        Args:
            rocket_config: Configuration for the rocket to simulate.
            sim_config: Simulation parameters. Uses defaults if not provided.
            body: Celestial body for gravity. Defaults to Earth.
        """
        self.rocket_config = rocket_config
        self.sim_config = sim_config or SimulationConfig()
        self.body = body or Physics.EARTH

        # Create rocket instance bound to this simulation's body so that
        # gravity and energy properties stay consistent.
        self.rocket = Rocket.from_config(rocket_config, body=self.body)

        logger.debug(
            f"Initialized simulation for {rocket_config.name} "
            f"(mass={rocket_config.mass}, thrust={rocket_config.thrust})"
        )

    def reset(self) -> None:
        """Reset the simulation to initial state."""
        self.rocket.reset()
        logger.debug("Simulation reset")

    def step(self, dt: float | None = None) -> SimulationState:
        """
        Perform a single simulation step.

        Args:
            dt: Time step in seconds. Uses config default if not specified.

        Returns:
            Current simulation state after the step.
        """
        if dt is None:
            dt = self.sim_config.dt

        old_velocity = self.rocket.velocity
        altitude, velocity = self.rocket.update(dt)

        acceleration = (velocity - old_velocity) / dt
        is_burning = self.rocket.engine.is_burning(self.rocket.time)

        return SimulationState(
            time=self.rocket.time,
            altitude=altitude,
            velocity=velocity,
            acceleration=acceleration,
            is_burning=is_burning,
        )

    def run(self) -> SimulationResult:
        """
        Run the complete simulation.

        Simulates the rocket from launch until it either lands back
        on the surface or achieves escape velocity.

        Returns:
            SimulationResult containing all trajectory data and statistics.
        """
        self.reset()

        dt = self.sim_config.dt
        max_time = self.sim_config.max_time

        result = SimulationResult(
            rocket_name=self.rocket_config.name,
            config=self.rocket_config,
        )

        logger.info(f"Starting simulation: {self.rocket_config.name}")

        # Initial state
        initial_state = SimulationState(
            time=0.0,
            altitude=0.0,
            velocity=0.0,
            acceleration=0.0,
            is_burning=True,
        )
        result.states.append(initial_state)

        while self.rocket.time <= max_time:
            state = self.step(dt)
            result.states.append(state)

            # Track maximums
            if state.altitude > result.max_altitude:
                result.max_altitude = state.altitude
            if abs(state.velocity) > result.max_velocity:
                result.max_velocity = abs(state.velocity)

            # Check for landing
            if self.rocket.is_on_ground and self.rocket.time > dt:
                result.landing_time = self.rocket.time
                result.flight_time = self.rocket.time
                logger.info(f"Rocket landed at t={self.rocket.time:.2f}s")
                break

            # Check for escape velocity
            if self.sim_config.detect_escape:
                escape_vel = Physics.escape_velocity(state.altitude, self.body)
                if state.velocity > escape_vel > 0:
                    result.escaped = True
                    result.flight_time = self.rocket.time
                    logger.info(
                        f"Escape velocity achieved at t={self.rocket.time:.2f}s, "
                        f"alt={state.altitude / 1000:.2f}km"
                    )
                    break

        if result.flight_time == 0:
            result.flight_time = self.rocket.time

        logger.info(
            f"Simulation complete: max_alt={result.max_altitude_km:.2f}km, "
            f"flight_time={result.flight_time:.2f}s"
        )

        return result

    def run_generator(self) -> Iterator[SimulationState]:
        """
        Run simulation as a generator, yielding states.

        This is useful for real-time visualization or progress tracking.

        Yields:
            SimulationState for each time step.
        """
        self.reset()

        dt = self.sim_config.dt
        max_time = self.sim_config.max_time

        # Yield initial state
        yield SimulationState(
            time=0.0,
            altitude=0.0,
            velocity=0.0,
            acceleration=0.0,
            is_burning=True,
        )

        while self.rocket.time <= max_time:
            state = self.step(dt)
            yield state

            # Check for landing
            if self.rocket.is_on_ground and self.rocket.time > dt:
                break

            # Check for escape velocity
            if self.sim_config.detect_escape:
                escape_vel = Physics.escape_velocity(state.altitude, self.body)
                if state.velocity > escape_vel > 0:
                    break


def simulate_rocket(
    config: RocketConfig,
    sim_config: SimulationConfig | None = None,
    body: CelestialBody | None = None,
) -> SimulationResult:
    """
    Convenience function to run a single rocket simulation.

    Args:
        config: Rocket configuration.
        sim_config: Optional simulation configuration.
        body: Celestial body for gravity. Defaults to Earth.

    Returns:
        SimulationResult with trajectory data.
    """
    sim = RocketSimulation(config, sim_config, body=body)
    return sim.run()


def simulate_multiple(
    configs: list[RocketConfig],
    sim_config: SimulationConfig | None = None,
    body: CelestialBody | None = None,
) -> list[SimulationResult]:
    """
    Simulate multiple rockets.

    Args:
        configs: List of rocket configurations.
        sim_config: Optional simulation configuration (shared).
        body: Celestial body for gravity (shared). Defaults to Earth.

    Returns:
        List of SimulationResult objects.
    """
    return [simulate_rocket(config, sim_config, body=body) for config in configs]
