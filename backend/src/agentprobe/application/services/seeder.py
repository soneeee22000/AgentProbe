"""Benchmark auto-seeder — loads built-in test cases into the database."""

import json
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agentprobe.domain.entities.benchmark import (
    BenchmarkCase,
    BenchmarkCategory,
    BenchmarkDifficulty,
)
from agentprobe.infrastructure.persistence.repositories.benchmark_repository import (
    SQLAlchemyBenchmarkRepository,
)

logger = logging.getLogger(__name__)


class BenchmarkSeeder:
    """Seeds the database with built-in benchmark cases from a JSON file.

    The seeder is idempotent: it checks whether cases already exist
    before inserting.  If the database already contains benchmark cases,
    seeding is skipped entirely.
    """

    @staticmethod
    async def seed(
        session_factory: async_sessionmaker[AsyncSession],
        data_path: str = "./data/benchmark_cases.json",
    ) -> int:
        """Load benchmark cases from a JSON file into the database.

        Args:
            session_factory: An async session factory bound to the engine.
            data_path: Filesystem path to the benchmark cases JSON file.

        Returns:
            The number of cases seeded.  Returns ``0`` when the database
            already contains cases (idempotent guard).

        Raises:
            FileNotFoundError: If *data_path* does not point to a valid file.
            json.JSONDecodeError: If the JSON file is malformed.
        """
        repo = SQLAlchemyBenchmarkRepository(session_factory)

        existing_cases = await repo.list_cases()
        if existing_cases:
            logger.info(
                "Database already contains %d benchmark cases — skipping seed.",
                len(existing_cases),
            )
            return 0

        resolved_path = Path(data_path).resolve()
        logger.info("Loading benchmark cases from %s", resolved_path)

        raw_text = resolved_path.read_text(encoding="utf-8")
        raw_cases: list[dict] = json.loads(raw_text)

        seeded_count = 0
        for entry in raw_cases:
            case = BenchmarkCase(
                id=entry["id"],
                query=entry["query"],
                category=BenchmarkCategory(entry["category"]),
                difficulty=BenchmarkDifficulty(entry["difficulty"]),
                expected_answer=entry["expected_answer"],
                expected_tools=entry.get("expected_tools", []),
                is_builtin=entry.get("is_builtin", True),
            )
            await repo.save_case(case)
            seeded_count += 1

        logger.info("Seeded %d benchmark cases.", seeded_count)
        return seeded_count
