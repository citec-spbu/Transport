from fastapi import APIRouter, Depends
from app.models.schemas import (
    RequestCodeRequest, RequestCodeResponse,
    VerifyCodeRequest, VerifyCodeResponse,
    GuestTokenResponse
)
from app.api.v1.endpoints.postgres import get_db
from datetime import datetime, timedelta, timezone
import secrets
import string

router = APIRouter()

@router.post("/request_code", response_model=RequestCodeResponse)
async def request_code(data: RequestCodeRequest, db = Depends(get_db)):
    code = "".join(secrets.choice(string.digits) for _ in range(6))
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

    # Создаём/обновляем пользователя (без verified)
    await db.execute(
        "INSERT INTO users (email, verified) VALUES ($1, FALSE) ON CONFLICT (email) DO NOTHING",
        data.email
    )

    # Сохраняем код
    await db.execute(
        """
        INSERT INTO verification_codes (email, code, expires_at)
        VALUES ($1, $2, $3)
        ON CONFLICT (email) DO UPDATE
        SET code = $2, expires_at = $3
        """,
        data.email, code, expires
    )

    print(f"Verification code for {data.email}: {code}")
    return RequestCodeResponse(message="Verification code sent")


@router.post("/verify_code", response_model=VerifyCodeResponse)
async def verify_code(data: VerifyCodeRequest, db = Depends(get_db)):
    row = await db.fetchrow(
        """
        SELECT code, expires_at FROM verification_codes
        WHERE email = $1
        """,
        data.email
    )

    if not row or row['code'] != data.code or row['expires_at'] < datetime.now(timezone.utc):
        return VerifyCodeResponse(token=None, email=data.email)

    # Удаляем код
    await db.execute("DELETE FROM verification_codes WHERE email = $1", data.email)

    # Помечаем как verified
    await db.execute("UPDATE users SET verified = TRUE WHERE email = $1", data.email)

    # Выдаём токен
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=30)

    await db.execute(
        "INSERT INTO tokens (token, email, expires_at) VALUES ($1, $2, $3)",
        token, data.email, expires
    )

    return VerifyCodeResponse(token=token, email=data.email)


@router.post("/guest", response_model=GuestTokenResponse)
async def guest():
    token = secrets.token_urlsafe(32)
    return GuestTokenResponse(token=token)
