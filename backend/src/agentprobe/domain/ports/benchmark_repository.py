"""Port interface for benchmark persistence."""

from abc import ABC, abstractmethod

from ..entities.benchmark import BenchmarkCase, BenchmarkResult, BenchmarkSuite


class IBenchmarkRepository(ABC):
    """Abstract interface for persisting benchmark data."""

    @abstractmethod
    async def save_case(self, case: BenchmarkCase) -> None:
        """Persist a benchmark case."""
        ...

    @abstractmethod
    async def get_case(self, case_id: str) -> BenchmarkCase | None:
        """Retrieve a benchmark case by ID."""
        ...

    @abstractmethod
    async def list_cases(
        self,
        *,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> list[BenchmarkCase]:
        """List benchmark cases with optional filters."""
        ...

    @abstractmethod
    async def save_suite(self, suite: BenchmarkSuite) -> None:
        """Persist a benchmark suite."""
        ...

    @abstractmethod
    async def get_suite(self, suite_id: str) -> BenchmarkSuite | None:
        """Retrieve a suite with its results."""
        ...

    @abstractmethod
    async def list_suites(self) -> list[BenchmarkSuite]:
        """List all benchmark suites."""
        ...

    @abstractmethod
    async def save_result(self, result: BenchmarkResult) -> None:
        """Persist a benchmark result."""
        ...

    @abstractmethod
    async def get_results_for_suite(
        self, suite_id: str
    ) -> list[BenchmarkResult]:
        """Get all results for a suite."""
        ...
