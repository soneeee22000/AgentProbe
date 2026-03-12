"""Domain entities for benchmarking system."""

from dataclasses import dataclass, field
from enum import Enum


class BenchmarkCategory(str, Enum):
    """Categories for benchmark test cases."""

    MATH = "math"
    SEARCH = "search"
    REASONING = "reasoning"
    MULTI_TOOL = "multi_tool"
    EDGE_CASES = "edge_cases"


class BenchmarkDifficulty(str, Enum):
    """Difficulty levels for benchmark cases."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class BenchmarkCase:
    """A single benchmark test case."""

    id: str
    query: str
    category: BenchmarkCategory
    difficulty: BenchmarkDifficulty
    expected_answer: str
    expected_tools: list[str] = field(default_factory=list)
    is_builtin: bool = True

    def to_dict(self) -> dict:
        """Serialize for API responses."""
        return {
            "id": self.id,
            "query": self.query,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "expected_answer": self.expected_answer,
            "expected_tools": self.expected_tools,
            "is_builtin": self.is_builtin,
        }


@dataclass
class BenchmarkResult:
    """Result of running a single benchmark case."""

    suite_id: str
    case_id: str
    run_id: str
    passed: bool
    score: float = 0.0
    answer_correct: bool = False
    tools_correct: bool = False
    failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for API responses."""
        return {
            "suite_id": self.suite_id,
            "case_id": self.case_id,
            "run_id": self.run_id,
            "passed": self.passed,
            "score": self.score,
            "answer_correct": self.answer_correct,
            "tools_correct": self.tools_correct,
            "failures": self.failures,
        }


@dataclass
class BenchmarkSuite:
    """A collection of benchmark results for a model."""

    id: str
    model_id: str
    provider: str
    status: str = "pending"
    total_cases: int = 0
    results: list[BenchmarkResult] = field(default_factory=list)
    success_rate: float = 0.0
    avg_steps: float = 0.0
    failure_summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize for API responses."""
        return {
            "id": self.id,
            "model_id": self.model_id,
            "provider": self.provider,
            "status": self.status,
            "total_cases": self.total_cases,
            "success_rate": self.success_rate,
            "avg_steps": self.avg_steps,
            "failure_summary": self.failure_summary,
        }
