from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.responses import success_response
from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import LoginRequest, UserCreate, UserResponse
from app.services.user_service import UserService

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    RefreshTokenRequest,
    UserCreate,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    repository = UserRepository(db)
    return UserService(repository)


@router.post("/register")
async def register(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
):
    user = await service.register(payload)

    return success_response(
        data=UserResponse.model_validate(user),
        message="User registered successfully.",
    )


@router.post("/login")
async def login(
    payload: LoginRequest,
    service: UserService = Depends(get_user_service),
):
    token = await service.login(payload)

    return success_response(
        data=token,
        message="Login successful.",
    )

@router.get("/me")
async def me(
    current_user: User = Depends(get_current_user),
):
    return success_response(
        data=UserResponse.model_validate(current_user),
        message="Current user fetched successfully.",
    )

@router.post("/token")
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
):
    payload = LoginRequest(
        email=form_data.username,
        password=form_data.password,
    )

    token_data = await service.login(payload)
    return token_data

@router.post("/refresh")
async def refresh(
    payload: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    token = await service.refresh_access_token(payload)

    return success_response(
        data=token,
        message="Access token refreshed successfully.",
    )
@router.post("/logout")
async def logout(
    payload: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    result = await service.logout(payload)

    return success_response(
        data=result,
        message="Logout successful.",
    )