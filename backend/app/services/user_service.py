from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import AppException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_refresh_token_expires_at,
    hash_password,
    verify_password,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import LoginRequest, UserCreate
from app.schemas.user import LoginRequest, RefreshTokenRequest, UserCreate

DUMMY_PASSWORD_HASH = hash_password("dummy-password-used-for-timing-only")

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def register(self, payload: UserCreate):
        exists = await self.repository.find_by_email(payload.email)

        if exists:
            raise AppException(
                status_code=status.HTTP_400_BAD_REQUEST,
                code="EMAIL_ALREADY_EXISTS",
                message="Email already exists.",
            )

        user_data = {
            "email": payload.email,
            "username": payload.username,
            "hashed_password": hash_password(payload.password),
        }

        return await self.repository.create(user_data)

    async def login(self, payload: LoginRequest):
        user = await self.repository.find_by_email(payload.email)
        password_hash = user.hashed_password if user is not None else DUMMY_PASSWORD_HASH
        password_matches = verify_password(payload.password, password_hash)

        if user is None or not password_matches or not user.is_active:
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token()

        refresh_token_repository = RefreshTokenRepository(self.repository.db)

        await refresh_token_repository.create(
            {
                "user_id": user.id,
                "token": refresh_token,
                "expires_at": get_refresh_token_expires_at(),
            }
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    
    async def refresh_access_token(self, payload: RefreshTokenRequest):
        refresh_token_repository = RefreshTokenRepository(self.repository.db)

        refresh_token = await refresh_token_repository.find_valid_token(
            payload.refresh_token
        )

        if refresh_token is None:
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_REFRESH_TOKEN",
                message="Invalid or expired refresh token.",
            )

        user = await self.repository.find_by_id(refresh_token.user_id)

        if user is None or not user.is_active:
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_USER",
                message="Invalid user.",
            )

        access_token = create_access_token(str(user.id))

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

    async def logout(self, payload: RefreshTokenRequest):
        refresh_token_repository = RefreshTokenRepository(self.repository.db)

        refresh_token = await refresh_token_repository.find_valid_token(
            payload.refresh_token
        )

        if refresh_token is None:
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_REFRESH_TOKEN",
                message="Invalid or expired refresh token.",
            )

        await refresh_token_repository.revoke(refresh_token)

        return {"message": "Logged out successfully."}
