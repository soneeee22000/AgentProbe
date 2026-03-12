"""Tests for ScoringEngine — answer matching, tool matching, edge cases."""

import pytest

from agentprobe.application.services.scoring import ScoringEngine
from agentprobe.domain.entities.benchmark import (
    BenchmarkCase,
    BenchmarkCategory,
    BenchmarkDifficulty,
)
from agentprobe.domain.entities.run import AgentRun
from agentprobe.domain.entities.step import AgentStep, FailureType, StepType


def _make_case(
    expected_answer: str = "42",
    expected_tools: list[str] | None = None,
) -> BenchmarkCase:
    """Create a benchmark case for testing."""
    return BenchmarkCase(
        id="test-001",
        query="What is the answer?",
        category=BenchmarkCategory.MATH,
        difficulty=BenchmarkDifficulty.EASY,
        expected_answer=expected_answer,
        expected_tools=expected_tools or [],
    )


def _make_run(
    final_answer: str | None = "42",
    tools_used: list[str] | None = None,
    step_count: int = 3,
    has_failures: bool = False,
) -> AgentRun:
    """Create a mock agent run for testing."""
    run = AgentRun(
        query="What is the answer?",
        run_id="test-run",
        model="test-model",
        provider="test",
    )

    for i in range(step_count):
        tool = tools_used[i] if tools_used and i < len(tools_used) else None
        failure = (
            FailureType.HALLUCINATED_TOOL
            if has_failures and i == 0
            else FailureType.NONE
        )
        step = AgentStep(
            step_type=StepType.ACTION if tool else StepType.THOUGHT,
            content=f"Step {i}",
            step_index=i,
            tool_name=tool,
            failure_type=failure,
        )
        run.add_step(step)

    if final_answer:
        final = AgentStep(
            step_type=StepType.FINAL,
            content=final_answer,
            step_index=step_count,
        )
        run.add_step(final)
        run.finish(final_answer=final_answer)
    else:
        run.finish()

    return run


class TestScoringEngine:
    """Tests for the ScoringEngine."""

    def setup_method(self) -> None:
        """Create scoring engine for each test."""
        self.scorer = ScoringEngine()

    def test_exact_answer_match(self) -> None:
        """Exact match should give perfect answer score."""
        case = _make_case(expected_answer="42")
        run = _make_run(final_answer="42")
        result = self.scorer.score_run(case, run)
        assert result.answer_correct is True
        assert result.passed is True

    def test_case_insensitive_match(self) -> None:
        """Answer matching should be case-insensitive."""
        case = _make_case(expected_answer="Paris")
        run = _make_run(final_answer="paris")
        result = self.scorer.score_run(case, run)
        assert result.answer_correct is True

    def test_answer_contained_in_response(self) -> None:
        """Expected answer contained in actual should score high."""
        case = _make_case(expected_answer="Paris")
        run = _make_run(
            final_answer="The capital of France is Paris."
        )
        result = self.scorer.score_run(case, run)
        assert result.answer_correct is True

    def test_wrong_answer(self) -> None:
        """Completely wrong answer should fail."""
        case = _make_case(expected_answer="42")
        run = _make_run(final_answer="banana")
        result = self.scorer.score_run(case, run)
        assert result.answer_correct is False

    def test_empty_answer(self) -> None:
        """No final answer should fail."""
        case = _make_case(expected_answer="42")
        run = _make_run(final_answer=None)
        result = self.scorer.score_run(case, run)
        assert result.answer_correct is False

    def test_keyword_overlap(self) -> None:
        """Partial keyword overlap should score proportionally."""
        case = _make_case(expected_answer="Mount Everest")
        run = _make_run(final_answer="Everest is the tallest")
        result = self.scorer.score_run(case, run)
        assert result.answer_correct is True

    def test_tool_matching_perfect(self) -> None:
        """Perfect tool match should score 1.0."""
        case = _make_case(expected_tools=["calculator"])
        run = _make_run(tools_used=["calculator"])
        result = self.scorer.score_run(case, run)
        assert result.tools_correct is True

    def test_tool_matching_jaccard(self) -> None:
        """Partial tool overlap should use Jaccard similarity."""
        score = ScoringEngine._check_tools(
            ["calculator", "web_search"], ["calculator"]
        )
        assert score == pytest.approx(0.5)

    def test_no_expected_tools(self) -> None:
        """No expected tools should score 1.0 if none used."""
        score = ScoringEngine._check_tools([], [])
        assert score == 1.0

    def test_efficiency_few_steps(self) -> None:
        """Three or fewer steps should get perfect efficiency."""
        score = ScoringEngine._check_efficiency(3)
        assert score == 1.0

    def test_efficiency_many_steps(self) -> None:
        """Many steps should decay efficiency."""
        score = ScoringEngine._check_efficiency(10)
        assert score < 1.0
        assert score >= 0.0

    def test_reliability_no_failures(self) -> None:
        """No failures should give perfect reliability."""
        run = _make_run(has_failures=False)
        score = ScoringEngine._check_reliability(run)
        assert score == 1.0

    def test_reliability_with_failures(self) -> None:
        """Any failures should give zero reliability."""
        run = _make_run(has_failures=True)
        score = ScoringEngine._check_reliability(run)
        assert score == 0.0

    def test_composite_score_range(self) -> None:
        """Composite score should be between 0 and 1."""
        case = _make_case()
        run = _make_run()
        result = self.scorer.score_run(case, run)
        assert 0.0 <= result.score <= 1.0

    def test_result_has_correct_ids(self) -> None:
        """Result should have correct case and run IDs."""
        case = _make_case()
        run = _make_run()
        result = self.scorer.score_run(case, run)
        assert result.case_id == "test-001"
        assert result.run_id == "test-run"
