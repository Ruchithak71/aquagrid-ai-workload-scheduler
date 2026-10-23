"""Historical benchmark runs persistence and retrieval routes."""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.db.models import BenchmarkRunRecord
from src.api.schemas import BenchmarkRunSummary, BenchmarkRunDetail

router = APIRouter(prefix="/history", tags=["History & Persistence"])


@router.get("", response_model=list[BenchmarkRunSummary])
def list_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[BenchmarkRunSummary]:
    """Retrieve a list of past benchmark comparison runs."""
    records = (
        db.query(BenchmarkRunRecord)
        .order_by(BenchmarkRunRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        BenchmarkRunSummary(
            id=r.id,
            created_at=r.created_at,
            name=r.name,
            enforce_water_budget=r.enforce_water_budget,
            total_jobs=r.total_jobs,
            winner_carbon=r.winner_carbon,
            winner_water=r.winner_water,
            winner_cost=r.winner_cost,
            fifo_carbon_kg=r.fifo_carbon_kg,
            cpsat_carbon_kg=r.cpsat_carbon_kg,
            carbon_reduction_pct=r.carbon_reduction_pct,
            water_violations_avoided_liters=r.water_violations_avoided_liters,
        )
        for r in records
    ]


@router.get("/{run_id}", response_model=BenchmarkRunDetail)
def get_history_detail(
    run_id: int,
    db: Session = Depends(get_db),
) -> BenchmarkRunDetail:
    """Retrieve full details of a specific past benchmark run, including full report JSON."""
    record = db.query(BenchmarkRunRecord).filter(BenchmarkRunRecord.id == run_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail=f"Benchmark run with ID {run_id} not found.")

    report_dict = json.loads(record.report_json)

    return BenchmarkRunDetail(
        id=record.id,
        created_at=record.created_at,
        name=record.name,
        enforce_water_budget=record.enforce_water_budget,
        total_jobs=record.total_jobs,
        winner_carbon=record.winner_carbon,
        winner_water=record.winner_water,
        winner_cost=record.winner_cost,
        fifo_carbon_kg=record.fifo_carbon_kg,
        cpsat_carbon_kg=record.cpsat_carbon_kg,
        carbon_reduction_pct=record.carbon_reduction_pct,
        water_violations_avoided_liters=record.water_violations_avoided_liters,
        report=report_dict,
    )


@router.delete("/{run_id}")
def delete_history_run(
    run_id: int,
    db: Session = Depends(get_db),
):
    """Delete a benchmark run record from history."""
    record = db.query(BenchmarkRunRecord).filter(BenchmarkRunRecord.id == run_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail=f"Benchmark run with ID {run_id} not found.")

    db.delete(record)
    db.commit()
    return {"message": f"Benchmark run {run_id} successfully deleted."}
