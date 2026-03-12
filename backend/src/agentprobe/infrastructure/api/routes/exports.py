"""Export endpoints for benchmarks and runs."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from agentprobe.application.services.exporter import ExportService
from agentprobe.infrastructure.api.dependencies import (
    get_benchmark_repository,
    get_run_repository,
)

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


def _get_user_id(request: Request) -> str:
    """Extract user_id from request state."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id


def _get_exporter() -> ExportService:
    """Create an ExportService with the current repositories."""
    return ExportService(
        run_repo=get_run_repository(),
        benchmark_repo=get_benchmark_repository(),
    )


@router.get("/runs/{run_id}/csv")
async def export_run_csv(run_id: str, request: Request) -> Response:
    """Export a run and its steps as a CSV file."""
    _get_user_id(request)
    exporter = _get_exporter()
    try:
        csv_content = await exporter.export_run_csv(run_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="run_{run_id}.csv"',
        },
    )


@router.get("/benchmarks/{suite_id}/csv")
async def export_benchmark_csv(suite_id: str, request: Request) -> Response:
    """Export benchmark suite results as a CSV file."""
    _get_user_id(request)
    exporter = _get_exporter()
    try:
        csv_content = await exporter.export_benchmark_csv(suite_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="benchmark_{suite_id}.csv"',
        },
    )


@router.get("/benchmarks/{suite_id}/pdf")
async def export_benchmark_pdf(suite_id: str, request: Request) -> Response:
    """Export benchmark suite results as a PDF file."""
    _get_user_id(request)
    exporter = _get_exporter()
    try:
        pdf_content = await exporter.export_benchmark_pdf(suite_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="benchmark_{suite_id}.pdf"',
        },
    )
