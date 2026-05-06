"""
Rocket Simulator - A physics-based rocket trajectory simulation library.

This package provides tools for simulating rocket launches and trajectories,
accounting for gravitational effects at various altitudes using real physics.
"""

from rocket_sim.config import SimulationConfig
from rocket_sim.models import Engine, Rocket, RocketConfig
from rocket_sim.physics import CelestialBody, Physics
from rocket_sim.presets import PRESETS, get_preset, list_presets
from rocket_sim.simulation import (
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
    # Core classes
    "Engine",
    "Rocket",
    "RocketConfig",
    "RocketSimulation",
    "SimulationResult",
    "SimulationState",
    # Simulation functions
    "simulate_rocket",
    "simulate_multiple",
    # Physics
    "Physics",
    "CelestialBody",
    # Configuration
    "SimulationConfig",
    # Presets
    "PRESETS",
    "get_preset",
    "list_presets",
    # Visualization
    "Plotter",
    "PlotStyle",
    "PlotOptions",
]
