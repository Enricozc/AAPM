from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.config.database import Base


class PasswordResetToken(Base):

    __tablename__ = "password_reset_tokens"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False
    )

    token = Column(
        String(255),
        unique=True,
        nullable=False
    )

    expiracao = Column(
        DateTime,
        nullable=False
    )

    criado_em = Column(
        DateTime,
        server_default=func.now()
    )