from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config.settings import settings

# O 'check_same_thread' é obrigatório para SQLite
if settings.DATABASE_URL.startswith("sqlite"):

    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

else:

    engine = create_engine(
        settings.DATABASE_URL
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

class Base(DeclarativeBase):
    pass


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()