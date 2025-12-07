from fastapi import APIRouter
from app.models.schemas import (
    RequestCodeRequest, RequestCodeResponse,
    VerifyCodeRequest, VerifyCodeResponse,
    GuestTokenResponse
)
import secrets
import string

router = APIRouter()

# Временное хранилище кодов (в продакшене использовать Redis или БД)
verification_codes = {}

@router.post("/request_code", response_model=RequestCodeResponse)
async def request_code(data: RequestCodeRequest):
    """Отправить код подтверждения на email"""
    code = "".join(secrets.choice(string.digits) for _ in range(6))
    verification_codes[data.email] = code
    
    # TODO: интегрировать отправку email через SMTP сервис
    print(f"Verification code for {data.email}: {code}")
    
    return RequestCodeResponse(message="Verification code sent")


@router.post("/verify_code", response_model=VerifyCodeResponse)
async def verify_code(data: VerifyCodeRequest):
    """Проверить код подтверждения и получить токен"""
    stored_code = verification_codes.get(data.email)
    
    if not stored_code or stored_code != data.code:
        token = None
    else:
        token = secrets.token_urlsafe(32)
        del verification_codes[data.email]
    
    return VerifyCodeResponse(token=token, email=data.email)


@router.post("/guest", response_model=GuestTokenResponse)
async def guest():
    """Гостевой вход без регистрации"""
    token = secrets.token_urlsafe(32)
    return GuestTokenResponse(token=token)
