"""Integration tests for the SQLAlchemy run repository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agentprobe.domain.entities.run import AgentRun
from agentprobe.domain.entities.step import AgentStep, FailureType, StepType
from agentprobe.infrastructure.persistence.repositories.run_repository import (
    SQLAlchemyRunRepository,
)


@pytest.fixture
def repo(db_session: async_sessionmaker[AsyncSession]) -> SQLAlchemyRunRepository:
    """Create a repository with in-memory database."""
    return SQLAlchemyRunRepository(session_factory=db_session)


def _make_run(run_id: str = "test-1", query: str = "What is 2+2?") -> AgentRun:
    """Create a sample AgentRun for testing."""
    run = AgentRun(
        query=query,
        run_id=run_id,
        model="llama-3.1-8b-instant",
        provider="groq",
    )
    run.add_step(AgentStep(
        step_type=StepType.SYSTEM,
        content="Starting...",
        step_index=0,
    ))
    run.add_step(AgentStep(
        step_type=StepType.THOUGHT,
        content="I need to calculate",
        step_index=1,
        token_count=20,
        latency_ms=150.0,
    ))
    run.add_step(AgentStep(
        step_type=StepType.ACTION,
        content="calculator(2+2)",
        step_index=2,
        tool_name="calculator",
        tool_args="2+2",
    ))
    run.add_step(AgentStep(
        step_type=StepType.OBSERVATION,
        content="2+2 = 4",
        step_index=3,
    ))
    run.add_step(AgentStep(
        step_type=StepType.FINAL,
        content="The answer is 4.",
        step_index=4,
    ))
    run.finish(final_answer="The answer is 4.")
    return run


class TestSQLAlchemyRunRepository:
    """Integration tests for run persistence."""

    @pytest.mark.asyncio
    async def test_save_and_get_by_id(self, repo: SQLAlchemyRunRepository) -> None:
        """Save a run and retrieve it by ID."""
        run = _make_run()
        await repo.save(run)

        loaded = await repo.get_by_id("test-1")
        assert loaded is not None
        assert loaded.run_id == "test-1"
        assert loaded.query == "What is 2+2?"
        assert loaded.model == "llama-3.1-8b-instant"
        assert loaded.succeeded is True
        assert loaded.final_answer == "The answer is 4."
        assert len(loaded.steps) == 5

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(
        self, repo: SQLAlchemyRunRepository,
    ) -> None:
        """Getting a non-existent run should return None."""
        result = await repo.get_by_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_runs_returns_all(
        self, repo: SQLAlchemyRunRepository,
    ) -> None:
        """List should return all saved runs."""
        await repo.save(_make_run("run-a", "query A"))
        await repo.save(_make_run("run-b", "query B"))

        runs = await repo.list_runs()
        assert len(runs) == 2

    @pytest.mark.asyncio
    async def test_list_runs_with_limit(
        self, repo: SQLAlchemyRunRepository,
    ) -> None:
        """Limit should restrict result count."""
        await repo.save(_make_run("r1"))
        await repo.save(_make_run("r2"))
        await repo.save(_make_run("r3"))

        runs = await repo.list_runs(limit=2)
        assert len(runs) == 2

    @pytest.mark.asyncio
    async def test_delete_removes_run(
        self, repo: SQLAlchemyRunRepository,
    ) -> None:
        """Delete should remove run and return True."""
        await repo.save(_make_run("del-me"))
        deleted = await repo.delete("del-me")
        assert deleted is True

        loaded = await repo.get_by_id("del-me")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(
        self, repo: SQLAlchemyRunRepository,
    ) -> None:
        """Deleting non-existent run returns False."""
        deleted = await repo.delete("ghost")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_count(self, repo: SQLAlchemyRunRepository) -> None:
        """Count should match saved runs."""
        await repo.save(_make_run("c1"))
        await repo.save(_make_run("c2"))

        count = await repo.count()
        assert count == 2

    @pytest.mark.asyncio
    async def test_save_run_with_failures(
        self, repo: SQLAlchemyRunRepository,
    ) -> None:
        """Runs with failures should persist failure records."""
        run = AgentRun(
            query="bad query",
            run_id="fail-1",
            model="llama",
            provider="groq",
        )
        run.add_step(AgentStep(
            step_type=StepType.ERROR,
            content="hallucinated",
            step_index=0,
            failure_type=FailureType.HALLUCINATED_TOOL,
        ))
        run.finish()
        await repo.save(run)

        loaded = await repo.get_by_id("fail-1")
        assert loaded is not None
        assert FailureType.HALLUCINATED_TOOL in loaded.failures
