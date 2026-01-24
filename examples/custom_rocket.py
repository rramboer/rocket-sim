#!/usr/bin/env python3
"""
Custom Rocket Example

This example demonstrates how to create and simulate a custom
rocket with user-defined parameters.
"""

from rocket_sim import Plotter, RocketConfig, RocketSimulation, SimulationConfig


def main() -> None:
    # Define a custom rocket
    config = RocketConfig(
        mass=50_000,  # 50 tons
        thrust=1_200_000,  # 1.2 MN
        burn_time=120,  # 2 minute burn
        name="My Custom Rocket",
    )

    print(f"Custom Rocket: {config.name}")
    print(f"  Mass: {config.mass:,} kg")
    print(f"  Thrust: {config.thrust:,} N")
    print(f"  Burn Time: {config.burn_time} s")
    print(f"  T/W Ratio: {config.thrust_to_weight_ratio:.2f}")

    # Check if rocket can lift off
    if config.thrust_to_weight_ratio < 1.0:
        print("\n  WARNING: Thrust-to-weight ratio < 1.0")
        print("  Rocket will not be able to lift off!")
    print()

    # Create simulation with custom parameters
    sim_config = SimulationConfig(
        dt=0.05,  # Finer time step for more accuracy
        max_time=600,  # 10 minute max simulation
    )

    sim = RocketSimulation(config, sim_config)
    result = sim.run()

    # Print detailed results
    print("Simulation Results:")
    print(f"  Max Altitude: {result.max_altitude_km:,.2f} km")
    print(f"  Max Velocity: {result.max_velocity:,.2f} m/s ({result.max_velocity * 3.6:.2f} km/h)")
    print(f"  Flight Time: {result.flight_time:,.2f} s ({result.flight_time / 60:.2f} min)")
    print(f"  Status: {'Escaped' if result.escaped else 'Landed'}")
    print()

    # Create a dashboard view
    plotter = Plotter()
    plotter.plot_dashboard(result, filename="custom_rocket_dashboard.png", show=True)


if __name__ == "__main__":
    main()
