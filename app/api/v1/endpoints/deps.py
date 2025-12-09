from fastapi import Header, Depends
from typing import Optional, Literal
from app.api.v1.endpoints.postgres import get_db

class UserContext:
    def __init__(self, type: Literal["user", "guest", "anonymous"], email: str = None, guest_token: str = None):
        self.type = type
        self.email = email
        self.guest_token = guest_token

async def get_user_or_guest(
    authorization: Optional[str] = Header(None),
    db = Depends(get_db)
) -> UserContext:
    if not authorization:
        return UserContext(type="anonymous")

    token = authorization[7:] if authorization.startswith("Bearer ") else authorization

    # Сначала проверим — это пользователь?
    row = await db.fetchrow(
        "SELECT email FROM tokens WHERE token = $1 AND expires_at > NOW()",
        token
    )
    if row:
        return UserContext(type="user", email=row["email"])

    # Иначе — считаем, что это guest_token
    return UserContext(type="guest", guest_token=token)

async def get_current_user_email(
    authorization: Optional[str] = Header(None),
    db = Depends(get_db)
) -> Optional[str]:
    if not authorization:
        return None

    token = authorization[7:] if authorization.startswith("Bearer ") else authorization

    # Только проверяем: есть ли такой токен у подтверждённого пользователя
    row = await db.fetchrow(
        "SELECT email FROM tokens WHERE token = $1 AND expires_at > NOW()",
        token
    )
    return row["email"] if row else None