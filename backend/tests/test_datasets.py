"""Unit tests for the canonical benchmark datasets."""

import pytest

from src.simulation.datasets import (
    get_default_sites,
    get_default_environmental_profiles,
    get_default_workloads,
)


class TestDefaultSitesDataset:
    """Tests for the canonical data-centre sites."""

    def test_default_sites_count_and_uniqueness(self):
        sites = get_default_sites()
        assert len(sites) == 3

        ids = [s.id for s in sites] 
        assert len(ids) == len(set(ids))
        assert "phoenix-01" in ids
        assert "quincy-01" in ids
        assert "council-bluffs-01" in ids

    def test_sites_physical_attributes(self):
        sites = get_default_sites()
        for site in sites:
            assert site.gpu_capacity > 0
            assert site.base_pue >= 1.0
            assert site.pue_temp_slope >= 0.0
            assert site.base_wue >= 0.0
            assert site.daily_water_budget_liters > 0
            assert site.gpu_power_kw > 0.0


class TestDefaultEnvironmentalProfiles:
    """Tests for the 24-hour weather, carbon, and pricing profiles."""

    def test_profiles_match_sites(self):
        sites = get_default_sites()
        site_ids = {s.id for s in sites}
        profiles = get_default_environmental_profiles()

        assert set(profiles.keys()) == site_ids

    def test_each_profile_has_24_valid_hours(self):
        profiles = get_default_environmental_profiles()
        for site_id, profile in profiles.items():
            assert profile.site_id == site_id
            assert len(profile.hourly_conditions) == 24
            for h, condition in enumerate(profile.hourly_conditions):
                assert condition.hour == h
                assert condition.temperature_c > -50.0
                assert condition.carbon_intensity_g_per_kwh >= 0.0
                assert condition.electricity_price_per_kwh > 0.0
                assert condition.grid_water_intensity_l_per_kwh >= 0.0

    def test_phoenix_solar_and_heat_tradeoff(self):
        """Phoenix must model the carbon-water conflict: low carbon solar midday with peak desert heat."""
        profiles = get_default_environmental_profiles()
        phoenix = profiles["phoenix-01"]

        midday_condition = phoenix.get_hour(12)  # Noon
        night_condition = phoenix.get_hour(2)    # 2 AM

        # Midday solar makes carbon near-zero
        assert midday_condition.carbon_intensity_g_per_kwh <= 50.0
        # But temperature is blisteringly hot (> 40°C)
        assert midday_condition.temperature_c >= 40.0
        # Night carbon is much dirtier from gas peakers
        assert night_condition.carbon_intensity_g_per_kwh >= 350.0

    def test_quincy_hydro_profile(self):
        """Quincy WA has clean hydro power all day but high off-site EWIF."""
        profiles = get_default_environmental_profiles()
        quincy = profiles["quincy-01"]

        for h in range(24):
            cond = quincy.get_hour(h)
            assert cond.carbon_intensity_g_per_kwh <= 90.0  # Clean hydro
            assert cond.grid_water_intensity_l_per_kwh >= 4.0  # High reservoir evaporation

    def test_council_bluffs_wind_profile(self):
        """Iowa has strong night wind (clean night carbon) and dirty daytime peak."""
        profiles = get_default_environmental_profiles()
        cb = profiles["council-bluffs-01"]

        night_cond = cb.get_hour(2)   # 2 AM wind
        day_cond = cb.get_hour(13)    # 1 PM afternoon

        assert night_cond.carbon_intensity_g_per_kwh < day_cond.carbon_intensity_g_per_kwh


class TestDefaultWorkloadsDataset:
    """Tests for the canonical AI batch workloads."""

    def test_workloads_count_and_feasibility(self):
        workloads = get_default_workloads()
        assert len(workloads) == 5

        ids = [w.id for w in workloads]
        assert len(ids) == len(set(ids))

        for w in workloads:
            assert w.gpus_required >= 1
            assert w.duration_hours >= 1
            assert 1 <= w.priority <= 5
            # The deadline feasibility validator guaranteed deadline >= arrival + duration
            assert w.deadline_hour >= w.arrival_hour + w.duration_hours

    def test_preemptibility_diversity(self):
        """Ensure we have a realistic mix of preemptible and non-preemptible jobs."""
        workloads = get_default_workloads()
        preemptible_count = sum(1 for w in workloads if w.is_preemptible)
        non_preemptible_count = sum(1 for w in workloads if not w.is_preemptible)

        assert preemptible_count > 0
        assert non_preemptible_count > 0
