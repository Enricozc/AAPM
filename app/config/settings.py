import os

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()


class Settings(BaseSettings):

    PROJECT_NAME: str = "PDV AAPM"

    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "chave_super_secreta_padrao"
    )

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./test.db"
    )

    class Config:
        case_sensitive = True


settings = Settings()