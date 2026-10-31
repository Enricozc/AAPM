import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.database import Base, get_db
from app.config.security import get_current_user, require_admin
from app.models.categoria_model import Categoria
from app.models.produto_model import Produto
from app.models.produto_variacao_model import ProdutoVariacao
from app.models.user_model import Usuario
from main import app


ADMIN = {"id": 1, "nome": "Administrador", "sub": "admin@aapm.test", "role": "ADMIN"}


@pytest.fixture
def db_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db(db_factory):
    session = db_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_factory):
    def override_db():
        session = db_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: ADMIN
    app.dependency_overrides[require_admin] = lambda: ADMIN
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def product_variation(db):
    category = Categoria(nome="Uniformes")
    db.add(category)
    db.flush()
    product = Produto(nome="Camiseta", preco=25, categoria_id=category.id)
    db.add(product)
    db.flush()
    variation = ProdutoVariacao(
        produto_id=product.id,
        tamanho="M",
        cor="Azul",
        preco=25,
        estoque_atual=10,
    )
    db.add(variation)
    db.commit()
    return variation


@pytest.fixture
def admin_user(db):
    from app.config.security import hash_password

    user = Usuario(
        nome="Administrador",
        email="admin@aapm.test",
        hashed_password=hash_password("senha-segura"),
        role="ADMIN",
        ativo=True,
    )
    db.add(user)
    db.commit()
    return user
