#!/usr/bin/env python3
"""
Basic Rocket Simulation Example

This example demonstrates how to run a simple rocket simulation
using a preset configuration.
"""

from rocket_sim import Plotter, RocketSimulation, get_preset


def main() -> None:
    # Get a preset rocket configuration
    config = get_preset("Falcon 9")
    print(f"Simulating: {config.name}")
    print(f"  Mass: {config.mass:,} kg")
    print(f"  Thrust: {config.thrust:,} N")
    print(f"  Burn Time: {config.burn_time} s")
    print(f"  T/W Ratio: {config.thrust_to_weight_ratio:.2f}")
    print()

    # Create and run simulation
    sim = RocketSimulation(config)
    result = sim.run()

    # Print results
    print("Results:")
    print(f"  Max Altitude: {result.max_altitude_km:,.2f} km")
    print(f"  Max Velocity: {result.max_velocity:,.2f} m/s")
    print(f"  Flight Time: {result.flight_time:,.2f} s")
    print(f"  Escaped: {result.escaped}")
    print()

    # Create plot
    plotter = Plotter()
    plotter.plot_trajectory(result, filename="basic_simulation.png", show=True)


if __name__ == "__main__":
    main()
