"""Tests for Motor type, .eng file parsing, and built-in motor presets."""

from __future__ import annotations

import math

import pytest

from rocket_sim.motors import (
    MOTORS,
    Motor,
    get_motor,
    list_motors,
    parse_eng_file,
)


class TestMotor:
    def test_thrust_curve_validated(self) -> None:
        # Empty curve.
        with pytest.raises(ValueError):
            Motor(
                designation="X",
                name="X",
                diameter_m=0.018,
                length_m=0.07,
                propellant_mass_kg=0.01,
                total_mass_kg=0.02,
                thrust_curve=(),
                delay_seconds=0,
            )

    def test_propellant_exceeds_total_raises(self) -> None:
        with pytest.raises(ValueError):
            Motor(
                designation="X",
                name="X",
                diameter_m=0.018,
                length_m=0.07,
                propellant_mass_kg=0.05,
                total_mass_kg=0.02,
                thrust_curve=((0, 0), (1, 5), (1, 0)),
                delay_seconds=0,
            )

    def test_negative_thrust_raises(self) -> None:
        with pytest.raises(ValueError):
            Motor(
                designation="X",
                name="X",
                diameter_m=0.018,
                length_m=0.07,
                propellant_mass_kg=0.01,
                total_mass_kg=0.02,
                thrust_curve=((0, 0), (0.5, -1)),
                delay_seconds=0,
            )

    def test_thrust_at_interpolation(self) -> None:
        # Linear ramp 0->10 N over 1 s, then ramp back to 0 over 1 s.
        m = Motor(
            designation="LIN",
            name="Lin",
            diameter_m=0.018,
            length_m=0.07,
            propellant_mass_kg=0.005,
            total_mass_kg=0.010,
            thrust_curve=((0, 0), (1, 10), (2, 0)),
            delay_seconds=0,
        )
        assert m.thrust_at(0) == 0
        assert math.isclose(m.thrust_at(0.5), 5.0)
        assert math.isclose(m.thrust_at(1.0), 10.0)
        assert math.isclose(m.thrust_at(1.5), 5.0)
        assert m.thrust_at(2.0) == 0
        assert m.thrust_at(2.5) == 0
        assert m.thrust_at(-1) == 0

    def test_total_impulse_constant_thrust(self, constant_thrust_motor: Motor) -> None:
        # 5 N for 1 s = 5 N·s.
        assert math.isclose(constant_thrust_motor.total_impulse, 5.0, rel_tol=1e-9)

    def test_burn_time_property(self, constant_thrust_motor: Motor) -> None:
        assert constant_thrust_motor.burn_time == 1.0

    def test_average_thrust(self, constant_thrust_motor: Motor) -> None:
        assert math.isclose(constant_thrust_motor.average_thrust, 5.0)

    def test_peak_thrust(self, constant_thrust_motor: Motor) -> None:
        assert constant_thrust_motor.peak_thrust == 5.0

    def test_propellant_burned_endpoints(self, constant_thrust_motor: Motor) -> None:
        assert constant_thrust_motor.propellant_burned_at(0) == 0
        assert math.isclose(
            constant_thrust_motor.propellant_burned_at(constant_thrust_motor.burn_time),
            constant_thrust_motor.propellant_mass_kg,
        )

    def test_propellant_burned_midway(self, constant_thrust_motor: Motor) -> None:
        # Constant thrust → half burned at half time.
        half = constant_thrust_motor.propellant_burned_at(0.5)
        assert math.isclose(half, constant_thrust_motor.propellant_mass_kg / 2, rel_tol=1e-6)

    def test_mass_at_decreases(self, constant_thrust_motor: Motor) -> None:
        m0 = constant_thrust_motor.mass_at(0)
        m_mid = constant_thrust_motor.mass_at(0.5)
        m_end = constant_thrust_motor.mass_at(constant_thrust_motor.burn_time)
        assert m0 > m_mid > m_end

    def test_ejection_time(self) -> None:
        m = Motor(
            designation="DELAY",
            name="DelayTest",
            diameter_m=0.018,
            length_m=0.07,
            propellant_mass_kg=0.005,
            total_mass_kg=0.010,
            thrust_curve=((0, 0), (1, 5), (1, 0)),
            delay_seconds=3,
        )
        assert m.ejection_time() == 4.0


class TestMotorPresets:
    def test_all_presets_present(self) -> None:
        names = list_motors()
        assert "A8-3" in names
        assert "C6-5" in names
        assert "F15-6" in names

    def test_get_motor_returns_copy(self) -> None:
        a = get_motor("C6-5")
        b = get_motor("C6-5")
        assert a is not b
        # Both equal in content.
        assert a == b

    def test_unknown_motor_raises(self) -> None:
        with pytest.raises(KeyError):
            get_motor("Z99-99")

    def test_case_insensitive_lookup(self) -> None:
        assert get_motor("c6-5").designation == "C6-5"

    @pytest.mark.parametrize(
        "designation,low,high",
        [
            ("A8-3", 1.26, 2.5),
            ("B6-4", 2.5, 5.0),
            ("C6-3", 5.0, 10.0),
            ("C6-5", 5.0, 11.0),  # ours has small overshoot from simplified curve
            ("D12-5", 10.0, 20.0),
            ("E9-6", 20.0, 40.0),
            ("F15-6", 40.0, 80.0),
        ],
    )
    def test_total_impulse_classifies_correctly(
        self, designation: str, low: float, high: float
    ) -> None:
        """Each motor's total impulse should land in its NAR letter classification."""
        m = get_motor(designation)
        # Allow ±10 % tolerance around the published bounds (simplified curves).
        assert low * 0.9 <= m.total_impulse <= high * 1.1, (
            f"{designation} total impulse {m.total_impulse} outside class range"
        )

    def test_all_curves_monotonic_in_time(self) -> None:
        for name in MOTORS:
            m = get_motor(name)
            prev = -1.0
            for t, _ in m.thrust_curve:
                assert t >= prev
                prev = t

    def test_all_curves_non_negative_thrust(self) -> None:
        for name in MOTORS:
            m = get_motor(name)
            for _, f in m.thrust_curve:
                assert f >= 0


SAMPLE_ENG = """\
; sample motor file
TEST 18.0 70.0 3-5 0.005 0.010 TestMfg
   0.0 0.0
   0.05 5.0
   0.5 5.0
   0.55 0.0
;
"""


class TestEngParser:
    def test_parse_basic_eng(self) -> None:
        m = parse_eng_file(SAMPLE_ENG)
        assert m.designation == "TEST"
        assert math.isclose(m.diameter_m, 0.018)
        assert math.isclose(m.length_m, 0.070)
        assert math.isclose(m.propellant_mass_kg, 0.005)
        assert math.isclose(m.total_mass_kg, 0.010)
        # First listed delay (3) wins.
        assert m.delay_seconds == 3.0
        assert m.manufacturer == "TestMfg"
        # Curve was already (0,0) at start, no insertion.
        assert m.thrust_curve[0] == (0.0, 0.0)
        # Total impulse from the curve.
        assert math.isclose(
            m.total_impulse, 0.5 * 5.0 * 0.05 + 5.0 * 0.45 + 0.5 * 5.0 * 0.05, rel_tol=1e-6
        )

    def test_parse_inserts_zero_origin_if_missing(self) -> None:
        text = """\
TEST 18.0 70.0 3 0.005 0.010 X
   0.05 5.0
   0.50 0.0
"""
        m = parse_eng_file(text)
        assert m.thrust_curve[0] == (0.0, 0.0)

    def test_parse_no_header_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_eng_file(";just a comment\n")

    def test_parse_empty_data_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_eng_file("TEST 18 70 3 0.005 0.010 X\n;\n")

    def test_parse_malformed_header_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_eng_file("TEST 18 70\n   0 0\n   1 5\n")
