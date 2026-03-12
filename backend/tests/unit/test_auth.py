"""Tests for the authentication service."""

import pytest

from agentprobe.application.services.auth import AuthService
from agentprobe.domain.entities.user import User
from agentprobe.domain.ports.user_repository import IUserRepository


class InMemoryUserRepo(IUserRepository):
    """In-memory user repository for testing."""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._keys: dict[str, str] = {}  # api_key -> user_id

    async def create(self, user: User) -> None:
        """Store user in memory."""
        self._users[user.id] = user

    async def get_by_email(self, email: str) -> User | None:
        """Find user by email."""
        for u in self._users.values():
            if u.email == email:
                return u
        return None

    async def get_by_id(self, user_id: str) -> User | None:
        """Find user by ID."""
        return self._users.get(user_id)

    async def get_by_api_key(self, api_key: str) -> User | None:
        """Find user by API key."""
        uid = self._keys.get(api_key)
        return self._users.get(uid) if uid else None

    async def add_api_key(self, user_id: str, api_key: str) -> None:
        """Add API key."""
        self._keys[api_key] = user_id
        user = self._users.get(user_id)
        if user:
            user.api_keys.append(api_key)


@pytest.fixture
def auth_service() -> AuthService:
    """Create an AuthService with in-memory repo."""
    return AuthService(
        user_repo=InMemoryUserRepo(),
        jwt_secret="test-secret",
        jwt_expire_minutes=60,
    )


class TestAuthService:
    """Tests for AuthService."""

    async def test_register_creates_user(self, auth_service: AuthService) -> None:
        """Register should create a new user."""
        user = await auth_service.register("test@example.com", "password123")
        assert user.email == "test@example.com"
        assert user.id

    async def test_register_duplicate_email_raises(self, auth_service: AuthService) -> None:
        """Register with existing email should raise ValueError."""
        await auth_service.register("test@example.com", "password123")
        with pytest.raises(ValueError, match="already registered"):
            await auth_service.register("test@example.com", "other")

    async def test_login_returns_token(self, auth_service: AuthService) -> None:
        """Login with valid credentials should return a JWT token."""
        await auth_service.register("test@example.com", "password123")
        token = await auth_service.login("test@example.com", "password123")
        assert isinstance(token, str)
        assert len(token) > 0

    async def test_login_invalid_password_raises(self, auth_service: AuthService) -> None:
        """Login with wrong password should raise ValueError."""
        await auth_service.register("test@example.com", "password123")
        with pytest.raises(ValueError, match="Invalid credentials"):
            await auth_service.login("test@example.com", "wrongpassword")

    async def test_login_unknown_email_raises(self, auth_service: AuthService) -> None:
        """Login with unknown email should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid credentials"):
            await auth_service.login("nobody@example.com", "password123")

    async def test_verify_token(self, auth_service: AuthService) -> None:
        """Token from login should verify and return user_id."""
        user = await auth_service.register("test@example.com", "password123")
        token = await auth_service.login("test@example.com", "password123")
        user_id = auth_service.verify_token(token)
        assert user_id == user.id

    async def test_verify_invalid_token(self, auth_service: AuthService) -> None:
        """Invalid token should return None."""
        assert auth_service.verify_token("invalid.token.here") is None

    async def test_create_api_key(self, auth_service: AuthService) -> None:
        """Should generate an API key prefixed with ap_."""
        user = await auth_service.register("test@example.com", "password123")
        api_key = await auth_service.create_api_key(user.id)
        assert api_key.startswith("ap_")
        assert len(api_key) > 10
