"""Adicionar pagamentos divididos e desconto às vendas."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6c1427f9b20"
down_revision: Union[str, Sequence[str], None] = "de7bb194d29c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vendas",
        sa.Column("valor_subtotal", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "vendas",
        sa.Column("desconto", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "vendas",
        sa.Column("valor_pagamento_1", sa.Float(), nullable=True),
    )
    op.add_column(
        "vendas",
        sa.Column("forma_pagamento_2", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "vendas",
        sa.Column("valor_pagamento_2", sa.Float(), nullable=True),
    )
    op.execute(
        "UPDATE vendas SET valor_subtotal = valor_total, "
        "valor_pagamento_1 = valor_total"
    )


def downgrade() -> None:
    op.drop_column("vendas", "valor_pagamento_2")
    op.drop_column("vendas", "forma_pagamento_2")
    op.drop_column("vendas", "valor_pagamento_1")
    op.drop_column("vendas", "desconto")
    op.drop_column("vendas", "valor_subtotal")
