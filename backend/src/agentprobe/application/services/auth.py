"""Authentication service — user registration, login, JWT, API keys."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from agentprobe.domain.entities.user import User
from agentprobe.domain.ports.user_repository import IUserRepository

_ALGORITHM = "HS256"


class AuthService:
    """Handles user authentication, JWT tokens, and API key management.

    Args:
        user_repo: Repository for user persistence.
        jwt_secret: Secret key for JWT signing.
        jwt_expire_minutes: Token expiration time in minutes.
    """

    def __init__(
        self,
        user_repo: IUserRepository,
        jwt_secret: str,
        jwt_expire_minutes: int = 1440,
    ) -> None:
        self._repo = user_repo
        self._jwt_secret = jwt_secret
        self._jwt_expire = jwt_expire_minutes

    async def register(self, email: str, password: str) -> User:
        """Register a new user.

        Args:
            email: User's email address.
            password: Plain-text password to hash.

        Returns:
            The newly created User entity.

        Raises:
            ValueError: If the email is already registered.
        """
        existing = await self._repo.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password=hashed,
        )
        await self._repo.create(user)
        return user

    async def login(self, email: str, password: str) -> str:
        """Authenticate a user and return a JWT token.

        Args:
            email: User's email address.
            password: Plain-text password to verify.

        Returns:
            JWT access token string.

        Raises:
            ValueError: If credentials are invalid.
        """
        user = await self._repo.get_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")

        if not bcrypt.checkpw(password.encode(), user.hashed_password.encode()):
            raise ValueError("Invalid credentials")

        return self._create_token(user.id)

    async def create_api_key(self, user_id: str) -> str:
        """Generate a new API key for the user.

        Args:
            user_id: The user's ID.

        Returns:
            The generated API key string.
        """
        api_key = f"ap_{secrets.token_urlsafe(32)}"
        await self._repo.add_api_key(user_id, api_key)
        return api_key

    def verify_token(self, token: str) -> str | None:
        """Verify a JWT token and extract the user ID.

        Args:
            token: JWT token string.

        Returns:
            User ID if valid, None otherwise.
        """
        try:
            payload = jwt.decode(token, self._jwt_secret, algorithms=[_ALGORITHM])
            return payload.get("sub")
        except jwt.JWTError:
            return None

    def _create_token(self, user_id: str) -> str:
        """Create a JWT access token.

        Args:
            user_id: User ID to encode as the subject.

        Returns:
            Encoded JWT token string.
        """
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._jwt_expire)
        payload = {"sub": user_id, "exp": expire}
        return jwt.encode(payload, self._jwt_secret, algorithm=_ALGORITHM)
