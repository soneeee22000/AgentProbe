"""User domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class User:
    """Represents a registered user.

    Attributes:
        id: Unique user identifier (UUID).
        email: User's email address.
        hashed_password: Bcrypt-hashed password.
        created_at: Account creation timestamp.
        api_keys: List of API keys associated with this user.
    """

    id: str
    email: str
    hashed_password: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    api_keys: list[str] = field(default_factory=list)
