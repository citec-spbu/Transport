from email.message import EmailMessage
from aiosmtplib import send
from app.core.configs.email_config import settings

async def send_verification_code(email: str, code: str):
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = email
    message["Subject"] = "Подтверждение электронной почты"

    message.set_content(
        f"""Здравствуйте!

Ваш код подтверждения: {code}

Код действует 10 минут.
Если вы не запрашивали код — просто проигнорируйте это письмо.
"""
    )

    await send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )
