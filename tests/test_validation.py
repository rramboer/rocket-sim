"""Tests for the pre-launch design validator."""

from __future__ import annotations

from dataclasses import replace

from rocket_sim.config import SimulationConfig
from rocket_sim.models import Parachute, Rocket
from rocket_sim.motors import Motor, get_motor
from rocket_sim.physics import Physics
from rocket_sim.validation import (
    DesignWarning,
    format_warnings,
    validate_design,
)


def _codes(warnings: list[DesignWarning]) -> set[str]:
    return {w.code for w in warnings}


class TestStaticChecks:
    def test_motor_too_big_for_airframe(self) -> None:
        # 24 mm motor in 18 mm tube.
        d12 = get_motor("D12-5")  # 24 mm motor
        rocket = Rocket(
            name="TooSmallTube",
            dry_mass_kg=0.05,
            motor=d12,
            diameter_m=0.018,  # 18 mm — too small
            drag_coefficient=0.75,
            recovery=Parachute(diameter_m=0.3),
        )
        codes = _codes(validate_design(rocket))
        assert "motor_too_big" in codes

    def test_will_not_lift_with_overweight_rocket(self) -> None:
        # Massive rocket, tiny A motor → T/W < 1.
        a8 = get_motor("A8-3")
        rocket = Rocket(
            name="TooHeavy",
            dry_mass_kg=10.0,  # 10 kg airframe with a tiny A motor
            motor=a8,
            diameter_m=0.025,
            drag_coefficient=0.75,
            recovery=Parachute(diameter_m=0.3),
        )
        codes = _codes(validate_design(rocket))
        assert "will_not_lift" in codes

    def test_low_twr_warning(self) -> None:
        # Heavy rocket where peak TWR is in (1, MIN_PEAK_TWR=5).
        a8 = get_motor("A8-3")  # peak ~13 N
        # weight at 5x = 13/5 = 2.6 N → mass 0.265 kg gives TWR ≈ 5.
        # Use a heavier mass to trigger the warning.
        rocket = Rocket(
            name="Marginal",
            dry_mass_kg=0.5,  # 500 g — very heavy for an A motor
            motor=a8,
            diameter_m=0.025,
            drag_coefficient=0.75,
            recovery=Parachute(diameter_m=0.3),
        )
        warnings = validate_design(rocket)
        codes = _codes(warnings)
        # Either won't-lift or low-twr will fire depending on exact values.
        assert "low_twr" in codes or "will_not_lift" in codes

    def test_clean_alpha_iii_no_critical_warnings(self, alpha_iii: Rocket) -> None:
        warnings = validate_design(alpha_iii)
        codes = _codes(warnings)
        # The default kit + motor should not produce errors.
        assert "motor_too_big" not in codes
        assert "will_not_lift" not in codes
        assert "lawn_dart" not in codes


class TestDynamicChecks:
    def test_lawn_dart_flagged(self) -> None:
        # 1-second motor with a 30-second delay grain on a small rocket.
        long_delay = Motor(
            designation="LONG-30",
            name="LongDelay",
            diameter_m=0.018,
            length_m=0.07,
            propellant_mass_kg=0.005,
            total_mass_kg=0.010,
            thrust_curve=((0, 0), (0.5, 8), (1, 8), (1, 0)),
            delay_seconds=30.0,
        )
        rocket = Rocket(
            name="LawnDartCandidate",
            dry_mass_kg=0.010,
            motor=long_delay,
            diameter_m=0.018,
            drag_coefficient=0.75,
            recovery=Parachute(diameter_m=0.3),
        )
        codes = _codes(validate_design(rocket, SimulationConfig(dt=0.05, max_time=120)))
        assert "lawn_dart" in codes

    def test_low_apogee_flagged_for_underpowered(self) -> None:
        # Tiny motor on a relatively heavy airframe → marginal apogee.
        rocket = Rocket(
            name="Underpowered",
            dry_mass_kg=0.060,  # 60 g, relatively heavy for a 1/2A motor
            motor=get_motor("1/2A6-2"),
            diameter_m=0.018,
            drag_coefficient=0.9,  # high Cd
            recovery=Parachute(diameter_m=0.3),
        )
        codes = _codes(validate_design(rocket))
        # Either underpowered (low apogee) or low TWR will fire here.
        assert codes & {"low_apogee", "low_twr"}

    def test_ballistic_descent_warned(self, alpha_iii: Rocket) -> None:
        ballistic = replace(alpha_iii, recovery=None)
        codes = _codes(validate_design(ballistic))
        assert "ballistic_descent" in codes

    def test_no_atmosphere_doesnt_break_validation(self, alpha_iii: Rocket) -> None:
        moon_rocket = replace(alpha_iii, body=Physics.MOON)
        # The validator must run without crashing on a vacuum body, even
        # though the simulation behaves very differently there.
        warnings = validate_design(moon_rocket, SimulationConfig(dt=0.05, max_time=1200))
        # Whatever fires, it should not include 'motor_too_big' or
        # 'will_not_lift' (Alpha III + C6-5 fits and lifts off on the Moon).
        codes = _codes(warnings)
        assert "motor_too_big" not in codes
        assert "will_not_lift" not in codes

    def test_transonic_warning_for_powerful_motor(self) -> None:
        # Very light rocket on the Moon (no drag) with the F15 motor:
        # easily breaks Mach 1.
        rocket = Rocket(
            name="MoonScreamer",
            dry_mass_kg=0.030,
            motor=get_motor("F15-6"),
            diameter_m=0.029,
            drag_coefficient=0.5,
            recovery=Parachute(diameter_m=0.3),
            body=Physics.MOON,
        )
        codes = _codes(validate_design(rocket, SimulationConfig(dt=0.02, max_time=600)))
        assert "transonic" in codes


class TestFormatWarnings:
    def test_empty_list_message(self) -> None:
        assert format_warnings([]) == "No design warnings."

    def test_renders_severities(self) -> None:
        ws = [
            DesignWarning(severity="error", code="x", message="m1"),
            DesignWarning(severity="warning", code="y", message="m2"),
            DesignWarning(severity="info", code="z", message="m3"),
        ]
        text = format_warnings(ws)
        assert "ERROR" in text
        assert "WARNING" in text
        assert "INFO" in text
        assert "m1" in text and "m2" in text and "m3" in text
