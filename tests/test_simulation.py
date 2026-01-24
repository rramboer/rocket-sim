"""
Tests for the simulation engine.
"""

from rocket_sim.config import SimulationConfig
from rocket_sim.models import RocketConfig
from rocket_sim.simulation import (
    RocketSimulation,
    SimulationResult,
    SimulationState,
    simulate_multiple,
    simulate_rocket,
)


class TestSimulationState:
    """Tests for SimulationState dataclass."""

    def test_state_creation(self) -> None:
        """Test state creation."""
        state = SimulationState(
            time=1.0,
            altitude=100.0,
            velocity=50.0,
            acceleration=10.0,
            is_burning=True,
        )
        assert state.time == 1.0
        assert state.altitude == 100.0
        assert state.velocity == 50.0
        assert state.is_burning

    def test_to_tuple(self) -> None:
        """Test conversion to tuple."""
        state = SimulationState(time=1.0, altitude=100.0, velocity=50.0)
        t = state.to_tuple()
        assert t == (1.0, 100.0, 50.0)


class TestSimulationResult:
    """Tests for SimulationResult dataclass."""

    def test_result_creation(self, simple_config: RocketConfig) -> None:
        """Test result creation."""
        result = SimulationResult(
            rocket_name="Test",
            config=simple_config,
        )
        assert result.rocket_name == "Test"
        assert result.max_altitude == 0
        assert not result.escaped

    def test_time_data_extraction(self, simple_config: RocketConfig) -> None:
        """Test extraction of time data from states."""
        result = SimulationResult(
            rocket_name="Test",
            config=simple_config,
            states=[
                SimulationState(time=0, altitude=0, velocity=0),
                SimulationState(time=1, altitude=100, velocity=50),
                SimulationState(time=2, altitude=150, velocity=25),
            ],
        )
        assert result.time_data == [0, 1, 2]

    def test_altitude_data_extraction(self, simple_config: RocketConfig) -> None:
        """Test extraction of altitude data from states."""
        result = SimulationResult(
            rocket_name="Test",
            config=simple_config,
            states=[
                SimulationState(time=0, altitude=0, velocity=0),
                SimulationState(time=1, altitude=100, velocity=50),
                SimulationState(time=2, altitude=150, velocity=25),
            ],
        )
        assert result.altitude_data == [0, 100, 150]

    def test_max_altitude_km(self, simple_config: RocketConfig) -> None:
        """Test max altitude in km conversion."""
        result = SimulationResult(
            rocket_name="Test",
            config=simple_config,
            max_altitude=100_000,
        )
        assert result.max_altitude_km == 100.0

    def test_summary(self, simple_config: RocketConfig) -> None:
        """Test summary generation."""
        result = SimulationResult(
            rocket_name="Test Rocket",
            config=simple_config,
            max_altitude=50_000,
            max_velocity=500,
            flight_time=100,
        )
        summary = result.summary()
        assert "Test Rocket" in summary
        assert "50.00 km" in summary


class TestRocketSimulation:
    """Tests for RocketSimulation class."""

    def test_simulation_creation(
        self, simple_config: RocketConfig, sim_config: SimulationConfig
    ) -> None:
        """Test simulation creation."""
        sim = RocketSimulation(simple_config, sim_config)
        assert sim.rocket_config == simple_config
        assert sim.sim_config == sim_config

    def test_simulation_reset(
        self, simple_config: RocketConfig, sim_config: SimulationConfig
    ) -> None:
        """Test simulation reset."""
        sim = RocketSimulation(simple_config, sim_config)

        # Advance simulation
        for _ in range(10):
            sim.step()

        assert sim.rocket.time > 0

        sim.reset()
        assert sim.rocket.time == 0
        assert sim.rocket.altitude == 0

    def test_simulation_step(
        self, simple_config: RocketConfig, sim_config: SimulationConfig
    ) -> None:
        """Test single simulation step."""
        sim = RocketSimulation(simple_config, sim_config)
        state = sim.step()

        assert isinstance(state, SimulationState)
        assert state.time > 0

    def test_simulation_run(
        self, simple_config: RocketConfig, fast_sim_config: SimulationConfig
    ) -> None:
        """Test complete simulation run."""
        sim = RocketSimulation(simple_config, fast_sim_config)
        result = sim.run()

        assert isinstance(result, SimulationResult)
        assert result.rocket_name == simple_config.name
        assert len(result.states) > 1
        assert result.max_altitude > 0
        assert result.flight_time > 0

    def test_simulation_landing_detection(
        self, simple_config: RocketConfig, fast_sim_config: SimulationConfig
    ) -> None:
        """Test that simulation detects landing."""
        sim = RocketSimulation(simple_config, fast_sim_config)
        result = sim.run()

        # Rocket should land (not escape)
        assert not result.escaped
        assert result.landing_time is not None
        assert result.landing_time > 0

    def test_simulation_generator(
        self, simple_config: RocketConfig, fast_sim_config: SimulationConfig
    ) -> None:
        """Test generator-based simulation."""
        sim = RocketSimulation(simple_config, fast_sim_config)

        states = list(sim.run_generator())
        assert len(states) > 1
        assert all(isinstance(s, SimulationState) for s in states)


class TestConvenienceFunctions:
    """Tests for convenience simulation functions."""

    def test_simulate_rocket(
        self, simple_config: RocketConfig, fast_sim_config: SimulationConfig
    ) -> None:
        """Test simulate_rocket function."""
        result = simulate_rocket(simple_config, fast_sim_config)

        assert isinstance(result, SimulationResult)
        assert result.rocket_name == simple_config.name

    def test_simulate_multiple(self, fast_sim_config: SimulationConfig) -> None:
        """Test simulate_multiple function."""
        configs = [
            RocketConfig(mass=1000, thrust=20000, burn_time=30, name="Rocket 1"),
            RocketConfig(mass=2000, thrust=40000, burn_time=30, name="Rocket 2"),
        ]

        results = simulate_multiple(configs, fast_sim_config)

        assert len(results) == 2
        assert results[0].rocket_name == "Rocket 1"
        assert results[1].rocket_name == "Rocket 2"
