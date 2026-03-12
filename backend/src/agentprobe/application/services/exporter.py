"""Export service — generates CSV and PDF reports for benchmarks and runs."""

import csv
import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from agentprobe.domain.ports.benchmark_repository import IBenchmarkRepository
from agentprobe.domain.ports.run_repository import IRunRepository


class ExportService:
    """Generates export files for benchmarks and runs.

    Args:
        run_repo: Repository for accessing run data.
        benchmark_repo: Repository for accessing benchmark data.
    """

    def __init__(
        self,
        run_repo: IRunRepository,
        benchmark_repo: IBenchmarkRepository,
    ) -> None:
        self._run_repo = run_repo
        self._benchmark_repo = benchmark_repo

    async def export_run_csv(self, run_id: str) -> str:
        """Export a single run and its steps as CSV.

        Args:
            run_id: The run ID to export.

        Returns:
            CSV content as a string.
        """
        run = await self._run_repo.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "step_index", "step_type", "content", "tool_name",
            "tool_args", "failure_type", "token_count", "latency_ms",
        ])

        for step in run.steps:
            writer.writerow([
                step.step_index,
                step.step_type.value if hasattr(step.step_type, "value") else step.step_type,
                step.content[:200],
                step.tool_name or "",
                step.tool_args or "",
                step.failure_type.value
                if hasattr(step.failure_type, "value")
                else step.failure_type,
                step.token_count or "",
                step.latency_ms or "",
            ])

        return output.getvalue()

    async def export_benchmark_csv(self, suite_id: str) -> str:
        """Export benchmark suite results as CSV.

        Args:
            suite_id: The suite ID to export.

        Returns:
            CSV content as a string.
        """
        suite = await self._benchmark_repo.get_suite(suite_id)
        if not suite:
            raise ValueError(f"Suite {suite_id} not found")

        results = await self._benchmark_repo.get_suite_results(suite_id)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "case_id", "passed", "score", "answer_correct",
            "tools_correct", "failures",
        ])

        for r in results:
            writer.writerow([
                r.case_id,
                r.passed,
                f"{r.score:.2f}",
                r.answer_correct,
                r.tools_correct,
                ", ".join(r.failures) if hasattr(r, "failures") else "",
            ])

        return output.getvalue()

    async def export_benchmark_pdf(self, suite_id: str) -> bytes:
        """Export benchmark suite results as PDF.

        Args:
            suite_id: The suite ID to export.

        Returns:
            PDF content as bytes.
        """
        suite = await self._benchmark_repo.get_suite(suite_id)
        if not suite:
            raise ValueError(f"Suite {suite_id} not found")

        results = await self._benchmark_repo.get_suite_results(suite_id)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements: list[Any] = []

        # Title
        elements.append(Paragraph(
            f"AgentProbe Benchmark Report — Suite {suite_id}",
            styles["Title"],
        ))
        elements.append(Spacer(1, 0.25 * inch))

        # Summary
        elements.append(Paragraph(
            f"Model: {suite.model_id} | Provider: {suite.provider} | "
            f"Success Rate: {suite.success_rate:.1%}",
            styles["Normal"],
        ))
        elements.append(Spacer(1, 0.25 * inch))

        # Results table
        table_data = [["Case ID", "Passed", "Score"]]
        for r in results:
            table_data.append([
                r.case_id,
                "Yes" if r.passed else "No",
                f"{r.score:.2f}",
            ])

        table = Table(table_data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.beige, colors.white]),
        ]))
        elements.append(table)

        doc.build(elements)
        return buffer.getvalue()
