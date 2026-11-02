"""Criar cadastro independente de alunos para armários."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a8b12d6c40"
down_revision: Union[str, Sequence[str], None] = "a6c1427f9b20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "alunos" not in tables:
        op.create_table(
            "alunos",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("nome", sa.String(length=100), nullable=False),
            sa.Column(
                "criado_em",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_alunos_nome", "alunos", ["nome"], unique=False)

    inspector = sa.inspect(bind)
    if "armarios" not in set(inspector.get_table_names()):
        return

    columns = {column["name"] for column in inspector.get_columns("armarios")}
    if "aluno_id" not in columns:
        aluno_column = sa.Column(
            "aluno_id",
            sa.Integer(),
            sa.ForeignKey(
                "alunos.id",
                name="fk_armarios_aluno_id_alunos",
                ondelete="SET NULL",
            ),
            nullable=True,
        )
        if bind.dialect.name == "sqlite":
            op.execute(
                "ALTER TABLE armarios ADD COLUMN aluno_id INTEGER "
                "CONSTRAINT fk_armarios_aluno_id_alunos "
                "REFERENCES alunos(id) ON DELETE SET NULL"
            )
        else:
            op.add_column(
                "armarios",
                aluno_column,
            )

    unique_constraints = inspector.get_unique_constraints("armarios")
    indexes = inspector.get_indexes("armarios")
    has_unique_student = any(
        constraint.get("column_names") == ["aluno_id"]
        for constraint in unique_constraints
    ) or any(
        index.get("column_names") == ["aluno_id"] and index.get("unique")
        for index in indexes
    )
    if not has_unique_student:
        op.create_index(
            "ix_armarios_aluno_id", "armarios", ["aluno_id"], unique=True
        )

    if "usuario_id" in columns:
        op.execute(
            "UPDATE armarios SET ocupado = 0, atribuido_em = NULL, usuario_id = NULL"
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "armarios" in tables:
        columns = {column["name"] for column in inspector.get_columns("armarios")}
        if "aluno_id" in columns:
            indexes = {index["name"] for index in inspector.get_indexes("armarios")}
            if "ix_armarios_aluno_id" in indexes:
                op.drop_index("ix_armarios_aluno_id", table_name="armarios")
            op.execute("UPDATE armarios SET ocupado = 0, atribuido_em = NULL")
            if bind.dialect.name == "sqlite":
                op.execute("ALTER TABLE armarios DROP COLUMN aluno_id")
            else:
                with op.batch_alter_table("armarios") as batch_op:
                    batch_op.drop_column("aluno_id")

    if "alunos" in tables:
        op.drop_table("alunos")
