from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # =====================================================
    # BANCO DE DADOS
    # =====================================================

    database_url: str = "sqlite:///./aapm.db"

    # =====================================================
    # JWT
    # =====================================================

    secret_key: str = "uma-chave-muito-segura-e-longa-aqui"

    algorithm: str = "HS256"

    access_token_expire_minutes: int = 60

    # =====================================================
    # E-MAIL / SMTP
    # =====================================================

    smtp_email: str = ""

    smtp_password: str = ""

    smtp_server: str = "smtp.gmail.com"

    smtp_port: int = 587

    # =====================================================
    # CONFIGURAÇÃO
    # =====================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()