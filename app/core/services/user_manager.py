from typing import Optional
from datetime import datetime, timezone
from fastapi import Header, Depends
from app.database.postgres import postgres_manager
from app.core.context.user_context import UserContext

class UserManager:
    async def get_context(
        self,
        authorization: Optional[str] = Header(None),
        db = Depends(postgres_manager.get_db)
    ) -> UserContext:

        if not authorization:
            return UserContext(type="anonymous")

        # Проверяем токен в БД
        row = await db.fetchrow(
            "SELECT email, expires_at FROM tokens WHERE token = $1",
            authorization
        )

        if not row or row["expires_at"] < datetime.now(timezone.utc):
            return UserContext(type="anonymous")

        if row["email"]:
            return UserContext(type="user", email=row["email"])
        
        return UserContext(type="guest", guest_token=authorization)
