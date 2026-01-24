# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-24

### Added

- **Core Simulation Engine**
  - Physics-based trajectory simulation with altitude-dependent gravity
  - Newton's inverse-square law for gravitational calculations
  - Escape velocity detection
  - Configurable time steps and simulation parameters

- **Rocket Models**
  - `Engine` class for propulsion modeling
  - `Rocket` class with full state tracking
  - `RocketConfig` dataclass for easy configuration
  - Validation of all input parameters

- **Pre-configured Rockets**
  - Saturn V
  - SpaceX Falcon 9
  - SpaceX Starship
  - Space Shuttle
  - Ariane 5
  - Delta IV Heavy
  - Atlas V
  - Soyuz-2
  - Long March 5
  - Vega
  - Electron
  - New Shepard
  - Vulcan Centaur

- **Visualization**
  - Trajectory plotting with matplotlib
  - Multi-rocket comparison plots
  - Velocity profiles
  - Dashboard view with multiple plots
  - Bar chart comparisons
  - Multiple plot styles (dark, light, seaborn, publication)
  - High-resolution export (configurable DPI)

- **Command-Line Interface**
  - `--preset` for quick rocket selection
  - `--all-presets` for batch simulation
  - `--interactive` mode for guided configuration
  - Custom rocket parameters via CLI flags
  - `--dashboard` for comprehensive output
  - Multiple output formats and styles

- **Physics Calculations**
  - Gravitational acceleration at altitude
  - Escape velocity calculations
  - Orbital velocity calculations
  - Atmospheric density model
  - Drag force calculations
  - Support for different celestial bodies (Earth, Moon, Mars)

- **Configuration System**
  - `SimulationConfig` for simulation parameters
  - `PlotConfig` for visualization settings
  - JSON serialization support
  - Integration method selection

- **Developer Experience**
  - Full type hints throughout codebase
  - Comprehensive docstrings
  - pytest test suite with fixtures
  - Pre-commit hooks configuration
  - GitHub Actions CI/CD
  - Black, isort, ruff for code quality
  - mypy for type checking

### Technical Details

- Python 3.10+ required
- Uses matplotlib for visualization
- NumPy for numerical operations
- Modern Python packaging with pyproject.toml
- src-layout package structure

## [Unreleased]

### Planned

- Multi-stage rocket support
- Atmospheric drag simulation
- 3D trajectory visualization
- Real-time simulation mode
- Rocket builder GUI
- Export to various data formats (CSV, JSON)
- Orbital insertion calculations
