from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str

settings = Settings()
