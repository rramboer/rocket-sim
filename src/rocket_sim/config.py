"""
Configuration management for rocket simulations.

Provides `SimulationConfig` controlling integration timestep, simulation
cap, recovery deploy timing, and launch-site elevation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

DeployMode = Literal["motor-delay", "apogee"]


@dataclass
class SimulationConfig:
    """
    Configuration for a rocket simulation.

    Attributes:
        dt: Integration timestep in seconds.
        max_time: Maximum simulation duration (seconds). Most flights
            are well under a few minutes.
        launch_altitude_m: Launch-site elevation above sea level
            (meters). Default 0 (sea level).
        deploy_mode: When recovery deploys.
            - ``"motor-delay"`` (default): ejection charge fires at
              ``motor.burn_time + motor.delay_seconds``, regardless of
              apogee. Realistic; reproduces the "lawn dart" failure
              mode if delay is mismatched.
            - ``"apogee"``: deploy exactly at apogee. Idealised; useful
              for design exploration.
    """

    dt: float = 0.05
    max_time: float = 600.0
    launch_altitude_m: float = 0.0
    deploy_mode: DeployMode = "motor-delay"

    def __post_init__(self) -> None:
        if self.dt <= 0:
            raise ValueError(f"Time step must be positive: {self.dt}")
        if self.max_time <= 0:
            raise ValueError(f"Max time must be positive: {self.max_time}")
        if self.launch_altitude_m < 0:
            raise ValueError(f"launch_altitude_m must be >= 0: {self.launch_altitude_m}")
        if self.deploy_mode not in ("motor-delay", "apogee"):
            raise ValueError(f"Unknown deploy_mode: {self.deploy_mode!r}")

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "dt": self.dt,
            "max_time": self.max_time,
            "launch_altitude_m": self.launch_altitude_m,
            "deploy_mode": self.deploy_mode,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimulationConfig:
        """Deserialise from a dict produced by `to_dict`."""
        deploy_mode = data.get("deploy_mode", "motor-delay")
        if deploy_mode not in ("motor-delay", "apogee"):
            raise ValueError(f"Unknown deploy_mode: {deploy_mode!r}")
        return cls(
            dt=float(data.get("dt", 0.05)),
            max_time=float(data.get("max_time", 600.0)),
            launch_altitude_m=float(data.get("launch_altitude_m", 0.0)),
            deploy_mode=deploy_mode,
        )

    def save(self, path: Path | str) -> None:
        """Save to a JSON file."""
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path | str) -> SimulationConfig:
        """Load from a JSON file."""
        return cls.from_dict(json.loads(Path(path).read_text()))
