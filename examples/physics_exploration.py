#!/usr/bin/env python3
"""
Launch the same rocket from every supported celestial body and
plot the resulting trajectories on the same axes.

Demonstrates how atmospheric density and surface gravity dominate
the apogee outcome — the Moon (vacuum, 1/6 g) sends the rocket much
higher than Earth, while Venus (thick atmosphere) cuts it short.
"""

from dataclasses import replace

from rocket_sim import (
    Physics,
    Plotter,
    SimulationConfig,
    get_kit,
    simulate_multiple,
)


def main() -> None:
    base = get_kit("alpha-iii")
    bodies = [Physics.EARTH, Physics.MOON, Physics.MARS, Physics.VENUS, Physics.TITAN]

    rockets = [replace(base, name=f"Alpha III on {b.name}", body=b) for b in bodies]
    cfg = SimulationConfig(dt=0.05, max_time=1200.0)
    results = simulate_multiple(rockets, cfg)

    print(f"{'Body':10s}  {'Apogee (m)':>14s}  {'Max v (m/s)':>14s}  {'Flight time (s)':>16s}")
    print("-" * 60)
    for result in results:
        body_name = result.rocket_name.split(" on ")[1]
        print(
            f"{body_name:10s}  {result.apogee_m:14.1f}  "
            f"{result.max_velocity_ms:14.1f}  {result.flight_time_s:16.1f}"
        )

    Plotter().plot_multiple_trajectories(
        results,
        title="Same rocket, five worlds",
        filename="physics_exploration.png",
        show=True,
    )


if __name__ == "__main__":
    main()
