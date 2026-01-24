"""
Visualization tools for rocket simulation results.

This module provides plotting capabilities for displaying rocket
trajectories and simulation data.
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
    from rocket_sim.simulation import SimulationResult


class PlotStyle(Enum):
    """Available plot styles."""

    DEFAULT = "default"
    DARK = "dark_background"
    SEABORN = "seaborn-v0_8-darkgrid"
    MINIMAL = "seaborn-v0_8-whitegrid"
    PUBLICATION = "seaborn-v0_8-paper"


@dataclass
class PlotOptions:
    """Options for customizing plots."""

    figsize: tuple[float, float] = (12, 8)
    dpi: int = 150
    style: PlotStyle = PlotStyle.SEABORN
    show_grid: bool = True
    show_legend: bool = True
    show_max_altitude: bool = True
    altitude_unit: str = "km"
    line_width: float = 2.0
    font_size: int = 12
    title_size: int = 14
    alpha: float = 0.9


class Plotter:
    """
    Visualization class for rocket simulation results.

    Provides methods for creating various plots of simulation data
    including trajectory plots, velocity profiles, and comparison charts.
    """

    # Color palette for multiple rockets
    COLORS = [
        "#2ecc71",  # Emerald green
        "#3498db",  # Dodger blue
        "#e74c3c",  # Alizarin red
        "#9b59b6",  # Amethyst purple
        "#f39c12",  # Orange
        "#1abc9c",  # Turquoise
        "#e91e63",  # Pink
        "#00bcd4",  # Cyan
        "#ff9800",  # Amber
        "#8bc34a",  # Light green
        "#673ab7",  # Deep purple
        "#795548",  # Brown
    ]

    def __init__(self, options: PlotOptions | None = None) -> None:
        """
        Initialize the plotter with options.

        Args:
            options: Plot customization options.
        """
        self.options = options or PlotOptions()

    def _setup_style(self) -> None:
        """Apply the configured plot style."""
        try:
            mpl_style.use(self.options.style.value)
        except OSError:
            # Fallback if style not available
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

    def _get_altitude_factor(self) -> tuple[float, str]:
        """Get conversion factor and label for altitude unit."""
        factors = {
            "m": (1.0, "Altitude (m)"),
            "km": (0.001, "Altitude (km)"),
            "mi": (0.000621371, "Altitude (mi)"),
        }
        return factors.get(self.options.altitude_unit, (0.001, "Altitude (km)"))

    def plot_trajectory(
        self,
        result: SimulationResult,
        filename: str | Path | None = None,
        show: bool = True,
    ) -> Figure:
        """
        Plot a single rocket trajectory.

        Args:
            result: Simulation result to plot.
            filename: Optional path to save the plot.
            show: Whether to display the plot.

        Returns:
            The matplotlib Figure object.
        """
        self._setup_style()

        fig, ax = plt.subplots(figsize=self.options.figsize)

        factor, ylabel = self._get_altitude_factor()
        altitudes = [alt * factor for alt in result.altitude_data]

        ax.plot(
            result.time_data,
            altitudes,
            color=self.COLORS[0],
            linewidth=self.options.line_width,
            alpha=self.options.alpha,
            label=result.rocket_name,
        )

        # Mark max altitude
        if self.options.show_max_altitude:
            max_idx = altitudes.index(max(altitudes))
            ax.annotate(
                f"Max: {max(altitudes):.2f} {self.options.altitude_unit}",
                xy=(result.time_data[max_idx], altitudes[max_idx]),
                xytext=(10, 10),
                textcoords="offset points",
                fontsize=self.options.font_size - 2,
                arrowprops={"arrowstyle": "->", "color": "gray"},
            )

        ax.set_xlabel("Time (s)")
        ax.set_ylabel(ylabel)
        ax.set_title(f"Trajectory: {result.rocket_name}")

        if self.options.show_grid:
            ax.grid(True, alpha=0.3)

        if self.options.show_legend:
            ax.legend(loc="upper right")

        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)

        plt.tight_layout()

        if filename:
            fig.savefig(filename, dpi=self.options.dpi, bbox_inches="tight")
            print(f"Plot saved to: {filename}")

        if show:
            plt.show()

        return fig

    def plot_multiple_trajectories(
        self,
        results: Sequence[SimulationResult],
        filename: str | Path | None = None,
        show: bool = True,
        title: str = "Rocket Altitude Comparison",
    ) -> Figure:
        """
        Plot multiple rocket trajectories on the same axes.

        Args:
            results: List of simulation results to plot.
            filename: Optional path to save the plot.
            show: Whether to display the plot.
            title: Plot title.

        Returns:
            The matplotlib Figure object.
        """
        if not results:
            raise ValueError("No results to plot")

        self._setup_style()

        fig, ax = plt.subplots(figsize=self.options.figsize)

        factor, ylabel = self._get_altitude_factor()

        for i, result in enumerate(results):
            color = self.COLORS[i % len(self.COLORS)]
            altitudes = [alt * factor for alt in result.altitude_data]
            max_alt = max(altitudes) if altitudes else 0

            label = f"{result.rocket_name} (Max: {max_alt:.2f} {self.options.altitude_unit})"

            ax.plot(
                result.time_data,
                altitudes,
                color=color,
                linewidth=self.options.line_width,
                alpha=self.options.alpha,
                label=label,
            )

        ax.set_xlabel("Time (s)")
        ax.set_ylabel(ylabel)
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
            print(f"Plot saved to: {filename}")

        if show:
            plt.show()

        return fig

    def plot_velocity_profile(
        self,
        result: SimulationResult,
        filename: str | Path | None = None,
        show: bool = True,
    ) -> Figure:
        """
        Plot velocity over time for a simulation.

        Args:
            result: Simulation result to plot.
            filename: Optional path to save the plot.
            show: Whether to display the plot.

        Returns:
            The matplotlib Figure object.
        """
        self._setup_style()

        fig, ax = plt.subplots(figsize=self.options.figsize)

        ax.plot(
            result.time_data,
            result.velocity_data,
            color=self.COLORS[1],
            linewidth=self.options.line_width,
            alpha=self.options.alpha,
        )

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Velocity (m/s)")
        ax.set_title(f"Velocity Profile: {result.rocket_name}")

        if self.options.show_grid:
            ax.grid(True, alpha=0.3)

        ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
        ax.set_xlim(left=0)

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
        """
        Create a dashboard with multiple plots for a single simulation.

        Includes: trajectory, velocity profile, and summary statistics.

        Args:
            result: Simulation result to plot.
            filename: Optional path to save the plot.
            show: Whether to display the plot.

        Returns:
            The matplotlib Figure object.
        """
        self._setup_style()

        fig = plt.figure(figsize=(14, 10))

        # Create grid for subplots
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

        # Trajectory plot (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        factor, ylabel = self._get_altitude_factor()
        altitudes = [alt * factor for alt in result.altitude_data]

        ax1.plot(
            result.time_data,
            altitudes,
            color=self.COLORS[0],
            linewidth=self.options.line_width,
        )
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel(ylabel)
        ax1.set_title("Altitude vs Time")
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(left=0)
        ax1.set_ylim(bottom=0)

        # Velocity plot (top right)
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(
            result.time_data,
            result.velocity_data,
            color=self.COLORS[1],
            linewidth=self.options.line_width,
        )
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Velocity (m/s)")
        ax2.set_title("Velocity vs Time")
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
        ax2.set_xlim(left=0)

        # Phase plot (bottom left) - altitude vs velocity
        ax3 = fig.add_subplot(gs[1, 0])
        ax3.plot(
            result.velocity_data,
            altitudes,
            color=self.COLORS[2],
            linewidth=self.options.line_width,
            alpha=0.7,
        )
        ax3.set_xlabel("Velocity (m/s)")
        ax3.set_ylabel(ylabel)
        ax3.set_title("Phase Plot (Altitude vs Velocity)")
        ax3.grid(True, alpha=0.3)

        # Statistics text (bottom right)
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis("off")

        stats_text = (
            f"Simulation Summary\n"
            f"{'=' * 30}\n\n"
            f"Rocket: {result.rocket_name}\n\n"
            f"Max Altitude: {result.max_altitude_km:,.2f} km\n"
            f"Max Velocity: {result.max_velocity:,.2f} m/s\n"
            f"Flight Time: {result.flight_time:,.2f} s\n"
            f"Status: {'Escaped' if result.escaped else 'Landed'}\n\n"
            f"Rocket Config:\n"
            f"  Mass: {result.config.mass:,.0f} kg\n"
            f"  Thrust: {result.config.thrust:,.0f} N\n"
            f"  Burn Time: {result.config.burn_time:.0f} s\n"
            f"  T/W Ratio: {result.config.thrust_to_weight_ratio:.2f}"
        )

        ax4.text(
            0.1,
            0.9,
            stats_text,
            transform=ax4.transAxes,
            fontsize=11,
            verticalalignment="top",
            fontfamily="monospace",
            bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
        )

        fig.suptitle(f"Simulation Dashboard: {result.rocket_name}", fontsize=16, y=0.98)

        plt.tight_layout()

        if filename:
            fig.savefig(filename, dpi=self.options.dpi, bbox_inches="tight")
            print(f"Dashboard saved to: {filename}")

        if show:
            plt.show()

        return fig

    def plot_comparison_bar(
        self,
        results: Sequence[SimulationResult],
        filename: str | Path | None = None,
        show: bool = True,
    ) -> Figure:
        """
        Create a bar chart comparing max altitudes of multiple rockets.

        Args:
            results: List of simulation results.
            filename: Optional path to save the plot.
            show: Whether to display the plot.

        Returns:
            The matplotlib Figure object.
        """
        self._setup_style()

        fig, ax = plt.subplots(figsize=self.options.figsize)

        names = [r.rocket_name for r in results]
        altitudes = [r.max_altitude_km for r in results]
        colors = [self.COLORS[i % len(self.COLORS)] for i in range(len(results))]

        bars = ax.bar(names, altitudes, color=colors, alpha=self.options.alpha)

        ax.set_xlabel("Rocket")
        ax.set_ylabel("Maximum Altitude (km)")
        ax.set_title("Maximum Altitude Comparison")

        # Add value labels on bars
        for bar, alt in zip(bars, altitudes, strict=False):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(altitudes) * 0.01,
                f"{alt:.0f}",
                ha="center",
                va="bottom",
                fontsize=self.options.font_size - 2,
            )

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        if filename:
            fig.savefig(filename, dpi=self.options.dpi, bbox_inches="tight")

        if show:
            plt.show()

        return fig
