#!/usr/bin/env python3
"""
Build a fully custom rocket (no kit preset) and run a dashboard plot.

Demonstrates how to assemble a `Rocket` from its component parts:
dry mass, motor, diameter, drag coefficient, recovery system.
"""

from rocket_sim import (
    Parachute,
    Plotter,
    Rocket,
    SimulationConfig,
    get_motor,
    simulate_rocket,
)


def main() -> None:
    rocket = Rocket(
        name="Custom Rocket",
        dry_mass_kg=0.060,  # 60 g airframe
        motor=get_motor("D12-5"),  # Bigger motor
        diameter_m=0.029,  # 29 mm body tube
        drag_coefficient=0.7,
        recovery=Parachute(diameter_m=0.45),
    )

    print(f"{rocket.name}: {rocket.launch_mass_kg * 1000:.1f} g loaded, motor {rocket.motor.designation}")

    result = simulate_rocket(rocket, SimulationConfig(dt=0.02))
    print(result.summary())

    Plotter().plot_dashboard(result, filename="custom_rocket_dashboard.png", show=True)


if __name__ == "__main__":
    main()
