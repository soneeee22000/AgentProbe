"""SQLAlchemy implementation of the user repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from agentprobe.domain.entities.user import User
from agentprobe.domain.ports.user_repository import IUserRepository
from agentprobe.infrastructure.persistence.models.tables import ApiKeyModel, UserModel


class SQLAlchemyUserRepository(IUserRepository):
    """User repository backed by SQLAlchemy.

    Args:
        session_factory: Async session factory for database access.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, user: User) -> None:
        """Persist a new user."""
        async with self._session_factory() as session:
            model = UserModel(
                id=user.id,
                email=user.email,
                hashed_password=user.hashed_password,
                created_at=user.created_at,
            )
            session.add(model)
            await session.commit()

    async def get_by_email(self, email: str) -> User | None:
        """Find a user by email address."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel)
                .options(selectinload(UserModel.api_keys))
                .where(UserModel.email == email)
            )
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def get_by_id(self, user_id: str) -> User | None:
        """Find a user by ID."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel)
                .options(selectinload(UserModel.api_keys))
                .where(UserModel.id == user_id)
            )
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def get_by_api_key(self, api_key: str) -> User | None:
        """Find a user by API key."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserModel)
                .join(ApiKeyModel)
                .options(selectinload(UserModel.api_keys))
                .where(ApiKeyModel.key == api_key)
            )
            model = result.scalar_one_or_none()
            return self._to_entity(model) if model else None

    async def add_api_key(self, user_id: str, api_key: str) -> None:
        """Add an API key to a user."""
        async with self._session_factory() as session:
            key_model = ApiKeyModel(user_id=user_id, key=api_key)
            session.add(key_model)
            await session.commit()

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        """Convert ORM model to domain entity."""
        return User(
            id=model.id,
            email=model.email,
            hashed_password=model.hashed_password,
            created_at=model.created_at,
            api_keys=[k.key for k in model.api_keys],
        )
