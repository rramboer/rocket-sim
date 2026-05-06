#!/usr/bin/env python3
"""
Compare every built-in rocket kit on Earth, plotted on the same axes.
"""

from rocket_sim import Plotter, get_kit, list_kits, simulate_multiple


def main() -> None:
    rockets = [get_kit(name) for name in list_kits()]
    print(f"Simulating {len(rockets)} kits on Earth:")
    for r in rockets:
        print(f"  - {r.name} ({r.motor.designation})")
    print()

    results = simulate_multiple(rockets)
    for result in results:
        print(f"  {result.rocket_name:25s} apogee = {result.apogee_m:7.1f} m")
    print()

    Plotter().plot_multiple_trajectories(
        results,
        filename="compare_rockets.png",
        title="Estes kit apogee comparison (Earth)",
        show=True,
    )


if __name__ == "__main__":
    main()
