"""SQLAlchemy implementation of the benchmark repository port."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from agentprobe.domain.entities.benchmark import (
    BenchmarkCase,
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkResult,
    BenchmarkSuite,
)
from agentprobe.domain.ports.benchmark_repository import IBenchmarkRepository
from agentprobe.infrastructure.persistence.models.tables import (
    BenchmarkCaseModel,
    BenchmarkResultModel,
    BenchmarkSuiteModel,
)


class SQLAlchemyBenchmarkRepository(IBenchmarkRepository):
    """Concrete repository for benchmark persistence via SQLAlchemy.

    Args:
        session_factory: Factory that produces AsyncSession instances.
    """

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        self._session_factory = session_factory

    async def save_case(self, case: BenchmarkCase) -> None:
        """Persist a benchmark case (upsert).

        Args:
            case: The benchmark case domain entity.
        """
        async with self._session_factory() as session:
            async with session.begin():
                model = BenchmarkCaseModel(
                    id=case.id,
                    query=case.query,
                    category=case.category.value,
                    difficulty=case.difficulty.value,
                    expected_answer=case.expected_answer,
                    expected_tools=json.dumps(case.expected_tools),
                    is_builtin=case.is_builtin,
                )
                await session.merge(model)

    async def get_case(self, case_id: str) -> BenchmarkCase | None:
        """Retrieve a benchmark case by ID.

        Args:
            case_id: The unique case identifier.

        Returns:
            The domain entity, or None if not found.
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(BenchmarkCaseModel).where(
                    BenchmarkCaseModel.id == case_id
                )
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return self._case_to_domain(row)

    async def list_cases(
        self,
        *,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> list[BenchmarkCase]:
        """List benchmark cases with optional filters.

        Args:
            category: Filter by category value.
            difficulty: Filter by difficulty value.

        Returns:
            List of matching benchmark cases.
        """
        async with self._session_factory() as session:
            stmt = select(BenchmarkCaseModel)
            if category:
                stmt = stmt.where(BenchmarkCaseModel.category == category)
            if difficulty:
                stmt = stmt.where(BenchmarkCaseModel.difficulty == difficulty)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [self._case_to_domain(r) for r in rows]

    async def save_suite(self, suite: BenchmarkSuite) -> None:
        """Persist a benchmark suite (upsert).

        Args:
            suite: The benchmark suite domain entity.
        """
        async with self._session_factory() as session:
            async with session.begin():
                model = BenchmarkSuiteModel(
                    id=suite.id,
                    model_id=suite.model_id,
                    provider=suite.provider,
                    status=suite.status,
                    total_cases=suite.total_cases,
                    success_rate=suite.success_rate,
                    avg_steps=suite.avg_steps,
                    failure_summary=json.dumps(suite.failure_summary),
                )
                await session.merge(model)

    async def get_suite(self, suite_id: str) -> BenchmarkSuite | None:
        """Retrieve a suite with its results.

        Args:
            suite_id: The unique suite identifier.

        Returns:
            The domain entity with results, or None if not found.
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(BenchmarkSuiteModel)
                .where(BenchmarkSuiteModel.id == suite_id)
                .options(selectinload(BenchmarkSuiteModel.results))
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return self._suite_to_domain(row)

    async def list_suites(self) -> list[BenchmarkSuite]:
        """List all benchmark suites ordered by creation date.

        Returns:
            List of all suites without their individual results.
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(BenchmarkSuiteModel).order_by(
                    BenchmarkSuiteModel.created_at.desc()
                )
            )
            rows = result.scalars().all()
            return [self._suite_to_domain(r, load_results=False) for r in rows]

    async def save_result(self, result: BenchmarkResult) -> None:
        """Persist a benchmark result.

        Args:
            result: The benchmark result domain entity.
        """
        async with self._session_factory() as session:
            async with session.begin():
                model = BenchmarkResultModel(
                    suite_id=result.suite_id,
                    case_id=result.case_id,
                    run_id=result.run_id,
                    passed=result.passed,
                    score=result.score,
                    answer_correct=result.answer_correct,
                    tools_correct=result.tools_correct,
                    failures=json.dumps(result.failures),
                )
                session.add(model)

    async def get_results_for_suite(
        self, suite_id: str
    ) -> list[BenchmarkResult]:
        """Get all results for a given suite.

        Args:
            suite_id: The suite identifier.

        Returns:
            List of benchmark results for the suite.
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(BenchmarkResultModel).where(
                    BenchmarkResultModel.suite_id == suite_id
                )
            )
            rows = result.scalars().all()
            return [self._result_to_domain(r) for r in rows]

    @staticmethod
    def _case_to_domain(row: BenchmarkCaseModel) -> BenchmarkCase:
        """Convert a BenchmarkCaseModel to a domain entity.

        Args:
            row: The ORM model.

        Returns:
            The domain BenchmarkCase.
        """
        return BenchmarkCase(
            id=row.id,
            query=row.query,
            category=BenchmarkCategory(row.category),
            difficulty=BenchmarkDifficulty(row.difficulty),
            expected_answer=row.expected_answer,
            expected_tools=json.loads(row.expected_tools),
            is_builtin=row.is_builtin,
        )

    @staticmethod
    def _suite_to_domain(
        row: BenchmarkSuiteModel, *, load_results: bool = True
    ) -> BenchmarkSuite:
        """Convert a BenchmarkSuiteModel to a domain entity.

        Args:
            row: The ORM model.
            load_results: Whether to include results.

        Returns:
            The domain BenchmarkSuite.
        """
        results = []
        if load_results and row.results:
            results = [
                BenchmarkResult(
                    suite_id=r.suite_id,
                    case_id=r.case_id,
                    run_id=r.run_id,
                    passed=r.passed,
                    score=r.score,
                    answer_correct=r.answer_correct,
                    tools_correct=r.tools_correct,
                    failures=json.loads(r.failures),
                )
                for r in row.results
            ]

        return BenchmarkSuite(
            id=row.id,
            model_id=row.model_id,
            provider=row.provider,
            status=row.status,
            total_cases=row.total_cases,
            success_rate=row.success_rate,
            avg_steps=row.avg_steps,
            failure_summary=json.loads(row.failure_summary),
            results=results,
        )

    @staticmethod
    def _result_to_domain(row: BenchmarkResultModel) -> BenchmarkResult:
        """Convert a BenchmarkResultModel to a domain entity.

        Args:
            row: The ORM model.

        Returns:
            The domain BenchmarkResult.
        """
        return BenchmarkResult(
            suite_id=row.suite_id,
            case_id=row.case_id,
            run_id=row.run_id,
            passed=row.passed,
            score=row.score,
            answer_correct=row.answer_correct,
            tools_correct=row.tools_correct,
            failures=json.loads(row.failures),
        )
