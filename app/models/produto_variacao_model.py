from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.config.database import Base


class ProdutoVariacao(Base):
    __tablename__ = "produto_variacoes"
    __table_args__ = (
        UniqueConstraint("produto_id", "tamanho", "cor", name="uq_variacao_produto_tamanho_cor"),
    )

    id            = Column(Integer, primary_key=True, autoincrement=True, index=True)
    produto_id    = Column(Integer, ForeignKey("produtos.id", ondelete="CASCADE"), nullable=False)
    tamanho       = Column(String(20), nullable=False)
    cor           = Column(String(50), nullable=False)
    sku           = Column(String(50), nullable=True, unique=True)
    preco         = Column(Float, nullable=True)  # se None, usa o preço base do produto
    estoque_atual = Column(Integer, nullable=False, default=0)
    ativo         = Column(Boolean, default=True)

    produto = relationship("Produto", back_populates="variacoes")

    @property
    def preco_efetivo(self):
        return self.preco if self.preco is not None else self.produto.preco

    @property
    def descricao(self):
        return f"{self.tamanho} / {self.cor}"