#!/usr/bin/env python3
"""
Compare Multiple Rockets Example

This example demonstrates how to simulate and compare multiple
rockets on the same plot.
"""

from rocket_sim import PlotOptions, PlotStyle, Plotter, get_preset, simulate_multiple


def main() -> None:
    # Select a few rockets to compare
    rocket_names = ["Falcon 9", "Saturn V", "SpaceX Starship", "Electron"]

    print("Comparing rockets:")
    for name in rocket_names:
        config = get_preset(name)
        print(f"  - {name} (T/W: {config.thrust_to_weight_ratio:.2f})")
    print()

    # Get configurations
    configs = [get_preset(name) for name in rocket_names]

    # Run simulations
    print("Running simulations...")
    results = simulate_multiple(configs)

    # Print comparison
    print("\nResults:")
    print("-" * 60)
    print(f"{'Rocket':<20} {'Max Alt (km)':>15} {'Flight Time (s)':>15}")
    print("-" * 60)
    for result in results:
        print(
            f"{result.rocket_name:<20} {result.max_altitude_km:>15,.2f} {result.flight_time:>15,.2f}"
        )
    print()

    # Create comparison plot with custom styling
    options = PlotOptions(
        style=PlotStyle.SEABORN,
        figsize=(14, 8),
        dpi=150,
    )
    plotter = Plotter(options)
    plotter.plot_multiple_trajectories(
        results,
        filename="rocket_comparison.png",
        title="Rocket Trajectory Comparison",
        show=True,
    )


if __name__ == "__main__":
    main()
