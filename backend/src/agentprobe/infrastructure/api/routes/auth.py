"""Authentication endpoints — register, login, API keys."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from agentprobe.infrastructure.api.dependencies import get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """Request body for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class ApiKeyResponse(BaseModel):
    """API key creation response."""

    api_key: str


class UserResponse(BaseModel):
    """Current user info response."""

    id: str
    email: str
    api_key_count: int


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest) -> TokenResponse:
    """Register a new user and return a JWT token."""
    auth = get_auth_service()
    try:
        await auth.register(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    token = await auth.login(body.email, body.password)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Authenticate and return a JWT token."""
    auth = get_auth_service()
    try:
        token = await auth.login(body.email, body.password)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return TokenResponse(access_token=token)


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(request: Request) -> ApiKeyResponse:
    """Generate a new API key for the authenticated user."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    auth = get_auth_service()
    api_key = await auth.create_api_key(user_id)
    return ApiKeyResponse(api_key=api_key)


@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request) -> UserResponse:
    """Return info about the currently authenticated user."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    from agentprobe.infrastructure.api.dependencies import get_user_repository
    repo = get_user_repository()
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        api_key_count=len(user.api_keys),
    )
