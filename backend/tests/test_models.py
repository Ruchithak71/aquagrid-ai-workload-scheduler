"""Unit tests for AquaGrid domain models and Pydantic validation."""

import pytest
from pydantic import ValidationError

from src.models import (
    DatacenterSite,
    CoolingTechnology,
    Workload,
    HourlyEnvironmentalCondition,
    SiteEnvironmentalProfile,
    ScheduleMetrics,
    ScheduleResult,
)


class TestDatacenterSiteModel:
    """Tests for the DatacenterSite domain model."""

    def test_valid_site_creation(self):
        site = DatacenterSite(
            id="phoenix-01",
            name="Phoenix Supercluster",
            location="Phoenix, AZ",
            gpu_capacity=128,
            cooling_type=CoolingTechnology.EVAPORATIVE,
            base_pue=1.15,
            base_wue=0.2,
            economizer_temp_c=18.0,
            wue_temp_slope=0.08,
            daily_water_budget_liters=5000.0,
            gpu_power_kw=0.7,
        )
        assert site.id == "phoenix-01"
        assert site.gpu_capacity == 128
        assert site.cooling_type == CoolingTechnology.EVAPORATIVE

    def test_invalid_gpu_capacity_zero_or_negative(self):
        with pytest.raises(ValidationError) as exc:
            DatacenterSite(
                id="site-bad",
                name="Bad Site",
                location="Nowhere",
                gpu_capacity=0,  # Must be > 0
                daily_water_budget_liters=1000.0,
            )
        assert "greater than 0" in str(exc.value)

    def test_invalid_base_pue_below_one(self):
        with pytest.raises(ValidationError) as exc:
            DatacenterSite(
                id="site-bad-pue",
                name="Bad PUE Site",
                location="Nowhere",
                gpu_capacity=10,
                base_pue=0.9,  # PUE cannot physically be < 1.0
                daily_water_budget_liters=1000.0,
            )
        assert "greater than or equal to 1" in str(exc.value)


class TestWorkloadModel:
    """Tests for the Workload domain model."""

    def test_valid_workload_creation(self):
        job = Workload(
            id="job-001",
            name="LLM Pre-training Batch",
            arrival_hour=8,
            duration_hours=4,
            gpus_required=32,
            deadline_hour=16,
            priority=4,
            is_preemptible=True,
        )
        assert job.id == "job-001"
        assert job.is_preemptible is True
        assert job.duration_hours == 4

    def test_impossible_deadline_raises_validation_error(self):
        """If a 4-hour job arrives at hour 8, deadline at hour 10 is impossible!"""
        with pytest.raises(ValidationError) as exc:
            Workload(
                id="job-impossible",
                name="Impossible Job",
                arrival_hour=8,
                duration_hours=4,
                gpus_required=16,
                deadline_hour=10,  # Needs until at least 8 + 4 = 12!
            )
        assert "impossible" in str(exc.value)
        assert "earliest finish hour is 12" in str(exc.value)

    def test_invalid_priority_range(self):
        with pytest.raises(ValidationError):
            Workload(
                id="job-bad-priority",
                name="Bad Priority",
                arrival_hour=0,
                duration_hours=2,
                gpus_required=4,
                deadline_hour=5,
                priority=10,  # Must be between 1 and 5
            )


class TestEnvironmentalProfileModel:
    """Tests for hourly weather and carbon profiles."""

    def test_valid_24_hour_profile(self):
        conditions = [
            HourlyEnvironmentalCondition(
                hour=h,
                temperature_c=25.0 + h * 0.5,
                carbon_intensity_g_per_kwh=300.0,
                electricity_price_per_kwh=0.12,
                grid_water_intensity_l_per_kwh=1.2,
            )
            for h in range(24)
        ]
        profile = SiteEnvironmentalProfile(
            site_id="phoenix-01",
            hourly_conditions=conditions,
        )
        assert len(profile.hourly_conditions) == 24
        assert profile.get_hour(12).hour == 12

    def test_incomplete_profile_raises_error(self):
        """Profiles with fewer than 24 hours must be rejected."""
        short_conditions = [
            HourlyEnvironmentalCondition(
                hour=h,
                temperature_c=20.0,
                carbon_intensity_g_per_kwh=200.0,
                electricity_price_per_kwh=0.10,
            )
            for h in range(12)  # Only 12 hours!
        ]
        with pytest.raises(ValidationError) as exc:
            SiteEnvironmentalProfile(
                site_id="short-site",
                hourly_conditions=short_conditions,
            )
        assert "exactly 24 hours" in str(exc.value)


class TestScheduleResultModel:
    """Tests for ScheduleResult and Metrics structures."""

    def test_schedule_result_instantiation(self):
        metrics = ScheduleMetrics(
            total_it_energy_kwh=100.0,
            total_facility_energy_kwh=120.0,
            total_direct_water_liters=240.0,
            total_indirect_water_liters=180.0,
            total_water_liters=420.0,
            total_carbon_kg=36.0,
            total_cost_usd=14.4,
            jobs_scheduled=5,
            jobs_unscheduled=0,
            deadline_violations=0,
            water_budget_violations_liters=0.0,
        )
        res = ScheduleResult(
            scheduler_name="AquaGrid_Optimizer",
            status="OPTIMAL",
            metrics=metrics,
            solve_time_seconds=0.45,
            notes="All jobs scheduled within water budget.",
        )
        assert res.status == "OPTIMAL"
        assert res.metrics.jobs_scheduled == 5
