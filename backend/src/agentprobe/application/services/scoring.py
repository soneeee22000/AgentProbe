"""ScoringEngine — composite scoring for benchmark evaluation."""

from agentprobe.domain.entities.benchmark import BenchmarkCase, BenchmarkResult
from agentprobe.domain.entities.run import AgentRun

# Scoring weights
WEIGHT_ANSWER = 0.4
WEIGHT_TOOLS = 0.2
WEIGHT_EFFICIENCY = 0.2
WEIGHT_RELIABILITY = 0.2

# Step count threshold for perfect efficiency score
EFFICIENT_STEP_THRESHOLD = 3


class ScoringEngine:
    """Scores agent runs against benchmark cases using composite metrics."""

    def score_run(
        self, case: BenchmarkCase, run: AgentRun
    ) -> BenchmarkResult:
        """Score a completed run against a benchmark case.

        Args:
            case: The benchmark case with expected answer/tools.
            run: The completed agent run to evaluate.

        Returns:
            A BenchmarkResult with pass/fail and detailed scores.
        """
        answer_score = self._check_answer(
            case.expected_answer, run.final_answer or ""
        )
        tools_score = self._check_tools(
            case.expected_tools, self._extract_tools(run)
        )
        efficiency_score = self._check_efficiency(len(run.steps))
        reliability_score = self._check_reliability(run)

        composite = (
            WEIGHT_ANSWER * answer_score
            + WEIGHT_TOOLS * tools_score
            + WEIGHT_EFFICIENCY * efficiency_score
            + WEIGHT_RELIABILITY * reliability_score
        )

        passed = answer_score >= 0.5 and composite >= 0.5
        failures = [f.value for f in run.failures]

        return BenchmarkResult(
            suite_id="",
            case_id=case.id,
            run_id=run.run_id,
            passed=passed,
            score=round(composite, 3),
            answer_correct=answer_score >= 0.5,
            tools_correct=tools_score >= 0.5,
            failures=failures,
        )

    @staticmethod
    def _check_answer(expected: str, actual: str) -> float:
        """Compare expected and actual answers using keyword overlap.

        Args:
            expected: The expected answer string.
            actual: The actual answer produced by the agent.

        Returns:
            Score between 0.0 and 1.0 based on keyword overlap.
        """
        if not expected or not actual:
            return 0.0

        expected_clean = expected.strip().lower()
        actual_clean = actual.strip().lower()

        if expected_clean == actual_clean:
            return 1.0

        if expected_clean in actual_clean:
            return 0.9

        expected_words = set(expected_clean.split())
        actual_words = set(actual_clean.split())

        if not expected_words:
            return 0.0

        overlap = expected_words & actual_words
        return len(overlap) / len(expected_words)

    @staticmethod
    def _check_tools(
        expected: list[str], actual: list[str]
    ) -> float:
        """Compare expected vs actual tools using Jaccard similarity.

        Args:
            expected: List of expected tool names.
            actual: List of actually used tool names.

        Returns:
            Jaccard similarity score between 0.0 and 1.0.
        """
        if not expected:
            return 1.0 if not actual else 0.5

        expected_set = set(expected)
        actual_set = set(actual)
        union = expected_set | actual_set

        if not union:
            return 1.0

        intersection = expected_set & actual_set
        return len(intersection) / len(union)

    @staticmethod
    def _check_efficiency(step_count: int) -> float:
        """Score efficiency based on step count.

        Args:
            step_count: Total number of steps in the run.

        Returns:
            1.0 for <= threshold steps, decaying for more.
        """
        if step_count <= EFFICIENT_STEP_THRESHOLD:
            return 1.0
        decay = max(0.0, 1.0 - (step_count - EFFICIENT_STEP_THRESHOLD) * 0.15)
        return round(decay, 3)

    @staticmethod
    def _check_reliability(run: AgentRun) -> float:
        """Score reliability — 1.0 if no failures, 0.0 if any.

        Args:
            run: The completed agent run.

        Returns:
            1.0 if no failures occurred, 0.0 otherwise.
        """
        return 1.0 if not run.failures else 0.0

    @staticmethod
    def _extract_tools(run: AgentRun) -> list[str]:
        """Extract unique tool names used during a run.

        Args:
            run: The completed agent run.

        Returns:
            List of unique tool names that were invoked.
        """
        tools: list[str] = []
        for step in run.steps:
            if step.tool_name and step.tool_name not in tools:
                tools.append(step.tool_name)
        return tools
