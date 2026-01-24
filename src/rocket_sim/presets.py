"""
Pre-configured rocket specifications.

This module contains realistic specifications for famous rockets,
making it easy to run simulations with real-world parameters.
"""

from __future__ import annotations

from rocket_sim.models import RocketConfig

# Pre-configured rocket specifications based on real-world data
PRESETS: dict[str, RocketConfig] = {
    "Saturn V": RocketConfig(
        name="Saturn V",
        mass=2_900_000,  # kg - total mass at liftoff
        thrust=33_800_000,  # N - first stage thrust
        burn_time=165,  # s - first stage burn time
    ),
    "Falcon 9": RocketConfig(
        name="Falcon 9",
        mass=549_054,  # kg
        thrust=7_607_000,  # N - sea level thrust
        burn_time=162,  # s
    ),
    "SpaceX Starship": RocketConfig(
        name="SpaceX Starship",
        mass=5_000_000,  # kg (estimated full stack)
        thrust=72_000_000,  # N (33 Raptor engines)
        burn_time=200,  # s (estimated)
    ),
    "Space Shuttle": RocketConfig(
        name="Space Shuttle",
        mass=2_030_000,  # kg
        thrust=30_600_000,  # N (SSMEs + SRBs)
        burn_time=510,  # s
    ),
    "Ariane 5": RocketConfig(
        name="Ariane 5",
        mass=777_000,  # kg
        thrust=11_600_000,  # N
        burn_time=540,  # s
    ),
    "Delta IV Heavy": RocketConfig(
        name="Delta IV Heavy",
        mass=733_000,  # kg
        thrust=17_840_000,  # N
        burn_time=360,  # s
    ),
    "Atlas V": RocketConfig(
        name="Atlas V",
        mass=584_000,  # kg
        thrust=10_500_000,  # N
        burn_time=270,  # s
    ),
    "Soyuz-2": RocketConfig(
        name="Soyuz-2",
        mass=308_000,  # kg
        thrust=4_150_000,  # N
        burn_time=290,  # s
    ),
    "Long March 5": RocketConfig(
        name="Long March 5",
        mass=867_000,  # kg
        thrust=10_600_000,  # N
        burn_time=480,  # s
    ),
    "Vega": RocketConfig(
        name="Vega",
        mass=137_000,  # kg
        thrust=2_310_000,  # N
        burn_time=110,  # s
    ),
    "Electron": RocketConfig(
        name="Electron",
        mass=12_550,  # kg
        thrust=240_000,  # N
        burn_time=150,  # s
    ),
    "New Shepard": RocketConfig(
        name="New Shepard",
        mass=75_000,  # kg (estimated)
        thrust=490_000,  # N (BE-3 engine)
        burn_time=110,  # s
    ),
    "Vulcan Centaur": RocketConfig(
        name="Vulcan Centaur",
        mass=546_700,  # kg
        thrust=11_340_000,  # N (with SRBs)
        burn_time=180,  # s
    ),
}


def get_preset(name: str) -> RocketConfig:
    """
    Get a rocket configuration by name.

    Args:
        name: Name of the rocket preset (case-insensitive).

    Returns:
        RocketConfig for the specified rocket.

    Raises:
        KeyError: If the preset name is not found.

    Examples:
        >>> config = get_preset("falcon 9")
        >>> config.thrust
        7607000
    """
    # Try exact match first
    if name in PRESETS:
        return PRESETS[name]

    # Try case-insensitive match
    name_lower = name.lower()
    for preset_name, config in PRESETS.items():
        if preset_name.lower() == name_lower:
            return config

    available = ", ".join(PRESETS.keys())
    raise KeyError(f"Unknown preset: '{name}'. Available: {available}")


def list_presets() -> list[str]:
    """
    Get a list of all available preset names.

    Returns:
        List of preset rocket names.
    """
    return list(PRESETS.keys())


def get_preset_info(name: str) -> str:
    """
    Get formatted information about a preset.

    Args:
        name: Name of the rocket preset.

    Returns:
        Formatted string with rocket specifications.
    """
    config = get_preset(name)
    twr = config.thrust_to_weight_ratio

    return (
        f"{config.name}\n"
        f"  Mass:              {config.mass:,.0f} kg\n"
        f"  Thrust:            {config.thrust:,.0f} N\n"
        f"  Burn Time:         {config.burn_time:.0f} s\n"
        f"  Thrust-to-Weight:  {twr:.2f}"
    )


def print_all_presets() -> None:
    """Print information about all available presets."""
    print("Available Rocket Presets")
    print("=" * 50)
    for name in PRESETS:
        print(get_preset_info(name))
        print("-" * 50)
