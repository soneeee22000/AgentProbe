"""AnalyticsService — aggregates failure and model performance data."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AnalyticsService:
    """Provides aggregated analytics from run and failure data.

    Args:
        session_factory: Async session factory for direct SQL queries.
    """

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        self._session_factory = session_factory

    async def get_failure_analytics(self) -> dict:
        """Aggregate failure counts by type, model, and time period.

        Returns:
            Dict with failure distribution breakdowns.
        """
        from sqlalchemy import text

        async with self._session_factory() as session:
            by_type = await session.execute(
                text(
                    "SELECT failure_type, COUNT(*) as count "
                    "FROM failures "
                    "GROUP BY failure_type "
                    "ORDER BY count DESC"
                )
            )
            type_rows = by_type.fetchall()

            by_model = await session.execute(
                text(
                    "SELECT r.model_id, f.failure_type, COUNT(*) as count "
                    "FROM failures f "
                    "JOIN runs r ON f.run_id = r.id "
                    "GROUP BY r.model_id, f.failure_type "
                    "ORDER BY r.model_id, count DESC"
                )
            )
            model_rows = by_model.fetchall()

            total_runs_result = await session.execute(
                text("SELECT COUNT(*) FROM runs")
            )
            total_runs = total_runs_result.scalar_one()

            failed_runs_result = await session.execute(
                text("SELECT COUNT(*) FROM runs WHERE succeeded = 0")
            )
            failed_runs = failed_runs_result.scalar_one()

        by_type_dict = {row[0]: row[1] for row in type_rows}

        model_failures: dict[str, dict[str, int]] = {}
        for row in model_rows:
            model_id, failure_type, count = row
            if model_id not in model_failures:
                model_failures[model_id] = {}
            model_failures[model_id][failure_type] = count

        return {
            "total_runs": total_runs,
            "failed_runs": failed_runs,
            "failure_rate": (
                round(failed_runs / total_runs, 3)
                if total_runs > 0
                else 0.0
            ),
            "by_type": by_type_dict,
            "by_model": model_failures,
        }

    async def get_model_analytics(self) -> dict:
        """Aggregate performance stats per model.

        Returns:
            Dict with per-model success rate, avg steps, avg latency, etc.
        """
        from sqlalchemy import text

        async with self._session_factory() as session:
            model_stats = await session.execute(
                text(
                    "SELECT "
                    "  model_id, "
                    "  COUNT(*) as total_runs, "
                    "  SUM(CASE WHEN succeeded = 1 THEN 1 ELSE 0 END) as successes, "
                    "  AVG(duration_ms) as avg_duration_ms, "
                    "  AVG(total_tokens) as avg_tokens "
                    "FROM runs "
                    "GROUP BY model_id "
                    "ORDER BY total_runs DESC"
                )
            )
            stats_rows = model_stats.fetchall()

            step_counts = await session.execute(
                text(
                    "SELECT r.model_id, AVG(step_count) as avg_steps "
                    "FROM ("
                    "  SELECT run_id, COUNT(*) as step_count "
                    "  FROM steps "
                    "  GROUP BY run_id"
                    ") sc "
                    "JOIN runs r ON sc.run_id = r.id "
                    "GROUP BY r.model_id"
                )
            )
            step_rows = {row[0]: row[1] for row in step_counts.fetchall()}

        models: dict[str, dict] = {}
        for row in stats_rows:
            model_id = row[0]
            total = row[1]
            successes = row[2]
            models[model_id] = {
                "total_runs": total,
                "successes": successes,
                "success_rate": round(successes / total, 3) if total > 0 else 0.0,
                "avg_duration_ms": round(row[3], 1) if row[3] else None,
                "avg_tokens": round(row[4], 1) if row[4] else None,
                "avg_steps": (
                    round(step_rows[model_id], 1)
                    if model_id in step_rows
                    else None
                ),
            }

        return {"models": models}
