"""
Built-in rocket kit presets.

Each preset is a fully-configured `Rocket` based on real published
specifications for popular Estes hobby kits, paired with an Estes-
recommended motor (and matching delay grain) and a stock recovery system.

Specifications are drawn from public Estes catalogs and product pages
and are accurate enough for an educational predictive simulator. They
are not an engineering reference — buy and read the kit instructions
before actually flying.
"""

from __future__ import annotations

from dataclasses import replace

from rocket_sim.models import Parachute, Rocket, Streamer
from rocket_sim.motors import get_motor

# Kit presets are stored as factory dicts (parameters) and instantiated
# fresh on each `get_kit` call so that motors are reset per fetch and
# mutation can't leak between callers.

_KIT_SPECS: dict[str, dict[str, object]] = {
    "alpha-iii": {
        "name": "Estes Alpha III",
        "dry_mass_kg": 0.034,  # 34 g
        "motor": "C6-5",
        "diameter_m": 0.0247,  # BT-50 body tube ≈ 24.7 mm
        "drag_coefficient": 0.75,
        "recovery": Parachute(diameter_m=0.305, drag_coefficient=0.75),  # 12-inch chute
    },
    "big-bertha": {
        "name": "Estes Big Bertha",
        "dry_mass_kg": 0.077,  # 77 g
        "motor": "C6-5",
        "diameter_m": 0.0413,  # BT-60 ≈ 41.3 mm
        "drag_coefficient": 0.75,
        "recovery": Parachute(diameter_m=0.457, drag_coefficient=0.75),  # 18-inch chute
    },
    "mosquito": {
        "name": "Estes Mosquito",
        "dry_mass_kg": 0.0045,  # 4.5 g — extremely small
        "motor": "1/2A6-2",  # Not in the built-in motor presets — we'll fall back below.
        "diameter_m": 0.0132,  # BT-5 ≈ 13.2 mm
        "drag_coefficient": 0.75,
        "recovery": Streamer(length_m=0.30, width_m=0.025, drag_coefficient=0.5),
    },
    "v-2": {
        "name": "Estes V-2",
        "dry_mass_kg": 0.064,  # 64 g
        "motor": "C6-3",
        "diameter_m": 0.0413,  # BT-60
        "drag_coefficient": 0.85,  # Wide tail flare → higher Cd
        "recovery": Parachute(diameter_m=0.305, drag_coefficient=0.75),
    },
}

# The Mosquito's stock motor (1/2A6-2) isn't in our built-in motor
# presets, so substitute the smallest motor we ship (A8-3) and note
# that in the docstring. Users wanting the exact stock motor can load
# it from a .eng file.
_KIT_MOTOR_FALLBACKS: dict[str, str] = {
    "1/2A6-2": "A8-3",
}


def _resolve_motor(designation: str) -> object:
    """Return a fresh Motor for a designation, with fallback for unsupported codes."""
    fallback = _KIT_MOTOR_FALLBACKS.get(designation, designation)
    return get_motor(fallback)


def get_kit(name: str) -> Rocket:
    """
    Look up a built-in rocket-kit preset by name (case-insensitive).

    Returns a fresh `Rocket` instance each call so that mutations
    cannot leak between callers.

    Args:
        name: Kit identifier, e.g. ``"alpha-iii"``, ``"big-bertha"``.

    Raises:
        KeyError: if the kit name is not recognised.

    Examples:
        >>> rocket = get_kit("alpha-iii")
        >>> rocket.name
        'Estes Alpha III'
    """
    key = name.lower()
    if key not in _KIT_SPECS:
        available = ", ".join(_KIT_SPECS.keys())
        raise KeyError(f"Unknown kit: {name!r}. Available: {available}")
    spec = _KIT_SPECS[key]
    motor = _resolve_motor(spec["motor"])  # type: ignore[arg-type]
    recovery = spec["recovery"]
    if recovery is not None:
        # Recovery is frozen but cheap; still return a fresh copy via replace
        # in case future versions add mutable fields.
        recovery = replace(recovery)  # type: ignore[type-var]
    return Rocket(
        name=spec["name"],  # type: ignore[arg-type]
        dry_mass_kg=spec["dry_mass_kg"],  # type: ignore[arg-type]
        motor=motor,  # type: ignore[arg-type]
        diameter_m=spec["diameter_m"],  # type: ignore[arg-type]
        drag_coefficient=spec["drag_coefficient"],  # type: ignore[arg-type]
        recovery=recovery,  # type: ignore[arg-type]
        body=None,  # defaults to Earth in simulation
    )


def list_kits() -> list[str]:
    """Return a list of available kit identifiers."""
    return list(_KIT_SPECS.keys())


def get_kit_info(name: str) -> str:
    """Return a multi-line, human-readable summary of a kit preset."""
    rocket = get_kit(name)
    motor = rocket.motor
    recovery = rocket.recovery
    if isinstance(recovery, Parachute):
        recovery_desc = f"Parachute ({recovery.diameter_m * 100:.1f} cm dia)"
    elif isinstance(recovery, Streamer):
        recovery_desc = f"Streamer ({recovery.length_m * 100:.0f}×{recovery.width_m * 100:.1f} cm)"
    else:
        recovery_desc = "Ballistic (no recovery)"
    return (
        f"{rocket.name}\n"
        f"  Dry mass:        {rocket.dry_mass_kg * 1000:.1f} g\n"
        f"  Diameter:        {rocket.diameter_m * 1000:.1f} mm\n"
        f"  Body Cd:         {rocket.drag_coefficient}\n"
        f"  Motor:           {motor.designation} ({motor.total_impulse:.2f} N·s, "
        f"{motor.burn_time:.2f} s burn, {motor.delay_seconds:.0f} s delay)\n"
        f"  Recovery:        {recovery_desc}"
    )
