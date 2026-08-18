"""adicionar variacoes de produto e vendas

Revision ID: de7bb194d29c
Revises: 63663cdd5270
Create Date: 2026-08-17 23:26:29.251599

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de7bb194d29c'
down_revision: Union[str, Sequence[str], None] = '63663cdd5270'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # ---- produto_variacoes ----
    if 'produto_variacoes' not in existing_tables:
        op.create_table('produto_variacoes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('produto_id', sa.Integer(), nullable=False),
        sa.Column('tamanho', sa.String(length=20), nullable=False),
        sa.Column('cor', sa.String(length=50), nullable=False),
        sa.Column('sku', sa.String(length=50), nullable=True),
        sa.Column('preco', sa.Float(), nullable=True),
        sa.Column('estoque_atual', sa.Integer(), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['produto_id'], ['produtos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('produto_id', 'tamanho', 'cor', name='uq_variacao_produto_tamanho_cor'),
        sa.UniqueConstraint('sku')
        )
        with op.batch_alter_table('produto_variacoes', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_produto_variacoes_id'), ['id'], unique=False)

    # ---- categorias: indice unico em nome ----
    categorias_indexes = [ix['name'] for ix in inspector.get_indexes('categorias')]
    if 'ix_categorias_nome' not in categorias_indexes:
        with op.batch_alter_table('categorias', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_categorias_nome'), ['nome'], unique=True)

    # ---- produtos: remover coluna antiga estoque_atual ----
    produtos_columns = [c['name'] for c in inspector.get_columns('produtos')]
    if 'estoque_atual' in produtos_columns:
        with op.batch_alter_table('produtos', schema=None) as batch_op:
            batch_op.drop_column('estoque_atual')

    # ---- usuarios: ajustar tamanho da coluna role ----
    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.VARCHAR(length=11),
               type_=sa.String(length=20),
               existing_nullable=True)

    # ---- venda_itens: trocar produto_id por produto_variacao_id ----
    venda_itens_columns = [c['name'] for c in inspector.get_columns('venda_itens')]
    if 'produto_variacao_id' not in venda_itens_columns:
        with op.batch_alter_table('venda_itens', schema=None, recreate='always') as batch_op:
            batch_op.add_column(sa.Column('produto_variacao_id', sa.Integer(), nullable=True))
            batch_op.alter_column('id',
                   existing_type=sa.INTEGER(),
                   nullable=False,
                   autoincrement=True)
            batch_op.alter_column('preco_unitario',
                   existing_type=sa.REAL(),
                   type_=sa.Float(),
                   existing_nullable=False)
            batch_op.alter_column('valor_total',
                   existing_type=sa.REAL(),
                   type_=sa.Float(),
                   existing_nullable=False)
            batch_op.create_index(batch_op.f('ix_venda_itens_id'), ['id'], unique=False)
            batch_op.create_foreign_key(
                'fk_venda_itens_produto_variacao_id',
                'produto_variacoes', ['produto_variacao_id'], ['id'], ondelete='SET NULL'
            )
            if 'produto_id' in venda_itens_columns:
                batch_op.drop_column('produto_id')

    # ---- vendas: remover colunas antigas (fosseis de antes de existir venda_itens) ----
    vendas_columns = [c['name'] for c in inspector.get_columns('vendas')]
    with op.batch_alter_table('vendas', schema=None, recreate='always') as batch_op:
        batch_op.alter_column('responsavel',
               existing_type=sa.VARCHAR(),
               nullable=False)
        batch_op.alter_column('forma_pagamento',
               existing_type=sa.VARCHAR(),
               nullable=False)
        if 'preco_unitario' in vendas_columns:
            batch_op.drop_column('preco_unitario')
        if 'quantidade' in vendas_columns:
            batch_op.drop_column('quantidade')
        if 'produto_id' in vendas_columns:
            batch_op.drop_column('produto_id')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('vendas', schema=None) as batch_op:
        batch_op.add_column(sa.Column('produto_id', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('quantidade', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('preco_unitario', sa.REAL(), nullable=True))
        batch_op.alter_column('forma_pagamento',
               existing_type=sa.VARCHAR(),
               nullable=True)
        batch_op.alter_column('responsavel',
               existing_type=sa.VARCHAR(),
               nullable=True)

    with op.batch_alter_table('venda_itens', schema=None, recreate='always') as batch_op:
        batch_op.add_column(sa.Column('produto_id', sa.INTEGER(), nullable=True))
        batch_op.drop_constraint('fk_venda_itens_produto_variacao_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_venda_itens_id'))
        batch_op.alter_column('valor_total',
               existing_type=sa.Float(),
               type_=sa.REAL(),
               existing_nullable=False)
        batch_op.alter_column('preco_unitario',
               existing_type=sa.Float(),
               type_=sa.REAL(),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               nullable=True,
               autoincrement=True)
        batch_op.drop_column('produto_variacao_id')

    with op.batch_alter_table('usuarios', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.String(length=20),
               type_=sa.VARCHAR(length=11),
               existing_nullable=True)

    with op.batch_alter_table('produtos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('estoque_atual', sa.INTEGER(), nullable=False, server_default='0'))

    with op.batch_alter_table('categorias', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_categorias_nome'))

    with op.batch_alter_table('produto_variacoes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_produto_variacoes_id'))

    op.drop_table('produto_variacoes')