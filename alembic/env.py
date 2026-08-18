from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.config.database import Base

# IMPORTAR OS MODELS
from app.models.user_model import Usuario
from app.models.categoria_model import Categoria
from app.models.produto_model import Produto
from app.models.produto_variacao_model import ProdutoVariacao
from app.models.venda_model import Venda
from app.models.venda_item_model import VendaItem

config = context.config

# Logs
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# METADATA DOS MODELS
target_metadata = Base.metadata


def run_migrations_offline() -> None:

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()