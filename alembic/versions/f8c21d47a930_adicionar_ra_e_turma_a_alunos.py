"""Adicionar RA e turma/curso ao cadastro independente de alunos."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8c21d47a930"
down_revision: Union[str, Sequence[str], None] = "f3a8b12d6c40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_column_if_missing(table: str, column: sa.Column) -> None:
    inspector = sa.inspect(op.get_bind())
    if table in inspector.get_table_names():
        existing = {item["name"] for item in inspector.get_columns(table)}
        if column.name not in existing:
            op.add_column(table, column)


def upgrade() -> None:
    _add_column_if_missing("alunos", sa.Column("ra", sa.String(length=30), nullable=True))
    _add_column_if_missing(
        "alunos",
        sa.Column("turma_curso", sa.String(length=100), nullable=True),
    )

    inspector = sa.inspect(op.get_bind())
    if "alunos" in inspector.get_table_names():
        indexes = {index["name"] for index in inspector.get_indexes("alunos")}
        if "ix_alunos_ra" not in indexes:
            op.create_index("ix_alunos_ra", "alunos", ["ra"], unique=True)

    _add_column_if_missing(
        "armario_historico",
        sa.Column("aluno_ra", sa.String(length=30), nullable=True),
    )
    _add_column_if_missing(
        "armario_historico",
        sa.Column("aluno_turma_curso", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "armario_historico" in inspector.get_table_names():
        columns = {
            column["name"] for column in inspector.get_columns("armario_historico")
        }
        with op.batch_alter_table("armario_historico") as batch_op:
            if "aluno_turma_curso" in columns:
                batch_op.drop_column("aluno_turma_curso")
            if "aluno_ra" in columns:
                batch_op.drop_column("aluno_ra")

    inspector = sa.inspect(bind)
    if "alunos" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("alunos")}
        indexes = {index["name"] for index in inspector.get_indexes("alunos")}
        if "ix_alunos_ra" in indexes:
            op.drop_index("ix_alunos_ra", table_name="alunos")
        with op.batch_alter_table("alunos") as batch_op:
            if "turma_curso" in columns:
                batch_op.drop_column("turma_curso")
            if "ra" in columns:
                batch_op.drop_column("ra")
