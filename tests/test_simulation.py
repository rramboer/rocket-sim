"""Tests for the trajectory simulation engine."""

from __future__ import annotations

import math

import pytest

from rocket_sim.config import SimulationConfig
from rocket_sim.models import Parachute, Rocket
from rocket_sim.motors import Motor
from rocket_sim.physics import CelestialBody, Physics
from rocket_sim.simulation import (
    FlightPhase,
    RocketSimulation,
    simulate_multiple,
    simulate_rocket,
)


class TestBasicFlight:
    def test_alpha_iii_lifts_off_and_lands(self, alpha_iii: Rocket) -> None:
        result = simulate_rocket(alpha_iii)
        assert result.apogee_m > 50  # at least gets off the ground
        assert result.flight_time_s > 0
        assert result.recovery_deployment_time_s is not None

    def test_apogee_within_published_ballpark(self, alpha_iii: Rocket) -> None:
        result = simulate_rocket(alpha_iii)
        # Estes-published apogee for Alpha III + C6-5 is ~200 m;
        # our simplified thrust curves make it run higher. Loose bound.
        assert 150 < result.apogee_m < 600

    def test_burnout_recorded(self, alpha_iii: Rocket) -> None:
        result = simulate_rocket(alpha_iii)
        assert math.isclose(result.burnout_time_s, alpha_iii.motor.burn_time, abs_tol=0.1)
        assert result.burnout_velocity_ms > 0


class TestPhases:
    def test_phases_progress(self, alpha_iii: Rocket) -> None:
        result = simulate_rocket(alpha_iii)
        phase_set = {s.phase for s in result.states}
        # All four phases should appear in a normal flight.
        assert FlightPhase.BOOST in phase_set
        assert FlightPhase.COAST in phase_set
        assert FlightPhase.DESCENT in phase_set
        assert FlightPhase.LANDED in phase_set

    def test_boost_only_during_burn(self, alpha_iii: Rocket) -> None:
        result = simulate_rocket(alpha_iii)
        for s in result.states:
            if s.phase == FlightPhase.BOOST:
                assert s.time <= alpha_iii.motor.burn_time + 0.1


class TestMultiBody:
    def test_moon_apogee_higher_than_earth(self, alpha_iii: Rocket) -> None:
        from dataclasses import replace

        earth_result = simulate_rocket(alpha_iii)
        moon_rocket = replace(alpha_iii, body=Physics.MOON)
        moon_result = simulate_rocket(moon_rocket, SimulationConfig(dt=0.05, max_time=600))
        # Moon: no atmosphere + lower gravity → much higher apogee.
        assert moon_result.apogee_m > earth_result.apogee_m * 5

    def test_mars_apogee_between_earth_and_moon(self, alpha_iii: Rocket) -> None:
        from dataclasses import replace

        earth_result = simulate_rocket(alpha_iii)
        moon_rocket = replace(alpha_iii, body=Physics.MOON)
        moon_result = simulate_rocket(moon_rocket, SimulationConfig(dt=0.05, max_time=600))
        mars_rocket = replace(alpha_iii, body=Physics.MARS)
        mars_result = simulate_rocket(mars_rocket, SimulationConfig(dt=0.05, max_time=600))
        assert earth_result.apogee_m < mars_result.apogee_m < moon_result.apogee_m


class TestVacuumAnalytic:
    def test_vacuum_constant_thrust_matches_kinematics(
        self, constant_thrust_motor: Motor, vacuum_body: CelestialBody
    ) -> None:
        """In vacuum with constant thrust, burnout velocity should match (T/m̄ - g)·t_burn."""
        rocket = Rocket(
            name="VacuumTest",
            dry_mass_kg=0.030,
            motor=constant_thrust_motor,
            diameter_m=0.025,
            drag_coefficient=0.5,  # No effect in vacuum.
            recovery=Parachute(diameter_m=0.3),
            body=vacuum_body,
        )
        result = simulate_rocket(rocket, SimulationConfig(dt=0.001, max_time=200))

        # Average mass over burn:
        m0 = rocket.dry_mass_kg + constant_thrust_motor.total_mass_kg
        m_end = rocket.dry_mass_kg + (
            constant_thrust_motor.total_mass_kg - constant_thrust_motor.propellant_mass_kg
        )
        m_avg = 0.5 * (m0 + m_end)
        avg_thrust = constant_thrust_motor.average_thrust
        g = vacuum_body.surface_gravity
        # Crude analytic estimate for burnout velocity: (T/m̄ - g)·t.
        expected_v = (avg_thrust / m_avg - g) * constant_thrust_motor.burn_time
        # Allow 10% tolerance for the mass-flow approximation.
        assert math.isclose(result.burnout_velocity_ms, expected_v, rel_tol=0.10)


class TestRecoveryDeployment:
    def test_motor_delay_fires_at_ejection_time(self, alpha_iii: Rocket) -> None:
        result = simulate_rocket(alpha_iii)
        ejection = alpha_iii.motor.ejection_time()
        assert result.recovery_deployment_time_s is not None
        # Must fire within one timestep of the ejection time.
        assert math.isclose(result.recovery_deployment_time_s, ejection, abs_tol=0.1)

    def test_apogee_mode_fires_at_apogee(self, alpha_iii: Rocket) -> None:
        from dataclasses import replace

        # With deploy_mode='apogee', the chute fires near apogee_time.
        result = simulate_rocket(
            alpha_iii,
            SimulationConfig(deploy_mode="apogee", dt=0.05),
        )
        assert result.recovery_deployment_time_s is not None
        assert math.isclose(result.recovery_deployment_time_s, result.apogee_time_s, abs_tol=0.2)
        _ = replace  # keep imported for future tests

    def test_lawn_dart_with_long_delay(self) -> None:
        """A small light rocket with an absurdly long delay grain hits the
        ground before recovery deploys (the "lawn dart" failure mode)."""
        # Build a small light rocket and a motor with a 30-second delay grain.
        long_delay_motor = Motor(
            designation="LONG-30",
            name="LongDelay",
            diameter_m=0.018,
            length_m=0.07,
            propellant_mass_kg=0.005,
            total_mass_kg=0.010,
            thrust_curve=((0, 0), (1, 5), (1, 0)),
            delay_seconds=30.0,  # Way too long.
        )
        rocket = Rocket(
            name="ShortLight",
            dry_mass_kg=0.010,
            motor=long_delay_motor,
            diameter_m=0.018,
            drag_coefficient=0.75,
            recovery=Parachute(diameter_m=0.3),
        )
        result = simulate_rocket(rocket, SimulationConfig(dt=0.05, max_time=120))
        # Rocket lands before the 30 s delay grain fires:
        assert result.flight_time_s < long_delay_motor.ejection_time()
        # Recovery may deploy at or after the ground impact ("deployed below ground").
        assert result.deployed_below_ground or result.recovery_deployment_time_s is None


class TestSimulateMultiple:
    def test_returns_one_result_per_rocket(self, alpha_iii: Rocket) -> None:
        from dataclasses import replace

        rocket2 = replace(alpha_iii, body=Physics.MOON)
        results = simulate_multiple([alpha_iii, rocket2])
        assert len(results) == 2


class TestTimeSeries:
    def test_states_are_chronological(self, alpha_iii: Rocket) -> None:
        result = simulate_rocket(alpha_iii)
        times = [s.time for s in result.states]
        assert times == sorted(times)

    def test_altitude_data_starts_at_zero(self, alpha_iii: Rocket) -> None:
        result = simulate_rocket(alpha_iii)
        assert result.altitude_data[0] == 0.0


class TestRocketSimulationClass:
    def test_can_construct(self, alpha_iii: Rocket) -> None:
        sim = RocketSimulation(alpha_iii)
        result = sim.run()
        assert result.apogee_m > 0

    def test_run_generator_yields_states(self, alpha_iii: Rocket) -> None:
        sim = RocketSimulation(alpha_iii)
        states = list(sim.run_generator())
        assert len(states) > 1
        assert states[0].time == 0


def test_invalid_deploy_mode_raises() -> None:
    with pytest.raises(ValueError):
        SimulationConfig(deploy_mode="oops")  # type: ignore[arg-type]


def test_negative_dt_raises() -> None:
    with pytest.raises(ValueError):
        SimulationConfig(dt=-1)


def test_negative_max_time_raises() -> None:
    with pytest.raises(ValueError):
        SimulationConfig(max_time=-1)


def test_negative_launch_altitude_raises() -> None:
    with pytest.raises(ValueError):
        SimulationConfig(launch_altitude_m=-1)
