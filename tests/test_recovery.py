"""Tests for recovery-system descent behavior."""

from __future__ import annotations

import math

from rocket_sim.config import SimulationConfig
from rocket_sim.models import Parachute, Rocket, Streamer
from rocket_sim.motors import Motor
from rocket_sim.physics import Physics
from rocket_sim.simulation import simulate_rocket


def _terminal_velocity(mass: float, density: float, cd: float, area: float, g: float) -> float:
    """Analytic terminal velocity: m·g = ½·ρ·v²·Cd·A."""
    return math.sqrt(2 * mass * g / (density * cd * area))


class TestParachuteDescent:
    def test_lands_at_low_velocity(self, alpha_iii: Rocket) -> None:
        result = simulate_rocket(alpha_iii)
        # Alpha III with 12-inch chute should land below 5 m/s.
        assert result.landing_velocity_ms < 5.0

    def test_terminal_velocity_within_bounds(self, alpha_iii: Rocket) -> None:
        """Landing velocity should be in the ballpark of the analytic terminal velocity."""
        result = simulate_rocket(alpha_iii)
        assert isinstance(alpha_iii.recovery, Parachute)
        # After motor burns, mass = dry + (motor_total - propellant)
        m = alpha_iii.dry_mass_kg + (
            alpha_iii.motor.total_mass_kg - alpha_iii.motor.propellant_mass_kg
        )
        # Compute analytic terminal velocity assuming descent through full Earth atmosphere.
        rho = 1.225
        v_term = _terminal_velocity(
            mass=m,
            density=rho,
            cd=alpha_iii.recovery.drag_coefficient,
            area=alpha_iii.recovery.cross_sectional_area,
            g=Physics.EARTH.surface_gravity,
        )
        # Sim landing speed should be in same order of magnitude.
        assert 0.4 * v_term < result.landing_velocity_ms < 1.6 * v_term


class TestNoRecoveryBallistic:
    def test_no_recovery_lands_fast(self, alpha_iii: Rocket) -> None:
        from dataclasses import replace

        # Build a copy of alpha_iii with no recovery system.
        ballistic = replace(alpha_iii, recovery=None)
        with_chute = simulate_rocket(alpha_iii)
        without_chute = simulate_rocket(ballistic)
        # No-chute landing speed should be much higher than with-chute.
        assert without_chute.landing_velocity_ms > with_chute.landing_velocity_ms * 3


class TestStreamerDescent:
    def test_streamer_lands_faster_than_parachute(self, constant_thrust_motor: Motor) -> None:
        from dataclasses import replace

        rocket_chute = Rocket(
            name="ChuteRocket",
            dry_mass_kg=0.030,
            motor=constant_thrust_motor,
            diameter_m=0.018,
            drag_coefficient=0.75,
            recovery=Parachute(diameter_m=0.30),
        )
        rocket_streamer = replace(
            rocket_chute,
            recovery=Streamer(length_m=0.30, width_m=0.025),
        )
        result_chute = simulate_rocket(rocket_chute, SimulationConfig(dt=0.05, max_time=300))
        result_streamer = simulate_rocket(rocket_streamer, SimulationConfig(dt=0.05, max_time=300))
        assert result_streamer.landing_velocity_ms > result_chute.landing_velocity_ms
