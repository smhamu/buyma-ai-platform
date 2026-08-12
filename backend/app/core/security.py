import secrets
from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": subject,
        "exp": expire,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def get_refresh_token_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )

        if payload.get("type") != "access":
            return None

        return payload.get("sub")

    except InvalidTokenError:
        return None
