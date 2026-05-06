"""
rocket-sim — a hobby/model-rocket trajectory simulator with multi-body support.

Predict the apogee, max velocity, peak acceleration, and recovery
behaviour of an Estes/Quest-class single-stage solid-motor rocket.
Launches can be configured for any celestial body the package ships
(Earth, Moon, Mars, Venus, Titan) or a custom `CelestialBody`.

The model is deliberately simplified: motion is 1-D vertical, single
stage, atmospherically realistic (drag is integrated into the
trajectory; mass loss during burn is modelled with a constant-Isp
approximation; thrust curves are interpolated). For more capable
simulation (6-DOF, wind, multi-stage) see OpenRocket.
"""

from rocket_sim.config import SimulationConfig
from rocket_sim.models import Parachute, Recovery, Rocket, Streamer
from rocket_sim.motors import (
    G0_STANDARD,
    MOTORS,
    Motor,
    get_motor,
    list_motors,
    load_motor_file,
    parse_eng_file,
)
from rocket_sim.physics import Atmosphere, CelestialBody, Physics
from rocket_sim.presets import get_kit, get_kit_info, list_kits
from rocket_sim.simulation import (
    FlightPhase,
    RocketSimulation,
    SimulationResult,
    SimulationState,
    simulate_multiple,
    simulate_rocket,
)
from rocket_sim.visualization import PlotOptions, PlotStyle, Plotter

__version__ = "0.1.0"
__author__ = "Ryan R"

__all__ = [
    # Core types
    "Rocket",
    "Motor",
    "Parachute",
    "Streamer",
    "Recovery",
    # Physics
    "Physics",
    "CelestialBody",
    "Atmosphere",
    # Configuration & simulation
    "SimulationConfig",
    "RocketSimulation",
    "SimulationResult",
    "SimulationState",
    "FlightPhase",
    # Convenience entry points
    "simulate_rocket",
    "simulate_multiple",
    # Motor data
    "MOTORS",
    "G0_STANDARD",
    "get_motor",
    "list_motors",
    "load_motor_file",
    "parse_eng_file",
    # Kit presets
    "get_kit",
    "get_kit_info",
    "list_kits",
    # Visualisation
    "Plotter",
    "PlotStyle",
    "PlotOptions",
]
