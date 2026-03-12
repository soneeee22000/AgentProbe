"""Port interface for user persistence."""

from abc import ABC, abstractmethod

from agentprobe.domain.entities.user import User


class IUserRepository(ABC):
    """Abstract interface for user data access."""

    @abstractmethod
    async def create(self, user: User) -> None:
        """Persist a new user."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Find a user by email address."""
        ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> User | None:
        """Find a user by ID."""
        ...

    @abstractmethod
    async def get_by_api_key(self, api_key: str) -> User | None:
        """Find a user by API key."""
        ...

    @abstractmethod
    async def add_api_key(self, user_id: str, api_key: str) -> None:
        """Add an API key to a user."""
        ...
