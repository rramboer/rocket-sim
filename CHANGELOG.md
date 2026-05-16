# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Pre-launch design validator** (`validate_design`, `DesignWarning`,
  `format_warnings`) with heuristic checks for marginal thrust-to-weight,
  predicted apogee, transonic flight, motor-too-big-for-airframe,
  ballistic descent, and "lawn dart" timing. Runs automatically in the
  CLI; pass `--no-validate` to skip.
- **CSV and JSON export** on `SimulationResult` (`.to_csv(path)`,
  `.to_dict()`, `.to_json(path)`) for downstream notebook / spreadsheet
  analysis. CLI flags `--csv FILE` and `--json FILE` write the same data.
- **`1/2A6-2` motor preset** for use with the Mosquito kit and other
  small rockets — replaces the previous silent fallback to A8-3.
- CLI exit code `2` when the design validator returns any `error`-level
  warning, for use in CI / scripts.

### Planned

- More built-in motor presets (1/4A and mid-power)
- Wind / weathercocking (would extend the model from 1-D to 2-D)
- Multi-stage configurations
- Stability-margin analysis (CG vs CP)

## [0.1.0]

First public release on PyPI. Educational hobby/model-rocket trajectory simulator.

### Added

- **Three-phase trajectory integrator** (BOOST / COAST / DESCENT) with
  symplectic Euler integration and semi-implicit drag treatment for
  stability when a parachute deploys at high velocity.
- **`Motor` type** with sampled thrust curves, linear-time interpolation,
  total-impulse / burn-time / peak-thrust / Isp properties, and
  constant-Isp mass-flow model.
- **Built-in motor presets**: A8-3, B6-4, C6-3, C6-5, D12-5, E9-6, F15-6.
- **`.eng` motor file loader** (`load_motor_file`, `parse_eng_file`)
  compatible with files from Thrustcurve.org and OpenRocket.
- **`Rocket` type** combining airframe (dry mass, diameter, drag
  coefficient), motor, recovery system, and launch body.
- **Recovery types**: `Parachute(diameter, Cd)`, `Streamer(length, width, Cd)`,
  or `None` (ballistic).
- **Kit presets**: Estes Alpha III, Big Bertha, Mosquito, V-2.
- **Multi-body support**: `Physics.EARTH`, `Physics.MOON`,
  `Physics.MARS`, `Physics.VENUS`, `Physics.TITAN`, plus user-defined
  `CelestialBody` instances.
- **`Atmosphere` type** with built-in `.earth()`, `.mars()`, `.venus()`,
  `.titan()` factories. Bodies with `atmosphere=None` are vacuums.
- **Recovery deployment timing**: realistic (motor delay grain) by
  default; idealised (deploy at apogee) as opt-in.
- **Standalone physics utilities**: `gravity_at_altitude`,
  `escape_velocity`, `orbital_velocity`. Not used by the trajectory
  loop but kept for educational comparisons.
- **Visualization**: phase-coloured trajectory plots, velocity profiles,
  thrust-curve plots, and a multi-panel dashboard.
- **CLI** (`rocket-sim`) with `--kit`, `--motor`, `--motor-file`,
  `--body`, `--deploy-mode`, `--launch-altitude`, `--dashboard`, and
  interactive mode.

### Technical Details

- Python 3.10+
- src-layout, hatchling build, ruff + mypy + pytest tooling
- Symplectic Euler with semi-implicit drag for numerical stability
- Constant-Isp mass-flow approximation
- 1-D vertical motion, single-stage only
