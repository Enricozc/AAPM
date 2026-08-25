from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime
)

from sqlalchemy.sql import func

from app.config.database import Base


class Usuario(Base):

    __tablename__ = "usuarios"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    nome = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(20),
        default="operador"
    )

    ativo = Column(
        Boolean,
        default=True
    )

    criado_em = Column(
        DateTime,
        server_default=func.now()
    )