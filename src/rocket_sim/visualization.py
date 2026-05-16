"""
Plotting utilities for rocket simulation results.

Provides a `Plotter` class with methods to render trajectory plots
(phase-coloured by BOOST/COAST/DESCENT), velocity profiles, thrust
curves, and a multi-panel dashboard summarising a single flight.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib import style as mpl_style
from matplotlib.figure import Figure

if TYPE_CHECKING:
    from rocket_sim.motors import Motor
    from rocket_sim.simulation import SimulationResult


class PlotStyle(Enum):
    """Available matplotlib plot styles."""

    DEFAULT = "default"
    DARK = "dark_background"
    SEABORN = "seaborn-v0_8-darkgrid"
    MINIMAL = "seaborn-v0_8-whitegrid"
    PUBLICATION = "seaborn-v0_8-paper"


@dataclass
class PlotOptions:
    """Plot customization options."""

    figsize: tuple[float, float] = (12, 8)
    dpi: int = 150
    style: PlotStyle = PlotStyle.SEABORN
    show_grid: bool = True
    show_legend: bool = True
    show_apogee_marker: bool = True
    line_width: float = 2.0
    font_size: int = 12
    title_size: int = 14
    alpha: float = 0.9


# Phase color palette used by `plot_trajectory` to colour the curve by phase.
PHASE_COLORS = {
    "boost": "#e67e22",  # orange
    "coast": "#3498db",  # blue
    "descent": "#27ae60",  # green
    "landed": "#7f8c8d",  # gray
}


class Plotter:
    """Renders matplotlib plots of `SimulationResult` data."""

    SERIES_COLORS = (
        "#2ecc71",
        "#3498db",
        "#e74c3c",
        "#9b59b6",
        "#f39c12",
        "#1abc9c",
        "#e91e63",
        "#00bcd4",
        "#ff9800",
        "#8bc34a",
        "#673ab7",
        "#795548",
    )

    def __init__(self, options: PlotOptions | None = None) -> None:
        self.options = options or PlotOptions()

    def _setup_style(self) -> None:
        """Apply matplotlib style and rcParams."""
        try:
            mpl_style.use(self.options.style.value)
        except OSError:
            import warnings

            warnings.warn(
                f"Matplotlib style {self.options.style.value!r} unavailable; "
                "falling back to 'default'.",
                stacklevel=2,
            )
            mpl_style.use("default")
        plt.rcParams.update(
            {
                "font.size": self.options.font_size,
                "axes.titlesize": self.options.title_size,
                "axes.labelsize": self.options.font_size,
                "legend.fontsize": self.options.font_size - 2,
                "figure.figsize": self.options.figsize,
                "figure.dpi": self.options.dpi,
            }
        )

    def plot_trajectory(
        self,
        result: SimulationResult,
        filename: str | Path | None = None,
        show: bool = True,
    ) -> Figure:
        """Plot altitude vs time, with the curve coloured by flight phase."""
        self._setup_style()
        fig, ax = plt.subplots(figsize=self.options.figsize)

        times = result.time_data
        alts = result.altitude_data
        phases = [s.phase.value for s in result.states]

        # Group consecutive same-phase samples into segments.
        segments: list[tuple[str, list[int]]] = []
        for i, phase in enumerate(phases):
            if segments and segments[-1][0] == phase:
                segments[-1][1].append(i)
            else:
                segments.append((phase, [i]))

        for phase, indices in segments:
            xs = [times[i] for i in indices]
            ys = [alts[i] for i in indices]
            ax.plot(
                xs,
                ys,
                color=PHASE_COLORS.get(phase, "#000000"),
                linewidth=self.options.line_width,
                alpha=self.options.alpha,
                label=phase.capitalize()
                if indices[0] == 0 or phase != phases[indices[0] - 1]
                else None,
            )

        if self.options.show_apogee_marker:
            ax.annotate(
                f"Apogee: {result.apogee_m:.1f} m",
                xy=(result.apogee_time_s, result.apogee_m),
                xytext=(10, 10),
                textcoords="offset points",
                fontsize=self.options.font_size - 1,
                arrowprops={"arrowstyle": "->", "color": "gray"},
            )

        # De-duplicate legend entries.
        handles, labels = ax.get_legend_handles_labels()
        seen: set[str] = set()
        deduped: list[tuple[object, str]] = []
        for handle, label in zip(handles, labels, strict=False):
            if label not in seen:
                seen.add(label)
                deduped.append((handle, label))
        if deduped and self.options.show_legend:
            ax.legend(*zip(*deduped, strict=False), loc="upper right")

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Altitude (m)")
        ax.set_title(f"Trajectory: {result.rocket_name}")
        if self.options.show_grid:
            ax.grid(True, alpha=0.3)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        plt.tight_layout()

        if filename:
            fig.savefig(filename, dpi=self.options.dpi, bbox_inches="tight")
        if show:
            plt.show()
        return fig

    def plot_velocity_profile(
        self,
        result: SimulationResult,
        filename: str | Path | None = None,
        show: bool = True,
    ) -> Figure:
        """Plot velocity vs time. Positive = upward; negative = descent."""
        self._setup_style()
        fig, ax = plt.subplots(figsize=self.options.figsize)
        ax.plot(
            result.time_data,
            result.velocity_data,
            color=self.SERIES_COLORS[1],
            linewidth=self.options.line_width,
            alpha=self.options.alpha,
        )
        ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Velocity (m/s)")
        ax.set_title(f"Velocity Profile: {result.rocket_name}")
        if self.options.show_grid:
            ax.grid(True, alpha=0.3)
        ax.set_xlim(left=0)
        plt.tight_layout()
        if filename:
            fig.savefig(filename, dpi=self.options.dpi, bbox_inches="tight")
        if show:
            plt.show()
        return fig

    def plot_thrust_curve(
        self,
        motor: Motor,
        filename: str | Path | None = None,
        show: bool = True,
    ) -> Figure:
        """Plot a motor's thrust curve."""
        self._setup_style()
        fig, ax = plt.subplots(figsize=self.options.figsize)
        times = [t for t, _ in motor.thrust_curve]
        thrusts = [f for _, f in motor.thrust_curve]
        ax.plot(
            times,
            thrusts,
            color=self.SERIES_COLORS[2],
            linewidth=self.options.line_width,
            alpha=self.options.alpha,
            marker="o",
            markersize=4,
        )
        ax.set_xlabel("Time since ignition (s)")
        ax.set_ylabel("Thrust (N)")
        ax.set_title(
            f"Thrust Curve: {motor.designation} "
            f"(I = {motor.total_impulse:.2f} N·s, peak {motor.peak_thrust:.1f} N)"
        )
        if self.options.show_grid:
            ax.grid(True, alpha=0.3)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        plt.tight_layout()
        if filename:
            fig.savefig(filename, dpi=self.options.dpi, bbox_inches="tight")
        if show:
            plt.show()
        return fig

    def plot_multiple_trajectories(
        self,
        results: Sequence[SimulationResult],
        filename: str | Path | None = None,
        show: bool = True,
        title: str = "Trajectory Comparison",
    ) -> Figure:
        """Plot several rocket trajectories on a single set of axes."""
        if not results:
            raise ValueError("No results to plot")
        self._setup_style()
        fig, ax = plt.subplots(figsize=self.options.figsize)
        for i, result in enumerate(results):
            color = self.SERIES_COLORS[i % len(self.SERIES_COLORS)]
            label = f"{result.rocket_name} (apogee {result.apogee_m:.0f} m)"
            ax.plot(
                result.time_data,
                result.altitude_data,
                color=color,
                linewidth=self.options.line_width,
                alpha=self.options.alpha,
                label=label,
            )
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Altitude (m)")
        ax.set_title(title)
        if self.options.show_grid:
            ax.grid(True, alpha=0.3)
        if self.options.show_legend:
            ax.legend(loc="upper right", framealpha=0.9)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        plt.tight_layout()
        if filename:
            fig.savefig(filename, dpi=self.options.dpi, bbox_inches="tight")
        if show:
            plt.show()
        return fig

    def plot_dashboard(
        self,
        result: SimulationResult,
        filename: str | Path | None = None,
        show: bool = True,
    ) -> Figure:
        """Multi-panel summary: trajectory, velocity, thrust curve, stats."""
        self._setup_style()
        fig = plt.figure(figsize=(14, 10))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # Top-left: altitude
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(
            result.time_data,
            result.altitude_data,
            color=self.SERIES_COLORS[0],
            linewidth=self.options.line_width,
        )
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel("Altitude (m)")
        ax1.set_title("Altitude vs Time")
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(left=0)
        ax1.set_ylim(bottom=0)

        # Top-right: velocity
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(
            result.time_data,
            result.velocity_data,
            color=self.SERIES_COLORS[1],
            linewidth=self.options.line_width,
        )
        ax2.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Velocity (m/s)")
        ax2.set_title("Velocity vs Time")
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(left=0)

        # Bottom-left: mass / thrust
        ax3 = fig.add_subplot(gs[1, 0])
        ax3b = ax3.twinx()
        masses_g = [m * 1000 for m in result.mass_data]
        ax3.plot(
            result.time_data,
            result.thrust_data,
            color=self.SERIES_COLORS[2],
            linewidth=self.options.line_width,
            label="Thrust (N)",
        )
        ax3b.plot(
            result.time_data,
            masses_g,
            color=self.SERIES_COLORS[3],
            linewidth=self.options.line_width,
            linestyle="--",
            label="Mass (g)",
        )
        ax3.set_xlabel("Time (s)")
        ax3.set_ylabel("Thrust (N)", color=self.SERIES_COLORS[2])
        ax3b.set_ylabel("Mass (g)", color=self.SERIES_COLORS[3])
        ax3.set_title("Thrust & Mass vs Time")
        ax3.grid(True, alpha=0.3)

        # Bottom-right: stats
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis("off")
        deploy = (
            f"{result.recovery_deployment_time_s:.2f} s"
            if result.recovery_deployment_time_s is not None
            else "did not deploy"
        )
        warn = " (LAWN DART!)" if result.deployed_below_ground else ""
        stats_text = (
            f"Flight Summary\n"
            f"{'=' * 30}\n\n"
            f"Rocket: {result.rocket_name}\n\n"
            f"Apogee:        {result.apogee_m:7.2f} m\n"
            f"  at t =       {result.apogee_time_s:.2f} s\n\n"
            f"Max velocity:  {result.max_velocity_ms:7.2f} m/s\n"
            f"Max accel:     {result.max_acceleration_ms2:7.2f} m/s²\n"
            f"             ({result.max_acceleration_ms2 / 9.80665:.2f} g)\n\n"
            f"Burnout:       {result.burnout_altitude_m:7.2f} m\n"
            f"  at t =       {result.burnout_time_s:.2f} s\n"
            f"  velocity:    {result.burnout_velocity_ms:7.2f} m/s\n\n"
            f"Recovery:      {deploy}{warn}\n"
            f"Flight time:   {result.flight_time_s:7.2f} s\n"
            f"Land speed:    {result.landing_velocity_ms:7.2f} m/s"
        )
        ax4.text(
            0.05,
            0.95,
            stats_text,
            transform=ax4.transAxes,
            fontsize=10,
            verticalalignment="top",
            fontfamily="monospace",
            bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
        )

        fig.suptitle(f"Flight Dashboard: {result.rocket_name}", fontsize=16, y=0.98)
        plt.tight_layout()
        if filename:
            fig.savefig(filename, dpi=self.options.dpi, bbox_inches="tight")
        if show:
            plt.show()
        return fig
