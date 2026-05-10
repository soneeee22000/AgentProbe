"""Seed demo runs for the in-person demo.

Inserts two hand-crafted runs into the database:

1. A successful multi-step ReAct trace (calculator + final answer).
2. A failed trace that triggers ``hallucinated_tool`` and ``goal_drift``
   — the most demo-friendly failure modes.

Idempotent: deletes runs with the same fixed IDs first, then inserts fresh.

Usage:
    cd backend
    python -m scripts.seed_demo_runs
"""

from __future__ import annotations

import asyncio
import os
import time

from sqlalchemy.ext.asyncio import AsyncEngine

from agentprobe.domain.entities import AgentRun, AgentStep, FailureType, StepType
from agentprobe.infrastructure.persistence.models import (
    DEFAULT_DATABASE_URL,
    get_engine,
    get_session_factory,
)
from agentprobe.infrastructure.persistence.models.tables import Base
from agentprobe.infrastructure.persistence.repositories.run_repository import (
    SQLAlchemyRunRepository,
)


HAPPY_RUN_ID = "demo-happy-001"
FAIL_RUN_ID = "demo-fail-001"


def build_happy_run() -> AgentRun:
    """A clean ReAct success path: thought -> action(calculator) -> obs -> final."""
    now = time.time() - 600  # 10 minutes ago for stable ordering
    run = AgentRun(
        query="What is 17 percent of 4280?",
        run_id=HAPPY_RUN_ID,
        model="llama-3.3-70b-versatile",
        provider="groq",
        start_time=now,
    )

    run.add_step(
        AgentStep(
            step_type=StepType.THOUGHT,
            content=(
                "The user asked for 17% of 4280. I should compute 0.17 * 4280 "
                "using the calculator tool to avoid arithmetic mistakes."
            ),
            step_index=0,
            timestamp=now,
            token_count=42,
            latency_ms=312.0,
        )
    )
    run.add_step(
        AgentStep(
            step_type=StepType.ACTION,
            content="calculator",
            step_index=1,
            timestamp=now + 0.4,
            tool_name="calculator",
            tool_args="0.17 * 4280",
            token_count=18,
            latency_ms=145.0,
        )
    )
    run.add_step(
        AgentStep(
            step_type=StepType.OBSERVATION,
            content="727.6",
            step_index=2,
            timestamp=now + 0.6,
            token_count=4,
            latency_ms=12.0,
        )
    )
    run.add_step(
        AgentStep(
            step_type=StepType.THOUGHT,
            content=(
                "The calculator returned 727.6. That's the answer to the user's "
                "question. I should produce a final answer now."
            ),
            step_index=3,
            timestamp=now + 1.1,
            token_count=38,
            latency_ms=287.0,
        )
    )
    run.add_step(
        AgentStep(
            step_type=StepType.FINAL,
            content="17% of 4280 is 727.6.",
            step_index=4,
            timestamp=now + 1.4,
            token_count=12,
            latency_ms=198.0,
        )
    )

    run.finish(final_answer="17% of 4280 is 727.6.")
    run.end_time = now + 1.4
    run.total_tokens = 114
    return run


def build_failure_run() -> AgentRun:
    """A failure trace: hallucinated tool + goal drift in one run.

    The agent invents a `weather_forecast` tool that doesn't exist, retries with
    the wrong intent, then produces a final answer that doesn't match the query.
    """
    now = time.time() - 300  # 5 minutes ago
    run = AgentRun(
        query="What is the population of Lyon, France?",
        run_id=FAIL_RUN_ID,
        model="llama-3.1-8b-instant",
        provider="groq",
        start_time=now,
    )

    run.add_step(
        AgentStep(
            step_type=StepType.THOUGHT,
            content=(
                "The user wants the population of Lyon. I'll search the web to "
                "find an authoritative figure."
            ),
            step_index=0,
            timestamp=now,
            token_count=34,
            latency_ms=298.0,
        )
    )
    # Hallucinated tool — agent invents a tool name that isn't in the registry.
    run.add_step(
        AgentStep(
            step_type=StepType.ACTION,
            content="weather_forecast",
            step_index=1,
            timestamp=now + 0.3,
            tool_name="weather_forecast",
            tool_args='{"city": "Lyon"}',
            failure_type=FailureType.HALLUCINATED_TOOL,
            token_count=22,
            latency_ms=156.0,
        )
    )
    run.add_step(
        AgentStep(
            step_type=StepType.OBSERVATION,
            content=(
                "[ERROR] Tool 'weather_forecast' is not registered. "
                "Available tools: calculator, web_search, think, read_file, "
                "save_memory, recall_memory."
            ),
            step_index=2,
            timestamp=now + 0.4,
            token_count=42,
            latency_ms=8.0,
        )
    )
    run.add_step(
        AgentStep(
            step_type=StepType.THOUGHT,
            content=(
                "The weather tool isn't available. Let me try web_search instead, "
                "but I'll search for Lyon weather since that's interesting context."
            ),
            step_index=3,
            timestamp=now + 0.9,
            token_count=38,
            latency_ms=312.0,
        )
    )
    run.add_step(
        AgentStep(
            step_type=StepType.ACTION,
            content="web_search",
            step_index=4,
            timestamp=now + 1.2,
            tool_name="web_search",
            tool_args='{"query": "Lyon France weather forecast today"}',
            token_count=28,
            latency_ms=178.0,
        )
    )
    run.add_step(
        AgentStep(
            step_type=StepType.OBSERVATION,
            content=(
                "Lyon weather: 18°C, partly cloudy. Forecast for the week shows "
                "mild temperatures with light rain expected on Thursday."
            ),
            step_index=5,
            timestamp=now + 2.4,
            token_count=46,
            latency_ms=1124.0,
        )
    )
    # Goal drift — final answer is about weather, not population.
    run.add_step(
        AgentStep(
            step_type=StepType.FINAL,
            content=(
                "Lyon currently has mild weather at 18°C with partly cloudy skies. "
                "Light rain is expected on Thursday."
            ),
            step_index=6,
            timestamp=now + 2.8,
            failure_type=FailureType.GOAL_DRIFT,
            token_count=32,
            latency_ms=287.0,
        )
    )

    run.finish(
        final_answer=(
            "Lyon currently has mild weather at 18°C with partly cloudy skies. "
            "Light rain is expected on Thursday."
        )
    )
    run.end_time = now + 2.8
    run.total_tokens = 242
    return run


async def _ensure_schema(engine: AsyncEngine) -> None:
    """Create all tables if they don't already exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed() -> None:
    """Insert (or refresh) the two demo runs."""
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    engine = get_engine(database_url)
    session_factory = get_session_factory(engine)
    repo = SQLAlchemyRunRepository(session_factory)

    await _ensure_schema(engine)

    # Idempotent: wipe the previous demo rows if they exist.
    await repo.delete(HAPPY_RUN_ID)
    await repo.delete(FAIL_RUN_ID)

    happy = build_happy_run()
    fail = build_failure_run()
    await repo.save(happy)
    await repo.save(fail)

    await engine.dispose()

    print(f"Seeded demo runs into {database_url}")
    print(f"  - {HAPPY_RUN_ID}  (success: calculator path)")
    print(f"  - {FAIL_RUN_ID}   (failures: hallucinated_tool + goal_drift)")
    print()
    print("Open these URLs to see the decision graph:")
    print(f"  http://localhost:3000/runs/{HAPPY_RUN_ID}")
    print(f"  http://localhost:3000/runs/{FAIL_RUN_ID}")


if __name__ == "__main__":
    asyncio.run(seed())
