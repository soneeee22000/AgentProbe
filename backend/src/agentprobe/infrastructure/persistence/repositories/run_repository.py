"""SQLAlchemy implementation of the run repository port."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from agentprobe.domain.entities import (
    AgentRun,
    AgentStep,
    FailureType,
    StepType,
)
from agentprobe.domain.ports.run_repository import IRunRepository
from agentprobe.infrastructure.persistence.models.tables import (
    FailureModel,
    RunModel,
    StepModel,
)


class SQLAlchemyRunRepository(IRunRepository):
    """Concrete repository that persists agent runs via SQLAlchemy.

    Converts between domain ``AgentRun`` entities and their ORM
    counterparts (``RunModel``, ``StepModel``, ``FailureModel``),
    providing full async CRUD operations.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialise with an async session factory.

        Args:
            session_factory: Factory that produces ``AsyncSession`` instances.
        """
        self._session_factory = session_factory

    async def save(self, run: AgentRun) -> None:
        """Persist a complete agent run with all its steps and failures.

        Converts the domain ``AgentRun`` into ORM models and merges them
        into the database, supporting both inserts and updates.

        Args:
            run: The domain entity to persist.
        """
        async with self._session_factory() as session:
            async with session.begin():
                run_model = RunModel(
                    id=run.run_id,
                    query=run.query,
                    model_id=run.model,
                    provider=run.provider,
                    status=run.status,
                    final_answer=run.final_answer,
                    total_tokens=run.total_tokens,
                    duration_ms=run.duration_ms,
                    succeeded=run.succeeded,
                    created_at=datetime.fromtimestamp(
                        run.start_time, tz=timezone.utc
                    ),
                )

                for step in run.steps:
                    step_model = StepModel(
                        run_id=run.run_id,
                        step_index=step.step_index,
                        step_type=step.step_type.value,
                        content=step.content,
                        tool_name=step.tool_name,
                        tool_args=step.tool_args,
                        failure_type=step.failure_type.value,
                        token_count=step.token_count,
                        latency_ms=step.latency_ms,
                        timestamp=step.timestamp,
                    )
                    run_model.steps.append(step_model)

                for idx, failure_type in enumerate(run.failures):
                    # Link failure to the step that caused it when possible.
                    step_id: int | None = None
                    for step in run.steps:
                        if step.failure_type == failure_type:
                            step_id = step.step_index
                            break

                    failure_model = FailureModel(
                        run_id=run.run_id,
                        step_id=step_id,
                        failure_type=failure_type.value,
                    )
                    run_model.failures.append(failure_model)

                await session.merge(run_model)

    async def get_by_id(self, run_id: str) -> AgentRun | None:
        """Retrieve a run by its ID, eagerly loading steps and failures.

        Args:
            run_id: Unique identifier of the run.

        Returns:
            The reconstructed ``AgentRun`` domain entity, or ``None``
            if no matching run exists.
        """
        async with self._session_factory() as session:
            stmt = (
                select(RunModel)
                .where(RunModel.id == run_id)
                .options(
                    selectinload(RunModel.steps),
                    selectinload(RunModel.failures),
                )
            )
            result = await session.execute(stmt)
            row: RunModel | None = result.scalar_one_or_none()

            if row is None:
                return None

            return self._to_domain(row)

    async def list_runs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        model: str | None = None,
        status: str | None = None,
    ) -> list[AgentRun]:
        """List runs with optional filters and pagination.

        Args:
            limit: Maximum number of runs to return.
            offset: Number of runs to skip for pagination.
            model: Filter by model identifier.
            status: Filter by run status.

        Returns:
            A list of ``AgentRun`` domain entities.
        """
        async with self._session_factory() as session:
            stmt = (
                select(RunModel)
                .options(
                    selectinload(RunModel.steps),
                    selectinload(RunModel.failures),
                )
                .order_by(RunModel.created_at.desc())
            )

            if model is not None:
                stmt = stmt.where(RunModel.model_id == model)
            if status is not None:
                stmt = stmt.where(RunModel.status == status)

            stmt = stmt.limit(limit).offset(offset)

            result = await session.execute(stmt)
            rows: list[RunModel] = list(result.scalars().all())

            return [self._to_domain(row) for row in rows]

    async def delete(self, run_id: str) -> bool:
        """Delete a run and cascade to its steps and failures.

        Args:
            run_id: Unique identifier of the run to delete.

        Returns:
            ``True`` if the run was found and deleted, ``False`` otherwise.
        """
        async with self._session_factory() as session:
            async with session.begin():
                stmt = (
                    select(RunModel)
                    .where(RunModel.id == run_id)
                    .options(
                        selectinload(RunModel.steps),
                        selectinload(RunModel.failures),
                    )
                )
                result = await session.execute(stmt)
                row: RunModel | None = result.scalar_one_or_none()

                if row is None:
                    return False

                await session.delete(row)
                return True

    async def count(
        self,
        *,
        model: str | None = None,
        status: str | None = None,
    ) -> int:
        """Count total runs matching the given filters.

        Args:
            model: Filter by model identifier.
            status: Filter by run status.

        Returns:
            The number of matching runs.
        """
        async with self._session_factory() as session:
            stmt = select(func.count(RunModel.id))

            if model is not None:
                stmt = stmt.where(RunModel.model_id == model)
            if status is not None:
                stmt = stmt.where(RunModel.status == status)

            result = await session.execute(stmt)
            return result.scalar_one()

    @staticmethod
    def _to_domain(row: RunModel) -> AgentRun:
        """Convert a ``RunModel`` ORM instance to a domain ``AgentRun``.

        Args:
            row: The ORM model loaded from the database.

        Returns:
            A fully reconstructed ``AgentRun`` domain entity.
        """
        steps = [
            AgentStep(
                step_type=StepType(s.step_type),
                content=s.content,
                step_index=s.step_index,
                timestamp=s.timestamp,
                tool_name=s.tool_name,
                tool_args=s.tool_args,
                failure_type=FailureType(s.failure_type),
                token_count=s.token_count,
                latency_ms=s.latency_ms,
            )
            for s in sorted(row.steps, key=lambda s: s.step_index)
        ]

        failures = [FailureType(f.failure_type) for f in row.failures]

        agent_run = AgentRun(
            query=row.query,
            run_id=row.id,
            model=row.model_id,
            provider=row.provider,
            steps=steps,
            start_time=row.created_at.replace(tzinfo=timezone.utc).timestamp(),
            final_answer=row.final_answer,
            failures=failures,
            total_tokens=row.total_tokens,
        )

        # Reconstruct end_time from duration_ms if available.
        if row.duration_ms is not None:
            agent_run.end_time = agent_run.start_time + (row.duration_ms / 1000)

        return agent_run
