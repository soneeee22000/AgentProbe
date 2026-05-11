"""Database engine and async session setup for AgentProbe persistence."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./agentprobe.db"


def _is_sqlite(url: str) -> bool:
    """Check if the database URL points to a SQLite database."""
    return url.startswith("sqlite")


def _normalize_postgres_url(url: str) -> str:
    """Coerce sync Postgres URLs into the asyncpg dialect we use.

    Hosted providers (Railway, Render, Heroku) hand out connection strings
    like ``postgresql://...`` or ``postgres://...`` — both of which would
    select SQLAlchemy's sync psycopg2 dialect and fail under our async
    engine.  Rewriting the prefix is the cheapest way to keep the env var
    untouched while still using ``asyncpg`` underneath.
    """
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://") :]
    return url


def get_engine(
    database_url: str = DEFAULT_DATABASE_URL,
    pool_size: int = 5,
    max_overflow: int = 10,
) -> AsyncEngine:
    """Create an async SQLAlchemy engine for the given database URL.

    Args:
        database_url: Connection string for the database.
            Defaults to a local SQLite file via aiosqlite.
        pool_size: Connection pool size (PostgreSQL only).
        max_overflow: Max overflow connections (PostgreSQL only).

    Returns:
        An ``AsyncEngine`` instance ready for session creation.
    """
    kwargs: dict = {
        "echo": False,
        "future": True,
    }

    normalized = _normalize_postgres_url(database_url)

    if _is_sqlite(normalized):
        kwargs["connect_args"] = {"check_same_thread": False}
        # In-memory SQLite gives each connection its own isolated database,
        # so the lifespan creates tables on connection A and request handlers
        # see connection B with no tables. StaticPool pins one connection for
        # the engine's lifetime — the standard fix for this class of bug.
        if ":memory:" in normalized:
            kwargs["poolclass"] = StaticPool
    else:
        kwargs["pool_size"] = pool_size
        kwargs["max_overflow"] = max_overflow

    return create_async_engine(normalized, **kwargs)


def get_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Build an async session factory bound to the provided engine.

    Args:
        engine: The ``AsyncEngine`` to bind sessions to.

    Returns:
        An ``async_sessionmaker`` that produces ``AsyncSession`` instances.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
