#!/usr/bin/env python3
"""
Physics Exploration Example

This example demonstrates the physics calculations available
in the rocket_sim library.
"""

from rocket_sim.physics import Physics


def main() -> None:
    print("=" * 60)
    print("  ROCKET SIMULATOR - Physics Exploration")
    print("=" * 60)

    # Earth properties
    print("\n1. EARTH PROPERTIES")
    print("-" * 40)
    print(f"   Mass: {Physics.EARTH.mass:.3e} kg")
    print(f"   Radius: {Physics.EARTH.radius:,.0f} m ({Physics.EARTH.radius/1000:.0f} km)")
    print(f"   Surface Gravity: {Physics.EARTH.surface_gravity:.4f} m/s^2")

    # Gravity at different altitudes
    print("\n2. GRAVITY AT DIFFERENT ALTITUDES")
    print("-" * 40)
    altitudes = [0, 10_000, 100_000, 400_000, 1_000_000]
    for alt in altitudes:
        g = Physics.gravity_at_altitude(alt)
        print(f"   {alt/1000:>7.0f} km: {g:.4f} m/s^2 ({g/9.81*100:.1f}% of surface)")

    # Escape velocities
    print("\n3. ESCAPE VELOCITY AT DIFFERENT ALTITUDES")
    print("-" * 40)
    for alt in altitudes:
        v = Physics.escape_velocity(alt)
        print(f"   {alt/1000:>7.0f} km: {v:,.0f} m/s ({v/1000:.2f} km/s)")

    # Orbital velocities
    print("\n4. ORBITAL VELOCITY AT DIFFERENT ALTITUDES")
    print("-" * 40)
    orbital_alts = [200_000, 400_000, 35_786_000]  # LEO, ISS, GEO
    orbit_names = ["Low Earth Orbit", "ISS Orbit", "Geostationary"]
    for alt, name in zip(orbital_alts, orbit_names, strict=False):
        v = Physics.orbital_velocity(alt)
        period = 2 * 3.14159 * (Physics.EARTH.radius + alt) / v
        print(f"   {name}: {v:,.0f} m/s, Period: {period/3600:.2f} hours")

    # Atmospheric density
    print("\n5. ATMOSPHERIC DENSITY")
    print("-" * 40)
    atm_alts = [0, 5_000, 10_000, 20_000, 50_000, 100_000]
    for alt in atm_alts:
        rho = Physics.atmospheric_density(alt)
        print(f"   {alt/1000:>6.0f} km: {rho:.6f} kg/m^3")

    # Comparison with Moon
    print("\n6. MOON COMPARISON")
    print("-" * 40)
    print(f"   Moon Mass: {Physics.MOON.mass:.3e} kg")
    print(f"   Moon Radius: {Physics.MOON.radius:,.0f} m")
    print(f"   Moon Surface Gravity: {Physics.MOON.surface_gravity:.4f} m/s^2")
    print(f"   Moon Escape Velocity: {Physics.escape_velocity(0, Physics.MOON):,.0f} m/s")

    earth_g = Physics.gravity_at_altitude(0, Physics.EARTH)
    moon_g = Physics.gravity_at_altitude(0, Physics.MOON)
    print(f"   Earth/Moon Gravity Ratio: {earth_g/moon_g:.2f}")


if __name__ == "__main__":
    main()
