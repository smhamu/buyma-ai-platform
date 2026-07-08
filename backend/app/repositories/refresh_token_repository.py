from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base_repository import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, RefreshToken)

    async def find_valid_token(self, token: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()
    
    async def revoke(self, refresh_token: RefreshToken) -> RefreshToken:
        refresh_token.revoked_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(refresh_token)

        return refresh_token