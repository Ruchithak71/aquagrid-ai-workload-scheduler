"""API route packages."""

from src.api.routes.health import router as health_router
from src.api.routes.sites import router as sites_router
from src.api.routes.workloads import router as workloads_router
from src.api.routes.scheduling import router as scheduling_router

__all__ = [
    "health_router",
    "sites_router",
    "workloads_router",
    "scheduling_router",
]
