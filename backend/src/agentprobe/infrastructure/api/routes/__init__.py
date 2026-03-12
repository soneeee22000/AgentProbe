"""API route modules."""

from .agent import router as agent_router
from .analytics import router as analytics_router
from .benchmarks import router as benchmarks_router
from .health import router as health_router
from .providers import router as providers_router
from .runs import router as runs_router
from .tools import router as tools_router

__all__ = [
    "agent_router",
    "analytics_router",
    "benchmarks_router",
    "health_router",
    "providers_router",
    "runs_router",
    "tools_router",
]
