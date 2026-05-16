# rocket-sim

[![PyPI](https://img.shields.io/pypi/v/rocket-sim.svg)](https://pypi.org/project/rocket-sim/)
[![Python](https://img.shields.io/pypi/pyversions/rocket-sim.svg)](https://pypi.org/project/rocket-sim/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/rramboer/rocket-sim/actions/workflows/ci.yml/badge.svg)](https://github.com/rramboer/rocket-sim/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A small, scriptable hobby/model-rocket flight simulator. Predict the
apogee, peak velocity, peak acceleration, and recovery behaviour of a
single-stage Estes/Quest-class rocket — and, just for fun, see what
the same rocket would do on the Moon, Mars, Venus, or Titan.

## Features

- **Real (interpolated) thrust curves** — solid motors aren't constant
  thrust, and `rocket-sim` doesn't pretend they are. Built-in presets
  cover **A8-3, B6-4, C6-3, C6-5, D12-5, E9-6, F15-6**, with
  manufacturer-consistent total impulse, burn time, and peak thrust.
- **Drag-aware trajectory** — exponential atmosphere with body-specific
  surface density and scale height; drag opposes motion throughout the
  flight.
- **Mass loss during burn** — propellant is a meaningful fraction of
  hobby-rocket mass, so the simulator integrates a constant-Isp mass
  flow rather than treating mass as constant.
- **Multi-body launches** — Earth, Moon, Mars, Venus, Titan ship
  built-in. Custom `CelestialBody` instances are supported.
- **Recovery modelling** — `Parachute`, `Streamer`, or ballistic.
  Realistic motor-delay-grain timing by default; `--deploy-mode apogee`
  for the idealised case.
- **Kit presets** — Estes Alpha III, Big Bertha, Mosquito, V-2, each
  configured with its recommended motor and recovery.
- **`.eng` motor file loader** — drop in any motor from
  [Thrustcurve.org](https://www.thrustcurve.org/).
- **Pre-launch design validator** flags marginal thrust-to-weight,
  underpowered configurations, transonic flight, motors that don't fit
  the body tube, and "lawn dart" timing.
- **CSV / JSON export** for the trajectory time-series and summary
  stats — pipe straight into a Jupyter notebook or spreadsheet.
- **CLI and library** — use `rocket-sim` as a command-line tool or
  `import rocket_sim` from your own scripts.

## Modelling caveats

This is a **deliberately simplified** simulator:

- Motion is **1-D vertical only** — no pitch-over, no horizontal velocity, no
  weathercocking, no wind.
- **Single stage only** — no boost-dart or multi-stage configurations.
- Built-in motor thrust curves are **simplified ~5-7-sample
  approximations** of public manufacturer data; expect apogee
  predictions accurate to ~30 % relative to a properly-instrumented
  real flight.
- No center-of-gravity / center-of-pressure stability analysis.
- `Physics.escape_velocity` and `Physics.orbital_velocity` are
  exposed as standalone utilities; they are not used in the
  trajectory loop (hobby rockets do not approach orbital speeds).

For higher-fidelity simulation (6-DOF, wind, multi-stage, optimisation,
GUI), see [OpenRocket](https://openrocket.info/) — the gold standard
in hobby-rocket simulation.

## Quick start

### Install

```bash
pip install rocket-sim
```

### Command line

```bash
# Launch an Estes Alpha III with a C6-5 motor on Earth
rocket-sim --kit alpha-iii --motor c6-5

# Same rocket, on the Moon
rocket-sim --kit alpha-iii --motor c6-5 --body moon

# Multi-panel dashboard, save as PNG
rocket-sim --kit big-bertha --dashboard -o flight.png

# Use a downloaded thrustcurve.org motor file
rocket-sim --kit alpha-iii --motor-file ./Estes_C6.eng

# Save the trajectory time-series for analysis
rocket-sim --kit alpha-iii --csv flight.csv --json flight.json --no-plot

# List available motors and kits
rocket-sim --list-motors
rocket-sim --list-kits
```

### Python library

```python
from rocket_sim import get_kit, simulate_rocket, Plotter

rocket = get_kit("alpha-iii")
result = simulate_rocket(rocket)

print(f"Apogee:      {result.apogee_m:.1f} m at t = {result.apogee_time_s:.2f} s")
print(f"Max velocity:{result.max_velocity_ms:.1f} m/s")
print(f"Max accel:   {result.max_acceleration_ms2 / 9.80665:.2f} g")

Plotter().plot_trajectory(result, filename="alpha-iii.png")
```

### Multi-body comparison

```python
from dataclasses import replace
from rocket_sim import Physics, get_kit, simulate_multiple, Plotter

rocket = get_kit("alpha-iii")
worlds = [Physics.EARTH, Physics.MOON, Physics.MARS]
rockets = [replace(rocket, body=b, name=f"Alpha III on {b.name}") for b in worlds]
results = simulate_multiple(rockets)
Plotter().plot_multiple_trajectories(results, title="Same rocket, three worlds")
```

### Custom rocket

```python
from rocket_sim import Rocket, Parachute, get_motor, simulate_rocket

rocket = Rocket(
    name="My Rocket",
    dry_mass_kg=0.060,           # 60 g airframe
    motor=get_motor("D12-5"),
    diameter_m=0.029,            # 29 mm body tube
    drag_coefficient=0.7,
    recovery=Parachute(diameter_m=0.45),
)

result = simulate_rocket(rocket)
print(result.summary())
```

### Validate a design

```python
from rocket_sim import get_kit, validate_design, format_warnings

rocket = get_kit("alpha-iii")
warnings = validate_design(rocket)
print(format_warnings(warnings))
# → "No design warnings."
```

### Export the time-series

```python
from rocket_sim import get_kit, simulate_rocket

result = simulate_rocket(get_kit("alpha-iii"))
result.to_csv("flight.csv")
result.to_json("flight.json")
```

## Built-in motor presets

| Designation | Total impulse | Burn time | Peak thrust | Delay grain |
|---|---|---|---|---|
| 1/2A6-2 | ~1.25 N·s | 0.32 s | ~7 N | 2 s |
| A8-3 | ~2.5 N·s | 0.5 s | ~13 N | 3 s |
| B6-4 | ~5.0 N·s | 0.86 s | ~12 N | 4 s |
| C6-3 | ~10.0 N·s | 1.85 s | ~14 N | 3 s |
| C6-5 | ~10.0 N·s | 1.85 s | ~14 N | 5 s |
| D12-5 | ~16.8 N·s | 1.6 s | ~30 N | 5 s |
| E9-6 | ~28.5 N·s | 2.83 s | ~24 N | 6 s |
| F15-6 | ~50 N·s | 3.45 s | ~30 N | 6 s |

Curves are simplified educational approximations of public manufacturer
data. For exact certified-motor data, download `.eng` files from
[Thrustcurve.org](https://www.thrustcurve.org/) and load them with
`load_motor_file(path)` or `--motor-file path.eng`.

## Built-in kit presets

| Kit | Dry mass | Diameter | Recommended motor | Recovery |
|---|---|---|---|---|
| Estes Alpha III | 34 g | 24.7 mm (BT-50) | C6-5 | 12-inch parachute |
| Estes Big Bertha | 77 g | 41.3 mm (BT-60) | C6-5 | 18-inch parachute |
| Estes Mosquito | 4.5 g | 13.2 mm (BT-5) | 1/2A6-2 | 30 × 2.5 cm streamer |
| Estes V-2 | 64 g | 41.3 mm (BT-60) | C6-3 | 12-inch parachute |

## Built-in celestial bodies

| Body | Surface gravity | Atmosphere | Notes |
|---|---|---|---|
| Earth | 9.82 m/s² | 1.225 kg/m³ surface, 8.5 km scale height | Default |
| Moon | 1.62 m/s² | none (vacuum) | Lots of altitude, no chute drag |
| Mars | 3.72 m/s² | 0.020 kg/m³ surface, 11.1 km scale height | Hits hard at landing |
| Venus | 8.87 m/s² | 65 kg/m³ surface, 15.9 km scale height | Soft launch, thermal hellscape |
| Titan | 1.35 m/s² | 5.4 kg/m³ surface, 21 km scale height | Thick cold atmosphere |

## Physics model

The integrator advances the state vector `(altitude, velocity, mass)`
through three flight phases (BOOST / COAST / DESCENT):

```
F_thrust(t) - drag(v, ρ(h), Cd, A) - m(t) · g(h)
```

- Gravity uses the inverse-square law: `g(h) = G·M / (R + h)²`.
- Drag is `½·ρ(h)·v²·Cd·A`, opposing the velocity vector. During
  BOOST and COAST, `Cd·A` comes from the airframe; during DESCENT,
  it comes from the deployed recovery device.
- Atmospheric density follows an exponential model:
  `ρ(h) = ρ₀ · exp(-h / H)`.
- Mass-flow is computed by assuming constant Isp:
  `dm/dt = thrust(t) / (Isp · g₀)`, equivalent to "propellant burns
  proportionally to delivered impulse."
- The integrator is **symplectic Euler with semi-implicit drag**,
  which keeps it stable when a parachute deploys at high speed.

## Project structure

```
rocket-sim/
├── src/rocket_sim/
│   ├── __init__.py        # Public exports
│   ├── physics.py         # Atmosphere, CelestialBody, Physics
│   ├── motors.py          # Motor type, .eng loader, motor presets
│   ├── models.py          # Rocket, Parachute, Streamer
│   ├── presets.py         # Kit presets
│   ├── simulation.py      # 3-phase trajectory integrator
│   ├── config.py          # SimulationConfig
│   ├── validation.py      # Pre-launch design validator
│   ├── visualization.py   # Plotter
│   └── cli.py             # rocket-sim CLI
├── tests/
└── examples/
```

## Development

```bash
git clone https://github.com/rramboer/rocket-sim.git
cd rocket-sim
pip install -e ".[dev]"
pre-commit install

# Test, lint, type-check
pytest
ruff check src tests
ruff format src tests
mypy src
```

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

- Motor thrust-curve data is informed by the public dataset at
  [Thrustcurve.org](https://www.thrustcurve.org/).
- Kit specifications are drawn from public Estes catalogs and
  product pages.
- For a full-featured open-source aerospace simulator, see
  [OpenRocket](https://openrocket.info/).
