"""
Configuration management for rocket simulations.

This module provides configuration dataclasses for controlling simulation
parameters and output settings.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class IntegrationMethod(Enum):
    """Numerical integration methods available for simulation."""

    EULER = "euler"
    EULER_CROMER = "euler_cromer"  # Symplectic Euler - better energy conservation


@dataclass
class SimulationConfig:
    """
    Configuration for rocket simulation parameters.

    Attributes:
        dt: Time step for simulation in seconds.
        max_time: Maximum simulation duration in seconds.
        integration_method: Numerical integration method to use.
        detect_escape: Whether to stop simulation on escape velocity.
        log_level: Logging verbosity level.
    """

    dt: float = 0.1
    max_time: float = 1_000_000.0
    integration_method: IntegrationMethod = IntegrationMethod.EULER
    detect_escape: bool = True
    log_level: int = logging.INFO

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if self.dt <= 0:
            raise ValueError(f"Time step must be positive: {self.dt}")
        if self.max_time <= 0:
            raise ValueError(f"Max time must be positive: {self.max_time}")

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "dt": self.dt,
            "max_time": self.max_time,
            "integration_method": self.integration_method.value,
            "detect_escape": self.detect_escape,
            "log_level": self.log_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimulationConfig:
        """Create configuration from dictionary."""
        method = data.get("integration_method", "euler")
        if isinstance(method, str):
            method = IntegrationMethod(method)

        return cls(
            dt=float(data.get("dt", 0.1)),
            max_time=float(data.get("max_time", 1_000_000.0)),
            integration_method=method,
            detect_escape=bool(data.get("detect_escape", True)),
            log_level=int(data.get("log_level", logging.INFO)),
        )

    def save(self, path: Path | str) -> None:
        """Save configuration to JSON file."""
        path = Path(path)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path | str) -> SimulationConfig:
        """Load configuration from JSON file."""
        path = Path(path)
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class PlotConfig:
    """
    Configuration for plot output.

    Attributes:
        figsize: Figure size as (width, height) in inches.
        dpi: Resolution in dots per inch.
        style: Matplotlib style to use.
        show_grid: Whether to display grid lines.
        show_legend: Whether to display legend.
        altitude_unit: Unit for altitude display ('m', 'km', 'mi').
        time_unit: Unit for time display ('s', 'min', 'h').
    """

    figsize: tuple[float, float] = (12, 8)
    dpi: int = 150
    style: str = "seaborn-v0_8-darkgrid"
    show_grid: bool = True
    show_legend: bool = True
    altitude_unit: str = "km"
    time_unit: str = "s"
    title: str = "Rocket Trajectory Simulation"

    # Unit conversion factors
    _altitude_factors: dict[str, float] = field(
        default_factory=lambda: {"m": 1.0, "km": 0.001, "mi": 0.000621371},
        repr=False,
    )
    _time_factors: dict[str, float] = field(
        default_factory=lambda: {"s": 1.0, "min": 1 / 60, "h": 1 / 3600},
        repr=False,
    )

    def get_altitude_factor(self) -> float:
        """Get conversion factor for altitude unit."""
        return self._altitude_factors.get(self.altitude_unit, 0.001)

    def get_time_factor(self) -> float:
        """Get conversion factor for time unit."""
        return self._time_factors.get(self.time_unit, 1.0)
