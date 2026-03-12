"""Unit tests for BenchmarkSeeder — idempotent benchmark auto-seeding."""

import json
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agentprobe.application.services.seeder import BenchmarkSeeder
from agentprobe.infrastructure.persistence.models.tables import Base
from agentprobe.infrastructure.persistence.repositories.benchmark_repository import (
    SQLAlchemyBenchmarkRepository,
)

SAMPLE_CASES = [
    {
        "id": "math-001",
        "query": "What is 25 * 17?",
        "category": "math",
        "difficulty": "easy",
        "expected_answer": "425",
        "expected_tools": ["calculator"],
    },
    {
        "id": "search-001",
        "query": "What is the capital of France?",
        "category": "search",
        "difficulty": "easy",
        "expected_answer": "Paris",
        "expected_tools": ["web_search"],
    },
    {
        "id": "reason-001",
        "query": "If all cats are animals and some animals are pets, are all cats pets?",
        "category": "reasoning",
        "difficulty": "easy",
        "expected_answer": "No",
        "expected_tools": ["think"],
    },
]


@pytest.fixture()
def benchmark_json_path(tmp_path: Path) -> str:
    """Write sample benchmark cases to a temporary JSON file.

    Returns:
        Absolute path to the temporary JSON file.
    """
    file_path = tmp_path / "benchmark_cases.json"
    file_path.write_text(json.dumps(SAMPLE_CASES), encoding="utf-8")
    return str(file_path)


@pytest.fixture()
async def session_factory() -> async_sessionmaker[AsyncSession]:
    """Create an in-memory aiosqlite engine and return a session factory.

    Tables are created fresh for every test invocation.

    Returns:
        An async session factory bound to the in-memory database.
    """
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, class_=AsyncSession
    )
    yield factory  # type: ignore[misc]
    await engine.dispose()


@pytest.mark.asyncio
async def test_seed_inserts_cases_into_empty_db(
    session_factory: async_sessionmaker[AsyncSession],
    benchmark_json_path: str,
) -> None:
    """Seeding an empty database should insert all cases and return the count."""
    count = await BenchmarkSeeder.seed(session_factory, data_path=benchmark_json_path)

    assert count == len(SAMPLE_CASES)

    repo = SQLAlchemyBenchmarkRepository(session_factory)
    stored = await repo.list_cases()
    assert len(stored) == len(SAMPLE_CASES)

    ids = {c.id for c in stored}
    expected_ids = {c["id"] for c in SAMPLE_CASES}
    assert ids == expected_ids


@pytest.mark.asyncio
async def test_seed_skips_when_cases_exist(
    session_factory: async_sessionmaker[AsyncSession],
    benchmark_json_path: str,
) -> None:
    """Seeding a non-empty database should be idempotent and return 0."""
    first_count = await BenchmarkSeeder.seed(
        session_factory, data_path=benchmark_json_path
    )
    assert first_count == len(SAMPLE_CASES)

    second_count = await BenchmarkSeeder.seed(
        session_factory, data_path=benchmark_json_path
    )
    assert second_count == 0

    repo = SQLAlchemyBenchmarkRepository(session_factory)
    stored = await repo.list_cases()
    assert len(stored) == len(SAMPLE_CASES)


@pytest.mark.asyncio
async def test_seed_with_real_data_file(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Seed using the actual benchmark_cases.json shipped with the project."""
    data_path = str(
        Path(__file__).resolve().parents[2] / "data" / "benchmark_cases.json"
    )
    count = await BenchmarkSeeder.seed(session_factory, data_path=data_path)

    assert count > 0

    repo = SQLAlchemyBenchmarkRepository(session_factory)
    stored = await repo.list_cases()
    assert len(stored) == count
