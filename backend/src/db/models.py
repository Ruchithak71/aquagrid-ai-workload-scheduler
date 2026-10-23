"""SQLAlchemy database models for persistence."""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text

from src.db.session import Base


class BenchmarkRunRecord(Base):
    """Stores full historical records of scheduler comparisons."""

    __tablename__ = "benchmark_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    name = Column(String(128), default="Benchmark Comparison", nullable=False)
    enforce_water_budget = Column(Boolean, default=True, nullable=False)
    total_jobs = Column(Integer, default=5, nullable=False)

    winner_carbon = Column(String(64), nullable=True)
    winner_water = Column(String(64), nullable=True)
    winner_cost = Column(String(64), nullable=True)

    fifo_carbon_kg = Column(Float, nullable=True)
    cpsat_carbon_kg = Column(Float, nullable=True)
    carbon_reduction_pct = Column(Float, nullable=True)
    water_violations_avoided_liters = Column(Float, nullable=True)

    report_json = Column(Text, nullable=False)
