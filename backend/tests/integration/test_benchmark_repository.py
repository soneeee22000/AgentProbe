"""Integration tests for the SQLAlchemy benchmark repository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agentprobe.domain.entities.benchmark import (
    BenchmarkCase,
    BenchmarkCategory,
    BenchmarkDifficulty,
    BenchmarkResult,
    BenchmarkSuite,
)
from agentprobe.infrastructure.persistence.repositories.benchmark_repository import (
    SQLAlchemyBenchmarkRepository,
)


@pytest.fixture
def bench_repo(
    db_session: async_sessionmaker[AsyncSession],
) -> SQLAlchemyBenchmarkRepository:
    """Create a benchmark repository with in-memory database."""
    return SQLAlchemyBenchmarkRepository(session_factory=db_session)


def _make_case(case_id: str = "math-001") -> BenchmarkCase:
    """Create a sample benchmark case."""
    return BenchmarkCase(
        id=case_id,
        query="What is 2+2?",
        category=BenchmarkCategory.MATH,
        difficulty=BenchmarkDifficulty.EASY,
        expected_answer="4",
        expected_tools=["calculator"],
    )


def _make_suite(suite_id: str = "suite-1") -> BenchmarkSuite:
    """Create a sample benchmark suite."""
    return BenchmarkSuite(
        id=suite_id,
        model_id="llama-3.1-8b",
        provider="groq",
        status="completed",
        total_cases=5,
        success_rate=0.8,
        avg_steps=3.5,
        failure_summary={"hallucinated_tool": 1},
    )


class TestBenchmarkCaseCRUD:
    """Tests for benchmark case persistence."""

    @pytest.mark.asyncio
    async def test_save_and_get_case(
        self, bench_repo: SQLAlchemyBenchmarkRepository
    ) -> None:
        """Save a case and retrieve it by ID."""
        case = _make_case()
        await bench_repo.save_case(case)

        loaded = await bench_repo.get_case("math-001")
        assert loaded is not None
        assert loaded.id == "math-001"
        assert loaded.query == "What is 2+2?"
        assert loaded.category == BenchmarkCategory.MATH
        assert loaded.expected_tools == ["calculator"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_case(
        self, bench_repo: SQLAlchemyBenchmarkRepository
    ) -> None:
        """Getting a non-existent case returns None."""
        loaded = await bench_repo.get_case("nonexistent")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_list_cases_all(
        self, bench_repo: SQLAlchemyBenchmarkRepository
    ) -> None:
        """List all cases without filters."""
        await bench_repo.save_case(_make_case("case-a"))
        await bench_repo.save_case(_make_case("case-b"))

        cases = await bench_repo.list_cases()
        assert len(cases) == 2

    @pytest.mark.asyncio
    async def test_list_cases_by_category(
        self, bench_repo: SQLAlchemyBenchmarkRepository
    ) -> None:
        """Filter cases by category."""
        math_case = _make_case("math-1")
        search_case = BenchmarkCase(
            id="search-1",
            query="Who is X?",
            category=BenchmarkCategory.SEARCH,
            difficulty=BenchmarkDifficulty.EASY,
            expected_answer="Y",
        )
        await bench_repo.save_case(math_case)
        await bench_repo.save_case(search_case)

        math_cases = await bench_repo.list_cases(category="math")
        assert len(math_cases) == 1
        assert math_cases[0].category == BenchmarkCategory.MATH

    @pytest.mark.asyncio
    async def test_upsert_case(
        self, bench_repo: SQLAlchemyBenchmarkRepository
    ) -> None:
        """Saving a case with existing ID should update it."""
        case = _make_case("upsert-1")
        await bench_repo.save_case(case)

        case.expected_answer = "updated"
        await bench_repo.save_case(case)

        loaded = await bench_repo.get_case("upsert-1")
        assert loaded is not None
        assert loaded.expected_answer == "updated"


class TestBenchmarkSuiteCRUD:
    """Tests for benchmark suite persistence."""

    @pytest.mark.asyncio
    async def test_save_and_get_suite(
        self, bench_repo: SQLAlchemyBenchmarkRepository
    ) -> None:
        """Save a suite and retrieve it with results."""
        suite = _make_suite()
        await bench_repo.save_suite(suite)

        loaded = await bench_repo.get_suite("suite-1")
        assert loaded is not None
        assert loaded.model_id == "llama-3.1-8b"
        assert loaded.success_rate == 0.8

    @pytest.mark.asyncio
    async def test_list_suites(
        self, bench_repo: SQLAlchemyBenchmarkRepository
    ) -> None:
        """List all suites."""
        await bench_repo.save_suite(_make_suite("s1"))
        await bench_repo.save_suite(_make_suite("s2"))

        suites = await bench_repo.list_suites()
        assert len(suites) == 2


class TestBenchmarkResultCRUD:
    """Tests for benchmark result persistence."""

    @pytest.mark.asyncio
    async def test_save_and_get_results(
        self, bench_repo: SQLAlchemyBenchmarkRepository,
        db_session: async_sessionmaker[AsyncSession],
    ) -> None:
        """Save results and retrieve by suite ID."""
        # Need a case and suite first due to foreign keys
        from agentprobe.domain.entities.run import AgentRun
        from agentprobe.infrastructure.persistence.repositories.run_repository import (
            SQLAlchemyRunRepository,
        )

        run_repo = SQLAlchemyRunRepository(session_factory=db_session)
        run = AgentRun(
            query="test", run_id="run-1", model="llama", provider="groq"
        )
        run.finish(final_answer="4")
        await run_repo.save(run)

        await bench_repo.save_case(_make_case("case-1"))
        await bench_repo.save_suite(_make_suite("suite-1"))

        result = BenchmarkResult(
            suite_id="suite-1",
            case_id="case-1",
            run_id="run-1",
            passed=True,
            score=0.85,
            answer_correct=True,
            tools_correct=True,
        )
        await bench_repo.save_result(result)

        results = await bench_repo.get_results_for_suite("suite-1")
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].score == 0.85
