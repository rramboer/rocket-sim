"""
Solid-propellant rocket motors.

This module models a single-shot solid rocket motor as a sampled thrust
curve plus mass and timing data, with linear interpolation between
samples. It also provides:

- A registry of common Estes-class motor presets (`MOTORS`) covering
  motor designations from A8-3 through F15-6.
- A loader for the standard `.eng` file format used by Thrustcurve.org
  and OpenRocket, so users can drop in any motor they have data for.

Thrust-curve coefficients in the built-in presets are simplified
approximations consistent with manufacturer-published total impulse,
average thrust, and burn time. They are intended for educational
prediction, not for engineering certification.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

# Sample standard for "g0" used in mass-flow / specific-impulse calculations.
G0_STANDARD: float = 9.80665


@dataclass(frozen=True)
class Motor:
    """
    A solid rocket motor with a sampled thrust curve.

    Attributes:
        designation: Short motor code, e.g. "C6-5". The number after the
            hyphen is the delay-grain time in seconds.
        name: Human-readable name, e.g. "Estes C6-5".
        diameter_m: Motor casing diameter in meters (informational).
        length_m: Motor casing length in meters (informational).
        propellant_mass_kg: Mass of propellant that burns away during
            firing (kg).
        total_mass_kg: Total motor mass at ignition, including casing
            (kg).
        thrust_curve: Tuple of (time_s, thrust_N) sample pairs. Must be
            non-empty, monotonically increasing in time, and have
            non-negative thrust. The first sample should be at t=0
            with thrust=0.
        delay_seconds: Time between thrust end and ejection charge
            firing (seconds). 0 disables the delay grain (deploy
            immediately at burnout).
        manufacturer: Manufacturer name (informational).
    """

    designation: str
    name: str
    diameter_m: float
    length_m: float
    propellant_mass_kg: float
    total_mass_kg: float
    thrust_curve: tuple[tuple[float, float], ...]
    delay_seconds: float
    manufacturer: str = "Unknown"

    def __post_init__(self) -> None:
        if self.propellant_mass_kg <= 0:
            raise ValueError(f"propellant_mass_kg must be > 0: {self.propellant_mass_kg}")
        if self.total_mass_kg <= 0:
            raise ValueError(f"total_mass_kg must be > 0: {self.total_mass_kg}")
        if self.total_mass_kg < self.propellant_mass_kg:
            raise ValueError(
                f"total_mass_kg ({self.total_mass_kg}) must be >= propellant_mass_kg "
                f"({self.propellant_mass_kg})"
            )
        if self.delay_seconds < 0:
            raise ValueError(f"delay_seconds must be >= 0: {self.delay_seconds}")
        if self.diameter_m <= 0 or self.length_m <= 0:
            raise ValueError("Motor diameter and length must be > 0")

        if not self.thrust_curve:
            raise ValueError("thrust_curve cannot be empty")
        prev_t = -1.0
        for t, f in self.thrust_curve:
            if t < prev_t:
                raise ValueError(
                    f"thrust_curve times must be monotonically increasing: {t} after {prev_t}"
                )
            if f < 0:
                raise ValueError(f"thrust_curve thrust values must be >= 0: {f} at t={t}")
            prev_t = t

    @property
    def burn_time(self) -> float:
        """Time in seconds at which thrust is last sampled (typically when thrust drops to 0)."""
        return self.thrust_curve[-1][0]

    @property
    def total_impulse(self) -> float:
        """Total impulse in Newton-seconds, computed by trapezoidal integration of the curve."""
        impulse = 0.0
        for (t0, f0), (t1, f1) in zip(self.thrust_curve, self.thrust_curve[1:], strict=False):
            impulse += 0.5 * (f0 + f1) * (t1 - t0)
        return impulse

    @property
    def average_thrust(self) -> float:
        """Average thrust over the burn (N)."""
        bt = self.burn_time
        return self.total_impulse / bt if bt > 0 else 0.0

    @property
    def peak_thrust(self) -> float:
        """Maximum thrust value in the curve (N)."""
        return max(f for _, f in self.thrust_curve)

    @property
    def specific_impulse(self) -> float:
        """
        Effective specific impulse in seconds.

        Computed as `total_impulse / (propellant_mass * g0)`. Used by
        the simulation to compute mass flow rate during burn.
        """
        return self.total_impulse / (self.propellant_mass_kg * G0_STANDARD)

    def thrust_at(self, t: float) -> float:
        """
        Return thrust in Newtons at time t (seconds since ignition).

        Linearly interpolates between adjacent samples. Returns 0
        before t=0 or after the final sample time.
        """
        if t < 0 or t >= self.burn_time:
            return 0.0
        samples = self.thrust_curve
        # Linear scan is fine for the small (~10-30 sample) curves shipped here.
        for (t0, f0), (t1, f1) in zip(samples, samples[1:], strict=False):
            if t0 <= t <= t1:
                if t1 == t0:
                    return f0
                frac = (t - t0) / (t1 - t0)
                return f0 + frac * (f1 - f0)
        return 0.0

    def is_burning(self, t: float) -> bool:
        """True if the motor is producing thrust at time t."""
        return 0 <= t < self.burn_time and self.thrust_at(t) > 0

    def propellant_burned_at(self, t: float) -> float:
        """
        Mass of propellant burned by time t (kg).

        Assumes constant Isp: propellant burns proportionally to delivered impulse.
        """
        if t <= 0:
            return 0.0
        if t >= self.burn_time:
            return self.propellant_mass_kg
        # Trapezoidal integration up to t.
        impulse = 0.0
        samples = self.thrust_curve
        for (t0, f0), (t1, f1) in zip(samples, samples[1:], strict=False):
            if t1 <= t:
                impulse += 0.5 * (f0 + f1) * (t1 - t0)
            elif t0 < t <= t1:
                # Partial trapezoid.
                f_at_t = f0 if t1 == t0 else f0 + (f1 - f0) * (t - t0) / (t1 - t0)
                impulse += 0.5 * (f0 + f_at_t) * (t - t0)
                break
            else:
                break
        if self.total_impulse <= 0:
            return 0.0
        return self.propellant_mass_kg * (impulse / self.total_impulse)

    def mass_at(self, t: float) -> float:
        """Motor mass at time t (kg). Decreases monotonically during burn."""
        return self.total_mass_kg - self.propellant_burned_at(t)

    def ejection_time(self) -> float:
        """Absolute time (seconds since ignition) at which the ejection charge fires."""
        return self.burn_time + self.delay_seconds


# ---------------------------------------------------------------------------
# .eng file format support
# ---------------------------------------------------------------------------


def parse_eng_file(text: str) -> Motor:
    """
    Parse a `.eng` motor data file and return a `Motor`.

    The `.eng` format used by Thrustcurve.org and OpenRocket is::

        ; comment lines start with semicolons
        NAME diameter_mm length_mm delays propellant_mass_kg total_mass_kg manufacturer
           t1 f1
           t2 f2
           ...
        ;

    where the data block is terminated by a `;` line, blank line, or
    end of file. Multiple delay options in the header are separated by
    hyphens (e.g. "3-5-7"); the first one is taken as the default.

    Args:
        text: File content as a string.

    Returns:
        A `Motor` instance.

    Raises:
        ValueError: If the file is malformed or missing required fields.
    """
    header: list[str] | None = None
    samples: list[tuple[float, float]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if header is not None and samples:
                break
            continue
        if line.startswith(";"):
            if header is not None and samples:
                break
            continue
        if header is None:
            parts = line.split()
            if len(parts) < 7:
                raise ValueError(
                    f"Malformed .eng header (need 7 whitespace-separated fields, got {len(parts)}): {line!r}"
                )
            header = parts
            continue
        parts = line.split()
        if len(parts) < 2:
            raise ValueError(f"Malformed .eng data line: {line!r}")
        try:
            t = float(parts[0])
            f = float(parts[1])
        except ValueError as exc:
            raise ValueError(f"Could not parse t/thrust from line {line!r}") from exc
        samples.append((t, f))

    if header is None:
        raise ValueError("No header line found in .eng file")
    if not samples:
        raise ValueError("No thrust samples found in .eng file")

    designation = header[0]
    diameter_mm = float(header[1])
    length_mm = float(header[2])
    delays_field = header[3]
    propellant_mass_kg = float(header[4])
    total_mass_kg = float(header[5])
    manufacturer = " ".join(header[6:])

    # Pick the first listed delay (e.g. "3-5-7" → 3).
    first_delay = delays_field.split("-")[0]
    try:
        delay_seconds = float(first_delay) if first_delay.lower() != "p" else 0.0
    except ValueError:
        delay_seconds = 0.0

    # Make sure the curve starts at (0, 0) for clean integration.
    if samples[0][0] > 0:
        samples = [(0.0, 0.0), *samples]
    # And ends at zero thrust for a clean cutoff.
    if samples[-1][1] != 0:
        samples.append((samples[-1][0], 0.0))

    return Motor(
        designation=designation,
        name=f"{manufacturer} {designation}".strip(),
        diameter_m=diameter_mm / 1000.0,
        length_m=length_mm / 1000.0,
        propellant_mass_kg=propellant_mass_kg,
        total_mass_kg=total_mass_kg,
        thrust_curve=tuple(samples),
        delay_seconds=delay_seconds,
        manufacturer=manufacturer,
    )


def load_motor_file(path: Path | str) -> Motor:
    """Load a `.eng` motor file from disk and return the corresponding `Motor`."""
    return parse_eng_file(Path(path).read_text())


# ---------------------------------------------------------------------------
# Built-in motor presets
#
# Curves are simplified ~5-7 sample approximations consistent with
# Estes-published total impulse, average thrust, and burn time. Real
# manufacturer thrust traces are available at https://thrustcurve.org.
# ---------------------------------------------------------------------------


def _make(
    designation: str,
    *,
    diameter_mm: float,
    length_mm: float,
    propellant_g: float,
    total_g: float,
    curve: tuple[tuple[float, float], ...],
    delay_s: float,
    manufacturer: str = "Estes",
) -> Motor:
    return Motor(
        designation=designation,
        name=f"{manufacturer} {designation}",
        diameter_m=diameter_mm / 1000.0,
        length_m=length_mm / 1000.0,
        propellant_mass_kg=propellant_g / 1000.0,
        total_mass_kg=total_g / 1000.0,
        thrust_curve=curve,
        delay_seconds=delay_s,
        manufacturer=manufacturer,
    )


MOTORS: dict[str, Motor] = {
    "1/2A6-2": _make(
        "1/2A6-2",
        diameter_mm=13.0,
        length_mm=45.0,
        propellant_g=1.66,
        total_g=4.7,
        delay_s=2.0,
        # Total impulse ~1.25 N*s, peak ~7 N, burn ~0.32 s
        curve=(
            (0.0, 0.0),
            (0.04, 5.0),
            (0.08, 7.0),
            (0.13, 4.0),
            (0.20, 2.5),
            (0.32, 1.5),
            (0.32, 0.0),
        ),
    ),
    "A8-3": _make(
        "A8-3",
        diameter_mm=18.0,
        length_mm=70.0,
        propellant_g=3.12,
        total_g=16.4,
        delay_s=3.0,
        # Total impulse ~2.5 N*s, peak ~13 N, burn ~0.5 s
        curve=(
            (0.0, 0.0),
            (0.05, 9.0),
            (0.10, 13.0),
            (0.15, 6.0),
            (0.20, 4.5),
            (0.40, 3.0),
            (0.50, 0.0),
        ),
    ),
    "B6-4": _make(
        "B6-4",
        diameter_mm=18.0,
        length_mm=70.0,
        propellant_g=5.6,
        total_g=17.0,
        delay_s=4.0,
        # Total impulse ~5.0 N*s, peak ~12 N, burn ~0.86 s
        curve=(
            (0.0, 0.0),
            (0.05, 8.0),
            (0.10, 12.0),
            (0.20, 6.0),
            (0.40, 4.5),
            (0.86, 3.5),
            (0.86, 0.0),
        ),
    ),
    "C6-3": _make(
        "C6-3",
        diameter_mm=18.0,
        length_mm=70.0,
        propellant_g=12.5,
        total_g=24.0,
        delay_s=3.0,
        # Total impulse ~10.0 N*s, peak ~14 N, burn ~1.85 s
        curve=(
            (0.0, 0.0),
            (0.10, 9.0),
            (0.20, 14.0),
            (0.30, 8.0),
            (0.50, 5.5),
            (1.00, 5.0),
            (1.85, 4.0),
            (1.85, 0.0),
        ),
    ),
    "C6-5": _make(
        "C6-5",
        diameter_mm=18.0,
        length_mm=70.0,
        propellant_g=12.5,
        total_g=24.0,
        delay_s=5.0,
        # Same propellant/curve as C6-3, longer delay grain.
        curve=(
            (0.0, 0.0),
            (0.10, 9.0),
            (0.20, 14.0),
            (0.30, 8.0),
            (0.50, 5.5),
            (1.00, 5.0),
            (1.85, 4.0),
            (1.85, 0.0),
        ),
    ),
    "D12-5": _make(
        "D12-5",
        diameter_mm=24.0,
        length_mm=70.0,
        propellant_g=16.84,
        total_g=42.5,
        delay_s=5.0,
        # Total impulse ~16.84 N*s, peak ~30 N, burn ~1.6 s
        curve=(
            (0.0, 0.0),
            (0.10, 18.0),
            (0.20, 30.0),
            (0.30, 18.0),
            (0.50, 9.0),
            (1.00, 8.0),
            (1.60, 7.0),
            (1.60, 0.0),
        ),
    ),
    "E9-6": _make(
        "E9-6",
        diameter_mm=24.0,
        length_mm=95.0,
        propellant_g=35.5,
        total_g=57.0,
        delay_s=6.0,
        # Total impulse ~28.45 N*s, peak ~24 N, burn ~2.83 s
        curve=(
            (0.0, 0.0),
            (0.15, 14.0),
            (0.30, 24.0),
            (0.55, 13.0),
            (1.00, 10.0),
            (2.00, 9.0),
            (2.83, 8.0),
            (2.83, 0.0),
        ),
    ),
    "F15-6": _make(
        "F15-6",
        diameter_mm=29.0,
        length_mm=95.0,
        propellant_g=60.0,
        total_g=95.0,
        delay_s=6.0,
        manufacturer="Aerotech",
        # Total impulse ~50 N*s, peak ~30 N, burn ~3.45 s
        curve=(
            (0.0, 0.0),
            (0.10, 22.0),
            (0.30, 30.0),
            (0.60, 22.0),
            (1.50, 16.0),
            (2.50, 14.0),
            (3.45, 12.0),
            (3.45, 0.0),
        ),
    ),
}


def get_motor(designation: str) -> Motor:
    """
    Look up a built-in motor preset by designation (case-insensitive).

    Returns a copy via `dataclasses.replace` so that mutations do not
    leak into the global registry. Raises `KeyError` if the designation
    is not recognised, with the list of available motors.

    Examples:
        >>> motor = get_motor("c6-5")
        >>> motor.designation
        'C6-5'
    """
    if designation in MOTORS:
        return replace(MOTORS[designation])
    upper = designation.upper()
    for key in MOTORS:
        if key.upper() == upper:
            return replace(MOTORS[key])
    available = ", ".join(MOTORS.keys())
    raise KeyError(f"Unknown motor: {designation!r}. Available: {available}")


def list_motors() -> list[str]:
    """Return a list of all built-in motor designations."""
    return list(MOTORS.keys())
