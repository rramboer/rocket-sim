#!/usr/bin/env python3
"""
Basic example: launch an Estes Alpha III with a C6-5 motor on Earth.

Prints flight statistics and renders a single trajectory plot, with the
curve coloured by flight phase (boost / coast / descent).
"""

from rocket_sim import Plotter, get_kit, simulate_rocket


def main() -> None:
    rocket = get_kit("alpha-iii")
    print(f"Simulating: {rocket.name}")
    print(f"  Launch mass:  {rocket.launch_mass_kg * 1000:.1f} g")
    print(f"  Diameter:     {rocket.diameter_m * 1000:.1f} mm")
    print(f"  Motor:        {rocket.motor.designation} ({rocket.motor.total_impulse:.2f} N·s)")
    print()

    result = simulate_rocket(rocket)
    print(result.summary())

    Plotter().plot_trajectory(result, filename="basic_simulation.png", show=True)


if __name__ == "__main__":
    main()
