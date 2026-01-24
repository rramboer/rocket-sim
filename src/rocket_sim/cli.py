"""
Command-line interface for the rocket simulator.

This module provides a rich CLI experience for running rocket simulations
with various options and output formats.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import NoReturn

from rocket_sim import __version__
from rocket_sim.config import SimulationConfig
from rocket_sim.models import RocketConfig
from rocket_sim.presets import get_preset, list_presets
from rocket_sim.simulation import simulate_multiple
from rocket_sim.visualization import PlotOptions, PlotStyle, Plotter


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="rocket-sim",
        description="Simulate rocket trajectories with realistic physics.",
        epilog="Example: rocket-sim --preset 'Falcon 9' -o trajectory.png",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Simulation source
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "-p",
        "--preset",
        type=str,
        metavar="NAME",
        help="Use a preset rocket configuration",
    )
    source_group.add_argument(
        "--all-presets",
        action="store_true",
        help="Simulate all available rocket presets",
    )
    source_group.add_argument(
        "--list-presets",
        action="store_true",
        help="List all available rocket presets and exit",
    )
    source_group.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )

    # Custom rocket parameters
    custom_group = parser.add_argument_group("custom rocket")
    custom_group.add_argument(
        "-m",
        "--mass",
        type=float,
        metavar="KG",
        help="Rocket mass in kilograms",
    )
    custom_group.add_argument(
        "-t",
        "--thrust",
        type=float,
        metavar="N",
        help="Engine thrust in Newtons",
    )
    custom_group.add_argument(
        "-b",
        "--burn-time",
        type=float,
        metavar="SEC",
        help="Engine burn time in seconds",
    )
    custom_group.add_argument(
        "-n",
        "--name",
        type=str,
        default="Custom Rocket",
        metavar="NAME",
        help="Name for the custom rocket",
    )

    # Simulation parameters
    sim_group = parser.add_argument_group("simulation options")
    sim_group.add_argument(
        "--dt",
        type=float,
        default=0.1,
        metavar="SEC",
        help="Time step for simulation (default: 0.1s)",
    )
    sim_group.add_argument(
        "--max-time",
        type=float,
        default=1_000_000,
        metavar="SEC",
        help="Maximum simulation time (default: 1000000s)",
    )

    # Output options
    output_group = parser.add_argument_group("output options")
    output_group.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="FILE",
        help="Save plot to file (e.g., trajectory.png)",
    )
    output_group.add_argument(
        "--no-plot",
        action="store_true",
        help="Don't display the plot",
    )
    output_group.add_argument(
        "--dashboard",
        action="store_true",
        help="Generate a full dashboard with multiple plots",
    )
    output_group.add_argument(
        "--style",
        type=str,
        choices=[s.value for s in PlotStyle],
        default="seaborn-v0_8-darkgrid",
        help="Plot style (default: seaborn-v0_8-darkgrid)",
    )
    output_group.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Output resolution in DPI (default: 150)",
    )

    # Verbosity
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for info, -vv for debug)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress all output except errors",
    )

    return parser


def setup_logging(verbose: int, quiet: bool) -> None:
    """Configure logging based on verbosity."""
    if quiet:
        level = logging.ERROR
    elif verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


def print_preset_list() -> None:
    """Print all available presets."""
    print("\nAvailable Rocket Presets")
    print("=" * 60)
    for name in list_presets():
        config = get_preset(name)
        twr = config.thrust_to_weight_ratio
        print(f"  {name:20} | Mass: {config.mass:>12,.0f} kg | T/W: {twr:.2f}")
    print()


def get_custom_rocket_interactive() -> RocketConfig:
    """Interactively get rocket configuration from user."""
    print("\nEnter custom rocket parameters:")

    while True:
        try:
            mass = float(input("  Mass (kg): "))
            thrust = float(input("  Thrust (N): "))
            burn_time = float(input("  Burn time (s): "))
            name = input("  Name (optional): ").strip() or "Custom Rocket"

            return RocketConfig(
                mass=mass,
                thrust=thrust,
                burn_time=burn_time,
                name=name,
            )
        except ValueError as e:
            print(f"Invalid input: {e}")
            print("Please try again.\n")


def run_interactive_mode() -> list[RocketConfig]:
    """Run interactive mode to select rockets."""
    print("\n" + "=" * 60)
    print("  ROCKET SIMULATOR - Interactive Mode")
    print("=" * 60)

    print_preset_list()

    print("Options:")
    print("  [number] - Select a preset by number")
    print("  [name]   - Select a preset by name")
    print("  'custom' - Enter custom rocket parameters")
    print("  'all'    - Simulate all presets")
    print("  'done'   - Finish selection and run simulation")
    print()

    configs: list[RocketConfig] = []
    preset_names = list_presets()

    while True:
        choice = input("Select rocket (or 'done'): ").strip()

        if choice.lower() == "done":
            if not configs:
                print("No rockets selected. Please select at least one.")
                continue
            break

        if choice.lower() == "all":
            configs = [get_preset(name) for name in preset_names]
            print(f"Selected all {len(configs)} presets.")
            break

        if choice.lower() == "custom":
            config = get_custom_rocket_interactive()
            configs.append(config)
            print(f"Added: {config.name}")
            continue

        # Try as number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(preset_names):
                config = get_preset(preset_names[idx])
                configs.append(config)
                print(f"Added: {config.name}")
                continue
        except ValueError:
            pass

        # Try as name
        try:
            config = get_preset(choice)
            configs.append(config)
            print(f"Added: {config.name}")
        except KeyError:
            print(f"Unknown preset: '{choice}'")

    return configs


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command-line arguments. Uses sys.argv if None.

    Returns:
        Exit code (0 for success).
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    setup_logging(args.verbose, args.quiet)

    # Handle --list-presets
    if args.list_presets:
        print_preset_list()
        return 0

    # Determine rocket configuration(s)
    configs: list[RocketConfig] = []

    if args.interactive:
        configs = run_interactive_mode()

    elif args.all_presets:
        configs = [get_preset(name) for name in list_presets()]
        if not args.quiet:
            print(f"Simulating {len(configs)} rocket presets...")

    elif args.preset:
        try:
            configs = [get_preset(args.preset)]
        except KeyError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    elif args.mass and args.thrust and args.burn_time:
        # Custom rocket from command line
        try:
            configs = [
                RocketConfig(
                    mass=args.mass,
                    thrust=args.thrust,
                    burn_time=args.burn_time,
                    name=args.name,
                )
            ]
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    else:
        # Default: run interactive mode
        configs = run_interactive_mode()

    if not configs:
        print("No rockets to simulate.", file=sys.stderr)
        return 1

    # Create simulation config
    sim_config = SimulationConfig(
        dt=args.dt,
        max_time=args.max_time,
        log_level=logging.DEBUG if args.verbose >= 2 else logging.WARNING,
    )

    # Run simulations
    if not args.quiet:
        print("\nRunning simulations...")

    results = simulate_multiple(configs, sim_config)

    # Print results
    if not args.quiet:
        print("\n" + "=" * 60)
        print("  SIMULATION RESULTS")
        print("=" * 60)
        for result in results:
            print(f"\n{result.summary()}")
        print()

    # Create plot
    if not args.no_plot or args.output:
        plot_style = PlotStyle(args.style) if args.style else PlotStyle.SEABORN
        options = PlotOptions(style=plot_style, dpi=args.dpi)
        plotter = Plotter(options)

        if args.dashboard and len(results) == 1:
            plotter.plot_dashboard(
                results[0],
                filename=args.output,
                show=not args.no_plot,
            )
        else:
            plotter.plot_multiple_trajectories(
                results,
                filename=args.output,
                show=not args.no_plot,
            )

    return 0


def cli_main() -> NoReturn:
    """Entry point that handles exit codes."""
    sys.exit(main())


if __name__ == "__main__":
    cli_main()
