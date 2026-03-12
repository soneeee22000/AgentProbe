"""Database engine and async session setup for AgentProbe persistence."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./agentprobe.db"


def _is_sqlite(url: str) -> bool:
    """Check if the database URL points to a SQLite database."""
    return url.startswith("sqlite")


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

    if _is_sqlite(database_url):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_size"] = pool_size
        kwargs["max_overflow"] = max_overflow

    return create_async_engine(database_url, **kwargs)


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
