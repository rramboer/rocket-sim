"""
Three-phase trajectory simulation for hobby rockets.

The simulator advances the rocket through three flight phases:

- BOOST: motor is producing thrust. Forces: thrust(t), drag, gravity.
  Mass decreases as propellant is consumed (constant-Isp model).
- COAST: motor has burned out, rocket continues upward (or starts
  falling) until recovery deploys. Forces: drag, gravity.
- DESCENT: recovery has deployed. Forces: drag (now using the recovery
  device's much larger Cd·A), gravity. Terminates when altitude reaches
  ground level.

Apogee is detected as the time of maximum altitude. Recovery deploys
either at apogee (`SimulationConfig.deploy_mode = "apogee"`) or at the
motor's ejection time (`burn_time + delay_seconds`, the realistic
default).

Integration uses symplectic (Euler-Cromer) Euler: velocity updates
first, then position with the updated velocity. This conserves energy
better than plain forward Euler and is adequate at the small timesteps
hobby trajectories require.
"""

from __future__ import annotations

import csv
import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from rocket_sim.config import SimulationConfig
from rocket_sim.models import Parachute, Rocket, Streamer
from rocket_sim.physics import Physics

logger = logging.getLogger(__name__)


class FlightPhase(Enum):
    """Discrete phases of a model-rocket flight."""

    BOOST = "boost"
    COAST = "coast"
    DESCENT = "descent"
    LANDED = "landed"


@dataclass(frozen=True)
class SimulationState:
    """A snapshot of simulation state at a single timestep."""

    time: float  # seconds since ignition
    altitude: float  # meters above launch site
    velocity: float  # m/s, positive = upward
    acceleration: float  # m/s²
    mass: float  # kg
    thrust: float  # N (signed; always >= 0 in this 1-D model)
    drag: float  # N (signed; always opposing velocity)
    phase: FlightPhase


@dataclass
class SimulationResult:
    """
    Complete results from a single rocket simulation.

    Most fields are populated by `RocketSimulation.run()`. Time-series
    accessors (`time_data`, `altitude_data`, `velocity_data`) read from
    `states`.
    """

    rocket_name: str
    states: list[SimulationState] = field(default_factory=list)
    apogee_m: float = 0.0
    apogee_time_s: float = 0.0
    burnout_altitude_m: float = 0.0
    burnout_velocity_ms: float = 0.0
    burnout_time_s: float = 0.0
    max_velocity_ms: float = 0.0
    max_acceleration_ms2: float = 0.0
    flight_time_s: float = 0.0
    recovery_deployment_time_s: float | None = None
    landing_velocity_ms: float = 0.0
    deployed_below_ground: bool = (
        False  # True if the rocket hit before recovery deployed (lawn dart)
    )

    @property
    def time_data(self) -> list[float]:
        return [s.time for s in self.states]

    @property
    def altitude_data(self) -> list[float]:
        return [s.altitude for s in self.states]

    @property
    def velocity_data(self) -> list[float]:
        return [s.velocity for s in self.states]

    @property
    def thrust_data(self) -> list[float]:
        return [s.thrust for s in self.states]

    @property
    def mass_data(self) -> list[float]:
        return [s.mass for s in self.states]

    @property
    def apogee_km(self) -> float:
        return self.apogee_m / 1000.0

    def summary(self) -> str:
        """Multi-line text summary suitable for CLI output."""
        deploy = (
            f"{self.recovery_deployment_time_s:.2f} s"
            if self.recovery_deployment_time_s is not None
            else "did not deploy"
        )
        warn = " (LAWN DART)" if self.deployed_below_ground else ""
        return (
            f"Simulation Results: {self.rocket_name}\n"
            f"  Apogee:               {self.apogee_m:7.2f} m at t = {self.apogee_time_s:.2f} s\n"
            f"  Max velocity:         {self.max_velocity_ms:7.2f} m/s\n"
            f"  Max acceleration:     {self.max_acceleration_ms2:7.2f} m/s² "
            f"({self.max_acceleration_ms2 / 9.80665:.2f} g)\n"
            f"  Burnout altitude:     {self.burnout_altitude_m:7.2f} m at t = {self.burnout_time_s:.2f} s\n"
            f"  Burnout velocity:     {self.burnout_velocity_ms:7.2f} m/s\n"
            f"  Recovery deployment:  {deploy}{warn}\n"
            f"  Flight time:          {self.flight_time_s:7.2f} s\n"
            f"  Landing velocity:     {self.landing_velocity_ms:7.2f} m/s"
        )

    # --- Export helpers ---------------------------------------------------

    _CSV_COLUMNS = (
        "time_s",
        "altitude_m",
        "velocity_ms",
        "acceleration_ms2",
        "mass_kg",
        "thrust_n",
        "drag_n",
        "phase",
    )

    def to_csv(self, path: Path | str) -> None:
        """
        Write the time-series of states to a CSV file.

        Columns: time_s, altitude_m, velocity_ms, acceleration_ms2,
        mass_kg, thrust_n, drag_n, phase. One row per simulation step.
        """
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self._CSV_COLUMNS)
            for s in self.states:
                writer.writerow(
                    [
                        s.time,
                        s.altitude,
                        s.velocity,
                        s.acceleration,
                        s.mass,
                        s.thrust,
                        s.drag,
                        s.phase.value,
                    ]
                )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict containing summary stats and the time-series."""
        return {
            "rocket_name": self.rocket_name,
            "summary": {
                "apogee_m": self.apogee_m,
                "apogee_time_s": self.apogee_time_s,
                "burnout_altitude_m": self.burnout_altitude_m,
                "burnout_velocity_ms": self.burnout_velocity_ms,
                "burnout_time_s": self.burnout_time_s,
                "max_velocity_ms": self.max_velocity_ms,
                "max_acceleration_ms2": self.max_acceleration_ms2,
                "flight_time_s": self.flight_time_s,
                "recovery_deployment_time_s": self.recovery_deployment_time_s,
                "landing_velocity_ms": self.landing_velocity_ms,
                "deployed_below_ground": self.deployed_below_ground,
            },
            "states": [
                {
                    "time_s": s.time,
                    "altitude_m": s.altitude,
                    "velocity_ms": s.velocity,
                    "acceleration_ms2": s.acceleration,
                    "mass_kg": s.mass,
                    "thrust_n": s.thrust,
                    "drag_n": s.drag,
                    "phase": s.phase.value,
                }
                for s in self.states
            ],
        }

    def to_json(self, path: Path | str, indent: int | None = 2) -> None:
        """Write the result (summary + time-series) to a JSON file."""
        Path(path).write_text(json.dumps(self.to_dict(), indent=indent))


def _recovery_drag_term(rocket: Rocket) -> tuple[float, float]:
    """
    Return ``(Cd, area)`` to use during the descent phase.

    For ballistic descent (no recovery), falls back to the airframe's
    own drag.
    """
    rec = rocket.recovery
    if isinstance(rec, (Parachute, Streamer)):
        return rec.drag_coefficient, rec.cross_sectional_area
    return rocket.drag_coefficient, rocket.cross_sectional_area


class RocketSimulation:
    """
    Trajectory simulator for a single hobby rocket.

    Example:
        >>> from rocket_sim import RocketSimulation, get_kit
        >>> rocket = get_kit("alpha-iii")
        >>> sim = RocketSimulation(rocket)
        >>> result = sim.run()
        >>> result.apogee_m  # doctest: +SKIP
    """

    def __init__(
        self,
        rocket: Rocket,
        sim_config: SimulationConfig | None = None,
    ) -> None:
        self.rocket = rocket
        self.config = sim_config or SimulationConfig()
        # Resolve body once; default to Earth.
        self.body = rocket.body if rocket.body is not None else Physics.EARTH

    def run(self) -> SimulationResult:
        """Run the simulation to completion and return a populated result."""
        cfg = self.config
        rocket = self.rocket
        body = self.body
        atmosphere = body.atmosphere
        dt = cfg.dt

        result = SimulationResult(rocket_name=rocket.name)

        # State variables.
        t = 0.0
        altitude = cfg.launch_altitude_m
        velocity = 0.0
        ground_altitude = cfg.launch_altitude_m
        phase = FlightPhase.BOOST
        recovery_deploy_t: float | None = None

        ejection_t = rocket.motor.ejection_time()
        deploy_at_apogee = cfg.deploy_mode == "apogee"

        # Body Cd·A (used during BOOST and COAST phases).
        body_cd_area = rocket.drag_coefficient * rocket.cross_sectional_area
        # Recovery Cd·A (used during DESCENT).
        recovery_cd, recovery_area = _recovery_drag_term(rocket)
        recovery_cd_area = recovery_cd * recovery_area

        # Track the apogee for both result reporting and deploy timing.
        apogee_alt = altitude
        apogee_t = 0.0

        # Initial state record.
        mass0 = rocket.mass_at(0.0)
        gravity0 = Physics.gravity_at_altitude(altitude - ground_altitude, body)
        result.states.append(
            SimulationState(
                time=0.0,
                altitude=altitude,
                velocity=0.0,
                acceleration=rocket.motor.thrust_at(0.0) / mass0 - gravity0,
                mass=mass0,
                thrust=rocket.motor.thrust_at(0.0),
                drag=0.0,
                phase=phase,
            )
        )

        prev_velocity = 0.0
        burnout_recorded = False

        while t < cfg.max_time:
            # Compute forces at current state.
            mass = rocket.mass_at(t)
            thrust = rocket.motor.thrust_at(t) if phase == FlightPhase.BOOST else 0.0

            altitude_above_surface = altitude - ground_altitude
            gravity = Physics.gravity_at_altitude(altitude_above_surface, body)

            # Drag opposes velocity. We treat the quadratic drag term
            # semi-implicitly so the integrator stays stable when a
            # parachute deploys at high speed (otherwise explicit Euler
            # would let drag flip the sign of velocity in one step).
            air_density = atmosphere.density_at(altitude_above_surface) if atmosphere else 0.0
            cd_area = recovery_cd_area if phase == FlightPhase.DESCENT else body_cd_area
            drag_coeff = 0.5 * air_density * cd_area  # multiplies |v|·v
            # Drag force used only for reporting (computed from pre-step velocity).
            drag = -drag_coeff * velocity * abs(velocity)

            other_force = thrust - mass * gravity
            # Semi-implicit update: v_{n+1} = (v_n + dt·a_other) / (1 + dt·drag_coeff·|v_n|/m)
            damping = 1.0 + dt * drag_coeff * abs(velocity) / mass
            prev_velocity = velocity
            velocity = (velocity + dt * other_force / mass) / damping
            altitude += velocity * dt
            t += dt
            acceleration = (velocity - prev_velocity) / dt if dt > 0 else 0.0

            # Ground constraint. The rocket cannot pass through the ground.
            landed_this_step = False
            if altitude < ground_altitude:
                altitude = ground_altitude
                if phase == FlightPhase.BOOST and prev_velocity <= 0 and velocity <= 0:
                    # Still on the pad — thrust has not yet overcome weight.
                    # Hold the rocket stationary; the launch tower would do
                    # this in real life.
                    velocity = 0.0
                else:
                    # In flight and now hitting the ground.
                    landed_this_step = True

            # Phase transitions.
            if phase == FlightPhase.BOOST and t >= rocket.motor.burn_time:
                phase = FlightPhase.COAST
                if not burnout_recorded:
                    result.burnout_altitude_m = altitude
                    result.burnout_velocity_ms = velocity
                    result.burnout_time_s = t
                    burnout_recorded = True

            # Track apogee (max altitude reached).
            if altitude > apogee_alt:
                apogee_alt = altitude
                apogee_t = t

            # Recovery deployment.
            if phase != FlightPhase.DESCENT and recovery_deploy_t is None:
                deploy_now = False
                if deploy_at_apogee:
                    # Detect velocity sign change: positive → non-positive at this step.
                    if prev_velocity > 0 >= velocity:
                        deploy_now = True
                else:
                    if t >= ejection_t:
                        deploy_now = True

                if deploy_now:
                    phase = FlightPhase.DESCENT
                    recovery_deploy_t = t
                    if altitude <= ground_altitude:
                        result.deployed_below_ground = True

            if landed_this_step:
                if phase != FlightPhase.LANDED:
                    result.flight_time_s = t
                    result.landing_velocity_ms = abs(velocity)
                # Lawn dart: ground impact before recovery deployed.
                if recovery_deploy_t is None and rocket.recovery is not None:
                    result.deployed_below_ground = True
                phase = FlightPhase.LANDED
                result.states.append(
                    SimulationState(
                        time=t,
                        altitude=altitude,
                        velocity=0.0,
                        acceleration=0.0,
                        mass=mass,
                        thrust=0.0,
                        drag=0.0,
                        phase=phase,
                    )
                )
                break

            # Track maxima.
            speed = abs(velocity)
            if speed > result.max_velocity_ms:
                result.max_velocity_ms = speed
            abs_accel = abs(acceleration)
            if abs_accel > result.max_acceleration_ms2:
                result.max_acceleration_ms2 = abs_accel

            result.states.append(
                SimulationState(
                    time=t,
                    altitude=altitude,
                    velocity=velocity,
                    acceleration=acceleration,
                    mass=mass,
                    thrust=thrust,
                    drag=drag,
                    phase=phase,
                )
            )
        else:
            # Simulation hit max_time without landing.
            logger.warning(
                "Simulation reached max_time=%s without landing for %r",
                cfg.max_time,
                rocket.name,
            )
            result.flight_time_s = t

        result.apogee_m = apogee_alt - ground_altitude  # report apogee above launch site
        result.apogee_time_s = apogee_t
        result.recovery_deployment_time_s = recovery_deploy_t
        if not burnout_recorded:
            # Motor burned out before the integrator stepped past it; reconstruct.
            result.burnout_time_s = rocket.motor.burn_time
            result.burnout_altitude_m = (
                result.states[-1].altitude if result.states else cfg.launch_altitude_m
            )
            result.burnout_velocity_ms = result.states[-1].velocity if result.states else 0.0

        return result

    def run_generator(self) -> Iterator[SimulationState]:
        """
        Run the simulation as a generator yielding states, for live plotting.

        Convenience: this just runs `run()` and yields its `states`.
        """
        result = self.run()
        yield from result.states


def simulate_rocket(
    rocket: Rocket,
    sim_config: SimulationConfig | None = None,
) -> SimulationResult:
    """Convenience: run a single rocket simulation."""
    return RocketSimulation(rocket, sim_config).run()


def simulate_multiple(
    rockets: list[Rocket],
    sim_config: SimulationConfig | None = None,
) -> list[SimulationResult]:
    """Convenience: run several simulations sequentially."""
    return [simulate_rocket(rocket, sim_config) for rocket in rockets]
