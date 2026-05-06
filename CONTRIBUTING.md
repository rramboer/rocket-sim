# Contributing to Rocket Simulator

Thank you for your interest in contributing to Rocket Simulator! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:

1. A clear, descriptive title
2. Steps to reproduce the problem
3. Expected behavior vs. actual behavior
4. Your environment (Python version, OS, etc.)
5. Any relevant error messages or logs

### Suggesting Features

Feature suggestions are welcome! Please open an issue with:

1. A clear description of the feature
2. Why it would be useful
3. Possible implementation approaches (optional)

### Pull Requests

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Install** development dependencies:
   ```bash
   pip install -e ".[dev]"
   pre-commit install
   ```
5. **Make your changes**
6. **Write tests** for new functionality
7. **Run the test suite**:
   ```bash
   pytest
   ```
8. **Ensure code quality**:
   ```bash
   ruff check --fix src tests
   ruff format src tests
   mypy src
   ```
9. **Commit** with a clear message:
   ```bash
   git commit -m "Add feature: description of changes"
   ```
10. **Push** to your fork:
    ```bash
    git push origin feature/your-feature-name
    ```
11. **Open a Pull Request** against the `main` branch

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip
- git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/rocket-sim.git
cd rocket-sim

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=rocket_sim --cov-report=html

# Run specific test file
pytest tests/test_physics.py

# Run tests matching a pattern
pytest -k "test_gravity"
```

### Code Style

This project uses:

- **Ruff** for linting and formatting (replaces black, isort, flake8, pyupgrade)
- **mypy** for type checking

All of these run automatically via pre-commit hooks, but you can also run them manually:

```bash
# Lint and auto-fix
ruff check --fix src tests

# Format
ruff format src tests

# Type check
mypy src
```

## Project Structure

```
rocket-sim/
├── src/rocket_sim/     # Main package
│   ├── __init__.py     # Package exports
│   ├── physics.py      # Physics calculations
│   ├── models.py       # Data models
│   ├── simulation.py   # Simulation engine
│   ├── visualization.py # Plotting
│   ├── presets.py      # Rocket presets
│   ├── config.py       # Configuration
│   └── cli.py          # CLI interface
├── tests/              # Test suite
├── docs/               # Documentation
└── examples/           # Example scripts
```

## Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Use pytest fixtures from `conftest.py`
- Aim for good coverage of new functionality

Example test:

```python
import pytest
from rocket_sim.physics import Physics

def test_gravity_at_surface():
    """Test gravity at Earth's surface."""
    g = Physics.gravity_at_altitude(0)
    assert 9.7 < g < 9.9

def test_negative_altitude_raises_error():
    """Test that negative altitude raises ValueError."""
    with pytest.raises(ValueError):
        Physics.gravity_at_altitude(-100)
```

## Documentation

- Add docstrings to all public functions and classes
- Follow Google-style docstrings
- Update README.md if adding user-facing features

Example docstring:

```python
def gravity_at_altitude(altitude: float) -> float:
    """
    Calculate gravitational acceleration at a given altitude.

    Args:
        altitude: Height above surface in meters. Must be >= 0.

    Returns:
        Gravitational acceleration in m/s^2.

    Raises:
        ValueError: If altitude is negative.

    Examples:
        >>> gravity_at_altitude(0)
        9.819...
    """
```

## Adding New Rocket Presets

To add a new rocket preset:

1. Find reliable specifications (mass, thrust, burn time)
2. Add to `src/rocket_sim/presets.py`:
   ```python
   "New Rocket": RocketConfig(
       name="New Rocket",
       mass=1000000,      # kg
       thrust=10000000,   # N
       burn_time=180,     # s
   ),
   ```
3. Add a test in `tests/test_presets.py`
4. Update the README table

## Questions?

If you have questions, feel free to open an issue or start a discussion.

Thank you for contributing!
