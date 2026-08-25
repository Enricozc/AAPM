from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config.settings import settings


DATABASE_URL = settings.database_url


# =====================================================
# ENGINE
# =====================================================

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)


# =====================================================
# SESSION
# =====================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# =====================================================
# BASE
# =====================================================

Base = declarative_base()


# =====================================================
# DEPENDÊNCIA DO BANCO
# =====================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()