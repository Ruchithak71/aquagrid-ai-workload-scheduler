"""Unit tests for the simulation calculation engine."""

import pytest

from src.models import (
    DatacenterSite,
    CoolingTechnology,
    HourlyEnvironmentalCondition,
)
from src.simulation.calculator import (
    calculate_hourly_pue,
    calculate_hourly_wue,
    calculate_indirect_water,
    calculate_carbon_emissions,
    calculate_electricity_cost,
    calculate_hourly_execution,
)


@pytest.fixture
def sample_site() -> DatacenterSite:
    """Fixture providing a standard test data-centre site."""
    return DatacenterSite(
        id="phoenix-test",
        name="Phoenix Desert Test Site",
        location="Phoenix, AZ",
        gpu_capacity=64,
        cooling_type=CoolingTechnology.EVAPORATIVE,
        base_pue=1.15,
        pue_temp_slope=0.01,
        base_wue=0.2,
        economizer_temp_c=18.0,
        wue_temp_slope=0.08,
        daily_water_budget_liters=2000.0,
        gpu_power_kw=0.7,
    )


class TestPUECalculations:
    """Tests for temperature-dependent PUE."""

    def test_pue_at_or_below_economizer_temp(self, sample_site: DatacenterSite):
        # Cool temperature: Free cooling active, PUE stays at baseline
        assert calculate_hourly_pue(sample_site, ambient_temp_c=10.0) == 1.15
        assert calculate_hourly_pue(sample_site, ambient_temp_c=18.0) == 1.15

    def test_pue_above_economizer_temp(self, sample_site: DatacenterSite):
        # 28°C is 10°C above threshold (18°C).
        # Expected: 1.15 + (0.01 * 10) = 1.25
        pue = calculate_hourly_pue(sample_site, ambient_temp_c=28.0)
        assert pytest.approx(pue, rel=1e-5) == 1.25

    def test_pue_high_desert_heat(self, sample_site: DatacenterSite):
        # 43°C is 25°C above threshold.
        # Expected: 1.15 + (0.01 * 25) = 1.40
        pue = calculate_hourly_pue(sample_site, ambient_temp_c=43.0)
        assert pytest.approx(pue, rel=1e-5) == 1.40


class TestWUECalculations:
    """Tests for direct cooling water usage effectiveness."""

    def test_wue_at_or_below_economizer_temp(self, sample_site: DatacenterSite):
        # Free cooling: minimal water consumption
        assert calculate_hourly_wue(sample_site, ambient_temp_c=12.0) == 0.2
        assert calculate_hourly_wue(sample_site, ambient_temp_c=18.0) == 0.2

    def test_wue_above_economizer_temp(self, sample_site: DatacenterSite):
        # 38°C is 20°C above threshold (18°C).
        # Expected: 0.2 + (0.08 * 20) = 0.2 + 1.6 = 1.8 L/kWh
        wue = calculate_hourly_wue(sample_site, ambient_temp_c=38.0)
        assert pytest.approx(wue, rel=1e-5) == 1.80


class TestEnvironmentalFormulas:
    """Tests for indirect water, carbon, and electricity cost."""

    def test_indirect_water(self):
        # 200 kWh * 1.5 L/kWh = 300 Litres
        assert calculate_indirect_water(total_energy_kwh=200.0, grid_water_intensity_l_per_kwh=1.5) == 300.0

    def test_carbon_emissions(self):
        # 100 kWh * 450 gCO2/kWh * 10^-3 = 45 kgCO2
        assert calculate_carbon_emissions(total_energy_kwh=100.0, carbon_intensity_g_per_kwh=450.0) == 45.0

    def test_electricity_cost(self):
        # 50 kWh * $0.12/kWh = $6.00
        assert calculate_electricity_cost(total_energy_kwh=50.0, electricity_price_per_kwh=0.12) == 6.0


class TestHourlyExecutionSlice:
    """End-to-end test for 1-hour job execution slice calculation."""

    def test_hourly_execution_calculation(self, sample_site: DatacenterSite):
        # Run 10 GPUs at 28°C
        condition = HourlyEnvironmentalCondition(
            hour=14,
            temperature_c=28.0,  # PUE = 1.25, WUE = 0.2 + 0.08*10 = 1.0 L/kWh
            carbon_intensity_g_per_kwh=200.0,
            electricity_price_per_kwh=0.10,
            grid_water_intensity_l_per_kwh=1.5,
        )

        exec_slice = calculate_hourly_execution(
            site=sample_site,
            workload_id="job-01",
            gpus_used=10,
            hour=14,
            condition=condition,
        )

        # 1. IT Energy: 10 GPUs * 0.7 kW * 1h = 7.0 kWh
        assert exec_slice.it_energy_kwh == 7.0

        # 2. Total Energy: 7.0 kWh * 1.25 PUE = 8.75 kWh
        assert exec_slice.total_energy_kwh == 8.75

        # 3. Direct Water: 7.0 kWh * 1.0 L/kWh = 7.0 Litres
        assert exec_slice.direct_water_liters == 7.0

        # 4. Indirect Water: 8.75 kWh * 1.5 L/kWh = 13.125 Litres
        assert exec_slice.indirect_water_liters == 13.125

        # 5. Carbon: 8.75 kWh * 200 g/kWh * 10^-3 = 1.75 kg
        assert exec_slice.carbon_kg == 1.75

        # 6. Cost: 8.75 kWh * $0.10/kWh = $0.875
        assert exec_slice.cost_usd == 0.875

    def test_negative_gpus_rejected(self, sample_site: DatacenterSite):
        condition = HourlyEnvironmentalCondition(
            hour=0,
            temperature_c=20.0,
            carbon_intensity_g_per_kwh=100.0,
            electricity_price_per_kwh=0.08,
            grid_water_intensity_l_per_kwh=1.0,
        )
        with pytest.raises(ValueError) as exc:
            calculate_hourly_execution(
                site=sample_site,
                workload_id="job-err",
                gpus_used=-5,
                hour=0,
                condition=condition,
            )
        assert "cannot be negative" in str(exc.value)
