"""
Pre-launch design validation for hobby rockets.

The `validate_design` function runs a quick simulation of the supplied
rocket and returns a list of `DesignWarning` flags for common
hobby-rocketry problems: marginal thrust-to-weight, predicted apogee
too low, transonic flight without reinforced airframe, motor too big
for the body tube, mismatched delay grain causing a "lawn dart", etc.

This is heuristic — it does not check stability margin (CG/CP), wind
weathercocking, or anything 2-D. Treat the warnings as starting
points, not certifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from rocket_sim.config import SimulationConfig
from rocket_sim.physics import Physics
from rocket_sim.simulation import simulate_rocket

if TYPE_CHECKING:
    from rocket_sim.models import Rocket

Severity = Literal["info", "warning", "error"]

# Speed of sound at sea level on Earth, used as the transonic warning
# threshold. Real value varies with temperature and altitude; this is a
# rounded reference value.
SPEED_OF_SOUND_M_S: float = 343.0

# Recommended minimum thrust-to-weight ratio at peak thrust for stable
# launch-rod departure. Below this, the rocket may not stabilise on a
# standard ~1 m launch rod.
MIN_PEAK_TWR: float = 5.0

# Predicted apogees below this in meters get an "underpowered" warning.
MIN_APOGEE_M: float = 30.0


@dataclass(frozen=True)
class DesignWarning:
    """
    A single advisory or error flagged by `validate_design`.

    Attributes:
        severity: ``"info"``, ``"warning"``, or ``"error"``. Errors
            indicate the configuration won't fly (or won't fly safely);
            warnings indicate suboptimal but functional configurations.
        code: Short identifier (e.g. ``"low_twr"``, ``"transonic"``)
            useful for programmatic filtering.
        message: Human-readable description.
    """

    severity: Severity
    code: str
    message: str


def validate_design(
    rocket: Rocket,
    sim_config: SimulationConfig | None = None,
) -> list[DesignWarning]:
    """
    Run pre-launch sanity checks on a `Rocket` configuration.

    Runs one simulation under the provided config (or defaults) and
    examines both static design parameters and dynamic flight outcomes.

    Returns a list of `DesignWarning` instances, ordered roughly from
    most serious to least serious. An empty list means no flagged
    issues.

    Args:
        rocket: The rocket configuration to check.
        sim_config: Optional simulation config; defaults to
            `SimulationConfig()`.

    Returns:
        A list of warnings. May be empty.
    """
    warnings: list[DesignWarning] = []

    body = rocket.body if rocket.body is not None else Physics.EARTH

    # --- Static (no-sim) checks ---

    # Motor must physically fit in the body tube.
    if rocket.motor.diameter_m > rocket.diameter_m * 1.001:
        warnings.append(
            DesignWarning(
                severity="error",
                code="motor_too_big",
                message=(
                    f"Motor diameter ({rocket.motor.diameter_m * 1000:.1f} mm) exceeds "
                    f"airframe diameter ({rocket.diameter_m * 1000:.1f} mm); "
                    "motor will not fit in the body tube."
                ),
            )
        )

    # Thrust-to-weight ratio at peak thrust.
    weight_n = rocket.launch_mass_kg * body.surface_gravity
    peak_twr = rocket.motor.peak_thrust / weight_n if weight_n > 0 else 0.0
    if peak_twr < 1.0:
        warnings.append(
            DesignWarning(
                severity="error",
                code="will_not_lift",
                message=(
                    f"Peak thrust-to-weight ratio is only {peak_twr:.2f} on "
                    f"{body.name}; rocket cannot lift off."
                ),
            )
        )
    elif peak_twr < MIN_PEAK_TWR:
        warnings.append(
            DesignWarning(
                severity="warning",
                code="low_twr",
                message=(
                    f"Peak thrust-to-weight ratio is {peak_twr:.2f} (below the "
                    f"recommended minimum of {MIN_PEAK_TWR:.0f}). The rocket may not "
                    "stabilise during launch-rod departure; consider a more powerful motor."
                ),
            )
        )

    # --- Run a simulation, then check dynamic outcomes ---

    result = simulate_rocket(rocket, sim_config)

    if result.deployed_below_ground:
        warnings.append(
            DesignWarning(
                severity="error",
                code="lawn_dart",
                message=(
                    f"Rocket impacts the ground at t = {result.flight_time_s:.2f} s, "
                    f"before the recovery system deploys at t = "
                    f"{rocket.motor.ejection_time():.2f} s. Use a shorter motor "
                    "delay grain to avoid a 'lawn dart' landing."
                ),
            )
        )

    if result.apogee_m < MIN_APOGEE_M:
        warnings.append(
            DesignWarning(
                severity="warning",
                code="low_apogee",
                message=(
                    f"Predicted apogee is only {result.apogee_m:.1f} m on "
                    f"{body.name}. Consider a more powerful motor or a lighter airframe."
                ),
            )
        )

    if result.max_velocity_ms > SPEED_OF_SOUND_M_S:
        warnings.append(
            DesignWarning(
                severity="warning",
                code="transonic",
                message=(
                    f"Predicted maximum velocity is {result.max_velocity_ms:.0f} m/s, "
                    f"exceeding the speed of sound ({SPEED_OF_SOUND_M_S:.0f} m/s). "
                    "Transonic flight stresses the airframe; reinforce fins and joints, "
                    "or choose a less powerful motor."
                ),
            )
        )

    if rocket.recovery is None:
        warnings.append(
            DesignWarning(
                severity="warning",
                code="ballistic_descent",
                message=(
                    f"No recovery system. Rocket will impact the ground at "
                    f"{result.landing_velocity_ms:.1f} m/s — likely destroying "
                    "the airframe and potentially injuring bystanders."
                ),
            )
        )

    if result.recovery_deployment_time_s is not None and not result.deployed_below_ground:
        # Check delay-grain timing accuracy.
        delta = result.recovery_deployment_time_s - result.apogee_time_s
        # Tolerate ±1 s of mismatch silently; flag larger ones as info.
        if delta < -2.0:
            warnings.append(
                DesignWarning(
                    severity="info",
                    code="delay_too_short",
                    message=(
                        f"Recovery deploys {-delta:.1f} s before apogee while the rocket "
                        "is still ascending; parachute may shred. Consider a longer motor delay."
                    ),
                )
            )
        elif delta > 2.0:
            warnings.append(
                DesignWarning(
                    severity="info",
                    code="delay_too_long",
                    message=(
                        f"Recovery deploys {delta:.1f} s after apogee; "
                        "rocket descends quite a bit before the chute opens. "
                        "Consider a shorter motor delay."
                    ),
                )
            )

    return warnings


def format_warnings(warnings: list[DesignWarning]) -> str:
    """Format a list of warnings as a human-readable multi-line string."""
    if not warnings:
        return "No design warnings."
    lines = []
    icons = {"error": "✗", "warning": "⚠", "info": "i"}
    for w in warnings:
        icon = icons.get(w.severity, "•")
        lines.append(f"  {icon}  [{w.severity.upper():7s} {w.code}] {w.message}")
    return "Design warnings:\n" + "\n".join(lines)
