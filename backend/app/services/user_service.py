from fastapi import status

from app.common.exceptions import AppException
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.user import LoginRequest, UserCreate


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

        if user is None or not verify_password(payload.password, user.hashed_password):
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        token = create_access_token(str(user.id))

        return {
            "access_token": token,
            "token_type": "bearer",
        }