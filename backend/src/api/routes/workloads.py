"""Workloads endpoint."""

from fastapi import APIRouter

from src.models import Workload
from src.simulation.datasets import get_default_workloads

router = APIRouter(prefix="/workloads", tags=["Workloads"])


@router.get("", response_model=list[Workload])
def list_canonical_workloads() -> list[Workload]:
    """Retrieve the 5 canonical benchmark AI workloads."""
    return get_default_workloads()
