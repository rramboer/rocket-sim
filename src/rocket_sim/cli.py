"""
Command-line interface for `rocket-sim`.

Run a hobby-rocket flight simulation from the command line. The CLI
supports:

- Built-in kit presets (``--kit alpha-iii``).
- Built-in motor presets (``--motor c6-5``); overrides the kit's default
  motor when supplied with ``--kit``.
- User-supplied .eng motor files (``--motor-file motor.eng``).
- Fully custom rockets (``--dry-mass``, ``--diameter``, ``--cd``,
  ``--recovery``).
- Multi-body launches (``--body {earth,moon,mars,venus,titan}``).
- Recovery-deploy timing (``--deploy-mode {motor-delay,apogee}``).

Default invocation with no rocket flags drops into interactive mode.
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import replace
from pathlib import Path
from typing import NoReturn

from rocket_sim import __version__
from rocket_sim.config import SimulationConfig
from rocket_sim.models import Parachute, Rocket, Streamer
from rocket_sim.motors import Motor, get_motor, list_motors, load_motor_file
from rocket_sim.physics import CelestialBody, Physics
from rocket_sim.presets import get_kit, get_kit_info, list_kits
from rocket_sim.simulation import simulate_multiple
from rocket_sim.visualization import PlotOptions, PlotStyle, Plotter

BODIES: dict[str, CelestialBody] = {
    "earth": Physics.EARTH,
    "moon": Physics.MOON,
    "mars": Physics.MARS,
    "venus": Physics.VENUS,
    "titan": Physics.TITAN,
}


def create_parser() -> argparse.ArgumentParser:
    """Build the argparse parser."""
    parser = argparse.ArgumentParser(
        prog="rocket-sim",
        description="Simulate the flight of a hobby model rocket.",
        epilog="Example: rocket-sim --kit alpha-iii --motor c6-5 --body mars -o flight.png",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    # Mutually-exclusive top-level mode selectors.
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--list-motors", action="store_true", help="List built-in motor presets and exit"
    )
    mode.add_argument(
        "--list-kits", action="store_true", help="List built-in rocket-kit presets and exit"
    )
    mode.add_argument("--interactive", action="store_true", help="Run in interactive mode")

    # Rocket selection (kit or custom).
    rocket_group = parser.add_argument_group("rocket")
    rocket_group.add_argument(
        "--kit", type=str, metavar="NAME", help="Use a kit preset (e.g. alpha-iii)"
    )
    rocket_group.add_argument(
        "--dry-mass", type=float, metavar="KG", help="Custom rocket: empty mass (kg)"
    )
    rocket_group.add_argument(
        "--diameter", type=float, metavar="M", help="Custom rocket: airframe diameter (m)"
    )
    rocket_group.add_argument(
        "--cd",
        type=float,
        metavar="FLOAT",
        default=0.75,
        help="Custom rocket: drag coefficient (default 0.75)",
    )
    rocket_group.add_argument(
        "--recovery",
        type=str,
        metavar="SPEC",
        default="parachute:0.3",
        help="Recovery system: 'parachute:DIAM_M', 'streamer:LENGTH_MxWIDTH_M', or 'none'",
    )

    # Motor selection.
    motor_group = parser.add_argument_group("motor")
    motor_group.add_argument(
        "--motor",
        type=str,
        metavar="NAME",
        help="Motor designation (e.g. C6-5). Overrides the kit's default motor.",
    )
    motor_group.add_argument(
        "--motor-file",
        type=Path,
        metavar="PATH.eng",
        help="Path to a .eng motor file",
    )

    # Body and launch site.
    site_group = parser.add_argument_group("launch site")
    site_group.add_argument(
        "--body",
        type=str,
        choices=list(BODIES.keys()),
        default="earth",
        help="Celestial body to launch from (default: earth)",
    )
    site_group.add_argument(
        "--launch-altitude",
        type=float,
        metavar="M",
        default=0.0,
        help="Launch site elevation above the body's surface (default: 0)",
    )

    # Simulation parameters.
    sim_group = parser.add_argument_group("simulation")
    sim_group.add_argument(
        "--deploy-mode",
        type=str,
        choices=("motor-delay", "apogee"),
        default="motor-delay",
        help="Recovery deployment timing (default: motor-delay)",
    )
    sim_group.add_argument(
        "--dt", type=float, default=0.05, help="Integration timestep in seconds (default: 0.05)"
    )
    sim_group.add_argument(
        "--max-time",
        type=float,
        default=600.0,
        help="Max simulation time in seconds (default: 600)",
    )

    # Output.
    out_group = parser.add_argument_group("output")
    out_group.add_argument("-o", "--output", type=Path, metavar="FILE", help="Save plot to FILE")
    out_group.add_argument("--no-plot", action="store_true", help="Do not display the plot window")
    out_group.add_argument("--dashboard", action="store_true", help="Render multi-panel dashboard")
    out_group.add_argument(
        "--style",
        type=str,
        choices=[s.value for s in PlotStyle],
        default="seaborn-v0_8-darkgrid",
        help="Matplotlib style",
    )
    out_group.add_argument("--dpi", type=int, default=150, help="Plot DPI (default: 150)")

    # Verbosity.
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-error output")

    return parser


def setup_logging(verbose: int, quiet: bool) -> None:
    """Configure root logging based on -v / -q flags."""
    if quiet:
        level = logging.ERROR
    elif verbose >= 2:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def parse_recovery(spec: str) -> Parachute | Streamer | None:
    """Parse the ``--recovery`` flag into a Recovery instance."""
    spec = spec.strip().lower()
    if spec in ("none", ""):
        return None
    if spec.startswith("parachute:"):
        diam = float(spec.split(":", 1)[1])
        return Parachute(diameter_m=diam)
    if spec.startswith("streamer:"):
        rest = spec.split(":", 1)[1]
        l_str, w_str = rest.split("x")
        return Streamer(length_m=float(l_str), width_m=float(w_str))
    raise ValueError(
        f"Unknown recovery spec: {spec!r}. Use 'parachute:DIAM_M', 'streamer:LxW', or 'none'."
    )


def print_motor_list() -> None:
    """Print all built-in motor presets."""
    print("\nBuilt-in motor presets")
    print("=" * 60)
    for name in list_motors():
        m = get_motor(name)
        print(
            f"  {m.designation:8} | I = {m.total_impulse:5.2f} N·s | "
            f"burn {m.burn_time:.2f} s | peak {m.peak_thrust:5.1f} N | delay {m.delay_seconds:.0f} s"
        )
    print()


def print_kit_list() -> None:
    """Print all built-in rocket-kit presets."""
    print("\nBuilt-in rocket-kit presets")
    print("=" * 60)
    for name in list_kits():
        print(get_kit_info(name))
        print("-" * 60)


def resolve_motor(args: argparse.Namespace, default: Motor | None = None) -> Motor | None:
    """Resolve the motor from CLI flags. Returns ``None`` only if no source is given."""
    if args.motor_file:
        return load_motor_file(args.motor_file)
    if args.motor:
        return get_motor(args.motor)
    return default


def build_rocket_from_args(args: argparse.Namespace, body: CelestialBody) -> Rocket:
    """Build a Rocket from the CLI flags. Combines kit + overrides + custom flags."""
    if args.kit:
        rocket = get_kit(args.kit)
        # Apply overrides on top of the kit.
        motor: Motor = resolve_motor(args, default=rocket.motor) or rocket.motor
        recovery = rocket.recovery  # keep kit's recovery unless explicit override below
        if args.recovery and "--recovery" in sys.argv:
            recovery = parse_recovery(args.recovery)
        return replace(rocket, motor=motor, recovery=recovery, body=body)

    # Custom rocket — all four pieces required.
    if args.dry_mass is None or args.diameter is None:
        raise SystemExit(
            "Custom rocket requires --dry-mass and --diameter (and --motor or --motor-file)."
        )
    custom_motor = resolve_motor(args)
    if custom_motor is None:
        raise SystemExit("Custom rocket requires --motor or --motor-file.")
    recovery = parse_recovery(args.recovery)
    return Rocket(
        name="Custom Rocket",
        dry_mass_kg=args.dry_mass,
        motor=custom_motor,
        diameter_m=args.diameter,
        drag_coefficient=args.cd,
        recovery=recovery,
        body=body,
    )


def run_interactive_mode() -> tuple[Rocket, str]:
    """Walk the user through kit and body selection. Returns (rocket, body_key)."""
    print("\n" + "=" * 60)
    print("  rocket-sim — Interactive Mode")
    print("=" * 60)

    print_kit_list()
    while True:
        choice = input("Select a kit by name (or 'custom'): ").strip().lower()
        if choice == "custom":
            print("\nEnter custom rocket parameters:")
            dry_mass = float(input("  Dry mass (kg): "))
            diameter = float(input("  Diameter (m): "))
            cd = float(input("  Drag coefficient (e.g. 0.75): "))
            motor_name = input("  Motor designation (e.g. C6-5): ").strip()
            motor = get_motor(motor_name)
            chute_diam = float(input("  Parachute diameter in meters (0 for none): "))
            recovery: Parachute | Streamer | None = (
                Parachute(diameter_m=chute_diam) if chute_diam > 0 else None
            )
            rocket = Rocket(
                name="Custom Rocket",
                dry_mass_kg=dry_mass,
                motor=motor,
                diameter_m=diameter,
                drag_coefficient=cd,
                recovery=recovery,
            )
            break
        try:
            rocket = get_kit(choice)
            break
        except KeyError:
            print(f"Unknown kit: {choice!r}\n")

    print("\nLaunch from which body?")
    for key in BODIES:
        print(f"  - {key}")
    body_key = input("Body [earth]: ").strip().lower() or "earth"
    if body_key not in BODIES:
        print(f"Unknown body {body_key!r}; using Earth.")
        body_key = "earth"
    rocket = replace(rocket, body=BODIES[body_key])
    return rocket, body_key


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns an exit code."""
    parser = create_parser()
    args = parser.parse_args(argv)
    setup_logging(args.verbose, args.quiet)

    if args.list_motors:
        print_motor_list()
        return 0
    if args.list_kits:
        print_kit_list()
        return 0

    body = BODIES[args.body]
    rocket: Rocket
    if args.interactive or (not args.kit and args.dry_mass is None):
        rocket, _ = run_interactive_mode()
    else:
        try:
            rocket = build_rocket_from_args(args, body)
        except (KeyError, ValueError, SystemExit) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    sim_config = SimulationConfig(
        dt=args.dt,
        max_time=args.max_time,
        launch_altitude_m=args.launch_altitude,
        deploy_mode=args.deploy_mode,
    )

    if not args.quiet:
        print()
        print(f"Simulating: {rocket.name} on {(rocket.body or Physics.EARTH).name}")
        print(f"  Motor:        {rocket.motor.designation}  ({rocket.motor.total_impulse:.2f} N·s)")
        print(f"  Launch mass:  {rocket.launch_mass_kg * 1000:.1f} g")
        print()

    results = simulate_multiple([rocket], sim_config)

    if not args.quiet:
        print(results[0].summary())
        print()

    # Plot.
    if not args.no_plot or args.output:
        options = PlotOptions(style=PlotStyle(args.style), dpi=args.dpi)
        plotter = Plotter(options)
        if args.dashboard:
            plotter.plot_dashboard(results[0], filename=args.output, show=not args.no_plot)
        else:
            plotter.plot_trajectory(results[0], filename=args.output, show=not args.no_plot)

    return 0


def cli_main() -> NoReturn:
    """Entry point that handles process exit."""
    sys.exit(main())


if __name__ == "__main__":
    cli_main()
