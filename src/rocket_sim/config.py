"""
Configuration management for rocket simulations.

This module provides configuration dataclasses for controlling simulation
parameters and output settings.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SimulationConfig:
    """
    Configuration for rocket simulation parameters.

    Attributes:
        dt: Time step for simulation in seconds.
        max_time: Maximum simulation duration in seconds.
        detect_escape: Whether to stop simulation on escape velocity.
    """

    dt: float = 0.1
    max_time: float = 1_000_000.0
    detect_escape: bool = True

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
            "detect_escape": self.detect_escape,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimulationConfig:
        """Create configuration from dictionary."""
        return cls(
            dt=float(data.get("dt", 0.1)),
            max_time=float(data.get("max_time", 1_000_000.0)),
            detect_escape=bool(data.get("detect_escape", True)),
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
