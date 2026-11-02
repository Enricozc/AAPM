import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


MIGRATION_FILE = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "f3a8b12d6c40_cadastro_de_alunos_para_armarios.py"
)
STUDENT_FIELDS_MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "f8c21d47a930_adicionar_ra_e_turma_a_alunos.py"
)


def test_migration_creates_student_roster_and_clears_legacy_assignments():
    spec = importlib.util.spec_from_file_location("armario_alunos_migration", MIGRATION_FILE)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()
            with connection.begin():
                connection.execute(
                    text(
                        """
                        CREATE TABLE armarios (
                            id INTEGER PRIMARY KEY,
                            numero VARCHAR(20) NOT NULL,
                            ocupado BOOLEAN NOT NULL,
                            usuario_id INTEGER,
                            atribuido_em DATETIME
                        )
                        """
                    )
                )
                connection.execute(
                    text(
                        """
                        CREATE TABLE armario_historico (
                            id INTEGER PRIMARY KEY,
                            armario_id INTEGER NOT NULL REFERENCES armarios(id)
                        )
                        """
                    )
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO armarios (id, numero, ocupado, usuario_id, atribuido_em)
                        VALUES (1, 'A1', 1, 42, '2026-01-01 10:00:00')
                        """
                    )
                )
                connection.execute(
                    text("INSERT INTO armario_historico (id, armario_id) VALUES (1, 1)")
                )

                context = MigrationContext.configure(connection)
                with Operations.context(context):
                    migration.upgrade()

                locker = connection.execute(
                    text(
                        "SELECT ocupado, usuario_id, aluno_id, atribuido_em FROM armarios"
                    )
                ).one()
                assert tuple(locker) == (0, None, None, None)
                assert connection.execute(
                    text("SELECT armario_id FROM armario_historico WHERE id=1")
                ).scalar_one() == 1
                assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
                assert "alunos" in inspect(connection).get_table_names()
                assert "nome" in {
                    column["name"]
                    for column in inspect(connection).get_columns("alunos")
                }

                with Operations.context(context):
                    migration.downgrade()
                assert "aluno_id" not in {
                    column["name"]
                    for column in inspect(connection).get_columns("armarios")
                }
                assert "alunos" not in inspect(connection).get_table_names()
                assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    finally:
        engine.dispose()


def test_student_fields_migration_preserves_existing_students_and_history():
    spec = importlib.util.spec_from_file_location(
        "student_fields_migration", STUDENT_FIELDS_MIGRATION
    )
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    engine = create_engine("sqlite://")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE alunos (
                        id INTEGER PRIMARY KEY,
                        nome VARCHAR(100) NOT NULL,
                        criado_em DATETIME
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    CREATE TABLE armario_historico (
                        id INTEGER PRIMARY KEY,
                        usuario_nome VARCHAR(100),
                        acao VARCHAR(20) NOT NULL
                    )
                    """
                )
            )
            connection.execute(
                text("INSERT INTO alunos (id, nome) VALUES (1, 'Ana Souza')")
            )
            connection.execute(
                text(
                    "INSERT INTO armario_historico (id, usuario_nome, acao) "
                    "VALUES (1, 'Ana Souza', 'ATRIBUIDO')"
                )
            )
            context = MigrationContext.configure(connection)
            with Operations.context(context):
                migration.upgrade()

            assert connection.execute(
                text("SELECT nome, ra, turma_curso FROM alunos WHERE id=1")
            ).one() == ("Ana Souza", None, None)
            assert connection.execute(
                text("SELECT usuario_nome, aluno_ra, aluno_turma_curso "
                     "FROM armario_historico WHERE id=1")
            ).one() == ("Ana Souza", None, None)
            assert any(
                index["name"] == "ix_alunos_ra" and index["unique"]
                for index in inspect(connection).get_indexes("alunos")
            )

            with Operations.context(context):
                migration.downgrade()
            assert "ra" not in {
                column["name"] for column in inspect(connection).get_columns("alunos")
            }
            assert connection.execute(
                text("SELECT nome FROM alunos WHERE id=1")
            ).scalar_one() == "Ana Souza"
    finally:
        engine.dispose()
