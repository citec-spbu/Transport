from app.models.schemas import (
    RequestCodeRequest, RequestCodeResponse,
    VerifyCodeRequest, VerifyCodeResponse,
    GuestTokenResponse
)
from app.core.services.email import send_verification_code
from app.database.postgres import postgres_manager

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime, timedelta, timezone
import secrets
import string

router = APIRouter()

@router.post("/request_code", response_model=RequestCodeResponse)
async def request_code(
    data: RequestCodeRequest, 
    background_tasks: BackgroundTasks, 
    db = Depends(postgres_manager.get_db)
):

    user = await db.fetchrow(
        "SELECT verified FROM users WHERE email = $1",
        data.email
    )

    if user and user["verified"]:
        return RequestCodeResponse(message="User already verified")

    # Если пользователь новый или не подтверждён, создаём/обновляем запись
    await db.execute(
        "INSERT INTO users (email, verified) VALUES ($1, FALSE) ON CONFLICT (email) DO NOTHING",
        data.email
    )

    code = "".join(secrets.choice(string.digits) for _ in range(6))
    expires = datetime.now(timezone.utc) + timedelta(minutes=10)

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

    try:
        background_tasks.add_task(send_verification_code, data.email, code)
    except Exception as e:
        await db.execute(
            "DELETE FROM verification_codes WHERE email = $1",
            data.email
        )
        raise HTTPException(
            status_code=503, 
            detail="Email service temporarily unavailable"
        ) from e

    return RequestCodeResponse(message="Verification code sent")

@router.post("/verify_code", response_model=VerifyCodeResponse)
async def verify_code(
    data: VerifyCodeRequest, 
    db=Depends(postgres_manager.get_db)
):
    row = await db.fetchrow(
        """
        SELECT code, expires_at FROM verification_codes
        WHERE email = $1
        """,
        data.email
    )

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Verification code not found for this email"
        )

    if row['code'] != data.code:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification code"
        )

    if row['expires_at'] < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Verification code has expired"
        )

    await db.execute("DELETE FROM verification_codes WHERE email = $1", data.email)
    await db.execute("UPDATE users SET verified = TRUE WHERE email = $1", data.email)

    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=30)

    await db.execute(
        "INSERT INTO tokens (token, email, expires_at) VALUES ($1, $2, $3)",
        token, data.email, expires
    )

    return VerifyCodeResponse(token=token, email=data.email)


@router.post("/guest", response_model=GuestTokenResponse)
async def guest(
    db=Depends(postgres_manager.get_db)
):
    # Генерация токена
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=1)  # срок действия 1 день

    # Сохраняем токен в БД
    await db.execute(
        "INSERT INTO tokens (token, email, expires_at) VALUES ($1, $2, $3)",
        token, None, expires  # email = None для гостя
    )

    return GuestTokenResponse(token=token)
